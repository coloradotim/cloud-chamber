# AGENTS.md - Cloud Chamber

## Project Identity

Cloud Chamber is a local-first configuration, run-management, and visualization environment for CM1 cloud experiments.

The goal is to make CM1 usable and beautiful for guided cloud-physics exploration.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.

## Product Rule

CM1 is the high-fidelity model. The app should not pretend to be CM1.

Reduced/light models may be used only for:

- preview
- explanation
- rough guidance
- sanity checks

They are not the source of truth for cloud evolution.

## Durable Distinction

Always distinguish:

```text
Preview estimate
CM1 run configuration
CM1 running/completed result
Visualization interpretation
```

## Guardrails

Do not commit:

- CM1 source
- CM1 binaries
- NetCDF output
- generated run directories
- LANDUSE.TBL
- local-data
- large processed visualization artifacts

Do commit:

- code
- tests
- docs
- schemas
- scenario templates
- tiny fixtures

## Development Expectations

- Use GitHub issues and PRs.
- Keep work scoped to the issue.
- Add tests for new behavior.
- Update docs when architecture/workflow changes.
- Use local fake fixtures in CI; do not require real CM1 in automated tests.
- Do not weaken scientific honesty to make UI look better.

## Initial Architecture Bias

Prefer:

```text
React/Vite frontend + Python FastAPI local backend
```

until a stronger reason appears.

## Local CM1 Runtime

CM1 should remain external to the repo.

Likely local path for Tim:

```text
/Users/timpeterson/cm1r21.1/run
```

Treat this as a local setting, not a hard-coded app constant.

## UI Language

Use atmospheric language first:

- lower-atmosphere humidity
- surface moisture
- surface heating
- cap strength
- cap height
- dry air aloft
- mixing / entrainment
- cloud base
- cloud top
- first cloud time
- rain onset

Raw namelist settings belong in advanced/developer views.

## Testing Notes

Use fake/small fixtures to test:

- scenario schemas
- config generation
- run manifest creation
- fake process execution
- NetCDF ingestion from tiny fixtures
- visualizer metadata loading

Do not require full CM1 runs in CI.

## Before Major Changes

If changing product direction, ask first.

If adding physics/science behavior, document:

1. what physical question it supports
2. what user control it enables
3. what diagnostics validate it
4. what limitations must be disclosed
