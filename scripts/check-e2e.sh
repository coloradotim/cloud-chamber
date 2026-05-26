#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_URL="${CLOUD_CHAMBER_E2E_BASE_URL:-http://localhost:5173}"

if [[ ! -d "$ROOT_DIR/app/frontend/node_modules" ]]; then
  echo "Missing app/frontend/node_modules." >&2
  echo "Run: cd app/frontend && npm install" >&2
  exit 127
fi

if ! curl -fsS "$FRONTEND_URL" >/dev/null 2>&1; then
  echo "Frontend dev server is not reachable at $FRONTEND_URL." >&2
  echo "Start it with: scripts/dev.sh start" >&2
  exit 1
fi

cd "$ROOT_DIR/app/frontend"
echo "== Playwright mocked smoke tests =="
npm run test:e2e:smoke
