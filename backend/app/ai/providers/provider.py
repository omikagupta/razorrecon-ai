from abc import ABC, abstractmethod


class AIProvider(ABC):
    """
    Abstract interface for AI providers.

    This allows RazorRecon AI to support different LLM providers
    without coupling application logic to a specific vendor.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response from the configured AI provider.
        """


class DisabledAIProvider(AIProvider):
    """
    Fallback provider used when no external AI provider
    is configured.
    """

    def generate(
        self,
        prompt: str,
    ) -> str:
        raise RuntimeError(
            "No AI provider is configured."
        )


def get_ai_provider() -> AIProvider:
    """
    Return the configured AI provider.

    Currently defaults to a disabled provider so the system
    remains functional without an API key.

    Future providers can be added here without changing
    investigation business logic.
    """

    return DisabledAIProvider()