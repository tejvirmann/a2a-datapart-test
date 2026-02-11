"""
Proper Event Queue Setup for A2A Streaming
Shows how to set up event_queue so both messages and status updates work together
"""

import asyncio
from typing import Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# A2A TYPES
# ============================================================================

class TaskState(str, Enum):
    PENDING = "pending"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


def new_agent_parts_message(parts: list, role: str = "assistant") -> dict:
    """Create agent parts message"""
    return {
        "type": "agent_parts",
        "role": role,
        "parts": parts,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# EVENT QUEUE - Shared by everything
# ============================================================================

class EventQueue:
    """
    Event queue that handles all events (messages, status updates, artifacts)
    This is the single source of truth for all streaming events
    """
    
    def __init__(self):
        self.queue = asyncio.Queue()
    
    async def enqueue_event(self, event: dict):
        """
        Enqueue any event (message, status, artifact)
        This is the method you call directly
        """
        await self.queue.put(event)
    
    async def get_event(self):
        """Get next event from queue"""
        return await self.queue.get()
    
    def is_empty(self):
        """Check if queue is empty"""
        return self.queue.empty()


# ============================================================================
# TASK UPDATER - Uses the shared event queue
# ============================================================================

class TaskUpdater:
    """
    TaskUpdater that uses a shared event_queue
    All methods enqueue events through the same queue
    """
    
    def __init__(self, event_queue: EventQueue, task_id: str, context_id: str):
        """
        Initialize with shared event queue
        
        Args:
            event_queue: Shared EventQueue instance
            task_id: Task ID
            context_id: Context ID
        """
        self.event_queue = event_queue
        self.task_id = task_id
        self.context_id = context_id
        self.current_state = TaskState.PENDING
    
    async def update_status(self, state: TaskState):
        """
        Update task status - goes through event_queue
        """
        self.current_state = state
        
        status_event = {
            "type": "statusUpdate",
            "task_id": self.task_id,
            "context_id": self.context_id,
            "state": state.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Uses the shared event_queue
        await self.event_queue.enqueue_event(status_event)
    
    async def add_artifact_update(self, artifact_id: str, content: str, metadata: Optional[dict] = None):
        """
        Add artifact - goes through event_queue
        """
        artifact_event = {
            "type": "artifactUpdate",
            "task_id": self.task_id,
            "context_id": self.context_id,
            "artifact_id": artifact_id,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Uses the shared event_queue
        await self.event_queue.enqueue_event(artifact_event)
    
    async def complete(self):
        """
        Complete task - goes through event_queue
        """
        await self.update_status(TaskState.COMPLETED)
        # Send end signal
        await self.event_queue.enqueue_event(None)
    
    async def fail(self, error_message: str):
        """
        Fail task - goes through event_queue
        """
        await self.update_status(TaskState.FAILED)
        
        # Send error message
        error_message_event = new_agent_parts_message(
            parts=[{"type": "text", "content": f"❌ Error: {error_message}"}],
            role="system"
        )
        error_message_event["task_id"] = self.task_id
        error_message_event["context_id"] = self.context_id
        
        await self.event_queue.enqueue_event(error_message_event)
        
        # Send end signal
        await self.event_queue.enqueue_event(None)


# ============================================================================
# PROPER SETUP PATTERN
# ============================================================================

async def proper_workflow_setup(task_id: str, context_id: str, query: str):
    """
    Demonstrates proper setup where everything goes through event_queue
    """
    
    # 1. CREATE EVENT QUEUE FIRST (single source of truth)
    event_queue = EventQueue()
    
    # 2. CREATE TASK UPDATER WITH THE EVENT QUEUE
    updater = TaskUpdater(event_queue, task_id, context_id)
    
    # 3. NOW YOU CAN USE BOTH PATTERNS WITHOUT BLOCKING!
    
    try:
        # Pattern 1: Use updater methods (recommended for status)
        await updater.update_status(TaskState.WORKING)
        
        # Pattern 2: Direct event_queue.enqueue_event (for messages)
        message = new_agent_parts_message(
            parts=[{"type": "text", "content": "Running step 1"}]
        )
        message["task_id"] = task_id
        message["context_id"] = context_id
        await event_queue.enqueue_event(message)  # ✅ Works!
        
        # Pattern 1 again: Use updater
        await updater.update_status(TaskState.WORKING)
        
        # Pattern 2 again: Direct enqueue
        message2 = new_agent_parts_message(
            parts=[{"type": "text", "content": "Running step 2"}]
        )
        message2["task_id"] = task_id
        message2["context_id"] = context_id
        await event_queue.enqueue_event(message2)  # ✅ Works!
        
        # Stream chunks via direct enqueue
        result = "This is the final result"
        for word in result.split():
            chunk = new_agent_parts_message(
                parts=[{"type": "text", "content": word + " "}]
            )
            chunk["task_id"] = task_id
            chunk["context_id"] = context_id
            await event_queue.enqueue_event(chunk)  # ✅ Works!
        
        # Add artifact via updater
        await updater.add_artifact_update(
            artifact_id="final_result",
            content=result,
            metadata={"words": len(result.split())}
        )  # ✅ Works!
        
        # Complete via updater
        await updater.complete()  # ✅ Works!
        
    except Exception as e:
        await updater.fail(str(e))


# ============================================================================
# HELPER FUNCTION FOR CONVENIENCE
# ============================================================================

async def send_message(event_queue: EventQueue, task_id: str, context_id: str, 
                      content: str, role: str = "assistant"):
    """
    Helper function to send messages through event_queue
    Makes it easier to send messages without manual setup
    """
    message = new_agent_parts_message(
        parts=[{"type": "text", "content": content}],
        role=role
    )
    message["task_id"] = task_id
    message["context_id"] = context_id
    await event_queue.enqueue_event(message)


# ============================================================================
# COMPLETE EXAMPLE WITH BOTH PATTERNS
# ============================================================================

async def complete_example():
    """Complete example showing both patterns working together"""
    
    # Setup
    task_id = "task_123"
    context_id = "ctx_456"
    event_queue = EventQueue()
    updater = TaskUpdater(event_queue, task_id, context_id)
    
    try:
        # Start: Use updater
        await updater.update_status(TaskState.WORKING)
        
        # System message: Use event_queue directly
        system_msg = new_agent_parts_message(
            parts=[{"type": "text", "content": "🔍 Starting analysis..."}],
            role="system"
        )
        system_msg["task_id"] = task_id
        system_msg["context_id"] = context_id
        await event_queue.enqueue_event(system_msg)
        
        # Or use helper
        await send_message(event_queue, task_id, context_id, "Processing...", "system")
        
        # Status update: Use updater
        await updater.update_status(TaskState.WORKING)
        
        # Stream response: Use event_queue directly
        response = "Here is the analysis result"
        for word in response.split():
            chunk = new_agent_parts_message(
                parts=[{"type": "text", "content": word + " "}]
            )
            chunk["task_id"] = task_id
            chunk["context_id"] = context_id
            await event_queue.enqueue_event(chunk)
        
        # Artifact: Use updater
        await updater.add_artifact_update(
            artifact_id="analysis_result",
            content=response,
            metadata={"type": "analysis"}
        )
        
        # Complete: Use updater
        await updater.complete()
        
        # Now consume events
        print("\nEvents in queue (with details):")
        print("=" * 70)
        event_num = 1
        while not event_queue.is_empty():
            event = await event_queue.get_event()
            if event is None:
                print(f"\n{event_num}. [END] - Stream finished")
                break
            
            print(f"\n{event_num}. Type: {event['type']}")
            print(f"   Task ID: {event.get('task_id', 'N/A')}")
            print(f"   Context ID: {event.get('context_id', 'N/A')}")
            
            if event['type'] == 'statusUpdate':
                print(f"   State: {event.get('state', 'N/A')}")
            
            elif event['type'] == 'agent_parts':
                print(f"   Role: {event.get('role', 'N/A')}")
                print(f"   Parts: {event.get('parts', [])}")
            
            elif event['type'] == 'artifactUpdate':
                print(f"   Artifact ID: {event.get('artifact_id', 'N/A')}")
                print(f"   Content: {event.get('content', 'N/A')}")
                print(f"   Metadata: {event.get('metadata', {})}")
            
            event_num += 1
        
        print("=" * 70)
        
    except Exception as e:
        await updater.fail(str(e))


# ============================================================================
# KEY PRINCIPLES
# ============================================================================

"""
KEY PRINCIPLES:

1. CREATE EVENT_QUEUE FIRST
   event_queue = EventQueue()

2. PASS IT TO TASK_UPDATER
   updater = TaskUpdater(event_queue, task_id, context_id)

3. BOTH PATTERNS USE THE SAME QUEUE:
   
   Pattern A (via updater):
     await updater.update_status(TaskState.WORKING)
     await updater.add_artifact_update(...)
     await updater.complete()
   
   Pattern B (direct queue):
     message = new_agent_parts_message(...)
     message["task_id"] = task_id
     message["context_id"] = context_id
     await event_queue.enqueue_event(message)

4. NO BLOCKING because everything goes through the same queue

5. UPDATER METHODS internally call event_queue.enqueue_event()
"""


if __name__ == "__main__":
    print("Event Queue Setup Example")
    print("=" * 70)
    print("\nProper setup:")
    print("1. event_queue = EventQueue()")
    print("2. updater = TaskUpdater(event_queue, task_id, context_id)")
    print("3. Use both patterns freely - they share the same queue!")
    print("\nRunning example...")
    asyncio.run(complete_example())
