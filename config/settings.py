"""Pydantic application settings loaded from environment."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="changeme", alias="NEO4J_PASSWORD")

    lightrag_working_dir: Path = Field(
        default=Path("./rag_storage"),
        alias="LIGHTRAG_WORKING_DIR",
    )
    lightrag_graph_storage: str = Field(
        default="Neo4JStorage",
        alias="LIGHTRAG_GRAPH_STORAGE",
    )

    elasticsearch_url: str | None = Field(default=None, alias="ELASTICSEARCH_URL")
    elasticsearch_index: str = Field(default="docs_bm25", alias="ELASTICSEARCH_INDEX")
    elasticsearch_content_field: str = Field(default="content", alias="ELASTICSEARCH_CONTENT_FIELD")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")

    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str | None = Field(
        default="https://cloud.langfuse.com",
        alias="LANGFUSE_HOST",
    )

    serpapi_api_key: str | None = Field(default=None, alias="SERPAPI_API_KEY")

    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_orchestrator_model: str = Field(
        default="gpt-4o-mini",
        alias="OPENAI_ORCHESTRATOR_MODEL",
    )
    openai_crag_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CRAG_MODEL")

    use_llm_planner: bool = Field(default=False, alias="USE_LLM_PLANNER")
    use_llm_step_back: bool = Field(default=False, alias="USE_LLM_STEP_BACK")
    enable_redis_query_cache: bool = Field(default=True, alias="ENABLE_REDIS_QUERY_CACHE")
    lightrag_query_cache_ttl_sec: int = Field(default=300, alias="LIGHTRAG_QUERY_CACHE_TTL_SEC")

    max_orchestrator_loops: int = Field(default=5, alias="MAX_ORCHESTRATOR_LOOPS")
    crag_high_confidence: float = Field(default=0.85, alias="CRAG_HIGH_CONFIDENCE")
    crag_expand_threshold: float = Field(default=0.60, alias="CRAG_EXPAND_THRESHOLD")
    crag_relevance_threshold: float = Field(default=0.50, alias="CRAG_RELEVANCE_THRESHOLD")

    ingest_root: Path | None = Field(
        default=None,
        alias="INGEST_ROOT",
        description="If set, ingest API only allows files under this directory.",
    )
def get_settings() -> Settings:
    return Settings()
