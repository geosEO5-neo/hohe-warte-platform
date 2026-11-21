# Runbook – Alerts von hohe-warte

## HoheWarteDown
**Bedeutung:** Prometheus erreicht keinen Pod.
1. `kubectl -n hohe-warte get pods -o wide` – laufen Pods? CrashLoopBackOff?
2. `kubectl -n hohe-warte describe pod <pod>` – Events (Image-Pull, Probes, OOMKilled).
3. ServiceMonitor-Label `release: kube-prometheus-stack` vorhanden? Target unter Prometheus → Status → Targets.
4. NetworkPolicy erlaubt Namespace `monitoring`?

## HoheWarteDataStale
**Bedeutung:** Seit > `maxStalenessSeconds` keine erfolgreiche Abfrage der GeoSphere API.
1. Logs: `kubectl -n hohe-warte logs -l app.kubernetes.io/name=hohe-warte | grep "refresh failed"`.
2. API manuell prüfen: `curl -I https://dataset.api.hub.geosphere.at/v1/station/current/tawes-v1-10min/metadata`.
3. Egress (DNS/443) durch NetworkPolicy oder Proxy blockiert?

## HoheWarteUpstreamErrors
**Bedeutung:** > 50 % der API-Anfragen schlagen fehl (30 min).
1. Statuscodes in den Logs (429 → Poll-Intervall erhöhen; 5xx → Upstream-Störung, abwarten).
2. Latenz-Panel im Dashboard prüfen; ggf. `REQUEST_TIMEOUT_SECONDS` anpassen.

## HoheWartePodRestarting
**Bedeutung:** Container wurde in 15 min mehr als 2-mal neu gestartet.
1. `kubectl -n hohe-warte logs <pod> --previous`.
2. OOMKilled? → `resources.limits.memory` erhöhen. Liveness-Probe zu streng? → Probe-Parameter.
