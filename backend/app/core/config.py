from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Auto-load .env from project root (parent of backend/)
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=False)


def _resolve(raw: str) -> Path:
    """Resolve a path relative to the project root if it is not absolute."""
    p = Path(raw)
    return p if p.is_absolute() else _PROJECT_ROOT / p


@dataclass(frozen=True)
class Settings:
    app_name: str = "Soil Intelligence API"
    api_prefix: str = "/api/v1"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./soil_dev.db")
    secret_key: str = os.getenv("SECRET_KEY", "development-only-change-me")
    upload_dir: Path = _resolve(os.getenv("UPLOAD_DIR", "storage/uploads"))
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", str(8 * 1024 * 1024)))
    model_dir: Path = _resolve(os.getenv("MODEL_DIR", "ml/artifacts/soil_classifier_v1.0"))
    cors_origins: tuple[str, ...] = tuple(filter(None, os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")))
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")


settings = Settings()
