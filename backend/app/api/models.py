from __future__ import annotations

import json

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=ApiResponse[list[dict]])
def models() -> ApiResponse[list[dict]]:
    metadata = settings.model_dir / "metadata.json"
    if not metadata.exists():
        return ApiResponse(data=[], message="No approved trained model artifact is installed; training is blocked pending data review")
    return ApiResponse(data=[json.loads(metadata.read_text(encoding="utf-8"))], message="Installed model metadata")
