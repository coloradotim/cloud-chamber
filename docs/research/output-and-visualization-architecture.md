# Output And Visualization Architecture Research Spike

Issue: #210

Status: research memo / PM input only

This memo defines a proposed output and visualization architecture for Cloud
Chamber before adding more renderer features. It does not implement UI, add
renderer dependencies, change CM1 package generation, change ingest behavior,
run CM1, or create follow-up GitHub issues.

## Executive Recommendation

Draft PM input, not a final product decision:

Cloud Chamber should keep **scientific inspection** and **visual rendering** as
two linked but separate layers.

Recommended next move:

```text
1. Keep Explore as the everyday scientific inspection surface.
2. Expand backend output products before expanding renderer ambition.
3. Add time/field/profile products that make realistic-input runs explainable.
4. Prototype external export/open workflows before committing to a heavy
   embedded render stack.
5. Defer Render Studio and Diagnostics Lab UI until the derived product
   contracts exist.
```

Avoid for now:

- do not keep stretching the current viewer into a production renderer studio;
- do not parse raw NetCDF in the browser;
- do not add VAPOR, ParaView, vtk.js, trame, hvPlot, Panel, or Zarr
  dependencies in product code yet;
- do not implement Bench Mode UI, GIS/map inputs, or new scenario families as
  part of output architecture;
- do not make beautiful rendered clouds the source of truth.

The near-term architecture should be:

```text
Raw CM1 NetCDF output
  -> Python/xarray backend
  -> small result metadata and diagnostics
  -> lazy visualization-ready slices, point clouds, profiles, time series
  -> optional cached derived artifacts
  -> React Explore for exact inspection
  -> later Render Studio / Diagnostics Lab after contracts stabilize
```

The first concrete implementation step should be an output product contract:
define what fields, time indices, summaries, profiles, and cached artifacts
Cloud Chamber produces from a completed CM1 run. Rendering upgrades should come
after that contract, not before it.

## Evidence Sources Inspected

Local/source evidence:

- CM1 namelist guide: `/Users/timpeterson/cm1r21.1/README.namelist`
- Cloud Chamber ingest metadata:
  `app/backend/cloud_chamber/result_ingest.py`
- Cloud Chamber diagnostics:
  `app/backend/cloud_chamber/result_diagnostics.py`
- Cloud Chamber selected-region diagnostics:
  `app/backend/cloud_chamber/selected_region_diagnostics.py`
- Cloud Chamber visualization-ready payloads:
  `app/backend/cloud_chamber/visualization_data.py`
- Cloud Chamber API routes:
  `app/backend/cloud_chamber/app.py`
- Cloud Chamber Explore / true 3-D frontend:
  `app/frontend/src/App.tsx` and `app/frontend/src/True3DViewer.tsx`
- Upstream realistic-input research:
  `docs/research/realistic-les-input-architecture.md`
- True 3-D architecture decision:
  `docs/true-3d-viewer-architecture-decision.md`
- Roadmap and product docs:
  `docs/cloud-chamber-product-spec.md`,
  `docs/architecture-and-data-model.md`,
  `docs/roadmap-and-issues.md`,
  `docs/testing-and-validation.md`,
  `docs/product-vision.md`
- GitHub issues inspected: #80, #112, #183, #187, #210.

External documentation inspected:

- VAPOR documentation:
  <https://ncar.github.io/VaporDocumentationWebsite/index.html>
- VAPOR natively supported data formats:
  <https://vapordocumentationwebsite.readthedocs.io/en/latest/dataFormatRequirements/nativelySupportedDataFormats.html>
- ParaView documentation:
  <https://docs.paraview.org/en/latest/>
- ParaView volume rendering and time/animation docs:
  <https://docs.paraview.org/en/latest/UsersGuide/displayingData.html>,
  <https://docs.paraview.org/en/latest/UsersGuide/animation.html>
- vtk.js documentation:
  <https://kitware.github.io/vtk-js/docs/>,
  <https://kitware.github.io/vtk-js/api/Rendering_Core_Volume.html>
- trame documentation:
  <https://kitware.github.io/trame/>
- xarray documentation:
  <https://docs.xarray.dev/en/stable/>
- hvPlot documentation:
  <https://hvplot.holoviz.org/>
- Panel documentation:
  <https://panel.holoviz.org/>
- Zarr documentation:
  <https://zarr.readthedocs.io/en/stable/>

## Current Cloud Chamber Output / Visualization Support

### Confirmed Current Support

Cloud Chamber currently treats NetCDF model-output files as the preferred ingest
source. Result ingest classifies `cm1out_*.nc` files as model-output files,
separates `cm1out_stats.nc`, opens the model-output sequence with xarray, and
writes `result_metadata.json` next to the run manifest. See
`app/backend/cloud_chamber/result_ingest.py:23-25`,
`app/backend/cloud_chamber/result_ingest.py:85-132`,
`app/backend/cloud_chamber/result_ingest.py:180-203`, and
`app/backend/cloud_chamber/result_ingest.py:214-250`.

Result metadata currently records:

- run/result/scenario identifiers;
- controls and run-size preset;
- raw CM1 artifact paths;
- NetCDF model-output paths;
- stats NetCDF paths;
- skipped NetCDF paths;
- dimensions, coordinates, variables, detected fields, grid shape;
- time coordinate metadata;
- warnings and caveats;
- first-pass diagnostics and process diagnostics.

See `app/backend/cloud_chamber/result_ingest.py:41-79` and
`app/backend/cloud_chamber/result_ingest.py:253-329`.

First-pass diagnostics currently compute:

- cloud formed;
- first cloud time;
- cloud base/top;
- max `qc`;
- `qc` max time series;
- cloud fraction time series;
- max/min `w`;
- `w` max/min time series;
- optional `qr` rain summary.

See `app/backend/cloud_chamber/result_diagnostics.py:314-327`,
`app/backend/cloud_chamber/result_diagnostics.py:343-403`,
`app/backend/cloud_chamber/result_diagnostics.py:406-457`, and
`app/backend/cloud_chamber/result_diagnostics.py:460-496`.

Process diagnostics currently classify conservative Thermal Fate states from
available diagnostics and fields. Moisture/saturation, buoyancy, cap/inversion,
deep breakthrough, and precipitation feedback are mostly candidate or
unsupported placeholders until more fields and derived diagnostics exist. See
`app/backend/cloud_chamber/result_diagnostics.py:133-292`.

Visualization-ready data is backend-owned. The module states that raw
NetCDF/xarray access stays on the backend and the frontend receives small,
provenance-labeled payloads. See
`app/backend/cloud_chamber/visualization_data.py:1-5`.

The current field map includes:

```text
qc, w, qr, qv, t/temp/temperature, th/theta, rain, dbz
```

`qc`, `qr`, `qv`, `dbz`, and surface `rain` can produce scalar point-cloud
payloads. `w` is explicitly slice-only until signed-flow rendering is added.
Temperature/potential-temperature fields are slice-capable, not current 3-D
point-cloud fields. See `app/backend/cloud_chamber/visualization_data.py:27-43`.

The API exposes:

- `GET /api/results/{result_id}/visualization/fields`
- `GET /api/results/{result_id}/visualization/defaults`
- `GET /api/results/{result_id}/visualization/slice`
- `GET /api/results/{result_id}/visualization/point-cloud`
- `GET /api/results/{result_id}/diagnostics/selected-region`

See `app/backend/cloud_chamber/app.py:214-335`.

The current slice API returns JSON numeric 2-D slices and records native-grid
selection, coordinate units, shape, dimension order, stats, provenance, and
caveats. It handles 3-D fields and surface 2-D fields. See
`app/backend/cloud_chamber/visualization_data.py:572-710`.

The current point-cloud API returns thresholded native-grid scalar points with
coordinate extents, min/max/mean, finite/non-finite counts, active vertical
range, max-value location, deterministic stride downsampling, and provenance.
See `app/backend/cloud_chamber/visualization_data.py:307-445`.

Selected-region diagnostics support point, column, and box request shapes, but
the current UI primarily uses selected slice cells. The backend computes bounded
local summaries for `qc`, `w`, and optional `qr`, and explicitly labels the
payload as a native-grid summary rather than cloud-object tracking. See
`app/backend/cloud_chamber/selected_region_diagnostics.py:1-5`,
`app/backend/cloud_chamber/selected_region_diagnostics.py:33-56`,
`app/backend/cloud_chamber/selected_region_diagnostics.py:82-105`, and
`app/backend/cloud_chamber/selected_region_diagnostics.py:143-199`.

The frontend Explore workspace is one selected-result surface. It renders the
selected result summary and a unified visualizer scene shell. See
`app/frontend/src/App.tsx:1786-1803`.

The true 3-D viewer uses Three.js directly in an isolated component. It renders
a domain scene, scalar point layer, slice plane, selected point marker, camera
controls, field legend, and provenance. See
`app/frontend/src/True3DViewer.tsx:122-171`,
`app/frontend/src/True3DViewer.tsx:173-281`, and
`app/frontend/src/True3DViewer.tsx:283-396`.

The current Explore shell already encodes scalar visualization modes for `qc`,
`qr`, `qv`, `dbz`, and surface `rain`, while treating temperature/theta fields
as slice-only. See `app/frontend/src/App.tsx:3475-3564`.

### Current Limitations

Cloud Chamber does not yet have:

- an output product manifest distinct from result metadata;
- cached derived visualization artifacts;
- profile products;
- time-height products;
- domain-mean vertical-profile diagnostics;
- selected-point time history;
- selected-column time history;
- render-ready volumes;
- binary array transport for large visualization products;
- a dedicated Diagnostics Lab;
- a dedicated Render Studio;
- external VAPOR/ParaView export/open workflow;
- 3-D signed `w` rendering.

The current implementation is a strong scientific-inspection scaffold, but it
should not be treated as the long-term realistic renderer architecture.

## CM1 Output Fields And Diagnostics To Prioritize

CM1 confirms NetCDF output via `output_format = 2`, and one-file-per-output-time
via `output_filetype = 2`. It also warns that NetCDF can be inefficient for very
large processor counts and describes GrADS/binary plus conversion for very large
MPI runs. See `/Users/timpeterson/cm1r21.1/README.namelist:1237-1272`.

CM1 documents a broad output field surface:

- surface rain and swaths:
  `/Users/timpeterson/cm1r21.1/README.namelist:1284-1310`
- surface fluxes, surface parameters, surface diagnostics:
  `/Users/timpeterson/cm1r21.1/README.namelist:1318-1328`
- heights, base state, potential temperature, pressure, density:
  `/Users/timpeterson/cm1r21.1/README.namelist:1329-1352`
- TKE and SGS diffusivity/viscosity:
  `/Users/timpeterson/cm1r21.1/README.namelist:1353-1357`
- water vapor, hydrometeors, reflectivity, buoyancy:
  `/Users/timpeterson/cm1r21.1/README.namelist:1359-1371`
- u/v/w winds and interpolation options:
  `/Users/timpeterson/cm1r21.1/README.namelist:1375-1390`
- vorticity, potential vorticity, updraft helicity, tendencies:
  `/Users/timpeterson/cm1r21.1/README.namelist:1391-1419`
- CAPE, CIN, LCL, LFC, precipitable water, liquid/cloud water path:
  `/Users/timpeterson/cm1r21.1/README.namelist:1421-1432`
- budget variables:
  `/Users/timpeterson/cm1r21.1/README.namelist:1434-1454`
- domain-wide diagnostics in CF-compliant NetCDF:
  `/Users/timpeterson/cm1r21.1/README.namelist:1753-1765`

### Priority Table

| Product group | Field or diagnostic | CM1 support / likely source | Current Cloud Chamber support | Raw or derived | Priority |
| --- | --- | --- | --- | --- | --- |
| Core cloud | `qc` | Hydrometeor output via `output_q` | ingest, diagnostics, slices, 3-D scalar points | raw + derived | near-term / already core |
| Core cloud | `qr` | Hydrometeor output via `output_q` | ingest, diagnostics, slices, 3-D scalar points | raw + derived | near-term / already useful |
| Core cloud | reflectivity `dbz` / `cref` | `output_dbz`, microphysics-dependent | field catalog/slice/3-D scalar if present | raw | near-term, validate per case |
| Core cloud | cloud fraction | derived from `qc` threshold | global and local diagnostics | derived | near-term / strengthen |
| Core cloud | cloud base/top | derived from `qc` + vertical coords | global and local diagnostics | derived | near-term / strengthen |
| Core cloud | liquid/cloud water path (`lwp`/CWP) | `output_lwp` | not currently productized | raw or derived | medium |
| Motion | `w` | `output_w` | ingest, diagnostics, slices; no 3-D signed layer yet | raw + derived | near-term |
| Motion | `u`, `v` | `output_u`, `output_v`, optionally interpolated | metadata only unless output exists | raw | medium |
| Motion/turbulence | TKE, `km`, `kh` | `output_tke`, `output_km`, `output_kh` | not productized | raw | medium |
| Motion/turbulence | vorticity/shear/updraft helicity | `output_vort`, `output_uh` | not productized | raw/derived | future |
| Thermodynamics | `qv` | `output_qv` | field catalog/slice/3-D scalar if present; no RH deficit yet | raw | near-term |
| Thermodynamics | `th` / temperature / pressure | `output_th`, `output_prs`, derived temperature | temperature/theta slice fields if present; no derived temp contract | raw/derived | near-term |
| Thermodynamics | buoyancy | `output_buoyancy` | process placeholder only | raw | medium |
| Thermodynamics | RH / saturation deficit | derive from `qv`, temperature, pressure | unsupported placeholder | derived | near-term for realistic runs |
| Thermodynamics | LCL/CAPE/CIN/LFC | CM1 output options | unsupported placeholder | raw or derived | medium |
| Surface/forcing | sensible/latent flux | `output_sfcflx` | not productized | raw | near-term for realistic inputs |
| Surface/forcing | 2 m temp/moisture, 10 m winds, roughness | `output_sfcdiags`, `output_sfcparams` | not productized | raw | near-term for land/diurnal |
| Surface/forcing | radiation terms / OLR | `output_radten`, `output_sfcparams` when radiation enabled | not productized | raw | medium with radiation runs |
| Time evolution | interesting times | derived from `qc`, `w`, `qr`, cloud top/base | partial defaults | derived | near-term |
| Time evolution | time-height cloud fraction/max `w` | derive from full sequence | not productized | derived | near-term |
| Time evolution | domain-mean profiles | domain diagnostics or derive from fields | not productized | raw/derived | near-term / medium |
| Budgets | `th/qv/u/v/w` budgets | CM1 budget outputs | not productized | raw | future |

### Realistic-Input Handoff

The #209 realistic-input memo says the next realistic-input implementation
should be a contract and observed sounding path, not Bench Mode UI or GIS/map
inputs yet. See `docs/research/realistic-les-input-architecture.md:802-811`.

It also asks #210 to prioritize outputs for:

- observed sounding runs;
- location/date/radiation runs;
- surface flux or wet-surface proxy runs;
- land/diurnal reference cases.

See `docs/research/realistic-les-input-architecture.md:983-1003`.

For those runs, #210's output implication is:

- observed soundings need source-profile metadata, vertical coordinates, wind
  caveats, and profile/time-height diagnostics;
- location/date/radiation needs radiation-relevant outputs and time metadata;
- surface/wetness proxy needs surface fluxes, 2 m temp/moisture, and proxy
  caveats;
- land/diurnal needs diurnal timing, boundary-layer growth, cloud onset,
  cloud top/base, and surface flux evolution.

## Backend Derived Output Products

### Compute At Ingest Time

Ingest-time work should stay bounded and metadata-heavy:

- result metadata;
- model-output file list and time index;
- field catalog;
- coordinate metadata;
- field availability by time and file;
- global finite/non-finite counts for priority fields;
- existing cloud/rain/updraft diagnostics;
- first cloud, max `qc`, max updraft, min downdraft, rain onset;
- cloud base/top and cloud fraction time series;
- output product manifest skeleton;
- caveats about missing fields, inferred time, units, skipped/corrupt files.

These are small enough to make Results and Explore trustworthy without forcing
large field arrays into the browser.

### Compute Lazily On Request

Lazy products should include:

- 2-D slices;
- 3-D thresholded scalar points;
- signed `w` point/glyph payloads;
- selected point, column, and box diagnostics;
- selected point time history;
- selected column vertical profile;
- time-height products;
- domain-mean vertical profiles;
- field max/min maps for one time;
- comparison slices or profiles for two results.

Lazy products should be computed with backend xarray and returned as bounded
JSON or binary payloads with provenance.

### Cache When Expensive Or Reused

Cacheable local artifacts should include:

- time-height arrays;
- domain-mean profiles by time;
- downsampled volumes;
- render-ready `qc` volume;
- signed `w` updraft/downdraft glyph datasets;
- selected-region summaries for named notebook selections;
- external export bundles for VAPOR/ParaView experiments.

These should live under the runtime home as generated derived artifacts, not in
git. They need their own manifest entries distinct from raw CM1 output and
result-card metadata.

### Raw Metadata vs Derived Visualization Artifacts

Use this distinction:

```text
result_metadata.json:
  small, durable, notebook/result-card metadata and diagnostics

derived output manifest:
  generated local cache index for products made from CM1 output

raw CM1 NetCDF:
  source of truth, local runtime artifact, never browser-parsed

visualization-ready artifacts:
  bounded products produced by backend/xarray, safe for browser consumption
```

The browser should never parse raw NetCDF directly. Current code already honors
this boundary in `visualization_data.py` and selected-region diagnostics.

## Explore Responsibility

Explore should remain the one-result, source-of-truth inspection surface.

It should own:

- selected result context;
- current true 3-D scene for spatial context;
- synchronized slice plane and slice inspector;
- exact field values from backend slices;
- field selector for currently supported fields;
- selected-point / selected-region `What happened here?`;
- basic time stepping and jumps to interesting times;
- provenance, caveats, and technical details;
- no-cloud / missing-field trust states.

Explore should expose first:

- `qc`, `qr`, `qv`, `dbz`, surface `rain`;
- `w` in slices until #183-style signed rendering exists;
- temperature/theta in slices and diagnostics, not 3-D point-cloud by default;
- profile/time-history links once backend products exist.

Explore should not own:

- cinematic cloud rendering;
- color-temperature/lighting/sun-angle art controls;
- video export;
- arbitrary camera path/fly-through;
- advanced multi-run diagnostics dashboards;
- heavyweight profile/time-height plot matrix;
- raw output file management;
- package generation or cleanup.

Those belong to future Render Studio, Diagnostics Lab, Build, and Storage.

## Future Render Studio Responsibility

Render Studio should be a future mode for beautiful, explicitly interpreted
rendering from backend-prepared products. It should not replace Explore.

Render Studio should eventually own:

- visually realistic `qc`/hydrometeor rendering;
- transfer functions;
- density/opacity controls;
- lighting and sun-angle controls;
- camera presets and camera paths;
- time-lapse playback;
- still/video export;
- thumbnails or shareable local renders;
- annotations that keep CM1 provenance visible.

The first honest visually realistic milestone should not be "make the current
point cloud prettier." It should be:

```text
backend render-ready qc volume / multiresolution product
-> prototype volume rendering or isosurface outside the main app
-> compare against Explore slices for scientific honesty
-> only then choose embedded Render Studio technology
```

Technique recommendation:

- keep thresholded points for current Explore context;
- prototype **volume rendering** for the serious cloud-render milestone because
  it is the closest visual match for translucent cloud water;
- prototype **isosurface** only as a secondary cloud-envelope view because it
  can overstate threshold boundaries;
- avoid ray-marched cinematic cloud rendering until render-ready products,
  transfer functions, and provenance language are stable.

VAPOR and ParaView both make sense as external reference renderers before Cloud
Chamber owns a production render stack. VAPOR documentation explicitly targets
ocean/atmosphere/solar researchers, provides interactive 3-D visualization,
animations, still frames, progressive data access, and imports some NetCDF
files. See VAPOR docs:
<https://ncar.github.io/VaporDocumentationWebsite/index.html>. VAPOR also
documents native support for CF-compliant NetCDF:
<https://vapordocumentationwebsite.readthedocs.io/en/latest/dataFormatRequirements/nativelySupportedDataFormats.html>.

ParaView is a heavier general scientific visualization environment. Its docs
cover loading time-varying datasets, volume rendering, transfer functions,
animation, export, screenshots, and remote/parallel visualization. See
<https://docs.paraview.org/en/latest/> and
<https://docs.paraview.org/en/latest/UsersGuide/animation.html>.

## Future Diagnostics Lab Responsibility

Diagnostics Lab should be a future scientific plots/profiles surface, not a
renderer. It should help answer "why did this run behave this way?" across time
and vertical structure.

Diagnostics Lab should eventually own:

- time-height cloud fraction;
- time-height max/min `w`;
- cloud base/top time series;
- max `qc`, max `qr`, max `dbz` time series;
- surface flux time series;
- boundary-layer depth proxy;
- domain-mean `qv`, `th`, temperature, pressure profiles;
- LCL/CAPE/CIN/LFC if available or derivable;
- selected-point time history;
- selected-column vertical profile and time history;
- side-by-side profile/time-history comparisons.

Explore should show compact versions or links to these products. Diagnostics Lab
should own the larger plot layouts, linked cursors, and scientific comparison.

xarray is already the right backend data model for this layer because it is
designed for labeled multidimensional arrays. See xarray docs:
<https://docs.xarray.dev/en/stable/>. hvPlot and Panel are worth prototyping as
a local diagnostics sidecar because hvPlot has gridded/time-series plotting
support and Panel can build Python apps, widgets, layouts, and dashboards
without first recreating every plot in React. See
<https://hvplot.holoviz.org/> and <https://panel.holoviz.org/>.

## External / Tooling Evaluation

| Option | Does well | Does poorly | CM1/NetCDF fit | Local-first fit | Recommended role |
| --- | --- | --- | --- | --- | --- |
| Current React + Three.js Explore | Integrated workflow, selected result context, slice/point explanation, provenance | Not a production cloud renderer, limited plot types, custom maintenance | consumes backend-prepared payloads only | excellent | keep for everyday scientific inspection |
| VAPOR | Atmospheric/science visualization, volume/isurface/slice/render/export, progressive data access | separate app, file compatibility may require CF/VDC prep, not notebook UI | direct import for some NetCDF, CF-compliant NetCDF supported | good if installed locally | external reference renderer/export prototype |
| ParaView | general heavy scientific visualization, volume rendering, transfer functions, time, export, remote/parallel | complex UI, may need preprocessing, not product-native | likely via NetCDF/converted structured grids | good but heavy | advanced external validation/export; maybe trame backend later |
| vtk.js | web scientific visualization, volume rendering API, GPU acceleration, transfer functions | adds frontend renderer complexity; requires ImageData/typed payloads; limited full VTK filters | needs backend-prepared arrays, not raw CM1 NetCDF | good once payloads exist | candidate embedded Render Studio renderer after render-ready volume product |
| trame | Python web apps around VTK/ParaView; can use Python data stack | separate sidecar architecture, dependency/process complexity | good with Python/xarray/VTK/ParaView conversion | good for local expert mode | spike only if Panel/hvPlot insufficient or ParaView sidecar needed |
| xarray + hvPlot + Panel | fast scientific diagnostics, profiles/time-height/time series, Python-native | not integrated React UX; not cinematic 3-D | excellent backend fit | good local sidecar | prototype Diagnostics Lab sidecar |
| Zarr | chunked/compressed N-D arrays, local/cloud/in-memory stores, performance | storage/schema decisions; another artifact format | derived store, not direct CM1 source | good for cached products | medium-term cache format for derived products |

vtk.js supports web scientific visualization and GPU-accelerated volume
rendering with opacity and color transfer functions. See
<https://kitware.github.io/vtk-js/docs/> and
<https://kitware.github.io/vtk-js/api/Rendering_Core_Volume.html>. That makes it
a better candidate for an embedded Render Studio prototype than for immediate
Explore tweaks.

trame is a Python-centric web application framework around VTK/ParaView and
other visualization libraries. Its docs emphasize VTK/ParaView 3-D visualization
and Python/web app development. See <https://kitware.github.io/trame/>. It is a
sidecar candidate, not a near-term dependency.

Zarr supports chunking, compression, multiple storage backends, and
N-dimensional arrays. See <https://zarr.readthedocs.io/en/stable/>. It is a
good candidate for derived caches once Cloud Chamber has products large enough
to justify a chunked store.

## Time-Lapse / Animation Architecture

Cloud Chamber should represent time explicitly as a derived product, not as a
viewer-only state.

Required metadata:

- output time values and source;
- output file -> time index mapping;
- direct vs inferred time caveat;
- run duration and cadence;
- interesting time index list;
- field availability by time;
- max/min summary by field/time;
- recommended default time for each field.

Near-term interesting times:

- first cloud;
- max `qc`;
- max updraft;
- min downdraft;
- highest cloud top;
- rain onset;
- max `qr`;
- max reflectivity;
- max surface rain;
- strongest surface flux;
- selected-point max field value once point time history exists.

First time-lapse implementation should support:

```text
scrub all output times
jump to first cloud
jump to max qc
jump to max updraft
jump to rain onset
lock camera while time changes
lock slice orientation/position while time changes
fetch one bounded payload per selected time
```

The backend should not load every full field into the browser. It should serve
bounded payloads for the active field/time/selection and optionally precompute
small time-index summaries.

Useful cadence depends on product target:

- quick-look: enough for smoke and rough evolution, often coarse;
- standard: enough for meaningful result review and basic time-lapse;
- Deep/visualization-quality: enough for smoother animation and rendered
  exports, opt-in because output size and wall time increase.

## What Happened Where: Selection / Explanation Model

Current supported primary interaction:

```text
click slice cell
-> backend selected-region diagnostics
-> What happened here?
```

The next selection modes should be staged:

| Selection mode | Usefulness | UI clarity | Backend requirement | Priority |
| --- | --- | --- | --- | --- |
| selected point | already useful for exact field value and local diagnostics | high | implemented for slice cells | current |
| selected vertical column | explains cloud/thermal profile above one surface point | high | local column profiles and time history | next |
| selected small 2-D box | reduces single-cell noise and supports local cloud patch explanation | medium/high | bounded box stats across time | next |
| selected 3-D box | useful for cloud/updraft region summaries | medium | bounded 3-D region stats; harder UI | later |
| selected cloud object | best semantic explanation of a cloud | high but advanced | connected components/object tracking | future |
| selected updraft core | useful for thermal fate | medium/high | signed `w` layer and local maxima tracking | after #183-style data |
| selected surface patch | important for realistic surface forcing | medium | surface flux/rain/diagnostic products | after surface outputs |

Recommended next step after selected point:

```text
selected column time history
```

Why:

- it connects surface, boundary-layer growth, saturation, cloud base/top, and
  updraft evolution;
- it is easier to explain than a freeform 3-D box;
- it fits both Explore and future Diagnostics Lab;
- it avoids premature cloud-object tracking.

## Recommended Output / Render Architecture

### Layered Architecture

```text
Raw CM1 output
  - NetCDF model-output files
  - stats/domain diagnostics files
  - source of truth
  - local runtime artifact

Result metadata
  - small JSON
  - result card/notebook state
  - field list, dimensions, time metadata
  - first-pass diagnostics and caveats

Derived output products
  - generated local cache
  - slices, profiles, time-height products
  - selected-point/column/box summaries
  - render-ready arrays
  - provenance and product manifest

Explore
  - one result
  - exact fields/slices/selected evidence
  - true 3-D context, not cinematic rendering

Diagnostics Lab
  - plots/profiles/time-height/time series
  - likely Python/xarray/hvPlot/Panel prototype first

Render Studio
  - optional future visual rendering mode
  - volume/isurface experiments from render-ready products
  - VAPOR/ParaView export first; embedded vtk.js only after payloads exist
```

### Practical Technology Call

For the next implementation:

- stay with current backend/xarray and React/Three Explore;
- do not add a new renderer dependency;
- add output product manifest and derived products.

For the next research/prototype after products exist:

1. Prototype VAPOR or ParaView export/open using one completed run.
2. Prototype xarray/hvPlot/Panel time-height/profile Diagnostics Lab sidecar.
3. Prototype vtk.js volume rendering only after a render-ready `qc` volume
   product exists.

Do not choose trame as the primary product path yet. It is promising if Cloud
Chamber wants a Python/ParaView sidecar, but too large for the immediate output
contract step.

## Recommended Next Implementation Issues

These are issue candidates only. This memo does not create GitHub issues.

### 1. Define Cloud Chamber Output Product Contract

Goal:

Define the backend schema for derived products made from CM1 output.

Scope:

- Add a documented output product manifest shape.
- Distinguish raw CM1 output, result metadata, derived diagnostics, cached
  visualization artifacts, external export bundles, and render-ready arrays.
- Define provenance, caveats, field/time coordinate metadata, cache keys, and
  generated-artifact cleanup rules.

Non-goals:

- No UI redesign.
- No renderer dependency.
- No new CM1 outputs.
- No heavy derived computation.

Why now:

Cloud Chamber has enough output paths that metadata-only result cards are no
longer sufficient. Every future visualization or diagnostics surface needs this
contract.

Dependencies:

- Current NetCDF ingest and visualization-ready APIs.

### 2. Add Time Index And Interesting-Time Products

Goal:

Create a robust time-product layer for playback, jumps, and diagnostics.

Scope:

- Record file/time mapping.
- Compute interesting times: first cloud, max `qc`, max `w`, min `w`, rain
  onset, max `qr`, max `dbz`, highest cloud top.
- Expose a small API payload for Explore and Results.
- Preserve direct vs inferred time caveats.

Non-goals:

- No video export.
- No renderer changes.
- No package cadence changes.

Why now:

Explore, time-lapse, and result comparison all need the same time semantics.

Dependencies:

- Output product contract.

### 3. Add Time-Height And Profile Derived Products

Goal:

Make realistic-input runs explainable through vertical/time structure.

Scope:

- Compute domain-mean profiles for priority fields when available.
- Compute time-height cloud fraction and max/min `w`.
- Compute selected-column profile payloads.
- Support observed-sounding and land/diurnal runs with provenance.

Non-goals:

- No Diagnostics Lab UI yet.
- No Panel/hvPlot dependency in product code.
- No scientific claims beyond available fields.

Why now:

The #209 realistic-input ladder needs output products that explain soundings,
surface fluxes, boundary-layer growth, and diurnal timing.

Dependencies:

- Output product contract.
- Time index products.

### 4. Expand Field Catalog For Realistic LES Outputs

Goal:

Prioritize and validate fields needed for realistic-input experiments.

Scope:

- Document and test catalog behavior for `qv`, temperature/theta/pressure,
  surface fluxes, surface diagnostics, radiation terms, `lwp`, CAPE/CIN/LCL/LFC
  if present.
- Add derived temperature/RH/saturation-deficit planning where source fields
  support it.
- Preserve slice vs 3-D render distinctions.

Non-goals:

- No package-generation changes.
- No browser NetCDF parsing.
- No arbitrary field UI dump.

Why now:

Cloud Chamber already displays a few additional fields. Realistic runs need a
more disciplined field catalog and product-facing meanings.

Dependencies:

- Output product contract.

### 5. Prototype External Visualization / Diagnostics Exports

Goal:

Evaluate serious visualization and diagnostics without committing to product
dependencies.

Scope:

- Prototype one VAPOR or ParaView export/open workflow from a completed run.
- Prototype one xarray/hvPlot/Panel diagnostics sidecar for time-height/profile
  products.
- Document what worked, what required preprocessing, and what should become
  product code later.

Non-goals:

- No embedded Render Studio.
- No committed external tool dependency.
- No production UI.
- No generated artifacts in git.

Why now:

External tools can reveal what good rendering/diagnostics should look like
before Cloud Chamber rebuilds those capabilities in the app.

Dependencies:

- At least one completed run with rich enough output.
- Output product contract preferred but not strictly required for a spike.

## Open Questions And Risks

### Data / Science

- Which CM1 fields are actually emitted by each current package preset?
- Which realistic-input cases should request `qv`, `th`, pressure, surface
  diagnostics, radiation terms, LCL/CAPE/CIN, and `lwp` by default?
- Can CM1's `output_lwp`, CAPE/CIN/LCL/LFC, and domain diagnostics be enabled
  in the relevant LES cases without destabilizing output size or runtime?
- Which derived diagnostics are robust enough to support user-facing process
  claims?
- How should Cloud Chamber calculate RH/saturation deficit: derived from
  `qv`/temperature/pressure, CM1 output, or both?

### Performance / Storage

- What payload sizes are safe for 8 GB local laptops in React/Three?
- When does JSON become unacceptable and require binary arrays?
- When does Zarr become worth its extra artifact-management complexity?
- How should derived products be invalidated if a result is reingested?
- How should Storage present generated derived artifacts without making users
  manage implementation folders?

### Product

- Should Diagnostics Lab be a separate top-level workspace, a Results subview,
  or an Explore mode?
- Should Render Studio be a separate workspace or an advanced mode inside
  Explore?
- How much visual beauty should live inside everyday Explore before it distracts
  from source-of-truth inspection?
- Which external export workflow is acceptable for a local-first personal lab?

### Tooling

- Will VAPOR directly accept Cloud Chamber's CM1 NetCDF shape, or will it need
  CF-compliance fixes or conversion?
- Will ParaView read the current file series cleanly, or should Cloud Chamber
  produce VTK/VTI/Zarr-derived exports?
- Is vtk.js performant enough for Cloud Chamber's likely volume sizes after
  downsampling?
- Is trame worth the process/dependency complexity compared with a simpler
  Panel/hvPlot diagnostics sidecar?

## Final Draft PM Input

Make the next output investment backend-first:

```text
Define output products
-> add time/interesting-time metadata
-> add profiles and time-height products
-> expand field catalog for realistic LES
-> prototype external render/diagnostics tooling
-> only then choose Render Studio / Diagnostics Lab product surfaces
```

This keeps Cloud Chamber's strongest product loop intact:

```text
Build
-> Results
-> Explore exact CM1-derived evidence
-> What happened here?
```

And it creates a deliberate path toward:

```text
beautiful renders
better plots
realistic-input experiments
trustworthy explanations
```

without confusing rendered interpretation with CM1 source data.
