from pathlib import Path

from tests.utils.capability_boundary import assert_no_forbidden_imports, python_files


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _capability_root() -> Path:
    return _backend_root() / "app/domains/intelligence/capabilities/knowledge_graph"


def test_knowledge_graph_inward_layers_do_not_import_infrastructure() -> None:
    inward_paths = (
        python_files(_capability_root() / "domain")
        + python_files(_capability_root() / "ports")
        + python_files(_capability_root() / "schemas")
    )

    assert_no_forbidden_imports(
        inward_paths,
        (
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
            "app.api",
            "app.middleware",
            "app.models",
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
