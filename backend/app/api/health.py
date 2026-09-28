from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.config import settings
from app.schemas.common import ApiResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[dict])
def health() -> ApiResponse[dict]:
    database = "unavailable"
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        pass
    return ApiResponse(data={"database": database, "model_artifact_installed": (settings.model_dir / "metadata.json").exists(), "demo_mode": settings.demo_mode}, message="Service health")
