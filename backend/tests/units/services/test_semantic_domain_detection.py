"""
TDD tests for REEVU Semantic Domain Detection.

Written BEFORE the implementation. RED → GREEN → REFACTOR.

Covers:
- Task 1: domain_corpus.py — DOMAIN_CORPUS structure and coverage
- Task 2.3: REEVU_EMBEDDING_DETECTION_ENABLED feature flag
- Task 4: DomainEmbeddingService interface (threshold, timeout, empty message)
- Task 5: ReevuPlanner.build_plan_async() — keyword parity, fallback safety
- Task 6.1: Feature flag controls injection
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, settings
from hypothesis import strategies as st


# ── Task 1: Domain corpus ─────────────────────────────────────────────────────

def test_domain_corpus_is_importable():
    from app.modules.ai.services.reevu.domain_corpus import DOMAIN_CORPUS
    assert DOMAIN_CORPUS is not None
    assert isinstance(DOMAIN_CORPUS, dict)


def test_domain_corpus_covers_all_registered_domains():
    """DOMAIN_CORPUS must have entries for all domains in DOMAIN_ORDER."""
    from app.modules.ai.services.reevu.domain_corpus import DOMAIN_CORPUS
    from app.modules.ai.services.reevu.planner import DOMAIN_ORDER

    missing = set(DOMAIN_ORDER.keys()) - set(DOMAIN_CORPUS.keys())
    assert not missing, f"DOMAIN_CORPUS missing domains: {missing}"


def test_domain_corpus_has_minimum_50_examples_per_domain():
    """Each domain must have at least 50 example questions."""
    from app.modules.ai.services.reevu.domain_corpus import DOMAIN_CORPUS

    for domain, examples in DOMAIN_CORPUS.items():
        assert len(examples) >= 50, (
            f"Domain '{domain}' has only {len(examples)} examples (need ≥ 50)"
        )


def test_domain_corpus_has_minimum_10_implicit_examples_per_domain():
    """Each domain must have at least 10 implicit examples (no explicit domain keyword)."""
    from app.modules.ai.services.reevu.domain_corpus import DOMAIN_CORPUS, IMPLICIT_MARKERS

    for domain, examples in DOMAIN_CORPUS.items():
        implicit = [e for e in examples if any(m in e.lower() for m in IMPLICIT_MARKERS)]
        assert len(implicit) >= 10, (
            f"Domain '{domain}' has only {len(implicit)} implicit examples (need ≥ 10)"
        )


def test_domain_corpus_examples_are_non_empty_strings():
    """All examples must be non-empty strings."""
    from app.modules.ai.services.reevu.domain_corpus import DOMAIN_CORPUS

    for domain, examples in DOMAIN_CORPUS.items():
        for i, ex in enumerate(examples):
            assert isinstance(ex, str) and len(ex.strip()) > 0, (
                f"Domain '{domain}' example {i} is empty or not a string"
            )


# ── Task 2.3: Feature flag ────────────────────────────────────────────────────

def test_embedding_detection_disabled_by_default():
    """REEVU_EMBEDDING_DETECTION_ENABLED defaults to False."""
    # Ensure env var is not set
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("REEVU_EMBEDDING_DETECTION_ENABLED", None)
        from app.modules.ai.services.reevu.domain_embedding_service import (
            is_embedding_detection_enabled,
        )
        assert is_embedding_detection_enabled() is False


def test_embedding_detection_enabled_when_flag_set():
    """REEVU_EMBEDDING_DETECTION_ENABLED=true enables the feature."""
    with patch.dict(os.environ, {"REEVU_EMBEDDING_DETECTION_ENABLED": "true"}):
        from app.modules.ai.services.reevu.domain_embedding_service import (
            is_embedding_detection_enabled,
        )
        assert is_embedding_detection_enabled() is True


# ── Task 4: DomainEmbeddingService ───────────────────────────────────────────

def test_domain_embedding_service_is_importable():
    from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService
    assert DomainEmbeddingService is not None


def test_domain_embedding_service_has_required_methods():
    from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService
    svc = DomainEmbeddingService()
    assert hasattr(svc, "initialize")
    assert hasattr(svc, "detect_domains")
    assert hasattr(svc, "_embed")


@pytest.mark.asyncio
async def test_detect_domains_returns_empty_for_empty_message():
    """detect_domains returns {} for empty or whitespace-only messages."""
    from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService

    svc = DomainEmbeddingService()
    db = AsyncMock()

    result = await svc.detect_domains("", db=db, threshold=0.6)
    assert result == {}

    result = await svc.detect_domains("   ", db=db, threshold=0.6)
    assert result == {}


@pytest.mark.asyncio
async def test_detect_domains_returns_empty_when_no_prototypes():
    """detect_domains returns {} when no prototypes are stored (not initialized)."""
    from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService

    svc = DomainEmbeddingService()
    db = AsyncMock()

    # Mock DB returning no prototypes
    mock_result = MagicMock()
    mock_result.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    result = await svc.detect_domains("show me trial results", db=db, threshold=0.6)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_detect_domains_filters_by_threshold():
    """detect_domains only returns domains with score >= threshold."""
    from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService

    svc = DomainEmbeddingService()

    # Mock _embed to return a fixed vector
    mock_embedding = [0.1] * 384

    # Mock DB returning prototypes with known similarities
    mock_row_high = MagicMock()
    mock_row_high.domain = "trials"
    mock_row_high.similarity = 0.85  # above threshold

    mock_row_low = MagicMock()
    mock_row_low.domain = "weather"
    mock_row_low.similarity = 0.45  # below threshold

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row_high, mock_row_low]
    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)

    with patch.object(svc, "_embed", return_value=mock_embedding):
        result = await svc.detect_domains("show me trial results", db=db, threshold=0.6)

    assert "trials" in result
    assert result["trials"] == 0.85
    assert "weather" not in result


@pytest.mark.asyncio
async def test_detect_domains_returns_empty_on_timeout():
    """detect_domains returns {} when embedding times out (fallback to keyword detection)."""
    from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService

    svc = DomainEmbeddingService()
    db = AsyncMock()

    async def slow_embed(*args, **kwargs):
        await asyncio.sleep(10)  # simulate timeout
        return {}

    with patch.object(svc, "_embed_async", side_effect=slow_embed):
        result = await svc.detect_domains(
            "show me trial results", db=db, threshold=0.6, timeout_seconds=0.01
        )

    assert result == {}


@pytest.mark.asyncio
async def test_detect_domains_returns_empty_on_exception():
    """detect_domains returns {} when an exception occurs (safe fallback)."""
    from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService

    svc = DomainEmbeddingService()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=Exception("DB error"))

    with patch.object(svc, "_embed", return_value=[0.1] * 384):
        result = await svc.detect_domains("show me trial results", db=db, threshold=0.6)

    assert result == {}


# ── Task 5: ReevuPlanner.build_plan_async() ───────────────────────────────────

@pytest.mark.asyncio
async def test_build_plan_async_without_embedding_service_matches_build_plan():
    """build_plan_async without embedding service produces same result as build_plan."""
    from app.modules.ai.services.reevu.planner import ReevuPlanner

    planner = ReevuPlanner()
    message = "show me wheat trial results"

    sync_plan = planner.build_plan(message)
    async_plan = await planner.build_plan_async(message, db=None)

    sync_domains = {s.domain for s in sync_plan.steps}
    async_domains = {s.domain for s in async_plan.steps}

    assert sync_domains == async_domains


@pytest.mark.asyncio
async def test_build_plan_async_with_embedding_service_is_superset():
    """build_plan_async with embedding service produces same or superset of keyword domains."""
    from app.modules.ai.services.reevu.planner import ReevuPlanner
    from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService

    mock_svc = MagicMock(spec=DomainEmbeddingService)
    # Embedding service adds "soil" domain that keyword detection misses
    mock_svc.detect_domains = AsyncMock(return_value={"trials": 0.9, "soil": 0.75})

    planner = ReevuPlanner(embedding_service=mock_svc)
    message = "show me wheat trial results"
    db = AsyncMock()

    sync_plan = planner.build_plan(message)
    async_plan = await planner.build_plan_async(message, db=db)

    sync_domains = {s.domain for s in sync_plan.steps}
    async_domains = {s.domain for s in async_plan.steps}

    # async must be a superset of sync
    assert sync_domains.issubset(async_domains)


@pytest.mark.asyncio
async def test_build_plan_async_falls_back_when_embedding_fails():
    """build_plan_async falls back to keyword-only when embedding service raises."""
    from app.modules.ai.services.reevu.planner import ReevuPlanner
    from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService

    mock_svc = MagicMock(spec=DomainEmbeddingService)
    mock_svc.detect_domains = AsyncMock(side_effect=Exception("embedding failed"))

    planner = ReevuPlanner(embedding_service=mock_svc)
    message = "show me wheat trial results"
    db = AsyncMock()

    sync_plan = planner.build_plan(message)
    async_plan = await planner.build_plan_async(message, db=db)

    sync_domains = {s.domain for s in sync_plan.steps}
    async_domains = {s.domain for s in async_plan.steps}

    # Fallback: same as keyword-only
    assert sync_domains == async_domains


@given(
    message=st.text(min_size=5, max_size=100).filter(lambda s: s.strip()),
)
@settings(max_examples=30)
def test_build_plan_async_keyword_parity_property(message):
    """For any message, build_plan_async without embedding produces same domains as build_plan."""
    from app.modules.ai.services.reevu.planner import ReevuPlanner

    planner = ReevuPlanner()
    sync_plan = planner.build_plan(message)
    async_plan = asyncio.get_event_loop().run_until_complete(
        planner.build_plan_async(message, db=None)
    )

    sync_domains = {s.domain for s in sync_plan.steps}
    async_domains = {s.domain for s in async_plan.steps}
    assert sync_domains == async_domains


# ── Task 6.1: Feature flag controls injection ─────────────────────────────────

def test_planner_accepts_embedding_service_parameter():
    """ReevuPlanner.__init__ accepts embedding_service parameter."""
    from app.modules.ai.services.reevu.planner import ReevuPlanner

    mock_svc = MagicMock()
    planner = ReevuPlanner(embedding_service=mock_svc)
    assert planner._embedding_service is mock_svc


def test_planner_embedding_service_defaults_to_none():
    """ReevuPlanner._embedding_service defaults to None."""
    from app.modules.ai.services.reevu.planner import ReevuPlanner

    planner = ReevuPlanner()
    assert planner._embedding_service is None
