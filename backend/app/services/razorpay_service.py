"""
Razorpay payment-link service for the collections flow.

Generates a short payment link that the voice agent sends over SMS so a
borrower can pay an overdue EMI mid-call. The link carries `notes` that tie
the payment back to the originating call (session_id / call_log_id), so the
Razorpay webhook can record a `payment_collected` outcome.

Gracefully degrades to a mock link when keys or the SDK are unavailable
(mirrors the mock behaviour of SmsService / PhoneNumberService).
"""

from typing import Any, Dict, Optional

from loguru import logger

from app.core.config import settings


class RazorpayService:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self._client = None
        self.is_configured = bool(self.key_id and self.key_secret)

        if self.is_configured:
            try:
                import razorpay
                self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
            except Exception as exc:  # SDK missing or auth error
                logger.warning(f"Razorpay SDK unavailable, using mock links: {exc}")
                self.is_configured = False

    def create_payment_link(
        self,
        amount_rupees: float,
        *,
        customer_phone: Optional[str] = None,
        customer_name: Optional[str] = None,
        description: str = "EMI payment",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a payment link for the given rupee amount. Returns {short_url, id, status}."""
        amount_paise = int(round(amount_rupees * 100))
        notes = notes or {}

        if not self.is_configured or not self._client:
            return self._mock_link(amount_rupees, notes)

        try:
            payload: Dict[str, Any] = {
                "amount": amount_paise,
                "currency": "INR",
                "accept_partial": False,
                "description": description,
                "notes": {k: str(v) for k, v in notes.items()},
                "reminder_enable": True,
            }
            customer: Dict[str, str] = {}
            if customer_name:
                customer["name"] = customer_name
            if customer_phone:
                customer["contact"] = customer_phone
            if customer:
                payload["customer"] = customer
                payload["notify"] = {"sms": bool(customer_phone), "email": False}

            link = self._client.payment_link.create(payload)
            logger.info(f"Razorpay payment link created: {link.get('id')} for ₹{amount_rupees}")
            return {
                "id": link.get("id"),
                "short_url": link.get("short_url"),
                "status": link.get("status", "created"),
                "amount": amount_rupees,
            }
        except Exception as exc:
            logger.error(f"Razorpay payment link creation failed: {exc}")
            return self._mock_link(amount_rupees, notes, error=str(exc))

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """Verify a Razorpay webhook signature. Returns False if secret unset."""
        secret = settings.RAZORPAY_WEBHOOK_SECRET
        if not secret:
            return False
        try:
            import hmac
            import hashlib
            expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as exc:
            logger.error(f"Razorpay webhook signature verification error: {exc}")
            return False

    def _mock_link(self, amount_rupees: float, notes: Dict[str, Any], error: Optional[str] = None) -> Dict[str, Any]:
        mock_id = f"plink_mock_{abs(hash(str(notes))) % 10_000_000}"
        logger.info(f"[MOCK Razorpay] link {mock_id} for ₹{amount_rupees}")
        return {
            "id": mock_id,
            "short_url": f"https://rzp.io/i/{mock_id}",
            "status": "created",
            "amount": amount_rupees,
            "mock": True,
            **({"error": error} if error else {}),
        }
