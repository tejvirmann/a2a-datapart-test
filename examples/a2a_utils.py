"""
A2A Utilities
Core A2A components for streaming and task management
"""

import asyncio
from enum import Enum
from datetime import datetime
from typing import Optional


# ============================================================================
# TASK STATE
# ============================================================================

class TaskState(str, Enum):
    """Task state enum for lifecycle management"""
    PENDING = "pending"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# EVENT QUEUE
# ============================================================================

class EventQueue:
    """
    Event queue for all streaming events
    Single shared queue for messages, status updates, and artifacts
    """
    
    def __init__(self):
        self.queue = asyncio.Queue()
    
    async def enqueue(self, event: dict):
        """Enqueue any event"""
        await self.queue.put(event)
    
    async def get(self):
        """Get next event"""
        return await self.queue.get()
    
    def is_empty(self):
        """Check if queue is empty"""
        return self.queue.empty()


# ============================================================================
# TASK UPDATER
# ============================================================================

class TaskUpdater:
    """
    A2A TaskUpdater
    Manages task lifecycle and streaming updates
    """
    
    def __init__(self, event_queue: EventQueue, task_id: str, context_id: str):
        self.event_queue = event_queue
        self.task_id = task_id
        self.context_id = context_id
        self.current_state = TaskState.PENDING
    
    async def update_status(self, state: TaskState):
        """
        Update task status - NO PARTS, just state
        This is for task lifecycle only, NOT content
        
        Usage:
            await updater.update_status(TaskState.WORKING)
        """
        self.current_state = state
        status_event = {
            "type": "statusUpdate",
            "task_id": self.task_id,
            "context_id": self.context_id,
            "state": state.value,  # ❌ NO PARTS - just state!
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.event_queue.enqueue(status_event)
    
    async def add_artifact_update(
        self, 
        artifact_id: str, 
        content: str, 
        metadata: Optional[dict] = None
    ):
        """
        Add artifact update - HAS CONTENT
        
        Usage:
            await updater.add_artifact_update(
                artifact_id="summary",
                content="Final output",
                metadata={"type": "summary"}
            )
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
        
        await self.event_queue.enqueue(artifact_event)
    
    async def complete(self):
        """
        Complete task successfully
        Sends COMPLETED status and end signal
        """
        await self.update_status(TaskState.COMPLETED)
        await self.event_queue.enqueue(None)  # End signal
    
    async def fail(self, error_message: Optional[str] = None):
        """
        Mark task as failed
        Sends FAILED status and optional error message
        """
        await self.update_status(TaskState.FAILED)
        
        if error_message:
            error_msg = new_agent_parts_message(
                parts=[{"type": "text", "content": f"❌ Error: {error_message}"}],
                role="system"
            )
            error_msg["task_id"] = self.task_id
            error_msg["context_id"] = self.context_id
            await self.event_queue.enqueue(error_msg)
        
        await self.event_queue.enqueue(None)  # End signal


# ============================================================================
# MESSAGE UTILITIES
# ============================================================================

def new_agent_parts_message(parts: list, role: str = "assistant") -> dict:
    """
    Create agent parts message - HAS PARTS
    This is for user-facing content
    
    Args:
        parts: List of message parts with content
               Example: [{"type": "text", "content": "Hello"}]
        role: Message role ("assistant", "system", "user")
    
    Returns:
        Message dict with type "agent_parts" and parts field
    
    Usage:
        message = new_agent_parts_message(
            parts=[{"type": "text", "content": "Hello world"}],
            role="assistant"
        )
        message["task_id"] = task_id
        message["context_id"] = context_id
        await event_queue.enqueue(message)
    """
    return {
        "type": "agent_parts",
        "role": role,
        "parts": parts,  # ✅ HAS PARTS
        "timestamp": datetime.utcnow().isoformat()
    }
