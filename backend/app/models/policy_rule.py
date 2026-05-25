from sqlalchemy import Column, String, JSON, DateTime, Boolean, Integer, ForeignKey
from datetime import datetime
from app.core.database import Base
import uuid
import enum

class PolicyAction(str, enum.Enum):
    PERMIT = "permit"
    DENY = "deny"
    ESCALATE = "escalate"

class PolicyRule(Base):
    """Pre-execution policy rule — evaluated before every tool call.
    DENY > ESCALATE > PERMIT precedence.
    """
    __tablename__ = "policy_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, index=True, nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")

    tool_name = Column(String, nullable=False, index=True)  # "*" for all tools, or specific tool name
    conditions = Column(JSON, default=dict)  # e.g. {"amount": {"gt": 500}}
    action = Column(String, nullable=False, default=PolicyAction.ESCALATE.value)  # permit | deny | escalate
    priority = Column(Integer, default=100)  # higher = evaluated first
    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
