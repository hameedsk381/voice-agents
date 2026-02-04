"""
Marketplace API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.services.marketplace_service import MarketplaceService

router = APIRouter()

@router.get("/templates")
async def get_templates(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = MarketplaceService(db)
    return service.get_templates()

@router.post("/install/{template_id}")
async def install_template(
    template_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = MarketplaceService(db)
    try:
        agent = await service.install_template(template_id, current_user.id)
        return {"status": "success", "agent_id": agent.id, "agent_name": agent.name}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
