from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = "GoBot API"
    api_prefix: str = "/api/v1"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    serve_frontend: bool = True

    scraper_database_path: Path = Field(default=Path("data/app.db"))
    frontend_dist_path: Path = Field(default=Path("../frontend/dist"))
    scraper_headless: bool = True
    scraper_timeout_ms: int = 60_000
    scraper_scroll_pause_ms: int = 2_000
    scraper_max_scroll_attempts: int = 50
    scraper_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_database_path(self) -> Path:
        if self.scraper_database_path.is_absolute():
            return self.scraper_database_path
        return BACKEND_DIR / self.scraper_database_path

    @property
    def resolved_frontend_dist_path(self) -> Path:
        if self.frontend_dist_path.is_absolute():
            return self.frontend_dist_path
        return BACKEND_DIR / self.frontend_dist_path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
