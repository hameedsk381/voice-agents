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
        description: str = None,
        concurrency_limit: int = 1,
        retry_config: Dict[str, Any] = None
    ) -> Campaign:
        campaign = Campaign(
            name=name,
            agent_id=agent_id,
            description=description,
            created_by=user_id,
            concurrency_limit=concurrency_limit,
            retry_config=retry_config or {"max_retries": 3, "retry_delay_minutes": 60}
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

    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        return self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

    async def list_campaigns(self, user_id: str = None) -> List[Campaign]:
        query = self.db.query(Campaign)
        if user_id:
            query = query.filter(Campaign.created_by == user_id)
        return query.order_by(Campaign.created_at.desc()).all()

    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        stats = self.db.query(
            CampaignContact.status, 
            func.count(CampaignContact.id)
        ).filter(CampaignContact.campaign_id == campaign_id).group_by(CampaignContact.status).all()
        
        return {status: count for status, count in stats}

    async def start_campaign(self, campaign_id: str):
        """Transition campaign to RUNNING status."""
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
            
        campaign.status = CampaignStatus.RUNNING.value
        self.db.commit()
        
        # Here we would trigger the Temporal workflow to start processing contacts
        logger.info(f"Campaign {campaign_id} started")
        return campaign

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
