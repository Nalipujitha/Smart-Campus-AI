import pytest
import json
from unittest.mock import patch, MagicMock
import urllib.error
from backend.services.gemini_service import GeminiService, SimpleRateLimiter

def test_chat_endpoint_missing_body(client):
    """Test POST /api/ai/chat with empty or invalid JSON body returns 400."""
    res = client.post('/api/ai/chat', data="invalid-json", content_type='text/plain')
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert "error" in data

def test_chat_endpoint_empty_message(client):
    """Test POST /api/ai/chat with empty message returns 400."""
    res = client.post('/api/ai/chat', json={"message": ""})
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert "empty" in data['error'].lower()

def test_chat_endpoint_whitespace_message(client):
    """Test POST /api/ai/chat with whitespace-only message returns 400."""
    res = client.post('/api/ai/chat', json={"message": "   \n\t  "})
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert "empty" in data['error'].lower()

def test_chat_endpoint_non_string_message(client):
    """Test POST /api/ai/chat with non-string message returns 400."""
    res = client.post('/api/ai/chat', json={"message": 12345})
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert "string" in data['error'].lower()

def test_chat_endpoint_missing_api_key_fallback(client, monkeypatch):
    """Test POST /api/ai/chat returns intelligent fallback response if GEMINI_API_KEY is not configured."""
    monkeypatch.setenv("GEMINI_API_KEY", "")
    res = client.post('/api/ai/chat', json={"message": "What is the minimum attendance policy?"})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert "reply" in data
    assert len(data['reply']) > 0


def test_chat_endpoint_success_mock(client, monkeypatch):
    """Test POST /api/ai/chat returns successful response from Gemini."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-fake-gemini-key")
    
    mock_gemini_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello! I am EduPulse AI. How can I help you today?"}],
                    "role": "model"
                },
                "finishReason": "STOP"
            }
        ]
    }
    
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_gemini_payload).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        res = client.post('/api/ai/chat', json={"message": "Hello!"})
        assert res.status_code == 200
        data = res.get_json()
        assert data['success'] is True
        assert "EduPulse AI" in data['reply']
        assert data['model'] == "gemini-1.5-flash"
        assert "timestamp" in data

def test_chat_endpoint_timeout_handling(client, monkeypatch):
    """Test POST /api/ai/chat returns 504 on timeout."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-fake-gemini-key")

    with patch("urllib.request.urlopen", side_effect=TimeoutError("Request timed out")):
        res = client.post('/api/ai/chat', json={"message": "Explain quantum computing"})
        assert res.status_code == 504
        data = res.get_json()
        assert data['success'] is False
        assert "timed out" in data['error'].lower()

def test_chat_endpoint_upstream_429_handling(client, monkeypatch):
    """Test POST /api/ai/chat handles upstream Gemini 429 quota exhaustion gracefully."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-fake-gemini-key")

    mock_err = urllib.error.HTTPError(
        url="https://generativelanguage.googleapis.com",
        code=429,
        msg="Too Many Requests",
        hdrs={},
        fp=MagicMock(read=lambda: b'{"error": {"message": "Resource has been exhausted (e.g. check quota)."}}')
    )

    with patch("urllib.request.urlopen", side_effect=mock_err):
        res = client.post('/api/ai/chat', json={"message": "Tell me about data structures"})
        assert res.status_code == 429
        data = res.get_json()
        assert data['success'] is False
        assert "quota" in data['error'].lower() or "rate limit" in data['error'].lower()

def test_rate_limiter_local_blocking():
    """Test in-memory rate limiter blocks requests exceeding max threshold."""
    limiter = SimpleRateLimiter(max_requests=3, window_seconds=60)
    client_ip = "192.168.1.100"

    assert limiter.is_allowed(client_ip)[0] is True
    assert limiter.is_allowed(client_ip)[0] is True
    assert limiter.is_allowed(client_ip)[0] is True
    
    # 4th request in the same window must be blocked
    allowed, retry_after = limiter.is_allowed(client_ip)
    assert allowed is False
    assert retry_after > 0
