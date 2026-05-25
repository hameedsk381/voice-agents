"""
Workflow automation models — definitions and running instances.
"""
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Boolean, Text
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class WorkflowStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class WorkflowInstanceStatus(str, enum.Enum):
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Workflow(Base):
    """Published workflow definition (JSON graph v1)."""

    __tablename__ = "workflows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    organization_id = Column(String, index=True, nullable=True)

    definition = Column(JSON, default=dict)
    version = Column(String, default="1")
    status = Column(String, default=WorkflowStatus.DRAFT.value)
    is_template = Column(Boolean, default=False)
    template_slug = Column(String, nullable=True, index=True)

    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowInstance(Base):
    """One execution of a workflow for a customer/case/contact."""

    __tablename__ = "workflow_instances"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, ForeignKey("workflows.id"), index=True, nullable=False)

    status = Column(String, default=WorkflowInstanceStatus.RUNNING.value, index=True)
    current_node_id = Column(String, nullable=True)
    context = Column(JSON, default=dict)
    wait_until = Column(DateTime, nullable=True)

    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)
    contact_id = Column(String, ForeignKey("campaign_contacts.id"), nullable=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    organization_id = Column(String, index=True, nullable=True)

    outcome = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class EmailMessage(Base):
    """Audit trail for workflow email steps."""

    __tablename__ = "email_messages"

    id = Column(String, primary_key=True)
    workflow_instance_id = Column(String, ForeignKey("workflow_instances.id"), nullable=True, index=True)
    to_address = Column(String, nullable=False)
    template = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    body_preview = Column(Text, nullable=True)
    status = Column(String, default="queued")  # queued, sent, simulated, failed, bounced
    provider_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WhatsAppMessage(Base):
    """Audit trail for workflow WhatsApp steps."""

    __tablename__ = "whatsapp_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_instance_id = Column(String, ForeignKey("workflow_instances.id"), nullable=True, index=True)
    organization_id = Column(String, index=True, nullable=True)
    to_phone = Column(String, nullable=False)
    template = Column(String, nullable=True)
    message_body = Column(Text, nullable=True)
    status = Column(String, default="queued")  # queued, sent, delivered, read, failed
    provider_message_sid = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SmsMessage(Base):
    """Audit trail for workflow SMS steps."""

    __tablename__ = "sms_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_instance_id = Column(String, ForeignKey("workflow_instances.id"), nullable=True, index=True)
    organization_id = Column(String, index=True, nullable=True)
    to_phone = Column(String, nullable=False)
    message_body = Column(Text, nullable=True)
    status = Column(String, default="queued")  # queued, sent, delivered, failed
    provider_message_sid = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
