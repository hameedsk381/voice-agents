from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Float
from datetime import datetime
from app.core.database import Base
import uuid


class AgentCapability(Base):
    """Registered capability for an agent — enables discovery and routing."""

    __tablename__ = "agent_capabilities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), index=True, nullable=False)
    organization_id = Column(String, index=True, nullable=True)

    name = Column(String, nullable=False)
    description = Column(String, default="")
    input_schema = Column(JSON, default=dict)
    output_schema = Column(JSON, default=dict)
    cost_per_call = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
