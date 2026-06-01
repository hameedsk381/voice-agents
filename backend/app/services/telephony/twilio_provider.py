from typing import Any, Optional

from loguru import logger
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from twilio.twiml.voice_response import Connect, VoiceResponse

from app.services.telephony.base import TelephonyProvider


class TwilioProvider(TelephonyProvider):
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self._client: Optional[Client] = None
        if account_sid and auth_token:
            self._client = Client(account_sid, auth_token)

    @property
    def client(self) -> Optional[Client]:
        return self._client

    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs: Any,
    ) -> Optional[str]:
        if not self._client:
            logger.error("Twilio client not initialized — missing credentials")
            return None
        try:
            call = self._client.calls.create(
                url=webhook_url,
                to=to_number,
                from_=from_number,
            )
            logger.info(f"Twilio outbound call initiated: SID={call.sid}")
            return call.sid
        except TwilioRestException as exc:
            logger.error(f"Twilio outbound call failed: {exc}")
            return None

    def generate_stream_twiml(
        self,
        stream_url: str,
        welcome_message: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        resp = VoiceResponse()
        if welcome_message:
            resp.say(welcome_message, voice=kwargs.get("voice", "Polly.Joanna"))
        connect = Connect()
        connect.stream(url=stream_url)
        resp.append(connect)
        return str(resp)

    def validate_inbound_request(self, request: Any) -> bool:
        return True
