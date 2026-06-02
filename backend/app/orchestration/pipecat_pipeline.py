import asyncio
import os
import uuid
import logging
from typing import Optional, Dict, Any
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.services.groq import GroqLLMService
from pipecat.transport.livekit.transport import LiveKitTransport, LiveKitTransportParams
from pipecat.frames.frames import EndFrame, TextFrame
from pipecat.processors.aggregators.llm_response import LLMAssistantResponseAggregator, LLMUserResponseAggregator
from app.core.database import SessionLocal
from app.orchestration.tool_executor import execute_tool
from app.services.tools.registry import AVAILABLE_TOOLS

logger = logging.getLogger(__name__)

# Cache API keys
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secret")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def generate_livekit_token(room_name: str, participant_name: str) -> str:
    """Generate a token for the frontend to join the room."""
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.with_identity(participant_name).with_name(participant_name).with_grants(
        api.VideoGrants(room_join=True, room=room_name)
    )
    return token.to_jwt()

async def run_pipecat_agent(
    room_name: str, 
    system_prompt: str, 
    greeting: Optional[str] = None,
    agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    active_tools: Optional[list] = None
):
    """
    Spins up a Pipecat pipeline using LiveKit Transport.
    This runs entirely locally and handles STT (Deepgram), LLM (Groq), TTS (ElevenLabs).
    """
    logger.info(f"Starting Pipecat Agent in room {room_name}")
    
    transport = LiveKitTransport(
        LiveKitTransportParams(
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
            url=LIVEKIT_URL,
            room=room_name,
            token_identity="agent",
        )
    )

    stt = DeepgramSTTService(
        api_key=DEEPGRAM_API_KEY,
        model="nova-2",
        language="en-US"
    )

    llm = GroqLLMService(
        api_key=GROQ_API_KEY,
        model="llama3-8b-8192"
    )

    tts = ElevenLabsTTSService(
        api_key=ELEVENLABS_API_KEY,
        voice_id="EXAVITQu4vr4xnSDxMaL"  # Default generic voice
    )

    task = None  # Declare early for closure

    # Register dynamic tools
    if active_tools and agent_id and session_id:
        for tool_dict in active_tools:
            tool_name = tool_dict.get("name")
            if tool_name in AVAILABLE_TOOLS:
                tool_obj = AVAILABLE_TOOLS[tool_name]
                
                async def make_wrapper(t_name):
                    async def wrapper(args: dict, _llm=None):
                        if task:
                            await task.queue_frames([TextFrame("Let me pull that up for you...")])
                        
                        db = SessionLocal()
                        try:
                            logger.info(f"Pipecat executing tool: {t_name} with args {args}")
                            res = await execute_tool(t_name, args, db, agent_id, session_id)
                            return str(res["result"])
                        finally:
                            db.close()
                    return wrapper
                
                # Register with LLM Service using tool's schema
                wrapper_func = await make_wrapper(tool_name)
                # Setting name of function for registration
                wrapper_func.__name__ = tool_name
                
                llm.register_function(
                    tool_name,
                    wrapper_func,
                    parameters=tool_obj.parameters
                )
                logger.info(f"Registered tool {tool_name} with Pipecat GroqLLMService")

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]
    
    # Context aggregator helps manage conversation state
    tma_in = LLMUserResponseAggregator(messages)
    tma_out = LLMAssistantResponseAggregator(messages)

    pipeline = Pipeline([
        transport.input(),   # WebRTC Audio In
        stt,                 # Speech to Text
        tma_in,              # Add user text to LLM context
        llm,                 # Run LLM
        tts,                 # Text to Speech
        transport.output(),  # WebRTC Audio Out
        tma_out              # Add assistant text to LLM context
    ])

    task = PipelineTask(
        pipeline,
        PipelineParams(
            allow_interruptions=True,
            enable_metrics=True
        )
    )

    # If greeting provided, have the agent speak first
    @transport.event_handler("on_participant_connected")
    async def on_participant_connected(transport, participant):
        logger.info(f"Participant {participant.identity} connected")
        if greeting:
            # Send initial frame through TTS
            await task.queue_frames([TextFrame(greeting)])

    @transport.event_handler("on_participant_disconnected")
    async def on_participant_disconnected(transport, participant):
        logger.info(f"Participant {participant.identity} disconnected")
        # Terminate pipeline when user leaves
        await task.queue_frames([EndFrame()])

    runner = PipelineRunner()
    
    try:
        await runner.run(task)
    except Exception as e:
        logger.error(f"Pipecat pipeline error: {e}")
    finally:
        logger.info("Pipecat pipeline finished.")
