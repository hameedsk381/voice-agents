"""
India telephony pre-dial compliance gate (TRAI / TCCCPR / DLT).

Decides whether an outbound voice call is permitted *before* it is dialed:
- Org-scoped Do-Not-Call (DND) list
- Consent requirement for promotional (140-series) traffic
- Permitted commercial calling hours (9am-9pm IST per TCCCPR)
- DLT registration enforcement on the originating number

This is distinct from compliance_service.py, which audits call *content* per turn.
Consent tracking mirrors the Redis opt-in pattern in sms_service.py.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.compliance import DoNotCall
from app.models.phone_number import PhoneNumber

# India Standard Time is UTC+5:30 (no DST).
IST = timezone(timedelta(hours=5, minutes=30))


class CallConsentTracker:
    """Voice-call consent, sharing the Redis opt-in store used by SMS where possible."""

    OPT_IN_PREFIX = "call:optin:"

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
        try:
            # Honour a voice-specific opt-in or a shared SMS opt-in.
            if self.redis.get(f"{self.OPT_IN_PREFIX}{phone}") == "1":
                return True
            return self.redis.get(f"sms:optin:{phone}") == "1"
        except Exception as exc:
            logger.warning(f"Consent lookup failed for {phone}: {exc}. Treating as not opted in.")
            return False

    def set_opted_in(self, phone: str) -> None:
        self.redis.set(f"{self.OPT_IN_PREFIX}{phone}", "1")

    def set_opted_out(self, phone: str) -> None:
        self.redis.set(f"{self.OPT_IN_PREFIX}{phone}", "0")


class CallComplianceService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.consent = CallConsentTracker()

    # -- DND list -----------------------------------------------------------

    def is_on_dnd(self, phone: str, organization_id: Optional[str]) -> bool:
        if not self.db:
            return False
        q = self.db.query(DoNotCall).filter(DoNotCall.phone == phone)
        if organization_id:
            # Block on org-specific OR global (null org) entries.
            q = q.filter(
                (DoNotCall.organization_id == organization_id)
                | (DoNotCall.organization_id.is_(None))
            )
        return self.db.query(q.exists()).scalar()

    def add_to_dnd(
        self,
        phone: str,
        organization_id: Optional[str] = None,
        source: str = "manual",
        reason: Optional[str] = None,
    ) -> DoNotCall:
        entry = DoNotCall(
            phone=phone,
            organization_id=organization_id,
            source=source,
            reason=reason,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    # -- Calling hours ------------------------------------------------------

    def within_calling_hours(self, now_ist: Optional[datetime] = None) -> bool:
        if not settings.CALLING_HOURS_ENFORCED:
            return True
        now_ist = now_ist or datetime.now(IST)
        return settings.CALLING_HOURS_START <= now_ist.hour < settings.CALLING_HOURS_END

    # -- DLT enforcement ----------------------------------------------------

    def is_number_dlt_registered(self, from_number: str) -> bool:
        if not self.db:
            return True
        record = self.db.query(PhoneNumber).filter(
            PhoneNumber.phone_number == from_number
        ).first()
        if not record:
            # Unknown number (e.g. a global Twilio test number) — treat as unregistered.
            return False
        return record.dlt_status == "registered"

    def number_series(self, from_number: str) -> Optional[str]:
        if not self.db:
            return None
        record = self.db.query(PhoneNumber).filter(
            PhoneNumber.phone_number == from_number
        ).first()
        return record.number_series if record else None

    # -- The gate -----------------------------------------------------------

    def check_call_allowed(
        self,
        to_phone: str,
        *,
        organization_id: Optional[str] = None,
        from_number: Optional[str] = None,
        number_series: Optional[str] = None,
        is_promotional: bool = False,
    ) -> Tuple[bool, str]:
        """
        Returns (allowed, reason). reason is a machine code on block, "ok" on allow.
        Call this immediately before initiating any outbound call.
        """
        # 1. DND list always wins.
        if self.is_on_dnd(to_phone, organization_id):
            return False, "on_do_not_call_list"

        # 2. Calling hours.
        if not self.within_calling_hours():
            return False, "outside_calling_hours"

        # 3. DLT enforcement on the originating number.
        if settings.DLT_ENFORCEMENT and from_number:
            if not self.is_number_dlt_registered(from_number):
                return False, "originating_number_not_dlt_registered"

        # 4. Promotional traffic requires consent. Series "140" => promotional.
        series = number_series or (self.number_series(from_number) if from_number else None)
        promotional = is_promotional or series == "140"
        if promotional and not self.consent.is_opted_in(to_phone):
            return False, "consent_required_for_promotional"

        return True, "ok"
