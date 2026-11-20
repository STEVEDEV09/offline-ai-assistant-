from abc import ABC, abstractmethod
from typing import Generator, Any, Optional

class AIProvider(ABC):
    """Abstract Base Class for all AI Model Providers."""

    def __init__(self, name: str, default_model: str, config: Optional[dict] = None):
        self.name = name
        self.default_model = default_model
        self.config = config or {}

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider service or API credentials are ready."""
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models for this provider."""
        pass

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.5,
        max_tokens: int = 512
    ) -> str | Generator[str, None, None]:
        """Generate response given conversation history."""
        pass
