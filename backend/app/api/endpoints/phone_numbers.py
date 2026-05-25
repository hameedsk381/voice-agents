"""
Phone number provisioning endpoints — search, purchase, list, configure, release.
"""
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.models.phone_number import PhoneNumber
from app.services.phone_number_service import PhoneNumberService

router = APIRouter()


class PurchaseRequest(BaseModel):
    phone_number: str
    friendly_name: Optional[str] = None
    voice_url: Optional[str] = None


class ConfigureRequest(BaseModel):
    voice_url: str


@router.get("/available")
async def search_available(
    country_code: str = Query("IN"),
    area_code: Optional[str] = Query(None),
    contains: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user_required),
):
    """Search for available phone numbers to purchase."""
    svc = PhoneNumberService()
    try:
        results = svc.search_available(
            country_code=country_code,
            area_code=area_code,
            contains=contains,
            limit=limit,
        )
        return {"results": results, "count": len(results)}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/purchase")
async def purchase_number(
    data: PurchaseRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Purchase a phone number and assign to your organization."""
    svc = PhoneNumberService(db)
    try:
        result = svc.purchase(
            phone_number=data.phone_number,
            friendly_name=data.friendly_name,
            voice_url=data.voice_url,
            organization_id=current_user.organization_id,
        )
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/owned")
async def list_owned_numbers(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """List phone numbers owned by your organization."""
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="No organization assigned")
    svc = PhoneNumberService(db)
    return {"numbers": svc.list_organization_numbers(current_user.organization_id)}


@router.post("/{number_id}/configure")
async def configure_number(
    number_id: str,
    data: ConfigureRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Configure the voice webhook URL for a phone number."""
    svc = PhoneNumberService(db)
    try:
        record = db.query(PhoneNumber).filter(
            PhoneNumber.id == number_id,
            PhoneNumber.organization_id == current_user.organization_id,
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="Phone number not found")
        result = svc.configure_voice_url(record.twilio_sid, data.voice_url)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{number_id}")
async def release_number(
    number_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Release a phone number back to Twilio."""
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="No organization assigned")
    svc = PhoneNumberService(db)
    try:
        svc.release(number_id, current_user.organization_id)
        return {"status": "released"}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
async def sync_numbers(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Sync Twilio-owned numbers into the local database."""
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="No organization assigned")
    svc = PhoneNumberService(db)
    try:
        count = svc.sync_from_twilio(current_user.organization_id)
        return {"synced": count}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))



