from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import current_user
from app.core.database import get_db
from app.models import SoilAnalysis, SoilProperty, User
from app.schemas.common import ApiResponse
from app.schemas.domain import AnalysisView, PropertyInput, PropertySaveInput
from app.services.inference import ModelUnavailable, classifier_service
from app.services.explainability import ExplanationUnavailable, explanation_service
from app.services.soil_properties import get_property_summary
from app.services.uploads import save_validated_upload

router = APIRouter(prefix="/soil", tags=["soil"])


@router.post("/analyze", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def analyze_image(upload: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    path = await save_validated_upload(upload)
    try:
        result = classifier_service.predict(path)
    except ModelUnavailable as error:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))
    analysis = SoilAnalysis(user_id=user.id, image_path=str(path), soil_type=result.soil_type, confidence=result.confidence, top_predictions={"items": result.alternatives}, model_version=result.model_version, warning=result.warning)
    db.add(analysis); db.commit(); db.refresh(analysis)
    property_ranges = get_property_summary(result.soil_type)
    return ApiResponse(data={"analysis_id": analysis.id, "soil_type": result.soil_type, "confidence": result.confidence, "top_predictions": result.alternatives, "model_version": result.model_version, "warning": result.warning, "property_ranges": property_ranges}, message="Soil analysis completed")


@router.get("/analyses", response_model=ApiResponse[list[AnalysisView]])
def list_analyses(user: User = Depends(current_user), db: Session = Depends(get_db)) -> ApiResponse[list[AnalysisView]]:
    analyses = db.scalars(select(SoilAnalysis).where(SoilAnalysis.user_id == user.id).order_by(SoilAnalysis.created_at.desc())).all()
    return ApiResponse(data=[AnalysisView.model_validate(item, from_attributes=True) for item in analyses], message="Analysis history")


@router.get("/analyses/{analysis_id}", response_model=ApiResponse[dict])
def analysis_detail(analysis_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    analysis = db.scalar(select(SoilAnalysis).where(SoilAnalysis.id == analysis_id, SoilAnalysis.user_id == user.id))
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    property_ranges = get_property_summary(analysis.soil_type)
    return ApiResponse(data={"id": analysis.id, "soil_type": analysis.soil_type, "confidence": analysis.confidence, "top_predictions": analysis.top_predictions, "model_version": analysis.model_version, "warning": analysis.warning, "property_ranges": property_ranges, "properties": [{"name": item.name, "value": item.value, "unit": item.unit, "source": item.source, "notes": item.notes} for item in analysis.properties], "recommendations": [{"crop": item.crop_name, "compatibility_score": item.score, "season": item.season, "matched_factors": item.matched_factors, "limiting_factors": item.limiting_factors} for item in analysis.recommendations]}, message="Analysis detail")


@router.get("/analyses/{analysis_id}/explanation", response_class=Response, responses={200: {"content": {"image/jpeg": {}}}})
def explanation(analysis_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    analysis = db.scalar(select(SoilAnalysis).where(SoilAnalysis.id == analysis_id, SoilAnalysis.user_id == user.id))
    if analysis is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    try:
        return Response(content=explanation_service.render(Path(analysis.image_path)), media_type="image/jpeg", headers={"Content-Disposition": "inline; filename=model-attention.jpg"})
    except ExplanationUnavailable as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))


@router.post("/analyses/{analysis_id}/properties", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
def add_property(analysis_id: str, request: PropertyInput, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    analysis = db.scalar(select(SoilAnalysis).where(SoilAnalysis.id == analysis_id, SoilAnalysis.user_id == user.id))
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    if request.source.value == "FUTURE_AI_ESTIMATE":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Image-based soil-property estimates are not enabled without labelled ground truth")
    property_value = SoilProperty(analysis_id=analysis.id, **request.model_dump(mode="json"))
    db.add(property_value); db.commit(); db.refresh(property_value)
    return ApiResponse(data={"id": property_value.id, **request.model_dump(mode="json")}, message="Measured property saved")


@router.post("/properties", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
def add_property_compatibility(request: PropertySaveInput, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """Versioned endpoint matching the public API contract; delegates to the owner-scoped service."""
    values = PropertyInput(**request.model_dump(exclude={"analysis_id"}))
    return add_property(request.analysis_id, values, user, db)
