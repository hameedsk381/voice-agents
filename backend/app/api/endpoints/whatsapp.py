"""WhatsApp webhook endpoints — status callback and inbound message handling."""

from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from loguru import logger
from sqlalchemy.orm import Session

from app.core import database
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()


@router.post("/webhook")
async def whatsapp_status_callback(request: Request, db: Session = Depends(database.get_db)):
    """Twilio status callback — updates WhatsAppMessage delivery status."""
    body = await request.body()
    params = {k: v[0] for k, v in parse_qs(body.decode()).items()}
    svc = WhatsAppService(db)
    sig = request.headers.get("X-Twilio-Signature", "")
    if sig and not svc.validate_webhook(str(request.url), params, sig):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    svc.handle_status_callback(params)
    return Response(content="", media_type="text/xml")


@router.post("/inbound")
async def whatsapp_inbound(request: Request, db: Session = Depends(database.get_db)):
    """Twilio inbound WhatsApp — handles opt-out/opt-in and logs messages."""
    body = await request.body()
    params = {k: v[0] for k, v in parse_qs(body.decode()).items()}
    svc = WhatsAppService(db)
    sig = request.headers.get("X-Twilio-Signature", "")
    if sig and not svc.validate_webhook(str(request.url), params, sig):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    result = svc.handle_inbound(params)
    logger.info(f"Inbound WhatsApp action: {result.get('action')}")
    return Response(content="", media_type="text/xml")
