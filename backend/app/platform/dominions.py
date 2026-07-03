"""Product dominion and capability-app registry.

Dominions are product/access suites. They are not backend implementation
folders. A dominion can coordinate many backend domains through explicit
capability manifests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.domains.registry import DomainName


DominionName = Literal[
    "intelligence_fabric",
    "plant_science_rnd",
    "germplasm_global_seed_registry",
    "seedops_commercialization",
    "field_agronomic_operations",
    "climate_environment_crop_systems",
    "sensing_robotics_automation",
    "frontier_space_agriculture",
    "enterprise_regulatory_governance",
    "knowledge_training_community",
    "scientific_publishing_fair_exchange",
]


PLATFORM_STANDARDS_SPINE = (
    "BrAPI v2.1",
    "FAIR",
    "MCPD",
    "MIAPPE",
    "Crop Ontology",
    "CG Core",
    "AgGateway",
    "Darwin Core",
    "JSON-LD",
    "Schema.org",
    "W3C PROV",
    "DataCite DOI",
    "Crossref DOI",
)


@dataclass(frozen=True)
class DominionDefinition:
    """A user-facing product/access suite in BijMantra."""

    name: DominionName
    title: str
    purpose: str
    primary_domains: tuple[DomainName, ...]
    supporting_domains: tuple[DomainName, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CapabilityManifest:
    """First-class capability app manifest for routing, access, and ownership."""

    id: str
    title: str
    dominion: DominionName
    owner_domain: DomainName
    supporting_domains: tuple[DomainName, ...]
    lifecycle: str
    standards: tuple[str, ...]
    frontend_routes: tuple[str, ...]
    backend_routes: tuple[str, ...]
    data_scopes: tuple[str, ...]
    required_permissions: tuple[str, ...]
    suggested_roles: tuple[str, ...]
    semantic_spine_adrs: tuple[str, ...]
    install_behavior: str
    uninstall_behavior: str
    tests: tuple[str, ...]
    audit_events: tuple[str, ...]
    source_context: tuple[str, ...] = ()
    backend_code_root: str | None = None
    frontend_code_root: str | None = None


DOMINION_REGISTRY: dict[DominionName, DominionDefinition] = {
    "intelligence_fabric": DominionDefinition(
        name="intelligence_fabric",
        title="Intelligence Fabric",
        purpose="Cross-domain REEVU, knowledge graph, retrieval, reasoning, AI orchestration, and decision support.",
        primary_domains=("intelligence",),
        supporting_domains=("breeding", "germplasm", "phenotyping", "field_operations", "commercial", "knowledge"),
        notes=("AI is a fabric across dominions, not a single isolated division.",),
    ),
    "plant_science_rnd": DominionDefinition(
        name="plant_science_rnd",
        title="Plant Science R&D",
        purpose="Breeding, genetics, genomics, phenotyping, trials, plant vision, and experimental analysis.",
        primary_domains=("breeding", "phenotyping", "field_operations"),
        supporting_domains=("intelligence", "germplasm"),
    ),
    "germplasm_global_seed_registry": DominionDefinition(
        name="germplasm_global_seed_registry",
        title="Germplasm & Global Seed Registry",
        purpose="Seed bank, accessions, passport/MCPD, conservation, exchange, GRIN/Genesys, and global registry workflows.",
        primary_domains=("germplasm",),
        supporting_domains=("intelligence", "knowledge"),
    ),
    "seedops_commercialization": DominionDefinition(
        name="seedops_commercialization",
        title="SeedOps & Commercialization",
        purpose="Seed production, lab testing, processing, inventory, dispatch, traceability, DUS, licensing, and commercialization.",
        primary_domains=("germplasm", "commercial"),
        supporting_domains=("field_operations", "intelligence", "knowledge"),
    ),
    "field_agronomic_operations": DominionDefinition(
        name="field_agronomic_operations",
        title="Field & Agronomic Operations",
        purpose="R&D trial fields, seed production fields, demo and marketing fields, agronomy, and farm advisory operations.",
        primary_domains=("field_operations",),
        supporting_domains=("phenotyping", "commercial", "intelligence"),
    ),
    "climate_environment_crop_systems": DominionDefinition(
        name="climate_environment_crop_systems",
        title="Climate, Environment & Crop Systems",
        purpose="Weather, soil, nutrients, water, crop protection, crop intelligence, and climate resilience.",
        primary_domains=("field_operations", "intelligence"),
        supporting_domains=("phenotyping", "breeding", "germplasm"),
    ),
    "sensing_robotics_automation": DominionDefinition(
        name="sensing_robotics_automation",
        title="Sensing, Robotics & Automation",
        purpose="Sensors, IoT, drones, UAV, robotics, field scanners, and automation workflows.",
        primary_domains=("field_operations", "intelligence"),
        supporting_domains=("phenotyping",),
    ),
    "frontier_space_agriculture": DominionDefinition(
        name="frontier_space_agriculture",
        title="Frontier & Space Agriculture",
        purpose="Space research, controlled environments, extreme agriculture, and future research systems.",
        primary_domains=("intelligence", "field_operations"),
        supporting_domains=("breeding", "phenotyping", "germplasm"),
    ),
    "enterprise_regulatory_governance": DominionDefinition(
        name="enterprise_regulatory_governance",
        title="Enterprise, Regulatory & Governance",
        purpose="Admin, users, audit, contracts, regulatory paperwork, ERP/accounting integration, and governance controls.",
        primary_domains=("commercial", "knowledge"),
        supporting_domains=("intelligence", "germplasm", "field_operations"),
    ),
    "knowledge_training_community": DominionDefinition(
        name="knowledge_training_community",
        title="Knowledge, Training & Community",
        purpose="Documentation, protocols, training, learning, community, DevGuru, and education surfaces.",
        primary_domains=("knowledge",),
        supporting_domains=("intelligence",),
    ),
    "scientific_publishing_fair_exchange": DominionDefinition(
        name="scientific_publishing_fair_exchange",
        title="Scientific Publishing & FAIR Exchange",
        purpose="BijMantra Publishers, AI-native publication, structured data companions, FAIR packages, journal workflows, and research-agent APIs.",
        primary_domains=("knowledge", "intelligence"),
        supporting_domains=("breeding", "phenotyping", "field_operations", "germplasm", "commercial"),
        notes=(
            "Grounded in the 2026-05-21 BijMantra Publishers founder note.",
            "Treat agricultural assets as publishable scientific objects with provenance.",
        ),
    ),
}


CAPABILITY_MANIFESTS: dict[str, CapabilityManifest] = {
    "intelligence_fabric.knowledge_graph": CapabilityManifest(
        id="intelligence_fabric.knowledge_graph",
        title="Cross-Domain Knowledge Graph",
        dominion="intelligence_fabric",
        owner_domain="intelligence",
        supporting_domains=("breeding", "germplasm", "phenotyping", "field_operations", "commercial", "knowledge"),
        lifecycle="active",
        standards=("FAIR", "JSON-LD", "Schema.org", "W3C PROV"),
        frontend_routes=("/knowledge-graph",),
        backend_routes=("/api/v2/knowledge-graph/*",),
        data_scopes=("organization", "asset", "evidence", "provenance"),
        required_permissions=("intelligence.knowledge_graph.read", "intelligence.knowledge_graph.write"),
        suggested_roles=("scientist", "knowledge_curator", "research_lead"),
        semantic_spine_adrs=("ADR-019", "ADR-020", "ADR-021", "ADR-023", "ADR-024"),
        install_behavior=(
            "Enable knowledge graph navigation, API access, retrieval jobs, and "
            "evidence/audit capture for permitted users."
        ),
        uninstall_behavior=(
            "Hide navigation and reject API access while preserving graph edges, "
            "evidence packs, and audit history."
        ),
        tests=(
            "tests/domains/intelligence",
            "tests/test_architecture_recovery_guards.py",
            "tests/test_platform_dominion_registry.py",
        ),
        audit_events=("knowledge_graph.edge_created", "knowledge_graph.evidence_retrieved"),
        source_context=(".github/docs/denish-ideas/2026-05-19-future-direction.md",),
        backend_code_root="backend/app/domains/intelligence/capabilities/knowledge_graph",
    ),
    "plant_science_rnd.trial_analysis": CapabilityManifest(
        id="plant_science_rnd.trial_analysis",
        title="Trial Analysis",
        dominion="plant_science_rnd",
        owner_domain="field_operations",
        supporting_domains=("breeding", "phenotyping", "intelligence", "germplasm"),
        lifecycle="active",
        standards=("BrAPI v2.1", "MIAPPE", "Crop Ontology", "FAIR"),
        frontend_routes=("/trials", "/phenotyping", "/breeding/trials"),
        backend_routes=("/brapi/v2/*", "/api/v2/trials/*", "/api/v2/phenotyping/*"),
        data_scopes=("organization", "program", "trial", "study", "location", "season"),
        required_permissions=("trials.read", "trials.analyze", "phenotyping.read"),
        suggested_roles=("breeder", "trial_manager", "phenotyping_scientist", "research_lead"),
        semantic_spine_adrs=("ADR-019", "ADR-020", "ADR-021", "ADR-022", "ADR-023", "ADR-024"),
        install_behavior=(
            "Expose trial-analysis navigation, BrAPI-backed trial/phenotyping "
            "routes, and eligible analysis jobs."
        ),
        uninstall_behavior=(
            "Hide trial-analysis surfaces and reject non-BrAPI product access "
            "while preserving trial, study, and observation records."
        ),
        tests=("tests/test_platform_dominion_registry.py",),
        audit_events=("trial.analysis_requested", "trial.result_promoted"),
        backend_code_root="backend/app/domains/field_operations/capabilities/trial_analysis",
    ),
    "germplasm_global_seed_registry.accession_passport": CapabilityManifest(
        id="germplasm_global_seed_registry.accession_passport",
        title="Accession Passport Registry",
        dominion="germplasm_global_seed_registry",
        owner_domain="germplasm",
        supporting_domains=("intelligence", "knowledge"),
        lifecycle="active",
        standards=("BrAPI v2.1", "MCPD", "FAIR", "DataCite DOI"),
        frontend_routes=("/germplasm", "/seed-bank/mcpd"),
        backend_routes=("/brapi/v2/germplasm/*", "/api/v2/germplasm/*", "/api/v2/seed-bank/*"),
        data_scopes=("organization", "collection", "accession", "material_transfer"),
        required_permissions=("germplasm.read", "germplasm.passport.manage"),
        suggested_roles=("germplasm_curator", "seed_bank_manager", "research_lead"),
        semantic_spine_adrs=("ADR-019", "ADR-020", "ADR-021", "ADR-022", "ADR-023"),
        install_behavior=(
            "Expose germplasm and accession-passport surfaces, BrAPI germplasm "
            "routes, and FAIR metadata workflows."
        ),
        uninstall_behavior=(
            "Hide registry surfaces and reject product API access while preserving "
            "accession identity, passport, DOI, and audit records."
        ),
        tests=("tests/test_platform_dominion_registry.py",),
        audit_events=("germplasm.mcpd_exported", "germplasm.mcpd_imported"),
        source_context=(".github/docs/denish-ideas/2026-05-19-future-direction.md",),
        backend_code_root="backend/app/domains/germplasm/capabilities/accession_passport",
    ),
    "seedops_commercialization.seed_lot_traceability": CapabilityManifest(
        id="seedops_commercialization.seed_lot_traceability",
        title="Seed Lot Traceability",
        dominion="seedops_commercialization",
        owner_domain="germplasm",
        supporting_domains=("commercial", "field_operations", "intelligence"),
        lifecycle="planned",
        standards=("FAIR", "AgGateway", "W3C PROV"),
        frontend_routes=("/seed-operations", "/inventory/seed-lots"),
        backend_routes=("/api/v2/inventory/*", "/api/v2/seed-inventory/*", "/api/v2/germplasm/*"),
        data_scopes=("organization", "location", "lot", "production_season"),
        required_permissions=(
            "seedops.seed_lots.read",
            "seedops.seed_lots.adjust",
            "seedops.traceability.manage",
        ),
        suggested_roles=("seed_operations_manager", "warehouse_operator", "quality_manager", "commercial_admin"),
        semantic_spine_adrs=("ADR-020", "ADR-023", "ADR-024"),
        install_behavior=(
            "Expose seed-lot inventory, traceability scans, movement workflows, "
            "and audit capture for permitted seed operations users."
        ),
        uninstall_behavior=(
            "Hide SeedOps navigation and reject write APIs while preserving lots, "
            "movement history, labels, and traceability audit records."
        ),
        tests=(
            "tests/test_platform_dominion_registry.py",
            "crates/bijmantra-server/tests/rust_330_gates.rs",
        ),
        audit_events=(
            "seed_lot.created",
            "seed_lot.moved",
            "seed_lot.adjusted",
            "seed_lot.traceability_scanned",
        ),
        source_context=(
            "contracts/fastapi-parity/seedlot-inventory-adjustment-write-contract.json",
            "docs/rust-id-strategy.md",
        ),
    ),
    "scientific_publishing_fair_exchange.research_asset_core": CapabilityManifest(
        id="scientific_publishing_fair_exchange.research_asset_core",
        title="Federated Research Asset Core",
        dominion="scientific_publishing_fair_exchange",
        owner_domain="knowledge",
        supporting_domains=("intelligence", "breeding", "phenotyping", "field_operations", "germplasm", "commercial"),
        lifecycle="active",
        standards=("FAIR", "JSON-LD", "Schema.org", "W3C PROV", "DataCite DOI", "BrAPI v2.1", "Crop Ontology"),
        frontend_routes=("/data/federated-assets", "/knowledge/research-assets"),
        backend_routes=("/api/v2/fair-metadata/*", "/api/v2/federated-assets/*"),
        data_scopes=("organization", "asset", "provenance", "license", "identifier", "connector", "evidence"),
        required_permissions=("research_assets.read", "research_assets.register", "research_assets.promote_fair"),
        suggested_roles=("data_steward", "knowledge_curator", "research_lead", "scientist"),
        semantic_spine_adrs=("ADR-019", "ADR-020", "ADR-021", "ADR-022", "ADR-023", "ADR-024", "ADR-036"),
        install_behavior=(
            "Enable FAIR metadata, federated registry, explicit promotion, "
            "audit-ledger, and research-asset retrieval workflows."
        ),
        uninstall_behavior=(
            "Hide research-asset navigation and reject product API access while "
            "preserving FAIR metadata, registry records, promotion history, "
            "provenance, and audit events."
        ),
        tests=(
            "tests/domains/knowledge/capabilities/research_asset_core",
            "tests/services/test_fair_metadata_service.py",
            "tests/services/test_federated_asset_registry_service.py",
            "tests/api/test_fair_metadata_api.py",
            "tests/api/test_federated_asset_registry_api.py",
            "tests/test_platform_dominion_registry.py",
        ),
        audit_events=(
            "federated_connector_upsert",
            "federated_connector_dry_run",
            "federated_asset_register",
            "federated_asset_promote_fair",
        ),
        source_context=(
            "backend-rs/BijMantra Realignment Report from Fairgrounds Signals.md",
            ".ai/decisions/ADR-036-federated-research-asset-core-inside-modular-monolith.md",
        ),
        backend_code_root="backend/app/domains/knowledge/capabilities/research_asset_core",
    ),
    "scientific_publishing_fair_exchange.ai_native_publications": CapabilityManifest(
        id="scientific_publishing_fair_exchange.ai_native_publications",
        title="AI-Native Scientific Publications",
        dominion="scientific_publishing_fair_exchange",
        owner_domain="knowledge",
        supporting_domains=("intelligence", "breeding", "phenotyping", "field_operations", "germplasm", "commercial"),
        lifecycle="proposed",
        standards=("FAIR", "JSON-LD", "Schema.org", "W3C PROV", "DataCite DOI", "Crossref DOI", "BrAPI v2.1", "Crop Ontology"),
        frontend_routes=("/publishers", "/knowledge/publications"),
        backend_routes=("/api/v2/publishers/*", "/api/v2/knowledge/publications/*"),
        data_scopes=("organization", "publication", "claim", "dataset", "embargo", "license"),
        required_permissions=("publishers.draft", "publishers.review", "publishers.publish"),
        suggested_roles=("scientist", "publisher_editor", "reviewer", "knowledge_admin"),
        semantic_spine_adrs=("ADR-019", "ADR-020", "ADR-021", "ADR-022", "ADR-023", "ADR-024"),
        install_behavior=(
            "Expose publication drafting, HIL review, structured companion-data, "
            "DOI, and research-agent API surfaces."
        ),
        uninstall_behavior=(
            "Hide publisher workspaces and reject publishing APIs while preserving "
            "drafts, claims, provenance, embargoes, licenses, and audit history."
        ),
        tests=("tests/test_platform_dominion_registry.py",),
        audit_events=("publication.draft_generated", "publication.claim_reviewed", "publication.hil_signed_off", "publication.published"),
        source_context=(".github/docs/denish-ideas/2026-05-21-bijmantra-publishers.md",),
    ),
}


def resolve_dominion(name: str) -> DominionDefinition | None:
    """Return a dominion definition by canonical key."""

    return DOMINION_REGISTRY.get(name)  # type: ignore[arg-type]


def resolve_capability_manifest(capability_id: str) -> CapabilityManifest | None:
    """Return a capability manifest by full manifest id."""

    return CAPABILITY_MANIFESTS.get(capability_id)


def capabilities_for_dominion(dominion: DominionName) -> tuple[CapabilityManifest, ...]:
    """Return capability manifests belonging to one dominion."""

    return tuple(manifest for manifest in CAPABILITY_MANIFESTS.values() if manifest.dominion == dominion)


def backend_route_matches(pattern: str, route_path: str) -> bool:
    """Return whether a backend route pattern owns a concrete path."""

    normalized_path = route_path.split("?", 1)[0].rstrip("/") or "/"
    normalized_pattern = pattern.rstrip("/") or "/"

    if normalized_pattern.endswith("/*"):
        prefix = normalized_pattern[:-2]
        return normalized_path == prefix or normalized_path.startswith(f"{prefix}/")
    return normalized_path == normalized_pattern


def capabilities_for_backend_route(route_path: str) -> tuple[CapabilityManifest, ...]:
    """Return capability manifests that claim a backend route path."""

    return tuple(
        manifest
        for manifest in CAPABILITY_MANIFESTS.values()
        if any(backend_route_matches(pattern, route_path) for pattern in manifest.backend_routes)
    )


def dominions_for_domain(domain: DomainName) -> tuple[DominionDefinition, ...]:
    """Return dominions that use a backend domain as primary or supporting ownership."""

    return tuple(
        dominion
        for dominion in DOMINION_REGISTRY.values()
        if domain in dominion.primary_domains or domain in dominion.supporting_domains
    )
