# Development

**Status:** Current operational guide

This guide describes how to work with the repository as it exists today. It does not define
product direction, recipe status, scenario priority, or final application architecture.

## Prerequisites

Install these tools locally:

- Git
- Bash
- Node.js with npm; CI currently uses Node 22
- Python 3.12 or newer
- `lsof`, used by `scripts/dev.sh` to detect listeners on local ports

The repository currently has app-level manifests rather than a root package manifest:

- frontend dependencies: `app/frontend/package.json`
- backend dependencies: `app/backend/pyproject.toml`

## Install Dependencies

Frontend:

```sh
cd app/frontend
npm install
```

Backend, using the same dependency set as CI:

```sh
cd app/backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If your Python executable has a different name, use any Python 3.12+ executable and set
`BACKEND_PYTHON` to an executable name on `PATH` or an absolute path when running repository
helper scripts.

## Development Servers

From the repository root:

```sh
scripts/dev.sh start
scripts/dev.sh status
scripts/dev.sh restart
scripts/dev.sh stop
scripts/dev.sh logs
```

Current defaults:

- backend: `http://127.0.0.1:8000`
- frontend: `http://localhost:5173`
- PID and log files: `.dev/`

Supported overrides:

```sh
BACKEND_PORT=8001 FRONTEND_PORT=5174 scripts/dev.sh start
BACKEND_PYTHON="$(pwd)/app/backend/.venv/bin/python" scripts/dev.sh start
```

`scripts/dev.sh` prefers `app/backend/.venv/bin/python` when it exists and
`BACKEND_PYTHON` is not set to another executable. It verifies that backend `uvicorn` and
frontend `node_modules` are available before starting servers.

Manual server commands remain available when needed:

```sh
cd app/backend
python -m uvicorn cloud_chamber.app:app --host 127.0.0.1 --port 8000 --reload
```

```sh
cd app/frontend
npm run dev
```

## Repository Layout

Current major areas:

```text
app/backend/                  FastAPI backend package, backend tests, pyproject
app/frontend/                 React/Vite frontend, frontend tests, Playwright checks
docs/current/                 Current descriptive implementation and lifecycle docs
docs/development/             Current operational developer docs
docs/product/                 Controlling product vision
docs/archive/                 Historical and superseded material
docs/contracts/               Contracts that must be verified against code before use
docs/research/                Research evidence and investigations
scenarios/                    Scenario templates used by current package generation
scripts/                      Local developer, validation, CM1, IGRA, and LAN helper scripts
```

This layout is a present implementation structure, not a final product decision.

## Runtime Home And Local Settings

Cloud Chamber stores local runtime state outside the repository by default:

```text
<runtime-home>/
  settings.json
  runs/
  cache/
  logs/
```

The default runtime home is `~/CloudChamber`. Use `CLOUD_CHAMBER_RUNTIME_HOME` when a
different runtime home is needed:

```sh
CLOUD_CHAMBER_RUNTIME_HOME=<runtime-home> scripts/dev.sh start
```

Local settings may be saved in:

```text
<runtime-home>/settings.json
```

Example shape:

```json
{
  "cm1_root": "<cm1-root>",
  "cm1_run_dir": "<cm1-run-dir>"
}
```

`CLOUD_CHAMBER_CM1_ROOT` can override `cm1_root` for local testing. `local-data/` is
gitignored and may be used as a repository-local development override for local-only data.

Do not commit local settings or machine-private paths.

## External CM1 Boundary

The repository does not contain CM1 source, a CM1 executable, `LANDUSE.TBL`, generated CM1
run directories, or NetCDF output.

The backend currently discovers or reads local CM1 paths, validates that an executable exists
in the configured run directory, stages required runtime files into generated run packages,
and launches the external executable only through local or LAN-worker runtime paths.

Automated tests use fake processes and tiny fixtures. Real CM1 execution is local/manual
operational or scientific validation, not a CI dependency.

## Validation Commands

Run the canonical local repository gate from the root:

```sh
scripts/check.sh
```

Common focused checks:

```sh
cd app/frontend
npm run lint
npm run test
npm run build
```

```sh
cd app/backend
python -m ruff format --check .
python -m ruff check .
python -m mypy .
python -m pytest
```

Mocked browser smoke tests are separate from the fast gate:

```sh
scripts/check-e2e.sh
```

`scripts/check-e2e.sh` expects the frontend dev server to be reachable. It runs only the
mocked smoke suite by default.

## Artifact Policy

Do not commit:

- CM1 source or binaries;
- NetCDF output;
- generated run directories;
- runtime data or sounding caches;
- `LANDUSE.TBL`;
- local settings or machine-private paths;
- logs, screenshots, videos, traces, reports, or large processed visualization artifacts.

Keep generated or local validation evidence outside git unless an approved task explicitly
allows a tiny fixture or text summary.

## Related Operational Docs

- [Current Architecture](../current/CURRENT_ARCHITECTURE.md)
- [Ingest, Results, And Runtime Cleanup Lifecycle](../current/INGEST_RESULTS_STORAGE_LIFECYCLE.md)
- [Testing](TESTING.md)
- [CI and Branch Protection](CI_AND_BRANCH_PROTECTION.md)
- [Trusted LAN Worker](LAN_WORKER.md)
- [Playwright E2E](../../app/frontend/e2e/README.md)
