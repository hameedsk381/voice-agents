"""
Marketplace service for agent templates and workflow plugins.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.agent import Agent

class MarketplaceService:
    def __init__(self, db: Session):
        self.db = db

    def get_templates(self) -> List[Dict[str, Any]]:
        """Returns pre-built agent templates."""
        return [
            {
                "id": "tpl_payment_reminder",
                "name": "Payment Reminder — Outbound",
                "category": "Outbound Collections",
                "role": "Accounts Receivable Specialist",
                "description": "Friendly past-due reminders with payment plans and compliant tone.",
                "persona": (
                    "You are {{agentName}} from {{companyName}}, calling {{customerName}} about a past-due balance. "
                    "Verify identity, state amount clearly, offer payment options, and never pressure or threaten."
                ),
                "language": "en-US",
                "recommended_tools": ["check_account_balance", "schedule_callback", "transfer_to_human"],
                "goals": ["Secure payment commitment", "Offer workable payment plan"],
                "success_criteria": ["payment scheduled", "amount confirmed", "plan accepted"],
                "failure_conditions": ["cease contact", "dispute unresolved", "verification failed"],
                "popularity": 98,
                "rating": 4.9
            },
            {
                "id": "tpl_lead_qualification",
                "name": "Lead Qualification — Outbound",
                "category": "Outbound Sales",
                "role": "Sales Development Representative",
                "description": "Qualifies marketing leads and books demos for your sales team.",
                "persona": (
                    "You are {{agentName}} from {{companyName}}, following up with {{customerName}} on product interest. "
                    "Confirm fit, capture timeline and budget, and book a demo when qualified."
                ),
                "language": "en-US",
                "recommended_tools": ["schedule_callback", "search_knowledge_base", "update_user_profile"],
                "goals": ["Confirm ICP fit", "Book qualified demo"],
                "success_criteria": ["demo scheduled", "decision maker identified"],
                "failure_conditions": ["opt out", "wrong number", "not qualified"],
                "popularity": 95,
                "rating": 4.8
            },
            {
                "id": "tpl_appointment_confirm",
                "name": "Appointment Confirmation — Outbound",
                "category": "Healthcare & Services",
                "role": "Scheduling Coordinator",
                "description": "Confirms upcoming visits, reschedules conflicts, and reduces no-shows.",
                "persona": (
                    "You are {{agentName}} from {{companyName}}, calling {{customerName}} to confirm an upcoming appointment. "
                    "State date, time, and location; offer reschedule; remind what to bring."
                ),
                "language": "en-US",
                "recommended_tools": ["schedule_callback", "search_knowledge_base", "transfer_to_human"],
                "goals": ["Confirm attendance", "Reschedule if needed"],
                "success_criteria": ["appointment confirmed", "new slot booked"],
                "failure_conditions": ["cancelled without rebook", "emergency symptoms"],
                "popularity": 92,
                "rating": 4.8
            },
            {
                "id": "tpl_support_pro",
                "name": "OmniSupport Pro",
                "category": "Customer Support",
                "role": "High-Empathy Support Specialist",
                "description": "Optimized for resolution time and customer satisfaction scores.",
                "persona": "You are a professional, calm, and highly empathetic customer support agent. Your goal is to resolve issues on the first call.",
                "language": "en-US",
                "recommended_tools": ["get_order_status", "search_knowledge_base"],
                "goals": ["Resolve user inquiry", "Maintain high empathy score"],
                "success_criteria": ["thank you", "resolved", "problem fixed"],
                "failure_conditions": ["not happy", "angry", "manager"],
                "popularity": 88,
                "rating": 4.9
            },
            {
                "id": "tpl_security_vault",
                "name": "SecurityVault Auditor",
                "category": "Security",
                "role": "Anti-Fraud Identity Verifier",
                "description": "High-security agent for multi-factor identity verification.",
                "persona": "You are a strict security auditor. Your ONLY job is to verify identity before any account changes are allowed. Be firm but professional.",
                "language": "en-US",
                "recommended_tools": ["send_verification_code", "verify_otp", "search_knowledge_base"],
                "goals": ["Verify identity", "Prevent unauthorized access"],
                "success_criteria": ["identity verified", "authenticated"],
                "failure_conditions": ["verification failed", "incorrect otp"],
                "popularity": 88,
                "rating": 4.9
            },
            {
                "id": "tpl_hr_onboard",
                "name": "HR Buddy",
                "category": "Corporate",
                "role": "Employee Onboarding Specialist",
                "description": "Automated internal assistant for new hire orientation.",
                "persona": "You are the friendly HR assistant. You guide new employees through their first day, explaining benefits and training modules.",
                "language": "en-US",
                "recommended_tools": ["search_knowledge_base", "update_user_profile"],
                "goals": ["Complete onboarding checklist", "Answer policy questions"],
                "success_criteria": ["onboarding complete", "policy understood"],
                "failure_conditions": ["legal issue", "harassment report"],
                "popularity": 76,
                "rating": 4.5
            },
            {
                "id": "tpl_travel_guide",
                "name": "GlobeTrotter Pro",
                "category": "Travel",
                "role": "Multilingual Logistics Specialist",
                "description": "Handles worldwide travel bookings and real-time translation.",
                "persona": "You are a world-class travel agent. You know everything about flights, hotels, and local customs across the globe.",
                "language": "en-US",
                "recommended_tools": ["search_knowledge_base", "check_flight_status", "book_hotel"],
                "goals": ["Complete travel booking", "Provide local insights"],
                "success_criteria": ["booking complete", "flight confirmed"],
                "failure_conditions": ["visa issues", "canceled flight"],
                "popularity": 84,
                "rating": 4.7
            },
            {
                "id": "tpl_tech_dr",
                "name": "TechDiagnostic v2",
                "category": "Technical",
                "role": "IT & Product Troubleshooting",
                "description": "Step-by-step diagnostic agent optimized for lowering ticket escalation rates.",
                "persona": "You are a highly logical and patient technical expert. You guide users through troubleshooting steps one at a time.",
                "language": "en-US",
                "recommended_tools": ["search_knowledge_base", "transfer_to_human"],
                "goals": ["Fix technical issue", "Reduce support tickets"],
                "success_criteria": ["resolved", "working now"],
                "failure_conditions": ["hardware failure", "smoke"],
                "popularity": 64,
                "rating": 4.6
            },
            {
                "id": "tpl_callback_survey",
                "name": "Post-Call Survey — Outbound",
                "category": "Outbound CX",
                "role": "Customer Experience Specialist",
                "description": "Short satisfaction surveys after support or sales interactions.",
                "persona": "You are a brief, respectful survey agent. Ask three rating questions and thank the customer.",
                "language": "en-US",
                "recommended_tools": ["update_user_profile", "schedule_callback"],
                "goals": ["Complete survey", "Capture NPS score"],
                "success_criteria": ["survey completed"],
                "failure_conditions": ["declined", "no time"],
                "popularity": 72,
                "rating": 4.5
            }
        ]

    async def install_template(self, template_id: str, user_id: str) -> Agent:
        """Clones a template into the user's agent list."""
        all_templates = self.get_templates()
        template = next((t for t in all_templates if t["id"] == template_id), None)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")

        new_agent = Agent(
            name=f"{template['name']} (Custom)",
            role=template['role'],
            description=template['description'],
            persona=template['persona'],
            language=template['language'],
            tools=template['recommended_tools'],
            goals=template.get('goals', []),
            success_criteria=template.get('success_criteria', []),
            failure_conditions=template.get('failure_conditions', []),
            exit_actions=template.get('exit_actions', []),
            is_active=True,
        )
        
        self.db.add(new_agent)
        self.db.commit()
        self.db.refresh(new_agent)
        return new_agent
