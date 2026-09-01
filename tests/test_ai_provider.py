import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.ai.providers.provider import (
    DisabledAIProvider,
    GeminiProvider,
    get_ai_provider,
)


# =========================================================
# DISABLED PROVIDER
# =========================================================


def test_disabled_ai_provider_raises_runtime_error():
    provider = DisabledAIProvider()

    with pytest.raises(
        RuntimeError,
        match="AI provider is disabled",
    ):
        provider.generate("test prompt")


# =========================================================
# PROVIDER SELECTION
# =========================================================


def test_get_ai_provider_defaults_to_disabled():
    with patch.dict(
        "os.environ",
        {},
        clear=True,
    ):
        provider = get_ai_provider()

    assert isinstance(
        provider,
        DisabledAIProvider,
    )


@pytest.mark.parametrize(
    "provider_name",
    ["", "none", "disabled", "NONE", "Disabled"],
)
def test_get_ai_provider_returns_disabled_provider(
    provider_name,
):
    with patch.dict(
        "os.environ",
        {"LLM_PROVIDER": provider_name},
        clear=True,
    ):
        provider = get_ai_provider()

    assert isinstance(
        provider,
        DisabledAIProvider,
    )


def test_get_ai_provider_returns_gemini_provider():
    fake_genai = MagicMock()

    fake_client = MagicMock()

    fake_genai.Client.return_value = fake_client

    with patch.dict(
        "os.environ",
        {
            "LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "test-api-key",
            "LLM_MODEL": "test-model",
        },
        clear=True,
    ):
        with patch.dict(
            sys.modules,
            {
                "google": SimpleNamespace(
                    genai=fake_genai,
                )
            },
        ):
            provider = get_ai_provider()

    assert isinstance(
        provider,
        GeminiProvider,
    )

    assert provider.model == "test-model"

    fake_genai.Client.assert_called_once_with(
        api_key="test-api-key",
    )


def test_get_ai_provider_rejects_unsupported_provider():
    with patch.dict(
        "os.environ",
        {
            "LLM_PROVIDER": "openai",
        },
        clear=True,
    ):
        with pytest.raises(
            RuntimeError,
            match="Unsupported AI provider: openai",
        ):
            get_ai_provider()


# =========================================================
# GEMINI INITIALIZATION
# =========================================================


def test_gemini_provider_requires_api_key():
    fake_genai = MagicMock()

    with patch.dict(
        "os.environ",
        {
            "GEMINI_API_KEY": "",
        },
        clear=True,
    ):
        with patch.dict(
            sys.modules,
            {
                "google": SimpleNamespace(
                    genai=fake_genai,
                )
            },
        ):
            with pytest.raises(
                RuntimeError,
                match="GEMINI_API_KEY environment variable is not configured",
            ):
                GeminiProvider()


def test_gemini_provider_requires_google_sdk():
    with patch.dict(
        "os.environ",
        {
            "GEMINI_API_KEY": "test-api-key",
        },
        clear=True,
    ):
        with patch.dict(
            sys.modules,
            {
                "google": None,
                "google.genai": None,
            },
        ):
            with pytest.raises(
                RuntimeError,
                match="Google GenAI SDK is not installed",
            ):
                GeminiProvider()


# =========================================================
# GEMINI GENERATION
# =========================================================


def create_gemini_provider():
    fake_genai = MagicMock()

    fake_client = MagicMock()

    fake_genai.Client.return_value = fake_client

    with patch.dict(
        "os.environ",
        {
            "GEMINI_API_KEY": "test-api-key",
            "LLM_MODEL": "test-model",
        },
        clear=True,
    ):
        with patch.dict(
            sys.modules,
            {
                "google": SimpleNamespace(
                    genai=fake_genai,
                )
            },
        ):
            provider = GeminiProvider()

    return provider, fake_client


def test_gemini_generate_returns_response_text():
    provider, fake_client = create_gemini_provider()

    fake_client.models.generate_content.return_value = (
        SimpleNamespace(
            text="AI investigation result",
        )
    )

    result = provider.generate(
        "Analyze this reconciliation exception."
    )

    assert result == "AI investigation result"

    fake_client.models.generate_content.assert_called_once_with(
        model="test-model",
        contents="Analyze this reconciliation exception.",
    )


def test_gemini_generate_wraps_api_failure():
    provider, fake_client = create_gemini_provider()

    fake_client.models.generate_content.side_effect = (
        Exception("API unavailable")
    )

    with pytest.raises(
        RuntimeError,
        match="Gemini generation failed: API unavailable",
    ):
        provider.generate("test prompt")


def test_gemini_generate_rejects_empty_response():
    provider, fake_client = create_gemini_provider()

    fake_client.models.generate_content.return_value = (
        SimpleNamespace(
            text="",
        )
    )

    with pytest.raises(
        RuntimeError,
        match="Gemini returned an empty response",
    ):
        provider.generate("test prompt")