"""
Long-term memory system for voice agents.
Inspired by memU architecture - provides persistent, cross-call memory.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Float, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base
import uuid


class MemoryItem(Base):
    """Individual memory fact extracted from conversations."""
    __tablename__ = "memory_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=True)  # Caller ID or user ID
    agent_id = Column(String, index=True, nullable=True)  # Which agent created this
    organization_id = Column(String, index=True, nullable=True)
    
    # Memory content
    category = Column(String, index=True)  # e.g., "preferences", "personal_info", "history"
    memory_type = Column(String, default="user_claim") # user_claim, system_verified, regulated_fact
    key = Column(String, index=True)  # e.g., "name", "preferred_language", "last_order"
    value = Column(Text)  # The actual memory content
    
    # Context
    source_session_id = Column(String, nullable=True)  # Which session this came from
    confidence = Column(Float, default=1.0)  # How confident we are in this memory
    
    # Governance
    expires_at = Column(DateTime, nullable=True) # TTL for memory
    is_sensitive = Column(Boolean, default=False) # Whether memory contains sensitive data
    
    # Vector embedding for semantic search
    embedding = Column(Vector(384))  # Using sentence-transformers all-MiniLM-L6-v2
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Float, default=1)  # For relevance decay
    
    # Indexes for efficient lookup
    __table_args__ = (
        Index('idx_memory_user_category', 'user_id', 'category'),
        Index('idx_memory_user_key', 'user_id', 'key'),
    )


class ConversationSummary(Base):
    """Summarized conversation for long-term storage."""
    __tablename__ = "conversation_summaries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    organization_id = Column(String, index=True, nullable=True)
    
    # Summary content
    summary = Column(Text)  # LLM-generated summary
    key_points = Column(JSON, default=list)  # Extracted key points
    action_items = Column(JSON, default=list)  # Any follow-up items
    sentiment = Column(String, nullable=True)  # Overall sentiment
    
    # Metadata
    turn_count = Column(Float, default=0)
    duration_seconds = Column(Float, nullable=True)
    outcome = Column(String, nullable=True)  # resolved, escalated, abandoned
    
    # Vector for semantic search across conversations
    embedding = Column(Vector(384))
    
    created_at = Column(DateTime, default=datetime.utcnow)


class UserProfile(Base):
    """Aggregated user profile from all interactions."""
    __tablename__ = "user_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, index=True)  # Phone number or user ID
    organization_id = Column(String, index=True, nullable=True)
    
    # Basic info (populated over time)
    name = Column(String, nullable=True)
    preferred_language = Column(String, default="en-US")
    timezone = Column(String, nullable=True)
    
    # Interaction stats
    total_calls = Column(Float, default=0)
    total_messages = Column(Float, default=0)
    avg_sentiment = Column(Float, nullable=True)
    last_interaction = Column(DateTime, nullable=True)
    
    # Preferences learned over time
    preferences = Column(JSON, default=dict)  # {"communication_style": "formal", ...}
    
    # Flags
    is_vip = Column(Float, default=False)
    # Governance
    consent_status = Column(String, default="unknown") # unknown, granted, withdrawn
    requires_escalation = Column(Float, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
