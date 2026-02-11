# 🎯 Event Queue Setup Guide

## The Problem You Were Having

```python
# ❌ WRONG: Separate queues cause blocking
eventqueue = SomeQueue()
updater = TaskUpdater(different_queue, task_id, context_id)

await eventqueue.enqueue_event(message)  # Goes to one queue
await updater.add_artifact(artifact)     # Goes to different queue ❌ BLOCKS!
await updater.complete()                 # Never reached!
```

---

## ✅ The Solution: Shared Event Queue

```python
# ✅ CORRECT: One queue for everything
event_queue = EventQueue()
updater = TaskUpdater(event_queue, task_id, context_id)

await event_queue.enqueue_event(message)  # Same queue ✅
await updater.add_artifact(artifact)       # Same queue ✅
await updater.complete()                   # Same queue ✅ Works!
```

---

## 📋 Step-by-Step Setup

### Step 1: Create Event Queue FIRST

```python
from asyncio import Queue

class EventQueue:
    def __init__(self):
        self.queue = Queue()  # Single asyncio.Queue
    
    async def enqueue_event(self, event: dict):
        """All events go through here"""
        await self.queue.put(event)
    
    async def get_event(self):
        return await self.queue.get()
```

### Step 2: Create TaskUpdater WITH the Event Queue

```python
class TaskUpdater:
    def __init__(self, event_queue: EventQueue, task_id: str, context_id: str):
        self.event_queue = event_queue  # ✅ Stores reference to shared queue
        self.task_id = task_id
        self.context_id = context_id
    
    async def update_status(self, state: TaskState):
        """Uses the shared event_queue"""
        status_event = {...}
        await self.event_queue.enqueue_event(status_event)  # ✅ Same queue!
    
    async def add_artifact_update(self, artifact_id, content, metadata):
        """Uses the shared event_queue"""
        artifact_event = {...}
        await self.event_queue.enqueue_event(artifact_event)  # ✅ Same queue!
```

### Step 3: Use Both Patterns Freely

```python
# Initialize
event_queue = EventQueue()
updater = TaskUpdater(event_queue, task_id, context_id)

# Method 1: Direct event_queue (for messages)
message = new_agent_parts_message(parts=[...])
message["task_id"] = task_id
message["context_id"] = context_id
await event_queue.enqueue_event(message)  # ✅

# Method 2: Via updater (for status/artifacts)
await updater.update_status(TaskState.WORKING)  # ✅
await updater.add_artifact_update(...)           # ✅
await updater.complete()                         # ✅

# ALL GO TO THE SAME QUEUE - NO BLOCKING!
```

---

## 🎯 Complete Working Example

```python
import asyncio
from enum import Enum

class TaskState(str, Enum):
    PENDING = "pending"
    WORKING = "working"
    COMPLETED = "completed"

class EventQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
    
    async def enqueue_event(self, event: dict):
        await self.queue.put(event)
    
    async def get_event(self):
        return await self.queue.get()

class TaskUpdater:
    def __init__(self, event_queue: EventQueue, task_id: str, context_id: str):
        self.event_queue = event_queue
        self.task_id = task_id
        self.context_id = context_id
    
    async def update_status(self, state: TaskState):
        await self.event_queue.enqueue_event({
            "type": "statusUpdate",
            "task_id": self.task_id,
            "context_id": self.context_id,
            "state": state.value
        })
    
    async def add_artifact_update(self, artifact_id, content, metadata):
        await self.event_queue.enqueue_event({
            "type": "artifactUpdate",
            "task_id": self.task_id,
            "context_id": self.context_id,
            "artifact_id": artifact_id,
            "content": content,
            "metadata": metadata
        })
    
    async def complete(self):
        await self.update_status(TaskState.COMPLETED)
        await self.event_queue.enqueue_event(None)  # End signal

# Usage
async def my_workflow():
    # Setup (ORDER MATTERS!)
    event_queue = EventQueue()  # 1. Create queue
    updater = TaskUpdater(event_queue, "task_1", "ctx_1")  # 2. Pass to updater
    
    # Now use both patterns
    await updater.update_status(TaskState.WORKING)  # ✅
    
    # Send message directly
    message = {"type": "agent_parts", "parts": [...]}
    message["task_id"] = "task_1"
    message["context_id"] = "ctx_1"
    await event_queue.enqueue_event(message)  # ✅
    
    # Add artifact via updater
    await updater.add_artifact_update("result", "data", {})  # ✅
    
    # Complete via updater
    await updater.complete()  # ✅ NO BLOCKING!
```

---

## 🔍 Why Your Code Was Blocking

### Your Original Code (Broken):
```python
# Two separate queues!
eventqueue = create_some_queue()           # Queue A
updater = TaskUpdater(internal_queue, ...) # Queue B (different!)

await eventqueue.enqueue_event(message)    # → Queue A
await updater.add_artifact(artifact)       # → Queue B ❌ Waiting for Queue A?
```

### Fixed Code:
```python
# One shared queue!
event_queue = EventQueue()                    # Create queue
updater = TaskUpdater(event_queue, ...)       # Pass THE SAME queue

await event_queue.enqueue_event(message)      # → Shared queue ✅
await updater.add_artifact(artifact)          # → Shared queue ✅ No blocking!
```

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                Your Code                        │
│                                                 │
│  event_queue = EventQueue()   ← CREATE FIRST   │
│  updater = TaskUpdater(event_queue, ...)       │
│                     ↓                           │
│                  SHARE THE QUEUE                │
└─────────────────────────────────────────────────┘
                      ↓
         ┌────────────┴────────────┐
         ↓                         ↓
┌────────────────┐        ┌────────────────┐
│  event_queue   │        │    updater     │
│  .enqueue()    │───────→│  .update_status│
│                │  BOTH  │  .add_artifact │
│                │  USE   │  .complete()   │
│                │  SAME  │                │
│                │  QUEUE │  (internally   │
│                │        │   calls queue) │
└────────────────┘        └────────────────┘
         ↓                         ↓
         └────────────┬────────────┘
                      ↓
         ┌────────────────────────┐
         │   asyncio.Queue()      │
         │   (Single Source)      │
         │                        │
         │  [statusUpdate]        │
         │  [agent_parts]         │
         │  [artifactUpdate]      │
         │  [None] (end)          │
         └────────────────────────┘
                      ↓
              Stream Consumer
```

---

## ✅ Checklist

- [ ] Create `EventQueue()` first
- [ ] Pass it to `TaskUpdater(event_queue, task_id, context_id)`
- [ ] Use `await event_queue.enqueue_event(message)` for messages
- [ ] Use `await updater.update_status()` for status
- [ ] Use `await updater.add_artifact_update()` for artifacts
- [ ] Use `await updater.complete()` to finish
- [ ] All methods internally use the same `event_queue.enqueue_event()`

---

## 🎯 Key Principle

**ONE QUEUE TO RULE THEM ALL**

```python
# ✅ This is the secret
event_queue = EventQueue()           # Single queue
updater = TaskUpdater(event_queue)   # Uses same queue

# Everything goes to the same place
await event_queue.enqueue_event(...)  # → queue
await updater.anything()              # → queue (internally)

# No blocking, no conflicts!
```

---

See `event_queue_setup.py` for complete working code! 🎉
