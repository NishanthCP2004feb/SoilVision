"""AI-powered soil suggestions using Google Gemini API.

Generates soil deficiency analysis, fertilizer recommendations,
and suitable crop suggestions based on soil type, properties, and season.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Map month to Indian agricultural season
def _get_current_season() -> str:
    month = datetime.now().month
    if month in (6, 7, 8, 9, 10):  # June-October
        return "Kharif"
    elif month in (11, 12, 1, 2, 3):  # November-March
        return "Rabi"
    else:  # April-May
        return "Zaid"


def _build_prompt(soil_type: str, properties: list[dict], season: str | None = None) -> str:
    """Build a detailed prompt for Gemini to generate soil suggestions."""
    current_season = season or _get_current_season()
    
    props_text = ""
    if properties:
        props_lines = []
        for p in properties:
            name = p.get("name", "unknown")
            value = p.get("typical_value", p.get("value", "N/A"))
            unit = p.get("unit", "")
            range_info = p.get("range", {})
            min_val = range_info.get("min", "?")
            max_val = range_info.get("max", "?")
            props_lines.append(f"  - {name}: {value} {unit} (normal range: {min_val}-{max_val} {unit})")
        props_text = "\n".join(props_lines)
    
    return f"""You are an expert agricultural soil scientist. Analyze the following soil data and provide detailed recommendations.

SOIL DATA:
- Soil Type: {soil_type.replace('_', ' ').title()}
- Current Season: {current_season}
- Soil Properties:
{props_text if props_text else '  No specific property data available. Use typical ranges for this soil type.'}

Provide your analysis in the following JSON format (respond ONLY with valid JSON, no markdown, no code blocks):
{{
  "season": "{current_season}",
  "deficiencies": [
    {{
      "nutrient": "<nutrient name>",
      "status": "<Low|Medium|Adequate|High|Excess>",
      "severity": "<Mild|Moderate|Severe>",
      "description": "<2-3 sentence explanation of the deficiency and its impact on crops>",
      "visual_signs": "<observable signs in plants/soil>"
    }}
  ],
  "fertilizer_recommendations": [
    {{
      "fertilizer_name": "<name of fertilizer>",
      "type": "<Organic|Chemical|Bio-fertilizer>",
      "dosage": "<recommended dosage per hectare or acre>",
      "application_method": "<how to apply>",
      "timing": "<when to apply relative to {current_season} season>",
      "purpose": "<which deficiency it addresses>",
      "cost_estimate": "<approximate cost in INR per acre>"
    }}
  ],
  "suitable_crops": [
    {{
      "crop_name": "<name of crop>",
      "suitability_score": <0-100>,
      "season": "{current_season}",
      "reason": "<why this crop is suitable for this soil type and season>",
      "expected_yield": "<approximate yield per acre>",
      "water_requirement": "<Low|Medium|High>",
      "growth_duration": "<approximate days to harvest>",
      "tips": "<1-2 practical tips for growing this crop in this soil>"
    }}
  ],
  "soil_health_summary": "<3-4 sentence overall assessment of soil health and priority actions>",
  "season_note": "<2-3 sentences about how the {current_season} season affects recommendations>"
}}

IMPORTANT:
- Provide at least 3-5 deficiencies based on the soil properties.
- Provide at least 4-6 fertilizer recommendations.
- Provide at least 5-8 suitable crops for the {current_season} season.
- All recommendations must be specific to Indian agriculture.
- Consider the current season ({current_season}) in all recommendations.
- Base your analysis on real agricultural science."""


@dataclass
class AiSuggestionsResponse:
    deficiencies: list[dict] = field(default_factory=list)
    fertilizer_recommendations: list[dict] = field(default_factory=list)
    suitable_crops: list[dict] = field(default_factory=list)
    soil_health_summary: str = ""
    season: str = ""
    season_note: str = ""
    error: str | None = None


async def generate_ai_suggestions(
    soil_type: str,
    properties: list[dict],
    season: str | None = None,
) -> AiSuggestionsResponse:
    """Call Google Gemini API to generate soil suggestions."""
    if not settings.gemini_api_key:
        return AiSuggestionsResponse(
            error="Gemini API key is not configured. Please set GEMINI_API_KEY in environment.",
        )
    
    current_season = season or _get_current_season()
    prompt = _build_prompt(soil_type, properties, current_season)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={settings.gemini_api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 4096,
                        "responseMimeType": "application/json",
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract text from Gemini response
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Parse the JSON response
            # Clean up the text - remove markdown code blocks if present
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            
            return AiSuggestionsResponse(
                deficiencies=result.get("deficiencies", []),
                fertilizer_recommendations=result.get("fertilizer_recommendations", []),
                suitable_crops=result.get("suitable_crops", []),
                soil_health_summary=result.get("soil_health_summary", ""),
                season=result.get("season", current_season),
                season_note=result.get("season_note", ""),
            )
    except httpx.HTTPStatusError as exc:
        logger.error("Gemini API HTTP error: %s - %s", exc.response.status_code, exc.response.text)
        return AiSuggestionsResponse(
            error=f"Gemini API error (HTTP {exc.response.status_code}). Please try again.",
        )
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini response as JSON: %s", exc)
        return AiSuggestionsResponse(
            error="Failed to parse AI response. Please try again.",
        )
    except Exception as exc:
        logger.exception("Gemini API error")
        return AiSuggestionsResponse(
            error=f"AI suggestions temporarily unavailable: {str(exc)}",
        )
