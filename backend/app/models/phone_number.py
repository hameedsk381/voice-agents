from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import uuid


class PhoneNumber(Base):
    """Provisioned phone numbers owned by an organization."""
    __tablename__ = "phone_numbers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    friendly_name = Column(String, nullable=True)
    twilio_sid = Column(String, unique=True, nullable=False)
    capabilities = Column(JSON, default=dict)
    region = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization")
