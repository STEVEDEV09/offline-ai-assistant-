import os
from typing import Generator, Optional
from ai.base import AIProvider
from ai.ollama_provider import OllamaProvider
from ai.openai_provider import OpenAICompatibleProvider
from ai.gemini_provider import GeminiProvider
from config.settings import load_config, get_setting

class AIProviderManager:
    """Central manager coordinating AI providers, fallbacks, and model routing."""

    def __init__(self):
        self.providers: dict[str, AIProvider] = {}
        self._init_providers()

    def _init_providers(self):
        cfg = load_config()
        p_cfg = cfg.get("providers", {})

        # 1. Ollama
        ollama_cfg = p_cfg.get("ollama", {})
        self.providers["ollama"] = OllamaProvider(
            host=ollama_cfg.get("host", "http://localhost:11434"),
            default_model=ollama_cfg.get("default_model", "tinyllama")
        )

        # 2. OpenAI
        openai_cfg = p_cfg.get("openai", {})
        self.providers["openai"] = OpenAICompatibleProvider(
            name="openai",
            default_model=openai_cfg.get("default_model", "gpt-4o-mini"),
            base_url=openai_cfg.get("base_url", "https://api.openai.com/v1"),
            api_key_env=openai_cfg.get("api_key_env", "OPENAI_API_KEY")
        )

        # 3. Groq
        groq_cfg = p_cfg.get("groq", {})
        self.providers["groq"] = OpenAICompatibleProvider(
            name="groq",
            default_model=groq_cfg.get("default_model", "llama-3.3-70b-versatile"),
            base_url="https://api.groq.com/openai/v1",
            api_key_env=groq_cfg.get("api_key_env", "GROQ_API_KEY")
        )

        # 4. Gemini
        gemini_cfg = p_cfg.get("gemini", {})
        self.providers["gemini"] = GeminiProvider(
            default_model=gemini_cfg.get("default_model", "gemini-1.5-flash"),
            api_key_env=gemini_cfg.get("api_key_env", "GEMINI_API_KEY")
        )

    def get_provider(self, provider_name: Optional[str] = None) -> AIProvider:
        if not provider_name:
            provider_name = get_setting("ai_provider", "ollama")

        if provider_name in self.providers:
            return self.providers[provider_name]

        # Default fallback
        return self.providers.get("ollama")

    def get_active_provider_name(self) -> str:
        return get_setting("ai_provider", "ollama")

    def list_available_providers(self) -> list[dict]:
        """Return list of providers with status and models."""
        result = []
        for name, provider in self.providers.items():
            avail = provider.is_available()
            models = provider.list_models() if avail else [provider.default_model]
            result.append({
                "name": name,
                "available": avail,
                "default_model": provider.default_model,
                "models": models
            })
        return result

    def get_all_models_for_active(self) -> list[str]:
        p = self.get_provider()
        return p.list_models()

    def generate(
        self,
        messages: list[dict],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.4,
        max_tokens: int = 512
    ) -> str | Generator[str, None, None]:
        """Generate response with automatic graceful fallback if preferred provider is down."""
        pref = self.get_provider(provider_name)

        # If preferred is available, use it
        if pref.is_available():
            return pref.generate(messages, model=model, stream=stream, temperature=temperature, max_tokens=max_tokens)

        # Try to find any available provider
        for alt_name, alt_provider in self.providers.items():
            if alt_provider != pref and alt_provider.is_available():
                return alt_provider.generate(messages, stream=stream, temperature=temperature, max_tokens=max_tokens)

        # If none available, call preferred anyway to get its specific diagnostic message
        return pref.generate(messages, model=model, stream=stream, temperature=temperature, max_tokens=max_tokens)

# Global singleton
_manager_instance = None

def get_ai_manager() -> AIProviderManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = AIProviderManager()
    return _manager_instance
