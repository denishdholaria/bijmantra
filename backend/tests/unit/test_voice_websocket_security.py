from types import SimpleNamespace
from inspect import signature

import pytest
from fastapi import WebSocketDisconnect

from app.api.bijmantra.ai import voice


class FakeWebSocket:
    def __init__(self, *, headers=None, query_params=None, messages=None):
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.messages = list(messages or [])
        self.accepted = False
        self.close_code = None
        self.sent_json = []
        self.sent_bytes = []

    async def accept(self):
        self.accepted = True

    async def close(self, code=None):
        self.close_code = code

    async def receive_json(self):
        if not self.messages:
            raise WebSocketDisconnect()
        next_message = self.messages.pop(0)
        if isinstance(next_message, BaseException):
            raise next_message
        return next_message

    async def send_json(self, payload):
        self.sent_json.append(payload)

    async def send_bytes(self, payload):
        self.sent_bytes.append(payload)


class FakeSessionManager:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeVoiceService:
    async def synthesize_stream(self, **_kwargs):
        yield b"pcm"


def _has_current_user_dependency(endpoint) -> bool:
    return any(
        getattr(parameter.default, "dependency", None) is voice.get_current_user
        for parameter in signature(endpoint).parameters.values()
    )


def test_voice_http_stream_routes_keep_explicit_auth_dependencies():
    assert _has_current_user_dependency(voice.voice_health)
    assert _has_current_user_dependency(voice.list_voices)
    assert _has_current_user_dependency(voice.synthesize_speech)
    assert _has_current_user_dependency(voice.synthesize_stream)


@pytest.mark.asyncio
async def test_voice_websocket_rejects_missing_token_before_accept():
    websocket = FakeWebSocket()

    await voice.voice_websocket(websocket)

    assert websocket.accepted is False
    assert websocket.close_code == voice.VOICE_WS_POLICY_VIOLATION


@pytest.mark.asyncio
async def test_voice_websocket_authenticates_query_token_against_active_user(monkeypatch):
    websocket = FakeWebSocket(query_params={"token": "valid-token"})

    monkeypatch.setattr(
        voice,
        "decode_access_token",
        lambda token: {"sub": "42", "organization_id": 7} if token == "valid-token" else None,
    )
    monkeypatch.setattr(voice, "AsyncSessionLocal", lambda: FakeSessionManager())

    async def fake_get_user(_db, *, id):
        assert id == 42
        return SimpleNamespace(id=42, organization_id=7, is_active=True)

    monkeypatch.setattr(voice.user_crud, "get", fake_get_user)

    current_user = await voice._authenticate_voice_websocket(websocket)

    assert current_user.id == 42
    assert current_user.organization_id == 7
    assert websocket.close_code is None


@pytest.mark.asyncio
async def test_voice_websocket_closes_inactive_user(monkeypatch):
    websocket = FakeWebSocket(headers={"authorization": "Bearer stale-token"})

    monkeypatch.setattr(voice, "decode_access_token", lambda _token: {"sub": "42"})
    monkeypatch.setattr(voice, "AsyncSessionLocal", lambda: FakeSessionManager())

    async def fake_get_user(_db, *, id):
        return SimpleNamespace(id=id, organization_id=7, is_active=False)

    monkeypatch.setattr(voice.user_crud, "get", fake_get_user)

    current_user = await voice._authenticate_voice_websocket(websocket)

    assert current_user is None
    assert websocket.close_code == voice.VOICE_WS_POLICY_VIOLATION


@pytest.mark.asyncio
async def test_voice_websocket_accepts_only_after_successful_auth(monkeypatch):
    websocket = FakeWebSocket(messages=[{"text": "hello"}])

    async def fake_auth(_websocket):
        return SimpleNamespace(id=42, organization_id=7, is_active=True)

    monkeypatch.setattr(voice, "_authenticate_voice_websocket", fake_auth)
    monkeypatch.setattr(voice, "get_voice_service", lambda: FakeVoiceService())

    await voice.voice_websocket(websocket)

    assert websocket.accepted is True
    assert websocket.close_code is None
    assert websocket.sent_json[0]["type"] == "start"
    assert websocket.sent_bytes == [b"pcm"]
    assert websocket.sent_json[-1]["type"] == "complete"
