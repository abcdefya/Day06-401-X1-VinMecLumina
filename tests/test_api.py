"""
Tests for Vinmec Lumina REST API endpoints.

Coverage
--------
- GET /health
- GET /ready
- POST /api/v1/analyze
- POST /api/v1/chat
- POST /api/v1/chat/stream
- GET  /api/v1/conversations/{conversation_id}
- Auth guard  (missing key / wrong key)
- Rate-limit guard
- Monthly cost guard
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ─────────────────────────── liveness / readiness ────────────────────────────

class TestHealthEndpoints:
    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_ready_returns_ready(self, client: TestClient) -> None:
        resp = client.get("/ready")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ready"] is True
        assert body["redis_ready"] is True
        assert body["shutting_down"] is False

    def test_ready_not_ready_when_redis_down(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Simulate Redis becoming unavailable after startup."""
        client.app.state.redis_state.redis.connection_pool.reset()
        # Override ping to return False without touching real Redis
        monkeypatch.setattr(client.app.state.redis_state, "ping", lambda: False)
        resp = client.get("/ready")
        assert resp.status_code == 503
        assert resp.json()["ready"] is False


# ─────────────────────────── authentication ──────────────────────────────────

class TestAuthentication:
    def test_missing_api_key_returns_401(self, client: TestClient) -> None:
        resp = client.post("/api/v1/analyze", json={"patient_id": "P001"})
        assert resp.status_code == 401
        assert "Missing" in resp.json()["detail"]

    def test_wrong_api_key_returns_401(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/analyze",
            json={"patient_id": "P001"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]


# ─────────────────────────── rate limiting ───────────────────────────────────

class TestRateLimit:
    def test_rate_limit_exceeded_returns_429(self, client: TestClient, auth_headers: dict) -> None:
        """Set rate limit to 2, hit 3 times → third request returns 429."""
        client.app.state.settings = _override_settings(client, rate_limit_per_minute=2)
        client.post("/api/v1/analyze", json={"patient_id": "P001"}, headers=auth_headers)
        client.post("/api/v1/analyze", json={"patient_id": "P001"}, headers=auth_headers)
        resp = client.post("/api/v1/analyze", json={"patient_id": "P001"}, headers=auth_headers)
        assert resp.status_code == 429
        assert "Rate limit" in resp.json()["detail"]


# ─────────────────────────── monthly cost guard ──────────────────────────────

class TestCostGuard:
    def test_cost_guard_returns_402_when_limit_reached(self, client: TestClient, auth_headers: dict) -> None:
        """Exhaust the monthly budget entirely, then next request should be 402."""
        from tests.conftest import VALID_USER
        # Inject usage that exceeds the limit
        client.app.state.redis_state.add_cost(VALID_USER, 9_999.0)
        resp = client.post("/api/v1/analyze", json={"patient_id": "P001"}, headers=auth_headers)
        assert resp.status_code == 402
        assert "cost limit" in resp.json()["detail"].lower()


# ─────────────────────────── /api/v1/analyze ─────────────────────────────────

class TestAnalyzeEndpoint:
    def test_analyze_valid_patient(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.post(
            "/api/v1/analyze",
            json={"patient_id": "P001", "llm_provider": "azure", "create_conversation": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "result" in body
        assert body["result"]["overall_severity"] == "WATCH"
        assert body["conversation_id"] is not None

    def test_analyze_without_create_conversation(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.post(
            "/api/v1/analyze",
            json={"patient_id": "P001", "create_conversation": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["conversation_id"] is None

    def test_analyze_missing_patient_id_and_state_returns_400(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.post("/api/v1/analyze", json={}, headers=auth_headers)
        assert resp.status_code == 400

    def test_analyze_invalid_patient_id_returns_404(self, client: TestClient, auth_headers: dict) -> None:
        with patch("src.api.server.run_workflow", side_effect=KeyError("X999")):
            resp = client.post(
                "/api/v1/analyze",
                json={"patient_id": "X999"},
                headers=auth_headers,
            )
        assert resp.status_code == 404


# ─────────────────────────── /api/v1/chat ────────────────────────────────────

class TestChatEndpoint:
    def _get_conversation_id(self, client: TestClient, auth_headers: dict) -> str:
        resp = client.post(
            "/api/v1/analyze",
            json={"patient_id": "P001", "create_conversation": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        return resp.json()["conversation_id"]

    def test_chat_with_existing_conversation(self, client: TestClient, auth_headers: dict) -> None:
        conv_id = self._get_conversation_id(client, auth_headers)
        resp = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Tai sao HbA1c cao?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["conversation_id"] == conv_id
        assert len(body["reply"]) > 0
        # History must contain system + user + assistant at minimum
        roles = [m["role"] for m in body["history"]]
        assert "user" in roles
        assert "assistant" in roles

    def test_chat_multi_turn_preserves_history(self, client: TestClient, auth_headers: dict) -> None:
        conv_id = self._get_conversation_id(client, auth_headers)
        client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Cau hoi 1"},
            headers=auth_headers,
        )
        resp2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Cau hoi 2"},
            headers=auth_headers,
        )
        assert resp2.status_code == 200
        history = resp2.json()["history"]
        user_msgs = [m for m in history if m["role"] == "user"]
        assert len(user_msgs) == 2, "Both user messages must be in history"

    def test_chat_new_conversation_via_patient_id(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.post(
            "/api/v1/chat",
            json={"patient_id": "P001", "message": "Xin chao Lumina"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["conversation_id"] is not None

    def test_chat_unknown_conversation_returns_404(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.post(
            "/api/v1/chat",
            json={"conversation_id": "nonexistent-uuid", "message": "Hi"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_chat_no_patient_no_conv_returns_400(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
            headers=auth_headers,
        )
        assert resp.status_code == 400


# ─────────────────────────── /api/v1/chat/stream ─────────────────────────────

class TestStreamEndpoint:
    def _get_conversation_id(self, client: TestClient, auth_headers: dict) -> str:
        resp = client.post(
            "/api/v1/analyze",
            json={"patient_id": "P001", "create_conversation": True},
            headers=auth_headers,
        )
        return resp.json()["conversation_id"]

    def test_stream_returns_sse_events(self, client: TestClient, auth_headers: dict) -> None:
        conv_id = self._get_conversation_id(client, auth_headers)
        with client.stream(
            "POST",
            "/api/v1/chat/stream",
            json={"conversation_id": conv_id, "message": "Giai thich LDL"},
            headers=auth_headers,
        ) as response:
            assert response.status_code == 200
            raw = b"".join(response.iter_bytes()).decode()

        assert "data:" in raw
        # Must include a done event
        assert '"type": "done"' in raw or '"type":"done"' in raw

    def test_stream_no_conversation_returns_400(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.post(
            "/api/v1/chat/stream",
            json={"message": "Hello"},
            headers=auth_headers,
        )
        assert resp.status_code == 400


# ─────────────────────────── /api/v1/conversations ───────────────────────────

class TestConversationsEndpoint:
    def test_get_conversation_returns_history(self, client: TestClient, auth_headers: dict) -> None:
        analyze_resp = client.post(
            "/api/v1/analyze",
            json={"patient_id": "P001", "create_conversation": True},
            headers=auth_headers,
        )
        conv_id = analyze_resp.json()["conversation_id"]

        # Add a chat turn so history has more than just system message
        client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Test message"},
            headers=auth_headers,
        )

        resp = client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["conversation_id"] == conv_id
        roles = [m["role"] for m in body["history"]]
        assert "system" in roles
        assert "user" in roles

    def test_get_unknown_conversation_returns_404(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.get("/api/v1/conversations/does-not-exist", headers=auth_headers)
        assert resp.status_code == 404


# ─────────────────────────── helpers ─────────────────────────────────────────

def _override_settings(client: TestClient, **overrides):
    """Return a new frozen settings instance with given fields overridden."""
    from dataclasses import replace
    current = client.app.state.settings
    return replace(current, **overrides)
