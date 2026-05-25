"""
Built-in workflow templates — duplicate and customize in the dashboard.
"""
from __future__ import annotations

from typing import Any, Dict, List

COLLECTIONS_PAYMENT_REMINDER: Dict[str, Any] = {
    "version": "1",
    "name": "Collections — Payment Reminder",
    "description": "Outbound voice reminder with retries, email fallback, and finance escalation.",
    "category": "collections",
    "entry": "check_vip",
    "nodes": [
        {
            "id": "check_vip",
            "type": "condition",
            "label": "VIP do-not-auto-call?",
            "config": {"rules": [{"field": "vip_no_auto_call", "op": "eq", "value": True}]},
            "on_true": "escalate_rm",
            "on_false": "voice_call",
        },
        {
            "id": "voice_call",
            "type": "voice_call",
            "label": "Payment reminder call",
            "config": {"max_attempts": 3, "retry_delay_minutes": [240, 1440, 2880]},
            "next": "check_call_outcome",
        },
        {
            "id": "check_call_outcome",
            "type": "condition",
            "label": "Call answered?",
            "config": {
                "rules": [{"field": "last_call_outcome", "op": "in", "value": ["answered", "success", "promise_to_pay"]}]
            },
            "on_true": "end_success",
            "on_false": "check_retries",
        },
        {
            "id": "check_retries",
            "type": "condition",
            "label": "Retries exhausted?",
            "config": {
                "rules": [{"field": "call_attempts", "op": "gte", "value": 3}]
            },
            "on_true": "email_reminder",
            "on_false": "wait_retry",
        },
        {
            "id": "wait_retry",
            "type": "wait",
            "label": "Wait before retry",
            "config": {"minutes": 240},
            "next": "voice_call",
        },
        {
            "id": "email_reminder",
            "type": "email",
            "label": "Send payment reminder email",
            "config": {"template": "payment_reminder", "track": True},
            "next": "check_aging",
        },
        {
            "id": "check_aging",
            "type": "condition",
            "label": "120+ days overdue?",
            "config": {"rules": [{"field": "aging_days", "op": "gte", "value": 120}]},
            "on_true": "approve_legal",
            "on_false": "escalate_branch",
        },
        {
            "id": "approve_legal",
            "type": "hitl_approval",
            "label": "Legal escalation approval",
            "config": {
                "action_type": "legal_escalation",
                "description": "Approve legal escalation for severely aged account",
            },
            "next": "escalate_legal",
        },
        {
            "id": "escalate_legal",
            "type": "escalate",
            "label": "Escalate to Legal",
            "config": {"owner_role": "legal", "priority": "high"},
            "next": "end_escalated",
        },
        {
            "id": "escalate_branch",
            "type": "escalate",
            "label": "Escalate to Branch Owner",
            "config": {"owner_role": "branch_owner", "priority": "medium"},
            "next": "end_escalated",
        },
        {
            "id": "escalate_rm",
            "type": "escalate",
            "label": "Escalate to Relationship Manager",
            "config": {"owner_role": "relationship_manager", "priority": "high"},
            "next": "end_escalated",
        },
        {
            "id": "end_success",
            "type": "end",
            "label": "Completed",
            "config": {"outcome": "success"},
        },
        {
            "id": "end_escalated",
            "type": "end",
            "label": "Escalated",
            "config": {"outcome": "escalated"},
        },
    ],
}

LEAD_QUALIFICATION: Dict[str, Any] = {
    "version": "1",
    "name": "Lead Qualification — Outbound",
    "description": "Qualify inbound leads by voice, book demo or send nurture email.",
    "category": "sales",
    "entry": "voice_call",
    "nodes": [
        {
            "id": "voice_call",
            "type": "voice_call",
            "label": "Qualification call",
            "config": {"max_attempts": 2, "retry_delay_minutes": [120, 480]},
            "next": "check_qualified",
        },
        {
            "id": "check_qualified",
            "type": "condition",
            "label": "Demo scheduled?",
            "config": {"rules": [{"field": "last_call_outcome", "op": "eq", "value": "demo_scheduled"}]},
            "on_true": "end_success",
            "on_false": "email_nurture",
        },
        {
            "id": "email_nurture",
            "type": "email",
            "label": "Nurture email",
            "config": {"template": "lead_nurture"},
            "next": "end_nurture",
        },
        {
            "id": "end_success",
            "type": "end",
            "config": {"outcome": "qualified"},
        },
        {
            "id": "end_nurture",
            "type": "end",
            "config": {"outcome": "nurture"},
        },
    ],
}

APPOINTMENT_CONFIRMATION: Dict[str, Any] = {
    "version": "1",
    "name": "Appointment Confirmation",
    "description": "Confirm upcoming visit; retry and email if no answer.",
    "category": "healthcare",
    "entry": "voice_call",
    "nodes": [
        {
            "id": "voice_call",
            "type": "voice_call",
            "label": "Confirmation call",
            "config": {"max_attempts": 2, "retry_delay_minutes": [60, 180]},
            "next": "check_confirmed",
        },
        {
            "id": "check_confirmed",
            "type": "condition",
            "label": "Confirmed?",
            "config": {"rules": [{"field": "last_call_outcome", "op": "in", "value": ["confirmed", "success"]}]},
            "on_true": "end_success",
            "on_false": "email_confirm",
        },
        {
            "id": "email_confirm",
            "type": "email",
            "label": "Confirmation email",
            "config": {"template": "appointment_confirm"},
            "next": "end_email",
        },
        {
            "id": "end_success",
            "type": "end",
            "config": {"outcome": "confirmed"},
        },
        {
            "id": "end_email",
            "type": "end",
            "config": {"outcome": "email_sent"},
        },
    ],
}

BUILTIN_TEMPLATES: List[Dict[str, Any]] = [
    COLLECTIONS_PAYMENT_REMINDER,
    LEAD_QUALIFICATION,
    APPOINTMENT_CONFIRMATION,
]

TEMPLATE_BY_SLUG = {
    "collections-payment-reminder": COLLECTIONS_PAYMENT_REMINDER,
    "lead-qualification": LEAD_QUALIFICATION,
    "appointment-confirmation": APPOINTMENT_CONFIRMATION,
}
