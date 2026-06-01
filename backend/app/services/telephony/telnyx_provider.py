from typing import Any, Optional

from loguru import logger

from app.services.telephony.base import TelephonyProvider


class TelnyxProvider(TelephonyProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self._client: Optional[Any] = None
        if api_key:
            try:
                import telnyx
                telnyx.api_key = api_key
                self._client = telnyx
            except ImportError:
                logger.warning("telnyx SDK not installed — install 'telnyx' package")

    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs: Any,
    ) -> Optional[str]:
        if not self._client:
            logger.error("Telnyx client not initialized — missing API key")
            return None
        try:
            response = self._client.Call.create(
                to=to_number,
                from_=from_number,
                webhook_url=webhook_url,
                webhook_url_method="POST",
            )
            call_control_id = None
            if hasattr(response, "call_control_id"):
                call_control_id = response.call_control_id
            elif isinstance(response, dict):
                call_control_id = response.get("call_control_id") or response.get("id")
            logger.info(f"Telnyx outbound call initiated: ID={call_control_id}")
            return call_control_id
        except Exception as exc:
            logger.error(f"Telnyx outbound call failed: {exc}")
            return None

    def generate_stream_twiml(
        self,
        stream_url: str,
        **kwargs: Any,
    ) -> str:
        return ""

    def validate_inbound_request(self, request: Any) -> bool:
        return True
