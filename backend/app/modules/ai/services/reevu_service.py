"""Canonical REEVU cognitive service facade.

This keeps the live runtime on REEVU-named imports while legacy veena_* service
implementations and persisted schemas remain intact during migration.
"""

from app.modules.ai.services.veena_service import VeenaService, get_veena_service


ReevuService = VeenaService
get_reevu_service = get_veena_service

# Legacy compatibility exports retained during migration.
VeenaService = ReevuService
get_veena_service = get_reevu_service

__all__ = [
    "ReevuService",
    "get_reevu_service",
    "VeenaService",
    "get_veena_service",
]