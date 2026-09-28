from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import current_user
from app.core.database import get_db
from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.domain import RecommendationInput
from app.services.recommendations import load_profiles, recommend

router = APIRouter(tags=["recommendations"])


@router.get("/crops", response_model=ApiResponse[list[dict]])
def crops() -> ApiResponse[list[dict]]:
    return ApiResponse(data=[{"name": item.name, "suitable_soil_types": item.suitable_soil_types, "seasons": item.seasons, "references": item.references} for item in load_profiles()], message="Configured crop profiles")


@router.get("/crops/{name}", response_model=ApiResponse[dict])
def crop(name: str) -> ApiResponse[dict]:
    profile = next((item for item in load_profiles() if item.name.lower() == name.lower()), None)
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Crop profile not found")
    return ApiResponse(data={"name": profile.name, "suitable_soil_types": profile.suitable_soil_types, "seasons": profile.seasons, "references": profile.references, "requirements": profile.requirements}, message="Crop profile")


@router.post("/recommendations", response_model=ApiResponse[list[dict]])
def recommendations(request: RecommendationInput, _: User = Depends(current_user), __: Session = Depends(get_db)) -> ApiResponse[list[dict]]:
    return ApiResponse(data=recommend(request), message="Recommendations generated from configured evidence and supplied measurements")
