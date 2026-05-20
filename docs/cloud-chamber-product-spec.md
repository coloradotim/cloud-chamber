# Cloud Chamber Product Spec

## Product Summary

Cloud Chamber is a local-first desktop/browser application for configuring, running, managing, and visualizing CM1 cloud experiments.

The product should make CM1 approachable without hiding scientific limits.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.

Cloud Chamber's main flow should be product-shaped, not namelist-shaped. Friendly atmospheric controls come first; raw CM1 namelist settings belong in advanced/developer views.

## Personas

### Primary User

A technically curious atmospheric-physics learner/builder who wants to play with real cloud modeling locally.

They are comfortable with long-running local jobs, but do not want to manually edit namelists, hunt for files, or use generic visualization tools for every experiment.

### Secondary User

A scientist/developer who wants a cleaner CM1 workflow for curated idealized cases and visual exploration.

## Key Workflows

### Workflow 1 — Choose Preset Experiment

1. Open app.
2. Choose scenario category.
3. Select preset.
4. See expected behavior, controls, run cost, and output fields.
5. Optionally adjust controls.

### Workflow 2 — Preview Setup

1. Adjust controls.
2. Placeholder preview panel reserves space for future guidance.
3. Future preview diagnostics update quickly when implemented.
4. User understands that preview is not CM1.

### Workflow 3 — Launch CM1 Run

1. Click `Run CM1` or `Create run`.
2. App writes a run manifest, namelist, input sounding, and run directory.
3. App launches local CM1 process or gives a command to run.
4. Status changes to queued/running.
5. Logs are captured.

### Workflow 4 — Monitor Runs

Run manager shows:

- queued
- running
- completed
- failed
- canceled

For each run:

- elapsed time
- current log tail
- output files seen
- estimated output size
- final status

### Workflow 5 — Open Result

1. Select completed run.
2. App ingests or loads processed data.
3. App shows diagnostics and visualizer.
4. User can save/name/tag result.

### Workflow 6 — 3-D Visualization

The visualizer should support:

- time slider/playback
- orbit/pan/zoom camera
- reset camera
- vertical slice
- horizontal slice
- isosurface threshold
- volume opacity controls
- sun angle
- color temperature
- brightness/contrast
- cloud appearance presets

### Workflow 7 — Duplicate / Tweak / Rerun

1. Duplicate previous setup.
2. Change one or more controls.
3. Preview likely difference.
4. Launch a new CM1 run.
5. Compare results later.

## Preset Scenario Schema

Each scenario should define:

```yaml
id:
name:
category:
question:
plain_english_description:
expected_behavior:
controls:
  - id
  - label
  - type
  - default
  - allowed range/options
  - maps_to
cm1_template:
  namelist_template
  input_sounding_template
  runtime_files_needed
outputs_expected:
  fields
  diagnostics
visualization_defaults:
  camera
  fields
  color/opacity
validation_status:
  unrun | generated | accepted | needs_calibration
notes:
```

Initial scenario templates should include:

1. Baseline shallow cumulus.
2. Dry failed cumulus.
3. Capped/suppressed cumulus.
4. Humid vigorous cumulus / humid low-cloud contrast.
5. Low stratus / low-cloud layer.
6. Warm rain / precipitating shallow cloud.

## Run Manifest Schema

Each run should write a manifest like:

```yaml
run_id:
scenario_id:
name:
created_at:
status:
cm1_version:
cm1_run_dir:
output_dir:
configuration:
  controls:
  namelist_parameters:
  input_sounding:
preview:
  expected_outcome:
  warnings:
execution:
  command:
  started_at:
  finished_at:
  exit_code:
  logs:
ingestion:
  status:
  processed_artifacts:
visualization:
  default_view:
  thumbnails:
user:
  saved:
  tags:
  notes:
```

Run lifecycle states should include:

```text
created
packaged
queued
running
completed
failed
canceled
```

Dry-run packaged experiments must be distinct from queued/running/completed CM1 runs.

## MVP Scope

### In Scope

- New local project skeleton
- Preset scenario definitions
- Local run manifest format
- Generate CM1 case/run directories
- Launch CM1 through local command
- Track process/log status
- Ingest NetCDF output or create intermediate artifacts
- Basic 3-D visualizer MVP
- Result library
- Save/name/tag runs

### Out Of Scope For MVP

- Cloud-hosted compute
- Browser-native CM1 execution
- Full namelist editor as primary UI
- Full photorealistic cloud rendering
- True production LES workflow guarantee
- Terrain/orographic cases unless explicitly added
- Warm-rain microphysics beyond fields CM1 already outputs

### Current Near-Term Non-Goals

- Build the full 3-D visualizer before the package/run spine exists.
- Implement a fake physics predictor.
- Vendor CM1.
- Commit generated CM1 output or real NetCDF outputs.
- Overbuild deployment.

## 3-D Visualizer MVP

Start with a practical visualizer, not a cinematic renderer.

MVP visual modes:

1. Cloud water isosurface
2. Cloud water volume/opacity approximation
3. X/Z/Y slices
4. Time replay
5. Camera orbit/pan/zoom
6. Field selector
7. Simple lighting controls

Later:

- volumetric ray marching
- shadows
- edge brightening
- cloud-base darkening
- fly-through
- cinematic export

## Local Data Policy

Do not commit:

- CM1 source
- CM1 binaries
- NetCDF outputs
- generated run directories
- thumbnails if large
- processed volume artifacts if large
- local runtime data under `~/CloudChamber`

Commit:

- scenario templates
- schema docs
- scripts
- tests
- small fixtures
- app code

## Existing Tools To Learn From

Evaluate but do not assume replacement by:

- VAPOR
- ParaView
- Vis5D
- GrADS
- Tecplot

Use them to understand data/visual targets. The product goal remains a CM1-specific guided studio.
