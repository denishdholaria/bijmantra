"""
REEVU Step Executor — Stage 3 (Data Execution)

Reads a ReevuExecutionPlan, executes steps in prerequisite order,
passes intermediate results between dependent steps (query narrowing),
accumulates evidence refs with step provenance, and enforces bounded
execution.  The cross-domain handler delegates to this module but
continues to own response payload assembly.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import math
import re
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Literal

from app.modules.environment.services.weather_service import WeatherForecastUnavailableError
from app.modules.germplasm.services.seedlot_search_service import seedlot_search_service
from app.modules.phenotyping.services.observation_search_service import observation_search_service
from app.modules.phenotyping.services.trait_search_service import trait_search_service
from app.modules.ai.services.reevu.analytics_engine import AnalyticsEngine, AnalyticsResult, extract_observations
from app.schemas.reevu_envelope import EvidenceRef
from app.schemas.reevu_plan import PlanStep, ReevuExecutionPlan

logger = logging.getLogger(__name__)

# Domain execution priority — lower index executes first when no
# dependency relationship exists between two steps.
DOMAIN_ORDER: dict[str, int] = {
    "weather": 0,
    "trials": 1,
    "field": 2,
    "phenotyping": 3,
    "genomics": 4,
    "breeding": 5,
    "seed_ops": 6,
    "protocols": 7,
    "analytics": 8,
}


# ── Data Models ──────────────────────────────────────────────────────


@dataclass
class StepResult:
    """Output of a single executed plan step."""

    step_id: str
    domain: str
    status: Literal["success", "failed", "skipped", "timed_out"]
    records: dict[str, Any] = field(default_factory=dict)
    entity_ids: list[str] = field(default_factory=list)
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    duration_ms: float = 0.0
    error_category: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntermediateResultContext:
    """Carries outputs from completed steps to dependent steps."""

    _results: dict[str, StepResult] = field(default_factory=dict)

    def add(self, result: StepResult) -> None:
        """Register a completed step's result."""
        self._results[result.step_id] = result

    def get(self, step_id: str) -> StepResult | None:
        """Retrieve a step's result, or None if not found."""
        return self._results.get(step_id)

    def get_entity_ids(self, step_id: str) -> list[str]:
        """Return entity IDs from a step, or empty list if step missing/failed."""
        result = self._results.get(step_id)
        if result is None or result.status != "success":
            return []
        return result.entity_ids

    def get_records(self, step_id: str) -> dict[str, Any]:
        """Return records from a step, or empty dict if step missing/failed."""
        result = self._results.get(step_id)
        if result is None or result.status != "success":
            return {}
        return result.records

    def all_results(self) -> list[StepResult]:
        """Return all results in insertion order."""
        return list(self._results.values())

    def all_evidence_refs(self) -> list[EvidenceRef]:
        """Collect evidence refs from all successful steps in execution order."""
        refs: list[EvidenceRef] = []
        for result in self._results.values():
            if result.status == "success":
                refs.extend(result.evidence_refs)
        return refs


@dataclass(slots=True)
class ExecutionOutcome:
    """Aggregate result of executing an entire plan."""

    step_results: list[StepResult]
    evidence_refs: list[EvidenceRef]
    total_duration_ms: float
    steps_completed: int
    steps_failed: int
    steps_skipped: int
    steps_timed_out: int
    budget_exhausted: bool

    @property
    def step_execution_trace(self) -> list[dict[str, Any]]:
        """Execution audit trail for the evidence envelope."""
        trace: list[dict[str, Any]] = []
        for result in self.step_results:
            entry = {
                "step_id": result.step_id,
                "domain": result.domain,
                "status": result.status,
                "duration_ms": result.duration_ms,
                "error_category": result.error_category,
            }
            if result.metadata:
                entry["metadata"] = dict(result.metadata)
            trace.append(entry)
        return trace


def _as_nonempty_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        return list(value)
    return [value]


def _coerce_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _parse_observation_value(observation: dict[str, Any]) -> float | None:
    value = None
    for key in ("value", "observation_value", "observationValue", "value_numeric", "valueNumeric"):
        if key in observation:
            value = observation.get(key)
            break
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _nested_dict(source: dict[str, Any], key: str) -> dict[str, Any]:
    value = source.get(key)
    return value if isinstance(value, dict) else {}


def _observation_identity(observation: dict[str, Any]) -> tuple[str, str] | None:
    for key in ("observation_db_id", "observationDbId", "id", "observation_id", "observationId"):
        value = _as_nonempty_string(observation.get(key))
        if value:
            return key, value
    return None


def _observation_trait_id(observation: dict[str, Any]) -> str | None:
    trait = _nested_dict(observation, "trait")
    observation_variable = _nested_dict(observation, "observation_variable") or _nested_dict(
        observation,
        "observationVariable",
    )
    return (
        _as_nonempty_string(observation.get("trait_id"))
        or _as_nonempty_string(observation.get("observation_variable_id"))
        or _as_nonempty_string(trait.get("id") or trait.get("db_id") or trait.get("dbId"))
        or _as_nonempty_string(
            observation_variable.get("id")
            or observation_variable.get("db_id")
            or observation_variable.get("dbId")
        )
    )


def _observation_trait_name(observation: dict[str, Any]) -> str | None:
    trait = _nested_dict(observation, "trait")
    observation_variable = _nested_dict(observation, "observation_variable") or _nested_dict(
        observation,
        "observationVariable",
    )
    return (
        _as_nonempty_string(observation.get("trait_name"))
        or _as_nonempty_string(observation.get("traitName"))
        or _as_nonempty_string(observation.get("observation_variable_name"))
        or _as_nonempty_string(observation.get("observationVariableName"))
        or _as_nonempty_string(trait.get("trait_name") or trait.get("traitName") or trait.get("name"))
        or _as_nonempty_string(
            observation_variable.get("trait_name")
            or observation_variable.get("traitName")
            or observation_variable.get("name")
        )
    )


def _observation_study_id(observation: dict[str, Any]) -> str | None:
    study = _nested_dict(observation, "study")
    return (
        _as_nonempty_string(observation.get("study_id"))
        or _as_nonempty_string(observation.get("studyId"))
        or _as_nonempty_string(study.get("id") or study.get("db_id") or study.get("dbId"))
    )


def _observation_study_name(observation: dict[str, Any]) -> str:
    study = _nested_dict(observation, "study")
    return (
        _as_nonempty_string(observation.get("study_name"))
        or _as_nonempty_string(observation.get("studyName"))
        or _as_nonempty_string(study.get("name"))
        or _as_nonempty_string(study.get("study_name"))
        or _observation_study_id(observation)
        or "unknown_study"
    )


def _build_stats(values: list[float]) -> dict[str, Any]:
    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "min": min(values),
        "max": max(values),
    }


def _dedupe_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for observation in observations:
        if not isinstance(observation, dict):
            continue
        identity = _observation_identity(observation)
        if identity is not None:
            if identity in seen:
                continue
            seen.add(identity)
        deduped.append(observation)
    return deduped


def _summarize_observations(observations: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_values: list[float] = []
    values_by_study: dict[str, list[float]] = defaultdict(list)
    dropped_non_numeric = 0

    for observation in observations:
        value = _parse_observation_value(observation)
        if value is None:
            dropped_non_numeric += 1
            logger.debug(
                "Skipping non-numeric phenotyping observation value for summary stats: %r",
                observation.get("value"),
            )
            continue
        numeric_values.append(value)
        values_by_study[_observation_study_name(observation)].append(value)

    by_study = [
        {"study": study_name, **_build_stats(values)}
        for study_name, values in sorted(values_by_study.items())
        if values
    ]
    return {
        "overall": _build_stats(numeric_values) if numeric_values else None,
        "by_study": by_study,
        "numeric_observation_count": len(numeric_values),
        "dropped_non_numeric_count": dropped_non_numeric,
    }


def _seedlot_quantity(seedlot: dict[str, Any]) -> float:
    for key in ("quantity", "amount", "count", "total_quantity", "total_quantity_grams"):
        value = seedlot.get(key)
        if value is None:
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(parsed):
            return parsed
    return 0.0


def _seedlot_identity(seedlot: dict[str, Any]) -> str:
    germplasm = _nested_dict(seedlot, "germplasm")
    return (
        _as_nonempty_string(germplasm.get("name"))
        or _as_nonempty_string(germplasm.get("accession"))
        or _as_nonempty_string(seedlot.get("germplasm_name"))
        or _as_nonempty_string(seedlot.get("name"))
        or _as_nonempty_string(seedlot.get("seedlot_db_id"))
        or _as_nonempty_string(seedlot.get("id"))
        or "unknown_seedlot"
    )


def _seedlot_id(seedlot: dict[str, Any]) -> str | None:
    return _as_nonempty_string(seedlot.get("seedlot_db_id")) or _as_nonempty_string(seedlot.get("id"))


def _build_seed_inventory_summary(seedlots: list[dict[str, Any]]) -> dict[str, Any]:
    low_stock_entries: list[str] = []
    unavailable_entries: list[str] = []
    total_quantity = 0.0
    availability_by_germplasm: dict[str, dict[str, Any]] = {}

    for seedlot in seedlots:
        quantity = _seedlot_quantity(seedlot)
        total_quantity += quantity
        identity = _seedlot_identity(seedlot)
        if quantity < 100:
            low_stock_entries.append(identity)
        status = str(seedlot.get("status") or seedlot.get("availability") or "").casefold()
        if quantity <= 0 or status in {"unavailable", "depleted", "out_of_stock"}:
            unavailable_entries.append(identity)

        germplasm = _nested_dict(seedlot, "germplasm")
        germplasm_key = (
            _as_nonempty_string(germplasm.get("id"))
            or _as_nonempty_string(seedlot.get("germplasm_id"))
            or identity
        )
        entry = availability_by_germplasm.setdefault(
            germplasm_key,
            {
                "germplasm_id": germplasm_key,
                "germplasm_name": _as_nonempty_string(germplasm.get("name")) or identity,
                "seedlot_count": 0,
                "total_quantity_grams": 0.0,
                "available": False,
            },
        )
        entry["seedlot_count"] += 1
        entry["total_quantity_grams"] += quantity
        entry["available"] = bool(entry["available"] or quantity > 0)

    return {
        "total_lots": len(seedlots),
        "total_quantity_grams": total_quantity,
        "low_stock_entries": list(dict.fromkeys(low_stock_entries)),
        "unavailable_entries": list(dict.fromkeys(unavailable_entries)),
        "availability": list(availability_by_germplasm.values()),
    }


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _location_id(location: dict[str, Any]) -> str | None:
    return (
        _as_nonempty_string(location.get("location_db_id"))
        or _as_nonempty_string(location.get("locationDbId"))
        or _as_nonempty_string(location.get("id"))
    )


def _location_name(location: dict[str, Any]) -> str | None:
    return (
        _as_nonempty_string(location.get("name"))
        or _as_nonempty_string(location.get("location_name"))
        or _as_nonempty_string(location.get("locationName"))
    )


def _iso_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def _record_value(record: Any, *keys: str) -> Any:
    for key in keys:
        if isinstance(record, dict) and key in record:
            return record.get(key)
        if not isinstance(record, dict) and hasattr(record, key):
            return getattr(record, key)
    return None


def _calendar_matches_scope(
    calendar: Any,
    *,
    crop_query: str | None,
    location_ids: set[str],
    season: str | None,
) -> bool:
    crop_id = _as_nonempty_string(_record_value(calendar, "crop_id", "crop", "crop_name"))
    if crop_query and crop_id and crop_query.casefold() not in crop_id.casefold():
        return False

    location_id = _as_nonempty_string(_record_value(calendar, "location_id", "locationDbId"))
    if location_ids and location_id and location_id not in location_ids:
        return False

    record_season = _as_nonempty_string(_record_value(calendar, "season"))
    if season and record_season and season.casefold() not in record_season.casefold():
        return False

    return True


def _calendar_event_dict(
    *,
    event_type: str,
    crop: str | None,
    location_id: str | None,
    planned_date: Any,
    season: str | None,
    notes: Any = None,
    status: Any = None,
) -> dict[str, Any]:
    event = {
        "event_type": event_type,
        "crop": crop,
        "location_id": location_id,
        "planned_date": _iso_or_none(planned_date),
        "season": season,
        "notes": _as_nonempty_string(notes),
    }
    if status is not None:
        event["status"] = _as_nonempty_string(status)
    return event


def _calendar_to_events(calendar: Any, *, default_season: str | None) -> list[dict[str, Any]]:
    if isinstance(calendar, dict):
        if "event_type" in calendar or "planned_date" in calendar or "scheduled_date" in calendar:
            planned_date = calendar.get("planned_date") or calendar.get("scheduled_date")
            return [
                {
                    **calendar,
                    "planned_date": _iso_or_none(planned_date),
                    "event_type": calendar.get("event_type") or calendar.get("activity_name") or "calendar_event",
                }
            ]
        if isinstance(calendar.get("crop_calendar_events"), list):
            return [
                {
                    **event,
                    "planned_date": _iso_or_none(event.get("planned_date") or event.get("scheduled_date")),
                }
                for event in calendar["crop_calendar_events"]
                if isinstance(event, dict)
            ]

    crop = _as_nonempty_string(_record_value(calendar, "crop_id", "crop", "crop_name"))
    location_id = _as_nonempty_string(_record_value(calendar, "location_id", "locationDbId"))
    notes = _record_value(calendar, "notes")
    season = _as_nonempty_string(_record_value(calendar, "season")) or default_season
    events: list[dict[str, Any]] = []

    planting_date = _record_value(calendar, "planting_date", "sowing_date")
    if planting_date is not None:
        events.append(
            _calendar_event_dict(
                event_type="planting",
                crop=crop,
                location_id=location_id,
                planned_date=planting_date,
                season=season,
                notes=notes,
                status=_record_value(calendar, "status"),
            )
        )

    harvest_date = _record_value(calendar, "expected_harvest_date", "harvest_date")
    if harvest_date is not None:
        events.append(
            _calendar_event_dict(
                event_type="harvest",
                crop=crop,
                location_id=location_id,
                planned_date=harvest_date,
                season=season,
                notes=notes,
                status=_record_value(calendar, "status"),
            )
        )

    for schedule_event in _as_list(_record_value(calendar, "events")):
        if schedule_event is None:
            continue
        events.append(
            _calendar_event_dict(
                event_type=(
                    _as_nonempty_string(_record_value(schedule_event, "activity_name", "event_type"))
                    or "calendar_event"
                ),
                crop=crop,
                location_id=location_id,
                planned_date=_record_value(schedule_event, "scheduled_date", "planned_date"),
                season=season,
                notes=_record_value(schedule_event, "notes"),
                status=_record_value(schedule_event, "status"),
            )
        )

    return events


def _extract_field_layouts(locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    layouts: list[dict[str, Any]] = []
    for location in locations:
        location_ref = _location_id(location)
        for key in ("field_layout", "field_layouts", "layout"):
            value = location.get(key)
            for layout in _as_list(value):
                if not isinstance(layout, dict):
                    continue
                entry = dict(layout)
                if location_ref and not entry.get("location_id"):
                    entry["location_id"] = location_ref
                layouts.append(entry)
    return layouts


# ── Step Executor ────────────────────────────────────────────────────


class StepExecutor:
    """Executes a ReevuExecutionPlan in dependency order with intermediate result chaining."""

    MAX_STEPS: int = 10
    MAX_TOTAL_SECONDS: float = 30.0
    MAX_STEP_SECONDS: float = 10.0
    _RANKING_KEYWORDS = {"rank", "best", "top", "worst", "bottom", "perform", "compare"}
    _COMPARISON_KEYWORDS = {"compare", "difference", "significant", "versus", "vs"}
    _DISTRIBUTION_KEYWORDS = {"distribution", "histogram", "spread", "quartile"}

    def __init__(
        self,
        executor: Any,
        organization_id: int,
        original_query: str,
        params: dict[str, Any],
    ) -> None:
        self._executor = executor
        self._organization_id = organization_id
        self._original_query = original_query
        self._params = params
        self._domain_handlers: dict[str, Callable[..., Coroutine[Any, Any, StepResult]]] = {
            "trials": self._execute_trials_step,
            "field": self._execute_field_step,
            "phenotyping": self._execute_phenotyping_step,
            "breeding": self._execute_breeding_step,
            "weather": self._execute_weather_step,
            "genomics": self._execute_genomics_step,
            "seed_ops": self._execute_seed_ops_step,
            "protocols": self._execute_protocols_step,
            "analytics": self._execute_analytics_step,
        }

    # ── Dispatch ─────────────────────────────────────────────────────

    def _domain_handler(self, domain: str) -> Callable[..., Coroutine[Any, Any, StepResult]] | None:
        return self._domain_handlers.get(domain)

    def _observation_search_service(self) -> Any:
        return getattr(self._executor, "observation_search_service", observation_search_service)

    def _seedlot_search_service(self) -> Any:
        return getattr(self._executor, "seedlot_search_service", seedlot_search_service)

    def _trait_search_service(self) -> Any:
        return getattr(self._executor, "trait_search_service", trait_search_service)

    def _crop_calendar_service(self) -> Any:
        return getattr(self._executor, "crop_calendar_service", None)

    def _qtl_mapping_service_factory(self) -> Callable[[], Any]:
        from app.modules.genomics.services.qtl_mapping_service import get_qtl_mapping_service

        return getattr(self._executor, "get_qtl_mapping_service", get_qtl_mapping_service)

    async def _fetch_crop_calendar_events(
        self,
        *,
        crop_calendar_service: Any,
        crop_query: str | None,
        location_ids: set[str],
        season: str | None,
    ) -> list[dict[str, Any]]:
        if crop_calendar_service is None:
            return []

        raw_records: list[Any] = []
        if hasattr(crop_calendar_service, "search"):
            raw_records = await _maybe_await(
                crop_calendar_service.search(
                    db=self._executor.db,
                    organization_id=self._organization_id,
                    crop=crop_query,
                    location_ids=sorted(location_ids) if location_ids else None,
                    season=season,
                    limit=100,
                )
            )
        elif hasattr(crop_calendar_service, "list_crop_calendars"):
            raw_records = await _maybe_await(
                crop_calendar_service.list_crop_calendars(
                    self._organization_id,
                    skip=0,
                    limit=100,
                )
            )
        elif hasattr(crop_calendar_service, "list_planting_events"):
            raw_records = await _maybe_await(
                crop_calendar_service.list_planting_events(crop=crop_query)
            )

        events: list[dict[str, Any]] = []
        for record in raw_records or []:
            if not _calendar_matches_scope(
                record,
                crop_query=crop_query,
                location_ids=location_ids,
                season=season,
            ):
                continue
            events.extend(_calendar_to_events(record, default_season=season))

        return events

    # ── Topological Sort ─────────────────────────────────────────────

    def _resolve_execution_order(self, plan: ReevuExecutionPlan) -> list[PlanStep]:
        """Topological sort respecting prerequisites, tie-breaking by DOMAIN_ORDER.

        Uses Kahn's algorithm.  If a cycle is detected (should not happen
        with a well-formed plan), falls back to DOMAIN_ORDER sort.
        """
        steps_by_id: dict[str, PlanStep] = {s.step_id: s for s in plan.steps}
        all_ids = set(steps_by_id.keys())

        # Build in-degree map and adjacency list
        in_degree: dict[str, int] = {sid: 0 for sid in all_ids}
        dependents: dict[str, list[str]] = defaultdict(list)

        for step in plan.steps:
            for prereq_id in step.prerequisites:
                if prereq_id in all_ids:
                    in_degree[step.step_id] += 1
                    dependents[prereq_id].append(step.step_id)

        # Seed the ready queue with steps that have no prerequisites
        ready: list[PlanStep] = sorted(
            [steps_by_id[sid] for sid, deg in in_degree.items() if deg == 0],
            key=lambda s: DOMAIN_ORDER.get(s.domain, 99),
        )

        ordered: list[PlanStep] = []
        while ready:
            # Pop the step with the lowest DOMAIN_ORDER among ready steps
            step = ready.pop(0)
            ordered.append(step)

            for dep_id in dependents.get(step.step_id, []):
                in_degree[dep_id] -= 1
                if in_degree[dep_id] == 0:
                    # Insert in sorted position by DOMAIN_ORDER
                    dep_step = steps_by_id[dep_id]
                    inserted = False
                    for i, r in enumerate(ready):
                        if DOMAIN_ORDER.get(dep_step.domain, 99) < DOMAIN_ORDER.get(r.domain, 99):
                            ready.insert(i, dep_step)
                            inserted = True
                            break
                    if not inserted:
                        ready.append(dep_step)

        # Cycle detection: if we didn't visit all steps, fall back
        if len(ordered) != len(plan.steps):
            logger.warning(
                "Cycle detected in plan %s; falling back to DOMAIN_ORDER sort",
                plan.plan_id,
            )
            return sorted(plan.steps, key=lambda s: DOMAIN_ORDER.get(s.domain, 99))

        return ordered

    # ── Prerequisite Helpers ─────────────────────────────────────────

    @staticmethod
    def _prerequisites_met(step: PlanStep, context: IntermediateResultContext) -> bool:
        """Return True when every prerequisite completed successfully."""
        for prereq_id in step.prerequisites:
            result = context.get(prereq_id)
            if result is None or result.status != "success":
                return False
        return True

    @staticmethod
    def _find_failed_prerequisite(step: PlanStep, context: IntermediateResultContext) -> str | None:
        """Return the step_id of the first failed/missing prerequisite."""
        for prereq_id in step.prerequisites:
            result = context.get(prereq_id)
            if result is None or result.status != "success":
                return prereq_id
        return None

    # ── Over-Limit Outcome ───────────────────────────────────────────

    @staticmethod
    def _over_limit_outcome(plan: ReevuExecutionPlan) -> ExecutionOutcome:
        """Return an outcome that refuses execution because the plan exceeds MAX_STEPS."""
        return ExecutionOutcome(
            step_results=[],
            evidence_refs=[],
            total_duration_ms=0.0,
            steps_completed=0,
            steps_failed=0,
            steps_skipped=0,
            steps_timed_out=0,
            budget_exhausted=True,
        )

    # ── Build Outcome ────────────────────────────────────────────────

    @staticmethod
    def _build_outcome(
        context: IntermediateResultContext,
        wall_start: float,
    ) -> ExecutionOutcome:
        results = context.all_results()
        return ExecutionOutcome(
            step_results=results,
            evidence_refs=context.all_evidence_refs(),
            total_duration_ms=(time.monotonic() - wall_start) * 1000,
            steps_completed=sum(1 for r in results if r.status == "success"),
            steps_failed=sum(1 for r in results if r.status == "failed"),
            steps_skipped=sum(1 for r in results if r.status == "skipped"),
            steps_timed_out=sum(1 for r in results if r.status == "timed_out"),
            budget_exhausted=False,
        )

    # ── Main Loop ────────────────────────────────────────────────────

    async def execute_plan(self, plan: ReevuExecutionPlan) -> ExecutionOutcome:
        """Execute all steps in dependency order with bounded execution."""

        # 1. Guard: step count
        if len(plan.steps) > self.MAX_STEPS:
            return self._over_limit_outcome(plan)

        # 2. Resolve execution order
        ordered_steps = self._resolve_execution_order(plan)

        # 3. Execute steps in order
        context = IntermediateResultContext()
        wall_start = time.monotonic()

        for idx, step in enumerate(ordered_steps):
            # Budget check
            elapsed = time.monotonic() - wall_start
            if elapsed >= self.MAX_TOTAL_SECONDS:
                # Mark this and all remaining steps as timed_out
                for remaining in ordered_steps[idx:]:
                    context.add(StepResult(
                        step_id=remaining.step_id,
                        domain=remaining.domain,
                        status="timed_out",
                        error_category="budget_exhausted",
                        error_message=f"Total budget of {self.MAX_TOTAL_SECONDS}s exhausted",
                    ))
                return ExecutionOutcome(
                    step_results=context.all_results(),
                    evidence_refs=context.all_evidence_refs(),
                    total_duration_ms=(time.monotonic() - wall_start) * 1000,
                    steps_completed=sum(1 for r in context.all_results() if r.status == "success"),
                    steps_failed=sum(1 for r in context.all_results() if r.status == "failed"),
                    steps_skipped=sum(1 for r in context.all_results() if r.status == "skipped"),
                    steps_timed_out=sum(1 for r in context.all_results() if r.status == "timed_out"),
                    budget_exhausted=True,
                )

            # Prerequisite check
            if not self._prerequisites_met(step, context):
                failed_prereq = self._find_failed_prerequisite(step, context)
                context.add(StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="skipped",
                    metadata={"skipped_prerequisite": failed_prereq},
                ))
                continue

            # Execute with per-step timeout
            handler = self._domain_handler(step.domain)
            if handler is None:
                context.add(StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    error_category="unknown_domain",
                    error_message=f"No handler for domain '{step.domain}'",
                ))
                continue

            step_start = time.monotonic()
            try:
                result = await asyncio.wait_for(
                    handler(step, context),
                    timeout=self.MAX_STEP_SECONDS,
                )
                result.duration_ms = (time.monotonic() - step_start) * 1000
            except asyncio.TimeoutError:
                result = StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="timed_out",
                    duration_ms=(time.monotonic() - step_start) * 1000,
                    error_category="step_timeout",
                    error_message=f"Step exceeded {self.MAX_STEP_SECONDS}s timeout",
                )
            except Exception as exc:
                result = StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    duration_ms=(time.monotonic() - step_start) * 1000,
                    error_category="execution_error",
                    error_message=str(exc),
                )

            context.add(result)

        # 4. Build outcome
        return self._build_outcome(context, wall_start)


    # ── Query Narrowing ──────────────────────────────────────────────

    def _narrow_from_trials(
        self, context: IntermediateResultContext, prereq_step_id: str,
    ) -> dict[str, Any]:
        """Extract trial IDs and location info from a completed trials step."""
        result = context.get(prereq_step_id)
        if result is None or result.status != "success":
            return {}

        narrowing: dict[str, Any] = {}

        if result.entity_ids:
            narrowing["trial_ids"] = result.entity_ids

        resolved_study_ids = result.metadata.get("resolved_study_ids", [])
        if resolved_study_ids:
            narrowing["study_ids"] = resolved_study_ids

        location_query = result.metadata.get("inferred_location_query")
        if location_query:
            narrowing["location_query"] = location_query

        location_records = result.records.get("locations", [])
        if location_records:
            narrowing["location_records"] = location_records

        return narrowing

    def _narrow_from_breeding(
        self, context: IntermediateResultContext, prereq_step_id: str,
    ) -> dict[str, Any]:
        """Extract germplasm IDs and trait names from a completed breeding step."""
        result = context.get(prereq_step_id)
        if result is None or result.status != "success":
            return {}

        narrowing: dict[str, Any] = {}

        if result.entity_ids:
            narrowing["germplasm_ids"] = result.entity_ids

        traits = result.records.get("traits", [])
        trait_names = [
            t.get("name") or t.get("trait_name")
            for t in traits
            if t.get("name") or t.get("trait_name")
        ]
        if trait_names:
            narrowing["trait_names"] = trait_names

        return narrowing

    def _narrow_from_phenotyping(
        self, context: IntermediateResultContext, prereq_step_id: str,
    ) -> dict[str, Any]:
        """Extract trait IDs and prefetched observations from a phenotyping step."""
        result = context.get(prereq_step_id)
        if result is None or result.status != "success":
            return {}

        narrowing: dict[str, Any] = {}

        if result.entity_ids:
            narrowing["trait_ids"] = result.entity_ids

        observations = result.records.get("observations", [])
        if observations:
            narrowing["phenotyping_observations"] = observations

        resolved_study_ids = result.metadata.get("resolved_study_ids", [])
        if resolved_study_ids:
            narrowing["study_ids"] = resolved_study_ids

        return narrowing

    def _narrow_from_field(
        self, context: IntermediateResultContext, prereq_step_id: str,
    ) -> dict[str, Any]:
        """Extract location records with coordinates from a field step."""
        result = context.get(prereq_step_id)
        if result is None or result.status != "success":
            return {}

        location_records = [
            location
            for location in result.records.get("locations", [])
            if isinstance(location, dict)
        ]
        if not location_records:
            return {}

        return {"location_records": location_records}

    def _get_narrowing_for_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> dict[str, Any]:
        """Get narrowing data from all prerequisites of a step."""
        narrowing: dict[str, Any] = {}
        for prereq_id in step.prerequisites:
            prereq_result = context.get(prereq_id)
            if prereq_result is None or prereq_result.status != "success":
                continue
            if prereq_result.domain in ("trials",):
                narrowing.update(self._narrow_from_trials(context, prereq_id))
            elif prereq_result.domain in ("breeding",):
                narrowing.update(self._narrow_from_breeding(context, prereq_id))
            elif prereq_result.domain in ("phenotyping",):
                narrowing.update(self._narrow_from_phenotyping(context, prereq_id))
            elif prereq_result.domain in ("field",):
                narrowing.update(self._narrow_from_field(context, prereq_id))
        return narrowing


    # ── Per-Domain Handlers ──────────────────────────────────────────

    async def _execute_trials_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> StepResult:
        """Execute a trials domain step."""
        try:
            if not self._executor.trial_search_service:
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    error_category="missing_service",
                    error_message="trial_search_service is not available",
                    metadata={"missing_runtime_service": "trial_search_service"},
                )

            crop_query = self._params.get("crop")
            location_query = self._params.get("location")
            program_query = self._params.get("program")
            trait_query = self._params.get("trait")

            trial_results = await self._executor.trial_search_service.search(
                db=self._executor.db,
                organization_id=self._organization_id,
                query=None,
                crop=crop_query,
                location=location_query,
                program=program_query,
                limit=20,
            )

            # Extract trial IDs for downstream narrowing
            trial_ids = [str(t.get("id", "")).strip() for t in trial_results if t.get("id")]

            # Infer location from trial results
            inferred_location_query: str | None = None
            if not location_query:
                for trial in trial_results:
                    trial_location = trial.get("location")
                    if isinstance(trial_location, dict):
                        candidate = trial_location.get("name")
                    else:
                        candidate = trial_location
                    if isinstance(candidate, str) and candidate.strip():
                        inferred_location_query = candidate.strip()
                        break

            # Resolve locations
            location_results: list[dict[str, Any]] = []
            resolved_location_query = location_query or inferred_location_query
            if resolved_location_query and self._executor.location_search_service:
                location_results = await self._executor.location_search_service.search(
                    db=self._executor.db,
                    organization_id=self._organization_id,
                    query=resolved_location_query,
                    limit=20,
                )

            # Trial-phenotype-environment mode: fetch trial details and observations
            observations: list[dict[str, Any]] = []
            resolved_study_ids: list[str] = []
            requested_domains = set(self._params.get("_requested_domains", []))
            germplasm_query = self._params.get("germplasm")

            trial_phenotype_environment_mode = (
                {"breeding", "trials", "weather"}.issubset(requested_domains)
                and germplasm_query is None
                and any(
                    token in self._original_query.lower()
                    for token in (
                        "performance", "yield", "observation", "phenotype",
                        "environment", "field data", "plot data",
                    )
                )
            )

            if trial_phenotype_environment_mode and hasattr(self._executor.trial_search_service, "get_by_id"):
                observation_service = self._observation_search_service()
                observation_ids_seen: set[str] = set()
                for trial in trial_results[:5]:
                    trial_detail = await self._executor.trial_search_service.get_by_id(
                        self._executor.db,
                        self._organization_id,
                        trial.get("id"),
                    )
                    # Infer location from trial detail
                    trial_additional_info = (
                        (trial_detail or {}).get("additional_info")
                        if isinstance(trial_detail, dict)
                        else None
                    )
                    if isinstance(trial_additional_info, dict) and not inferred_location_query:
                        for key in ("location_context", "location_name", "location_label"):
                            candidate = trial_additional_info.get(key)
                            if isinstance(candidate, str) and candidate.strip():
                                inferred_location_query = candidate.strip()
                                break

                    trial_location = (
                        (trial_detail or {}).get("location")
                        if isinstance(trial_detail, dict)
                        else None
                    )
                    if isinstance(trial_location, dict) and not inferred_location_query:
                        candidate = trial_location.get("name")
                        if isinstance(candidate, str) and candidate.strip():
                            inferred_location_query = candidate.strip()

                    for study in (trial_detail or {}).get("studies", [])[:5]:
                        study_id = study.get("id")
                        if study_id is None:
                            continue
                        study_id_ref = str(study_id).strip()
                        if study_id_ref and study_id_ref not in resolved_study_ids:
                            resolved_study_ids.append(study_id_ref)
                        study_observations = await observation_service.search(
                            db=self._executor.db,
                            organization_id=self._organization_id,
                            study_id=int(study_id),
                            trait=trait_query,
                            limit=25,
                        )
                        for obs in study_observations:
                            obs_ref = obs.get("observation_db_id") or str(obs.get("id") or "")
                            if not obs_ref or obs_ref in observation_ids_seen:
                                continue
                            observation_ids_seen.add(obs_ref)
                            observations.append(obs)

            records: dict[str, Any] = {
                "trials": trial_results,
                "locations": location_results,
            }
            if observations:
                records["observations"] = observations

            metadata: dict[str, Any] = {}
            if inferred_location_query:
                metadata["inferred_location_query"] = inferred_location_query
            if resolved_study_ids:
                metadata["resolved_study_ids"] = resolved_study_ids

            evidence_refs = [
                EvidenceRef(
                    source_type="database",
                    entity_id=f"step:{step.step_id}:trial_search",
                    query_or_method="trial_search_service.search",
                ),
            ]

            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records=records,
                entity_ids=trial_ids,
                evidence_refs=evidence_refs,
                metadata=metadata,
            )

        except Exception as exc:
            logger.error("Trials step %s failed: %s", step.step_id, exc)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="failed",
                error_category="execution_error",
                error_message=str(exc),
            )

    async def _execute_field_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> StepResult:
        """Execute a field operations domain step."""
        try:
            narrowing = self._get_narrowing_for_step(step, context)
            narrowed_locations = [
                location
                for location in narrowing.get("location_records", [])
                if isinstance(location, dict)
            ]

            location_service = getattr(self._executor, "location_search_service", None)
            if location_service is None and not narrowed_locations:
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    error_category="missing_service",
                    error_message="location_search_service is not available",
                    metadata={"missing_runtime_service": "location_search_service"},
                )

            location_query = _as_nonempty_string(
                self._params.get("location")
                or self._params.get("location_query")
                or self._params.get("query")
            )
            crop_query = _as_nonempty_string(self._params.get("crop"))
            season = _as_nonempty_string(self._params.get("season") or self._params.get("temporal"))

            query_mode = "trials_narrowed" if narrowed_locations else "location_search"
            if narrowed_locations:
                locations = narrowed_locations
            else:
                locations = await location_service.search(
                    db=self._executor.db,
                    organization_id=self._organization_id,
                    query=location_query or self._original_query,
                    limit=50,
                )

            location_ids = {
                location_id
                for location in locations
                if isinstance(location, dict) and (location_id := _location_id(location))
            }
            field_layouts = _extract_field_layouts(
                [location for location in locations if isinstance(location, dict)]
            )

            crop_calendar_events: list[dict[str, Any]] = []
            crop_calendar_service = self._crop_calendar_service()
            crop_calendar_warning: str | None = None
            if crop_calendar_service is not None:
                try:
                    crop_calendar_events = await self._fetch_crop_calendar_events(
                        crop_calendar_service=crop_calendar_service,
                        crop_query=crop_query,
                        location_ids=location_ids,
                        season=season,
                    )
                except Exception as exc:
                    crop_calendar_warning = str(exc)
                    logger.warning(
                        "Field step %s continuing without crop calendar events: %s",
                        step.step_id,
                        exc,
                    )

            season_info = {
                "season": season,
                "crop": crop_query,
                "location_count": len(locations),
                "crop_calendar_event_count": len(crop_calendar_events),
            }

            evidence_refs = [
                EvidenceRef(
                    source_type="database",
                    entity_id=f"step:{step.step_id}:location_search",
                    query_or_method=(
                        "trials.location_records"
                        if narrowed_locations
                        else "location_search_service.search"
                    ),
                )
            ]
            if crop_calendar_service is not None:
                evidence_refs.append(
                    EvidenceRef(
                        source_type="database",
                        entity_id=f"step:{step.step_id}:crop_calendar",
                        query_or_method=(
                            "crop_calendar_service.search"
                            if hasattr(crop_calendar_service, "search")
                            else "crop_calendar_service.list_crop_calendars"
                        ),
                    )
                )

            metadata = {
                "narrowing_applied": bool(narrowed_locations),
                "narrowing_source": "trials" if narrowed_locations else None,
                "query_mode": query_mode,
                "resolved_location_ids": sorted(location_ids),
                "crop_calendar_service_available": crop_calendar_service is not None,
            }
            if crop_calendar_warning:
                metadata["crop_calendar_warning"] = crop_calendar_warning

            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={
                    "locations": locations,
                    "field_layouts": field_layouts,
                    "crop_calendar_events": crop_calendar_events,
                    "season_info": season_info,
                },
                entity_ids=sorted(location_ids),
                evidence_refs=evidence_refs,
                metadata=metadata,
            )

        except Exception as exc:
            logger.error("Field step %s failed: %s", step.step_id, exc)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="failed",
                error_category="execution_error",
                error_message=str(exc),
            )


    def _query_suggests_distribution(self) -> bool:
        query_lower = self._original_query.lower()
        return any(keyword in query_lower for keyword in self._DISTRIBUTION_KEYWORDS)

    @staticmethod
    def _compute_trait_distribution(
        values: list[float],
        n_bins: int = 10,
    ) -> dict[str, Any] | None:
        """Compute lightweight distribution data for numeric trait values."""
        numeric_values = [float(value) for value in values if math.isfinite(float(value))]
        if not numeric_values:
            return None

        sorted_values = sorted(numeric_values)
        n = len(sorted_values)
        min_value = sorted_values[0]
        max_value = sorted_values[-1]
        median = statistics.median(sorted_values)
        mean = statistics.fmean(sorted_values)

        if n >= 2:
            q1, _, q3 = statistics.quantiles(sorted_values, n=4, method="inclusive")
        else:
            q1 = q3 = median

        if math.isclose(mean, median, rel_tol=1e-12, abs_tol=1e-12):
            skewness_indicator = "symmetric"
        elif mean > median:
            skewness_indicator = "right"
        else:
            skewness_indicator = "left"

        if n_bins < 1:
            n_bins = 1

        if math.isclose(min_value, max_value, rel_tol=1e-12, abs_tol=1e-12):
            half_width = 0.5 if min_value == 0 else max(abs(min_value) * 0.05, 0.5)
            start = min_value - half_width
            width = (2 * half_width) / n_bins
        else:
            start = min_value
            width = (max_value - min_value) / n_bins

        bin_edges = [start + i * width for i in range(n_bins + 1)]
        bin_counts = [0 for _ in range(n_bins)]
        for value in sorted_values:
            if math.isclose(value, bin_edges[-1], rel_tol=1e-12, abs_tol=1e-12):
                bin_index = n_bins - 1
            else:
                bin_index = int((value - start) / width) if width else 0
                bin_index = min(max(bin_index, 0), n_bins - 1)
            bin_counts[bin_index] += 1

        return {
            "bin_edges": bin_edges,
            "bin_counts": bin_counts,
            "quartiles": {"q1": q1, "median": median, "q3": q3},
            "skewness_indicator": skewness_indicator,
            "n": n,
            "min": min_value,
            "max": max_value,
        }

    async def _resolve_study_ids_from_trials(self, trial_ids: list[Any]) -> list[str]:
        if not trial_ids or not getattr(self._executor, "trial_search_service", None):
            return []
        if not hasattr(self._executor.trial_search_service, "get_by_id"):
            return []

        resolved_study_ids: list[str] = []
        for trial_id in trial_ids[:5]:
            trial_detail = await self._executor.trial_search_service.get_by_id(
                self._executor.db,
                self._organization_id,
                trial_id,
            )
            for study in (trial_detail or {}).get("studies", [])[:10]:
                study_id = _as_nonempty_string(study.get("id")) if isinstance(study, dict) else None
                if study_id and study_id not in resolved_study_ids:
                    resolved_study_ids.append(study_id)
        return resolved_study_ids

    async def _execute_phenotyping_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> StepResult:
        """Execute a phenotyping domain step."""
        try:
            observation_service = self._observation_search_service()
            if observation_service is None:
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    error_category="missing_service",
                    error_message="observation_search_service is not available",
                    metadata={"missing_runtime_service": "observation_search_service"},
                )

            trait_query = _as_nonempty_string(self._params.get("trait"))
            crop_query = _as_nonempty_string(self._params.get("crop"))
            season = _as_nonempty_string(self._params.get("season") or self._params.get("temporal"))
            date_from = _as_nonempty_string(self._params.get("date_from"))
            date_to = _as_nonempty_string(self._params.get("date_to"))

            if season and not (date_from or date_to):
                year_match = re.search(r"\b(19|20)\d{2}\b", season)
                if year_match:
                    year = year_match.group(0)
                    date_from = f"{year}-01-01"
                    date_to = f"{year}-12-31"

            narrowing = self._get_narrowing_for_step(step, context)
            study_ids = [
                str(value).strip()
                for value in (
                    _as_list(self._params.get("study_id"))
                    + _as_list(self._params.get("study_ids"))
                    + _as_list(narrowing.get("study_ids"))
                )
                if str(value).strip()
            ]
            germplasm_ids = [
                str(value).strip()
                for value in (
                    _as_list(self._params.get("germplasm_id"))
                    + _as_list(self._params.get("germplasm_ids"))
                    + _as_list(narrowing.get("germplasm_ids"))
                )
                if str(value).strip()
            ]
            if not study_ids and narrowing.get("trial_ids"):
                study_ids = await self._resolve_study_ids_from_trials(narrowing["trial_ids"])

            narrowing_sources: list[str] = []
            if study_ids:
                narrowing_sources.append("trials")
            if germplasm_ids:
                narrowing_sources.append("breeding")

            observations: list[dict[str, Any]] = []
            query_mode = "trait_first"

            if study_ids:
                query_mode = "study_scoped"
                for study_id in study_ids[:10]:
                    int_study_id = _coerce_int(study_id)
                    if int_study_id is None:
                        logger.debug("Skipping non-integer study_id in phenotyping step: %s", study_id)
                        continue
                    observations.extend(
                        await observation_service.search(
                            db=self._executor.db,
                            organization_id=self._organization_id,
                            trait=trait_query,
                            study_id=int_study_id,
                            date_from=date_from,
                            date_to=date_to,
                            limit=100,
                        )
                    )
            elif germplasm_ids:
                query_mode = "germplasm_scoped"
                for germplasm_id in germplasm_ids[:10]:
                    int_germplasm_id = _coerce_int(germplasm_id)
                    if int_germplasm_id is None:
                        logger.debug(
                            "Skipping non-integer germplasm_id in phenotyping step: %s",
                            germplasm_id,
                        )
                        continue
                    observations.extend(
                        await observation_service.search(
                            db=self._executor.db,
                            organization_id=self._organization_id,
                            trait=trait_query,
                            germplasm_id=int_germplasm_id,
                            date_from=date_from,
                            date_to=date_to,
                            limit=100,
                        )
                    )
            else:
                observations = await observation_service.search(
                    db=self._executor.db,
                    organization_id=self._organization_id,
                    query=trait_query or self._original_query,
                    trait=trait_query,
                    date_from=date_from,
                    date_to=date_to,
                    limit=100,
                )

            observations = _dedupe_observations(observations)

            trait_results: list[dict[str, Any]] = []
            trait_service = self._trait_search_service()
            trait_metadata_warning: str | None = None
            if trait_query:
                if trait_service is None:
                    trait_metadata_warning = "trait_search_service is unavailable"
                    logger.warning(
                        "Phenotyping step %s continuing without trait metadata: %s",
                        step.step_id,
                        trait_metadata_warning,
                    )
                else:
                    trait_results = await trait_service.search(
                        db=self._executor.db,
                        organization_id=self._organization_id,
                        query=trait_query,
                        crop=crop_query,
                        limit=20,
                    )

            numeric_values = [
                parsed
                for observation in observations
                if (parsed := _parse_observation_value(observation)) is not None
            ]
            distribution = (
                self._compute_trait_distribution(numeric_values)
                if self._query_suggests_distribution() and len(numeric_values) >= 2
                else None
            )

            trait_ids = [
                str(trait.get("id")).strip()
                for trait in trait_results
                if isinstance(trait, dict) and trait.get("id")
            ]
            if not trait_ids:
                trait_ids = [
                    trait_id
                    for observation in observations
                    if (trait_id := _observation_trait_id(observation))
                ]
            trait_ids = list(dict.fromkeys(trait_ids))

            evidence_refs = [
                EvidenceRef(
                    source_type="database",
                    entity_id=f"step:{step.step_id}:observation_search",
                    query_or_method="observation_search_service.search",
                ),
            ]
            if trait_query and trait_service is not None:
                evidence_refs.append(
                    EvidenceRef(
                        source_type="database",
                        entity_id=f"step:{step.step_id}:trait_search",
                        query_or_method="trait_search_service.search",
                    )
                )

            observed_study_ids: list[str] = []
            for observation in observations:
                observed_study_id = _observation_study_id(observation)
                if observed_study_id:
                    observed_study_ids.append(observed_study_id)
            resolved_study_ids = list(
                dict.fromkeys(study_id for study_id in study_ids + observed_study_ids if study_id)
            )

            metadata = {
                "narrowing_applied": bool(narrowing_sources),
                "narrowing_source": ",".join(narrowing_sources) if narrowing_sources else None,
                "resolved_study_ids": resolved_study_ids,
                "query_mode": query_mode,
            }
            if trait_metadata_warning:
                metadata["trait_metadata_warning"] = trait_metadata_warning

            records: dict[str, Any] = {
                "observations": observations,
                "traits": trait_results,
                "summary_stats": _summarize_observations(observations),
                "distribution": distribution,
                "observation_count": len(observations),
            }

            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records=records,
                entity_ids=trait_ids,
                evidence_refs=evidence_refs,
                metadata=metadata,
            )

        except Exception as exc:
            logger.error("Phenotyping step %s failed: %s", step.step_id, exc)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="failed",
                error_category="execution_error",
                error_message=str(exc),
            )


    async def _execute_breeding_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> StepResult:
        """Execute a breeding domain step."""
        try:
            germplasm_query = self._params.get("germplasm")
            trait_query = self._params.get("trait")
            crop_query = self._params.get("crop")
            seedlot_query = self._params.get("seedlot")

            narrowing = self._get_narrowing_for_step(step, context)
            observation_service = self._observation_search_service()
            seedlot_service = self._seedlot_search_service()
            trait_service = self._trait_search_service()

            germplasm_results: list[dict[str, Any]] = []
            all_observations: list[dict[str, Any]] = []
            trait_results: list[dict[str, Any]] = []
            seedlot_results: list[dict[str, Any]] = []

            # Only switch into trial-scoped observation lookup when we do not
            # have a germplasm service path. Queries with an explicit or
            # resolvable germplasm scope should keep the established
            # germplasm-first path so the response contract stays aligned with
            # existing cross-domain expectations and tests.
            trial_ids = narrowing.get("trial_ids", [])
            use_trial_scoped_observations = bool(trial_ids) and not (
                germplasm_query or self._executor.germplasm_search_service
            )
            if use_trial_scoped_observations:
                # Observations are already fetched in the trials step when
                # trial_phenotype_environment_mode is active.  For the
                # breeding step we fetch observations per trial study.
                for tid in trial_ids[:5]:
                    if hasattr(self._executor, "trial_search_service") and self._executor.trial_search_service:
                        trial_detail = None
                        if hasattr(self._executor.trial_search_service, "get_by_id"):
                            trial_detail = await self._executor.trial_search_service.get_by_id(
                                self._executor.db,
                                self._organization_id,
                                tid,
                            )
                        for study in (trial_detail or {}).get("studies", [])[:5]:
                            study_id = study.get("id")
                            if study_id is None:
                                continue
                            obs = await observation_service.search(
                                db=self._executor.db,
                                organization_id=self._organization_id,
                                study_id=int(study_id),
                                trait=trait_query,
                                limit=25,
                            )
                            all_observations.extend(obs)
            else:
                # Standard germplasm-first search
                if not self._executor.germplasm_search_service:
                    return StepResult(
                        step_id=step.step_id,
                        domain=step.domain,
                        status="failed",
                        error_category="missing_service",
                        error_message="germplasm_search_service is not available",
                        metadata={
                            **({"narrowing_skipped": True} if not narrowing else {}),
                            "missing_runtime_service": "germplasm_search_service",
                        },
                    )

                germplasm_results = await self._executor.germplasm_search_service.search(
                    db=self._executor.db,
                    organization_id=self._organization_id,
                    query=germplasm_query,
                    trait=trait_query,
                    limit=20,
                )

                # Fetch observations per germplasm
                for germ in germplasm_results[:5]:
                    observations = await observation_service.get_by_germplasm(
                        db=self._executor.db,
                        organization_id=self._organization_id,
                        germplasm_id=int(germ["id"]),
                        limit=10,
                    )
                    if observations:
                        all_observations.extend(observations)

            # Fetch traits
            if trait_query:
                trait_results = await trait_service.search(
                    db=self._executor.db,
                    organization_id=self._organization_id,
                    query=trait_query,
                    crop=crop_query,
                    limit=20,
                )

            # Fetch seedlots
            if seedlot_query or germplasm_query:
                seedlot_results = await seedlot_service.search(
                    db=self._executor.db,
                    organization_id=self._organization_id,
                    query=seedlot_query,
                    limit=20,
                )

            germplasm_ids = [str(g.get("id", "")).strip() for g in germplasm_results if g.get("id")]

            records: dict[str, Any] = {
                "germplasm": germplasm_results,
                "observations": all_observations,
                "traits": trait_results,
                "seedlots": seedlot_results,
            }

            metadata: dict[str, Any] = {}
            if step.prerequisites:
                metadata["narrowing_applied"] = bool(narrowing)
            if step.prerequisites and not narrowing:
                metadata["narrowing_skipped"] = True

            evidence_refs = [
                EvidenceRef(
                    source_type="database",
                    entity_id=f"step:{step.step_id}:breeding_search",
                    query_or_method="germplasm_search_service.search",
                ),
            ]

            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records=records,
                entity_ids=germplasm_ids,
                evidence_refs=evidence_refs,
                metadata=metadata,
            )

        except Exception as exc:
            logger.error("Breeding step %s failed: %s", step.step_id, exc)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="failed",
                error_category="execution_error",
                error_message=str(exc),
            )


    async def _execute_seed_ops_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> StepResult:
        """Execute a seed operations domain step."""
        try:
            seedlot_service = self._seedlot_search_service()
            if seedlot_service is None:
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    error_category="missing_service",
                    error_message="seedlot_search_service is not available",
                    metadata={"missing_runtime_service": "seedlot_search_service"},
                )

            narrowing = self._get_narrowing_for_step(step, context)
            germplasm_query = _as_nonempty_string(self._params.get("germplasm"))
            query = (
                _as_nonempty_string(self._params.get("query"))
                or _as_nonempty_string(self._params.get("q"))
                or _as_nonempty_string(self._params.get("seedlot"))
                or germplasm_query
            )
            location_id = _coerce_int(self._params.get("location_id"))
            if location_id is None:
                location_id = _coerce_int(self._params.get("location"))

            germplasm_ids = [
                str(value).strip()
                for value in (
                    _as_list(self._params.get("germplasm_id"))
                    + _as_list(self._params.get("germplasm_ids"))
                    + _as_list(narrowing.get("germplasm_ids"))
                )
                if str(value).strip()
            ]

            seedlots: list[dict[str, Any]] = []
            query_mode = "query"
            if germplasm_ids:
                query_mode = "germplasm_scoped"
                for germplasm_id in germplasm_ids[:10]:
                    int_germplasm_id = _coerce_int(germplasm_id)
                    if int_germplasm_id is None:
                        logger.debug(
                            "Skipping non-integer germplasm_id in seed ops step: %s",
                            germplasm_id,
                        )
                        continue
                    seedlots.extend(
                        await seedlot_service.search(
                            db=self._executor.db,
                            organization_id=self._organization_id,
                            germplasm_id=int_germplasm_id,
                            limit=100,
                        )
                    )
            else:
                seedlots = await seedlot_service.search(
                    db=self._executor.db,
                    organization_id=self._organization_id,
                    query=query,
                    location_id=location_id,
                    limit=100,
                )

            deduped_seedlots: list[dict[str, Any]] = []
            seen_seedlot_ids: set[str] = set()
            for seedlot in seedlots:
                seedlot_identifier = _seedlot_id(seedlot)
                if seedlot_identifier and seedlot_identifier in seen_seedlot_ids:
                    continue
                if seedlot_identifier:
                    seen_seedlot_ids.add(seedlot_identifier)
                deduped_seedlots.append(seedlot)
            seedlots = deduped_seedlots

            inventory_summary = _build_seed_inventory_summary(seedlots)

            evidence_refs = [
                EvidenceRef(
                    source_type="database",
                    entity_id=f"step:{step.step_id}:seedlot_search",
                    query_or_method="seedlot_search_service.search",
                )
            ]

            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={
                    "seedlots": seedlots,
                    "inventory_summary": inventory_summary,
                    "availability": inventory_summary["availability"],
                },
                entity_ids=[seedlot_id for seedlot in seedlots if (seedlot_id := _seedlot_id(seedlot))],
                evidence_refs=evidence_refs,
                metadata={
                    "narrowing_applied": bool(germplasm_ids and narrowing),
                    "narrowing_source": "breeding" if narrowing.get("germplasm_ids") else None,
                    "query_mode": query_mode,
                    "resolved_germplasm_ids": list(dict.fromkeys(germplasm_ids)),
                },
            )

        except Exception as exc:
            logger.error("Seed operations step %s failed: %s", step.step_id, exc)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="failed",
                error_category="execution_error",
                error_message=str(exc),
            )


    async def _execute_weather_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> StepResult:
        """Execute a weather domain step."""
        try:
            location_query = self._params.get("location")
            crop_query = self._params.get("crop")

            narrowing = self._get_narrowing_for_step(step, context)

            # Resolve location from narrowing or original params
            narrowed_location_query = narrowing.get("location_query")
            location_records = narrowing.get("location_records", [])
            resolved_location_query = location_query or narrowed_location_query

            metadata: dict[str, Any] = {}
            if step.prerequisites:
                metadata["narrowing_applied"] = bool(narrowing)
            if step.prerequisites and not narrowing:
                metadata["narrowing_skipped"] = True

            if not resolved_location_query and not location_records:
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    error_category="weather_resolution_error",
                    error_message="no location query was provided",
                    metadata=metadata,
                )

            if not self._executor.weather_service:
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    error_category="missing_service",
                    error_message="weather_service is not available",
                    metadata={**metadata, "missing_runtime_service": "weather_service"},
                )

            # Resolve location coordinates
            resolved_weather_location: dict[str, Any] | None = None

            # First try location_records from narrowing (already resolved)
            if location_records:
                resolved_weather_location = next(
                    (
                        loc
                        for loc in location_records
                        if loc.get("latitude") is not None and loc.get("longitude") is not None
                    ),
                    None,
                )

            # If no coordinates from narrowing, search locations
            if resolved_weather_location is None and resolved_location_query and self._executor.location_search_service:
                search_results = await self._executor.location_search_service.search(
                    db=self._executor.db,
                    organization_id=self._organization_id,
                    query=resolved_location_query,
                    limit=20,
                )
                resolved_weather_location = next(
                    (
                        loc
                        for loc in search_results
                        if loc.get("latitude") is not None and loc.get("longitude") is not None
                    ),
                    None,
                )

            if resolved_weather_location is None:
                error_msg = (
                    "resolved location has no stored coordinates"
                    if location_records or resolved_location_query
                    else "no matching location was found"
                )
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    error_category="weather_resolution_error",
                    error_message=error_msg,
                    metadata={**metadata, "location_query": resolved_location_query},
                )

            # Call weather service
            try:
                forecast = await self._executor.weather_service.get_forecast(
                    location_id=str(
                        resolved_weather_location.get("id")
                        or resolved_weather_location.get("location_db_id")
                        or resolved_location_query
                    ),
                    location_name=resolved_weather_location.get("name") or resolved_location_query or "",
                    days=7,
                    crop=crop_query or "wheat",
                    lat=resolved_weather_location.get("latitude"),
                    lon=resolved_weather_location.get("longitude"),
                    allow_generated_fallback=False,
                )
            except WeatherForecastUnavailableError as exc:
                logger.warning(
                    "REEVU weather enrichment unavailable for %s: %s",
                    resolved_location_query,
                    exc,
                )
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    error_category="weather_resolution_error",
                    error_message=str(exc) or "weather provider request failed",
                    metadata=metadata,
                )

            weather_data = {
                "location": resolved_weather_location.get("name") or resolved_location_query,
                "source": "live_provider",
                "summary": self._executor.weather_service.get_veena_summary(forecast),
                "alerts": list(forecast.alerts),
                "impacts_count": len(getattr(forecast, "impacts", [])),
            }

            evidence_refs = [
                EvidenceRef(
                    source_type="function",
                    entity_id=f"step:{step.step_id}:weather_forecast",
                    query_or_method="weather_service.get_forecast",
                ),
            ]

            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={"weather": weather_data},
                entity_ids=[str(resolved_weather_location.get("id", ""))],
                evidence_refs=evidence_refs,
                metadata=metadata,
            )

        except Exception as exc:
            logger.error("Weather step %s failed: %s", step.step_id, exc)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="failed",
                error_category="execution_error",
                error_message=str(exc),
            )


    async def _execute_genomics_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> StepResult:
        """Execute a genomics domain step."""
        try:
            trait_query = self._params.get("trait")
            narrowing = self._get_narrowing_for_step(step, context)

            metadata: dict[str, Any] = {}
            if step.prerequisites:
                metadata["narrowing_applied"] = bool(narrowing)
            if step.prerequisites and not narrowing:
                metadata["narrowing_skipped"] = True

            # Resolve trait names from narrowing (breeding step) or params
            narrowed_trait_names = narrowing.get("trait_names", [])

            qtl_service = self._qtl_mapping_service_factory()()

            available_traits = await qtl_service.get_traits(
                self._executor.db, self._organization_id,
            )

            # Resolve the requested trait against available traits
            from app.modules.ai.services.tool_query_helpers import _resolve_trait_query

            # Explicit user trait requests stay authoritative; only fall back
            # to narrowed breeding traits when the query itself did not provide
            # a resolvable trait.
            resolved_trait: str | None = None
            matches: list[str] = []

            if trait_query:
                resolved_trait, matches = _resolve_trait_query(
                    available_traits=available_traits,
                    requested_trait=trait_query,
                )

            if not resolved_trait and narrowed_trait_names:
                for candidate in narrowed_trait_names:
                    resolved_trait, matches = _resolve_trait_query(
                        available_traits=available_traits,
                        requested_trait=candidate,
                    )
                    if resolved_trait:
                        break

            genomics_data: dict[str, Any] | None = None
            if resolved_trait:
                qtls = await qtl_service.list_qtls(
                    self._executor.db,
                    self._organization_id,
                    trait=resolved_trait,
                )
                associations = await qtl_service.get_gwas_results(
                    self._executor.db,
                    self._organization_id,
                    trait=resolved_trait,
                )
                if qtls or associations:
                    genomics_data = {
                        "trait": resolved_trait,
                        "qtls": qtls,
                        "associations": associations,
                        "summary": {
                            "qtl_count": len(qtls),
                            "association_count": len(associations),
                            "matched_trait_candidates": matches,
                        },
                    }

            evidence_refs = [
                EvidenceRef(
                    source_type="database",
                    entity_id=f"step:{step.step_id}:genomics_search",
                    query_or_method="QTLMappingService.list_qtls",
                ),
            ]

            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={"genomics": genomics_data},
                entity_ids=narrowed_trait_names or ([resolved_trait] if resolved_trait else []),
                evidence_refs=evidence_refs,
                metadata=metadata,
            )

        except Exception as exc:
            logger.error("Genomics step %s failed: %s", step.step_id, exc)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="failed",
                error_category="execution_error",
                error_message=str(exc),
            )

    async def _execute_protocols_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> StepResult:
        """Execute a protocols domain step."""
        try:
            if not self._executor.protocol_search_service:
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="failed",
                    error_category="missing_service",
                    error_message="protocol_search_service is not available",
                    metadata={"missing_runtime_service": "protocol_search_service"},
                )

            crop_query = self._params.get("crop")

            protocol_records = await self._executor.protocol_search_service.get_protocols(
                db=self._executor.db,
                organization_id=self._organization_id,
                crop=crop_query,
            )

            serialized_protocols: list[dict[str, Any]] = []
            for record in protocol_records:
                serialized = (
                    record
                    if isinstance(record, dict)
                    else {
                        "id": str(getattr(record, "id", "")).strip(),
                        "name": getattr(record, "name", None),
                        "crop": getattr(record, "crop", None),
                        "status": getattr(record, "status", None),
                        "photoperiod": getattr(record, "photoperiod", None),
                        "days_to_flower": getattr(record, "days_to_flower", None),
                        "generations_per_year": getattr(record, "generations_per_year", None),
                    }
                )
                if serialized.get("id"):
                    serialized_protocols.append(serialized)

            protocol_ids = [str(p.get("id", "")).strip() for p in serialized_protocols if p.get("id")]

            evidence_refs = [
                EvidenceRef(
                    source_type="database",
                    entity_id=f"step:{step.step_id}:protocol_search",
                    query_or_method="protocol_search_service.get_protocols",
                ),
            ]

            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={"protocols": serialized_protocols},
                entity_ids=protocol_ids,
                evidence_refs=evidence_refs,
            )

        except Exception as exc:
            logger.error("Protocols step %s failed: %s", step.step_id, exc)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="failed",
                error_category="execution_error",
                error_message=str(exc),
            )

    def _query_suggests_ranking(self) -> bool:
        query_lower = self._original_query.lower()
        return any(keyword in query_lower for keyword in self._RANKING_KEYWORDS)

    def _query_suggests_comparison(self) -> bool:
        query_lower = self._original_query.lower()
        return any(keyword in query_lower for keyword in self._COMPARISON_KEYWORDS)

    def _ranking_direction(self) -> Literal["desc", "asc"]:
        query_lower = self._original_query.lower()
        if any(keyword in query_lower for keyword in ("lowest", "worst", "bottom")):
            return "asc"
        return "desc"

    @staticmethod
    def _has_trial_data(context: IntermediateResultContext) -> bool:
        return any(
            result.domain == "trials"
            and result.status == "success"
            for result in context.all_results()
        )

    def _select_analytics_trait(self, observations: list[dict[str, Any]]) -> str | None:
        requested_trait = self._params.get("trait")
        if isinstance(requested_trait, str) and requested_trait.strip():
            return requested_trait.strip()

        trait_counts: dict[str, int] = defaultdict(int)
        for observation in observations:
            trait_name = str(observation.get("trait_name") or "").strip()
            if trait_name:
                trait_counts[trait_name] += 1
        if not trait_counts:
            return None
        return sorted(trait_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def _analytics_group_ids(self) -> list[str] | None:
        group_ids = self._params.get("group_ids") or self._params.get("germplasm_ids")
        if group_ids is None:
            return None
        if isinstance(group_ids, str):
            parsed = [value.strip() for value in group_ids.split(",") if value.strip()]
            return parsed or None
        if isinstance(group_ids, list | tuple | set):
            parsed = [str(value).strip() for value in group_ids if str(value).strip()]
            return parsed or None
        return None

    @staticmethod
    def _trial_name_from_context(context: IntermediateResultContext) -> str | None:
        for result in context.all_results():
            if result.domain != "trials" or result.status != "success":
                continue
            trials = result.records.get("trials", [])
            if not isinstance(trials, list) or not trials:
                continue
            first = trials[0]
            if isinstance(first, dict) and first.get("name"):
                return str(first["name"])
        return None

    async def _execute_analytics_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> StepResult:
        """Execute an analytics domain step with deterministic statistics."""
        try:
            engine = AnalyticsEngine()
            narrowing = self._get_narrowing_for_step(step, context)
            observations = extract_observations(context)
            used_phenotyping_observations = bool(narrowing.get("phenotyping_observations"))
            if used_phenotyping_observations and not observations:
                narrowed_context = IntermediateResultContext()
                narrowed_context.add(
                    StepResult(
                        step_id=f"{step.step_id}:phenotyping_narrowing",
                        domain="phenotyping",
                        status="success",
                        records={"observations": narrowing["phenotyping_observations"]},
                    )
                )
                observations = extract_observations(narrowed_context)
            trait_name = self._select_analytics_trait(observations)

            computation_results: dict[str, AnalyticsResult] = {}
            computation_results["descriptive_stats"] = engine.compute_descriptive_stats(
                observations,
                trait_filter=trait_name if trait_name else None,
            )

            if trait_name and self._query_suggests_ranking():
                computation_results["ranking"] = engine.compute_ranking(
                    observations,
                    trait_name=trait_name,
                    direction=self._ranking_direction(),
                )

            if trait_name and self._query_suggests_comparison():
                computation_results["comparison"] = engine.compute_comparison(
                    observations,
                    trait_name=trait_name,
                    group_ids=self._analytics_group_ids(),
                )

            if self._has_trial_data(context):
                computation_results["trial_summary"] = engine.compute_trial_summary(
                    observations,
                    trial_name=self._trial_name_from_context(context),
                )

            records: dict[str, Any] = {}
            computation_modes: list[str] = []
            evidence_refs: list[EvidenceRef] = []
            calculation_steps: list[dict[str, Any]] = []
            warnings: list[str] = []
            confidence_scores: list[float] = []
            missing_data: list[str] = []

            for mode, result in computation_results.items():
                if result.status == "insufficient_data" and "safe_failure" in result.data:
                    records.setdefault("safe_failures", {})[mode] = result.data["safe_failure"]
                else:
                    records[mode] = result.data
                    computation_modes.append(mode)

                evidence_refs.extend(result.evidence_refs)
                calculation_steps.extend(step.model_dump() for step in result.calculation_steps)
                warnings.extend(result.warnings)
                if result.uncertainty.confidence is not None:
                    confidence_scores.append(result.uncertainty.confidence)
                missing_data.extend(result.uncertainty.missing_data)

            if not observations:
                records["insights"] = [
                    {
                        "type": "insufficient_data",
                        "message": "No numeric observations were available for analytics.",
                        "recommendation": "Add phenotypic observations before requesting analytics.",
                    }
                ]
            elif records.get("safe_failures") and not computation_modes:
                records["insights"] = [
                    {
                        "type": "insufficient_data",
                        "message": "Observations were available but did not meet analytics thresholds.",
                        "recommendation": "Add replicate observations for the requested trait.",
                    }
                ]

            records["calculation_steps"] = calculation_steps
            records["uncertainty"] = {
                "confidence": min(confidence_scores) if confidence_scores else None,
                "missing_data": list(dict.fromkeys(missing_data)),
            }
            records["warnings"] = list(dict.fromkeys(warnings))

            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records=records,
                entity_ids=[],
                evidence_refs=evidence_refs,
                metadata={
                    "computation_modes": computation_modes,
                    "observations_count": len(observations),
                    "trait_name": trait_name,
                    "used_phenotyping_observations": used_phenotyping_observations,
                },
            )

        except Exception as exc:
            logger.error("Analytics step %s failed: %s", step.step_id, exc)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="failed",
                error_category="computation_error",
                error_message=str(exc),
            )
