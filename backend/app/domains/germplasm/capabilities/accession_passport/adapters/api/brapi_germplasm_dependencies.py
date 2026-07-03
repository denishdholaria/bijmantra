"""API dependency wiring for BrAPI germplasm routes."""

from __future__ import annotations

from typing import Any

from app.domains.germplasm.capabilities.accession_passport.adapters.brapi_germplasm import (
    SqlAlchemyBrAPIGermplasmReadAdapter,
    SqlAlchemyBrAPIGermplasmWriteAdapter,
)
from app.domains.germplasm.capabilities.accession_passport.application import (
    BrAPIGermplasmApplicationService,
)


def build_brapi_germplasm_application_service(
    db: Any,
) -> BrAPIGermplasmApplicationService:
    """Build the BrAPI germplasm application service for one request."""

    return BrAPIGermplasmApplicationService(
        read_repository=SqlAlchemyBrAPIGermplasmReadAdapter(db),
        write_repository=SqlAlchemyBrAPIGermplasmWriteAdapter(db),
    )
