"""REEVU genomic prediction service."""

from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sqlalchemy import func, select

from app.modules.ai.services.statistics_calculator_service import ObservationData
from app.schemas.reevu_envelope import CalculationStep, EvidenceRef
from app.services.compute_engine import compute_engine as default_compute_engine


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GEBVEntry:
    germplasm_id: str
    germplasm_name: str
    gebv: float
    reliability: float | None
    rank: int


@dataclass(slots=True)
class GRMResult:
    n_individuals: int
    n_markers: int
    matrix_available: bool
    cache_key: str | None
    matrix: list[list[float]] | None = None
    reason: str | None = None
    cache_hit: bool = False


@dataclass(slots=True)
class GEBVResult:
    trait_name: str
    method: str
    gebvs: list[GEBVEntry] = field(default_factory=list)
    accuracy: float | None = None
    n_individuals: int = 0
    n_markers: int = 0
    insufficient_data: bool = False
    reason: str | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    calculation_steps: list[CalculationStep] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    genetic_variance: float | None = None
    error_variance: float | None = None
    mean: float | None = None
    converged: bool | None = None


class GenomicPredictionService:
    """Compute GEBVs from phenotype values and genomic relationship data."""

    MIN_INDIVIDUALS = 10
    MIN_MARKERS = 100
    GRM_CACHE_TTL_SECONDS = 24 * 60 * 60

    def __init__(
        self,
        *,
        compute_engine: Any = None,
        cache: Any = None,
        observation_search_service: Any = None,
        germplasm_search_service: Any = None,
    ) -> None:
        self._compute_engine = compute_engine or default_compute_engine
        self._cache = cache
        self._observation_search_service = observation_search_service
        self._germplasm_search_service = germplasm_search_service

    async def compute_gebv(
        self,
        db: Any,
        organization_id: int,
        trait_name: str,
        germplasm_ids: list[str] | None = None,
        method: str = "GBLUP",
        *,
        phenotype_values: list[float] | None = None,
        genotype_matrix: list[list[float]] | None = None,
        g_matrix: list[list[float]] | None = None,
        heritability: float = 0.3,
        enforce_minimums: bool = True,
    ) -> GEBVResult:
        """Compute genomic estimated breeding values for a trait."""
        if method.upper() != "GBLUP":
            return self._insufficient_result(
                trait_name=trait_name,
                method=method,
                reason="unsupported_method",
                message="Only GBLUP genomic prediction is supported by this REEVU service.",
            )

        labels = await self._resolve_germplasm_labels(
            db=db,
            organization_id=organization_id,
            germplasm_ids=germplasm_ids,
        )
        if phenotype_values is None:
            phenotype_values, labels = await self._load_phenotypes(
                db=db,
                organization_id=organization_id,
                trait_name=trait_name,
                germplasm_ids=labels or germplasm_ids,
            )

        if not phenotype_values:
            return self._insufficient_result(
                trait_name=trait_name,
                method="GBLUP",
                reason="missing_phenotypes",
                message="No numeric phenotype values were available for GBLUP.",
            )

        labels = _labels_for_values(labels or germplasm_ids, len(phenotype_values))

        if g_matrix is not None:
            grm = GRMResult(
                n_individuals=len(g_matrix),
                n_markers=len(g_matrix[0]) if g_matrix and isinstance(g_matrix[0], list) else 0,
                matrix_available=True,
                cache_key=None,
                matrix=g_matrix,
            )
        else:
            grm = await self._build_grm(
                db=db,
                organization_id=organization_id,
                germplasm_ids=labels,
                genotype_matrix=genotype_matrix,
                enforce_minimums=enforce_minimums,
            )

        if not grm.matrix_available or grm.matrix is None:
            return self._insufficient_result(
                trait_name=trait_name,
                method="GBLUP",
                reason=grm.reason or "missing_grm",
                message=grm.reason or "A genomic relationship matrix was not available.",
                n_individuals=grm.n_individuals,
                n_markers=grm.n_markers,
            )

        if enforce_minimums and len(phenotype_values) < self.MIN_INDIVIDUALS:
            return self._insufficient_result(
                trait_name=trait_name,
                method="GBLUP",
                reason="insufficient_individuals",
                message=(
                    f"GBLUP requires at least {self.MIN_INDIVIDUALS} individuals; "
                    f"found {len(phenotype_values)}."
                ),
                n_individuals=len(phenotype_values),
                n_markers=grm.n_markers,
            )

        phenotypes = np.asarray(phenotype_values, dtype=np.float64)
        if genotype_matrix is not None and g_matrix is None:
            compute_result = self._compute_engine.compute_gblup(
                genotypes=np.asarray(genotype_matrix, dtype=np.float64),
                phenotypes=phenotypes,
                heritability=heritability,
            )
            n_markers = len(genotype_matrix[0]) if genotype_matrix else grm.n_markers
        else:
            compute_result = self._compute_engine.compute_gblup_from_grm(
                phenotypes=phenotypes,
                grm=np.asarray(grm.matrix, dtype=np.float64),
                heritability=heritability,
            )
            n_markers = grm.n_markers

        return self._result_from_compute_output(
            trait_name=trait_name,
            method="GBLUP",
            labels=labels,
            compute_result=compute_result,
            n_markers=n_markers,
            heritability=heritability,
            cache_key=grm.cache_key,
            cache_hit=grm.cache_hit,
        )

    async def _build_grm(
        self,
        db: Any,
        organization_id: int,
        germplasm_ids: list[str],
        *,
        genotype_matrix: list[list[float]] | None = None,
        enforce_minimums: bool = True,
    ) -> GRMResult:
        """Build or retrieve a cached genomic relationship matrix."""
        cache_key = self._cache_key(organization_id, germplasm_ids)
        cached = await self._cache_get(cache_key)
        if isinstance(cached, dict) and cached.get("matrix") is not None:
            return GRMResult(
                n_individuals=int(cached.get("n_individuals") or len(cached["matrix"])),
                n_markers=int(cached.get("n_markers") or 0),
                matrix_available=True,
                cache_key=cache_key,
                matrix=cached["matrix"],
                cache_hit=True,
            )

        if genotype_matrix is None:
            genotype_matrix = await self._load_genotype_matrix_from_db(
                db=db,
                organization_id=organization_id,
                germplasm_ids=germplasm_ids,
            )

        n_individuals = len(genotype_matrix or [])
        n_markers = (
            len(genotype_matrix[0])
            if genotype_matrix and isinstance(genotype_matrix[0], list)
            else 0
        )
        if enforce_minimums and (
            n_individuals < self.MIN_INDIVIDUALS or n_markers < self.MIN_MARKERS
        ):
            return GRMResult(
                n_individuals=n_individuals,
                n_markers=n_markers,
                matrix_available=False,
                cache_key=cache_key,
                reason=(
                    f"GBLUP requires at least {self.MIN_INDIVIDUALS} individuals and "
                    f"{self.MIN_MARKERS} markers; found {n_individuals} individuals "
                    f"and {n_markers} markers."
                ),
            )

        if not genotype_matrix:
            return GRMResult(
                n_individuals=0,
                n_markers=0,
                matrix_available=False,
                cache_key=cache_key,
                reason="No genotype matrix was available for GRM construction.",
            )

        grm_result = self._compute_engine.compute_grm(
            np.asarray(genotype_matrix, dtype=np.float64),
            method="vanraden1",
        )
        matrix = grm_result.matrix.tolist()
        await self._cache_set(
            cache_key,
            {
                "matrix": matrix,
                "n_individuals": grm_result.n_individuals,
                "n_markers": grm_result.n_markers,
            },
        )
        return GRMResult(
            n_individuals=grm_result.n_individuals,
            n_markers=grm_result.n_markers,
            matrix_available=True,
            cache_key=cache_key,
            matrix=matrix,
            cache_hit=False,
        )

    async def _resolve_germplasm_labels(
        self,
        *,
        db: Any,
        organization_id: int,
        germplasm_ids: list[str] | None,
    ) -> list[str] | None:
        if not germplasm_ids:
            return None
        if self._germplasm_search_service is None:
            return [str(germplasm_id) for germplasm_id in germplasm_ids]

        labels: list[str] = []
        for germplasm_id in germplasm_ids:
            try:
                matches = await self._germplasm_search_service.search(
                    db=db,
                    organization_id=organization_id,
                    query=str(germplasm_id),
                    limit=1,
                )
            except Exception:
                logger.exception("Failed to resolve germplasm label %s", germplasm_id)
                matches = []
            if matches:
                match = matches[0]
                labels.append(
                    str(
                        match.get("accession")
                        or match.get("name")
                        or match.get("germplasm_name")
                        or match.get("id")
                        or germplasm_id
                    )
                )
            else:
                labels.append(str(germplasm_id))
        return labels

    async def _load_phenotypes(
        self,
        *,
        db: Any,
        organization_id: int,
        trait_name: str,
        germplasm_ids: list[str] | None,
    ) -> tuple[list[float], list[str]]:
        if self._observation_search_service is None:
            return [], []

        observations = await self._observation_search_service.search(
            db=db,
            organization_id=organization_id,
            trait=trait_name,
            limit=500,
        )
        grouped: dict[str, list[float]] = {}
        requested = {str(germplasm_id).lower() for germplasm_id in (germplasm_ids or [])}
        for observation in observations:
            value = _numeric_value(observation)
            if value is None:
                continue
            germplasm = observation.get("germplasm") if isinstance(observation, dict) else {}
            label = str(
                observation.get("germplasm_id")
                or (germplasm or {}).get("accession")
                or (germplasm or {}).get("name")
                or (germplasm or {}).get("id")
                or observation.get("id")
            )
            if requested and label.lower() not in requested:
                continue
            grouped.setdefault(label, []).append(value)

        labels = sorted(grouped)
        return [float(np.mean(grouped[label])) for label in labels], labels

    async def _load_genotype_matrix_from_db(
        self,
        *,
        db: Any,
        organization_id: int,
        germplasm_ids: list[str],
    ) -> list[list[float]] | None:
        if not hasattr(db, "execute") or not germplasm_ids:
            return None

        from app.models.genotyping import Call, CallSet, Variant

        requested = [label.lower() for label in germplasm_ids]
        stmt = (
            select(
                CallSet.call_set_name.label("call_set_name"),
                Variant.variant_db_id.label("variant_db_id"),
                Variant.variant_name.label("variant_name"),
                Variant.start.label("variant_start"),
                Call.genotype_value.label("genotype_value"),
                Call.genotype.label("genotype"),
            )
            .select_from(CallSet)
            .join(Call, Call.call_set_id == CallSet.id)
            .join(Variant, Variant.id == Call.variant_id)
            .where(CallSet.organization_id == organization_id)
            .where(func.lower(CallSet.call_set_name).in_(requested))
            .order_by(
                CallSet.call_set_name.asc(),
                Variant.start.asc(),
                Variant.variant_name.asc(),
            )
        )
        rows = (await db.execute(stmt)).all()
        genotype_rows_by_label: dict[str, dict[str, float]] = {}
        variant_order: dict[str, tuple[float, str]] = {}
        for row in rows:
            label = str(row.call_set_name or "").strip().lower()
            dosage = _coerce_genotype_dosage(row.genotype_value, row.genotype)
            if not label or dosage is None:
                continue
            variant_key = (
                str(row.variant_db_id or "").strip()
                or str(row.variant_name or "").strip()
                or f"variant-{len(variant_order) + 1}"
            )
            genotype_rows_by_label.setdefault(label, {})[variant_key] = dosage
            variant_order.setdefault(
                variant_key,
                (
                    float(row.variant_start)
                    if row.variant_start is not None
                    else float("inf"),
                    str(row.variant_name or variant_key),
                ),
            )

        ordered_labels = [label for label in requested if genotype_rows_by_label.get(label)]
        if not ordered_labels:
            return None
        shared_variants = set(genotype_rows_by_label[ordered_labels[0]])
        for label in ordered_labels[1:]:
            shared_variants &= set(genotype_rows_by_label[label])
        ordered_variants = sorted(
            shared_variants,
            key=lambda variant: variant_order.get(variant, (float("inf"), variant)),
        )
        return [
            [genotype_rows_by_label[label][variant] for variant in ordered_variants]
            for label in ordered_labels
        ]

    def _result_from_compute_output(
        self,
        *,
        trait_name: str,
        method: str,
        labels: list[str],
        compute_result: Any,
        n_markers: int | None,
        heritability: float,
        cache_key: str | None,
        cache_hit: bool,
    ) -> GEBVResult:
        breeding_values = [float(value) for value in compute_result.breeding_values.tolist()]
        reliability_values = (
            [float(value) for value in compute_result.reliability.tolist()]
            if compute_result.reliability is not None
            else [None for _ in breeding_values]
        )
        accuracy_values = (
            [float(value) for value in compute_result.accuracy.tolist()]
            if compute_result.accuracy is not None
            else [
                math.sqrt(value)
                for value in reliability_values
                if isinstance(value, (int, float)) and value >= 0
            ]
        )
        accuracy = float(np.mean(accuracy_values)) if accuracy_values else None
        warnings = []
        if accuracy is not None and accuracy < 0.3:
            warnings.append("low_accuracy")

        entries = [
            GEBVEntry(
                germplasm_id=labels[index],
                germplasm_name=labels[index],
                gebv=breeding_value,
                reliability=_bounded_reliability(reliability_values[index]),
                rank=0,
            )
            for index, breeding_value in enumerate(breeding_values)
        ]
        entries.sort(key=lambda entry: entry.gebv, reverse=True)
        for rank, entry in enumerate(entries, start=1):
            entry.rank = rank

        evidence_refs = [
            EvidenceRef(
                source_type="function",
                entity_id="fn:compute.gblup",
                query_or_method="compute_engine.compute_gblup",
            ),
            EvidenceRef(
                source_type="database",
                entity_id=f"org:{trait_name}:phenotypes",
                query_or_method="observation_search_service.search",
            ),
            EvidenceRef(
                source_type="database",
                entity_id=cache_key or f"org:{trait_name}:grm",
                query_or_method="genomic_prediction_service._build_grm",
            ),
        ]
        calculation_steps = [
            CalculationStep(
                step_id="fn:compute.gblup",
                formula="GBLUP mixed model solve using genomic relationship matrix",
                inputs={
                    "trait": trait_name,
                    "method": method,
                    "heritability": heritability,
                    "n_individuals": len(entries),
                    "n_markers": n_markers,
                    "grm_cache_hit": cache_hit,
                },
            )
        ]

        return GEBVResult(
            trait_name=trait_name,
            method=method,
            gebvs=entries,
            accuracy=accuracy,
            n_individuals=len(entries),
            n_markers=int(n_markers or 0),
            insufficient_data=False,
            reason=None,
            evidence_refs=evidence_refs,
            calculation_steps=calculation_steps,
            warnings=warnings,
            genetic_variance=compute_result.genetic_variance,
            error_variance=compute_result.error_variance,
            mean=float(compute_result.fixed_effects[0])
            if len(compute_result.fixed_effects) > 0
            else None,
            converged=compute_result.converged,
        )

    def _insufficient_result(
        self,
        *,
        trait_name: str,
        method: str,
        reason: str,
        message: str,
        n_individuals: int = 0,
        n_markers: int = 0,
    ) -> GEBVResult:
        return GEBVResult(
            trait_name=trait_name,
            method=method,
            n_individuals=n_individuals,
            n_markers=n_markers,
            insufficient_data=True,
            reason=message,
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id=f"genomic_prediction:{reason}",
                    query_or_method="genomic_prediction_service.compute_gebv",
                )
            ],
            calculation_steps=[
                CalculationStep(
                    step_id=f"genomic_prediction:{reason}",
                    formula="input_count < required_minimum",
                    inputs={
                        "n_individuals": n_individuals,
                        "n_markers": n_markers,
                        "min_individuals": self.MIN_INDIVIDUALS,
                        "min_markers": self.MIN_MARKERS,
                    },
                )
            ],
            warnings=[reason],
        )

    async def _cache_get(self, cache_key: str) -> Any:
        cache = self._cache or _default_cache()
        if cache is None:
            return None
        value = await cache.get(cache_key)
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return value

    async def _cache_set(self, cache_key: str, value: dict[str, Any]) -> None:
        cache = self._cache or _default_cache()
        if cache is None:
            return
        try:
            await cache.set(cache_key, value, ttl_seconds=self.GRM_CACHE_TTL_SECONDS)
        except TypeError:
            await cache.set(cache_key, json.dumps(value), ex=self.GRM_CACHE_TTL_SECONDS)

    @staticmethod
    def _cache_key(organization_id: int, germplasm_ids: list[str]) -> str:
        digest = hashlib.sha256(
            json.dumps(sorted(germplasm_ids), separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:16]
        return f"grm:{organization_id}:{digest}"


def _labels_for_values(labels: list[str] | None, count: int) -> list[str]:
    valid = [label for label in (labels or []) if isinstance(label, str) and label.strip()]
    if len(valid) == count:
        return valid
    return [f"candidate-{index}" for index in range(1, count + 1)]


def _numeric_value(observation: dict[str, Any]) -> float | None:
    try:
        parsed = float(observation.get("value"))
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _bounded_reliability(value: Any) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def _coerce_genotype_dosage(genotype_value: Any, genotype_payload: Any = None) -> float | None:
    def _coerce(candidate: Any) -> float | None:
        if candidate is None or isinstance(candidate, bool):
            return None
        if isinstance(candidate, (int, float)):
            return float(candidate)
        if isinstance(candidate, list):
            alleles = []
            for item in candidate:
                if isinstance(item, bool):
                    return None
                if isinstance(item, (int, float)):
                    alleles.append(int(item))
                    continue
                if isinstance(item, str) and item.strip().isdigit():
                    alleles.append(int(item.strip()))
                    continue
                return None
            return float(sum(alleles)) if alleles else None
        if isinstance(candidate, str):
            normalized = candidate.strip()
            if not normalized or normalized in {".", "./.", ".|."}:
                return None
            if normalized.isdigit():
                return float(int(normalized))
            if "/" in normalized or "|" in normalized:
                alleles = []
                for token in normalized.replace("|", "/").split("/"):
                    stripped = token.strip()
                    if not stripped or stripped == "." or not stripped.isdigit():
                        return None
                    alleles.append(int(stripped))
                return float(sum(alleles)) if alleles else None
        return None

    dosage = _coerce(genotype_value)
    if dosage is not None:
        return dosage
    if isinstance(genotype_payload, dict):
        return _coerce(genotype_payload.get("values"))
    return _coerce(genotype_payload)


def _default_cache() -> Any:
    try:
        from app.core.redis import redis_client

        return redis_client
    except Exception:
        return None
