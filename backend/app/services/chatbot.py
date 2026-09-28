"""AI agricultural chatbot via NVIDIA NIM API.

Proxies user messages through the backend so the API key never
reaches the browser. Supports six languages.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

LANGUAGES = {
    "en": "English",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "hi": "Hindi",
    "ml": "Malayalam",
}

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_NAME = "meta/llama-3.1-8b-instruct"


def _build_system_prompt(language: str, analysis_context: dict | None = None) -> str:
    lang_name = LANGUAGES.get(language, "English")
    base = f"""You are SoilWise AI Assistant, an agricultural chatbot that helps farmers and students understand soil analysis results and crop recommendations.

IMPORTANT RULES:
- Respond in {lang_name}. Keep technical terms, units, and numbers (like pH = 6.4, NPK values, dS/m) in their original form even when responding in {lang_name}.
- You help with soil analysis explanation, pH, NPK, crop recommendations, season information, fertilizer guidance, and general agriculture questions.
- NEVER invent laboratory results or claim measurements that were not provided.
- NEVER claim that an image-based analysis replaces laboratory soil testing.
- ALWAYS acknowledge uncertainty when discussing estimated values.
- Recommend consulting agricultural experts and soil testing laboratories for critical decisions.
- Be helpful, accurate, and respectful."""
    
    if analysis_context:
        ctx_lines = ["\nCurrent analysis context:"]
        if analysis_context.get("soil_type"):
            ctx_lines.append(f"- Detected soil type: {analysis_context['soil_type']}")
        if analysis_context.get("confidence"):
            ctx_lines.append(f"- Classification confidence: {analysis_context['confidence']:.1%}")
        if analysis_context.get("model_version"):
            ctx_lines.append(f"- Model: {analysis_context['model_version']}")
        if analysis_context.get("property_ranges"):
            ctx_lines.append("- Reference property ranges (from published literature, NOT image predictions):")
            for prop in analysis_context["property_ranges"]:
                ctx_lines.append(f"  {prop['name']}: {prop.get('typical_value', 'N/A')} {prop.get('unit', '')} (range: {prop.get('range', {}).get('min', '?')}-{prop.get('range', {}).get('max', '?')})")
        if analysis_context.get("recommendations"):
            ctx_lines.append("- Recommended crops: " + ", ".join(r.get("crop", "") for r in analysis_context["recommendations"][:5]))
        if analysis_context.get("warning"):
            ctx_lines.append(f"- Warning: {analysis_context['warning']}")
        base += "\n".join(ctx_lines)
    
    return base


@dataclass
class ChatResponse:
    message: str
    language: str
    model: str
    error: str | None = None


async def chat(
    user_message: str,
    language: str = "en",
    analysis_context: dict | None = None,
    conversation_history: list[dict] | None = None,
) -> ChatResponse:
    """Send a message to the NVIDIA NIM API and return the response."""
    if not settings.nvidia_api_key:
        return ChatResponse(
            message="The AI assistant is not configured. Please set the NVIDIA_API_KEY environment variable.",
            language=language,
            model="none",
            error="NVIDIA_API_KEY not configured",
        )
    
    if language not in LANGUAGES:
        language = "en"
    
    system_prompt = _build_system_prompt(language, analysis_context)
    
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        # Only keep last 10 messages to manage context length
        for msg in conversation_history[-10:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_message})
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                NVIDIA_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.nvidia_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
            )
            response.raise_for_status()
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            return ChatResponse(
                message=reply,
                language=language,
                model=MODEL_NAME,
            )
    except httpx.HTTPStatusError as exc:
        logger.error("NVIDIA API HTTP error: %s", exc.response.status_code)
        return ChatResponse(
            message="The AI assistant encountered an error. Please try again.",
            language=language,
            model=MODEL_NAME,
            error=f"HTTP {exc.response.status_code}",
        )
    except Exception as exc:
        logger.exception("NVIDIA API error")
        return ChatResponse(
            message="The AI assistant is temporarily unavailable. Please try again later.",
            language=language,
            model=MODEL_NAME,
            error=str(exc),
        )
