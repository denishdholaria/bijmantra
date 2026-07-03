"""
REEVU Domain Embedding Service

Provides embedding-based semantic domain detection using sentence-transformers
and pgvector cosine similarity. Runs alongside keyword detection as a hybrid
approach for natural-language domain routing.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from app.modules.ai.services.reevu.domain_corpus import DOMAIN_CORPUS


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)

# Guard the sentence_transformers import — it lives in the optional `ml` extra.
try:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer

    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    _SentenceTransformer = None  # type: ignore[assignment,misc]
    _SENTENCE_TRANSFORMERS_AVAILABLE = False


class DomainEmbeddingService:
    """Embedding-based semantic domain detection using pgvector.

    Prototype embeddings (mean of all corpus examples per domain) are stored
    in the ``reevu_domain_prototypes`` table and queried at runtime using
    pgvector cosine similarity.

    Usage::

        service = DomainEmbeddingService()
        await service.initialize(db)          # once at startup
        scores = await service.detect_domains(message, db)
    """

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    PROTOTYPE_TABLE = "reevu_domain_prototypes"
    CACHE_TTL_SECONDS = 86400  # 24 hours
    EMBED_TIMEOUT_SECONDS = 0.5  # 500 ms

    # Class-level lazy model cache — shared across all instances.
    _model: "_SentenceTransformer | None" = None  # type: ignore[type-arg]

    # ── Public API ────────────────────────────────────────────────────────────

    async def initialize(self, db: "AsyncSession") -> None:
        """Embed all domain corpus examples and upsert prototypes into pgvector.

        Computes the mean embedding per domain (prototype = mean of all example
        embeddings) and upserts into ``reevu_domain_prototypes``.

        Args:
            db: An open async SQLAlchemy session.
        """
        from sqlalchemy import text

        domains = list(DOMAIN_CORPUS.keys())
        logger.info(
            "DomainEmbeddingService.initialize: embedding %d domains", len(domains)
        )

        upserted = 0
        for domain, examples in DOMAIN_CORPUS.items():
            if not examples:
                logger.warning("Domain '%s' has no corpus examples — skipping", domain)
                continue

            # Embed all examples and compute the mean prototype vector.
            embeddings = [self._embed(ex) for ex in examples]
            n = len(embeddings)
            dim = len(embeddings[0])
            prototype = [
                sum(embeddings[i][j] for i in range(n)) / n for j in range(dim)
            ]

            # Upsert into reevu_domain_prototypes.
            await db.execute(
                text(
                    """
                    INSERT INTO reevu_domain_prototypes
                        (domain, embedding, example_count, updated_at)
                    VALUES
                        (:domain, :embedding, :example_count, NOW())
                    ON CONFLICT (domain) DO UPDATE
                        SET embedding     = EXCLUDED.embedding,
                            example_count = EXCLUDED.example_count,
                            updated_at    = NOW()
                    """
                ),
                {
                    "domain": domain,
                    "embedding": str(prototype),
                    "example_count": n,
                },
            )
            upserted += 1

        await db.commit()
        logger.info(
            "DomainEmbeddingService.initialize: upserted %d domain prototypes",
            upserted,
        )

    async def detect_domains(
        self,
        message: str,
        db: "AsyncSession",
        threshold: float = 0.6,
    ) -> dict[str, float]:
        """Return domain → similarity score for domains above threshold.

        Embeds *message* and queries pgvector for cosine similarity against all
        stored prototypes.  Returns an empty dict if:
        - *message* is empty / whitespace-only
        - embedding computation exceeds 500 ms
        - any unexpected error occurs

        Args:
            message:   The user's query string.
            db:        An open async SQLAlchemy session.
            threshold: Minimum cosine similarity to include a domain (default 0.6).

        Returns:
            ``{domain: score}`` for domains where ``score >= threshold``.
        """
        if not message or not message.strip():
            return {}

        # ── Embed with 500 ms timeout ─────────────────────────────────────────
        try:
            query_vector = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, self._embed, message),
                timeout=self.EMBED_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "DomainEmbeddingService.detect_domains: embedding timed out after %.0fms "
                "— falling through to keyword detection",
                self.EMBED_TIMEOUT_SECONDS * 1000,
            )
            return {}
        except Exception:
            logger.exception(
                "DomainEmbeddingService.detect_domains: embedding failed — "
                "falling through to keyword detection"
            )
            return {}

        # ── pgvector cosine similarity query ──────────────────────────────────
        from sqlalchemy import text

        try:
            result = await db.execute(
                text(
                    """
                    SELECT domain,
                           1 - (embedding <=> CAST(:query_vector AS vector)) AS similarity
                    FROM   reevu_domain_prototypes
                    WHERE  1 - (embedding <=> CAST(:query_vector AS vector)) >= :threshold
                    ORDER  BY similarity DESC
                    """
                ),
                {
                    "query_vector": str(query_vector),
                    "threshold": threshold,
                },
            )
            rows = result.fetchall()
        except Exception:
            logger.exception(
                "DomainEmbeddingService.detect_domains: pgvector query failed"
            )
            return {}

        return {row[0]: float(row[1]) for row in rows}

    def _embed(self, text: str) -> list[float]:
        """Embed *text* using the local sentence-transformer model.

        The model is lazy-loaded on first call and cached at the class level.

        Args:
            text: The string to embed.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            ImportError: If ``sentence-transformers`` is not installed.
        """
        if not _SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with: uv sync --extra ml"
            )

        if DomainEmbeddingService._model is None:
            logger.info(
                "DomainEmbeddingService._embed: loading model '%s'",
                self.EMBEDDING_MODEL,
            )
            DomainEmbeddingService._model = _SentenceTransformer(self.EMBEDDING_MODEL)

        embedding = DomainEmbeddingService._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
