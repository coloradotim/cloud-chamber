# Cloud Chamber Product Vision

## Product Name

**Cloud Chamber**

## North Star

Cloud Chamber helps users configure, run, manage, and beautifully visualize local CM1 cloud experiments.

Short version:

> A local studio for playing with CM1 and seeing cloud physics come alive.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.

The lesson from earlier Cloud Lab-style experimentation is simple: do not rebuild CM1 poorly. Cloud Chamber should wrap CM1 with a clearer product workflow, not replace the atmospheric model with hidden fake physics.

## What Cloud Chamber Is

Cloud Chamber is a local-first experiment and visualization environment for CM1.

It should help a user:

```text
Choose a cloud scenario
→ adjust atmospheric controls
→ preview likely behavior
→ run CM1 locally
→ track the run
→ ingest and organize results
→ visualize the 3-D cloud evolution beautifully
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
→ duplicate/tweak/rerun
```

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

Users can name, save, tag, inspect, duplicate, and delete runs.

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
CM1 run configuration
CM1 running/completed result
Visualizer interpretation
```

Never imply:

- a preview is CM1 output
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
10. Duplicate and rerun a scenario.
