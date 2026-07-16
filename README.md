# Cloud Chamber

Cloud Chamber is a local-first **cloud-making sandbox that uses real atmospheres
as raw material**.

Its organizing question is:

> Given the soundings available, which ones can make interesting clouds, what
> setup should I use, and how far do I need to push them?

CM1 is the high-fidelity simulation engine. Cloud Chamber finds cloud
opportunities, recommends recipes and run setups, manages local CM1 runs,
organizes results, and helps users watch and understand cloud evolution.

The first visible priorities are growing cumulus/congestus, deep convective
towers, and then precipitation. Cloud Chamber is not a forecast or warning
product.

## Core Direction

The primary experience should support both:

```text
Show me something cool
```

and:

```text
What can we do with this sounding?
```

Cloud Chamber should rank:

```text
sounding + recipe + run setup
```

rather than asking the user to interpret a sounding and guess which CM1
configuration might work.

## Core Workflow

```text
Find promising sounding–recipe pairs
→ recommend a concrete run setup
→ queue a meaningful scout through Build
→ automatically promote a promising scout to a visible full run
→ ingest the result
→ explore the evolving cloud
```

The existing Build workflow remains the execution center: run plan, package,
queue, progress/ETA, stop, ingest, and cleanup. Automatic scout promotion must be
visible and reversible.

## Initial Cloud Recipes

The starting recipe catalog is:

1. **Daytime Evolution** — simplified ordinary heated-day evolution.
2. **Broad Warm/Moist Surface Region** — lower-boundary heterogeneity intended to
   organize growing ascent.
3. **Explicit Thermal Initiation** — a clearly labeled supplied thermal.
4. **Deep-Tower Benchmark** — strong explicit initiation intended to reveal the
   sounding's convective ceiling.
5. **Suppression / Cap Challenge** — learn what is required to make a capped
   atmosphere produce cloud.

Strong idealized assumptions are acceptable when clearly labeled. Scientific
honesty does not require the weakest possible run setup.

## Current Product Shape

- **Build**: cloud-opportunity discovery, sounding/recipe recommendation, run
  setup, package generation, queue/progress/ETA, stop, ingest, and cleanup.
- **Results**: local notebook of completed and ingested CM1 cloud runs.
- **Explore**: time replay, field inspection, cloud interpretation, and visual
  payoff.
- **Frontend**: TypeScript, React, Vite, Vitest, ESLint, Prettier.
- **Backend/tooling**: Python 3.12+, FastAPI, xarray, pytest, ruff, mypy.
- **CI**: GitHub Actions for frontend, backend, scripts, docs, and config sanity.

Real CM1 execution remains local and outside CI.

## Product Guardrails

Cloud Chamber should not pretend to be CM1. Analyzer scores and previews support
recommendation and explanation; CM1 output remains the source of truth for cloud
evolution.

Always distinguish:

```text
Analyzer/recommendation estimate
CM1 run configuration
Packaged run
Queued/running CM1 process
Completed/ingested CM1 result
Visualization interpretation
```

Do not commit CM1 source, CM1 binaries, NetCDF output, generated run directories,
`LANDUSE.TBL`, local data, machine-private settings, or large processed
visualization artifacts.

## Docs

- [Cloud-first product reset](docs/cloud-first-product-reset.md)
- [Product vision](docs/product-vision.md)
- [Current roadmap](docs/current-roadmap.md)
- [Product spec](docs/cloud-chamber-product-spec.md)
- [Architecture and data model](docs/architecture-and-data-model.md)
- [Agent operating rules](AGENTS.md)
- [Development](docs/development.md)
- [Testing and validation](docs/testing-and-validation.md)
- [CI and branch protection](docs/ci-and-branch-protection.md)

## Local Checks

From the repo root:

```sh
scripts/check.sh
```

The script runs the fast checks used by CI. It intentionally does not require a
real CM1 installation or generated model output.

## Local Dev Servers

```sh
scripts/dev.sh start
scripts/dev.sh restart
scripts/dev.sh stop
```

The helper runs the FastAPI backend on `http://127.0.0.1:8000` and the Vite
frontend on `http://localhost:5173`, with logs and PID files under `.dev/`.

## Runtime Data

Runtime data belongs outside the repo:

```text
~/CloudChamber/
  settings.json
  runs/
  cache/
  logs/
```

`./local-data/` may be used as a gitignored development override. Generated CM1
runs and outputs should not live in source control.

## Immediate Work

- **#346**: rank cloud opportunities and build the visible scout-to-full-run
  workflow.
- **#341**: restore the proven explicit thermal/deep-tower capability from the
  earlier Deep Convection Trial.
- **#287**: implement a real daytime-evolution recipe using active place/time
  forcing or an honestly labeled evolving proxy.

Infrastructure is successful only when it helps produce an interesting cloud,
continues a promising one, skips a poor bet, identifies a broken run, or makes a
cloud easier to see and understand.
