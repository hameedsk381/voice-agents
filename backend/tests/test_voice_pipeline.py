import pytest
from app.schemas.policy import ConversationPolicy, State, Guardrail
from app.orchestration.policy_engine import PolicyEngine
from app.orchestration.agent_orchestrator import AgentOrchestrator, AgentContext, ConfidenceScores

@pytest.fixture
def mock_policy():
    return ConversationPolicy(
        initial_state="GREETING",
        states={
            "GREETING": State(
                name="GREETING",
                allowed_intents=["greeting"],
                guardrails=[]
            ),
            "PAYMENT": State(
                name="PAYMENT",
                allowed_intents=["billing", "payment"],
                guardrails=[
                    Guardrail(name="pii_email", type="pii", action="block")
                ]
            )
        },
        global_guardrails=[
            Guardrail(name="no_profanity", type="regex", config={"pattern": r"\b(damn|hell)\b"}, action="block")
        ]
    )

def test_policy_engine_intent_locking(mock_policy):
    engine = PolicyEngine(mock_policy)
    
    # Allowed intent in state
    is_allowed, reason = engine.validate_input("GREETING", "hello", "greeting")
    assert is_allowed is True
    
    # Blocked intent in state (asking for billing in GREETING state)
    is_allowed, reason = engine.validate_input("GREETING", "i want a refund", "billing")
    assert is_allowed is False
    assert "not allowed" in reason

def test_policy_engine_pii_redaction(mock_policy):
    engine = PolicyEngine(mock_policy)
    
    # User provides email in payment state where PII guardrail exists
    is_allowed, reason = engine.validate_input("PAYMENT", "my email is test@example.com", "billing")
    assert is_allowed is False
    assert "PII detected" in reason

def test_policy_engine_global_guardrails(mock_policy):
    engine = PolicyEngine(mock_policy)
    
    # Test global regex guardrail
    is_allowed, reason = engine.validate_input("GREETING", "this is hell", "greeting")
    assert is_allowed is False
    assert "disallowed pattern" in reason

def test_orchestrator_low_confidence_handoff():
    orchestrator = AgentOrchestrator(db=None)
    context = AgentContext(
        session_id="123",
        caller_id=None,
        history=[],
        current_intent="billing",
        extracted_info={},
        confidence=ConfidenceScores(stt=1.0, intent=0.4, policy=1.0, overall=0.7)
    )
    
    # Intent confidence < 0.5 should trigger clarification
    response = orchestrator.handle_low_confidence(context)
    assert response is not None
    assert "billing" in response
    assert "clarify" in response.lower() or "tell me a bit more" in response.lower()
