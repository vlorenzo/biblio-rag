"""Application configuration management."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5433/rag_unito",
        description="Database connection URL",
    )

    # OpenAI
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model",
    )
    openai_chat_model: str = Field(
        #default="gpt-4o-mini",
        default="gpt-4.1",
        description="OpenAI chat model",
    )

    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )

    # Ingestion
    max_chunk_size: int = Field(default=1000, description="Maximum chunk size")
    chunk_overlap: int = Field(default=100, description="Chunk overlap")
    max_concurrent_embeddings: int = Field(
        default=10, description="Max concurrent embedding requests"
    )
    embedding_batch_size: int = Field(
        default=20, description="Batch size for OpenAI embedding requests"
    )

    # RAG
    max_retrieval_results: int = Field(default=5, description="Max retrieval results")
    max_chunk_distance: float = Field(default=1.0, description="Max cosine distance for chunk retrieval")
    similarity_threshold: float = Field(
        default=0.7, description="Similarity threshold for retrieval"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format (json|text)")

    # Metrics
    metrics_token: str | None = Field(
        default=None,
        description="Bearer token required to access /metrics endpoint. If None, endpoint is public.",
    )


# Global settings instance
settings = Settings() 