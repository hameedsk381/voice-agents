import json
from typing import Any, Optional

from loguru import logger

from app.services.telephony.base import TelephonyProvider


class VonageProvider(TelephonyProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        application_id: Optional[str] = None,
        private_key: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.application_id = application_id
        self.private_key = private_key
        self._client: Optional[Any] = None
        if api_key and api_secret and application_id:
            try:
                from vonage import Auth, Voice
                from vonage_voice import VoiceResult

                auth = Auth(api_key=api_key, api_secret=api_secret)
                self._client = Voice(auth)
                self._client.application_id = application_id
                if private_key:
                    self._client.private_key = private_key
            except ImportError:
                logger.warning("vonage SDK not installed — install 'vonage' package")

    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs: Any,
    ) -> Optional[str]:
        if not self._client:
            logger.error("Vonage client not initialized — missing credentials")
            return None
        try:
            ncco_url = webhook_url
            if "?" in webhook_url:
                ncco_url = f"{webhook_url}&format=ncco"
            else:
                ncco_url = f"{webhook_url}?format=ncco"

            response = self._client.create_call({
                "to": [{"type": "phone", "number": to_number}],
                "from": {"type": "phone", "number": from_number},
                "ncco": [{"action": "talk", "text": "Connecting you to our AI assistant. Please wait."}],
                "answer_url": [ncco_url],
            })
            call_uuid = None
            if hasattr(response, "call_uuid"):
                call_uuid = response.call_uuid
            elif isinstance(response, dict):
                call_uuid = response.get("call_uuid") or response.get("uuid")
            logger.info(f"Vonage outbound call initiated: UUID={call_uuid}")
            return call_uuid
        except Exception as exc:
            logger.error(f"Vonage outbound call failed: {exc}")
            return None

    def generate_stream_twiml(
        self,
        stream_url: str,
        **kwargs: Any,
    ) -> str:
        ncco = [
            {
                "action": "connect",
                "endpoint": [
                    {
                        "type": "websocket",
                        "uri": stream_url,
                        "content-type": "audio/l16;rate=16000",
                    }
                ],
            }
        ]
        return json.dumps(ncco)

    def validate_inbound_request(self, request: Any) -> bool:
        return True
