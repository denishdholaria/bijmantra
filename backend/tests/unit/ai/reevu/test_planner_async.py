"""
Property-based tests for ReevuPlanner.build_plan_async().

**Validates: Requirements 1.2, 2**

Properties tested:
1. Keyword parity: for any query where keyword detection produces correct
   domains, build_plan_async() (with no embedding service) produces the same
   or a superset of those domains.
   i.e. set(keyword_domains) ⊆ set(async_domains)

2. Embedding superset: when the embedding service returns additional domains
   (above the 0.8 threshold), those domains are included in the async plan.

3. Fallback safety: when the embedding service raises an exception,
   build_plan_async() still returns a valid plan (keyword-only).

Strategy: queries are drawn from the DOMAIN_CORPUS so they are guaranteed to
be realistic domain-relevant strings.  The embedding service is mocked so no
real model or database is required.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Stub sentence_transformers so the service module can be imported without
# the optional ML dependency being installed.
# ---------------------------------------------------------------------------

def _install_sentence_transformers_stub() -> None:
    if "sentence_transformers" in sys.modules:
        return
    stub = types.ModuleType("sentence_transformers")

    class _StubSentenceTransformer:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def encode(self, text: str, **kwargs: object) -> list[float]:
            raise RuntimeError("Real SentenceTransformer.encode called in unit test — mock it!")

    stub.SentenceTransformer = _StubSentenceTransformer  # type: ignore[attr-defined]
    sys.modules["sentence_transformers"] = stub


_install_sentence_transformers_stub()

# ---------------------------------------------------------------------------
# Imports (after stub is in place)
# ---------------------------------------------------------------------------

from app.modules.ai.services.reevu.domain_corpus import DOMAIN_CORPUS  # noqa: E402
from app.modules.ai.services.reevu.planner import (  # noqa: E402
    ReevuPlanner,
    _nlp_detect_domains,
    DOMAIN_ORDER,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Build a flat list of (domain, query) pairs from the corpus so Hypothesis
# can draw realistic queries that are known to belong to a specific domain.
_CORPUS_PAIRS: list[tuple[str, str]] = [
    (domain, query)
    for domain, queries in DOMAIN_CORPUS.items()
    for query in queries
]

# Strategy: draw a single (domain, query) pair from the corpus.
corpus_query_strategy = st.sampled_from(_CORPUS_PAIRS)

# Strategy: draw a list of 1–4 corpus queries (possibly from different domains).
multi_query_strategy = st.lists(
    st.sampled_from(_CORPUS_PAIRS),
    min_size=1,
    max_size=4,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_embedding_service(return_scores: dict[str, float]) -> MagicMock:
    """Return a mock DomainEmbeddingService whose detect_domains returns *return_scores*."""
    service = MagicMock()
    service.detect_domains = AsyncMock(return_value=return_scores)
    return service


def _make_failing_embedding_service() -> MagicMock:
    """Return a mock DomainEmbeddingService whose detect_domains always raises."""
    service = MagicMock()
    service.detect_domains = AsyncMock(side_effect=RuntimeError("embedding service down"))
    return service


def _keyword_domains(message: str) -> set[str]:
    """Return the set of domains keyword detection would produce for *message*."""
    scores = _nlp_detect_domains(message)
    return {d for d, s in scores.items() if s >= 0.8}


# ---------------------------------------------------------------------------
# Property 1: Keyword parity — async plan is a superset of keyword plan
# ---------------------------------------------------------------------------

class TestKeywordParity:
    """
    **Validates: Requirements 1.2, 2**

    For any query where keyword detection produces domains, build_plan_async()
    with no embedding service must produce the same or a superset of those
    domains.  This ensures the async path never loses keyword-detected domains.
    """

    @pytest.mark.asyncio
    @given(pair=corpus_query_strategy)
    @settings(max_examples=60, deadline=5000)
    async def test_async_domains_are_superset_of_keyword_domains(
        self, pair: tuple[str, str]
    ) -> None:
        """set(keyword_domains) ⊆ set(async_domains) for all corpus queries."""
        _domain, query = pair

        # Keyword-only baseline
        kw_domains = _keyword_domains(query)

        # build_plan_async with no embedding service (keyword-only path)
        planner = ReevuPlanner(embedding_service=None)
        plan = await planner.build_plan_async(query, db=None)
        async_domains = set(plan.domains_involved)

        # The async plan must contain every domain keyword detection found.
        assert kw_domains <= async_domains, (
            f"Query: {query!r}\n"
            f"Keyword domains: {kw_domains}\n"
            f"Async domains:   {async_domains}\n"
            f"Missing:         {kw_domains - async_domains}"
        )

    @pytest.mark.asyncio
    @given(pair=corpus_query_strategy)
    @settings(max_examples=60, deadline=5000)
    async def test_async_domains_superset_with_empty_embedding_scores(
        self, pair: tuple[str, str]
    ) -> None:
        """When embedding service returns {}, async plan equals keyword plan."""
        _domain, query = pair

        kw_domains = _keyword_domains(query)

        # Embedding service returns empty dict — no additional domains
        mock_service = _make_mock_embedding_service({})
        mock_db = AsyncMock()

        planner = ReevuPlanner(embedding_service=mock_service)
        plan = await planner.build_plan_async(query, db=mock_db)
        async_domains = set(plan.domains_involved)

        assert kw_domains <= async_domains, (
            f"Query: {query!r}\n"
            f"Keyword domains: {kw_domains}\n"
            f"Async domains:   {async_domains}\n"
            f"Missing:         {kw_domains - async_domains}"
        )

    @pytest.mark.asyncio
    async def test_no_embedding_service_no_db_matches_keyword_plan(self) -> None:
        """Concrete example: no embedding service → async plan == keyword plan."""
        query = "Show me trial results for wheat"
        kw_domains = _keyword_domains(query)

        planner = ReevuPlanner(embedding_service=None)
        plan = await planner.build_plan_async(query, db=None)
        async_domains = set(plan.domains_involved)

        assert kw_domains <= async_domains

    @pytest.mark.asyncio
    async def test_embedding_service_without_db_falls_back_to_keyword(self) -> None:
        """When db=None, embedding service is not called even if set."""
        query = "Show me SNP markers for chromosome 5"
        kw_domains = _keyword_domains(query)

        mock_service = _make_mock_embedding_service({"genomics": 0.95})
        planner = ReevuPlanner(embedding_service=mock_service)

        # db=None → embedding service must NOT be called
        plan = await planner.build_plan_async(query, db=None)
        async_domains = set(plan.domains_involved)

        mock_service.detect_domains.assert_not_called()
        assert kw_domains <= async_domains


# ---------------------------------------------------------------------------
# Property 2: Embedding superset — additional embedding domains are included
# ---------------------------------------------------------------------------

class TestEmbeddingSuperset:
    """
    **Validates: Requirements 1.2, 2**

    When the embedding service returns domains with scores >= 0.8, those
    domains must appear in the async plan's domains_involved list.
    """

    @pytest.mark.asyncio
    async def test_embedding_domain_added_to_plan(self) -> None:
        """A domain returned by embedding (score 0.9) must appear in the plan."""
        # Use a query that keyword detection won't route to 'soil'
        query = "The land is acidic and needs treatment"

        # Force embedding to return soil with a high score
        mock_service = _make_mock_embedding_service({"soil": 0.9})
        mock_db = AsyncMock()

        planner = ReevuPlanner(embedding_service=mock_service)
        plan = await planner.build_plan_async(query, db=mock_db)

        assert "soil" in plan.domains_involved

    @pytest.mark.asyncio
    async def test_embedding_domain_below_threshold_not_added(self) -> None:
        """A domain returned by embedding with score < 0.8 must NOT be added."""
        query = "Show me trial results"

        # Embedding returns 'spatial' with score 0.5 — below the 0.8 threshold
        mock_service = _make_mock_embedding_service({"spatial": 0.5})
        mock_db = AsyncMock()

        planner = ReevuPlanner(embedding_service=mock_service)
        plan = await planner.build_plan_async(query, db=mock_db)

        assert "spatial" not in plan.domains_involved

    @pytest.mark.asyncio
    @given(
        pair=corpus_query_strategy,
        extra_domain=st.sampled_from(list(DOMAIN_ORDER.keys())),
        extra_score=st.floats(min_value=0.8, max_value=1.0),
    )
    @settings(max_examples=50, deadline=5000)
    async def test_embedding_extra_domain_always_included(
        self,
        pair: tuple[str, str],
        extra_domain: str,
        extra_score: float,
    ) -> None:
        """Any domain returned by embedding with score >= 0.8 must be in the plan."""
        _domain, query = pair

        mock_service = _make_mock_embedding_service({extra_domain: extra_score})
        mock_db = AsyncMock()

        planner = ReevuPlanner(embedding_service=mock_service)
        plan = await planner.build_plan_async(query, db=mock_db)

        assert extra_domain in plan.domains_involved, (
            f"Query: {query!r}\n"
            f"Extra domain: {extra_domain!r} (score={extra_score:.3f})\n"
            f"Plan domains: {plan.domains_involved}"
        )

    @pytest.mark.asyncio
    async def test_score_fusion_uses_max(self) -> None:
        """Fused score = max(keyword_score, embedding_score) per domain."""
        # 'trials' is a keyword-detectable domain; embedding returns a lower score.
        # The domain should still appear because keyword score >= 0.8.
        query = "Show me all active experiments at Hyderabad"

        kw_domains = _keyword_domains(query)
        assert "trials" in kw_domains, "Precondition: keyword detection must find 'trials'"

        # Embedding returns trials with a low score — keyword score should win
        mock_service = _make_mock_embedding_service({"trials": 0.3})
        mock_db = AsyncMock()

        planner = ReevuPlanner(embedding_service=mock_service)
        plan = await planner.build_plan_async(query, db=mock_db)

        assert "trials" in plan.domains_involved


# ---------------------------------------------------------------------------
# Property 3: Fallback safety — embedding failure does not break the plan
# ---------------------------------------------------------------------------

class TestFallbackSafety:
    """
    **Validates: Requirements 2**

    When the embedding service raises an exception, build_plan_async() must
    still return a valid plan using keyword-only scores.
    """

    @pytest.mark.asyncio
    @given(pair=corpus_query_strategy)
    @settings(max_examples=40, deadline=5000)
    async def test_embedding_failure_returns_valid_plan(
        self, pair: tuple[str, str]
    ) -> None:
        """Even when embedding raises, a valid plan is returned."""
        _domain, query = pair

        failing_service = _make_failing_embedding_service()
        mock_db = AsyncMock()

        planner = ReevuPlanner(embedding_service=failing_service)
        plan = await planner.build_plan_async(query, db=mock_db)

        # Plan must be valid: non-empty domains, non-empty steps
        assert len(plan.domains_involved) >= 1
        assert len(plan.steps) >= 1
        assert plan.original_query == query

    @pytest.mark.asyncio
    @given(pair=corpus_query_strategy)
    @settings(max_examples=40, deadline=5000)
    async def test_embedding_failure_preserves_keyword_domains(
        self, pair: tuple[str, str]
    ) -> None:
        """When embedding fails, keyword domains are still in the plan."""
        _domain, query = pair

        kw_domains = _keyword_domains(query)
        failing_service = _make_failing_embedding_service()
        mock_db = AsyncMock()

        planner = ReevuPlanner(embedding_service=failing_service)
        plan = await planner.build_plan_async(query, db=mock_db)
        async_domains = set(plan.domains_involved)

        assert kw_domains <= async_domains, (
            f"Query: {query!r}\n"
            f"Keyword domains: {kw_domains}\n"
            f"Async domains:   {async_domains}\n"
            f"Missing:         {kw_domains - async_domains}"
        )

    @pytest.mark.asyncio
    async def test_embedding_failure_recorded_in_metadata(self) -> None:
        """Embedding failure is recorded in plan metadata fallback_reasons."""
        query = "Show me trial results for wheat"

        failing_service = _make_failing_embedding_service()
        mock_db = AsyncMock()

        planner = ReevuPlanner(embedding_service=failing_service)
        plan = await planner.build_plan_async(query, db=mock_db)

        fallback_reasons = plan.metadata.get("fallback_reasons", [])
        assert "embedding_detection_failed" in fallback_reasons

    @pytest.mark.asyncio
    async def test_plan_structure_is_valid(self) -> None:
        """Concrete check: plan has correct structure after async build."""
        query = "Show me SNP markers for chromosome 5 and trial results"

        planner = ReevuPlanner(embedding_service=None)
        plan = await planner.build_plan_async(query, db=None)

        assert plan.plan_id.startswith("plan-")
        assert plan.original_query == query
        assert isinstance(plan.domains_involved, list)
        assert len(plan.domains_involved) >= 1
        assert all(step.step_id.startswith("step-") for step in plan.steps)
        assert len(plan.steps) == len(plan.domains_involved)
