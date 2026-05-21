"""
Seed realistic Voise AI demo data for outbound voice use cases.

Usage (from backend/):
  python -m scripts.seed_demo_data
  python -m scripts.seed_demo_data --reset

Demo login:
  Email:    demo@voise.ai
  Password: DemoVoise2026!
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow running as `python -m scripts.seed_demo_data` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.agent import Agent
from app.models.analytics import CallLog
from app.models.campaign import Campaign, CampaignContact, CampaignStatus, ContactStatus
from app.models.hitl import PendingAction
from app.models.knowledge import AgentKnowledge
from app.models.user import User, UserRole

# --- Stable IDs (safe to re-run with --reset) ---
ORG_ID = "org_voise_demo"

USER_DEMO_ID = "user_demo_admin"
USER_MANAGER_ID = "user_demo_manager"

AGENT_PAYMENT_ID = "agent_payment_reminder"
AGENT_LEAD_ID = "agent_lead_qualification"
AGENT_APPOINTMENT_ID = "agent_appointment_confirm"

CAMPAIGN_PAYMENT_ID = "campaign_payment_q2"
CAMPAIGN_LEAD_ID = "campaign_lead_march"
CAMPAIGN_APPOINTMENT_ID = "campaign_appointment_week"

DEMO_EMAIL = "demo@voise.ai"
DEMO_PASSWORD = "DemoVoise2026!"

SEED_ENTITY_IDS = [
    USER_DEMO_ID,
    USER_MANAGER_ID,
    AGENT_PAYMENT_ID,
    AGENT_LEAD_ID,
    AGENT_APPOINTMENT_ID,
    CAMPAIGN_PAYMENT_ID,
    CAMPAIGN_LEAD_ID,
    CAMPAIGN_APPOINTMENT_ID,
]


def _sign_transcript(transcript: List[Dict[str, Any]], session_id: str) -> str:
    text = json.dumps(transcript, sort_keys=True) + session_id
    secret = (settings.SECRET_KEY or "enterprise-secret").encode()
    return hmac.new(secret, text.encode(), hashlib.sha256).hexdigest()


def _embed_texts(texts: List[str]) -> List[List[float]]:
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        return [model.encode(t).tolist() for t in texts]
    except Exception as exc:
        print(f"Warning: could not load embedding model ({exc}). Knowledge search may be empty.")
        return [[0.0] * 384 for _ in texts]


def clear_seed_data(db) -> None:
    """Remove previously seeded rows (by stable IDs and demo emails)."""
    from app.models.analytics import CallLog as CL

    db.query(CL).filter(CL.organization_id == ORG_ID).delete(synchronize_session=False)
    db.query(CL).filter(CL.session_id.like("demo-session-%")).delete(synchronize_session=False)
    db.query(PendingAction).filter(PendingAction.organization_id == ORG_ID).delete(synchronize_session=False)
    db.query(AgentKnowledge).filter(AgentKnowledge.agent_id.in_(SEED_ENTITY_IDS)).delete(synchronize_session=False)
    db.query(CampaignContact).filter(CampaignContact.campaign_id.in_(SEED_ENTITY_IDS)).delete(synchronize_session=False)
    db.query(Campaign).filter(Campaign.id.in_(SEED_ENTITY_IDS)).delete(synchronize_session=False)
    db.query(Agent).filter(Agent.id.in_(SEED_ENTITY_IDS)).delete(synchronize_session=False)
    db.query(User).filter(User.email.in_([DEMO_EMAIL, "ops@voise.ai"])).delete(synchronize_session=False)
    db.commit()
    print("Cleared existing demo seed data.")


def seed_users(db) -> None:
    now = datetime.utcnow()
    users = [
        User(
            id=USER_DEMO_ID,
            email=DEMO_EMAIL,
            hashed_password=get_password_hash(DEMO_PASSWORD),
            full_name="Alex Morgan",
            role=UserRole.ADMIN.value,
            is_active=True,
            is_superuser=True,
            created_at=now - timedelta(days=90),
            last_login=now - timedelta(hours=2),
        ),
        User(
            id=USER_MANAGER_ID,
            email="ops@voise.ai",
            hashed_password=get_password_hash(DEMO_PASSWORD),
            full_name="Jordan Lee",
            role=UserRole.MANAGER.value,
            is_active=True,
            is_superuser=False,
            created_at=now - timedelta(days=60),
            last_login=now - timedelta(days=1),
        ),
    ]
    for user in users:
        if not db.query(User).filter(User.id == user.id).first():
            db.add(user)
    db.commit()
    print(f"Users ready — login with {DEMO_EMAIL} / {DEMO_PASSWORD}")


def seed_agents(db) -> None:
    agents = [
        Agent(
            id=AGENT_PAYMENT_ID,
            name="Payment Reminder — Consumer Loans",
            role="Accounts Receivable Specialist",
            description="Outbound payment reminders for past-due consumer loan accounts. Polite, compliant, and resolution-focused.",
            persona=(
                "You are {{agentName}}, a courteous collections specialist at {{companyName}}. "
                "You are calling {{customerName}} about an overdue installment. "
                "Confirm identity, state the balance and due date clearly, offer payment plan options, "
                "and never threaten or pressure. Respond only in {{language}}."
            ),
            language="en-US",
            tools=["check_account_balance", "schedule_callback", "transfer_to_human"],
            goals=["Secure payment commitment", "Offer workable payment plan", "Maintain positive tone"],
            success_criteria=[
                "Customer agrees to pay today or schedules a payment",
                "Customer confirms amount owed",
                "Payment plan accepted",
            ],
            failure_conditions=[
                "Customer requests cease contact",
                "Customer disputes debt without resolution path",
                "Three failed verification attempts",
            ],
            exit_actions=["schedule_callback", "transfer_to_human"],
            config={
                "voice": "auto",
                "greeting": (
                    "Hello {{customerName}}, this is {{agentName}} calling from {{companyName}} "
                    "regarding your account. Do you have a moment?"
                ),
            },
            organization_id=ORG_ID,
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=45),
        ),
        Agent(
            id=AGENT_LEAD_ID,
            name="Lead Qualification — B2B SaaS",
            role="Sales Development Representative",
            description="Qualifies inbound marketing leads for mid-market SaaS. Books demos for account executives.",
            persona=(
                "You are {{agentName}}, an upbeat SDR for {{companyName}}. "
                "You are speaking with {{customerName}} who downloaded a pricing guide. "
                "Confirm role and company size, assess timeline and budget fit, and book a demo if qualified. "
                "Keep the call under four minutes. Respond only in {{language}}."
            ),
            language="en-US",
            tools=["schedule_callback", "search_knowledge_base", "update_user_profile"],
            goals=["Confirm ICP fit", "Capture BANT basics", "Book qualified demo"],
            success_criteria=[
                "Demo scheduled",
                "Lead marked as qualified",
                "Decision maker identified",
            ],
            failure_conditions=[
                "Not a decision maker with no path forward",
                "Explicit opt-out",
                "Wrong number",
            ],
            exit_actions=["schedule_callback"],
            config={
                "voice": "auto",
                "greeting": (
                    "Hi {{customerName}}, this is {{agentName}} from {{companyName}} — "
                    "I'm following up on your interest in our platform. Is now a good time?"
                ),
            },
            organization_id=ORG_ID,
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=30),
        ),
        Agent(
            id=AGENT_APPOINTMENT_ID,
            name="Appointment Confirmation — Health Clinic",
            role="Patient Scheduling Coordinator",
            description="Confirms upcoming appointments, offers reschedule slots, and reduces no-shows.",
            persona=(
                "You are {{agentName}}, a friendly scheduling coordinator at {{companyName}}. "
                "You are calling {{customerName}} to confirm an upcoming visit. "
                "State date, time, and location; offer to reschedule if needed; "
                "remind them to bring ID and insurance card. Respond only in {{language}}."
            ),
            language="en-US",
            tools=["schedule_callback", "search_knowledge_base", "transfer_to_human"],
            goals=["Confirm attendance", "Reschedule if conflict", "Reduce no-show risk"],
            success_criteria=[
                "Appointment confirmed",
                "New slot booked",
                "Patient acknowledges instructions",
            ],
            failure_conditions=[
                "Patient cancels without rebooking",
                "Emergency symptoms mentioned",
            ],
            exit_actions=["transfer_to_human", "schedule_callback"],
            config={
                "voice": "auto",
                "greeting": (
                    "Hello {{customerName}}, this is {{agentName}} from {{companyName}} "
                    "calling to confirm your upcoming appointment. Is this still a good time for you?"
                ),
            },
            organization_id=ORG_ID,
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=20),
        ),
    ]
    for agent in agents:
        existing = db.query(Agent).filter(Agent.id == agent.id).first()
        if existing:
            for key in [
                "name", "role", "description", "persona", "language", "tools", "goals",
                "success_criteria", "failure_conditions", "exit_actions", "config",
                "organization_id", "is_active",
            ]:
                setattr(existing, key, getattr(agent, key))
        else:
            db.add(agent)
    db.commit()
    print("Seeded 3 voice agents (payment, leads, appointments).")


def seed_knowledge(db) -> None:
    db.query(AgentKnowledge).filter(AgentKnowledge.organization_id == ORG_ID).delete(synchronize_session=False)
    db.commit()

    chunks: List[Dict[str, Any]] = [
        # Payment agent
        {"agent_id": AGENT_PAYMENT_ID, "title": "Payment plan options", "content": "Customers may split past-due balances into up to 3 monthly installments with no additional fee if enrolled before day 45 past due. Minimum first payment is 25% of total past-due amount."},
        {"agent_id": AGENT_PAYMENT_ID, "title": "Compliance script", "content": "Do not threaten legal action. Do not call before 8am or after 9pm local time. If customer requests do-not-call, mark account and end call politely."},
        {"agent_id": AGENT_PAYMENT_ID, "title": "Verification", "content": "Verify last four digits of SSN and billing ZIP before discussing balance. After three failed attempts, offer callback with specialist."},
        # Lead agent
        {"agent_id": AGENT_LEAD_ID, "title": "ICP definition", "content": "Ideal customer: 50–500 employees, US or Canada, uses a CRM, evaluating voice automation for sales or support. Disqualify if under 10 employees unless strategic logo."},
        {"agent_id": AGENT_LEAD_ID, "title": "Qualification questions", "content": "Ask: current outbound volume, timeline to purchase, who else is involved, and whether they have budget this quarter."},
        {"agent_id": AGENT_LEAD_ID, "title": "Demo booking", "content": "Offer 30-minute product demo Tue–Thu 10am–4pm ET. Send calendar invite to work email only."},
        # Appointment agent
        {"agent_id": AGENT_APPOINTMENT_ID, "title": "Clinic hours", "content": "Main clinic open Mon–Fri 8am–6pm, Sat 9am–1pm. Telehealth visits available for follow-ups only."},
        {"agent_id": AGENT_APPOINTMENT_ID, "title": "Cancellation policy", "content": "Appointments may be cancelled or rescheduled up to 24 hours before visit without fee. Same-day cancellation may incur $25 fee."},
        {"agent_id": AGENT_APPOINTMENT_ID, "title": "What to bring", "content": "Patients should bring photo ID, insurance card, and list of current medications. Arrive 15 minutes early for paperwork."},
    ]
    texts = [c["content"] for c in chunks]
    embeddings = _embed_texts(texts)
    for chunk, emb in zip(chunks, embeddings):
        db.add(
            AgentKnowledge(
                id=str(uuid.uuid4()),
                agent_id=chunk["agent_id"],
                organization_id=ORG_ID,
                title=chunk["title"],
                content=chunk["content"],
                data_metadata={"source": "demo_seed"},
                embedding=emb,
            )
        )
    db.commit()
    print(f"Seeded {len(chunks)} knowledge base articles.")


def seed_campaigns(db) -> None:
    for camp_id in [CAMPAIGN_PAYMENT_ID, CAMPAIGN_LEAD_ID, CAMPAIGN_APPOINTMENT_ID]:
        db.query(CampaignContact).filter(CampaignContact.campaign_id == camp_id).delete(
            synchronize_session=False
        )
    db.commit()

    campaigns = [
        Campaign(
            id=CAMPAIGN_PAYMENT_ID,
            name="Q2 Past-Due — Tier 1 Accounts",
            description="Automated friendly reminders for accounts 15–45 days past due.",
            organization_id=ORG_ID,
            agent_id=AGENT_PAYMENT_ID,
            status=CampaignStatus.RUNNING.value,
            concurrency_limit=8,
            retry_config={"max_retries": 2, "retry_delay_minutes": 1440},
            call_config={
                "greeting": (
                    "Hello {{contactName}}, this is {{agentName}} from {{companyName}} "
                    "about your recent statement. May I speak with you briefly?"
                ),
            },
            total_contacts=0,
            completed_calls=0,
            failed_calls=0,
            created_by=USER_DEMO_ID,
            created_at=datetime.utcnow() - timedelta(days=14),
            start_time=datetime.utcnow() - timedelta(days=10),
        ),
        Campaign(
            id=CAMPAIGN_LEAD_ID,
            name="March Inbound — Pricing Guide Leads",
            description="Same-day qualification for leads who requested pricing in the last 72 hours.",
            organization_id=ORG_ID,
            agent_id=AGENT_LEAD_ID,
            status=CampaignStatus.RUNNING.value,
            concurrency_limit=5,
            retry_config={"max_retries": 3, "retry_delay_minutes": 240},
            call_config={
                "greeting": "Hi {{contactName}}, thanks for your interest in {{companyName}} — I have a quick question about your evaluation.",
            },
            total_contacts=0,
            completed_calls=0,
            failed_calls=0,
            created_by=USER_DEMO_ID,
            created_at=datetime.utcnow() - timedelta(days=7),
            start_time=datetime.utcnow() - timedelta(days=5),
        ),
        Campaign(
            id=CAMPAIGN_APPOINTMENT_ID,
            name="This Week — Appointment Confirmations",
            description="Outbound confirmations for primary care visits in the next 48 hours.",
            organization_id=ORG_ID,
            agent_id=AGENT_APPOINTMENT_ID,
            status=CampaignStatus.SCHEDULED.value,
            concurrency_limit=10,
            retry_config={"max_retries": 2, "retry_delay_minutes": 120},
            call_config={
                "greeting": "Hello {{contactName}}, {{companyName}} here to confirm your upcoming visit.",
            },
            total_contacts=0,
            completed_calls=0,
            failed_calls=0,
            created_by=USER_MANAGER_ID,
            created_at=datetime.utcnow() - timedelta(days=3),
            start_time=datetime.utcnow() + timedelta(days=1),
        ),
    ]
    for camp in campaigns:
        if not db.query(Campaign).filter(Campaign.id == camp.id).first():
            db.add(camp)
        else:
            db.merge(camp)
    db.commit()

    contacts_spec = [
        # Payment campaign
        (CAMPAIGN_PAYMENT_ID, "+15551234001", "Maria Gonzalez", ContactStatus.COMPLETED.value, {"balance": "284.50", "days_past_due": "22"}),
        (CAMPAIGN_PAYMENT_ID, "+15551234002", "James Chen", ContactStatus.COMPLETED.value, {"balance": "1190.00", "days_past_due": "31"}),
        (CAMPAIGN_PAYMENT_ID, "+15551234003", "Priya Sharma", ContactStatus.IN_PROGRESS.value, {"balance": "456.75", "days_past_due": "18"}),
        (CAMPAIGN_PAYMENT_ID, "+15551234004", "Robert Miller", ContactStatus.PENDING.value, {"balance": "89.20", "days_past_due": "15"}),
        (CAMPAIGN_PAYMENT_ID, "+15551234005", "Elena Vasquez", ContactStatus.FAILED.value, {"balance": "712.00", "days_past_due": "40"}),
        (CAMPAIGN_PAYMENT_ID, "+15551234006", "David Okonkwo", ContactStatus.COMPLETED.value, {"balance": "330.00", "days_past_due": "27"}),
        (CAMPAIGN_PAYMENT_ID, "+15551234007", "Sarah Kim", ContactStatus.QUEUED.value, {"balance": "198.40", "days_past_due": "16"}),
        # Lead campaign
        (CAMPAIGN_LEAD_ID, "+15552234001", "Marcus Rivera", ContactStatus.COMPLETED.value, {"company": "HealthBridge AI", "title": "Director of Ops", "employees": "120"}),
        (CAMPAIGN_LEAD_ID, "+15552234002", "Amanda Foster", ContactStatus.COMPLETED.value, {"company": "Brightline Retail", "title": "VP Sales", "employees": "340"}),
        (CAMPAIGN_LEAD_ID, "+15552234003", "Tyler Brooks", ContactStatus.IN_PROGRESS.value, {"company": "Nexus Logistics", "title": "Head of CX", "employees": "85"}),
        (CAMPAIGN_LEAD_ID, "+15552234004", "Lisa Nguyen", ContactStatus.PENDING.value, {"company": "Summit Legal", "title": "Office Manager", "employees": "45"}),
        (CAMPAIGN_LEAD_ID, "+15552234005", "Chris Patel", ContactStatus.FAILED.value, {"company": "Startup (stealth)", "title": "Founder", "employees": "8"}),
        (CAMPAIGN_LEAD_ID, "+15552234006", "Jennifer Walsh", ContactStatus.COMPLETED.value, {"company": "Metro Finance", "title": "COO", "employees": "210"}),
        # Appointment campaign
        (CAMPAIGN_APPOINTMENT_ID, "+15553334001", "Thomas Wright", ContactStatus.PENDING.value, {"appt": "Thu 10:30 AM", "provider": "Dr. Patel"}),
        (CAMPAIGN_APPOINTMENT_ID, "+15553334002", "Angela Morrison", ContactStatus.PENDING.value, {"appt": "Thu 2:00 PM", "provider": "Dr. Lee"}),
        (CAMPAIGN_APPOINTMENT_ID, "+15553334003", "Kevin O'Brien", ContactStatus.PENDING.value, {"appt": "Fri 9:00 AM", "provider": "Dr. Patel"}),
        (CAMPAIGN_APPOINTMENT_ID, "+15553334004", "Sandra Lewis", ContactStatus.PENDING.value, {"appt": "Fri 11:15 AM", "provider": "Dr. Kim"}),
        (CAMPAIGN_APPOINTMENT_ID, "+15553334005", "Michael Torres", ContactStatus.PENDING.value, {"appt": "Fri 3:45 PM", "provider": "Dr. Lee"}),
    ]

    for campaign_id, phone, name, status, custom in contacts_spec:
        db.add(
            CampaignContact(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                phone_number=phone,
                contact_name=name,
                custom_data=custom,
                status=status,
                attempts=1 if status != ContactStatus.PENDING.value else 0,
                last_attempt_at=datetime.utcnow() - timedelta(hours=6) if status != ContactStatus.PENDING.value else None,
            )
        )

    for camp_id in [CAMPAIGN_PAYMENT_ID, CAMPAIGN_LEAD_ID, CAMPAIGN_APPOINTMENT_ID]:
        camp = db.query(Campaign).filter(Campaign.id == camp_id).first()
        total = db.query(CampaignContact).filter(CampaignContact.campaign_id == camp_id).count()
        completed = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == camp_id,
            CampaignContact.status == ContactStatus.COMPLETED.value,
        ).count()
        failed = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == camp_id,
            CampaignContact.status == ContactStatus.FAILED.value,
        ).count()
        camp.total_contacts = total
        camp.completed_calls = completed
        camp.failed_calls = failed

    db.commit()
    print("Seeded 3 campaigns with 18 contacts.")


def _transcript_payment_success() -> List[Dict[str, str]]:
    return [
        {"role": "assistant", "content": "Hello Maria, this is Alex from Voise Financial regarding your account. Do you have a moment?"},
        {"role": "user", "content": "Yes, I know I'm a bit behind."},
        {"role": "assistant", "content": "Thank you. I'm showing a past-due balance of two hundred eighty-four dollars and fifty cents. Would you like to pay the full amount today or set up a short payment plan?"},
        {"role": "user", "content": "I can pay half today and the rest next Friday."},
        {"role": "assistant", "content": "That works. I'll note a payment of one hundred forty-two dollars today and the remainder on the twenty-fourth. You'll receive a confirmation text shortly."},
        {"role": "user", "content": "Perfect, thank you."},
    ]


def _transcript_lead_success() -> List[Dict[str, str]]:
    return [
        {"role": "assistant", "content": "Hi Marcus, this is Jordan from Voise AI following up on your pricing guide download. Is now okay?"},
        {"role": "user", "content": "Sure, we are evaluating voice tools for our patient outreach team."},
        {"role": "assistant", "content": "Great. Roughly how many outbound calls does your team handle per week, and are you hoping to go live this quarter?"},
        {"role": "user", "content": "About two thousand a week. We'd want something live in six weeks."},
        {"role": "assistant", "content": "That fits our sweet spot. I can book a thirty-minute demo with a solutions engineer Thursday at two PM Eastern. Does that work?"},
        {"role": "user", "content": "Thursday at two works. Send the invite to marcus@healthbridge.ai."},
        {"role": "assistant", "content": "Done — you'll see the invite shortly. Thanks Marcus!"},
    ]


def _transcript_appointment_success() -> List[Dict[str, str]]:
    return [
        {"role": "assistant", "content": "Hello Thomas, Voise Health Clinic calling to confirm your visit this Thursday at ten thirty with Dr. Patel."},
        {"role": "user", "content": "Yes, I'll be there."},
        {"role": "assistant", "content": "Wonderful. Please arrive fifteen minutes early with your ID and insurance card. Would you like a reminder text the morning of?"},
        {"role": "user", "content": "Yes please."},
        {"role": "assistant", "content": "You're all set. See you Thursday."},
    ]


def seed_call_logs(db) -> None:
    db.query(CallLog).filter(CallLog.organization_id == ORG_ID).delete(synchronize_session=False)
    db.query(CallLog).filter(CallLog.session_id.like("demo-session-%")).delete(synchronize_session=False)
    db.commit()

    now = datetime.utcnow()
    scenarios = [
        (AGENT_PAYMENT_ID, CAMPAIGN_PAYMENT_ID, "+15551234001", "Maria Gonzalez", "SUCCESS", _transcript_payment_success(), 142.0, 4),
        (AGENT_PAYMENT_ID, CAMPAIGN_PAYMENT_ID, "+15551234002", "James Chen", "SUCCESS", _transcript_payment_success(), 198.0, 5),
        (AGENT_PAYMENT_ID, CAMPAIGN_PAYMENT_ID, "+15551234005", "Elena Vasquez", "FAILURE", [
            {"role": "assistant", "content": "Hello, may I speak with Elena Vasquez?"},
            {"role": "user", "content": "Stop calling me. I already told your company."},
            {"role": "assistant", "content": "I apologize for the inconvenience. I'll mark your preference and end the call."},
        ], 45.0, 2),
        (AGENT_LEAD_ID, CAMPAIGN_LEAD_ID, "+15552234001", "Marcus Rivera", "SUCCESS", _transcript_lead_success(), 165.0, 6),
        (AGENT_LEAD_ID, CAMPAIGN_LEAD_ID, "+15552234006", "Jennifer Walsh", "SUCCESS", _transcript_lead_success(), 210.0, 7),
        (AGENT_LEAD_ID, CAMPAIGN_LEAD_ID, "+15552234005", "Chris Patel", "NEUTRAL", [
            {"role": "assistant", "content": "Hi Chris, following up from Voise AI on your platform interest."},
            {"role": "user", "content": "We're too early stage — only eight people. Call back in six months."},
            {"role": "assistant", "content": "Understood. I'll note that and reach out later this year."},
        ], 88.0, 3),
        (AGENT_APPOINTMENT_ID, CAMPAIGN_APPOINTMENT_ID, "+15553334001", "Thomas Wright", "SUCCESS", _transcript_appointment_success(), 95.0, 4),
        (AGENT_PAYMENT_ID, None, "+15559876543", "Unknown Caller", "NEUTRAL", [
            {"role": "assistant", "content": "Hello, this is Voise Financial. May I verify who I'm speaking with?"},
            {"role": "user", "content": "Wrong number."},
        ], 22.0, 1),
    ]

    # Add more volume spread across last 7 days
    extra_days = [
        (AGENT_PAYMENT_ID, CAMPAIGN_PAYMENT_ID, "SUCCESS", 120, 4),
        (AGENT_PAYMENT_ID, CAMPAIGN_PAYMENT_ID, "SUCCESS", 155, 5),
        (AGENT_LEAD_ID, CAMPAIGN_LEAD_ID, "SUCCESS", 140, 6),
        (AGENT_LEAD_ID, CAMPAIGN_LEAD_ID, "FAILURE", 60, 2),
        (AGENT_APPOINTMENT_ID, CAMPAIGN_APPOINTMENT_ID, "SUCCESS", 90, 3),
        (AGENT_APPOINTMENT_ID, CAMPAIGN_APPOINTMENT_ID, "NEUTRAL", 70, 2),
        (AGENT_PAYMENT_ID, CAMPAIGN_PAYMENT_ID, "NEUTRAL", 110, 3),
        (AGENT_LEAD_ID, CAMPAIGN_LEAD_ID, "SUCCESS", 175, 5),
    ]

    logs: List[CallLog] = []
    session_counter = 0

    def add_log(
        agent_id: str,
        campaign_id: Optional[str],
        caller: str,
        outcome: str,
        transcript: List[Dict[str, str]],
        duration: float,
        turns: int,
        days_ago: float,
        end_reason: str = "completed",
    ) -> None:
        nonlocal session_counter
        session_counter += 1
        session_id = f"demo-session-{session_counter:04d}"
        start = now - timedelta(days=days_ago, hours=session_counter % 12)
        end = start + timedelta(seconds=duration)
        logs.append(
            CallLog(
                id=str(uuid.uuid4()),
                session_id=session_id,
                agent_id=agent_id,
                organization_id=ORG_ID,
                caller_id=caller,
                campaign_id=campaign_id,
                start_time=start,
                end_time=end,
                duration_seconds=duration,
                avg_latency_ms=380 + (session_counter % 5) * 40,
                ttfap_ms=420 + (session_counter % 3) * 30,
                total_turns=turns,
                total_tokens=turns * 450,
                estimated_cost=round(turns * 0.008, 4),
                status="completed",
                end_reason=end_reason,
                outcome=outcome,
                outcome_reason=_outcome_reason(outcome, agent_id),
                transcript=transcript,
                metadata_json={"channel": "outbound", "demo": True},
                signature=_sign_transcript(transcript, session_id),
                created_at=start,
            )
        )

    for i, (agent_id, camp_id, phone, name, outcome, transcript, dur, turns) in enumerate(scenarios):
        add_log(agent_id, camp_id, phone, outcome, transcript, dur, turns, i * 0.8 + 0.5)

    for i, (agent_id, camp_id, outcome, dur, turns) in enumerate(extra_days):
        t = _transcript_payment_success() if agent_id == AGENT_PAYMENT_ID else (
            _transcript_lead_success() if agent_id == AGENT_LEAD_ID else _transcript_appointment_success()
        )
        add_log(agent_id, camp_id, f"+1555{7000000 + i}", outcome, t, float(dur), turns, i + 1.5)

    for log in logs:
        db.add(log)
    db.commit()
    print(f"Seeded {len(logs)} call logs with transcripts (last 7 days).")


def _outcome_reason(outcome: str, agent_id: str) -> str:
    if outcome == "SUCCESS":
        if agent_id == AGENT_PAYMENT_ID:
            return "Customer committed to payment or plan."
        if agent_id == AGENT_LEAD_ID:
            return "Qualified lead; demo scheduled."
        return "Appointment confirmed."
    if outcome == "FAILURE":
        return "Customer declined or could not verify."
    return "Call ended without clear resolution."


def seed_hitl(db) -> None:
    db.query(PendingAction).filter(PendingAction.organization_id == ORG_ID).delete(synchronize_session=False)
    db.commit()

    actions = [
        PendingAction(
            id=str(uuid.uuid4()),
            session_id="demo-session-0002",
            agent_id=AGENT_PAYMENT_ID,
            organization_id=ORG_ID,
            action_type="payment_plan_override",
            description="Approve 6-month payment plan for James Chen — $1,190 balance, first payment $200.",
            payload={"account_id": "ACC-88421", "plan_months": 6, "first_payment": 200},
            status="pending",
            created_at=datetime.utcnow() - timedelta(hours=3),
        ),
        PendingAction(
            id=str(uuid.uuid4()),
            session_id="demo-session-0005",
            agent_id=AGENT_LEAD_ID,
            organization_id=ORG_ID,
            action_type="high_value_demo",
            description="Confirm executive demo for Jennifer Walsh — Metro Finance, 210 employees.",
            payload={"lead_id": "LEAD-9921", "demo_slot": "Wed 3pm ET"},
            status="pending",
            created_at=datetime.utcnow() - timedelta(hours=5),
        ),
    ]
    for action in actions:
        db.add(action)
    db.commit()
    print(f"Seeded {len(actions)} approval queue items.")


def seed_all(reset: bool = False) -> None:
    db = SessionLocal()
    try:
        if reset:
            clear_seed_data(db)
        seed_users(db)
        seed_agents(db)
        seed_knowledge(db)
        seed_campaigns(db)
        seed_call_logs(db)
        seed_hitl(db)
        print("\nDemo data ready. Open the dashboard and explore:")
        print("  • Agents — payment, lead qualification, appointments")
        print("  • Campaigns — running + scheduled with contacts")
        print("  • Analytics / Logs — call history and outcomes")
        print("  • Approvals — pending actions")
        print(f"  • Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Voise AI demo data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing demo seed rows before inserting",
    )
    args = parser.parse_args()
    seed_all(reset=args.reset)


if __name__ == "__main__":
    main()
