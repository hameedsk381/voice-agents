from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import database
from app.core.deps import get_current_user_required, require_admin
from app.models.user import User
from app.models.tenant import Organization

router = APIRouter()


class OrgUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class MemberRoleUpdate(BaseModel):
    role: str


class InviteMemberRequest(BaseModel):
    email: str
    role: str = "viewer"


@router.get("/me")
async def get_my_organization(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="No organization assigned")
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {
        "id": org.id,
        "name": org.name,
        "domain": org.domain,
        "subscription_plan": org.subscription_plan,
        "is_active": org.is_active,
        "settings": org.settings or {},
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "updated_at": org.updated_at.isoformat() if org.updated_at else None,
    }


@router.put("/me")
async def update_my_organization(
    data: OrgUpdate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="No organization assigned")
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if data.name is not None:
        org.name = data.name
    if data.settings is not None:
        current_settings = org.settings or {}
        current_settings.update(data.settings)
        org.settings = current_settings
    db.commit()
    db.refresh(org)
    return {
        "id": org.id,
        "name": org.name,
        "domain": org.domain,
        "subscription_plan": org.subscription_plan,
        "is_active": org.is_active,
        "settings": org.settings or {},
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "updated_at": org.updated_at.isoformat() if org.updated_at else None,
    }


@router.post("/me/onboarding/complete")
async def complete_onboarding(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="No organization assigned")
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    current_settings = org.settings or {}
    current_settings["onboarding_completed"] = True
    org.settings = current_settings
    db.commit()
    return {"status": "ok", "onboarding_completed": True}


@router.get("/me/members")
async def list_org_members(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="No organization assigned")
    members = db.query(User).filter(
        User.organization_id == current_user.organization_id
    ).all()
    return [
        {
            "id": m.id,
            "email": m.email,
            "full_name": m.full_name,
            "role": m.role,
            "is_active": m.is_active,
            "is_superuser": m.is_superuser,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "last_login": m.last_login.isoformat() if m.last_login else None,
        }
        for m in members
    ]


@router.put("/me/members/{user_id}/role")
async def update_member_role(
    user_id: str,
    data: MemberRoleUpdate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="No organization assigned")
    if current_user.role != "admin" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    member = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.role = data.role
    db.commit()
    return {"id": member.id, "email": member.email, "role": member.role}
