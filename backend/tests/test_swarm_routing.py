import pytest
from unittest.mock import AsyncMock, MagicMock
from app.orchestration.agent_swarm import SwarmOrchestrator
from app.models.agent import Agent

@pytest.fixture
def mock_supervisor():
    agent = Agent(id="sup-1", name="Supervisor", role="router")
    return agent

@pytest.fixture
def mock_pool():
    return [
        Agent(id="agent-id-billing-123", name="BillingAgent", role="billing", description="Handles payments"),
        Agent(id="agent-id-tech-supp", name="TechSupport", role="support", description="Handles tech issues")
    ]

@pytest.mark.asyncio
async def test_route_task_to_specialist(mock_supervisor, mock_pool, mocker):
    orchestrator = SwarmOrchestrator(db=None, supervisor_agent=mock_supervisor)
    
    # Mock LLM to return the billing agent ID
    mocker.patch.object(orchestrator.llm, "generate_response", return_value="agent-id-billing-123")
    
    selected_agent = await orchestrator.route_task("I want to pay my bill", [], mock_pool)
    
    assert selected_agent is not None
    assert selected_agent.id == "agent-id-billing-123"

@pytest.mark.asyncio
async def test_route_task_fallback_to_supervisor(mock_supervisor, mock_pool, mocker):
    orchestrator = SwarmOrchestrator(db=None, supervisor_agent=mock_supervisor)
    
    # Mock LLM to return SUPERVISOR
    mocker.patch.object(orchestrator.llm, "generate_response", return_value="SUPERVISOR")
    
    selected_agent = await orchestrator.route_task("Hello", [], mock_pool)
    
    assert selected_agent.id == mock_supervisor.id

@pytest.mark.asyncio
async def test_discover_and_hire(mock_supervisor, mock_pool, mocker):
    # Mock DB session
    mock_db = MagicMock()
    # Mock the query chain: db.query().filter().all()
    mock_db.query.return_value.filter.return_value.all.return_value = mock_pool
    
    orchestrator = SwarmOrchestrator(db=mock_db, supervisor_agent=mock_supervisor)
    
    # Mock LLM to return the tech support agent ID
    mocker.patch.object(orchestrator.llm, "generate_response", return_value="agent-id-tech-supp")
    
    discovered_agent = await orchestrator.discover_and_hire("My internet is down")
    
    assert discovered_agent is not None
    assert discovered_agent.id == "agent-id-tech-supp"
