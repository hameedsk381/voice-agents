"""Cryptographic audit chain service — append-only, tamper-evident, compliance-ready."""
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from app.models.compliance import AuditLog
from app.services.identity_service import IdentityService


class AuditService:
    """Append-only audit chain with cryptographic signatures for every turn."""

    def __init__(self, db: Session):
        self.db = db
        self.identity_service = IdentityService(db)

    def _compute_entry_hash(self, entry_data: Dict[str, Any]) -> str:
        """SHA-256 hash of the canonical entry data for chaining."""
        serialized = json.dumps(entry_data, sort_keys=True, default=str).encode()
        return hashlib.sha256(serialized).hexdigest()

    def append(
        self,
        session_id: str,
        agent_id: str,
        turn_index: float,
        user_message: str,
        ai_response: str,
        is_compliant: bool,
        violations: List[Dict[str, Any]],
        risk_score: float,
        organization_id: Optional[str] = None,
        state_name: Optional[str] = None,
    ) -> AuditLog:
        """Create a new audit entry with cryptographic chaining and agent signature."""

        # Find the previous chain head for this agent
        previous_entry = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.agent_id == agent_id,
                AuditLog.chain_head == True,
            )
            .order_by(AuditLog.created_at.desc())
            .first()
        )

        # Mark old head as non-head
        if previous_entry:
            previous_entry.chain_head = False

        now = datetime.utcnow()
        created_at_str = now.isoformat()
        turn_index = float(turn_index)
        risk_score = float(risk_score)

        entry_data = {
            "session_id": session_id,
            "agent_id": agent_id,
            "turn_index": turn_index,
            "user_message": user_message,
            "ai_response": ai_response,
            "is_compliant": is_compliant,
            "violations": violations,
            "risk_score": risk_score,
            "organization_id": organization_id,
            "state_name": state_name,
            "created_at": created_at_str,
        }

        # Compute previous_hash — SHA-256 of the last entry's canonical data
        previous_hash = None
        if previous_entry:
            prev_data = {
                "session_id": previous_entry.session_id,
                "agent_id": previous_entry.agent_id,
                "turn_index": previous_entry.turn_index,
                "user_message": previous_entry.user_message,
                "ai_response": previous_entry.ai_response,
                "is_compliant": previous_entry.is_compliant,
                "violations": previous_entry.violations or [],
                "risk_score": previous_entry.risk_score,
                "organization_id": previous_entry.organization_id,
                "state_name": previous_entry.state_name,
                "created_at": previous_entry.created_at.isoformat() if previous_entry.created_at else "",
            }
            previous_hash = self._compute_entry_hash(prev_data)

        entry_data["previous_hash"] = previous_hash

        # Sign the entry with the agent's identity
        signature = self.identity_service.sign_action(agent_id, entry_data)

        audit_log = AuditLog(
            session_id=session_id,
            agent_id=agent_id,
            turn_index=turn_index,
            user_message=user_message,
            ai_response=ai_response,
            is_compliant=is_compliant,
            violations=violations,
            risk_score=risk_score,
            organization_id=organization_id,
            state_name=state_name,
            previous_hash=previous_hash,
            signature=signature,
            chain_head=True,
            created_at=now,
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

    def verify_chain(self, agent_id: str) -> Dict[str, Any]:
        """Walk the entire audit chain for an agent and verify cryptographic integrity."""
        entries = (
            self.db.query(AuditLog)
            .filter(AuditLog.agent_id == agent_id)
            .order_by(AuditLog.created_at.asc())
            .all()
        )

        if not entries:
            return {"agent_id": agent_id, "verified": True, "total_entries": 0, "errors": []}

        errors = []
        prev_entry_hash = None

        for entry in entries:
            entry_data = {
                "session_id": entry.session_id,
                "agent_id": entry.agent_id,
                "turn_index": entry.turn_index,
                "user_message": entry.user_message,
                "ai_response": entry.ai_response,
                "is_compliant": entry.is_compliant,
                "violations": entry.violations or [],
                "risk_score": entry.risk_score,
                "organization_id": entry.organization_id,
                "state_name": entry.state_name,
                "created_at": entry.created_at.isoformat() if entry.created_at else "",
            }

            stored_prev_hash = entry.previous_hash

            # Chain link check: stored previous_hash must match computed hash of previous entry
            if prev_entry_hash is None and stored_prev_hash is not None:
                errors.append(f"Entry {entry.id}: first entry has non-null previous_hash")
            elif prev_entry_hash is not None:
                if stored_prev_hash != prev_entry_hash:
                    errors.append(
                        f"Entry {entry.id} (turn {entry.turn_index}): hash chain broken — "
                        f"expected {prev_entry_hash}, got {stored_prev_hash}"
                    )

            # Signature verification: sign(entry_data + previous_hash)
            verify_data = {**entry_data, "previous_hash": stored_prev_hash}
            if entry.signature:
                valid = self.identity_service.verify_action(
                    agent_id, verify_data, entry.signature
                )
                if not valid:
                    errors.append(
                        f"Entry {entry.id} (turn {entry.turn_index}): signature invalid"
                    )

            # Compute hash of this entry for the next iteration's chain check
            prev_entry_hash = self._compute_entry_hash(entry_data)

        # Check the chain_head flag — exactly one should be True
        heads = [e for e in entries if e.chain_head]
        if len(heads) != 1:
            errors.append(f"Chain integrity: expected 1 head, found {len(heads)}")

        return {
            "agent_id": agent_id,
            "verified": len(errors) == 0,
            "total_entries": len(entries),
            "errors": errors,
        }

    def export_for_compliance(
        self,
        agent_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate a compliance-ready audit report."""
        q = self.db.query(AuditLog).filter(AuditLog.agent_id == agent_id)
        if start:
            q = q.filter(AuditLog.created_at >= start)
        if end:
            q = q.filter(AuditLog.created_at <= end)
        entries = q.order_by(AuditLog.created_at.asc()).all()

        chain_verification = self.verify_chain(agent_id)

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "period": {
                "start": start.isoformat() if start else None,
                "end": end.isoformat() if end else None,
            },
            "total_entries": len(entries),
            "chain_verified": chain_verification["verified"],
            "chain_errors": chain_verification["errors"],
            "entries": [
                {
                    "id": e.id,
                    "session_id": e.session_id,
                    "turn_index": e.turn_index,
                    "is_compliant": e.is_compliant,
                    "risk_score": e.risk_score,
                    "violations": e.violations or [],
                    "signature": e.signature,
                    "previous_hash": e.previous_hash,
                    "created_at": e.created_at.isoformat() if e.created_at else "",
                }
                for e in entries
            ],
        }

    def get_chain_status(self, agent_id: str) -> Dict[str, Any]:
        """Quick status of the latest chain entry."""
        head = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.agent_id == agent_id,
                AuditLog.chain_head == True,
            )
            .first()
        )
        return {
            "agent_id": agent_id,
            "has_chain": head is not None,
            "total_entries": self.db.query(AuditLog).filter(
                AuditLog.agent_id == agent_id
            ).count(),
            "last_entry_at": head.created_at.isoformat() if head else None,
            "head_signed": head.signature is not None if head else False,
        }
