from pydantic import BaseModel
from typing import Optional, List, Dict, Any

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
