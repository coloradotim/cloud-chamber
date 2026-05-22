# Cloud Chamber Product Spec

## Product Summary

Cloud Chamber is a local-first desktop/browser application for configuring, running, managing, and visualizing CM1 cloud experiments for personal learning and exploration.

The product should make CM1 approachable without hiding scientific limits.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.

Cloud Chamber's main flow should be product-shaped, not namelist-shaped. Friendly atmospheric controls come first; raw CM1 namelist settings belong in advanced/developer views.

The first Golden Path case is Baseline Shallow Cumulus. Warm rain remains early, but it should not block completing that first end-to-end case.

Replay / inspect / save is core MVP. Duplicate / tweak / rerun is later.

## Personas

### Primary User

A technically curious atmospheric-physics learner/builder who wants to play with real cloud modeling locally.

They are comfortable with long-running local jobs, but do not want to manually edit namelists, hunt for files, or use generic visualization tools for every experiment.

### Secondary User

A scientist/developer who wants a cleaner CM1 workflow for curated idealized cases and visual exploration.

## Key Workflows

### Workflow 0 — Baseline Shallow Cumulus Golden Path

The first complete product loop is:

```text
Pick Baseline Shallow Cumulus
-> adjust curated controls
-> choose run-size preset
-> validate setup
-> generate CM1 run package
-> launch local CM1
-> monitor logs/status
-> ingest NetCDF output
-> create result card / experiment notebook entry
-> replay cloud evolution
-> open 3-D visualizer
-> save/name/tag result
```

Physical question:

```text
How do low-level moisture, surface heating, cap strength, cap height, dry air aloft, and mixing/entrainment affect shallow-cumulus formation, timing, depth, updraft strength, and cloud-water evolution?
```

Expected CM1-facing package contents:

```text
run_manifest.json
scenario metadata / case_manifest.json
namelist.input
input_sounding or sounding/input profile file
runtime file checklist
dry-run report
visualization defaults
```

Expected diagnostics:

```text
cloud formed / failed
first cloud time
cloud base
cloud top
max vertical velocity
max or summary cloud water
cloud-water time evolution
rain onset if available
main limiting factor or interpretation note
```

Exact morphology is not pass/fail. The acceptance question is whether the product honestly configures, runs, records, ingests, replays, inspects, and visualizes a credible idealized CM1 result.

### Workflow 1 — Choose Preset Experiment

1. Open app.
2. Choose scenario category.
3. Select preset.
4. See expected behavior, controls, run cost, and output fields.
5. Optionally adjust controls.

The first implemented Scenario Builder flow is intentionally narrow: it loads validated scenario templates from the local backend, defaults to Baseline Shallow Cumulus, displays the scenario description and physical question, exposes only product-facing curated controls, lets the user choose a run-size preset, and requests a dry-run package for review.

The UI must continue to avoid raw CM1 namelist fields in the primary flow. Raw generated files can be listed in dry-run review because they are outputs of the package step, not user-facing controls.

### Workflow 2 — Preview Setup

1. Adjust controls.
2. Placeholder preview panel reserves space for future guidance.
3. Future preview diagnostics update quickly when implemented.
4. User understands that preview is not CM1.

Current behavior is a placeholder only. It must explicitly say preview is not implemented, not CM1 output, not a completed result, and not a visualization interpretation.

### Workflow 2.5 — Review Dry-Run Package

1. Request a dry-run package from the Scenario Builder.
2. Backend validates the scenario template and selected controls.
3. Backend writes package files under the configured runtime home, not the repo.
4. UI displays package path, validation/product state, generated files, physical question, selected run-size preset, and cost/size notes.
5. UI states that CM1 was not launched and the package is not a completed CM1 result.

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
5. User can replay and inspect the saved result later.

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

The broad original visualizer goal in #31 has been superseded by staged implementation issues. The visualizer should build from saved/ingested results and backend visualization-ready data, not from raw NetCDF parsing in the browser.

Staged visualizer path:

```text
Visualization-ready data contract (#72)
-> 2-D field inspection MVP (#73)
-> 3-D scene shell (#77)
-> cloud-water rendering MVP (#78)
-> slice planes (#79)
-> later visual polish / fly-through / export (#80)
```

Every visualizer stage must preserve provenance labels and make clear that rendered output is an interpretation of CM1-derived data.

### Workflow 7 — Duplicate / Tweak / Rerun

1. Duplicate previous setup.
2. Change one or more controls.
3. Preview likely difference.
4. Launch a new CM1 run.
5. Compare results later.

This workflow is useful, but it is not the core first-MVP result behavior. Replay, inspect, save, name, and tag completed CM1 results first; duplicate/tweak/rerun can mature after the Result Card / Experiment Notebook model is reliable.

## Run Size Presets

### Quick look

- Target: roughly 10-20 minutes when feasible on the local Mac.
- Purpose: sanity checks, setup inspection, and rough cloud behavior.
- For Baseline Shallow Cumulus, this is the first runtime-only variant derived from the validated `les_ShallowCu` baseline: `timax = 10800.0` and `tapfrq = 900.0`.
- It preserves the reference grid, vertical spacing, domain top, surface stress/roughness path, moisture/sounding, surface fluxes, turbulence/SGS settings, damping settings, boundary conditions, NetCDF output, and reference `LANDUSE.TBL` staging behavior.
- Lower confidence is acceptable if clearly labeled; do not use the old compact quick-look derivative as evidence or as a tuning base.

### Standard

- Target: normal personal exploration run and the current Baseline Shallow Cumulus reference-derived baseline.
- Purpose: useful saved result and diagnostics.
- For Baseline Shallow Cumulus, this preserves the validated `les_ShallowCu` timing: `timax = 21600.0` and `tapfrq = 3600.0`.
- Expected to balance runtime, output size, and confidence for repeated local use after manual validation.

### Deep / overnight

- Target: long richer runs that may take hours or overnight.
- Purpose: prettier, more detailed, or higher-confidence result exploration.
- Should be explicit about local resource use and output size before launch.

Runtime estimates are approximate until locally validated for a specific CM1 build, scenario, and machine. The first local hardware target is a 2024 MacBook Air with 8GB RAM, so the MVP should assume one local CM1 run at a time and conservative output handling.

Runtime tier metadata should be carried through scenario templates, generated run packages, dry-run reports, run manifests, result metadata, and result cards. If estimate data is not locally validated yet, the UI/report should say `unknown until validated` instead of inventing precision.

## Preset Scenario Schema

Backend scenario templates are validated by the `ScenarioTemplate` contract. Each scenario should define:

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
run_size_presets:
  quick_look
  standard
  deep_overnight
physical_question:
learning_goals:
variation_policy:
  one_control_at_a_time_from_baseline: true
validation_status:
  unrun | generated | accepted | needs_calibration
notes:
```

Validation rules should reject templates that:

- omit product-facing controls
- define a choice control whose default is not one of its options
- define a number control without a valid range
- omit one of the quick / standard / deep run-size presets
- reference unknown controls from the one-control variation policy
- include undeclared fields

The schema is intentionally product-first. Raw CM1/developer controls can exist as advanced metadata, but product-facing controls remain the primary path.

Initial scenario templates should include:

1. Baseline shallow cumulus.
2. Dry failed cumulus.
3. Capped/suppressed cumulus.
4. Humid vigorous cumulus / humid low-cloud contrast.
5. Low stratus / low-cloud layer.
6. Warm rain / precipitating shallow cloud.

Baseline shallow cumulus is the first hero case. Warm rain remains early but does not block the Golden Path.

The initial lower-atmosphere templates live under `scenarios/lower-atmosphere/` as validated JSON metadata. They are honest scenario definitions and teaching contracts, not final scientific calibration. Baseline Shallow Cumulus now has a CM1-facing package candidate, while broader control-to-CM1 mapping fields remain provisional until local/manual CM1 validation accepts them.

## CM1 Input Generation Contract

Generated run packages should eventually include:

```text
run_manifest.json
case_manifest.json
namelist.input
input_sounding
dry_run_report.json
runtime_file_checklist.json
```

The current Baseline Shallow Cumulus recovery contract renders CM1-facing `namelist.input` from CM1's local `les_ShallowCu` reference path (`testcase = 3`, `isnd = 19`). It preserves the reference grid, runtime, domain top, Rayleigh damping, surface/ocean/flux settings, and surface stress path as much as possible. It also writes a numeric CM1-readable `input_sounding` reference profile, although the baseline namelist uses CM1's built-in BOMEX analytic sounding rather than reading that file by default.

The first full-sequence NetCDF ingest of `dry-run-157b09a178e1` found 25 model-output files and 25 time steps, but no usable cloud or vertical velocity: `max_qc_kg_kg = 0.0`, `max_w_m_s = 0.0`, and multiple NaN/Infinity caveats in surface and thermodynamic fields. The generated quick-look package therefore now uses a fixed small ocean roughness length (`set_znt = 1`, `cnst_znt = 0.0002`) instead of the reference dynamic roughness / fixed friction-velocity path that produced invalid local output.

A follow-up local/manual validation run, `dry-run-calibration-20260522132903`, confirmed the fixed roughness value is written and CM1 completes with NetCDF output, but it still produces no cloud, no vertical motion, and NaN/Infinity caveats in target fields. The fixed-roughness derivative is therefore not the recovery baseline. Cloud Chamber should recover from `les_ShallowCu` first, then introduce any quick-look scaling one change at a time.

The first `les_ShallowCu` reference-derived Cloud Chamber run, `dry-run-les-shallowcu-20260522140642`, completed with `exit_code = 0`, produced NetCDF output, and ingested 7 model-output time steps from 0 to 21600 seconds. First-pass diagnostics reported `cloud formed; rain detected`, first cloud time at 3600 seconds, `max_qc_kg_kg = 0.002192789688706398`, `max_w_m_s = 6.962291717529297`, and `min_w_m_s = -3.7671568393707275`. This validates the recovery direction: use the reference-derived case as the Baseline Shallow Cumulus Golden Path source, then derive shorter quick-look variants later.

The first quick-look Baseline Shallow Cumulus variant is derived from that validated reference package by changing only runtime and output cadence: `timax = 10800.0` and `tapfrq = 900.0`. It intentionally preserves the reference domain/grid, vertical spacing, domain top, surface stress/roughness path, moisture/sounding, surface fluxes, turbulence/SGS settings, damping settings, boundary conditions, NetCDF output, and reference `LANDUSE.TBL` staging behavior.

The first quick-look validation run, `dry-run-quicklook-les-shallowcu-20260522151536`, completed with `exit_code = 0`, produced NetCDF output, and ingested 13 model-output time steps from 0 to 10800 seconds. Package size was 206 MB. First-pass diagnostics reported `cloud formed; rain detected`, first cloud time at 1800 seconds, `max_qc_kg_kg = 0.002192789688706398`, `max_w_m_s = 6.866957187652588`, and `min_w_m_s = -4.21529483795166`. This confirms the shorter runtime/cadence-only quick-look variant still produces cloud and vertical motion while preserving the reference-derived settings.

Default cloud-scale assumptions:

```text
64 x 64 x 75 grid
100 m horizontal spacing
40 m nominal vertical spacing
18000 m domain top
21600 s runtime
3600 s output cadence
NetCDF output as the intentional Cloud Chamber ingest-path change
```

Quick-look timing for Baseline Shallow Cumulus:

```text
10800 s runtime
900 s output cadence
all other reference-derived case settings preserved
```

If a scenario needs different size, spacing, runtime, cadence, or runtime files, the deviation must be explicit and documented.

Dry-run package generation creates these files for review without launching CM1:

- `run_manifest.json`
- `case_manifest.json`
- `namelist.input`
- `input_sounding`
- `dry_run_report.json`
- `runtime_file_checklist.json`

The dry-run report must state that it is not a completed CM1 result, record that CM1 was not launched, include selected run-size preset, include physical question and controls, include expected diagnostics and visualization defaults, and use `unknown until validated` for unvalidated cost/size estimates.

Launch preflight must reject placeholder-only CM1-facing files, including old `&cloud_chamber_domain` fragments or notes-only `input_sounding` artifacts. Required external runtime files such as `LANDUSE.TBL` are copied from the configured local CM1 run directory into the generated runtime package at launch time. These staged files are local/generated artifacts and must not be committed.

## Curated Controls And Diagnostics

The first lower-atmosphere controls should use atmospheric language:

```text
low-level humidity
surface heating
surface moisture / moisture supply
cap strength
cap height
dry air aloft
mixing / entrainment
```

Early controls can be relative presets such as drier/baseline/more humid, weaker/baseline/stronger heating, lower/baseline/higher cap, and less dry/baseline/drier air aloft. Raw namelist fields belong in advanced/developer views.

Initial diagnostics should include:

```text
cloud formed / failed
first cloud time
cloud base
cloud top
max vertical velocity
max or summary cloud water
cloud-water time evolution
rain onset if available
rain-water summary if available
main limiting factor
```

First variations should favor one-control-at-a-time changes around Baseline Shallow Cumulus. Large arbitrary parameter sweeps are not the primary learning path.

### First Baseline Shallow Cumulus Diagnostics

The first implemented diagnostics are personal-learning summaries, not publication-quality LES validation. Exact cloud morphology is not pass/fail.

Cloud detection uses:

```text
qc_cloud_threshold_kg_kg = 1e-6
minimum_cloud_grid_cells = 10
```

Cloud Chamber marks `cloud_formed` only when at least one output time has 10 or more finite grid cells with `qc >= 1e-6 kg/kg`. This avoids declaring cloud from one isolated noisy cell. First cloud time is the first output time meeting the same rule.

Cloud-water diagnostics include max `qc`, time of max `qc`, a `qc` max time series, cloud fraction time series, cloud-present time steps, and first-pass cloud base/top when a vertical coordinate is available. Cloud fraction is the count of finite cells at or above the `qc` threshold divided by the count of finite `qc` cells. Cloud base/top is a grid-cell diagnostic: lowest/highest vertical coordinate where any finite grid cell has `qc` above threshold. It is not yet a polished meteorological cloud-base product.

Vertical velocity diagnostics use `w` when present and compute max/min `w`, time of max/min `w`, and max/min time series while preserving units when available.

Rain diagnostics use `qr` when present:

```text
qr_rain_threshold_kg_kg = 1e-7
```

If `qr` is absent, the user-facing result says `No rain detected.` and the metadata records that the `qr` field was absent. Missing `qr` does not fail the diagnostics.

NaN and infinity values are ignored for finite min/max and fraction summaries. Field-specific caveats record non-finite values or entirely non-finite target fields. CM1 runtime floating-point exception flags are preserved as caveats and evaluated against the target diagnostic fields rather than treated as automatic run failure.

Shared controls are controls that can be compared across multiple lower-atmosphere scenarios, such as low-level humidity, surface heating, cap strength, cap height, dry air aloft, and mixing/entrainment. Scenario-specific controls should be introduced only when a scenario needs them to answer its physical question.

## Run Manifest Schema

Run manifests are validated metadata records. They describe what Cloud Chamber generated, where it lives, how it maps toward CM1, and what product state it is in. They do not require NetCDF output to exist.

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
result:
  result_id:
  diagnostics_summary:
  key_frames:
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
ingested
saved
```

Dry-run packaged experiments must be distinct from queued/running/completed CM1 runs.

Validation rules should reject packaged dry-run manifests that include NetCDF output paths, completed/saved manifests that still claim to be dry-run packages, unknown lifecycle states, and saved result entries that are not marked as user-saved.

## Product States And Provenance

Cloud Chamber must preserve these distinctions in UI labels, manifests, result cards, and visualizer copy:

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

A preview or dry-run package is not a completed CM1 result. A visualization is an interpretation of CM1 output, not a new physical source of truth.

Product copy and state names should prefer nouns that reveal provenance:

- `Preview estimate`
- `CM1 configuration package`
- `CM1 run`
- `Completed CM1 result`
- `Ingested result metadata`
- `Visualizer interpretation`
- `Saved experiment notebook entry`

## Result Card / Experiment Notebook

A completed run should produce a replayable saved result. It should feel like an experiment notebook entry, not a disposable job row.

Result cards should support:

```text
result_id
run_id
name
tags
scenario_id
scenario_name
physical question
created_at
completed_at
controls used
run-size preset
CM1 version/path metadata
status
generated config paths
output paths
run logs
diagnostics summary
first cloud time
cloud base/top
max vertical velocity
cloud-water summary
rain onset if available
key frames or bookmarked times
visualization defaults
notes
provenance labels
open in visualizer action
```

The first backend Result Card / Experiment Notebook API exposes a scan-friendly
card over ingested result metadata:

```text
run id
scenario
run-size preset
physical question
diagnostics summary
first cloud time
max qc
max/min w
rain yes/no
caveats
output file summary
saved/protected flag
notes/tags/name
```

Editable notebook state lives beside the local run as `result_card.json`; it
stores `name`, `tags`, `notes`, `saved`, and `protected` without modifying or
copying CM1 output. Saving a card marks it as a saved/protected notebook entry.

The first Results Library UI is intentionally table-first. It lists result
cards from the backend, lets the user select one result, and shows a
detail/notebook card with scenario, run-size preset, status, diagnostics
summary, cloud/rain outcome, first cloud time, max `qc`, max/min `w`, caveats,
output summary, provenance labels, saved/protected state, and editable
name/tags/notes. It can save/protect a result through the backend API.

The library opens a 2-D field inspector from a result detail/notebook entry.
The inspector is a CM1-output inspection surface, not a visualizer or replay
system.

Completed results should be replayable and inspectable without rerunning CM1. Duplicate/tweak/rerun is useful later, but replay/inspect/save is the core MVP result-library behavior.

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
- Replay and inspect saved results

### Out Of Scope For MVP

- Cloud-hosted compute
- Browser-native CM1 execution
- Full namelist editor as primary UI
- Full photorealistic cloud rendering
- True production LES workflow guarantee
- Terrain/orographic cases unless explicitly added
- Warm-rain microphysics beyond fields CM1 already outputs
- Publication-quality LES guarantees
- Operational forecasting workflows

### Current Near-Term Non-Goals

- Build the full 3-D visualizer before the package/run spine exists.
- Implement a fake physics predictor.
- Vendor CM1.
- Commit generated CM1 output or real NetCDF outputs.
- Overbuild deployment.

## 3-D Visualizer MVP

Start with a practical visualizer, not a cinematic renderer.

MVP visualizer work should be staged:

1. Visualization-ready backend data contract.
2. 2-D field inspection for orientation, time indexing, scaling, and field availability.
3. 3-D scene shell with orbit/pan/zoom, reset camera, time slider, field selector, and provenance/rendering labels.
4. Cloud-water rendering MVP for `qc` using visualization-ready data.
5. Horizontal and vertical slice planes for `qc` and `w`.

Later:

- volumetric ray marching
- shadows
- edge brightening
- cloud-base darkening
- fly-through
- cinematic export

True fly-through or move-through should remain on the roadmap after the MVP. Orbit/pan/zoom, reset camera, time replay, slices, field selection, and cloud-water isosurface/opacity approximation are enough for the first visualizer.

The browser should not parse raw CM1 NetCDF directly. Backend ingest and visualization-ready preprocessing should provide selected, provenance-labeled fields for inspection and rendering.

## 2-D Field Inspection MVP

The first inspector opens from a saved or ingested Result Card / Experiment
Notebook entry. It consumes the #72 backend fields/slice API; the browser never
parses raw CM1 NetCDF.

MVP behavior:

- list available fields from the backend, starting with `qc` and `w`, and `qr`
  when present;
- allow field selection and output time selection;
- request horizontal and vertical slice payloads from the backend;
- show field units, native grid, selected time, slice shape/dimensions,
  min/max, finite and non-finite counts, and provenance labels;
- represent missing fields and bad slice requests as UI errors instead of
  crashing;
- clearly label slices as CM1-derived inspection data, not 3-D rendering.

The 2-D inspector is deliberately practical and small. It helps verify field
orientation, time indexing, vertical coordinates, units, and scaling before the
3-D scene shell and cloud rendering work begin.

## Visualization-Ready Data Contract

The first visualization contract is slice-first and backend-owned. The browser
does not parse raw NetCDF; it asks the local backend for selected,
provenance-labeled field metadata and JSON slice payloads from an ingested CM1
result.

Implemented backend endpoints:

```text
GET /api/results/{result_id}/visualization/fields
GET /api/results/{result_id}/visualization/slice
```

The field catalog supports `qc` and `w` first, with `qr` exposed when present.
Initial canonical mapping:

```text
qc   -> cloud_water
w    -> vertical_velocity
qr   -> rain_water
rain -> accumulated_surface_rain
dbz  -> reflectivity
```

The slice endpoint supports:

```text
horizontal: fixed vertical level, y-x plane
vertical_x: fixed y index, z-x plane
vertical_y: fixed x index, z-y plane
```

MVP slices use native CM1 grids and do not interpolate staggered fields:

```text
qc: time, zh, yh, xh
w:  time, zf, yh, xh
```

Every slice payload includes field metadata, selected time/index, shape,
dimension order, JSON numeric values, min/max/mean, finite/non-finite counts,
native coordinate units, caveats, and provenance/rendering/processing labels.
Non-finite values are represented as `null` in JSON.

Vertical coordinate units are preserved. If a vertical coordinate is in
kilometers, Cloud Chamber may add a meter display value while still returning
the native coordinate value and native units.

Future 3-D block payloads should use JSON metadata plus binary `float32` arrays
with max-voxel/downsampling controls. This is a future backend contract, not a
requirement for the 2-D inspector.

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
