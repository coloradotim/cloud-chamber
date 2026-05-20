# Cloud Chamber Roadmap And Initial Issues

## Phase 0 — Product / Repo Setup

### Issue 1 — Create Cloud Chamber project skeleton

Goal:

Create a new local-first app repo for Cloud Chamber.

Acceptance:

- repo initialized
- AGENTS.md present
- README present
- docs folder present
- frontend/backend skeleton chosen
- generated data ignored
- basic test commands documented

### Issue 2 — Define scenario/run/result schemas

Goal:

Create JSON/YAML schemas or TypeScript/Python types for scenarios, run manifests, and result manifests.

Acceptance:

- scenario schema exists
- run manifest schema exists
- result manifest schema exists
- tests validate example fixtures

### Issue 3 — Add initial scenario catalog

Goal:

Add first CM1 scenario templates as data/config, not code magic.

Initial scenarios:

- baseline shallow cumulus
- dry failed cumulus
- capped/suppressed cumulus
- humid vigorous / humid low-cloud contrast
- low stratus

Acceptance:

- each scenario has friendly controls
- each scenario maps to CM1 config templates
- no generated output committed

## Phase 1 — Local CM1 Configuration And Run Management

### Issue 4 — Build CM1 environment/preflight checker

Goal:

Detect local CM1 readiness.

Checks:

- CM1 run directory
- cm1.exe
- executable bit
- LANDUSE.TBL
- NetCDF support
- Python NetCDF dependencies

### Issue 5 — Generate run directory from scenario

Goal:

Given scenario + controls, produce a runnable CM1 run directory.

Outputs:

- namelist.input
- input_sounding
- run-manifest.json
- copied runtime files

### Issue 6 — Launch and monitor local CM1 run

Goal:

Run CM1 from the app/backend and track status.

Acceptance:

- start run
- capture logs
- detect completion/failure
- prevent overwrite
- store status in manifest

### Issue 7 — Run library MVP

Goal:

List local runs and status.

Acceptance:

- show queued/running/completed/failed
- open logs
- show run metadata
- rename/save/tag

## Phase 2 — Ingestion And Diagnostics

### Issue 8 — Ingest CM1 NetCDF output

Goal:

Convert completed CM1 run output into app-friendly result artifacts.

Acceptance:

- reads NetCDF
- extracts core fields
- creates result manifest
- computes basic diagnostics

Core fields:

- cloud liquid water
- rain water if present
- water vapor
- potential temperature / temperature
- vertical velocity
- pressure/height/coordinates

### Issue 9 — Diagnostics summary

Goal:

Compute and display run-level diagnostics.

Diagnostics:

- first cloud time
- cloud base/top
- max cloud water
- max updraft
- rain onset if present
- domain/resolution
- run duration

## Phase 3 — Visualization MVP

### Issue 10 — 3-D visualizer shell

Goal:

Create a 3-D scene that can load a completed run and display basic spatial data.

Acceptance:

- Three.js/R3F scene
- camera orbit/pan/zoom
- time slider
- field metadata loaded
- placeholder grid/domain box

### Issue 11 — Cloud-water isosurface / volume MVP

Goal:

Render cloud liquid water from processed CM1 output.

Acceptance:

- load time frame
- display cloud water in 3-D
- threshold/opacity control
- time replay
- no fake cloud where cloud water is zero

### Issue 12 — Slices and projections

Goal:

Add scientific inspection views.

Views:

- x-z vertical slice
- y-z vertical slice
- x-y horizontal slice
- max projection
- mean projection

### Issue 13 — Lighting and appearance controls

Goal:

Add beautiful rendering controls.

Controls:

- sun angle
- color temperature
- cloud opacity
- brightness/contrast
- shadow/darkening approximation
- edge highlight later

## Phase 4 — Preview / Explanation Layer

### Issue 14 — Lightweight setup predictor

Goal:

Preview likely behavior before CM1 run.

Outputs:

- likely cloud/no-cloud
- LCL trend
- cap limitation
- dry-air risk
- expected cloud depth/timing rough notes

Clear label:

```text
Preview only — run CM1 for high-fidelity result.
```

### Issue 15 — What changed and why explanation

Goal:

After a completed result, explain the result in user language.

Inputs:

- scenario controls
- diagnostics
- preview expectation
- CM1 result

Outputs:

- what happened
- why it happened
- what to try next

## Phase 5 — Scenario Expansion

Add later after MVP:

- warm rain
- terrain/orographic
- layered atmosphere
- true fog / radiation cooling
- mixed phase / ice

## Recommended First Codex Sequence

1. Create repo skeleton and docs.
2. Add schemas and example scenario fixtures.
3. Add local data ignore policy.
4. Add CM1 environment checker.
5. Add run directory generator.
6. Add fake-CM1 run manager tests.
7. Add ingestion from tiny fixture.
8. Add result library shell.
9. Add 3-D visualizer shell.

## Do Not Start With

Do not start with:

- photorealistic renderer
- full CM1 namelist GUI
- job queue complexity
- cloud deployment
- all scenario types
- full 3-D volume optimization

Start with one credible end-to-end path.
