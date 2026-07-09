# Cloud Chamber Product Vision

## Product Name

**Cloud Chamber**

## North Star

Cloud Chamber helps users configure, run, manage, inspect, explain, and
beautifully visualize local CM1 cloud experiments.

Short version:

> A local CM1 workbench for exploring thermal fate and seeing cloud physics come alive.

Internal anchor:

> Cloud Chamber is a personal, scientifically honest CM1 Thermal Fate workbench:
> curated experiments, meaningful controls, local-first CM1 runs, replayable
> saved results, process diagnostics, selected-region inspection, and beautiful
> visualization.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local
experiment builder, run manager, result notebook, diagnostics layer, and
visualizer.

The lesson from earlier Cloud Lab-style experimentation is simple: do not rebuild CM1 poorly. Cloud Chamber should wrap CM1 with a clearer product workflow, not replace the atmospheric model with hidden fake physics.

Cloud Lab should be treated as archived lesson/source material only. New product work belongs in Cloud Chamber, with useful lessons ported intentionally.

## What Cloud Chamber Is

Cloud Chamber is a local-first experiment and visualization environment for
CM1, primarily for personal exploration and learning. Its organizing product
concept is **Thermal Fate**: why air rises, why some thermals do or do not form
cloud, why some clouds stay shallow, why others grow taller, why some break
through into deep convection, and how precipitation feedback can reorganize or
suppress convection.

It should help a user:

```text
Choose a cloud scenario
→ adjust atmospheric controls
→ preview likely behavior
→ run CM1 locally
→ track the run
→ ingest and organize results
→ inspect and visualize CM1-derived fields beautifully
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
- a real-time slider toy for CM1 execution

## Core Product Promise

A user can choose or configure an atmospheric experiment, run CM1 locally, save
the completed result, and explore what happened through diagnostics, comparison,
selected-region inspection, and provenance-labeled visualization.

CM1 run latency is part of the product model: scenario design, result browsing,
comparison, and inspection are interactive; CM1 execution is a local simulation
run, not an instant slider update.

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
→ inspect diagnostics and fields
→ visualize in 2-D/3-D
→ save/name/tag
→ replay and inspect later
→ compare with related scenario variants
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

Baseline Shallow Cumulus proves the first executable loop. It is not the entire
product vision. The broader product should grow into Thermal Fate scenario
families: moisture-limited, surface-heating-driven, cap-limited,
dry-air-aloft/dilution-limited, deep-convection breakthrough, precipitation
feedback/cold-pool interaction, and low-cloud/stratus cases where useful.

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
- thermal fate
- selected region
- What happened here?
- saturation deficit
- deep breakthrough
- precipitation feedback
- downdraft
- cold pool
- outflow boundary

Raw CM1 namelist settings and raw variable names belong in technical,
advanced, or developer views.

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

### 5. Thermal Fate Diagnostics

Backend-owned diagnostics should sit between result ingest and visualization.
They should distinguish global run diagnostics, local selected-region
diagnostics, comparison diagnostics, and visualizer interpretation.

The selected-region product question is:

```text
What happened here?
```

### 6. Unified Explore

An important payoff, but not the only product center of gravity. Explore should
first feel like one trustworthy instrument for understanding a selected result:
cloud context, synchronized slices, `What happened here?`, and technical
evidence on demand.

Near-term Explore should support:

- time replay
- projection/view controls
- zoom and reset view
- slices
- projections
- selected-region markers
- plain-language explanations
- provenance and caveats

## First Scenario Set

Thermal Fate scenario families should start with:

1. Moisture-limited thermal fate: Baseline, Dry Failed, and humidity ladder.
2. Surface-heating-driven thermal fate.
3. Cap-limited thermal fate: Capped / Suppressed Cumulus.
4. Dry-air-aloft / dilution-limited thermal fate.
5. Deep-convection breakthrough.
6. Precipitation feedback / cold-pool interaction.
7. Low stratus / low-cloud layer where appropriate.

Baseline shallow cumulus is the first end-to-end Golden Path scenario. Warm rain remains early and important, but it should not block proving the baseline shallow-cumulus loop first.

The first variation workflow should favor one-control-at-a-time changes around the baseline instead of arbitrary giant parameter sweeps. This keeps the learning path understandable and keeps CM1 as the truth source.

Later product families can include terrain/orographic cloud, layered
atmospheres, fog / near-surface cloud, and mixed-phase / ice.

## Thermal Fate And Visualization Philosophy

CM1 output is physical source data. The visualizer may interpret it, but must label the interpretation.

The visualizer should serve the Thermal Fate workbench: process overlays,
selected-region markers, cloud base/top, cap/inversion context, updrafts,
moisture/saturation evidence, and precipitation-feedback caveats should guide
renderer choices. Visual polish follows process needs, not the other way
around.

Useful views for the current Explore loop:

- Cloud-water context
- Rain-water field
- Vertical velocity field
- Horizontal slices
- Vertical slices
- Cloud top/base diagnostics
- Time replay
- 3-D projection context
- Selected-region explanation
- Technical evidence and caveats

Renderer upgrades such as isosurfaces, volumetric rendering, cinematic lighting,
fly-through, export, and appearance polish should wait until the notebook,
comparison, and `What happened here?` loop are stable.

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
Editable result/notebook entry
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
7. Open diagnostics and visualization-ready fields.
8. Replay and inspect cloud evolution over time.
9. Save/name/tag the run.
10. Reopen, replay, inspect, and explain a saved result later.

Optional later behavior:

- Create a new variation from the same setup.
- Duplicate and rerun a scenario when that workflow is implemented.

The MVP scientific standard is a credible idealized CM1 cloud lab for personal learning and exploration. It is not a publication-quality LES workflow and not operational forecasting.
