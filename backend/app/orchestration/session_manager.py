"""
Session state management using Redis for persistent call state.
"""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.core.config import settings
from loguru import logger


class SessionManager:
    """Manages conversation sessions with Redis persistence."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.session_ttl = 3600 * 24  # 24 hours
    
    async def connect(self):
        """Connect to Redis."""
        if not self.redis:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    def _session_key(self, session_id: str) -> str:
        return f"session:{session_id}"
    
    def _agent_sessions_key(self, agent_id: str) -> str:
        return f"agent_sessions:{agent_id}"
    
    def _active_sessions_key(self) -> str:
        return "active_sessions_global"
    
    async def create_session(
        self, 
        session_id: str, 
        agent_id: str, 
        caller_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new conversation session."""
        await self.connect()
        
        session = {
            "session_id": session_id,
            "agent_id": agent_id,
            "caller_id": caller_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": "active",
            "history": [],
            "tool_calls": [],
            "metadata": metadata or {},
            "escalation_reason": None,
            "transferred_to": None
        }
        
        await self.redis.setex(
            self._session_key(session_id),
            self.session_ttl,
            json.dumps(session)
        )
        
        # Track session under agent and globally
        await self.redis.sadd(self._agent_sessions_key(agent_id), session_id)
        await self.redis.sadd(self._active_sessions_key(), session_id)
        
        logger.info(f"Created session {session_id} for agent {agent_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session by ID."""
        await self.connect()
        
        data = await self.redis.get(self._session_key(session_id))
        if data:
            return json.loads(data)
        return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update session with new data."""
        await self.connect()
        
        session = await self.get_session(session_id)
        if not session:
            return None
        
        session.update(updates)
        session["updated_at"] = datetime.utcnow().isoformat()
        
        await self.redis.setex(
            self._session_key(session_id),
            self.session_ttl,
            json.dumps(session)
        )
        return session
    
    async def add_to_history(self, session_id: str, role: str, content: str) -> bool:
        """Add a message to session history."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session["history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await self.update_session(session_id, {"history": session["history"]})
        return True
    
    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session."""
        session = await self.get_session(session_id)
        if session:
            # Return in format expected by LLM
            return [{"role": h["role"], "content": h["content"]} for h in session["history"]]
        return []
    
    async def log_tool_call(self, session_id: str, tool_name: str, arguments: dict, result: str):
        """Log a tool call in the session."""
        session = await self.get_session(session_id)
        if not session:
            return
        
        session["tool_calls"].append({
            "tool": tool_name,
            "arguments": arguments,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await self.update_session(session_id, {"tool_calls": session["tool_calls"]})
    
    async def escalate_session(self, session_id: str, reason: str, target: str = "human"):
        """Mark session as escalated."""
        await self.update_session(session_id, {
            "status": "escalated",
            "escalation_reason": reason,
            "transferred_to": target
        })
        logger.warning(f"Session {session_id} escalated: {reason}")
    
    async def end_session(self, session_id: str, reason: str = "completed"):
        """End a session."""
        await self.update_session(session_id, {
            "status": "ended",
            "ended_at": datetime.utcnow().isoformat(),
            "end_reason": reason
        })
        # Remove from active global tracking
        await self.redis.srem(self._active_sessions_key(), session_id)
        
        logger.info(f"Session {session_id} ended: {reason}")
    
        return active

    async def get_all_active_sessions(self) -> List[Dict[str, Any]]:
        """Get details for all globally active sessions."""
        await self.connect()
        
        session_ids = await self.redis.smembers(self._active_sessions_key())
        active_details = []
        
        for sid in session_ids:
            session = await self.get_session(sid)
            if session:
                if session["status"] in ["active", "escalated"]:
                    active_details.append(session)
                else:
                    # Clean up if status is not active/escalated
                    await self.redis.srem(self._active_sessions_key(), sid)
        
        return active_details


# Singleton instance
session_manager = SessionManager()
