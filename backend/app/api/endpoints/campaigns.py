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
from app.services.workflow_service import WorkflowService

router = APIRouter()

class CampaignCreate(BaseModel):
    name: str
    agent_id: str
    description: Optional[str] = None
    concurrency_limit: Optional[int] = 1
    greeting: Optional[str] = None
    workflow_id: Optional[str] = None


class CampaignCallConfigUpdate(BaseModel):
    greeting: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

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
    call_config: Dict[str, Any] = {}
    if data.greeting:
        call_config["greeting"] = data.greeting

    campaign = await service.create_campaign(
        name=data.name,
        agent_id=data.agent_id,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        description=data.description,
        concurrency_limit=data.concurrency_limit,
        call_config=call_config,
        workflow_id=data.workflow_id,
    )
    return {
        "id": campaign.id,
        "name": campaign.name,
        "workflow_id": campaign.workflow_id,
    }

@router.get("/")
async def list_campaigns(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = CampaignService(db)
    return await service.list_campaigns(user_id=current_user.id, organization_id=current_user.organization_id)

@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = CampaignService(db)
    campaign = await service.get_campaign(campaign_id, organization_id=current_user.organization_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    stats = await service.get_campaign_stats(campaign_id)
    wf_service = WorkflowService(db)
    workflow_summary = wf_service.campaign_workflow_summary(
        campaign_id, getattr(campaign, "workflow_id", None)
    )
    return {
        "campaign": campaign,
        "stats": stats,
        "workflow": workflow_summary,
    }

@router.get("/{campaign_id}/contacts")
async def list_campaign_contacts(
    campaign_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = CampaignService(db)
    wf_service = WorkflowService(db)
    campaign = await service.get_campaign(campaign_id, organization_id=current_user.organization_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    contacts = await service.list_contacts(campaign_id)
    result = []
    for c in contacts:
        insts = wf_service.list_instances_for_contact(c.id)
        latest = insts[0] if insts else None
        result.append(
            {
                "id": c.id,
                "phone_number": c.phone_number,
                "contact_name": c.contact_name,
                "status": c.status,
                "session_id": c.session_id,
                "workflow_instance": (
                    {
                        "id": latest.id,
                        "status": latest.status,
                        "current_node_id": latest.current_node_id,
                        "outcome": latest.outcome,
                        "wait_until": latest.wait_until.isoformat()
                        if latest.wait_until
                        else None,
                    }
                    if latest
                    else None
                ),
            }
        )
    return result


@router.post("/{campaign_id}/contacts")
async def add_contacts(
    campaign_id: str,
    contacts: List[ContactCreate],
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = CampaignService(db)
    campaign = await service.get_campaign(campaign_id, organization_id=current_user.organization_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    count = await service.add_contacts(campaign_id, [c.dict() for c in contacts])
    return {"added": count}


@router.post("/{campaign_id}/upload-csv")
async def upload_contacts_csv(
    campaign_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = CampaignService(db)
    campaign = await service.get_campaign(campaign_id, organization_id=current_user.organization_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

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
    
    count = await service.add_contacts(campaign_id, contacts)
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

@router.put("/{campaign_id}/call-config")
async def update_campaign_call_config(
    campaign_id: str,
    body: CampaignCallConfigUpdate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = CampaignService(db)
    patch: Dict[str, Any] = {}
    if body.greeting is not None:
        patch["greeting"] = body.greeting
    if body.context:
        patch.update(body.context)
    campaign = await service.update_call_config(campaign_id, patch, organization_id=current_user.organization_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"call_config": campaign.call_config}


@router.post("/{campaign_id}/dial/{contact_id}")
async def dial_campaign_contact(
    campaign_id: str,
    contact_id: str,
    from_number: Optional[str] = None,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = CampaignService(db)
    try:
        return await service.dial_contact(campaign_id, contact_id, from_number=from_number, organization_id=current_user.organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = CampaignService(db)
    campaign = await service.start_campaign(campaign_id, organization_id=current_user.organization_id)
    return {"status": "started", "campaign": campaign.name}
