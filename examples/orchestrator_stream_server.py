"""
A2A Stream Server with OrchestratorAgentExecutor

Run with:
    venv/bin/python3 examples/orchestrator_stream_server.py

Or:
    make run-orchestrator-server
    
Then query with:
    curl -N http://localhost:8000/stream?query=test
"""

import asyncio
import json
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart, DataPart, TaskState

app = FastAPI(title="A2A Orchestrator Stream Server")


class SimpleGraph:
    """Simulates OrchestratorGraph"""
    
    def __init__(self, request: Dict[str, Any]):
        self.request = request
        self.state = {"query": request.get("query", "test")}
        self.graph = self
    
    def compile_graph(self):
        return self
    
    async def generate_streaming_response(self, inputs: Dict):
        """Streaming response"""
        yield b'{"step": "research", "status": "analyzing logs"}\n'
        await asyncio.sleep(0.1)
        yield b'{"step": "analysis", "status": "identifying patterns"}\n'
        await asyncio.sleep(0.1)
        yield b'{"step": "summary", "status": "generating report"}\n'
        await asyncio.sleep(0.1)
    
    async def run(self):
        return {
            "status": "complete",
            "findings": ["Issue found in service A", "Performance degradation detected"],
            "recommendations": ["Scale service", "Optimize queries"]
        }


class OrchestratorAgentExecutor(AgentExecutor):
    """OrchestratorAgentExecutor with streaming"""
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute with streaming pattern"""
        
        message = getattr(context, "message", None)
        query = ""
        
        if message and getattr(message, "content", None):
            try:
                query = message.content[0].text
            except Exception:
                query = ""
        
        # Metadata
        raw_metadata = getattr(message, "metadata", None) if message else None
        metadata: Dict[str, Any] = {}
        
        if raw_metadata is not None:
            try:
                from google.protobuf.json_format import MessageToDict
                metadata = MessageToDict(raw_metadata)
            except Exception:
                try:
                    metadata = dict(raw_metadata)
                except Exception:
                    metadata = {}
        
        # Task
        task = context.current_task
        if not task:
            from a2a.server.tasks import new_task
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        
        try:
            # Build request
            request = self._build_request(query, metadata)
            
            # Compile graph
            graph = SimpleGraph(request=request)
            graph.graph = graph.compile_graph()
            
            # Start event
            start_event = self._create_start_event(task.id)
            start_message = updater.new_agent_message([
                Part(root=DataPart(mime_type="application/json", data=start_event)),
                Part(root=TextPart(text="Investigation started"))
            ])
            
            await updater.update_status(TaskState.working, message=start_message)
            
            # Stream responses
            async for _lines_bytes in graph.graph.generate_streaming_response(inputs=graph.state):
                data = json.loads(_lines_bytes.decode('utf-8'))
                
                custom_message = updater.new_agent_message([
                    Part(root=DataPart(mime_type="application/json", data=data)),
                    Part(root=TextPart(text=f"Processssing: {data['step']}"))
                ])
                
                await event_queue.enqueue_event(custom_message)
            
            # Final report
            final_report = await graph.run()
            
            # Add artifact update before completing
            await updater.add_artifact(
                parts=[
                    Part(root=DataPart(mime_type="application/json", data=final_report))
                ],
                artifact_id=f"report-{task.id}",
                name="Investigation Report",
                last_chunk=True
            )
            
            final_message = updater.new_agent_message([
                Part(root=TextPart(text="Investigation complete")),
                Part(root=DataPart(mime_type="application/json", data=final_report))
            ])
            
            await updater.complete(message=final_message)
            
        except Exception as e:
            error_message = updater.new_agent_message([
                Part(root=TextPart(text=f"Execution failed: {str(e)}"))
            ])
            await updater.complete(message=error_message)
            raise
    
    def _build_request(self, query_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "query": query_text or "test",
            "metadata": metadata,
            "application": metadata.get("application", "test-app"),
        }
    
    def _create_start_event(self, task_id: str) -> Dict[str, Any]:
        return {
            "event_type": "orchestrator_start",
            "task_id": task_id,
            "status": "started",
        }
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


async def stream_generator(query: str):
    """Generate SSE stream from executor"""
    
    # Setup
    event_queue = EventQueue()
    
    # Mock context
    class MockMessage:
        content = [type('obj', (object,), {'text': query})]
        metadata = {"application": "test-app", "requested_by": "curl-user"}
    
    class MockTask:
        id = f"task-{query[:10]}"
        context_id = "ctx-stream"
    
    class MockContext:
        message = MockMessage()
        current_task = MockTask()
    
    context = MockContext()
    
    # Start executor in background
    executor = OrchestratorAgentExecutor()
    executor_task = asyncio.create_task(executor.execute(context, event_queue))
    
    try:
        # Stream events as SSE
        while True:
            try:
                event = await asyncio.wait_for(event_queue.dequeue_event(), timeout=0.5)
                event_type = type(event).__name__
                
                # Format as SSE
                if 'Status' in event_type:
                    event_data = {
                        "state": str(event.status.state),
                        "hasMessage": hasattr(event.status, 'message') and event.status.message is not None
                    }
                    yield {
                        "event": "statusUpdate",
                        "data": json.dumps(event_data)
                    }
                
                elif 'Message' in event_type:
                    parts_data = []
                    for part in event.parts:
                        if hasattr(part, 'root'):
                            root = part.root
                            if isinstance(root, DataPart):
                                parts_data.append({"type": "DataPart", "data": root.data})
                            elif isinstance(root, TextPart):
                                parts_data.append({"type": "TextPart", "text": root.text})
                    
                    event_data = {
                        "messageId": event.message_id,
                        "role": str(event.role),
                        "parts": parts_data
                    }
                    yield {
                        "event": "agent_parts",
                        "data": json.dumps(event_data)
                    }
                
                elif 'Artifact' in event_type:
                    # Handle artifact updates (TaskArtifactUpdateEvent)
                    artifact = event.artifact
                    artifact_data = {
                        "artifactId": artifact.artifact_id,
                        "name": artifact.name,
                        "lastChunk": getattr(event, 'last_chunk', True),
                    }
                    
                    # Extract parts data
                    parts_data = []
                    for part in artifact.parts:
                        if hasattr(part, 'root'):
                            root = part.root
                            if isinstance(root, DataPart):
                                parts_data.append({"type": "DataPart", "data": root.data})
                            elif isinstance(root, TextPart):
                                parts_data.append({"type": "TextPart", "text": root.text})
                    
                    artifact_data["parts"] = parts_data
                    
                    yield {
                        "event": "artifactUpdate",
                        "data": json.dumps(artifact_data)
                    }
                
                # Check if executor is done
                if executor_task.done():
                    break
                    
            except asyncio.TimeoutError:
                # Check if executor finished
                if executor_task.done():
                    break
                continue
    
    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }
    
    finally:
        # Ensure executor completes
        if not executor_task.done():
            executor_task.cancel()


@app.post("/a2a/stream")
async def a2a_stream_endpoint(query: str = "test"):
    """
    A2A Stream endpoint (POST)
    
    Usage:
        curl -X POST -N http://localhost:8000/a2a/stream?query=test
    """
    return EventSourceResponse(stream_generator(query))


@app.get("/a2a/stream")
async def a2a_stream_endpoint_get(query: str = "test"):
    """
    A2A Stream endpoint (GET for easy testing)
    
    Usage:
        curl -N http://localhost:8000/a2a/stream?query=test
    """
    return EventSourceResponse(stream_generator(query))


@app.get("/")
async def root():
    """Root endpoint with instructions"""
    return {
        "service": "A2A Orchestrator Stream Server",
        "version": "1.0.0",
        "protocol": "a2a",
        "endpoints": {
            "/a2a/stream?query=YOUR_QUERY": "Stream orchestrator results (A2A protocol)",
        },
        "example": "curl -N http://localhost:8000/a2a/stream?query=test"
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 Starting A2A Orchestrator Stream Server")
    print("=" * 70)
    print()
    print("Server: http://localhost:8000")
    print("A2A Stream Endpoint: http://localhost:8000/a2a/stream")
    print()
    print("Test with:")
    print("  curl -N http://localhost:8000/a2a/stream?query=test")
    print()
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
