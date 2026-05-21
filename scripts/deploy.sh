#!/usr/bin/env bash
# Deploy stock-mcp to the home server as a Docker container.
# Run from this repo's root. Usage: REMOTE=kite@192.168.1.2 bash scripts/deploy.sh

set -euo pipefail

REMOTE="${REMOTE:-kite@192.168.1.2}"
REMOTE_DIR="${REMOTE_DIR:-/home/kite/stock-mcp}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Syncing source to ${REMOTE}:${REMOTE_DIR}"
rsync -az --delete \
  --exclude='.git/' --exclude='.venv/' --exclude='__pycache__/' \
  --exclude='*.egg-info/' --exclude='.env' --exclude='dist/' \
  --exclude='build/' --exclude='data/' --exclude='.ruff_cache/' \
  "${HERE}/" "${REMOTE}:${REMOTE_DIR}/"

echo "==> Building and (re)starting the container on remote"
ssh "${REMOTE}" bash -se <<'EOF'
set -euo pipefail
cd ~/stock-mcp

# OAuth SQLite store lives here, mounted as a volume. Preserved across rsync.
mkdir -p data

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created stub .env from .env.example -- fill in API keys, then re-run."
fi

docker compose up -d --build
docker compose ps
EOF

echo "==> Done."
