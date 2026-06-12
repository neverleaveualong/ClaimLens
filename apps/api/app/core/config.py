from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    database_url: str = "postgresql+psycopg://claimlens:claimlens@localhost:5432/claimlens"
    qdrant_url: str = "http://localhost:6333"
    pinecone_api_key: str | None = None
    pinecone_index_name: str = "claimlens-patents"
    pinecone_namespace: str = "dev"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    kipris_api_key: str | None = None
    allowed_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
