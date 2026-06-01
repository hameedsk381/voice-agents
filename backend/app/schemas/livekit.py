from typing import Any, Dict, Optional

from pydantic import BaseModel


class LiveKitTokenRequest(BaseModel):
    room_name: Optional[str] = None
    participant_identity: Optional[str] = None
    participant_name: Optional[str] = None
    participant_metadata: Optional[str] = None
    participant_attributes: Optional[Dict[str, str]] = None
    room_config: Optional[Dict[str, Any]] = None
    language: Optional[str] = None
    voice: Optional[str] = None
    caller_id: Optional[str] = None


class LiveKitTokenResponse(BaseModel):
    server_url: str
    participant_token: str
    room_name: str
    agent_name: str
