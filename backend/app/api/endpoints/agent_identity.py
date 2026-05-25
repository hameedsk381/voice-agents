"""REST endpoints for agent identity management and audit chain verification."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.services.identity_service import IdentityService
from app.services.audit_service import AuditService

router = APIRouter()


class IdentityResponse(BaseModel):
    id: str
    agent_id: str
    public_key: str
    certificate_pem: Optional[str] = None
    spiffe_id: Optional[str] = None
    key_version: str
    is_active: bool
    created_at: str = ""
    rotated_at: Optional[str] = None


def _identity_to_response(identity) -> IdentityResponse:
    """Convert AgentIdentity ORM to response with proper datetime serialization."""
    return IdentityResponse(
        id=identity.id,
        agent_id=identity.agent_id,
        public_key=identity.public_key,
        certificate_pem=identity.certificate_pem,
        spiffe_id=identity.spiffe_id,
        key_version=identity.key_version,
        is_active=identity.is_active,
        created_at=identity.created_at.isoformat() if identity.created_at else "",
        rotated_at=identity.rotated_at.isoformat() if identity.rotated_at else None,
    )


@router.post("/identities/{agent_id}", response_model=IdentityResponse)
async def issue_identity(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Issue a new cryptographic identity (Ed25519 keypair + SPIFFE cert) for an agent."""
    svc = IdentityService(db)
    identity = svc.issue_agent_identity(agent_id)
    logger.info(f"Identity issued for agent {agent_id} by user {current_user.id}")
    return _identity_to_response(identity)


@router.get("/identities/{agent_id}", response_model=IdentityResponse)
async def get_identity(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Get the active identity for an agent."""
    svc = IdentityService(db)
    identity = svc.get_identity(agent_id)
    if not identity:
        raise HTTPException(status_code=404, detail="No active identity for this agent")
    return _identity_to_response(identity)


@router.post("/identities/{agent_id}/rotate", response_model=IdentityResponse)
async def rotate_identity(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Rotate an agent's keypair — deactivates old key, issues new one."""
    svc = IdentityService(db)
    new = svc.rotate_keys(agent_id)
    if not new:
        raise HTTPException(status_code=404, detail="Agent not found")
    logger.info(f"Identity rotated for agent {agent_id} by user {current_user.id}")
    return _identity_to_response(new)


# --- Audit Chain Endpoints ---


class ChainStatusResponse(BaseModel):
    agent_id: str
    has_chain: bool
    total_entries: int
    last_entry_at: Optional[str] = None
    head_signed: bool = False


class ChainVerifyResponse(BaseModel):
    agent_id: str
    verified: bool
    total_entries: int
    errors: list


@router.get("/audit/{agent_id}/status", response_model=ChainStatusResponse)
async def audit_chain_status(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Get the status of the audit chain for an agent."""
    svc = AuditService(db)
    return svc.get_chain_status(agent_id)


@router.get("/audit/{agent_id}/verify", response_model=ChainVerifyResponse)
async def verify_audit_chain(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Verify the cryptographic integrity of the entire audit chain for an agent."""
    svc = AuditService(db)
    return svc.verify_chain(agent_id)


@router.get("/audit/{agent_id}/export")
async def export_audit_chain(
    agent_id: str,
    start: Optional[str] = Query(None, description="ISO datetime start"),
    end: Optional[str] = Query(None, description="ISO datetime end"),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Export the audit chain as a compliance-ready report."""
    svc = AuditService(db)
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None
    return svc.export_for_compliance(agent_id, start=start_dt, end=end_dt)
