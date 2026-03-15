"""
AI provider and REEVU agent configuration models.

These tables persist organization-scoped provider setup, model preferences,
and agent defaults so REEVU configuration can move out of environment-only
settings over time.
"""

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


if TYPE_CHECKING:
	from app.models.core import Organization


class AIProvider(BaseModel):
	"""Organization-scoped provider credentials and routing defaults."""

	__tablename__ = "ai_providers"
	__table_args__ = (
		UniqueConstraint("organization_id", "provider_key", name="uq_ai_provider_org_key"),
		{"extend_existing": True},
	)

	organization_id: Mapped[int] = mapped_column(
		Integer, ForeignKey("organizations.id"), nullable=False, index=True
	)
	provider_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
	display_name: Mapped[str] = mapped_column(String(255), nullable=False)
	base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
	auth_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="api_key")
	# ADR-004: Values are now Fernet-encrypted on write via set_api_key().
	# Legacy plaintext values (without "enc:v1:" prefix) are returned as-is
	# on read, supporting zero-downtime migration.
	encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
	priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
	is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	is_byok_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

	@property
	def api_key_plaintext(self) -> str | None:
		"""Decrypt and return the API key.

		ADR-004: Handles both encrypted (``enc:v1:`` prefix) and
		legacy plaintext values transparently.
		"""
		from app.core.secrets import decrypt_value
		return decrypt_value(self.encrypted_api_key)

	def set_api_key(self, plaintext: str | None) -> None:
		"""Encrypt and store an API key.

		ADR-004: Applies Fernet encryption if ``BIJMANTRA_SECRET_KEY``
		is configured. Falls back to plaintext storage otherwise.
		"""
		from app.core.secrets import encrypt_value
		self.encrypted_api_key = encrypt_value(plaintext)

	organization: Mapped["Organization"] = relationship("Organization")
	models: Mapped[list["AIProviderModel"]] = relationship(
		"AIProviderModel",
		back_populates="provider",
		cascade="all, delete-orphan",
	)
	agent_settings: Mapped[list["ReevuAgentSetting"]] = relationship(
		"ReevuAgentSetting",
		back_populates="provider",
	)
	routing_policies: Mapped[list["ReevuRoutingPolicy"]] = relationship(
		"ReevuRoutingPolicy",
		back_populates="provider",
		foreign_keys="ReevuRoutingPolicy.preferred_provider_id",
	)


class AIProviderModel(BaseModel):
	"""Persisted model configuration for a provider within an organization."""

	__tablename__ = "ai_provider_models"
	__table_args__ = (
		UniqueConstraint("provider_id", "model_name", name="uq_ai_provider_model_name"),
		{"extend_existing": True},
	)

	organization_id: Mapped[int] = mapped_column(
		Integer, ForeignKey("organizations.id"), nullable=False, index=True
	)
	provider_id: Mapped[int] = mapped_column(
		Integer, ForeignKey("ai_providers.id"), nullable=False, index=True
	)
	model_name: Mapped[str] = mapped_column(String(255), nullable=False)
	display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
	capability_tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
	max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
	temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
	is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	is_streaming_supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

	organization: Mapped["Organization"] = relationship("Organization")
	provider: Mapped["AIProvider"] = relationship("AIProvider", back_populates="models")
	agent_settings: Mapped[list["ReevuAgentSetting"]] = relationship(
		"ReevuAgentSetting",
		back_populates="provider_model",
	)


class ReevuAgentSetting(BaseModel):
	"""Organization-scoped defaults for named REEVU agents."""

	__tablename__ = "reevu_agent_settings"
	__table_args__ = (
		UniqueConstraint("organization_id", "agent_key", name="uq_reevu_agent_org_key"),
		{"extend_existing": True},
	)

	organization_id: Mapped[int] = mapped_column(
		Integer, ForeignKey("organizations.id"), nullable=False, index=True
	)
	agent_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
	display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
	provider_id: Mapped[int | None] = mapped_column(
		Integer, ForeignKey("ai_providers.id"), nullable=True, index=True
	)
	provider_model_id: Mapped[int | None] = mapped_column(
		Integer, ForeignKey("ai_provider_models.id"), nullable=True, index=True
	)
	system_prompt_override: Mapped[str | None] = mapped_column(Text, nullable=True)
	tool_policy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
	default_task_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
	sampling_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
	max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
	capability_overrides: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
	prompt_mode_capabilities: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

	organization: Mapped["Organization"] = relationship("Organization")
	provider: Mapped["AIProvider | None"] = relationship("AIProvider", back_populates="agent_settings")
	provider_model: Mapped["AIProviderModel | None"] = relationship(
		"AIProviderModel",
		back_populates="agent_settings",
	)


class ReevuRoutingPolicy(BaseModel):
	"""Organization-scoped runtime routing defaults for named REEVU agents."""

	__tablename__ = "reevu_routing_policies"
	__table_args__ = (
		UniqueConstraint("organization_id", "agent_key", name="uq_reevu_routing_policy_org_key"),
		{"extend_existing": True},
	)

	organization_id: Mapped[int] = mapped_column(
		Integer, ForeignKey("organizations.id"), nullable=False, index=True
	)
	agent_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
	display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
	preferred_provider_id: Mapped[int | None] = mapped_column(
		Integer, ForeignKey("ai_providers.id"), nullable=True, index=True
	)
	preferred_provider_model_id: Mapped[int | None] = mapped_column(
		Integer, ForeignKey("ai_provider_models.id"), nullable=True, index=True
	)
	fallback_to_priority_order: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

	organization: Mapped["Organization"] = relationship("Organization")
	provider: Mapped[AIProvider | None] = relationship(
		"AIProvider",
		foreign_keys=[preferred_provider_id],
		back_populates="routing_policies",
	)
	provider_model: Mapped[AIProviderModel | None] = relationship(
		"AIProviderModel",
		foreign_keys=[preferred_provider_model_id],
	)