"""Prometheus-Metriken. Eigene Registry, damit Tests isoliert laufen können."""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Info

REGISTRY = CollectorRegistry()

BUILD_INFO = Info("hohe_warte_build", "Build-Informationen", registry=REGISTRY)

OBSERVATION = Gauge(
    "geosphere_observation",
    "Jüngster Messwert einer TAWES-Station",
    ["station_id", "parameter", "unit"],
    registry=REGISTRY,
)
UPSTREAM_REQUESTS = Counter(
    "hohe_warte_upstream_requests",
    "Anfragen an die GeoSphere Dataset API",
    ["outcome"],
    registry=REGISTRY,
)
UPSTREAM_LATENCY = Histogram(
    "hohe_warte_upstream_latency_seconds",
    "Latenz der Anfragen an die GeoSphere Dataset API",
    buckets=(0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    registry=REGISTRY,
)
LAST_SUCCESS = Gauge(
    "hohe_warte_last_success_timestamp_seconds",
    "Unix-Zeitstempel der letzten erfolgreichen Datenabfrage",
    registry=REGISTRY,
)
