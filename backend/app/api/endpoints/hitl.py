"""
HITL API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.services.hitl_service import HITLService

router = APIRouter()

class ActionDecision(BaseModel):
    decision: str # approved or rejected
    feedback: Optional[str] = None

class InterventionRequest(BaseModel):
    mode: str # takeover, whisper, ai_only
    
class HumanResponse(BaseModel):
    text: str

@router.get("/pending")
async def get_pending_actions(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = HITLService(db)
    return await service.list_pending_actions()

@router.post("/{action_id}/decide")
async def decide_action(
    action_id: str,
    data: ActionDecision,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = HITLService(db)
    action = await service.process_action(
        action_id=action_id,
        user_id=current_user.id,
        decision=data.decision,
        feedback=data.feedback
    )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    return {"status": "processed", "decision": action.status}

@router.post("/sessions/{session_id}/takeover")
async def start_takeover(
    session_id: str,
    data: InterventionRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = HITLService(db)
    intervention = await service.start_intervention(
        session_id=session_id,
        user_id=current_user.id,
        mode=data.mode
    )
    return {"status": "intervention_active", "mode": intervention.mode}

@router.post("/sessions/{session_id}/release")
async def stop_takeover(
    session_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required)
):
    service = HITLService(db)
    success = await service.stop_intervention(session_id)
    return {"status": "intervention_stopped" if success else "no_active_intervention"}

@router.post("/sessions/{session_id}/respond")
async def send_human_response(
    session_id: str,
    data: HumanResponse,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Send text from human agent to user via session Redis channel."""
    from app.orchestration.session_manager import session_manager
    # We'll use the session_manager to publish a message that the orchestrator loop picks up
    await session_manager.publish_human_message(session_id, data.text)
    return {"status": "message_sent"}
