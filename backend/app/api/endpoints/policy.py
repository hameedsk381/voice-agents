from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.schemas.policy_rule import PolicyRuleCreate, PolicyRuleUpdate, PolicyRuleResponse, PolicyEvaluationResult
from app.services.policy_service import PolicyService

router = APIRouter()

@router.get("/rules", response_model=List[PolicyRuleResponse])
async def list_rules(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """List all policy rules, ordered by priority (highest first)."""
    service = PolicyService(db)
    return service.list_rules(organization_id=current_user.organization_id if hasattr(current_user, 'organization_id') else None)

@router.get("/rules/{rule_id}", response_model=PolicyRuleResponse)
async def get_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = PolicyService(db)
    rule = service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Policy rule not found")
    return rule

@router.post("/rules", response_model=PolicyRuleResponse, status_code=201)
async def create_rule(
    data: PolicyRuleCreate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Create a new policy rule."""
    service = PolicyService(db)
    org_id = current_user.organization_id if hasattr(current_user, 'organization_id') else None
    return service.create_rule(data.model_dump(), organization_id=org_id)

@router.put("/rules/{rule_id}", response_model=PolicyRuleResponse)
async def update_rule(
    rule_id: str,
    data: PolicyRuleUpdate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = PolicyService(db)
    rule = service.update_rule(rule_id, data.model_dump(exclude_none=True))
    if not rule:
        raise HTTPException(status_code=404, detail="Policy rule not found")
    return rule

@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = PolicyService(db)
    if not service.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Policy rule not found")
    return {"status": "deleted"}
