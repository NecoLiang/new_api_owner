#!/usr/bin/env bash
# Pull latest repo and redeploy new-api.
# Layout expectation:
#   REPO_DIR=/root/new-api-src    (git clone of this repo)
#   RUN_DIR=/root/new-api         (holds .env, data/, mysql-data/, and receives compose)
set -euo pipefail

REPO_DIR="${REPO_DIR:-/root/new-api-src}"
RUN_DIR="${RUN_DIR:-/root/new-api}"

echo "==> pulling repo ${REPO_DIR}"
git -C "${REPO_DIR}" pull --ff-only

echo "==> syncing compose + scripts into ${RUN_DIR}"
cp "${REPO_DIR}/deploy/docker-compose.yml"             "${RUN_DIR}/docker-compose.yml"
cp "${REPO_DIR}/deploy/migrate_sqlite_to_mysql.py"     "${RUN_DIR}/migrate_sqlite_to_mysql.py"

if [[ ! -f "${RUN_DIR}/.env" ]]; then
    echo "!! ${RUN_DIR}/.env missing; copy deploy/.env.example and fill it in first" >&2
    exit 1
fi

echo "==> docker compose up -d"
cd "${RUN_DIR}"
docker compose up -d

echo "==> current containers"
docker compose ps
