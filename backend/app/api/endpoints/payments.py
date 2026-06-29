"""
Razorpay payment webhooks → collections outcome tracking.

When a payment link generated during a collections call is paid, Razorpay
fires `payment_link.paid` / `payment.captured`. We map it back to the
originating call (via the link `notes.session_id`) and record a
`payment_collected` outcome plus a billable usage event.
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request, HTTPException
from loguru import logger
from sqlalchemy.orm import Session

from app.core import database
from app.models.analytics import CallLog
from app.services.razorpay_service import RazorpayService
from app.services.usage_service import UsageService

router = APIRouter()


def _extract_payment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Pull the relevant entity out of a Razorpay webhook envelope."""
    entity = payload.get("payload", {})
    link = entity.get("payment_link", {}).get("entity", {})
    payment = entity.get("payment", {}).get("entity", {})
    notes = link.get("notes") or payment.get("notes") or {}
    amount_paise = payment.get("amount") or link.get("amount") or 0
    return {
        "notes": notes,
        "amount_rupees": (amount_paise or 0) / 100.0,
        "payment_id": payment.get("id") or link.get("id"),
    }


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(database.get_db)) -> Dict[str, Any]:
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    rzp = RazorpayService()
    # Verify when a webhook secret is configured; skip in mock/dev.
    from app.core.config import settings
    if settings.RAZORPAY_WEBHOOK_SECRET:
        if not rzp.verify_webhook_signature(raw_body, signature):
            raise HTTPException(status_code=403, detail="Invalid Razorpay signature")

    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    event = payload.get("event", "")
    if event not in ("payment_link.paid", "payment.captured"):
        return {"ok": True, "ignored": event}

    info = _extract_payment(payload)
    notes = info["notes"]
    session_id = notes.get("session_id")
    organization_id = notes.get("organization_id") or None
    agent_id = notes.get("agent_id") or None
    amount = info["amount_rupees"]

    if not session_id:
        logger.warning(f"Razorpay {event} without session_id note; cannot attribute.")
        return {"ok": True, "matched": False}

    call_log = db.query(CallLog).filter(CallLog.session_id == session_id).first()
    if call_log:
        call_log.outcome = "SUCCESS"
        call_log.outcome_reason = "payment_collected"
        meta = dict(call_log.metadata_json or {})
        meta["payment_collected"] = {"amount": amount, "payment_id": info["payment_id"]}
        call_log.metadata_json = meta
        db.commit()
        organization_id = organization_id or call_log.organization_id
        agent_id = agent_id or call_log.agent_id

    # Record billable outcome.
    try:
        UsageService(db).record_usage(
            organization_id=organization_id,
            metric="payment_collected",
            quantity=1,
            unit="count",
            session_id=session_id,
            agent_id=agent_id,
            metadata={"amount": amount, "payment_id": info["payment_id"]},
        )
    except Exception as exc:
        logger.error(f"Failed to record payment_collected usage: {exc}")

    logger.info(f"Recorded payment_collected ₹{amount} for session {session_id}")
    return {"ok": True, "matched": bool(call_log), "amount": amount}
