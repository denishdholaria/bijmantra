"""Shared record codecs for project-brain memory repositories."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.modules.ai.services.project_brain_memory import (
    ProjectBrainCorrectionRecord,
    ProjectBrainMemoryEdgeRecord,
    ProjectBrainMemoryNodeRecord,
    ProjectBrainProjectionRecord,
    ProjectBrainScope,
    ProjectBrainSourceArtifactRecord,
    ProjectBrainSourceSurface,
    ProjectBrainTrustRank,
    _utc_now,
)


def parse_project_brain_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def decode_source_artifact_record(data: dict[str, Any]) -> ProjectBrainSourceArtifactRecord:
    return ProjectBrainSourceArtifactRecord(
        id=data["id"],
        source_path=data["source_path"],
        source_surface=ProjectBrainSourceSurface(data["source_surface"]),
        source_kind=data["source_kind"],
        authority_class=data["authority_class"],
        capture_timestamp=parse_project_brain_datetime(data.get("capture_timestamp")) or _utc_now(),
        version=data.get("version"),
        digest=data.get("digest"),
        metadata=data.get("metadata", {}),
    )


def decode_projection_record(data: dict[str, Any]) -> ProjectBrainProjectionRecord:
    return ProjectBrainProjectionRecord(
        id=data["id"],
        source_id=data["source_id"],
        projection_type=data["projection_type"],
        summary=data["summary"],
        trust_rank=ProjectBrainTrustRank(data["trust_rank"]),
        scope=ProjectBrainScope(data["scope"]),
        metadata=data.get("metadata", {}),
        created_at=parse_project_brain_datetime(data.get("created_at")) or _utc_now(),
        invalidated_at=parse_project_brain_datetime(data.get("invalidated_at")),
    )


def decode_memory_node_record(data: dict[str, Any]) -> ProjectBrainMemoryNodeRecord:
    return ProjectBrainMemoryNodeRecord(
        id=data["id"],
        node_type=data["node_type"],
        title=data["title"],
        trust_rank=ProjectBrainTrustRank(data["trust_rank"]),
        scope=ProjectBrainScope(data["scope"]),
        source_ids=tuple(data.get("source_ids", [])),
        metadata=data.get("metadata", {}),
        created_at=parse_project_brain_datetime(data.get("created_at")) or _utc_now(),
        invalidated_at=parse_project_brain_datetime(data.get("invalidated_at")),
    )


def decode_memory_edge_record(data: dict[str, Any]) -> ProjectBrainMemoryEdgeRecord:
    return ProjectBrainMemoryEdgeRecord(
        id=data["id"],
        from_node_id=data["from_node_id"],
        to_node_id=data["to_node_id"],
        relation_type=data["relation_type"],
        source_id=data.get("source_id"),
        confidence=data.get("confidence"),
        is_derived=data.get("is_derived", False),
        created_at=parse_project_brain_datetime(data.get("created_at")) or _utc_now(),
    )


def decode_correction_record(data: dict[str, Any]) -> ProjectBrainCorrectionRecord:
    return ProjectBrainCorrectionRecord(
        id=data["id"],
        target_kind=data["target_kind"],
        target_id=data["target_id"],
        reason=data["reason"],
        recorded_at=parse_project_brain_datetime(data.get("recorded_at")) or _utc_now(),
    )
