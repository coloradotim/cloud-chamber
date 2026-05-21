#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PYTHON="${BACKEND_PYTHON:-python}"

require_command() {
  local command_name="$1"
  local install_hint="$2"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    echo "$install_hint" >&2
    exit 127
  fi
}

if [[ -x "$ROOT_DIR/app/backend/.venv/bin/python" && "${BACKEND_PYTHON}" == "python" ]]; then
  BACKEND_PYTHON="$ROOT_DIR/app/backend/.venv/bin/python"
fi
require_command "$BACKEND_PYTHON" "Install Python, or set BACKEND_PYTHON to the Python executable for app/backend."

echo "== Frontend checks =="
cd "$ROOT_DIR/app/frontend"
require_command npm "Install Node.js/npm, then run npm install in app/frontend."
npm run lint
npm run test
npm run build

echo "== Backend checks =="
cd "$ROOT_DIR/app/backend"
if ! "$BACKEND_PYTHON" -c "import mypy, pytest, ruff" >/dev/null 2>&1; then
  echo "Missing backend development dependencies for $BACKEND_PYTHON." >&2
  echo "Run: cd app/backend && python -m pip install -e '.[dev]'" >&2
  exit 127
fi
"$BACKEND_PYTHON" -m ruff format --check .
"$BACKEND_PYTHON" -m ruff check .
"$BACKEND_PYTHON" -m mypy .
"$BACKEND_PYTHON" -m pytest

echo "== Script syntax checks =="
cd "$ROOT_DIR"
require_command bash "Install bash or run this script from an environment with bash available."
find scripts -name "*.sh" -print0 | xargs -0 -r bash -n

echo "== Forbidden tracked artifact checks =="
require_command git "Install git before running the local validation gate."
forbidden_tracked="$(git ls-files \
  'local-data/*' \
  'runs/*' \
  'local-runs/*' \
  'cm1-runs/*' \
  'generated-runs/*' \
  'processed/*' \
  'validation-reports/*' \
  'local-validation-reports/*' \
  'cm1r*/*' \
  'LANDUSE.TBL' \
  '*.nc' \
  '*.nc4' \
  '*.cdf' \
  '*.netcdf' \
  '*.vtk' \
  '*.vti' \
  '*.vtr' \
  '*.vts' \
  '*.vtu' \
  '*.mp4' \
  '*.mov' \
  '*.webm')"
if [[ -n "$forbidden_tracked" ]]; then
  echo "Forbidden generated/local artifacts are tracked:" >&2
  echo "$forbidden_tracked" >&2
  exit 1
fi

echo "== Docs/JSON/YAML sanity checks =="
if ! "$BACKEND_PYTHON" -c "import yaml" >/dev/null 2>&1; then
  echo "Missing Python dependency: PyYAML." >&2
  echo "Run: cd app/backend && python -m pip install -e '.[dev]'" >&2
  exit 127
fi
"$BACKEND_PYTHON" - <<'PY'
import json
from pathlib import Path

json.loads(Path("app/frontend/package.json").read_text())
PY
"$BACKEND_PYTHON" - <<'PY'
from pathlib import Path

import yaml

for path in [
    ".github/workflows/ci.yml",
    ".github/dependabot.yml",
    ".github/ISSUE_TEMPLATE/feature.md",
    ".github/ISSUE_TEMPLATE/bug.md",
    ".github/ISSUE_TEMPLATE/docs.md",
    ".github/ISSUE_TEMPLATE/cm1-scenario.md",
    ".github/ISSUE_TEMPLATE/visualization.md",
]:
    text = Path(path).read_text()
    if path.endswith(".md") and text.startswith("---"):
        yaml.safe_load(text.split("---", 2)[1])
    else:
        yaml.safe_load(text)
PY
"$BACKEND_PYTHON" - <<'PY'
import os
from pathlib import Path

required_phrase = "Cloud Chamber"
old_product_name = "CM1 " + "Studio"
pruned_dirs = {".git", "node_modules", ".venv", "dist", "coverage", ".mypy_cache", ".pytest_cache", ".ruff_cache"}

for root, dirs, files in os.walk("."):
    dirs[:] = [directory for directory in dirs if directory not in pruned_dirs]
    for filename in files:
        if not filename.endswith(".md"):
            continue
        path = Path(root, filename)
        text = path.read_text()
        if not text.strip():
            raise SystemExit(f"{path} is empty")
        if not text.lstrip().startswith(("#", "---")):
            raise SystemExit(f"{path} should start with a heading or YAML front matter")
        if old_product_name in text:
            raise SystemExit(f"{path} still contains old product naming")

for path in [Path("README.md"), Path("AGENTS.md")]:
    if required_phrase not in path.read_text():
        raise SystemExit(f"{path} must mention {required_phrase}")
PY

echo "All checks passed."
