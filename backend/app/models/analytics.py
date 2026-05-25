"""
Call Log model for detailed observability and analytics.
"""
from sqlalchemy import Column, String, JSON, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import uuid

class CallLog(Base):
    """Stores detailed metrics for every completed call."""
    __tablename__ = "call_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True, unique=True)
    
    # Context
    agent_id = Column(String, ForeignKey("agents.id"), index=True)
    organization_id = Column(String, index=True, nullable=True)
    caller_id = Column(String, nullable=True, index=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)
    
    # Timing Metrics (ms)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    
    # Performance Metrics
    avg_latency_ms = Column(Float, default=0.0)
    ttfap_ms = Column(Float, default=0.0) # Time to First Audio Packet
    total_turns = Column(Integer, default=0)
    
    # Usage & Cost
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    
    # Outcome
    status = Column(String) # completed, failed, escalated
    end_reason = Column(String) # hung up, completed, error
    outcome = Column(String) # SUCCESS, FAILURE, NEUTRAL
    outcome_reason = Column(String) # Explanation for the outcome
    
    # Data
    transcript = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)
    signature = Column(String, nullable=True) # Hash-signed transcript for audit proof
    
    created_at = Column(DateTime, default=datetime.utcnow)


class TraceLog(Base):
    __tablename__ = "trace_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True, nullable=True)
    parent_span_id = Column(String, nullable=True, index=True)
    span_name = Column(String, index=True)
    span_type = Column(String)  # llm, stt, tts, turn, tool, compliance, etc.
    duration_ms = Column(Float)
    attributes = Column(JSON, default=dict)
    status_code = Column(String, default="OK")
    status_message = Column(String, default="")
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True, index=True)
    organization_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    suite_name = Column(String, index=True)
    status = Column(String, default="running")
    total_tests = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    score = Column(Float, nullable=True)
    model_under_test = Column(String)
    run_metadata = Column(JSON, default=dict)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvalTestCaseResult(Base):
    __tablename__ = "eval_test_case_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("eval_runs.id"), index=True)
    test_name = Column(String)
    input_text = Column(String)
    expected_output = Column(String, nullable=True)
    actual_output = Column(String, nullable=True)
    passed = Column(Boolean)
    score = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    failure_reason = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class ShadowLog(Base):
    """
    Comparison logs between Primary and Shadow models.
    Used to validate if cheaper models can handle the workload.
    """
    __tablename__ = "shadow_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True)
    organization_id = Column(String, index=True, nullable=True)
    turn_index = Column(Integer)
    
    primary_model = Column(String) # e.g. gpt-4o
    shadow_model = Column(String) # e.g. llama3-8b-8192
    
    primary_response = Column(String)
    shadow_response = Column(String)
    
    # Comparison Metrics
    similarity_score = Column(Float) # 0.0 to 1.0 (Cosine Similarity)
    intent_match = Column(Boolean, default=True)
    
    # Latency Comparison
    primary_latency_ms = Column(Float)
    shadow_latency_ms = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
