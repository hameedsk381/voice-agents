"""
Call Log model for detailed observability and analytics.
"""
from sqlalchemy import Column, String, JSON, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import uuid

class CallLog(Base):
    """Stores detailed metrics for every completed call."""
    __tablename__ = "call_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True, unique=True)
    
    # Context
    agent_id = Column(String, ForeignKey("agents.id"))
    caller_id = Column(String, nullable=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)
    
    # Timing Metrics (ms)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    
    # Performance Metrics
    avg_latency_ms = Column(Float, default=0.0)
    ttfap_ms = Column(Float, default=0.0) # Time to First Audio Packet
    total_turns = Column(Integer, default=0)
    
    # Usage & Cost
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    
    # Outcome
    status = Column(String) # completed, failed, escalated
    end_reason = Column(String) # hung up, completed, error
    
    # Data
    transcript = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
