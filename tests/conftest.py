"""
Pytest fixtures for Vinmec Lumina API tests.

Strategy
--------
- fakeredis.FakeRedis  → replaces real Redis; no external service needed
- unittest.mock.patch  → injects a stub LLM that returns a fixed reply
- TestClient(app)      → runs the full ASGI lifespan (startup/shutdown)
- LUMINA_API_KEYS env var is set before each test client is created
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import fakeredis
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_USER = "test_user"
VALID_KEY = "test-api-key-123"
_API_KEYS_ENV = f"{VALID_USER}:{VALID_KEY}"

_FAKE_LLM_REPLY = "Day la cau tra loi gia lap tu LLM."


def _make_fake_llm() -> MagicMock:
    """Return a stub LLM whose .invoke() and .stream() behave deterministically."""
    llm = MagicMock()
    llm.invoke.return_value = AIMessage(content=_FAKE_LLM_REPLY)
    llm.stream.return_value = iter([AIMessage(content=_FAKE_LLM_REPLY)])
    return llm


# ---------------------------------------------------------------------------
# Shared env fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required env vars before every test."""
    monkeypatch.setenv("LUMINA_API_KEYS", _API_KEYS_ENV)
    monkeypatch.setenv("LUMINA_RATE_LIMIT_PER_MINUTE", "100")  # high limit → not a blocker in tests
    monkeypatch.setenv("LUMINA_MONTHLY_COST_LIMIT_USD", "999")
    monkeypatch.setenv("LUMINA_DEFAULT_REQUEST_COST_USD", "0.001")
    monkeypatch.setenv("LUMINA_ANALYZE_COST_USD", "0.001")
    monkeypatch.setenv("LUMINA_REDIS_URL", "redis://localhost:6379/0")  # overridden by fake


# ---------------------------------------------------------------------------
# Client fixture  (one per test, isolated fakeredis)
# ---------------------------------------------------------------------------

@pytest.fixture()
def client() -> TestClient:  # type: ignore[return]
    """
    Provide a TestClient backed by fakeredis and a stub LLM.

    The lifespan context manager runs, so app.state is fully populated.
    """
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    # Patch Redis.from_url so the server's lifespan gets our fake instance.
    with patch("src.api.server.Redis") as mock_redis_class:
        mock_redis_class.from_url.return_value = fake_redis

        # Patch build_llm so no real API keys are required.
        with patch("src.api.server.build_llm", return_value=_make_fake_llm()):
            with patch("src.api.server.run_agent_turn") as mock_turn:
                from langchain_core.messages import HumanMessage, SystemMessage

                def _fake_turn(user_q: str, history: list, provider: str = "azure"):
                    return history + [HumanMessage(content=user_q), AIMessage(content=_FAKE_LLM_REPLY)]

                mock_turn.side_effect = _fake_turn

                with patch("src.api.server.run_workflow") as mock_workflow:
                    mock_workflow.return_value = {
                        "overall_severity": "WATCH",
                        "summary": "2 chi so bat thuong can chu y.",
                        "explanations": [
                            {"test_code": "HBA1C", "test_name": "HbA1c", "value": 8.2, "unit": "%", "severity": "SEE_DOCTOR", "explanation": "HbA1c cao."},
                            {"test_code": "LDL", "test_name": "LDL Cholesterol", "value": 3.4, "unit": "mmol/L", "severity": "WATCH", "explanation": "LDL cao nhe."},
                        ],
                        "suggestions": ["Gap bac si trong 24-72 gio.", "Tai xet nghiem theo huong dan bac si."],
                        "is_critical": False,
                        "critical_alert": None,
                        "errors": [],
                    }

                    from src.api.server import app
                    with TestClient(app) as c:
                        yield c


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": VALID_KEY}
