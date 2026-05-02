"""Provider adapter and registry scaffolding for REEVU."""

from app.modules.ai.adapters.anthropic_adapter import AnthropicAdapter
from app.modules.ai.adapters.base import IProviderAdapter
from app.modules.ai.adapters.google_adapter import GoogleAdapter
from app.modules.ai.adapters.groq_adapter import GroqAdapter
from app.modules.ai.adapters.huggingface_adapter import HuggingFaceAdapter
from app.modules.ai.adapters.ollama_adapter import OllamaAdapter
from app.modules.ai.adapters.openai_adapter import OpenAIAdapter
from app.modules.ai.adapters.provider_registry import ProviderRegistry

__all__ = [
	"AnthropicAdapter",
	"GoogleAdapter",
	"GroqAdapter",
	"HuggingFaceAdapter",
	"IProviderAdapter",
	"OllamaAdapter",
	"OpenAIAdapter",
	"ProviderRegistry",
]