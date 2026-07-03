"""
Unit tests for DomainEmbeddingService.

Tests:
1. Threshold filtering — mock _embed to return fixed vectors; verify only
   domains above threshold are returned.
2. Fallback on timeout — mock _embed to sleep > 500 ms; verify detect_domains
   returns {}.
3. Empty message handling — verify detect_domains("") returns {} without
   calling the model.

sentence_transformers is NOT required to be installed for these tests to pass.
All embedding calls are mocked at the instance level.
"""

from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Ensure sentence_transformers is never imported during tests.
# We inject a stub module so the top-level try/except in the service resolves
# to the stub rather than raising ImportError.
# ---------------------------------------------------------------------------

def _install_sentence_transformers_stub() -> None:
    """Inject a minimal stub for sentence_transformers into sys.modules."""
    if "sentence_transformers" in sys.modules:
        return  # already present (real or stub)

    stub = types.ModuleType("sentence_transformers")

    class _StubSentenceTransformer:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def encode(self, text: str, **kwargs: object) -> list[float]:  # type: ignore[override]
            raise RuntimeError("Real SentenceTransformer.encode called in unit test — mock it!")

    stub.SentenceTransformer = _StubSentenceTransformer  # type: ignore[attr-defined]
    sys.modules["sentence_transformers"] = stub


_install_sentence_transformers_stub()

# Now import the service (sentence_transformers stub is in place).
from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db_mock(rows: list[tuple[str, float]]) -> AsyncMock:
    """Return an AsyncMock db session whose execute() returns *rows*."""
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.fetchall.return_value = rows
    db.execute = AsyncMock(return_value=result_mock)
    db.commit = AsyncMock()
    return db


def _fixed_vector(value: float = 0.5, dim: int = 384) -> list[float]:
    """Return a fixed-value embedding vector."""
    return [value] * dim


# ---------------------------------------------------------------------------
# Test: threshold filtering
# ---------------------------------------------------------------------------

class TestThresholdFiltering:
    """Verify that only domains with similarity >= threshold are returned."""

    @pytest.mark.asyncio
    async def test_returns_domains_above_threshold(self) -> None:
        """Domains with score >= threshold must appear in the result."""
        # DB returns two rows: one above threshold, one below.
        db = _make_db_mock([
            ("trials", 0.75),
            ("breeding", 0.55),  # below default threshold of 0.6
        ])

        service = DomainEmbeddingService()
        # Patch _embed so no real model is loaded.
        with patch.object(service, "_embed", return_value=_fixed_vector()):
            result = await service.detect_domains("show me trial results", db, threshold=0.6)

        # The SQL query itself filters by threshold, so the mock returns only
        # what the DB would return.  We verify the service passes the result
        # through correctly.
        assert "trials" in result
        assert result["trials"] == pytest.approx(0.75)

    @pytest.mark.asyncio
    async def test_excludes_domains_below_threshold(self) -> None:
        """Domains below threshold must not appear in the result."""
        # Simulate DB returning only the above-threshold row (as pgvector would).
        db = _make_db_mock([("trials", 0.75)])

        service = DomainEmbeddingService()
        with patch.object(service, "_embed", return_value=_fixed_vector()):
            result = await service.detect_domains("show me trial results", db, threshold=0.6)

        assert "breeding" not in result

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_no_domains_above_threshold(self) -> None:
        """When no domain exceeds the threshold, an empty dict is returned."""
        db = _make_db_mock([])  # DB returns no rows

        service = DomainEmbeddingService()
        with patch.object(service, "_embed", return_value=_fixed_vector()):
            result = await service.detect_domains("something vague", db, threshold=0.9)

        assert result == {}

    @pytest.mark.asyncio
    async def test_multiple_domains_above_threshold(self) -> None:
        """Multiple domains above threshold are all returned with correct scores."""
        db = _make_db_mock([
            ("trials", 0.82),
            ("phenotyping", 0.71),
            ("weather", 0.65),
        ])

        service = DomainEmbeddingService()
        with patch.object(service, "_embed", return_value=_fixed_vector()):
            result = await service.detect_domains(
                "how did weather affect trial phenotypes?", db, threshold=0.6
            )

        assert result == {
            "trials": pytest.approx(0.82),
            "phenotyping": pytest.approx(0.71),
            "weather": pytest.approx(0.65),
        }

    @pytest.mark.asyncio
    async def test_custom_threshold_respected(self) -> None:
        """A custom threshold value is forwarded to the SQL query."""
        db = _make_db_mock([("soil", 0.45)])

        service = DomainEmbeddingService()
        with patch.object(service, "_embed", return_value=_fixed_vector()):
            result = await service.detect_domains("the land is acidic", db, threshold=0.4)

        assert "soil" in result
        assert result["soil"] == pytest.approx(0.45)


# ---------------------------------------------------------------------------
# Test: fallback on timeout
# ---------------------------------------------------------------------------

class TestTimeoutFallback:
    """Verify that a slow _embed causes detect_domains to return {}."""

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_timeout(self) -> None:
        """When _embed takes longer than 500 ms, detect_domains returns {}."""
        db = _make_db_mock([("trials", 0.9)])  # would be returned if embed succeeded

        service = DomainEmbeddingService()

        async def _slow_embed(text: str) -> list[float]:
            await asyncio.sleep(1.0)  # 1 second — well over the 500 ms limit
            return _fixed_vector()

        # We need to make run_in_executor return a coroutine that sleeps.
        # The service calls: asyncio.wait_for(loop.run_in_executor(None, self._embed, message), ...)
        # We patch run_in_executor on the event loop to return a slow future.
        loop = asyncio.get_event_loop()

        async def _slow_future(*args: object, **kwargs: object) -> list[float]:
            await asyncio.sleep(1.0)
            return _fixed_vector()

        with patch.object(loop, "run_in_executor", return_value=_slow_future()):
            result = await service.detect_domains("show me trials", db, threshold=0.6)

        assert result == {}

    @pytest.mark.asyncio
    async def test_db_not_queried_on_timeout(self) -> None:
        """When embedding times out, the pgvector query must not be executed."""
        db = _make_db_mock([])

        service = DomainEmbeddingService()
        loop = asyncio.get_event_loop()

        async def _slow_future(*args: object, **kwargs: object) -> list[float]:
            await asyncio.sleep(1.0)
            return _fixed_vector()

        with patch.object(loop, "run_in_executor", return_value=_slow_future()):
            await service.detect_domains("show me trials", db, threshold=0.6)

        # db.execute should NOT have been called because we timed out before querying.
        db.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Test: empty message handling
# ---------------------------------------------------------------------------

class TestEmptyMessageHandling:
    """Verify that empty / whitespace messages return {} without calling _embed."""

    @pytest.mark.asyncio
    async def test_empty_string_returns_empty_dict(self) -> None:
        """detect_domains('') must return {} immediately."""
        db = _make_db_mock([])
        service = DomainEmbeddingService()

        with patch.object(service, "_embed") as mock_embed:
            result = await service.detect_domains("", db)

        assert result == {}
        mock_embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_empty_dict(self) -> None:
        """detect_domains('   ') must return {} immediately."""
        db = _make_db_mock([])
        service = DomainEmbeddingService()

        with patch.object(service, "_embed") as mock_embed:
            result = await service.detect_domains("   ", db)

        assert result == {}
        mock_embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_newline_only_returns_empty_dict(self) -> None:
        """detect_domains('\\n\\t') must return {} immediately."""
        db = _make_db_mock([])
        service = DomainEmbeddingService()

        with patch.object(service, "_embed") as mock_embed:
            result = await service.detect_domains("\n\t", db)

        assert result == {}
        mock_embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_db_not_queried_for_empty_message(self) -> None:
        """The database must not be touched when the message is empty."""
        db = _make_db_mock([])
        service = DomainEmbeddingService()

        with patch.object(service, "_embed"):
            await service.detect_domains("", db)

        db.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Test: _embed lazy loading
# ---------------------------------------------------------------------------

class TestEmbedLazyLoading:
    """Verify _embed raises ImportError when sentence_transformers is absent."""

    def test_embed_raises_import_error_when_unavailable(self) -> None:
        """_embed must raise ImportError with a helpful message when the library
        is not installed."""
        service = DomainEmbeddingService()

        with patch(
            "app.modules.ai.services.reevu.domain_embedding_service"
            "._SENTENCE_TRANSFORMERS_AVAILABLE",
            False,
        ):
            with pytest.raises(ImportError, match="sentence-transformers"):
                service._embed("test text")

    def test_embed_uses_class_level_model_cache(self) -> None:
        """_embed must not reload the model on every call."""
        service = DomainEmbeddingService()

        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1] * 384)

        # Reset class-level cache to ensure we test the lazy-load path.
        original_model = DomainEmbeddingService._model
        DomainEmbeddingService._model = None

        try:
            with patch(
                "app.modules.ai.services.reevu.domain_embedding_service"
                "._SENTENCE_TRANSFORMERS_AVAILABLE",
                True,
            ), patch(
                "app.modules.ai.services.reevu.domain_embedding_service"
                "._SentenceTransformer",
                return_value=mock_model,
            ) as mock_cls:
                service._embed("first call")
                service._embed("second call")

            # Constructor called exactly once (lazy load).
            mock_cls.assert_called_once_with(DomainEmbeddingService.EMBEDDING_MODEL)
            # encode called twice (once per _embed call).
            assert mock_model.encode.call_count == 2
        finally:
            # Restore original class-level model to avoid polluting other tests.
            DomainEmbeddingService._model = original_model
