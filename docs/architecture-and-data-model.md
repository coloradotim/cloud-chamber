# Cloud Chamber Architecture And Data Model

## Architecture Overview

Cloud Chamber should be local-first.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.

The first MVP target is a 2024 MacBook Air with 8GB RAM. Design for one local CM1 run at a time, conservative output handling, and backend-side processing/downsampling. Optional cloud compute can be researched later, but it is not part of the core architecture.

Replay / inspect / save is core MVP. Duplicate / tweak / rerun is later and should not drive the first result storage model.

Recommended architecture:

```text
Frontend UI
  ↓
Local app/server API
  ↓
Scenario/config generator
  ↓
Run manager
  ↓
CM1 process
  ↓
Output watcher / ingester
  ↓
Local result store
  ↓
3-D visualizer
```

## Suggested Stack

This is not final, but a reasonable starting point:

### Frontend

- React + TypeScript
- Vite or Next.js local app
- Three.js / React Three Fiber for 3-D visualizer later
- Zustand or similar small state store

### Local Backend

Options:

1. Python FastAPI local server
2. Node/Electron/Tauri local app shell
3. Hybrid: Python backend for CM1/run/data handling + React frontend

Recommendation:

Start with **Python FastAPI + React/Vite**.

Reason:

- Python is better for NetCDF/xarray preprocessing.
- React is good for UI/visualization.
- Local server avoids browser filesystem limitations.
- Use `uv` for Python dependency/project workflows when backend implementation expands.

Later, package with Tauri/Electron if needed.

## Major Components

### Scenario Catalog

Stores preset scenario definitions.

Responsibilities:

- list scenarios
- expose controls
- map friendly controls to CM1 configuration
- define expected outputs
- define visualization defaults
- define run-size presets and one-control variation metadata around a baseline
- define the physical question and learning goals

Baseline Shallow Cumulus is the first hero case. Warm rain remains early but does not block the Golden Path.

Scenario templates are validated before package generation. The schema supports stable IDs, display names, descriptions, physical questions, learning goals, friendly controls, advanced/developer-only settings, run-size presets, expected diagnostics, CM1 mapping notes, visualization defaults, warnings, limitations, and one-control variation metadata. Invalid templates should fail with actionable validation messages before any CM1-facing files are generated.

The local FastAPI backend exposes the implemented catalog through `GET /api/scenarios`. The response should include the Golden Path scenario ID and product-facing scenario summaries only; advanced/developer controls can remain in the template but should not appear in the primary Scenario Builder flow.

### Configuration Builder

Turns a scenario + user controls into:

- `namelist.input`
- `input_sounding`
- `case_manifest.json`
- run manifest
- dry-run report
- visualization defaults

For the Baseline Shallow Cumulus Golden Path, the generated package should preserve the physical question, curated controls, run-size preset, expected diagnostics, expected output fields, and provenance labels before CM1 starts.

The CM1 input generation contract is deterministic and testable before full package generation. It documents the expected generated files and preserves product-facing controls separately from raw namelist/developer settings.

For Baseline Shallow Cumulus, the recovery package is derived from CM1's local `les_ShallowCu` reference case. It preserves `testcase = 3`, the reference grid, runtime, domain top, Rayleigh damping, surface/ocean/flux settings, surface stress path, and wind profile as much as possible. The external-sounding reproduction changes the thermodynamic source from the built-in BOMEX analytic sounding (`isnd = 19`) to CM1's `input_sounding` route (`isnd = 17`) so future one-control moisture experiments have a validated profile path. The intentional Cloud Chamber output-path change remains NetCDF output (`output_format = 2`) so the completed run can flow into ingest and diagnostics.

The earlier Cloud Chamber quick-look derivative is not scientifically accepted: full-sequence ingest evaluated all 25 model-output files, but the run produced no cloud, no vertical motion, and NaN/Infinity caveats; a fixed-roughness follow-up still failed in the same way. Quick-look scaling should happen only after the reference-derived package works, and future changes should be introduced one at a time with manual CM1 validation.

The first reference-derived validation run, `dry-run-les-shallowcu-20260522140642`, completed locally with NetCDF output and ingested 7 model-output time steps over 21600 seconds. It produced cloud water and vertical velocity diagnostics, so the architecture should treat the reference-derived package as the recovery baseline and the earlier compact derivative as invalid evidence rather than a tuning base.

Run-size presets now vary only runtime timing for this recovered baseline. The standard/reference package preserves `timax = 21600.0` and `tapfrq = 3600.0`. The first quick-look variant preserves every reference-derived science/numerics setting and changes only `timax = 10800.0` and `tapfrq = 900.0`. Domain/grid, vertical spacing, domain top, surface stress/roughness path, moisture/sounding, surface fluxes, turbulence/SGS settings, damping settings, boundary conditions, NetCDF output, and reference `LANDUSE.TBL` staging should remain unchanged.

The first quick-look validation run, `dry-run-quicklook-les-shallowcu-20260522151536`, preserved those settings, completed locally, and ingested 13 model-output time steps over 10800 seconds. Diagnostics still reported cloud formation, vertical motion, and rain, so the architecture can treat this runtime-only quick-look preset as the first validated shorter Baseline Shallow Cumulus variant.

The external-sounding reproduction run, `dry-run-external-sounding-baseline-20260522185000`,
preserved the same quick-look timing and used `isnd = 17` with a generated
numeric `input_sounding`. It completed locally, produced NetCDF, ingested 13
model-output time steps over 10800 seconds, and retained cloud formation,
vertical motion, and rain. The architecture can now treat external-sounding
Baseline Shallow Cumulus as the accepted profile path for one-factor moisture
experiments.

Dry Failed Cumulus should branch from this validated reference-derived family,
not from the invalid compact quick-look derivative. Architecturally, it is a
moisture-limited contrast case: preserve the validated grid/domain, surface
forcing, stress/roughness path, damping, turbulence/SGS settings, boundary
conditions, NetCDF output, runtime-file staging, and quick-look timing, then
change only the lower-atmosphere moisture/sounding path once that path has been
validated. The intended product control is `low-level humidity = drier`; raw
sounding or namelist edits belong in developer implementation details.

Because the accepted baseline originally relied on the CM1 `les_ShallowCu`
built-in sounding behavior, Cloud Chamber must preserve evidence for the
external `input_sounding` reproduction before drying the profile. Only after
that reproduction succeeds should Dry Failed reduce low-level moisture. A run
with no cloud and no meaningful vertical motion, or no cloud with severe
NaN/Infinity caveats, is not a valid Dry Failed Cumulus result.

The first accepted Dry Failed implementation uses the same generated namelist as
the accepted external-sounding baseline and changes only the generated
lower-atmosphere moisture profile for `low_level_humidity = drier`. Validation
run `dry-run-dry-failed-cumulus-20260522192000` completed locally, produced
NetCDF, ingested 13 model-output time steps, and produced no cloud/rain while
retaining meaningful vertical motion. This establishes the first two-outcome
lab pair: Baseline forms cloud; Dry Failed has thermals without meaningful
cloud water.

Cloud-scale defaults for the first lower-atmosphere contract are:

```text
domain/grid: 64 x 64 x 75
horizontal spacing: 100 m
nominal vertical spacing: 40 m
domain top: 18000 m
runtime: 21600 s
output cadence: 3600 s
```

Baseline Shallow Cumulus quick-look timing:

```text
runtime: 10800 s
output cadence: 900 s
unchanged: reference-derived grid/domain/surface/damping/boundary settings
```

Scenario-specific deviations from these defaults must be explicit in the scenario template or generated report.

Dry-run package generation uses the validated scenario template and CM1 input contract to create a reviewable package under the configured runtime home, normally `~/CloudChamber/runs/<run-id>/`. The package writer should refuse to overwrite existing run directories, validate controls before writing, and produce only package inputs/reports, not CM1 output.

The implemented dry-run API is `POST /api/dry-run-package`. It accepts scenario ID, selected product controls, and run-size preset, then returns the package paths and dry-run report summary for UI review. It must not launch CM1, write NetCDF, or place generated packages inside the source tree during tests.

### Preview Engine

Fast reduced/light predictor.

Responsibilities:

- estimate likely cloud/no-cloud behavior
- estimate LCL/cloud base trend
- warn about cap/moisture/dry-air constraints
- label as preview only

This is not the truth source.

### Run Manager

Responsibilities:

- create run directory
- copy CM1 runtime files
- launch CM1 process
- capture stdout/stderr
- track status
- detect completion/failure
- expose logs
- prevent accidental overwrite

The first implemented local run manager is intentionally conservative:

- one local CM1 process may be active at a time;
- launch requires valid local CM1 settings and a generated `run_manifest.json`;
- command construction points at the configured local `cm1.exe`;
- stdout and stderr are written into the run package `logs/` directory for later result notebook provenance;
- lifecycle states move through queued, running, completed, failed, or canceled;
- launch refuses packages that already contain output-like files such as NetCDF,
  `cm1out_*.dat`, or `cm1out_*.ctl`;
- launch refuses placeholder-only `namelist.input` or notes-only `input_sounding` files;
- launch rejects Rayleigh damping settings that start too low and would damp more than half the vertical domain;
- launch stages required local runtime files such as `LANDUSE.TBL` from the configured CM1 run directory into the generated package directory;
- process exit code 0 is not enough to mark a usable completed CM1 result; NetCDF or raw CM1 `.dat/.ctl` output artifacts must exist before `completed_cm1_result` is used;
- tests inject fake subprocesses, so CI never needs a real CM1 executable.

Real CM1 execution remains a manual/local responsibility until the user has local settings and runtime files in place. The manager must fail clearly when CM1 paths are missing rather than pretending a run started. If the process exits successfully but no NetCDF or raw CM1 `.dat/.ctl` output exists, the manifest remains `completed` at the process level but uses `validation_status: needs_review` and `product_state: process_completed_no_output`.

The first successful Baseline Shallow Cumulus smoke run produced GrADS/direct-access CM1 artifacts (`cm1out_*.dat` plus `.ctl` descriptors) rather than NetCDF. That proves local execution but is not full ingest. The manifest should catalog those raw artifacts separately from NetCDF paths and processed visualization artifacts. Floating-point exception flags reported in stderr should be surfaced as runtime warnings/caveats, not automatically treated as launch failure.

### Runtime Storage Inventory And Cleanup

Cloud Chamber runtime cleanup operates only under the configured runtime home, normally `~/CloudChamber`. The backend storage service inventories `~/CloudChamber/runs/<run-id>/` directories, reads `run_manifest.json` when available, reports total runtime-home size, the 50 GB MVP warning threshold, whether the runtime home is above that threshold, per-run size, lifecycle/provenance metadata, output artifact counts, and conservative categories:

```text
dry_run_only
running
completed_with_output
completed_no_output
failed
canceled
saved_or_protected
missing_manifest
malformed_manifest
unknown
```

Malformed or missing manifests are reported without crashing inventory. Largest runs are surfaced by size so the user can see what is consuming disk.

The 50 GB warning threshold is a configurable product default, not a scientific limit. Crossing the threshold should point the user to the largest-run inventory and safe cleanup actions. It must not trigger automatic deletion.

Deletion is explicit and scoped to one selected run directory. The cleanup service refuses path traversal, symlink escapes, the runtime home itself, the user's home directory, the source repo by construction, and configured CM1 root/run paths. It also refuses running runs and saved/protected runs unless a force flag is provided. A dry-run delete returns the selected path and estimated size reclaimed without deleting files; a real delete requires explicit confirmation.

Deleting a run removes local generated CM1 inputs, copied runtime files, logs, raw CM1 output, NetCDF output, and processed artifacts inside that run directory. It does not delete result-library metadata outside that directory, repo files, or the external CM1 installation.

### Output Ingester

Responsibilities:

- inspect preferred NetCDF outputs
- catalog raw CM1 `.dat/.ctl` artifacts until NetCDF ingest is verified
- extract NetCDF metadata and fields
- produce app-friendly artifacts
- compute diagnostics
- create thumbnails/previews
- record provenance

The first implemented ingest step creates `result_metadata.json` in the completed run directory. It reads NetCDF with xarray and records result ID, run ID, scenario, physical question, controls, run-size preset, source lifecycle/product/provenance state, raw CM1 artifacts, NetCDF paths, processed artifact placeholders, dimensions, coordinates, variables, units, time coordinate, grid shape, warnings, and timestamps.

The next implemented step attaches first-pass Baseline Shallow Cumulus diagnostics to that result metadata. Diagnostics read NetCDF fields through the backend and summarize `qc`, `w`, and optional `qr` without parsing raw `.dat/.ctl` artifacts. Raw `.dat/.ctl` artifacts remain cataloged on the run metadata but are not parsed as ingest input.

CM1 may write a completed run as a sequence of NetCDF model-output files such as `cm1out_000001.nc` through `cm1out_000025.nc`. Cloud Chamber must ingest the model-field sequence, not just the first NetCDF file, before making cloud/no-cloud statements. Stats files such as `cm1out_stats.nc` are NetCDF artifacts but are not model-field time-series inputs for `qc`, `w`, and `qr` diagnostics.

Result metadata records model-output paths separately from stats NetCDF paths, skipped/corrupt files, contributing model-output file count, total time steps, first/last output time, and whether time came directly from a NetCDF coordinate or an inferred fallback.

### Result Cards / Experiment Notebook Entries

The backend result-card layer is the product-facing view over ingested metadata.
It does not rerun CM1 and does not parse raw output directly. It summarizes:

- run ID, scenario, run-size preset, and physical question;
- diagnostics summary, first cloud time, max `qc`, max/min `w`, rain yes/no, and caveats;
- output file summary, including NetCDF/model-output/stat/raw/processed counts and time-step range;
- provenance labels that distinguish completed CM1 result, ingested metadata, and saved notebook entry;
- editable notebook fields: name, tags, notes, saved, and protected.

Editable notebook state is stored as `result_card.json` beside `result_metadata.json`.
The saved/protected flag prevents accidental cleanup through the runtime storage
layer, while CM1 output remains local/generated and uncommitted.

Current diagnostics compute:

- cloud formed yes/no using `qc >= 1e-6 kg/kg` and a minimum 10 cloudy grid-cell rule;
- first cloud time from the NetCDF time coordinate when available, otherwise inferred output index;
- first-pass cloud base/top from available vertical coordinates;
- max `qc`, time of max `qc`, `qc` max time series, cloud fraction time series, and cloud-present time steps;
- max/min `w`, time of max/min `w`, and `w` max/min time series;
- optional rain summary from `qr >= 1e-7 kg/kg`.

Diagnostics preserve runtime warnings from the run manifest/result metadata. CM1 floating-point exception flags are caveats, not automatic failure. The diagnostics also count non-finite values in target fields where practical, ignore NaN/infinity for finite summaries, and record field-specific caveats if `qc`, `w`, or `qr` are missing or entirely non-finite.

This result metadata is not a Result Card UI and not visualization-ready data. It is the backend bridge that later result cards and inspectors can consume.

### Result Library

Responsibilities:

- list runs/results
- rename/save/tag
- search/filter
- open visualizer
- duplicate setup
- delete local output safely

For MVP, replayable and inspectable saved results are more important than rerunning a saved setup. Duplicate/tweak/rerun can build on the same metadata later.

### 3-D Visualizer

Responsibilities:

- load processed field data
- display volume/slices/isosurfaces
- time playback
- camera controls
- lighting controls
- field controls
- rendering labels/provenance

#31 has been superseded by staged visualizer implementation issues. The architecture should not treat a single broad visualizer issue as the implementation plan anymore.

The staged dependency path is:

```text
NetCDF ingest (#68)
-> diagnostics (#69)
-> result cards / notebook entries (#70)
-> Results Library UI (#71)
-> visualization-ready data contract (#72)
-> 2-D field inspection (#73)
-> 3-D scene shell (#77)
-> cloud-water rendering (#78)
-> slice planes (#79)
-> visual polish / fly-through / export later (#80)
```

The 3-D viewer should open from saved or ingested results and consume visualization-ready backend data. It should not parse raw NetCDF directly in the browser. Rendering remains a visualizer interpretation of CM1-derived output and must carry source model, run/result, field, processing, and rendering-method provenance.

The first 3-D scene shell is the frontend interaction/container layer. It opens
from a Result Card / Experiment Notebook entry, requests the visualization-ready
field catalog, and exposes:

- scene container;
- orbit/pan camera mode shell;
- zoom control;
- reset camera action;
- time slider shell;
- field selector shell;
- loading, empty, and error states;
- provenance and rendering-method labels.

Cloud-water rendering starts as a thresholded point cloud for `qc`, not an
isosurface or volume renderer. The backend owns field selection and thresholding
through:

- `GET /api/results/{result_id}/visualization/point-cloud`

The point-cloud endpoint reads the selected NetCDF output time, uses native
`zh/yh/xh` coordinates for `qc`, returns `[x, y, z, value]` points where `qc`
meets the requested threshold, and records source count, returned count,
min/max value, downsampling status, coordinate units, and provenance. If source
points exceed `max_points`, the backend applies deterministic stride
downsampling and labels it. The frontend renders only the returned
visualization-ready points and must label the result as a CM1-derived
interpretation.

3-D slice planes reuse the same backend slice endpoint as the 2-D inspector:

- horizontal plane: `orientation=horizontal`;
- vertical plane: `orientation=vertical_x` or `orientation=vertical_y`;
- fields: `qc` and `w` first;
- time: synced with the visualizer time state and cloud-water point cloud.

The browser receives JSON slice payloads with field metadata, min/max stats,
dimension order, selected native-grid location, caveats, and provenance labels.
The scene may draw simple inspection planes from those payloads, but it must not
parse raw NetCDF in the browser, interpolate native grids, ray march, or invent
synthetic cloud physics.

Post-MVP visual polish is a later rendering layer, not part of the data-source
contract. Volumetric ray marching, shadows, edge brightening, cloud-base
darkening, fly-through/move-through camera modes, cinematic export, and
generated thumbnails should build on the same ingested result and
visualization-ready data contracts. They must continue to label rendered output
as an interpretation of CM1-derived data and carry source model, run/result,
field, processing method, rendering method, and caveats.

Future export artifacts should be treated as local/generated outputs unless a
specific policy says otherwise. Generated thumbnails, preview frames, videos,
large processed visualization data, and browser-ready render caches should not
be committed. If small visual fixtures are needed for tests, they should be
intentionally tiny and documented separately from real CM1 output.

### Visualization-Ready Field Slices

The backend owns NetCDF/xarray field selection. Browsers should request
visualization-ready payloads from ingested results instead of opening raw CM1
NetCDF files.

Implemented MVP endpoints:

- `GET /api/results/{result_id}/visualization/fields`
- `GET /api/results/{result_id}/visualization/slice`
- `GET /api/results/{result_id}/visualization/point-cloud`

The field catalog exposes available visualizable fields, starting with `qc`
and `w` and including `qr` when present. It maps raw CM1 field names to product
canonical names such as `cloud_water` and `vertical_velocity`, includes native
dimensions, coordinate names, units, time values, source model/run/result
provenance, processing method, and rendering method labels.

The slice endpoint returns JSON numeric arrays for the slice-first MVP. It
supports horizontal slices and vertical `x`/`y` slices on native grids:

- `qc`: `time, zh, yh, xh`
- `w`: `time, zf, yh, xh`

It does not interpolate staggered fields. Payloads include the selected time,
orientation, level/index, dimension order, shape, min/max/mean, finite and
non-finite counts, caveats, and provenance. Non-finite values are represented
as `null` in JSON arrays and counted in stats.

Vertical coordinate units are preserved. When a vertical coordinate is in
kilometers, payloads may include a safe meter display conversion while still
recording the native units and native value.

Future 3-D block data should use JSON metadata plus binary `float32` arrays
with explicit downsampling/max-voxel controls. That binary block contract should
build on the same provenance labels and native-grid rules, but it is not needed
for the first 2-D inspector.

### 2-D Field Inspector

The frontend uses a task-based workspace shell with `Build`, `Results`,
`Inspect`, and `Visualize` sections. `Results` is the default landing section so
the selected result context is obvious before field inspection or 3-D
visualization. The selected result ID flows from the Results Library into the
2-D inspector and 3-D visualizer; those consumers request backend-prepared
payloads for that result rather than opening files directly.

User-facing state labels are separate from technical provenance. The primary UI
may translate raw states like `ingested_result_metadata` or
`completed_cm1_result` into `Ingested`, `Completed CM1 result`, `Saved`, or
`Needs review`. The raw lifecycle, product state, source model, processing
method, rendering method, and native-grid caveats remain available under
technical details so scientific honesty is preserved without making the main
workflow read like a manifest.

Successful cloud-forming results can show `Minor caveat` in the primary UI when
warnings or coordinate notes exist but the run is still inspectable. `Needs
review` should be reserved for failed, no-cloud, missing-diagnostics, or
incomplete states where the result needs closer attention before it is treated
as a validated learning case.

The first field inspector is a frontend consumer of the visualization-ready
fields/slice API. It opens from a Result Card / Experiment Notebook entry and
does not read raw NetCDF or parse CM1 files in the browser.

The inspector requests:

- the field catalog for the selected result;
- one horizontal slice for the selected field/time/vertical level;
- one vertical slice for the selected field/time and `vertical_x` or
  `vertical_y` orientation.

It displays field name, units, native grid, selected time, min/max, finite and
non-finite counts, heatmap slices, caveats, and provenance labels. The raw JSON
numeric slice values remain available under technical details for audit and
debugging, but the primary inspection surface should be a readable heatmap.
Errors from unavailable fields or invalid slice selections remain UI-level
inspection errors; they do not alter the underlying result metadata or imply a
failed CM1 run.

The 2-D inspector and 3-D visualizer both choose an initial interesting time
from result diagnostics: first cloud time when present, otherwise time of max
cloud water when available, otherwise the latest output time. This prevents the
validated Baseline Shallow Cumulus quick-look result from opening at an empty
`t=0` frame when clouds form later.

The 3-D viewer keeps the same data-source contract while improving first-look
readability: cloud-water points should be visible at the default time, slice
planes should provide spatial context without overwhelming the point cloud, and
long provenance/rendering labels should sit in technical details rather than in
the main scene controls.

The backend also exposes an interesting-view defaults contract for UI startup:

```text
GET /api/results/{result_id}/visualization/defaults
```

The response reports per-field native-grid defaults for `qc` and `w`, including
time index/seconds, horizontal level index, vertical `x`/`y` slice indices,
source label, max value when available, caveats, and provenance. These defaults
are computed from backend xarray access to ingested NetCDF output. The browser
uses them to pick cloud-bearing or max-updraft views but still requests normal
slice/point-cloud payloads for rendering. The defaults endpoint does not
interpolate fields, parse raw NetCDF in the browser, or change result metadata.

This is not a 3-D viewer, replay engine, or rendering pipeline. It is the
orientation/scaling check that should happen before 3-D visualizer work.

## Data Flow

### Create Run

```text
scenario + controls
→ config builder
→ run directory
→ run manifest
```

Runtime tier metadata should flow through this path: scenario templates define available run-size presets, generated run packages record the selected preset, run manifests preserve it during execution, and result metadata keeps it available for later inspection.

If size/runtime estimates are not validated yet, manifests and reports should record that explicitly rather than presenting guessed precision.

### Execute Run

```text
run manifest
→ CM1 command
→ logs + NetCDF output
→ status update
```

### Ingest Run

```text
NetCDF output
→ metadata
→ diagnostics
→ visualization artifacts
→ result manifest
```

### Visualize Run

```text
result manifest
→ selected field/time
→ visualizer data loader
→ 3-D view
```

### Result Notebook Entry

Conceptually, a saved result can be represented as a notebook-style entry:

```text
result notebook entry
  result_manifest.json
  run_manifest.json
  diagnostics_summary.json
  key_frames.json
  user_notes.md or notes field
  visualization_defaults.json
```

These file names are conceptual for now. Implementation should choose concrete schemas when the result model is built.

The result manifest should be able to answer:

```text
What scenario was this?
What physical question was tested?
What controls were used?
What run-size preset was selected?
What did CM1 do?
What diagnostics summarize the cloud evolution?
Can I replay it?
Can I open it in the 3-D visualizer?
Can I find it again later?
```

## Storage Layout

Default runtime data belongs outside the repo:

```text
~/CloudChamber/
  settings.json
  runs/
  cache/
  logs/
```

The repo may support `./local-data/` as a gitignored development override, but the default should remain `~/CloudChamber`.

The top-level `data/` directory, if present, is reserved for documented tiny fixtures or placeholders only. It is not a runtime storage location.

Optional ignored local development layout:

```text
local-data/
  cm1-runs/
    <run-id>/
      namelist.input
      input_sounding
      run-manifest.json
      cm1.stdout.log
      cm1.stderr.log
      cm1out_*.nc
  processed/
    <run-id>/
      result-manifest.json
      fields/
      thumbnails/
  library/
    index.json
```

## Settings Model

Settings should support:

- Cloud Chamber runtime home, defaulting to `~/CloudChamber`.
- CM1 root path.
- CM1 run directory path.
- optional cache/log directories.
- environment override such as `CLOUD_CHAMBER_CM1_ROOT`.
- optional runtime-home override `CLOUD_CHAMBER_RUNTIME_HOME` for tests/local development.
- saved config in `~/CloudChamber/settings.json`.

Likely local CM1 probe paths may include:

```text
/Users/timpeterson/cm1r21.1
/Users/timpeterson/cm1r21.1/run
```

These are probes/defaults, not hard-coded requirements. If CM1 is missing, Cloud Chamber should fail clearly with settings guidance rather than silently pretending work succeeded.

The backend settings model loads saved JSON config from the runtime home, lets `CLOUD_CHAMBER_CM1_ROOT` override saved CM1 root paths, infers `<cm1_root>/run` when only a root is provided, and reports a ready/missing CM1 discovery status without launching CM1 or writing runtime data into the repo.

Committed scenario templates:

```text
scenarios/
  lower-atmosphere/
    baseline-shallow-cumulus/
    dry-failed-cumulus/
    capped-suppressed/
    humid-vigorous/
    low-stratus/
    warm-rain/
```

## Run Manifest Concept

Run manifests should record the scenario template, adjusted controls, generated CM1-facing files, runtime paths, lifecycle state, validation status, timestamps, and later output paths. A manifest should not require NetCDF output to exist.

Run manifests should also record the selected run-size preset, physical question, expected diagnostics, and visualization defaults when those concepts are available from the scenario template.

The backend run-manifest schema records run ID, scenario reference/version, adjusted controls, generated CM1 input paths, CM1 root/run paths, app metadata, timestamps, lifecycle state, validation status, output paths, user notes/tags, and provenance labels. It serializes/deserializes as JSON and does not require NetCDF output.

Output metadata distinguishes:

- `raw_cm1_artifacts`: local CM1 `.dat/.ctl` files such as `cm1out_000001_s.dat`, `cm1out_s.ctl`, `cm1out_stats.dat`, and `cm1out_metadata.ctl`;
- `netcdf_paths`: preferred self-describing CM1 output files such as `.nc`, `.nc4`, `.cdf`, or `.netcdf`;
- `processed_artifacts`: future Cloud Chamber-derived browser/diagnostic artifacts;
- `runtime_warnings`: caveats captured from logs, such as CM1 floating-point exception flags.

Raw `.dat/.ctl` artifact detection is an honest catalog, not full ingest, diagnostics extraction, or visualization preprocessing.

Lifecycle states:

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

`packaged` means Cloud Chamber generated a dry-run package. It is not equivalent to queued, running, or completed CM1 output.

`ingested` means Cloud Chamber has derived metadata or browser-friendly artifacts from completed CM1 output. `saved` means the user has a named/tagged experiment notebook entry. Neither state changes the underlying CM1 output provenance.

## Process Control

The app should support:

- start run
- tail logs
- cancel run if possible
- mark failed
- retry run
- ingest completed run

Avoid complex job scheduling at first. One local run at a time is fine for MVP.

## CM1 Runtime Assumptions

CM1 is external to the app.

User provides path like:

```text
/Users/timpeterson/cm1r21.1/run
```

The app checks:

- `cm1.exe`
- `LANDUSE.TBL`
- NetCDF support
- required Python/xarray/netCDF dependencies

Do not vendor CM1.

The app should avoid assuming large in-memory NetCDF processing. Ingestion should prefer selected fields, selected frames, chunking, downsampling, or other backend-side reductions before browser visualization.

## NetCDF And Visualization Data Contract

NetCDF is Cloud Chamber's preferred ingest path because it is self-describing, portable, and well suited for Python/xarray diagnostics. CM1 can also write GrADS/direct-access `.dat/.ctl` output. Cloud Chamber should catalog those raw files, but the main product should not become a full `.dat/.ctl` parser unless NetCDF proves blocked or impractical.

The current Baseline Shallow Cumulus generator sets CM1 `output_format = 2`, which CM1 documents as NetCDF output. The first successful local smoke run used the prior `.dat/.ctl` path, so the next manual validation should confirm whether the generated NetCDF configuration works with the local CM1 build.

Raw NetCDF is authoritative CM1 output, but it is not ideal for direct browser rendering. The ingestion layer should create explicit metadata and browser-friendly derivatives that preserve provenance:

- source model
- run ID
- scenario ID
- field name and units
- time coordinate
- processing method
- rendering method

Generated visualization artifacts are interpretations of CM1 data and must be labeled that way.

The practical path before 3-D rendering is to define the visualization-ready data contract, then build a 2-D field inspector that can verify orientation, time indexing, field availability, units, and scaling. The 3-D scene shell, cloud-water rendering, and slice planes should build on that same contract.

## Visualization Data Strategy

Raw NetCDF is not ideal for direct browser rendering, and the browser should
not parse raw CM1 output. The local backend should load CM1 NetCDF through
xarray, select only the requested field/time/slice, and return a bounded,
provenance-labeled payload.

Recommended staged path:

1. Load/inspect NetCDF in backend.
2. Extract selected fields and time frames.
3. Return interesting native-grid defaults for `qc`/`w` field/time/slice
   startup state.
4. Return JSON 2-D slices for the slice-first MVP.
5. Downsample or chunk as needed for future larger payloads.
6. Use JSON metadata plus binary `float32` arrays for future 3-D blocks.
7. Load fields into the 2-D inspector or later Three.js/WebGL viewer.

Potential processed formats:

- JSON numeric arrays for MVP 2-D slices
- JSON metadata + binary `float32` arrays for future 3-D blocks
- Zarr later
- compressed chunks later
- PNG/texture stacks for MVP if easier

## Provenance Labels

Every visual field should know:

```text
source_model: CM1
run_id
scenario_id
field_name
units
time_seconds
processing_method
rendering_method
```

Rendering method examples:

- raw slice
- interpolated slice
- max projection
- mean projection
- isosurface
- volume opacity interpretation

Result-card metadata should include the same provenance labels used by visualization data so the Results Library and visualizer tell the same truth about the source model, run, processing, and rendering method.

## Testing Strategy

Early tests should cover:

- scenario schema validation
- config generation
- run manifest creation
- fake CM1 run process
- output detection
- ingestion from tiny fixture NetCDF
- result manifest generation
- visualizer metadata loading
- no generated outputs committed

Golden Path implementation tests should use fake/minimal fixtures for scenario schema, package generation, manifest lifecycle, result-card serialization, and visualization metadata. Real CM1 validation remains local/manual/offline.

## Safety / Guardrails

- Generated outputs ignored by git.
- Confirm before deleting local runs.
- Do not overwrite run directories.
- Clear labels for preview vs CM1 result.
- No hidden fake clouds.
