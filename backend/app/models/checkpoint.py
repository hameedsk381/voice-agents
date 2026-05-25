from sqlalchemy import Column, String, JSON, DateTime, Integer, ForeignKey
from datetime import datetime
from app.core.database import Base
import uuid


class CallCheckpoint(Base):
    """Durable checkpoint — full session state snapshot after each turn.
    Enables crash recovery and long-running call resilience.
    """
    __tablename__ = "call_checkpoints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True, nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), index=True, nullable=True)
    turn_index = Column(Integer, nullable=False)
    state_json = Column(JSON, nullable=False)  # serialised session state
    conversation_summary = Column(String, nullable=True)  # brief summary of progress so far
    created_at = Column(DateTime, default=datetime.utcnow)
