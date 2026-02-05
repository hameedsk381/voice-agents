from sqlalchemy import Column, String, DateTime, JSON, Float, Text, ForeignKey, Index, Boolean
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from datetime import datetime
import uuid

class AgentKnowledge(Base):
    """
    Knowledge base chunks for AI agents.
    Provides RAG (Retrieval Augmented Generation) capabilities.
    """
    __tablename__ = "agent_knowledge"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), index=True)
    organization_id = Column(String, index=True, nullable=True)
    
    # Content
    title = Column(String, index=True) # Source document name
    content = Column(Text) # The chunk of text
    data_metadata = Column(JSON, default=dict) # Page numbers, source URL, etc.
    
    # Vector embedding for semantic search
    embedding = Column(Vector(384)) # Using sentence-transformers all-MiniLM-L6-v2 (same as memory)
    
    # Tracking
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index for fast vector similarity search
    # Note: pgvector specific index usually created via migration or raw SQL
