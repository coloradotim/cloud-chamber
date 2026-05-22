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

For Baseline Shallow Cumulus, the first CM1-facing package uses CM1's BOMEX shallow-cumulus reference behavior (`testcase = 3`, `isnd = 19`) with Cloud Chamber quick-look grid/runtime settings. The generated `input_sounding` is numeric and CM1-readable, but the baseline namelist uses CM1's built-in analytic BOMEX sounding by default.

The first full-sequence NetCDF ingest of the local quick-look run confirmed that all 25 model-output files were evaluated, but the run produced no cloud, no vertical motion, and NaN/Infinity caveats in surface/thermodynamic fields. The quick-look baseline now keeps the BOMEX sounding and surface-flux approach but uses fixed small ocean roughness (`set_znt = 1`, `cnst_znt = 0.0002`) rather than the dynamic roughness / fixed friction-velocity path that produced invalid local output. A subsequent fixed-roughness validation package completed and produced NetCDF output, but still had no cloud, no vertical motion, and NaN/Infinity caveats. This keeps the case a Cloud Chamber-tuned BOMEX-style quick-look candidate, not a scientifically accepted reference simulation.

Cloud-scale defaults for the first lower-atmosphere contract are:

```text
domain: about 16 km x 16 km x 6 km
horizontal spacing: about 200 m
vertical spacing: about 125 m
runtime: about 7200 s
output cadence: about 300 s
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

Raw NetCDF is not ideal for direct browser rendering.

Recommended staged path:

1. Load/inspect NetCDF in backend.
2. Extract selected fields and time frames.
3. Downsample or chunk as needed.
4. Store browser-friendly arrays.
5. Load fields into Three.js/WebGL viewer.

Potential processed formats:

- JSON metadata + binary float arrays
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
