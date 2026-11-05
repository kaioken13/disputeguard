from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "DisputeGuard API"
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    PORT: int = Field(default=8000, validation_alias="PORT")

    # LLM / Groq
    GROQ_API_KEY: str = Field(..., validation_alias="GROQ_API_KEY")
    LLM_MODEL: str = Field(default="groq/llama-3.3-70b-versatile", validation_alias="LLM_MODEL")

    # ChromaDB / RAG
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="/app/data/chroma", validation_alias="CHROMA_PERSIST_DIRECTORY"
    )
    CHROMA_COLLECTION_NAME: str = "dispute_policies"

    # Mock Data Path (padrão busca na raiz do projeto)
    MOCK_ORDERS_PATH: str = Field(
        default="mock_orders.json", validation_alias="MOCK_ORDERS_PATH"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
