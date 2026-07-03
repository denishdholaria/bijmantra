"""FastAPI adapters for accession passport capability routes."""

from app.domains.germplasm.capabilities.accession_passport.adapters.api.mcpd import (
    router,
)


__all__ = ["router"]
