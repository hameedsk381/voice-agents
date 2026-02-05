from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ComplianceSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class ComplianceRule(BaseModel):
    id: str
    name: str
    description: str
    severity: ComplianceSeverity = ComplianceSeverity.WARNING
    rule_type: str # "regex", "llm_check", "mandatory_phrase"
    config: Dict[str, Any] = {}

class ComplianceViolation(BaseModel):
    rule_id: str
    rule_name: str
    severity: ComplianceSeverity
    reason: str
    turn_index: int
    matched_text: Optional[str] = None

class ComplianceCheckResult(BaseModel):
    session_id: str
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    violations: List[ComplianceViolation] = []
    is_compliant: bool = True
    risk_score: float = 0.0 # 0.0 (safe) to 1.0 (dangerous)
