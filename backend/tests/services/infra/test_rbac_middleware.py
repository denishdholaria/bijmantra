import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

# Mock BaseHTTPMiddleware
class MockBaseHTTPMiddleware:
    def __init__(self, app):
        self.app = app

# Mock dependencies
sys.modules["fastapi"] = MagicMock()
sys.modules["sqlalchemy"] = MagicMock()
sys.modules["sqlalchemy.ext.asyncio"] = MagicMock()
sys.modules["sqlalchemy.future"] = MagicMock()
sys.modules["sqlalchemy.orm"] = MagicMock()

# Mock starlette
starlette_mock = MagicMock()
starlette_mock.BaseHTTPMiddleware = MockBaseHTTPMiddleware
sys.modules["starlette.middleware.base"] = starlette_mock
sys.modules["starlette.datastructures"] = MagicMock()

# Mock app modules
sys.modules["app.core.database"] = MagicMock()
sys.modules["app.core.security"] = MagicMock()
sys.modules["app.models.core"] = MagicMock()

# Import middleware
from app.modules.core.services.infra.rbac_row_level_security_middleware import (
    RBACRowLevelSecurityMiddleware,
    get_rbac_db,
    RBACDatabaseDependency
)

# Setup mocks
Request = MagicMock()
Response = MagicMock()
AsyncSession = MagicMock()

class MockUser:
    def __init__(self, user_id=1, org_id=10, roles=["viewer"], is_superuser=False):
        self.id = user_id
        self.organization_id = org_id
        self.roles = roles
        self.is_superuser = is_superuser
        self.permissions = ["read:test"]

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session

def test_middleware_extracts_token_context():
    async def _run():
        app_mock = MagicMock()
        middleware = RBACRowLevelSecurityMiddleware(app_mock)

        mock_payload = {
            "sub": "123",
            "organization_id": 456,
            "roles": ["admin"],
            "permissions": ["read:all"],
            "is_superuser": False
        }

        from app.modules.core.services.infra.rbac_row_level_security_middleware import decode_access_token
        decode_access_token.return_value = mock_payload

        request = MagicMock()
        request.url.path = "/api/v2/data"
        request.headers.get.return_value = "Bearer valid_token"
        request.state = MagicMock()

        async def call_next(req):
            return "response"

        await middleware.dispatch(request, call_next)

        assert request.state.user_id == 123
        assert request.state.organization_id == 456
        assert request.state.roles == ["admin"]
        assert request.state.permissions == ["read:all"]
        assert request.state.is_superuser is False

    asyncio.run(_run())

def test_middleware_fetches_missing_context(mock_session):
    async def _run():
        app_mock = MagicMock()
        middleware = RBACRowLevelSecurityMiddleware(app_mock)

        mock_payload = {"sub": "123"}

        from app.modules.core.services.infra.rbac_row_level_security_middleware import decode_access_token, AsyncSessionLocal
        decode_access_token.return_value = mock_payload

        AsyncSessionLocal.return_value.__aenter__.return_value = mock_session

        mock_user = MockUser(user_id=123, org_id=999, roles=["breeder"])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        request = MagicMock()
        request.url.path = "/api/v2/data"
        request.headers.get.return_value = "Bearer legacy_token"
        request.state = MagicMock()

        async def call_next(req):
            return "response"

        await middleware.dispatch(request, call_next)

        assert request.state.user_id == 123
        assert request.state.organization_id == 999
        assert request.state.roles == ["breeder"]
        assert mock_session.execute.called

    asyncio.run(_run())

def test_get_rbac_db_sets_session_variables(mock_session):
    async def _run():
        dependency = RBACDatabaseDependency()

        request = MagicMock()
        request.state.user_id = 123
        request.state.organization_id = 456
        request.state.roles = ["admin", "manager"]
        request.state.permissions = ["read:all"]
        request.state.is_superuser = False

        from app.modules.core.services.infra.rbac_row_level_security_middleware import AsyncSessionLocal
        AsyncSessionLocal.return_value.__aenter__.return_value = mock_session

        gen = dependency(request)
        session = await anext(gen)

        assert session == mock_session

        # Verify calls to set_config
        calls = mock_session.execute.call_args_list
        # We expect 4 calls to set_config
        assert len(calls) == 4

        # Collect parameters passed to execute
        params_list = []
        for call in calls:
            # call.args[0] is text(), call.args[1] is params dict
            if len(call.args) > 1:
                params_list.append(call.args[1])

        # Check expected values in params
        # Note: keys are "key" and "value"
        kv_pairs = {}
        for p in params_list:
            kv_pairs[p["key"]] = p["value"]

        assert kv_pairs["app.current_organization_id"] == "456"
        assert kv_pairs["app.current_user_id"] == "123"
        assert kv_pairs["app.current_user_roles"] == "admin,manager"
        assert kv_pairs["app.current_user_permissions"] == "read:all"

    asyncio.run(_run())

def test_get_rbac_db_superuser_bypass(mock_session):
    async def _run():
        dependency = RBACDatabaseDependency()

        request = MagicMock()
        request.state.is_superuser = True
        request.state.user_id = 1
        request.state.roles = []
        request.state.permissions = []

        from app.modules.core.services.infra.rbac_row_level_security_middleware import AsyncSessionLocal
        AsyncSessionLocal.return_value.__aenter__.return_value = mock_session

        gen = dependency(request)
        await anext(gen)

        calls = mock_session.execute.call_args_list
        params_list = []
        for call in calls:
            if len(call.args) > 1:
                params_list.append(call.args[1])

        kv_pairs = {}
        for p in params_list:
            kv_pairs[p["key"]] = p["value"]

        assert kv_pairs["app.current_organization_id"] == "0"

    asyncio.run(_run())
