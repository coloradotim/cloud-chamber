#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PYTHON="${BACKEND_PYTHON:-python}"

if [[ -x "$ROOT_DIR/app/backend/.venv/bin/python" && "${BACKEND_PYTHON}" == "python" ]]; then
  BACKEND_PYTHON="$ROOT_DIR/app/backend/.venv/bin/python"
fi

echo "== Frontend checks =="
cd "$ROOT_DIR/app/frontend"
npm run lint
npm run test
npm run build

echo "== Backend checks =="
cd "$ROOT_DIR/app/backend"
"$BACKEND_PYTHON" -m ruff format --check .
"$BACKEND_PYTHON" -m ruff check .
"$BACKEND_PYTHON" -m mypy .
"$BACKEND_PYTHON" -m pytest

echo "== Script syntax checks =="
cd "$ROOT_DIR"
find scripts -name "*.sh" -print0 | xargs -0 -r bash -n

echo "== Docs/JSON/YAML sanity checks =="
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
