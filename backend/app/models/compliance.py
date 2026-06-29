from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey, Boolean, Float
from datetime import datetime
from app.core.database import Base
import uuid

class AuditLog(Base):
    """Immutable audit trail for every call turn — chained with cryptographic signatures."""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True)
    organization_id = Column(String, index=True, nullable=True)
    turn_index = Column(Float)
    
    # Content snapshot (PII redacted versions)
    user_message = Column(String)
    ai_response = Column(String)
    
    # Audit Results
    is_compliant = Column(Boolean, default=True)
    violations = Column(JSON, default=list)
    risk_score = Column(Float, default=0.0)
    
    # State Metadata
    agent_id = Column(String, ForeignKey("agents.id"))
    state_name = Column(String)
    
    # Cryptographic Chain Fields
    signature = Column(Text, nullable=True)
    previous_hash = Column(String, nullable=True)
    chain_head = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class DoNotCall(Base):
    """Org-scoped do-not-call list — numbers that must never receive outbound calls."""
    __tablename__ = "do_not_call"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, index=True, nullable=True)
    phone = Column(String, index=True, nullable=False)
    source = Column(String, nullable=True)  # manual | inbound_optout | ncpr | complaint
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PilotApplication(Base):
    """Inbound pilot-program applications from the marketing site."""
    __tablename__ = "pilot_applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    company = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    volume = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=False)
    use_case = Column(Text, nullable=True)
    status = Column(String, default="new")  # new | contacted | scoping | accepted | rejected
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
