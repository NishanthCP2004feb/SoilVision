from __future__ import annotations

import sys
from pathlib import Path

# Add project root (parent of backend/) to sys.path so sibling packages like 'ml' can be imported.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import ai_suggestions, auth, chat, health, models, recommendations, soil
from app.core.config import settings
from app.core.database import Base, engine
import app.models  # Ensure SQLAlchemy mappings are registered.

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(_: FastAPI):
    # Production deployments must use `alembic upgrade head`; this permits an out-of-box SQLite development run.
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", openapi_url=f"{settings.api_prefix}/openapi.json", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = str(uuid4())
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request failure request_id=%s path=%s", request_id, request.url.path)
        return JSONResponse(status_code=500, content={"success": False, "data": None, "message": "Internal server error", "error": "internal_error"})
    response.headers["X-Request-ID"] = request_id
    logger.info("request_id=%s method=%s path=%s status=%s", request_id, request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"success": False, "data": None, "message": "Request validation failed", "error": error.errors()})


app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(soil.router, prefix=settings.api_prefix)
app.include_router(recommendations.router, prefix=settings.api_prefix)
app.include_router(models.router, prefix=settings.api_prefix)
app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(ai_suggestions.router, prefix=settings.api_prefix)
