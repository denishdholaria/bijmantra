"""Admin API for org-scoped AI provider configuration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_organization_id
from app.core.database import get_db
from app.models.ai_configuration import AIProvider, AIProviderModel, ReevuAgentSetting, ReevuRoutingPolicy
from app.modules.ai.services.engine import get_llm_service
from app.modules.ai.services.model_catalog import ModelLifecycleStrategy, get_provider_model_catalog
from app.schemas.prompt_modes import PROMPT_MODE_DEFINITIONS, PromptModeDefinition
from app.schemas.functions import get_function_manifest


router = APIRouter(
	prefix="/ai-configuration",
	tags=["AI Configuration"],
	dependencies=[Depends(get_current_superuser)],
)


class AIProviderBase(BaseModel):
	provider_key: str = Field(..., min_length=1, max_length=50)
	display_name: str = Field(..., min_length=1, max_length=255)
	base_url: str | None = Field(default=None, max_length=500)
	auth_mode: str = Field(default="api_key", min_length=1, max_length=50)
	encrypted_api_key: str | None = None
	priority: int = 100
	is_enabled: bool = True
	is_byok_allowed: bool = True
	settings: dict[str, Any] | None = None


class AIProviderCreate(AIProviderBase):
	pass


class AIProviderUpdate(BaseModel):
	provider_key: str | None = Field(default=None, min_length=1, max_length=50)
	display_name: str | None = Field(default=None, min_length=1, max_length=255)
	base_url: str | None = Field(default=None, max_length=500)
	auth_mode: str | None = Field(default=None, min_length=1, max_length=50)
	encrypted_api_key: str | None = None
	priority: int | None = None
	is_enabled: bool | None = None
	is_byok_allowed: bool | None = None
	settings: dict[str, Any] | None = None


class AIProviderResponse(BaseModel):
	id: int
	organization_id: int
	provider_key: str
	display_name: str
	base_url: str | None
	auth_mode: str
	priority: int
	is_enabled: bool
	is_byok_allowed: bool
	settings: dict[str, Any] | None
	has_api_key: bool
	created_at: datetime
	updated_at: datetime

	model_config = ConfigDict(from_attributes=True)


class AIProviderModelBase(BaseModel):
	provider_id: int
	model_name: str = Field(..., min_length=1, max_length=255)
	display_name: str | None = Field(default=None, max_length=255)
	capability_tags: list[str] | None = None
	max_tokens: int | None = None
	temperature: float | None = None
	is_default: bool = False
	is_streaming_supported: bool = False
	is_active: bool = True
	settings: dict[str, Any] | None = None


class AIProviderModelCreate(AIProviderModelBase):
	pass


class AIProviderModelUpdate(BaseModel):
	provider_id: int | None = None
	model_name: str | None = Field(default=None, min_length=1, max_length=255)
	display_name: str | None = Field(default=None, max_length=255)
	capability_tags: list[str] | None = None
	max_tokens: int | None = None
	temperature: float | None = None
	is_default: bool | None = None
	is_streaming_supported: bool | None = None
	is_active: bool | None = None
	settings: dict[str, Any] | None = None


class AIProviderModelResponse(BaseModel):
	id: int
	organization_id: int
	provider_id: int
	model_name: str
	display_name: str | None
	capability_tags: list[str] | None
	max_tokens: int | None
	temperature: float | None
	is_default: bool
	is_streaming_supported: bool
	is_active: bool
	settings: dict[str, Any] | None
	created_at: datetime
	updated_at: datetime

	model_config = ConfigDict(from_attributes=True)


class OllamaModelListResponse(BaseModel):
	models: list[str]


class ReevuAgentSettingBase(BaseModel):
	agent_key: str = Field(..., min_length=1, max_length=100)
	display_name: str | None = Field(default=None, max_length=255)
	provider_id: int | None = None
	provider_model_id: int | None = None
	system_prompt_override: str | None = None
	tool_policy: dict[str, Any] | None = None
	default_task_context: dict[str, Any] | None = None
	sampling_temperature: float | None = None
	max_tokens: int | None = None
	capability_overrides: list[str] | None = None
	prompt_mode_capabilities: list[str] | None = None
	is_active: bool = True


class ReevuAgentSettingCreate(ReevuAgentSettingBase):
	pass


class ReevuAgentSettingUpdate(BaseModel):
	agent_key: str | None = Field(default=None, min_length=1, max_length=100)
	display_name: str | None = Field(default=None, max_length=255)
	provider_id: int | None = None
	provider_model_id: int | None = None
	system_prompt_override: str | None = None
	tool_policy: dict[str, Any] | None = None
	default_task_context: dict[str, Any] | None = None
	sampling_temperature: float | None = None
	max_tokens: int | None = None
	capability_overrides: list[str] | None = None
	prompt_mode_capabilities: list[str] | None = None
	is_active: bool | None = None


class ReevuAgentSettingResponse(BaseModel):
	id: int
	organization_id: int
	agent_key: str
	display_name: str | None
	provider_id: int | None
	provider_model_id: int | None
	system_prompt_override: str | None
	tool_policy: dict[str, Any] | None
	default_task_context: dict[str, Any] | None
	sampling_temperature: float | None
	max_tokens: int | None
	capability_overrides: list[str] | None
	prompt_mode_capabilities: list[str] | None
	is_active: bool
	created_at: datetime
	updated_at: datetime

	model_config = ConfigDict(from_attributes=True)


class ReevuRoutingPolicyBase(BaseModel):
	agent_key: str = Field(..., min_length=1, max_length=100)
	display_name: str | None = Field(default=None, max_length=255)
	preferred_provider_id: int | None = None
	preferred_provider_model_id: int | None = None
	fallback_to_priority_order: bool = True
	is_active: bool = True
	settings: dict[str, Any] | None = None


class ReevuRoutingPolicyUpsert(ReevuRoutingPolicyBase):
	pass


class ReevuRoutingPolicyResponse(BaseModel):
	id: int
	organization_id: int
	agent_key: str
	display_name: str | None
	preferred_provider_id: int | None
	preferred_provider_model_id: int | None
	fallback_to_priority_order: bool
	is_active: bool
	settings: dict[str, Any] | None
	created_at: datetime
	updated_at: datetime

	model_config = ConfigDict(from_attributes=True)


class CapabilityToolManifestItem(BaseModel):
	name: str
	label: str
	description: str


class CapabilityManifestCategory(BaseModel):
	id: str
	label: str
	description: str
	tools: list[CapabilityToolManifestItem]


class ModelCatalogPreset(BaseModel):
	label: str
	model_name: str
	display_name: str
	capability_tags: list[str]
	max_tokens: int
	temperature: float
	lifecycle: ModelLifecycleStrategy
	lifecycle_label: str


class ProviderModelCatalogEntry(BaseModel):
	provider_key: str
	provider_label: str
	provider_display_name: str
	base_url: str
	default_priority: int
	recommended_model: str
	model_lifecycle: ModelLifecycleStrategy
	model_lifecycle_label: str
	provider_preset_label: str
	model_presets: list[ModelCatalogPreset]


def _provider_response(provider: AIProvider) -> AIProviderResponse:
	return AIProviderResponse.model_validate(
		{
			"id": provider.id,
			"organization_id": provider.organization_id,
			"provider_key": provider.provider_key,
			"display_name": provider.display_name,
			"base_url": provider.base_url,
			"auth_mode": provider.auth_mode,
			"priority": provider.priority,
			"is_enabled": provider.is_enabled,
			"is_byok_allowed": provider.is_byok_allowed,
			"settings": provider.settings,
			"has_api_key": bool(provider.encrypted_api_key),
			"created_at": provider.created_at,
			"updated_at": provider.updated_at,
		}
	)


def _provider_payload_values(payload: AIProviderBase | AIProviderUpdate) -> tuple[dict[str, Any], str | None, bool]:
	values = payload.model_dump(exclude_unset=True)
	api_key = values.pop("encrypted_api_key", None)
	return values, api_key, "encrypted_api_key" in payload.model_fields_set


async def _get_provider_or_404(db: AsyncSession, organization_id: int, provider_id: int) -> AIProvider:
	result = await db.execute(
		select(AIProvider).where(
			AIProvider.id == provider_id,
			AIProvider.organization_id == organization_id,
		)
	)
	provider = result.scalar_one_or_none()
	if provider is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found")
	return provider


async def _get_ollama_provider(db: AsyncSession, organization_id: int) -> AIProvider | None:
	result = await db.execute(
		select(AIProvider).where(
			AIProvider.organization_id == organization_id,
			AIProvider.provider_key == "ollama",
		)
	)
	return result.scalar_one_or_none()


async def _get_model_or_404(db: AsyncSession, organization_id: int, model_id: int) -> AIProviderModel:
	result = await db.execute(
		select(AIProviderModel).where(
			AIProviderModel.id == model_id,
			AIProviderModel.organization_id == organization_id,
		)
	)
	model = result.scalar_one_or_none()
	if model is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider model not found")
	return model


async def _get_agent_setting_or_404(
	db: AsyncSession,
	organization_id: int,
	setting_id: int,
) -> ReevuAgentSetting:
	result = await db.execute(
		select(ReevuAgentSetting).where(
			ReevuAgentSetting.id == setting_id,
			ReevuAgentSetting.organization_id == organization_id,
		)
	)
	setting = result.scalar_one_or_none()
	if setting is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="REEVU agent setting not found")
	return setting


async def _get_routing_policy_or_404(
	db: AsyncSession,
	organization_id: int,
	agent_key: str,
) -> ReevuRoutingPolicy:
	result = await db.execute(
		select(ReevuRoutingPolicy).where(
			ReevuRoutingPolicy.organization_id == organization_id,
			ReevuRoutingPolicy.agent_key == agent_key,
		)
	)
	policy = result.scalar_one_or_none()
	if policy is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="REEVU routing policy not found")
	return policy


async def _validate_provider_reference(db: AsyncSession, organization_id: int, provider_id: int | None) -> None:
	if provider_id is None:
		return
	await _get_provider_or_404(db, organization_id, provider_id)


async def _validate_model_reference(
	db: AsyncSession,
	organization_id: int,
	provider_model_id: int | None,
) -> AIProviderModel | None:
	if provider_model_id is None:
		return None
	return await _get_model_or_404(db, organization_id, provider_model_id)


async def _validate_agent_links(
	db: AsyncSession,
	organization_id: int,
	provider_id: int | None,
	provider_model_id: int | None,
) -> None:
	await _validate_provider_reference(db, organization_id, provider_id)
	model = await _validate_model_reference(db, organization_id, provider_model_id)
	if provider_id is not None and model is not None and model.provider_id != provider_id:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="provider_model_id does not belong to provider_id",
		)


async def _validate_routing_policy_links(
	db: AsyncSession,
	organization_id: int,
	provider_id: int | None,
	provider_model_id: int | None,
) -> None:
	await _validate_agent_links(db, organization_id, provider_id, provider_model_id)


async def _normalize_default_model(
	db: AsyncSession,
	organization_id: int,
	provider_id: int,
	selected_model_id: int,
	make_default: bool,
) -> None:
	if not make_default:
		return
	await db.execute(
		update(AIProviderModel)
		.where(
			AIProviderModel.organization_id == organization_id,
			AIProviderModel.provider_id == provider_id,
			AIProviderModel.id != selected_model_id,
		)
		.values(is_default=False)
	)


def _commit_conflict(detail: str):
	return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


@router.get("/capabilities", response_model=list[CapabilityManifestCategory])
async def list_capabilities():
	return [CapabilityManifestCategory.model_validate(category) for category in get_function_manifest()]


@router.get("/prompt-modes", response_model=list[PromptModeDefinition])
async def list_prompt_modes():
	return list(PROMPT_MODE_DEFINITIONS)


@router.get("/model-catalog", response_model=list[ProviderModelCatalogEntry])
async def list_model_catalog():
	return [ProviderModelCatalogEntry.model_validate(entry) for entry in get_provider_model_catalog()]


@router.get("/ollama-models", response_model=OllamaModelListResponse)
async def list_ollama_models(
	organization_id: int = Depends(get_organization_id),
	db: AsyncSession = Depends(get_db),
):
	"""Return runtime model names available from the local Ollama endpoint."""
	ollama_provider = await _get_ollama_provider(db, organization_id)
	llm_service = get_llm_service()
	if ollama_provider and ollama_provider.base_url:
		from app.modules.ai.services.provider_types import LLMConfig, LLMProvider
		config = LLMConfig(
			provider=LLMProvider.OLLAMA,
			model=(ollama_provider.settings or {}).get("model") if isinstance(ollama_provider.settings, dict) else "",
			base_url=ollama_provider.base_url,
			available=False,
		)
		models = await llm_service.list_ollama_models(config)
	else:
		models = await llm_service.list_ollama_models()

	return OllamaModelListResponse(models=models)


@router.get("/providers", response_model=list[AIProviderResponse])
async def list_ai_providers(
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	result = await db.execute(
		select(AIProvider)
		.where(AIProvider.organization_id == organization_id)
		.order_by(AIProvider.priority.asc(), AIProvider.id.asc())
	)
	return [_provider_response(provider) for provider in result.scalars().all()]


@router.post("/providers", response_model=AIProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_provider(
	payload: AIProviderCreate,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	provider_values, api_key, _ = _provider_payload_values(payload)
	provider = AIProvider(organization_id=organization_id, **provider_values)
	if api_key is not None:
		provider.set_api_key(api_key)
	db.add(provider)
	try:
		await db.commit()
	except IntegrityError as exc:
		await db.rollback()
		raise _commit_conflict("AI provider already exists for this organization") from exc
	await db.refresh(provider)
	return _provider_response(provider)


@router.get("/providers/{provider_id}", response_model=AIProviderResponse)
async def get_ai_provider(
	provider_id: int,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	provider = await _get_provider_or_404(db, organization_id, provider_id)
	return _provider_response(provider)


@router.patch("/providers/{provider_id}", response_model=AIProviderResponse)
async def update_ai_provider(
	provider_id: int,
	payload: AIProviderUpdate,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	provider = await _get_provider_or_404(db, organization_id, provider_id)
	provider_values, api_key, api_key_supplied = _provider_payload_values(payload)
	for field_name, value in provider_values.items():
		setattr(provider, field_name, value)
	if api_key_supplied:
		provider.set_api_key(api_key)
	try:
		await db.commit()
	except IntegrityError as exc:
		await db.rollback()
		raise _commit_conflict("AI provider update conflicts with an existing configuration") from exc
	await db.refresh(provider)
	return _provider_response(provider)


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_provider(
	provider_id: int,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	provider = await _get_provider_or_404(db, organization_id, provider_id)
	await db.delete(provider)
	await db.commit()
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/models", response_model=list[AIProviderModelResponse])
async def list_ai_provider_models(
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	result = await db.execute(
		select(AIProviderModel)
		.where(AIProviderModel.organization_id == organization_id)
		.order_by(AIProviderModel.provider_id.asc(), AIProviderModel.id.asc())
	)
	return [AIProviderModelResponse.model_validate(model) for model in result.scalars().all()]


@router.post("/models", response_model=AIProviderModelResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_provider_model(
	payload: AIProviderModelCreate,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	await _validate_provider_reference(db, organization_id, payload.provider_id)
	model = AIProviderModel(organization_id=organization_id, **payload.model_dump())
	db.add(model)
	try:
		await db.flush()
		await _normalize_default_model(db, organization_id, model.provider_id, model.id, model.is_default)
		await db.commit()
	except IntegrityError as exc:
		await db.rollback()
		raise _commit_conflict("AI provider model already exists for this provider") from exc
	await db.refresh(model)
	return AIProviderModelResponse.model_validate(model)


@router.get("/models/{model_id}", response_model=AIProviderModelResponse)
async def get_ai_provider_model(
	model_id: int,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	model = await _get_model_or_404(db, organization_id, model_id)
	return AIProviderModelResponse.model_validate(model)


@router.patch("/models/{model_id}", response_model=AIProviderModelResponse)
async def update_ai_provider_model(
	model_id: int,
	payload: AIProviderModelUpdate,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	model = await _get_model_or_404(db, organization_id, model_id)
	update_data = payload.model_dump(exclude_unset=True)
	provider_id = update_data.get("provider_id", model.provider_id)
	await _validate_provider_reference(db, organization_id, provider_id)
	for field_name, value in update_data.items():
		setattr(model, field_name, value)
	try:
		await db.flush()
		await _normalize_default_model(db, organization_id, model.provider_id, model.id, model.is_default)
		await db.commit()
	except IntegrityError as exc:
		await db.rollback()
		raise _commit_conflict("AI provider model update conflicts with an existing configuration") from exc
	await db.refresh(model)
	return AIProviderModelResponse.model_validate(model)


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_provider_model(
	model_id: int,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	model = await _get_model_or_404(db, organization_id, model_id)
	await db.delete(model)
	await db.commit()
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/agent-settings", response_model=list[ReevuAgentSettingResponse])
async def list_reevu_agent_settings(
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	result = await db.execute(
		select(ReevuAgentSetting)
		.where(ReevuAgentSetting.organization_id == organization_id)
		.order_by(ReevuAgentSetting.agent_key.asc(), ReevuAgentSetting.id.asc())
	)
	return [ReevuAgentSettingResponse.model_validate(setting) for setting in result.scalars().all()]


@router.get("/routing-policies", response_model=list[ReevuRoutingPolicyResponse])
async def list_reevu_routing_policies(
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	result = await db.execute(
		select(ReevuRoutingPolicy)
		.where(ReevuRoutingPolicy.organization_id == organization_id)
		.order_by(ReevuRoutingPolicy.agent_key.asc(), ReevuRoutingPolicy.id.asc())
	)
	return [ReevuRoutingPolicyResponse.model_validate(policy) for policy in result.scalars().all()]


@router.put("/routing-policies/{agent_key}", response_model=ReevuRoutingPolicyResponse)
async def upsert_reevu_routing_policy(
	agent_key: str,
	payload: ReevuRoutingPolicyUpsert,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	if payload.agent_key != agent_key:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="agent_key path and payload must match")

	await _validate_routing_policy_links(
		db,
		organization_id,
		payload.preferred_provider_id,
		payload.preferred_provider_model_id,
	)

	result = await db.execute(
		select(ReevuRoutingPolicy).where(
			ReevuRoutingPolicy.organization_id == organization_id,
			ReevuRoutingPolicy.agent_key == agent_key,
		)
	)
	policy = result.scalar_one_or_none()

	if policy is None:
		policy = ReevuRoutingPolicy(organization_id=organization_id, **payload.model_dump())
		db.add(policy)
	else:
		for field_name, value in payload.model_dump().items():
			setattr(policy, field_name, value)

	try:
		await db.commit()
	except IntegrityError as exc:
		await db.rollback()
		raise _commit_conflict("REEVU routing policy update conflicts with an existing configuration") from exc
	await db.refresh(policy)
	return ReevuRoutingPolicyResponse.model_validate(policy)


@router.delete("/routing-policies/{agent_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reevu_routing_policy(
	agent_key: str,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	policy = await _get_routing_policy_or_404(db, organization_id, agent_key)
	await db.delete(policy)
	await db.commit()
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
	"/agent-settings",
	response_model=ReevuAgentSettingResponse,
	status_code=status.HTTP_201_CREATED,
)
async def create_reevu_agent_setting(
	payload: ReevuAgentSettingCreate,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	await _validate_agent_links(db, organization_id, payload.provider_id, payload.provider_model_id)
	setting = ReevuAgentSetting(organization_id=organization_id, **payload.model_dump())
	db.add(setting)
	try:
		await db.commit()
	except IntegrityError as exc:
		await db.rollback()
		raise _commit_conflict("REEVU agent setting already exists for this organization") from exc
	await db.refresh(setting)
	return ReevuAgentSettingResponse.model_validate(setting)


@router.get("/agent-settings/{setting_id}", response_model=ReevuAgentSettingResponse)
async def get_reevu_agent_setting(
	setting_id: int,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	setting = await _get_agent_setting_or_404(db, organization_id, setting_id)
	return ReevuAgentSettingResponse.model_validate(setting)


@router.patch("/agent-settings/{setting_id}", response_model=ReevuAgentSettingResponse)
async def update_reevu_agent_setting(
	setting_id: int,
	payload: ReevuAgentSettingUpdate,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	setting = await _get_agent_setting_or_404(db, organization_id, setting_id)
	update_data = payload.model_dump(exclude_unset=True)
	provider_id = update_data.get("provider_id", setting.provider_id)
	provider_model_id = update_data.get("provider_model_id", setting.provider_model_id)
	await _validate_agent_links(db, organization_id, provider_id, provider_model_id)
	for field_name, value in update_data.items():
		setattr(setting, field_name, value)
	try:
		await db.commit()
	except IntegrityError as exc:
		await db.rollback()
		raise _commit_conflict("REEVU agent setting update conflicts with an existing configuration") from exc
	await db.refresh(setting)
	return ReevuAgentSettingResponse.model_validate(setting)


@router.delete("/agent-settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reevu_agent_setting(
	setting_id: int,
	db: AsyncSession = Depends(get_db),
	organization_id: int = Depends(get_organization_id),
):
	setting = await _get_agent_setting_or_404(db, organization_id, setting_id)
	await db.delete(setting)
	await db.commit()
	return Response(status_code=status.HTTP_204_NO_CONTENT)