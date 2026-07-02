#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PYTHON="${BACKEND_PYTHON:-python}"

if [[ -x "$ROOT_DIR/app/backend/.venv/bin/python" && "$BACKEND_PYTHON" == "python" ]]; then
  BACKEND_PYTHON="$ROOT_DIR/app/backend/.venv/bin/python"
fi

if ! command -v "$BACKEND_PYTHON" >/dev/null 2>&1; then
  echo "Missing backend Python: $BACKEND_PYTHON" >&2
  echo "Run backend setup from docs/development.md, or set BACKEND_PYTHON." >&2
  exit 127
fi

cd "$ROOT_DIR/app/backend"
exec "$BACKEND_PYTHON" -m cloud_chamber.igra_recent_cli "$@"
