# 🌊 A2A Stream Server Commands

## 🚀 Start the Server

```bash
make run-orchestrator-server
```

Or directly:
```bash
venv/bin/python3 examples/orchestrator_stream_server.py
```

Server will start on: **http://localhost:8000**

---

## 🔥 Query the A2A Stream Endpoint

### Basic curl command:
```bash
curl -N http://localhost:8000/a2a/stream?query=test
```

### With custom query:
```bash
curl -N http://localhost:8000/a2a/stream?query="investigate service errors"
```

### POST request (A2A standard):
```bash
curl -X POST -N http://localhost:8000/a2a/stream?query=test
```

### Pretty-printed output:
```bash
curl -N http://localhost:8000/a2a/stream?query=test 2>/dev/null | while IFS= read -r line; do echo "$line"; done
```

---

## 📊 Expected Output

You'll see Server-Sent Events (SSE) streaming in real-time:

```
event: statusUpdate
data: {"state": "TaskState.working", "hasMessage": true}

event: agent_parts
data: {"messageId": "...", "role": "Role.agent", "parts": [{"type": "DataPart", "data": {"step": "research"}}, {"type": "TextPart", "text": "Processing: research"}]}

event: agent_parts
data: {"messageId": "...", "role": "Role.agent", "parts": [{"type": "DataPart", "data": {"step": "analysis"}}, {"type": "TextPart", "text": "Processing: analysis"}]}

event: agent_parts
data: {"messageId": "...", "role": "Role.agent", "parts": [{"type": "DataPart", "data": {"step": "summary"}}, {"type": "TextPart", "text": "Processing: summary"}]}

event: statusUpdate
data: {"state": "TaskState.completed", "hasMessage": true}
```

---

## 🛑 Stop the Server

Press `Ctrl+C` in the terminal running the server

Or if running in background:
```bash
lsof -ti:8000 | xargs kill -9
```

---

## 🧪 Advanced Testing

### With httpie (more readable):
```bash
http --stream GET http://localhost:8000/a2a/stream query==test
```

### Save stream to file:
```bash
curl -N http://localhost:8000/a2a/stream?query=test > stream_output.txt
```

### Test from JavaScript:
```javascript
const eventSource = new EventSource('http://localhost:8000/a2a/stream?query=test');

eventSource.addEventListener('statusUpdate', (e) => {
  console.log('Status:', JSON.parse(e.data));
});

eventSource.addEventListener('agent_parts', (e) => {
  console.log('Message:', JSON.parse(e.data));
});
```

### Test from Python:
```python
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream('GET', 'http://localhost:8000/a2a/stream?query=test') as response:
        async for line in response.aiter_lines():
            if line.startswith('data:'):
                print(line)
```

---

## 📁 Files

- **Server:** `examples/orchestrator_stream_server.py`
- **Makefile:** Contains `run-orchestrator-server` command
- **Requirements:** `sse-starlette` added for SSE support

---

## 🔑 Key Features

✅ **OrchestratorAgentExecutor** - Full execute() method
✅ **SSE Streaming** - Real-time events via Server-Sent Events
✅ **statusUpdate events** - Task state changes
✅ **agent_parts events** - Streaming messages with DataPart and TextPart
✅ **Works with curl** - No special client needed

---

## 💡 Troubleshooting

### Port already in use:
```bash
lsof -ti:8000 | xargs kill -9
make run-orchestrator-server
```

### Missing dependencies:
```bash
venv/bin/pip install -r requirements.txt
```

### Can't connect:
- Check server is running: `lsof -i:8000`
- Verify URL: `curl http://localhost:8000/`
- Check firewall settings

---

**Ready to stream! 🚀**
