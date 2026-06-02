import uuid
import asyncio
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from loguru import logger

from app.core import database
from app.core.config import settings
from app.core.deps import get_current_user_required
from app.models.user import User
from app.models import agent as models
from app.schemas.orchestrator import ChatRequest, ChatResponse, LiveKitJoinRequest, LiveKitJoinResponse
from app.orchestration.session_manager import session_manager
from app.orchestration.pipecat_pipeline import generate_livekit_token, run_pipecat_agent

router = APIRouter()

def _resolve_agent_config(agent, db, agent_id: str):
    """Apply A/B version or pinned version overrides."""
    from app.orchestration.agent_config import resolve_active_agent_config
    active_persona, active_tools, _ = resolve_active_agent_config(db, agent)
    return active_persona, active_tools or []

@router.post("/livekit/join/{agent_id}", response_model=LiveKitJoinResponse)
async def livekit_join_call(
    agent_id: str,
    background_tasks: BackgroundTasks,
    body: LiveKitJoinRequest = None,
    db: Session = Depends(database.get_db),
    # Optional: current_user: User = Depends(get_current_user_required)
):
    """Create a LiveKit room, generate token, and spin up Pipecat."""
    body = body or LiveKitJoinRequest()
    
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    active_persona, active_tools = _resolve_agent_config(agent, db, agent_id)
    session_language = body.language or agent.language or "en-US"
    
    # 1. Create a unique Room Name for this session
    room_name = f"room-{uuid.uuid4().hex[:8]}"
    call_id = room_name
    session_id = str(uuid.uuid4())
    
    # 2. Generate a Participant Token for the Frontend
    participant_name = body.caller_id or "user"
    token = await generate_livekit_token(room_name, participant_name)
    
    # 3. Resolve Greeting
    agent_config = agent.config or {}
    greeting = agent_config.get("greeting", "Hello! How can I help you today?")
    
    # 4. Spin up the Pipecat Agent Pipeline as a background task
    system_prompt = active_persona or "You are a helpful AI assistant."
    background_tasks.add_task(
        run_pipecat_agent, 
        room_name=room_name, 
        system_prompt=system_prompt, 
        greeting=greeting,
        agent_id=agent_id,
        session_id=session_id,
        active_tools=active_tools
    )
    
    # 5. Track the session in our database
    await session_manager.create_session(
        session_id=session_id, agent_id=agent_id,
        caller_id=body.caller_id,
        metadata={
            "channel": "livekit", "org_id": agent.organization_id,
            "livekit_room": room_name,
        },
    )

    return LiveKitJoinResponse(
        room_name=room_name,
        participant_token=token,
        call_id=call_id,
        session_id=session_id,
        agent_id=agent_id,
        agent_name=agent.name,
        voice="deepgram/elevenlabs",
        language=session_language,
        tool_names=[t.get("name") for t in active_tools] if active_tools else [],
    )

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(database.get_db)):
    """Experimental: Stateless/REST Chat connector for Text Agents."""
    agent = db.query(models.Agent).filter(models.Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    session_id = request.session_id or str(uuid.uuid4())
    org_id = agent.organization_id
    
    # Basic Chat implementation using Groq
    from app.services.llm.groq_provider import GroqLLM
    llm_service = GroqLLM(model="llama3-8b-8192")
    
    await session_manager.connect()
    session = await session_manager.get_session(session_id)
    if not session:
        await session_manager.create_session(session_id, request.agent_id, request.caller_id, metadata={"channel": "rest"})
        history = []
    else:
        history = await session_manager.get_history(session_id)

    response_text = await llm_service.generate_response(
        request.text, 
        agent.persona, 
        history
    )
    
    await session_manager.add_to_history(session_id, "user", request.text)
    await session_manager.add_to_history(session_id, "assistant", response_text)
    
    return ChatResponse(
        session_id=session_id,
        text=response_text,
        agent_id=request.agent_id,
        metadata={"org_id": org_id}
    )
