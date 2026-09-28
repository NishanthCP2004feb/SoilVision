"""API endpoints for AI-powered soil suggestions."""
from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from app.api.dependencies import current_user
from app.models import User
from app.schemas.common import ApiResponse
from app.services.ai_suggestions import generate_ai_suggestions

router = APIRouter(prefix="/ai-suggestions", tags=["ai-suggestions"])


class AiSuggestionsRequest(BaseModel):
    soil_type: str = Field(min_length=1)
    season: str | None = Field(default=None, pattern="^(Kharif|Rabi|Zaid)$")
    properties: list[dict] = Field(default_factory=list)


@router.post("", response_model=ApiResponse[dict])
async def get_ai_suggestions(
    request: AiSuggestionsRequest,
    _: User = Depends(current_user),
) -> ApiResponse[dict]:
    """Generate AI-powered soil deficiency analysis, fertilizer and crop recommendations."""
    result = await generate_ai_suggestions(
        soil_type=request.soil_type,
        properties=request.properties,
        season=request.season,
    )
    
    if result.error:
        return ApiResponse(
            success=False,
            data={"error": result.error},
            message=result.error,
        )
    
    return ApiResponse(
        data={
            "deficiencies": result.deficiencies,
            "fertilizer_recommendations": result.fertilizer_recommendations,
            "suitable_crops": result.suitable_crops,
            "soil_health_summary": result.soil_health_summary,
            "season": result.season,
            "season_note": result.season_note,
        },
        message="AI suggestions generated successfully",
    )
