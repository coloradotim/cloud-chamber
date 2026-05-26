# Cloud Chamber

Cloud Chamber is a local CM1 experiment builder, run manager, results notebook,
and Thermal Fate exploration workbench.

It helps users configure CM1 scenarios, run them locally, ingest outputs, save
and compare results, inspect CM1 fields, and understand the fate of thermals
through diagnostics and provenance-labeled visualizations.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local
experiment builder, run manager, result notebook, diagnostics layer, and
visualizer.

## Core Direction

Build a local-first, personal-use CM1 configuration, run-management,
diagnostics, and visualization environment for guided cloud-physics
experiments.

The first executable Golden Path is **Baseline Shallow Cumulus**: a credible
idealized CM1 case for learning how lower-atmosphere controls shape thermal
fate, cloud formation, vertical motion, and rain.

## Core Workflow

```text
Choose experiment
-> adjust meaningful atmospheric controls
-> preview likely behavior with a lightweight predictor
-> generate/launch a local CM1 run
-> monitor status/logs
-> ingest results
-> inspect and visualize CM1-derived fields
-> save/name/tag useful runs
-> replay and inspect them later
-> compare scenario variants
-> ask what happened to a selected thermal/region as diagnostics mature
```

This repo is still evolving, but it is no longer only the initial scaffold. The
current app has a guided local run loop, local CM1 launch/status handling,
NetCDF ingest, result cards/notebook entries, Results/Compare/Storage
workspaces, 2-D field inspection, and an initial 3-D cloud-water/slice
visualization path. Real CM1 execution remains local/manual and outside CI.

## Docs

- [Product vision](docs/product-vision.md)
- [Product spec](docs/cloud-chamber-product-spec.md)
- [Architecture and data model](docs/architecture-and-data-model.md)
- [Thermal Fate process diagnostics](docs/thermal-fate-process-diagnostics.md)
- [Roadmap and issues](docs/roadmap-and-issues.md)
- [Codex project setup](docs/codex-project-setup.md)
- [Development](docs/development.md)
- [Testing and validation](docs/testing-and-validation.md)
- [CI and branch protection](docs/ci-and-branch-protection.md)

## Current App Shape

- Frontend: TypeScript, React, Vite, Vitest, ESLint, Prettier.
- Backend/tooling: Python 3.12+, pytest, ruff, mypy.
- Build workspace: scenario selection, curated controls, package generation,
  launch/status review, and ingest action against local backend APIs.
- Results workspace: result notebook, comparison, and runtime storage views.
- Explore workspace: 2-D slices and initial 3-D visualization over backend
  visualization-ready data.
- Local checks: `scripts/check.sh`.
- CI: GitHub Actions jobs for frontend, backend, scripts, docs, and config sanity.

## Guardrails

Cloud Chamber should not pretend to be CM1. Lightweight previews may support explanation, rough guidance, and sanity checks, but CM1 remains the source of truth for cloud evolution.

Saved results should behave like experiment notebook entries: named, tagged, replayable, inspectable, and explainable. Rerunning or duplicating a saved setup is useful later, but replay/inspect/save is the core MVP result behavior.

Optional remote compute is future research only. Cloud Chamber remains local-first for the MVP.

Do not commit CM1 source, CM1 binaries, NetCDF output, generated run directories, `LANDUSE.TBL`, local data, or large processed visualization artifacts.

## Local Checks

From the repo root:

```sh
scripts/check.sh
```

The script is executable and runs the same fast checks as CI.

`scripts/check.sh` is the canonical local validation gate. Run it before opening PRs. It intentionally does not run real CM1, require a local CM1 installation, use NetCDF sample output, or create generated CM1 artifacts.

## Local Dev Servers

From the repo root:

```sh
scripts/dev.sh start
scripts/dev.sh restart
scripts/dev.sh stop
```

The helper runs the FastAPI backend on `http://127.0.0.1:8000` and the Vite frontend on `http://localhost:5173`, with logs and PID files under `.dev/`.

## Runtime Data

Runtime data belongs outside the repo by default:

```text
~/CloudChamber/
  settings.json
  runs/
  cache/
  logs/
```

`./local-data/` may be used as a gitignored development override, but generated CM1 runs and outputs should not live in source control.

The top-level `data/` directory is placeholder/fixture-only. It is not the runtime data home.

## Current Near-Term Scope

Near-term work is shifting from the first executable Baseline Shallow Cumulus
loop toward Thermal Fate diagnostics: process summaries, selected-region
`What happened here?` inspection, surface-heating and deep-breakthrough
scenario families, precipitation-feedback/cold-pool reasoning, and renderer
upgrades only after those process needs are clear.
