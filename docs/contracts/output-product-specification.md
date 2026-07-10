# Cloud Chamber Output Product Specification

Issue: #214

Status: v1 product/data contract

Source context:

- #210 output and visualization architecture research
- #215 deep-output Explore timeout fix
- current NetCDF ingest, Result Card, Explore, Storage, and selected-region
  diagnostics behavior

This specification defines what Cloud Chamber may produce from completed CM1
output before more rendering, diagnostics, export, or UI surfaces are added.
It is a contract between backend ingest, Results, Explore, Storage, future
Diagnostics Lab, future Render Studio, docs, and tests.

It does not implement new output products.

## Executive Contract

CM1 NetCDF output remains the source data. Cloud Chamber output products are
derived local records or bounded payloads that make completed CM1 runs easier
to inspect, explain, compare, render, cache, or export.

The browser must not parse raw NetCDF. It should request backend-owned,
provenance-labeled products with explicit size, time, field, and processing
boundaries.

The next implementation should create:

```text
output product manifest skeleton
+ robust file/time index mapping
+ interesting-time products
+ profile/time-height product definitions
```

That should happen before adding new renderer dependencies, Render Studio,
Diagnostics Lab, or external export workflows.

## Artifact Classes

| Artifact class | What it is | Source of truth? | Typical owner | Browser access |
| --- | --- | --- | --- | --- |
| Raw CM1 NetCDF output | `cm1out_*.nc` model-field files and `cm1out_stats.nc` stats files written by CM1 | Yes, for model fields | CM1 / local runtime directory | Never directly |
| Runtime logs/manifests | `run_manifest.json`, `case_manifest.json`, `stdout.log`, `stderr.log`, package inputs, runtime checklist | Yes, for run configuration and execution state | Build / local run manager | Only summarized through API |
| Result metadata / notebook state | `result_metadata.json` plus optional `result_card.json` | Source for ingested metadata and notebook state, not raw model values | Ingest / Results | Through Results API |
| Output product manifest | Generated index of derived products, time mapping, cache keys, and provenance | Source for derived-product availability, not raw model values | Backend product builder | Through bounded API summaries |
| Derived scientific products | Diagnostics, profiles, time-height arrays, selected-place summaries, interesting times | Derived from raw output and metadata | Backend diagnostics/product layer | Bounded JSON or future binary payloads |
| Visualization-ready payloads | Field catalogs, slices, point clouds, defaults, selected-region evidence | Derived request payloads for Explore | Backend visualization/data layer | Yes, bounded and provenance-labeled |
| Future render-ready products | Multiresolution volumes, transfer-function metadata, scalar/signed-flow arrays | Derived, cacheable render inputs | Future Render Studio backend | Only through render APIs, not raw NetCDF |
| External export bundles | VAPOR, ParaView/VTK, xarray/hvPlot/Panel, or future Zarr sidecars | Derived/export copies, not source truth | Future export jobs | Download/open workflow only |

## Source Of Truth And Browser / Backend Boundary

CM1 is the high-fidelity model. Raw CM1 NetCDF files, run manifests, and logs
are the durable local evidence for what ran and what CM1 produced.

Cloud Chamber may create derived products, but those products must remain
clearly labeled as:

- diagnostics derived from CM1 output;
- visualization interpretations of CM1 output;
- cached local products that can become stale or be deleted;
- export bundles for external tools.

The backend owns:

- NetCDF/xarray access;
- file/time mapping;
- field selection;
- finite/non-finite checks;
- unit and coordinate interpretation;
- downsampling and bounded payload construction;
- provenance and caveat construction.

The browser owns:

- user selection state;
- requesting one bounded product at a time;
- rendering received payloads;
- displaying provenance and caveats;
- never treating visualization as a new physical source of truth.

The browser must not:

- open raw NetCDF files;
- infer multi-file time mapping on its own;
- compute global scientific diagnostics from raw field arrays;
- silently invent fields, units, coordinates, or physical explanations.

## Multi-File Output And Time-Index Mapping

CM1 runs can produce many model-output NetCDF files. Cloud Chamber must treat
the model run as one time sequence, even when each output time is written to a
separate file.

The output product manifest should define a global output-time index:

```json
{
  "time_index": 12,
  "time_seconds": 7200.0,
  "source_file": "<runtime-home>/runs/<run-id>/cm1out_000013.nc",
  "source_file_kind": "model_output_netcdf",
  "local_time_index": 0,
  "time_source": "netcdf_time_coordinate",
  "time_caveats": []
}
```

Rules:

- `cm1out_stats.nc` is not a model-field time-series file.
- Model-output files must be sorted by direct time coordinate when available,
  otherwise by validated output index.
- `time_index` is the global model-output index used by Results, Explore,
  comparison views, diagnostics, and future renderer products.
- `local_time_index` is the index inside the source file after the global time
  is resolved.
- Selected timestep requests must resolve through this mapping before any
  NetCDF file is opened.
- A selected timestep request should open only the required file when the
  mapping proves that the file contains that timestep.
- If files contain multiple timesteps, the mapping should preserve both global
  and local indices.
- Missing, corrupt, skipped, inferred, duplicated, or non-monotonic times must
  become caveats.

### #215 Performance Lesson

Field catalogs and default view state should be served from ingested metadata or
bounded derived products whenever possible.

Basic Explore startup must not trigger raw full-sequence NetCDF parsing. The
field catalog, field availability, broad time range, and default-interesting
time should be metadata-backed or product-backed. Slice and point-cloud
requests for a selected time should use the explicit file/time mapping to open a
bounded source, not concatenate the full output sequence per request.

## Output Product Manifest

Cloud Chamber should introduce an output product manifest as a generated,
local, rebuildable index for output-derived products.

It is distinct from:

- `run_manifest.json`, which records generated package and execution state;
- `result_metadata.json`, which records ingested result metadata and first-pass
  diagnostics;
- `result_card.json`, which records notebook/user state.

Draft manifest shape:

```json
{
  "manifest_version": 1,
  "product_manifest_id": "output-products-<result-id>",
  "result_id": "result-<run-id>",
  "run_id": "<run-id>",
  "scenario_id": "baseline-shallow-cumulus",
  "source_model": "CM1",
  "source_result_metadata_path": ".../result_metadata.json",
  "source_run_manifest_path": ".../run_manifest.json",
  "source_raw_outputs": {
    "model_output_files": [],
    "stats_files": [],
    "raw_cm1_artifacts": []
  },
  "time_index": [],
  "field_catalog_product": {},
  "interesting_time_product": {},
  "products": [],
  "cache": {
    "product_root": ".../derived-products",
    "cache_key": "result-metadata-and-source-output-fingerprint",
    "invalidated": false
  },
  "provenance": {},
  "caveats": [],
  "created_at": "2026-06-29T00:00:00Z",
  "updated_at": "2026-06-29T00:00:00Z"
}
```

The manifest should record what products exist, how they were made, what source
files they depend on, and how to invalidate or delete them. It should not copy
large raw NetCDF files into the repository or make derived products appear more
authoritative than CM1 output.

Implementation note: the first backend foundation for this contract lives in
`cloud_chamber.output_products`. Ingested results now write a runtime-local
`derived-products/output_product_manifest.json` beside the run directory's
result metadata. That manifest currently focuses on source output references
and global file/time index mapping; later product records should build on it
rather than inventing separate time addressing.

## Product Type Decisions

| Product type | When computed | Format now | Future format | Size class | API owner | Frontend consumer |
| --- | --- | --- | --- | --- | --- | --- |
| File/time index | At ingest or first product-build pass | JSON | JSON | small | backend ingest/product layer | Results, Explore, Storage, tests |
| Interesting times | At ingest or first product-build pass | JSON | JSON | small | diagnostics/product layer | Results, Explore, future Compare |
| Field catalog | At ingest or metadata-backed request | JSON | JSON | small | visualization/product layer | Explore, future Compare, future Render Studio |
| Slice products | Lazy request, optionally cached | JSON numeric arrays | binary or chunked arrays for large slices | small to medium | visualization API | Explore, future Compare |
| Vertical profiles | Lazy or cached from selected fields | JSON arrays | binary/chunked for long sequences | small to medium | diagnostics/product API | future Diagnostics Lab, Explore evidence |
| Time-height products | Cached derived product | JSON for tiny fixtures | binary/chunked arrays | medium | diagnostics/product API | future Diagnostics Lab |
| Selected-point/column products | Lazy bounded request, optionally cached | JSON summaries/arrays | JSON plus binary arrays if needed | small to medium | selected-region diagnostics API | Explore `What happened here?` |
| Render-ready products | Cached explicit build | none yet | binary float32, multiresolution, or chunked store | medium to large | future render-product API | future Render Studio |
| External export bundles | Explicit user/export job | none yet | tool-specific files | medium to large | future export API/job | external apps |

## Interesting-Time Products

Interesting-time products provide small, reusable time landmarks for Results,
Explore, comparison, diagnostics, and future time-lapse rendering.

Near-term interesting times:

- first cloud;
- max `qc`;
- max updraft `w`;
- min downdraft `w`;
- highest cloud top;
- rain-water onset from `qr`;
- max rain water aloft from `qr`;
- max `dbz`;
- max surface rain;
- selected-time fallback such as latest output.

Each interesting time should include:

```json
{
  "key": "max_qc",
  "label": "Max cloud water",
  "time_index": 3,
  "time_seconds": 2700.0,
  "field": "qc",
  "value": 0.0028,
  "units": "kg/kg",
  "source": "diagnostics.max_qc",
  "confidence": "supported",
  "caveats": []
}
```

Interesting-time products should not require opening the full NetCDF sequence
when a user merely opens Explore. They should be computed from existing
diagnostics, stored product summaries, or a bounded product-build pass.

The first implementation stores an `interesting_time_product` in the runtime
output product manifest and mirrors compact fields into `result_metadata.json`:
`interesting_times`, `default_time_by_field`, `science_summary`, and
`interesting_time_caveats`. It uses the output-product manifest time index plus
existing CM1-derived diagnostics; it does not build a second time index and it
does not ask the browser to parse NetCDF. Missing fields, no-event outcomes,
and diagnostics that are not implemented yet are represented explicitly with
support states such as `unavailable`, `unsupported_missing_fields`, and
`unsupported_missing_diagnostic` rather than silently falling back to a
misleading cloud/rain-water landmark.

Deep Convection Trial results extend the same product with backend-owned
summary fields for deep-cloud formation, first deep-convection time, strong
updraft detection, cloud top, rain-water onset, max `qr`, and the default Explore
time. Unsupported severe-storm diagnostics such as reflectivity maxima,
surface-rain maxima, updraft-depth proxy, cold-pool proxy, and near-surface
theta perturbation proxy must be recorded as unavailable or caveated until a
supported backend diagnostic exists. When candidate-screening metadata is
present, result metadata may include a compact `candidate_hypothesis_comparison`
with `Screened as`, `Ran as`, `CM1 outcome`, match state, evidence, and caveats.
The comparison uses simple v1 rules and remains a post-run interpretation of
CM1 output, not proof that the observed sounding was validated in advance.

## Field Catalog Products

The field catalog answers:

```text
What fields are available for this result, and what can Cloud Chamber safely do
with each one?
```

The field catalog should include:

- raw field name;
- canonical field name;
- display name;
- units;
- dimensions;
- coordinate names;
- native grid;
- shape;
- time availability;
- direct vs inferred coordinate caveats;
- supported product capabilities:
  - slice;
  - point cloud;
  - selected point;
  - selected column;
  - profile;
  - time-height;
  - render-ready candidate;
  - export candidate;
- frontend consumer guidance;
- provenance.

Example:

```json
{
  "raw_field_name": "qc",
  "canonical_field_name": "cloud_water",
  "display_name": "Cloud water",
  "units": "kg/kg",
  "dimensions": ["time", "zh", "yh", "xh"],
  "native_grid": "cell_center",
  "coordinates": {"time": "time", "z": "zh", "y": "yh", "x": "xh"},
  "capabilities": {
    "slice": true,
    "point_cloud": true,
    "selected_point": true,
    "selected_column": true,
    "profile": true,
    "time_height": true,
    "render_ready_candidate": true,
    "external_export_candidate": true
  },
  "provenance": {
    "source_model": "CM1",
    "processing_method": "ingested_result_metadata_field_catalog"
  },
  "caveats": []
}
```

## Slice Products

Slice products are the current everyday Explore payload. They provide one
native-grid 2-D field view for one result, field, global time index,
orientation, and level/index.

Supported MVP orientations:

- horizontal layer;
- vertical `x-z` slice;
- vertical `y-z` slice;
- surface 2-D field when the field is already surface-native.

Rules:

- Use native grids first.
- Do not interpolate staggered fields unless a future product explicitly says
  so.
- Preserve native coordinate names and units.
- Include display-friendly coordinate values where safe.
- Include min, max, mean, finite count, non-finite count, and caveats.
- Include the global `time_index`, `time_seconds`, source file, and local time
  index when available.
- JSON arrays are acceptable for MVP-size slices.
- Larger slices may require binary arrays or a chunked product later.

## Vertical Profile Products

Vertical profile products summarize a field as a function of height for a
selected time, selected column, region, or domain.

Candidate profiles:

- domain mean/min/max `qv`, temperature, potential temperature, pressure;
- selected-column `qc`, `qr`, `qv`, `w`, temperature, potential temperature;
- profile at selected point/column for `What happened here?`;
- cloud-base/cloud-top-relevant vertical summaries.

Profile products should preserve:

- field units;
- vertical coordinate units;
- height conversion where safe;
- selected horizontal coordinate/index;
- aggregation method;
- caveats for missing or inferred coordinates.

## Time-Height Products

Time-height products summarize evolution across output times and vertical
levels. They are the likely bridge from Explore to a future Diagnostics Lab.

Candidate time-height products:

- cloud fraction by time and height;
- max `qc` by time and height;
- max/min `w` by time and height;
- domain mean `qv` by time and height;
- domain mean temperature/potential temperature by time and height;
- selected-column cloud-water time-height;
- cloud-base/cloud-top time series.

Rules:

- These products should be computed by backend jobs or bounded product builders,
  not by the browser.
- They should include direct/inferred time caveats and coordinate metadata.
- They should be cacheable because they may require reading the full sequence.
- JSON is acceptable for tiny fixtures; binary/chunked formats should be
  considered for real deep outputs.

## Selected-Point And Selected-Column Products

Selected-place products power the user-facing question:

```text
What happened here?
```

Supported or near-term selections:

- selected point from a 2-D slice;
- selected vertical column;
- selected small 2-D region;
- selected 3-D box later;
- selected cloud object later;
- selected updraft core later.

Selected-point product requirements:

- selected field and value;
- selected time;
- selected native-grid indices;
- selected physical coordinates;
- local `qc`, `w`, and optional `qr` summaries;
- comparison to domain where practical;
- conservative explanation label;
- caveats;
- source fields and processing method.

Selected-column product requirements:

- column profile at selected time;
- local time history where practical;
- first local cloud time;
- local max `qc`;
- local max/min `w`;
- local rain-water onset when `qr` exists;
- cloud-base/cloud-top evidence where supported.

These products should not become cloud-object tracking unless a future issue
adds object definitions and validation.

## Visualization-Ready Payloads

Visualization-ready payloads are small request/response products consumed by
Explore and comparison views.

Current examples:

- field catalog;
- view/defaults payload;
- slice payload;
- point-cloud payload;
- selected-region diagnostics payload.

Contract:

- bounded in size;
- backend-prepared;
- provenance-labeled;
- caveated;
- no browser NetCDF parsing;
- no silent interpolation;
- no hidden full-sequence reads for simple startup state.

The endpoint implementation may be lazy, cached, or metadata-backed. The
payload contract should remain stable even if the backend later introduces an
output product manifest and caches.

## Future Render-Ready Products

Render-ready products are future artifacts for Render Studio or external
renderers. They are not required for current Explore.

Candidate render-ready products:

- thresholded scalar point sets;
- downsampled scalar volumes;
- multiresolution `qc` volumes;
- rain-water point/volume products;
- reflectivity render arrays;
- signed `w` updraft/downdraft products;
- transfer-function metadata;
- camera/render preset metadata;
- provenance and interpretation labels.

Render-ready products must state:

- source field(s);
- time index and time seconds;
- grid and coordinate assumptions;
- downsampling or thresholding method;
- color/opacity transfer function;
- whether the payload is exact, approximate, downsampled, or interpreted.

Explore may keep using lightweight point and slice payloads. Render Studio, if
built later, should consume explicit render-ready products rather than direct
raw CM1 NetCDF.

## Future Diagnostics Lab Boundary

Diagnostics Lab is a future analysis surface for profiles, time-height plots,
field time series, and process evidence.

It should consume:

- interesting-time products;
- field catalog products;
- vertical profile products;
- time-height products;
- selected-column products;
- process-diagnostics products.

It should not be implemented by making the React browser parse NetCDF or by
turning Explore into a broad plotting cockpit.

Python/xarray/hvPlot/Panel sidecar prototypes may be useful research later, but
they should not become product dependencies until the product contract and
workflow are accepted.

## Future Render Studio Boundary

Render Studio is a future optional visual-rendering surface. It is not the
source of truth and should not displace Explore's scientific inspection role.

Render Studio should depend on:

- output product manifest;
- render-ready products;
- explicit cache and invalidation behavior;
- provenance and interpretation labels;
- browser memory constraints;
- external renderer prototype evidence.

Do not add vtk.js, trame, VAPOR, ParaView, Zarr, hvPlot, or Panel dependencies
as part of this spec.

## External Export Bundle Candidates

External export bundles are opt-in derived products for tool-specific
workflows.

Candidate bundles:

- VAPOR open/export package;
- ParaView/VTK structured-grid package;
- xarray analysis sidecar;
- hvPlot/Panel diagnostics sidecar;
- future Zarr derived store.

Export bundles should record:

- source result ID and run ID;
- source raw files;
- fields included;
- times included;
- coordinate assumptions;
- conversion method;
- generated file paths;
- external tool/version target if known;
- caveats;
- cleanup behavior.

They should be prototypes before Cloud Chamber commits to embedding a heavy
renderer stack.

## Cache, Storage, Invalidation, And Cleanup

Output products live under the configured runtime home, not in the repository.

They should be treated as generated local artifacts:

- safe to rebuild when raw outputs and result metadata still exist;
- eligible for cleanup through Storage policy;
- never committed to git;
- protected only when product policy explicitly says so.

The output product manifest should record a cache key or fingerprint derived
from:

- result metadata version;
- product manifest version;
- source raw output file list;
- source file sizes and modified times, or stronger hashes where practical;
- product parameters such as field, time, threshold, orientation, level, and
  downsampling method.

Invalidation rules:

- If `result_metadata.json` changes, derived products should be considered
  stale unless their cache key still matches.
- If source raw output files are missing or changed, dependent products should
  be invalidated.
- If product schema/version changes, products should be rebuilt or marked
  stale.
- If a run directory is deleted, products inside it are deleted too.
- If products later move outside the run directory, Storage must still show the
  relationship and cleanup impact clearly.

Storage should show output-product artifacts as generated local data associated
with a run/result. Results should not become a deletion surface. Explore should
handle missing or stale products with retry/rebuild states when implementation
exists.

## Provenance And Caveats

Every output product must carry enough provenance to answer:

```text
What CM1 run and result did this come from?
Which raw files and fields contributed?
What time and coordinate mapping was used?
What processing was applied?
What is direct model output versus derived interpretation?
What caveats should the user know?
```

Minimum provenance:

- source model;
- run ID;
- result ID;
- scenario ID;
- raw source file(s);
- raw field name(s);
- canonical field name(s);
- time index and time seconds;
- coordinate names and units;
- processing method;
- product version;
- rendering method when visual;
- source warnings/caveats.

Common caveats:

- inferred time coordinate;
- inferred units;
- missing target field;
- non-finite values detected;
- skipped/corrupt file;
- downsampled payload;
- native-grid view, no interpolation;
- visualization interpretation, not source truth;
- runtime stderr warning surfaced from CM1.

## Results, Explore, And Storage Consumers

Results should consume small result metadata, notebook state, diagnostics
summaries, interesting-time summaries, and output-product availability. It
should not fetch large field payloads just to list notebook entries.

Explore should consume one selected result and one bounded field/time/selection
payload at a time. It may use metadata-backed defaults and interesting-time
products to open at useful frames. It should not parse raw NetCDF or request a
full sequence just to load field availability.

Storage should inventory raw outputs, logs, result metadata, result-card state,
and generated output products as local runtime artifacts. It should explain
which artifacts are source data, which are derived/cache, and what cleanup will
remove.

Future diagnostics and rendering surfaces should build on the output product
manifest rather than inventing independent file discovery rules.

## First Implementation Recommendation

The first issue after this spec should implement:

```text
output product manifest skeleton
+ robust time index / interesting-time product
+ vertical profile and time-height product definitions
```

Suggested scope:

- define a small output product manifest model;
- write or expose a file/time mapping derived from existing result metadata and
  model-output files;
- populate interesting times from existing diagnostics where available;
- define profile/time-height product records without computing heavy products;
- add tests using tiny synthetic fixtures only;
- update docs to point Results, Explore, Storage, future Diagnostics Lab, and
  future Render Studio at the manifest.

Non-goals for that first implementation:

- no new renderer dependencies;
- no UI redesign;
- no external export implementation;
- no heavy full-run derived arrays unless test fixtures prove the shape;
- no raw NetCDF parsing in the browser.

## PM Decisions Needed

These decisions should be made before or during the first implementation issue:

- Where should `output_product_manifest.json` live: inside each run directory,
  inside a sibling derived-products directory, or both via pointer?
- Should derived products be rebuilt automatically on demand, or only through
  explicit product-build actions?
- Which derived products should be retained if a future archive or keep-local-output mode is introduced?
- What is the first supported binary/chunked payload format after JSON slices
  become too large?
- Which fields are MVP profile/time-height fields?
- Should external VAPOR/ParaView/xarray export be an export action, an external
  open action, or a separate local sidecar workflow?
- What UI language should distinguish "raw output", "derived product", and
  "render-ready product" without overwhelming the user?

## Acceptance Checklist

- Raw CM1 NetCDF output remains the source data.
- Runtime logs/manifests remain distinct from result metadata.
- Result metadata/notebook state remains distinct from output products.
- Output product manifest is a generated local index, not a new physical source
  of truth.
- Derived scientific products are labeled with provenance and caveats.
- Visualization-ready payloads are bounded backend products.
- Future render-ready products are separated from current Explore payloads.
- External export bundles are future derived artifacts, not embedded product
  dependencies.
- Multi-file output uses explicit global time-index mapping.
- Basic field catalog/default loading must not read the full NetCDF sequence.
- Selected time requests resolve through file/time mapping.
- Browser code does not parse raw NetCDF.
- Storage and cleanup understand generated products as local artifacts.
- Diagnostics Lab and Render Studio boundaries remain future contracts.
