from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def identifier() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    analyses: Mapped[list["SoilAnalysis"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class SoilAnalysis(Base):
    __tablename__ = "soil_analyses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    image_path: Mapped[str] = mapped_column(String(512))
    soil_type: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float)
    top_predictions: Mapped[dict] = mapped_column(JSON, default=dict)
    model_version: Mapped[str] = mapped_column(String(100))
    warning: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    user: Mapped[User] = relationship(back_populates="analyses")
    properties: Mapped[list["SoilProperty"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    recommendations: Mapped[list["CropRecommendation"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class SoilProperty(Base):
    __tablename__ = "soil_properties"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("soil_analyses.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis: Mapped[SoilAnalysis] = relationship(back_populates="properties")


class CropRecommendation(Base):
    __tablename__ = "crop_recommendations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("soil_analyses.id"), index=True)
    crop_name: Mapped[str] = mapped_column(String(100))
    score: Mapped[float] = mapped_column(Float)
    season: Mapped[str] = mapped_column(String(32))
    matched_factors: Mapped[list] = mapped_column(JSON, default=list)
    limiting_factors: Mapped[list] = mapped_column(JSON, default=list)
    analysis: Mapped[SoilAnalysis] = relationship(back_populates="recommendations")


class ModelVersion(Base):
    __tablename__ = "model_versions"
    version: Mapped[str] = mapped_column(String(100), primary_key=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
