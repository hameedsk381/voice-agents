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
