# A2A EventQueue & TaskUpdater Test Project

> **Testing and examples for A2A SDK 0.3.22 EventQueue and TaskUpdater patterns**

This project demonstrates proper usage of the A2A Python SDK, focusing on `EventQueue`, `TaskUpdater`, and message streaming patterns.

---

## 📁 Project Structure

```
a2a-datapart-test/
├── examples/          # Working code examples
├── tests/             # Test scripts to verify behavior
├── docs/              # Documentation and guides
├── requirements.txt   # Python dependencies
├── Makefile          # Common commands
└── README.md         # This file
```

---

## 🚀 Quick Start

### 1. Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Tests

```bash
# Prove enqueue_event() works correctly
python tests/PROOF_QUEUE_WORKS.py

# Diagnose common queue issues
python tests/FINAL_DIAGNOSIS.py

# Test specific enqueue methods
python tests/test_enqueue_methods.py
```

### 3. Run Examples

```bash
# Simple executor example
python examples/executor_with_taskupdater.py

# Streaming server (run in separate terminal)
python examples/stream_server.py

# Streaming client (in another terminal)
python examples/stream_client.py
```

---

## 📝 Examples

### Core Examples

| File | Purpose | Run Command |
|------|---------|-------------|
| **`event_queue_setup.py`** | Shows proper shared EventQueue setup | `python examples/event_queue_setup.py` |
| **`executor_with_taskupdater.py`** | AgentExecutor with TaskUpdater pattern | `python examples/executor_with_taskupdater.py` |
| **`stream_server.py`** | FastAPI server with SSE streaming | `python examples/stream_server.py` |
| **`stream_client.py`** | Client to consume streamed events | `python examples/stream_client.py` |

### Utility Modules

| File | Purpose |
|------|---------|
| **`a2a_utils.py`** | Reference implementations of EventQueue, TaskUpdater, TaskState |
| **`agent_executor.py`** | Reference AgentExecutor with LangGraph-style nodes |

---

## 🧪 Tests

### Main Test Files

#### **`PROOF_QUEUE_WORKS.py`** ⭐ **MOST IMPORTANT**
**Purpose:** Definitively proves that `enqueue_event()` works correctly with the real A2A SDK 0.3.22.

**What it tests:**
- ✅ 10 consecutive `enqueue_event()` calls
- ✅ Complex messages with `DataPart` and `TextPart`
- ✅ Mixing `update_status()` and `enqueue_event()`
- ✅ Queue behavior after `complete()`
- ✅ Queue never blocks or closes unexpectedly

**Run:**
```bash
python tests/PROOF_QUEUE_WORKS.py
```

**Expected Output:**
```
✅ enqueue_event() works perfectly!
✅ Queue never blocks, even after complete()!
✅ Same queue (event_queue is updater.event_queue) works fine!
```

---

#### **`FINAL_DIAGNOSIS.py`** ⭐ **DIAGNOSE YOUR ISSUES**
**Purpose:** Replicates common `update_status()` bugs and shows the correct patterns.

**What it tests:**
- ❌ Wrong pattern: Passing `Message` as first arg to `update_status()`
- ✅ Correct pattern: Using `TaskState` as first arg
- ✅ Optional message parameter
- ✅ Direct `enqueue_event()` usage
- ✅ Queue closure behavior

**Run:**
```bash
python tests/FINAL_DIAGNOSIS.py
```

**Use this when:**
- You get `TypeError` from `update_status()`
- Your queue seems to "block"
- You're unsure of correct `update_status()` usage

---

#### **`test_enqueue_methods.py`**
**Purpose:** Answers: "Does `enqueue_event()` or `enqueue()` exist?"

**What it tests:**
- ✅ Checks if `event_queue.enqueue_event()` exists (YES)
- ❌ Checks if `event_queue.enqueue()` exists (NO)
- ✅ Lists all available EventQueue methods
- ✅ Tests both methods if they exist

**Run:**
```bash
python tests/test_enqueue_methods.py
```

**Expected Output:**
```
✅ YES: event_queue.enqueue_event(message) EXISTS and WORKS
❌ NO: event_queue.enqueue(message) does NOT exist
```

---

#### **`simple_blocking_test.py`**
**Purpose:** Simple test to show when queue actually closes.

**What it tests:**
- ✅ Multiple `enqueue_event()` calls
- ✅ Queue state before/after `complete()`
- ✅ Basic queue behavior

**Run:**
```bash
python tests/simple_blocking_test.py
```

---

## 📚 Documentation

### Guides

| File | Purpose |
|------|---------|
| **`EVENT_QUEUE_GUIDE.md`** | Comprehensive guide to EventQueue setup and usage |
| **`WHY_QUEUE_BLOCKS.md`** | Troubleshooting guide for queue blocking issues |
| **`YOUR_BUG_EXPLAINED.md`** | Common bugs and their fixes |

---

## 🔧 Common Use Cases

### Use Case 1: Send a Message to the Queue

```python
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart

# Setup
event_queue = EventQueue()
updater = TaskUpdater(event_queue, task_id="task-123", context_id="ctx-456")

# Create and send message
message = updater.new_agent_message([
    Part(root=TextPart(text="Hello from agent"))
])
await event_queue.enqueue_event(message)
```

---

### Use Case 2: Update Task Status

```python
from a2a.types import TaskState

# ✅ CORRECT: State only
await updater.update_status(TaskState.working)

# ✅ CORRECT: State + message
message = updater.new_agent_message([...])
await updater.update_status(TaskState.working, message=message)

# ❌ WRONG: Missing TaskState
await updater.update_status(message)  # This fails!
```

---

### Use Case 3: Send Data Parts

```python
from a2a.types import Part, DataPart, TextPart

data = {"status": "started", "progress": 0}

message = updater.new_agent_message([
    Part(root=DataPart(mime_type="application/json", data=data)),
    Part(root=TextPart(text="Task started"))
])

await event_queue.enqueue_event(message)
```

---

### Use Case 4: Complete a Task

```python
# Send final message
final_message = updater.new_agent_message([
    Part(root=TextPart(text="Task completed successfully"))
])
await event_queue.enqueue_event(final_message)

# Mark task as complete
await updater.complete()
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "Queue is closed" Error

**Symptoms:**
- `enqueue_event()` fails with "queue is closed"
- Messages stop being sent

**Causes:**
1. Different `EventQueue` instances
2. Calling `complete()` too early
3. Exception in code flow

**Solution:**
```python
# ✅ CORRECT: Use same queue instance
event_queue = EventQueue()
updater = TaskUpdater(event_queue, task_id, context_id)

# Verify same queue
assert event_queue is updater.event_queue  # Should be True
```

**Run this test:**
```bash
python tests/PROOF_QUEUE_WORKS.py
```

---

### Issue 2: `TypeError` from `update_status()`

**Symptoms:**
- `TypeError: cannot use 'a2a.types.Message' as a set element`

**Cause:**
- Missing `TaskState` as first argument

**Solution:**
```python
# ❌ WRONG
await updater.update_status(
    updater.new_agent_message([...])  # Missing TaskState!
)

# ✅ CORRECT
await updater.update_status(
    TaskState.working,  # First arg is TaskState
    message=updater.new_agent_message([...])  # Message is optional
)
```

**Run this test:**
```bash
python tests/FINAL_DIAGNOSIS.py
```

---

### Issue 3: Not Sure Which Method to Use

**Question:** Should I use `enqueue_event()` or `enqueue()`?

**Answer:** Use `enqueue_event()` - it's the only method that exists!

**Verify:**
```bash
python tests/test_enqueue_methods.py
```

---

## 📦 Dependencies

```
a2a-sdk==0.3.22    # A2A Python SDK
fastapi            # For streaming server example
uvicorn            # ASGI server
httpx              # HTTP client with SSE support
```

Install all:
```bash
pip install -r requirements.txt
```

---

## 🎯 Key Learnings

### EventQueue
- ✅ Use `event_queue.enqueue_event(message)`
- ✅ Pass the SAME queue instance to `TaskUpdater`
- ✅ Queue does NOT close after `complete()` in SDK 0.3.22
- ✅ Use `await` for async methods

### TaskUpdater
- ✅ `update_status(state, message=None, final=False)`
  - First arg: `TaskState` (required)
  - Second arg: `message` (optional)
- ✅ Use `updater.new_agent_message([parts])` to create messages
- ✅ Call `complete()` only at the very end

### Message Creation
- ✅ Use `Part(root=TextPart(text="..."))` for text
- ✅ Use `Part(root=DataPart(mime_type="...", data={...}))` for structured data
- ✅ Always pass a list of `Part` objects

---

## 📖 Further Reading

1. **Start here:** Run `python tests/PROOF_QUEUE_WORKS.py`
2. **If issues:** Read `docs/YOUR_BUG_EXPLAINED.md`
3. **Deep dive:** Read `docs/EVENT_QUEUE_GUIDE.md`
4. **Troubleshooting:** Read `docs/WHY_QUEUE_BLOCKS.md`

---

## 🤝 Contributing

This is a test/example project. Feel free to:
- Add more examples
- Improve documentation
- Report issues

---

## 📄 License

MIT

---

## 🔗 Resources

- [A2A SDK GitHub](https://github.com/a2aproject/a2a-python)
- [A2A Protocol](https://a2a-protocol.org/)

---

**Last Updated:** February 11, 2026  
**A2A SDK Version:** 0.3.22  
**Python Version:** 3.14+
