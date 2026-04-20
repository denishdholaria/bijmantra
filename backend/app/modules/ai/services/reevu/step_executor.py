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
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Literal

from app.modules.environment.services.weather_service import WeatherForecastUnavailableError
from app.modules.germplasm.services.seedlot_search_service import seedlot_search_service
from app.modules.phenotyping.services.observation_search_service import observation_search_service
from app.modules.phenotyping.services.trait_search_service import trait_search_service
from app.schemas.reevu_envelope import EvidenceRef
from app.schemas.reevu_plan import PlanStep, ReevuExecutionPlan

logger = logging.getLogger(__name__)

# Domain execution priority — lower index executes first when no
# dependency relationship exists between two steps.
DOMAIN_ORDER: dict[str, int] = {
    "weather": 0,
    "trials": 1,
    "genomics": 2,
    "breeding": 3,
    "protocols": 4,
    "analytics": 5,
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
        return [
            {
                "step_id": r.step_id,
                "domain": r.domain,
                "status": r.status,
                "duration_ms": r.duration_ms,
                "error_category": r.error_category,
            }
            for r in self.step_results
        ]


# ── Step Executor ────────────────────────────────────────────────────


class StepExecutor:
    """Executes a ReevuExecutionPlan in dependency order with intermediate result chaining."""

    MAX_STEPS: int = 10
    MAX_TOTAL_SECONDS: float = 30.0
    MAX_STEP_SECONDS: float = 10.0

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
            "breeding": self._execute_breeding_step,
            "weather": self._execute_weather_step,
            "genomics": self._execute_genomics_step,
            "protocols": self._execute_protocols_step,
            "analytics": self._execute_analytics_step,
        }

    # ── Dispatch ─────────────────────────────────────────────────────

    def _domain_handler(self, domain: str) -> Callable[..., Coroutine[Any, Any, StepResult]] | None:
        return self._domain_handlers.get(domain)

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
                        study_observations = await observation_search_service.search(
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

            germplasm_results: list[dict[str, Any]] = []
            all_observations: list[dict[str, Any]] = []
            trait_results: list[dict[str, Any]] = []
            seedlot_results: list[dict[str, Any]] = []

            # If narrowing provides trial_ids from a trials step, fetch
            # observations scoped to those trials instead of doing a
            # germplasm-first search.
            trial_ids = narrowing.get("trial_ids", [])
            if trial_ids:
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
                            obs = await observation_search_service.search(
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
                        metadata={"narrowing_skipped": True} if not narrowing else {},
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
                    observations = await observation_search_service.get_by_germplasm(
                        db=self._executor.db,
                        organization_id=self._organization_id,
                        germplasm_id=int(germ["id"]),
                        limit=10,
                    )
                    if observations:
                        all_observations.extend(observations)

            # Fetch traits
            if trait_query:
                trait_results = await trait_search_service.search(
                    db=self._executor.db,
                    organization_id=self._organization_id,
                    query=trait_query,
                    crop=crop_query,
                    limit=20,
                )

            # Fetch seedlots
            if seedlot_query or germplasm_query:
                seedlot_results = await seedlot_search_service.search(
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
                    metadata=metadata,
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
            if step.prerequisites and not narrowing:
                metadata["narrowing_skipped"] = True

            # Resolve trait names from narrowing (breeding step) or params
            narrowed_trait_names = narrowing.get("trait_names", [])

            # Get QTL mapping service — it's constructed fresh each time
            # (same pattern as the cross-domain handler).
            from app.modules.genomics.services.qtl_mapping_service import QTLMappingService

            qtl_service = QTLMappingService()

            available_traits = await qtl_service.get_traits(
                self._executor.db, self._organization_id,
            )

            # Resolve the requested trait against available traits
            from app.modules.ai.services.tool_query_helpers import _resolve_trait_query

            # Try narrowed trait names first, then fall back to params
            resolved_trait: str | None = None
            matches: list[str] = []

            if narrowed_trait_names:
                for candidate in narrowed_trait_names:
                    resolved_trait, matches = _resolve_trait_query(
                        available_traits=available_traits,
                        requested_trait=candidate,
                    )
                    if resolved_trait:
                        break

            if not resolved_trait and trait_query:
                resolved_trait, matches = _resolve_trait_query(
                    available_traits=available_traits,
                    requested_trait=trait_query,
                )

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

    async def _execute_analytics_step(
        self, step: PlanStep, context: IntermediateResultContext,
    ) -> StepResult:
        """Execute an analytics domain step.

        Placeholder: produces insights from accumulated context.
        The real analytics engine will be wired in a future phase.
        """
        try:
            insights: list[dict[str, Any]] = []

            # Gather data from all completed prerequisite steps
            for prereq_id in step.prerequisites:
                prereq_result = context.get(prereq_id)
                if prereq_result is None or prereq_result.status != "success":
                    continue

                if prereq_result.domain == "trials" and prereq_result.records.get("trials"):
                    trials = prereq_result.records["trials"]
                    trials_needing_data = [
                        t for t in trials if t.get("study_count", 0) == 0
                    ]
                    if trials_needing_data:
                        insights.append({
                            "type": "incomplete_trial",
                            "message": f"{len(trials_needing_data)} trials have no studies/observations",
                            "affected_items": [t["name"] for t in trials_needing_data[:5] if t.get("name")],
                            "recommendation": "Add studies and record observations for these trials",
                        })

                if prereq_result.domain == "breeding":
                    germplasm = prereq_result.records.get("germplasm", [])
                    observations = prereq_result.records.get("observations", [])
                    if germplasm and observations:
                        germplasm_with_obs = {
                            (obs.get("germplasm") or {}).get("id")
                            for obs in observations
                            if obs.get("germplasm")
                        }
                        germplasm_without_obs = [
                            g for g in germplasm if g["id"] not in germplasm_with_obs
                        ]
                        if germplasm_without_obs:
                            insights.append({
                                "type": "data_gap",
                                "message": (
                                    f"{len(germplasm_without_obs)} germplasm entries "
                                    "have no phenotypic observations recorded"
                                ),
                                "affected_items": [
                                    g["name"] for g in germplasm_without_obs[:5] if g.get("name")
                                ],
                                "recommendation": "Consider phenotyping these accessions to enable trait-based selection",
                            })

            evidence_refs = [
                EvidenceRef(
                    source_type="function",
                    entity_id=f"step:{step.step_id}:analytics",
                    query_or_method="analytics_engine.generate_insights",
                ),
            ]

            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={"insights": insights},
                entity_ids=[],
                evidence_refs=evidence_refs,
            )

        except Exception as exc:
            logger.error("Analytics step %s failed: %s", step.step_id, exc)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="failed",
                error_category="execution_error",
                error_message=str(exc),
            )
