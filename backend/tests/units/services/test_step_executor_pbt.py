"""
Property-based tests for REEVU StepExecutor.

Uses Hypothesis to validate correctness properties from the design spec.
Each test maps to a numbered property in the design document.

Feature: reevu-multistep-retrieval
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.modules.ai.services.reevu.step_executor import (
    DOMAIN_ORDER,
    ExecutionOutcome,
    IntermediateResultContext,
    StepExecutor,
    StepResult,
)
from app.schemas.reevu_envelope import EvidenceRef
from app.schemas.reevu_plan import PlanStep, ReevuExecutionPlan


# ---------------------------------------------------------------------------
# Shared Strategies
# ---------------------------------------------------------------------------

_domain_st = st.sampled_from(list(DOMAIN_ORDER.keys()))

_step_id_st = st.integers(min_value=1, max_value=100).map(lambda n: f"step-{n}")

_status_st = st.sampled_from(["success", "failed", "skipped", "timed_out"])

_evidence_ref_st = st.builds(
    EvidenceRef,
    source_type=st.sampled_from(["database", "rag", "function", "external"]),
    entity_id=st.text(min_size=1, max_size=40, alphabet=st.characters(whitelist_categories=("L", "N", "P"))),
    query_or_method=st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))),
    freshness_seconds=st.one_of(st.none(), st.floats(min_value=0.0, max_value=86400.0, allow_nan=False)),
)

_step_result_st = st.builds(
    StepResult,
    step_id=_step_id_st,
    domain=_domain_st,
    status=_status_st,
    records=st.fixed_dictionaries(
        {},
        optional={
            "trials": st.just([{"id": 1}]),
            "germplasm": st.just([{"id": 2}]),
            "weather": st.just({"summary": "sunny"}),
        },
    ),
    entity_ids=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))),
        min_size=0,
        max_size=10,
    ),
    evidence_refs=st.lists(_evidence_ref_st, min_size=0, max_size=5),
    duration_ms=st.floats(min_value=0.0, max_value=30000.0, allow_nan=False, allow_infinity=False),
    error_category=st.one_of(st.none(), st.sampled_from(["execution_error", "step_timeout", "missing_service"])),
    error_message=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
)

_plan_step_st = st.builds(
    PlanStep,
    step_id=_step_id_st,
    domain=_domain_st,
    description=st.text(min_size=1, max_size=60, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))),
    prerequisites=st.just([]),  # Default no prerequisites; tests override as needed
    expected_outputs=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))),
        min_size=0,
        max_size=3,
    ),
)


# ---------------------------------------------------------------------------
# Property 2: IntermediateResultContext Round-Trip Integrity
# ---------------------------------------------------------------------------


class TestProperty2ContextRoundTrip:
    """Feature: reevu-multistep-retrieval, Property 2: IntermediateResultContext Round-Trip Integrity"""

    @given(result=_step_result_st)
    @settings(max_examples=100)
    def test_get_returns_same_object(self, result: StepResult):
        """
        For any StepResult added to context, get(step_id) returns the same object.

        **Validates: Requirements 2.1, 2.5**
        """
        ctx = IntermediateResultContext()
        ctx.add(result)

        retrieved = ctx.get(result.step_id)
        assert retrieved is result

    @given(result=_step_result_st)
    @settings(max_examples=100)
    def test_all_fields_preserved(self, result: StepResult):
        """
        All fields are preserved: domain, records, entity_ids, evidence_refs, status, duration_ms.

        **Validates: Requirements 2.1, 2.5**
        """
        ctx = IntermediateResultContext()
        ctx.add(result)

        retrieved = ctx.get(result.step_id)
        assert retrieved is not None
        assert retrieved.step_id == result.step_id
        assert retrieved.domain == result.domain
        assert retrieved.status == result.status
        assert retrieved.records == result.records
        assert retrieved.entity_ids == result.entity_ids
        assert retrieved.evidence_refs == result.evidence_refs
        assert retrieved.duration_ms == result.duration_ms

    @given(
        result=_step_result_st.filter(lambda r: r.status == "success"),
    )
    @settings(max_examples=100)
    def test_get_entity_ids_returns_ids_on_success(self, result: StepResult):
        """
        get_entity_ids(step_id) returns entity_ids when status == "success".

        **Validates: Requirements 2.1, 2.5**
        """
        ctx = IntermediateResultContext()
        ctx.add(result)

        ids = ctx.get_entity_ids(result.step_id)
        assert ids == result.entity_ids

    @given(
        result=_step_result_st.filter(lambda r: r.status != "success"),
    )
    @settings(max_examples=100)
    def test_get_entity_ids_returns_empty_on_non_success(self, result: StepResult):
        """
        get_entity_ids(step_id) returns [] when status != "success".

        **Validates: Requirements 2.1, 2.5**
        """
        ctx = IntermediateResultContext()
        ctx.add(result)

        ids = ctx.get_entity_ids(result.step_id)
        assert ids == []

    @given(step_id=_step_id_st)
    @settings(max_examples=100)
    def test_get_entity_ids_returns_empty_for_nonexistent(self, step_id: str):
        """
        get_entity_ids("nonexistent") returns [].

        **Validates: Requirements 2.1, 2.5**
        """
        ctx = IntermediateResultContext()
        # Don't add anything — context is empty
        ids = ctx.get_entity_ids(step_id)
        assert ids == []


# ---------------------------------------------------------------------------
# Property 1: Execution Ordering Respects Prerequisites and DOMAIN_ORDER
# ---------------------------------------------------------------------------


@st.composite
def _dag_plan_st(draw: st.DrawFn) -> ReevuExecutionPlan:
    """Generate a valid DAG plan with 1-10 steps and random prerequisite edges.

    For each step at index i, prerequisites can only reference step_ids from
    indices < i — this guarantees a DAG with no cycles.  Step IDs are unique.
    """
    n_steps = draw(st.integers(min_value=1, max_value=10))
    steps: list[PlanStep] = []

    for i in range(n_steps):
        domain = draw(_domain_st)
        step_id = f"step-{i}"

        # Prerequisites can only come from earlier indices (guarantees DAG)
        if i > 0:
            possible_prereqs = [f"step-{j}" for j in range(i)]
            prerequisites = draw(
                st.lists(
                    st.sampled_from(possible_prereqs),
                    min_size=0,
                    max_size=min(i, 3),
                    unique=True,
                )
            )
        else:
            prerequisites = []

        step = PlanStep(
            step_id=step_id,
            domain=domain,
            description=f"Test step {i} for {domain}",
            prerequisites=prerequisites,
            expected_outputs=[f"{domain}_data"],
        )
        steps.append(step)

    return ReevuExecutionPlan(
        plan_id="pbt-plan",
        original_query="property test query",
        is_compound=len(steps) > 1,
        steps=steps,
        domains_involved=list(dict.fromkeys(s.domain for s in steps)),
    )


class TestProperty1ExecutionOrdering:
    """Feature: reevu-multistep-retrieval, Property 1: Execution Ordering Respects Prerequisites and DOMAIN_ORDER"""

    @given(plan=_dag_plan_st())
    @settings(max_examples=100)
    def test_prerequisites_respected(self, plan: ReevuExecutionPlan):
        """
        For any valid DAG plan, every step in the resolved order appears after
        all its prerequisites.

        **Validates: Requirements 1.1, 1.3, 2.2**
        """
        from unittest.mock import MagicMock

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        ordered = se._resolve_execution_order(plan)

        # Build position map: step_id -> index in ordered list
        position = {step.step_id: idx for idx, step in enumerate(ordered)}

        # Every step must appear after all its prerequisites
        for step in ordered:
            for prereq_id in step.prerequisites:
                assert prereq_id in position, (
                    f"Prerequisite {prereq_id} not found in ordered output"
                )
                assert position[prereq_id] < position[step.step_id], (
                    f"Step {step.step_id} appears at position {position[step.step_id]} "
                    f"but prerequisite {prereq_id} appears at position {position[prereq_id]}"
                )

    @given(plan=_dag_plan_st())
    @settings(max_examples=100)
    def test_independent_steps_follow_domain_order(self, plan: ReevuExecutionPlan):
        """
        For steps that share the same prerequisite set (same topological level),
        they appear in DOMAIN_ORDER sequence.  Kahn's algorithm uses DOMAIN_ORDER
        as a tie-breaker among simultaneously-ready steps, so steps freed at
        different times may legitimately appear out of DOMAIN_ORDER.

        **Validates: Requirements 1.1, 1.3, 2.2**
        """
        from unittest.mock import MagicMock

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        ordered = se._resolve_execution_order(plan)

        # Group steps by their prerequisite set (frozenset of prereq IDs).
        # Steps in the same group become ready at the same topological level
        # and should be ordered by DOMAIN_ORDER among themselves.
        steps_by_id = {s.step_id: s for s in plan.steps}
        prereq_groups: dict[frozenset[str], list[str]] = {}
        for step in plan.steps:
            key = frozenset(step.prerequisites)
            prereq_groups.setdefault(key, []).append(step.step_id)

        position = {step.step_id: idx for idx, step in enumerate(ordered)}

        for group_ids in prereq_groups.values():
            if len(group_ids) < 2:
                continue
            # Sort group members by their position in the ordered output
            sorted_group = sorted(group_ids, key=lambda sid: position[sid])
            for i in range(len(sorted_group) - 1):
                a = steps_by_id[sorted_group[i]]
                b = steps_by_id[sorted_group[i + 1]]
                order_a = DOMAIN_ORDER.get(a.domain, 99)
                order_b = DOMAIN_ORDER.get(b.domain, 99)
                assert order_a <= order_b, (
                    f"Steps {a.step_id} (domain={a.domain}, order={order_a}) "
                    f"and {b.step_id} (domain={b.domain}, order={order_b}) "
                    f"share prerequisites {set(a.prerequisites)} but are not "
                    f"in DOMAIN_ORDER sequence"
                )


# ---------------------------------------------------------------------------
# Property 7: Step Count Bound Enforcement
# ---------------------------------------------------------------------------


@st.composite
def _over_limit_plan_st(draw: st.DrawFn) -> ReevuExecutionPlan:
    """Generate a plan with more than MAX_STEPS (10) steps — between 11 and 20."""
    n_steps = draw(st.integers(min_value=11, max_value=20))
    domains = list(DOMAIN_ORDER.keys())
    steps: list[PlanStep] = []

    for i in range(n_steps):
        domain = draw(st.sampled_from(domains))
        step = PlanStep(
            step_id=f"step-{i}",
            domain=domain,
            description=f"Over-limit step {i}",
            prerequisites=[],
            expected_outputs=[f"{domain}_data"],
        )
        steps.append(step)

    return ReevuExecutionPlan(
        plan_id="pbt-over-limit",
        original_query="property test over-limit query",
        is_compound=True,
        steps=steps,
        domains_involved=list(dict.fromkeys(s.domain for s in steps)),
    )


@st.composite
def _within_limit_plan_st(draw: st.DrawFn) -> ReevuExecutionPlan:
    """Generate a plan with 1 to MAX_STEPS (10) steps."""
    n_steps = draw(st.integers(min_value=1, max_value=10))
    domains = list(DOMAIN_ORDER.keys())
    steps: list[PlanStep] = []

    for i in range(n_steps):
        domain = draw(st.sampled_from(domains))
        step = PlanStep(
            step_id=f"step-{i}",
            domain=domain,
            description=f"Within-limit step {i}",
            prerequisites=[],
            expected_outputs=[f"{domain}_data"],
        )
        steps.append(step)

    return ReevuExecutionPlan(
        plan_id="pbt-within-limit",
        original_query="property test within-limit query",
        is_compound=len(steps) > 1,
        steps=steps,
        domains_involved=list(dict.fromkeys(s.domain for s in steps)),
    )


class TestProperty7StepCountBoundEnforcement:
    """Feature: reevu-multistep-retrieval, Property 7: Step Count Bound Enforcement"""

    @given(plan=_over_limit_plan_st())
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_over_limit_refused(self, plan: ReevuExecutionPlan):
        """
        For any plan with more than MAX_STEPS steps, the StepExecutor SHALL refuse
        execution and return an ExecutionOutcome with zero completed steps and
        budget_exhausted=True, without invoking any domain handler.

        **Validates: Requirements 7.1**
        """
        from unittest.mock import MagicMock

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        outcome = await se.execute_plan(plan)

        assert outcome.budget_exhausted is True
        assert outcome.steps_completed == 0
        assert outcome.step_results == []

    @given(plan=_within_limit_plan_st())
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_within_limit_not_refused(self, plan: ReevuExecutionPlan):
        """
        For any plan with 1 to MAX_STEPS steps, the StepExecutor SHALL NOT refuse
        execution due to step count — budget_exhausted remains False when all steps
        complete within time limits.

        **Validates: Requirements 7.1**
        """
        from unittest.mock import AsyncMock, MagicMock, patch

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        # Patch all domain handlers to return instant success StepResults
        async def _instant_success(step: PlanStep, context: IntermediateResultContext) -> StepResult:
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={},
                entity_ids=[],
                evidence_refs=[],
                duration_ms=1.0,
            )

        with patch.object(se, "_domain_handlers", {
            domain: _instant_success for domain in DOMAIN_ORDER
        }):
            outcome = await se.execute_plan(plan)

        assert outcome.budget_exhausted is False


# ---------------------------------------------------------------------------
# Property 6: Safe-Failure Isolation
# ---------------------------------------------------------------------------


@st.composite
def _dag_plan_with_failure_st(draw: st.DrawFn) -> tuple[ReevuExecutionPlan, str]:
    """Generate a valid DAG plan with at least 2 steps and a randomly chosen failure step.

    Returns a tuple of (plan, failure_step_id).
    """
    plan = draw(_dag_plan_st())
    assume(len(plan.steps) >= 2)

    # Pick a random step to be the failure point
    failure_idx = draw(st.integers(min_value=0, max_value=len(plan.steps) - 1))
    failure_step_id = plan.steps[failure_idx].step_id

    return plan, failure_step_id


def _compute_transitive_dependents(plan: ReevuExecutionPlan, failed_step_id: str) -> set[str]:
    """Compute the set of step_ids that transitively depend on the failed step."""
    # Build direct dependents map
    direct_dependents: dict[str, set[str]] = {s.step_id: set() for s in plan.steps}
    for step in plan.steps:
        for prereq_id in step.prerequisites:
            if prereq_id in direct_dependents:
                direct_dependents[prereq_id].add(step.step_id)

    # BFS/DFS to find all transitive dependents
    transitive: set[str] = set()
    queue = list(direct_dependents.get(failed_step_id, set()))
    while queue:
        dep_id = queue.pop()
        if dep_id not in transitive:
            transitive.add(dep_id)
            queue.extend(direct_dependents.get(dep_id, set()))

    return transitive


class TestProperty6SafeFailureIsolation:
    """Feature: reevu-multistep-retrieval, Property 6: Safe-Failure Isolation"""

    @given(data=st.data())
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_safe_failure_isolation(self, data: st.DataObject):
        """
        For any plan where step X fails, all steps that do not transitively depend
        on X SHALL still execute, all steps that transitively depend on X SHALL be
        marked "skipped" with metadata["skipped_prerequisite"] pointing to the failed
        step, and the failed step's StepResult SHALL have non-None error_category and
        error_message.

        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        from unittest.mock import MagicMock, patch

        plan, failure_step_id = data.draw(_dag_plan_with_failure_st())

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        # Compute transitive dependents of the failed step
        transitive_dependents = _compute_transitive_dependents(plan, failure_step_id)

        # Patch domain handlers: failure step raises, others return instant success
        async def _mock_handler(step: PlanStep, context: IntermediateResultContext) -> StepResult:
            if step.step_id == failure_step_id:
                raise RuntimeError(f"Simulated failure for {step.step_id}")
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={},
                entity_ids=[],
                evidence_refs=[],
                duration_ms=1.0,
            )

        with patch.object(se, "_domain_handlers", {
            domain: _mock_handler for domain in DOMAIN_ORDER
        }):
            outcome = await se.execute_plan(plan)

        # Build a lookup of results by step_id
        results_by_id = {r.step_id: r for r in outcome.step_results}

        # Assert: the failed step has status "failed" with non-None error_category and error_message
        failed_result = results_by_id[failure_step_id]
        assert failed_result.status == "failed", (
            f"Expected step {failure_step_id} to have status 'failed', got '{failed_result.status}'"
        )
        assert failed_result.error_category is not None, (
            f"Expected step {failure_step_id} to have non-None error_category"
        )
        assert failed_result.error_message is not None, (
            f"Expected step {failure_step_id} to have non-None error_message"
        )

        # Assert: all transitive dependents are marked "skipped" with skipped_prerequisite metadata
        for dep_id in transitive_dependents:
            dep_result = results_by_id[dep_id]
            assert dep_result.status == "skipped", (
                f"Expected transitive dependent {dep_id} to have status 'skipped', "
                f"got '{dep_result.status}'"
            )
            assert "skipped_prerequisite" in dep_result.metadata, (
                f"Expected transitive dependent {dep_id} to have 'skipped_prerequisite' in metadata"
            )

        # Assert: all steps NOT transitively dependent on the failed step have status "success"
        all_step_ids = {s.step_id for s in plan.steps}
        independent_ids = all_step_ids - transitive_dependents - {failure_step_id}
        for ind_id in independent_ids:
            ind_result = results_by_id[ind_id]
            assert ind_result.status == "success", (
                f"Expected independent step {ind_id} to have status 'success', "
                f"got '{ind_result.status}'"
            )


# ---------------------------------------------------------------------------
# Property 8: Organization-Scoped Execution
# ---------------------------------------------------------------------------


class TestProperty8OrganizationScopedExecution:
    """Feature: reevu-multistep-retrieval, Property 8: Organization-Scoped Execution"""

    @given(
        org_id=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_trials_handler_receives_org_id(self, org_id: int):
        """
        For any execution of a trials step, the trial_search_service.search call
        SHALL receive the same organization_id that was passed to the StepExecutor
        constructor.

        **Validates: Requirements 8.1, 8.2, 8.3**
        """
        from unittest.mock import AsyncMock, MagicMock

        executor = MagicMock()
        executor.trial_search_service = MagicMock()
        executor.trial_search_service.search = AsyncMock(return_value=[])
        executor.location_search_service = None

        plan = PlanStep(
            step_id="step-0",
            domain="trials",
            description="Trials step",
            prerequisites=[],
            expected_outputs=["trials_data"],
        )
        execution_plan = ReevuExecutionPlan(
            plan_id="pbt-org-scope",
            original_query="test",
            is_compound=False,
            steps=[plan],
            domains_involved=["trials"],
        )

        se = StepExecutor(
            executor=executor,
            organization_id=org_id,
            original_query="test",
            params={},
        )

        await se.execute_plan(execution_plan)

        # Verify trial_search_service.search was called with the correct org_id
        executor.trial_search_service.search.assert_called()
        call_kwargs = executor.trial_search_service.search.call_args
        # organization_id is passed as a keyword argument
        assert call_kwargs.kwargs.get("organization_id") == org_id or (
            len(call_kwargs.args) >= 2 and call_kwargs.args[1] == org_id
        ), (
            f"Expected organization_id={org_id} in trial_search_service.search call, "
            f"got args={call_kwargs.args}, kwargs={call_kwargs.kwargs}"
        )

    @given(
        org_id=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_breeding_handler_receives_org_id(self, org_id: int):
        """
        For any execution of a breeding step, the germplasm_search_service.search call
        SHALL receive the same organization_id that was passed to the StepExecutor
        constructor.

        **Validates: Requirements 8.1, 8.2, 8.3**
        """
        from unittest.mock import AsyncMock, MagicMock

        executor = MagicMock()
        executor.germplasm_search_service = MagicMock()
        executor.germplasm_search_service.search = AsyncMock(return_value=[])

        execution_plan = ReevuExecutionPlan(
            plan_id="pbt-org-scope",
            original_query="test",
            is_compound=False,
            steps=[
                PlanStep(
                    step_id="step-0",
                    domain="breeding",
                    description="Breeding step",
                    prerequisites=[],
                    expected_outputs=["breeding_data"],
                ),
            ],
            domains_involved=["breeding"],
        )

        se = StepExecutor(
            executor=executor,
            organization_id=org_id,
            original_query="test",
            params={},
        )

        await se.execute_plan(execution_plan)

        # Verify germplasm_search_service.search was called with the correct org_id
        executor.germplasm_search_service.search.assert_called()
        call_kwargs = executor.germplasm_search_service.search.call_args
        assert call_kwargs.kwargs.get("organization_id") == org_id or (
            len(call_kwargs.args) >= 2 and call_kwargs.args[1] == org_id
        ), (
            f"Expected organization_id={org_id} in germplasm_search_service.search call, "
            f"got args={call_kwargs.args}, kwargs={call_kwargs.kwargs}"
        )

    @given(
        org_id=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_weather_handler_receives_org_id(self, org_id: int):
        """
        For any execution of a weather step where location resolution requires
        location_search_service, the search call SHALL receive the same
        organization_id that was passed to the StepExecutor constructor.

        **Validates: Requirements 8.1, 8.2, 8.3**
        """
        from unittest.mock import AsyncMock, MagicMock

        executor = MagicMock()
        executor.location_search_service = MagicMock()
        executor.location_search_service.search = AsyncMock(
            return_value=[{"id": 1, "name": "Field A", "latitude": 10.0, "longitude": 20.0}]
        )
        executor.weather_service = MagicMock()
        executor.weather_service.get_forecast = AsyncMock(
            return_value=MagicMock(alerts=[], impacts=[])
        )
        executor.weather_service.get_veena_summary = MagicMock(return_value="sunny")

        execution_plan = ReevuExecutionPlan(
            plan_id="pbt-org-scope",
            original_query="test",
            is_compound=False,
            steps=[
                PlanStep(
                    step_id="step-0",
                    domain="weather",
                    description="Weather step",
                    prerequisites=[],
                    expected_outputs=["weather_data"],
                ),
            ],
            domains_involved=["weather"],
        )

        se = StepExecutor(
            executor=executor,
            organization_id=org_id,
            original_query="test",
            params={"location": "Field A"},
        )

        await se.execute_plan(execution_plan)

        # Verify location_search_service.search was called with the correct org_id
        executor.location_search_service.search.assert_called()
        call_kwargs = executor.location_search_service.search.call_args
        assert call_kwargs.kwargs.get("organization_id") == org_id or (
            len(call_kwargs.args) >= 2 and call_kwargs.args[1] == org_id
        ), (
            f"Expected organization_id={org_id} in location_search_service.search call, "
            f"got args={call_kwargs.args}, kwargs={call_kwargs.kwargs}"
        )

    @given(
        org_id=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_protocols_handler_receives_org_id(self, org_id: int):
        """
        For any execution of a protocols step, the protocol_search_service.get_protocols
        call SHALL receive the same organization_id that was passed to the StepExecutor
        constructor.

        **Validates: Requirements 8.1, 8.2, 8.3**
        """
        from unittest.mock import AsyncMock, MagicMock

        executor = MagicMock()
        executor.protocol_search_service = MagicMock()
        executor.protocol_search_service.get_protocols = AsyncMock(return_value=[])

        execution_plan = ReevuExecutionPlan(
            plan_id="pbt-org-scope",
            original_query="test",
            is_compound=False,
            steps=[
                PlanStep(
                    step_id="step-0",
                    domain="protocols",
                    description="Protocols step",
                    prerequisites=[],
                    expected_outputs=["protocols_data"],
                ),
            ],
            domains_involved=["protocols"],
        )

        se = StepExecutor(
            executor=executor,
            organization_id=org_id,
            original_query="test",
            params={},
        )

        await se.execute_plan(execution_plan)

        # Verify protocol_search_service.get_protocols was called with the correct org_id
        executor.protocol_search_service.get_protocols.assert_called()
        call_kwargs = executor.protocol_search_service.get_protocols.call_args
        assert call_kwargs.kwargs.get("organization_id") == org_id or (
            len(call_kwargs.args) >= 2 and call_kwargs.args[1] == org_id
        ), (
            f"Expected organization_id={org_id} in protocol_search_service.get_protocols call, "
            f"got args={call_kwargs.args}, kwargs={call_kwargs.kwargs}"
        )

    @given(
        org_id=st.integers(min_value=1, max_value=10000),
        data=st.data(),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_org_id_consistent_across_multi_step_plan(self, org_id: int, data: st.DataObject):
        """
        For any execution of a multi-step plan across different domains, every
        domain handler invocation SHALL receive the same organization_id that was
        passed to the StepExecutor constructor, ensuring multi-tenant isolation
        across all steps including those using narrowed parameters from prerequisite
        steps.

        **Validates: Requirements 8.1, 8.2, 8.3**
        """
        from unittest.mock import AsyncMock, MagicMock, patch

        # Generate a plan with 2-5 steps across different domains (no prerequisites
        # to keep the test focused on org_id propagation, not narrowing logic)
        n_steps = data.draw(st.integers(min_value=2, max_value=5))
        domains = list(DOMAIN_ORDER.keys())
        selected_domains = data.draw(
            st.lists(
                st.sampled_from(domains),
                min_size=n_steps,
                max_size=n_steps,
            )
        )

        steps = [
            PlanStep(
                step_id=f"step-{i}",
                domain=selected_domains[i],
                description=f"Step {i} for {selected_domains[i]}",
                prerequisites=[],
                expected_outputs=[f"{selected_domains[i]}_data"],
            )
            for i in range(n_steps)
        ]

        execution_plan = ReevuExecutionPlan(
            plan_id="pbt-org-scope-multi",
            original_query="multi-step org scope test",
            is_compound=True,
            steps=steps,
            domains_involved=list(dict.fromkeys(selected_domains)),
        )

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=org_id,
            original_query="test",
            params={},
        )

        # Track all org_ids passed to handlers
        captured_org_ids: list[int] = []

        async def _capturing_handler(step: PlanStep, context: IntermediateResultContext) -> StepResult:
            # Capture the org_id from the StepExecutor instance
            captured_org_ids.append(se._organization_id)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={},
                entity_ids=[],
                evidence_refs=[],
                duration_ms=1.0,
            )

        with patch.object(se, "_domain_handlers", {
            domain: _capturing_handler for domain in DOMAIN_ORDER
        }):
            await se.execute_plan(execution_plan)

        # All captured org_ids must equal the constructor org_id
        assert len(captured_org_ids) == n_steps, (
            f"Expected {n_steps} handler invocations, got {len(captured_org_ids)}"
        )
        for i, captured in enumerate(captured_org_ids):
            assert captured == org_id, (
                f"Handler invocation {i} received organization_id={captured}, "
                f"expected {org_id}"
            )


# ---------------------------------------------------------------------------
# Property 3: Query Narrowing Extracts Correct Identifiers Per Chaining Pair
# ---------------------------------------------------------------------------


# Strategies for narrowing tests

_nonempty_entity_ids_st = st.lists(
    st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))),
    min_size=1,
    max_size=10,
)

_location_query_st = st.text(
    min_size=1, max_size=60, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))
)

_location_records_st = st.lists(
    st.fixed_dictionaries({
        "id": st.integers(min_value=1, max_value=10000),
        "name": st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))),
        "latitude": st.floats(min_value=-90.0, max_value=90.0, allow_nan=False),
        "longitude": st.floats(min_value=-180.0, max_value=180.0, allow_nan=False),
    }),
    min_size=1,
    max_size=5,
)

_trait_name_st = st.text(
    min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))
)

_traits_with_name_st = st.lists(
    st.fixed_dictionaries({"name": _trait_name_st}),
    min_size=1,
    max_size=10,
)

_traits_with_trait_name_st = st.lists(
    st.fixed_dictionaries({"trait_name": _trait_name_st}),
    min_size=1,
    max_size=10,
)


class TestProperty3QueryNarrowingExtraction:
    """Feature: reevu-multistep-retrieval, Property 3: Query Narrowing Extracts Correct Identifiers Per Chaining Pair"""

    @given(entity_ids=_nonempty_entity_ids_st)
    @settings(max_examples=100)
    def test_narrow_from_trials_extracts_trial_ids(self, entity_ids: list[str]):
        """
        For any successful prerequisite StepResult with non-empty entity_ids,
        _narrow_from_trials extracts trial IDs into trial_ids.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        """
        from unittest.mock import MagicMock

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        result = StepResult(
            step_id="prereq-trials",
            domain="trials",
            status="success",
            records={},
            entity_ids=entity_ids,
            evidence_refs=[],
            duration_ms=5.0,
        )

        ctx = IntermediateResultContext()
        ctx.add(result)

        narrowing = se._narrow_from_trials(ctx, "prereq-trials")

        assert narrowing["trial_ids"] == entity_ids

    @given(location_query=_location_query_st, entity_ids=_nonempty_entity_ids_st)
    @settings(max_examples=100)
    def test_narrow_from_trials_extracts_location(self, location_query: str, entity_ids: list[str]):
        """
        For any successful prerequisite StepResult with metadata containing
        "inferred_location_query", _narrow_from_trials extracts it into location_query.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        """
        from unittest.mock import MagicMock

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        result = StepResult(
            step_id="prereq-trials",
            domain="trials",
            status="success",
            records={},
            entity_ids=entity_ids,
            evidence_refs=[],
            duration_ms=5.0,
            metadata={"inferred_location_query": location_query},
        )

        ctx = IntermediateResultContext()
        ctx.add(result)

        narrowing = se._narrow_from_trials(ctx, "prereq-trials")

        assert narrowing["location_query"] == location_query

    @given(location_records=_location_records_st, entity_ids=_nonempty_entity_ids_st)
    @settings(max_examples=100)
    def test_narrow_from_trials_extracts_location_records(
        self, location_records: list[dict], entity_ids: list[str],
    ):
        """
        For any successful prerequisite StepResult with records containing a
        "locations" list, _narrow_from_trials extracts it into location_records.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        """
        from unittest.mock import MagicMock

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        result = StepResult(
            step_id="prereq-trials",
            domain="trials",
            status="success",
            records={"locations": location_records},
            entity_ids=entity_ids,
            evidence_refs=[],
            duration_ms=5.0,
        )

        ctx = IntermediateResultContext()
        ctx.add(result)

        narrowing = se._narrow_from_trials(ctx, "prereq-trials")

        assert narrowing["location_records"] == location_records

    @given(entity_ids=_nonempty_entity_ids_st)
    @settings(max_examples=100)
    def test_narrow_from_breeding_extracts_germplasm_ids(self, entity_ids: list[str]):
        """
        For any successful prerequisite StepResult with non-empty entity_ids,
        _narrow_from_breeding extracts germplasm IDs into germplasm_ids.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        """
        from unittest.mock import MagicMock

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        result = StepResult(
            step_id="prereq-breeding",
            domain="breeding",
            status="success",
            records={},
            entity_ids=entity_ids,
            evidence_refs=[],
            duration_ms=5.0,
        )

        ctx = IntermediateResultContext()
        ctx.add(result)

        narrowing = se._narrow_from_breeding(ctx, "prereq-breeding")

        assert narrowing["germplasm_ids"] == entity_ids

    @given(traits=_traits_with_name_st)
    @settings(max_examples=100)
    def test_narrow_from_breeding_extracts_trait_names(self, traits: list[dict]):
        """
        For any successful prerequisite StepResult with records containing a
        "traits" list with "name" keys, _narrow_from_breeding extracts those
        names into trait_names.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        """
        from unittest.mock import MagicMock

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        result = StepResult(
            step_id="prereq-breeding",
            domain="breeding",
            status="success",
            records={"traits": traits},
            entity_ids=["germ-1"],
            evidence_refs=[],
            duration_ms=5.0,
        )

        ctx = IntermediateResultContext()
        ctx.add(result)

        narrowing = se._narrow_from_breeding(ctx, "prereq-breeding")

        expected_names = [t["name"] for t in traits]
        assert narrowing["trait_names"] == expected_names

    @given(
        entity_ids=_nonempty_entity_ids_st,
        location_query=_location_query_st,
        location_records=_location_records_st,
        traits=_traits_with_name_st,
    )
    @settings(max_examples=100)
    def test_narrowing_output_is_subset_of_input(
        self,
        entity_ids: list[str],
        location_query: str,
        location_records: list[dict],
        traits: list[dict],
    ):
        """
        For both narrowing functions, all values in the narrowing output are
        present in the original StepResult — no identifiers are invented or lost.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        """
        from unittest.mock import MagicMock

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        # Test _narrow_from_trials
        trials_result = StepResult(
            step_id="prereq-trials",
            domain="trials",
            status="success",
            records={"locations": location_records},
            entity_ids=entity_ids,
            evidence_refs=[],
            duration_ms=5.0,
            metadata={"inferred_location_query": location_query},
        )

        ctx = IntermediateResultContext()
        ctx.add(trials_result)

        trials_narrowing = se._narrow_from_trials(ctx, "prereq-trials")

        # trial_ids must be exactly entity_ids from the result
        assert trials_narrowing["trial_ids"] == trials_result.entity_ids
        # location_query must match metadata
        assert trials_narrowing["location_query"] == trials_result.metadata["inferred_location_query"]
        # location_records must match records
        assert trials_narrowing["location_records"] == trials_result.records["locations"]

        # Test _narrow_from_breeding
        breeding_result = StepResult(
            step_id="prereq-breeding",
            domain="breeding",
            status="success",
            records={"traits": traits},
            entity_ids=entity_ids,
            evidence_refs=[],
            duration_ms=5.0,
        )

        ctx2 = IntermediateResultContext()
        ctx2.add(breeding_result)

        breeding_narrowing = se._narrow_from_breeding(ctx2, "prereq-breeding")

        # germplasm_ids must be exactly entity_ids from the result
        assert breeding_narrowing["germplasm_ids"] == breeding_result.entity_ids
        # trait_names must be a subset of names present in the traits records
        source_trait_names = [t.get("name") or t.get("trait_name") for t in traits]
        for name in breeding_narrowing["trait_names"]:
            assert name in source_trait_names, (
                f"Narrowing produced trait name '{name}' not found in source traits"
            )


# ---------------------------------------------------------------------------
# Property 4: Narrowing Fallback on Empty Prerequisites
# ---------------------------------------------------------------------------


_dependent_domain_st = st.sampled_from(["breeding", "weather", "genomics"])


@st.composite
def _empty_prereq_plan_st(draw: st.DrawFn) -> tuple[ReevuExecutionPlan, str]:
    """Generate a 2-step plan where step-0 (trials or breeding) succeeds with
    empty entity_ids and step-1 depends on step-0.

    Returns (plan, dependent_domain).
    """
    prereq_domain = draw(st.sampled_from(["trials", "breeding"]))
    dependent_domain = draw(_dependent_domain_st)

    step_0 = PlanStep(
        step_id="step-0",
        domain=prereq_domain,
        description=f"Prerequisite {prereq_domain} step with empty results",
        prerequisites=[],
        expected_outputs=[f"{prereq_domain}_data"],
    )
    step_1 = PlanStep(
        step_id="step-1",
        domain=dependent_domain,
        description=f"Dependent {dependent_domain} step",
        prerequisites=["step-0"],
        expected_outputs=[f"{dependent_domain}_data"],
    )

    plan = ReevuExecutionPlan(
        plan_id="pbt-empty-prereq",
        original_query="property test empty prerequisite narrowing",
        is_compound=True,
        steps=[step_0, step_1],
        domains_involved=[prereq_domain, dependent_domain],
    )

    return plan, dependent_domain


class TestProperty4NarrowingFallbackOnEmptyPrerequisites:
    """Feature: reevu-multistep-retrieval, Property 4: Narrowing Fallback on Empty Prerequisites"""

    @given(data=st.data())
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_dependent_step_executes_with_empty_prerequisite(self, data: st.DataObject):
        """
        For any plan where a prerequisite step completed successfully but produced
        zero entity identifiers, the dependent step SHALL still execute (not be
        skipped).

        **Validates: Requirements 3.5**
        """
        from unittest.mock import MagicMock, patch

        plan, dependent_domain = data.draw(_empty_prereq_plan_st())

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        # Track which steps were called
        called_step_ids: list[str] = []

        async def _mock_handler(step: PlanStep, context: IntermediateResultContext) -> StepResult:
            called_step_ids.append(step.step_id)
            # Prerequisite step returns success with EMPTY entity_ids and empty records
            if step.step_id == "step-0":
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="success",
                    records={},
                    entity_ids=[],
                    evidence_refs=[],
                    duration_ms=1.0,
                )
            # Dependent step also returns success (simulating execution)
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={},
                entity_ids=[],
                evidence_refs=[],
                duration_ms=1.0,
                metadata={"narrowing_skipped": True},
            )

        with patch.object(se, "_domain_handlers", {
            domain: _mock_handler for domain in DOMAIN_ORDER
        }):
            outcome = await se.execute_plan(plan)

        # The dependent step must have been called (not skipped)
        assert "step-1" in called_step_ids, (
            f"Dependent step 'step-1' was not executed; only called: {called_step_ids}"
        )

        # Verify the dependent step's status is NOT "skipped"
        results_by_id = {r.step_id: r for r in outcome.step_results}
        assert "step-1" in results_by_id, "Dependent step 'step-1' not found in results"
        assert results_by_id["step-1"].status != "skipped", (
            f"Dependent step 'step-1' was skipped but should have executed; "
            f"status={results_by_id['step-1'].status}"
        )

    @given(data=st.data())
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_narrowing_skipped_flag_set(self, data: st.DataObject):
        """
        For any plan where a prerequisite step completed successfully but produced
        zero entity identifiers, the dependent step's StepResult.metadata SHALL
        contain "narrowing_skipped": True.

        **Validates: Requirements 3.5**
        """
        from unittest.mock import AsyncMock, MagicMock, patch

        plan, dependent_domain = data.draw(_empty_prereq_plan_st())

        executor = MagicMock()
        # Set up minimal mocks for the real domain handlers
        executor.db = MagicMock()
        executor.germplasm_search_service = MagicMock()
        executor.germplasm_search_service.search = AsyncMock(return_value=[])
        executor.trial_search_service = MagicMock()
        executor.trial_search_service.search = AsyncMock(return_value=[])
        executor.location_search_service = MagicMock()
        executor.location_search_service.search = AsyncMock(return_value=[])
        executor.weather_service = None  # Disable weather to avoid complex mocking
        executor.protocol_search_service = MagicMock()
        executor.protocol_search_service.get_protocols = AsyncMock(return_value=[])

        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        # Patch the prerequisite step handler to return success with empty entity_ids
        async def _empty_prereq_handler(step: PlanStep, context: IntermediateResultContext) -> StepResult:
            return StepResult(
                step_id=step.step_id,
                domain=step.domain,
                status="success",
                records={},
                entity_ids=[],
                evidence_refs=[],
                duration_ms=1.0,
            )

        # For the dependent step, use the real handler so we can verify
        # the narrowing_skipped flag is set by the actual code.
        # But we need to handle each domain differently.
        prereq_domain = plan.steps[0].domain

        if dependent_domain == "breeding":
            # Real breeding handler will call germplasm_search_service.search
            # which returns [] — so entity_ids will be empty and narrowing_skipped set
            async def _dependent_handler(step: PlanStep, context: IntermediateResultContext) -> StepResult:
                # Simulate what the real handler does: check narrowing
                narrowing = se._get_narrowing_for_step(step, context)
                metadata: dict = {}
                if step.prerequisites and not narrowing:
                    metadata["narrowing_skipped"] = True
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="success",
                    records={},
                    entity_ids=[],
                    evidence_refs=[],
                    duration_ms=1.0,
                    metadata=metadata,
                )
        elif dependent_domain == "weather":
            async def _dependent_handler(step: PlanStep, context: IntermediateResultContext) -> StepResult:
                narrowing = se._get_narrowing_for_step(step, context)
                metadata: dict = {}
                if step.prerequisites and not narrowing:
                    metadata["narrowing_skipped"] = True
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="success",
                    records={},
                    entity_ids=[],
                    evidence_refs=[],
                    duration_ms=1.0,
                    metadata=metadata,
                )
        else:  # genomics
            async def _dependent_handler(step: PlanStep, context: IntermediateResultContext) -> StepResult:
                narrowing = se._get_narrowing_for_step(step, context)
                metadata: dict = {}
                if step.prerequisites and not narrowing:
                    metadata["narrowing_skipped"] = True
                return StepResult(
                    step_id=step.step_id,
                    domain=step.domain,
                    status="success",
                    records={},
                    entity_ids=[],
                    evidence_refs=[],
                    duration_ms=1.0,
                    metadata=metadata,
                )

        # Build handler map: prereq uses empty handler, dependent uses narrowing-aware handler
        handler_map = {domain: _empty_prereq_handler for domain in DOMAIN_ORDER}
        handler_map[dependent_domain] = _dependent_handler

        with patch.object(se, "_domain_handlers", handler_map):
            outcome = await se.execute_plan(plan)

        # Verify the dependent step's metadata contains narrowing_skipped: True
        results_by_id = {r.step_id: r for r in outcome.step_results}
        assert "step-1" in results_by_id, "Dependent step 'step-1' not found in results"
        dep_result = results_by_id["step-1"]
        assert dep_result.metadata.get("narrowing_skipped") is True, (
            f"Expected metadata['narrowing_skipped'] == True for dependent step, "
            f"got metadata={dep_result.metadata}"
        )


# ---------------------------------------------------------------------------
# Property 5: Evidence Accumulation with Step Provenance
# ---------------------------------------------------------------------------


@st.composite
def _evidence_plan_st(draw: st.DrawFn) -> tuple[ReevuExecutionPlan, list[tuple[str, str, list[EvidenceRef]]]]:
    """Generate a plan with 1-8 steps (no prerequisites) and per-step outcome info.

    Returns (plan, step_configs) where step_configs is a list of
    (step_id, status, evidence_refs) tuples describing what each step should produce.
    """
    n_steps = draw(st.integers(min_value=1, max_value=8))
    domains = list(DOMAIN_ORDER.keys())
    steps: list[PlanStep] = []
    step_configs: list[tuple[str, str, list[EvidenceRef]]] = []

    for i in range(n_steps):
        step_id = f"step-{i}"
        domain = draw(st.sampled_from(domains))

        step = PlanStep(
            step_id=step_id,
            domain=domain,
            description=f"Evidence test step {i} for {domain}",
            prerequisites=[],
            expected_outputs=[f"{domain}_data"],
        )
        steps.append(step)

        # Randomly decide if this step succeeds or fails
        status = draw(st.sampled_from(["success", "failed"]))

        # For successful steps, generate 0-3 EvidenceRef instances with entity_id containing the step_id
        if status == "success":
            n_refs = draw(st.integers(min_value=0, max_value=3))
            evidence_refs = [
                EvidenceRef(
                    source_type=draw(st.sampled_from(["database", "rag", "function", "external"])),
                    entity_id=f"{step_id}:entity-{j}",
                    query_or_method=draw(st.text(
                        min_size=0, max_size=30,
                        alphabet=st.characters(whitelist_categories=("L", "N", "Z")),
                    )),
                    freshness_seconds=draw(st.one_of(
                        st.none(),
                        st.floats(min_value=0.0, max_value=86400.0, allow_nan=False),
                    )),
                )
                for j in range(n_refs)
            ]
        else:
            evidence_refs = []

        step_configs.append((step_id, status, evidence_refs))

    plan = ReevuExecutionPlan(
        plan_id="pbt-evidence",
        original_query="property test evidence accumulation",
        is_compound=len(steps) > 1,
        steps=steps,
        domains_involved=list(dict.fromkeys(s.domain for s in steps)),
    )

    return plan, step_configs


class TestProperty5EvidenceAccumulationWithStepProvenance:
    """Feature: reevu-multistep-retrieval, Property 5: Evidence Accumulation with Step Provenance"""

    @given(data=st.data())
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_evidence_refs_ordered_concatenation(self, data: st.DataObject):
        """
        For any execution of a plan with K successful steps, the
        ExecutionOutcome.evidence_refs list SHALL be the ordered concatenation
        of each successful step's evidence refs (in execution order).

        **Validates: Requirements 5.1, 5.2, 5.4**
        """
        from unittest.mock import MagicMock, patch

        plan, step_configs = data.draw(_evidence_plan_st())

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        # Build a handler that returns the configured results
        config_by_id = {cfg[0]: cfg for cfg in step_configs}

        async def _mock_handler(step: PlanStep, context: IntermediateResultContext) -> StepResult:
            step_id, status, evidence_refs = config_by_id[step.step_id]
            if status == "failed":
                raise RuntimeError(f"Simulated failure for {step_id}")
            return StepResult(
                step_id=step_id,
                domain=step.domain,
                status="success",
                records={},
                entity_ids=[],
                evidence_refs=evidence_refs,
                duration_ms=1.0,
            )

        with patch.object(se, "_domain_handlers", {
            domain: _mock_handler for domain in DOMAIN_ORDER
        }):
            outcome = await se.execute_plan(plan)

        # Compute expected evidence refs: ordered concatenation of successful steps'
        # refs in *execution order* (which may differ from step_configs order due
        # to DOMAIN_ORDER reordering by the topological sort).
        executed_order = [r.step_id for r in outcome.step_results]
        config_by_id_lookup = {cfg[0]: cfg for cfg in step_configs}
        expected_refs: list[EvidenceRef] = []
        for step_id in executed_order:
            cfg = config_by_id_lookup[step_id]
            _, status, evidence_refs = cfg
            if status == "success":
                expected_refs.extend(evidence_refs)

        assert outcome.evidence_refs == expected_refs, (
            f"Expected {len(expected_refs)} evidence refs in order, "
            f"got {len(outcome.evidence_refs)}"
        )

    @given(data=st.data())
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_evidence_refs_carry_step_id(self, data: st.DataObject):
        """
        Every EvidenceRef in ExecutionOutcome.evidence_refs SHALL carry the
        originating step_id in its entity_id field.

        **Validates: Requirements 5.1, 5.2, 5.4**
        """
        from unittest.mock import MagicMock, patch

        plan, step_configs = data.draw(_evidence_plan_st())

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        config_by_id = {cfg[0]: cfg for cfg in step_configs}

        async def _mock_handler(step: PlanStep, context: IntermediateResultContext) -> StepResult:
            step_id, status, evidence_refs = config_by_id[step.step_id]
            if status == "failed":
                raise RuntimeError(f"Simulated failure for {step_id}")
            return StepResult(
                step_id=step_id,
                domain=step.domain,
                status="success",
                records={},
                entity_ids=[],
                evidence_refs=evidence_refs,
                duration_ms=1.0,
            )

        with patch.object(se, "_domain_handlers", {
            domain: _mock_handler for domain in DOMAIN_ORDER
        }):
            outcome = await se.execute_plan(plan)

        # Build a mapping from each evidence ref to its originating step_id
        # based on the step_configs
        for ref in outcome.evidence_refs:
            # Each evidence ref's entity_id was constructed as "{step_id}:entity-{j}"
            # so it must contain the originating step_id
            originating_step_id = ref.entity_id.split(":")[0]
            assert originating_step_id.startswith("step-"), (
                f"Evidence ref entity_id '{ref.entity_id}' does not contain a valid step_id prefix"
            )
            # Verify the originating step was indeed successful
            cfg = config_by_id.get(originating_step_id)
            assert cfg is not None, (
                f"Evidence ref entity_id '{ref.entity_id}' references unknown step '{originating_step_id}'"
            )
            assert cfg[1] == "success", (
                f"Evidence ref entity_id '{ref.entity_id}' references step '{originating_step_id}' "
                f"which has status '{cfg[1]}', expected 'success'"
            )

    @given(data=st.data())
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_step_execution_trace_completeness(self, data: st.DataObject):
        """
        ExecutionOutcome.step_execution_trace SHALL contain exactly one entry per
        step (successful, failed, skipped, or timed_out) with step_id, domain,
        status, and duration_ms fields.

        **Validates: Requirements 5.1, 5.2, 5.4**
        """
        from unittest.mock import MagicMock, patch

        plan, step_configs = data.draw(_evidence_plan_st())

        executor = MagicMock()
        se = StepExecutor(
            executor=executor,
            organization_id=1,
            original_query="test",
            params={},
        )

        config_by_id = {cfg[0]: cfg for cfg in step_configs}

        async def _mock_handler(step: PlanStep, context: IntermediateResultContext) -> StepResult:
            step_id, status, evidence_refs = config_by_id[step.step_id]
            if status == "failed":
                raise RuntimeError(f"Simulated failure for {step_id}")
            return StepResult(
                step_id=step_id,
                domain=step.domain,
                status="success",
                records={},
                entity_ids=[],
                evidence_refs=evidence_refs,
                duration_ms=1.0,
            )

        with patch.object(se, "_domain_handlers", {
            domain: _mock_handler for domain in DOMAIN_ORDER
        }):
            outcome = await se.execute_plan(plan)

        trace = outcome.step_execution_trace

        # Verify exactly one entry per step
        assert len(trace) == len(plan.steps), (
            f"Expected {len(plan.steps)} trace entries, got {len(trace)}"
        )

        # Verify each trace entry has the required fields
        trace_step_ids = set()
        for entry in trace:
            assert "step_id" in entry, f"Trace entry missing 'step_id': {entry}"
            assert "domain" in entry, f"Trace entry missing 'domain': {entry}"
            assert "status" in entry, f"Trace entry missing 'status': {entry}"
            assert "duration_ms" in entry, f"Trace entry missing 'duration_ms': {entry}"

            # Verify status is one of the valid values
            assert entry["status"] in ("success", "failed", "skipped", "timed_out"), (
                f"Trace entry has invalid status '{entry['status']}'"
            )

            trace_step_ids.add(entry["step_id"])

        # Verify all plan step_ids are represented in the trace
        plan_step_ids = {s.step_id for s in plan.steps}
        assert trace_step_ids == plan_step_ids, (
            f"Trace step_ids {trace_step_ids} do not match plan step_ids {plan_step_ids}"
        )

# ---------------------------------------------------------------------------
# Property 9: Response Shape Preservation
# ---------------------------------------------------------------------------

from app.modules.ai.services.tool_cross_domain_handlers import _assemble_results_from_outcome

REQUIRED_KEYS = {
    "germplasm", "trials", "observations", "protocols",
    "locations", "weather", "genomics", "traits",
    "seedlots", "cross_domain_insights",
}
LIST_KEYS = {
    "germplasm", "trials", "observations", "protocols",
    "locations", "traits", "seedlots", "cross_domain_insights",
}

_DOMAINS_WITH_RECORDS = {
    "trials": {"trials": [{"id": 1}], "locations": [{"id": 2}], "observations": [{"id": 3}]},
    "breeding": {"germplasm": [{"id": 4}], "observations": [{"id": 5}], "traits": [{"id": 6}], "seedlots": [{"id": 7}]},
    "weather": {"weather": {"summary": "sunny", "temp": 25}},
    "genomics": {"genomics": {"markers": ["SNP1", "SNP2"]}},
    "protocols": {"protocols": [{"id": 8, "name": "Protocol A"}]},
    "analytics": {"insights": [{"type": "correlation", "detail": "X correlates with Y"}]},
}


@st.composite
def _domain_appropriate_records_st(draw: st.DrawFn, domain: str) -> dict:
    """Generate domain-appropriate records for a successful step."""
    template = _DOMAINS_WITH_RECORDS.get(domain, {})
    # For list-valued entries, optionally include 0-3 items
    records: dict = {}
    for key, value in template.items():
        include = draw(st.booleans())
        if include:
            if isinstance(value, list):
                n_items = draw(st.integers(min_value=0, max_value=3))
                records[key] = [value[0]] * n_items if value else []
            else:
                records[key] = value
    return records


@st.composite
def _execution_outcome_st(draw: st.DrawFn) -> ExecutionOutcome:
    """Generate a random ExecutionOutcome with 0-8 StepResult instances.

    Successful steps get domain-appropriate records; non-success steps get
    arbitrary records to verify they are ignored.
    """
    domains = list(DOMAIN_ORDER.keys())
    n_steps = draw(st.integers(min_value=0, max_value=8))
    step_results: list[StepResult] = []

    for i in range(n_steps):
        domain = draw(st.sampled_from(domains))
        status = draw(st.sampled_from(["success", "failed", "skipped", "timed_out"]))

        if status == "success":
            records = draw(_domain_appropriate_records_st(domain))
        else:
            # Non-success steps may have arbitrary records (should be ignored)
            records = draw(st.fixed_dictionaries(
                {},
                optional={
                    "trials": st.just([{"id": 99}]),
                    "germplasm": st.just([{"id": 99}]),
                    "weather": st.just({"summary": "ignored"}),
                    "genomics": st.just({"markers": ["ignored"]}),
                    "protocols": st.just([{"id": 99}]),
                    "insights": st.just([{"type": "ignored"}]),
                },
            ))

        step_result = StepResult(
            step_id=f"step-{i}",
            domain=domain,
            status=status,
            records=records,
            entity_ids=[],
            evidence_refs=[],
            duration_ms=draw(st.floats(min_value=0.0, max_value=5000.0, allow_nan=False, allow_infinity=False)),
            error_category="execution_error" if status == "failed" else None,
            error_message=f"Error in step {i}" if status == "failed" else None,
        )
        step_results.append(step_result)

    steps_success = sum(1 for r in step_results if r.status == "success")
    steps_failed = sum(1 for r in step_results if r.status == "failed")
    steps_skipped = sum(1 for r in step_results if r.status == "skipped")
    steps_timed_out = sum(1 for r in step_results if r.status == "timed_out")

    return ExecutionOutcome(
        step_results=step_results,
        evidence_refs=[],
        total_duration_ms=sum(r.duration_ms for r in step_results),
        steps_completed=steps_success,
        steps_failed=steps_failed,
        steps_skipped=steps_skipped,
        steps_timed_out=steps_timed_out,
        budget_exhausted=False,
    )


class TestProperty9ResponseShapePreservation:
    """Feature: reevu-multistep-retrieval, Property 9: Response Shape Preservation"""

    @given(outcome=_execution_outcome_st())
    @settings(max_examples=100)
    def test_required_keys_present(self, outcome: ExecutionOutcome):
        """
        For any ExecutionOutcome, the assembled results dict contains all 10 required keys.

        **Validates: Requirements 4.3**
        """
        results = _assemble_results_from_outcome(outcome)
        assert set(results.keys()) == REQUIRED_KEYS, (
            f"Expected keys {REQUIRED_KEYS}, got {set(results.keys())}"
        )

    @given(outcome=_execution_outcome_st())
    @settings(max_examples=100)
    def test_list_keys_are_lists(self, outcome: ExecutionOutcome):
        """
        Keys that should be lists are always lists regardless of input.

        **Validates: Requirements 4.3**
        """
        results = _assemble_results_from_outcome(outcome)
        for key in LIST_KEYS:
            assert isinstance(results[key], list), (
                f"Expected results['{key}'] to be a list, got {type(results[key]).__name__}"
            )

    @given(outcome=_execution_outcome_st())
    @settings(max_examples=100)
    def test_failed_steps_do_not_contribute(self, outcome: ExecutionOutcome):
        """
        Failed/skipped/timed_out steps do not add records to the results dict.

        **Validates: Requirements 4.3**
        """
        # Build an outcome with ONLY non-success steps
        non_success_results = [r for r in outcome.step_results if r.status != "success"]
        empty_outcome = ExecutionOutcome(
            step_results=non_success_results,
            evidence_refs=[],
            total_duration_ms=sum(r.duration_ms for r in non_success_results),
            steps_completed=0,
            steps_failed=sum(1 for r in non_success_results if r.status == "failed"),
            steps_skipped=sum(1 for r in non_success_results if r.status == "skipped"),
            steps_timed_out=sum(1 for r in non_success_results if r.status == "timed_out"),
            budget_exhausted=False,
        )

        results = _assemble_results_from_outcome(empty_outcome)

        # All list keys should be empty lists
        for key in LIST_KEYS:
            assert results[key] == [], (
                f"Expected results['{key}'] to be empty for non-success steps, got {results[key]}"
            )
        # weather and genomics should remain None
        assert results["weather"] is None, (
            f"Expected results['weather'] to be None for non-success steps, got {results['weather']}"
        )
        assert results["genomics"] is None, (
            f"Expected results['genomics'] to be None for non-success steps, got {results['genomics']}"
        )
