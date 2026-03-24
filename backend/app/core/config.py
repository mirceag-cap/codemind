# Central configuration — reads all environment variables in one typed class

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# Walk up: config.py → core/ → app/ → backend/ → codemind/ → .env
ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    # LLM
    openai_api_key: str

    # LangSmith observability
    langchain_api_key: str
    langchain_tracing_v2: bool = True
    langchain_project: str = "codemind"

    # Weaviate vector database
    weaviate_url: str = "http://localhost:8080"

    # App behaviour
    app_name: str = "CodeMind"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
