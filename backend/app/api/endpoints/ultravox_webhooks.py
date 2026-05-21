"""
Ultravox lifecycle webhooks (call.ended → analytics + campaign updates).
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core import database
from app.services.ultravox_webhook_service import (
    UltravoxWebhookService,
    verify_ultravox_webhook,
)

router = APIRouter()


@router.post("/call-ended")
async def ultravox_call_ended_webhook(
    request: Request,
    db: Session = Depends(database.get_db),
) -> Dict[str, Any]:
    """
    Receives Ultravox call.ended lifecycle callbacks.
    Configure via ULTRAVOX_CALLBACK_SECRET and public SERVER_HOST (ngrok in dev).
    """
    raw_body = await request.body()
    verify_ultravox_webhook(request, raw_body)

    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    service = UltravoxWebhookService(db)
    return await service.handle_call_ended(payload)
