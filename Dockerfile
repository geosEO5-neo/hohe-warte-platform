# syntax=docker/dockerfile:1.7
# ---- Build-Stage: Wheels bauen, keine Compiler im Laufzeit-Image ----
FROM python:3.13-slim AS build
WORKDIR /build
COPY app/pyproject.toml ./
COPY app/src ./src
RUN pip install --no-cache-dir --upgrade pip==24.3.1 \
 && pip wheel --no-cache-dir --wheel-dir /wheels .

# ---- Runtime-Stage: minimal, non-root, read-only-fähig ----
FROM python:3.13-slim AS runtime
ARG VERSION=dev
ARG REVISION=unknown
LABEL org.opencontainers.image.title="hohe-warte" \
      org.opencontainers.image.description="Prometheus-Exporter & API für GeoSphere Austria TAWES-Daten" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.licenses="MIT"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz',timeout=2).status==200 else 1)"]
ENTRYPOINT ["uvicorn", "--factory", "hohe_warte.main:create_app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
