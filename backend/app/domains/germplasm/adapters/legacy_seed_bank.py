"""Germplasm persistence bridge for legacy Seed Bank ORM models."""

from __future__ import annotations

from app.modules.seed_bank.models import Accession as SeedBankAccession


def get_seed_bank_accession_model() -> type:
    """Return the transitional Seed Bank accession ORM model."""

    return SeedBankAccession
