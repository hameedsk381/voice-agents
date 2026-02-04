"""
Campaign models for outbound calling.
"""
from sqlalchemy import Column, String, JSON, Integer, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import uuid
import enum

class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ContactStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class Campaign(Base):
    """Outbound call campaign configuration."""
    __tablename__ = "campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)
    
    # Configuration
    agent_id = Column(String, ForeignKey("agents.id"))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=True)
    
    status = Column(String, default=CampaignStatus.DRAFT.value)
    
    # Scheduling & Rate Limiting
    start_time = Column(DateTime, nullable=True)
    concurrency_limit = Column(Integer, default=1)  # Max parallel calls
    retry_config = Column(JSON, default=lambda: {"max_retries": 3, "retry_delay_minutes": 60})
    
    # Stats
    total_contacts = Column(Integer, default=0)
    completed_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CampaignContact(Base):
    """Individual contact for a campaign."""
    __tablename__ = "campaign_contacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    
    # Contact Info
    phone_number = Column(String, nullable=False)
    contact_name = Column(String)
    
    # Custom Data (used as context for the agent)
    custom_data = Column(JSON, default=dict)
    
    # Execution State
    status = Column(String, default=ContactStatus.PENDING.value)
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    session_id = Column(String, nullable=True)  # Links to the conversation
    
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
