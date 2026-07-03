"""Compatibility shim for BrAPI v2 germplasm routes.

Route ownership lives in the Accession Passport capability adapter. Keep this
module import-compatible because the BrAPI v2 router still mounts
``app.api.brapi.v2.germplasm.router``.
"""

from app.domains.germplasm.capabilities.accession_passport.adapters.api.brapi_germplasm import (
    _require_brapi_germplasm_manage_access,
    _require_brapi_germplasm_read_access,
    create_germplasm,
    delete_germplasm,
    get_current_user,
    get_germplasm,
    get_germplasm_mcpd,
    get_germplasm_pedigree,
    get_germplasm_progeny,
    get_optional_user,
    get_tenant_db,
    list_germplasm,
    router,
    update_germplasm,
)
from app.domains.germplasm.capabilities.accession_passport.adapters.api.brapi_germplasm_compatibility import (
    Germplasm,
    GermplasmBase,
    GermplasmCreate,
    _brapi_response,
    _model_to_brapi,
)


__all__ = [
    "Germplasm",
    "GermplasmBase",
    "GermplasmCreate",
    "_brapi_response",
    "_model_to_brapi",
    "_require_brapi_germplasm_manage_access",
    "_require_brapi_germplasm_read_access",
    "create_germplasm",
    "delete_germplasm",
    "get_current_user",
    "get_germplasm",
    "get_germplasm_mcpd",
    "get_germplasm_pedigree",
    "get_germplasm_progeny",
    "get_optional_user",
    "get_tenant_db",
    "list_germplasm",
    "router",
    "update_germplasm",
]
