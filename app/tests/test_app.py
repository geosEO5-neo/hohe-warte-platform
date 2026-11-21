import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from hohe_warte.config import Settings
from hohe_warte.geosphere import GeoSphereClient, parse_feature_collection
from hohe_warte.main import create_app

BASE = "https://dataset.api.hub.geosphere.at/v1"
PAYLOAD = {
    "type": "FeatureCollection",
    "timestamps": ["2026-11-21T08:50+00:00"],
    "features": [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [16.3564, 48.2486]},
        "properties": {"station": "11035", "parameters": {
            "TL": {"name": "Lufttemperatur", "unit": "°C", "data": [6.3]},
            "RF": {"name": "Relative Feuchte", "unit": "%", "data": [66.0]},
            "FF": {"name": "Windgeschwindigkeit", "unit": "m/s", "data": [None]},
        }},
    }],
}


def test_parse_feature_collection():
    obs = parse_feature_collection(PAYLOAD)
    assert len(obs) == 3
    tl = next(o for o in obs if o.parameter == "TL")
    assert tl.value == 6.3 and tl.unit == "°C" and tl.station_id == "11035"


@pytest.fixture
def client():
    settings = Settings(station_ids=["11035"], parameters=["TL", "RF", "FF"])
    app = create_app(settings, GeoSphereClient(BASE, settings.resource), start_poller=False)
    with TestClient(app) as c:
        yield c


def test_health_and_not_ready_before_first_fetch(client):
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 503


@respx.mock
def test_refresh_exposes_api_and_metrics(client):
    respx.get(f"{BASE}/station/current/tawes-v1-10min").mock(
        return_value=httpx.Response(200, json=PAYLOAD))
    client.portal.call(client.app.state.refresh)

    assert client.get("/readyz").status_code == 200
    body = client.get("/api/v1/stations/11035/current").json()
    assert body["values"]["TL"]["value"] == 6.3

    metrics = client.get("/metrics/").text
    assert 'geosphere_observation{parameter="TL",station_id="11035",unit="°C"} 6.3' in metrics
    assert 'hohe_warte_upstream_requests_total{outcome="success"}' in metrics
    assert client.get("/api/v1/stations/99999/current").status_code == 404


@respx.mock
def test_upstream_error_is_counted(client):
    respx.get(f"{BASE}/station/current/tawes-v1-10min").mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        client.portal.call(client.app.state.refresh)
    assert 'hohe_warte_upstream_requests_total{outcome="error"}' in client.get("/metrics/").text
