"""FastAPI access guard for Accession Passport capability APIs."""

from __future__ import annotations

from typing import Any

from app.platform.capability_guards import require_platform_capability_api_access


ACCESSION_PASSPORT_CAPABILITY_ID = "germplasm_global_seed_registry.accession_passport"


async def require_accession_passport_api_access(
    actor: Any,
    *,
    db: Any | None = None,
    required_permission: str,
    required_data_scopes: tuple[str, ...] = ("organization", "accession"),
) -> None:
    """Reject API access when Accession Passport capability policy denies it."""

    await require_platform_capability_api_access(
        ACCESSION_PASSPORT_CAPABILITY_ID,
        actor,
        db=db,
        required_permission=required_permission,
        required_data_scopes=required_data_scopes,
        missing_manifest_detail="Accession Passport capability manifest missing",
    )
