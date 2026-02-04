from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class AgentBase(BaseModel):
    name: str
    role: str
    persona: str
    language: str = "en-US"
    tools: List[Any] = []
    goals: List[Any] = []
    is_active: bool = True

class AgentCreate(AgentBase):
    pass

class AgentUpdate(AgentBase):
    pass

class Agent(AgentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
