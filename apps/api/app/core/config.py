from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str | None = None
    database_url: str = "postgresql+psycopg://claimlens:claimlens@localhost:5432/claimlens"
    qdrant_url: str = "http://localhost:6333"
    kipris_api_key: str | None = None
    allowed_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
