"""
Session service for REEVU chat.

Handles request-scoped session setup: LLM service instantiation, capability registry,
agent settings, quota enforcement, and LLM routing state extraction.
Extracted from backend/app/api/v2/chat.py.
"""

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.core import User
from app.modules.ai.service import get_ai_provider_service
from app.modules.ai.services.capability_registry import CapabilityRegistry
from app.modules.ai.services.engine import MultiTierLLMService, get_llm_service
from app.modules.ai.services.memory import BreedingVectorService, EmbeddingService, VectorStoreService
from app.modules.ai.services.quota import AIQuotaService

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing request-scoped session state."""

    # ------------------------------------------------------------------ #
    # LLM service                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def get_request_llm_service(
        db: AsyncSession,
        current_user: User,
    ) -> Any:
        """Create a request-scoped LLM service using persisted org config when present."""
        base_service = get_llm_service()
        if not isinstance(base_service, MultiTierLLMService):
            return base_service

        registry = await get_ai_provider_service().load_registry(
            db,
            int(current_user.organization_id),
            is_superuser=bool(getattr(current_user, "is_superuser", False)),
        )
        llm_service = MultiTierLLMService()
        llm_service.set_provider_registry(registry)
        return llm_service

    # ------------------------------------------------------------------ #
    # Capability registry / agent settings                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def get_request_agent_setting(
        db: AsyncSession,
        current_user: User,
    ) -> Any | None:
        """Load per-org agent settings (prompt-mode overrides, capability flags)."""
        provider_service = get_ai_provider_service()
        get_agent_setting = getattr(provider_service, "get_agent_setting", None)
        if get_agent_setting is None:
            return None

        try:
            return await get_agent_setting(
                db,
                int(current_user.organization_id),
                is_superuser=bool(getattr(current_user, "is_superuser", False)),
            )
        except Exception as exc:
            logger.warning(
                "[REEVU] Prompt-mode agent settings unavailable, continuing without overrides: %s",
                exc,
            )
            return None

    @staticmethod
    async def get_request_capability_registry(
        db: AsyncSession,
        current_user: User,
    ) -> CapabilityRegistry:
        """Build a CapabilityRegistry scoped to the current request."""
        agent_setting = await SessionService.get_request_agent_setting(db, current_user)
        if agent_setting is None:
            return CapabilityRegistry()
        return CapabilityRegistry.from_agent_setting(agent_setting)

    # ------------------------------------------------------------------ #
    # Vector / breeding service                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_embedding_service() -> EmbeddingService:
        """Return the process-level singleton EmbeddingService."""
        # Mirrors the module-level singleton pattern in chat.py.
        if not hasattr(SessionService, "_embedding_service") or SessionService._embedding_service is None:
            SessionService._embedding_service = EmbeddingService()
        return SessionService._embedding_service

    @staticmethod
    async def get_vector_store(db: AsyncSession) -> VectorStoreService:
        """Create a request-scoped VectorStoreService."""
        embedding_service = SessionService.get_embedding_service()
        return VectorStoreService(db, embedding_service)

    @staticmethod
    async def get_breeding_service(db: AsyncSession) -> BreedingVectorService:
        """Create a request-scoped BreedingVectorService."""
        vector_store = await SessionService.get_vector_store(db)
        return BreedingVectorService(vector_store)

    # ------------------------------------------------------------------ #
    # Quota enforcement                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def enforce_quota(
        db: AsyncSession,
        organization_id: int,
        user_api_key: str | None,
    ) -> None:
        """Check and increment the daily AI quota unless the user supplies their own key."""
        if user_api_key:
            return

        try:
            await AIQuotaService.check_and_increment_usage(
                db,
                organization_id=organization_id,
                increment=True,
            )
        except HTTPException:
            raise
        except Exception as quota_error:
            logger.warning("[REEVU] Quota check skipped due to error: %s", quota_error)
            try:
                await db.rollback()
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    # LLM routing state helpers                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_llm_routing_state(llm_service: Any) -> dict[str, Any]:
        """Extract request-scoped routing state from the active LLM service."""
        get_routing_state = getattr(llm_service, "get_routing_state", None)
        if callable(get_routing_state):
            return get_routing_state()

        registry = getattr(llm_service, "registry", None) or getattr(llm_service, "_registry", None)
        if registry is not None:
            registry_get_routing_state = getattr(registry, "get_routing_state", None)
            if callable(registry_get_routing_state):
                return registry_get_routing_state()

        return {
            "preferred_provider": None,
            "preferred_provider_only": False,
            "selection_mode": "priority_order",
        }

    @staticmethod
    def derive_routing_decisions(
        *,
        requested_provider: str | None,
        actual_provider: str | None,
        routing_state: dict[str, Any] | None,
    ) -> list[str]:
        """Summarize how runtime routing resolved a chat request."""
        decisions: list[str] = []
        normalized_requested = requested_provider.lower() if requested_provider else None
        normalized_actual = actual_provider.lower() if actual_provider else None
        normalized_preferred = None
        preferred_provider_only = False

        if routing_state:
            preferred_value = routing_state.get("preferred_provider")
            if isinstance(preferred_value, str) and preferred_value:
                normalized_preferred = preferred_value.lower()
            preferred_provider_only = bool(routing_state.get("preferred_provider_only"))

        if normalized_requested:
            decisions.append("request_override")
            if normalized_actual == normalized_requested:
                decisions.append("request_override_applied")
            else:
                decisions.append("request_override_fallback")
        elif normalized_preferred:
            decisions.append(
                "managed_preferred_only" if preferred_provider_only else "managed_preferred"
            )
            if normalized_actual == normalized_preferred:
                decisions.append("managed_preferred_hit")
            else:
                decisions.append("managed_preferred_miss")
        else:
            decisions.append("priority_order")

        if normalized_actual == "template":
            decisions.append("template_fallback")

        return decisions

    # ------------------------------------------------------------------ #
    # Database authority                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_database_authority() -> dict[str, Any]:
        """Return a sanitized summary of the active database authority."""
        if settings.USE_SQLITE:
            return {
                "backend": "sqlite",
                "server": None,
                "port": None,
                "database": "bijmantra.db",
                "user": None,
                "url_redacted": "sqlite+aiosqlite:///./bijmantra.db",
            }

        return {
            "backend": "postgresql",
            "server": settings.POSTGRES_SERVER,
            "port": settings.POSTGRES_PORT,
            "database": settings.POSTGRES_DB,
            "user": settings.POSTGRES_USER,
            "url_redacted": (
                f"postgresql+asyncpg://{settings.POSTGRES_USER}:***@"
                f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
            ),
        }
