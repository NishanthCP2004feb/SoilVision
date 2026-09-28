from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.schemas.domain import PropertyInput, RecommendationInput


@dataclass(frozen=True)
class CropProfile:
    name: str
    suitable_soil_types: tuple[str, ...]
    seasons: tuple[str, ...]
    references: tuple[str, ...]
    requirements: dict[str, tuple[float, float]]


def load_profiles(path: Path = Path("backend/app/data/crop_profiles.json")) -> list[CropProfile]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [CropProfile(item["name"], tuple(item["suitable_soil_types"]), tuple(item["seasons"]), tuple(item["references"]), {key: tuple(value) for key, value in item.get("requirements", {}).items()}) for item in data]


def recommend(request: RecommendationInput, profiles: list[CropProfile] | None = None) -> list[dict]:
    profiles = profiles if profiles is not None else load_profiles()
    measured = {item.name: item for item in request.properties if item.source != "FUTURE_AI_ESTIMATE"}
    ranked: list[dict] = []
    for profile in profiles:
        matched, limiting, possible = [], [], 0
        score = 0.0
        possible += 1
        if request.soil_type in profile.suitable_soil_types:
            score += 1
            matched.append("Detected soil type is listed as suitable in the configured crop profile.")
        else:
            limiting.append("Detected soil type is not listed as suitable in the configured crop profile.")
        if request.season:
            possible += 1
            if request.season in profile.seasons:
                score += 1
                matched.append(f"Configured generic season includes {request.season}.")
            else:
                limiting.append(f"Configured generic season does not include {request.season}.")
        for name, bounds in profile.requirements.items():
            if name not in measured:
                continue
            possible += 1
            value = measured[name].value
            if bounds[0] <= value <= bounds[1]:
                score += 1
                matched.append(f"Measured {name} is within the configured profile range.")
            else:
                limiting.append(f"Measured {name} is outside the configured profile range.")
        ranked.append({"crop": profile.name, "compatibility_score": round(100 * score / possible, 1), "season": request.season or ", ".join(profile.seasons), "matched_factors": matched, "limiting_factors": limiting, "references": list(profile.references), "warning": "Recommendation is based primarily on detected soil type and available verified measurements; regional validation is required."})
    return sorted(ranked, key=lambda item: item["compatibility_score"], reverse=True)
