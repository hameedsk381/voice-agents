"""
WhatsApp messaging service with real Twilio WhatsApp Business API integration.

Capabilities:
- Send templated and free-form messages via Twilio WhatsApp API
- Manage Twilio Content API templates (create, list, submit for approval)
- Track delivery status via webhook callbacks with signature verification
- Handle inbound WhatsApp messages (opt-in, opt-out, replies)
- Enforce opt-in/opt-out consent tracking in Redis
- Optional per-contact rate limiting (24h session window)
- Full audit trail via WhatsAppMessage DB model
"""

import os
import re
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import parse_qs

from twilio.rest import Client
from twilio.request_validator import RequestValidator
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.workflow import WhatsAppMessage

# ─── Built-in message templates with variable substitution ──────────────────

MESSAGE_TEMPLATES: Dict[str, str] = {
    "payment_reminder": (
        "Dear {{customer_name}}, this is a reminder that your payment of "
        "{{currency}} {{outstanding_amount}} is due. Please pay at your earliest "
        "convenience to avoid any late fees. Reply STOP to opt out."
    ),
    "lead_nurture": (
        "Hi {{customer_name}}, thank you for your interest in our services. "
        "Our team will reach out to you shortly. "
        "In the meantime, feel free to visit our website for more information."
    ),
    "appointment_confirm": (
        "Dear {{customer_name}}, your appointment is confirmed for "
        "{{appointment_date}}. Please arrive 10 minutes early. "
        "Reply 1 to confirm, 2 to reschedule, or 3 to cancel."
    ),
    "payment_received": (
        "Dear {{customer_name}}, thank you! We have received your payment of "
        "{{currency}} {{outstanding_amount}}. Your account is now up to date."
    ),
    "escalation_notice": (
        "Dear {{customer_name}}, your request has been escalated to our "
        "{{escalated_to}} team for priority handling. "
        "We will keep you updated on the progress."
    ),
    "collection_final": (
        "URGENT: Dear {{customer_name}}, this is your final notice for "
        "{{currency}} {{outstanding_amount}} overdue by {{aging_days}} days. "
        "Please pay immediately to avoid escalation. Reply STOP to opt out."
    ),
    "satisfaction_survey": (
        "Hi {{customer_name}}, we value your feedback! How would you rate "
        "your recent experience with us? Reply 1-5 (5 = excellent)."
    ),
}


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """Render a WhatsApp message template with {{variable}} substitution."""
    template_str = MESSAGE_TEMPLATES.get(template_name, template_name)

    def replace_var(match: re.Match) -> str:
        key = match.group(1)
        val = context.get(key)
        if val is None:
            return match.group(0)
        return str(val)

    return re.sub(r"\{\{(\w+)\}\}", replace_var, template_str)


# ─── Opt-in/opt-out tracking in Redis ──────────────────────────────────────


class WhatsAppConsentTracker:
    """Tracks WhatsApp opt-in/opt-out status per phone number using Redis."""

    OPT_IN_PREFIX = "whatsapp:optin:"
    RATE_LIMIT_PREFIX = "whatsapp:ratelimit:"
    SESSION_TTL_HOURS = 24

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
        if settings.WHATSAPP_OPTIN_REQUIRED and not self.is_opted_in(phone):
            return False, "user_has_not_opted_in"
        if settings.WHATSAPP_RATE_LIMIT_PER_HOUR > 0:
            key = f"{self.RATE_LIMIT_PREFIX}{phone}"
            count = int(self.redis.get(key) or 0)
            if count >= settings.WHATSAPP_RATE_LIMIT_PER_HOUR:
                return False, "rate_limit_exceeded"
            self.redis.incr(key)
            self.redis.expire(key, 3600)
        return True, "ok"

    def start_session(self, phone: str) -> None:
        key = f"{self.OPT_IN_PREFIX}session:{phone}"
        self.redis.setex(key, self.SESSION_TTL_HOURS * 3600, "1")

    def has_active_session(self, phone: str) -> bool:
        return bool(self.redis.get(f"{self.OPT_IN_PREFIX}session:{phone}"))


# ─── Main WhatsApp service ─────────────────────────────────────────────────


class WhatsAppService:
    """Production WhatsApp service using Twilio WhatsApp Business API."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.sender = settings.TWILIO_WHATSAPP_SENDER
        self.status_callback_url = settings.TWILIO_STATUS_CALLBACK_URL
        self.is_configured = bool(self.account_sid and self.auth_token)
        self.consent = WhatsAppConsentTracker()
        self._validator: Optional[RequestValidator] = None

        if self.is_configured:
            self.client = Client(self.account_sid, self.auth_token)

    @property
    def validator(self) -> Optional[RequestValidator]:
        if self._validator is None and self.auth_token:
            self._validator = RequestValidator(self.auth_token)
        return self._validator

    # ── Sending ───────────────────────────────────────────────────────────

    def send_message(
        self,
        to_phone: str,
        message: str,
        *,
        workflow_instance_id: Optional[str] = None,
        template_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message via Twilio WhatsApp Business API.

        Supports:
        - Text messages (free-form or pre-rendered)
        - Media attachments (images, documents, audio)
        - Template-based messages for proactive outreach
        - Automatic opt-in enforcement and rate limiting
        - Full audit trail
        """
        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"

        # Opt-in check
        if not self.is_configured:
            logger.error(f"WhatsApp not sent to {to_phone}: Twilio is not configured")
            self._write_audit(
                to_phone, message, template_name, workflow_instance_id, organization_id,
                status="failed", error="whatsapp_not_configured",
            )
            return {"status": "failed", "error": "whatsapp_not_configured"}

        can_send, reason = self.consent.can_send(to_phone)
        if not can_send:
            logger.warning(f"WhatsApp blocked for {to_phone}: {reason}")
            self._write_audit(to_phone, message, template_name, workflow_instance_id, organization_id, status="blocked", error=reason)
            return {"status": "blocked", "reason": reason}

        try:
            kwargs: Dict[str, Any] = {
                "from_": self.sender,
                "to": to_phone,
            }

            if media_url:
                kwargs["body"] = message
                kwargs["media_url"] = [media_url]
            else:
                kwargs["body"] = message

            if self.status_callback_url:
                kwargs["status_callback"] = self.status_callback_url

            msg = self.client.messages.create(**kwargs)
            self.consent.start_session(to_phone)

            self._write_audit(
                to_phone, message, template_name,
                workflow_instance_id, organization_id,
                status=msg.status or "sent",
                provider_sid=msg.sid,
            )

            logger.info(f"WhatsApp sent to {to_phone}, SID: {msg.sid}, status: {msg.status}")
            return {"status": msg.status, "message_sid": msg.sid, "error_message": msg.error_message}

        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {to_phone}: {e}")
            self._write_audit(to_phone, message, template_name, workflow_instance_id, organization_id, status="failed", error=str(e))
            return {"status": "failed", "error_message": str(e)}

    def send_template(
        self,
        to_phone: str,
        template_name: str,
        context: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        """Render and send a built-in template."""
        message = render_template(template_name, context)
        return self.send_message(to_phone, message, template_name=template_name, **kwargs)

    def send_with_media(
        self,
        to_phone: str,
        message: str,
        media_url: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send a WhatsApp message with a media attachment."""
        return self.send_message(to_phone, message, media_url=media_url, **kwargs)

    # ── Template management (Twilio Content API) ──────────────────────────

    def create_content_template(
        self,
        name: str,
        body: str,
        language: str = "en",
        category: str = "MARKETING",
    ) -> Dict[str, Any]:
        """
        Create a WhatsApp message template via the Twilio Content API.

        Templates must be submitted and approved by Meta before they can
        be used for proactive (business-initiated) messaging.
        """
        if not self.is_configured:
            logger.error(f"WhatsApp template '{name}' not created: Twilio is not configured")
            return {"status": "failed", "error": "whatsapp_not_configured", "template_name": name}

        try:
            content = self.client.content.v1.contents.create(
                friendly_name=name,
                language=language,
                types={
                    "twilio/text": {
                        "body": body,
                    }
                },
            )
            logger.info(f"Twilio Content template created: {content.sid}")
            return {
                "status": "created",
                "template_sid": content.sid,
                "template_name": name,
                "language": language,
            }
        except Exception as e:
            logger.error(f"Failed to create Content template '{name}': {e}")
            return {"status": "error", "error_message": str(e)}

    def list_content_templates(self) -> List[Dict[str, Any]]:
        """List all WhatsApp content templates."""
        if not self.is_configured:
            return []
        try:
            contents = self.client.content.v1.contents.list()
            return [
                {
                    "sid": c.sid,
                    "name": c.friendly_name,
                    "language": c.language,
                    "status": c.status,
                    "created_at": str(c.date_created) if c.date_created else None,
                }
                for c in contents
            ]
        except Exception as e:
            logger.error(f"Failed to list Content templates: {e}")
            return []

    # ── Delivery status ───────────────────────────────────────────────────

    def check_delivery_status(self, message_sid: str) -> Dict[str, Any]:
        """Check delivery status via Twilio API."""
        if not self.is_configured:
            return {"status": "unknown", "message_sid": message_sid}
        try:
            msg = self.client.messages(message_sid).fetch()
            return {
                "status": msg.status,
                "message_sid": msg.sid,
                "error_message": msg.error_message,
                "date_sent": str(msg.date_sent) if msg.date_sent else None,
            }
        except Exception as e:
            return {"status": "error", "error_message": str(e)}

    # ── Status callback webhook ───────────────────────────────────────────

    def validate_webhook(self, request_url: str, params: Dict[str, str], signature_header: str) -> bool:
        """Validate Twilio webhook signature."""
        if not self.validator:
            return False
        return self.validator.validate(request_url, params, signature_header)

    def handle_status_callback(self, payload: Dict[str, Any]) -> None:
        """Process status callback and update audit trail."""
        if not self.db:
            return
        message_sid = payload.get("MessageSid")
        new_status = payload.get("MessageStatus")
        if not message_sid or not new_status:
            return
        entry = self.db.query(WhatsAppMessage).filter(
            WhatsAppMessage.provider_message_sid == message_sid
        ).first()
        if entry:
            entry.status = new_status
            if new_status == "delivered":
                entry.delivered_at = datetime.utcnow()
            self.db.commit()
            logger.debug(f"WhatsApp status update: {message_sid} -> {new_status}")

    # ── Inbound message handling ──────────────────────────────────────────

    def handle_inbound(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an inbound WhatsApp message (text, opt-in, opt-out, reply).

        - "STOP" / "UNSTOP" keywords handle opt-out/opt-in automatically.
        - All other messages are logged for processing.
        """
        from_phone = payload.get("From", "")
        body = (payload.get("Body") or "").strip().upper()
        message_sid = payload.get("MessageSid", "")
        num_media = int(payload.get("NumMedia", 0))

        # Opt-out handling
        if body in ("STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"):
            self.consent.set_opted_out(from_phone)
            logger.info(f"WhatsApp opt-out from {from_phone}")
            self._write_audit(from_phone, body, "opt_out", provider_sid=message_sid, status="received")
            return {"action": "opted_out", "message": "You have been unsubscribed."}

        # Opt-in handling
        if body in ("START", "UNSTOP", "YES", "SUBSCRIBE"):
            self.consent.set_opted_in(from_phone)
            logger.info(f"WhatsApp opt-in from {from_phone}")
            self._write_audit(from_phone, body, "opt_in", provider_sid=message_sid, status="received")
            return {"action": "opted_in", "message": "You have been subscribed."}

        # Media message
        media_info = []
        if num_media > 0:
            for i in range(num_media):
                media_info.append({
                    "url": payload.get(f"MediaUrl{i}"),
                    "type": payload.get(f"MediaContentType{i}"),
                })

        self._write_audit(from_phone, body, "inbound_reply", provider_sid=message_sid, status="received")

        return {
            "action": "received",
            "from": from_phone,
            "body": body,
            "media": media_info,
            "message_sid": message_sid,
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    def _write_audit(
        self,
        to_phone: str,
        message: str,
        template: Optional[str] = None,
        workflow_instance_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        status: str = "queued",
        provider_sid: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        if not self.db:
            return
        entry = WhatsAppMessage(
            workflow_instance_id=workflow_instance_id,
            organization_id=organization_id,
            to_phone=to_phone,
            template=template,
            message_body=message[:500] if message else None,
            status=status,
            provider_message_sid=provider_sid,
            error_message=error,
            sent_at=datetime.utcnow() if status == "sent" else None,
        )
        self.db.add(entry)
        self.db.commit()
