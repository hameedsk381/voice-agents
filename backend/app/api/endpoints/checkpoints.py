"""REST endpoints for durable checkpoint management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.services.checkpoint_service import CheckpointService

router = APIRouter()


@router.get("/sessions")
async def list_checkpointed_sessions(
    agent_id: str = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """List sessions with active checkpoints (candidates for recovery)."""
    service = CheckpointService(db)
    return service.list_sessions(agent_id=agent_id, limit=limit)


@router.get("/sessions/{session_id}")
async def get_session_checkpoint(
    session_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Get the latest checkpoint state summary for a session."""
    service = CheckpointService(db)
    state = service.resume_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="No checkpoint found for this session")
    cp = service.load_latest(session_id)
    return {
        "session_id": session_id,
        "turn_index": cp.turn_index if cp else 0,
        "created_at": cp.created_at.isoformat() if cp and cp.created_at else None,
        "state_summary": {
            "history_length": len(state.get("history", [])),
            "current_state": state.get("current_state"),
            "turn_count": state.get("turn_count", 0),
            "token_count": state.get("token_count", 0),
        },
    }


@router.delete("/sessions/{session_id}")
async def delete_session_checkpoints(
    session_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Remove all checkpoints for a completed session."""
    service = CheckpointService(db)
    deleted = service.delete_session_checkpoints(session_id)
    return {"deleted": deleted, "session_id": session_id}
