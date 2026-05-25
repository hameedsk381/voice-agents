"""
Billing, subscription, and usage metering models.
"""
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON, Date
from datetime import datetime, date
import uuid
import enum
from app.core.database import Base


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"
    EXPIRED = "expired"


class UsageMetric(str, enum.Enum):
    CALL_MINUTES = "call_minutes"
    CALL_COUNT = "call_count"
    STT_SECONDS = "stt_seconds"
    TTS_SECONDS = "tts_seconds"
    LLM_TOKENS = "llm_tokens"
    LLM_INPUT_TOKENS = "llm_input_tokens"
    LLM_OUTPUT_TOKENS = "llm_output_tokens"
    TOOL_CALLS = "tool_calls"
    MESSAGES_SENT = "messages_sent"
    MESSAGES_RECEIVED = "messages_received"
    STORAGE_MB = "storage_mb"
    KNOWLEDGE_DOCS = "knowledge_docs"


class Subscription(Base):
    """Active subscription for an organization."""
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), unique=True, nullable=False, index=True)
    plan = Column(String, default="free")  # free, professional, enterprise
    status = Column(String, default=SubscriptionStatus.ACTIVE.value)

    billing_period_start = Column(Date, nullable=False)
    billing_period_end = Column(Date, nullable=False)

    auto_renew = Column(String, default="true")
    payment_provider = Column(String, nullable=True)
    payment_provider_subscription_id = Column(String, nullable=True)

    trial_starts_at = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)

    feature_overrides = Column(JSON, default=dict)
    rate_overrides = Column(JSON, default=dict)
    metadata_json = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UsageRecord(Base):
    """Granular usage record per organization per metric per billing period."""
    __tablename__ = "usage_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    session_id = Column(String, nullable=True, index=True)
    agent_id = Column(String, nullable=True)

    metric = Column(String, nullable=False, index=True)
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String, default="count")

    billing_period_start = Column(Date, nullable=False)
    billing_period_end = Column(Date, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    metadata_json = Column(JSON, default=dict)


class RateCard(Base):
    """Rate card entries per plan for cost calculation."""
    __tablename__ = "rate_cards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan = Column(String, nullable=False, index=True)
    metric = Column(String, nullable=False)
    unit = Column(String, default="count")
    price_per_unit = Column(Float, nullable=False)
    included_units = Column(Float, default=0)
    overage_price_per_unit = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
