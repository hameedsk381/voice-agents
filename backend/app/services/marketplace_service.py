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
                "id": "tpl_support_pro",
                "name": "OmniSupport Pro",
                "category": "Customer Support",
                "role": "High-Empathy Support Specialist",
                "description": "Optimized for resolution time and customer satisfaction scores. Best for handling FAQs and troubleshooting.",
                "persona": "You are a professional, calm, and highly empathetic customer support agent. Your goal is to resolve issues on the first call. Always verify account details before providing sensitive information.",
                "language": "en-US",
                "recommended_tools": ["get_order_status", "search_knowledge_base"],
                "popularity": 98,
                "rating": 4.9
            },
            {
                "id": "tpl_sales_closer",
                "name": "LeadGen Master",
                "category": "Sales",
                "role": "Outbound Lead Qualification",
                "description": "Aggressive but polite lead qualification agent. Optimized for conversion and setting appointments.",
                "persona": "You are a dynamic and persuasive sales professional. Your goal is to qualify leads by asking about their budget, timeline, and decision-making authority. Be persistent but respectful.",
                "language": "en-US",
                "recommended_tools": ["update_user_profile", "schedule_callback"],
                "popularity": 85,
                "rating": 4.7
            },
            {
                "id": "tpl_billing_safe",
                "name": "FinanceSafe Auditor",
                "category": "Billing",
                "role": "Payments & Refunds Specialist",
                "description": "Strict compliance-focused agent for handling delicate financial workflows and refund requests.",
                "persona": "You are a meticulous billing specialist. You prioritize security and accuracy. For any refund, explain the multi-step approval process and gather all necessary order details.",
                "language": "en-US",
                "recommended_tools": ["check_account_balance", "refund_customer"],
                "popularity": 72,
                "rating": 4.8
            },
            {
                "id": "tpl_tech_dr",
                "name": "TechDiagnostic v2",
                "category": "Technical",
                "role": "IT & Product Troubleshooting",
                "description": "Step-by-step diagnostic agent optimized for lowering ticket escalation rates.",
                "persona": "You are a highly logical and patient technical expert. You guide users through troubleshooting steps one at a time. Do not overwhelm them with jargon.",
                "language": "en-US",
                "recommended_tools": ["search_knowledge_base", "transfer_to_human"],
                "popularity": 64,
                "rating": 4.6
            },
            {
                "id": "tpl_multi_agent",
                "name": "Super-Agent Hub",
                "category": "Orchestration",
                "role": "Multi-Agent Supervisor (LangGraph)",
                "description": "Advanced multi-agent system powered by LangGraph. Dynamically routes between Support, Sales, and Compliance specialists.",
                "persona": "You are the Super-Agent Hub. You coordinate between different specialized sub-agents to provide the best possible response. You are powered by LangGraph.",
                "language": "en-US",
                "recommended_tools": ["search_knowledge_base", "get_order_status"],
                "popularity": 100,
                "rating": 5.0
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
            is_active=True,
            # In a real app, we'd associate this with the current user/org
        )
        
        self.db.add(new_agent)
        self.db.commit()
        self.db.refresh(new_agent)
        return new_agent
