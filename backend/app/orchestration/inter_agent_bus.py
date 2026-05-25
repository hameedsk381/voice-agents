"""
Inter-Agent Message Bus — Redis pub/sub for agent-to-agent communication.

Provides async request/response, fire-and-forget, and pub/sub patterns
so agents can coordinate, hand off tasks, and share context without
shared memory.
"""
import json
import uuid
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime
from loguru import logger
import redis.asyncio as redis
from app.core.config import settings


class InterAgentBus:
    """Redis-backed message bus for inter-agent communication."""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._handlers: Dict[str, Callable] = {}

    async def _connect(self):
        if not self._redis:
            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            logger.info("InterAgentBus: connected to Redis")

    def _agent_channel(self, agent_id: str) -> str:
        return f"agent_bus:{agent_id}"

    async def send(
        self,
        source_agent_id: str,
        target_agent_id: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> str:
        """Fire-and-forget message to another agent."""
        await self._connect()
        msg_id = str(uuid.uuid4())
        message = {
            "id": msg_id,
            "source_agent_id": source_agent_id,
            "target_agent_id": target_agent_id,
            "type": "fire_and_forget",
            "payload": payload,
            "correlation_id": correlation_id or msg_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._redis.publish(
            self._agent_channel(target_agent_id), json.dumps(message)
        )
        logger.debug(f"Agent {source_agent_id} -> {target_agent_id}: {msg_id[:8]}")
        return msg_id

    async def request(
        self,
        source_agent_id: str,
        target_agent_id: str,
        payload: Dict[str, Any],
        timeout: float = 10.0,
    ) -> Optional[Dict[str, Any]]:
        """Request-reply pattern. Publishes a request and waits for a response on a temp channel."""
        await self._connect()
        correlation_id = str(uuid.uuid4())
        reply_channel = f"agent_bus_reply:{correlation_id}"
        msg_id = str(uuid.uuid4())

        message = {
            "id": msg_id,
            "source_agent_id": source_agent_id,
            "target_agent_id": target_agent_id,
            "type": "request",
            "payload": payload,
            "correlation_id": correlation_id,
            "reply_channel": reply_channel,
            "timestamp": datetime.utcnow().isoformat(),
        }

        pubsub = self._redis.pubsub()
        await pubsub.subscribe(reply_channel)

        await self._redis.publish(
            self._agent_channel(target_agent_id), json.dumps(message)
        )

        try:
            raw = await pubsub.get_message(timeout=timeout)
            if raw and raw["type"] == "message":
                reply = json.loads(raw["data"])
                return reply.get("payload")
        except Exception:
            pass
        finally:
            await pubsub.unsubscribe(reply_channel)
            await self._redis.delete(reply_channel)

        return None

    async def reply(self, message: Dict[str, Any], payload: Dict[str, Any]):
        """Reply to a previous request message."""
        reply_channel = message.get("reply_channel")
        if not reply_channel:
            return
        await self._connect()
        reply = {
            "correlation_id": message.get("correlation_id"),
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._redis.publish(reply_channel, json.dumps(reply))

    async def listen(
        self, agent_id: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ):
        """Subscribe to messages for a given agent and dispatch to handler."""
        await self._connect()
        channel = self._agent_channel(agent_id)
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        logger.info(f"InterAgentBus: listening on {channel}")

        async for raw in pubsub.listen():
            if raw["type"] != "message":
                continue
            try:
                message = json.loads(raw["data"])
                msg_type = message.get("type")

                if msg_type == "request":
                    response_payload = await handler(message)
                    if response_payload is not None:
                        await self.reply(message, response_payload)
                else:
                    await handler(message)
            except Exception as e:
                logger.error(f"InterAgentBus handler error: {e}")


inter_agent_bus = InterAgentBus()
