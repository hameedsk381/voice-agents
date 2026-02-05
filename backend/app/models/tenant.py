from sqlalchemy import Column, String, DateTime, Boolean, JSON
from datetime import datetime
import uuid
from app.core.database import Base

class Organization(Base):
    """The root tenant entity for multi-tenancy."""
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=True)
    
    # Billing & Plan
    subscription_plan = Column(String, default="free") # free, professional, enterprise
    is_active = Column(Boolean, default=True)
    
    # Custom Global Metadata
    settings = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
