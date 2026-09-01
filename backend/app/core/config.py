from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # Application
    app_name: str = "RazorRecon AI"
    app_env: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str

    # AI
    llm_provider: str = "none"
    llm_model: str = ""
    gemini_api_key: str | None = None

    # API / Security
    cors_origins: str = "http://localhost:5173"

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        allowed = {"development", "testing", "production"}

        if value.lower() not in allowed:
            raise ValueError(
                f"APP_ENV must be one of {', '.join(sorted(allowed))}"
            )

        return value.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

        value = value.upper()

        if value not in allowed:
            raise ValueError(
                f"LOG_LEVEL must be one of {', '.join(sorted(allowed))}"
            )

        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()