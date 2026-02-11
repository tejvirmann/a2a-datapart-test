"""
A2A Streaming Server with Agent Executor
FastAPI server that streams events from the executor
"""

import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# ✅ A2A IMPORTS - Using proper imports
from a2a_utils import EventQueue, TaskUpdater, TaskState, new_agent_parts_message
from agent_executor import AgentExecutor


# ✅ All A2A components imported from a2a_utils.py and agent_executor.py
# No duplicate definitions needed!


# ============================================================================
# FASTAPI SERVER
# ============================================================================

app = FastAPI(title="A2A Stream Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def event_generator(query: str, task_id: str, context_id: str):
    """Generate SSE events from the executor"""
    
    # Create shared event queue
    event_queue = EventQueue()
    
    # Create executor
    executor = AgentExecutor(event_queue, task_id, context_id)
    
    # Start execution in background
    execution_task = asyncio.create_task(executor.execute(query))
    
    # Stream events as they come
    while True:
        event = await event_queue.get()
        
        # End signal
        if event is None:
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            break
        
        # Send event as SSE
        yield f"data: {json.dumps(event)}\n\n"
    
    # Wait for execution to complete
    await execution_task


@app.get("/")
async def root():
    return {
        "message": "A2A Stream Server",
        "endpoints": {
            "stream": "/stream?query=YOUR_QUERY"
        }
    }


@app.get("/stream")
async def stream_endpoint(query: str = "Analyze the latest market trends"):
    """
    Streaming endpoint that returns SSE events
    
    Example: http://localhost:8000/stream?query=Hello
    """
    
    import uuid
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    context_id = f"ctx_{uuid.uuid4().hex[:8]}"
    
    return StreamingResponse(
        event_generator(query, task_id, context_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting A2A Stream Server...")
    print("📡 Server: http://localhost:8000")
    print("🔗 Stream: http://localhost:8000/stream")
    uvicorn.run(app, host="0.0.0.0", port=8000)
