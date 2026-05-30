from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from fastapi import Response

from app.middleware.tenant_context import TenantContextMiddleware, apply_tenant_context
from app.models.core import User


# Helper to create a mock request
class MockRequest:
    def __init__(self, path="/", headers=None):
        self.url = MagicMock()
        self.url.path = path
        self.headers = headers or {}
        self.state = MagicMock()
        # Ensure state attributes are None initially to simulate fresh request state
        self.state.organization_id = None
        self.state.is_superuser = False
        self.state.user_id = None


@pytest.fixture
def mock_call_next():
    return AsyncMock(return_value=Response(content="OK"))


@pytest.mark.asyncio
async def test_exempt_path_skips_context(mock_call_next):
    middleware = TenantContextMiddleware(app=MagicMock())
    request = MockRequest(path="/health")

    await middleware.dispatch(request, mock_call_next)

    # Verify context was NOT set (attributes remain default/None)
    assert request.state.organization_id is None
    assert request.state.is_superuser is False
    assert request.state.user_id is None
    mock_call_next.assert_called_once_with(request)


@pytest.mark.asyncio
@patch("app.middleware.tenant_context.decode_access_token")
async def test_valid_token_sets_context(mock_decode, mock_call_next):
    middleware = TenantContextMiddleware(app=MagicMock())
    request = MockRequest(
        path="/api/v2/some-resource", headers={"Authorization": "Bearer valid_token"}
    )

    mock_decode.return_value = {"organization_id": 123, "is_superuser": True, "sub": "user_456"}

    await middleware.dispatch(request, mock_call_next)

    assert request.state.organization_id == 123
    assert request.state.is_superuser is True
    assert request.state.user_id == "user_456"
    mock_call_next.assert_called_once_with(request)


@pytest.mark.asyncio
@patch("app.middleware.tenant_context.AsyncSessionLocal")
@patch("app.middleware.tenant_context.decode_access_token")
async def test_legacy_local_token_fetches_user_context(
    mock_decode,
    mock_session_local,
    mock_call_next,
):
    middleware = TenantContextMiddleware(app=MagicMock())
    request = MockRequest(
        path="/api/v2/chat/stream",
        headers={"Authorization": "Bearer legacy_token"},
    )
    user = User(
        id=42,
        organization_id=7,
        email="breeder@bijmantra.org",
        hashed_password="hash",
        is_active=True,
        is_superuser=False,
    )
    session = AsyncMock()
    session.get = AsyncMock(return_value=user)
    mock_session_local.return_value.__aenter__.return_value = session
    mock_decode.return_value = {"sub": "42"}

    await middleware.dispatch(request, mock_call_next)

    assert request.state.organization_id == 7
    assert request.state.is_superuser is False
    assert request.state.user_id == 42
    session.get.assert_awaited_once_with(User, 42)
    mock_call_next.assert_called_once_with(request)


@pytest.mark.asyncio
async def test_missing_header_empty_context(mock_call_next):
    middleware = TenantContextMiddleware(app=MagicMock())
    request = MockRequest(path="/api/v2/some-resource", headers={})

    await middleware.dispatch(request, mock_call_next)

    assert request.state.organization_id is None
    assert request.state.is_superuser is False
    assert request.state.user_id is None
    mock_call_next.assert_called_once_with(request)


@pytest.mark.asyncio
async def test_malformed_header_empty_context(mock_call_next):
    middleware = TenantContextMiddleware(app=MagicMock())
    request = MockRequest(path="/api/v2/some-resource", headers={"Authorization": "InvalidToken"})

    await middleware.dispatch(request, mock_call_next)

    assert request.state.organization_id is None
    assert request.state.is_superuser is False
    assert request.state.user_id is None
    mock_call_next.assert_called_once_with(request)


@pytest.mark.asyncio
@patch("app.middleware.tenant_context.decode_access_token")
async def test_invalid_token_empty_context(mock_decode, mock_call_next):
    middleware = TenantContextMiddleware(app=MagicMock())
    request = MockRequest(
        path="/api/v2/some-resource", headers={"Authorization": "Bearer invalid_token"}
    )

    mock_decode.return_value = None  # Simulate invalid token

    await middleware.dispatch(request, mock_call_next)

    assert request.state.organization_id is None
    assert request.state.is_superuser is False
    assert request.state.user_id is None
    mock_call_next.assert_called_once_with(request)


class RecordingSession:
    def __init__(self):
        self.execute_calls = []

    async def execute(self, statement, params=None):
        self.execute_calls.append((statement, params or {}))


def _session_config_values(session: RecordingSession) -> dict[str, str]:
    return {
        params["key"]: params["value"]
        for _statement, params in session.execute_calls
        if "key" in params
    }


@pytest.mark.asyncio
async def test_apply_tenant_context_sets_organization_and_user_context():
    session = RecordingSession()

    await apply_tenant_context(session, organization_id=456, user_id=123)

    config_values = _session_config_values(session)
    assert config_values["app.current_organization_id"] == "456"
    assert config_values["app.current_user_id"] == "123"


@pytest.mark.asyncio
async def test_apply_tenant_context_sets_restricted_user_context_when_missing():
    session = RecordingSession()

    await apply_tenant_context(session, organization_id=None, user_id=None)

    config_values = _session_config_values(session)
    assert config_values["app.current_organization_id"] == "-1"
    assert config_values["app.current_user_id"] == "-1"


@pytest.mark.asyncio
async def test_apply_tenant_context_preserves_user_id_for_superuser_audit_context():
    session = RecordingSession()

    await apply_tenant_context(
        session,
        organization_id=456,
        is_superuser=True,
        user_id=123,
    )

    config_values = _session_config_values(session)
    assert config_values["app.current_organization_id"] == "0"
    assert config_values["app.current_user_id"] == "123"
