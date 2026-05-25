"""
Outbound email for workflow automation (SMTP when configured, always audited).
"""
from __future__ import annotations

import smtplib
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.workflow import EmailMessage


class EmailService:
    def __init__(self, db: Session):
        self.db = db

    def _smtp_configured(self) -> bool:
        return bool(getattr(settings, "SMTP_HOST", None) and getattr(settings, "SMTP_FROM", None))

    async def send_template_email(
        self,
        *,
        to_address: str,
        template: str,
        context: Dict[str, Any],
        workflow_instance_id: Optional[str] = None,
        subject_override: Optional[str] = None,
    ) -> EmailMessage:
        subject, body = self._render_template(template, context)
        if subject_override:
            subject = subject_override

        status = "queued"
        provider_id = None
        error = None

        if self._smtp_configured():
            try:
                provider_id = self._send_smtp(to_address, subject, body)
                status = "sent"
            except Exception as exc:
                logger.error(f"SMTP send failed: {exc}")
                status = "failed"
                error = str(exc)
        else:
            status = "simulated"
            provider_id = f"sim-{uuid.uuid4().hex[:12]}"
            logger.info(f"[email simulated] to={to_address} template={template} subject={subject}")

        row = EmailMessage(
            id=str(uuid.uuid4()),
            workflow_instance_id=workflow_instance_id,
            to_address=to_address,
            template=template,
            subject=subject,
            body_preview=body[:500],
            status=status,
            provider_id=provider_id,
            error_message=error,
            metadata_json={"context_keys": list(context.keys())},
            sent_at=datetime.utcnow() if status in ("sent", "simulated") else None,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _render_template(self, template: str, context: Dict[str, Any]) -> tuple[str, str]:
        name = context.get("customer_name") or context.get("contact_name") or "Customer"
        amount = context.get("outstanding_amount") or context.get("amount") or "—"
        due = context.get("due_date") or "—"
        invoice = context.get("invoice_number") or "—"

        templates = {
            "payment_reminder": (
                f"Payment reminder — account {context.get('customer_id', '')}",
                f"Hello {name},\n\nThis is a friendly reminder that invoice {invoice} "
                f"for {amount} was due on {due}. Please contact us to arrange payment.\n\nThank you.",
            ),
            "lead_nurture": (
                "Following up on your interest",
                f"Hi {name},\n\nThanks for your interest. We'd love to schedule a short call "
                f"when convenient.\n\nBest regards,\nVoise AI",
            ),
            "appointment_confirm": (
                "Appointment confirmation",
                f"Hello {name},\n\nPlease confirm your upcoming appointment on {due}.\n\nThank you.",
            ),
            "escalation_internal": (
                f"Escalation: {name}",
                f"Account requires attention.\nCustomer: {name}\nAmount: {amount}\n"
                f"Branch: {context.get('branch_code', '—')}\nAging: {context.get('aging_bucket', '—')}",
            ),
        }
        return templates.get(
            template,
            (f"Notification from Voise AI", f"Hello {name},\n\nThis is an automated message regarding your account.\n"),
        )

    def _send_smtp(self, to_address: str, subject: str, body: str) -> str:
        host = settings.SMTP_HOST
        port = int(getattr(settings, "SMTP_PORT", 587) or 587)
        user = getattr(settings, "SMTP_USER", None)
        password = getattr(settings, "SMTP_PASSWORD", None)
        from_addr = settings.SMTP_FROM
        use_tls = bool(getattr(settings, "SMTP_USE_TLS", True))

        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(host, port, timeout=30) as server:
            if use_tls:
                server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_address], msg.as_string())
        return f"smtp-{uuid.uuid4().hex[:10]}"
