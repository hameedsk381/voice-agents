"""Durable execution via Postgres-backed checkpoints.

Saves a full snapshot of session state after every completed turn,
enabling the system to resume a call after a crash or restart without
losing conversation history or task progress.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger
from app.models.checkpoint import CallCheckpoint


class CheckpointService:
    """Manages durable checkpoints for call session resilience."""

    def __init__(self, db: Session):
        self.db = db

    def save(
        self,
        session_id: str,
        agent_id: str,
        turn_index: int,
        state: Dict[str, Any],
        summary: Optional[str] = None,
    ) -> CallCheckpoint:
        """Persist a full session snapshot after a completed turn."""
        cp = CallCheckpoint(
            session_id=session_id,
            agent_id=agent_id,
            turn_index=turn_index,
            state_json=state,
            conversation_summary=summary,
        )
        self.db.add(cp)
        self.db.commit()
        self.db.refresh(cp)
        logger.debug(f"Checkpoint saved for session {session_id} turn {turn_index}")
        return cp

    def load_latest(self, session_id: str) -> Optional[CallCheckpoint]:
        """Retrieve the most recent checkpoint for a session."""
        return (
            self.db.query(CallCheckpoint)
            .filter(CallCheckpoint.session_id == session_id)
            .order_by(desc(CallCheckpoint.turn_index))
            .first()
        )

    def list_sessions(
        self,
        agent_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List active sessions that have checkpoints, grouped by session.

        Returns the latest checkpoint summary for each session so callers
        can decide which sessions to recover.
        """
        q = (
            self.db.query(
                CallCheckpoint.session_id,
                CallCheckpoint.agent_id,
                CallCheckpoint.turn_index,
                CallCheckpoint.conversation_summary,
                CallCheckpoint.created_at,
            )
            .distinct(CallCheckpoint.session_id)
            .order_by(CallCheckpoint.session_id, desc(CallCheckpoint.turn_index))
        )
        if agent_id:
            q = q.filter(CallCheckpoint.agent_id == agent_id)
        rows = q.limit(limit).all()
        return [
            {
                "session_id": r.session_id,
                "agent_id": r.agent_id,
                "last_turn": r.turn_index,
                "summary": r.conversation_summary,
                "last_checkpoint_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    def resume_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load the latest checkpoint and return its state_json.

        Returns None if no checkpoint exists for the session.
        The caller is responsible for restoring any in-memory objects
        (WebSocket, LLM instance, etc.) that cannot be serialised.
        """
        cp = self.load_latest(session_id)
        if cp is None:
            return None
        return cp.state_json

    def delete_session_checkpoints(self, session_id: str) -> int:
        """Remove all checkpoints for a completed / abandoned session.

        Returns the number of deleted rows.
        """
        deleted = (
            self.db.query(CallCheckpoint)
            .filter(CallCheckpoint.session_id == session_id)
            .delete()
        )
        self.db.commit()
        if deleted:
            logger.info(f"Deleted {deleted} checkpoint(s) for session {session_id}")
        return deleted
