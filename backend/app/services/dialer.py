import asyncio
import uuid
from loguru import logger

from app.core.database import SessionLocal
from app.models.campaign import Campaign, CampaignContact, CampaignStatus, ContactStatus
from app.models.agent import Agent
from app.orchestration.pipecat_pipeline import run_pipecat_agent

async def dialer_loop():
    logger.info("Starting background dialer loop...")
    while True:
        try:
            db = SessionLocal()
            # Find running campaigns
            campaigns = db.query(Campaign).filter(Campaign.status == CampaignStatus.RUNNING.value).all()
            for campaign in campaigns:
                # Check concurrency limit
                in_progress = db.query(CampaignContact).filter(
                    CampaignContact.campaign_id == campaign.id,
                    CampaignContact.status == ContactStatus.IN_PROGRESS.value
                ).count()
                
                available_slots = (campaign.concurrency_limit or 1) - in_progress
                if available_slots <= 0:
                    continue
                    
                pending_contacts = db.query(CampaignContact).filter(
                    CampaignContact.campaign_id == campaign.id,
                    CampaignContact.status == ContactStatus.PENDING.value
                ).limit(available_slots).all()
                
                for contact in pending_contacts:
                    contact.status = ContactStatus.IN_PROGRESS.value
                    contact.session_id = str(uuid.uuid4())
                    db.commit()
                    
                    agent = db.query(Agent).filter(Agent.id == campaign.agent_id).first()
                    
                    # Spawn pipecat agent in background
                    asyncio.create_task(
                        run_pipecat_agent(
                            room_name=contact.session_id,
                            system_prompt=agent.system_prompt if agent else "You are an AI.",
                            greeting=campaign.call_config.get("greeting", "Hello!"),
                            agent_id=campaign.agent_id,
                            session_id=contact.session_id,
                            active_tools=agent.tools if agent else []
                        )
                    )
                    logger.info(f"Dialer spawned Pipecat for contact {contact.phone_number} (session: {contact.session_id})")
                    
        except Exception as e:
            logger.error(f"Error in dialer loop: {e}")
        finally:
            if 'db' in locals():
                db.close()
                
        await asyncio.sleep(5) # Poll every 5 seconds
