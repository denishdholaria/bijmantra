"""
Demo AI provider seeder.

Keeps development demo credentials on the same local REEVU runtime path as the
admin account, without copying cloud credentials into demo-owned records.
"""

import logging

from sqlalchemy.orm import selectinload

from app.core.config import settings

from .base import BaseSeeder, register_seeder
from .demo_germplasm import get_or_create_demo_organization


logger = logging.getLogger(__name__)


@register_seeder
class DemoAIProviderSeeder(BaseSeeder):
    """Seed a local Ollama REEVU provider for the Demo Organization."""

    name = "demo_ai_provider"
    description = "Demo Organization REEVU provider configuration for local Ollama"
    is_demo_data = True

    def seed(self) -> int:
        """Ensure demo users can use the same local Ollama runtime as admin."""
        from app.models.ai_configuration import AIProvider, AIProviderModel
        from app.models.core import Organization

        demo_org = get_or_create_demo_organization(self.db)
        source_provider = (
            self.db.query(AIProvider)
            .options(selectinload(AIProvider.models))
            .join(Organization, AIProvider.organization_id == Organization.id)
            .filter(
                AIProvider.provider_key == "ollama",
                AIProvider.is_enabled.is_(True),
                AIProvider.organization_id != demo_org.id,
            )
            .order_by(
                (Organization.name == "BijMantra HQ").desc(),
                AIProvider.id.asc(),
            )
            .first()
        )

        provider_values = self._provider_values(source_provider)
        model_values = self._model_values(source_provider)
        if not provider_values or not model_values:
            logger.info("Skipping demo AI provider seed: no local Ollama provider/model available")
            return 0

        count = 0
        demo_provider = (
            self.db.query(AIProvider)
            .filter(
                AIProvider.organization_id == demo_org.id,
                AIProvider.provider_key == "ollama",
            )
            .first()
        )

        if demo_provider is None:
            demo_provider = AIProvider(
                organization_id=demo_org.id,
                provider_key="ollama",
                **provider_values,
            )
            self.db.add(demo_provider)
            self.db.flush()
            count += 1
        else:
            count += self._update_provider(demo_provider, provider_values)

        existing_models = {
            model.model_name: model
            for model in self.db.query(AIProviderModel)
            .filter(
                AIProviderModel.organization_id == demo_org.id,
                AIProviderModel.provider_id == demo_provider.id,
            )
            .all()
        }

        for model_name, values in model_values.items():
            existing_model = existing_models.get(model_name)
            if existing_model is None:
                self.db.add(
                    AIProviderModel(
                        organization_id=demo_org.id,
                        provider_id=demo_provider.id,
                        model_name=model_name,
                        **values,
                    )
                )
                count += 1
            else:
                count += self._update_model(existing_model, values)

        self.db.commit()
        logger.info("Seeded demo AI provider changes: %s", count)
        return count

    def clear(self) -> int:
        """Remove the demo-owned local Ollama provider configuration."""
        from app.models.ai_configuration import AIProvider
        from app.models.core import Organization

        demo_org = (
            self.db.query(Organization)
            .filter(Organization.name == "Demo Organization")
            .first()
        )
        if demo_org is None:
            return 0

        provider = (
            self.db.query(AIProvider)
            .filter(
                AIProvider.organization_id == demo_org.id,
                AIProvider.provider_key == "ollama",
            )
            .first()
        )
        if provider is None:
            return 0

        self.db.delete(provider)
        self.db.commit()
        return 1

    def _provider_values(self, source_provider):
        base_url = getattr(source_provider, "base_url", None) or settings.OLLAMA_HOST
        if not base_url:
            return None

        return {
            "display_name": getattr(source_provider, "display_name", None) or "Ollama (Local)",
            "base_url": base_url,
            "auth_mode": getattr(source_provider, "auth_mode", None) or "api_key",
            "encrypted_api_key": None,
            "priority": getattr(source_provider, "priority", None) or 70,
            "is_enabled": True,
            "is_byok_allowed": True,
            "settings": getattr(source_provider, "settings", None),
        }

    def _model_values(self, source_provider) -> dict[str, dict]:
        source_models = [
            model
            for model in getattr(source_provider, "models", []) or []
            if getattr(model, "is_active", False)
        ]

        if not source_models and settings.OLLAMA_MODEL:
            return {
                settings.OLLAMA_MODEL: {
                    "display_name": settings.OLLAMA_MODEL,
                    "capability_tags": ["local", "chat"],
                    "max_tokens": None,
                    "temperature": None,
                    "is_default": True,
                    "is_streaming_supported": True,
                    "is_active": True,
                    "settings": None,
                }
            }

        values: dict[str, dict] = {}
        for index, model in enumerate(sorted(source_models, key=lambda item: (not item.is_default, item.id))):
            model_name = getattr(model, "model_name", None)
            if not model_name:
                continue
            values[model_name] = {
                "display_name": getattr(model, "display_name", None) or model_name,
                "capability_tags": getattr(model, "capability_tags", None),
                "max_tokens": getattr(model, "max_tokens", None),
                "temperature": getattr(model, "temperature", None),
                "is_default": bool(getattr(model, "is_default", False) or index == 0),
                "is_streaming_supported": bool(getattr(model, "is_streaming_supported", False)),
                "is_active": True,
                "settings": getattr(model, "settings", None),
            }
        return values

    def _update_provider(self, provider, values: dict) -> int:
        changed = False
        for key, value in values.items():
            if getattr(provider, key) != value:
                setattr(provider, key, value)
                changed = True
        return 1 if changed else 0

    def _update_model(self, model, values: dict) -> int:
        changed = False
        for key, value in values.items():
            if getattr(model, key) != value:
                setattr(model, key, value)
                changed = True
        return 1 if changed else 0
