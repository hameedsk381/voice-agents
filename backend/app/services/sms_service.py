"""
SMS messaging service using Twilio SMS API.

Mirrors WhatsAppService structure:
- Send messages via Twilio SMS
- Track delivery via status callbacks
- Handle inbound SMS and opt-out keywords
- Redis-backed rate limiting and consent tracking
- Full audit trail via SmsMessage DB model
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from twilio.rest import Client
from twilio.request_validator import RequestValidator
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.workflow import SmsMessage


SMS_TEMPLATES: Dict[str, str] = {
    "payment_reminder": (
        "Hi {{customer_name}}, your payment of {{currency}} {{outstanding_amount}} is due. "
        "Please pay at your earliest convenience. Reply STOP to opt out."
    ),
    "appointment_confirm": (
        "Hi {{customer_name}}, your appointment is confirmed for {{appointment_date}}. "
        "Reply 1 to confirm, 2 to reschedule. Reply STOP to opt out."
    ),
    "lead_followup": (
        "Hi {{customer_name}}, thanks for your enquiry. "
        "Our team will call you shortly. Reply STOP to opt out."
    ),
    "order_update": (
        "Hi {{customer_name}}, your order {{order_id}} will be delivered by {{delivery_time}}. "
        "Reply STOP to opt out."
    ),
}


def _render_template(template_name: str, context: Dict[str, Any]) -> str:
    template_str = SMS_TEMPLATES.get(template_name, template_name)

    def replace_var(match: re.Match) -> str:
        key = match.group(1)
        val = context.get(key)
        return str(val) if val is not None else match.group(0)

    return re.sub(r"\{\{(\w+)\}\}", replace_var, template_str)


class SmsConsentTracker:
    OPT_IN_PREFIX = "sms:optin:"
    RATE_LIMIT_PREFIX = "sms:ratelimit:"

    def __init__(self):
        self._redis = None

    @property
    def redis(self):
        if self._redis is None:
            import redis as redis_mod
            self._redis = redis_mod.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
            )
        return self._redis

    def is_opted_in(self, phone: str) -> bool:
        val = self.redis.get(f"{self.OPT_IN_PREFIX}{phone}")
        return val == "1"

    def set_opted_in(self, phone: str) -> None:
        self.redis.set(f"{self.OPT_IN_PREFIX}{phone}", "1")

    def set_opted_out(self, phone: str) -> None:
        self.redis.set(f"{self.OPT_IN_PREFIX}{phone}", "0")

    def can_send(self, phone: str) -> Tuple[bool, str]:
        if settings.SMS_OPTIN_REQUIRED and not self.is_opted_in(phone):
            return False, "user_has_not_opted_in"
        if settings.SMS_RATE_LIMIT_PER_HOUR > 0:
            key = f"{self.RATE_LIMIT_PREFIX}{phone}"
            count = int(self.redis.get(key) or 0)
            if count >= settings.SMS_RATE_LIMIT_PER_HOUR:
                return False, "rate_limit_exceeded"
            self.redis.incr(key)
            self.redis.expire(key, 3600)
        return True, "ok"


class SmsService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_PHONE_NUMBER
        self.is_configured = bool(self.account_sid and self.auth_token and self.from_number)
        self.consent = SmsConsentTracker()
        self._validator: Optional[RequestValidator] = None

        if self.is_configured:
            self.client = Client(self.account_sid, self.auth_token)

    @property
    def validator(self) -> Optional[RequestValidator]:
        if self._validator is None and self.auth_token:
            self._validator = RequestValidator(self.auth_token)
        return self._validator

    def send_message(
        self,
        to_phone: str,
        message: str,
        *,
        workflow_instance_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return self._mock_send(to_phone, message, workflow_instance_id, organization_id)

        can_send, reason = self.consent.can_send(to_phone)
        if not can_send:
            logger.warning(f"SMS blocked for {to_phone}: {reason}")
            self._write_audit(to_phone, message, workflow_instance_id, organization_id, status="blocked", error=reason)
            return {"status": "blocked", "reason": reason}

        try:
            kwargs: Dict[str, Any] = {
                "body": message,
                "from_": self.from_number,
                "to": to_phone,
            }
            if settings.SMS_WEBHOOK_URL:
                kwargs["status_callback"] = settings.SMS_WEBHOOK_URL

            msg = self.client.messages.create(**kwargs)
            self._write_audit(
                to_phone, message, workflow_instance_id, organization_id,
                status=msg.status or "sent",
                provider_sid=msg.sid,
            )
            logger.info(f"SMS sent to {to_phone}, SID: {msg.sid}")
            return {"status": msg.status, "message_sid": msg.sid}

        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {e}")
            self._write_audit(to_phone, message, workflow_instance_id, organization_id, status="failed", error=str(e))
            return {"status": "failed", "error_message": str(e)}

    def send_template(
        self,
        to_phone: str,
        template_name: str,
        context: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        message = _render_template(template_name, context)
        return self.send_message(to_phone, message, **kwargs)

    def validate_webhook(self, request_url: str, params: Dict[str, str], signature_header: str) -> bool:
        if not self.validator:
            return False
        return self.validator.validate(request_url, params, signature_header)

    def handle_status_callback(self, payload: Dict[str, Any]) -> None:
        if not self.db:
            return
        message_sid = payload.get("MessageSid")
        new_status = payload.get("MessageStatus")
        if not message_sid or not new_status:
            return
        entry = self.db.query(SmsMessage).filter(
            SmsMessage.provider_message_sid == message_sid
        ).first()
        if entry:
            entry.status = new_status
            if new_status == "delivered":
                entry.delivered_at = datetime.utcnow()
            self.db.commit()
            logger.debug(f"SMS status update: {message_sid} -> {new_status}")

    def handle_inbound(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        from_phone = payload.get("From", "")
        body = (payload.get("Body") or "").strip().upper()
        message_sid = payload.get("MessageSid", "")

        if body in ("STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"):
            self.consent.set_opted_out(from_phone)
            logger.info(f"SMS opt-out from {from_phone}")
            self._write_audit(from_phone, body, status="received", provider_sid=message_sid)
            return {"action": "opted_out"}

        if body in ("START", "UNSTOP", "YES", "SUBSCRIBE"):
            self.consent.set_opted_in(from_phone)
            logger.info(f"SMS opt-in from {from_phone}")
            self._write_audit(from_phone, body, status="received", provider_sid=message_sid)
            return {"action": "opted_in"}

        self._write_audit(from_phone, body, status="received", provider_sid=message_sid)
        return {"action": "received", "from": from_phone, "body": body, "message_sid": message_sid}

    def _mock_send(self, to_phone, message, workflow_instance_id, organization_id) -> Dict[str, Any]:
        logger.info(f"[MOCK SMS] to={to_phone} msg='{message[:120]}'")
        self._write_audit(to_phone, message, workflow_instance_id, organization_id, status="simulated", provider_sid="mock_sid")
        return {"status": "simulated", "message_sid": "mock_sid"}

    def _write_audit(
        self,
        to_phone: str,
        message: str,
        workflow_instance_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        status: str = "queued",
        provider_sid: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        if not self.db:
            return
        entry = SmsMessage(
            workflow_instance_id=workflow_instance_id,
            organization_id=organization_id,
            to_phone=to_phone,
            message_body=message[:500] if message else None,
            status=status,
            provider_message_sid=provider_sid,
            error_message=error,
            sent_at=datetime.utcnow() if status in ("sent", "simulated") else None,
        )
        self.db.add(entry)
        self.db.commit()
