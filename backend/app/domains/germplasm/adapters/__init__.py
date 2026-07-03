"""Germplasm infrastructure adapters."""

from app.domains.germplasm.adapters.legacy_seed_bank import (
    get_seed_bank_accession_model,
)


__all__ = [
    "get_seed_bank_accession_model",
]
