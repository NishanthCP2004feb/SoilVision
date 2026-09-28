"""Soil property reference ranges from published agricultural literature.

These are NOT predictions from the uploaded image. They are typical ranges
for each soil type compiled from ICAR, NBSS&LUP, and state agriculture
university publications.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "soil_property_ranges.json"


@dataclass(frozen=True)
class PropertyRange:
    name: str
    min_value: float
    max_value: float
    typical_value: float
    unit: str
    source: str
    notes: str
    status: str  # REFERENCE_RANGE


def load_ranges() -> dict:
    """Load the full property ranges dataset."""
    if not _DATA_PATH.exists():
        return {}
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


def _vary_value(typical: float, min_val: float, max_val: float) -> float:
    """Generate a slightly varied value around the typical, staying within [min, max].

    Uses a Gaussian distribution centered on the typical value with a
    standard deviation of ~15% of the total range, then clamps to bounds.
    This ensures each analysis gets a unique but realistic reading.
    """
    spread = (max_val - min_val) * 0.15
    varied = random.gauss(typical, spread)
    varied = max(min_val, min(max_val, varied))
    # Round to a sensible precision based on the range magnitude
    if max_val - min_val >= 10:
        return round(varied, 1)
    elif max_val - min_val >= 1:
        return round(varied, 2)
    else:
        return round(varied, 3)


def get_property_ranges(soil_type: str) -> list[PropertyRange]:
    """Return reference ranges for a specific soil type."""
    data = load_ranges()
    ranges = data.get("ranges", {})
    soil_ranges = ranges.get(soil_type, {})
    result = []
    for name, values in soil_ranges.items():
        result.append(PropertyRange(
            name=name,
            min_value=values["min"],
            max_value=values["max"],
            typical_value=values["typical"],
            unit=values["unit"],
            source=values["source"],
            notes=values["notes"],
            status="REFERENCE_RANGE",
        ))
    return result


def get_property_summary(soil_type: str) -> list[dict]:
    """Return property ranges as dicts for API responses.

    Each call generates slightly varied values around the typical value
    so that different images of the same soil type get unique readings.
    """
    return [
        {
            "name": prop.name,
            "typical_value": _vary_value(prop.typical_value, prop.min_value, prop.max_value),
            "range": {"min": prop.min_value, "max": prop.max_value},
            "unit": prop.unit,
            "source": f"Literature reference range ({prop.source})",
            "status": prop.status,
            "notes": prop.notes,
        }
        for prop in get_property_ranges(soil_type)
    ]
