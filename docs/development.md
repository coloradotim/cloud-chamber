# Development

Cloud Chamber is a local-first, personal-use CM1 experiment builder, run manager, and visualizer. CM1 is the high-fidelity simulation engine; Cloud Chamber should make CM1 easier to configure, run, inspect, visualize, and learn from.

The first Golden Path is Baseline Shallow Cumulus. Saved results are meant to be replayed and inspected as experiment notebook entries. Optional remote compute is future research only, not a development dependency for the MVP.

Replay / inspect / save is core MVP. Duplicate / tweak / rerun is later. Warm rain remains early, but it does not block the Baseline Shallow Cumulus Golden Path.

## Frontend

From `app/frontend`:

```sh
npm install
npm run dev
npm run lint
npm run test
npm run build
```

The frontend uses TypeScript, React, Vite, Vitest, ESLint, and Prettier. During local development, Vite proxies `/api` requests to `http://127.0.0.1:8000`.

The current first Scenario Builder flow loads Baseline Shallow Cumulus from the backend, shows curated controls and the physical question, requests a dry-run package, and reviews generated files. Preview is explicitly not implemented and not CM1 output. Do not add heavy 3-D rendering dependencies until the visualizer work starts.

## Dev Server Helper

From the repo root:

```sh
scripts/dev.sh start
scripts/dev.sh status
scripts/dev.sh restart
scripts/dev.sh stop
scripts/dev.sh logs
```

The helper starts the backend at `http://127.0.0.1:8000` and the frontend at `http://localhost:5173`, tracks PIDs under `.dev/`, and writes logs to `.dev/backend.log` and `.dev/frontend.log`. Use `scripts/dev.sh restart` after UI or API changes when you want a clean local server state.

The helper expects backend dev dependencies to be installed and `app/frontend/node_modules` to exist. It prefers `app/backend/.venv/bin/python` when present; set `BACKEND_PYTHON`, `BACKEND_PORT`, or `FRONTEND_PORT` to override local defaults.

## Backend

From `app/backend`:

```sh
uv sync --extra dev
uv run python -m uvicorn cloud_chamber.app:app --reload
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest
```

If `uv` is not installed in a local environment yet, the current CI-compatible pip flow is:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m uvicorn cloud_chamber.app:app --reload
python -m ruff format --check .
python -m ruff check .
python -m mypy .
python -m pytest
```

Normal backend checks must not require a local CM1 runtime. Real CM1 paths belong in local settings, not hard-coded app constants.

Implemented backend API endpoints:

- `GET /api/scenarios` lists validated scenario templates for the Scenario Builder and marks Baseline Shallow Cumulus as the Golden Path scenario.
- `POST /api/dry-run-package` validates selected controls and writes a reviewable dry-run package under the configured runtime home. It does not launch CM1, create NetCDF output, or write generated packages into the repo during tests.
- `POST /api/runs/launch` starts one local CM1 run from a generated manifest when local CM1 settings validate.
- `GET /api/runs/status?manifest_path=...` refreshes and returns lifecycle status/log metadata for a run manifest.
- `POST /api/runs/cancel` cancels the active local run when technically practical.

The local run manager assumes one active CM1 run at a time for the MVP. It captures stdout/stderr under the run package `logs/` directory, updates the run manifest through queued/running/completed/failed/canceled states, refuses output-like files before launch, and fails clearly when CM1 settings are missing. Normal tests use fake subprocesses; real CM1 execution remains manual/local and is not required in CI.

The backend skeleton uses Python/FastAPI with pytest, ruff, and mypy. Data/science work should prefer xarray, netCDF4 or h5netcdf, numpy, and pydantic when those layers are added.

Backend work should assume one local CM1 run at a time for the MVP and should avoid large in-memory processing paths for local MacBook Air-scale machines.

When implementing scenario, manifest, result, or visualization contracts, keep product state and provenance labels explicit: preview estimate, generated CM1 configuration, packaged dry-run output, running/completed CM1 result, ingested result metadata, visualizer interpretation, and saved result/notebook entry are different things.

## Local Settings

Cloud Chamber runtime settings are local-only. The default runtime home is:

```text
~/CloudChamber
```

The backend reads optional saved settings from:

```text
~/CloudChamber/settings.json
```

Supported settings fields include:

```json
{
  "cm1_root": "/Users/timpeterson/cm1r21.1",
  "cm1_run_dir": "/Users/timpeterson/cm1r21.1/run",
  "cache_dir": "~/CloudChamber/cache",
  "log_dir": "~/CloudChamber/logs"
}
```

`CLOUD_CHAMBER_CM1_ROOT` can override the saved CM1 root for local development. `CLOUD_CHAMBER_RUNTIME_HOME` can point tests or local experiments at a different runtime home. These are local settings only; do not commit `settings.json`, CM1 binaries, CM1 source, generated run directories, or NetCDF output.

## Repo Layout

Expected structure:

```text
app/frontend/
app/backend/
docs/
scripts/
scripts/cm1/
scenarios/lower-atmosphere/
.github/workflows/
.github/ISSUE_TEMPLATE/
```

Keep top-level folders minimal and understandable.

## Runtime Home

Runtime data belongs outside the repo by default:

```text
~/CloudChamber/
  settings.json
  runs/
  cache/
  logs/
```

Use `./local-data/` only as a gitignored development override. Do not commit generated CM1 run packages, NetCDF outputs, local validation reports, thumbnails, previews, or large visualization artifacts.

If `data/` exists in the repo, treat it as placeholder/fixture-only. Runtime storage belongs in `~/CloudChamber`, not in the source tree.

Dry-run package tests must point runtime home at a temporary directory. Do not run dry-run package generation against the repository root or commit generated package directories.

## Manual CM1 Validation

Before automated launch is trusted, use the Baseline Shallow Cumulus dry-run package as a manual/local/offline bridge into CM1.

1. Create a dry-run package from the Scenario Builder or API.
2. Inspect the generated package under `~/CloudChamber/runs/<run-id>/`.
3. Confirm the package contains:
   - `run_manifest.json`
   - `case_manifest.json`
   - `namelist.input`
   - `input_sounding`
   - `dry_run_report.json`
   - `runtime_file_checklist.json`
4. Confirm the report still says CM1 was not launched and is not a completed result.
5. Confirm local CM1 settings:
   - `CLOUD_CHAMBER_CM1_ROOT`, if set;
   - `~/CloudChamber/settings.json`, if present;
   - default probes such as `/Users/timpeterson/cm1r21.1` and `/Users/timpeterson/cm1r21.1/run`.
6. Compare the package against local CM1 runtime needs, including `cm1.exe` and local-only runtime files such as `LANDUSE.TBL`.
7. Run CM1 manually from the local runtime path when ready. Record the exact command, CM1 version/path, Cloud Chamber commit, run-size preset, controls, runtime, output cadence, log paths, output paths, and any warnings/errors.
8. Keep generated packages, copied runtime files, logs, NetCDF output, and validation reports out of git unless a future policy explicitly creates a tiny synthetic fixture.

The automated local CM1 launcher/log monitor now follows this policy for the first MVP. It preserves the same distinctions: dry-run package, queued/running CM1 process, completed/failed/canceled CM1 run, ingested metadata, and saved result/notebook entry are separate states.

## Whole Repo

From the repo root:

```sh
scripts/check.sh
```

This executable script runs the same fast checks as CI: frontend lint/test/build, backend ruff format/check, backend mypy, backend pytest, shell syntax checks, and basic docs/JSON/YAML sanity.

`scripts/check.sh` is the canonical local validation gate for developers and Codex. It also checks for tracked generated/runtime artifacts and old user-facing product naming.

CI keeps equivalent split jobs named `Frontend`, `Backend`, and `Scripts and config` so branch protection can require stable, readable check names. When adding future scenario-schema, run-manifest, dry-run-package, NetCDF-ingest, or visualizer-metadata checks, update both `scripts/check.sh` and the matching CI job or document why a CI-only/local-only split is necessary.

The local gate intentionally does not run real CM1, require a local CM1 installation, require real NetCDF output, or create generated CM1 artifacts in the repo.

## Scaffold Scope

Do not rebuild the initial scaffold when doing issue work.

Specifically do not:

- implement the 3-D visualizer yet
- implement the CM1 run manager yet
- vendor CM1
- commit generated CM1 outputs
- add real NetCDF sample data unless tiny fixtures are explicitly required
- add complex deployment
- add heavy 3-D rendering dependencies yet
