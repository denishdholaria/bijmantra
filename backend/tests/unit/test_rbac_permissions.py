import pytest
from unittest.mock import AsyncMock, Mock

from app.services.authorization import has_permission


@pytest.mark.asyncio
async def test_has_permission_from_role_json_permissions():
    db = AsyncMock()
    result = Mock()
    result.all.return_value = [(["read:plant_sciences"], None)]
    db.execute.return_value = result

    assert await has_permission(db, 1, "read:plant_sciences") is True


@pytest.mark.asyncio
async def test_has_permission_from_role_permission_join():
    db = AsyncMock()
    result = Mock()
    result.all.return_value = [([], "view:audit_log")]
    db.execute.return_value = result

    assert await has_permission(db, 1, "view:audit_log") is True


@pytest.mark.asyncio
async def test_has_permission_denied_when_missing():
    db = AsyncMock()
    result = Mock()
    result.all.return_value = [(["read:seed_bank"], None)]
    db.execute.return_value = result

    assert await has_permission(db, 1, "manage:users") is False
