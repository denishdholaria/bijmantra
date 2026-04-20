import { ApiClientCore } from "../core/client";

export interface AIProvider {
  id: number;
  organization_id: number;
  provider_key: string;
  display_name: string;
  base_url: string | null;
  auth_mode: string;
  priority: number;
  is_enabled: boolean;
  is_byok_allowed: boolean;
  settings: Record<string, unknown> | null;
  has_api_key: boolean;
  created_at: string;
  updated_at: string;
}

export interface AIProviderCreatePayload {
  provider_key: string;
  display_name: string;
  base_url?: string | null;
  auth_mode?: string;
  encrypted_api_key?: string | null;
  priority?: number;
  is_enabled?: boolean;
  is_byok_allowed?: boolean;
  settings?: Record<string, unknown> | null;
}

export interface AIProviderUpdatePayload extends Partial<AIProviderCreatePayload> {}

export interface AIProviderModel {
  id: number;
  organization_id: number;
  provider_id: number;
  model_name: string;
  display_name: string | null;
  capability_tags: string[] | null;
  max_tokens: number | null;
  temperature: number | null;
  is_default: boolean;
  is_streaming_supported: boolean;
  is_active: boolean;
  settings: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface AIProviderModelCreatePayload {
  provider_id: number;
  model_name: string;
  display_name?: string | null;
  capability_tags?: string[] | null;
  max_tokens?: number | null;
  temperature?: number | null;
  is_default?: boolean;
  is_streaming_supported?: boolean;
  is_active?: boolean;
  settings?: Record<string, unknown> | null;
}

export interface AIProviderModelUpdatePayload extends Partial<AIProviderModelCreatePayload> {}

export interface ReevuAgentSetting {
  id: number;
  organization_id: number;
  agent_key: string;
  display_name: string | null;
  provider_id: number | null;
  provider_model_id: number | null;
  system_prompt_override: string | null;
  tool_policy: Record<string, unknown> | null;
  default_task_context: Record<string, unknown> | null;
  sampling_temperature: number | null;
  max_tokens: number | null;
  capability_overrides: string[] | null;
  prompt_mode_capabilities?: string[] | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReevuAgentSettingCreatePayload {
  agent_key: string;
  display_name?: string | null;
  provider_id?: number | null;
  provider_model_id?: number | null;
  system_prompt_override?: string | null;
  tool_policy?: Record<string, unknown> | null;
  default_task_context?: Record<string, unknown> | null;
  sampling_temperature?: number | null;
  max_tokens?: number | null;
  capability_overrides?: string[] | null;
  is_active?: boolean;
}

export interface ReevuAgentSettingUpdatePayload
  extends Partial<ReevuAgentSettingCreatePayload> {}

export interface ReevuRoutingPolicy {
  id: number;
  organization_id: number;
  agent_key: string;
  display_name: string | null;
  preferred_provider_id: number | null;
  preferred_provider_model_id: number | null;
  fallback_to_priority_order: boolean;
  is_active: boolean;
  settings: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ReevuRoutingPolicyUpsertPayload {
  agent_key: string;
  display_name?: string | null;
  preferred_provider_id?: number | null;
  preferred_provider_model_id?: number | null;
  fallback_to_priority_order?: boolean;
  is_active?: boolean;
  settings?: Record<string, unknown> | null;
}

export interface CapabilityToolManifestItem {
  name: string;
  label: string;
  description: string;
}

export interface CapabilityManifestCategory {
  id: string;
  label: string;
  description: string;
  tools: CapabilityToolManifestItem[];
}

export interface ModelCatalogPreset {
  label: string;
  model_name: string;
  display_name: string;
  capability_tags: string[];
  max_tokens: number;
  temperature: number;
  lifecycle: string;
  lifecycle_label: string;
}

export interface ProviderModelCatalogEntry {
  provider_key: string;
  provider_label: string;
  provider_display_name: string;
  base_url: string;
  default_priority: number;
  recommended_model: string;
  model_lifecycle: string;
  model_lifecycle_label: string;
  provider_preset_label: string;
  model_presets: ModelCatalogPreset[];
}

export interface OllamaModelListResponse {
  models: string[];
}

export class AIConfigurationService {
  constructor(private client: ApiClientCore) {}

  async listProviders() {
    return this.client.get<AIProvider[]>("/api/v2/ai-configuration/providers");
  }

  async createProvider(payload: AIProviderCreatePayload) {
    return this.client.post<AIProvider>("/api/v2/ai-configuration/providers", payload);
  }

  async updateProvider(providerId: number, payload: AIProviderUpdatePayload) {
    return this.client.patch<AIProvider>(`/api/v2/ai-configuration/providers/${providerId}`, payload);
  }

  async deleteProvider(providerId: number) {
    await this.deleteVoid(`/api/v2/ai-configuration/providers/${providerId}`);
  }

  async listModels() {
    return this.client.get<AIProviderModel[]>("/api/v2/ai-configuration/models");
  }

  async createModel(payload: AIProviderModelCreatePayload) {
    return this.client.post<AIProviderModel>("/api/v2/ai-configuration/models", payload);
  }

  async updateModel(modelId: number, payload: AIProviderModelUpdatePayload) {
    return this.client.patch<AIProviderModel>(`/api/v2/ai-configuration/models/${modelId}`, payload);
  }

  async deleteModel(modelId: number) {
    await this.deleteVoid(`/api/v2/ai-configuration/models/${modelId}`);
  }

  async listAgentSettings() {
    return this.client.get<ReevuAgentSetting[]>("/api/v2/ai-configuration/agent-settings");
  }

  async listRoutingPolicies() {
    return this.client.get<ReevuRoutingPolicy[]>("/api/v2/ai-configuration/routing-policies");
  }

  async listCapabilities() {
    return this.client.get<CapabilityManifestCategory[]>("/api/v2/ai-configuration/capabilities");
  }

  async listModelCatalog() {
    return this.client.get<ProviderModelCatalogEntry[]>("/api/v2/ai-configuration/model-catalog");
  }

  async listOllamaModels() {
    return this.client.get<OllamaModelListResponse>("/api/v2/ai-configuration/ollama-models");
  }

  async createAgentSetting(payload: ReevuAgentSettingCreatePayload) {
    return this.client.post<ReevuAgentSetting>("/api/v2/ai-configuration/agent-settings", payload);
  }

  async updateAgentSetting(settingId: number, payload: ReevuAgentSettingUpdatePayload) {
    return this.client.patch<ReevuAgentSetting>(`/api/v2/ai-configuration/agent-settings/${settingId}`, payload);
  }

  async deleteAgentSetting(settingId: number) {
    await this.deleteVoid(`/api/v2/ai-configuration/agent-settings/${settingId}`);
  }

  async upsertRoutingPolicy(agentKey: string, payload: ReevuRoutingPolicyUpsertPayload) {
    return this.client.put<ReevuRoutingPolicy>(`/api/v2/ai-configuration/routing-policies/${agentKey}`, payload);
  }

  async deleteRoutingPolicy(agentKey: string) {
    await this.deleteVoid(`/api/v2/ai-configuration/routing-policies/${agentKey}`);
  }

  private async deleteVoid(endpoint: string) {
    const response = await fetch(`${this.client.getBaseURL()}${endpoint}`, {
      method: "DELETE",
      headers: this.client.getAuthHeaders(),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Request failed with status ${response.status}`);
    }
  }
}