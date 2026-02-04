"""
Monitoring service for real-time call tracking.
Uses Redis Pub/Sub to broadcast call events to supervisors.
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
import redis.asyncio as redis
from app.core.config import settings

class MonitoringService:
    """Handles broadcasting and streaming of live call events."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        if not self.redis:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )
    
    def _channel_name(self, session_id: str) -> str:
        return f"monitor:session:{session_id}"
    
    def _global_channel(self) -> str:
        return "monitor:all_sessions"

    async def broadcast_event(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """Publish an event to the session-specific and global monitoring channels."""
        await self.connect()
        
        event = {
            "session_id": session_id,
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        payload = json.dumps(event)
        
        # Publish to specific session channel
        await self.redis.publish(self._channel_name(session_id), payload)
        
        # Publish to global monitoring channel
        await self.redis.publish(self._global_channel(), payload)
        
        logger.debug(f"Broadcasted monitoring event {event_type} for session {session_id}")

    async def subscribe_to_session(self, session_id: str):
        """Generator that yields events for a specific session."""
        await self.connect()
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self._channel_name(session_id))
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield json.loads(message["data"])
        finally:
            await pubsub.unsubscribe(self._channel_name(session_id))

    async def subscribe_to_all(self):
        """Generator that yields events for all active sessions."""
        await self.connect()
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self._global_channel())
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield json.loads(message["data"])
        finally:
            await pubsub.unsubscribe(self._global_channel())

# Singleton
monitoring_service = MonitoringService()
