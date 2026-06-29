import random
import json
import base64
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from starlette.websockets import WebSocketState
from loguru import logger

from app.core import database
from app.core.config import settings
from app.core.security import decode_token
from app.core.deps import get_current_user_required
from app.models.user import User
from app.models import agent as models
from app.schemas.policy import ConversationPolicy, State, Transition, Guardrail
from app.schemas.orchestrator import ChatRequest, ChatResponse, UltravoxJoinRequest, UltravoxJoinResponse

from app.orchestration.session_manager import session_manager
from app.services.monitoring_service import monitoring_service
from app.services.hitl_service import HITLService
from app.services.agent_registry_service import AgentRegistryService

# Import modular components
from app.orchestration.websocket_proxy import run_ultravox_proxy_session, is_ultravox_runtime
from app.orchestration.ultravox_call import (
    build_ultravox_selected_tools,
    build_system_prompt,
    extract_agent_tool_names,
)
from app.services.ultravox_service import UltravoxService
from app.orchestration.tool_executor import execute_tool

ultravox_service = UltravoxService()

def get_sample_policy():
    return ConversationPolicy(
        initial_state="GREETING",
        states={
            "GREETING": State(
                name="GREETING",
                enforce_script="Hello! I'm your AI assistant. How can I help you today?",
                allowed_intents=["greeting", "ask_help", "billing", "technical", "sales", "account"],
                transitions=[
                    Transition(event="user_spoke", target_state="PROCESSING")
                ]
            ),
            "PROCESSING": State(
                name="PROCESSING",
                allowed_intents=["billing", "technical", "sales", "order", "account", "fallback"],
                transitions=[
                    Transition(event="billing_intent", target_state="BILLING_SUPPORT"),
                    Transition(event="technical_intent", target_state="TECH_SUPPORT"),
                    Transition(event="tool_needed", target_state="WAITING_FOR_TOOL")
                ],
                guardrails=[
                    Guardrail(name="Disallow-Profanity", type="regex", config={"pattern": r"fuck|shit|damn"}, action="block")
                ]
            ),
            "WAITING_FOR_TOOL": State(
                name="WAITING_FOR_TOOL",
                transitions=[
                    Transition(event="tool_complete", target_state="PROCESSING")
                ]
            ),
            "BILLING_SUPPORT": State(
                name="BILLING_SUPPORT",
                enforce_script="I can certainly help you with your billing inquiry. Could you please provide your account number?",
                allowed_intents=["provide_account", "ask_why"],
                guardrails=[
                    Guardrail(name="PII-Check", type="pii", action="mask")
                ]
            ),
            "TECH_SUPPORT": State(
                name="TECH_SUPPORT",
                enforce_script="Technical support here. What seems to be the issue with your service?",
                allowed_intents=["describe_problem"]
            )
        }
    )

router = APIRouter()


def _resolve_agent_config(agent, db, agent_id: str):
    """Apply A/B version or pinned version overrides."""
    from app.orchestration.agent_config import resolve_active_agent_config
    from app.schemas.policy import ConversationPolicy

    active_persona, active_tools, active_policy_raw = resolve_active_agent_config(db, agent)
    active_policy = None
    if active_policy_raw:
        active_policy = ConversationPolicy.parse_obj(active_policy_raw)
    return active_persona, active_tools or [], active_policy


def _resolve_agent_by_id_or_capability(
    db: Session, agent_id: Optional[str], capability: Optional[str]
) -> models.Agent:
    """Resolve an agent by direct ID or by registry capability discovery."""
    if capability:
        svc = AgentRegistryService(db)
        agent = svc.find_agent_for_capability(capability)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"No active agent found for capability '{capability}'",
            )
        return agent
    if not agent_id:
        raise HTTPException(status_code=400, detail="Either agent_id or capability is required")
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


async def _create_ultravox_join(
    agent: models.Agent,
    db: Session,
    body: UltravoxJoinRequest,
) -> UltravoxJoinResponse:
    """Shared Ultravox call creation logic used by both agent_id and capability endpoints."""
    agent_id = agent.id
    active_persona, active_tools, _ = _resolve_agent_config(agent, db, agent_id)

    # Pre-call limit check
    from app.services.usage_service import UsageService
    usage_svc = UsageService(db)
    call_check = usage_svc.check_call_allowed(agent.organization_id)
    if not call_check["allowed"]:
        reason = call_check.get("reason", "limit_exceeded")
        logger.warning(f"Call blocked for org {agent.organization_id}: {reason}")
        raise HTTPException(status_code=402, detail=f"Cannot initiate call — {reason.replace('_', ' ')}")

    session_language = body.language or agent.language or "en-US"
    agent_config = agent.config or {}
    selected_voice = body.voice or agent_config.get("voice")
    if not selected_voice or selected_voice == "auto":
        selected_voice = settings.ULTRAVOX_VOICE

    from app.orchestration.ultravox_call import (
        build_caller_memory_context,
        build_template_context,
        resolve_call_greeting,
    )
    from app.services.ultravox_agent_sync import (
        ensure_ultravox_agent_id,
        start_ultravox_call_for_agent,
    )
    from app.services.identity_service import IdentityService

    # Attach agent identity (SPIFFE ID) to call metadata
    identity_svc = IdentityService(db)
    identity = identity_svc.get_identity(agent_id)
    spiffe_id = identity.spiffe_id if identity else None

    metadata = {
        "agent_id": agent_id,
        "org_id": agent.organization_id or "",
        "channel": "browser_sdk",
        "spiffe_id": spiffe_id,
    }
    caller_context = await build_caller_memory_context(
        db, body.caller_id, organization_id=agent.organization_id, agent_id=agent_id
    )
    template_context = build_template_context(
        agent,
        caller_id=body.caller_id,
        language=session_language,
        extra={"callerContext": caller_context} if caller_context else None,
    )

    ultravox_agent_id = await ensure_ultravox_agent_id(
        agent, db, active_persona=active_persona, language=session_language, voice=selected_voice,
    )

    greeting = resolve_call_greeting(agent)

    if ultravox_agent_id:
        call = await start_ultravox_call_for_agent(
            agent, ultravox_agent_id=ultravox_agent_id,
            template_context=template_context, metadata=metadata,
            tools=active_tools, tool_implementation="client", greeting=greeting,
            temperature=body.temperature,
            max_duration=body.max_duration,
            recording_enabled=body.recording_enabled,
            join_timeout=body.join_timeout,
            initial_messages=body.initial_messages,
            initial_state=body.initial_state,
            deferred_messages=body.deferred_messages,
            prior_call_id=body.prior_call_id,
        )
    else:
        selected_tools = build_ultravox_selected_tools(active_tools, implementation="client")
        system_prompt = build_system_prompt(agent, active_persona, session_language)
        call = await ultravox_service.create_browser_call(
            system_prompt=system_prompt, voice=selected_voice,
            metadata=metadata, selected_tools=selected_tools,
            initial_state=body.initial_state or {"agent_id": agent_id, "organization_id": agent.organization_id},
        )

    join_url = call.get("joinUrl")
    call_id = call.get("callId") or str(uuid.uuid4())
    logger.info(f"Ultravox joinUrl: {join_url}")
    if not join_url:
        raise HTTPException(status_code=502, detail="Ultravox did not return joinUrl")

    session_id = call_id
    await session_manager.create_session(
        session_id=session_id, agent_id=agent_id,
        caller_id=body.caller_id,
        metadata={
            "channel": "ultravox_sdk", "org_id": agent.organization_id,
            "floor_owner": "user", "provider": "ultravox",
            "ultravox_call_id": call_id,
        },
    )
    await session_manager.link_ultravox_call_id(session_id, call_id)

    await monitoring_service.broadcast_event(session_id, "session_start", {
        "agent_id": agent_id, "agent_name": agent.name, "provider": "ultravox_sdk",
    })

    return UltravoxJoinResponse(
        join_url=join_url, call_id=call_id, session_id=session_id,
        agent_id=agent_id, agent_name=agent.name,
        voice=selected_voice, language=session_language,
        tool_names=extract_agent_tool_names(active_tools),
        ultravox_agent_id=ultravox_agent_id,
    )


@router.post("/ultravox/join/{agent_id}", response_model=UltravoxJoinResponse)
async def ultravox_join_call(
    agent_id: str,
    body: UltravoxJoinRequest = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Create an Ultravox call by agent_id and return joinUrl."""
    if not is_ultravox_runtime():
        raise HTTPException(status_code=503, detail="Ultravox is not configured.")

    body = body or UltravoxJoinRequest()
    agent = _resolve_agent_by_id_or_capability(db, agent_id, body.capability if body else None)
    return await _create_ultravox_join(agent, db, body)


@router.post("/ultravox/join-by-capability/{capability}", response_model=UltravoxJoinResponse)
async def ultravox_join_by_capability(
    capability: str,
    body: UltravoxJoinRequest = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Create an Ultravox call by discovering the best agent for a given capability."""
    if not is_ultravox_runtime():
        raise HTTPException(status_code=503, detail="Ultravox is not configured.")

    body = body or UltravoxJoinRequest()
    agent = _resolve_agent_by_id_or_capability(db, None, capability)
    return await _create_ultravox_join(agent, db, body)


@router.get("/ultravox/calls")
async def ultravox_list_calls(
    agent_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_required),
):
    """List Ultravox calls for the organization, optionally filtered by agent."""
    if not is_ultravox_runtime():
        raise HTTPException(status_code=503, detail="Ultravox is not configured.")
    calls = await ultravox_service.list_calls(
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )
    return {"calls": calls, "total": len(calls)}


@router.post("/ultravox/tools/{tool_name}")
async def ultravox_execute_tool(
    tool_name: str,
    payload: Dict[str, Any],
    agent_id: str = Query(...),
    session_id: str = Query(None),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Execute a platform tool on behalf of Ultravox client-tool invocations."""

    arguments = payload.get("parameters") or payload.get("arguments") or payload
    if not isinstance(arguments, dict):
        arguments = {}

    result = await execute_tool(tool_name, arguments, db, agent_id, session_id)
    return {"result": result}


@router.websocket("/ws/{agent_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    agent_id: str, 
    db: Session = Depends(database.get_db),
    language: str = Query(None),
    voice: str = Query(None),
    caller_id: str = Query(None),
    token: str = Query(None)
):
    # Retrieve token from query param or cookies
    ws_token = token
    if not ws_token:
        ws_token = websocket.query_params.get("token")
    if not ws_token:
        ws_token = websocket.cookies.get("access_token")

    token_data = None
    if ws_token:
        token_data = decode_token(ws_token)

    user = None
    if token_data:
        user = db.query(User).filter(User.id == token_data.user_id).first()

    if not user or not user.is_active:
        await websocket.accept()
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    
    # Fetch agent configuration
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        await websocket.close(code=4004, reason="Agent not found")
        return

    org_id = agent.organization_id
    active_persona, active_tools, active_policy = _resolve_agent_config(agent, db, agent_id)

    if is_ultravox_runtime():
        if not settings.USE_ULTRAVOX_WEBSOCKET_PROXY:
            await websocket.send_json({
                "type": "error",
                "code": "use_ultravox_sdk",
                "message": (
                    "Voice uses the Ultravox client SDK (WebRTC). "
                    "POST /api/v1/orchestrator/ultravox/join/{agent_id} then session.joinCall(joinUrl)."
                ),
            })
            await websocket.close(code=1000, reason="Use Ultravox client SDK")
            return
        try:
            await run_ultravox_proxy_session(
                websocket=websocket,
                agent=agent,
                agent_id=agent_id,
                db=db,
                active_persona=active_persona,
                active_tools=active_tools,
                language=language,
                voice=voice,
                caller_id=caller_id,
            )
        except Exception as e:
            correlation_id = str(uuid.uuid4())[:8]
            logger.exception(f"Ultravox proxy session failed [CID: {correlation_id}]: {e}")
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.send_json({
                    "type": "error", 
                    "message": f"An internal connection error occurred. Reference: {correlation_id}"
                })
                await websocket.close(code=1011, reason="Runtime error")
        return

    # The custom (non-Ultravox) voice runtime has been removed; Ultravox is the
    # sole production voice runtime. Reaching here means Ultravox is not configured.
    await websocket.send_json({
        "type": "error",
        "code": "ultravox_required",
        "message": "Voice runtime unavailable. Configure ULTRAVOX_API_KEY to enable voice.",
    })
    await websocket.close(code=1011, reason="Ultravox not configured")
    return


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(database.get_db)):
    """Experimental: Stateless/REST Chat connector for Text Agents."""
    agent = db.query(models.Agent).filter(models.Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    session_id = request.session_id or str(uuid.uuid4())
    org_id = agent.organization_id
    
    # Initialize basic services dynamically
    from app.services.memory import get_memory_service
    from app.orchestration.agent_orchestrator import AgentOrchestrator
    from app.services.llm.enterprise_llm import EnterpriseLLM
    
    memory_service = get_memory_service(db)
    orchestrator = AgentOrchestrator(db, policy=get_sample_policy())
    llm_service = EnterpriseLLM()
    
    # 1. Update Session / History
    await session_manager.connect()
    session = await session_manager.get_session(session_id)
    if not session:
        await session_manager.create_session(session_id, request.agent_id, request.caller_id, metadata={"channel": "rest"})
        history = []
    else:
        history = await session_manager.get_history(session_id)

    # 2. Intent Detection
    intent, _intent_conf = orchestrator.detect_intent(request.text)
    
    # 3. Generate Response (Non-streaming for REST POST)
    response_text = await llm_service.generate_response(
        request.text, 
        agent.persona, 
        history
    )
    
    # 4. Save & Return
    await session_manager.add_to_history(session_id, "user", request.text)
    await session_manager.add_to_history(session_id, "assistant", response_text)
    
    return ChatResponse(
        session_id=session_id,
        text=response_text,
        agent_id=request.agent_id,
        metadata={"org_id": org_id}
    )

@router.get("/voices")
async def get_voices(primaryLanguage: Optional[str] = None):
    """Proxy to get available voices from the Ultravox voice runtime."""
    if is_ultravox_runtime():
        return await ultravox_service.list_voices(primaryLanguage=primaryLanguage)
    raise HTTPException(status_code=503, detail="Voice runtime unavailable. Configure ULTRAVOX_API_KEY.")
