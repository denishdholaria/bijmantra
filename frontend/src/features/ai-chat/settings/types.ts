/**
 * AI Settings Types
 * 
 * Form state and helper types for AI configuration management.
 * Extracted from pages/AISettings.tsx as part of Titanium Path hot-file reduction.
 */

export type JsonRecord = Record<string, unknown> | null;

export interface ProviderFormState {
  provider_key: string;
  display_name: string;
  base_url: string;
  auth_mode: string;
  encrypted_api_key: string;
  priority: string;
  is_enabled: boolean;
  is_byok_allowed: boolean;
  settings: string;
}

export interface ModelFormState {
  provider_id: string;
  model_name: string;
  display_name: string;
  capability_tags: string;
  max_tokens: string;
  temperature: string;
  is_default: boolean;
  is_streaming_supported: boolean;
  is_active: boolean;
  settings: string;
}

export interface AgentFormState {
  agent_key: string;
  display_name: string;
  provider_id: string;
  provider_model_id: string;
  system_prompt_override: string;
  tool_policy: string;
  default_task_context: string;
  sampling_temperature: string;
  max_tokens: string;
  capability_overrides: string;
  is_active: boolean;
}

export interface RoutingPolicyFormState {
  agent_key: string;
  display_name: string;
  preferred_provider_id: string;
  preferred_provider_model_id: string;
  fallback_to_priority_order: boolean;
  is_active: boolean;
}
