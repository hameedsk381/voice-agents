"""
Campaign service to manage outbound call workflows.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
from loguru import logger

from app.models.campaign import Campaign, CampaignContact, CampaignStatus, ContactStatus
from app.models.agent import Agent

class CampaignService:
    def __init__(self, db: Session):
        self.db = db

    async def create_campaign(
        self, 
        name: str, 
        agent_id: str, 
        user_id: str,
        organization_id: Optional[str] = None,
        description: str = None,
        concurrency_limit: int = 1,
        retry_config: Dict[str, Any] = None,
        call_config: Dict[str, Any] = None,
        workflow_id: str = None,
    ) -> Campaign:
        campaign = Campaign(
            name=name,
            agent_id=agent_id,
            description=description,
            created_by=user_id,
            organization_id=organization_id,
            workflow_id=workflow_id,
            concurrency_limit=concurrency_limit,
            retry_config=retry_config or {"max_retries": 3, "retry_delay_minutes": 60},
            call_config=call_config or {},
        )
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    async def add_contacts(self, campaign_id: str, contacts: List[Dict[str, Any]]):
        """Add contacts to a campaign."""
        batch = []
        for c in contacts:
            contact = CampaignContact(
                campaign_id=campaign_id,
                phone_number=c["phone_number"],
                contact_name=c.get("contact_name"),
                custom_data=c.get("custom_data", {})
            )
            batch.append(contact)
        
        self.db.bulk_save_objects(batch)
        
        # Update campaign total count
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.total_contacts += len(batch)
            self.db.commit()
            
        return len(batch)

    async def get_campaign(self, campaign_id: str, organization_id: Optional[str] = None) -> Optional[Campaign]:
        q = self.db.query(Campaign).filter(Campaign.id == campaign_id)
        if organization_id:
            q = q.filter(Campaign.organization_id == organization_id)
        return q.first()

    async def list_campaigns(self, user_id: str = None, organization_id: Optional[str] = None) -> List[Campaign]:
        query = self.db.query(Campaign)
        if organization_id:
            query = query.filter(Campaign.organization_id == organization_id)
        elif user_id:
            query = query.filter(Campaign.created_by == user_id)
        return query.order_by(Campaign.created_at.desc()).all()

    async def list_contacts(self, campaign_id: str) -> List[CampaignContact]:
        return (
            self.db.query(CampaignContact)
            .filter(CampaignContact.campaign_id == campaign_id)
            .order_by(CampaignContact.created_at.desc())
            .all()
        )

    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        stats = self.db.query(
            CampaignContact.status, 
            func.count(CampaignContact.id)
        ).filter(CampaignContact.campaign_id == campaign_id).group_by(CampaignContact.status).all()
        
        return {status: count for status, count in stats}

    async def start_campaign(self, campaign_id: str, organization_id: Optional[str] = None):
        """Transition campaign to RUNNING and start linked workflow instances."""
        campaign = await self.get_campaign(campaign_id, organization_id=organization_id)
        if not campaign:
            raise ValueError("Campaign not found")
            
        campaign.status = CampaignStatus.RUNNING.value
        self.db.commit()

        instances_started = 0
        if campaign.workflow_id:
            from app.services.workflow_service import WorkflowService

            wf_service = WorkflowService(self.db)
            pending = (
                self.db.query(CampaignContact)
                .filter(
                    CampaignContact.campaign_id == campaign_id,
                    CampaignContact.status == ContactStatus.PENDING.value,
                )
                .all()
            )
            for contact in pending:
                ctx = dict(contact.custom_data or {})
                ctx.update(
                    {
                        "customer_name": contact.contact_name,
                        "phone_number": contact.phone_number,
                        "campaign_id": campaign_id,
                        "contact_id": contact.id,
                        "agent_id": campaign.agent_id,
                    }
                )
                try:
                    await wf_service.create_instance(
                        campaign.workflow_id,
                        context=ctx,
                        campaign_id=campaign_id,
                        contact_id=contact.id,
                        agent_id=campaign.agent_id,
                        auto_start=True,
                    )
                    contact.status = ContactStatus.QUEUED.value
                    instances_started += 1
                except Exception as exc:
                    logger.warning(f"Workflow start failed for contact {contact.id}: {exc}")
            self.db.commit()

        logger.info(f"Campaign {campaign_id} started, workflow instances={instances_started}")
        return campaign

    async def update_call_config(
        self, campaign_id: str, call_config: Dict[str, Any],
        organization_id: Optional[str] = None,
    ) -> Optional[Campaign]:
        campaign = await self.get_campaign(campaign_id, organization_id=organization_id)
        if not campaign:
            return None
        merged = dict(campaign.call_config or {})
        merged.update(call_config)
        campaign.call_config = merged
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    async def dial_contact(
        self,
        campaign_id: str,
        contact_id: str,
        from_number: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place an outbound Ultravox/Twilio call for one campaign contact."""
        from app.core.config import settings
        import os
        from app.orchestration.ultravox_twilio import create_ultravox_twilio_call

        campaign = await self.get_campaign(campaign_id, organization_id=organization_id)
        if not campaign:
            raise ValueError("Campaign not found")

        contact = (
            self.db.query(CampaignContact)
            .filter(
                CampaignContact.id == contact_id,
                CampaignContact.campaign_id == campaign_id,
            )
            .first()
        )
        if not contact:
            raise ValueError("Contact not found")

        agent = self.db.query(Agent).filter(Agent.id == campaign.agent_id).first()
        if not agent:
            raise ValueError("Agent not found for campaign")

        from_e164 = (
            from_number
            or settings.TWILIO_PHONE_NUMBER
            or os.getenv("TWILIO_FROM_NUMBER")
        )
        if not from_e164:
            raise ValueError("Missing TWILIO_PHONE_NUMBER for outbound dial")

        contact.status = ContactStatus.IN_PROGRESS.value
        self.db.commit()

        created = await create_ultravox_twilio_call(
            db=self.db,
            agent=agent,
            call_direction="outbound",
            caller_id=from_e164,
            called_number=contact.phone_number,
            twilio_call_sid=None,
            outgoing_to=contact.phone_number,
            outgoing_from=from_e164,
            campaign=campaign,
            campaign_contact=contact,
        )
        contact.session_id = created["session_id"]
        self.db.commit()

        return {
            "status": "initiated",
            "session_id": created["session_id"],
            "call_id": created["call"].get("callId"),
            "contact_id": contact.id,
        }

    async def update_contact_status(
        self, 
        contact_id: str, 
        status: ContactStatus, 
        error: str = None,
        session_id: str = None
    ):
        contact = self.db.query(CampaignContact).filter(CampaignContact.id == contact_id).first()
        if contact:
            contact.status = status.value
            if error:
                contact.error_message = error
            if session_id:
                contact.session_id = session_id
                
            if status == ContactStatus.COMPLETED:
                # Increment campaign success count
                self.db.query(Campaign).filter(Campaign.id == contact.campaign_id).update({
                    "completed_calls": Campaign.completed_calls + 1
                })
            elif status == ContactStatus.FAILED:
                self.db.query(Campaign).filter(Campaign.id == contact.campaign_id).update({
                    "failed_calls": Campaign.failed_calls + 1
                })
                
            self.db.commit()
