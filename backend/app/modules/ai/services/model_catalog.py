"""Central model reference defaults for managed AI providers.

This catalog keeps provider model identifiers in one place so model lifecycle
changes do not require edits across settings, registries, and UI presets.
Where a provider offers a documented rolling alias, prefer that alias.
"""

from __future__ import annotations

from typing import Final, Literal, TypeAlias, TypedDict


ModelLifecycleStrategy: TypeAlias = Literal[
    "provider_alias_latest",
    "provider_named_family",
    "managed_named_model",
    "builtin_template",
]


DEFAULT_MODEL_PRESET_CAPABILITY_TAGS: Final[tuple[str, ...]] = ("chat", "reasoning", "streaming")
MANAGED_PROVIDER_CATALOG_KEYS: Final[tuple[str, ...]] = (
    "google",
    "groq",
    "functiongemma",
    "openai",
    "anthropic",
    "huggingface",
    "ollama",
)


class ModelCatalogPreset(TypedDict):
    label: str
    model_name: str
    display_name: str
    capability_tags: list[str]
    max_tokens: int
    temperature: float
    lifecycle: ModelLifecycleStrategy
    lifecycle_label: str


class ProviderModelCatalogEntry(TypedDict):
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


class ProviderModelReference(TypedDict):
    provider_label: str
    base_url: str
    default_priority: int
    default_model: str
    lifecycle: ModelLifecycleStrategy
    lifecycle_label: str
    provider_preset_label: str
    model_preset_label: str
    model_preset_display_name: str


PROVIDER_MODEL_REFERENCES: Final[dict[str, ProviderModelReference]] = {
    "groq": {
        "provider_label": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "default_priority": 10,
        "default_model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "lifecycle": "managed_named_model",
        "lifecycle_label": "Named managed default",
        "provider_preset_label": "Groq",
        "model_preset_label": "Llama 4 Scout",
        "model_preset_display_name": "Llama 4 Scout",
    },
    "google": {
        "provider_label": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_priority": 20,
        "default_model": "gemini-flash-latest",
        "lifecycle": "provider_alias_latest",
        "lifecycle_label": "Provider latest alias",
        "provider_preset_label": "Google Gemini",
        "model_preset_label": "Gemini Flash",
        "model_preset_display_name": "Gemini Flash (Latest)",
    },
    "openai": {
        "provider_label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_priority": 40,
        "default_model": "gpt-4.1-mini",
        "lifecycle": "provider_named_family",
        "lifecycle_label": "Provider family default",
        "provider_preset_label": "OpenAI",
        "model_preset_label": "GPT-4.1 Mini",
        "model_preset_display_name": "GPT-4.1 Mini",
    },
    "anthropic": {
        "provider_label": "Anthropic",
        "base_url": "https://api.anthropic.com/v1",
        "default_priority": 50,
        "default_model": "claude-3-7-sonnet-latest",
        "lifecycle": "provider_alias_latest",
        "lifecycle_label": "Provider latest alias",
        "provider_preset_label": "Anthropic",
        "model_preset_label": "Claude Sonnet",
        "model_preset_display_name": "Claude Sonnet (Latest)",
    },
    "huggingface": {
        "provider_label": "HuggingFace Inference",
        "base_url": "https://api-inference.huggingface.co/models",
        "default_priority": 60,
        "default_model": "mistralai/Mistral-7B-Instruct-v0.2",
        "lifecycle": "managed_named_model",
        "lifecycle_label": "Named managed default",
        "provider_preset_label": "HuggingFace",
        "model_preset_label": "Mistral 7B Instruct",
        "model_preset_display_name": "Mistral 7B Instruct",
    },
    "functiongemma": {
        "provider_label": "FunctionGemma",
        "base_url": "https://api-inference.huggingface.co/models",
        "default_priority": 30,
        "default_model": "google/functiongemma-270m-it",
        "lifecycle": "managed_named_model",
        "lifecycle_label": "Named managed default",
        "provider_preset_label": "FunctionGemma",
        "model_preset_label": "FunctionGemma 270M",
        "model_preset_display_name": "FunctionGemma 270M",
    },
    "ollama": {
        "provider_label": "Ollama (Local)",
        "base_url": "http://localhost:11434",
        "default_priority": 70,
        "default_model": "llama3.2:3b",
        "lifecycle": "managed_named_model",
        "lifecycle_label": "Local named model",
        "provider_preset_label": "Ollama (Local, Advanced)",
        "model_preset_label": "Llama 3.2 3B",
        "model_preset_display_name": "Llama 3.2 3B",
    },
    "template": {
        "provider_label": "Template",
        "base_url": "",
        "default_priority": 999,
        "default_model": "template-v1",
        "lifecycle": "builtin_template",
        "lifecycle_label": "Built-in template fallback",
        "provider_preset_label": "Template",
        "model_preset_label": "Template",
        "model_preset_display_name": "Template",
    },
}


def get_default_provider_model(provider_key: str, fallback: str) -> str:
    reference = PROVIDER_MODEL_REFERENCES.get(provider_key)
    return reference["default_model"] if reference else fallback


def get_provider_model_catalog() -> list[ProviderModelCatalogEntry]:
    catalog: list[ProviderModelCatalogEntry] = []
    for provider_key in MANAGED_PROVIDER_CATALOG_KEYS:
        reference = PROVIDER_MODEL_REFERENCES[provider_key]
        catalog.append(
            {
                "provider_key": provider_key,
                "provider_label": reference["provider_label"],
                "provider_display_name": reference["provider_label"],
                "base_url": reference["base_url"],
                "default_priority": reference["default_priority"],
                "recommended_model": reference["default_model"],
                "model_lifecycle": reference["lifecycle"],
                "model_lifecycle_label": reference["lifecycle_label"],
                "provider_preset_label": reference["provider_preset_label"],
                "model_presets": [
                    {
                        "label": reference["model_preset_label"],
                        "model_name": reference["default_model"],
                        "display_name": reference["model_preset_display_name"],
                        "capability_tags": list(DEFAULT_MODEL_PRESET_CAPABILITY_TAGS),
                        "max_tokens": 8192,
                        "temperature": 0.7,
                        "lifecycle": reference["lifecycle"],
                        "lifecycle_label": reference["lifecycle_label"],
                    }
                ],
            }
        )

    return catalog