"""
Tests for the Orchard.ai FastAPI agent service.
All LLM calls are mocked — no real API keys required.
Run: pytest tests/test_api.py -v
"""
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Create TestClient once for the whole module (app startup is slow)."""
    from api.main import app
    return TestClient(app)


SECRET = "test-secret"  # matches conftest.py os.environ.setdefault


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_health(client):
    """GET /health returns {"status": "ok", "mock_mode": <bool>}."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert isinstance(data["mock_mode"], bool)


def test_sms_inbound_returns_twiml(client):
    """POST /sms/inbound returns valid TwiML XML."""
    res = client.post(
        "/sms/inbound",
        data={
            "From": "+15555550101",
            "To": "+15555550200",
            "Body": "I need my AC fixed this week",
            "MessageSid": "SM_test_123",
            "NumMedia": "0",
        },
    )
    assert res.status_code == 200
    assert "text/xml" in res.headers["content-type"]
    assert "<Response>" in res.text
    assert "<Message>" in res.text


def test_classify_requires_secret(client):
    """POST /agent/classify returns 401 if X-Orchard-Secret is missing or wrong."""
    # Missing header
    res = client.post("/agent/classify", json={"message": "I need my AC fixed"})
    assert res.status_code == 401

    # Wrong header
    res = client.post(
        "/agent/classify",
        json={"message": "I need my AC fixed"},
        headers={"X-Orchard-Secret": "wrong-secret"},
    )
    assert res.status_code == 401


def test_classify_happy_path(client):
    """POST /agent/classify returns intent + extracted fields when secret is correct."""
    with patch("utils.llm_client.call_claude", return_value="booking_request"):
        res = client.post(
            "/agent/classify",
            json={"message": "I need my AC fixed this week", "conversation_history": []},
            headers={"X-Orchard-Secret": SECRET},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "booking_request"
    assert "extracted" in data
    assert isinstance(data["extracted"], dict)
    assert "needs_followup" in data
    assert data["needs_followup"] is False
    assert "suggested_response" in data
    assert data["suggested_response"] is None


def test_classify_fallback_on_llm_error(client):
    """POST /agent/classify returns intent=unknown (HTTP 200) when LLM raises."""
    with patch("utils.llm_client.call_claude", side_effect=Exception("Anthropic down")):
        res = client.post(
            "/agent/classify",
            json={"message": "test message"},
            headers={"X-Orchard-Secret": SECRET},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "unknown"
    assert data["needs_followup"] is True
