# Cloud Chamber

Cloud Chamber is a local CM1 experiment builder, run manager, and 3-D cloud visualization lab.

It helps users configure CM1 scenarios, run them locally, ingest outputs, and explore cloud evolution through beautiful scientific and atmospheric visualizations.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.

## Core Direction

Build a local-first, personal-use CM1 configuration, run-management, and 3-D visualization environment for guided cloud-physics experiments.

The first Golden Path is **Baseline Shallow Cumulus**: a credible idealized CM1 case for learning how lower-atmosphere controls shape cloud formation.

## Core Workflow

```text
Choose experiment
-> adjust meaningful atmospheric controls
-> preview likely behavior with a lightweight predictor
-> generate/launch a local CM1 run
-> monitor status/logs
-> ingest results
-> visualize cloud evolution in 3-D
-> save/name/tag useful runs
-> replay and inspect them later
-> optionally create a new variation from the same setup
```

This repo is early-stage. The current app can load the first Scenario Builder flow, select Baseline Shallow Cumulus, show curated controls and the physical question, create a dry-run CM1 package for review, and label preview as not implemented. It does not launch CM1, ingest outputs, or visualize completed results yet.

## Docs

- [Product vision](docs/product-vision.md)
- [Product spec](docs/cloud-chamber-product-spec.md)
- [Architecture and data model](docs/architecture-and-data-model.md)
- [Roadmap and issues](docs/roadmap-and-issues.md)
- [Codex project setup](docs/codex-project-setup.md)
- [Development](docs/development.md)
- [Testing and validation](docs/testing-and-validation.md)
- [CI and branch protection](docs/ci-and-branch-protection.md)

## Current Scaffold

- Frontend: TypeScript, React, Vite, Vitest, ESLint, Prettier.
- Backend/tooling: Python 3.12+, pytest, ruff, mypy.
- First Scenario Builder flow: Baseline Shallow Cumulus selection, curated controls, physical question, dry-run package request, and generated-file review.
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

The first Scenario Builder and dry-run review flow exists. Cloud Chamber still does not implement preview physics, the 3-D visualizer, CM1 run manager, CM1 vendoring, real NetCDF sample data, complex deployment, or heavy 3-D rendering dependencies.
