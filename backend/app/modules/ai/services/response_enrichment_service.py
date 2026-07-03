"""
REEVU Response Enrichment Service — Phase 1

Post-execution enrichment for search_trials and search_germplasm results.
Enriches each item with cross-domain context from related tables, builds
deterministic markdown summaries, and attaches evidence envelopes tracing
every data point to its source query.

Integration point: called in chat.py between function_executor.execute()
and _extract_function_response_message().
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, ClassVar

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Study
from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable
from app.schemas.reevu_envelope import EvidenceRef, ReevuEnvelope, UncertaintyInfo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Trial batch query helpers
# ---------------------------------------------------------------------------


async def _query_trial_observation_counts(
    db: AsyncSession,
    organization_id: int,
    trial_ids: list[int],
) -> tuple[dict[int, int], EvidenceRef | None]:
    """Batch query: observation count per trial via studies → observations."""
    try:
        stmt = (
            select(
                Study.trial_id,
                func.count(Observation.id).label("obs_count"),
            )
            .join(Observation, Observation.study_id == Study.id)
            .where(
                Study.trial_id.in_(trial_ids),
                Observation.organization_id == organization_id,
            )
            .group_by(Study.trial_id)
        )
        result = await db.execute(stmt)
        rows = result.all()
        counts: dict[int, int] = {row[0]: row[1] for row in rows}
        ref = EvidenceRef(
            source_type="database",
            entity_id="enrichment:trial_observation_counts:search_trials",
            query_or_method=f"Batch trial_observation_counts for {len(trial_ids)} items",
        )
        return counts, ref
    except Exception:
        logger.warning("[Enrichment] _query_trial_observation_counts failed", exc_info=True)
        return {}, None


async def _query_trial_germplasm_counts_and_dates(
    db: AsyncSession,
    organization_id: int,
    trial_ids: list[int],
) -> tuple[dict[int, dict[str, Any]], EvidenceRef | None]:
    """Batch query: distinct germplasm count + latest observation date per trial."""
    try:
        stmt = (
            select(
                Study.trial_id,
                func.count(distinct(ObservationUnit.germplasm_id)).label("germ_count"),
                func.max(Observation.observation_time_stamp).label("latest_obs"),
            )
            .join(Study, ObservationUnit.study_id == Study.id)
            .outerjoin(
                Observation,
                (Observation.observation_unit_id == ObservationUnit.id)
                & (Observation.organization_id == organization_id),
            )
            .where(
                Study.trial_id.in_(trial_ids),
                ObservationUnit.organization_id == organization_id,
            )
            .group_by(Study.trial_id)
        )
        result = await db.execute(stmt)
        rows = result.all()
        data: dict[int, dict[str, Any]] = {
            row[0]: {"germplasm_count": row[1], "latest_observation_date": row[2]}
            for row in rows
        }
        ref = EvidenceRef(
            source_type="database",
            entity_id="enrichment:trial_germplasm_counts_and_dates:search_trials",
            query_or_method=f"Batch trial_germplasm_counts_and_dates for {len(trial_ids)} items",
        )
        return data, ref
    except Exception:
        logger.warning("[Enrichment] _query_trial_germplasm_counts_and_dates failed", exc_info=True)
        return {}, None


async def _query_trial_primary_traits(
    db: AsyncSession,
    organization_id: int,
    trial_ids: list[int],
    max_traits: int = 5,
) -> tuple[dict[int, list[str]], EvidenceRef | None]:
    """Batch query: top N trait names per trial ordered by observation frequency."""
    try:
        stmt = (
            select(
                Study.trial_id,
                ObservationVariable.observation_variable_name,
                func.count(Observation.id).label("freq"),
            )
            .join(Study, Observation.study_id == Study.id)
            .join(
                ObservationVariable,
                Observation.observation_variable_id == ObservationVariable.id,
            )
            .where(
                Study.trial_id.in_(trial_ids),
                Observation.organization_id == organization_id,
            )
            .group_by(Study.trial_id, ObservationVariable.observation_variable_name)
            .order_by(Study.trial_id, func.count(Observation.id).desc())
        )
        result = await db.execute(stmt)
        rows = result.all()

        # Post-process: take top N per trial_id
        traits_map: dict[int, list[str]] = defaultdict(list)
        for trial_id, trait_name, _freq in rows:
            if len(traits_map[trial_id]) < max_traits:
                traits_map[trial_id].append(trait_name)

        ref = EvidenceRef(
            source_type="database",
            entity_id="enrichment:trial_primary_traits:search_trials",
            query_or_method=f"Batch trial_primary_traits for {len(trial_ids)} items",
        )
        return dict(traits_map), ref
    except Exception:
        logger.warning("[Enrichment] _query_trial_primary_traits failed", exc_info=True)
        return {}, None


# ---------------------------------------------------------------------------
# Germplasm batch query helpers
# ---------------------------------------------------------------------------


async def _query_germplasm_observation_counts(
    db: AsyncSession,
    organization_id: int,
    germplasm_ids: list[int],
) -> tuple[dict[int, int], EvidenceRef | None]:
    """Batch query: observation count per germplasm."""
    try:
        stmt = (
            select(
                Observation.germplasm_id,
                func.count(Observation.id).label("obs_count"),
            )
            .where(
                Observation.germplasm_id.in_(germplasm_ids),
                Observation.organization_id == organization_id,
            )
            .group_by(Observation.germplasm_id)
        )
        result = await db.execute(stmt)
        rows = result.all()
        counts: dict[int, int] = {row[0]: row[1] for row in rows}
        ref = EvidenceRef(
            source_type="database",
            entity_id="enrichment:germplasm_observation_counts:search_germplasm",
            query_or_method=f"Batch germplasm_observation_counts for {len(germplasm_ids)} items",
        )
        return counts, ref
    except Exception:
        logger.warning("[Enrichment] _query_germplasm_observation_counts failed", exc_info=True)
        return {}, None


async def _query_germplasm_trial_participation(
    db: AsyncSession,
    organization_id: int,
    germplasm_ids: list[int],
) -> tuple[dict[int, int], EvidenceRef | None]:
    """Batch query: distinct trial participation count per germplasm."""
    try:
        stmt = (
            select(
                ObservationUnit.germplasm_id,
                func.count(distinct(Study.trial_id)).label("trial_count"),
            )
            .join(Study, ObservationUnit.study_id == Study.id)
            .where(
                ObservationUnit.germplasm_id.in_(germplasm_ids),
                ObservationUnit.organization_id == organization_id,
            )
            .group_by(ObservationUnit.germplasm_id)
        )
        result = await db.execute(stmt)
        rows = result.all()
        counts: dict[int, int] = {row[0]: row[1] for row in rows}
        ref = EvidenceRef(
            source_type="database",
            entity_id="enrichment:germplasm_trial_participation:search_germplasm",
            query_or_method=f"Batch germplasm_trial_participation for {len(germplasm_ids)} items",
        )
        return counts, ref
    except Exception:
        logger.warning("[Enrichment] _query_germplasm_trial_participation failed", exc_info=True)
        return {}, None


async def _query_germplasm_key_traits(
    db: AsyncSession,
    organization_id: int,
    germplasm_ids: list[int],
    max_traits: int = 5,
) -> tuple[dict[int, list[dict[str, str]]], EvidenceRef | None]:
    """Batch query: top N trait name+value pairs per germplasm ordered by recency."""
    try:
        stmt = (
            select(
                Observation.germplasm_id,
                ObservationVariable.observation_variable_name,
                Observation.value,
                Observation.observation_time_stamp,
            )
            .join(
                ObservationVariable,
                Observation.observation_variable_id == ObservationVariable.id,
            )
            .where(
                Observation.germplasm_id.in_(germplasm_ids),
                Observation.organization_id == organization_id,
            )
            .order_by(
                Observation.germplasm_id,
                Observation.observation_time_stamp.desc().nulls_last(),
            )
        )
        result = await db.execute(stmt)
        rows = result.all()

        # Post-process: deduplicate by trait name per germplasm, take top N
        traits_map: dict[int, list[dict[str, str]]] = defaultdict(list)
        seen: dict[int, set[str]] = defaultdict(set)
        for germ_id, trait_name, value, _ts in rows:
            if trait_name in seen[germ_id]:
                continue
            if len(traits_map[germ_id]) >= max_traits:
                continue
            seen[germ_id].add(trait_name)
            traits_map[germ_id].append({"name": trait_name, "value": value or "\u2014"})

        ref = EvidenceRef(
            source_type="database",
            entity_id="enrichment:germplasm_key_traits:search_germplasm",
            query_or_method=f"Batch germplasm_key_traits for {len(germplasm_ids)} items",
        )
        return dict(traits_map), ref
    except Exception:
        logger.warning("[Enrichment] _query_germplasm_key_traits failed", exc_info=True)
        return {}, None


# ---------------------------------------------------------------------------
# ResponseEnrichmentService
# ---------------------------------------------------------------------------


class ResponseEnrichmentService:
    """Post-execution enrichment for search function results.

    Enriches search_trials and search_germplasm results with cross-domain
    context from related tables. All other function names pass through unchanged.
    """

    SUPPORTED_FUNCTIONS: ClassVar[set[str]] = {"search_trials", "search_germplasm"}
    MAX_ENRICHMENT_ITEMS: ClassVar[int] = 20
    DOMAIN_TIMEOUT_SECONDS: ClassVar[float] = 2.0
    MAX_TRAITS_PER_ITEM: ClassVar[int] = 5

    # ------------------------------------------------------------------
    # Enrichment orchestrators
    # ------------------------------------------------------------------

    @classmethod
    async def _enrich_trials(
        cls,
        items: list[dict[str, Any]],
        db: AsyncSession,
        organization_id: int,
    ) -> tuple[dict[int, dict[str, Any]], list[EvidenceRef], list[str]]:
        """Run 3 batch enrichment queries for trial items.

        Returns:
            (enrichment_map, evidence_refs, missing_signals)
        """
        batch = items[: cls.MAX_ENRICHMENT_ITEMS]
        trial_ids = [item.get("id") for item in batch if item.get("id") is not None]
        if not trial_ids:
            return {}, [], []

        enrichment_map: dict[int, dict[str, Any]] = {tid: {} for tid in trial_ids}
        evidence_refs: list[EvidenceRef] = []
        missing_signals: list[str] = []

        # Domain 1: observation counts
        try:
            obs_counts, ref = await asyncio.wait_for(
                _query_trial_observation_counts(db, organization_id, trial_ids),
                timeout=cls.DOMAIN_TIMEOUT_SECONDS,
            )
            for tid, count in obs_counts.items():
                enrichment_map.setdefault(tid, {})["observation_count"] = count
            if ref:
                evidence_refs.append(ref)
        except asyncio.TimeoutError:
            logger.warning("[Enrichment] trial observation_counts domain timed out")
            missing_signals.append("trial_observation_counts: timeout")
        except Exception as exc:
            logger.warning("[Enrichment] trial observation_counts domain failed: %s", exc)
            missing_signals.append("trial_observation_counts: database error")

        # Domain 2: germplasm counts + latest observation dates
        try:
            germ_data, ref = await asyncio.wait_for(
                _query_trial_germplasm_counts_and_dates(db, organization_id, trial_ids),
                timeout=cls.DOMAIN_TIMEOUT_SECONDS,
            )
            for tid, data in germ_data.items():
                enrichment_map.setdefault(tid, {}).update(data)
            if ref:
                evidence_refs.append(ref)
        except asyncio.TimeoutError:
            logger.warning("[Enrichment] trial germplasm_counts_and_dates domain timed out")
            missing_signals.append("trial_germplasm_counts_and_dates: timeout")
        except Exception as exc:
            logger.warning("[Enrichment] trial germplasm_counts_and_dates domain failed: %s", exc)
            missing_signals.append("trial_germplasm_counts_and_dates: database error")

        # Domain 3: primary traits
        try:
            traits_data, ref = await asyncio.wait_for(
                _query_trial_primary_traits(
                    db, organization_id, trial_ids, max_traits=cls.MAX_TRAITS_PER_ITEM,
                ),
                timeout=cls.DOMAIN_TIMEOUT_SECONDS,
            )
            for tid, traits in traits_data.items():
                enrichment_map.setdefault(tid, {})["primary_traits"] = traits
            if ref:
                evidence_refs.append(ref)
        except asyncio.TimeoutError:
            logger.warning("[Enrichment] trial primary_traits domain timed out")
            missing_signals.append("trial_primary_traits: timeout")
        except Exception as exc:
            logger.warning("[Enrichment] trial primary_traits domain failed: %s", exc)
            missing_signals.append("trial_primary_traits: database error")

        return enrichment_map, evidence_refs, missing_signals

    @classmethod
    async def _enrich_germplasm(
        cls,
        items: list[dict[str, Any]],
        db: AsyncSession,
        organization_id: int,
    ) -> tuple[dict[int, dict[str, Any]], list[EvidenceRef], list[str]]:
        """Run 3 batch enrichment queries for germplasm items.

        Returns:
            (enrichment_map, evidence_refs, missing_signals)
        """
        batch = items[: cls.MAX_ENRICHMENT_ITEMS]
        germplasm_ids = [item.get("id") for item in batch if item.get("id") is not None]
        if not germplasm_ids:
            return {}, [], []

        enrichment_map: dict[int, dict[str, Any]] = {gid: {} for gid in germplasm_ids}
        evidence_refs: list[EvidenceRef] = []
        missing_signals: list[str] = []

        # Domain 1: observation counts
        try:
            obs_counts, ref = await asyncio.wait_for(
                _query_germplasm_observation_counts(db, organization_id, germplasm_ids),
                timeout=cls.DOMAIN_TIMEOUT_SECONDS,
            )
            for gid, count in obs_counts.items():
                enrichment_map.setdefault(gid, {})["observation_count"] = count
            if ref:
                evidence_refs.append(ref)
        except asyncio.TimeoutError:
            logger.warning("[Enrichment] germplasm observation_counts domain timed out")
            missing_signals.append("germplasm_observation_counts: timeout")
        except Exception as exc:
            logger.warning("[Enrichment] germplasm observation_counts domain failed: %s", exc)
            missing_signals.append("germplasm_observation_counts: database error")

        # Domain 2: trial participation
        try:
            trial_counts, ref = await asyncio.wait_for(
                _query_germplasm_trial_participation(db, organization_id, germplasm_ids),
                timeout=cls.DOMAIN_TIMEOUT_SECONDS,
            )
            for gid, count in trial_counts.items():
                enrichment_map.setdefault(gid, {})["trial_count"] = count
            if ref:
                evidence_refs.append(ref)
        except asyncio.TimeoutError:
            logger.warning("[Enrichment] germplasm trial_participation domain timed out")
            missing_signals.append("germplasm_trial_participation: timeout")
        except Exception as exc:
            logger.warning("[Enrichment] germplasm trial_participation domain failed: %s", exc)
            missing_signals.append("germplasm_trial_participation: database error")

        # Domain 3: key traits
        try:
            traits_data, ref = await asyncio.wait_for(
                _query_germplasm_key_traits(
                    db, organization_id, germplasm_ids, max_traits=cls.MAX_TRAITS_PER_ITEM,
                ),
                timeout=cls.DOMAIN_TIMEOUT_SECONDS,
            )
            for gid, traits in traits_data.items():
                enrichment_map.setdefault(gid, {})["key_traits"] = traits
            if ref:
                evidence_refs.append(ref)
        except asyncio.TimeoutError:
            logger.warning("[Enrichment] germplasm key_traits domain timed out")
            missing_signals.append("germplasm_key_traits: timeout")
        except Exception as exc:
            logger.warning("[Enrichment] germplasm key_traits domain failed: %s", exc)
            missing_signals.append("germplasm_key_traits: database error")

        return enrichment_map, evidence_refs, missing_signals

    # ------------------------------------------------------------------
    # Summary builders
    # ------------------------------------------------------------------

    @classmethod
    def _build_trial_summary(
        cls,
        items: list[dict[str, Any]],
        enrichment_map: dict[int, dict[str, Any]],
        total_count: int,
        search_context: str,
    ) -> str:
        """Build deterministic markdown summary for enriched trial results."""
        context_suffix = f" matching '{search_context}'" if search_context else ""
        lines: list[str] = [f"## Found {total_count} trials{context_suffix}", ""]

        for item in items[: cls.MAX_ENRICHMENT_ITEMS]:
            tid = item.get("id")
            enrichment = enrichment_map.get(tid, {}) if tid is not None else {}

            name = item.get("name") or item.get("trial_name") or "\u2014"
            crop = item.get("crop") or item.get("common_crop_name") or "\u2014"
            program = item.get("program") or item.get("program_name") or "\u2014"
            location = item.get("location") or item.get("location_name") or "\u2014"
            start_date = item.get("start_date") or "\u2014"
            end_date = item.get("end_date") or "\u2014"
            study_count = item.get("study_count") if item.get("study_count") is not None else "\u2014"

            obs_count = enrichment.get("observation_count", "\u2014")
            germ_count = enrichment.get("germplasm_count", "\u2014")
            latest_date = enrichment.get("latest_observation_date") or "\u2014"
            primary_traits = enrichment.get("primary_traits", [])
            traits_str = ", ".join(primary_traits) if primary_traits else "\u2014"

            lines.append(f"### {name}")
            lines.append(f"- **Crop:** {crop} | **Program:** {program}")
            lines.append(f"- **Location:** {location}")
            lines.append(f"- **Date range:** {start_date} \u2192 {end_date}")
            lines.append(
                f"- **Studies:** {study_count} | **Observations:** {obs_count}"
                f" | **Germplasm entries:** {germ_count}"
            )
            lines.append(f"- **Latest observation:** {latest_date}")
            lines.append(f"- **Primary traits:** {traits_str}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def _build_germplasm_summary(
        cls,
        items: list[dict[str, Any]],
        enrichment_map: dict[int, dict[str, Any]],
        total_count: int,
        search_context: str,
    ) -> str:
        """Build deterministic markdown summary for enriched germplasm results."""
        context_suffix = f" matching '{search_context}'" if search_context else ""
        lines: list[str] = [f"## Found {total_count} germplasm records{context_suffix}", ""]

        for item in items[: cls.MAX_ENRICHMENT_ITEMS]:
            gid = item.get("id")
            enrichment = enrichment_map.get(gid, {}) if gid is not None else {}

            name = item.get("name") or item.get("germplasm_name") or "\u2014"
            accession = item.get("accession") or item.get("accession_number") or "\u2014"
            species = item.get("species") or "\u2014"
            origin = item.get("origin") or item.get("country_of_origin") or "\u2014"

            obs_count = enrichment.get("observation_count", "\u2014")
            trial_count = enrichment.get("trial_count", "\u2014")
            key_traits = enrichment.get("key_traits", [])
            if key_traits:
                traits_str = ", ".join(
                    f"{t.get('name', '\u2014')}: {t.get('value', '\u2014')}" for t in key_traits
                )
            else:
                traits_str = "\u2014"

            lines.append(f"### {name}")
            lines.append(f"- **Accession:** {accession} | **Species:** {species}")
            lines.append(f"- **Origin:** {origin}")
            lines.append(
                f"- **Observations:** {obs_count} | **Trial participation:** {trial_count}"
            )
            lines.append(f"- **Key traits:** {traits_str}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Evidence envelope
    # ------------------------------------------------------------------

    @classmethod
    def _build_evidence_envelope(
        cls,
        evidence_refs: list[EvidenceRef],
        missing_signals: list[str],
    ) -> ReevuEnvelope:
        """Construct a ReevuEnvelope from collected evidence refs and failure signals."""
        return ReevuEnvelope(
            evidence_refs=evidence_refs,
            missing_evidence_signals=missing_signals,
            claims=[],
            claim_traces=[],
            calculation_steps=[],
            uncertainty=UncertaintyInfo(
                confidence=None,
                missing_data=missing_signals,
            ),
        )

    # ------------------------------------------------------------------
    # Top-level entry point
    # ------------------------------------------------------------------

    @classmethod
    async def enrich(
        cls,
        function_name: str,
        function_result: dict[str, Any],
        db: AsyncSession,
        organization_id: int,
    ) -> dict[str, Any]:
        """Enrich a function result with cross-domain context.

        Args:
            function_name: The executed function name.
            function_result: The raw result dict from the search handler.
            db: Async database session (scoped to the request).
            organization_id: Tenant ID for multi-tenant query scoping.

        Returns:
            The function_result dict, potentially with:
            - data.message replaced by a structured markdown summary
            - evidence key added with a ReevuEnvelope
            All other fields preserved unchanged.
        """
        if function_name not in cls.SUPPORTED_FUNCTIONS:
            return function_result

        try:
            if not function_result.get("success"):
                return function_result

            data = function_result.get("data")
            if not data or not isinstance(data, dict):
                return function_result

            items = data.get("items")
            if not items:
                return function_result

            total_count = data.get("total", len(items))
            search_context = data.get("search_context", "")
            # Derive search context from the original message if not explicitly set
            if not search_context:
                msg = data.get("message", "")
                if "matching '" in msg:
                    search_context = msg.split("matching '", 1)[1].rstrip("'")

            # Dispatch to the appropriate enrichment orchestrator
            if function_name == "search_trials":
                enrichment_map, evidence_refs, missing_signals = await cls._enrich_trials(
                    items, db, organization_id,
                )
            else:
                enrichment_map, evidence_refs, missing_signals = await cls._enrich_germplasm(
                    items, db, organization_id,
                )

            # If enrichment map is entirely empty (all domains failed), return unchanged
            if not any(enrichment_map.values()):
                return function_result

            # Build summary and replace data.message
            if function_name == "search_trials":
                summary = cls._build_trial_summary(
                    items, enrichment_map, total_count, search_context,
                )
            else:
                summary = cls._build_germplasm_summary(
                    items, enrichment_map, total_count, search_context,
                )

            data["message"] = summary

            # Build evidence envelope and attach
            envelope = cls._build_evidence_envelope(evidence_refs, missing_signals)
            function_result["evidence"] = envelope.model_dump()

            return function_result

        except Exception as exc:
            logger.error(
                "[Enrichment] Top-level enrichment failed for %s: %s",
                function_name,
                exc,
            )
            return function_result