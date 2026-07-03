"""Legacy BrAPI germplasm compatibility helpers.

These private names were historically exported by ``app.api.brapi.v2.germplasm``.
Keep them outside the route adapter so transport code does not carry unused
schema-mapper imports only for compatibility.
"""

from app.domains.germplasm.capabilities.accession_passport.schemas import (
    Germplasm,
    GermplasmBase,
    GermplasmCreate,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import (
    brapi_germplasm_record_to_payload as _model_to_brapi,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import (
    brapi_response as _brapi_response,
)


__all__ = [
    "Germplasm",
    "GermplasmBase",
    "GermplasmCreate",
    "_brapi_response",
    "_model_to_brapi",
]
