# Architektur & Betriebskonzept

## Komponenten

1. **hohe-warte (App)** – FastAPI, asynchroner Poller (`httpx`), eigene Prometheus-Registry.
   Zustand liegt nur im Speicher; jede Replica pollt selbstständig → horizontal skalierbar ohne
   gemeinsame Abhängigkeiten. Bei Upstream-Fehlern liefert die App weiter die letzten Werte und
   wird erst nach `MAX_STALENESS_SECONDS` „not ready“.
2. **Helm-Chart** – eine Quelle für alle Umgebungen. `checksum/config`-Annotation erzwingt Rollout
   bei Config-Änderungen. Monitoring-Ressourcen werden nur gerendert, wenn die CRDs vorhanden sind
   (`.Capabilities.APIVersions.Has`), damit das Chart auch ohne Prometheus Operator installierbar ist.
3. **Terraform** – `kind_cluster` → Namespaces (Pod Security Admission `restricted`) →
   `helm_release` kube-prometheus-stack → `kind load` des Images → `helm_release` App.
   Provider-Versionen sind gepinnt, Lockfile ist eingecheckt.
4. **Pipeline** – siehe Tabelle im README. Das E2E-Job prüft nicht nur „Pods laufen“, sondern dass
   Prometheus die Metriken tatsächlich scrapt und die Alert-Regeln geladen hat.

## Deployment-Strategie

- RollingUpdate mit `maxUnavailable: 0`, `maxSurge: 1` + Readiness-Probe → Zero-Downtime.
- PodDisruptionBudget `minAvailable: 1` schützt bei Node-Wartung (z. B. Hypervisor-Patching).
- `topologySpreadConstraints` verteilen Replicas über Nodes.
- Release über Git-Tag `vX.Y.Z` → Image + Chart werden versioniert nach GHCR veröffentlicht;
  Deployments referenzieren unveränderliche Versionen (GitOps-fähig, z. B. mit Argo CD/Flux).

## Erweiterungen (nächste Schritte)

- GitOps mit Argo CD (App-of-Apps) statt `helm upgrade` aus der Pipeline
- Logs mit Loki + Promtail/Alloy, Traces mit OpenTelemetry
- Externe Secrets (Vault/External Secrets Operator) für Grafana-Admin & Registry-Credentials
- Cluster auf VMs (Proxmox-Provider + RKE2/kubeadm) als zweites Terraform-Modul
