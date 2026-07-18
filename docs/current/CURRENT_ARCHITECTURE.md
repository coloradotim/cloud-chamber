# Cloud Chamber Current Architecture

**Status:** Descriptive implementation snapshot

This document describes the repository and application architecture that exist today. It is not
a final product architecture, product specification, recipe policy, or roadmap.

The controlling product documents remain:

1. [North Star](../../NORTH_STAR.md)
2. [Product Vision](../product/PRODUCT_VISION.md)
3. [Current State](CURRENT_STATE.md)

## Current Implementation Flow

The current technical flow is:

```text
React / TypeScript / Vite frontend
-> FastAPI backend
-> package generation and manifests
-> external CM1 execution
-> local or trusted-LAN run handling
-> runtime output and NetCDF ingest
-> result metadata and optional notebook state
-> backend diagnostics and bounded visualization payloads
-> browser inspection
```

This is the present implementation. It does not establish that the same surfaces, boundaries,
or persistence choices belong in the eventual product.

## State Distinctions

The current code keeps these states distinct:

| State | Current meaning | Primary implementation |
| --- | --- | --- |
| Configured/generated package | CM1-facing files have been written under the runtime home, but CM1 has not produced output. | `generate_dry_run_package` and `RunManifest` |
| Queued or running CM1 process | A packaged run is queued or an external CM1 executable is active. | `LocalRunQueueManager`, `LocalRunManager`, LAN worker wrapper |
| Completed process | CM1 exited or a stale running manifest was reconciled. | `LocalRunManager._refresh_active`, `reconcile_completed_run_manifest` |
| Completed process with output | The completed manifest lists NetCDF or raw CM1 artifacts. | `OutputMetadata`, runtime inventory |
| Runtime-integrity assessment | Backend-derived trust state based on runtime warnings and field-quality evidence. | `runtime_integrity.py`, ingest diagnostics |
| Ingested result metadata | Backend-created `result_metadata.json` beside the run output. | `result_ingest.py` |
| Editable notebook state | Optional local sidecar state for name, tags, and notes. | `result_cards.py` |
| Backend-derived diagnostic | Summary or science metadata computed by backend code from CM1-derived data. | `result_diagnostics.py`, `output_products.py` |
| Visualization interpretation | Browser-ready field catalogs, slices, point clouds, defaults, and selected-region summaries. | `visualization_data.py`, `selected_region_diagnostics.py` |

The application currently treats process success, output existence, ingest success, runtime
integrity, notebook edits, and browser visualization as separate facts.

## Frontend

The frontend is a React and TypeScript application built with Vite under `app/frontend`.
It currently exposes Build, Results, and Explore surfaces. Those are present UI surfaces,
not a final decision about product navigation.

The browser calls backend APIs for package generation, local queueing, LAN-worker actions,
storage inventory, result cards, diagnostics, and visualization-ready payloads.

Browser code currently does not parse raw NetCDF. Raw CM1 output is handled by the backend.
Any browser view of CM1 fields is an interpretation of backend-derived data, with source,
field, time, and rendering caveats carried by the payload when available.

## Backend

The backend is a FastAPI app under `app/backend/cloud_chamber`. It currently owns:

- scenario and observed-sounding API surfaces;
- dry-run package generation;
- run manifests and lifecycle states;
- local CM1 launch/status/cancel handling;
- serial local queueing and automatic ingest;
- trusted-LAN worker command wrapping;
- result ingest and result-card sidecar state;
- runtime storage inventory and safe cleanup;
- backend diagnostics and visualization-ready field payloads.

This backend ownership is a present constraint, not a final product decision.

## Package Generation

`generate_dry_run_package` writes a run directory under:

```text
<runtime-home>/runs/<run-id>/
```

The current generated package includes:

- `run_manifest.json`
- `case_manifest.json`
- `namelist.input`
- `input_sounding`
- `dry_run_report.json`
- `runtime_file_checklist.json`
- optional source-customization or surface-forcing sidecar files for supported paths

Package generation writes reviewable inputs and metadata. It does not launch CM1, create
NetCDF output, or make a scientific outcome trustworthy by itself.

## CM1 Execution

CM1 remains external to the repository. The current local launch path discovers configured
CM1 settings from the runtime home, environment variables, or local probes, stages required
runtime files from the configured CM1 run directory, and executes `cm1.exe` from the generated
package directory.

The local run manager tracks one active local CM1 process at a time. It records command,
process ID, timestamps, stdout/stderr log paths, exit code, output artifacts, and runtime
warnings on the run manifest.

The serial queue persists queue state in the runtime home, launches packaged runs one at a
time, refreshes the active run, and auto-ingests successful output-producing completed runs.
When ingest fails, the queue records the failure and leaves manual retry possible.

The trusted-LAN path is optional and bounded. The primary Cloud Chamber host generates the
package and remains the system of record. The worker receives a copied package, runs CM1,
returns output and logs to the primary host runtime home, and then local ingest handles the
result.

## Ingest, Results, And Storage

The current ingest path reads completed CM1 NetCDF model-output files with backend Python
code. Raw `.dat` and `.ctl` artifacts may be cataloged on the manifest, but NetCDF model-field
files are required for current ingest.

`result_metadata.json` is written inside the original run directory. Optional notebook state
is written to sibling `result_card.json`.

Results currently list cards by scanning:

```text
<runtime-home>/runs/*/result_metadata.json
```

Explore and visualization endpoints also rely on the original run directory and the NetCDF
paths referenced by result metadata. Deleting a run directory currently removes the package,
logs, CM1 output, result metadata, and notebook sidecar state for that result.

See [Ingest, Results, And Runtime Cleanup Lifecycle](INGEST_RESULTS_STORAGE_LIFECYCLE.md)
for the current lifecycle audit.

## Diagnostics And Visualization Payloads

Backend diagnostics currently derive cloud, vertical velocity, rain, reflectivity,
runtime-integrity, field-quality, selected-region, and output-product summaries where
the required fields exist.

Visualization endpoints return bounded backend-derived payloads for field catalogs,
view defaults, slices, point clouds, output-product options, profiles, time-height data,
time series, and selected-region summaries.

These payloads are not raw model output. They are current interpretations of CM1-derived
data intended for browser inspection.

## Runtime Boundaries

The runtime home defaults to `~/CloudChamber` unless overridden. Runtime-local data includes
settings, generated run packages, CM1 output, logs, cached sounding source data, queue state,
LAN-worker configuration, and local result metadata.

The repository must not track runtime-local data, CM1 source trees, CM1 executables, NetCDF
output, generated packages, `LANDUSE.TBL`, local settings, logs, screenshots, videos, traces,
or large processed visualization artifacts.

## Open Product Questions

The current architecture leaves several decisions unresolved:

- whether Build, Results, and Explore remain the long-term interface structure;
- whether filesystem-backed result metadata remains sufficient;
- whether observed soundings, candidate screening, local queueing, LAN execution, or specific
  initiation and forcing mechanisms remain product priorities;
- which current scenarios or run paths become supported cloud worlds;
- how visualization and process explanation are combined in the final experience.

Those decisions are outside this descriptive architecture snapshot.
