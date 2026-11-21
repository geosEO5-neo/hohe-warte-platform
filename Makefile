IMAGE ?= hohe-warte:dev
TF    := terraform -chdir=infra/terraform

.PHONY: help test lint image run chart-lint up down status grafana prometheus

help:            ## Diese Hilfe
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

lint:            ## Python-Linting (ruff)
	cd app && ruff check .

test:            ## Unit-Tests
	cd app && pytest -v

image:           ## Container-Image bauen
	docker build -t $(IMAGE) .

run: image       ## Container lokal starten (read-only, ohne Capabilities)
	docker run --rm -p 8080:8080 --read-only --tmpfs /tmp --cap-drop ALL $(IMAGE)

chart-lint:      ## Helm-Chart prüfen
	helm lint deploy/helm/hohe-warte --strict

up: image        ## Komplette Plattform (kind + Monitoring + App) per Terraform
	$(TF) init -input=false
	$(TF) apply -auto-approve -var app_image=$(IMAGE)

down:            ## Plattform abbauen
	$(TF) destroy -auto-approve -var app_image=$(IMAGE)

status:          ## Status der App im Cluster
	kubectl -n hohe-warte get pods,svc,servicemonitor,prometheusrule

grafana:         ## Grafana auf http://localhost:3000 (admin/admin)
	kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80

prometheus:      ## Prometheus auf http://localhost:9090
	kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
