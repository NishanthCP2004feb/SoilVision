from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(RegisterRequest):
    pass


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PropertySource(str, Enum):
    LAB_MEASUREMENT = "LAB_MEASUREMENT"
    SENSOR_MEASUREMENT = "SENSOR_MEASUREMENT"
    USER_PROVIDED = "USER_PROVIDED"
    REFERENCE_RANGE = "REFERENCE_RANGE"
    FUTURE_AI_ESTIMATE = "FUTURE_AI_ESTIMATE"


class PropertyInput(BaseModel):
    name: str = Field(pattern="^(ph|nitrogen|phosphorus|potassium|moisture|organic_carbon|electrical_conductivity)$")
    value: float
    unit: str = Field(min_length=1, max_length=32)
    source: PropertySource
    notes: str | None = Field(default=None, max_length=1000)


class PropertySaveInput(PropertyInput):
    analysis_id: str = Field(min_length=36, max_length=36)


class Prediction(BaseModel):
    soil_type: str
    confidence: float


class RecommendationInput(BaseModel):
    soil_type: str
    season: str | None = Field(default=None, pattern="^(Kharif|Rabi|Zaid)$")
    properties: list[PropertyInput] = Field(default_factory=list)


class AnalysisView(BaseModel):
    id: str
    soil_type: str
    confidence: float
    model_version: str
    warning: str | None
    created_at: datetime
