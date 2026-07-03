from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from .support import mock_db, mock_user


@pytest.fixture
def db():
    return mock_db


@pytest.fixture
def current_user():
    return mock_user


@pytest.fixture(autouse=True)
def auto_patch_deps():
    tenant_db_dependency = MagicMock(return_value=mock_db)
    current_user_dependency = MagicMock(return_value=mock_user)
    optional_user_dependency = MagicMock(return_value=mock_user)
    with (
        patch("app.api.brapi.v2.germplasm.get_tenant_db", tenant_db_dependency),
        patch("app.api.brapi.v2.germplasm.get_current_user", current_user_dependency),
        patch("app.api.brapi.v2.germplasm.get_optional_user", optional_user_dependency),
        patch(
            "app.domains.germplasm.capabilities.accession_passport.adapters.api.brapi_germplasm.get_tenant_db",
            tenant_db_dependency,
        ),
        patch(
            "app.domains.germplasm.capabilities.accession_passport.adapters.api.brapi_germplasm.get_current_user",
            current_user_dependency,
        ),
        patch(
            "app.domains.germplasm.capabilities.accession_passport.adapters.api.brapi_germplasm.get_optional_user",
            optional_user_dependency,
        ),
    ):
        yield


@pytest.fixture(autouse=True)
def reset_mocks():
    mock_db.reset_mock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()
