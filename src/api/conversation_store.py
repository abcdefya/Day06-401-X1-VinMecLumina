from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from redis import Redis
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage


@dataclass
class Conversation:
    id: str
    history: list[AnyMessage] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def serialize_history(messages: list[AnyMessage]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            role = "system"
        elif isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        else:
            continue
        output.append({"role": role, "content": str(getattr(msg, "content", "") or "")})
    return output


def deserialize_history(items: list[dict[str, str]]) -> list[AnyMessage]:
    messages: list[AnyMessage] = []
    for item in items:
        role = item.get("role")
        content = item.get("content", "")
        if role == "system":
            messages.append(SystemMessage(content=content))
        elif role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


class RedisConversationStore:
    """Redis-backed conversation store for stateless API instances."""

    def __init__(self, redis_client: Redis, ttl_seconds: int = 60 * 60 * 24) -> None:
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds

    def _key(self, conversation_id: str) -> str:
        return f"lumina:conversation:{conversation_id}"

    @staticmethod
    def _to_payload(conv: Conversation) -> str:
        payload = {
            "id": conv.id,
            "history": serialize_history(conv.history),
            "metadata": conv.metadata,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        }
        return json.dumps(payload, ensure_ascii=True)

    @staticmethod
    def _from_payload(raw: str) -> Conversation:
        data = json.loads(raw)
        return Conversation(
            id=data["id"],
            history=deserialize_history(data.get("history", [])),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data.get("updated_at")) if data.get("updated_at") else datetime.now(timezone.utc),
        )

    def create(self, *, history: list[AnyMessage] | None = None, metadata: dict[str, Any] | None = None) -> Conversation:
        now = datetime.now(timezone.utc)
        conv = Conversation(
            id=str(uuid4()),
            history=list(history or []),
            metadata=dict(metadata or {}),
            created_at=now,
            updated_at=now,
        )
        self._redis.set(self._key(conv.id), self._to_payload(conv), ex=self._ttl_seconds)
        return conv

    def get(self, conversation_id: str) -> Conversation | None:
        raw = self._redis.get(self._key(conversation_id))
        if not raw:
            return None
        conv = self._from_payload(raw)
        # Keep active conversations alive.
        self._redis.expire(self._key(conversation_id), self._ttl_seconds)
        return conv

    def set_history(self, conversation_id: str, history: list[AnyMessage]) -> Conversation | None:
        conv = self.get(conversation_id)
        if not conv:
            return None
        conv.history = list(history)
        conv.updated_at = datetime.now(timezone.utc)
        self._redis.set(self._key(conversation_id), self._to_payload(conv), ex=self._ttl_seconds)
        return conv
