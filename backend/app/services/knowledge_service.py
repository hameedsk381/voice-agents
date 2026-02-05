from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from loguru import logger
from sentence_transformers import SentenceTransformer
from app.models.knowledge import AgentKnowledge
from app.models.agent import Agent
from datetime import datetime
import uuid

class KnowledgeService:
    """
    Service for Agent Knowledge Base (RAG).
    Handles document ingestion, embedding generation, and semantic retrieval.
    """
    
    _embedding_model = None
    
    @classmethod
    def get_embedding_model(cls):
        if cls._embedding_model is None:
            logger.info("Loading knowledge embedding model (all-MiniLM-L6-v2)...")
            cls._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._embedding_model
        
    def __init__(self, db: Session):
        self.db = db
        self.model = self.get_embedding_model()
        
    def _generate_embedding(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    async def add_knowledge(
        self,
        agent_id: str,
        title: str,
        content: str,
        data_metadata: Dict[str, Any] = None,
        organization_id: str = None
    ) -> AgentKnowledge:
        """Add a new piece of knowledge to the agent."""
        embedding = self._generate_embedding(content)
        
        db_knowledge = AgentKnowledge(
            agent_id=agent_id,
            organization_id=organization_id,
            title=title,
            content=content,
            data_metadata=data_metadata or {},
            embedding=embedding
        )
        self.db.add(db_knowledge)
        self.db.commit()
        self.db.refresh(db_knowledge)
        return db_knowledge

    async def query_knowledge(
        self,
        agent_id: str,
        query_text: str,
        limit: int = 3,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on the agent's knowledge base.
        Returns the most relevant chunks.
        """
        query_embedding = self._generate_embedding(query_text)
        
        # pgvector cosine similarity search
        # 1 - (embedding <=> query_embedding) as score
        query = (
            self.db.query(
                AgentKnowledge,
                (1 - AgentKnowledge.embedding.cosine_distance(query_embedding)).label("score")
            )
            .filter(AgentKnowledge.agent_id == agent_id)
            .filter(AgentKnowledge.is_active == True)
            .order_by("score")
            .limit(limit)
        )
        
        results = query.all()
        
        formatted_results = []
        for knowledge, score in results:
            if score >= min_score:
                formatted_results.append({
                    "content": knowledge.content,
                    "title": knowledge.title,
                    "score": float(score),
                    "data_metadata": knowledge.data_metadata
                })
        
        return formatted_results

    async def delete_knowledge(self, knowledge_id: str):
        self.db.query(AgentKnowledge).filter(AgentKnowledge.id == knowledge_id).delete()
        self.db.commit()
