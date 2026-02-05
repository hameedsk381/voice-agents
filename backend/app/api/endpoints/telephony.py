"""
Telephony Webhooks and Streaming endpoints.
"""
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
import json
import base64
import os
from loguru import logger
from app.core import database
from app.core.config import settings
from app.services.telephony_service import telephony_service
from app.services.stt.deepgram_provider import DeepgramSTT
from app.services.tts.deepgram_provider import DeepgramTTS
from app.services.llm.groq_provider import GroqLLM

from app.services.memory import get_memory_service
from app.services.analytics_service import AnalyticsService
from app.services.monitoring_service import monitoring_service
from app.services.tools.registry import get_tool_schemas, AVAILABLE_TOOLS
from app.orchestration.session_manager import session_manager
from app.orchestration.agent_orchestrator import AgentOrchestrator, AgentContext, ConversationFlow
from app.models.agent import Agent
import uuid
from datetime import datetime

# Initialize backend providers (mirrored from orchestrator.py)
if settings.GROQ_API_KEY:
    llm_service = GroqLLM()
else:
    logger.error("No GROQ_API_KEY found. Groq LLM required.")
    llm_service = GroqLLM() 

stt_service = DeepgramSTT()
tts_service = DeepgramTTS()

router = APIRouter()

@router.post("/voice")
async def twilio_voice_webhook(request: Request, db: Session = Depends(database.get_db)):
    """Twilio hits this when a call is received."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    to_number = form_data.get("To")
    
    # In a real scenario, you'd look up which agent is assigned to this number
    # For MVP, we'll use a default or first active agent
    agent = db.query(Agent).filter(Agent.is_active == True).first()
    agent_id = agent.id if agent else "default"
    
    logger.info(f"Incoming call {call_sid} for agent {agent_id}")
    
    # Public URL where the server is hosted (Twilio needs to reach this)
    host = settings.SERVER_HOST if hasattr(settings, "SERVER_HOST") else os.getenv("SERVER_HOST", "your-ngrok-url.ngrok.app")
    stream_url = f"wss://{host}/api/v1/telephony/stream/{agent_id}"
    
    twiml = telephony_service.generate_twiml_stream(
        stream_url=stream_url,
        welcome_message=f"Hello, I am {agent.name if agent else 'your voice assistant'}. How can I help you today?"
    )
    
    return Response(content=twiml, media_type="application/xml")

@router.websocket("/stream/{agent_id}")
async def twilio_media_stream(websocket: WebSocket, agent_id: str, db: Session = Depends(database.get_db)):
    """WebSocket for Twilio's Bi-directional Media Stream."""
    await websocket.accept()
    logger.info(f"Twilio Media Stream connected for agent {agent_id}")
    
    # Fetch agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        await websocket.close()
        return

    session_id = str(uuid.uuid4())
    stream_sid = None
    
    # Initialize same orchestration logic as Playground
    orchestrator = AgentOrchestrator(db)
    flow = ConversationFlow(session_id=session_id)
    memory_service = get_memory_service(db)
    
    context = AgentContext(
        session_id=session_id,
        history=[],
        current_intent="welcome"
    )
    
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data['event'] == 'start':
                stream_sid = data['start']['streamSid']
                logger.info(f"Twilio Stream started: {stream_sid}")
                
            elif data['event'] == 'media':
                # Twilio sends Mu-law audio
                payload = data['media']['payload']
                audio_bytes = base64.b64decode(payload)
                
                # Full integration would involve real-time streaming to STT
                # For now, we wire the logic pipeline
                # In a live call, we would detect speech end then trigger:
                # response = await orchestrator.get_response(context)
                pass
                
            elif data['event'] == 'stop':
                logger.info(f"Twilio Stream stopped: {stream_sid}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"Twilio Media Stream disconnected")
    except Exception as e:
        logger.error(f"Error in Telephony Orchestration: {e}")

@router.post("/outbound")
async def make_outbound_call(
    to_number: str,
    agent_id: str,
    db: Session = Depends(database.get_db)
):
    """API to trigger a call to a specific number."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        return {"error": "Agent not found"}
        
    # Public URL
    host = os.getenv("SERVER_HOST", "your-ngrok-url.ngrok.app")
    webhook_url = f"https://{host}/api/v1/telephony/voice"
    
    from_number = os.getenv("TWILIO_FROM_NUMBER", "+15550001234")
    
    call_sid = await telephony_service.initiate_outbound_call(
        to_number=to_number,
        from_number=from_number,
        webhook_url=webhook_url
    )
    
    return {"status": "initiated", "call_sid": call_sid}
