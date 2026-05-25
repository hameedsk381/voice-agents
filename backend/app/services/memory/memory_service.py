"""
Memory service for long-term user memory and cross-call context.
Inspired by memU's proactive memory architecture.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func
from sentence_transformers import SentenceTransformer
from loguru import logger
import json

from app.models.memory import MemoryItem, ConversationSummary, UserProfile, WorkingMemory, ProceduralMemory
from app.services.compliance_service import redactor
from datetime import timedelta


class MemoryService:
    """
    Provides long-term memory capabilities for voice agents.
    - Memorize: Extract and store facts from conversations
    - Retrieve: Semantic search across user memories
    - Profile: Aggregate user information over time
    """
    
    _embedding_model = None
    
    @classmethod
    def get_embedding_model(cls):
        """Lazy load the embedding model."""
        if cls._embedding_model is None:
            logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
            cls._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded")
        return cls._embedding_model
    
    def __init__(self, db: Session):
        self.db = db
        self.model = self.get_embedding_model()
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        return self.model.encode(text).tolist()
    
    # ==================== MEMORIZE ====================
    
    async def memorize(
        self,
        user_id: str,
        category: str,
        key: str,
        value: str,
        memory_type: str = "user_claim",
        agent_id: str = None,
        session_id: str = None,
        confidence: float = 1.0,
        ttl_seconds: int = None,
        is_sensitive: bool = False,
        organization_id: str = None
    ) -> MemoryItem:
        """
        Store a memory fact. Updates existing memory if key exists.
        """
        # Check if memory exists
        existing = self.db.query(MemoryItem).filter(
            MemoryItem.user_id == user_id,
            MemoryItem.key == key,
            MemoryItem.organization_id == organization_id
        ).first()

        # Respect do_not_remember — refuse to create new memories under this key
        if not existing and self.db.query(MemoryItem).filter(
            MemoryItem.user_id == user_id,
            MemoryItem.key == key,
            MemoryItem.do_not_remember == True
        ).first():
            logger.info(f"Skipping memorize for {user_id}/{key}: flagged do_not_remember")
            return None

        if existing:
            # Update existing memory
            # Mandatory PII masking at storage layer for sensitive fields
            final_value = redactor.redact_text(value) if is_sensitive else value
            
            existing.value = final_value
            existing.memory_type = memory_type
            existing.confidence = max(existing.confidence, confidence)
            existing.updated_at = datetime.utcnow()
            existing.embedding = self._generate_embedding(f"[{memory_type}] {category}: {key} = {value}")
            self.db.commit()
            logger.info(f"Updated memory [{memory_type}] for user {user_id}: {key}")
            return existing
        
        # Create new memory
        embedding = self._generate_embedding(f"[{memory_type}] {category}: {key} = {value}")
        
        # Mandatory PII masking at storage layer for sensitive fields
        final_value = redactor.redact_text(value) if is_sensitive else value
        
        memory = MemoryItem(
            user_id=user_id,
            organization_id=organization_id,
            agent_id=agent_id,
            category=category,
            memory_type=memory_type,
            key=key,
            value=final_value,
            source_session_id=session_id,
            confidence=confidence,
            embedding=embedding,
            expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds) if ttl_seconds else None,
            is_sensitive=is_sensitive
        )
        
        self.db.add(memory)
        self.db.commit()
        logger.info(f"Stored new memory for user {user_id}: {key} = {value}")
        return memory
    
    async def memorize_from_conversation(
        self,
        user_id: str,
        conversation: List[Dict[str, str]],
        agent_id: str = None,
        session_id: str = None,
        llm_service = None,
        organization_id: str = None
    ) -> List[MemoryItem]:
        """
        Extract and store memories from a conversation using LLM.
        """
        if not llm_service:
            logger.warning("No LLM service provided for memory extraction")
            return []
        
        # 1. Check for "Do Not Remember" signal
        conv_text_full = "\n".join([m['content'].lower() for m in conversation])
        if any(trigger in conv_text_full for trigger in ["forget this", "don't remember", "do not store", "delete my data"]):
            logger.info(f"Memory extraction skipped due to user preference for session {session_id}")
            return []

        # 2. Check for Consent
        profile = await self.get_or_create_profile(user_id)
        if profile.consent_status == "withdrawn":
            logger.warning(f"Memory extraction skipped: User {user_id} has withdrawn consent")
            return []

        # Build extraction prompt with PII Redaction
        conv_text = "\n".join([f"{m['role']}: {redactor.redact_text(m['content'])}" for m in conversation])
        
        extraction_prompt = f"""Analyze this conversation and extract key facts about the user.
Return a JSON array of memory items to store. Each item should have:
- category: one of [personal_info, preferences, history, feedback, needs]
- type: one of [user_claim, system_verified, regulated_fact]
- key: specific attribute (e.g., "name", "favorite_product", "complaint_topic")
- value: the extracted value
- confidence: 0.0-1.0 how certain you are
- is_sensitive: true/false if this contains PII or private data
- ttl_seconds: optional integer for how long this should be remembered (e.g. 3600 for 1 hour)

Note: Most facts from conversation are 'user_claim' unless explicitly confirmed by the agent or a system tool.

Conversation:
{conv_text}

Return ONLY valid JSON array, no other text:"""

        try:
            response = await llm_service.generate_response(
                extraction_prompt,
                "You are a memory extraction system. Extract factual information only.",
                []
            )
            
            # Parse JSON response
            memories_data = json.loads(response)
            memories = []
            
            for item in memories_data:
                memory = await self.memorize(
                    user_id=user_id,
                    category=item.get("category", "general"),
                    key=item["key"],
                    value=item["value"],
                    memory_type=item.get("type", "user_claim"),
                    agent_id=agent_id,
                    session_id=session_id,
                    ttl_seconds=item.get("ttl_seconds"),
                    is_sensitive=item.get("is_sensitive", False),
                    organization_id=organization_id
                )
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to extract memories: {e}")
            return []
    
    # ==================== RETRIEVE ====================
    
    async def retrieve(
        self,
        query: str,
        user_id: str = None,
        category: str = None,
        limit: int = 10,
        min_confidence: float = 0.5,
        organization_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across memories.
        """
        query_embedding = self._generate_embedding(query)
        
        # Build query
        stmt = select(
            MemoryItem,
            MemoryItem.embedding.cosine_distance(query_embedding).label('distance')
        )
        
        filters = [
            MemoryItem.confidence >= min_confidence,
            MemoryItem.do_not_remember == False,
            or_(MemoryItem.expires_at == None, MemoryItem.expires_at > datetime.utcnow())
        ]
        if user_id:
            filters.append(MemoryItem.user_id == user_id)
        if organization_id:
            filters.append(MemoryItem.organization_id == organization_id)
        if category:
            filters.append(MemoryItem.category == category)
        
        stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by('distance').limit(limit)
        
        results = self.db.execute(stmt).all()
        
        memories = []
        for memory, distance in results:
            # Update access tracking
            memory.last_accessed_at = datetime.utcnow()
            memory.access_count += 1
            
            memories.append({
                "id": memory.id,
                "category": memory.category,
                "type": memory.memory_type,
                "key": memory.key,
                "value": memory.value,
                "confidence": memory.confidence,
                "relevance": 1 - distance,  # Convert distance to similarity
                "is_sensitive": memory.is_sensitive,
                "last_updated": memory.updated_at.isoformat() if memory.updated_at else None
            })
        
        self.db.commit()
        return memories
    
    # ==================== SUMMARIZE ====================
    
    async def summarize_conversation(
        self,
        session_id: str,
        user_id: str,
        agent_id: str,
        conversation: List[Dict[str, str]],
        outcome: str = None,
        llm_service = None,
        organization_id: str = None
    ) -> ConversationSummary:
        """
        Generate and store a summary of a conversation.
        """
        # Build summary prompt with PII Redaction
        conv_text = "\n".join([f"{m['role']}: {redactor.redact_text(m['content'])}" for m in conversation])
        
        # Generate summary using LLM if available
        summary_text = ""
        key_points = []
        
        if llm_service:
            prompt = f"""Summarize this conversation in 2-3 sentences. Then list 3-5 key points.

Conversation:
{conv_text}

Format your response as:
SUMMARY: <2-3 sentence summary>
KEY POINTS:
- point 1
- point 2
..."""
            
            try:
                response = await llm_service.generate_response(prompt, "You are a summarization assistant.", [])
                
                if "SUMMARY:" in response:
                    parts = response.split("KEY POINTS:")
                    summary_text = parts[0].replace("SUMMARY:", "").strip()
                    if len(parts) > 1:
                        key_points = [p.strip().lstrip("- ") for p in parts[1].strip().split("\n") if p.strip()]
                else:
                    summary_text = response[:500]
            except Exception as e:
                logger.error(f"Failed to generate summary: {e}")
                summary_text = f"Conversation with {len(conversation)} turns"
        else:
            summary_text = f"Conversation with {len(conversation)} turns"
        
        # Generate embedding
        embedding = self._generate_embedding(summary_text)
        
        summary = ConversationSummary(
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            summary=summary_text,
            key_points=key_points,
            turn_count=len(conversation),
            outcome=outcome,
            organization_id=organization_id,
            embedding=embedding
        )
        
        self.db.add(summary)
        
        # Update user profile
        await self._update_user_profile(user_id)
        
        self.db.commit()
        return summary
    
    # ==================== USER PROFILE ====================
    
    async def _update_user_profile(self, user_id: str):
        """Update or create user profile after a conversation."""
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        
        profile.total_calls += 1
        profile.last_interaction = datetime.utcnow()
        
        # Try to get name from memories
        name_memory = self.db.query(MemoryItem).filter(
            MemoryItem.user_id == user_id,
            MemoryItem.key == "name"
        ).first()
        
        if name_memory:
            profile.name = name_memory.value
    
    async def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get or create a user profile."""
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
        
        return profile

    async def set_user_consent(self, user_id: str, status: str):
        """Set or update user consent status."""
        profile = await self.get_or_create_profile(user_id)
        profile.consent_status = status
        self.db.commit()
        logger.info(f"Consent for user {user_id} updated to: {status}")


    # ==================== WORKING MEMORY ====================

    async def set_working(
        self,
        agent_id: str,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: int = None
    ) -> WorkingMemory:
        """Store ephemeral working memory for an active session."""
        existing = self.db.query(WorkingMemory).filter(
            WorkingMemory.session_id == session_id,
            WorkingMemory.key == key
        ).first()

        if existing:
            existing.value = value
            existing.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds) if ttl_seconds else None
            self.db.commit()
            return existing

        wm = WorkingMemory(
            agent_id=agent_id,
            session_id=session_id,
            key=key,
            value=value,
            expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        )
        self.db.add(wm)
        self.db.commit()
        logger.debug(f"Working memory set: {session_id}/{key}")
        return wm

    async def get_working(
        self,
        session_id: str,
        key: str = None
    ) -> Any:
        """Retrieve working memory for a session. Returns single value or all as dict."""
        if key:
            entry = self.db.query(WorkingMemory).filter(
                WorkingMemory.session_id == session_id,
                WorkingMemory.key == key,
                or_(WorkingMemory.expires_at == None, WorkingMemory.expires_at > datetime.utcnow())
            ).first()
            return entry.value if entry else None

        entries = self.db.query(WorkingMemory).filter(
            WorkingMemory.session_id == session_id,
            or_(WorkingMemory.expires_at == None, WorkingMemory.expires_at > datetime.utcnow())
        ).all()
        return {e.key: e.value for e in entries}

    async def clear_working(self, session_id: str):
        """Clear all working memory for a finished session."""
        self.db.query(WorkingMemory).filter(WorkingMemory.session_id == session_id).delete()
        self.db.commit()
        logger.debug(f"Working memory cleared for session {session_id}")

    # ==================== PROCEDURAL MEMORY ====================

    async def store_procedure(
        self,
        agent_id: str,
        name: str,
        steps: List[Dict[str, Any]],
        description: str = None,
        tags: List[str] = None
    ) -> ProceduralMemory:
        """Store or update a procedure for an agent."""
        existing = self.db.query(ProceduralMemory).filter(
            ProceduralMemory.agent_id == agent_id,
            ProceduralMemory.name == name
        ).first()

        if existing:
            existing.steps = steps
            existing.description = description or existing.description
            existing.tags = tags or existing.tags
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return existing

        proc = ProceduralMemory(
            agent_id=agent_id,
            name=name,
            description=description,
            steps=steps,
            tags=tags or []
        )
        self.db.add(proc)
        self.db.commit()
        logger.info(f"Procedure stored: {agent_id}/{name}")
        return proc

    async def recall_procedure(
        self,
        agent_id: str,
        name: str = None,
        tags: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Recall procedures for an agent. Filter by name or tags."""
        query = self.db.query(ProceduralMemory).filter(ProceduralMemory.agent_id == agent_id)

        if name:
            query = query.filter(ProceduralMemory.name == name)
            proc = query.first()
            if not proc:
                return []
            return [{"id": proc.id, "name": proc.name, "description": proc.description, "steps": proc.steps, "tags": proc.tags, "updated_at": proc.updated_at.isoformat() if proc.updated_at else None}]

        if tags:
            query = query.filter(ProceduralMemory.tags.contains(tags))

        procs = query.order_by(ProceduralMemory.name).all()
        return [{"id": p.id, "name": p.name, "description": p.description, "steps": p.steps, "tags": p.tags, "updated_at": p.updated_at.isoformat() if p.updated_at else None} for p in procs]

    async def delete_procedure(self, agent_id: str, name: str):
        """Delete a procedure."""
        self.db.query(ProceduralMemory).filter(
            ProceduralMemory.agent_id == agent_id,
            ProceduralMemory.name == name
        ).delete()
        self.db.commit()

    # ==================== GOVERNANCE ====================

    async def mark_do_not_remember(self, user_id: str, key: str = None):
        """Flag a memory as 'do not remember' — prevents future extraction."""
        query = self.db.query(MemoryItem).filter(MemoryItem.user_id == user_id)
        if key:
            query = query.filter(MemoryItem.key == key)
        for m in query.all():
            m.do_not_remember = True
        self.db.commit()
        logger.info(f"Marked do_not_remember for user {user_id}", extra={"key": key})

    async def forget(self, user_id: str, key: str = None, category: str = None):
        """GDPR-style deletion of memories."""
        query = self.db.query(MemoryItem).filter(MemoryItem.user_id == user_id)
        if key:
            query = query.filter(MemoryItem.key == key)
        if category:
            query = query.filter(MemoryItem.category == category)
        count = query.delete()
        self.db.commit()
        logger.info(f"Forgot {count} memories for user {user_id}")
        return count

    async def run_ttl_cleanup(self):
        """Remove all expired memories. Called by scheduler."""
        now = datetime.utcnow()
        expired_memories = self.db.query(MemoryItem).filter(
            MemoryItem.expires_at != None,
            MemoryItem.expires_at <= now
        )
        count_mem = expired_memories.count()

        expired_working = self.db.query(WorkingMemory).filter(
            WorkingMemory.expires_at != None,
            WorkingMemory.expires_at <= now
        )
        count_wm = expired_working.count()

        expired_memories.delete()
        expired_working.delete()
        self.db.commit()
        if count_mem or count_wm:
            logger.info(f"TTL cleanup: removed {count_mem} memories, {count_wm} working entries")
        return count_mem + count_wm

    async def get_context_for_call(self, user_id: str, organization_id: str = None, agent_id: str = None) -> str:
        """
        Build a context string for an agent about a user.
        Now includes procedural memory for the agent.
        Called at the start of a conversation to provide history.
        """
        # Get user profile
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        # Get recent memories (skip do_not_remember)
        memories = await self.get_user_memories(user_id, organization_id=organization_id)

        # Get last conversation summary
        last_summary = self.db.query(ConversationSummary).filter(
            ConversationSummary.user_id == user_id
        ).order_by(ConversationSummary.created_at.desc()).first()

        context_parts = []

        if profile:
            context_parts.append(f"**Returning caller**: {profile.name or 'Unknown name'}")
            context_parts.append(f"- Total previous calls: {int(profile.total_calls)}")
            if profile.preferences:
                context_parts.append(f"- Known preferences: {json.dumps(profile.preferences)}")
        else:
            context_parts.append("**New caller**: No previous interaction history")

        if memories:
            context_parts.append("\n**Known facts about this caller:**")
            for category, items in memories.items():
                context_parts.append(f"- {category}:")
                for item in items[:5]:
                    type_icon = "[✓]" if item['type'] in ['system_verified', 'regulated_fact'] else "[?]"
                    context_parts.append(f"  {type_icon} {item['key']}: {item['value']} ({item['type']})")

        if last_summary:
            context_parts.append(f"\n**Last conversation ({last_summary.created_at.strftime('%Y-%m-%d')}):**")
            context_parts.append(f"- Summary: {last_summary.summary}")
            if last_summary.outcome:
                context_parts.append(f"- Outcome: {last_summary.outcome}")

        # Append procedural memory relevant to the agent
        if agent_id:
            procedures = await self.recall_procedure(agent_id)
            if procedures:
                context_parts.append(f"\n**Available procedures ({len(procedures)}):**")
                for p in procedures[:3]:
                    context_parts.append(f"- {p['name']}: {p.get('description', '')}")

        return "\n".join(context_parts) if context_parts else ""

    async def get_user_memories(
        self,
        user_id: str,
        categories: List[str] = None,
        organization_id: str = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all memories for a user, grouped by category.
        Respects do_not_remember flag.
        """
        query = self.db.query(MemoryItem).filter(
            MemoryItem.user_id == user_id,
            MemoryItem.do_not_remember == False
        )
        if organization_id:
            query = query.filter(MemoryItem.organization_id == organization_id)

        if categories:
            query = query.filter(MemoryItem.category.in_(categories))

        memories = query.order_by(MemoryItem.category, MemoryItem.updated_at.desc()).all()

        result = {}
        for memory in memories:
            if memory.category not in result:
                result[memory.category] = []
            result[memory.category].append({
                "key": memory.key,
                "value": memory.value,
                "type": memory.memory_type,
                "confidence": memory.confidence,
                "updated_at": memory.updated_at.isoformat() if memory.updated_at else None
            })

        return result


# Singleton-ish factory function
def get_memory_service(db: Session) -> MemoryService:
    return MemoryService(db)
