# 🚀 Quick Start Guide

## 1️⃣ Setup (One-Time)

```bash
# Navigate to project
cd /Users/tejvirmann/Documents/a2a-datapart-test

# Setup virtual environment and install dependencies
make setup

# Activate virtual environment
source venv/bin/activate
```

---

## 2️⃣ Run Tests (Recommended First Step)

### Prove enqueue_event() Works ⭐
```bash
make test-proof
```
**This proves the SDK works correctly!**

### Diagnose Common Issues ⭐
```bash
make test-diag
```
**Shows your exact bug and how to fix it!**

### Test Which Methods Exist
```bash
make test-methods
```

### Run All Tests
```bash
make test
```

---

## 3️⃣ Run Examples

### Simple Executor
```bash
make run-executor
```

### Streaming Server & Client

**Terminal 1 - Start Server:**
```bash
make run-server
```

**Terminal 2 - Run Client:**
```bash
make run-client
```

---

## 4️⃣ Read Documentation

1. **Main README**: `README.md` - Complete reference
2. **Event Queue Guide**: `docs/EVENT_QUEUE_GUIDE.md`
3. **Troubleshooting**: `docs/WHY_QUEUE_BLOCKS.md`
4. **Bug Fixes**: `docs/YOUR_BUG_EXPLAINED.md`

---

## 5️⃣ Common Commands

```bash
make help          # Show all commands
make setup         # Install dependencies
make test          # Run all tests
make test-proof    # Prove enqueue_event works
make test-diag     # Diagnose issues
make run-executor  # Run executor example
make run-server    # Start streaming server
make run-client    # Start client
make clean         # Clean cache files
make list          # Show project structure
```

---

## 📁 Project Structure

```
a2a-datapart-test/
├── examples/              # Working code examples
│   ├── a2a_utils.py                 # Reference SDK utilities
│   ├── agent_executor.py            # Reference executor
│   ├── event_queue_setup.py         # Shared queue setup
│   ├── executor_with_taskupdater.py # Full executor example
│   ├── stream_server.py             # FastAPI streaming server
│   └── stream_client.py             # SSE client
├── tests/                 # Test scripts
│   ├── PROOF_QUEUE_WORKS.py         # ⭐ Proves SDK works
│   ├── FINAL_DIAGNOSIS.py           # ⭐ Shows your bug
│   ├── test_enqueue_methods.py      # Tests methods
│   └── simple_blocking_test.py      # Simple test
├── docs/                  # Documentation
│   ├── EVENT_QUEUE_GUIDE.md         # Complete guide
│   ├── WHY_QUEUE_BLOCKS.md          # Troubleshooting
│   └── YOUR_BUG_EXPLAINED.md        # Bug fixes
├── requirements.txt       # Dependencies
├── Makefile              # Commands
└── README.md             # Main documentation
```

---

## 🎯 Most Important Files

### For Testing:
1. `tests/PROOF_QUEUE_WORKS.py` - **START HERE!**
2. `tests/FINAL_DIAGNOSIS.py` - **Shows your bug**

### For Learning:
1. `README.md` - **Complete reference**
2. `examples/executor_with_taskupdater.py` - **Working example**

### For Troubleshooting:
1. `docs/YOUR_BUG_EXPLAINED.md` - **Bug fixes**
2. `docs/WHY_QUEUE_BLOCKS.md` - **Queue issues**

---

## 💡 Quick Answers

### Q: Does `enqueue_event()` work?
**A:** YES! Run `make test-proof` to see proof.

### Q: Why is my queue blocking?
**A:** Your `update_status()` is missing `TaskState`. Run `make test-diag` to see the fix.

### Q: Which method should I use?
**A:** Use `event_queue.enqueue_event(message)`. Run `make test-methods` to verify.

### Q: How do I fix my code?
**A:** Read `docs/YOUR_BUG_EXPLAINED.md` or run `make test-diag`.

---

## 🆘 Still Stuck?

1. **Read:** `docs/YOUR_BUG_EXPLAINED.md`
2. **Run:** `make test-diag`
3. **Check:** The debug code in the documentation

---

**Happy Testing! 🚀**
