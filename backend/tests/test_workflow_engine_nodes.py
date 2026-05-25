"""
Tests for new workflow engine node types: SMS, webhook, DB query, fork/join, agent_task,
and the fork branch switching logic in run_until_wait_or_done.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from typing import Any, Dict

from app.workflows.schema import (
    NodeType,
    WorkflowDefinitionV1,
    WorkflowNode,
    StepResult,
)
from app.workflows.engine import WorkflowEngine, _render_template


# ─── _render_template ───────────────────────────────────────────────

class TestRenderTemplate:
    def test_simple_substitution(self):
        ctx = {"name": "Alice", "amount": 1500}
        result = _render_template("Hello {{name}}, pay ₹{{amount}}", ctx)
        assert result == "Hello Alice, pay ₹1500"

    def test_missing_var_returns_empty(self):
        result = _render_template("Hi {{unknown}}", {})
        assert result == "Hi "

    def test_default_value(self):
        result = _render_template("Hi {{name|Guest}}", {})
        assert result == "Hi Guest"

    def test_default_falls_back_when_none(self):
        result = _render_template("Hi {{name|Guest}}", {"name": None})
        assert result == "Hi Guest"

    def test_no_template_returns_original(self):
        result = _render_template("plain text", {"x": "y"})
        assert result == "plain text"

    def test_numeric_context_value(self):
        result = _render_template("Amount: {{amount}}", {"amount": 2500})
        assert result == "Amount: 2500"


# ─── SMS Node ────────────────────────────────────────────────────────

class TestSmsNode:
    @pytest.mark.asyncio
    async def test_sms_sent_successfully(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="sms1", type=NodeType.SMS, config={
            "message": "Dear {{customer_name}}, your payment is due.",
        })
        ctx = {"customer_name": "Raj", "phone_number": "+919999999999"}
        meta = {"instance_id": "inst-1"}

        with patch("twilio.rest.Client") as mock_client, \
             patch("app.core.config.settings") as mock_settings:
            mock_client.return_value.messages.create.return_value.sid = "SM123"
            mock_settings.TWILIO_ACCOUNT_SID = "ACxxx"
            mock_settings.TWILIO_AUTH_TOKEN = "tok"
            mock_settings.TWILIO_PHONE_NUMBER = "+18005551234"
            result = await engine.execute_node(node, ctx, meta)

        assert result.status == "continue"
        assert result.context_patch.get("last_sms_status") == "sent"

    @pytest.mark.asyncio
    async def test_sms_skipped_no_phone(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="sms1", type=NodeType.SMS, config={
            "message": "Hello",
        })
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}
        result = await engine.execute_node(node, ctx, meta)
        assert result.status == "continue"
        assert result.context_patch.get("last_sms_status") == "skipped"

    @pytest.mark.asyncio
    async def test_sms_phone_from_config(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="sms1", type=NodeType.SMS, config={
            "to_phone": "+911234567890",
            "message": "Test",
        })
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}

        with patch("twilio.rest.Client") as mock_client, \
             patch("app.core.config.settings") as mock_settings:
            mock_client.return_value.messages.create.return_value.sid = "SM456"
            mock_settings.TWILIO_ACCOUNT_SID = "ACxxx"
            mock_settings.TWILIO_AUTH_TOKEN = "tok"
            mock_settings.TWILIO_PHONE_NUMBER = "+18005551234"
            result = await engine.execute_node(node, ctx, meta)

        assert result.context_patch.get("last_sms_status") == "sent"


# ─── Webhook Node ────────────────────────────────────────────────────

class TestWebhookNode:
    @pytest.mark.asyncio
    async def test_webhook_post_success(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="wh1", type=NodeType.WEBHOOK, config={
            "url": "https://api.example.com/tickets",
            "method": "POST",
            "headers": {"Authorization": "Bearer tok"},
            "body_template": '{"customer": "{{name}}"}',
            "response_key": "ticket_resp",
        })
        ctx = {"name": "Raj"}
        meta: Dict[str, Any] = {}

        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.status_code = 201
        mock_response.text = '{"id": "TKT-123"}'

        mock_hc = AsyncMock()
        mock_hc.__aenter__.return_value.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_hc):
            result = await engine.execute_node(node, ctx, meta)

        assert result.status == "continue"
        assert result.context_patch.get("last_webhook_status") == "success"

    @pytest.mark.asyncio
    async def test_webhook_get(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="wh1", type=NodeType.WEBHOOK, config={
            "url": "https://api.example.com/status/{{order_id}}",
            "method": "GET",
            "response_key": "status_resp",
        })
        ctx = {"order_id": "ORD-99"}
        meta: Dict[str, Any] = {}

        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.text = '{"status": "shipped"}'

        mock_hc = AsyncMock()
        mock_hc.__aenter__.return_value.get.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_hc):
            result = await engine.execute_node(node, ctx, meta)

        assert result.status == "continue"
        assert result.context_patch.get("last_webhook_status") == "success"

    @pytest.mark.asyncio
    async def test_webhook_http_error(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="wh1", type=NodeType.WEBHOOK, config={
            "url": "https://api.example.com/fail",
            "response_key": "resp",
        })
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}

        mock_response = AsyncMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.text = "Server error"

        mock_hc = AsyncMock()
        mock_hc.__aenter__.return_value.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_hc):
            result = await engine.execute_node(node, ctx, meta)

        assert result.status == "continue"
        assert "http_500" in result.context_patch.get("last_webhook_status", "")

    @pytest.mark.asyncio
    async def test_webhook_no_url_skipped(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="wh1", type=NodeType.WEBHOOK, config={})
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}
        result = await engine.execute_node(node, ctx, meta)
        assert result.status == "continue"
        assert result.context_patch.get("last_webhook_status") == "skipped"


# ─── DB Query Node ───────────────────────────────────────────────────

class TestDbQueryNode:
    @pytest.mark.asyncio
    async def test_db_query_returns_rows(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="dq1", type=NodeType.DB_QUERY, config={
            "query": "SELECT name, email FROM customers WHERE id = :customer_id",
            "result_key": "customer_data",
        })
        ctx = {"customer_id": "CUST-001"}
        meta: Dict[str, Any] = {}

        mock_row = MagicMock()
        mock_row._mapping = {"name": "Raj", "email": "raj@test.com"}
        mock_db.execute.return_value.fetchall.return_value = [mock_row]

        result = await engine.execute_node(node, ctx, meta)

        assert result.status == "continue"
        assert result.context_patch.get("customer_data") == [{"name": "Raj", "email": "raj@test.com"}]
        assert result.context_patch.get("last_db_query_status") == "1 rows"

    @pytest.mark.asyncio
    async def test_db_query_empty(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="dq1", type=NodeType.DB_QUERY, config={
            "query": "SELECT * FROM customers WHERE 1=0",
            "result_key": "data",
        })
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}
        mock_db.execute.return_value.fetchall.return_value = []
        result = await engine.execute_node(node, ctx, meta)
        assert result.context_patch.get("data") == []
        assert result.context_patch.get("last_db_query_status") == "0 rows"

    @pytest.mark.asyncio
    async def test_db_query_no_query_skipped(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="dq1", type=NodeType.DB_QUERY, config={})
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}
        result = await engine.execute_node(node, ctx, meta)
        assert result.context_patch.get("last_db_query_status") == "skipped"

    @pytest.mark.asyncio
    async def test_db_query_error(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="dq1", type=NodeType.DB_QUERY, config={
            "query": "SELECT * FROM nonexistent",
        })
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}
        mock_db.execute.side_effect = Exception("Table not found")
        result = await engine.execute_node(node, ctx, meta)
        assert result.context_patch.get("last_db_query_status") == "failed"


# ─── FORK Node ───────────────────────────────────────────────────────

class TestForkNode:
    @pytest.mark.asyncio
    async def test_fork_sets_tracker_and_routes(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(
            id="fork1", type=NodeType.FORK,
            config={"branches": ["b1", "b2"]},
            next="join1",
        )
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}
        result = await engine.execute_node(node, ctx, meta)

        assert result.status == "continue"
        assert result.next_node_id == "b1"
        tracker = result.context_patch.get("_fork_tracker")
        assert tracker is not None
        assert tracker["branches"] == ["b1", "b2"]
        assert tracker["pending"] == ["b1", "b2"]
        assert tracker["join_node"] == "join1"

    @pytest.mark.asyncio
    async def test_fork_empty_branches(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(
            id="fork1", type=NodeType.FORK,
            config={},
            next="join1",
        )
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}
        result = await engine.execute_node(node, ctx, meta)
        # No branches → go to next
        assert result.next_node_id == "join1"


# ─── JOIN Node ───────────────────────────────────────────────────────

class TestJoinNode:
    @pytest.mark.asyncio
    async def test_join_pops_pending_routes_next_branch(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="join1", type=NodeType.JOIN, next="continue_id")
        ctx: Dict[str, Any] = {
            "_fork_tracker": {
                "branches": ["b1", "b2"],
                "pending": ["b1", "b2"],
                "join_node": "join1",
            }
        }
        meta: Dict[str, Any] = {}
        result = await engine.execute_node(node, ctx, meta)

        assert result.status == "continue"
        assert result.next_node_id == "b2"

    @pytest.mark.asyncio
    async def test_join_all_branches_done(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="join1", type=NodeType.JOIN, next="continue_id")
        ctx: Dict[str, Any] = {
            "_fork_tracker": {
                "branches": ["b1"],
                "pending": [],
                "join_node": "join1",
            }
        }
        meta: Dict[str, Any] = {}
        result = await engine.execute_node(node, ctx, meta)

        assert result.status == "continue"
        assert result.next_node_id == "continue_id"
        assert result.context_patch.get("_fork_tracker") is None

    @pytest.mark.asyncio
    async def test_join_no_fork_context_pass_through(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="join1", type=NodeType.JOIN, next="continue_id")
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}
        result = await engine.execute_node(node, ctx, meta)
        assert result.status == "continue"
        assert result.next_node_id == "continue_id"


# ─── agent_task Node ─────────────────────────────────────────────────

class TestAgentTaskNode:
    @pytest.mark.asyncio
    async def test_agent_task_routes_to_capability(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="at1", type=NodeType.AGENT_TASK, config={
            "capability": "collections",
            "input": "Handle payment follow-up",
        })
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}

        mock_agent = MagicMock()
        mock_agent.id = "target-agent-id"
        mock_agent.name = "Collections Bot"

        mock_registry = MagicMock()
        mock_registry.find_agent_for_capability.return_value = mock_agent

        mock_swarm = MagicMock()
        mock_swarm.route_task = AsyncMock()
        mock_swarm.route_task.return_value.name = "Collections Bot"

        with patch("app.services.agent_registry_service.AgentRegistryService", return_value=mock_registry), \
             patch("app.orchestration.agent_swarm.SwarmOrchestrator", return_value=mock_swarm), \
             patch("app.models.agent.Agent") as mock_agent_model:
            mock_db.query.return_value.filter.return_value.first.return_value = mock_agent
            result = await engine.execute_node(node, ctx, meta)

        assert result.status == "continue"

    @pytest.mark.asyncio
    async def test_agent_task_no_target_fails(self, mock_db):
        engine = WorkflowEngine(mock_db)
        node = WorkflowNode(id="at1", type=NodeType.AGENT_TASK, config={
            "capability": "nonexistent",
        })
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}

        mock_registry = MagicMock()
        mock_registry.find_agent_for_capability.return_value = None

        with patch("app.services.agent_registry_service.AgentRegistryService", return_value=mock_registry):
            result = await engine.execute_node(node, ctx, meta)

        assert result.status == "failed"
        assert "no_target_agent" in result.context_patch.get("agent_task_error", "")


# ─── run_until_wait_or_done: Fork branch switching ───────────────────

class TestForkBranchSwitching:
    def _make_def(self, nodes):
        return WorkflowDefinitionV1(version="1", entry=nodes[0].id, nodes=nodes)

    @pytest.mark.asyncio
    async def test_branch_completes_switches_to_next(self, mock_db):
        """Branch 1 hits END → engine should switch to branch 2 instead of completing."""
        engine = WorkflowEngine(mock_db)
        fork_node = WorkflowNode(
            id="fork1", type=NodeType.FORK,
            config={"branches": ["b1_end", "b2_end"]},
            next="join1",
        )
        b1_end = WorkflowNode(id="b1_end", type=NodeType.END, config={"outcome": "done"})
        b2_end = WorkflowNode(id="b2_end", type=NodeType.END, config={"outcome": "done"})
        join_node = WorkflowNode(id="join1", type=NodeType.JOIN, next="final")
        final = WorkflowNode(id="final", type=NodeType.END, config={"outcome": "all_done"})

        definition = self._make_def([fork_node, b1_end, b2_end, join_node, final])
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}

        result = await engine.run_until_wait_or_done(
            definition, current_node_id="fork1", context=ctx, instance_meta=meta,
        )

        assert result["status"] == "completed"
        assert ctx.get("workflow_outcome") == "all_done"

    @pytest.mark.asyncio
    async def test_all_branches_complete_continues_from_join(self, mock_db):
        """Both branches hit END → engine continues from JOIN's next."""
        engine = WorkflowEngine(mock_db)
        fork_node = WorkflowNode(
            id="fork1", type=NodeType.FORK,
            config={"branches": ["b1_end", "b2_end"]},
            next="join1",
        )
        b1_end = WorkflowNode(id="b1_end", type=NodeType.END, config={"outcome": "b1_done"})
        b2_end = WorkflowNode(id="b2_end", type=NodeType.END, config={"outcome": "b2_done"})
        join_node = WorkflowNode(id="join1", type=NodeType.JOIN, next="final")
        final = WorkflowNode(id="final", type=NodeType.END, config={"outcome": "merged"})

        definition = self._make_def([fork_node, b1_end, b2_end, join_node, final])
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}

        result = await engine.run_until_wait_or_done(
            definition, current_node_id="fork1", context=ctx, instance_meta=meta,
        )

        # Both branches hit END immediately → merge at join → final END
        assert result["status"] == "completed"
        assert ctx.get("workflow_outcome") == "merged"

    @pytest.mark.asyncio
    async def test_branch_with_wait_returns_waiting(self, mock_db):
        """One branch has a WAIT → engine should pause and wait for it."""
        engine = WorkflowEngine(mock_db)
        fork_node = WorkflowNode(
            id="fork1", type=NodeType.FORK,
            config={"branches": ["b1_long_wait", "b2_quick"]},
            next="join1",
        )
        b1_long_wait = WorkflowNode(id="b1_long_wait", type=NodeType.WAIT, config={"minutes": 60}, next="join1")
        b2_quick = WorkflowNode(id="b2_quick", type=NodeType.WAIT, config={"minutes": 0}, next="join1")
        join_node = WorkflowNode(id="join1", type=NodeType.JOIN, next="final")
        final = WorkflowNode(id="final", type=NodeType.END, config={"outcome": "done"})

        definition = self._make_def([fork_node, b1_long_wait, b2_quick, join_node, final])
        ctx: Dict[str, Any] = {}
        meta: Dict[str, Any] = {}

        result = await engine.run_until_wait_or_done(
            definition, current_node_id="fork1", context=ctx, instance_meta=meta,
        )

        # First branch has wait=60 → should return waiting
        # Quick branch would complete but we're stuck on the waiting first branch
        assert result["status"] == "waiting"
