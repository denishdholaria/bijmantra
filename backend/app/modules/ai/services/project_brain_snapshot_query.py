"""Developer query surface for file-backed project-brain snapshots.

primary_domain = "ai_orchestration"
secondary_domains = ["knowledge_management", "developer_experience"]
assumptions = [
    "Developers need a lightweight way to inspect file-backed project-brain snapshots before any database-backed sidecar exists.",
    "Query results should preserve provenance instead of collapsing into opaque relevance output.",
    "This surface is for developer inspection and bootstrap validation, not end-user REEVU runtime use."
]
limitations = [
    "This module only queries file-backed snapshots.",
    "It does not mutate source artifacts or snapshot contents.",
    "It relies on the current bootstrap projection quality and cannot exceed that source fidelity."
]
uncertainty_handling = "The query surface is intentionally lightweight so recall usefulness can be proven before a database-backed sidecar is introduced."
"""

from __future__ import annotations

from pathlib import Path

from app.modules.ai.services.project_brain_memory import (
    ProjectBrainMemoryService,
    ProjectBrainScope,
    ProjectBrainTrustRank,
)
from app.modules.ai.services.project_brain_memory_file import FileBackedProjectBrainMemoryRepository
from app.modules.ai.services.project_brain_query import ProjectBrainQueryResult, ProjectBrainQueryService


ProjectBrainSnapshotQueryResult = ProjectBrainQueryResult


class ProjectBrainSnapshotQueryService:
    def __init__(self, snapshot_path: str | Path):
        self.snapshot_path = Path(snapshot_path)
        self.repository = FileBackedProjectBrainMemoryRepository(self.snapshot_path)
        self.memory_service = ProjectBrainMemoryService(self.repository)
        self.query_service = ProjectBrainQueryService(self.memory_service)

    async def query(
        self,
        query: str,
        *,
        include_provenance: bool = True,
        trust_ranks: tuple[ProjectBrainTrustRank, ...] | None = None,
        scopes: tuple[ProjectBrainScope, ...] | None = None,
    ) -> ProjectBrainSnapshotQueryResult:
        return await self.query_service.query(
            query,
            include_provenance=include_provenance,
            trust_ranks=trust_ranks,
            scopes=scopes,
        )
