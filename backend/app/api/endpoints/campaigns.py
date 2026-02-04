"""
Campaign API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import csv
import io

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.services.campaign_service import CampaignService

router = APIRouter()

class CampaignCreate(BaseModel):
    name: str
    agent_id: str
    description: Optional[str] = None
    concurrency_limit: Optional[int] = 1

class ContactCreate(BaseModel):
    phone_number: str
    contact_name: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None

@router.post("/", response_model=Dict[str, Any])
async def create_new_campaign(
    data: CampaignCreate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = CampaignService(db)
    campaign = await service.create_campaign(
        name=data.name,
        agent_id=data.agent_id,
        user_id=current_user.id,
        description=data.description,
        concurrency_limit=data.concurrency_limit
    )
    return {"id": campaign.id, "name": campaign.name}

@router.get("/")
async def list_campaigns(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = CampaignService(db)
    return await service.list_campaigns(current_user.id)

@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = CampaignService(db)
    campaign = await service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    stats = await service.get_campaign_stats(campaign_id)
    return {
        "campaign": campaign,
        "stats": stats
    }

@router.post("/{campaign_id}/contacts")
async def add_contacts(
    campaign_id: str,
    contacts: List[ContactCreate],
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = CampaignService(db)
    count = await service.add_contacts(campaign_id, [c.dict() for c in contacts])
    return {"added": count}

@router.post("/{campaign_id}/upload-csv")
async def upload_contacts_csv(
    campaign_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    content = await file.read()
    decoded = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    contacts = []
    for row in csv_reader:
        if 'phone_number' not in row:
            continue
        contacts.append({
            "phone_number": row['phone_number'],
            "contact_name": row.get('name') or row.get('contact_name'),
            "custom_data": {k: v for k, v in row.items() if k not in ['phone_number', 'name', 'contact_name']}
        })
    
    service = CampaignService(db)
    count = await service.add_contacts(campaign_id, contacts)
    return {"added": count}

@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = CampaignService(db)
    campaign = await service.start_campaign(campaign_id)
    return {"status": "started", "campaign": campaign.name}
