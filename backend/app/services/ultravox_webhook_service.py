"""
Handle Ultravox lifecycle callbacks (call.ended) for Voise AI analytics.
https://docs.ultravox.ai/webhooks/securing-webhooks
"""

import datetime
import hmac
import json
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agent import Agent
from app.models.campaign import CampaignContact, ContactStatus
from app.orchestration.session_manager import session_manager
from app.services.analytics_service import AnalyticsService
from app.services.monitoring_service import monitoring_service
from app.services.ultravox_service import UltravoxService


def verify_ultravox_webhook(request: Request, raw_body: bytes) -> None:
    secret = settings.ULTRAVOX_CALLBACK_SECRET
    if not secret:
        return

    timestamp = request.headers.get("X-Ultravox-Webhook-Timestamp")
    signature_header = request.headers.get("X-Ultravox-Webhook-Signature")
    if not timestamp or not signature_header:
        raise HTTPException(status_code=401, detail="Missing Ultravox webhook signature headers")

    try:
        sent_at = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=datetime.timezone.utc)
        age = datetime.datetime.now(datetime.timezone.utc) - sent_at
        if age > datetime.timedelta(minutes=5):
            raise HTTPException(status_code=401, detail="Ultravox webhook timestamp expired")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid webhook timestamp") from exc

    expected = hmac.new(
        secret.encode(),
        raw_body + timestamp.encode(),
        "sha256",
    ).hexdigest()

    for part in signature_header.split(","):
        if hmac.compare_digest(part.strip(), expected):
            return

    raise HTTPException(status_code=401, detail="Invalid Ultravox webhook signature")


def _messages_to_transcript(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    transcript: List[Dict[str, str]] = []
    for msg in messages or []:
        role = (msg.get("role") or msg.get("speaker") or "unknown").lower()
        if role in ("assistant", "agent"):
            role = "assistant"
        elif role in ("user", "caller"):
            role = "user"
        text = msg.get("text") or msg.get("content") or ""
        if text:
            transcript.append({"role": role, "content": str(text)})
    return transcript


def _parse_duration_seconds(call: Dict[str, Any]) -> float:
    created = call.get("created")
    ended = call.get("ended")
    if not created or not ended:
        return 0.0
    try:
        start = datetime.datetime.fromisoformat(str(created).replace("Z", "+00:00"))
        end = datetime.datetime.fromisoformat(str(ended).replace("Z", "+00:00"))
        return max((end - start).total_seconds(), 0.0)
    except ValueError:
        return 0.0


class UltravoxWebhookService:
    def __init__(self, db: Session):
        self.db = db
        self.ultravox = UltravoxService()

    async def handle_call_ended(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        call = payload.get("call") if isinstance(payload.get("call"), dict) else payload
        call_id = call.get("callId") or call.get("id")
        if not call_id:
            raise HTTPException(status_code=400, detail="Missing callId in webhook payload")

        session_id = await session_manager.resolve_session_id_by_ultravox_call(str(call_id))
        session = await session_manager.get_session(session_id) if session_id else None

        if not session and call.get("metadata"):
            meta = call.get("metadata") or {}
            session_id = meta.get("voise_session_id") or meta.get("session_id")

        if session_id and not session:
            session = await session_manager.get_session(session_id)

        if not session:
            logger.warning(f"Ultravox call.ended for unknown call {call_id}")
            return {"ok": True, "matched": False, "call_id": call_id}

        if session.get("status") == "ended":
            return {"ok": True, "matched": True, "session_id": session_id, "duplicate": True}

        try:
            full_call = await self.ultravox.get_call(str(call_id))
            call = {**call, **full_call}
        except Exception as exc:
            logger.warning(f"Could not fetch Ultravox call {call_id}: {exc}")

        transcript = _messages_to_transcript(call.get("messages") or [])
        if not transcript:
            transcript = await session_manager.get_history(session_id)

        metadata = session.get("metadata") or {}
        end_reason = call.get("endReason") or call.get("endedReason") or "ultravox_ended"
        short_summary = call.get("shortSummary") or call.get("summary")

        await session_manager.end_session(session_id, reason=str(end_reason))
        await session_manager.update_session(session_id, {
            "transcript": transcript,
            "short_summary": short_summary,
        })

        agent = self.db.query(Agent).filter(Agent.id == session["agent_id"]).first()
        session_data = {
            "session_id": session_id,
            "agent_id": session["agent_id"],
            "caller_id": session.get("caller_id"),
            "campaign_id": metadata.get("campaign_id"),
            "org_id": metadata.get("org_id"),
            "start_time": session.get("created_at"),
            "duration": _parse_duration_seconds(call),
            "turns": len(transcript),
            "status": "completed",
            "reason": str(end_reason),
            "transcript": transcript,
        }

        analytics = AnalyticsService(self.db)
        call_log = await analytics.log_call_completion(session_data, agent=agent)

        # Collections: a promise-to-pay captured mid-call deterministically marks
        # the call a success and records a billable outcome (overrides LLM classification).
        collections_outcome = metadata.get("collections_outcome")
        if call_log and collections_outcome and collections_outcome.get("type") == "promise_to_pay":
            call_log.outcome = "SUCCESS"
            call_log.outcome_reason = "promise_to_pay"
            meta = dict(call_log.metadata_json or {})
            meta["promise_to_pay"] = collections_outcome
            call_log.metadata_json = meta
            self.db.commit()
            try:
                from app.services.usage_service import UsageService
                UsageService(self.db).record_usage(
                    organization_id=metadata.get("org_id"),
                    metric="promise_to_pay_captured",
                    quantity=1,
                    unit="count",
                    session_id=session_id,
                    agent_id=session["agent_id"],
                    metadata=collections_outcome,
                )
            except Exception as exc:
                logger.error(f"Failed to record promise_to_pay usage: {exc}")

        contact_id = metadata.get("campaign_contact_id")
        if contact_id:
            contact = self.db.query(CampaignContact).filter(
                CampaignContact.id == contact_id
            ).first()
            if contact:
                contact.status = ContactStatus.COMPLETED.value
                contact.session_id = session_id
                self.db.commit()

        await monitoring_service.broadcast_event(session_id, "call_ended", {
            "call_id": call_id,
            "end_reason": end_reason,
            "short_summary": short_summary,
            "outcome": call_log.outcome if call_log else None,
        })

        workflow_advanced = {"advanced": 0, "skipped": True}
        if contact_id:
            from app.services.workflow_service import WorkflowService

            wf_service = WorkflowService(self.db)
            workflow_advanced = await wf_service.advance_on_call_ended(
                contact_id=str(contact_id),
                analytics_outcome=call_log.outcome if call_log else None,
                end_reason=str(end_reason),
                short_summary=short_summary,
                session_id=session_id,
                call_id=str(call_id),
                organization_id=metadata.get("org_id"),
            )

        logger.info(f"Finalized session {session_id} from Ultravox call.ended ({call_id})")
        return {
            "ok": True,
            "matched": True,
            "session_id": session_id,
            "call_id": call_id,
            "outcome": call_log.outcome if call_log else None,
            "workflow": workflow_advanced,
        }
