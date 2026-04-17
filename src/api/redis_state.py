from __future__ import annotations

import time
from datetime import datetime, timezone

from redis import Redis


def month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


class RedisStateStore:
    """Shared Redis-backed state for rate limits and monthly cost tracking."""

    def __init__(self, redis_client: Redis, key_prefix: str = "lumina") -> None:
        self.redis = redis_client
        self.key_prefix = key_prefix

    def ping(self) -> bool:
        try:
            return bool(self.redis.ping())
        except Exception:
            return False

    def check_rate_limit(self, user_id: str, limit_per_minute: int) -> tuple[bool, int]:
        minute = int(time.time() // 60)
        key = f"{self.key_prefix}:ratelimit:{user_id}:{minute}"
        current = int(self.redis.incr(key))
        if current == 1:
            self.redis.expire(key, 65)

        allowed = current <= limit_per_minute
        remaining = max(0, limit_per_minute - current)
        return allowed, remaining

    def get_spent_monthly(self, user_id: str) -> float:
        key = f"{self.key_prefix}:cost:{month_key()}"
        raw = self.redis.hget(key, user_id)
        if raw is None:
            return 0.0
        return float(raw)

    def can_spend(self, user_id: str, amount_usd: float, monthly_limit_usd: float) -> bool:
        amount = max(0.0, float(amount_usd))
        spent = self.get_spent_monthly(user_id)
        return (spent + amount) <= monthly_limit_usd

    def add_cost(self, user_id: str, amount_usd: float) -> float:
        key = f"{self.key_prefix}:cost:{month_key()}"
        return float(self.redis.hincrbyfloat(key, user_id, max(0.0, float(amount_usd))))
