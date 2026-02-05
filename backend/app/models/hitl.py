"""
Human-in-the-Loop models for manual approval workflows.
"""
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Enum, Boolean
from datetime import datetime
from app.core.database import Base
import uuid
import enum

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class InterventionMode(str, enum.Enum):
    AI_ONLY = "ai_only"         # Default AI control
    WHISPER = "whisper"         # Human suggests, AI speaks (human provides text/prompt)
    HUMAN_TAKEOVER = "takeover" # Human speaks directly (AI disabled)
    MONITORING = "monitoring"   # Human just watching

class PendingAction(Base):
    """Actions initiated by AI that require human approval."""
    __tablename__ = "pending_actions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    organization_id = Column(String, index=True, nullable=True)
    
    action_type = Column(String) # e.g., "refund", "database_update", "high_value_transaction"
    description = Column(String)
    payload = Column(JSON) # The data to be executed upon approval
    
    status = Column(String, default=ApprovalStatus.PENDING.value)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(String, ForeignKey("users.id"), nullable=True)
    feedback = Column(String, nullable=True) # Reason for rejection or notes

class SessionIntervention(Base):
    """Tracks active human interventions in a call session."""
    __tablename__ = "session_interventions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id")) # The human agent
    organization_id = Column(String, index=True, nullable=True)
    
    mode = Column(String, default=InterventionMode.AI_ONLY.value)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
