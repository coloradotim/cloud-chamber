# Testing

**Status:** Current validation guide

This guide describes the current test and validation layers. It does not define product
priority, recipe status, scenario status, or scientific acceptance criteria.

## Fast Local/CI Gate

From the repository root:

```sh
scripts/check.sh
```

The current fast gate runs:

- frontend lint via `npm run lint`;
- frontend unit/component tests via `npm run test`;
- frontend production build via `npm run build`;
- backend `ruff format --check`;
- backend `ruff check`;
- backend `mypy`;
- backend `pytest`;
- Bash syntax checks for `scripts/*.sh`;
- forbidden tracked-artifact checks for runtime data, CM1 files, NetCDF, videos, and large visualization artifacts;
- basic JSON, YAML, and Markdown sanity checks.

The script uses `app/backend/.venv/bin/python` when present and `BACKEND_PYTHON` has not
been set to another executable. Otherwise it uses `BACKEND_PYTHON` or `python`; when
`BACKEND_PYTHON` points at a local file, use an absolute path so it remains valid after the
script changes working directories.

The fast gate currently does not run Playwright, real CM1, live NOAA/NCEI downloads,
LAN-worker execution, manual browser review, or real scientific validation.

## Frontend Unit And Component Tests

Frontend tests live under `app/frontend` and run with Vitest:

```sh
cd app/frontend
npm run test
```

Current frontend checks use mocked data and API responses. They are appropriate for UI state,
copy, controls, API-request payloads, and rendering behavior that can be tested without
launching CM1 or reading local runtime data.

## Backend Unit And API Tests

Backend tests live under `app/backend/tests` and run with pytest:

```sh
cd app/backend
python -m pytest
```

The current backend suite covers package generation, manifests, local settings, fake local
run execution, queue behavior, LAN-worker helper behavior, ingest, result cards, diagnostics,
runtime storage, sounding parsing, sounding candidates, and visualization payloads.

Backend tests use tiny fixtures, temporary directories, and fake processes. They must not
depend on a real CM1 source tree, CM1 binary, NetCDF run archive, local runtime home, LAN
worker, or live network data.

## Mocked Browser Smoke Tests

Mocked Playwright smoke tests live under:

```text
app/frontend/e2e/mocked-smoke/
```

From the repository root:

```sh
scripts/check-e2e.sh
```

From `app/frontend`:

```sh
npm run test:e2e:smoke
```

`scripts/check-e2e.sh` requires the frontend dev server to be reachable at
`CLOUD_CHAMBER_E2E_BASE_URL` or `http://localhost:5173`. These checks mock API routes and
must not run CM1, mutate real notebook data, delete real run directories, or fetch external
data.

## Read-Only Local-Data Browser Checks

Read-only Playwright checks under `app/frontend/e2e/local-data/` may inspect a local backend
and runtime home when available. They may skip when prerequisites are absent.

These checks are for local confidence only. They must not edit real notebook state, delete
run directories, launch CM1, or commit captured artifacts.

## Manual Operational Validation

Manual operational validation can verify local behavior that automated tests intentionally
mock, such as:

- creating a package through the UI;
- queueing or launching a local run when a real CM1 install is configured;
- observing queue progress and cancellation behavior;
- ingesting completed output;
- using Results and Explore against local runtime data;
- exercising trusted-LAN copy/run/collect/cleanup with a configured worker.

Record only concise findings in a PR or local note. Keep generated packages, logs, output,
screenshots, reports, and runtime data out of git.

## Real CM1 Scientific Validation

Real CM1 runs are scientific or operational evidence, not automated tests. They may establish
what happened for a particular package, sounding, trigger, forcing setup, executable, and
runtime configuration.

When a task requires real CM1 evidence, record:

- package and run identity;
- source sounding or scenario;
- CM1 source/executable provenance when available;
- namelist and output cadence facts needed to interpret the result;
- runtime integrity;
- cloud, velocity, precipitation, reflectivity, and visual outcome facts requested by the task;
- limitations and unresolved questions.

Do not treat a completed CM1 process as a trustworthy scientific result without output,
runtime-integrity, and field-quality context.

## Network/External-Data Validation

Live NOAA/NCEI or other external-data work is manual/local unless a task explicitly authorizes
it. Automated tests use tiny checked-in fixtures and temporary runtime/cache directories.

Downloaded station archives, cache manifests, sounding source files, and derived local cache
data belong under the runtime home or another ignored local path, not under source control.

## Tests Prohibited From CI

CI must not require:

- real CM1 source or binaries;
- real CM1 execution;
- generated run directories;
- NetCDF archives from real simulations;
- live NOAA/NCEI or other network calls;
- trusted-LAN worker access;
- local runtime homes or user settings;
- screenshots, videos, traces, or browser reports committed as evidence.

## Artifact Policy

The validation gate rejects tracked runtime and generated artifacts, including common CM1
output, NetCDF, direct-access files, videos, and large visualization artifacts.

Allowed fixtures must be small, deterministic, and intentionally scoped to tests. Local run
packages, real station caches, CM1 output, Playwright reports, logs, screenshots, and videos
remain untracked.

For browser-test categories and commands, see [Cloud Chamber Playwright E2E](../../app/frontend/e2e/README.md).
