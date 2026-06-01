from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = BACKEND_ROOT / "data"
DEFAULT_DB_DIR = BACKEND_ROOT / "db"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "worknoon.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    data_dir: Path = DEFAULT_DATA_DIR
    mistral_api_key: str | None = None  # env: MISTRAL_API_KEY
    mistral_model: str = "mistral-small-latest"
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
