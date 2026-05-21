# Cloud Chamber Product Vision

## Product Name

**Cloud Chamber**

## North Star

Cloud Chamber helps users configure, run, manage, and beautifully visualize local CM1 cloud experiments.

Short version:

> A local studio for playing with CM1 and seeing cloud physics come alive.

Internal anchor:

> Cloud Chamber is a personal, scientifically honest CM1 cloud playground: curated lower-atmosphere experiments, meaningful controls, local-first CM1 runs, replayable saved results, and a beautiful 3-D viewer.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.

The lesson from earlier Cloud Lab-style experimentation is simple: do not rebuild CM1 poorly. Cloud Chamber should wrap CM1 with a clearer product workflow, not replace the atmospheric model with hidden fake physics.

Cloud Lab should be treated as archived lesson/source material only. New product work belongs in Cloud Chamber, with useful lessons ported intentionally.

## What Cloud Chamber Is

Cloud Chamber is a local-first experiment and visualization environment for CM1, primarily for personal exploration and learning.

It should help a user:

```text
Choose a cloud scenario
→ adjust atmospheric controls
→ preview likely behavior
→ run CM1 locally
→ track the run
→ ingest and organize results
→ visualize the 3-D cloud evolution beautifully
→ replay and inspect saved results later
→ understand what happened
```

## What Cloud Chamber Is Not

Cloud Chamber is not:

- a replacement for CM1
- a lightweight solver pretending to be CM1
- a generic scientific plotting tool
- a web app that runs CM1 in the browser
- a dashboard full of raw namelist parameters
- a toy renderer with hidden fake physics

## Core Product Promise

A user can choose or configure an atmospheric experiment, run CM1 locally, and explore the output in a beautiful 3-D visualizer with understandable controls and diagnostics.

## First Useful Workflow

The first useful workflow is not a full visualizer. It is the scenario package spine:

```text
scenario template
-> user-adjusted experiment config
-> validation
-> run manifest
-> generated CM1 run package
-> dry-run report
```

That spine should lead directly to local CM1 launch/monitoring, then ingest and visualization.

## Primary User Loop

```text
Choose experiment
→ adjust controls
→ preview likely outcome
→ launch CM1 run
→ monitor status/logs
→ open result
→ visualize in 3-D
→ save/name/tag
→ replay and inspect later
→ optionally create a new variation from the same setup
```

Replay / inspect / save is core MVP. Duplicate / tweak / rerun is later.

## Golden Path Principle

Baseline Shallow Cumulus is the first hero case because it can prove the whole Cloud Chamber loop with one scientifically honest, approachable CM1 experiment.

The first hero case should answer:

```text
How do low-level moisture, surface heating, cap strength, and dry air aloft shape whether shallow cumulus forms, when it appears, how tall it gets, and how much cloud water develops?
```

Warm rain remains early, but it should not block the Golden Path. Precipitating shallow cloud workflows should build on the baseline loop after the baseline case can be configured, packaged, run locally, ingested, replayed, inspected, and opened in the visualizer.

## User-Facing Concepts

The product should use atmospheric language first:

- low-level humidity
- surface moisture
- surface heating
- cap strength
- cap height
- dry air aloft
- mixing/entrainment
- cloud base
- cloud top
- first cloud time
- rain onset
- updraft strength
- cloud water

Raw CM1 namelist settings belong in an advanced/developer view.

The first controls should favor relative, teachable changes around a baseline:

- drier / baseline / more humid low-level air
- weaker / baseline / stronger surface heating
- lower / baseline / higher cap
- weaker / baseline / stronger cap
- less dry / baseline / drier air aloft
- weaker / baseline / stronger mixing/entrainment

The first variation workflow should change one control at a time. This is a product teaching choice, not a claim that the atmosphere changes one variable at a time.

## Product Layers

### 1. Scenario Builder

Guided setup for CM1 experiments.

It should provide presets and friendly controls that map to CM1 namelists/soundings/manifests.

### 2. Preview / Light Predictor

A simplified model or diagnostic layer that helps users understand likely behavior before running CM1.

It should be clearly labeled as preview only.

### 3. Local Run Manager

Creates, launches, tracks, and logs CM1 runs.

CM1 runs can be long and local. The user should be able to start a run, leave it, and come back later.

### 4. Results Library

Local library of completed/failed/running CM1 experiments.

Users can name, save, tag, replay, inspect, explain, and delete runs. Saved completed results should behave like experiment notebook entries. Duplicating or rerunning a saved setup is useful later, but the first MVP does not need to make rerun a central result-library feature.

### 5. 3-D Visualizer

The main payoff.

Visualize CM1 output with:

- time replay
- orbit/pan/zoom
- pan/tilt/zoom camera controls
- fly-through / move-through later
- sun angle
- color temperature
- opacity/brightness controls
- slices
- projections
- isosurfaces
- volume rendering eventually

## First Scenario Set

Start with:

1. Baseline shallow cumulus
2. Dry failed cumulus
3. Capped/suppressed cumulus
4. Humid vigorous cloud / humid low-cloud contrast
5. Low stratus / low-cloud layer
6. Warm rain / precipitating shallow cloud

Baseline shallow cumulus is the first end-to-end Golden Path scenario. Warm rain remains early and important, but it should not block proving the baseline shallow-cumulus loop first.

The first variation workflow should favor one-control-at-a-time changes around the baseline instead of arbitrary giant parameter sweeps. This keeps the learning path understandable and keeps CM1 as the truth source.

Later:

7. Terrain/orographic cloud
8. Layered atmosphere
9. Fog / near-surface cloud
10. Mixed-phase / ice

## Visualization Philosophy

CM1 output is physical source data. The visualizer may interpret it, but must label the interpretation.

Useful views:

- Cloud-water volume / isosurface
- Rain-water field
- Vertical velocity field
- Horizontal slices
- Vertical slices
- Cloud top/base diagnostics
- Time replay
- 3-D camera exploration
- Appearance rendering from cloud water
- Lighting and camera controls

## Trust/Honesty Rules

Always distinguish:

```text
Preview estimate
Generated CM1 configuration
Packaged dry-run output
Queued/running CM1 process
Completed CM1 result
Failed/canceled CM1 run
Ingested result metadata
Visualizer interpretation
Saved result/notebook entry
```

Never imply:

- a preview is CM1 output
- a dry-run package is a completed result
- a visualization interpretation is a raw model field
- CM1 runs live in browser
- a scenario is validated if it has not been inspected

## Success Criteria For The MVP

The MVP should let a user:

1. Pick a preset scenario.
2. See/edit meaningful controls.
3. Generate a CM1 run directory from the setup.
4. Launch CM1 locally.
5. Track whether the run is queued/running/done/failed.
6. Ingest NetCDF output into an app-friendly format.
7. Open the result in a basic 3-D viewer.
8. Replay cloud evolution over time.
9. Save/name/tag the run.
10. Reopen, replay, inspect, and explain a saved result later.

Optional later behavior:

- Create a new variation from the same setup.
- Duplicate and rerun a scenario when that workflow is implemented.

The MVP scientific standard is a credible idealized CM1 cloud lab for personal learning and exploration. It is not a publication-quality LES workflow and not operational forecasting.
