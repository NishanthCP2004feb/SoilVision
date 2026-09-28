"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa

revision, down_revision, branch_labels, depends_on = "0001", None, None, None

def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.String(36), primary_key=True), sa.Column("email", sa.String(320), nullable=False, unique=True), sa.Column("password_hash", sa.String(256), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_table("soil_analyses", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("image_path", sa.String(512), nullable=False), sa.Column("soil_type", sa.String(100), nullable=False), sa.Column("confidence", sa.Float, nullable=False), sa.Column("top_predictions", sa.JSON, nullable=False), sa.Column("model_version", sa.String(100), nullable=False), sa.Column("warning", sa.Text), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_table("soil_properties", sa.Column("id", sa.String(36), primary_key=True), sa.Column("analysis_id", sa.String(36), sa.ForeignKey("soil_analyses.id"), nullable=False), sa.Column("name", sa.String(64), nullable=False), sa.Column("value", sa.Float, nullable=False), sa.Column("unit", sa.String(32), nullable=False), sa.Column("source", sa.String(32), nullable=False), sa.Column("notes", sa.Text))
    op.create_table("crop_recommendations", sa.Column("id", sa.String(36), primary_key=True), sa.Column("analysis_id", sa.String(36), sa.ForeignKey("soil_analyses.id"), nullable=False), sa.Column("crop_name", sa.String(100), nullable=False), sa.Column("score", sa.Float, nullable=False), sa.Column("season", sa.String(32), nullable=False), sa.Column("matched_factors", sa.JSON, nullable=False), sa.Column("limiting_factors", sa.JSON, nullable=False))
    op.create_table("model_versions", sa.Column("version", sa.String(100), primary_key=True), sa.Column("metadata_json", sa.JSON, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_soil_analyses_user_id", "soil_analyses", ["user_id"]); op.create_index("ix_soil_analyses_created_at", "soil_analyses", ["created_at"])

def downgrade() -> None:
    op.drop_table("model_versions"); op.drop_table("crop_recommendations"); op.drop_table("soil_properties"); op.drop_table("soil_analyses"); op.drop_table("users")
