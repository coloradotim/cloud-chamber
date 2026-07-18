# Cloud Chamber Product Spec

> **Archive status:** This historical/superseded document is preserved for project history. It does not establish current product direction, recipe status, roadmap priority, or MVP scope.

## Product Summary

Cloud Chamber is a local-first desktop/browser application for configuring,
running, managing, diagnosing, comparing, and visualizing CM1 cloud experiments
for personal learning and exploration.

The product should make CM1 approachable without hiding scientific limits.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local
experiment builder, run manager, result notebook, diagnostics layer, and
visualizer.

Cloud Chamber's main flow should be product-shaped, not namelist-shaped.
Friendly atmospheric controls come first; raw CM1 namelist settings belong in
advanced/developer views.

The current UX reset direction is:

```text
Cloud Chamber is a guided experiment notebook for understanding why clouds formed, failed, stayed shallow, or grew stronger.
```

The current product model is:

```text
Build = configure and launch one or more planned CM1 runs
Results = notebook for completed/ingested runs
Explore = inspect one result with CM1-derived evidence
```

Build should be organized around configurable observed-sounding runs. Presets
are useful starting points, not separate product cages: a user should be able to
start from a sane preset, inspect the actual CM1-facing settings, and adjust
numeric surface forcing, duration, horizontal cell budget, domain size, and
output cadence within guarded bounds while requesting the full output field set.

See [UX Reset: Guided Experiment Notebook](ux-reset-guided-experiment-notebook.md)
for the PM/design source of truth for future UX work.

See [Current Roadmap](current-roadmap.md) for active sequencing after the
realistic-input and output-product contracts. The legacy issue-by-issue roadmap
is archived reference only.

The first Golden Path case is Baseline Shallow Cumulus. Warm rain remains early, but it should not block completing that first end-to-end case.

Replay / inspect / save is core MVP. Duplicate / tweak / rerun is later.

The user-facing product model is guided experiments, an experiment notebook,
focused visualization, `What happened here?` selected-region explanation,
plain-language explanation, comparison between variants, and technical details
on demand.

**Thermal Fate** remains the internal scientific diagnostic and explanation
model. It should power explanations, confidence/caveat labels, comparison
summaries, selected-region diagnostics, and technical provenance. It should not
dominate the primary visible UI as a process-taxonomy cockpit.

Cloud Chamber is not a real-time slider toy. Scenario design, result browsing,
comparison, and inspection should feel interactive; CM1 execution is a local
simulation run with latency, logs, outputs, and caveats.

See [Thermal Fate process diagnostics](thermal-fate-process-diagnostics.md) for
the current process-diagnostics contract.

See [Cloud Chamber output product specification](contracts/output-product-specification.md)
for the contract that separates raw CM1 NetCDF output, result metadata,
derived scientific products, visualization-ready payloads, future render-ready
products, and external export bundles. Future Explore, Diagnostics Lab, Render
Studio, runtime cleanup, and export work should preserve that browser/backend boundary:
the browser receives bounded backend-prepared products and does not parse raw
NetCDF.

See [Cloud Chamber realistic LES input specification](contracts/realistic-les-input-specification.md)
for the input-side contract before observed sounding import, location/date/
radiation controls, surface-flux controls, GIS/map inputs, or Bench Mode UI.
The first realistic-input path is observed/detailed sounding metadata plus the
CM1 `input_sounding` conversion path, with place/time/source provenance
preserved even when radiation remains disabled.

The first implemented observed-sounding path is intentionally local and
bounded. Build can accept an uploaded NOAA/NCEI IGRA station sounding-data text
file, parse the available sounding times, default to the latest sounding, and
show a package-review summary before generation. Cloud Chamber does not fetch
remote sounding archives in v1. The converted package anchors CM1 `z = 0` to
the station surface elevation, converts geopotential height above mean sea
level into model height above the station, preserves station/location/elevation,
valid time, source format, units, wind metadata, and caveats, and renders a
numeric CM1-readable `input_sounding`. Observed wind direction/speed is
converted to CM1 `u`/`v` wind components, written into the `input_sounding`
profile, and applied through CM1's `isnd = 7` external-sounding path. Packages
with missing or unusable observed winds should block rather than silently fall
back to a reference wind profile.

Cloud Chamber also owns a backend-only local cache foundation for recent IGRA
station-period source files. V1 can refresh the NOAA/NCEI IGRA recent catalog,
join station metadata, filter to a broad Great Plains / Midwest bounding box
(`35.0` to `50.0` latitude, `-106.0` to `-82.0` longitude), and cache selected
or batched station ZIP/text files under `<runtime-home>/cache/igra/recent/`.
The local script surface can list cached sounding times so Tim can inspect a
batch of recent soundings without hand-written HTTP requests. A backend
screening layer can match cached sounding times against explicit pre-run
experiment stories such as shallow cumulus, dry failed, capped/suppressed, or
humid/rainy. There is no universal "best sounding" ranking: the useful candidate
depends on the atmospheric question being tested. Ingredient scores are
transparent candidate-selection aids that rank sounding ingredients only; they
are not CM1 outcome predictions. Saved candidates live in the runtime cache and
may be handed into package metadata as provenance for why a sounding was tried.
The browser never parses remote directory listings, ZIP files, or station text
files. The current story identifiers, feature inputs, evidence-tier states,
evidence requirements, and caveat rules are defined in
[contracts/sounding-candidate-screening.md](contracts/sounding-candidate-screening.md).
The forward analyzer contract for testable hypotheses, explicit run
assumptions, predicted CM1-observable signatures, and predicted-vs-actual
comparison is defined in
[contracts/analyzer-hypothesis-output-signature.md](contracts/analyzer-hypothesis-output-signature.md).
The bridge from those hypotheses to CM1 run recipes is defined in
[contracts/run-recipe-and-story-mapping.md](contracts/run-recipe-and-story-mapping.md):
it maps current story IDs to observed surface-forced, differential
surface-forced, Deep-Tower Benchmark, blocked, or future recipes and names the
assumptions and output fields required before Results can compare predicted
signatures. The legacy `triggered_deep_potential` identifier is only a
compatibility alias for the current Deep-Tower Benchmark recipe.
Real-sounding story families, including severe/deep-convection, boundary-layer,
low-cloud, and winter/cold-season candidates, are defined in
[research/expanded-sounding-candidate-taxonomy.md](research/expanded-sounding-candidate-taxonomy.md).
Those labels must remain disabled, caveated, or absent from product UI until
backend scoring, evidence, caveats, and package-readiness states support them.
Severe/deep-convection candidates may be presented as pre-run atmospheric
hypotheses for the Deep-Tower Benchmark, not as forecasts or guaranteed storm
outcomes. Product copy should make the selected run assumptions visible:
CM1 `iinit = 3` warm-bubble initiation is an idealized trigger, uniform
lower-boundary forcing is a separate surface-forced recipe, and the differential
surface patch is a separate lower-boundary initiation experiment.
The backend may compute richer sounding diagnostics such as profile quality,
moisture/LCL proxies, lapse-rate and cap proxies, wind shear, dry-layer
signals, and freezing-level context to support future screening. These are
pre-run evidence and context only. Parcel, storm-relative, wet-bulb, and
winter-phase diagnostics must remain explicitly unavailable until their methods
are implemented and tested.

In Build, `Observed Soundings` is the product-facing entry point for observed
atmosphere work. It should offer one source path at a time: cached local
recommendations, saved candidates, or manual IGRA station text upload. The
cached-recommendation path should lead with product-level search controls such
as source region, search intent, station set, history scope, and returned
candidate limit, with secondary backend filters kept in advanced refinements.
The workbench can refresh the IGRA catalog, cache selected station files,
analyze the selected station/history set into station-diverse recommendations,
show the exact analyzed set and filter trace, show why each candidate is
interesting, expose story, story-family, evidence-tier, readiness,
station-search, and sort controls as advanced refinements, show package-ready
and blocked candidates with evidence and caveats, and save candidates with
freeform tags and notes for later review. History-scope labels must describe
the actual set being analyzed. The default recommendation pass analyzes all
cached history for all cached stations. `Latest N per station` is an explicit
user selection, and the returned-candidate limit is applied only after the
selected soundings have been analyzed. A deep-convection search intent scopes
recommendations to deep-convection ingredient stories; it must not silently
mean "supported-only" evidence or primary-story-only membership.
Manual upload should stay hidden while cached recommendations or saved
candidates are the active source path.

Saved candidates are a source path and shortlist, not an always-visible side
panel. Selecting the saved source should load saved candidates without requiring
a catalog refresh, cache action, or new analysis run. All candidate language
must remain pre-run and provisional: a candidate is an observed atmosphere worth
trying, not a prediction that clouds, rain, or suppression will occur. When a
candidate is selected for run setup, Build should use the same recipe and run
configuration flow used for uploads. When that configured sounding is added to
the run plan, its screening story, score, evidence, feature summary, saved
tags/notes, selected numeric surface-forcing values, and caveats should be
copied into package metadata as provenance.

When an uploaded, cached, or saved observed sounding is selected, Build should
show one shared selected-sounding setup flow above the run plan. The source path
should determine where the selected atmosphere came from, not create a separate
configuration workflow. The run plan should sit below the source/setup flow and
support multiple candidate atmospheres, duplicate variants, per-item forcing and
run-configuration edits, local or LAN queue target selection, remove/clear
actions, and a batch action to create packages and queue selected runs. Per-item
packaging or queue failures should remain visible instead of clearing the failed
item from the plan.

Observed-sounding experiments use the observed temperature, moisture, and
complete wind profile through CM1 `isnd = 7` and request the full
Results/Explore output field set. Severe/deep-convection candidates remain
first-class atmospheric hypotheses and default to the Deep-Tower Benchmark:
surface fluxes disabled, stock CM1 `iinit = 3` three-warm-bubble initiation,
storm-scale domain, and explicit caveats that the trigger is idealized rather
than an observed boundary. Observed surface-forced runs still apply selected
lower-boundary heat/moisture forcing. Differential surface heating/moisture
forcing is a current v0 patch recipe for localized initiation or boundary-style
experiments; it is not a real front, dryline, land-surface, GIS, or radiation
model. Its initial v0 geometry is a centered circular patch. It is local-only;
the external CM1 source customization path has
runtime-local compile and emitted hfx/qfx forcing-footprint smoke evidence, but
matched dynamic-response validation remains the #307 closure gate. Results carry
per-run localized diagnostic availability for emitted footprint regions
(core/taper/background), convergence when physical u/v coordinates are
available, and instantaneous patch-to-updraft/cloud/rain/reflectivity distance
metrics with field-quality state. These are not causal response verdicts until
matched uniform-versus-patch comparisons define persistence and directional
criteria. Short science configurations must still run long
enough to be meteorologically useful. Build should show expected cost, runtime,
and output volume, and note when a configuration is better suited to larger
compute instead of making machine choice the primary product axis.

The run monitor should be compact by default. It should summarize active,
queued, and completed runtime work while keeping detailed package, queue, LAN,
ingest, and cleanup actions reachable on demand. The package/run status rail is
supporting context for the run plan, not the primary place to continue after
choosing a sounding.

Explore should be a focused visualization plus explanation screen for one
selected result. Its core interaction is `What happened here?`: select a cloud,
updraft, clear-air thermal, or no-cloud region and receive a CM1-backed
explanation of what happened there and why. Thermal Fate process evidence
remains available in secondary or technical layers, but the primary view should
lead with the experiment story, outcome, visualization, selected-region
explanation, and next action. The browser receives only backend-prepared
slices, point clouds, result-card process fields, and bounded summaries; it
does not parse raw NetCDF or invent process claims.

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
-> choose or adjust run configuration
-> validate setup
-> generate CM1 run package
-> launch local CM1
-> monitor logs/status
-> ingest NetCDF output
-> create result card / experiment notebook entry
-> replay cloud evolution
-> open Explore
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

### Workflow 1 — Configure A CM1 Experiment

1. Open app.
2. Choose scenario category.
3. Select a starting scenario or observed-sounding run direction.
4. See expected behavior, controls, run cost, and output fields.
5. Adjust numeric surface heat/moisture fluxes, duration, horizontal cells,
   domain, and output cadence before package review.

The Scenario Builder flow is intentionally bounded: it loads
validated scenario templates from the local backend, defaults to Baseline
Shallow Cumulus, displays the scenario description and physical question,
exposes only product-facing curated controls, lets the user adjust explicit
run-configuration choices, and requests a dry-run package for review.

The primary current-run path should stay in one vertical flow: choose the
atmosphere, choose or confirm the hypothesis, configure the CM1 run, review
pre-run validation, then create the package and queue that package. The
right-side launchpad is a status rail for generated packages, queue state,
ingest, worker status, and cleanup; it should not force the user to hunt there
for the next action after choosing a sounding or run configuration.

Build should not assume the user is working one perfectly linear package at a
time. Local experiments can be packaged, running, failed, completed-but-not-
ingested, ingested, carrying legacy saved/protected metadata, or ready for
cleanup at the same time. The Build workspace should include a compact local
run launchpad for active and incomplete package/run work only: show generated
package details, launch eligible stored packages, refresh running/failed/
completed status, troubleshoot failed or no-output runs, and ingest completed
output. Fully ingested results belong in Results.

When a local backend restart leaves a completed CM1 run's manifest marked
running, Build refresh may reconcile the state only if stdout contains
normal CM1 termination evidence and output artifacts are present. The UI should
then offer ingest rather than leaving the run stranded as running.

The UI must continue to avoid raw CM1 namelist fields in the primary flow. Raw generated files can be listed in dry-run review because they are outputs of the package step, not user-facing controls.

### Workflow 2 — Preview Setup

1. Adjust controls.
2. Placeholder preview panel reserves space for future guidance.
3. Future preview diagnostics update quickly when implemented.
4. User understands that preview is not CM1.

Current behavior is a placeholder only. It must explicitly say preview is not implemented, not CM1 output, not a completed result, and not a visualization interpretation.

### Workflow 2.5 — Package And Review Local Runs

1. Request a dry-run package from the Scenario Builder.
2. Backend validates the scenario template and selected controls.
3. Backend writes package files under the configured runtime home, not the repo.
4. UI displays run ID, package path, manifest path, scenario, validation/product state, generated files, physical question, selected run configuration, expected diagnostics, and cost/size notes.
5. UI states that CM1 was not launched and the package is not a completed CM1 result.
6. The launchpad also surfaces other local package/run directories from the
   runtime inventory when they still need Build action: packaged-only, running,
   completed with output and not yet ingested, completed without usable output,
   failed/canceled, or malformed/missing manifest. Fully ingested results are
   reviewed and managed in Results.

### Workflow 3 — Launch CM1 Run

1. Click `Queue local CM1 run` from the end of the current setup flow, or from
   an eligible stored-package card in the launchpad.
2. Backend launches local CM1 from the generated run package only after preflight passes.
3. UI shows the running state, command/log paths, stdout/stderr tail when available, and one-local-run-at-a-time policy.
4. If local CM1 settings are missing, the UI shows the backend failure reason and no run is implied.
5. The UI continues to distinguish the package, running CM1 process, completed CM1 result, and later ingest/result states.

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

The Build workspace provides the first guided local launchpad without curl
commands: create package, launch eligible local CM1 packages, refresh status/log
summaries, see output-artifact counts, inspect elapsed wall-clock and model-time
progress when CM1 logs expose it, ingest completed NetCDF output, and open
created Result Cards in Results or Explore. Percent complete and ETA should only
appear when configured model time and latest model time are both known. It is a
pipeline view over local runtime state, not a single active wizard. This is
local-first orchestration only; CI still uses fake fixtures and never runs CM1.

Local package launch should go through a serial queue. Users can queue multiple
ready packages, but Cloud Chamber must run only one local CM1 process at a time.
When a queued run completes with usable NetCDF output, Build should auto-ingest
the result and show the generated Result ID. Failed, no-output, or ingest-failed
runs stay visible with manual fallback actions. Auto-ingest should finalize
queue state, not silently delete result-backed local run data.

### Workflow 4.5 — Manage Runtime Cleanup

Build exposes runtime-home inventory for active, incomplete, and non-ingested
package/run work. It shows lifecycle-aware identities for run directories that
still need launch, status review, troubleshooting, ingest, or cleanup. Fully
ingested results are omitted from Build cleanup and managed from Results.

Build should describe each non-ingested local run directory as part of the
experiment lifecycle: ready-to-run package, running/queued CM1 process,
completed with usable output, completed with no usable output, failed/canceled,
ready to ingest, or missing/malformed manifest that needs cleanup review. It
should avoid duplicate or contradictory badges.

Build offers non-destructive state transitions where they belong: launch
packaged runs, refresh status, and ingest completed output when a
completed-with-output run has a manifest but no associated result. Cleanup for
non-ingested run directories remains behind preview and confirmation.

Results owns destructive cleanup for ingested results. The selected notebook
entry offers a secondary/danger action to preview deletion by result ID. The
preview states that deleting removes the ingested result, notebook edits,
diagnostics, derived products, CM1 output, logs, and local run files stored
under the run directory, and that the result will disappear from Results,
Explore, and local inventory after confirmation.

Deletion is always explicit. The UI first requests a dry-run delete preview for
one selected run/result, then requires a separate confirm action before
deleting. Running runs cannot be deleted. Legacy saved/protected metadata does
not make a non-running run/result undeletable. The warning threshold never
auto-deletes anything. The relationship should be clear: Build moves local runs
forward and cleans up non-ingested runs; Results reviews, edits, and deletes
ingested experiment notebook entries plus their backing local data.

### Workflow 5 — Open Result

1. Select completed run.
2. App ingests or loads processed data.
3. App shows diagnostics and a unified Explore workspace.
4. User can name, tag, and annotate the result.
5. User can reopen, inspect, and explain the saved result later.

### Workflow 6 — Unified Explore

Explore is now the single selected-result inspection and explanation workspace.
It should keep the current product loop focused on:

```text
selected-result trust
-> 3-D scalar-field context
-> shared time / field / slice controls
-> saved-output timelapse playback without interpolation
-> visible native-grid slice plane
-> matching 2-D slice inspector
-> click-cell "What happened here?" explanation
-> technical details on demand
```

The broad original visualizer goal in #31 has been superseded by staged
implementation issues and the UX reset. Explore should build from saved/ingested
results and backend visualization-ready data, not from raw NetCDF parsing in the
browser. Every stage must preserve provenance labels and make clear that rendered
output is an interpretation of CM1-derived data.

Renderer upgrades such as isosurfaces, volumetric opacity, cinematic lighting,
appearance presets, fly-through, and export are not near-term payoff work. They
remain deferred to the renderer-upgrade decision (#112) and later visual polish
planning (#80) after the guided experiment notebook and `What happened here?`
loop are stable.

### Workflow 6.5 — What Happened Here?

`What happened here?` is the core Explore interaction, not a buried technical
diagnostics panel:

```text
open a completed or ingested result
-> see the main 2-D or 3-D visualization
-> click a cloud, updraft, clear-air thermal, or no-cloud region
-> the app marks the selected spot or region
-> the app opens an explanation panel
-> the panel answers what happened there, what evidence supports it, and what is uncertain
```

This workflow must use backend diagnostics over CM1-derived fields. The browser
must not parse raw NetCDF or invent scientific explanations.

The first implementation can start with 2-D selection if 3-D selection is too
hard. Users can click a backend-prepared heatmap cell to inspect the nearest
native-grid column, select a bounded center point or small box, clear the
selection, and review the backend-returned explanation, confidence, caveats,
local `qc`/`w`/rain summaries, selected-region bounds, domain comparison, and
provenance. The UI is presentation-only for scientific interpretation: labels
and summaries come from the selected-region diagnostics API.

The explanation should use simple primary language such as:

```text
What happened here?
Cloud formed here
Thermal without cloud
Cloud stayed shallow
Growth was limited
Evidence
Still uncertain
Technical details
```

Thermal Fate labels, native variables, source fields, confidence details, and
provenance remain available behind details/disclosure. They should not be the
first-read interaction model.

Process evidence controls in Explore should be result-aware. The primary
`Explanation focus` control should show only supported modes and caveated modes
that are still useful for the selected result. For example, direct `qc` cloud
water and `w` updraft evidence can be normal focus choices when those fields are
available, moisture limitation can be a candidate focus for Dry Failed-style
results, and cap/inversion can be a candidate focus for stronger-cap results.
Modes that need missing fields or future backend diagnostics, such as buoyancy,
deep breakthrough, or precipitation feedback without cold-pool/outflow evidence,
belong under a collapsed `Not available for this result` disclosure with plain
reasons. The browser may gate presentation from existing result metadata,
support/confidence labels, caveats, and available visualization fields, but it
must not invent unsupported scientific classifications.

### Workflow 7 — Duplicate / Tweak / Rerun

1. Duplicate previous setup.
2. Change one or more controls.
3. Preview likely difference.
4. Launch a new CM1 run.
5. Inspect result differences later when a real comparison workflow exists.

This workflow is useful, but it is not the core first-MVP result behavior. Replay, inspect, save, name, and tag completed CM1 results first; duplicate/tweak/rerun can mature after the Result Card / Experiment Notebook model is reliable.

## Thermal Fate Diagnostic Scope

Product diagnostics should be framed at three levels:

- **Global run diagnostics**: cloud formed, first cloud time, cloud base/top,
  `qc`, `w`, rain, cloud fraction, and later process summaries for the whole
  completed CM1 result.
- **Local selected-region diagnostics**: the `What happened here?` point,
  column, or box story, including local `qc`, `w`, rain, saturation/cap evidence
  where supported, and comparison to domain behavior.
- **Comparison diagnostics**: what changed between Baseline and a variant, such
  as Dry Failed, Capped / Suppressed, humidity-ladder, or future
  surface-heating/deep-breakthrough cases.

Deep-convection breakthrough and precipitation-feedback/cold-pool diagnostics
are first-class science directions, but they should remain unavailable,
candidate, or insufficient-evidence states until the required CM1 fields and
derived diagnostics exist.

The first backend process-diagnostics implementation supports a conservative
global result summary. It can label moisture-limited thermal-without-cloud
results when `w` is meaningful and `qc` stays below threshold, mark
Capped / Suppressed as a candidate when the stronger-cap scenario/control path
is selected, and expose growing/fair-weather cumulus candidate labels from
available cloud-top and cloud-water diagnostics. It does not compute buoyancy,
entrainment, CAPE/CIN/LFC/EL, cold pools, or selected-region explanations yet.

## Run Configuration Model

Build should present starting configuration choices for a CM1-facing run, not
rigid experiment families or mandatory run-size schema slots. The
user should be able to start from a trusted default, inspect what it means,
adjust guarded settings, and receive a pre-run validation report before package
generation or launch.

Quick means quick to execute for the selected configuration; it must not mean
meteorologically too short to produce useful evolution. Smoke checks prove that
package generation, CM1 launch, output production, ingest, and basic
visualization wiring are healthy. They are not evidence that a specific observed
sounding validates a science hypothesis. Science runs should use enough model
time, domain, and output cadence for the atmospheric question being asked.

Grid/detail and output cadence are the main user-facing cost levers. Raw
numerical timestep is not a normal v1 user control, but campaign and numerical
validation matrices may set an explicit advanced timestep target when that value
is part of the evidence being tested. Cloud Chamber should warn or caveat
unvalidated control combinations when they can be safely generated, block
configurations that cannot be rendered or launched honestly, and avoid silently
replacing bad observed-sounding input with reference defaults.

Generated packages include a backend-owned pre-run validation report. The
report records the selected candidate/hypothesis, selected run recipe and
assumption set, hypothesis/recipe alignment, observed-input validation,
run-shape estimates, forcing support, required/enabled output fields, runtime
file staging status, blocking errors, and caveats. Blocked reports stop package
creation before a run directory is written; caveated reports may be packaged but
must remain visibly caveated before launch and after ingest.

Forward run configuration should include:

```yaml
run_configuration:
  preset_id:
    optional starting point, not a required product family
  duration:
    model_time_seconds
    purpose: smoke_check | quick_science | standard_science | extended_science
  grid_detail:
    label
    nx
    ny
    nz
    dx_m
    dy_m
    vertical_grid_summary
  domain:
    width_m
    depth_m
    model_top_m
  output_cadence:
    model_seconds_between_outputs
    expected_saved_frames
  output_field_density:
    minimal | standard | expanded
    requested_fields
  forcing:
    surface_sensible_heat_flux
    surface_latent_heat_flux
    radiation_mode
    place_time_context
  advanced_cm1_values:
    timestep_target_seconds
    namelist_summary
    input_sounding_summary
    runtime_files_needed
  pre_run_validation_report:
    status
    blocking_errors
    caveats
    estimated_runtime
    estimated_output_volume
```

Starting choices may populate these fields, but former run-size tier names are
not active product schema. Generated packages, manifests, reports, and result
cards should use the resolved `run_configuration` object as the run-shape source
of truth.

## Current Run-Configuration Defaults

Current defaults are product choices, not compatibility holdovers:

- Baseline lower-atmosphere scenarios default to `short_6h`, `cells_64`,
  `local_6km`, `standard_15min`, and full output fields. This keeps the
  first run cheap enough to iterate while still giving six hours of model
  evolution and enough fields for Results/Explore diagnostics.
- Uploaded observed-sounding surface-forced runs default to the same duration,
  cadence, and full output field set, but use `cells_128` and `wide_12km` so observed
  winds do not make the package misleadingly small by default.
- `smoke_1h` is an explicit smoke-check mode for package health, CM1 startup,
  ingest, and basic visualization wiring. It is not evidence for normal
  atmospheric evolution.

The dry-run report must show runtime, output cadence, expected saved frames,
grid dimensions, spacing, model top, grid-cell multiplier, output-frame
multiplier, compute multiplier, output-volume multiplier, and a clear warning
when wall-clock or storage estimates need local/manual validation.

Runtime estimates are approximate until locally validated for a specific CM1 build, scenario, and machine. The first local hardware target is a 2024 MacBook Air with 8GB RAM, so the MVP should assume one local CM1 run at a time and conservative output handling.

Run-configuration estimate metadata should be carried through scenario
templates, generated run packages, dry-run reports, run manifests, result
metadata, and result cards. If estimate data is not locally validated yet, the
UI/report should say `unknown until validated` instead of inventing precision.

## Run Configuration Schema

Backend scenario templates are validated by the `ScenarioTemplate` contract.
Scenario templates define product controls and science story metadata; run shape
is carried by the resolved `run_configuration` object:

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
run_configuration:
  duration: model_time_seconds
  grid_detail: nx
    ny
    nz
    dx_m
    dy_m
    vertical_grid_summary
  domain: width_m
    depth_m
    model_top_m
  output_cadence: model_seconds_between_outputs
    expected_saved_frames
  output_field_density: level
    requested_fields
  forcing: surface_sensible_heat_flux
    surface_latent_heat_flux
    radiation_mode
    place_time_context
  advanced_cm1_values: timestep_target_seconds
    namelist_summary
    input_sounding_summary
    runtime_files_needed
pre_run_validation_report:
  status:
  blocking_errors:
  caveats:
  estimated_runtime:
  estimated_output_volume:
outputs_expected: fields
  diagnostics
visualization_defaults: camera
  fields
  color/opacity
physical_question:
learning_goals:
variation_policy:
  recommended_story_thread:
  recommended_comparison_pattern:
validation_status: unrun | generated | accepted | needs_calibration
notes:
```

Validation rules should reject templates that:

- omit product-facing controls
- omit a valid run-configuration default for package generation
- define a choice control whose default is not one of its options
- define a number control without a valid range
- reference unknown controls from validation policy
- include undeclared fields

The schema is intentionally product-first. Raw CM1/developer controls can exist
as advanced metadata, but product-facing controls and the pre-run validation
report remain the primary path.

Thermal Fate diagnostic directions should include:

1. Moisture-limited thermal fate: Baseline, Dry Failed, and humidity ladder.
2. Surface-heating-driven thermal fate: weaker/baseline/stronger heating,
   focused warm patch, patchy heating, and gradients.
3. Cap-limited thermal fate: Capped / Suppressed Cumulus.
4. Dry-air-aloft / dilution-limited thermal fate.
5. Deep-convection breakthrough: growing, towering, and cumulonimbus candidates.
6. Precipitation feedback / cold-pool interaction.
7. Low stratus / low-cloud layer where appropriate.

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

The current Baseline Shallow Cumulus recovery contract renders CM1-facing `namelist.input` from CM1's local `les_ShallowCu` reference path. The external-sounding reproduction keeps `testcase = 3`, the reference grid, runtime, domain top, Rayleigh damping, surface/ocean/flux settings, surface stress path, and wind profile as much as possible, but switches the thermodynamic source from CM1's built-in BOMEX analytic sounding (`isnd = 19`) to CM1's external `input_sounding` route (`isnd = 17`). The generated `input_sounding` is a numeric CM1-readable BOMEX/Siebesma profile that extends above the 18 km model top.

Observed IGRA sounding import uses the same external `input_sounding` route.
The generated thermodynamic/moisture profile comes from the selected observed
sounding after unit conversion and vertical-datum handling. Observed wind
direction/speed is converted to CM1 `u`/`v`, written into `input_sounding`, and
used by CM1 through `isnd = 7`. The generated
package records the selected station, valid time, uploaded filename,
provider/format, model-bottom elevation, conversion choices, wind-handling
method, validation status, and caveats in the run manifest, case manifest, and
dry-run report. It must not imply location/date/radiation behavior beyond the
observed-profile provenance; radiation remains whatever the scenario package
currently configures.

The first full-sequence NetCDF ingest of `dry-run-157b09a178e1` found 25 model-output files and 25 time steps, but no usable cloud or vertical velocity: `max_qc_kg_kg = 0.0`, `max_w_m_s = 0.0`, and multiple NaN/Infinity caveats in surface and thermodynamic fields. The generated quick-look package therefore now uses a fixed small ocean roughness length (`set_znt = 1`, `cnst_znt = 0.0002`) instead of the reference dynamic roughness / fixed friction-velocity path that produced invalid local output.

A follow-up local/manual validation run, `dry-run-calibration-20260522132903`, confirmed the fixed roughness value is written and CM1 completes with NetCDF output, but it still produces no cloud, no vertical motion, and NaN/Infinity caveats in target fields. The fixed-roughness derivative is therefore not the recovery baseline. Cloud Chamber should recover from `les_ShallowCu` first, then introduce any quick-look scaling one change at a time.

The first `les_ShallowCu` reference-derived Cloud Chamber run, `dry-run-les-shallowcu-20260522140642`, completed with `exit_code = 0`, produced NetCDF output, and ingested 7 model-output time steps from 0 to 21600 seconds. First-pass diagnostics reported `cloud formed; rain detected`, first cloud time at 3600 seconds, `max_qc_kg_kg = 0.002192789688706398`, `max_w_m_s = 6.962291717529297`, and `min_w_m_s = -3.7671568393707275`. This validates the recovery direction: use the reference-derived case as the Baseline Shallow Cumulus Golden Path source, then derive shorter quick-look variants later.

The first quick-look Baseline Shallow Cumulus variant is derived from that validated reference package by changing only runtime and output cadence: `timax = 10800.0` and `tapfrq = 900.0`. It intentionally preserves the reference domain/grid, vertical spacing, domain top, surface stress/roughness path, moisture/sounding, surface fluxes, turbulence/SGS settings, damping settings, boundary conditions, NetCDF output, and reference `LANDUSE.TBL` staging behavior.

The first quick-look validation run, `dry-run-quicklook-les-shallowcu-20260522151536`, completed with `exit_code = 0`, produced NetCDF output, and ingested 13 model-output time steps from 0 to 10800 seconds. Package size was 206 MB. First-pass diagnostics reported `cloud formed; rain detected`, first cloud time at 1800 seconds, `max_qc_kg_kg = 0.002192789688706398`, `max_w_m_s = 6.866957187652588`, and `min_w_m_s = -4.21529483795166`. This confirms the shorter runtime/cadence-only quick-look variant still produces cloud and vertical motion while preserving the reference-derived settings.

The external-sounding Baseline Shallow Cumulus reproduction run,
`dry-run-external-sounding-baseline-20260522185000`, completed with
`exit_code = 0`, produced NetCDF output, and ingested 13 model-output time
steps from 0 to 10800 seconds. First-pass diagnostics reported `cloud formed;
rain detected`, first cloud time at 1800 seconds, `max_qc_kg_kg =
0.001976807601749897`, `max_w_m_s = 6.270190238952637`, and `min_w_m_s =
-4.416495323181152`. This accepts the external `input_sounding` path as the
baseline reproduction path for the next one-factor moisture experiment.

The Baseline Shallow Cumulus low-level humidity ladder now uses that accepted
external-sounding path. `drier`, `baseline`, and `more humid` preserve the same
grid/domain, selected run configuration, surface/ocean/flux settings,
stress/roughness path, damping, turbulence/SGS settings, boundary conditions,
NetCDF output, and runtime-file staging. The only intended generated-input difference is the
low-level moisture profile in `input_sounding`. These variants are disciplined
one-control-at-a-time experiments, not arbitrary parameter sweeps.

Initial quick-look validation supports the ladder direction. The drier run
`dry-run-004bd57bb8cc` completed, produced 13 model-output time steps, ingested
successfully, and reported `no cloud formed; no rain detected` with meaningful
vertical motion (`max_w_m_s = 2.0368008613586426`, `min_w_m_s =
-1.26932954788208`). The more-humid run `dry-run-4e64317c62ec` completed,
produced 13 model-output time steps, ingested successfully, and reported `cloud
formed; rain detected`, first cloud at 900 seconds, `max_qc_kg_kg =
0.00285167433321476`, `max_w_m_s = 10.37020206451416`, and `min_w_m_s =
-5.2025837898254395`.

### Dry Failed Cumulus Planning

Dry Failed Cumulus is the next planned lower-atmosphere contrast case after
Baseline Shallow Cumulus. It should answer:

```text
How does insufficient low-level moisture prevent shallow cumulus formation even when boundary-layer thermals and vertical motion are present?
```

This is a moisture-limited failed-cumulus case. It should not mean a dead
simulation, a too-stable/capped atmosphere, weak surface forcing, numerical
failure, or "no cloud" by itself. The target is thermals without meaningful
cloud.

Teaching contrast:

```text
Baseline Shallow Cumulus:
  thermals rise
  cloud water forms
  rain may appear
  qc and w are both visually/scientifically interesting

Dry Failed Cumulus:
  thermals still rise
  parcels do not reach enough saturation
  qc stays below cloud threshold or appears only as trace amounts
  rain does not appear
  w remains scientifically meaningful
```

The MVP product-facing variation should change one physical factor:

```text
low-level humidity = drier
```

Other curated controls should stay at the validated baseline for the first
implementation:

```text
surface heating = baseline
cap strength = baseline
dry air aloft = baseline
mixing / entrainment = baseline
```

The diagnostic target is:

```text
CM1 completes cleanly
NetCDF output is produced
full output sequence ingests
cloud_formed = false
rain_present = false
max_qc_kg_kg remains below the 1e-6 kg/kg cloud threshold,
  or fewer than 10 grid cells exceed threshold
max_w_m_s is meaningfully nonzero
min_w_m_s is finite and preferably negative/nonzero
no severe NaN/Infinity caveats in qc/w/qv/thermodynamic target fields
main limiting factor = insufficient low-level moisture / saturation deficit
```

Inspection should show `w` without meaningful `qc`: 2-D `qc` slices should be
mostly empty/trace while `w` slices still show thermal/updraft structure. The
3-D cloud-water point cloud should be mostly absent, while slice planes remain
useful for explaining the failed-cloud contrast.

Dry Failed starts from the validated reference-derived Baseline Shallow Cumulus
setup, not the old compact quick-look derivative that produced no cloud, no
vertical motion, and NaN/Infinity caveats. The implementation path is:

1. #102 validates an external-sounding Baseline Shallow Cumulus reproduction while
   preserving the validated grid/domain/runtime/surface/damping/boundary
   settings and changing only the thermodynamic sounding source.
2. #103 implements the moisture-limited Dry Failed variant by drying the validated
   external-sounding baseline and preserving vertical motion.

The first Dry Failed Cumulus validation run,
`dry-run-dry-failed-cumulus-20260522192000`, completed with `exit_code = 0`,
produced NetCDF output, and ingested 13 model-output time steps from 0 to
10800 seconds. First-pass diagnostics reported `no cloud formed; no rain
detected`, `max_qc_kg_kg = 0.0`, `max_w_m_s = 1.949130654335022`, and
`min_w_m_s = -1.0865488052368164`. This is the first accepted
moisture-limited contrast case: thermals and vertical motion remain, but cloud
water and rain stay absent by the MVP diagnostics.

### Capped / Suppressed Cumulus Planning

Capped / Suppressed Cumulus is the next planned lower-atmosphere contrast after
Dry Failed Cumulus and the low-level humidity ladder. It should tell a distinct
stability/inhibition story:

```text
How does a stronger cap suppress or limit shallow-cumulus growth even when moisture and boundary-layer thermals are available?
```

Dry Failed Cumulus is the moisture-limited no-cloud contrast. Capped /
Suppressed Cumulus should not target a total no-cloud case for the first
version. The first target is:

```text
same cloud setup, but a stronger lid
```

Moisture remains available and thermals still rise. Shallow or weak cloud may
still form, but the stronger cap should limit cloud depth, reduce cloud water
or cloud fraction, and suppress or reduce rain relative to the accepted Baseline
Shallow Cumulus quick-look.

Teaching contrast:

```text
Baseline Shallow Cumulus:
  thermals rise
  cloud water forms
  cloud grows deeper
  rain may appear
  qc and w are both visually/scientifically interesting

Dry Failed Cumulus:
  thermals rise
  lower atmosphere is too dry
  cloud water stays absent or below threshold
  rain does not appear
  w remains scientifically meaningful

Capped / Suppressed Cumulus:
  thermals rise
  moisture is available
  cloud may still form
  stronger cap limits vertical growth
  cloud tops are lower
  max qc / cloud fraction are reduced
  rain is suppressed or absent
```

First product-facing controls:

```text
cap_strength:
  baseline
  stronger

cap_height:
  baseline initially
  lower later

low_level_humidity:
  baseline for first implementation

surface_heating:
  baseline for first implementation
```

The first implementation, #140, uses `cap_strength = stronger`, keeps cap
height at the accepted baseline, keeps low-level humidity and surface heating
at baseline, and changes only the potential-temperature / stability structure
near the capping layer in the generated external `input_sounding`.

Expected MVP target:

```text
CM1 completes cleanly
NetCDF output exists
full output sequence ingests
max w is meaningfully nonzero
min w is finite
cloud_formed may be true
first_cloud_time may be delayed
cloud_top lower than baseline
max_qc lower than baseline
cloud_fraction lower than baseline
rain_present false or reduced
main_limiting_factor = cap/stability
```

Exact morphology is not pass/fail. The key outcome is healthy thermals plus
available moisture plus limited cloud depth because of the stronger cap. If the
run becomes indistinguishable from Dry Failed Cumulus, or if diagnostics cannot
separate cap limitation from moisture limitation, the scenario should be marked
`needs_calibration` rather than overclaimed.

The first stronger-cap validation run,
`dry-run-capped-suppressed-20260526015634`, is accepted with notes as a
cap-limited candidate. It completed local CM1 with `exit_code = 0`, produced
NetCDF output, ingested 13 model-output time steps from 0 to 10800 seconds, and
produced `cloud formed; rain detected`. Compared with the accepted
external-sounding Baseline Shallow Cumulus quick-look, it reduced cloud top
from about 2.14 km to about 1.34 km, reduced `max_qc_kg_kg` from
0.001976807601749897 to 0.0013941252836957574, reduced max cloud fraction from
about 0.01273 to about 0.00847, reduced max/min vertical velocity from about
6.27 / -4.42 m/s to about 3.52 / -1.67 m/s, and reduced max rain water from
about `1.3015507647651248e-05` to `4.473397439141991e-06`. Rain still occurred
and first cloud time stayed at 1800 seconds, so the result should not be
overstated as fully rain-suppressed or definitively process-diagnosed yet.
Current language should remain candidate/accepted-with-notes until process
diagnostics can directly explain cap limitation.

Standard cloud-scale assumptions:

```text
64 x 64 x 100 grid
100 m horizontal spacing
stretched vertical grid: 40 m low-level spacing to 600 m aloft
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

Deep / overnight differences:

```text
192 x 192 x 75 grid
about 33.333 m horizontal spacing
40 m nominal vertical spacing
18000 m domain top
21600 s runtime
300 s output cadence
3.0 s model timestep (unchanged from Standard)
physical domain and reference-derived science settings preserved
```

If a scenario needs different size, spacing, runtime, cadence, or runtime files, the deviation must be explicit and documented.

Dry-run package generation creates these files for review without launching CM1:

- `run_manifest.json`
- `case_manifest.json`
- `namelist.input`
- `input_sounding`
- `dry_run_report.json`
- `runtime_file_checklist.json`

The dry-run report must state that it is not a completed CM1 result, record
that CM1 was not launched, include the selected run configuration, include
physical question and controls, include expected diagnostics and
visualization defaults, show expected runtime/cost/output-volume information
when available, and use `unknown until validated` for unvalidated estimates.

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

If `qr` is absent, the user-facing result must say that rain-water-aloft diagnostics are unavailable, not that rain water aloft was absent. The metadata records that the `qr` field was absent. Missing `qr` does not fail the diagnostics, but it cannot support a clean rain-water outcome.

NaN and infinity values are ignored for finite min/max and fraction summaries. Field-specific caveats record non-finite values or entirely non-finite target fields. Target fields also carry field-quality state: `trusted`, `caveated`, `untrusted`, or `unavailable`. Entirely non-finite `qc`, `w`, `qr`, surface `rain`, or `dbz` fields are untrusted and must not be summarized as clean cloud, updraft, rain-water, surface-rain, or reflectivity evidence. CM1 runtime floating-point exception flags are preserved as caveats and evaluated against the target diagnostic fields rather than treated as automatic run failure.

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
  run_configuration:
    duration:
    grid_detail:
    domain:
    output_cadence:
    output_field_density:
    forcing:
    advanced_cm1_values:
      timestep_target_seconds:
    pre_run_validation_report:
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

Validation rules should reject packaged dry-run manifests that include NetCDF output paths, completed/ingested manifests that still claim to be dry-run packages, unknown lifecycle states, and inconsistent legacy saved metadata.

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
Editable result/notebook entry
```

A preview or dry-run package is not a completed CM1 result. A visualization is an interpretation of CM1 output, not a new physical source of truth.

Product copy and state names should prefer nouns that reveal provenance:

- `Preview estimate`
- `CM1 configuration package`
- `CM1 run`
- `Completed CM1 result`
- `Ingested result metadata`
- `Visualizer interpretation`
- `Editable experiment notebook entry`

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
run configuration
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
run configuration
physical question
diagnostics summary
first cloud time
max qc
max/min w
rain yes/no
caveats
output file summary
notes/tags/name
```

Editable notebook state lives beside the local run as `result_card.json`; it
stores `name`, `tags`, and `notes` without modifying or copying CM1 output.
Older cards may still include `saved` and `protected` fields for compatibility,
but the current product does not expose a separate save/protect mode.

The Results Library UI is an experiment notebook, not an admin table. It lists
result cards from the backend as scan-friendly experiment entries, lets the user
select one result, and shows a detail/notebook card with scenario, run
configuration, cloud/rain outcome, diagnostics summary, first
cloud time, max `qc`, max/min `w`, caveats, output summary, and editable name/tags/notes. Notebook
edits use `Save changes`; ingested results already appear in Results.
The notebook also exposes backend-derived science summary fields such as
first-cloud time, max `qc`, max updraft, rain onset, latest output time, and
interesting-time evidence state so the user can search, filter, and sort the
experiment list by meaningful scientific evidence rather than raw file order.
Result Cards must also distinguish generated-reference runs from runs
created from an uploaded observed sounding, preserving station/time/source
metadata as provenance. Observed-sounding results should read as `Uploaded
Sounding` or the active observed run recipe in notebook names, scenario labels,
and scenario filtering while the underlying generated scenario ID remains
available in technical details as lineage.
Observed-sounding results should retain their run provenance after ingest: the
original observed station/time, generated scenario ID, numeric surface-forcing
values, expected outputs, caveats, and candidate-screening hypothesis remain
available as provenance.
Technical metadata such as raw lifecycle/product states, run IDs, provenance
labels, controls, and detailed caveats remain available under disclosure rather
than dominating the first read. The layout should be mobile-first: cards stack
naturally on narrow screens, and desktop can use a list/detail notebook split.

The library opens a 2-D field inspector from a result detail/notebook entry.
The inspector is a CM1-output inspection surface, not a visualizer or replay
system.

The MVP frontend is organized as a task-based workspace:

```text
Build
Results
Explore
```

`Build` creates and runs experiments. `Results` reviews, edits, and
manages experiment results. `Explore` inspects and visualizes one selected
result's CM1 fields. The app should open on `Results`, because the most useful
first click path is to choose the validated reference Baseline Shallow Cumulus
result and open it in Explore or 3-D. Results should prioritize completed, ingested, cloud-forming
reference baseline entries ahead of failed/no-cloud or historical
attempts. User-facing labels should say `Completed CM1 result`, `Ingested`,
`Needs review`, `Cloud formed`, `No cloud`, and `Rain detected` rather
than leading with raw lifecycle strings. Raw lifecycle/product/provenance labels
remain available under technical details.

The shared visual system should read as an atmospheric experiment notebook, not
a terminal dashboard or cockpit. The app chrome should use a soft neutral /
pale blue-gray background, light or very soft slate surfaces, cloud/sky-inspired
panels, blue / blue-gray primary accents, subtle amber warnings, and subtle red
destructive/error states. Green is reserved for success or healthy states only;
it is not the brand or primary navigation color. Visualization viewports may use
dark plotting backgrounds when they make CM1-derived fields easier to read, but
the surrounding app shell, navigation, cards, buttons, badges, loading/error
states, and technical-detail areas should stay calm, readable, and secondary to
the workspace content.

For completed cloud-forming results, minor runtime or coordinate caveats should
read as caveats, not failed-run warnings. A result can be a successful,
inspectable CM1 run while still carrying `Minor caveat` details such as
floating-point flags or vertical-coordinate unit notes. `Needs review` remains
appropriate for no-cloud, missing-diagnostics, failed, or otherwise incomplete
results.

Dry Failed Cumulus is an intentional no-cloud contrast case, not a failed run,
when it completes locally, ingests successfully, preserves meaningful vertical
motion, and keeps cloud water below threshold. Its primary badges should read
like an accepted moisture-limited outcome: `No cloud formed`, `No rain
detected`, and `Moisture-limited`, with caveats secondary.

`Results` is the Result Card / Experiment Notebook: a scan-friendly list of
experiment cards plus a selected notebook detail, with technical run metadata
kept secondary. It does not expose a Compare tab until Cloud Chamber has a real
user-driven comparison workflow. Ingested-result cleanup lives on the selected
notebook detail as a secondary/danger preview action, not as a separate Storage
workspace.

`Explore` is one desktop cloud-context and slice-inspection workflow for a
single selected result. The old `2-D Slices` / `3-D View` split was useful
scaffolding while capabilities were built separately, but the product workflow
is now a unified instrument: compact selected-result context, shared
field/time/slice controls, a 3-D scalar-field context, a visible native-grid
slice plane, the matching 2-D slice inspector, and a `What happened here?`
selected-point explanation panel. Selecting a result in Results should preserve
that context. If no selected result is available, Explore should tell the user
to select an ingested result from Results.

Shared time controls should operate on actual saved CM1 output times. Explore
may provide play/pause timelapse playback and a scrubber across those saved
time indices, but it must not interpolate between model outputs or imply a
continuous movie. Manual time changes and pausing playback update the 3-D
scalar context and 2-D slice inspector together, preserve the current camera,
field, slice orientation, and slice position, and clear selected-cell
explanation state because the old point evidence belongs to a different model
time. While playback is running, Explore should update the main 3-D scalar
layer for the visible saved output time, but it should not refetch or recompute
all synchronized field products every frame. The 2-D slice, selected-point
diagnostics, defaults, and evidence panels may remain on the last committed time
until playback is paused. At the end of the saved-output sequence, playback
should stop and reset to the first output time rather than looping indefinitely.
The selected-point panel should invite the user to pause before asking `What
happened here?`.

The first-read Explore screen should be an explanation workspace, not a
process-mode cockpit. The 3-D context renders only backend-supported scalar
layers: `qc` cloud water, `qr` rain water, `qv` water vapor, `dbz`
reflectivity, and surface `rain` when those fields exist in the ingested result.
It does not pretend that every CM1 output field has a trustworthy 3-D rendering.
`w`, potential temperature, and direct temperature remain native-grid slice
inspection fields until a later issue defines scientifically honest 3-D
rendering for them. Core field/time/slice controls stay visible and shared
across the 3-D context and slice inspector. Process focus,
projection/rendering details, raw coordinate metadata, and long provenance
labels belong behind details/disclosure until the user asks for them.

Explore's cloud context and slice inspector should default to physically
interesting output views, not arbitrary zero-index slices. The backend should
provide default field/time/slice locations from native-grid data when possible:
for `qc`, first cloud time or the max cloud-water location; for `w`, the
max-updraft location. If those locations are unavailable, the UI may fall back
to domain-center slices and clearly keep the native-grid/provenance caveats
available. Explore should not open at `t=0` when diagnostics show clouds appear
later.

Future comparison work should be user-driven rather than a fixed lab pair. It
should let the user choose results, explain the comparison target, and preserve
the current scientific honesty boundary: no browser-side NetCDF parsing, no
invented unsupported diagnostics, and clear provenance for every compared
metric.

The next comparison step may add side-by-side 2-D slices for an accepted lab
pair. It consumes the existing backend visualization-ready fields/slice API for
`qc` and `w`, supports shared output-index selection with mismatch labels when
times differ, and shows units, min/max, finite/non-finite counts, and provenance
for each result. The browser still does not parse raw NetCDF or implement new
3-D rendering for this comparison.

Completed results should be replayable and inspectable without rerunning CM1. Duplicate/tweak/rerun is useful later, but replay, inspect, explain, and edit notebook fields are the core MVP result-library behavior.

## MVP Scope

### In Scope

- New local project skeleton
- Preset scenario definitions
- Local run manifest format
- Generate CM1 case/run directories
- Launch CM1 through local command
- Track process/log status
- Ingest NetCDF output or create intermediate artifacts
- Unified Explore cloud context, slice inspector, and explanation workflow
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

## Unified Explore MVP

Start with a practical, trustworthy Explore instrument, not a cinematic
renderer. The near-term MVP is the product loop: select a saved result, see the
scalar-field context, inspect the synchronized native-grid slice, click a cell,
and get a CM1-backed `What happened here?` explanation.

The implemented/near-term Explore layers are:

1. Visualization-ready backend data contract.
2. Native-grid slice inspection for orientation, time indexing, scaling, and
   field availability.
3. Scalar 3-D context for supported fields using thresholded backend-prepared
   point payloads (`qc`, `qr`, `qv`, `dbz`) and a surface-floor layer for
   surface `rain`.
4. Horizontal and vertical slice planes for native-grid fields such as `qc`,
   `w`, `qr`, `qv`, `dbz`, temperature, and potential temperature when present.
5. Selected-cell / selected-region explanation backed by Thermal Fate
   diagnostics.

Later renderer decisions live in #112 and #80, not in the near-term Explore MVP:
volumetric ray marching, isosurfaces, lighting, appearance controls,
fly-through/move-through, cinematic export, and thumbnail/preview generation.

The browser should not parse raw CM1 NetCDF directly. Backend ingest and visualization-ready preprocessing should provide selected, provenance-labeled fields for inspection and rendering.

The first 3-D scalar renderer uses thresholded point clouds and a surface-floor
layer, not volumes or isosurfaces. The backend selects a supported field at a
chosen output time, keeps native coordinates, returns points that pass the
field-specific threshold, reports full NetCDF coordinate extents, active height
range where applicable, thresholded point count, full selected-field
min/max/mean stats, max-value location, and deterministic downsampling if
needed. The browser renders those returned points only; it does not parse raw
NetCDF, interpolate, run marching cubes, extract isosurfaces, ray march, or
invent cloud physics. The rendering method should be labeled as a direct scalar
point cloud or surface-floor layer, and the processing method should identify
the backend native-grid threshold operation.

Reflectivity uses weather-radar-style fixed dBZ colors rather than a dynamic
per-run scale. The legend should cover 0 to 60+ dBZ even when a shallow-cumulus
result only contains weak or sparse reflectivity. The UI should show the current
field max and the visible-point threshold so a low-reflectivity case is
understandable without presenting it as a rendering failure.

Point placement must use full coordinate extents from the payload, not the
min/max of returned cloudy points. Side/elevation views are the first scientific
check: `Side x-z` and `Side y-z` map model height `z` to visual height so cloud
base/top are legible. `Top-down x-y` is for horizontal footprint, and `Oblique
overview` is an interpretive overview. The domain box, floor, axis labels, and
points should use the same coordinate transform, with technical details showing
the actual coordinate units and visualized extent.

The MVP viewer uses a fixed scientific workbench rather than a long scrolling
page section or a pretend physical camera. The workbench should keep primary
visual controls near the viewport, keep timeline and slice-position controls
directly below the render, and move provenance/details into a secondary
collapsible panel. Zoom scales the rendered data layer while preserving the
underlying CM1 coordinate transform; it does not change the model data, slice
selection, axes labels, or diagnostic values. Projection labels should be
explicit:

- `Side x-z`: height is vertical; `y` is compressed or hidden.
- `Side y-z`: height is vertical; `x` is compressed or hidden.
- `Top-down x-y`: horizontal footprint; height is not shown vertically.
- `Oblique overview`: interpretive overview, not a true perspective camera.

Scale markers should show horizontal distance, height when visible, the domain
floor, and the active cloud-water height range so the view remains readable at
normal browser zoom and across common screen sizes.

The first 3-D slice planes reuse the #72 JSON slice endpoint. The scene can
request horizontal and vertical native-grid slices for the selected slice field
at the same output time as the 3-D scalar layer. Slice
planes are optional inspection aids, not the cloud itself: they should be
toggleable, visually secondary, semi-transparent, and tied to the same
interesting native-grid locations used by Inspect. The UI must show field name,
units, selected time, slice location, min/max, native-grid caveats, and
provenance labels. These planes are inspection overlays, not ray-marched volumes
or interpolated fields.

Slice-plane controls should let the user choose the native-grid plane and move
it through the domain:

- horizontal `z` / height slice: moves up and down through vertical levels;
- vertical `x-z` slice: moves forward/back through `y`;
- vertical `y-z` slice: moves left/right through `x`.

These controls change the selected slice request to the backend. They are not
true 3-D rotation controls, do not interpolate staggered grids, and do not
change the underlying CM1 result.

The 3-D viewer should provide simple view presets:

- Cloud overview: cloud-water points with no planes or one subtle reference
  slice.
- Vertical cross-section: a vertical slice through max `qc` or max `w`.
- Top-down slice: a horizontal slice through the cloud-bearing level.
- Inspect updraft slice: `w` slice through the max-updraft location.

The viewer should also provide quick jumps for first cloud, max cloud water, and
max updraft when result diagnostics provide enough timing metadata. Slice-plane
defaults should avoid empty zero-index views where a center/cloud-bearing level
is more useful. Slice defaults should be selected for the current output time:
`qc` slices should center on the selected-time max cloud-water cell, and `w`
slices should center on the selected-time max-updraft cell. Native-grid/no-
interpolation caveats and rendering provenance must stay available, but long
technical labels belong under `About this visualization` rather than dominating
the primary view.

The first 3-D impression should make the validated reference baseline obvious:
opening from Results should land on the first-cloud or max-cloud-water time when
available, show a visible cloud-water point cloud, show the domain box, axes,
ground/base plane, current time, and threshold, keep slice planes optional and
secondary, and place detailed provenance/rendering labels under `About this
visualization`.

### Post-MVP Visual Polish, Fly-Through, and Export

Visual polish is deliberately post-MVP. The first product loop should prove that
Cloud Chamber can generate CM1 packages, run CM1 locally, ingest results,
produce diagnostics, save/reopen result cards, inspect fields, and render a
practical 3-D interpretation. Only after that loop is useful should the
visualizer pursue cinematic work.

Post-MVP visual work may include:

- volumetric ray marching for cloud-water fields;
- shadows and simple atmospheric lighting;
- edge brightening to make cloud boundaries readable;
- cloud-base darkening to emphasize vertical structure;
- fly-through / move-through camera modes;
- cinematic export for short videos or stills;
- generated thumbnails or previews for saved results.

These features must remain interpretations of CM1-derived data. The UI should
continue to show the source result, field, units, processing method, rendering
method, and any caveats. Visual polish must not imply extra model detail,
interpolate native grids without disclosure, or turn preview imagery into a
completed CM1 result.

Generated thumbnails, videos, preview frames, and other visual artifacts are
local/generated outputs by default. They should stay outside git unless a future
issue defines a tiny fixture or documented artifact policy for tests. Large
visualization artifacts must not be committed.

## 2-D Field Inspection MVP

The first inspector opens from a saved or ingested Result Card / Experiment
Notebook entry. It consumes the #72 backend fields/slice API; the browser never
parses raw CM1 NetCDF.

MVP behavior:

- list available fields from the backend, starting with `qc` and `w`, and `qr`
  when present;
- allow field selection and output time selection;
- default to a physically interesting time and slice location using backend
  defaults when available;
- request horizontal and vertical slice payloads from the backend;
- show one primary heatmap by default, with `Horizontal`, `Vertical X`, and
  `Vertical Y` modes;
- show heatmaps with field units, native
  grid, selected time, slice shape/dimensions, min/max, finite and non-finite
  counts, and provenance labels;
- keep raw JSON numeric slice values available under technical details rather
  than making matrix dumps the primary UI;
- represent missing fields and bad slice requests as UI errors instead of
  crashing;
- clearly label slices as CM1-derived inspection data, not 3-D rendering.

The 2-D inspector is deliberately practical and small. It helps verify field
orientation, time indexing, vertical coordinates, units, and scaling inside the
unified Explore workflow before any later renderer upgrade changes the visual
representation.

## Visualization-Ready Data Contract

The first visualization contract is slice-first and backend-owned. The browser
does not parse raw NetCDF; it asks the local backend for selected,
provenance-labeled field metadata and JSON slice payloads from an ingested CM1
result.

Implemented backend endpoints:

```text
GET /api/results/{result_id}/visualization/fields
GET /api/results/{result_id}/visualization/defaults
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

The defaults endpoint chooses physically interesting native-grid locations for
the unified Explore workflow. It reports max-value locations for `qc` and `w` when
available, including selected time index, horizontal level, vertical slice
indices, source label, and caveats. It does not interpolate or invent data; if
the field is missing or non-finite, the UI falls back to domain-center slices.

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
