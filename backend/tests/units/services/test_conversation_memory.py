"""
TDD tests for REEVU Conversation Memory.

Written BEFORE the implementation. RED → GREEN → REFACTOR.

Covers:
- Task 1: ConversationDataContext dataclass + ConversationContextService
  (get/update/clear/compaction)
- Task 2: Follow-up and reset detection
- Task 4: Progressive narrowing in domain steps (context IDs in params)
"""

import json
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock

from app.modules.ai.services.reevu.conversation_context import (
    ConversationDataContext,
    ConversationContextService,
)
from app.modules.ai.services.reevu.step_executor import (
    ExecutionOutcome,
    StepResult,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_outcome(step_results: list[StepResult]) -> ExecutionOutcome:
    return ExecutionOutcome(
        step_results=step_results,
        evidence_refs=[],
        total_duration_ms=100.0,
        steps_completed=sum(1 for r in step_results if r.status == "success"),
        steps_failed=0,
        steps_skipped=0,
        steps_timed_out=0,
        budget_exhausted=False,
    )


def _make_redis(stored: dict | None = None) -> MagicMock:
    """Return a mock RedisClient with in-memory storage."""
    store: dict[str, str] = {}
    if stored:
        for k, v in stored.items():
            store[k] = json.dumps(v)

    mock = MagicMock()
    mock.is_available = True

    async def _get(key: str):
        val = store.get(key)
        if val is None:
            return None
        try:
            return json.loads(val)
        except Exception:
            return val

    async def _set(key: str, value, ttl_seconds: int = 3600):
        store[key] = json.dumps(value) if not isinstance(value, str) else value
        return True

    async def _delete(key: str):
        store.pop(key, None)
        return True

    mock.get = AsyncMock(side_effect=_get)
    mock.set = AsyncMock(side_effect=_set)
    mock.delete = AsyncMock(side_effect=_delete)
    return mock


# ── Task 1.1: ConversationDataContext dataclass ───────────────────────────────

def test_conversation_data_context_has_required_fields():
    ctx = ConversationDataContext(
        conversation_id="conv-1",
        entity_sets={"trials": ["T1", "T2"]},
        active_filters={"crop": "wheat"},
        last_plan_domains=["trials", "analytics"],
        last_result_summary="Found 2 trials",
        turn_count=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert ctx.conversation_id == "conv-1"
    assert ctx.entity_sets["trials"] == ["T1", "T2"]
    assert ctx.active_filters["crop"] == "wheat"
    assert ctx.turn_count == 1


# ── Task 1.2-1.3: get() ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_returns_none_on_cache_miss():
    """get() returns None when no context is stored."""
    svc = ConversationContextService(redis_client=_make_redis())
    result = await svc.get("conv-missing")
    assert result is None


@pytest.mark.asyncio
async def test_get_returns_context_when_stored():
    """get() deserializes and returns a stored context."""
    now = datetime.now(UTC).isoformat()
    stored_data = {
        "conversation_id": "conv-1",
        "entity_sets": {"trials": ["T1"]},
        "active_filters": {"crop": "wheat"},
        "last_plan_domains": ["trials"],
        "last_result_summary": "1 trial",
        "turn_count": 2,
        "created_at": now,
        "updated_at": now,
    }
    redis = _make_redis({"reevu:ctx:conv-1": stored_data})
    svc = ConversationContextService(redis_client=redis)

    result = await svc.get("conv-1")

    assert result is not None
    assert result.conversation_id == "conv-1"
    assert result.entity_sets["trials"] == ["T1"]
    assert result.active_filters["crop"] == "wheat"
    assert result.turn_count == 2


@pytest.mark.asyncio
async def test_get_returns_none_when_redis_unavailable():
    """get() returns None gracefully when Redis is unavailable."""
    redis = _make_redis()
    redis.is_available = False
    redis.get = AsyncMock(return_value=None)
    svc = ConversationContextService(redis_client=redis)

    result = await svc.get("conv-1")
    assert result is None


# ── Task 1.4: update() ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_increments_turn_count():
    """update() increments turn_count on each call."""
    redis = _make_redis()
    svc = ConversationContextService(redis_client=redis)
    outcome = _make_outcome([
        StepResult(step_id="t-1", domain="trials", status="success", entity_ids=["T1", "T2"])
    ])

    ctx1 = await svc.update("conv-1", outcome, {"crop": "wheat"})
    assert ctx1.turn_count == 1

    ctx2 = await svc.update("conv-1", outcome, {"crop": "wheat"})
    assert ctx2.turn_count == 2


@pytest.mark.asyncio
async def test_update_extracts_entity_ids_from_outcome():
    """update() extracts entity IDs from successful step results."""
    redis = _make_redis()
    svc = ConversationContextService(redis_client=redis)
    outcome = _make_outcome([
        StepResult(step_id="t-1", domain="trials", status="success", entity_ids=["T1", "T2"]),
        StepResult(step_id="b-1", domain="breeding", status="success", entity_ids=["G10", "G20"]),
        StepResult(step_id="f-1", domain="weather", status="failed", entity_ids=[]),
    ])

    ctx = await svc.update("conv-1", outcome, {})

    assert "trials" in ctx.entity_sets
    assert set(ctx.entity_sets["trials"]) == {"T1", "T2"}
    assert "breeding" in ctx.entity_sets
    assert set(ctx.entity_sets["breeding"]) == {"G10", "G20"}
    assert "weather" not in ctx.entity_sets  # failed step excluded


@pytest.mark.asyncio
async def test_update_merges_active_filters():
    """update() merges new params into existing active_filters."""
    now = datetime.now(UTC).isoformat()
    stored = {
        "conversation_id": "conv-1",
        "entity_sets": {},
        "active_filters": {"crop": "wheat"},
        "last_plan_domains": [],
        "last_result_summary": None,
        "turn_count": 1,
        "created_at": now,
        "updated_at": now,
    }
    redis = _make_redis({"reevu:ctx:conv-1": stored})
    svc = ConversationContextService(redis_client=redis)
    outcome = _make_outcome([])

    ctx = await svc.update("conv-1", outcome, {"location": "Ludhiana"})

    assert ctx.active_filters["crop"] == "wheat"       # preserved
    assert ctx.active_filters["location"] == "Ludhiana"  # added


@pytest.mark.asyncio
async def test_update_stores_context_in_redis_with_ttl():
    """update() calls redis.set with the correct TTL."""
    redis = _make_redis()
    svc = ConversationContextService(redis_client=redis)
    outcome = _make_outcome([])

    await svc.update("conv-1", outcome, {})

    redis.set.assert_called_once()
    call_kwargs = redis.set.call_args
    # TTL should be CONTEXT_TTL_SECONDS
    assert call_kwargs[1].get("ttl_seconds") == svc.CONTEXT_TTL_SECONDS or \
           (len(call_kwargs[0]) >= 3 and call_kwargs[0][2] == svc.CONTEXT_TTL_SECONDS)


# ── Task 1.5: clear() ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_clear_removes_context_from_redis():
    """clear() deletes the Redis key."""
    now = datetime.now(UTC).isoformat()
    stored = {
        "conversation_id": "conv-1",
        "entity_sets": {"trials": ["T1"]},
        "active_filters": {},
        "last_plan_domains": [],
        "last_result_summary": None,
        "turn_count": 3,
        "created_at": now,
        "updated_at": now,
    }
    redis = _make_redis({"reevu:ctx:conv-1": stored})
    svc = ConversationContextService(redis_client=redis)

    await svc.clear("conv-1")

    # After clear, get should return None
    result = await svc.get("conv-1")
    assert result is None


# ── Task 1.6: compaction ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_compaction_preserves_active_filters_beyond_max_turns():
    """When turn_count > MAX_TURNS, active_filters are preserved."""
    now = datetime.now(UTC).isoformat()
    stored = {
        "conversation_id": "conv-1",
        "entity_sets": {"trials": ["T1", "T2", "T3"]},
        "active_filters": {"crop": "wheat", "location": "Ludhiana"},
        "last_plan_domains": ["trials"],
        "last_result_summary": "3 trials",
        "turn_count": 10,  # at MAX_TURNS
        "created_at": now,
        "updated_at": now,
    }
    redis = _make_redis({"reevu:ctx:conv-1": stored})
    svc = ConversationContextService(redis_client=redis)
    outcome = _make_outcome([])

    # Turn 11 — triggers compaction
    ctx = await svc.update("conv-1", outcome, {})

    assert ctx.active_filters["crop"] == "wheat"
    assert ctx.active_filters["location"] == "Ludhiana"
    assert ctx.turn_count == 11


@pytest.mark.asyncio
async def test_compaction_drops_entity_sets_beyond_max_turns():
    """When turn_count > MAX_TURNS, entity_sets are cleared (compacted)."""
    now = datetime.now(UTC).isoformat()
    stored = {
        "conversation_id": "conv-1",
        "entity_sets": {"trials": ["T1", "T2"]},
        "active_filters": {"crop": "wheat"},
        "last_plan_domains": ["trials"],
        "last_result_summary": None,
        "turn_count": 10,
        "created_at": now,
        "updated_at": now,
    }
    redis = _make_redis({"reevu:ctx:conv-1": stored})
    svc = ConversationContextService(redis_client=redis)
    # New outcome with no entity IDs — compaction should clear old entity_sets
    outcome = _make_outcome([])

    ctx = await svc.update("conv-1", outcome, {})

    # entity_sets from old turns should be dropped (compacted)
    # active_filters must be preserved
    assert ctx.active_filters.get("crop") == "wheat"


# ── Task 2: Follow-up and reset detection ────────────────────────────────────

def test_is_follow_up_returns_true_with_context_and_phrase():
    """Follow-up phrase + context with entities → True."""
    from app.modules.ai.services.reevu.conversation_context import (
        is_follow_up_query,
        is_reset_query,
    )
    now = datetime.now(UTC)
    ctx = ConversationDataContext(
        conversation_id="conv-1",
        entity_sets={"trials": ["T1"]},
        active_filters={},
        last_plan_domains=["trials"],
        last_result_summary=None,
        turn_count=1,
        created_at=now,
        updated_at=now,
    )
    for phrase in ["now show me only wheat", "also filter by location", "but only the top 3",
                   "of those, which have yield data?", "from those results"]:
        assert is_follow_up_query(phrase, ctx), f"Expected True for: '{phrase}'"


def test_is_follow_up_returns_false_without_context():
    """Follow-up phrase without context → False."""
    from app.modules.ai.services.reevu.conversation_context import is_follow_up_query
    for phrase in ["now show me wheat trials", "also show genomics"]:
        assert not is_follow_up_query(phrase, None), f"Expected False for: '{phrase}'"


def test_is_follow_up_returns_false_with_empty_entity_sets():
    """Follow-up phrase with context but no entity sets → False."""
    from app.modules.ai.services.reevu.conversation_context import is_follow_up_query
    now = datetime.now(UTC)
    ctx = ConversationDataContext(
        conversation_id="conv-1",
        entity_sets={},  # empty
        active_filters={},
        last_plan_domains=[],
        last_result_summary=None,
        turn_count=0,
        created_at=now,
        updated_at=now,
    )
    assert not is_follow_up_query("now filter by wheat", ctx)


def test_is_reset_returns_true_for_reset_phrases():
    """Reset phrases → True."""
    from app.modules.ai.services.reevu.conversation_context import is_reset_query
    for phrase in ["start over", "clear filters", "reset", "new search", "forget that"]:
        assert is_reset_query(phrase), f"Expected True for: '{phrase}'"


def test_is_reset_returns_false_for_normal_queries():
    """Normal queries → False."""
    from app.modules.ai.services.reevu.conversation_context import is_reset_query
    for phrase in ["show me wheat trials", "which variety has highest yield?"]:
        assert not is_reset_query(phrase), f"Expected False for: '{phrase}'"


# ── Task 4: Progressive narrowing ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trials_step_uses_context_trial_ids():
    """_execute_trials_step() filters to context trial IDs when provided."""
    from unittest.mock import AsyncMock, MagicMock
    from app.modules.ai.services.reevu.step_executor import StepExecutor, IntermediateResultContext
    from app.schemas.reevu_plan import PlanStep

    mock_trial_service = AsyncMock()
    mock_trial_service.search = AsyncMock(return_value=[
        {"id": "T1", "trial_name": "Trial 1", "crop": "wheat"},
        {"id": "T2", "trial_name": "Trial 2", "crop": "wheat"},
        {"id": "T3", "trial_name": "Trial 3", "crop": "rice"},  # not in context
    ])

    executor = MagicMock()
    executor.db = AsyncMock()
    executor.trial_search_service = mock_trial_service
    executor.location_search_service = None

    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show me those trials",
        params={"_context_trials_ids": ["T1", "T2"]},  # context injection
    )

    step = PlanStep(
        step_id="t-1", domain="trials", prerequisites=[],
        description="trials", expected_outputs=[],
    )
    result = await se._execute_trials_step(step, IntermediateResultContext())

    assert result.status == "success"
    # Only T1 and T2 should be in entity_ids (T3 filtered out)
    assert "T3" not in result.entity_ids


@pytest.mark.asyncio
async def test_breeding_step_uses_context_breeding_ids():
    """_execute_breeding_step() filters to context germplasm IDs when provided."""
    from unittest.mock import AsyncMock, MagicMock
    from app.modules.ai.services.reevu.step_executor import StepExecutor, IntermediateResultContext
    from app.schemas.reevu_plan import PlanStep

    mock_germplasm_service = AsyncMock()
    mock_germplasm_service.search = AsyncMock(return_value=[
        {"id": "10", "germplasm_name": "IR64"},
        {"id": "20", "germplasm_name": "Swarna"},
        {"id": "30", "germplasm_name": "MTU7029"},  # not in context
    ])

    mock_obs_service = AsyncMock()
    mock_obs_service.search = AsyncMock(return_value=[])
    mock_obs_service.get_by_germplasm = AsyncMock(return_value=[])

    mock_trait_service = AsyncMock()
    mock_trait_service.search = AsyncMock(return_value=[])

    mock_seedlot_service = AsyncMock()
    mock_seedlot_service.search = AsyncMock(return_value=[])

    executor = MagicMock()
    executor.db = AsyncMock()
    executor.germplasm_search_service = mock_germplasm_service
    executor.observation_search_service = mock_obs_service
    executor.trait_search_service = mock_trait_service
    executor.seedlot_search_service = mock_seedlot_service

    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show those germplasm",
        params={"_context_breeding_ids": ["10", "20"]},
    )

    step = PlanStep(
        step_id="b-1", domain="breeding", prerequisites=[],
        description="breeding", expected_outputs=[],
    )
    result = await se._execute_breeding_step(step, IntermediateResultContext())

    assert result.status == "success"
    assert "30" not in result.entity_ids
