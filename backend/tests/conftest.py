import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.orchestration.agent_orchestrator import AgentContext, ConfidenceScores, MemoryItem, MemoryType

@pytest.fixture
def mock_db():
    """Provides a mocked SQLAlchemy DB Session."""
    db = MagicMock(spec=Session)
    
    # Mocking standard query method
    mock_query = MagicMock()
    db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    
    # Mock query first() and all()
    mock_query.first.return_value = None
    mock_query.all.return_value = []
    
    # Enable add, commit, refresh, rollback without execution
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.rollback = MagicMock()
    db.flush = MagicMock()
    return db

@pytest.fixture
def mock_agent():
    """Provides a baseline Agent model instance for orchestration testing."""
    agent = Agent(
        id="test-agent-uuid-12345",
        name="Support Specialist",
        role="support",
        persona="You are a calm, professional support agent. Help the user with their needs.",
        language="en-US",
        is_active=True,
        success_criteria=["acknowledge frustration", "propose solution"],
        failure_conditions=["user angry", "offensive language"],
        exit_actions=["escalate"]
    )
    return agent

@pytest.fixture
def mock_context():
    """Provides a standard pre-configured AgentContext."""
    return AgentContext(
        session_id="test_session_id_999",
        caller_id="test_caller_id_888",
        history=[
            {"role": "assistant", "content": "Hello, how can I help you today?"},
            {"role": "user", "content": "I need help with my payment."}
        ],
        current_intent="billing",
        extracted_info={},
        current_state="GREETING",
        confidence=ConfidenceScores(stt=0.9, intent=0.9, policy=1.0, llm_response=0.9, overall=0.92),
        sentiment_slope=0.8,
        memory=[
            MemoryItem(key="first_name", value="Alice", type=MemoryType.USER_CLAIM)
        ]
    )

@pytest.fixture
def mock_websocket():
    """Provides an async mock of FastAPI's WebSocket class."""
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.close = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_text = AsyncMock(return_value='{"type": "text", "text": "hello"}')
    return websocket

@pytest.fixture
def mock_llm_service():
    """Provides a mock LLM service returning stable mock responses."""
    llm = MagicMock()
    llm.generate_response = AsyncMock(return_value="This is a mock LLM generated response.")
    return llm

@pytest.fixture
def mock_tts_service():
    """Provides a mock TTS service returning mock audio bytes."""
    tts = MagicMock()
    tts.synthesize = AsyncMock(return_value=b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
    return tts
