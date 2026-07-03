"""Compatibility namespace for the former ``app.lokas`` package.

Canonical backend code now lives under ``app.domains``. This shim exists only
so old agent prompts and transitional imports can discover the new location.
Do not add domain implementation code here.
"""

from app.domains.registry import (  # noqa: F401
    CANONICAL_ARCHITECTURE,
    DOMAIN_BOUNDARIES,
    DOMAIN_CODE_ROOT,
    DOMAIN_OWNERSHIP,
    HEXAGONAL_DOMAIN_LAYERS,
    LEGACY_ARCHITECTURE_ALIASES,
    LEGACY_DOMAIN_ALIASES,
    LOKA_BOUNDARIES,
    LOKA_DOMAIN_OWNERSHIP,
    TRANSITIONAL_SURFACES,
    resolve_domain_for_capability,
    resolve_domain_name,
    resolve_loka_for_domain,
    resolve_loka_name,
)
