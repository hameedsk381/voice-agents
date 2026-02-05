from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Boolean, Float
from datetime import datetime
from app.core.database import Base
import uuid

class AuditLog(Base):
    """Immutable audit trail for every call turn."""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True)
    organization_id = Column(String, index=True, nullable=True) # Multitenancy
    turn_index = Column(Float) # turn counter
    
    # Content snapshot (PII redacted versions are optional)
    user_message = Column(String)
    ai_response = Column(String)
    
    # Audit Results
    is_compliant = Column(Boolean, default=True)
    violations = Column(JSON, default=list) # List of violations details
    risk_score = Column(Float, default=0.0)
    
    # State Metadata
    agent_id = Column(String, ForeignKey("agents.id"))
    state_name = Column(String) # Converstion state name
    
    created_at = Column(DateTime, default=datetime.utcnow)

class RegulatoryPolicy(Base):
    """Sets of rules applied to sessions based on industry/region."""
    __tablename__ = "regulatory_policies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True)
    organization_id = Column(String, index=True, nullable=True)
    description = Column(String)
    
    # Rules definitions
    rules = Column(JSON) # List of ComplianceRule objects
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
