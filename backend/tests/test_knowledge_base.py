import pytest
from unittest.mock import MagicMock
from app.services.knowledge_service import KnowledgeService

@pytest.fixture
def mock_db():
    return MagicMock()

def test_generate_embedding(mock_db, mocker):
    # Mock SentenceTransformer
    mock_model = MagicMock()
    mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
    
    mocker.patch.object(KnowledgeService, "get_embedding_model", return_value=mock_model)
    
    service = KnowledgeService(db=mock_db)
    
    embedding = service._generate_embedding("This is a test document")
    
    assert len(embedding) == 3
    assert embedding == [0.1, 0.2, 0.3]
    mock_model.encode.assert_called_once_with("This is a test document")

@pytest.mark.asyncio
async def test_add_knowledge(mock_db, mocker):
    mock_model = MagicMock()
    mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
    mocker.patch.object(KnowledgeService, "get_embedding_model", return_value=mock_model)
    
    service = KnowledgeService(db=mock_db)
    
    await service.add_knowledge(
        agent_id="agt-123",
        title="Refund Policy",
        content="Refunds are allowed within 30 days."
    )
    
    # Verify DB add was called
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    
    # Extract the added object
    added_obj = mock_db.add.call_args[0][0]
    assert added_obj.agent_id == "agt-123"
    assert added_obj.title == "Refund Policy"
    assert added_obj.embedding == [0.1, 0.2, 0.3]
