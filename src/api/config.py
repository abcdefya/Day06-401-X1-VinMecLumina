from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class APISettings:
    app_name: str
    app_version: str
    redis_url: str
    conversation_ttl_seconds: int
    api_keys: dict[str, str]
    rate_limit_per_minute: int
    monthly_cost_limit_usd: float
    default_estimated_request_cost_usd: float
    analyze_cost_usd: float
    input_cost_per_1k_usd: float
    output_cost_per_1k_usd: float
    shutdown_grace_seconds: float

    @staticmethod
    def _load_api_keys(raw: str) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for part in raw.split(","):
            item = part.strip()
            if not item or ":" not in item:
                continue
            user_id, api_key = item.split(":", 1)
            user_id = user_id.strip()
            api_key = api_key.strip()
            if user_id and api_key:
                mapping[user_id] = api_key
        return mapping

    @classmethod
    def from_env(cls) -> "APISettings":
        return cls(
            app_name=os.getenv("LUMINA_APP_NAME", "Vinmec Lumina API"),
            app_version=os.getenv("LUMINA_APP_VERSION", "1.2.0"),
            redis_url=os.getenv("LUMINA_REDIS_URL", "redis://redis:6379/0"),
            conversation_ttl_seconds=int(os.getenv("LUMINA_CONVERSATION_TTL_SECONDS", str(60 * 60 * 24))),
            api_keys=cls._load_api_keys(os.getenv("LUMINA_API_KEYS", "")),
            rate_limit_per_minute=int(os.getenv("LUMINA_RATE_LIMIT_PER_MINUTE", "10")),
            monthly_cost_limit_usd=float(os.getenv("LUMINA_MONTHLY_COST_LIMIT_USD", "10")),
            default_estimated_request_cost_usd=float(os.getenv("LUMINA_DEFAULT_REQUEST_COST_USD", "0.05")),
            analyze_cost_usd=float(os.getenv("LUMINA_ANALYZE_COST_USD", "0.05")),
            input_cost_per_1k_usd=float(os.getenv("LUMINA_INPUT_COST_PER_1K_USD", "0.005")),
            output_cost_per_1k_usd=float(os.getenv("LUMINA_OUTPUT_COST_PER_1K_USD", "0.015")),
            shutdown_grace_seconds=float(os.getenv("LUMINA_SHUTDOWN_GRACE_SECONDS", "10")),
        )
