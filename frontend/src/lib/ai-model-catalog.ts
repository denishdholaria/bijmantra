export type ModelLifecycleStrategy =
  | 'provider_alias_latest'
  | 'provider_named_family'
  | 'managed_named_model'
  | 'builtin_template'

export interface ProviderPreset {
  label: string
  provider_key: string
  display_name: string
  base_url: string
  priority: string
  recommended_model: string
  model_lifecycle: ModelLifecycleStrategy
  model_lifecycle_label: string
}

export interface ModelPreset {
  label: string
  model_name: string
  display_name: string
  capability_tags: string
  max_tokens: string
  temperature: string
  lifecycle: ModelLifecycleStrategy
  lifecycle_label: string
}

export const DEFAULT_REEVU_BYOK_PROVIDER = 'google'
export const DEFAULT_REEVU_BYOK_MODEL = 'gemini-flash-latest'

export const PROVIDER_PRESETS: ProviderPreset[] = [
  {
    label: 'Google Gemini',
    provider_key: 'google',
    display_name: 'Google Gemini',
    base_url: 'https://generativelanguage.googleapis.com/v1beta',
    priority: '20',
    recommended_model: 'gemini-flash-latest',
    model_lifecycle: 'provider_alias_latest',
    model_lifecycle_label: 'Latest alias',
  },
  {
    label: 'Groq',
    provider_key: 'groq',
    display_name: 'Groq',
    base_url: 'https://api.groq.com/openai/v1',
    priority: '10',
    recommended_model: 'meta-llama/llama-4-scout-17b-16e-instruct',
    model_lifecycle: 'managed_named_model',
    model_lifecycle_label: 'Named managed default',
  },
  {
    label: 'OpenAI',
    provider_key: 'openai',
    display_name: 'OpenAI',
    base_url: 'https://api.openai.com/v1',
    priority: '40',
    recommended_model: 'gpt-4.1-mini',
    model_lifecycle: 'provider_named_family',
    model_lifecycle_label: 'Family default',
  },
  {
    label: 'FunctionGemma',
    provider_key: 'functiongemma',
    display_name: 'FunctionGemma',
    base_url: 'https://api-inference.huggingface.co/models',
    priority: '30',
    recommended_model: 'google/functiongemma-270m-it',
    model_lifecycle: 'managed_named_model',
    model_lifecycle_label: 'Named managed default',
  },
  {
    label: 'Anthropic',
    provider_key: 'anthropic',
    display_name: 'Anthropic',
    base_url: 'https://api.anthropic.com/v1',
    priority: '50',
    recommended_model: 'claude-3-7-sonnet-latest',
    model_lifecycle: 'provider_alias_latest',
    model_lifecycle_label: 'Latest alias',
  },
  {
    label: 'HuggingFace',
    provider_key: 'huggingface',
    display_name: 'HuggingFace Inference',
    base_url: 'https://api-inference.huggingface.co/models',
    priority: '60',
    recommended_model: 'mistralai/Mistral-7B-Instruct-v0.2',
    model_lifecycle: 'managed_named_model',
    model_lifecycle_label: 'Named managed default',
  },
  {
    label: 'Ollama (Local, Advanced)',
    provider_key: 'ollama',
    display_name: 'Ollama (Local)',
    base_url: 'http://localhost:11434',
    priority: '70',
    recommended_model: 'llama3.2:3b',
    model_lifecycle: 'managed_named_model',
    model_lifecycle_label: 'Local named model',
  },
]

const MODEL_PRESET_MAP: Record<string, ModelPreset[]> = {
  google: [
    {
      label: 'Gemini Flash',
      model_name: 'gemini-flash-latest',
      display_name: 'Gemini Flash (Latest)',
      capability_tags: 'chat, reasoning, streaming',
      max_tokens: '8192',
      temperature: '0.7',
      lifecycle: 'provider_alias_latest',
      lifecycle_label: 'Latest alias',
    },
  ],
  groq: [
    {
      label: 'Llama 4 Scout',
      model_name: 'meta-llama/llama-4-scout-17b-16e-instruct',
      display_name: 'Llama 4 Scout',
      capability_tags: 'chat, reasoning, streaming',
      max_tokens: '8192',
      temperature: '0.7',
      lifecycle: 'managed_named_model',
      lifecycle_label: 'Named managed default',
    },
  ],
  openai: [
    {
      label: 'GPT-4.1 Mini',
      model_name: 'gpt-4.1-mini',
      display_name: 'GPT-4.1 Mini',
      capability_tags: 'chat, reasoning, streaming',
      max_tokens: '8192',
      temperature: '0.7',
      lifecycle: 'provider_named_family',
      lifecycle_label: 'Family default',
    },
  ],
  functiongemma: [
    {
      label: 'FunctionGemma 270M',
      model_name: 'google/functiongemma-270m-it',
      display_name: 'FunctionGemma 270M',
      capability_tags: 'chat, reasoning, streaming',
      max_tokens: '8192',
      temperature: '0.7',
      lifecycle: 'managed_named_model',
      lifecycle_label: 'Named managed default',
    },
  ],
  anthropic: [
    {
      label: 'Claude Sonnet',
      model_name: 'claude-3-7-sonnet-latest',
      display_name: 'Claude Sonnet (Latest)',
      capability_tags: 'chat, reasoning, streaming',
      max_tokens: '8192',
      temperature: '0.7',
      lifecycle: 'provider_alias_latest',
      lifecycle_label: 'Latest alias',
    },
  ],
  huggingface: [
    {
      label: 'Mistral 7B Instruct',
      model_name: 'mistralai/Mistral-7B-Instruct-v0.2',
      display_name: 'Mistral 7B Instruct',
      capability_tags: 'chat, reasoning, streaming',
      max_tokens: '8192',
      temperature: '0.7',
      lifecycle: 'managed_named_model',
      lifecycle_label: 'Named managed default',
    },
  ],
  ollama: [
    {
      label: 'Llama 3.2 3B',
      model_name: 'llama3.2:3b',
      display_name: 'Llama 3.2 3B',
      capability_tags: 'chat, reasoning, streaming',
      max_tokens: '8192',
      temperature: '0.7',
      lifecycle: 'managed_named_model',
      lifecycle_label: 'Local named model',
    },
    {
      label: 'Qwen 2.5 3B',
      model_name: 'qwen2.5:3b',
      display_name: 'Qwen 2.5 3B',
      capability_tags: 'chat, reasoning, streaming',
      max_tokens: '8192',
      temperature: '0.7',
      lifecycle: 'managed_named_model',
      lifecycle_label: 'Local named model',
    },
  ],
}

export function getProviderPreset(providerKey: string): ProviderPreset | undefined {
  return PROVIDER_PRESETS.find(preset => preset.provider_key === providerKey)
}

export function getModelPresets(providerKey: string): ModelPreset[] {
  return MODEL_PRESET_MAP[providerKey] || []
}