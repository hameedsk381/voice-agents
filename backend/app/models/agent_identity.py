from sqlalchemy import Column, String, JSON, DateTime, Boolean, Text
from datetime import datetime
from app.core.database import Base
import uuid


class AgentIdentity(Base):
    """Agent cryptographic identity — Ed25519 keypair store."""
    __tablename__ = "agent_identities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, index=True, nullable=False)
    public_key = Column(Text, nullable=False)
    private_key_encrypted = Column(Text, nullable=True)
    certificate_pem = Column(Text, nullable=True)
    spiffe_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    key_version = Column(String, default="v1")
    created_at = Column(DateTime, default=datetime.utcnow)
    rotated_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, default=dict)
