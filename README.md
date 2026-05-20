# Cloud Chamber

Cloud Chamber is a local CM1 experiment builder, run manager, and 3-D cloud visualization lab.

It helps users configure CM1 scenarios, run them locally, ingest outputs, and explore cloud evolution through beautiful scientific and atmospheric visualizations.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.

## Core Direction

Build a local CM1 configuration, run-management, and 3-D visualization environment for guided cloud-physics experiments.

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
-> duplicate/tweak/rerun
```

This repo is early-stage. The current code is project foundation, not the full product workflow.

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
- Local checks: `scripts/check.sh`.
- CI: GitHub Actions jobs for frontend, backend, scripts, docs, and config sanity.

## Guardrails

Cloud Chamber should not pretend to be CM1. Lightweight previews may support explanation, rough guidance, and sanity checks, but CM1 remains the source of truth for cloud evolution.

Do not commit CM1 source, CM1 binaries, NetCDF output, generated run directories, `LANDUSE.TBL`, local data, or large processed visualization artifacts.

## Local Checks

From the repo root:

```sh
scripts/check.sh
```

The script is executable and runs the same fast checks as CI.

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

## Initial Scope

This scaffold does not implement the CM1 scenario UI, 3-D visualizer, CM1 run manager, CM1 vendoring, real NetCDF sample data, complex deployment, or heavy 3-D rendering dependencies.
