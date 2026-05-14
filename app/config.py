from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_data_dir: Path = Path("./data")
    app_upload_dir: Path = Path("./data/uploads")
    qdrant_path: Path = Path("./data/qdrant")
    trace_path: Path = Path("./data/traces.jsonl")
    qdrant_collection: str = "documents"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:e2b"
    top_k: int = 4
    chunk_size: int = 700
    chunk_overlap: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.app_data_dir.mkdir(parents=True, exist_ok=True)
    settings.app_upload_dir.mkdir(parents=True, exist_ok=True)
    settings.qdrant_path.mkdir(parents=True, exist_ok=True)
    settings.trace_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
