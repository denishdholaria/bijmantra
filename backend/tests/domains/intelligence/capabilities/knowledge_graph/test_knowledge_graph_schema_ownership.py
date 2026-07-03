import subprocess
import sys
from pathlib import Path

from app.domains.intelligence.capabilities.knowledge_graph.schemas import (
    knowledge_graph as capability_schemas,
)
from app.schemas import knowledge_graph as legacy_schemas


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[5]


def test_global_knowledge_graph_schema_module_is_compatibility_shim() -> None:
    assert legacy_schemas.KnowledgeGraphEdgeCreate is capability_schemas.KnowledgeGraphEdgeCreate
    assert (
        legacy_schemas.KnowledgeGraphRankedCandidate
        is capability_schemas.KnowledgeGraphRankedCandidate
    )
    assert (
        legacy_schemas.KnowledgeGraphRetrievalDiagnosticCandidate
        is capability_schemas.KnowledgeGraphRetrievalDiagnosticCandidate
    )


def test_global_knowledge_graph_schema_file_does_not_own_contract_implementations() -> None:
    backend_root = _backend_root()
    shim_path = backend_root / "app/schemas/knowledge_graph.py"
    source = shim_path.read_text()
    forbidden_fragments = [
        "class ",
        "BaseModel",
        "ConfigDict",
        "Field(",
        "from pydantic",
        "from datetime",
    ]

    assert "capabilities.knowledge_graph.schemas.knowledge_graph" in source
    for fragment in forbidden_fragments:
        assert fragment not in source, (
            f"{shim_path.relative_to(backend_root)} should re-export Knowledge Graph "
            f"contracts instead of owning implementation fragment {fragment!r}"
        )


def test_knowledge_graph_runtime_code_imports_capability_owned_contracts() -> None:
    backend_root = _backend_root()
    capability_paths = [
        backend_root
        / "app/domains/intelligence/capabilities/knowledge_graph/application/knowledge_graph.py",
        backend_root
        / "app/domains/intelligence/capabilities/knowledge_graph/adapters/api/knowledge_graph.py",
        backend_root
        / "app/domains/intelligence/capabilities/knowledge_graph/adapters/knowledge_graph.py",
        backend_root
        / "app/domains/intelligence/capabilities/knowledge_graph/adapters/knowledge_graph_persistence.py",
        backend_root / "app/services/knowledge_graph_service.py",
    ]

    for capability_path in capability_paths:
        source = capability_path.read_text()
        assert "capabilities.knowledge_graph.schemas.knowledge_graph" in source
        assert "app.schemas.knowledge_graph" not in source, (
            f"{capability_path.relative_to(backend_root)} should import Knowledge Graph "
            "contracts from the capability schema owner"
        )


def test_legacy_knowledge_graph_service_imports_without_adapter_cycle() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import app.services.knowledge_graph_service"],
        cwd=_backend_root(),
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
