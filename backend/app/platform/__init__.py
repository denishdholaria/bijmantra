"""Platform-level product taxonomy and capability access scaffolds."""

from app.platform.capability_bootstrap import (  # noqa: F401
    FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS,
    CapabilityBootstrapReceipt,
    bootstrap_capability_installations,
)
from app.platform.capability_installations import (  # noqa: F401
    UnknownCapability,
    build_persisted_capability_access_context,
    build_persisted_capability_access_context_if_present,
    disable_capability_for_organization,
    get_capability_installation,
    install_capability_for_organization,
    list_capability_installations,
    list_enabled_capability_installations,
)
from app.platform.dominions import (  # noqa: F401
    CAPABILITY_MANIFESTS,
    DOMINION_REGISTRY,
    PLATFORM_STANDARDS_SPINE,
    CapabilityManifest,
    DominionDefinition,
    capabilities_for_dominion,
    dominions_for_domain,
    resolve_capability_manifest,
    resolve_dominion,
)


__all__ = [
    "CAPABILITY_MANIFESTS",
    "DOMINION_REGISTRY",
    "PLATFORM_STANDARDS_SPINE",
    "CapabilityManifest",
    "CapabilityBootstrapReceipt",
    "DominionDefinition",
    "FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS",
    "bootstrap_capability_installations",
    "capabilities_for_dominion",
    "dominions_for_domain",
    "resolve_capability_manifest",
    "resolve_dominion",
    "UnknownCapability",
    "build_persisted_capability_access_context",
    "build_persisted_capability_access_context_if_present",
    "disable_capability_for_organization",
    "get_capability_installation",
    "install_capability_for_organization",
    "list_capability_installations",
    "list_enabled_capability_installations",
]
