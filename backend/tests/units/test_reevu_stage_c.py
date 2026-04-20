"""Unit tests for Stage C: cross-domain planner, deterministic router, and recommendation formatter."""

import pytest

from app.schemas.reevu_plan import (
    ComparisonResult,
    PlanStep,
    RankedItem,
    ReevuExecutionPlan,
    RoutingDecision,
)
from app.modules.ai.services.reevu.planner import ReevuPlanner, _detect_domains
from app.modules.ai.services.reevu.deterministic_router import DeterministicRouter
from app.modules.ai.services.reevu.recommendation_formatter import RecommendationFormatter


# ═══════════════════════════════════════════════════════════════════════
# Plan Schema
# ═══════════════════════════════════════════════════════════════════════

class TestPlanStep:
    def test_defaults(self):
        step = PlanStep(step_id="step-1", domain="breeding", description="fetch germplasm")
        assert step.step_id == "step-1"
        assert step.domain == "breeding"
        assert step.completed is False
        assert step.deterministic is False
        assert step.prerequisites == []

    def test_frozen(self):
        step = PlanStep(step_id="s1", domain="weather", description="get data")
        with pytest.raises(Exception):
            step.completed = True  # type: ignore[misc]


class TestReevuExecutionPlan:
    def test_empty_plan(self):
        plan = ReevuExecutionPlan(plan_id="p1", original_query="hello")
        assert plan.total_steps == 0
        assert plan.completed_count == 0
        assert plan.is_compound is False

    def test_compound_plan(self):
        steps = [
            PlanStep(step_id="s1", domain="weather", description="get weather"),
            PlanStep(step_id="s2", domain="breeding", description="get germplasm", prerequisites=["s1"]),
        ]
        plan = ReevuExecutionPlan(
            plan_id="p2",
            original_query="weather and breeding query",
            is_compound=True,
            steps=steps,
            domains_involved=["weather", "breeding"],
        )
        assert plan.total_steps == 2
        assert plan.is_compound is True
        assert plan.domains_involved == ["weather", "breeding"]


class TestRoutingDecision:
    def test_no_route(self):
        rd = RoutingDecision()
        assert rd.should_route is False
        assert rd.matched_criteria == []

    def test_routed(self):
        rd = RoutingDecision(
            should_route=True,
            reason="test",
            matched_criteria=["function_prefix:calculate_gdd"],
        )
        assert rd.should_route is True
        assert len(rd.matched_criteria) == 1


class TestRankedItem:
    def test_basic(self):
        item = RankedItem(candidate="HD-2967", rank=1, score=0.95, rationale="best yield")
        assert item.candidate == "HD-2967"
        assert item.rank == 1
        assert item.score == 0.95
        assert item.calculation_method_refs == []

    def test_min_rank(self):
        with pytest.raises(Exception):
            RankedItem(candidate="x", rank=0)  # rank must be >= 1


# ═══════════════════════════════════════════════════════════════════════
# Multi-Domain Planner
# ═══════════════════════════════════════════════════════════════════════

class TestDomainDetection:
    def test_breeding_keywords(self):
        domains = _detect_domains("Compare wheat varieties for drought resistance")
        assert "breeding" in domains

    def test_weather_keywords(self):
        domains = _detect_domains("What is the rainfall forecast for next week?")
        assert "weather" in domains

    def test_genomics_keywords(self):
        domains = _detect_domains("Find SNP markers linked to blast resistance")
        assert "genomics" in domains

    def test_trials_keywords(self):
        domains = _detect_domains("Show trial results for location Pune")
        assert "trials" in domains

    def test_analytics_keywords(self):
        domains = _detect_domains("Run statistical analysis and compare yield trends")
        assert "analytics" in domains

    def test_trial_top_performer_prompt_counts_as_analytics(self):
        domains = _detect_domains("Which entry was the top performer in our wheat trial this season?")
        assert "analytics" in domains
        assert "trials" in domains

    def test_genomic_selection_prompt_counts_as_analytics(self):
        domains = _detect_domains(
            "Run genomic selection with GBLUP for grain yield on our wheat training population"
        )
        assert "analytics" in domains
        assert "genomics" in domains

    def test_drought_trait_prompt_does_not_imply_weather_without_explicit_weather_context(self):
        domains = _detect_domains("Compare breeding lines with the latest trial results for drought tolerance")
        assert "breeding" in domains
        assert "trials" in domains
        assert "weather" not in domains

    def test_multi_domain(self):
        domains = _detect_domains(
            "Compare wheat varieties with genomic markers and weather data from trials"
        )
        assert len(domains) >= 3

    def test_implicit_domain_cues(self):
        # "sowing window" -> weather, analytics
        assert "weather" in _detect_domains("Find the best sowing window for maize")
        assert "analytics" in _detect_domains("Find the best sowing window for maize")
        
        # "recommendation" / "recommend" -> analytics
        assert "analytics" in _detect_domains("Recommend a fertilizer strategy")
        
        # "accuracy" -> analytics
        assert "analytics" in _detect_domains("Assess model accuracy")
        
        # "soil moisture" -> weather
        assert "weather" in _detect_domains("Check soil moisture deficit")
        
        # "disease pattern" -> analytics
        assert "analytics" in _detect_domains("Analyze disease pattern")

        domains = _detect_domains("Recommend a wheat variety from trials at Ludhiana under current weather")
        assert "analytics" in domains
        assert "breeding" in domains
        assert "trials" in domains
        assert "weather" in domains

    def test_negative_cues(self):
        # "solar radiation trend" penalizes analytics, leaves weather
        domains = _detect_domains("solar radiation trend in mp")
        assert "weather" in domains
        assert "analytics" not in domains

    def test_no_domain_detected(self):
        domains = _detect_domains("Hello, how are you?")
        assert domains == []


# ═══════════════════════════════════════════════════════════════════════
# Evaluator Strict Metrics
# ═══════════════════════════════════════════════════════════════════════

from scripts.eval_cross_domain_reasoning import evaluate

class TestEvaluatorStrictMetrics:
    def test_empty_expected_domain_handling(self, monkeypatch):
        # Mock planner to return no domains
        def mock_build_plan(*args, **kwargs):
            return ReevuExecutionPlan(plan_id="1", original_query="hi", is_compound=False, steps=[], domains_involved=[])
        monkeypatch.setattr(ReevuPlanner, "build_plan", mock_build_plan)
        
        fixtures = [{
            "prompt_id": "test-empty",
            "query": "hi",
            "expected_domains": [],
            "is_compound": False,
            "expected_min_steps": 1
        }]
        
        res = evaluate(fixtures)
        details = res["details"][0]["strict_metrics"]
        
        # When expected is empty and detected is empty -> precision=1, recall=1, f1=1
        assert details["precision"] == 1.0
        assert details["recall"] == 1.0
        assert details["f1"] == 1.0
        assert res["exact_domain_match_rate"] == 1.0

    def test_empty_expected_domain_with_false_positive(self, monkeypatch):
        # Mock planner to return a domain when none expected
        def mock_build_plan(*args, **kwargs):
            return ReevuExecutionPlan(plan_id="1", original_query="hi", is_compound=False, steps=[], domains_involved=["breeding"])
        monkeypatch.setattr(ReevuPlanner, "build_plan", mock_build_plan)
        
        fixtures = [{
            "prompt_id": "test-empty-fp",
            "query": "hi",
            "expected_domains": [],
            "is_compound": False,
            "expected_min_steps": 1
        }]
        
        res = evaluate(fixtures)
        details = res["details"][0]["strict_metrics"]
        
        # When expected is empty and detected is not empty -> precision=0, recall=0, f1=0
        assert details["precision"] == 0.0
        assert details["recall"] == 0.0
        assert details["f1"] == 0.0
        assert res["exact_domain_match_rate"] == 0.0
        assert res["details"][0]["domain_match"] is False

    def test_strict_metrics_calculation(self, monkeypatch):
        # Mock planner to return ["weather", "analytics"]
        def mock_build_plan(*args, **kwargs):
            return ReevuExecutionPlan(plan_id="1", original_query="hi", is_compound=True, steps=[], domains_involved=["weather", "analytics"])
        monkeypatch.setattr(ReevuPlanner, "build_plan", mock_build_plan)
        
        fixtures = [{
            "prompt_id": "test-strict",
            "query": "hi",
            "expected_domains": ["weather", "breeding"],
            "is_compound": True,
            "expected_min_steps": 2
        }]
        
        res = evaluate(fixtures)
        details = res["details"][0]["strict_metrics"]
        
        # Detected: {weather, analytics}. Expected: {weather, breeding}. Intersection: {weather} (size 1)
        # Precision = 1 / 2 = 0.5
        # Recall = 1 / 2 = 0.5
        # F1 = (2 * 0.5 * 0.5) / (0.5 + 0.5) = 0.5
        assert details["precision"] == 0.5
        assert details["recall"] == 0.5
        assert details["f1"] == 0.5


class TestReevuPlanner:
    def test_single_domain_plan(self):
        planner = ReevuPlanner()
        plan = planner.build_plan("Show wheat varieties")
        assert plan.is_compound is False
        assert plan.total_steps >= 1
        assert "breeding" in plan.domains_involved

    def test_compound_plan(self):
        planner = ReevuPlanner()
        plan = planner.build_plan(
            "Compare genomic markers for drought resistance across trial locations with weather data"
        )
        assert plan.is_compound is True
        assert plan.total_steps >= 3

    def test_breeding_trials_compound_plan(self):
        planner = ReevuPlanner()
        plan = planner.build_plan(
            "Which wheat varieties performed best in trials at Ludhiana?"
        )
        assert plan.is_compound is True
        assert "trials" in plan.domains_involved
        assert "breeding" in plan.domains_involved
        assert "weather" not in plan.domains_involved

    def test_drought_tolerance_trial_plan_avoids_weather_without_explicit_weather_context(self):
        planner = ReevuPlanner()
        plan = planner.build_plan(
            "Compare breeding lines with the latest trial results for drought tolerance"
        )
        assert plan.is_compound is True
        assert "breeding" in plan.domains_involved
        assert "trials" in plan.domains_involved
        assert "weather" not in plan.domains_involved

    def test_breeding_genomics_compound_plan(self):
        planner = ReevuPlanner()
        plan = planner.build_plan(
            "Which rice varieties have blast resistance markers?"
        )
        assert plan.is_compound is True
        assert "genomics" in plan.domains_involved
        assert "breeding" in plan.domains_involved
        assert "trials" not in plan.domains_involved

    def test_genomic_selection_plan_includes_analytics_domain(self):
        planner = ReevuPlanner()
        plan = planner.build_plan(
            "Run genomic selection with GBLUP for grain yield on our wheat training population"
        )
        assert "genomics" in plan.domains_involved
        assert "analytics" in plan.domains_involved

    def test_trials_phenotype_environment_compound_plan(self):
        planner = ReevuPlanner()
        plan = planner.build_plan(
            "Show phenotype observations from trials at Ludhiana under current weather"
        )
        assert plan.is_compound is True
        assert "trials" in plan.domains_involved
        assert "breeding" in plan.domains_involved
        assert "weather" in plan.domains_involved

    def test_germplasm_trait_protocol_compound_plan(self):
        planner = ReevuPlanner()
        plan = planner.build_plan(
            "Which rice germplasm support yield improvement under speed breeding protocols?"
        )
        assert plan.is_compound is True
        assert "breeding" in plan.domains_involved
        assert "protocols" in plan.domains_involved

    def test_default_breeding_fallback(self):
        planner = ReevuPlanner()
        plan = planner.build_plan("Hello there")
        assert plan.total_steps == 1
        assert plan.domains_involved == ["breeding"]

    def test_plan_has_id(self):
        planner = ReevuPlanner()
        plan = planner.build_plan("test query")
        assert plan.plan_id.startswith("plan-")

    def test_step_ordering(self):
        planner = ReevuPlanner()
        plan = planner.build_plan(
            "Show weather data and analyze breeding performance"
        )
        if plan.total_steps >= 2:
            # Weather should come before breeding/analytics in order.
            domains_order = [s.domain for s in plan.steps]
            weather_idx = domains_order.index("weather") if "weather" in domains_order else 999
            for domain in ["breeding", "analytics"]:
                if domain in domains_order:
                    assert domains_order.index(domain) > weather_idx

    def test_deterministic_flag_for_analytics(self):
        planner = ReevuPlanner()
        plan = planner.build_plan("Run statistical analysis on trial data")
        analytics_steps = [s for s in plan.steps if s.domain == "analytics"]
        assert any(s.deterministic for s in analytics_steps)

    def test_deterministic_flag_for_calculate_function(self):
        planner = ReevuPlanner()
        plan = planner.build_plan(
            "What is the GDD for maize?",
            function_call_name="calculate_gdd",
        )
        assert any(s.deterministic for s in plan.steps)

    def test_prerequisites_chain(self):
        planner = ReevuPlanner()
        plan = planner.build_plan(
            "Get weather data and run breeding analysis with genomic markers"
        )
        if plan.total_steps >= 2:
            # Every step after the first should have a prerequisite.
            for step in plan.steps[1:]:
                assert len(step.prerequisites) > 0

    def test_nlp_exception_falls_back_to_keyword_path(self, monkeypatch):
        planner = ReevuPlanner()

        def raise_nlp(_: str) -> tuple[list[str], float]:
            raise RuntimeError("nlp unavailable")

        monkeypatch.setattr(planner, "_detect_domains_nlp", raise_nlp)
        plan = planner.build_plan("Show weather data")

        assert plan.domains_involved == ["weather"]
        assert "nlp_exception" in plan.metadata["fallback_reasons"]

    def test_dag_builder_error_falls_back_to_linear_plan(self, monkeypatch):
        planner = ReevuPlanner()

        monkeypatch.setattr(
            planner,
            "_build_domain_order_dag",
            lambda _: (_ for _ in ()).throw(RuntimeError("dag failure")),
        )
        plan = planner.build_plan("Show weather and trial analysis")

        assert plan.domains_involved == ["weather", "trials", "analytics"]
        assert "dag_builder_error" in plan.metadata["fallback_reasons"]

    def test_low_confidence_uses_keyword_fallback(self, monkeypatch):
        planner = ReevuPlanner()

        monkeypatch.setattr(planner, "_detect_domains_nlp", lambda _: (["genomics"], 0.2))
        plan = planner.build_plan("Show wheat varieties")

        assert plan.domains_involved == ["breeding"]
        assert "low_confidence_threshold" in plan.metadata["fallback_reasons"]

    def test_ambiguous_domain_does_not_crash_planner(self, monkeypatch):
        planner = ReevuPlanner()

        monkeypatch.setattr(planner, "_detect_domains_nlp", lambda _: (["unknown-domain"], 0.95))
        plan = planner.build_plan("Ambiguous request")

        assert plan.total_steps == 1
        assert plan.domains_involved == ["breeding"]
        assert "ambiguous_domain_filtered" in plan.metadata["fallback_reasons"]


@pytest.mark.parametrize(
    ("nlp_enabled", "dag_enabled"),
    [
        (True, True),
        (False, True),
        (True, False),
        (False, False),
    ],
)
def test_planner_toggle_matrix_produces_valid_plan(nlp_enabled: bool, dag_enabled: bool):
    planner = ReevuPlanner(nlp_enabled=nlp_enabled, dag_enabled=dag_enabled)
    plan = planner.build_plan(
        "Compare genomic markers for drought resistance across trial locations with weather data"
    )

    assert plan.plan_id.startswith("plan-")
    assert plan.total_steps >= 1
    assert len(plan.steps) == plan.total_steps
    assert len(plan.domains_involved) >= 1

    # Contract safety: schema fields remain present for downstream chat envelope assembly.
    plan_payload = plan.model_dump()
    assert {"plan_id", "original_query", "is_compound", "steps", "domains_involved"}.issubset(
        plan_payload.keys()
    )

    for step in plan.steps:
        assert step.step_id
        assert step.domain
        assert isinstance(step.prerequisites, list)
        assert isinstance(step.expected_outputs, list)
        step_payload = step.model_dump()
        assert {
            "step_id",
            "domain",
            "description",
            "prerequisites",
            "expected_outputs",
            "completed",
            "deterministic",
        }.issubset(step_payload.keys())

    # DAG toggle controls prerequisites chain independently from domain detection.
    if dag_enabled and plan.total_steps > 1:
        assert any(step.prerequisites for step in plan.steps[1:])
    else:
        assert all(not step.prerequisites for step in plan.steps)


def test_planner_linear_fallback_when_nlp_and_dag_disabled():
    planner = ReevuPlanner(nlp_enabled=False, dag_enabled=False)
    plan = planner.build_plan(
        "Compare genomic markers for drought resistance across trial locations with weather data"
    )

    assert plan.is_compound is False
    assert plan.domains_involved == ["breeding"]
    assert plan.total_steps == 1
    assert plan.steps[0].prerequisites == []


def test_planner_toggle_env_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("REEVU_PLANNER_NLP_ENABLED", "false")
    monkeypatch.setenv("REEVU_PLANNER_DAG_ENABLED", "false")

    plan = ReevuPlanner().build_plan(
        "Compare genomic markers for drought resistance across trial locations with weather data"
    )

    assert plan.total_steps == 1
    assert plan.domains_involved == ["breeding"]
    assert plan.steps[0].prerequisites == []


# ═══════════════════════════════════════════════════════════════════════
# Deterministic Router
# ═══════════════════════════════════════════════════════════════════════

class TestDeterministicRouter:
    def test_no_route_for_simple_query(self):
        router = DeterministicRouter()
        decision = router.get_routing_decision("What varieties are available?")
        assert decision.should_route is False

    def test_route_for_calculate_function(self):
        router = DeterministicRouter()
        decision = router.get_routing_decision(
            "Calculate GDD for wheat",
            function_call_name="calculate_gdd",
        )
        assert decision.should_route is True
        assert any("function_prefix" in c for c in decision.matched_criteria)

    def test_route_for_numeric_keyword(self):
        router = DeterministicRouter()
        decision = router.get_routing_decision("Calculate the average yield for trial T-001")
        assert decision.should_route is True
        assert any("keyword" in c for c in decision.matched_criteria)

    def test_route_for_numeric_density(self):
        router = DeterministicRouter()
        decision = router.get_routing_decision(
            "Compare 42.5% yield with 38.2% yield and 45.1% yield across 3 locations"
        )
        assert decision.should_route is True

    def test_convenience_should_route(self):
        router = DeterministicRouter()
        assert router.should_route("What is 5 + 3?", function_call_name="calculate_sum") is True
        assert router.should_route("Hello world") is False

    def test_analyze_prefix_triggers_routing(self):
        router = DeterministicRouter()
        decision = router.get_routing_decision(
            "Analyze resistance",
            function_call_name="analyze_resistance_patterns",
        )
        assert decision.should_route is True

    def test_predict_prefix_triggers_routing(self):
        router = DeterministicRouter()
        decision = router.get_routing_decision(
            "Predict yield",
            function_call_name="predict_yield_performance",
        )
        assert decision.should_route is True


# ═══════════════════════════════════════════════════════════════════════
# Recommendation Formatter
# ═══════════════════════════════════════════════════════════════════════

class TestRecommendationFormatter:
    def test_empty_candidates(self):
        fmt = RecommendationFormatter()
        result = fmt.format_comparison([])
        assert isinstance(result, ComparisonResult)
        assert result.items == []
        assert result.overall_recommendation == ""

    def test_single_candidate(self):
        fmt = RecommendationFormatter()
        result = fmt.format_comparison([
            {"candidate": "HD-2967", "score": 0.85, "rationale": "High yield"}
        ])
        assert len(result.items) == 1
        assert result.items[0].rank == 1
        assert result.items[0].candidate == "HD-2967"
        assert "HD-2967" in result.overall_recommendation

    def test_sorted_by_score(self):
        fmt = RecommendationFormatter()
        result = fmt.format_comparison([
            {"candidate": "A", "score": 0.5},
            {"candidate": "B", "score": 0.9},
            {"candidate": "C", "score": 0.7},
        ])
        assert result.items[0].candidate == "B"
        assert result.items[1].candidate == "C"
        assert result.items[2].candidate == "A"
        assert result.items[0].rank == 1
        assert result.items[2].rank == 3

    def test_evidence_refs_forwarded(self):
        fmt = RecommendationFormatter()
        result = fmt.format_comparison([
            {"candidate": "X", "score": 1.0, "evidence_refs": ["ref-1", "ref-2"]}
        ])
        assert result.items[0].evidence_refs == ["ref-1", "ref-2"]

    def test_calculation_method_refs_forwarded(self):
        fmt = RecommendationFormatter()
        result = fmt.format_comparison(
            [
                {
                    "candidate": "X",
                    "score": 1.0,
                    "calculation_method_refs": ["fn:selection_index", "fn:gblup"],
                }
            ],
            calculation_method_refs=["fn:multi_trait_selection"],
        )
        assert result.items[0].calculation_method_refs == ["fn:selection_index", "fn:gblup"]
        assert result.calculation_method_refs == ["fn:multi_trait_selection"]

    def test_methodology_and_domains(self):
        fmt = RecommendationFormatter()
        result = fmt.format_comparison(
            [{"candidate": "A", "score": 1.0}],
            methodology="Multi-trait selection index",
            domains_used=["breeding", "genomics"],
        )
        assert result.methodology == "Multi-trait selection index"
        assert result.domains_used == ["breeding", "genomics"]

    def test_uncertainty_note(self):
        fmt = RecommendationFormatter()
        result = fmt.format_comparison([
            {"candidate": "Y", "score": 0.6, "uncertainty": "Limited trial data"}
        ])
        assert result.items[0].uncertainty_note == "Limited trial data"

    def test_name_fallback(self):
        fmt = RecommendationFormatter()
        result = fmt.format_comparison([
            {"name": "Variety-Z", "score": 0.8}
        ])
        assert result.items[0].candidate == "Variety-Z"


# ═══════════════════════════════════════════════════════════════════════
# Formatter Integration (chat.py _maybe_format_comparison path)
# ═══════════════════════════════════════════════════════════════════════

from app.api.v2.chat import _maybe_format_comparison


class TestFormatterIntegration:
    """Tests for the recommendation formatter wiring into function-result post-processing."""

    def test_comparison_from_function_result_with_scores(self):
        """Scored candidates in function_result.data should produce a comparison_result."""
        function_result = {
            "data": [
                {"candidate": "HD-2967", "score": 0.92, "rationale": "High yield"},
                {"candidate": "PBW-343", "score": 0.85, "rationale": "Good disease res."},
                {"candidate": "WH-1105", "score": 0.78, "rationale": "Moderate stability"},
            ]
        }
        result = _maybe_format_comparison(function_result, function_call_name="compare_germplasm")
        assert result is not None
        assert result["items"][0]["candidate"] == "HD-2967"
        assert result["items"][0]["rank"] == 1
        assert result["methodology"] == "function:compare_germplasm"

    def test_no_comparison_for_non_ranking_result(self):
        """Function results without score/name/candidate keys should return None."""
        function_result = {
            "data": [
                {"id": "T-001", "status": "active", "location": "Pune"},
                {"id": "T-002", "status": "active", "location": "Delhi"},
            ]
        }
        result = _maybe_format_comparison(function_result, function_call_name="search_trials")
        assert result is None

    def test_no_comparison_for_none_result(self):
        """None function_result should return None."""
        assert _maybe_format_comparison(None) is None

    def test_no_comparison_for_empty_data(self):
        """Empty data list should return None."""
        assert _maybe_format_comparison({"data": []}) is None

    def test_no_comparison_for_non_list_data(self):
        """Non-list data should return None."""
        assert _maybe_format_comparison({"data": "not a list"}) is None

    def test_evidence_refs_aligned_with_ranking(self):
        """Evidence refs in ranked items should survive the formatting pipeline."""
        function_result = {
            "data": [
                {"candidate": "X", "score": 1.0, "evidence_refs": ["ref-101", "ref-102"]},
                {"candidate": "Y", "score": 0.5, "evidence_refs": ["ref-201"]},
            ]
        }
        result = _maybe_format_comparison(function_result)
        assert result is not None
        top_item = result["items"][0]
        assert top_item["candidate"] == "X"
        assert "ref-101" in top_item["evidence_refs"]
        assert "ref-102" in top_item["evidence_refs"]

    def test_calculation_method_refs_aligned_with_ranking(self):
        """Deterministic method refs should survive the comparison formatting pipeline."""
        function_result = {
            "data": [
                {
                    "candidate": "X",
                    "score": 1.0,
                    "calculation_method_refs": ["fn:selection_index", "fn:gblup"],
                }
            ],
            "calculation_method_refs": ["fn:multi_trait_selection"],
        }
        result = _maybe_format_comparison(function_result, function_call_name="compare_germplasm")
        assert result is not None
        assert result["items"][0]["calculation_method_refs"] == ["fn:selection_index", "fn:gblup"]
        assert result["calculation_method_refs"] == ["fn:multi_trait_selection"]

    def test_name_key_detected_as_rankable(self):
        """Items with 'name' key (instead of 'candidate') should be detected as rankable."""
        function_result = {
            "data": [
                {"name": "Variety-A", "score": 0.9},
                {"name": "Variety-B", "score": 0.7},
            ]
        }
        result = _maybe_format_comparison(function_result)
        assert result is not None
        assert result["items"][0]["candidate"] == "Variety-A"

    def test_cross_domain_recommendations_are_formatted_as_comparison(self):
        function_result = {
            "data": {
                "recommendations": [
                    {
                        "candidate": "IR64",
                        "score": 0.88,
                        "rationale": "trial evidence available; weather context is available",
                        "evidence_refs": ["db:germplasm:IR64", "db:trial:TRIAL-1"],
                        "calculation_method_refs": ["fn:cross_domain_recommendation_ranker"],
                    }
                ]
            },
            "calculation_method_refs": ["fn:cross_domain_recommendation_ranker"],
        }

        result = _maybe_format_comparison(function_result, function_call_name="cross_domain_query")
        assert result is not None
        assert result["items"][0]["candidate"] == "IR64"
        assert result["items"][0]["calculation_method_refs"] == ["fn:cross_domain_recommendation_ranker"]
        assert result["overall_recommendation"].startswith("Recommended: IR64")

    def test_domains_passed_through(self):
        """domains_involved parameter should appear in comparison result."""
        function_result = {
            "data": [{"candidate": "A", "score": 1.0}]
        }
        result = _maybe_format_comparison(
            function_result,
            domains_involved=["breeding", "genomics"],
        )
        assert result is not None
        assert result["domains_used"] == ["breeding", "genomics"]

    def test_trial_results_interpretation_ranking_formats_as_comparison(self):
        """Deterministic trial-summary ranking should surface as a structured comparison."""
        function_result = {
            "calculation_method_refs": ["fn:trial_summary.mean"],
            "data": {
                "trial": {"trialDbId": "TRIAL-1", "trialName": "Yield Trial"},
                "top_performers": [{"germplasmName": "Fallback", "yield_value": 4.8, "change_percent": "+4.0%"}],
                "interpretation": {
                    "ranking": [
                        {
                            "entity_name": "Swarna",
                            "score": 5.1,
                            "rationale": "Highest trial mean yield",
                            "evidence_refs": ["db:observation:OBS-2"],
                            "delta_percent_vs_baseline": 12.5,
                        },
                        {
                            "entity_name": "IR64",
                            "score": 4.7,
                            "rationale": "Second-highest trial mean yield",
                            "evidence_refs": ["db:observation:OBS-3"],
                        },
                    ]
                },
            }
        }

        result = _maybe_format_comparison(function_result, function_call_name="get_trial_results")

        assert result is not None
        assert result["methodology"] == "function:get_trial_results"
        assert result["items"][0]["candidate"] == "Swarna"
        assert result["items"][0]["rank"] == 1
        assert result["items"][0]["evidence_refs"] == ["db:observation:OBS-2"]
        assert result["items"][0]["calculation_method_refs"] == ["fn:trial_summary.mean"]
        assert result["calculation_method_refs"] == ["fn:trial_summary.mean"]
        assert "12.50%" in result["items"][0]["uncertainty_note"]

    def test_trial_results_top_performers_fallback_formats_as_comparison(self):
        """Top-performer payload should still format when interpretation ranking is absent."""
        function_result = {
            "data": {
                "top_performers": [
                    {"germplasmName": "Swarna", "yield_value": 5.1, "change_percent": "+12.1%"},
                    {"germplasmName": "IR64", "yield_value": 4.7, "change_percent": "+3.2%"},
                ],
                "interpretation": {},
            }
        }

        result = _maybe_format_comparison(function_result, function_call_name="get_trial_results")

        assert result is not None
        assert result["items"][0]["candidate"] == "Swarna"
        assert result["items"][0]["score"] == 5.1
        assert "Change vs baseline: +12.1%" == result["items"][0]["rationale"]
