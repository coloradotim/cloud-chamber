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

The frontend uses TypeScript, React, Vite, Vitest, ESLint, and Prettier. Do not add heavy 3-D rendering dependencies until the visualizer work starts.

## Backend

From `app/backend`:

```sh
uv sync --extra dev
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
python -m ruff format --check .
python -m ruff check .
python -m mypy .
python -m pytest
```

Normal backend checks must not require a local CM1 runtime. Real CM1 paths belong in local settings, not hard-coded app constants.

The backend skeleton uses Python/FastAPI with pytest, ruff, and mypy. Data/science work should prefer xarray, netCDF4 or h5netcdf, numpy, and pydantic when those layers are added.

Backend work should assume one local CM1 run at a time for the MVP and should avoid large in-memory processing paths for local MacBook Air-scale machines.

When implementing scenario, manifest, result, or visualization contracts, keep product state and provenance labels explicit: preview estimate, generated CM1 configuration, packaged dry-run output, running/completed CM1 result, ingested result metadata, visualizer interpretation, and saved result/notebook entry are different things.

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

Do not implement product features in this scaffold PR.

Specifically do not:

- build the CM1 scenario UI yet
- implement the 3-D visualizer yet
- implement the CM1 run manager yet
- vendor CM1
- commit generated CM1 outputs
- add real NetCDF sample data unless tiny fixtures are explicitly required
- add complex deployment
- add heavy 3-D rendering dependencies yet
