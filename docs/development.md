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

The current first Scenario Builder flow loads Baseline Shallow Cumulus from the backend, shows curated controls and the physical question, requests a dry-run package, and reviews generated files. Preview is explicitly not implemented and not CM1 output. The first 3-D visualizer work is a scene shell only: use existing React/CSS controls, consume visualization-ready backend metadata, and do not add rendering dependencies until a concrete rendering issue requires them.

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
- `GET /api/runs/status?manifest_path=...` refreshes and returns lifecycle status, product/validation state, command/log paths, short stdout/stderr tails, output-artifact counts, runtime warnings, and timestamps for a run manifest.
- `POST /api/runs/cancel` cancels the active local run when technically practical.
- `GET /api/storage/inventory` reports configured runtime-home disk usage and per-run metadata under `~/CloudChamber/runs/`.
- `POST /api/storage/delete-run` previews or deletes one selected run directory under the configured runtime home.
- `POST /api/results/ingest` creates result metadata from a completed run manifest with NetCDF output.
- `GET /api/results` lists Result Card / Experiment Notebook entries under the configured runtime home.
- `GET /api/results/{result_id}` returns one Result Card with run ID, scenario, run-size preset, physical question, diagnostics summary, first cloud time, max `qc`, max/min `w`, rain yes/no, caveats, output file summary, saved/protected flag, and editable name/tags/notes.
- `PATCH /api/results/{result_id}` updates notebook fields: `name`, `tags`, `notes`, `saved`, and `protected`.
- `POST /api/results/{result_id}/save` marks a card saved/protected without rerunning CM1.

The frontend Results Library shell consumes those Result Card endpoints. It
starts as a scan-friendly table plus a selected result detail/notebook card,
with editable name/tags/notes and save/protect actions when the backend
supports them.

The first 2-D field inspector opens from a Results Library detail/notebook card
and consumes the backend visualization fields/slice endpoints. It requests JSON
slice payloads only; it does not parse raw NetCDF in the browser, replay fields,
or implement 3-D visualization.

The local run manager assumes one active CM1 run at a time for the MVP. It captures stdout/stderr under the run package `logs/` directory, updates the run manifest through queued/running/completed/failed/canceled states, refuses output-like files before launch, and fails clearly when CM1 settings are missing. Normal tests use fake subprocesses; real CM1 execution remains manual/local and is not required in CI.

Launch preflight also refuses placeholder-only CM1-facing files. Older packages containing `&cloud_chamber_domain` or notes-only `input_sounding` files must be regenerated before launch. For Baseline Shallow Cumulus, generated packages now preserve the validated `les_ShallowCu` reference-derived settings while using CM1's external `input_sounding` route for the thermodynamic profile, quick-look runtime/cadence when selected, and NetCDF output for ingest.

Baseline Shallow Cumulus currently uses `zd = 4500.0` for Rayleigh damping in the 6 km quick-look domain. Preflight rejects namelists where Rayleigh damping would begin at or below half the configured domain top. A CM1 process that exits `0` without NetCDF or raw CM1 `.dat/.ctl` artifacts is recorded as `validation_status: needs_review` and `product_state: process_completed_no_output`, not as a completed usable CM1 result.

Generated Baseline Shallow Cumulus packages prefer CM1 NetCDF output with `output_format = 2` and `output_filetype = 2`. CM1 documents `output_format = 1` as GrADS/direct-access output and `output_format = 2` as NetCDF. The first successful smoke run produced `.dat/.ctl` files, so those are cataloged as raw CM1 artifacts while the next manual run should verify the NetCDF path.

When a run completes, manifest output metadata should keep these buckets separate:

- `raw_cm1_artifacts` for `.dat/.ctl` CM1 output files;
- `netcdf_paths` for preferred NetCDF output;
- `processed_artifacts` for future Cloud Chamber-derived ingest/visualization artifacts;
- `runtime_warnings` for caveats surfaced from logs, such as CM1 floating-point exception flags.

Required runtime files such as `LANDUSE.TBL` are copied from the configured local CM1 run directory into the generated package at launch time. Baseline Shallow Cumulus recovery packages prefer `config_files/les_ShallowCu/LANDUSE.TBL` when that local CM1 reference file is available. These copied files are local/generated artifacts under `~/CloudChamber/runs/<run-id>/`; do not commit them.

Runtime output can grow quickly. The storage inventory endpoint scans only the configured Cloud Chamber runtime home, normally `~/CloudChamber`, and reports total size plus per-run size, manifest metadata, output artifact counts, and conservative cleanup categories such as `dry_run_only`, `completed_with_output`, `completed_no_output`, `failed`, `canceled`, `saved_or_protected`, `missing_manifest`, and `malformed_manifest`.

Results / Storage uses the same endpoints. It shows the runtime-home summary, the 50 GB warning-threshold state, largest run directories first, result-card names when associated, output artifact counts, saved/protected state, and cleanup categories. It never deletes automatically.

The MVP storage warning threshold is 50 GB for the configured runtime home. Inventory reports the threshold and whether runtime storage is at or above it. This is a configurable product default, not a hard scientific limit, and it never auto-deletes anything. When the threshold is reached, use the inventory's largest-run list and dry-run cleanup mode before confirming deletion of selected runs.

Run deletion is explicit and conservative. A preview request uses `dry_run: true`; a real delete requires `dry_run: false` and `confirm: true`. Cleanup only targets `~/CloudChamber/runs/<run-id>/`, refuses path traversal and symlink escapes, refuses running runs, and refuses saved/protected runs unless `force_saved: true` is supplied. The MVP UI does not expose force deletion for saved/protected runs. Deleting a run removes its local generated package, output artifacts, copied runtime files, and logs. Cleanup must never target the source repo, home directory, runtime home itself, or the external CM1 installation.

The backend skeleton uses Python/FastAPI with pytest, ruff, and mypy. Data/science work should prefer xarray, netCDF4 or h5netcdf, numpy, and pydantic when those layers are added.

The first result ingest path uses xarray to read tiny or local NetCDF files and writes `result_metadata.json` next to the run manifest under the generated run directory. It extracts metadata only: dimensions, coordinates, variables, units, time coordinate, grid shape, source paths, provenance, and warnings. It does not compute diagnostics, create visualization-ready arrays, parse `.dat/.ctl` payloads, or copy real output into git.

NetCDF ingest reads the full CM1 model-output sequence when a run writes files such as `cm1out_000001.nc`, `cm1out_000002.nc`, and later output indices. Stats files such as `cm1out_stats.nc` are classified separately from model-field time-series files. Re-ingesting a completed run rewrites `result_metadata.json` with model-output file count, total time steps, first/last output time, direct-or-inferred time source, diagnostics, and caveats for skipped/corrupt files.

Result cards are derived from `result_metadata.json` and optional local
`result_card.json` notebook state. Updating or saving a result card writes only
that small notebook-state file under the run directory; it does not copy,
rewrite, or commit NetCDF output.

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
7. Regenerate any package that still contains placeholder-only `namelist.input` or notes-only `input_sounding` files.
8. Run CM1 manually from the local runtime path when ready. Record the exact command, CM1 version/path, Cloud Chamber commit, run-size preset, controls, runtime, output cadence, log paths, output paths, and any warnings/errors.
9. Confirm whether the generated `output_format = 2` package produces NetCDF on the local CM1 build. If it does not, keep `.dat/.ctl` output cataloged as raw artifacts and document the blocker before changing ingest strategy.
10. Keep generated packages, copied runtime files, logs, NetCDF output, `.dat/.ctl` output, and validation reports out of git unless a future policy explicitly creates a tiny synthetic fixture.

The automated local CM1 launcher/log monitor now follows this policy for the first MVP. It preserves the same distinctions: dry-run package, queued/running CM1 process, completed/failed/canceled CM1 run, ingested metadata, and saved result/notebook entry are separate states.

The Build workspace now stitches the local loop together in the app: create a
package, launch local CM1, refresh status/logs, review output counts, ingest
completed NetCDF output, then open the resulting card in Results, Inspect, or
Visualize. Use mocked backend responses for automated UI tests. Do not run real
CM1 or write generated output in CI.

## Whole Repo

From the repo root:

```sh
scripts/check.sh
```

This executable script runs the same fast checks as CI: frontend lint/test/build, backend ruff format/check, backend mypy, backend pytest, shell syntax checks, and basic docs/JSON/YAML sanity.

`scripts/check.sh` is the canonical local validation gate for developers and Codex. It also checks for tracked generated/runtime artifacts and old user-facing product naming.

CI keeps equivalent split jobs named `Frontend`, `Backend`, and `Scripts and config` so branch protection can require stable, readable check names. When adding future scenario-schema, run-manifest, dry-run-package, NetCDF-ingest, or visualizer-metadata checks, update both `scripts/check.sh` and the matching CI job or document why a CI-only/local-only split is necessary.

The local gate intentionally does not run real CM1, require a local CM1 installation, require real NetCDF or `.dat/.ctl` output, or create generated CM1 artifacts in the repo.

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
