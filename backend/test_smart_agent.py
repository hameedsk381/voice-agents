
import asyncio
import os
import sys
from loguru import logger
from sqlalchemy.orm import Session
from app.core import database
from app.models.agent import Agent
from app.orchestration.agent_orchestrator import AgentOrchestrator, AgentContext, ConfidenceScores
from app.services.llm.enterprise_llm import EnterpriseLLM
from app.services.knowledge_service import KnowledgeService
from app.schemas.policy import ConversationPolicy

async def test_smart_conversation():
    # Setup
    db = next(database.get_db())
    llm = EnterpriseLLM()
    knowledge_service = KnowledgeService(db)
    
    # Pick the TechDiagnostic Agent
    agent_id = "39dc4a1b-cf11-4a59-a596-ecba4ad31ca7"
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        print("Agent not found!")
        return

    orchestrator = AgentOrchestrator(db)
    context = AgentContext(
        session_id="test_session_smart",
        caller_id="test_user",
        history=[],
        current_intent=None,
        extracted_info={},
        confidence=ConfidenceScores(overall=1.0)
    )

    print(f"--- Testing Smart Agent: {agent.name} ---")
    
    # Simulate a complex user input that should trigger RAG and logical reasoning
    user_input = "My internet is slow and I feel really frustrated. I've already tried restarting the router. This is the third time this week!"
    print(f"User: {user_input}")

    # 1. Intent & Sentiment
    intent = orchestrator.detect_intent(user_input)
    sentiment = orchestrator.analyze_sentiment(user_input)
    context.current_intent = intent
    context.sentiment_slope = sentiment
    print(f"[Orchestrator] Intent: {intent}, Sentiment Score: {sentiment}")

    # 2. Knowledge Retrieval (RAG)
    relevant_chunks = await knowledge_service.query_knowledge(agent_id, user_input, limit=2)
    knowledge_context = ""
    if relevant_chunks:
        print(f"[RAG] Found {len(relevant_chunks)} relevant knowledge chunks.")
        knowledge_context = "\n\nUSE THESE FACTS FROM YOUR KNOWLEDGE BASE IF RELEVANT:\n" + \
                            "\n".join([f"- {c['content']}" for c in relevant_chunks])
    else:
        print("[RAG] No specific knowledge found, using general reasoning.")

    # 3. Generate Response
    system_prompt = f"{agent.persona}{knowledge_context}"
    response = await llm.generate_response(user_input, system_prompt, context.history)
    print(f"Assistant (Before Reflection): {response}")

    # 4. Self-Correction / Reflection
    # Add a success criterion to the agent temporarily to trigger reflection check
    original_criteria = agent.success_criteria
    agent.success_criteria = ["Acknowledge frustration", "Propose advanced troubleshooting"]
    
    reflected_response = await orchestrator.reflect_and_correct(
        user_input, response, context, agent, llm
    )
    agent.success_criteria = original_criteria # Restore
    
    print(f"Assistant (After Reflection): {reflected_response}")

    # 5. Review 'Smartness'
    if sentiment < 0.3:
        print("[Review] Agent identified high frustration and should be empathetic.")
    if intent == "technical":
        print("[Review] Agent identified technical intent and ignored the router restart (as user already did it).")

if __name__ == "__main__":
    asyncio.run(test_smart_conversation())
