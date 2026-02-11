"""
Test using REAL A2A SDK imports with STREAMING pattern

Shows ONLY the streamed objects:
- statusUpdate
- agent_parts Messages  
- artifactUpdate

HOW TO RUN:
    venv/bin/python3 tests/test_enqueue_methods.py
"""

import asyncio
import json
from typing import Dict, Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart, DataPart, TaskState


class SimpleGraph:
    """Simulates OrchestratorGraph"""
    
    def __init__(self, request: Dict[str, Any]):
        self.request = request
        self.state = {"query": request.get("query", "test")}
        self.graph = self
    
    def compile_graph(self):
        """Compile the graph"""
        return self
    
    async def generate_streaming_response(self, inputs: Dict):
        """Streaming response"""
        yield b'{"step": "research"}\n'
        await asyncio.sleep(0.05)
        yield b'{"step": "analysis"}\n'
        await asyncio.sleep(0.05)
        yield b'{"step": "summary"}\n'
    
    async def run(self):
        return {"status": "complete", "findings": ["f1", "f2"]}


class OrchestratorAgentExecutor(AgentExecutor):
    """
    Your OrchestratorAgentExecutor pattern with execute method
    """
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Execute method matching YOUR orchestrator pattern
        """
        
        message = getattr(context, "message", None)
        query = ""
        
        if message and getattr(message, "content", None):
            try:
                query = message.content[0].text
            except Exception:
                query = ""
        
        # Metadata extraction
        raw_metadata = getattr(message, "metadata", None) if message else None
        metadata: Dict[str, Any] = {}
        
        if raw_metadata is not None:
            try:
                from google.protobuf.json_format import MessageToDict
                metadata = MessageToDict(raw_metadata)
            except Exception:
                try:
                    metadata = dict(raw_metadata)  # type: ignore
                except Exception:
                    metadata = {}
        
        # Task Handling
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
            
            # Emit start event
            start_event = self._create_start_event(task.id)
            
            # ✅ CORRECT PATTERN (fixed from your code):
            start_message = updater.new_agent_message([
                Part(
                    root=DataPart(
                        mime_type="application/json",
                        data=start_event,
                    )
                ),
                Part(
                    root=TextPart(text="Investigation started")
                ),
            ])
            
            await updater.update_status(
                TaskState.working,  # ← Fixed: Added TaskState
                message=start_message
            )
            
            # Stream graph responses
            async for _lines_bytes in graph.graph.generate_streaming_response(inputs=graph.state):
                data = json.loads(_lines_bytes.decode('utf-8'))
                
                # Create custom message for streaming
                custom_message = updater.new_agent_message([
                    Part(root=DataPart(mime_type="application/json", data=data)),
                    Part(root=TextPart(text=f"Processing: {data['step']}"))
                ])
                
                await event_queue.enqueue_event(custom_message)
            
            # Run graph to get final report
            final_report = await graph.run()
            
            # ✅ CORRECT: Complete with message
            final_message = updater.new_agent_message([
                Part(root=TextPart(text="Investigation complete")),
                Part(
                    root=DataPart(
                        mime_type="application/json",
                        data=final_report,
                    )
                ),
            ])
            
            await updater.complete(message=final_message)
            
        except Exception as e:
            error_message = updater.new_agent_message([
                Part(root=TextPart(text=f"Execution failed: {str(e)}"))
            ])
            await updater.complete(message=error_message)
            raise
    
    def _build_request(self, query_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build request from query and metadata"""
        return {
            "query": query_text,
            "metadata": metadata,
            "application": metadata.get("application", "test-app"),
            "requested_by": metadata.get("requested_by", "test-user"),
        }
    
    def _create_start_event(self, task_id: str) -> Dict[str, Any]:
        """Create start event"""
        return {
            "event_type": "orchestrator_start",
            "task_id": task_id,
            "status": "started",
        }
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel implementation (required by AgentExecutor)"""
        pass


async def consume_queue(event_queue: EventQueue, show_raw_stream: bool = False):
    """Consume and display events from queue"""
    events_shown = 0
    max_events = 10  # Safety limit
    raw_stream = []
    
    while events_shown < max_events:
        try:
            event = await asyncio.wait_for(event_queue.dequeue_event(), timeout=0.2)
            event_type = type(event).__name__
            
            # Build raw SSE stream representation
            if show_raw_stream:
                event_name = "unknown"
                event_data = {}
                
                # Determine event type for SSE
                if 'Status' in event_type:
                    event_name = "statusUpdate"
                    event_data = {
                        "state": str(event.status.state),
                        "hasMessage": hasattr(event.status, 'message') and event.status.message is not None
                    }
                    if event.status.message:
                        event_data["messageParts"] = len(event.status.message.parts)
                
                elif 'Message' in event_type:
                    event_name = "agent_parts"
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
                
                elif 'Artifact' in event_type:
                    event_name = "artifactUpdate"
                    event_data = {"artifactParts": len(event.artifact.parts) if hasattr(event, 'artifact') else 0}
                
                # Format as SSE
                raw_stream.append(f"event: {event_name}")
                raw_stream.append(f"data: {json.dumps(event_data)}")
                raw_stream.append("")
            
            # StatusUpdate
            if 'Status' in event_type:
                print(f"\n📤 statusUpdate:")
                print(f"   State: {event.status.state}")
                if hasattr(event.status, 'message') and event.status.message:
                    print(f"   Has message: Yes ({len(event.status.message.parts)} parts)")
            
            # Message (agent_parts)
            elif 'Message' in event_type:
                print(f"\n📨 agent_parts Message:")
                print(f"   ID: {event.message_id}")
                print(f"   Role: {event.role}")
                print(f"   Parts: {len(event.parts)}")
                for i, part in enumerate(event.parts):
                    if hasattr(part, 'root'):
                        root = part.root
                        if isinstance(root, DataPart):
                            print(f"      [{i}] DataPart: {root.data}")
                        elif isinstance(root, TextPart):
                            print(f"      [{i}] TextPart: {root.text}")
            
            # Artifact
            elif 'Artifact' in event_type:
                print(f"\n📦 artifactUpdate:")
                if hasattr(event, 'artifact'):
                    print(f"   Artifact parts: {len(event.artifact.parts)}")
            
            events_shown += 1
            
        except asyncio.TimeoutError:
            break
    
    return events_shown, raw_stream


async def test_streaming():
    """Test orchestrator pattern with streaming using execute method"""
    
    print("=" * 70)
    print("🎯 ORCHESTRATOR EXECUTE METHOD WITH STREAMING")
    print("=" * 70)
    
    # Setup
    event_queue = EventQueue()
    
    # Create mock context
    class MockMessage:
        content = [type('obj', (object,), {'text': 'test query'})]
        metadata = {"application": "test-app", "requested_by": "test-user"}
    
    class MockTask:
        id = "task-123"
        context_id = "ctx-456"
    
    class MockContext:
        message = MockMessage()
        current_task = MockTask()
    
    context = MockContext()
    
    # Start consumer task with raw stream capture
    consumer_task = asyncio.create_task(consume_queue(event_queue, show_raw_stream=True))
    
    try:
        # Create executor and run execute method
        executor = OrchestratorAgentExecutor()
        
        await executor.execute(context, event_queue)
        
        await asyncio.sleep(0.2)  # Let consumer finish
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Wait for consumer
    events_count, raw_stream = await consumer_task
    
    print("\n" + "=" * 70)
    print(f"✅ Streamed {events_count} events via execute()")
    print("=" * 70)
    
    # Show raw stream
    print("\n" + "=" * 70)
    print("🌊 RAW A2A STREAM ENDPOINT OUTPUT (SSE Format)")
    print("=" * 70)
    print("\nWhat you would receive from: GET /stream?query=test\n")
    for line in raw_stream:
        print(line)
    print("\n" + "=" * 70)


async def show_pattern():
    """Show the correct code pattern"""
    print("\n" + "=" * 70)
    print("💡 YOUR EXECUTE METHOD - CORRECTED")
    print("=" * 70)
    print("""
class OrchestratorAgentExecutor(AgentExecutor):
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Get task and create updater
        task = context.current_task
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        
        try:
            # Build and compile graph
            request = self._build_request(query, metadata)
            graph = OrchestratorGraph(request=request)
            graph.graph = graph.compile_graph()
            
            # ✅ FIX #1: Create message, then update status with TaskState
            start_message = updater.new_agent_message([
                Part(root=DataPart(mime_type="application/json", data=start_event)),
                Part(root=TextPart(text="Investigation started"))
            ])
            await updater.update_status(TaskState.working, message=start_message)
            
            # ✅ FIX #2: Stream with custom messages
            async for _lines_bytes in graph.graph.generate_streaming_response(inputs=graph.state):
                data = json.loads(_lines_bytes.decode('utf-8'))
                custom_msg = updater.new_agent_message([
                    Part(root=DataPart(mime_type="application/json", data=data)),
                    Part(root=TextPart(text=f"Step: {data['step']}"))
                ])
                await event_queue.enqueue_event(custom_msg)
            
            # Get final report
            final_report = await graph.run()
            
            # ✅ FIX #3: Create message, then complete
            final_message = updater.new_agent_message([
                Part(root=TextPart(text="Investigation complete")),
                Part(root=DataPart(mime_type="application/json", data=final_report))
            ])
            await updater.complete(message=final_message)
            
        except Exception as e:
            error_msg = updater.new_agent_message([
                Part(root=TextPart(text=f"Execution failed: {str(e)}"))
            ])
            await updater.complete(message=error_msg)
            raise
""")
    print("=" * 70)
    print("\n🔑 KEY FIXES:")
    print("  1. update_status(TaskState.working, message=...)  ← TaskState first")
    print("  2. complete(message=...)  ← Pass message parameter")
    print("  3. Use new_agent_message() to create all messages")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_streaming())
    asyncio.run(show_pattern())
