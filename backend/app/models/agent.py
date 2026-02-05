from sqlalchemy import Column, String, JSON, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.core.database import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    role = Column(String)  # e.g. "support", "sales"
    description = Column(String, nullable=True)
    persona = Column(String) # The system prompt description
    organization_id = Column(String, index=True, nullable=True) # Multitenancy
    
    # Configuration
    language = Column(String, default="en-US")
    tools = Column(JSON, default=list) # List of enabled tool names/configs
    goals = Column(JSON, default=list) # List of goals
    success_criteria = Column(JSON, default=list) # e.g. ["payment_confirmed"]
    failure_conditions = Column(JSON, default=list) # e.g. ["user_angry"]
    exit_actions = Column(JSON, default=list) # e.g. ["escalate"]
    config = Column(JSON, default=dict) # Catch-all for miscellaneous settings
    
    # Cost Awareness
    token_limit = Column(Integer, default=50000) # Max tokens per call
    fallback_model = Column(String, default="llama-3.1-8b-instant") # Cheaper fallback
    
    
    # Status
    is_active = Column(Boolean, default=True)
    active_version_id = Column(String, nullable=True) # Pin to a specific version
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AgentVersion(Base):
    """Immutable snapshots of an agent's configuration."""
    __tablename__ = "agent_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), index=True)
    version_number = Column(Integer)
    
    persona = Column(String)
    tools = Column(JSON)
    policy = Column(JSON, nullable=True) # Linked conversation policy
    success_criteria = Column(JSON, nullable=True)
    failure_conditions = Column(JSON, nullable=True)
    exit_actions = Column(JSON, nullable=True)
    
    token_limit = Column(Integer, nullable=True)
    fallback_model = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True) # User ID who created this version
    change_log = Column(String, nullable=True)
    
    # A/B Testing & Rollout
    weight = Column(Integer, default=0) # 0-100 percentage for routing
    is_canary = Column(Boolean, default=False)

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    description = Column(String, nullable=True)
    definition = Column(JSON) # The workflow graph/steps
    
    created_at = Column(DateTime, default=datetime.utcnow)
