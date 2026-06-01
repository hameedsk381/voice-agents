from typing import Any, Optional

from loguru import logger

from app.services.telephony.base import TelephonyProvider


class PlivoProvider(TelephonyProvider):
    def __init__(
        self,
        auth_id: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> None:
        self.auth_id = auth_id
        self.auth_token = auth_token
        self._client: Optional[Any] = None
        if auth_id and auth_token:
            try:
                from plivo import RestClient
                self._client = RestClient(auth_id=auth_id, auth_token=auth_token)
            except ImportError:
                logger.warning("plivo SDK not installed — install 'plivo' package")

    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs: Any,
    ) -> Optional[str]:
        if not self._client:
            logger.error("Plivo client not initialized — missing credentials")
            return None
        try:
            response = self._client.calls.create(
                to_number=to_number,
                from_=from_number,
                answer_url=webhook_url,
                answer_method="GET",
            )
            call_uuid = None
            if hasattr(response, "call_uuid"):
                call_uuid = response.call_uuid
            elif hasattr(response, "request_uuid"):
                call_uuid = response.request_uuid
            logger.info(f"Plivo outbound call initiated: UUID={call_uuid}")
            return call_uuid
        except Exception as exc:
            logger.error(f"Plivo outbound call failed: {exc}")
            return None

    def generate_stream_twiml(
        self,
        stream_url: str,
        welcome_message: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        parts = ['<?xml version="1.0" encoding="UTF-8"?>', "<Response>"]
        if welcome_message:
            parts.append(f"<Speak>{_xml_escape(welcome_message)}</Speak>")
        parts.append(f'<Stream url="{_xml_escape(stream_url)}"/>')
        parts.append("</Response>")
        return "\n".join(parts)

    def validate_inbound_request(self, request: Any) -> bool:
        return True


def _xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
