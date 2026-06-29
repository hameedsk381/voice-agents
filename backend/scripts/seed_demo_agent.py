"""
Seed a demo collections agent for the public live-demo (homepage "Call Me Now").

Run:  python -m scripts.seed_demo_agent
Then set the printed agent id as DEMO_AGENT_ID in your .env and restart the API.

Idempotent: re-running updates the existing demo agent rather than duplicating it.
"""

import sys

from app.core.database import SessionLocal
from app.models.agent import Agent
from app.services.tools.registry import get_collections_toolset

DEMO_AGENT_NAME = "Voise Demo — EMI Collections"


def main() -> None:
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.name == DEMO_AGENT_NAME).first()
        persona = (
            "You are Asha from Voise AI, demonstrating an EMI collections call. "
            "Greet the person warmly, explain this is a short live demo of an AI collections agent, "
            "then role-play reminding them about a sample overdue EMI of 4,500 rupees. "
            "Be empathetic and never threatening. If they agree to pay, call record_promise_to_pay. "
            "Keep it under two minutes and end by inviting them to apply for a free pilot."
        )
        config = {
            "greeting": "Hi! This is a quick live demo of Voise AI's collections agent. May I show you how it works?",
            "company_name": "Voise AI",
        }
        tools = get_collections_toolset()

        if agent:
            agent.persona = persona
            agent.config = config
            agent.tools = tools
            agent.language = "en-IN"
            agent.is_active = True
            action = "Updated"
        else:
            agent = Agent(
                name=DEMO_AGENT_NAME,
                role="Collections Specialist",
                description="Public live-demo collections agent.",
                persona=persona,
                language="en-IN",
                tools=tools,
                goals=["Demonstrate a collections call", "Invite pilot signup"],
                success_criteria=["promise to pay", "pilot interest"],
                config=config,
                is_active=True,
            )
            db.add(agent)
            action = "Created"

        db.commit()
        db.refresh(agent)

        print(f"{action} demo agent.")
        print(f"DEMO_AGENT_ID={agent.id}")
        print("Set this in your .env and restart the API to enable the homepage live demo.")
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
