import pytest
from unittest.mock import MagicMock, patch
from app.services.marketplace_service import MarketplaceService, TEMPLATES


@pytest.fixture
def service():
    db = MagicMock()
    return MarketplaceService(db)


class TestGetTemplates:
    def test_returns_all_templates(self, service):
        templates = service.get_templates()
        assert len(templates) == 9
        assert all(t["id"] for t in templates)

    def test_all_tool_refs_are_valid(self, service):
        valid_tools = {
            "verify_aadhaar", "verify_pan", "check_upi_payment",
            "lookup_pincode", "check_gst", "translate_to_hindi",
            "check_loan_emi", "schedule_callback", "transfer_to_human",
            "search_knowledge_base",
        }
        for t in service.get_templates():
            for tool in t["recommended_tools"]:
                assert tool in valid_tools, f"{t['id']} references invalid tool: {tool}"

    def test_filter_by_category(self, service):
        templates = service.get_templates(category="Travel")
        assert len(templates) == 1
        assert templates[0]["id"] == "tpl_travel_guide"

    def test_filter_by_category_case_insensitive(self, service):
        templates = service.get_templates(category="travel")
        assert len(templates) == 1

    def test_filter_by_category_no_match(self, service):
        templates = service.get_templates(category="Nonexistent")
        assert len(templates) == 0


class TestInstallTemplate:
    @pytest.mark.asyncio
    async def test_install_creates_agent_with_org(self, service):
        template = TEMPLATES[0]
        agent = await service.install_template(template["id"], "user-1", organization_id="org-abc")

        service.db.add.assert_called_once()
        service.db.commit.assert_called_once()
        service.db.refresh.assert_called_once()

        added = service.db.add.call_args[0][0]
        assert added.name == f"{template['name']} (Custom)"
        assert added.organization_id == "org-abc"
        assert added.tools == template["recommended_tools"]
        assert added.is_active is True

    @pytest.mark.asyncio
    async def test_install_without_org(self, service):
        template = TEMPLATES[0]
        agent = await service.install_template(template["id"], "user-1")

        added = service.db.add.call_args[0][0]
        assert added.organization_id is None

    @pytest.mark.asyncio
    async def test_install_unknown_template(self, service):
        with pytest.raises(ValueError, match="not found"):
            await service.install_template("tpl_nonexistent", "user-1")

    def test_all_templates_have_required_fields(self, service):
        required = {"id", "name", "category", "role", "description", "persona",
                     "language", "recommended_tools", "goals", "success_criteria",
                     "failure_conditions", "popularity", "rating"}
        for t in TEMPLATES:
            missing = required - set(t.keys())
            assert not missing, f"{t['id']} missing fields: {missing}"
