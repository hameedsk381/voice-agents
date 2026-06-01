"""
Legacy TelephonyService — delegates to the provider factory.
Kept for backwards compatibility with existing endpoint imports.
"""
from typing import Any, Optional

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from loguru import logger

from app.core.config import settings
from app.services.telephony.factory import get_telephony_provider


class TelephonyService:
    """Legacy service — delegates to the configured TelephonyProvider."""

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID or None
        self.auth_token = settings.TWILIO_AUTH_TOKEN or None
        self._twilio_client: Optional[Client] = None
        if self.account_sid and self.auth_token:
            self._twilio_client = Client(self.account_sid, self.auth_token)

    def get_twilio_client(self) -> Optional[Client]:
        """Return the Twilio client if configured (legacy compat)."""
        return self._twilio_client

    def generate_twiml_stream(self, stream_url: str, welcome_message: str = None) -> str:
        """Generate TwiML to connect a call to a media stream."""
        resp = VoiceResponse()
        if welcome_message:
            resp.say(welcome_message)
        connect = Connect()
        connect.stream(url=stream_url)
        resp.append(connect)
        return str(resp)

    async def initiate_outbound_call(self, to_number: str, from_number: str, webhook_url: str) -> Optional[str]:
        """Triggers an outbound call via the configured provider."""
        try:
            provider = get_telephony_provider()
            return await provider.initiate_outbound_call(
                to_number=to_number,
                from_number=from_number,
                webhook_url=webhook_url,
            )
        except Exception as exc:
            logger.error(f"Outbound call failed: {exc}")
            return None


telephony_service = TelephonyService()
