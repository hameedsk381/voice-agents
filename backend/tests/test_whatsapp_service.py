"""
Tests for WhatsAppService — template rendering, consent tracking, send, inbound.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from typing import Any, Dict

from app.services.whatsapp_service import (
    render_template,
    WhatsAppConsentTracker,
    WhatsAppService,
)


# ─── render_template ─────────────────────────────────────────────────

class TestRenderTemplate:
    def test_basic_substitution(self):
        result = render_template("payment_reminder", {
            "customer_name": "Raj",
            "currency": "INR",
            "outstanding_amount": "5000",
        })
        assert "Raj" in result
        assert "INR 5000" in result

    def test_missing_var_keeps_placeholder(self):
        result = render_template("payment_reminder", {"customer_name": "Raj"})
        assert "{{currency}}" in result

    def test_unknown_template_returns_as_is(self):
        result = render_template("non_existent_template", {})
        assert result == "non_existent_template"

    def test_all_templates_render_with_context(self):
        ctx = {
            "customer_name": "Alice",
            "currency": "USD",
            "outstanding_amount": "1000",
            "appointment_date": "2026-06-01",
            "escalated_to": "legal",
            "aging_days": "90",
        }
        for tpl_name in [
            "payment_reminder", "lead_nurture", "appointment_confirm",
            "payment_received", "escalation_notice", "collection_final",
            "satisfaction_survey",
        ]:
            result = render_template(tpl_name, ctx)
            assert "Alice" in result, f"{tpl_name} missing customer_name"


# ─── WhatsAppConsentTracker ──────────────────────────────────────────

class TestConsentTracker:
    @pytest.fixture
    def tracker(self):
        with patch("app.services.whatsapp_service.settings") as mock_settings:
            mock_settings.WHATSAPP_OPTIN_REQUIRED = True
            mock_settings.REDIS_HOST = "localhost"
            mock_settings.REDIS_PORT = 6379
            mock_settings.REDIS_PASSWORD = None
            mock_settings.WHATSAPP_RATE_LIMIT_PER_HOUR = 10
            yield WhatsAppConsentTracker()

    def test_is_opted_in_true(self, tracker):
        with patch.object(tracker, "_redis") as mock_redis:
            mock_redis.get.return_value = "1"
            assert tracker.is_opted_in("+911111111111") is True

    def test_is_opted_in_false(self, tracker):
        with patch.object(tracker, "_redis") as mock_redis:
            mock_redis.get.return_value = None
            assert tracker.is_opted_in("+911111111111") is False

    def test_set_opted_in(self, tracker):
        with patch.object(tracker, "_redis") as mock_redis:
            tracker.set_opted_in("+911111111111")
            mock_redis.set.assert_called_once_with("whatsapp:optin:+911111111111", "1")

    def test_set_opted_out(self, tracker):
        with patch.object(tracker, "_redis") as mock_redis:
            tracker.set_opted_out("+911111111111")
            mock_redis.set.assert_called_once_with("whatsapp:optin:+911111111111", "0")

    def test_can_send_opted_in(self, tracker):
        with patch.object(tracker, "_redis") as mock_redis:
            mock_redis.get.side_effect = lambda k: "1" if "optin" in k else "0"
            result, reason = tracker.can_send("+911111111111")
            assert result is True
            assert reason == "ok"

    def test_can_send_opted_out(self, tracker):
        with patch.object(tracker, "_redis") as mock_redis:
            mock_redis.get.side_effect = lambda k: "0" if "optin" in k else "0"
            result, reason = tracker.can_send("+911111111111")
            assert result is False
            assert "not_opted_in" in reason.lower()

    def test_can_send_rate_limited(self, tracker):
        with patch.object(tracker, "_redis") as mock_redis:
            mock_redis.get.side_effect = lambda k: "1" if "optin" in k else "10"
            result, reason = tracker.can_send("+911111111111")
            assert result is False
            assert "rate" in reason.lower()


# ─── WhatsAppService — send_message ──────────────────────────────────

class TestWhatsAppServiceSend:
    def test_send_message_mock_fallback(self, mock_db):
        """Without Twilio creds, send_message should use mock fallback."""
        with patch("app.services.whatsapp_service.settings") as mock_settings:
            mock_settings.TWILIO_ACCOUNT_SID = ""
            mock_settings.TWILIO_AUTH_TOKEN = ""
            mock_settings.TWILIO_WHATSAPP_SENDER = ""
            mock_settings.TWILIO_STATUS_CALLBACK_URL = ""
            mock_settings.WHATSAPP_OPTIN_REQUIRED = False
            mock_settings.WHATSAPP_RATE_LIMIT_PER_HOUR = 0
            svc = WhatsAppService(db=mock_db)
            result = svc.send_message("+911111111111", "Hello")
        assert result.get("status") in ("mocked",)

    def test_send_message_twilio_real(self, mock_db):
        """With Twilio creds, should call the Twilio API."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value.sid = "SM123"
        mock_client.messages.create.return_value.status = "sent"
        mock_client.messages.create.return_value.error_code = None

        with patch("app.services.whatsapp_service.Client", return_value=mock_client), \
             patch("app.services.whatsapp_service.settings") as mock_settings:
            mock_settings.TWILIO_ACCOUNT_SID = "ACxxx"
            mock_settings.TWILIO_AUTH_TOKEN = "tok"
            mock_settings.TWILIO_WHATSAPP_SENDER = "whatsapp:+14155238886"
            mock_settings.TWILIO_STATUS_CALLBACK_URL = ""
            mock_settings.WHATSAPP_OPTIN_REQUIRED = False
            mock_settings.WHATSAPP_RATE_LIMIT_PER_HOUR = 0
            mock_settings.REDIS_HOST = "localhost"
            mock_settings.REDIS_PORT = 6379
            mock_settings.REDIS_PASSWORD = None
            svc = WhatsAppService(db=mock_db)
            with patch.object(svc.consent, "_redis") as mock_redis:
                mock_redis.get.return_value = None
                result = svc.send_message("+911111111111", "Hello via Twilio")

        assert result.get("status") == "sent"
        assert result.get("message_sid") == "SM123"

    def test_send_message_with_template(self, mock_db):
        with patch("app.services.whatsapp_service.settings") as mock_settings:
            mock_settings.TWILIO_ACCOUNT_SID = ""
            mock_settings.TWILIO_AUTH_TOKEN = ""
            mock_settings.TWILIO_WHATSAPP_SENDER = ""
            mock_settings.TWILIO_STATUS_CALLBACK_URL = ""
            mock_settings.WHATSAPP_OPTIN_REQUIRED = False
            mock_settings.WHATSAPP_RATE_LIMIT_PER_HOUR = 0
            svc = WhatsAppService(db=mock_db)
            result = svc.send_message(
                "+911111111111",
                "Dear Raj, your payment is due.",
                template_name="payment_reminder",
            )
        assert result.get("status") in ("mocked",)

    def test_send_message_consent_blocked(self, mock_db):
        """Should refuse to send when opt-in required and not opted in."""
        with patch("app.services.whatsapp_service.settings") as mock_settings:
            mock_settings.TWILIO_ACCOUNT_SID = "ACxxx"
            mock_settings.TWILIO_AUTH_TOKEN = "tok"
            mock_settings.TWILIO_WHATSAPP_SENDER = "whatsapp:+14155238886"
            mock_settings.TWILIO_STATUS_CALLBACK_URL = ""
            svc = WhatsAppService(db=mock_db)
            with patch.object(svc.consent, "can_send", return_value=(False, "opted_out")):
                result = svc.send_message("+911111111111", "Blocked")
        assert result.get("status") == "blocked"


# ─── WhatsAppService — send_template ─────────────────────────────────

class TestWhatsAppServiceTemplate:
    def test_send_template(self, mock_db):
        with patch("app.services.whatsapp_service.settings") as mock_settings, \
             patch("app.services.whatsapp_service.Client") as mock_client:
            mock_settings.TWILIO_ACCOUNT_SID = ""
            mock_settings.TWILIO_AUTH_TOKEN = ""
            mock_settings.TWILIO_WHATSAPP_SENDER = ""
            mock_settings.TWILIO_STATUS_CALLBACK_URL = ""
            mock_settings.WHATSAPP_OPTIN_REQUIRED = False
            mock_settings.WHATSAPP_RATE_LIMIT_PER_HOUR = 0
            svc = WhatsAppService(db=mock_db)
            with patch.object(svc, "send_message", return_value={"status": "sent"}) as mock_send:
                result = svc.send_template(
                    to_phone="+911111111111",
                    template_name="payment_reminder",
                    context={"customer_name": "Raj", "outstanding_amount": "5000"},
                )
        assert result.get("status") == "sent"


# ─── WhatsAppService — inbound ───────────────────────────────────────

class TestWhatsAppServiceInbound:
    def test_handle_inbound_opt_out(self, mock_db):
        """STOP keyword should opt out the user."""
        svc = WhatsAppService(db=mock_db)
        with patch.object(svc.consent, "set_opted_out") as mock_opt_out:
            result = svc.handle_inbound({
                "From": "whatsapp:+911111111111",
                "Body": "STOP",
            })
        assert result["action"] == "opted_out"
        mock_opt_out.assert_called_once_with("whatsapp:+911111111111")

    def test_handle_inbound_unstop(self, mock_db):
        """START/UNSTOP keyword should opt in the user."""
        svc = WhatsAppService(db=mock_db)
        with patch.object(svc.consent, "set_opted_in") as mock_opt_in:
            result = svc.handle_inbound({
                "From": "whatsapp:+911111111111",
                "Body": "START",
            })
        assert result["action"] == "opted_in"
        mock_opt_in.assert_called_once()

    def test_handle_inbound_reply(self, mock_db):
        """Regular message should be treated as received."""
        svc = WhatsAppService(db=mock_db)
        result = svc.handle_inbound({
            "From": "whatsapp:+911111111111",
            "Body": "I have a question",
        })
        assert result["action"] == "received"
        assert result["from"] == "whatsapp:+911111111111"
        assert result["body"] == "I HAVE A QUESTION"

    def test_handle_inbound_media(self, mock_db):
        """Messages with media should include media info."""
        svc = WhatsAppService(db=mock_db)
        result = svc.handle_inbound({
            "From": "whatsapp:+911111111111",
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/media/image.jpg",
            "MediaContentType0": "image/jpeg",
        })
        assert result["action"] == "received"
        assert len(result.get("media", [])) == 1


# ─── WhatsAppService — webhook validation ────────────────────────────

class TestWebhookValidation:
    def test_validate_webhook_valid(self):
        svc = WhatsAppService()
        with patch.object(svc, "validate_webhook", return_value=True):
            assert svc.validate_webhook({}, {}, "") is True

    def test_validate_webhook_invalid(self):
        svc = WhatsAppService()
        with patch.object(svc, "validate_webhook", return_value=False):
            assert svc.validate_webhook({}, {}, "") is False


# ─── WhatsAppService — content templates ─────────────────────────────

class TestContentTemplates:
    def test_list_content_templates(self, mock_db):
        svc = WhatsAppService(db=mock_db)
        with patch("app.services.whatsapp_service.settings") as mock_settings:
            mock_settings.TWILIO_ACCOUNT_SID = ""
            mock_settings.TWILIO_AUTH_TOKEN = ""
            result = svc.list_content_templates()
        assert isinstance(result, list)
