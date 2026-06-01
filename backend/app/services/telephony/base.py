from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class TelephonyProvider(ABC):
    @abstractmethod
    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs: Any,
    ) -> Optional[str]:
        """Place an outbound call. Returns a call ID/SID on success."""

    @abstractmethod
    def generate_stream_twiml(self, stream_url: str, **kwargs: Any) -> str:
        """Generate provider-specific XML/NCCO/JSON to connect a call to a media stream."""

    @abstractmethod
    def validate_inbound_request(self, request: Any) -> bool:
        """Validate that an inbound webhook request came from the provider."""

    def get_call_status_url(self, call_id: str) -> Optional[str]:
        """Return a URL to check the status of an active call (provider-specific)."""
        return None
