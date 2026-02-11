"""
Simple test: Why does enqueue_event() cause blocking when queue is the same?
"""

import asyncio
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart

async def test():
    print("Testing queue blocking scenario...\n")
    
    # Setup - same queue
    event_queue = EventQueue()
    updater = TaskUpdater(event_queue, "task-123", "context-456")
    
    print(f"Queue is same: {event_queue is updater.event_queue}")
    print(f"Queue closed: {event_queue.is_closed()}\n")
    
    # First enqueue_event - should work
    print("1. First enqueue_event()...")
    msg1 = updater.new_agent_message([Part(root=TextPart(text="Message 1"))])
    await event_queue.enqueue_event(msg1)
    print(f"   ✅ Success! Queue closed: {event_queue.is_closed()}\n")
    
    # Second enqueue_event - should work
    print("2. Second enqueue_event()...")
    msg2 = updater.new_agent_message([Part(root=TextPart(text="Message 2"))])
    await event_queue.enqueue_event(msg2)
    print(f"   ✅ Success! Queue closed: {event_queue.is_closed()}\n")
    
    # Call complete - THIS closes the queue
    print("3. Calling updater.complete()...")
    await updater.complete()
    print(f"   Queue closed: {event_queue.is_closed()}\n")
    
    # Third enqueue_event - THIS should fail
    print("4. Third enqueue_event() AFTER complete()...")
    try:
        msg3 = updater.new_agent_message([Part(root=TextPart(text="Message 3"))])
        await event_queue.enqueue_event(msg3)
        print(f"   ✅ Still worked? Queue closed: {event_queue.is_closed()}")
    except Exception as e:
        print(f"   ❌ BLOCKED: {e}")
    
    print("\n" + "="*60)
    print("ANSWER: Queue blocks when complete() is called!")
    print("="*60)

asyncio.run(test())
