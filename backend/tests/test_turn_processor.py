import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.orchestration.turn_processor import TurnProcessor
from app.models.agent import Agent
from app.orchestration.agent_orchestrator import AgentContext

@pytest.fixture
def mock_dependencies():
    """Patches all external service initializations in TurnProcessor to avoid DB/network issues."""
    with patch("app.orchestration.turn_processor.EnterpriseLLM") as mock_llm_class, \
         patch("app.orchestration.turn_processor.get_memory_service") as mock_mem_func, \
         patch("app.orchestration.turn_processor.AnalyticsService") as mock_analytics_class, \
         patch("app.orchestration.turn_processor.VoiceUXService") as mock_voice_class, \
         patch("app.orchestration.turn_processor.ShadowComparisonService") as mock_shadow_class, \
         patch("app.orchestration.turn_processor.HITLService") as mock_hitl_class:
         
         # Instantiate mock services
         mock_llm = MagicMock()
         mock_llm.generate_response = AsyncMock(return_value="Mocked response")
         mock_llm_class.return_value = mock_llm
         
         mock_mem = MagicMock()
         mock_mem.get_context_for_call = AsyncMock(return_value=None)
         mock_mem_func.return_value = mock_mem
         
         mock_analytics = MagicMock()
         mock_analytics_class.return_value = mock_analytics
         
         mock_voice = MagicMock()
         mock_voice_class.return_value = mock_voice
         
         mock_shadow = MagicMock()
         mock_shadow_class.return_value = mock_shadow
         
         mock_hitl = MagicMock()
         mock_hitl.get_intervention_status = AsyncMock(return_value=None)
         mock_hitl_class.return_value = mock_hitl
         
         yield {
             "llm": mock_llm,
             "mem": mock_mem,
             "analytics": mock_analytics,
             "voice": mock_voice,
             "shadow": mock_shadow,
             "hitl": mock_hitl
         }

def test_turn_processor_is_fast_path_turn(mock_db, mock_websocket, mock_agent, mock_dependencies):
    processor = TurnProcessor(
        db=mock_db,
        websocket=mock_websocket,
        agent=mock_agent,
        agent_id="test-agent-id",
        session_id="test-session-id"
    )
    
    # 1. Matches expected shortcuts
    assert processor.is_fast_path_turn("hello") == "Hi there! How can I help?"
    assert processor.is_fast_path_turn("OK ") == "Got it."
    assert processor.is_fast_path_turn("thanks!!!") == "You're welcome."
    
    # 2. None for normal complex sentences
    assert processor.is_fast_path_turn("I have an error on my screen and I need technical assistance") is None

@pytest.mark.asyncio
async def test_turn_processor_initialize_context(mock_db, mock_websocket, mock_agent, mock_dependencies):
    mem_service_mock = mock_dependencies["mem"]
    
    # Mock loaded context value
    mock_memory_item = MagicMock()
    mem_service_mock.get_context_for_call.return_value = mock_memory_item
    
    processor = TurnProcessor(
        db=mock_db,
        websocket=mock_websocket,
        agent=mock_agent,
        agent_id="test-agent-id",
        session_id="test-session-id",
        caller_id="test-caller-id"
    )
    
    await processor.initialize_context()
    
    # Verify memory service was consulted
    mem_service_mock.get_context_for_call.assert_called_once_with("test-caller-id", organization_id=None)
    # Verify loaded context was put in state memory list
    assert len(processor.context.memory) == 1
    assert processor.context.memory[0] == mock_memory_item

@pytest.mark.asyncio
async def test_turn_processor_fast_path_execution(mock_db, mock_websocket, mock_agent, mock_dependencies):
    processor = TurnProcessor(
        db=mock_db,
        websocket=mock_websocket,
        agent=mock_agent,
        agent_id="test-agent-id",
        session_id="test-session-id"
    )
    
    with patch("app.orchestration.turn_processor.send_with_tts", AsyncMock()) as mock_send_tts, \
         patch("app.orchestration.turn_processor.session_manager.add_to_history", AsyncMock()), \
         patch("app.orchestration.turn_processor.monitoring_service.broadcast_event", AsyncMock()):
         
         await processor.process_turn("hello", stt_confidence=0.95, stt_ms=12.5)
         
         mock_send_tts.assert_called_once()
         assert mock_send_tts.call_args[0][1] == "Hi there! How can I help?"
         
         calls = [c.args[0] for c in mock_websocket.send_json.call_args_list]
         assert any(c.get("type") == "turn_metrics" for c in calls)
         metrics_msg = next(c for c in calls if c.get("type") == "turn_metrics")
         assert metrics_msg["path"] == "fast_path"
         assert metrics_msg["stt_ms"] == 12.5
         assert metrics_msg["confidence_vector"]["stt"] == 0.95
         assert calls[-1] == {"type": "end_response"}


@pytest.mark.asyncio
async def test_low_stt_confidence_triggers_clarify(mock_db, mock_websocket, mock_agent, mock_dependencies):
    processor = TurnProcessor(
        db=mock_db,
        websocket=mock_websocket,
        agent=mock_agent,
        agent_id="test-agent-id",
        session_id="test-session-id",
        session_policy=None,
    )
    processor.orchestrator.policy_engine = None

    with patch("app.orchestration.turn_processor.send_with_tts", AsyncMock()) as mock_send_tts, \
         patch("app.orchestration.turn_processor.monitoring_service.broadcast_event", AsyncMock()):
        await processor.process_turn(
            "I need help with my billing account",
            stt_confidence=0.25,
        )
        mock_send_tts.assert_called_once()
        calls = [c.args[0] for c in mock_websocket.send_json.call_args_list]
        metrics_msg = next(c for c in calls if c.get("type") == "turn_metrics")
        assert metrics_msg["path"] == "clarify"
        assert metrics_msg["confidence_vector"]["stt"] == 0.25

@pytest.mark.asyncio
async def test_barge_in_truncation(mock_db, mock_websocket, mock_agent, mock_dependencies):
    processor = TurnProcessor(
        db=mock_db,
        websocket=mock_websocket,
        agent=mock_agent,
        agent_id="test-agent-id",
        session_id="test-session-id"
    )
    
    # Simulate that some text was sent before cancellation
    processor._sent_buffer = ["Hello, I", " am looking ", "into that"]
    
    with patch("app.orchestration.turn_processor.session_manager.add_to_history", AsyncMock()) as mock_hist:
        try:
            raise asyncio.CancelledError()
        except asyncio.CancelledError:
            sent_text = "".join(processor._sent_buffer).strip()
            if sent_text:
                await mock_hist("test-session-id", "assistant", sent_text)
    
    # Only the sent buffer text should be persisted, not a full predicted response
    mock_hist.assert_called_once_with("test-session-id", "assistant", "Hello, I am looking into that")
