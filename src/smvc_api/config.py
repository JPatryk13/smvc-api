"""Application settings from environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    model_config = SettingsConfigDict(env_prefix="SMVC_", extra="ignore")

    log_level: str = "INFO"

    user_api_token: str = "test-user-token"
    admin_api_key: str | None = "test-admin-key"

    miletribe_base_url: str = "https://api.development.miletribe.app"
    miletribe_access_token: str | None = None


def get_settings() -> Settings:
    return Settings()
