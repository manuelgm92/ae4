#!/usr/bin/env bash
# deploy.sh — reconstruye y verifica el despliegue (curso DPL, UT4).
set -euo pipefail

echo "== Construyendo imagenes =="
docker compose build

echo "== Arrancando servicios =="
docker compose up -d

echo "== Esperando a que /healthz responda 200 =="
for intento in $(seq 1 30); do
  if curl -sf http://localhost:8000/healthz >/dev/null; then
    echo "Despliegue sano tras $intento intento(s)."
    docker compose ps
    exit 0
  fi
  sleep 2
done

echo "ERROR: /healthz no respondio en 60 s" >&2
docker compose logs --tail=20 >&2
exit 1
