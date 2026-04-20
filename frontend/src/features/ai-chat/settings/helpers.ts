/**
 * AI Settings Helpers
 * 
 * Form defaults, payload builders, and utility functions for AI configuration.
 * Extracted from pages/AISettings.tsx as part of Titanium Path hot-file reduction.
 */

import type {
  AIProviderCreatePayload,
  AIProviderModelCreatePayload,
  ReevuAgentSettingCreatePayload,
  ReevuRoutingPolicyUpsertPayload,
} from "@/lib/api/system/ai-configuration";
import {
  getProviderPreset,
  type ModelLifecycleStrategy,
  type ModelPreset,
  type ProviderPreset,
} from "@/lib/ai-model-catalog";
import type {
  ProviderFormState,
  ModelFormState,
  AgentFormState,
  RoutingPolicyFormState,
  JsonRecord,
} from "./types";

// Form defaults
export const providerDefaults = (): ProviderFormState => ({
  provider_key: "",
  display_name: "",
  base_url: "",
  auth_mode: "api_key",
  encrypted_api_key: "",
  priority: "100",
  is_enabled: true,
  is_byok_allowed: true,
  settings: "",
});

export const modelDefaults = (): ModelFormState => ({
  provider_id: "",
  model_name: "",
  display_name: "",
  capability_tags: "",
  max_tokens: "",
  temperature: "",
  is_default: false,
  is_streaming_supported: true,
  is_active: true,
  settings: "",
});

export const agentDefaults = (): AgentFormState => ({
  agent_key: "",
  display_name: "",
  provider_id: "",
  provider_model_id: "",
  system_prompt_override: "",
  tool_policy: "",
  default_task_context: "",
  sampling_temperature: "",
  max_tokens: "",
  capability_overrides: "",
  is_active: true,
});

export const routingPolicyDefaults = (): RoutingPolicyFormState => ({
  agent_key: "reevu",
  display_name: "REEVU Routing Policy",
  preferred_provider_id: "",
  preferred_provider_model_id: "",
  fallback_to_priority_order: true,
  is_active: true,
});

// Preset application
export function applyProviderPreset(form: ProviderFormState, preset: ProviderPreset): ProviderFormState {
  return {
    ...form,
    provider_key: preset.provider_key,
    display_name: preset.display_name,
    base_url: preset.base_url,
    auth_mode: preset.provider_key === "ollama" ? "none" : "api_key",
    priority: preset.priority,
  };
}

export function applyModelPreset(form: ModelFormState, preset: ModelPreset): ModelFormState {
  return {
    ...form,
    model_name: preset.model_name,
    display_name: preset.display_name,
    capability_tags: preset.capability_tags,
    max_tokens: preset.max_tokens,
    temperature: preset.temperature,
  };
}

// Model lifecycle helpers
const modelLifecycleStrategies = new Set<ModelLifecycleStrategy>([
  "provider_alias_latest",
  "provider_named_family",
  "managed_named_model",
  "builtin_template",
]);

const modelLifecycleLabels: Record<ModelLifecycleStrategy, string> = {
  provider_alias_latest: "Provider latest alias",
  provider_named_family: "Provider family default",
  managed_named_model: "Named managed default",
  builtin_template: "Built-in template fallback",
};

export function normalizeModelLifecycleStrategy(value: string): ModelLifecycleStrategy {
  return modelLifecycleStrategies.has(value as ModelLifecycleStrategy)
    ? (value as ModelLifecycleStrategy)
    : "managed_named_model";
}

export function normalizeModelLifecycleLabel(strategy: ModelLifecycleStrategy, label: string): string {
  const trimmed = label.trim();
  return trimmed || modelLifecycleLabels[strategy];
}

// JSON parsing
export function parseJsonObject(raw: string, label: string): JsonRecord {
  const trimmed = raw.trim();
  if (!trimmed) {
    return null;
  }

  try {
    const parsed = JSON.parse(trimmed);
    if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
      throw new Error(`${label} must be a JSON object`);
    }
    return parsed as Record<string, unknown>;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`${label}: ${error.message}`);
    }
    throw new Error(`${label} is not valid JSON`);
  }
}

export function parseTagList(raw: string) {
  const tags = raw
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
  return tags.length > 0 ? tags : null;
}

export function toNumberOrNull(raw: string) {
  const trimmed = raw.trim();
  if (!trimmed) {
    return null;
  }

  const parsed = Number(trimmed);
  if (Number.isNaN(parsed)) {
    throw new Error(`Invalid number: ${raw}`);
  }
  return parsed;
}

// Formatting helpers
export function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

export function formatUptime(seconds: number | undefined) {
  if (!seconds) {
    return "-";
  }

  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }

  if (seconds < 3600) {
    return `${Math.round(seconds / 60)}m`;
  }

  if (seconds < 86400) {
    return `${Math.round(seconds / 3600)}h`;
  }

  return `${Math.round(seconds / 86400)}d`;
}

export function formatRoutingLabel(value: string) {
  return value.replace(/_/g, " ");
}

export function extractErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }
  return "Request failed";
}

// Payload builders
export function buildProviderPayload(form: ProviderFormState): AIProviderCreatePayload {
  return {
    provider_key: form.provider_key.trim(),
    display_name: form.display_name.trim(),
    base_url: form.base_url.trim() || null,
    auth_mode: form.auth_mode.trim() || "api_key",
    encrypted_api_key: form.encrypted_api_key.trim() || null,
    priority: Number(form.priority || "100"),
    is_enabled: form.is_enabled,
    is_byok_allowed: form.is_byok_allowed,
    settings: parseJsonObject(form.settings, "Provider settings"),
  };
}

export function buildModelPayload(form: ModelFormState): AIProviderModelCreatePayload {
  const providerId = Number(form.provider_id);
  if (!providerId) {
    throw new Error("Provider is required");
  }

  return {
    provider_id: providerId,
    model_name: form.model_name.trim(),
    display_name: form.display_name.trim() || null,
    capability_tags: parseTagList(form.capability_tags),
    max_tokens: toNumberOrNull(form.max_tokens),
    temperature: toNumberOrNull(form.temperature),
    is_default: form.is_default,
    is_streaming_supported: form.is_streaming_supported,
    is_active: form.is_active,
    settings: parseJsonObject(form.settings, "Model settings"),
  };
}

export function buildAgentPayload(form: AgentFormState): ReevuAgentSettingCreatePayload {
  return {
    agent_key: form.agent_key.trim(),
    display_name: form.display_name.trim() || null,
    provider_id: form.provider_id ? Number(form.provider_id) : null,
    provider_model_id: form.provider_model_id ? Number(form.provider_model_id) : null,
    system_prompt_override: form.system_prompt_override.trim() || null,
    tool_policy: parseJsonObject(form.tool_policy, "Tool policy"),
    default_task_context: parseJsonObject(form.default_task_context, "Default task context"),
    sampling_temperature: toNumberOrNull(form.sampling_temperature),
    max_tokens: toNumberOrNull(form.max_tokens),
    capability_overrides: parseTagList(form.capability_overrides),
    is_active: form.is_active,
  };
}

export function buildRoutingPolicyPayload(form: RoutingPolicyFormState): ReevuRoutingPolicyUpsertPayload {
  return {
    agent_key: form.agent_key.trim(),
    display_name: form.display_name.trim() || null,
    preferred_provider_id: form.preferred_provider_id ? Number(form.preferred_provider_id) : null,
    preferred_provider_model_id: form.preferred_provider_model_id
      ? Number(form.preferred_provider_model_id)
      : null,
    fallback_to_priority_order: form.fallback_to_priority_order,
    is_active: form.is_active,
  };
}
