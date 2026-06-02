from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class StageDefinition(BaseModel):
    """A named conversation stage that can be switched to mid-call via a stage-change tool."""
    name: str
    system_prompt: Optional[str] = None
    voice: Optional[str] = None
    temperature: Optional[float] = None
    language_hint: Optional[str] = None
    tools: Optional[List[str]] = None


class InactivityMessage(BaseModel):
    text: str
    duration_seconds: int
    end_behaviour: str = "END_BEHAVIOR_UNSPECIFIED"


class DeferredMessage(BaseModel):
    message: str
    delay: str = "5m"
    medium: str = "sms"


class LiveKitJoinRequest(BaseModel):
    language: Optional[str] = None
    voice: Optional[str] = None
    caller_id: Optional[str] = None
    capability: Optional[str] = None
    temperature: Optional[float] = None
    max_duration: Optional[str] = None
    recording_enabled: Optional[bool] = None
    join_timeout: Optional[str] = None
    initial_messages: Optional[List[Dict[str, str]]] = None
    initial_state: Optional[Dict[str, Any]] = None
    deferred_messages: Optional[List[Dict[str, Any]]] = None
    prior_call_id: Optional[str] = None


class LiveKitJoinResponse(BaseModel):
    room_name: str
    participant_token: str
    call_id: str
    session_id: str
    agent_id: str
    agent_name: str
    voice: str
    language: str
    tool_names: List[str] = []


class ChatRequest(BaseModel):
    agent_id: str
    text: str
    session_id: Optional[str] = None
    caller_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    session_id: str
    text: str
    agent_id: str
    done: bool = True
    metadata: Optional[Dict[str, Any]] = {}
