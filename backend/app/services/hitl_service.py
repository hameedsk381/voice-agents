"""
Human-in-the-Loop (HITL) Service for managing pending actions.
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.models.hitl import PendingAction, ApprovalStatus

class HITLService:
    def __init__(self, db: Session):
        self.db = db

    async def create_pending_action(
        self, 
        session_id: str, 
        agent_id: str, 
        action_type: str, 
        description: str, 
        payload: Dict[str, Any]
    ) -> PendingAction:
        action = PendingAction(
            session_id=session_id,
            agent_id=agent_id,
            action_type=action_type,
            description=description,
            payload=payload,
            status=ApprovalStatus.PENDING.value
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    async def list_pending_actions(self, status: str = "pending") -> List[PendingAction]:
        return self.db.query(PendingAction)\
            .filter(PendingAction.status == status)\
            .order_by(desc(PendingAction.created_at)).all()

    async def process_action(
        self, 
        action_id: str, 
        user_id: str, 
        decision: str, 
        feedback: str = None
    ) -> Optional[PendingAction]:
        action = self.db.query(PendingAction).filter(PendingAction.id == action_id).first()
        if not action:
            return None
            
        action.status = decision
        action.processed_by = user_id
        action.processed_at = datetime.utcnow()
        action.feedback = feedback
        
        self.db.commit()
        self.db.refresh(action)
        return action
