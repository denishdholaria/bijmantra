"""
Phenotype evidence envelope builder.

Extracted from app.api.bijmantra.phenotyping.phenotype_comparison so that
the AI tools layer (app.modules.ai.services.tools) can import it without
creating a service → API layer dependency.

This module contains only pure functions — no HTTP, no DB, no FastAPI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.modules.ai.services.reevu_provenance_validator import validate_all as validate_provenance
from app.schemas.reevu_envelope import CalculationStep, EvidenceRef, ReevuEnvelope, UncertaintyInfo


def _parse_observation_timestamp(ts: str | None) -> datetime | None:
    """Parse an ISO-8601 observation timestamp to a timezone-aware datetime."""
    if not ts:
        return None
    try:
        from datetime import timezone
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def build_phenotype_evidence_refs(
    observations: list[Any],
    interpretation: Any,
) -> list[EvidenceRef]:
    """Build evidence refs from observations and interpretation."""
    freshness_by_ref: dict[str, float | None] = {}
    observation_ref_ids: set[str] = set()

    for observation in observations:
        obs_id = getattr(observation, "id", None)
        obs_db_id = getattr(observation, "observation_db_id", None)
        observation_ref = obs_db_id or f"db:observation:{obs_id}"
        observation_ref_ids.add(observation_ref)
        ts = getattr(observation, "observation_time_stamp", None)
        observed_at = _parse_observation_timestamp(ts)
        freshness = None
        if observed_at is not None:
            freshness = max((datetime.now(UTC) - observed_at).total_seconds(), 0.0)
        freshness_by_ref[observation_ref] = freshness

    ranking_refs = [
        ref
        for item in (getattr(interpretation, "ranking", []) or [])
        for ref in getattr(item, "evidence_refs", [])
    ]
    all_refs = sorted(
        {*(getattr(interpretation, "evidence_refs", []) or []), *ranking_refs}
    )
    return [
        EvidenceRef(
            source_type=(
                "database"
                if str(ref).startswith("db:") or str(ref) in observation_ref_ids
                else "function"
            ),
            entity_id=str(ref),
            query_or_method="phenotype_comparison.query",
            freshness_seconds=freshness_by_ref.get(str(ref)),
        )
        for ref in all_refs
    ]


def build_phenotype_calculation_steps(interpretation: Any) -> list[CalculationStep]:
    """Build calculation steps from interpretation."""
    return [
        CalculationStep(step_id=str(calc_id))
        for calc_id in (getattr(interpretation, "calculation_ids", []) or [])
    ]


def derive_interpretation_counts(interpretation: Any) -> tuple[int, int, int]:
    """Return (entity_count, trait_count, observation_count) from an interpretation."""
    summary = getattr(interpretation, "summary", None)
    entity_count = getattr(summary, "entity_count", None)
    trait_count = getattr(summary, "trait_count", None)
    observation_count = getattr(summary, "observation_count", None)

    entities = getattr(interpretation, "entities", []) or []
    if entity_count in (None, 0) and entities:
        entity_count = len(entities)

    if trait_count in (None, 0):
        trait_keys = {
            getattr(metric, "trait_key", None)
            for entity in entities
            for metric in getattr(entity, "metrics", []) or []
            if getattr(metric, "trait_key", None)
        }
        ranking = getattr(interpretation, "ranking", []) or []
        trait_keys.update(
            getattr(item, "score_trait_key", None)
            for item in ranking
            if getattr(item, "score_trait_key", None)
        )
        trait_count = len(trait_keys)

    if observation_count in (None, 0):
        observation_count = sum(
            getattr(metric, "observation_count", 0)
            for entity in entities
            for metric in getattr(entity, "metrics", []) or []
        )

    return entity_count or 0, trait_count or 0, observation_count or 0


def build_phenotype_evidence_envelope(
    *,
    scope: str,
    observations: list[Any],
    interpretation: Any,
) -> ReevuEnvelope:
    """
    Build a REEVU evidence envelope for a phenotype comparison result.

    This is the canonical implementation.  The API router
    (app.api.bijmantra.phenotyping.phenotype_comparison) delegates to this
    function; the AI tools layer imports it directly from here.
    """
    entity_count, trait_count, observation_count = derive_interpretation_counts(interpretation)

    confidence = 0.35
    if observation_count > 0:
        confidence += 0.25
    if trait_count > 0:
        confidence += 0.15
    if entity_count >= 2:
        confidence += 0.15
    if not (getattr(interpretation, "warnings", []) or []):
        confidence += 0.1

    missing_data: list[str] = []
    if observation_count == 0:
        missing_data.append("numeric_observations")
    if trait_count == 0:
        missing_data.append("trait_coverage")
    if entity_count < 2:
        missing_data.append("comparison_subjects")

    # Extract claims from interpretation
    claims: list[str] = []
    summary = getattr(interpretation, "summary", None)
    if summary:
        summary_text = getattr(summary, "summary_text", None)
        if summary_text:
            claims.append(str(summary_text))

    ranking = getattr(interpretation, "ranking", []) or []
    if ranking:
        leader = ranking[0]
        leader_name = getattr(leader, "entity_name", None) or getattr(leader, "entity_db_id", "")
        leader_score = getattr(leader, "score", None)
        score_trait = getattr(leader, "score_trait_key", None)
        if leader_score is not None and score_trait:
            claims.append(
                f"Top-ranked entry {leader_name} leads on {score_trait} "
                f"with score {leader_score}."
            )

    methodology = getattr(interpretation, "methodology", None)
    if methodology:
        claims.append(f"Interpretation methodology: {methodology}.")

    envelope = ReevuEnvelope(
        claims=claims[:4],
        evidence_refs=build_phenotype_evidence_refs(observations, interpretation),
        calculation_steps=build_phenotype_calculation_steps(interpretation),
        uncertainty=UncertaintyInfo(
            confidence=round(min(confidence, 0.95), 2),
            missing_data=missing_data,
        ),
        policy_flags=list(getattr(interpretation, "warnings", []) or []),
    )
    provenance_flags = validate_provenance(envelope)
    if provenance_flags:
        envelope = envelope.model_copy(
            update={"policy_flags": envelope.policy_flags + provenance_flags}
        )
    return envelope
