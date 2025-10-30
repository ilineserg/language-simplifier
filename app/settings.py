from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Bot & WebApp
    bot_token: str = Field(validation_alias="BOT_TOKEN")
    public_base_url: str = Field(validation_alias="PUBLIC_BASE_URL")
    host: str = Field(validation_alias="HOST", default="0.0.0.0")
    port: int = Field(validation_alias="PORT", default=8000)

    # --- App behavior
    max_queue: int = 64
    token_delay_ms: int = 25

    # --- OpenAI
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini")

    # --- Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
