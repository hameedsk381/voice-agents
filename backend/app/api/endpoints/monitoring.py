"""
Monitoring API endpoints.
Provides real-time call tracking and supervisor tools.
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Any
import asyncio
from app.orchestration.session_manager import session_manager
from app.services.monitoring_service import monitoring_service
from app.core.deps import require_manager, get_current_user_required
from app.models.user import User

router = APIRouter()

@router.get("/active-sessions")
async def get_active_sessions(
    current_user: User = Depends(require_manager)
):
    """List all currently active sessions."""
    return await session_manager.get_all_active_sessions()

@router.get("/session/{session_id}")
async def get_session_details(
    session_id: str,
    current_user: User = Depends(require_manager)
):
    """Get full details of a specific session."""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.websocket("/stream/all")
async def stream_all_sessions(
    websocket: WebSocket
):
    """WebSocket to monitor all active sessions globally."""
    await websocket.accept()
    
    # Optional: Auth check here if needed via token in query param
    
    try:
        async for event in monitoring_service.subscribe_to_all():
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Monitoring stream error: {e}")

@router.websocket("/stream/{session_id}")
async def stream_session(
    websocket: WebSocket,
    session_id: str
):
    """WebSocket to monitor a specific session in real-time."""
    await websocket.accept()
    
    # Send current state first
    session = await session_manager.get_session(session_id)
    if session:
        await websocket.send_json({
            "type": "initial_state",
            "data": session
        })
    
    try:
        async for event in monitoring_service.subscribe_to_session(session_id):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Session monitoring stream error: {e}")
