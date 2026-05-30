from pathlib import Path

import yaml

from app.domains.registry import (
    DOMAIN_BOUNDARIES,
    DOMAIN_CAPABILITY_CODE_ROOTS,
    DOMAIN_CREATION_CRITERIA,
    DOMAIN_GROWTH_POLICY,
    FDCA_STATUS,
    FEDERATION_SPINE,
)
from app.platform.dominions import (
    CAPABILITY_MANIFESTS,
    DOMINION_REGISTRY,
    PLATFORM_STANDARDS_SPINE,
    backend_route_matches,
    capabilities_for_backend_route,
    capabilities_for_dominion,
    dominions_for_domain,
    resolve_capability_manifest,
    resolve_dominion,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_domain_registry_is_open_not_a_fixed_taxonomy() -> None:
    assert DOMAIN_GROWTH_POLICY == "open_registry_not_fixed_taxonomy"
    assert FEDERATION_SPINE == "research_asset_core_inside_modular_monolith"
    assert FDCA_STATUS == "federation_pattern_not_replacement_architecture"
    assert "stable ubiquitous language" in DOMAIN_CREATION_CRITERIA
    assert "tenant and policy boundary" in DOMAIN_CREATION_CRITERIA
    assert "migration path from transitional surfaces" in DOMAIN_CREATION_CRITERIA
    assert set(DOMAIN_BOUNDARIES) >= {
        "breeding",
        "germplasm",
        "phenotyping",
        "field_operations",
        "intelligence",
        "commercial",
        "knowledge",
    }
    assert "knowledge.research_asset_core" in DOMAIN_CAPABILITY_CODE_ROOTS


def test_dominions_are_product_suites_not_backend_domains() -> None:
    assert len(DOMINION_REGISTRY) >= 10
    assert "intelligence_fabric" in DOMINION_REGISTRY
    assert "plant_science_rnd" in DOMINION_REGISTRY
    assert "scientific_publishing_fair_exchange" in DOMINION_REGISTRY
    assert "intelligence_fabric" not in DOMAIN_BOUNDARIES
    assert resolve_dominion("intelligence_fabric").primary_domains == ("intelligence",)
    assert dominions_for_domain("intelligence")


def test_platform_standards_spine_keeps_brapi_and_fair_visible() -> None:
    assert "BrAPI v2.1" in PLATFORM_STANDARDS_SPINE
    assert "FAIR" in PLATFORM_STANDARDS_SPINE
    assert "MCPD" in PLATFORM_STANDARDS_SPINE
    assert "MIAPPE" in PLATFORM_STANDARDS_SPINE
    assert "Crop Ontology" in PLATFORM_STANDARDS_SPINE
    assert "DataCite DOI" in PLATFORM_STANDARDS_SPINE


def test_capability_manifests_reference_valid_dominions_and_domains() -> None:
    assert CAPABILITY_MANIFESTS

    for manifest in CAPABILITY_MANIFESTS.values():
        assert manifest.dominion in DOMINION_REGISTRY
        assert manifest.owner_domain in DOMAIN_BOUNDARIES
        assert set(manifest.supporting_domains).issubset(DOMAIN_BOUNDARIES)
        assert manifest.required_permissions
        assert manifest.suggested_roles
        assert manifest.semantic_spine_adrs
        assert manifest.install_behavior
        assert manifest.uninstall_behavior
        assert manifest.data_scopes
        assert manifest.audit_events
        assert manifest.backend_routes
        assert manifest.frontend_routes
        assert manifest.tests


def test_brapi_remains_primary_standard_for_breeding_community_paths() -> None:
    trial_analysis = resolve_capability_manifest("plant_science_rnd.trial_analysis")
    accession_passport = resolve_capability_manifest("germplasm_global_seed_registry.accession_passport")

    assert trial_analysis is not None
    assert accession_passport is not None
    assert "BrAPI v2.1" in trial_analysis.standards
    assert "BrAPI v2.1" in accession_passport.standards
    assert any(route.startswith("/brapi/v2") for route in trial_analysis.backend_routes)
    assert any(route.startswith("/brapi/v2") for route in accession_passport.backend_routes)


def test_publishers_is_a_first_class_fair_exchange_capability() -> None:
    publishers = resolve_capability_manifest("scientific_publishing_fair_exchange.ai_native_publications")

    assert publishers is not None
    assert publishers.owner_domain == "knowledge"
    assert "intelligence" in publishers.supporting_domains
    assert "FAIR" in publishers.standards
    assert "JSON-LD" in publishers.standards
    assert "DataCite DOI" in publishers.standards
    assert "ADR-024" in publishers.semantic_spine_adrs
    assert "publisher_editor" in publishers.suggested_roles
    assert "DOI" in publishers.install_behavior
    assert "publication.hil_signed_off" in publishers.audit_events
    assert ".github/docs/denish-ideas/2026-05-21-bijmantra-publishers.md" in publishers.source_context


def test_research_asset_core_is_the_fdca_reconciliation_capability() -> None:
    research_assets = resolve_capability_manifest(
        "scientific_publishing_fair_exchange.research_asset_core"
    )

    assert research_assets is not None
    assert research_assets.owner_domain == "knowledge"
    assert "intelligence" in research_assets.supporting_domains
    assert "FAIR" in research_assets.standards
    assert "BrAPI v2.1" in research_assets.standards
    assert "ADR-036" in research_assets.semantic_spine_adrs
    assert "/api/v2/fair-metadata/*" in research_assets.backend_routes
    assert "/api/v2/federated-assets/*" in research_assets.backend_routes
    assert "research_assets.promote_fair" in research_assets.required_permissions
    assert "federated_asset_promote_fair" in research_assets.audit_events
    assert "backend-rs/BijMantra Realignment Report from Fairgrounds Signals.md" in (
        research_assets.source_context
    )


def test_capabilities_are_grouped_by_dominion_without_becoming_domain_folders() -> None:
    intelligence_capabilities = capabilities_for_dominion("intelligence_fabric")

    assert intelligence_capabilities
    assert all(capability.dominion == "intelligence_fabric" for capability in intelligence_capabilities)
    assert all(capability.owner_domain in DOMAIN_BOUNDARIES for capability in intelligence_capabilities)


def test_backend_route_patterns_match_concrete_capability_paths() -> None:
    assert backend_route_matches("/api/v2/knowledge-graph/*", "/api/v2/knowledge-graph")
    assert backend_route_matches("/api/v2/knowledge-graph/*", "/api/v2/knowledge-graph/edges")
    assert backend_route_matches(
        "/api/v2/knowledge-graph/*",
        "/api/v2/knowledge-graph/evidence-pack?asset_id=IR64",
    )
    assert not backend_route_matches("/api/v2/knowledge-graph/*", "/api/v2/knowledge")


def test_capabilities_can_be_resolved_from_backend_routes() -> None:
    knowledge_graph_capabilities = capabilities_for_backend_route("/api/v2/knowledge-graph/edges")
    inventory_capabilities = capabilities_for_backend_route("/api/v2/inventory/seed-lots")

    assert [capability.id for capability in knowledge_graph_capabilities] == [
        "intelligence_fabric.knowledge_graph"
    ]
    assert "seedops_commercialization.seed_lot_traceability" in {
        capability.id for capability in inventory_capabilities
    }


def test_knowledge_graph_manifest_points_to_canonical_capability_pack() -> None:
    manifest = resolve_capability_manifest("intelligence_fabric.knowledge_graph")

    assert manifest is not None
    assert manifest.backend_code_root == "backend/app/domains/intelligence/capabilities/knowledge_graph"
    assert (REPO_ROOT / manifest.backend_code_root).is_dir()
    assert "tests/domains/intelligence" in manifest.tests


def test_knowledge_graph_capability_pack_manifest_matches_registry() -> None:
    manifest = resolve_capability_manifest("intelligence_fabric.knowledge_graph")
    assert manifest is not None

    capability_manifest = yaml.safe_load(
        (REPO_ROOT / manifest.backend_code_root / "capability.yaml").read_text()
    )

    assert capability_manifest["id"] == manifest.id
    assert capability_manifest["title"] == manifest.title
    assert capability_manifest["dominion"] == manifest.dominion
    assert capability_manifest["owner_domain"] == manifest.owner_domain
    assert tuple(capability_manifest["supporting_domains"]) == manifest.supporting_domains
    assert tuple(capability_manifest["standards"]) == manifest.standards
    assert tuple(capability_manifest["semantic_spine_adrs"]) == manifest.semantic_spine_adrs
    assert tuple(capability_manifest["frontend_routes"]) == manifest.frontend_routes
    assert tuple(capability_manifest["backend_routes"]) == manifest.backend_routes
    assert tuple(capability_manifest["data_scopes"]) == manifest.data_scopes
    assert tuple(capability_manifest["required_permissions"]) == manifest.required_permissions
    assert tuple(capability_manifest["suggested_roles"]) == manifest.suggested_roles
    assert tuple(capability_manifest["audit_events"]) == manifest.audit_events
    assert tuple(capability_manifest["source_context"]) == manifest.source_context


def test_backend_capability_pack_manifests_match_registered_capabilities() -> None:
    manifest_paths = sorted((REPO_ROOT / "backend/app/domains").glob("*/capabilities/*/capability.yaml"))

    assert manifest_paths
    for manifest_path in manifest_paths:
        capability_manifest = yaml.safe_load(manifest_path.read_text())
        registered = resolve_capability_manifest(capability_manifest["id"])

        assert registered is not None
        assert capability_manifest["title"] == registered.title
        assert capability_manifest["dominion"] == registered.dominion
        assert capability_manifest["owner_domain"] == registered.owner_domain
        assert tuple(capability_manifest["backend_routes"]) == registered.backend_routes
        assert tuple(capability_manifest["required_permissions"]) == registered.required_permissions
        assert tuple(capability_manifest["data_scopes"]) == registered.data_scopes
        assert tuple(capability_manifest["audit_events"]) == registered.audit_events


def test_frontend_capability_seed_matches_knowledge_graph_manifest() -> None:
    manifest = resolve_capability_manifest("intelligence_fabric.knowledge_graph")
    assert manifest is not None
    frontend_source = (
        REPO_ROOT / "frontend/src/framework/registry/capabilities.ts"
    ).read_text()

    assert f"id: '{manifest.id}'" in frontend_source
    assert f"ownerDomain: '{manifest.owner_domain}'" in frontend_source
    for route in manifest.frontend_routes:
        assert f"'{route}'" in frontend_source
    for route in manifest.backend_routes:
        assert f"'{route}'" in frontend_source
    for permission in manifest.required_permissions:
        assert f"'{permission}'" in frontend_source
