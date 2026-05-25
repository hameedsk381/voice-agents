"""
Tests for CampaignService — CRUD, contacts, dial, start, org scoping.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from typing import Any, Dict

from app.services.campaign_service import CampaignService
from app.models.campaign import Campaign, CampaignContact, CampaignStatus, ContactStatus


def _fake_campaign(**kwargs) -> Campaign:
    defaults = dict(
        id="camp-1", name="Test Campaign", agent_id="agent-1",
        created_by="user-1", organization_id="default",
        status=CampaignStatus.DRAFT.value,
        total_contacts=0, completed_calls=0, failed_calls=0,
        retry_config={"max_retries": 3, "retry_delay_minutes": 60},
        call_config={},
    )
    defaults.update(kwargs)
    return Campaign(**defaults)


def _fake_contact(**kwargs) -> CampaignContact:
    defaults = dict(
        id="contact-1", campaign_id="camp-1",
        phone_number="+919999999999", contact_name="Raj",
        status=ContactStatus.PENDING.value,
        custom_data={},
    )
    defaults.update(kwargs)
    return CampaignContact(**defaults)


# ─── Create Campaign ─────────────────────────────────────────────────

class TestCreateCampaign:
    @pytest.mark.asyncio
    async def test_create_campaign_basic(self, mock_db):
        svc = CampaignService(mock_db)

        def _refresh(camp):
            camp.id = "new-camp-id"
        mock_db.refresh.side_effect = _refresh

        result = await svc.create_campaign(
            name="Promo Campaign",
            agent_id="agent-1",
            user_id="user-1",
            organization_id="default",
        )
        assert result.name == "Promo Campaign"
        assert result.agent_id == "agent-1"
        assert result.organization_id == "default"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_campaign_with_all_options(self, mock_db):
        svc = CampaignService(mock_db)

        def _refresh(camp):
            camp.id = "camp-full"
        mock_db.refresh.side_effect = _refresh

        result = await svc.create_campaign(
            name="Full Campaign",
            agent_id="agent-2",
            user_id="user-1",
            organization_id="org-1",
            description="A full config campaign",
            concurrency_limit=5,
            retry_config={"max_retries": 5, "retry_delay_minutes": 30},
            call_config={"greeting": "Hello"},
            workflow_id="wf-1",
        )
        assert result.name == "Full Campaign"
        assert result.organization_id == "org-1"
        assert result.workflow_id == "wf-1"


# ─── List/Get Campaigns ──────────────────────────────────────────────

class TestListGetCampaigns:
    @pytest.mark.asyncio
    async def test_list_campaigns_by_org(self, mock_db):
        c1 = _fake_campaign(id="c1")
        c2 = _fake_campaign(id="c2")
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [c1, c2]

        svc = CampaignService(mock_db)
        result = await svc.list_campaigns(organization_id="default")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_campaigns_by_user_fallback(self, mock_db):
        c = _fake_campaign()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [c]

        svc = CampaignService(mock_db)
        result = await svc.list_campaigns(user_id="user-1")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_campaign(self, mock_db):
        c = _fake_campaign()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = c

        svc = CampaignService(mock_db)
        result = await svc.get_campaign("camp-1", organization_id="default")
        assert result is not None
        assert result.id == "camp-1"

    @pytest.mark.asyncio
    async def test_get_campaign_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        svc = CampaignService(mock_db)
        result = await svc.get_campaign("nonexistent", organization_id="default")
        assert result is None


# ─── Contacts ────────────────────────────────────────────────────────

class TestContacts:
    @pytest.mark.asyncio
    async def test_add_contacts(self, mock_db):
        c = _fake_campaign(total_contacts=0)
        mock_db.query.return_value.filter.return_value.first.return_value = c
        mock_db.commit = MagicMock()

        svc = CampaignService(mock_db)
        count = await svc.add_contacts("camp-1", [
            {"phone_number": "+911111111111", "contact_name": "Alice"},
            {"phone_number": "+912222222222", "contact_name": "Bob"},
        ])
        assert count == 2
        # Should have updated contact count
        assert c.total_contacts == 2

    @pytest.mark.asyncio
    async def test_list_contacts(self, mock_db):
        ct1 = _fake_contact(id="ct-1")
        ct2 = _fake_contact(id="ct-2")
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [ct1, ct2]

        svc = CampaignService(mock_db)
        result = await svc.list_contacts("camp-1")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_contact_status(self, mock_db):
        ct = _fake_contact()
        mock_db.query.return_value.filter.return_value.first.return_value = ct

        svc = CampaignService(mock_db)
        await svc.update_contact_status("contact-1", ContactStatus.COMPLETED)
        assert ct.status == ContactStatus.COMPLETED.value


# ─── Start Campaign ──────────────────────────────────────────────────

class TestStartCampaign:
    @pytest.mark.asyncio
    async def test_start_campaign_no_workflow(self, mock_db):
        c = _fake_campaign(status=CampaignStatus.DRAFT.value)
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = c

        svc = CampaignService(mock_db)
        result = await svc.start_campaign("camp-1", organization_id="default")
        assert result.status == CampaignStatus.RUNNING.value

    @pytest.mark.asyncio
    async def test_start_campaign_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        svc = CampaignService(mock_db)
        with pytest.raises(ValueError, match="Campaign not found"):
            await svc.start_campaign("nonexistent")


# ─── Stats ───────────────────────────────────────────────────────────

class TestStats:
    @pytest.mark.asyncio
    async def test_get_campaign_stats(self, mock_db):
        mock_row_completed = MagicMock()
        mock_row_completed.__iter__.return_value = iter([ContactStatus.COMPLETED.value, 5])
        mock_row_pending = MagicMock()
        mock_row_pending.__iter__.return_value = iter([ContactStatus.PENDING.value, 3])
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            mock_row_completed, mock_row_pending,
        ]

        svc = CampaignService(mock_db)
        stats = await svc.get_campaign_stats("camp-1")
        assert stats.get(ContactStatus.COMPLETED.value) == 5
        assert stats.get(ContactStatus.PENDING.value) == 3


# ─── Org Scoping ─────────────────────────────────────────────────────

class TestOrgScoping:
    @pytest.mark.asyncio
    async def test_create_campaign_sets_org(self, mock_db):
        svc = CampaignService(mock_db)

        def _refresh(camp):
            camp.id = "scoped-camp"
        mock_db.refresh.side_effect = _refresh

        result = await svc.create_campaign(
            name="Scoped", agent_id="a1", user_id="u1", organization_id="org-alpha",
        )
        assert result.organization_id == "org-alpha"

    @pytest.mark.asyncio
    async def test_list_campaigns_filters_by_org(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        svc = CampaignService(mock_db)
        result = await svc.list_campaigns(organization_id="org-alpha")
        assert result == []
        # Verify the filter was applied
        mock_db.query.assert_called_once()
