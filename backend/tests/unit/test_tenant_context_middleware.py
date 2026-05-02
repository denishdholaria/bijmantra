import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request, Response
from app.middleware.tenant_context import TenantContextMiddleware

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
    request = MockRequest(path="/api/v2/some-resource", headers={"Authorization": "Bearer valid_token"})

    mock_decode.return_value = {
        "organization_id": 123,
        "is_superuser": True,
        "sub": "user_456"
    }

    await middleware.dispatch(request, mock_call_next)

    assert request.state.organization_id == 123
    assert request.state.is_superuser is True
    assert request.state.user_id == "user_456"
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
    request = MockRequest(path="/api/v2/some-resource", headers={"Authorization": "Bearer invalid_token"})

    mock_decode.return_value = None # Simulate invalid token

    await middleware.dispatch(request, mock_call_next)

    assert request.state.organization_id is None
    assert request.state.is_superuser is False
    assert request.state.user_id is None
    mock_call_next.assert_called_once_with(request)
