from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from app.api.dependencies import current_user
from app.models import User
from app.schemas.common import ApiResponse
from app.services.chatbot import chat, LANGUAGES

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en", pattern="^(en|kn|ta|te|hi|ml)$")
    analysis_context: dict | None = None
    conversation_history: list[dict] = Field(default_factory=list)


@router.post("", response_model=ApiResponse[dict])
async def send_message(request: ChatRequest, _: User = Depends(current_user)) -> ApiResponse[dict]:
    result = await chat(
        user_message=request.message,
        language=request.language,
        analysis_context=request.analysis_context,
        conversation_history=request.conversation_history,
    )
    return ApiResponse(
        data={
            "message": result.message,
            "language": result.language,
            "model": result.model,
        },
        message="Chat response generated",
    )


@router.get("/languages", response_model=ApiResponse[dict])
def supported_languages() -> ApiResponse[dict]:
    return ApiResponse(data=LANGUAGES, message="Supported chatbot languages")
