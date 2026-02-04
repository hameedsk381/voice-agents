from sqlalchemy import Column, String, JSON, DateTime, Boolean
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
    
    # Configuration
    language = Column(String, default="en-US")
    tools = Column(JSON, default=list) # List of enabled tool names/configs
    goals = Column(JSON, default=list) # List of goals
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    description = Column(String, nullable=True)
    definition = Column(JSON) # The workflow graph/steps
    
    created_at = Column(DateTime, default=datetime.utcnow)
