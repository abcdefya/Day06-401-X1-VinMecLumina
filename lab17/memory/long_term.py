"""Long-term memory: Redis-backed key-value store for user preferences and facts."""
from __future__ import annotations
import json
import os
from typing import Any


def _make_redis():
    """Return a real Redis client or fakeredis fallback."""
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        try:
            import redis
            return redis.from_url(redis_url, decode_responses=True)
        except Exception:
            pass
    import fakeredis
    return fakeredis.FakeRedis(decode_responses=True)


class LongTermMemory:
    """
    Redis-backed persistent store.
    Keys are namespaced as  ltm:<session_id>:<category>:<key>
    Categories: preference | fact | profile
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._r = _make_redis()
        self._prefix = f"ltm:{session_id}"

    def store(self, category: str, key: str, value: Any, ttl: int = 86400) -> None:
        full_key = f"{self._prefix}:{category}:{key}"
        self._r.set(full_key, json.dumps(value), ex=ttl)

    def retrieve(self, category: str, key: str) -> Any | None:
        full_key = f"{self._prefix}:{category}:{key}"
        raw = self._r.get(full_key)
        return json.loads(raw) if raw is not None else None

    def retrieve_all(self, category: str) -> dict[str, Any]:
        pattern = f"{self._prefix}:{category}:*"
        result = {}
        for k in self._r.keys(pattern):
            short_key = k.split(":")[-1]
            raw = self._r.get(k)
            if raw:
                result[short_key] = json.loads(raw)
        return result

    def delete(self, category: str, key: str) -> None:
        self._r.delete(f"{self._prefix}:{category}:{key}")

    def flush_session(self) -> None:
        for k in self._r.keys(f"{self._prefix}:*"):
            self._r.delete(k)
