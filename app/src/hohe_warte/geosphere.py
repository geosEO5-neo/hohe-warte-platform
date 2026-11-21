"""Schlanker Client für die GeoSphere Austria Dataset API (https://dataset.api.hub.geosphere.at)."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from .metrics import UPSTREAM_LATENCY, UPSTREAM_REQUESTS


@dataclass(frozen=True)
class Observation:
    station_id: str
    parameter: str
    name: str
    unit: str
    value: float | None
    timestamp: str
    lon: float
    lat: float


class GeoSphereClient:
    def __init__(self, base_url: str, resource: str, timeout: float = 10.0,
                 transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._resource = resource
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            transport=transport,
            headers={"User-Agent": "hohe-warte/0.1 (+https://github.com)"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def current(self, station_ids: list[str], parameters: list[str]) -> list[Observation]:
        """Liefert die jeweils jüngsten Messwerte der angegebenen Stationen."""
        start = time.perf_counter()
        try:
            resp = await self._client.get(
                f"/station/current/{self._resource}",
                params={"station_ids": ",".join(station_ids),
                        "parameters": ",".join(parameters)},
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            UPSTREAM_REQUESTS.labels(outcome="error").inc()
            raise
        finally:
            UPSTREAM_LATENCY.observe(time.perf_counter() - start)

        UPSTREAM_REQUESTS.labels(outcome="success").inc()
        return parse_feature_collection(resp.json())


def parse_feature_collection(payload: dict) -> list[Observation]:
    timestamps = payload.get("timestamps") or [""]
    ts = timestamps[-1]
    out: list[Observation] = []
    for feature in payload.get("features", []):
        lon, lat = feature["geometry"]["coordinates"][:2]
        props = feature["properties"]
        for code, p in props.get("parameters", {}).items():
            data = p.get("data") or [None]
            out.append(Observation(
                station_id=str(props["station"]), parameter=code, name=p.get("name", code),
                unit=p.get("unit", ""), value=data[-1], timestamp=ts, lon=lon, lat=lat,
            ))
    return out
