"""Optional provider boundaries. No live weather/location data is fabricated."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class WeatherObservation:
    temperature_c: float | None = None
    rainfall_mm: float | None = None
    source: str = "UNAVAILABLE"


class WeatherService(Protocol):
    def current(self, latitude: float, longitude: float) -> WeatherObservation: ...


class LocationService(Protocol):
    def resolve(self, query: str) -> tuple[float, float] | None: ...


class UnavailableWeatherService:
    def current(self, latitude: float, longitude: float) -> WeatherObservation:
        return WeatherObservation()
