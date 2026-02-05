from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class KnowledgeBase(BaseModel):
    title: str
    content: str
    data_metadata: Optional[Dict[str, Any]] = {}
    is_active: bool = True

class KnowledgeCreate(KnowledgeBase):
    pass

class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    data_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class Knowledge(KnowledgeBase):
    id: str
    agent_id: str
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KnowledgeQueryResult(BaseModel):
    content: str
    title: str
    score: float
    data_metadata: Dict[str, Any]
