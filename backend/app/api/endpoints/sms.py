"""SMS endpoints — send, inbound webhook, and status callback."""

from typing import Any, Dict, Optional
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.services.sms_service import SmsService

router = APIRouter()


class SmsSendRequest(BaseModel):
    to_phone: str
    message: str
    workflow_instance_id: Optional[str] = None


@router.post("/send")
async def send_sms(
    payload: SmsSendRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
) -> Dict[str, Any]:
    svc = SmsService(db)
    return svc.send_message(
        to_phone=payload.to_phone,
        message=payload.message,
        workflow_instance_id=payload.workflow_instance_id,
        organization_id=current_user.organization_id,
    )


@router.post("/webhook")
async def sms_status_callback(request: Request, db: Session = Depends(database.get_db)):
    """Twilio status callback — updates SmsMessage delivery status."""
    body = await request.body()
    params = {k: v[0] for k, v in parse_qs(body.decode()).items()}
    svc = SmsService(db)
    sig = request.headers.get("X-Twilio-Signature", "")
    if sig and not svc.validate_webhook(str(request.url), params, sig):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    svc.handle_status_callback(params)
    return Response(content="", media_type="text/xml")


@router.post("/inbound")
async def sms_inbound(request: Request, db: Session = Depends(database.get_db)):
    """Twilio inbound SMS — handles opt-out/opt-in keywords and logs messages."""
    body = await request.body()
    params = {k: v[0] for k, v in parse_qs(body.decode()).items()}
    svc = SmsService(db)
    sig = request.headers.get("X-Twilio-Signature", "")
    if sig and not svc.validate_webhook(str(request.url), params, sig):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    result = svc.handle_inbound(params)
    logger.info(f"Inbound SMS action: {result.get('action')}")
    return Response(content="", media_type="text/xml")
