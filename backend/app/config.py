from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Every field can be set via an env var prefixed with Z2_."""

    model_config = SettingsConfigDict(env_prefix="Z2_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./zone2.db"
    telegram_bot_token: str = ""
    jwt_secret: str = "change-me"
    jwt_ttl_hours: int = 24 * 7
    # Max age of Telegram initData / Login Widget payloads we accept.
    telegram_auth_max_age_s: int = 24 * 3600
    # Enables POST /api/auth/dev for local development without Telegram. Never enable in production.
    dev_login: bool = False
    web_app_url: str = "http://localhost:5173"
    cors_origins: list[str] = ["http://localhost:5173"]
    # Directory with the built web app (web/dist). When set, the API serves it at "/" (single-origin deploy).
    static_dir: str | None = None
    # Run the Telegram bot (long polling) inside the API process. Only one process may poll per bot token.
    run_bot: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
