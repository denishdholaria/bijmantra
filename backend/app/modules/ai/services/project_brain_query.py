"""Repository-agnostic project-brain query surface.

primary_domain = "ai_orchestration"
secondary_domains = ["knowledge_management", "developer_experience"]
assumptions = [
    "Developers need one readable query surface regardless of whether project-brain memory is file-backed, volatile, or persisted in a sidecar.",
    "Query results should preserve provenance instead of collapsing recall into opaque ranking output.",
    "The project-brain query surface is for developer and operator inspection, not direct end-user REEVU use."
]
limitations = [
    "This surface is only as useful as the stored source metadata, projections, and nodes it searches.",
    "It does not mutate memory state or create new projections.",
    "Ranking remains lightweight and metadata-driven rather than semantic-vector based."
]
uncertainty_handling = "A unified query surface lets the team prove whether the sidecar feels like a useful project brain before deeper graph or retrieval complexity is added."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.modules.ai.services.project_brain_memory import (
    ProjectBrainMemoryService,
    ProjectBrainProvenanceTrail,
    ProjectBrainRecallView,
    ProjectBrainScope,
    ProjectBrainTrustRank,
)


@dataclass(frozen=True, slots=True)
class ProjectBrainQueryResult:
    query: str
    recall_view: ProjectBrainRecallView
    provenance_trails: tuple[ProjectBrainProvenanceTrail, ...] = tuple()

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "recall_view": self.recall_view.to_dict(),
            "provenance_trails": [item.to_dict() for item in self.provenance_trails],
        }


class ProjectBrainQueryService:
    def __init__(self, memory_service: ProjectBrainMemoryService):
        self.memory_service = memory_service

    async def query(
        self,
        query: str,
        *,
        include_provenance: bool = True,
        trust_ranks: tuple[ProjectBrainTrustRank, ...] | None = None,
        scopes: tuple[ProjectBrainScope, ...] | None = None,
    ) -> ProjectBrainQueryResult:
        recall_view = await self.memory_service.recall(
            query,
            trust_ranks=trust_ranks,
            scopes=scopes,
        )
        provenance_trails: list[ProjectBrainProvenanceTrail] = []
        if include_provenance:
            for node in recall_view.nodes:
                provenance_trails.append(await self.memory_service.get_provenance_trail(node.id))
        return ProjectBrainQueryResult(
            query=query,
            recall_view=recall_view,
            provenance_trails=tuple(provenance_trails),
        )


def render_project_brain_query_result(result: ProjectBrainQueryResult) -> str:
    payload = result.to_dict()
    lines = [
        f"Query: {payload['query']}",
        f"Source matches: {len(payload['recall_view']['source_artifacts'])}",
        f"Projection matches: {len(payload['recall_view']['projections'])}",
        f"Node matches: {len(payload['recall_view']['nodes'])}",
    ]
    for artifact in payload["recall_view"]["source_artifacts"][:5]:
        title = artifact.get("metadata", {}).get("title") or artifact["source_path"]
        lines.append(f"- source: {title} -> {artifact['source_path']}")
    for node in payload["recall_view"]["nodes"][:5]:
        lines.append(f"- node: {node['title']} ({node['trust_rank']}, {node['scope']})")
    if payload["provenance_trails"]:
        lines.append(f"Provenance trails: {len(payload['provenance_trails'])}")
        for trail in payload["provenance_trails"][:3]:
            node = trail["node"]["title"]
            sources = ", ".join(item["source_path"] for item in trail["source_artifacts"][:3])
            lines.append(f"- provenance: {node} <- {sources}")
    return "\n".join(lines)
