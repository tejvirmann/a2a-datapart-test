"""
A2A Agent Executor
Orchestrates workflow execution with TaskUpdater and EventQueue
"""

import asyncio
from typing import TypedDict

# A2A imports
from a2a_utils import (
    TaskUpdater,
    EventQueue,
    TaskState,
    new_agent_parts_message
)


# ============================================================================
# AGENT STATE
# ============================================================================

class AgentState(TypedDict):
    """State for the agent workflow"""
    messages: list
    current_step: str
    task_id: str
    context_id: str


# ============================================================================
# AGENT NODES
# ============================================================================

async def research_node(
    state: AgentState, 
    updater: TaskUpdater, 
    event_queue: EventQueue
) -> AgentState:
    """
    Research node - demonstrates streaming with parts
    """
    
    # Update status (NO PARTS)
    await updater.update_status(TaskState.WORKING)
    
    # Create message WITH PARTS and add to queue
    message = new_agent_parts_message(
        parts=[{"type": "text", "content": "🔍 Researching..."}],
        role="system"
    )
    message["task_id"] = state["task_id"]
    message["context_id"] = state["context_id"]
    
    # Add to event queue directly
    await event_queue.enqueue(message)
    
    # Do work
    result = "Research complete"
    
    # ✅ STREAMING: word-by-word (messages WITH PARTS)
    for word in result.split():
        chunk = new_agent_parts_message(
            parts=[{"type": "text", "content": word + " "}],
            role="assistant"
        )
        chunk["task_id"] = state["task_id"]
        chunk["context_id"] = state["context_id"]
        await event_queue.enqueue(chunk)
    
    state["messages"].append({"role": "assistant", "content": result})
    return state


async def summary_node(
    state: AgentState, 
    updater: TaskUpdater, 
    event_queue: EventQueue
) -> AgentState:
    """
    Summary node - demonstrates artifact updates
    """
    
    # Status update (NO PARTS)
    await updater.update_status(TaskState.WORKING)
    
    # System message (HAS PARTS)
    msg = new_agent_parts_message(
        parts=[{"type": "text", "content": "📝 Creating summary..."}],
        role="system"
    )
    msg["task_id"] = state["task_id"]
    msg["context_id"] = state["context_id"]
    await event_queue.enqueue(msg)
    
    summary = "Final summary complete"
    
    # ✅ STREAMING: word-by-word
    for word in summary.split():
        chunk = new_agent_parts_message(
            parts=[{"type": "text", "content": word + " "}],
            role="assistant"
        )
        chunk["task_id"] = state["task_id"]
        chunk["context_id"] = state["context_id"]
        await event_queue.enqueue(chunk)
    
    # Artifact (HAS CONTENT)
    await updater.add_artifact_update(
        artifact_id="summary",
        content=summary,
        metadata={"type": "summary"}
    )
    
    state["messages"].append({"role": "assistant", "content": summary})
    return state


# ============================================================================
# AGENT EXECUTOR (A2A Pattern)
# ============================================================================

class AgentExecutor:
    """
    A2A Agent Executor
    
    Manages workflow execution with TaskUpdater and EventQueue.
    Uses proper A2A imports for streaming message delivery.
    
    Key Features:
    - Orchestrates agent nodes
    - Manages task lifecycle via TaskUpdater
    - Streams messages with parts via EventQueue
    - Handles errors gracefully
    
    Usage:
        event_queue = EventQueue()
        executor = AgentExecutor(event_queue, task_id, context_id)
        await executor.execute("Your query here")
    """
    
    def __init__(self, event_queue: EventQueue, task_id: str, context_id: str):
        """
        Initialize the executor
        
        Args:
            event_queue: Shared EventQueue for all events
            task_id: Unique task identifier
            context_id: Context identifier
        """
        self.event_queue = event_queue
        self.task_id = task_id
        self.context_id = context_id
        self.updater = TaskUpdater(event_queue, task_id, context_id)
    
    async def execute(self, query: str) -> AgentState:
        """
        Execute the workflow
        
        Args:
            query: User query to process
        
        Returns:
            Final agent state
        
        Flow:
            1. Update status to WORKING (NO parts)
            2. Execute agent nodes (stream messages WITH parts)
            3. Complete task (status update + end signal)
        """
        try:
            # Initial status (NO PARTS)
            await self.updater.update_status(TaskState.WORKING)
            
            # Initial state
            initial_state: AgentState = {
                "messages": [{"role": "user", "content": query}],
                "current_step": "start",
                "task_id": self.task_id,
                "context_id": self.context_id
            }
            
            # Execute nodes (pass both updater and event_queue)
            state = initial_state
            state = await research_node(state, self.updater, self.event_queue)
            state = await summary_node(state, self.updater, self.event_queue)
            
            # Complete (status update + end signal)
            await self.updater.complete()
            
            return state
            
        except Exception as e:
            # Fail gracefully
            await self.updater.fail(str(e))
            raise


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """
    Example usage of AgentExecutor with proper A2A imports
    """
    print("=" * 80)
    print("A2A AGENT EXECUTOR - Streaming Demo")
    print("=" * 80)
    print()
    
    # Setup
    event_queue = EventQueue()
    task_id = "task_123"
    context_id = "ctx_456"
    
    # Create executor
    executor = AgentExecutor(event_queue, task_id, context_id)
    
    # Execute workflow
    print("▶️  Starting workflow...\n")
    await executor.execute("Test query")
    
    # Read and display events
    print("=" * 80)
    print("STREAMING EVENTS:")
    print("=" * 80)
    
    event_num = 1
    while not event_queue.is_empty():
        event = await event_queue.get()
        
        if event is None:
            print(f"\n{event_num}. 🏁 END SIGNAL")
            break
        
        event_type = event.get("type")
        print(f"\n{event_num}. Type: {event_type}")
        
        if event_type == "statusUpdate":
            print("   ❌ NO PARTS - Status updates are state-only")
            print(f"   State: {event.get('state')}")
        
        elif event_type == "agent_parts":
            print("   ✅ HAS PARTS - Streaming message content")
            parts = event.get('parts', [])
            if parts:
                content = parts[0].get('content', '')
                print(f"   Content: {content}")
        
        elif event_type == "artifactUpdate":
            print("   ✅ HAS CONTENT - Artifact update")
            print(f"   Artifact ID: {event.get('artifact_id')}")
        
        event_num += 1
    
    print("\n" + "=" * 80)
    print("✅ Workflow complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
