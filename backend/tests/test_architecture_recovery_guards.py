import ast
from pathlib import Path

import yaml

from app.domains.registry import (
    CAPABILITY_LAYER_ROOT,
    CAPABILITY_LAYER_RULE,
    CANONICAL_ARCHITECTURE,
    DOMAIN_CAPABILITIES,
    DOMAIN_CAPABILITY_CODE_ROOTS,
    DOMAIN_BOUNDARIES,
    DOMAIN_CREATION_CRITERIA,
    DOMAIN_GROWTH_POLICY,
    DOMAIN_OWNERSHIP,
    HEXAGONAL_DOMAIN_LAYERS,
    LEGACY_ARCHITECTURE_ALIASES,
    TRANSITIONAL_SURFACES,
    resolve_domain_for_capability,
    resolve_domain_name,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_DOMAIN_IMPORTS = (
    "from fastapi",
    "import fastapi",
    "from sqlalchemy",
    "import sqlalchemy",
    "from app.core.database",
    "from app.models",
    "from app.crud",
    "import redis",
    "import httpx",
    "import requests",
)


def test_domain_registry_declares_the_canonical_architecture() -> None:
    assert CANONICAL_ARCHITECTURE == "domain_bounded_modular_monolith_with_hexagonal_architecture"
    assert "loka_modular_monolith_with_hexagonal_architecture" in LEGACY_ARCHITECTURE_ALIASES
    assert "loka_hexagonal_modular_monolith" in LEGACY_ARCHITECTURE_ALIASES
    assert DOMAIN_GROWTH_POLICY == "open_registry_not_fixed_taxonomy"
    assert "stable ubiquitous language" in DOMAIN_CREATION_CRITERIA
    assert "clear data ownership" in DOMAIN_CREATION_CRITERIA
    assert set(DOMAIN_BOUNDARIES) >= {
        "breeding",
        "germplasm",
        "phenotyping",
        "field_operations",
        "intelligence",
        "commercial",
        "knowledge",
    }


def test_germplasm_is_the_canonical_seed_treasury_domain_name() -> None:
    assert "germplasm" in DOMAIN_BOUNDARIES
    assert "bijkosha" not in DOMAIN_BOUNDARIES
    assert "bija_kosha" not in DOMAIN_BOUNDARIES
    assert DOMAIN_OWNERSHIP["germplasm"] == "germplasm"
    assert DOMAIN_OWNERSHIP["seed_bank"] == "germplasm"
    assert resolve_domain_name("germplasm") == "germplasm"
    assert resolve_domain_name("bijkosha") == "germplasm"
    assert resolve_domain_name("bija_kosha") == "germplasm"
    assert resolve_domain_name("bij-kosha") == "germplasm"


def test_sanskrit_domain_names_are_legacy_aliases_only() -> None:
    assert resolve_domain_name("sristi") == "breeding"
    assert resolve_domain_name("rupa") == "phenotyping"
    assert resolve_domain_name("kshetra") == "field_operations"
    assert resolve_domain_name("medha") == "intelligence"
    assert resolve_domain_name("vani") == "commercial"
    assert resolve_domain_name("vidya") == "knowledge"


def test_all_canonical_domains_have_hexagonal_package_shape() -> None:
    domains_root = REPO_ROOT / "backend/app/domains"

    for domain_name in DOMAIN_BOUNDARIES:
        domain_root = domains_root / domain_name
        assert domain_root.is_dir()
        assert (domain_root / "__init__.py").exists()
        assert (domain_root / "README.md").exists()
        for layer_name in HEXAGONAL_DOMAIN_LAYERS:
            layer_root = domain_root / layer_name
            assert layer_root.is_dir()
            assert (layer_root / "__init__.py").exists()


def test_domains_compatibility_namespace_has_no_implementation_tree() -> None:
    compatibility_root = REPO_ROOT / "backend/app/lokas"

    assert (compatibility_root / "__init__.py").exists()
    assert (compatibility_root / "registry.py").exists()
    assert not any(path.is_dir() for path in compatibility_root.iterdir() if path.name != "__pycache__")


def test_domain_cartography_matches_registry_and_hexagonal_shape() -> None:
    cartography = (REPO_ROOT / ".github/docs/architecture/2026-05-22-bijmantra-system-cartography.md").read_text()

    assert "backend/app/domains/<domain>/" in cartography
    for layer_name in HEXAGONAL_DOMAIN_LAYERS:
        assert f"{layer_name}/" in cartography

    for domain_name in DOMAIN_BOUNDARIES:
        assert f"├── {domain_name}/" in cartography or f"└── {domain_name}/" in cartography


def test_domain_registry_yaml_is_the_same_architecture_spine() -> None:
    registry = yaml.safe_load((REPO_ROOT / "backend/app/domain_registry.yaml").read_text())

    assert registry["architecture"]["type"] == CANONICAL_ARCHITECTURE
    assert registry["architecture"]["code_surface"] == "backend/app/domains"
    assert registry["architecture"]["code_vocabulary"] == "industry_domain"
    assert registry["architecture"]["legacy_vocabulary"] == "LOKA"
    assert registry["architecture"]["migration_rule"] == "wrap_extract_drain"
    assert registry["architecture"]["domain_growth_policy"] == DOMAIN_GROWTH_POLICY
    assert "stable ubiquitous language" in registry["domain_creation_criteria"]
    assert "tenant and policy boundary" in registry["domain_creation_criteria"]
    assert tuple(registry["hexagonal_shape"]["canonical_layers"]) == HEXAGONAL_DOMAIN_LAYERS
    assert tuple(registry["domains"]) == tuple(DOMAIN_BOUNDARIES)
    assert "bija_kosha" not in registry["domains"]
    assert registry["legacy_domain_aliases"]["medha"] == "intelligence"
    assert registry["legacy_domain_aliases"]["bijkosha"] == "germplasm"


def test_capability_layer_prevents_domains_from_becoming_god_buckets() -> None:
    registry = yaml.safe_load((REPO_ROOT / "backend/app/domain_registry.yaml").read_text())

    assert CAPABILITY_LAYER_ROOT == "capabilities"
    assert CAPABILITY_LAYER_RULE == "domain -> capability -> hexagonal slice"
    assert registry["capability_layer"]["status"] == "required_for_large_domain_growth"
    assert (
        registry["capability_layer"]["current_code_roots"]["intelligence.knowledge_graph"]["backend"]
        == DOMAIN_CAPABILITY_CODE_ROOTS["intelligence.knowledge_graph"].backend_root
    )
    assert (
        registry["capability_layer"]["current_code_roots"]["intelligence.knowledge_graph"]["status"]
        == "drained_reference_slice"
    )
    assert (
        registry["capability_layer"]["current_code_roots"]["intelligence.knowledge_graph"][
            "legacy_service_state"
        ]
        == "compatibility_facade_only"
    )
    assert (
        registry["capability_layer"]["current_code_roots"]["germplasm.accession_passport"]["backend"]
        == DOMAIN_CAPABILITY_CODE_ROOTS["germplasm.accession_passport"].backend_root
    )
    assert (
        registry["capability_layer"]["current_code_roots"]["germplasm.accession_passport"]["status"]
        == "active_mcpd_reference_import_export_access_audited_slice"
    )
    assert (
        registry["capability_layer"]["current_code_roots"]["germplasm.accession_passport"][
            "route_owner"
        ]
        == [
            "backend/app/domains/germplasm/capabilities/accession_passport/adapters/api/mcpd.py",
            "backend/app/domains/germplasm/capabilities/accession_passport/adapters/api/brapi_germplasm.py",
        ]
    )
    assert (
        registry["capability_layer"]["current_code_roots"]["field_operations.trial_analysis"]["backend"]
        == DOMAIN_CAPABILITY_CODE_ROOTS["field_operations.trial_analysis"].backend_root
    )
    assert (
        registry["capability_layer"]["current_code_roots"]["field_operations.trial_analysis"]["status"]
        == "scaffolded_foundation"
    )
    assert (
        registry["capability_layer"]["current_code_roots"]["knowledge.research_asset_core"]["status"]
        == "active_foundation"
    )
    assert (
        registry["capability_layer"]["current_code_roots"]["knowledge.research_asset_core"][
            "legacy_service_state"
        ]
        == "compatibility_facade_only"
    )
    assert registry["capability_inventory"]["status"] == "initial_not_exhaustive"
    assert registry["capability_inventory"]["intelligence"] == list(DOMAIN_CAPABILITIES["intelligence"])
    assert registry["capability_inventory"]["germplasm"] == list(DOMAIN_CAPABILITIES["germplasm"])
    assert registry["capability_inventory"]["field_operations"] == list(
        DOMAIN_CAPABILITIES["field_operations"]
    )
    assert resolve_domain_for_capability("knowledge_graph") == DOMAIN_BOUNDARIES["intelligence"]
    assert resolve_domain_for_capability("accession_passport") == DOMAIN_BOUNDARIES["germplasm"]
    assert resolve_domain_for_capability("accession_passport_mcpd") == DOMAIN_BOUNDARIES["germplasm"]
    assert resolve_domain_for_capability("trial_analysis") == DOMAIN_BOUNDARIES["field_operations"]


def test_brapi_germplasm_routes_remain_behind_accession_passport_policy() -> None:
    source_path = (
        REPO_ROOT
        / "backend/app/domains/germplasm/capabilities/accession_passport/adapters/api/brapi_germplasm.py"
    )
    source = source_path.read_text()
    module = ast.parse(source)
    route_functions = {}

    for node in module.body:
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and ast.unparse(decorator.func).startswith("router."):
                route_functions[node.name] = ast.get_source_segment(source, node) or ""

    read_routes = {
        "list_germplasm",
        "get_germplasm",
        "get_germplasm_pedigree",
        "get_germplasm_progeny",
        "get_germplasm_mcpd",
    }
    manage_routes = {
        "create_germplasm",
        "update_germplasm",
        "delete_germplasm",
    }

    assert set(route_functions) == read_routes | manage_routes
    for route_name in read_routes:
        assert "await _require_brapi_germplasm_read_access(current_user, db)" in route_functions[route_name]
    for route_name in manage_routes:
        assert (
            "await _require_brapi_germplasm_manage_access(current_user, db)"
            in route_functions[route_name]
        )
    assert 'required_permission="germplasm.read"' in source
    assert 'required_permission="germplasm.passport.manage"' in source


def test_legacy_brapi_germplasm_module_is_a_compatibility_shim() -> None:
    source = (REPO_ROOT / "backend/app/api/brapi/v2/germplasm.py").read_text()

    assert "capabilities.accession_passport.adapters.api.brapi_germplasm" in source
    assert "router" in source
    assert "APIRouter" not in source
    assert "HTTPException" not in source
    assert "Depends" not in source
    assert "Query" not in source
    assert "@router." not in source
    assert "select(" not in source
    assert "GermplasmModel" not in source
    assert len(source.splitlines()) <= 60


def test_backend_capability_packs_have_manifest_and_hexagonal_shape() -> None:
    domains_root = REPO_ROOT / "backend/app/domains"
    capability_roots = sorted(
        path
        for path in domains_root.glob("*/capabilities/*")
        if path.is_dir() and path.name != "__pycache__"
    )

    assert capability_roots
    for capability_root in capability_roots:
        manifest_path = capability_root / "capability.yaml"
        assert manifest_path.exists()
        manifest = yaml.safe_load(manifest_path.read_text())
        owner_domain = capability_root.parent.parent.name

        assert manifest["owner_domain"] == owner_domain
        assert manifest["id"].endswith(f".{capability_root.name}")
        assert manifest["backend_routes"]
        assert manifest["required_permissions"]
        assert manifest["data_scopes"]
        assert manifest["audit_events"]

        for layer_name in HEXAGONAL_DOMAIN_LAYERS:
            layer_root = capability_root / layer_name
            assert layer_root.is_dir()
            assert (layer_root / "__init__.py").exists()


def test_transitional_architecture_rules_define_modules_versus_domains() -> None:
    rules = (
        REPO_ROOT
        / ".github/docs/architecture/2026-05-24-transitional-architecture-rules.md"
    ).read_text()

    assert "**Document Status:** ACTIVE" in rules
    assert "modules/" in rules
    assert "transitional runtime-oriented capability modules" in rules
    assert "domains/" in rules
    assert "canonical business/domain ownership boundaries" in rules
    assert "models/ schemas/ crud/ services/" in rules
    assert "legacy layered architecture" in rules


def test_domain_layers_do_not_import_infrastructure() -> None:
    domains_root = REPO_ROOT / "backend/app/domains"

    for domain_name in DOMAIN_BOUNDARIES:
        for source_path in (domains_root / domain_name / "domain").rglob("*.py"):
            source = source_path.read_text()
            for forbidden_import in FORBIDDEN_DOMAIN_IMPORTS:
                assert forbidden_import not in source


def test_domains_do_not_import_other_domain_internals() -> None:
    domains_root = REPO_ROOT / "backend/app/domains"
    internal_layers = ("domain", "application", "adapters")

    for domain_name in DOMAIN_BOUNDARIES:
        for source_path in (domains_root / domain_name).rglob("*.py"):
            source = source_path.read_text()
            for other_domain_name in DOMAIN_BOUNDARIES:
                if other_domain_name == domain_name:
                    continue
                for internal_layer in internal_layers:
                    forbidden = f"app.domains.{other_domain_name}.{internal_layer}"
                    assert forbidden not in source


def test_intelligence_knowledge_graph_retrieval_paths_use_hexagonal_boundary() -> None:
    api_source = (
        REPO_ROOT
        / "backend/app/domains/intelligence/capabilities/knowledge_graph/adapters/api/knowledge_graph.py"
    ).read_text()

    expected_files = (
        "backend/app/domains/intelligence/capabilities/knowledge_graph/capability.yaml",
        "backend/app/domains/intelligence/capabilities/knowledge_graph/schemas/knowledge_graph.py",
        "backend/app/domains/intelligence/capabilities/knowledge_graph/ports/knowledge_graph.py",
        "backend/app/domains/intelligence/capabilities/knowledge_graph/application/knowledge_graph.py",
        "backend/app/domains/intelligence/capabilities/knowledge_graph/adapters/knowledge_graph.py",
        "backend/app/domains/intelligence/capabilities/knowledge_graph/adapters/api/knowledge_graph.py",
        "backend/app/domains/intelligence/capabilities/knowledge_graph/domain/knowledge_graph_retrieval.py",
        "backend/app/domains/intelligence/capabilities/knowledge_graph/adapters/knowledge_graph_persistence.py",
    )
    for relative_path in expected_files:
        assert (REPO_ROOT / relative_path).exists()

    assert "KnowledgeGraphExplorerSnapshotQuery" in api_source
    assert "KnowledgeGraphExplorerSnapshotUseCase" in api_source
    assert "KnowledgeGraphRankedCandidatesQuery" in api_source
    assert "KnowledgeGraphRankedCandidatesUseCase" in api_source
    assert "KnowledgeGraphRetrievalDiagnosticsQuery" in api_source
    assert "KnowledgeGraphRetrievalDiagnosticsUseCase" in api_source
    assert "KnowledgeGraphRetrievalCandidatesQuery" in api_source
    assert "KnowledgeGraphRetrievalCandidatesUseCase" in api_source
    assert "KnowledgeGraphReevuDryRunPreviewQuery" in api_source
    assert "KnowledgeGraphReevuDryRunPreviewUseCase" in api_source
    assert "KnowledgeGraphEvidenceSearchQuery" in api_source
    assert "KnowledgeGraphEvidenceSearchUseCase" in api_source
    assert "KnowledgeGraphEvidencePackQuery" in api_source
    assert "KnowledgeGraphEvidencePackUseCase" in api_source
    assert "KnowledgeGraphFacetsQuery" in api_source
    assert "KnowledgeGraphFacetsUseCase" in api_source
    assert "KnowledgeGraphEdgesListQuery" in api_source
    assert "KnowledgeGraphEdgesListUseCase" in api_source
    assert "KnowledgeGraphNeighborhoodQuery" in api_source
    assert "KnowledgeGraphNeighborhoodUseCase" in api_source
    assert "KnowledgeGraphUpsertEdgeCommand" in api_source
    assert "KnowledgeGraphUpsertEdgeUseCase" in api_source
    assert "SqlAlchemyKnowledgeGraphAdapter" in api_source
    assert "knowledge_graph_service.build_explorer_snapshot" not in api_source
    assert "knowledge_graph_service.rank_retrieval_candidates" not in api_source
    assert "knowledge_graph_service.build_retrieval_diagnostics" not in api_source
    assert "knowledge_graph_service.build_retrieval_candidates" not in api_source
    assert "knowledge_graph_service.build_reevu_dry_run_preview" not in api_source
    assert "knowledge_graph_service.search_evidence" not in api_source
    assert "knowledge_graph_service.build_evidence_pack" not in api_source
    assert "knowledge_graph_service.get_facets" not in api_source
    assert "knowledge_graph_service.list_edges" not in api_source
    assert "knowledge_graph_service.get_neighborhood" not in api_source
    assert "knowledge_graph_service.upsert_edge" not in api_source


def test_intelligence_knowledge_graph_active_docs_record_drained_reference_slice() -> None:
    active_docs = (
        REPO_ROOT / "backend/app/domains/intelligence/README.md",
        REPO_ROOT
        / ".github/docs/architecture/2026-05-21-domain-bounded-modular-monolith-recovery-roadmap.md",
        REPO_ROOT / ".github/docs/architecture/2026-05-22-bijmantra-system-cartography.md",
        REPO_ROOT / ".github/docs/architecture/CURRENT.md",
    )

    for doc_path in active_docs:
        source = doc_path.read_text()
        assert "compatibility facade" in source
        assert "knowledge_graph_legacy.py" not in source
        assert "transitional bridge" not in source
        assert "transitional delegator" not in source


def test_intelligence_knowledge_graph_root_files_are_compatibility_shims() -> None:
    legacy_files = (
        "backend/app/domains/intelligence/schemas/knowledge_graph.py",
        "backend/app/domains/intelligence/ports/knowledge_graph.py",
        "backend/app/domains/intelligence/application/knowledge_graph.py",
        "backend/app/domains/intelligence/adapters/knowledge_graph.py",
        "backend/app/domains/intelligence/adapters/knowledge_graph_persistence.py",
        "backend/app/domains/intelligence/domain/knowledge_graph_retrieval.py",
    )

    for relative_path in legacy_files:
        source = (REPO_ROOT / relative_path).read_text()
        assert "capabilities.knowledge_graph" in source
        assert "noqa: F401,F403" in source
        assert len(source.splitlines()) <= 4


def test_new_backend_code_imports_knowledge_graph_capability_pack_not_root_shims() -> None:
    allowed_compatibility_files = {
        REPO_ROOT / "backend/app/domains/intelligence/schemas/knowledge_graph.py",
        REPO_ROOT / "backend/app/domains/intelligence/ports/knowledge_graph.py",
        REPO_ROOT / "backend/app/domains/intelligence/application/knowledge_graph.py",
        REPO_ROOT / "backend/app/domains/intelligence/adapters/knowledge_graph.py",
        REPO_ROOT / "backend/app/domains/intelligence/adapters/knowledge_graph_persistence.py",
        REPO_ROOT / "backend/app/domains/intelligence/domain/knowledge_graph_retrieval.py",
        REPO_ROOT / "backend/app/domains/intelligence/contracts/__init__.py",
        REPO_ROOT / "backend/app/domains/intelligence/contracts/knowledge_graph.py",
    }
    forbidden_imports = (
        "app.domains.intelligence.schemas.knowledge_graph",
        "app.domains.intelligence.ports.knowledge_graph",
        "app.domains.intelligence.application.knowledge_graph",
        "app.domains.intelligence.adapters.knowledge_graph",
        "app.domains.intelligence.adapters.knowledge_graph_persistence",
        "app.domains.intelligence.domain.knowledge_graph_retrieval",
    )

    for source_path in (REPO_ROOT / "backend/app").rglob("*.py"):
        if source_path in allowed_compatibility_files:
            continue
        source = source_path.read_text()
        for forbidden_import in forbidden_imports:
            assert forbidden_import not in source


def test_intelligence_knowledge_graph_retrieval_candidate_builder_owns_grouping() -> None:
    service_source = (
        REPO_ROOT / "backend/app/services/knowledge_graph_service.py"
    ).read_text()
    application_source = (
        REPO_ROOT
        / "backend/app/domains/intelligence/capabilities/knowledge_graph/application/knowledge_graph.py"
    ).read_text()

    assert "SqlAlchemyKnowledgeGraphAdapter" in service_source
    assert "KnowledgeGraphRetrievalCandidatesQuery" in service_source
    assert "LegacyKnowledgeGraph" not in service_source
    assert "grouped_results" not in service_source
    assert "class KnowledgeGraphRetrievalCandidatesBuilder" in application_source
    assert "grouped_results" in application_source


def test_intelligence_knowledge_graph_persistence_adapter_owns_sqlalchemy_queries() -> None:
    service_source = (
        REPO_ROOT / "backend/app/services/knowledge_graph_service.py"
    ).read_text()
    persistence_source = (
        REPO_ROOT
        / "backend/app/domains/intelligence/capabilities/knowledge_graph/adapters/knowledge_graph_persistence.py"
    ).read_text()

    assert "SqlAlchemyKnowledgeGraphAdapter" in service_source
    assert "SqlAlchemyKnowledgeGraphPersistence" not in service_source
    assert "from sqlalchemy import" not in service_source
    assert "select(" not in service_source
    assert "func.count" not in service_source
    assert "class SqlAlchemyKnowledgeGraphPersistence" in persistence_source
    assert "select(" in persistence_source
    assert "func.count" in persistence_source


def test_intelligence_knowledge_graph_evidence_search_builder_owns_response_assembly() -> None:
    service_source = (
        REPO_ROOT / "backend/app/services/knowledge_graph_service.py"
    ).read_text()
    application_source = (
        REPO_ROOT
        / "backend/app/domains/intelligence/capabilities/knowledge_graph/application/knowledge_graph.py"
    ).read_text()

    assert "SqlAlchemyKnowledgeGraphAdapter" in service_source
    assert "KnowledgeGraphEvidenceSearchQuery" in service_source
    assert "LegacyKnowledgeGraphEvidenceSearchDataSource" not in service_source
    assert "KnowledgeGraphEvidenceSearchResult" not in service_source
    assert "class KnowledgeGraphEvidenceSearchBuilder" in application_source
    assert "KnowledgeGraphEvidenceSearchResult" in application_source


def test_intelligence_knowledge_graph_evidence_pack_builder_owns_response_assembly() -> None:
    service_source = (
        REPO_ROOT / "backend/app/services/knowledge_graph_service.py"
    ).read_text()
    application_source = (
        REPO_ROOT
        / "backend/app/domains/intelligence/capabilities/knowledge_graph/application/knowledge_graph.py"
    ).read_text()

    assert "SqlAlchemyKnowledgeGraphAdapter" in service_source
    assert "KnowledgeGraphEvidencePackQuery" in service_source
    assert "LegacyKnowledgeGraphEvidencePackDataSource" not in service_source
    assert "_deduplicate_evidence_refs" not in service_source
    assert "class KnowledgeGraphEvidencePackBuilder" in application_source
    assert "_deduplicate_evidence_refs" in application_source


def test_knowledge_graph_is_owned_by_intelligence_not_the_developer_control_plane() -> None:
    assert DOMAIN_OWNERSHIP["knowledge_graph"] == "intelligence"
    assert resolve_domain_for_capability("knowledge_graph") == DOMAIN_BOUNDARIES["intelligence"]
    assert "knowledge graph" in DOMAIN_BOUNDARIES["intelligence"].owns


def test_developer_master_board_does_not_mount_product_knowledge_graph_ui() -> None:
    control_plane_page = (
        REPO_ROOT / "frontend/src/features/dev-control-plane/ui/ControlPlanePage.tsx"
    )
    source = control_plane_page.read_text()

    assert "KnowledgeGraphExplorerTab" not in source
    assert 'value="knowledge-graph"' not in source
    assert "Knowledge Graph" not in source

    rejected_files = [
        "frontend/src/features/dev-control-plane/api/knowledgeGraphExplorer.ts",
        "frontend/src/features/dev-control-plane/api/knowledgeGraphExplorer.test.ts",
        "frontend/src/features/dev-control-plane/ui/knowledge-graph/KnowledgeGraphExplorerTab.tsx",
        "frontend/src/features/dev-control-plane/ui/knowledge-graph/KnowledgeGraphExplorerTab.test.tsx",
    ]
    for relative_path in rejected_files:
        assert not (REPO_ROOT / relative_path).exists()


def test_capability_api_access_guards_delegate_to_platform_guard() -> None:
    access_guard_paths = sorted(
        (REPO_ROOT / "backend/app/domains").glob("*/capabilities/*/adapters/api/access.py")
    )

    assert access_guard_paths
    for access_guard_path in access_guard_paths:
        source = access_guard_path.read_text()
        assert "from app.platform.capability_guards import" in source
        assert "require_platform_capability_api_access" in source
        assert "build_persisted_capability_access_context_if_present" not in source
        assert "from app.platform.capability_access import" not in source


def test_transitional_surfaces_are_explicitly_tracked() -> None:
    assert TRANSITIONAL_SURFACES == (
        "backend/app/modules",
        "backend/app/services",
        "backend/app/models",
        "backend/app/schemas",
        "backend/app/crud",
        "frontend/src/pages",
    )

    for relative_path in TRANSITIONAL_SURFACES:
        assert (REPO_ROOT / relative_path).exists()
