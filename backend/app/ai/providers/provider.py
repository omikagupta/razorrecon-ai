from abc import ABC, abstractmethod
import os
from pathlib import Path

from dotenv import load_dotenv


# Load environment variables from project root .env
PROJECT_ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


class AIProvider(ABC):
    """
    Abstract interface for AI providers.

    This abstraction allows RazorRecon AI to support different
    LLM providers without coupling investigation logic to one vendor.
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
    Provider used when AI is intentionally disabled.
    """

    def generate(
        self,
        prompt: str,
    ) -> str:
        raise RuntimeError(
            "AI provider is disabled. "
            "Configure LLM_PROVIDER to enable AI investigation."
        )


class GeminiProvider(AIProvider):
    """
    Gemini API provider implementation.
    """

    def __init__(self) -> None:
        try:
            from google import genai
        except ImportError as error:
            raise RuntimeError(
                "Google GenAI SDK is not installed. "
                "Install it using: pip install -U google-genai"
            ) from error

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not configured."
            )

        self.model = os.getenv(
            "LLM_MODEL",
            "gemini-2.5-flash",
        )

        self.client = genai.Client(
            api_key=api_key,
        )

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response using Gemini.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except Exception as error:
            raise RuntimeError(
                f"Gemini generation failed: {str(error)}"
            ) from error

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text


def get_ai_provider() -> AIProvider:
    """
    Return the configured AI provider.

    Supported providers:
    - none
    - gemini
    """

    provider_name = os.getenv(
        "LLM_PROVIDER",
        "none",
    ).strip().lower()

    if provider_name in {"", "none", "disabled"}:
        return DisabledAIProvider()

    if provider_name == "gemini":
        return GeminiProvider()

    raise RuntimeError(
        f"Unsupported AI provider: {provider_name}"
    )