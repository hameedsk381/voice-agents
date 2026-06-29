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

    # India DLT (Distributed Ledger Technology) registration metadata — TRAI/TCCCPR
    dlt_entity_id = Column(String, nullable=True)  # Principal Entity ID on the DLT platform
    dlt_header = Column(String, nullable=True)  # Registered sender ID / header
    number_series = Column(String, nullable=True)  # "1600" transactional, "140" promotional
    dlt_status = Column(String, default="unregistered")  # unregistered | pending | registered
    consent_template_id = Column(String, nullable=True)  # Registered consent template reference

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization")
