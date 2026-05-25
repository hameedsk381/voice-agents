"""
Phone number provisioning service — Twilio integration for searching,
purchasing, configuring, and releasing phone numbers.
"""
from typing import Optional, List, Dict, Any
from loguru import logger
from sqlalchemy.orm import Session
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

from app.core.config import settings
from app.models.phone_number import PhoneNumber


class PhoneNumberService:
    def __init__(self, db: Optional[Session] = None):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.client = (
            TwilioClient(self.account_sid, self.auth_token)
            if self.account_sid and self.auth_token
            else None
        )
        self.db = db

    def _check_twilio(self):
        if not self.client:
            raise RuntimeError("Twilio not configured — missing TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN")

    # ─── Search ──────────────────────────────────────────────────────────

    def search_available(
        self,
        country_code: str = "IN",
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for available phone numbers via Twilio."""
        self._check_twilio()
        kwargs: Dict[str, Any] = {"limit": limit}
        if area_code:
            kwargs["area_code"] = area_code
        if contains:
            kwargs["contains"] = contains

        try:
            numbers = self.client.available_phone_numbers(country_code).local.list(**kwargs)
            return [
                {
                    "phone_number": n.phone_number,
                    "friendly_name": n.friendly_name,
                    "locality": n.locality,
                    "region": n.region,
                    "capabilities": {
                        "voice": n.capabilities.get("voice", False),
                        "sms": n.capabilities.get("sms", False),
                        "mms": n.capabilities.get("mms", False),
                    },
                    "price": n.voice_price if hasattr(n, "voice_price") else None,
                }
                for n in numbers
            ]
        except TwilioRestException as e:
            logger.error(f"Twilio search failed: {e}")
            raise RuntimeError(f"Failed to search phone numbers: {e.msg}")

    # ─── Purchase ────────────────────────────────────────────────────────

    def purchase(
        self,
        phone_number: str,
        friendly_name: Optional[str] = None,
        voice_url: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Purchase a phone number and store in local DB."""
        self._check_twilio()
        try:
            kwargs: Dict[str, Any] = {
                "phone_number": phone_number,
            }
            if friendly_name:
                kwargs["friendly_name"] = friendly_name
            if voice_url:
                kwargs["voice_url"] = voice_url

            incoming = self.client.incoming_phone_numbers.create(**kwargs)
            logger.info(f"Purchased phone number {phone_number} (Twilio SID: {incoming.sid})")

            if self.db and organization_id:
                record = PhoneNumber(
                    organization_id=organization_id,
                    phone_number=phone_number,
                    friendly_name=friendly_name or incoming.friendly_name,
                    twilio_sid=incoming.sid,
                    capabilities={
                        "voice": incoming.capabilities.get("voice", False),
                        "sms": incoming.capabilities.get("sms", False),
                        "mms": incoming.capabilities.get("mms", False),
                    },
                    region=getattr(incoming, "region", None),
                    is_active=True,
                )
                self.db.add(record)
                self.db.commit()
                self.db.refresh(record)
                local_id = record.id
            else:
                local_id = None

            return {
                "id": local_id,
                "phone_number": incoming.phone_number,
                "friendly_name": incoming.friendly_name,
                "twilio_sid": incoming.sid,
                "capabilities": {
                    "voice": incoming.capabilities.get("voice", False),
                    "sms": incoming.capabilities.get("sms", False),
                    "mms": incoming.capabilities.get("mms", False),
                },
                "region": getattr(incoming, "region", None),
            }
        except TwilioRestException as e:
            logger.error(f"Twilio purchase failed: {e}")
            raise RuntimeError(f"Failed to purchase phone number: {e.msg}")

    # ─── List Owned (from Twilio) ────────────────────────────────────────

    def list_owned_twilio(self) -> List[Dict[str, Any]]:
        """List all phone numbers owned in the Twilio account."""
        self._check_twilio()
        try:
            numbers = self.client.incoming_phone_numbers.list(limit=50)
            return [
                {
                    "sid": n.sid,
                    "phone_number": n.phone_number,
                    "friendly_name": n.friendly_name,
                    "capabilities": {
                        "voice": n.capabilities.get("voice", False),
                        "sms": n.capabilities.get("sms", False),
                        "mms": n.capabilities.get("mms", False),
                    },
                    "voice_url": n.voice_url,
                }
                for n in numbers
            ]
        except TwilioRestException as e:
            logger.error(f"Twilio list failed: {e}")
            raise RuntimeError(f"Failed to list phone numbers: {e.msg}")

    def list_organization_numbers(self, organization_id: str) -> List[Dict[str, Any]]:
        """List phone numbers owned by an organization (from local DB)."""
        if not self.db:
            raise RuntimeError("No database session available")
        records = self.db.query(PhoneNumber).filter(
            PhoneNumber.organization_id == organization_id,
            PhoneNumber.is_active == True,
        ).all()
        return [
            {
                "id": r.id,
                "phone_number": r.phone_number,
                "friendly_name": r.friendly_name,
                "twilio_sid": r.twilio_sid,
                "capabilities": r.capabilities or {},
                "region": r.region,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]

    # ─── Configure Voice URL ─────────────────────────────────────────────

    def configure_voice_url(self, twilio_sid: str, voice_url: str) -> Dict[str, Any]:
        """Update the voice URL (webhook) for a Twilio phone number."""
        self._check_twilio()
        try:
            incoming = self.client.incoming_phone_numbers(twilio_sid).update(voice_url=voice_url)
            logger.info(f"Configured voice URL for {twilio_sid}: {voice_url}")
            return {
                "sid": incoming.sid,
                "phone_number": incoming.phone_number,
                "voice_url": incoming.voice_url,
            }
        except TwilioRestException as e:
            logger.error(f"Twilio configure failed: {e}")
            raise RuntimeError(f"Failed to configure phone number: {e.msg}")

    # ─── Release ─────────────────────────────────────────────────────────

    def release(self, phone_number_id: str, organization_id: str) -> bool:
        """Release a phone number back to Twilio."""
        if not self.db:
            raise RuntimeError("No database session available")
        record = self.db.query(PhoneNumber).filter(
            PhoneNumber.id == phone_number_id,
            PhoneNumber.organization_id == organization_id,
        ).first()
        if not record:
            raise RuntimeError("Phone number not found")

        self._check_twilio()
        try:
            self.client.incoming_phone_numbers(record.twilio_sid).delete()
            logger.info(f"Released phone number {record.phone_number} (SID: {record.twilio_sid})")
        except TwilioRestException as e:
            logger.error(f"Twilio release failed: {e}")
            raise RuntimeError(f"Failed to release phone number: {e.msg}")

        record.is_active = False
        self.db.commit()
        return True

    # ─── Sync Twilio → Local ─────────────────────────────────────────────

    def sync_from_twilio(self, organization_id: str) -> int:
        """Sync all Twilio-owned numbers into our local DB for an organization."""
        self._check_twilio()
        twilio_numbers = self.list_owned_twilio()
        synced = 0
        for tn in twilio_numbers:
            existing = self.db.query(PhoneNumber).filter(
                PhoneNumber.twilio_sid == tn["sid"]
            ).first()
            if not existing:
                record = PhoneNumber(
                    organization_id=organization_id,
                    phone_number=tn["phone_number"],
                    friendly_name=tn["friendly_name"],
                    twilio_sid=tn["sid"],
                    capabilities=tn["capabilities"],
                    is_active=True,
                )
                self.db.add(record)
                synced += 1
        if synced:
            self.db.commit()
        return synced


phone_number_service = PhoneNumberService()
