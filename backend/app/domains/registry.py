"""Canonical domain ownership map for architecture recovery.

This module is intentionally small and side-effect free. It gives tests,
agents, and future migration scripts one importable source for the target
bounded-context vocabulary without moving existing routes or services yet.

Older BijMantra documents may use "LOKA" or Sanskrit names. Backend code uses
industry-standard domain names so folder names stay unsurprising for future
contributors and AI agents.
"""

from dataclasses import dataclass
from typing import Literal, cast


DomainName = Literal[
    "breeding",
    "germplasm",
    "phenotyping",
    "field_operations",
    "intelligence",
    "commercial",
    "knowledge",
]

CANONICAL_ARCHITECTURE = "domain_bounded_modular_monolith_with_hexagonal_architecture"
FEDERATION_SPINE = "research_asset_core_inside_modular_monolith"
FDCA_STATUS = "federation_pattern_not_replacement_architecture"
LEGACY_ARCHITECTURE_ALIASES = (
    "loka_modular_monolith_with_hexagonal_architecture",
    "loka_hexagonal_modular_monolith",
)
DOMAIN_CODE_ROOT = "backend/app/domains"
HEXAGONAL_DOMAIN_LAYERS = ("domain", "application", "ports", "schemas", "adapters")
CAPABILITY_LAYER_ROOT = "capabilities"
CAPABILITY_LAYER_RULE = "domain -> capability -> hexagonal slice"
TRANSITIONAL_CONTRACTS_LAYER = "contracts"
DOMAIN_GROWTH_POLICY = "open_registry_not_fixed_taxonomy"
DOMAIN_CREATION_CRITERIA = (
    "stable ubiquitous language",
    "clear data ownership",
    "clear capability ownership",
    "explicit ports and schemas",
    "tenant and policy boundary",
    "migration path from transitional surfaces",
)
LEGACY_DOMAIN_ALIASES = {
    "sristi": "breeding",
    "bijkosha": "germplasm",
    "bija_kosha": "germplasm",
    "bij_kosha": "germplasm",
    "bija-kosha": "germplasm",
    "bij-kosha": "germplasm",
    "rupa": "phenotyping",
    "kshetra": "field_operations",
    "medha": "intelligence",
    "vani": "commercial",
    "vidya": "knowledge",
}


@dataclass(frozen=True)
class DomainBoundary:
    """One bounded context in the BijMantra modular monolith."""

    name: DomainName
    product_name: str
    meaning: str
    owns: tuple[str, ...]
    backend_sources: tuple[str, ...]
    frontend_sources: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityCodeRoot:
    """Canonical implementation root for a large domain-owned capability."""

    domain: DomainName
    capability: str
    backend_root: str
    frontend_root: str | None = None


DOMAIN_BOUNDARIES: dict[DomainName, DomainBoundary] = {
    "breeding": DomainBoundary(
        name="breeding",
        product_name="Breeding",
        meaning="Creation and breeding",
        owns=("breeding", "crosses", "selection", "breeding programs"),
        backend_sources=("api/bijmantra/breeding", "modules/breeding"),
        frontend_sources=("divisions/breeding",),
    ),
    "germplasm": DomainBoundary(
        name="germplasm",
        product_name="Germplasm",
        meaning="Seed treasury and germplasm",
        owns=("germplasm", "accessions", "seed bank", "seed inventory"),
        backend_sources=("api/bijmantra/germplasm", "modules/germplasm", "modules/seed_bank"),
        frontend_sources=("divisions/germplasm", "divisions/seed-bank", "divisions/seed-operations"),
    ),
    "phenotyping": DomainBoundary(
        name="phenotyping",
        product_name="Phenotyping",
        meaning="Form, traits, and phenotyping",
        owns=("phenotyping", "morphology", "observations", "image analysis"),
        backend_sources=("api/bijmantra/phenotyping", "modules/phenotyping", "modules/plant_sciences"),
        frontend_sources=("divisions/phenotyping", "divisions/plant-sciences"),
    ),
    "field_operations": DomainBoundary(
        name="field_operations",
        product_name="Field Operations",
        meaning="Field and operations",
        owns=("field", "trials", "operations", "agronomy", "irrigation"),
        backend_sources=("api/bijmantra/field", "api/bijmantra/trials", "api/bijmantra/operations"),
        frontend_sources=(
            "divisions/agronomy",
            "divisions/field",
            "divisions/harvest",
            "divisions/irrigation",
            "divisions/water-irrigation",
        ),
    ),
    "intelligence": DomainBoundary(
        name="intelligence",
        product_name="Intelligence",
        meaning="Intelligence and analytics",
        owns=("ai", "analytics", "knowledge graph", "compute orchestration"),
        backend_sources=(
            "api/bijmantra/ai",
            "api/bijmantra/compute",
            "modules/ai",
            "modules/bio_analytics",
            "services/knowledge_graph_service.py",
        ),
        frontend_sources=("features/ai-chat", "future product-owned knowledge graph surface"),
    ),
    "commercial": DomainBoundary(
        name="commercial",
        product_name="Commercial",
        meaning="Commercial and business workflows",
        owns=("commercial", "inventory", "business operations"),
        backend_sources=("api/bijmantra/inventory",),
        frontend_sources=("divisions/commercial",),
    ),
    "knowledge": DomainBoundary(
        name="knowledge",
        product_name="Knowledge",
        meaning="Knowledge, training, and learning",
        owns=("knowledge", "training", "documentation intelligence"),
        backend_sources=("future knowledge/training services",),
        frontend_sources=("future knowledge/training surface",),
    ),
}


DOMAIN_CAPABILITY_CODE_ROOTS: dict[str, CapabilityCodeRoot] = {
    "intelligence.knowledge_graph": CapabilityCodeRoot(
        domain="intelligence",
        capability="knowledge_graph",
        backend_root="backend/app/domains/intelligence/capabilities/knowledge_graph",
        frontend_root=None,
    ),
    "germplasm.accession_passport": CapabilityCodeRoot(
        domain="germplasm",
        capability="accession_passport",
        backend_root="backend/app/domains/germplasm/capabilities/accession_passport",
        frontend_root=None,
    ),
    "field_operations.trial_analysis": CapabilityCodeRoot(
        domain="field_operations",
        capability="trial_analysis",
        backend_root="backend/app/domains/field_operations/capabilities/trial_analysis",
        frontend_root=None,
    ),
    "knowledge.research_asset_core": CapabilityCodeRoot(
        domain="knowledge",
        capability="research_asset_core",
        backend_root="backend/app/domains/knowledge/capabilities/research_asset_core",
        frontend_root=None,
    ),
}


DOMAIN_OWNERSHIP: dict[str, DomainName] = {
    "ai": "intelligence",
    "analytics": "intelligence",
    "breeding": "breeding",
    "commercial": "commercial",
    "compute": "intelligence",
    "environment": "field_operations",
    "field": "field_operations",
    "genomics": "breeding",
    "germplasm": "germplasm",
    "inventory": "commercial",
    "knowledge_graph": "intelligence",
    "operations": "field_operations",
    "phenotyping": "phenotyping",
    "seed_bank": "germplasm",
    "seed_operations": "germplasm",
    "trial_analysis": "field_operations",
    "trials": "field_operations",
}


DOMAIN_CAPABILITIES: dict[DomainName, tuple[str, ...]] = {
    "breeding": (
        "breeding_programs",
        "crossing_projects",
        "crossing_planner",
        "planned_crosses",
        "parent_selection",
        "progeny_and_pedigree",
        "selection_decisions",
        "breeding_values",
        "genetic_gain",
        "speed_breeding",
        "doubled_haploid",
        "breeding_pipeline",
        "genomic_selection_strategy",
    ),
    "germplasm": (
        "germplasm_identity",
        "accession_passport",
        "accession_passport_mcpd",
        "germplasm_collection",
        "germplasm_search",
        "germplasm_attributes",
        "pedigree_links",
        "seed_bank_accessions",
        "seed_lots",
        "seed_inventory",
        "storage_vaults",
        "material_transfer_agreements",
        "barcode_and_labeling",
        "traceability",
    ),
    "phenotyping": (
        "trait_catalog",
        "observation_variables",
        "scales_and_methods",
        "observation_units",
        "observations",
        "field_data_collection",
        "phenotype_comparison",
        "image_metadata",
        "plant_vision_annotation",
        "morphology",
        "nirs_analysis",
        "trait_ontology_mapping",
    ),
    "field_operations": (
        "trials",
        "trial_analysis",
        "studies",
        "locations",
        "seasons",
        "field_layout",
        "field_book",
        "field_planning",
        "nursery_management",
        "crop_calendar",
        "agronomy_operations",
        "irrigation",
        "harvest",
        "weather",
        "soil",
        "sensor_networks",
        "uav_and_field_scans",
        "disease_and_stress_monitoring",
        "resource_management",
    ),
    "intelligence": (
        "knowledge_graph",
        "reevu_chat",
        "ai_configuration",
        "vector_search",
        "retrieval_and_evidence",
        "ontology_reasoning",
        "analytics_dashboards",
        "compute_orchestration",
        "genomic_compute_engines",
        "statistical_models",
        "simulation",
        "model_registry",
        "fair_federated_retrieval",
    ),
    "commercial": (
        "commercial_catalog",
        "warehouse",
        "dispatch",
        "orders",
        "cost_analysis",
        "pricing_and_market_analysis",
        "compliance_tracking",
        "licensing",
        "marketplace",
        "label_printing_business_flow",
    ),
    "knowledge": (
        "research_asset_core",
        "training_hub",
        "protocol_library",
        "documentation_intelligence",
        "help_center",
        "glossary",
        "release_notes",
        "research_publication_tracking",
        "educational_content",
    ),
}


STANDARDS_SPINE_CAPABILITIES = (
    "brapi_adapter",
    "research_asset_core",
    "fair_metadata",
    "federated_asset_registry",
    "ontology_reference_mapping",
    "mcpd_passport_mapping",
    "miappe_export",
    "cg_core_mapping",
    "crop_ontology_mapping",
    "aggateway_adapter_candidate",
    "darwin_core_adapter_candidate",
)


TRANSITIONAL_SURFACES = (
    "backend/app/modules",
    "backend/app/services",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/crud",
    "frontend/src/pages",
)


INTERNAL_PLATFORM_SURFACES = {
    "developer_control_plane": "Internal app-development coordination and autonomy control surface",
    "control_plane": "Internal architecture template and orchestration surface",
}


def resolve_domain_for_capability(capability: str) -> DomainBoundary | None:
    """Resolve a capability slug to its target domain boundary."""

    domain_name = DOMAIN_OWNERSHIP.get(capability)
    if domain_name is None:
        for candidate_domain_name, capabilities in DOMAIN_CAPABILITIES.items():
            if capability in capabilities:
                domain_name = candidate_domain_name
                break
    if domain_name is None:
        return None
    return DOMAIN_BOUNDARIES[domain_name]


def resolve_domain_name(name: str) -> DomainName | None:
    """Resolve a canonical or legacy domain name to the canonical key."""

    if name in DOMAIN_BOUNDARIES:
        return cast(DomainName, name)
    legacy_name = LEGACY_DOMAIN_ALIASES.get(name)
    if legacy_name is None:
        return None
    return cast(DomainName, legacy_name)


# Compatibility aliases for older architecture documents and agent prompts.
LokaName = DomainName
LokaBoundary = DomainBoundary
LOKA_BOUNDARIES = DOMAIN_BOUNDARIES
LOKA_DOMAIN_OWNERSHIP = DOMAIN_OWNERSHIP
LEGACY_LOKA_ALIASES = LEGACY_DOMAIN_ALIASES
resolve_loka_for_domain = resolve_domain_for_capability
resolve_loka_name = resolve_domain_name
