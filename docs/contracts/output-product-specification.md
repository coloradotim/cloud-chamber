# Output Product Specification

**Status:** Implemented contract

## Purpose

This contract documents the current implemented output-product behavior for
ingested CM1 results: runtime-local metadata, derived output-product manifests,
backend diagnostics, and bounded browser-facing visualization payloads.

## Authority Boundary

This is a current implementation contract. It does not define final product
architecture, final persistence, final visualization surfaces, or supported
Cloud Worlds or Recipes.

Current implementation terms such as Result, Result Card, Results, Explore, and
output product are subordinate to
`docs/product/APPLICATION_SEMANTICS.md`. Current code and tests remain the
source of truth for implemented behavior.

## Current Implemented Model

Current ingest accepts completed run manifests whose lifecycle state is
`completed` and whose product state is `completed_cm1_result`. NetCDF model-field
files named like `cm1out_<number>.nc` or `cm1out_<number>.nc4` are required for
ingest. Stats NetCDF files and raw CM1 `.dat` / `.ctl` artifacts may be
cataloged, but stats-only output is not enough for current field diagnostics.

Ingest writes these runtime-local records in the original run directory:

- `result_metadata.json`;
- `derived-products/output_product_manifest.json`;
- optional `result_card.json` when the editable Result Card state is updated.

`result_metadata.json` records run, scenario, input, observed-sounding,
`run_recipe`, recipe metadata, candidate-screening, pre-run-validation, output
file, diagnostic, runtime-integrity, field-quality, interesting-time, and
science-summary fields where available.

The output-product manifest is versioned as manifest version `1`. It records:

- `product_manifest_id`, `result_id`, `run_id`, optional `scenario_id`, and
  source model;
- source `result_metadata.json` and `run_manifest.json` paths when available;
- classified source outputs: model-output NetCDF, stats NetCDF, and raw CM1
  artifacts;
- a global output time index mapping each `time_index` to source file, source
  kind, local file index, time seconds/source value, and time caveats;
- cache metadata for the runtime-local derived-products directory;
- provenance and caveats;
- an optional embedded interesting-time product.

Interesting-time and science-summary records are derived from backend
diagnostics and output-time mapping. Current records include cloud, cloud-top,
cloud-water, updraft/downdraft, rain, reflectivity, latest-output, and
field-default-time evidence when the required diagnostics and fields exist.
Support states are `supported`, `fallback`, `unavailable`,
`unsupported_missing_fields`, and `unsupported_missing_diagnostic`.

Field catalogs expose recognized CM1 fields with raw and canonical field names,
display labels, units, dimensions, native-grid class, coordinate names,
capabilities, provenance, and caveats. Current recognized fields include cloud
water, vertical velocity, wind components, rain water aloft, water vapor,
temperature/potential temperature, pressure, accumulated surface rain,
reflectivity, surface fluxes, selected surface diagnostics, parcel-diagnostic
fields when present, and radiation tendency fields when present.

Current backend output-product payloads include:

- field catalogs;
- view defaults;
- bounded 2-D slices;
- thresholded point clouds for supported scalar fields;
- output-product catalogs;
- vertical profiles;
- time-height arrays;
- time-series arrays;
- selected-region diagnostics for point, column, and box requests.

## Behavioral Rules And Invariants

Raw NetCDF stays backend-owned. The browser receives JSON payloads produced by
backend code; `encoding=json` is the only supported browser-facing encoding for
current slice and point-cloud endpoints.

The output time index excludes stats files from model-field time mapping. When
all model-output files expose numeric time coordinates, the global index is
sorted by time. When times must be inferred, filename order is preserved and a
caveat is recorded. Missing, skipped, duplicate, or non-model files are recorded
as caveats where applicable.

Field quality is assessed by backend diagnostics for tracked fields and is
propagated into interesting-time, Result Card, and output-product payloads where
available. Missing fields are represented as unavailable/caveated behavior, not
as physically meaningful zero values.

Visualization payloads use native-grid views and aggregations. Current profile
aggregation methods are `domain_mean`, `domain_min`, `domain_max`, and
`selected_column`. Current time-height and time-series methods are
`cloud_fraction`, `domain_mean`, `domain_min`, and `domain_max` where supported
for the selected field.

Large output defaults may be metadata-based instead of full-field scans so that
Explore can open without scanning gigabytes of NetCDF first. Such defaults carry
caveats.

Deleting a managed runtime run directory deletes current package files, logs,
CM1 output, `result_metadata.json`, optional `result_card.json`, and derived
product files under that directory. Result deletion resolves `result_id` to the
run directory and requires explicit confirmation before deleting.

## Current Ownership And Interfaces

The backend owns ingest, NetCDF/xarray access, diagnostics, output-product
manifest generation, field catalogs, slices, point clouds, profiles,
time-height/time-series products, selected-region diagnostics, Result Cards,
and runtime cleanup.

The frontend owns current Build, Results, and Explore interaction and
presentation. It does not parse raw NetCDF and does not own scientific truth.

CM1 owns simulated atmospheric evolution for a given executable and
configuration. Runtime storage owns only current local files and cache state; its
location does not define product identity.

Current API routes include:

- `/api/results/ingest`;
- `/api/results`;
- `/api/results/{result_id}`;
- `/api/results/{result_id}/delete-preview`;
- `/api/results/{result_id}/delete`;
- `/api/results/{result_id}`;
- `/api/results/{result_id}/save`;
- `/api/results/{result_id}/visualization/fields`;
- `/api/results/{result_id}/visualization/defaults`;
- `/api/results/{result_id}/visualization/slice`;
- `/api/results/{result_id}/visualization/point-cloud`;
- `/api/results/{result_id}/output-products`;
- `/api/results/{result_id}/output-products/profile`;
- `/api/results/{result_id}/output-products/time-height`;
- `/api/results/{result_id}/output-products/time-series`;
- `/api/results/{result_id}/diagnostics/selected-region`;
- `/api/storage/inventory`;
- `/api/storage/delete-run`.

## Persistence Or Runtime Records

Current implemented records live under `<runtime-home>/runs/<run-id>/`. Results
are discovered by scanning `<runtime-home>/runs/*/result_metadata.json`. Explore
requires both discoverable result metadata and readable NetCDF paths referenced
by that metadata.

`result_card.json` stores editable current Result Card state: name, tags, notes,
and compatibility saved/protected fields. It is a sidecar to current result
metadata, not a final product persistence model.

## Terminology Mapping

- **Result**: current API/UI term for ingested result metadata and its card
  projection; not the product center.
- **Result Card**: current UI/API projection over `result_metadata.json` plus
  optional `result_card.json`; not a canonical saved view or Experiment.
- **Results**: current UI surface for locating ingested output.
- **Explore**: current UI surface for inspecting backend-derived visualization
  payloads and diagnostics.
- **Output product**: current backend-derived payload or manifest for bounded
  browser consumption; not raw model data.
- **Model data**: CM1-produced output files, primarily NetCDF model-field files.
- **Diagnostic**: backend-derived scientific or quality summary, not raw CM1
  state.
- **Run**: current execution/package machinery beneath a Simulation.
- **Simulation**: product-semantic term for the evolving modeled cloud or cloud
  field the user watches; current output records can support viewing a
  Simulation but do not define the final product object.

## Evidence Map

Implementation evidence:

- `app/backend/cloud_chamber/result_ingest.py`;
- `app/backend/cloud_chamber/output_products.py`;
- `app/backend/cloud_chamber/result_diagnostics.py`;
- `app/backend/cloud_chamber/visualization_data.py`;
- `app/backend/cloud_chamber/selected_region_diagnostics.py`;
- `app/backend/cloud_chamber/result_cards.py`;
- `app/backend/cloud_chamber/runtime_storage.py`;
- `app/backend/cloud_chamber/run_manifest.py`;
- `app/backend/cloud_chamber/app.py`.

Frontend consumers:

- `app/frontend/src/App.tsx`;
- `app/frontend/e2e/mocked-smoke/build-results-explore.spec.ts`.

Tests:

- `app/backend/tests/test_result_ingest.py`;
- `app/backend/tests/test_output_products.py`;
- `app/backend/tests/test_result_diagnostics.py`;
- `app/backend/tests/test_visualization_data.py`;
- `app/backend/tests/test_selected_region_diagnostics.py`;
- `app/backend/tests/test_result_cards.py`;
- `app/backend/tests/test_runtime_storage.py`;
- `app/backend/tests/test_app.py`;
- `app/frontend/src/App.test.tsx`.

## Known Implementation Limits

Current result discovery is filesystem-coupled to run directories under the
runtime home. There is no separate database-backed result index.

Current output products are JSON payloads and runtime-local derived records.
There is no implemented Render Studio, Diagnostics Lab, VAPOR/ParaView/VTK/Zarr
export path, browser-side raw NetCDF parser, or future binary/chunked product
format in this contract.

Field availability, field quality, interesting times, and diagnostics depend on
the fields produced by the run and on backend diagnostic support. Unsupported
or missing fields produce unavailable/caveated payloads.

Current cleanup deletes the managed run directory. The implementation records
the storage coupling; it does not choose a future archive or metadata-only
retention model.

## Non-Implications

This contract does not approve final storage, cleanup, rendering, export,
notebook, comparison, database, or compute architecture.

It does not make Results or Result Cards the product center, does not define a
Cloud World, does not approve a Recipe, and does not make an ingested record or
notebook sidecar an Experiment.
