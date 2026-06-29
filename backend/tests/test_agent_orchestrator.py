import pytest
from unittest.mock import MagicMock, AsyncMock
from app.orchestration.agent_orchestrator import AgentOrchestrator, AgentContext, ConfidenceScores
from app.models.agent import Agent

def test_analyze_sentiment_positive_and_negative():
    orchestrator = AgentOrchestrator(db=MagicMock())
    
    # 1. Simple Positive
    pos_score = orchestrator.analyze_sentiment("This is a great and wonderful day! Thank you.")
    assert pos_score > 0.5
    
    # 2. Simple Negative
    neg_score = orchestrator.analyze_sentiment("This is a terrible, bad, and broken issue. I hate it.")
    assert neg_score < 0.5
    
    # 3. Neutral/Empty
    neutral_score = orchestrator.analyze_sentiment("")
    assert neutral_score == 0.5

def test_analyze_sentiment_negations():
    orchestrator = AgentOrchestrator(db=MagicMock())
    
    # "not bad" -> negation flips bad (negative) to positive
    score_not_bad = orchestrator.analyze_sentiment("It is not bad.")
    assert score_not_bad > 0.5
    
    # "not good" -> negation flips good (positive) to negative
    score_not_good = orchestrator.analyze_sentiment("It is not good.")
    assert score_not_good < 0.5
    
    # "never happy" -> negation flips happy (positive) to negative
    score_never_happy = orchestrator.analyze_sentiment("I am never happy with this.")
    assert score_never_happy < 0.5

def test_detect_intent_word_boundaries():
    orchestrator = AgentOrchestrator(db=MagicMock())
    
    # Matches correct intent with high confidence
    intent, conf = orchestrator.detect_intent("I have a billing inquiry")
    assert intent == "billing"
    assert conf == 0.95
    
    intent, conf = orchestrator.detect_intent("My system has an error and a bug")
    assert intent == "technical"
    assert conf == 0.95
    
    intent, conf = orchestrator.detect_intent("I want to subscribe to a new plan")
    assert intent == "sales"
    assert conf == 0.95
    
    intent, conf = orchestrator.detect_intent("Where is my package and delivery?")
    assert intent == "order"
    assert conf == 0.95
    
    intent, conf = orchestrator.detect_intent("I cannot login to my account")
    assert intent == "account"
    assert conf == 0.95
    
    # Exact word boundaries: partial match should NOT trigger strict match
    # "billionaire" contains "bill" which matches loose keyword with 0.6
    intent, conf = orchestrator.detect_intent("The billionaire bought a house")
    assert intent == "billing"
    assert conf == 0.6
    
    # "building" doesn't match "bill" or any keyword -> no intent
    intent, conf = orchestrator.detect_intent("I love building sandcastles")
    assert intent is None
    assert conf == 0.0

def test_detect_intent_loose_keyword_confidence():
    orchestrator = AgentOrchestrator(db=MagicMock())
    
    # Loose keyword match (substring, no word boundaries) returns 0.6
    intent, conf = orchestrator.detect_intent("I have a billingq")
    assert intent == "billing"
    assert conf == 0.6

@pytest.mark.asyncio
async def test_should_escalate(mock_agent, mock_context, mock_llm_service):
    orchestrator = AgentOrchestrator(db=MagicMock())
    
    # 1. Neutral history -> No escalation
    should, reason = await orchestrator.should_escalate(mock_context, "Here is a normal response", mock_agent, mock_llm_service)
    assert not should
    assert reason is None
    
    # 2. Sentiment drop -> Escalate
    mock_context.sentiment_slope = 0.2
    should, reason = await orchestrator.should_escalate(mock_context, "Empathetic response", mock_agent, mock_llm_service)
    assert should
    assert "sentiment" in reason.lower()
    
    # Reset sentiment
    mock_context.sentiment_slope = 0.8
    
    # 3. Explicit keywords -> Escalate
    mock_context.history.append({"role": "user", "content": "Let me speak to a human manager immediately!"})
    should, reason = await orchestrator.should_escalate(mock_context, "Please wait.", mock_agent, mock_llm_service)
    assert should
    assert "human" in reason.lower() or "manager" in reason.lower()
    
    # 4. Agent-specific failure condition (keyword fallback, no LLM) -> Escalate
    mock_context.history = [{"role": "user", "content": "This is offensive language"}]
    should, reason = await orchestrator.should_escalate(mock_context, "Apologies.", mock_agent)  # no llm_service
    assert should
    assert "failure condition" in reason.lower()

def test_handle_low_confidence_contextual():
    orchestrator = AgentOrchestrator(db=MagicMock())
    
    ctx = AgentContext(
        session_id="s1", caller_id="c1", history=[], current_intent=None,
        extracted_info={}, confidence=ConfidenceScores(stt=0.3, intent=0.9, overall=0.6)
    )
    result = orchestrator.handle_low_confidence(ctx)
    # Medium tier with low STT -> ask the caller to repeat.
    assert "repeat" in result

    ctx.confidence = ConfidenceScores(stt=0.9, intent=0.3, overall=0.6)
    result = orchestrator.handle_low_confidence(ctx)
    # Medium tier, STT ok, no intent yet -> generic clarification.
    assert "clarify" in result.lower()

    ctx.current_intent = "billing"
    result = orchestrator.handle_low_confidence(ctx)
    # Medium tier with a detected intent -> surface it for confirmation.
    assert "billing" in result


@pytest.mark.asyncio
async def test_should_escalate_semantic_llm(mock_agent, mock_context, mock_llm_service):
    orchestrator = AgentOrchestrator(db=MagicMock())
    
    # LLM says YES failure condition -> escalate
    mock_llm_service.generate_response.return_value = "YES"
    mock_context.history = [{"role": "user", "content": "I am very angry about this!"}]
    should, reason = await orchestrator.should_escalate(mock_context, "I understand.", mock_agent, mock_llm_service)
    assert should
    assert "Failure Condition" in reason
    
    # LLM says NO -> no escalation
    mock_llm_service.generate_response.return_value = "NO"
    mock_context.history = [{"role": "user", "content": "Not bad at all, I'm fine"}]
    should, reason = await orchestrator.should_escalate(mock_context, "Great!", mock_agent, mock_llm_service)
    # "not bad" should NOT trigger a failure condition - the LLM correctly says NO
    assert not should

@pytest.mark.asyncio
async def test_reflect_and_correct(mock_agent, mock_context, mock_llm_service):
    orchestrator = AgentOrchestrator(db=MagicMock())
    
    original_response = "Here is your requested refund today."
    
    # LLM Critic echoes the response (CORRECTED == original) -> no correction.
    mock_llm_service.generate_response.return_value = f"CONFIDENCE: 0.9\nCORRECTED: {original_response}"
    res = await orchestrator.reflect_and_correct("I want my money back.", original_response, mock_context, mock_agent, mock_llm_service)
    assert res == original_response

    # LLM Critic returns an improved CORRECTED response -> correction applied.
    improved_response = "I have initiated your refund, and apologized for the wait."
    mock_llm_service.generate_response.return_value = f"CONFIDENCE: 0.5\nCORRECTED: {improved_response}"
    res = await orchestrator.reflect_and_correct("I want my money back.", original_response, mock_context, mock_agent, mock_llm_service)
    assert res == improved_response
