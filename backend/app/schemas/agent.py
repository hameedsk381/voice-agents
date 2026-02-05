from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class AgentBase(BaseModel):
    name: str
    role: str
    persona: str
    description: Optional[str] = None
    language: str = "en-US"
    tools: Optional[List[Any]] = []
    goals: Optional[List[Any]] = []
    success_criteria: Optional[List[Any]] = []
    failure_conditions: Optional[List[Any]] = []
    exit_actions: Optional[List[Any]] = []
    is_active: bool = True
    active_version_id: Optional[str] = None
    token_limit: Optional[int] = 50000
    fallback_model: Optional[str] = "llama-3.1-8b-instant"
    organization_id: Optional[str] = None
    config: Optional[Any] = {}

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    persona: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    tools: Optional[List[Any]] = None
    goals: Optional[List[Any]] = None
    success_criteria: Optional[List[Any]] = None
    failure_conditions: Optional[List[Any]] = None
    exit_actions: Optional[List[Any]] = None
    is_active: Optional[bool] = None
    active_version_id: Optional[str] = None
    token_limit: Optional[int] = None
    fallback_model: Optional[str] = None
    organization_id: Optional[str] = None
    config: Optional[Any] = None

class Agent(AgentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AgentVersionBase(BaseModel):
    version_number: int
    persona: str
    description: Optional[str] = None
    tools: List[Any] = []
    policy: Optional[Any] = None
    success_criteria: Optional[List[Any]] = None
    failure_conditions: Optional[List[Any]] = None
    exit_actions: Optional[List[Any]] = None
    change_log: Optional[str] = None
    token_limit: Optional[int] = None
    fallback_model: Optional[str] = None
    organization_id: Optional[str] = None

class AgentVersionCreate(AgentVersionBase):
    pass

class AgentVersion(AgentVersionBase):
    id: str
    agent_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
