# Cloud Chamber Architecture And Data Model

## Architecture Overview

Cloud Chamber should be local-first.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.

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

### Configuration Builder

Turns a scenario + user controls into:

- `namelist.input`
- `input_sounding`
- `case_manifest.json`
- run manifest

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

### Output Ingester

Responsibilities:

- inspect NetCDF outputs
- extract metadata and fields
- produce app-friendly artifacts
- compute diagnostics
- create thumbnails/previews
- record provenance

### Result Library

Responsibilities:

- list runs/results
- rename/save/tag
- search/filter
- open visualizer
- duplicate setup
- delete local output safely

### 3-D Visualizer

Responsibilities:

- load processed field data
- display volume/slices/isosurfaces
- time playback
- camera controls
- lighting controls
- field controls
- rendering labels/provenance

## Data Flow

### Create Run

```text
scenario + controls
→ config builder
→ run directory
→ run manifest
```

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

## Storage Layout

Recommended local layout inside project, all ignored except templates/docs:

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

Committed scenario templates:

```text
scenarios/
  lower-atmosphere/
    baseline-shallow-cumulus/
    dry-failed-cumulus/
    capped-suppressed/
    humid-vigorous/
    low-stratus/
```

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

## Safety / Guardrails

- Generated outputs ignored by git.
- Confirm before deleting local runs.
- Do not overwrite run directories.
- Clear labels for preview vs CM1 result.
- No hidden fake clouds.
