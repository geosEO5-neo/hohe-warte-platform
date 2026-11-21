"""Konfiguration ausschließlich über Umgebungsvariablen (12-Factor)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _list(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    api_base: str = field(
        default_factory=lambda: os.getenv(
            "GEOSPHERE_API_BASE", "https://dataset.api.hub.geosphere.at/v1"
        )
    )
    resource: str = field(
        default_factory=lambda: os.getenv("GEOSPHERE_RESOURCE", "tawes-v1-10min")
    )
    station_ids: list[str] = field(
        default_factory=lambda: _list(os.getenv("STATION_IDS", "11035,11034"))
    )
    parameters: list[str] = field(
        default_factory=lambda: _list(os.getenv("PARAMETERS", "TL,RF,FF,P,RR"))
    )
    poll_interval_s: int = field(
        default_factory=lambda: int(os.getenv("POLL_INTERVAL_SECONDS", "600"))
    )
    request_timeout_s: float = field(
        default_factory=lambda: float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
    )
    # Readiness schlägt fehl, wenn die letzte erfolgreiche Abfrage älter ist.
    max_staleness_s: int = field(
        default_factory=lambda: int(os.getenv("MAX_STALENESS_SECONDS", "1800"))
    )
