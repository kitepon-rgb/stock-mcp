#!/usr/bin/env bash
# Deploy stock-mcp to the target server. Run from this repo's root.
# Usage: REMOTE=kite@192.168.1.2 bash scripts/deploy.sh

set -euo pipefail

REMOTE="${REMOTE:-kite@192.168.1.2}"
REMOTE_DIR="${REMOTE_DIR:-/home/kite/stock-mcp}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Syncing source to ${REMOTE}:${REMOTE_DIR}"
rsync -az --delete \
  --exclude='.venv/' --exclude='__pycache__/' --exclude='*.egg-info/' \
  --exclude='.env' --exclude='dist/' --exclude='build/' \
  --exclude='data/' \
  "${HERE}/" "${REMOTE}:${REMOTE_DIR}/"

echo "==> Bootstrapping venv and installing on remote"
ssh "${REMOTE}" bash -se <<'EOF'
set -euo pipefail
cd ~/stock-mcp

# OAuth SQLite store lives here. Preserved across rsync (deploy.sh excludes data/).
mkdir -p data

# Ensure python3-venv & pip ecosystem available without requiring system pip globally.
if ! python3 -c 'import ensurepip' 2>/dev/null; then
  echo "ensurepip module missing; installing python3-venv"
  sudo apt-get update -qq
  sudo apt-get install -y python3-venv python3-pip
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
python -m pip install --quiet --upgrade pip wheel
python -m pip install --quiet -e .

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created stub .env from .env.example -- fill in API keys as needed."
fi

echo "Installed. Use 'systemctl --user' or copy scripts/stock-mcp.service to /etc/systemd/system."
EOF

echo "==> Done."
