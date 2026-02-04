"""
Temporal workflow definitions for durable call orchestration.
"""
from datetime import timedelta
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import asyncio


@dataclass
class CallInput:
    """Input for a call workflow."""
    session_id: str
    agent_id: str
    caller_id: Optional[str]
    call_type: str  # "inbound" or "outbound"


@dataclass 
class CallResult:
    """Result of a call workflow."""
    session_id: str
    status: str  # "completed", "escalated", "failed", "abandoned"
    duration_seconds: int
    turn_count: int
    escalated: bool
    escalation_reason: Optional[str]
    transcript_summary: Optional[str]


@activity.defn
async def initialize_session(session_id: str, agent_id: str, caller_id: str) -> Dict[str, Any]:
    """Activity: Initialize a new session in Redis."""
    from app.orchestration.session_manager import session_manager
    
    session = await session_manager.create_session(
        session_id=session_id,
        agent_id=agent_id,
        caller_id=caller_id
    )
    return session


@activity.defn
async def process_user_input(session_id: str, audio_data: bytes) -> str:
    """Activity: Transcribe user audio."""
    # This would call the STT service
    # For now, return placeholder
    return "User input transcribed"


@activity.defn
async def generate_response(session_id: str, user_input: str, agent_id: str) -> Dict[str, Any]:
    """Activity: Generate AI response."""
    # This would call the LLM
    return {
        "text": "AI response",
        "tool_calls": [],
        "should_escalate": False
    }


@activity.defn
async def synthesize_audio(text: str) -> bytes:
    """Activity: Convert text to speech."""
    # This would call TTS
    return b"audio_bytes"


@activity.defn
async def execute_tool_activity(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Activity: Execute a tool."""
    from app.services.tools.registry import AVAILABLE_TOOLS
    
    if tool_name in AVAILABLE_TOOLS:
        tool = AVAILABLE_TOOLS[tool_name]
        result = await tool.execute(**arguments)
        return result
    return f"Tool {tool_name} not found"


@activity.defn
async def transfer_to_human(session_id: str, reason: str) -> bool:
    """Activity: Transfer call to human agent."""
    from app.orchestration.session_manager import session_manager
    
    await session_manager.escalate_session(session_id, reason, "human_agent")
    # In real implementation, this would trigger SIP transfer or queue
    return True


@activity.defn
async def end_session_activity(session_id: str, reason: str) -> bool:
    """Activity: End the session."""
    from app.orchestration.session_manager import session_manager
    
    await session_manager.end_session(session_id, reason)
    return True


@workflow.defn
class CallWorkflow:
    """
    Temporal workflow for managing a complete call lifecycle.
    This provides durability - if the process crashes, Temporal will resume.
    """
    
    def __init__(self):
        self.session_id: Optional[str] = None
        self.is_active: bool = True
        self.turn_count: int = 0
        self.max_turns: int = 100
        self.pending_input: Optional[str] = None
    
    @workflow.run
    async def run(self, input: CallInput) -> CallResult:
        """Main workflow execution."""
        self.session_id = input.session_id
        
        # Initialize session
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3
        )
        
        await workflow.execute_activity(
            initialize_session,
            args=[input.session_id, input.agent_id, input.caller_id],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy
        )
        
        escalated = False
        escalation_reason = None
        
        # Main conversation loop
        while self.is_active and self.turn_count < self.max_turns:
            # Wait for user input signal
            await workflow.wait_condition(lambda: self.pending_input is not None or not self.is_active)
            
            if not self.is_active:
                break
            
            user_input = self.pending_input
            self.pending_input = None
            self.turn_count += 1
            
            # Generate response
            response = await workflow.execute_activity(
                generate_response,
                args=[input.session_id, user_input, input.agent_id],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy
            )
            
            # Handle tool calls
            if response.get("tool_calls"):
                for tc in response["tool_calls"]:
                    await workflow.execute_activity(
                        execute_tool_activity,
                        args=[tc["name"], tc["arguments"]],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
            
            # Check for escalation
            if response.get("should_escalate"):
                escalated = True
                escalation_reason = response.get("escalation_reason", "Unknown")
                await workflow.execute_activity(
                    transfer_to_human,
                    args=[input.session_id, escalation_reason],
                    start_to_close_timeout=timedelta(seconds=30),
                )
                break
        
        # End session
        await workflow.execute_activity(
            end_session_activity,
            args=[input.session_id, "completed" if not escalated else "escalated"],
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        return CallResult(
            session_id=input.session_id,
            status="escalated" if escalated else "completed",
            duration_seconds=0,  # Would calculate from timestamps
            turn_count=self.turn_count,
            escalated=escalated,
            escalation_reason=escalation_reason,
            transcript_summary=None
        )
    
    @workflow.signal
    async def receive_user_input(self, text: str):
        """Signal: Receive user input from external source."""
        self.pending_input = text
    
    @workflow.signal
    async def end_call(self):
        """Signal: End the call explicitly."""
        self.is_active = False
    
    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """Query: Get current workflow status."""
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "turn_count": self.turn_count
        }
