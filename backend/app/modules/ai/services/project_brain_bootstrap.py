"""Bootstrap ingestion for the project-brain first-wave source inventory.

primary_domain = "ai_orchestration"
secondary_domains = ["knowledge_management", "governance", "developer_experience"]
assumptions = [
    "Bootstrap ingestion should follow the first-wave source inventory before any broad repo ingestion is attempted.",
    "Source files remain authoritative; ingestion records projections and graph-friendly nodes only.",
    "The first proving slice should use stable ids so repeated bootstrap runs refresh records instead of multiplying them."
]
limitations = [
    "This module only covers the current first-wave source set.",
    "Markdown and JSON summarization are intentionally heuristic and conservative.",
    "No automatic write-back into source artifacts is supported."
]
uncertainty_handling = "The first-wave inventory is intentionally narrow; broader ingestion should wait until projection quality and recall usefulness are proven."
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.modules.ai.services.project_brain_memory import (
    ProjectBrainMemoryService,
    ProjectBrainScope,
    ProjectBrainSourceSurface,
    ProjectBrainTrustRank,
)


@dataclass(frozen=True, slots=True)
class ProjectBrainBootstrapSourceSpec:
    relative_path: str
    source_surface: ProjectBrainSourceSurface
    source_kind: str
    authority_class: str
    trust_rank: ProjectBrainTrustRank
    scope: ProjectBrainScope
    wave: str


@dataclass(frozen=True, slots=True)
class ProjectBrainBootstrapIngestionReport:
    source_count: int
    projection_count: int
    node_count: int
    missing_paths: tuple[str, ...] = tuple()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_count": self.source_count,
            "projection_count": self.projection_count,
            "node_count": self.node_count,
            "missing_paths": list(self.missing_paths),
        }


@dataclass(frozen=True, slots=True)
class ProjectBrainMarkdownExtractionProfile:
    preferred_headings: tuple[str, ...]
    keywords: tuple[str, ...]


_DEFAULT_MARKDOWN_PROFILE = ProjectBrainMarkdownExtractionProfile(
    preferred_headings=("Purpose", "Objective", "Problem", "Decision", "Core Rule"),
    keywords=("project_brain_source",),
)

_MARKDOWN_EXTRACTION_PROFILES: dict[str, ProjectBrainMarkdownExtractionProfile] = {
    "charter": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Purpose", "Current Operating Decision", "Relationship to REEVU"),
        keywords=("being_surface", "surface_governance", "reevu_boundary"),
    ),
    "glossary": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Purpose",),
        keywords=("shared_vocabulary", "concept_index"),
    ),
    "mission_constitution": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Mission", "Constitutional Laws", "Governance Implications"),
        keywords=("constitutional_memory", "mission_law", "authority_boundary"),
    ),
    "memory_model": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Core Principle", "Memory Classes", "Trust Ranking of Memory"),
        keywords=("governed_memory", "memory_classes", "trust_ranking"),
    ),
    "project_brain_roadmap": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Where SurrealDB Fits", "Recommended Brain Stack", "Core Interpretation"),
        keywords=("project_brain", "surrealdb_sidecar", "authority_boundary"),
    ),
    "surrealdb_sidecar_direction": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Core Decision", "Relationship To Existing SurrealDB Direction", "Physical Deployment Rule"),
        keywords=("beingbijmantra_surrealdb", "surrealdb_sidecar", "database_boundary"),
    ),
    "project_brain_memory_contract": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Core Rule", "Contract Objects", "Trust Ranks", "Storage-Neutral Adapter Boundary"),
        keywords=("project_brain_contract", "projection_rules", "storage_neutral_adapter"),
    ),
    "translation_map": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Core Rule", "Translation Destinations", "Current Translation Priorities"),
        keywords=("translation_contract", "meaning_to_runtime", "single_authority_owner"),
    ),
    "reevu_governed_memory_embodiment": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Core Diagnosis", "Governing Principle", "Operator-Legible Behavior"),
        keywords=("reevu_memory_boundary", "operator_legibility", "governed_memory"),
    ),
    "project_brain_proposal": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Problem", "Proposed Solution", "Implementation Steps"),
        keywords=("project_brain_architecture", "surrealdb_candidate", "sidecar_memory"),
    ),
    "planning_task": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Objective", "Workstreams", "Notes"),
        keywords=("planning_sequence", "bootstrap_path", "execution_slice"),
    ),
    "bootstrap_task": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Objective", "Acceptance Criteria", "Notes"),
        keywords=("bootstrap_contract", "storage_neutral", "proof_before_runtime"),
    ),
    "accepted_decision": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Decision", "Rationale", "Implementation"),
        keywords=("accepted_decision", "authority_boundary", "runtime_direction"),
    ),
    "instruction": ProjectBrainMarkdownExtractionProfile(
        preferred_headings=("Being Bijmantra Document Guidelines", "AI Control Surface Guidelines", "REEVU Trusted-Surface Lock"),
        keywords=("active_control_document", "procedural_memory", "repo_rule"),
    ),
}


FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS: tuple[ProjectBrainBootstrapSourceSpec, ...] = (
    ProjectBrainBootstrapSourceSpec(
        relative_path=".beingbijmantra/2026-04-03-being-bijmantra-surface-charter.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="charter",
        authority_class="constitutional",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        wave="1A",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".beingbijmantra/2026-04-03-being-bijmantra-glossary.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="glossary",
        authority_class="constitutional",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        wave="1A",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".beingbijmantra/2026-04-03-being-bijmantra-mission-constitution.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="mission_constitution",
        authority_class="constitutional",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        wave="1A",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".beingbijmantra/2026-04-03-being-bijmantra-memory-model.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="memory_model",
        authority_class="constitutional",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        wave="1A",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".beingbijmantra/2026-04-04-being-bijmantra-project-brain-roadmap.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="project_brain_roadmap",
        authority_class="constitutional",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        wave="1A",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".beingbijmantra/2026-04-04-being-bijmantra-surrealdb-sidecar-direction.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="surrealdb_sidecar_direction",
        authority_class="constitutional",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        wave="1A",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".beingbijmantra/2026-04-04-being-bijmantra-project-brain-memory-contract.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="project_brain_memory_contract",
        authority_class="constitutional",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        wave="1A",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".beingbijmantra/2026-04-04-being-bijmantra-translation-map.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="translation_map",
        authority_class="constitutional",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        wave="1A",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".beingbijmantra/2026-04-04-reevu-governed-memory-embodiment.md",
        source_surface=ProjectBrainSourceSurface.BEING,
        source_kind="reevu_governed_memory_embodiment",
        authority_class="constitutional",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.GLOBAL_PROJECT,
        wave="1A",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".ai/proposals/2026-04-04-being-bijmantra-project-brain-architecture.md",
        source_surface=ProjectBrainSourceSurface.AI,
        source_kind="project_brain_proposal",
        authority_class="operational",
        trust_rank=ProjectBrainTrustRank.RANK_B,
        scope=ProjectBrainScope.WORKSTREAM,
        wave="1B",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".ai/proposals/2026-04-04-being-bijmantra-surrealdb-sidecar-bootstrap.md",
        source_surface=ProjectBrainSourceSurface.AI,
        source_kind="project_brain_proposal",
        authority_class="operational",
        trust_rank=ProjectBrainTrustRank.RANK_B,
        scope=ProjectBrainScope.WORKSTREAM,
        wave="1B",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".ai/tasks/2026-04-04-project-brain-contract-inventory-and-adapter-plan.md",
        source_surface=ProjectBrainSourceSurface.AI,
        source_kind="planning_task",
        authority_class="operational",
        trust_rank=ProjectBrainTrustRank.RANK_B,
        scope=ProjectBrainScope.WORKSTREAM,
        wave="1B",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".ai/decisions/ADR-010-surrealdb-orchestration-memory-candidate.md",
        source_surface=ProjectBrainSourceSurface.AI,
        source_kind="accepted_decision",
        authority_class="accepted_adr",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.WORKSTREAM,
        wave="1B",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".ai/decisions/ADR-012-orchestrator-authority-and-state-bootstrap.md",
        source_surface=ProjectBrainSourceSurface.AI,
        source_kind="accepted_decision",
        authority_class="accepted_adr",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.WORKSTREAM,
        wave="1B",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".ai/tasks/2026-03-15-orchestrator-mission-state-bootstrap.md",
        source_surface=ProjectBrainSourceSurface.AI,
        source_kind="bootstrap_task",
        authority_class="operational",
        trust_rank=ProjectBrainTrustRank.RANK_B,
        scope=ProjectBrainScope.WORKSTREAM,
        wave="1B",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".github/instructions/ai-control-surfaces.instructions.md",
        source_surface=ProjectBrainSourceSurface.GITHUB,
        source_kind="instruction",
        authority_class="active_control_document",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.SURFACE,
        wave="1C",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".github/instructions/being-bijmantra-docs.instructions.md",
        source_surface=ProjectBrainSourceSurface.GITHUB,
        source_kind="instruction",
        authority_class="active_control_document",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.SURFACE,
        wave="1C",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path=".github/instructions/reevu-trusted-surfaces.instructions.md",
        source_surface=ProjectBrainSourceSurface.GITHUB,
        source_kind="instruction",
        authority_class="active_control_document",
        trust_rank=ProjectBrainTrustRank.RANK_A,
        scope=ProjectBrainScope.SURFACE,
        wave="1C",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path="backend/test_reports/reevu_local_readiness_census.json",
        source_surface=ProjectBrainSourceSurface.RUNTIME_EVIDENCE,
        source_kind="runtime_evidence",
        authority_class="verified_runtime_evidence",
        trust_rank=ProjectBrainTrustRank.RANK_B,
        scope=ProjectBrainScope.SURFACE,
        wave="1D",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path="backend/test_reports/reevu_authority_gap_report.json",
        source_surface=ProjectBrainSourceSurface.RUNTIME_EVIDENCE,
        source_kind="runtime_evidence",
        authority_class="verified_runtime_evidence",
        trust_rank=ProjectBrainTrustRank.RANK_B,
        scope=ProjectBrainScope.SURFACE,
        wave="1D",
    ),
    ProjectBrainBootstrapSourceSpec(
        relative_path="backend/test_reports/reevu_ops_report.json",
        source_surface=ProjectBrainSourceSurface.RUNTIME_EVIDENCE,
        source_kind="runtime_evidence",
        authority_class="verified_runtime_evidence",
        trust_rank=ProjectBrainTrustRank.RANK_B,
        scope=ProjectBrainScope.SURFACE,
        wave="1D",
    ),
)


def _stable_id(prefix: str, key: str) -> str:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _sha256_digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _trim_text(value: str, limit: int = 240) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[: limit - 3].rstrip()}..."


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _normalize_heading(value: str) -> str:
    return " ".join(value.lower().split())


def _markdown_body_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return lines[index + 1 :]
    return lines


def _parse_markdown_sections(text: str, fallback_title: str) -> tuple[str, list[tuple[str, str]]]:
    lines = _markdown_body_lines(text)
    metadata_prefixes = ("Created:", "Last Updated:", "Status:", "Scope:")
    title = fallback_title
    sections: list[tuple[str, str]] = []
    current_heading = "Lead"
    current_lines: list[str] = []

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            if current_lines and current_lines[-1] != "":
                current_lines.append("")
            continue
        if stripped.startswith("# "):
            if title == fallback_title:
                title = stripped[2:].strip() or fallback_title
                continue
        if stripped.startswith("#"):
            content = _trim_text(" ".join(item for item in current_lines if item))
            if content:
                sections.append((current_heading, content))
            current_heading = stripped.lstrip("#").strip() or current_heading
            current_lines = []
            continue
        if any(stripped.startswith(prefix) for prefix in metadata_prefixes):
            continue
        current_lines.append(stripped)

    content = _trim_text(" ".join(item for item in current_lines if item))
    if content:
        sections.append((current_heading, content))
    return title, sections


def _select_focus_section(
    sections: list[tuple[str, str]],
    preferred_headings: tuple[str, ...],
) -> tuple[str | None, str]:
    normalized_preferences = tuple(_normalize_heading(item) for item in preferred_headings)
    for preferred in normalized_preferences:
        for heading, content in sections:
            normalized_heading = _normalize_heading(heading)
            if normalized_heading == preferred or preferred in normalized_heading:
                return heading, content
    for heading, content in sections:
        if heading != "Lead" and content:
            return heading, content
    if sections:
        return sections[0]
    return None, ""


def _extract_markdown_descriptor(
    text: str,
    fallback_title: str,
    source_kind: str,
) -> dict[str, Any]:
    profile = _MARKDOWN_EXTRACTION_PROFILES.get(source_kind, _DEFAULT_MARKDOWN_PROFILE)
    title, sections = _parse_markdown_sections(text, fallback_title)
    focus_heading, focus_excerpt = _select_focus_section(sections, profile.preferred_headings)
    headings = [heading for heading, _ in sections if heading != "Lead"]
    keyword_values = list(profile.keywords)
    keyword_values.extend(_slugify(heading) for heading in headings[:6])
    keywords = [keyword for index, keyword in enumerate(keyword_values) if keyword and keyword not in keyword_values[:index]]
    summary_base = focus_excerpt or title
    summary = title if not summary_base or summary_base == title else f"{title}: {summary_base}"
    return {
        "title": title,
        "summary": _trim_text(summary, limit=300),
        "metadata": {
            "title": title,
            "headings": headings,
            "focus_heading": focus_heading,
            "focus_excerpt": _trim_text(focus_excerpt, limit=260),
            "keywords": keywords,
        },
    }


def _extract_json_descriptor(
    payload: dict[str, Any],
    fallback_title: str,
    relative_path: str,
) -> dict[str, Any]:
    title = fallback_title
    metadata: dict[str, Any] = {"title": title, "top_level_keys": sorted(payload.keys())[:10]}
    if "overall_floor_met" in payload:
        summary = (
            f"Operational report generated at {payload.get('generated_at', 'unknown')} with "
            f"overall_floor_met={payload.get('overall_floor_met')} and stages={payload.get('stages_evaluated', [])}"
        )
        metadata["keywords"] = ["ops_kpis", "runtime_evidence", "floor_status"]
        metadata["overall_floor_met"] = payload.get("overall_floor_met")
        return {"title": title, "summary": _trim_text(summary), "metadata": metadata}
    if "overall_gap_status" in payload:
        summary = (
            f"Authority gap report generated at {payload.get('generated_at', 'unknown')} with "
            f"overall_gap_status={payload.get('overall_gap_status')} and selected_local_organization_id={payload.get('selected_local_organization_id')}"
        )
        metadata["keywords"] = ["trusted_surface_gap", "selected_org_blocker", "runtime_evidence"]
        metadata["overall_gap_status"] = payload.get("overall_gap_status")
        return {"title": title, "summary": _trim_text(summary), "metadata": metadata}
    if "benchmark_ready_organization_ids" in payload:
        summary = (
            f"Readiness census generated at {payload.get('generated_at', 'unknown')} with "
            f"benchmark_ready_organization_ids={payload.get('benchmark_ready_organization_ids', [])} and blocked_organization_ids={payload.get('blocked_organization_ids', [])}"
        )
        metadata["keywords"] = ["tenant_readiness", "canonical_local_lane", "runtime_evidence"]
        metadata["benchmark_ready_organization_ids"] = payload.get("benchmark_ready_organization_ids", [])
        return {"title": title, "summary": _trim_text(summary), "metadata": metadata}
    top_level_keys = sorted(payload.keys())
    summary = f"JSON source {relative_path} with top-level keys: {', '.join(top_level_keys[:6])}"
    metadata["keywords"] = ["json_source", "runtime_evidence"]
    return {"title": title, "summary": _trim_text(summary), "metadata": metadata}


def _extract_source_descriptor(repo_root: Path, spec: ProjectBrainBootstrapSourceSpec) -> dict[str, Any]:
    full_path = repo_root / spec.relative_path
    raw_bytes = full_path.read_bytes()
    digest = _sha256_digest(raw_bytes)
    metadata = {
        "wave": spec.wave,
        "relative_path": spec.relative_path,
        "size_bytes": len(raw_bytes),
        "suffix": full_path.suffix,
    }
    fallback_title = full_path.stem.replace("-", " ").replace("_", " ").strip().title()

    if full_path.suffix.lower() == ".json":
        payload = json.loads(raw_bytes.decode("utf-8"))
        descriptor = _extract_json_descriptor(payload, fallback_title, spec.relative_path)
    else:
        text = raw_bytes.decode("utf-8")
        descriptor = _extract_markdown_descriptor(text, fallback_title, spec.source_kind)
    metadata.update(descriptor["metadata"])
    return {
        "digest": digest,
        "title": descriptor["title"],
        "summary": descriptor["summary"],
        "metadata": metadata,
    }


class ProjectBrainBootstrapIngestionService:
    def __init__(self, memory_service: ProjectBrainMemoryService):
        self.memory_service = memory_service

    async def bootstrap_first_wave(self, repo_root: Path) -> ProjectBrainBootstrapIngestionReport:
        missing_paths = [
            spec.relative_path
            for spec in FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS
            if not (repo_root / spec.relative_path).exists()
        ]
        if missing_paths:
            return ProjectBrainBootstrapIngestionReport(
                source_count=0,
                projection_count=0,
                node_count=0,
                missing_paths=tuple(missing_paths),
            )

        source_count = 0
        projection_count = 0
        node_count = 0
        for spec in FIRST_WAVE_PROJECT_BRAIN_SOURCE_SPECS:
            descriptor = _extract_source_descriptor(repo_root, spec)
            source_id = _stable_id("source", spec.relative_path)
            projection_id = _stable_id("projection", spec.relative_path)
            node_id = _stable_id("node", spec.relative_path)

            artifact = await self.memory_service.register_source_artifact(
                source_path=spec.relative_path,
                source_surface=spec.source_surface,
                source_kind=spec.source_kind,
                authority_class=spec.authority_class,
                digest=descriptor["digest"],
                metadata=descriptor["metadata"],
                source_artifact_id=source_id,
            )
            await self.memory_service.project_from_source(
                source_id=artifact.id,
                projection_type="bootstrap_summary",
                summary=descriptor["summary"],
                trust_rank=spec.trust_rank,
                scope=spec.scope,
                metadata={"wave": spec.wave, **descriptor["metadata"]},
                projection_id=projection_id,
            )
            await self.memory_service.upsert_memory_node(
                node_type="source_document",
                title=descriptor["title"],
                trust_rank=spec.trust_rank,
                scope=spec.scope,
                source_ids=(artifact.id,),
                metadata={"wave": spec.wave, **descriptor["metadata"]},
                node_id=node_id,
            )
            source_count += 1
            projection_count += 1
            node_count += 1

        return ProjectBrainBootstrapIngestionReport(
            source_count=source_count,
            projection_count=projection_count,
            node_count=node_count,
        )
