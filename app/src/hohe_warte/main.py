"""FastAPI-Anwendung: REST-Endpunkte, Health-Checks und /metrics.

Start: uvicorn --factory hohe_warte.main:create_app
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import make_asgi_app

from . import __version__
from .config import Settings
from .geosphere import GeoSphereClient, Observation
from .metrics import BUILD_INFO, LAST_SUCCESS, OBSERVATION, REGISTRY

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)
log = logging.getLogger("hohe_warte")


class State:
    def __init__(self) -> None:
        self.observations: dict[str, list[Observation]] = {}
        self.last_success: float | None = None


async def refresh(client: GeoSphereClient, settings: Settings, state: State) -> None:
    obs = await client.current(settings.station_ids, settings.parameters)
    grouped: dict[str, list[Observation]] = {}
    for o in obs:
        grouped.setdefault(o.station_id, []).append(o)
        if o.value is not None:
            OBSERVATION.labels(o.station_id, o.parameter, o.unit).set(o.value)
    state.observations = grouped
    state.last_success = time.time()
    LAST_SUCCESS.set(state.last_success)
    log.info("refreshed %d observations for %d stations", len(obs), len(grouped))


async def poll_forever(client: GeoSphereClient, settings: Settings, state: State) -> None:
    while True:
        try:
            await refresh(client, settings, state)
        except Exception as exc:  # Poller darf nie sterben
            log.warning("refresh failed: %s", exc)
        await asyncio.sleep(settings.poll_interval_s)


def create_app(settings: Settings | None = None, client: GeoSphereClient | None = None,
               start_poller: bool = True) -> FastAPI:
    settings = settings or Settings()
    client = client or GeoSphereClient(settings.api_base, settings.resource,
                                       settings.request_timeout_s)
    state = State()
    BUILD_INFO.info({"version": __version__})

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        task = asyncio.create_task(poll_forever(client, settings, state)) if start_poller else None
        yield
        if task:
            task.cancel()
        await client.close()

    app = FastAPI(title="hohe-warte", version=__version__, lifespan=lifespan)
    app.state.hw = state
    app.state.refresh = lambda: refresh(client, settings, state)
    app.mount("/metrics", make_asgi_app(registry=REGISTRY))

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz", include_in_schema=False)
    async def readyz(response: Response) -> dict:
        age = None if state.last_success is None else time.time() - state.last_success
        if age is None or age > settings.max_staleness_s:
            response.status_code = 503
            return {"status": "not ready", "data_age_seconds": age}
        return {"status": "ready", "data_age_seconds": round(age, 1)}

    @app.get("/api/v1/stations")
    async def stations() -> dict:
        return {"stations": sorted(state.observations)}

    @app.get("/api/v1/stations/{station_id}/current")
    async def current(station_id: str) -> dict:
        obs = state.observations.get(station_id)
        if not obs:
            raise HTTPException(404, f"keine Daten für Station {station_id}")
        return {
            "station_id": station_id,
            "timestamp": obs[0].timestamp,
            "location": {"lon": obs[0].lon, "lat": obs[0].lat},
            "values": {o.parameter: {"name": o.name, "unit": o.unit, "value": o.value}
                       for o in obs},
        }

    return app

