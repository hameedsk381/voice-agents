from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class PolicyRuleCreate(BaseModel):
    name: str
    description: str = ""
    tool_name: str = "*"
    conditions: Dict[str, Any] = {}
    action: str = "escalate"  # permit | deny | escalate
    priority: int = 100
    enabled: bool = True

class PolicyRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tool_name: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    action: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None

class PolicyRuleResponse(BaseModel):
    id: str
    organization_id: Optional[str] = None
    name: str
    description: str
    tool_name: str
    conditions: Dict[str, Any]
    action: str
    priority: int
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PolicyEvaluationResult(BaseModel):
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    action: str  # permit | deny | escalate
    reason: str = ""
    tool_name: str
    arguments: Dict[str, Any]
