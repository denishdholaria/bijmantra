from cryptography.fernet import Fernet
from sqlalchemy import select

from app.models.ai_configuration import AIProvider
from app.models.core import Organization


async def test_ai_configuration_requires_superuser(authenticated_client):
	response = await authenticated_client.get("/api/v2/ai-configuration/providers")
	assert response.status_code == 403

	capabilities_response = await authenticated_client.get("/api/v2/ai-configuration/capabilities")
	assert capabilities_response.status_code == 403

	model_catalog_response = await authenticated_client.get("/api/v2/ai-configuration/model-catalog")
	assert model_catalog_response.status_code == 403


async def test_ai_capability_manifest_lists_grouped_tools(superuser_client):
	response = await superuser_client.get("/api/v2/ai-configuration/capabilities")
	assert response.status_code == 200

	manifest = response.json()
	assert len(manifest) >= 4
	assert manifest[0]["id"] == "germplasm_breeding"
	search_trials = next(
		tool
		for category in manifest
		for tool in category["tools"]
		if tool["name"] == "search_trials"
	)
	assert search_trials["label"] == "Search Trials"


async def test_ai_prompt_mode_manifest_lists_available_modes(superuser_client):
	response = await superuser_client.get("/api/v2/ai-configuration/prompt-modes")
	assert response.status_code == 200

	modes = response.json()
	assert [mode["id"] for mode in modes] == [
		"breeding_mode",
		"genomics_mode",
		"environment_mode",
		"compliance_mode",
	]


async def test_ai_model_catalog_lists_expected_provider_contract(superuser_client):
	response = await superuser_client.get("/api/v2/ai-configuration/model-catalog")
	assert response.status_code == 200

	catalog = response.json()
	assert [entry["provider_key"] for entry in catalog] == ["google", "groq", "functiongemma", "openai", "anthropic", "huggingface", "ollama"]

	valid_lifecycle_values = {
		"provider_alias_latest",
		"provider_named_family",
		"managed_named_model",
		"builtin_template",
	}

	for entry in catalog:
		assert set(entry) == {
			"provider_key",
			"provider_label",
			"provider_display_name",
			"base_url",
			"default_priority",
			"recommended_model",
			"model_lifecycle",
			"model_lifecycle_label",
			"provider_preset_label",
			"model_presets",
		}
		assert entry["provider_label"] == entry["provider_display_name"]
		assert isinstance(entry["base_url"], str)
		assert isinstance(entry["default_priority"], int)
		assert entry["recommended_model"]
		assert entry["model_lifecycle"] in valid_lifecycle_values
		assert entry["model_lifecycle_label"]
		assert entry["provider_preset_label"]
		assert len(entry["model_presets"]) == 1

		preset = entry["model_presets"][0]
		assert set(preset) == {
			"label",
			"model_name",
			"display_name",
			"capability_tags",
			"max_tokens",
			"temperature",
			"lifecycle",
			"lifecycle_label",
		}
		assert preset["label"]
		assert preset["model_name"] == entry["recommended_model"]
		assert preset["display_name"]
		assert preset["capability_tags"] == ["chat", "reasoning", "streaming"]
		assert preset["max_tokens"] == 8192
		assert preset["temperature"] == 0.7
		assert preset["lifecycle"] == entry["model_lifecycle"]
		assert preset["lifecycle"] in valid_lifecycle_values
		assert preset["lifecycle_label"] == entry["model_lifecycle_label"]

	google = next(entry for entry in catalog if entry["provider_key"] == "google")
	assert google["provider_label"] == "Google Gemini"
	assert google["recommended_model"] == "gemini-flash-latest"
	assert google["model_lifecycle"] == "provider_alias_latest"
	assert google["provider_preset_label"] == "Google Gemini"
	assert google["model_presets"][0]["model_name"] == "gemini-flash-latest"

	functiongemma = next(entry for entry in catalog if entry["provider_key"] == "functiongemma")
	assert functiongemma["provider_label"] == "FunctionGemma"
	assert functiongemma["recommended_model"] == "google/functiongemma-270m-it"
	assert functiongemma["model_lifecycle"] == "managed_named_model"

	huggingface = next(entry for entry in catalog if entry["provider_key"] == "huggingface")
	assert huggingface["provider_label"] == "HuggingFace Inference"
	assert huggingface["recommended_model"] == "mistralai/Mistral-7B-Instruct-v0.2"
	assert huggingface["model_lifecycle"] == "managed_named_model"

	ollama = next(entry for entry in catalog if entry["provider_key"] == "ollama")
	assert ollama["provider_label"] == "Ollama (Local)"
	assert ollama["recommended_model"] == "llama3.2:3b"
	assert ollama["model_lifecycle"] == "managed_named_model"
	assert ollama["provider_preset_label"] == "Ollama (Local, Advanced)"


async def test_ai_provider_crud_round_trip(superuser_client):
	create_response = await superuser_client.post(
		"/api/v2/ai-configuration/providers",
		json={
			"provider_key": "openai",
			"display_name": "OpenAI",
			"encrypted_api_key": "secret-key",
			"priority": 5,
			"settings": {"region": "global"},
		},
	)
	assert create_response.status_code == 201
	created = create_response.json()
	provider_id = created["id"]
	assert created["provider_key"] == "openai"
	assert created["has_api_key"] is True

	list_response = await superuser_client.get("/api/v2/ai-configuration/providers")
	assert list_response.status_code == 200
	providers = list_response.json()
	assert [provider["id"] for provider in providers] == [provider_id]

	update_response = await superuser_client.patch(
		f"/api/v2/ai-configuration/providers/{provider_id}",
		json={"display_name": "OpenAI Primary", "is_enabled": False},
	)
	assert update_response.status_code == 200
	updated = update_response.json()
	assert updated["display_name"] == "OpenAI Primary"
	assert updated["is_enabled"] is False

	delete_response = await superuser_client.delete(f"/api/v2/ai-configuration/providers/{provider_id}")
	assert delete_response.status_code == 204

	get_response = await superuser_client.get(f"/api/v2/ai-configuration/providers/{provider_id}")
	assert get_response.status_code == 404


async def test_ai_provider_write_paths_encrypt_api_keys_when_secret_key_is_configured(
	superuser_client,
	async_db_session,
	monkeypatch,
):
	fernet_key = Fernet.generate_key().decode()
	monkeypatch.setenv("BIJMANTRA_SECRET_KEY", fernet_key)
	monkeypatch.setattr("app.core.secrets._fernet", None)

	create_response = await superuser_client.post(
		"/api/v2/ai-configuration/providers",
		json={
			"provider_key": "openai",
			"display_name": "OpenAI",
			"encrypted_api_key": "secret-key",
			"priority": 5,
		},
	)
	assert create_response.status_code == 201
	provider_id = create_response.json()["id"]

	created = await async_db_session.scalar(select(AIProvider).where(AIProvider.id == provider_id))
	assert created is not None
	assert created.encrypted_api_key is not None
	assert created.encrypted_api_key.startswith("enc:v1:")
	assert created.api_key_plaintext == "secret-key"

	update_response = await superuser_client.patch(
		f"/api/v2/ai-configuration/providers/{provider_id}",
		json={"encrypted_api_key": "rotated-secret"},
	)
	assert update_response.status_code == 200

	await async_db_session.refresh(created)
	assert created.encrypted_api_key is not None
	assert created.encrypted_api_key.startswith("enc:v1:")
	assert created.api_key_plaintext == "rotated-secret"

	delete_response = await superuser_client.delete(
		f"/api/v2/ai-configuration/providers/{provider_id}"
	)
	assert delete_response.status_code == 204


async def test_ai_provider_list_is_scoped_to_current_org(superuser_client, async_db_session):
	foreign_org = Organization(name="Foreign AI Org")
	async_db_session.add(foreign_org)
	await async_db_session.flush()
	async_db_session.add(
		AIProvider(
			organization_id=foreign_org.id,
			provider_key="anthropic",
			display_name="Anthropic",
			auth_mode="api_key",
			priority=1,
			is_enabled=True,
			is_byok_allowed=True,
		)
	)
	await async_db_session.commit()

	create_response = await superuser_client.post(
		"/api/v2/ai-configuration/providers",
		json={
			"provider_key": "groq",
			"display_name": "Groq",
			"priority": 10,
		},
	)
	assert create_response.status_code == 201

	list_response = await superuser_client.get("/api/v2/ai-configuration/providers")
	assert list_response.status_code == 200
	providers = list_response.json()
	assert len(providers) == 1
	assert providers[0]["provider_key"] == "groq"


async def test_ai_provider_model_crud_round_trip(superuser_client):
	provider_response = await superuser_client.post(
		"/api/v2/ai-configuration/providers",
		json={
			"provider_key": "google",
			"display_name": "Google AI",
			"priority": 20,
		},
	)
	provider_id = provider_response.json()["id"]

	create_response = await superuser_client.post(
		"/api/v2/ai-configuration/models",
		json={
			"provider_id": provider_id,
			"model_name": "gemini-flash-latest",
			"display_name": "Gemini Flash (Latest)",
			"is_default": True,
			"is_streaming_supported": True,
		},
	)
	assert create_response.status_code == 201
	model = create_response.json()
	model_id = model["id"]
	assert model["provider_id"] == provider_id
	assert model["is_default"] is True

	update_response = await superuser_client.patch(
		f"/api/v2/ai-configuration/models/{model_id}",
		json={"max_tokens": 4096, "temperature": 0.2},
	)
	assert update_response.status_code == 200
	updated = update_response.json()
	assert updated["max_tokens"] == 4096
	assert updated["temperature"] == 0.2

	delete_response = await superuser_client.delete(f"/api/v2/ai-configuration/models/{model_id}")
	assert delete_response.status_code == 204


async def test_reevu_agent_setting_crud_round_trip(superuser_client):
	provider_response = await superuser_client.post(
		"/api/v2/ai-configuration/providers",
		json={
			"provider_key": "openai",
			"display_name": "OpenAI",
			"priority": 1,
		},
	)
	provider_id = provider_response.json()["id"]

	model_response = await superuser_client.post(
		"/api/v2/ai-configuration/models",
		json={
			"provider_id": provider_id,
			"model_name": "gpt-4.1-mini",
			"is_default": True,
		},
	)
	model_id = model_response.json()["id"]

	create_response = await superuser_client.post(
		"/api/v2/ai-configuration/agent-settings",
		json={
			"agent_key": "reevu",
			"display_name": "REEVU Default",
			"provider_id": provider_id,
			"provider_model_id": model_id,
			"sampling_temperature": 0.1,
			"max_tokens": 2048,
			"tool_policy": {"allow": ["search_trials"]},
			"prompt_mode_capabilities": ["breeding_mode", "genomics_mode"],
		},
	)
	assert create_response.status_code == 201
	setting = create_response.json()
	setting_id = setting["id"]
	assert setting["agent_key"] == "reevu"
	assert setting["provider_id"] == provider_id
	assert setting["provider_model_id"] == model_id
	assert setting["prompt_mode_capabilities"] == ["breeding_mode", "genomics_mode"]

	update_response = await superuser_client.patch(
		f"/api/v2/ai-configuration/agent-settings/{setting_id}",
		json={"is_active": False, "max_tokens": 4096, "prompt_mode_capabilities": ["compliance_mode"]},
	)
	assert update_response.status_code == 200
	updated = update_response.json()
	assert updated["is_active"] is False
	assert updated["max_tokens"] == 4096
	assert updated["prompt_mode_capabilities"] == ["compliance_mode"]

	delete_response = await superuser_client.delete(f"/api/v2/ai-configuration/agent-settings/{setting_id}")
	assert delete_response.status_code == 204


async def test_reevu_agent_setting_rejects_mismatched_provider_and_model(superuser_client):
	provider_a = (
		await superuser_client.post(
			"/api/v2/ai-configuration/providers",
			json={"provider_key": "openai-mismatch", "display_name": "OpenAI", "priority": 1},
		)
	).json()["id"]
	provider_b = (
		await superuser_client.post(
			"/api/v2/ai-configuration/providers",
			json={"provider_key": "anthropic-mismatch", "display_name": "Anthropic", "priority": 2},
		)
	).json()["id"]
	model_b = (
		await superuser_client.post(
			"/api/v2/ai-configuration/models",
			json={"provider_id": provider_b, "model_name": "claude-3-7-sonnet"},
		)
	).json()["id"]

	response = await superuser_client.post(
		"/api/v2/ai-configuration/agent-settings",
		json={
			"agent_key": "reevu",
			"provider_id": provider_a,
			"provider_model_id": model_b,
		},
	)
	assert response.status_code == 400
	assert response.json()["detail"] == "provider_model_id does not belong to provider_id"


async def test_reevu_agent_setting_prompt_modes_default_to_null(superuser_client):
	response = await superuser_client.post(
		"/api/v2/ai-configuration/agent-settings",
		json={
			"agent_key": "reevu-null-modes",
			"display_name": "Null Modes",
		},
	)
	assert response.status_code == 201
	setting = response.json()
	assert setting["prompt_mode_capabilities"] is None


async def test_reevu_routing_policy_upsert_round_trip(superuser_client):
	provider_response = await superuser_client.post(
		"/api/v2/ai-configuration/providers",
		json={
			"provider_key": "groq-routing",
			"display_name": "Groq Routing",
			"priority": 1,
		},
	)
	provider_id = provider_response.json()["id"]

	model_response = await superuser_client.post(
		"/api/v2/ai-configuration/models",
		json={
			"provider_id": provider_id,
			"model_name": "llama-4-scout",
			"is_default": True,
		},
	)
	model_id = model_response.json()["id"]

	upsert_response = await superuser_client.put(
		"/api/v2/ai-configuration/routing-policies/reevu",
		json={
			"agent_key": "reevu",
			"display_name": "REEVU Org Default",
			"preferred_provider_id": provider_id,
			"preferred_provider_model_id": model_id,
			"fallback_to_priority_order": False,
			"is_active": True,
		},
	)
	assert upsert_response.status_code == 200
	policy = upsert_response.json()
	assert policy["agent_key"] == "reevu"
	assert policy["preferred_provider_id"] == provider_id
	assert policy["preferred_provider_model_id"] == model_id
	assert policy["fallback_to_priority_order"] is False

	list_response = await superuser_client.get("/api/v2/ai-configuration/routing-policies")
	assert list_response.status_code == 200
	policies = list_response.json()
	assert [item["agent_key"] for item in policies] == ["reevu"]

	update_response = await superuser_client.put(
		"/api/v2/ai-configuration/routing-policies/reevu",
		json={
			"agent_key": "reevu",
			"display_name": "REEVU Fallback Default",
			"preferred_provider_id": provider_id,
			"preferred_provider_model_id": model_id,
			"fallback_to_priority_order": True,
			"is_active": True,
		},
	)
	assert update_response.status_code == 200
	updated = update_response.json()
	assert updated["display_name"] == "REEVU Fallback Default"
	assert updated["fallback_to_priority_order"] is True

	delete_response = await superuser_client.delete("/api/v2/ai-configuration/routing-policies/reevu")
	assert delete_response.status_code == 204

	missing_response = await superuser_client.delete("/api/v2/ai-configuration/routing-policies/reevu")
	assert missing_response.status_code == 404


async def test_reevu_routing_policy_rejects_mismatched_provider_and_model(superuser_client):
	provider_a = (
		await superuser_client.post(
			"/api/v2/ai-configuration/providers",
			json={"provider_key": "groq-route-a", "display_name": "Groq A", "priority": 1},
		)
	).json()["id"]
	provider_b = (
		await superuser_client.post(
			"/api/v2/ai-configuration/providers",
			json={"provider_key": "openai-route-b", "display_name": "OpenAI B", "priority": 2},
		)
	).json()["id"]
	model_b = (
		await superuser_client.post(
			"/api/v2/ai-configuration/models",
			json={"provider_id": provider_b, "model_name": "gpt-4.1-mini"},
		)
	).json()["id"]

	response = await superuser_client.put(
		"/api/v2/ai-configuration/routing-policies/reevu",
		json={
			"agent_key": "reevu",
			"preferred_provider_id": provider_a,
			"preferred_provider_model_id": model_b,
			"fallback_to_priority_order": True,
			"is_active": True,
		},
	)
	assert response.status_code == 400
	assert response.json()["detail"] == "provider_model_id does not belong to provider_id"