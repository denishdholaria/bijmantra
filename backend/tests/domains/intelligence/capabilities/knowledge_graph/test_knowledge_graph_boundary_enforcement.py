from pathlib import Path

from tests.utils.capability_boundary import assert_no_forbidden_imports, python_files


LEGACY_KNOWLEDGE_GRAPH_MODULES = (
    "app.api.bijmantra.data.knowledge_graph",
    "app.domains.intelligence.contracts.knowledge_graph",
    "app.schemas.knowledge_graph",
    "app.services.knowledge_graph_service",
)


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _capability_root() -> Path:
    return _backend_root() / "app/domains/intelligence/capabilities/knowledge_graph"


def test_knowledge_graph_inward_layers_do_not_import_infrastructure() -> None:
    inward_paths = (
        python_files(_capability_root() / "domain")
        + python_files(_capability_root() / "ports")
        + python_files(_capability_root() / "contracts")
        + python_files(_capability_root() / "schemas")
    )

    assert_no_forbidden_imports(
        inward_paths,
        (
            *LEGACY_KNOWLEDGE_GRAPH_MODULES,
            "app.api",
            "app.middleware",
            "app.models",
            "app.services",
            "sqlalchemy",
            "fastapi",
        ),
        repo_root=_backend_root(),
        boundary_name="KnowledgeGraph",
    )


def test_knowledge_graph_application_layer_does_not_import_legacy_or_http_surfaces() -> None:
    assert_no_forbidden_imports(
        python_files(_capability_root() / "application"),
        (
            *LEGACY_KNOWLEDGE_GRAPH_MODULES,
            "app.api",
            "app.middleware",
            "app.models",
            "app.schemas",
            "app.services",
            "fastapi",
            "sqlalchemy",
        ),
        repo_root=_backend_root(),
        boundary_name="KnowledgeGraph",
    )


def test_knowledge_graph_persistence_uses_research_asset_port_not_fair_metadata_model() -> None:
    source = (
        _capability_root() / "adapters/knowledge_graph_persistence.py"
    ).read_text()

    assert "app.models.fair_metadata" not in source
    assert "FairAssetMetadataRepository" in source
    assert "FairAssetMetadataRecord" in source


def test_knowledge_graph_legacy_service_does_not_import_edge_orm_model() -> None:
    source = (_backend_root() / "app/services/knowledge_graph_service.py").read_text()

    assert "from app.models.knowledge_graph import AgriculturalKnowledgeGraphEdge" not in source
    assert "KnowledgeGraphEdgeRecord" in source


def test_knowledge_graph_port_records_are_plain_application_records() -> None:
    records_path = _capability_root() / "ports/records.py"

    assert_no_forbidden_imports(
        [records_path],
        (
            "app.api",
            "app.middleware",
            "app.models",
            "app.schemas",
            "app.services",
            "fastapi",
            "pydantic",
            "sqlalchemy",
        ),
        repo_root=_backend_root(),
        boundary_name="KnowledgeGraph",
    )


def test_knowledge_graph_direct_edge_ports_use_records_not_response_dtos() -> None:
    source = (_capability_root() / "ports/knowledge_graph.py").read_text()

    assert "KnowledgeGraphEdgeRecord" in source
    assert "KnowledgeGraphNeighborhoodRecord" in source
    assert "KnowledgeGraphEdgeResponse" not in source
    assert "KnowledgeGraphNeighborhoodResponse" not in source


def test_knowledge_graph_sqlalchemy_adapter_lists_edges_without_legacy_service() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "SqlAlchemyKnowledgeGraphPersistence" in source
    assert "self._service.list_edges" not in source


def test_knowledge_graph_sqlalchemy_adapter_gets_neighborhood_without_legacy_service() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "SqlAlchemyKnowledgeGraphPersistence" in source
    assert "list_neighborhood_edges" in source
    assert "self._service.get_neighborhood" not in source


def test_knowledge_graph_sqlalchemy_adapter_upserts_edges_without_legacy_service() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "deterministic_edge_id" in source
    assert "persistence.upsert_edge" in source
    assert "self._service.upsert_edge" not in source


def test_knowledge_graph_sqlalchemy_adapter_gets_facets_without_legacy_service() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "count_by_edge_column" in source
    assert "count_asset_type_pairs" in source
    assert "self._service.get_facets" not in source


def test_knowledge_graph_sqlalchemy_adapter_searches_evidence_without_legacy_service() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "KnowledgeGraphEvidenceSearchBuilder" in source
    assert "KnowledgeGraphFairAssetRecord" in source
    assert "self._service.search_evidence" not in source


def test_knowledge_graph_sqlalchemy_adapter_builds_evidence_pack_without_legacy_service() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "KnowledgeGraphEvidencePackBuilder" in source
    assert "KnowledgeGraphNeighborhoodRecord" in source
    assert "self._service.build_evidence_pack" not in source


def test_knowledge_graph_sqlalchemy_adapter_builds_retrieval_candidates_without_legacy_service() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "KnowledgeGraphRetrievalCandidatesBuilder" in source
    assert "def normalize_direction" in source
    assert "self._service.build_retrieval_candidates" not in source


def test_knowledge_graph_sqlalchemy_adapter_ranks_candidates_without_legacy_service() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "KnowledgeGraphRankedCandidatesBuilder" in source
    assert "self._service.rank_retrieval_candidates" not in source


def test_knowledge_graph_sqlalchemy_adapter_builds_diagnostics_without_legacy_service() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "KnowledgeGraphRetrievalDiagnosticsBuilder" in source
    assert "self._service.build_retrieval_diagnostics" not in source


def test_knowledge_graph_sqlalchemy_adapter_builds_preview_and_snapshot_without_legacy_service() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "KnowledgeGraphReevuDryRunPreviewBuilder" in source
    assert "KnowledgeGraphExplorerSnapshotBuilder" in source
    assert "app.services.knowledge_graph_service" not in source
    assert "self._service" not in source


def test_knowledge_graph_adapter_uses_domain_vocabulary_policy() -> None:
    source = (_capability_root() / "adapters/knowledge_graph.py").read_text()

    assert "knowledge_graph_vocabulary" in source
    assert "def _require_supported_relationship_type" not in source
    assert "def _require_supported_direction" not in source
    assert "def _require_supported_result_side" not in source


def test_knowledge_graph_legacy_service_is_capability_adapter_facade() -> None:
    source = (_backend_root() / "app/services/knowledge_graph_service.py").read_text()

    assert "SqlAlchemyKnowledgeGraphAdapter" in source
    assert "knowledge_graph_vocabulary" in source
    assert "LegacyKnowledgeGraph" not in source
    assert "KnowledgeGraphRankedCandidatesBuilder" not in source
    assert "KnowledgeGraphRetrievalDiagnosticsBuilder" not in source
    assert "def _candidate_score_factors" not in source
    assert "def _candidate_diagnostic_warnings" not in source


def test_knowledge_graph_edge_identity_is_pure_domain_logic() -> None:
    source = (_capability_root() / "domain/knowledge_graph_edges.py").read_text()

    assert "def deterministic_edge_id" in source
    assert "app.models" not in source
    assert "sqlalchemy" not in source
    assert "fastapi" not in source
