"""
Human-in-the-Loop models for manual approval workflows.
"""
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Enum
from datetime import datetime
from app.core.database import Base
import uuid
import enum

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class PendingAction(Base):
    """Actions initiated by AI that require human approval."""
    __tablename__ = "pending_actions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    
    action_type = Column(String) # e.g., "refund", "database_update", "high_value_transaction"
    description = Column(String)
    payload = Column(JSON) # The data to be executed upon approval
    
    status = Column(String, default=ApprovalStatus.PENDING.value)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(String, ForeignKey("users.id"), nullable=True)
    feedback = Column(String, nullable=True) # Reason for rejection or notes
