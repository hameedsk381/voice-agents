from typing import Optional

from app.core.config import settings
from app.services.telephony.base import TelephonyProvider

_instance: Optional[TelephonyProvider] = None


def get_telephony_provider() -> TelephonyProvider:
    global _instance
    if _instance is not None:
        return _instance

    provider = (settings.TELEPHONY_PROVIDER or "twilio").lower()

    if provider == "twilio":
        from app.services.telephony.twilio_provider import TwilioProvider
        _instance = TwilioProvider(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            auth_token=settings.TWILIO_AUTH_TOKEN,
        )
    elif provider == "vonage":
        from app.services.telephony.vonage_provider import VonageProvider
        _instance = VonageProvider(
            api_key=settings.VONAGE_API_KEY,
            api_secret=settings.VONAGE_API_SECRET,
            application_id=settings.VONAGE_APPLICATION_ID,
            private_key=settings.VONAGE_PRIVATE_KEY,
        )
    elif provider == "plivo":
        from app.services.telephony.plivo_provider import PlivoProvider
        _instance = PlivoProvider(
            auth_id=settings.PLIVO_AUTH_ID,
            auth_token=settings.PLIVO_AUTH_TOKEN,
        )
    elif provider == "telnyx":
        from app.services.telephony.telnyx_provider import TelnyxProvider
        _instance = TelnyxProvider(
            api_key=settings.TELNYX_API_KEY,
        )
    else:
        raise ValueError(f"Unknown telephony provider: {provider}")

    return _instance


def reset_telephony_provider() -> None:
    global _instance
    _instance = None
