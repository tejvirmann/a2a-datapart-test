"""
A2A Agent Executor Example - With Proper Imports
Demonstrates proper usage of A2A utilities with streaming
Shows difference between messages (with parts) and status updates (without parts)
"""

import asyncio

# ✅ A2A IMPORTS - Using proper A2A utilities
from a2a_utils import (
    TaskUpdater,
    EventQueue,
    TaskState,
    new_agent_parts_message
)
from agent_executor import AgentExecutor


# ============================================================================
# SPECIFIC ANSWER TO YOUR QUESTIONS
# ============================================================================

async def answer_your_questions():
    """
    Answers:
    1. Should message have dataparts when added to event_queue? YES
    2. Should it have dataparts when using update_status? NO
    """
    
    print("\n" + "=" * 80)
    print("ANSWERING YOUR QUESTIONS - Using A2A Imports")
    print("=" * 80)
    
    # ✅ Using imported EventQueue and TaskUpdater
    event_queue = EventQueue()
    updater = TaskUpdater(event_queue, "task_1", "ctx_1")
    
    print("\nQUESTION 1: Create message and add to event_queue")
    print("-" * 80)
    print("Should this message have dataparts? ✅ YES\n")
    
    # Create message WITH parts using imported utility
    message = new_agent_parts_message(
        parts=[{"type": "text", "content": "Hello world"}],  # ✅ HAS PARTS
        role="assistant"
    )
    message["task_id"] = "task_1"
    message["context_id"] = "ctx_1"
    
    print("Created message:")
    print(f"  Type: {message['type']}")
    print(f"  Has 'parts' field: {('parts' in message)}")
    print(f"  Parts: {message['parts']}")
    
    await event_queue.enqueue(message)
    print("\n✅ Added to event_queue with parts!")
    
    print("\n" + "=" * 80)
    print("QUESTION 2: Add via updater.update_status()")
    print("-" * 80)
    print("Should it have dataparts? ❌ NO - Status updates are state-only\n")
    
    # Update status (NO parts) using imported TaskUpdater
    await updater.update_status(TaskState.WORKING)
    
    # Retrieve and show
    msg_from_queue = await event_queue.get()
    status_from_queue = await event_queue.get()
    
    print("Message from queue (from event_queue.enqueue):")
    print(f"  Type: {msg_from_queue['type']}")
    print(f"  Has 'parts': {('parts' in msg_from_queue)} ✅")
    print(f"  Parts: {msg_from_queue.get('parts')}")
    
    print("\nStatus update from queue (from updater.update_status):")
    print(f"  Type: {status_from_queue['type']}")
    print(f"  Has 'parts': {('parts' in status_from_queue)} ❌")
    print(f"  Has 'state': {('state' in status_from_queue)} ✅")
    print(f"  State: {status_from_queue.get('state')}")
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print("✅ event_queue.enqueue(message)     → message HAS parts")
    print("❌ updater.update_status(state)     → NO parts, just state")
    print("=" * 80)


# ============================================================================
# DEMONSTRATION WITH AGENT EXECUTOR
# ============================================================================

async def demonstrate_agent_executor():
    """
    Demonstrates:
    1. ✅ Using AgentExecutor (imported from agent_executor.py)
    2. ✅ Streaming messages (word-by-word)
    3. Messages added via event_queue.enqueue() - HAS PARTS
    4. Status updates via updater.update_status() - NO PARTS
    """
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION: Agent Executor with Streaming")
    print("=" * 80)
    
    # Setup with imported classes
    event_queue = EventQueue()
    task_id = "task_123"
    context_id = "ctx_456"
    
    # ✅ Using imported AgentExecutor
    executor = AgentExecutor(event_queue, task_id, context_id)
    
    # Execute
    print("\n▶️  Executing workflow...\n")
    await executor.execute("Test query")
    
    # Read events and show difference
    print("\n" + "=" * 80)
    print("STREAMING EVENTS IN QUEUE:")
    print("=" * 80)
    
    event_num = 1
    while not event_queue.is_empty():
        event = await event_queue.get()
        
        if event is None:
            print(f"\n{event_num}. END SIGNAL")
            break
        
        print(f"\n{event_num}. Type: {event['type']}")
        
        if event['type'] == 'statusUpdate':
            print("   ❌ NO PARTS - Status updates are state-only")
            print(f"   State: {event.get('state')}")
            print(f"   Task ID: {event.get('task_id')}")
            print(f"   Context ID: {event.get('context_id')}")
        
        elif event['type'] == 'agent_parts':
            print("   ✅ HAS PARTS - Messages have content (STREAMING)")
            print(f"   Role: {event.get('role')}")
            print(f"   Parts: {event.get('parts')}")
            print(f"   Task ID: {event.get('task_id')}")
            print(f"   Context ID: {event.get('context_id')}")
        
        elif event['type'] == 'artifactUpdate':
            print("   ✅ HAS CONTENT - Artifacts have content")
            print(f"   Artifact ID: {event.get('artifact_id')}")
            print(f"   Content: {event.get('content')}")
        
        event_num += 1
    
    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS:")
    print("=" * 80)
    print("✅ Using A2A imports:")
    print("   - from a2a_utils import TaskUpdater, EventQueue, TaskState")
    print("   - from agent_executor import AgentExecutor")
    print()
    print("✅ Streaming works:")
    print("   - Messages added via event_queue.enqueue()")
    print("   - HAS 'parts' field with content")
    print("   - Word-by-word delivery")
    print()
    print("❌ Status updates:")
    print("   - Via updater.update_status()")
    print("   - NO 'parts' field")
    print("   - ONLY has 'state' field (WORKING, COMPLETED, etc.)")
    print("=" * 80)


# ============================================================================
# IMPORTS SUMMARY
# ============================================================================

def show_imports():
    """Show what imports are being used"""
    print("\n" + "=" * 80)
    print("A2A IMPORTS USED IN THIS FILE:")
    print("=" * 80)
    print()
    print("from a2a_utils import (")
    print("    TaskUpdater,        # ← Manages task lifecycle and updates")
    print("    EventQueue,         # ← Shared queue for all events")
    print("    TaskState,          # ← Enum for task states")
    print("    new_agent_parts_message  # ← Creates messages WITH parts")
    print(")")
    print()
    print("from agent_executor import (")
    print("    AgentExecutor       # ← Orchestrates workflow execution")
    print(")")
    print("=" * 80)


if __name__ == "__main__":
    print("=" * 80)
    print("A2A EXECUTOR WITH PROPER IMPORTS")
    print("=" * 80)
    
    # Show imports
    show_imports()
    
    # Run demonstrations
    asyncio.run(answer_your_questions())
    asyncio.run(demonstrate_agent_executor())
    
    print("\n" + "=" * 80)
    print("✅ All demonstrations complete!")
    print("=" * 80)
