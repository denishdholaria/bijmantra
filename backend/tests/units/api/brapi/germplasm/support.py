from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.domains.germplasm.capabilities.accession_passport.adapters.api.access import (
    ACCESSION_PASSPORT_CAPABILITY_ID,
)


mock_db = AsyncMock()
mock_user = SimpleNamespace(
    id=1,
    organization_id=1,
    full_name="Test User",
    email="test@example.com",
    installed_capabilities=(ACCESSION_PASSPORT_CAPABILITY_ID,),
    permissions=("germplasm.read", "germplasm.passport.manage"),
    data_scopes=("organization", "accession"),
)


def capability_installation_absent_result():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    return result


def backend_root() -> Path:
    return Path(__file__).resolve().parents[5]
