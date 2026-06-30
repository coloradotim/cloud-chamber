# Realistic LES Input Architecture Research Spike

Issue: #209

Status: research memo / PM input only

This memo gathers evidence for how Cloud Chamber could evolve from curated
idealized CM1 LES cases toward more realistic LES inputs. It does not make
final product decisions, change CM1 package generation, add scenario families,
or implement UI.

## Scope And Non-Decisions

This research separates:

- what CM1 can do
- what Cloud Chamber currently supports
- what appears to be namelist/config-only
- what requires generated files
- what requires Fortran edits
- what requires external preprocessing
- what remains unknown or needs an experiment

The PM/human review should decide what to build next.

## Evidence Sources

Confirmed local/source files inspected:

- CM1 namelist guide: `/Users/timpeterson/cm1r21.1/README.namelist`
- CM1 example configs under `/Users/timpeterson/cm1r21.1/run/config_files/`
  - `les_ShallowCu`
  - `les_ShallowCuLand`
  - `les_ShallowCuPrecip`
  - `les_ConvBoundLayer`
  - `les_ConvPBL_moisture`
  - `les_HurrCoast`
  - `sea_breeze`
- Cloud Chamber package generation code:
  - `app/backend/cloud_chamber/cm1_input_contract.py`
  - `app/backend/cloud_chamber/dry_run_package.py`
  - `app/backend/cloud_chamber/scenario_schema.py`
- Cloud Chamber product/architecture docs:
  - `docs/product-vision.md`
  - `docs/cloud-chamber-product-spec.md`
  - `docs/architecture-and-data-model.md`
  - `docs/testing-and-validation.md`
  - `docs/current-roadmap.md`
  - `docs/development.md`

## Executive Recommendation

Draft PM input, not a final decision:

Cloud Chamber should not jump directly from the current idealized Baseline
Shallow Cumulus family to arbitrary "real-world location" LES. The next
architecture step should be a staged realistic-input ladder:

1. Preserve the current accepted external-sounding shallow-cumulus path as the
   trusted Golden Path.
2. Add a research-backed "realistic input contract" before adding UI controls:
   location/time/radiation, sounding source, surface model, surface flux/wetness,
   and compute tier should be explicit input groups rather than hidden namelist
   tweaks.
3. Treat observed/detailed soundings as the first realistic-input capability.
   This is closest to the current Cloud Chamber architecture because it already
   generates `input_sounding`.
4. Treat location/date/start-time/radiation as a second capability. CM1 has
   namelist support, but the examples imply runtime files and microphysics
   compatibility must be validated.
5. Treat realistic GIS/imagery-derived land/surface inputs as a later phase.
   CM1 documentation says spatially varying surface fields require
   `init_surface.F` customization, which is outside the current package-only
   Cloud Chamber model.
6. Use existing CM1 reference cases as architecture guides:
   `les_ShallowCuLand` for land/diurnal shallow cumulus, `sea_breeze` for
   radiation/location/date/external sounding mechanics, and `les_ShallowCuPrecip`
   for precipitating shallow cumulus.

In short: **build a realistic LES input contract before building realistic LES
scenario UI.** The first credible product step is "observed sounding plus
documented surface/radiation assumptions," not "pick any map location and run
realistic weather."

## Current Cloud Chamber Baseline

Confirmed from code and docs:

- Cloud Chamber is a local-first CM1 experiment builder, run manager, result
  notebook, diagnostics layer, and visualizer. It must not replace CM1 or hide
  fake physics. See `docs/product-vision.md`.
- The current package generator writes a run package under the configured
  runtime home with `run_manifest.json`, `case_manifest.json`,
  `namelist.input`, `input_sounding`, `dry_run_report.json`, and
  `runtime_file_checklist.json`.
- Current generated CM1 inputs are derived from the local CM1 `les_ShallowCu`
  reference case.
- Current Cloud Chamber package generation switches the thermodynamic source
  from CM1 built-in BOMEX (`isnd = 19`) to an external `input_sounding`
  path via `isnd = 17`.
- Current generated packages set `output_format = 2` for NetCDF ingest.
- Current product-facing controls are atmospheric controls such as
  low-level humidity, surface heating, cap strength, and cap height. Raw
  namelist settings remain technical/developer details.
- Current runtime presets are `quick_look`, `standard`, and
  `deep_overnight`; scenario templates require those three profiles.

Relevant source anchors:

- `app/backend/cloud_chamber/cm1_input_contract.py` defines current defaults and
  runtime presets at lines 24-61.
- `app/backend/cloud_chamber/cm1_input_contract.py` documents the generated
  external-sounding reproduction path at lines 211-224.
- `app/backend/cloud_chamber/cm1_input_contract.py` renders `isnd = 17`,
  `radopt = 0`, fixed ocean/surface settings, constant sensible/latent flux,
  and NetCDF output in the generated namelist.
- `app/backend/cloud_chamber/dry_run_package.py` writes the package files and
  runtime checklist at lines 76-142.
- `app/backend/cloud_chamber/scenario_schema.py` requires product-facing
  controls and the three run-size presets at lines 142-187.

## CM1 Capability Summary

### LES Mode And Built-In LES Cases

Confirmed fact:

CM1 supports LES through `cm1setup = 1`. The namelist guide describes this as
large-eddy simulation that integrates the filtered Navier-Stokes equations and
requires an SGS model. Source: `README.namelist`, lines 122-132.

Confirmed fact:

CM1 includes documented built-in test cases relevant to Cloud Chamber:

- `testcase = 1`: Convective Boundary Layer LES, `les_ConvBoundLayer`
- `testcase = 3`: Shallow cumulus LES / BOMEX, `les_ShallowCu`
- `testcase = 7`: Precipitating shallow cumulus LES / RICO,
  `les_ShallowCuPrecip`
- `testcase = 11`: Moist convective boundary layer without clouds,
  `les_ConvPBL_moisture`
- `testcase = 14`: Shallow cumulus over land with diurnal cycle,
  `les_ShallowCuLand`

Source: `README.namelist`, lines 151-215.

Current Cloud Chamber support:

Cloud Chamber currently uses a `les_ShallowCu`-derived path and a generated
external `input_sounding`. It does not currently expose a generalized selector
over the CM1 built-in LES cases.

### Soundings

Confirmed fact:

CM1 supports external sounding input through `isnd = 7`, using a file named
`input_sounding`, and `isnd = 17`, which is the same external sounding path but
neglects the wind profile in the file and uses the `iwnd` option instead.
Source: `README.namelist`, lines 612-639.

Current Cloud Chamber support:

Cloud Chamber currently generates `input_sounding` and uses `isnd = 17`.
This makes soundings the most natural first realistic-input expansion.

Likely capability:

Cloud Chamber can likely support observed or detailed sounding import by
converting an external profile into CM1's `input_sounding` format, while keeping
the rest of the validated package path stable. This still needs format
validation against CM1's reader and local smoke tests.

Unknown / needs experiment:

- exact tolerance and required column structure for arbitrary observed
  soundings in CM1's `base.F`
- how best to handle wind profiles if the product wants observed winds rather
  than the existing reference `iwnd = 9` path
- whether observed soundings should be normalized, smoothed, or capped for
  numerical stability before launch

Classification: generated file required; no Fortran edit expected for the
first external-sounding path.

### Location, Date, Start Time, And Radiation

Confirmed fact:

CM1 supports atmospheric radiation with `radopt`:

- `0`: off
- `1`: NASA-Goddard
- `2`: RRTMG

When `radopt >= 1`, CM1 takes `dtrad`, `ctrlat`, `ctrlon`, `year`, `month`,
`day`, `hour`, `minute`, and `second`. Latitude and longitude apply to the
entire domain. Source: `README.namelist`, lines 830-905.

Confirmed fact:

Radiation uses surface temperature, land/water flag, and land-use type from the
surface section. Source: `README.namelist`, lines 901-905.

Confirmed fact:

RRTMG radiation is accurately coupled only with selected microphysics schemes,
including Morrison (`ptype = 5`), which Cloud Chamber currently uses. Source:
`README.namelist`, lines 865-868.

Confirmed example:

The local CM1 `sea_breeze` example uses:

- external `input_sounding` (`isnd = 7`)
- `radopt = 2`
- `ctrlat = 30.00`
- `ctrlon = 0.00`
- `year = 2007`
- `month = 6`
- `day = 1`
- `hour = 5`
- RRTMG runtime data files in the config directory

But `sea_breeze` uses `cm1setup = 2`, not LES.

Current Cloud Chamber support:

Current generated baseline-style packages set `radopt = 0` and static
placeholder date/location values. There is no product-facing or schema-level
location/date/radiation input yet.

Likely capability:

Location/date/start-time/radiation looks mostly namelist-configurable for
spatially uniform small domains, but enabling it safely in Cloud Chamber would
also require staging radiation runtime data files when needed and validating the
selected microphysics/radiation combination.

Unknown / needs experiment:

- whether the current local CM1 build and staged runtime files are sufficient
  for RRTMG in the shallow-cumulus LES package
- whether `testcase = 3` plus `radopt = 2` produces scientifically meaningful
  behavior or double-counts/contradicts the idealized forcing
- whether `les_ShallowCuLand`'s "diurnal cycle" is implemented internally by
  `testcase = 14`, since its example namelist has `radopt = 0`

Classification: namelist/config-only for simple fields; generated runtime files
likely required for RRTMG; scientific experiment required before productizing.

### Surface And Land Conditions

Confirmed fact:

CM1 supports surface fluxes with `isfcflx`, and several surface-layer models
through `sfcmodel`, including simple CM1 formulation, WRF-like surface layers,
and Monin-Obukhov Similarity Theory for LES. Source: `README.namelist`,
lines 908-968.

Confirmed fact:

Default initial surface conditions are spatially uniform. CM1 supports simple
initial surface options:

- constant values
- sea-breeze test case
- rough west / smoother east
- coastline

For other spatially varying surface values, the guide says the user must
initialize them in `init_surface.F`. Source: `README.namelist`, lines 980-1013.

Confirmed fact:

CM1 supports constant sensible and latent heat flux settings for `sfcmodel = 1`
through `set_flx`, `cnst_shflx`, and `cnst_lhflx`, and supports roughness and
friction velocity controls through `set_znt`, `cnst_znt`, `set_ust`, and
`cnst_ust`. Source: `README.namelist`, lines 1017-1078.

Current Cloud Chamber support:

Current generated baseline-style packages use:

- `isfcflx = 1`
- `sfcmodel = 1`
- `oceanmodel = 1`
- `initsfc = 1`
- water/ocean-like land flag and land-use values
- constant heat and moisture fluxes
- reference roughness/stress settings

Current product controls can alter a surface-heating concept at the scenario
level, but Cloud Chamber does not yet implement a generalized surface/land
condition architecture.

Likely capability:

Uniform surface conditions, simple constant flux changes, and idealized
surface-pattern choices look feasible through namelist/config generation.

Unknown / needs experiment:

- whether `les_ShallowCuLand` can be adapted as a Cloud Chamber land-surface
  baseline without changing package assumptions too much
- how much surface realism is possible without editing `init_surface.F`
- how to expose wet-surface or moisture-source controls honestly without
  implying dynamic soil hydrology

Classification:

- uniform surface and flux values: namelist/config-only
- `LANDUSE.TBL` and radiation data: generated/runtime files required
- arbitrary spatial surface maps: Fortran edits and/or external preprocessing
  likely required

### Terrain And GIS / Map / Imagery Feasibility

Confirmed fact:

CM1 terrain setup includes `itern`, and custom terrain requires setting the `zs`
array in `init_terrain.F`. The guide also notes that output interpolation is
available for terrain-following coordinates. Sources: `README.namelist`,
lines 672-673 and 1274-1280.

Confirmed fact:

Spatially varying surface temperature, deep-layer temperature, land/water flag,
and land-use index require coding `init_surface.F`. Source:
`README.namelist`, lines 1010-1013.

Current Cloud Chamber support:

Cloud Chamber does not currently ingest GIS/map/imagery data, generate surface
rasters, edit CM1 Fortran, or build terrain/surface preprocessing outputs.

Likely capability:

A very limited "map-inspired" MVP could use idealized surface patterns already
represented by CM1 (`initsfc = 3` or `initsfc = 4`) or generated uniform surface
settings. This is not the same as realistic GIS.

Unknown / needs experiment:

- whether a package-only route can stage externally prepared GrADS or other
  files for terrain/surface without recompiling CM1
- whether local CM1 build tooling can safely support generated Fortran
  initialization patches
- what data sources, projections, and resampling would be required for imagery
  or GIS-derived surface categories

Classification:

- idealized coastline/roughness pattern: namelist/config-only, if scientifically
  appropriate
- arbitrary realistic GIS surface: external preprocessing plus Fortran or
  CM1-specific initialization hooks likely required
- imagery-derived wetness/land-surface proxy: external preprocessing and
  scientific validation required

### Output And Diagnostics Inputs

Confirmed fact:

CM1 writes NetCDF with `output_format = 2`. The guide warns NetCDF can be
inefficient for very large processor counts, but that limitation is not directly
about the current local Mac-scale use. Source: `README.namelist`, lines
1237-1255.

Confirmed fact:

CM1 can output relevant fields:

- surface rainfall
- surface fluxes
- surface parameters
- surface diagnostics
- pressure
- potential temperature
- water vapor
- hydrometeor mixing ratios
- reflectivity for supported microphysics
- buoyancy
- winds including `w`
- radiative tendencies when `radopt >= 1`
- CAPE/CIN/LCL

Source: `README.namelist`, lines 1284-1419.

Current Cloud Chamber support:

Cloud Chamber currently ingests NetCDF output, computes diagnostics from fields
such as `qc`, `w`, and `qr`, exposes result cards, and serves
visualization-ready backend payloads for selected fields. The browser should
not parse raw NetCDF.

Likely capability:

Realistic-input architecture should include explicit output requirements per
input mode. Radiation experiments should request radiation and surface
diagnostic outputs. Surface/moisture-source experiments should request surface
flux and surface diagnostic fields.

Unknown / needs experiment:

- which additional outputs materially increase local output size
- whether backend ingest and Explore performance remains acceptable for large
  multi-file, multi-field realistic runs

## Reference Case Candidates

| Reference | Confirmed CM1 setup | What it teaches | Cloud Chamber fit |
| --- | --- | --- | --- |
| `les_ShallowCu` | LES, BOMEX shallow cumulus, 64x64x75, 100 m, 6 h, `testcase = 3`, `isnd = 19`, `radopt = 0`, ocean/simple fluxes | Trusted current baseline source | Current source of truth for Baseline family |
| `les_ShallowCuLand` | LES, ARM-SGP shallow Cu over land, 96x96x110, 66.7 m, 15 h, `testcase = 14`, `isnd = 23`, `sfcmodel = 5`, `radopt = 0` | Land/diurnal shallow cumulus reference | Strong candidate for future land/diurnal research; exact forcing needs investigation |
| `les_ShallowCuPrecip` | LES, RICO precipitating shallow cumulus, 128x128x100, 100 m, 24 h, `testcase = 7`, `isnd = 20` | Precipitating shallow cumulus | Useful later for rain/cold-pool paths, heavier run |
| `les_ConvBoundLayer` | Dry CBL LES, 128x128x128, 40 m, 6 h, `testcase = 1` | Thermals without cloud/moisture | Useful process reference, not cloud-forming |
| `les_ConvPBL_moisture` | Moist CBL no-cloud LES, 512x512x200, 15 m, 13 h, `testcase = 11` | Moist boundary layer without cloud | Scientifically useful but likely too expensive for local MVP |
| `sea_breeze` | Mesoscale/PBL, not LES; external sounding, `radopt = 2`, date/time/location, RRTMG files, sea-breeze surface | Mechanics of location/date/radiation/runtime files | Not a direct LES base, but valuable architecture reference |
| `les_HurrCoast` | LES hurricane-coast, 600x200x100, 20 m, coastline initial surface | Surface heterogeneity/coastline pattern | Too specialized/expensive; useful for evidence that idealized coastline exists |

## Realistic Input Domains

### 1. Location

CM1 can do this:

- Radiation latitude/longitude through `ctrlat` and `ctrlon` when
  `radopt >= 1`.
- The location applies to the entire domain, not a map projection.

Cloud Chamber currently supports this:

- Static generated namelist values only; no product control or schema.

Namelist/config only:

- latitude/longitude values for radiation in a small-domain experiment.

Generated files required:

- radiation data files when using RRTMG, based on the `sea_breeze` example.

Fortran edits / external preprocessing:

- realistic spatial maps, terrain, and land-use categories beyond simple
  built-in patterns.

Unknown / needs experiment:

- whether changing only `ctrlat`/`ctrlon` in the current shallow-cumulus package
  is scientifically meaningful without also changing sounding, surface, and
  radiation.

### 2. Date / Day Of Year / Start Time

CM1 can do this:

- `year`, `month`, `day`, `hour`, `minute`, and `second` are namelist inputs for
  radiation.

Cloud Chamber currently supports this:

- Static placeholder values in generated namelist; not product-controlled.

Namelist/config only:

- start date/time values when radiation is active.

Unknown / needs experiment:

- how date/time affects a `testcase = 3` idealized shallow cumulus package when
  other reference forcings remain active.

### 3. Radiation / Diurnal Behavior

CM1 can do this:

- NASA-Goddard or RRTMG atmospheric radiation.
- RRTMG is documented as accurately coupled with Morrison microphysics
  (`ptype = 5`), among others.
- Radiative tendency output is available when `radopt >= 1`.

Cloud Chamber currently supports this:

- Not currently enabled. Generated baseline has `radopt = 0`.

Namelist/config only:

- `radopt`, `dtrad`, location, and start date/time.

Generated files required:

- likely RRTMG runtime data files for `radopt = 2`, as shown in `sea_breeze`.

Unknown / needs experiment:

- whether shallow-cumulus LES reference forcings and active radiation should be
  combined, replaced, or treated as separate scenario templates.
- how `les_ShallowCuLand` implements its documented diurnal behavior with
  `radopt = 0`.

### 4. Observed Or Detailed Soundings

CM1 can do this:

- External `input_sounding` through `isnd = 7` or `isnd = 17`.

Cloud Chamber currently supports this:

- Generated external `input_sounding` via `isnd = 17`.

Generated files required:

- `input_sounding`.

Likely next product capability:

- Import or paste an observed/detailed sounding, convert to CM1 format, validate
  profile sanity, and label all smoothing/inference.

Unknown / needs experiment:

- arbitrary observed wind profile support if Cloud Chamber moves from
  `isnd = 17` to `isnd = 7`.
- safe smoothing and cap/moisture adjustments for numerically stable LES.

### 5. Surface / Land Conditions

CM1 can do this:

- Uniform constant surface fields via namelist.
- Simple built-in spatial patterns such as sea breeze, rough/smooth split, and
  coastline.
- Surface-layer models and surface flux controls.

Cloud Chamber currently supports this:

- Current baseline-style generated namelist uses ocean/simple surface settings
  and constant sensible/latent flux values inherited from `les_ShallowCu`.

Namelist/config only:

- constant skin temperature, land/water flag, land-use index, season, surface
  fluxes, roughness/stress, and simple `initsfc` patterns.

Fortran edits required:

- arbitrary spatially varying `tsk`, `tmn`, `xland`, or `lu`.

Unknown / needs experiment:

- whether Cloud Chamber should first target uniform land, idealized patterns,
  or a `les_ShallowCuLand` reference path.

### 6. Surface Sensible / Latent Flux

CM1 can do this:

- Constant sensible and latent heat fluxes for `sfcmodel = 1` through
  `set_flx`, `cnst_shflx`, and `cnst_lhflx`.
- Surface flux outputs through `output_sfcflx`.

Cloud Chamber currently supports this:

- Current generated baseline includes constant sensible and latent heat flux
  values from the reference path.

Namelist/config only:

- first-pass surface-heating and moisture-source proxy through constant fluxes.

Likely capability:

- A "wet surface / dry surface" proxy could be represented as a controlled
  latent-heat-flux or moisture-availability change, but must be labeled as a
  proxy rather than a real hydrology model.

Unknown / needs experiment:

- how to preserve scientific honesty when mapping product words like
  "wet ground" to constant flux or fixed moisture availability.

### 7. GIS / Map / Imagery

CM1 can do this:

- CM1 has hooks for terrain and spatial surface initialization.

Cloud Chamber currently supports this:

- None.

Namelist/config only:

- no realistic GIS path.

Generated files required:

- potentially terrain/surface intermediates if a future CM1 path supports them.

Fortran edits required:

- documented path for arbitrary spatial surface fields uses `init_surface.F`.
- documented custom terrain path uses `init_terrain.F`.

External preprocessing required:

- map projection, raster resampling, land-use classification, surface wetness
  proxy derivation, and metadata/provenance.

Unknown / needs experiment:

- whether a package-only approach can be built without recompiling CM1.
- whether imagery-derived wetness is scientifically credible enough for the
  product without ancillary soil/vegetation data.

## Compute And Runtime Tiers

Confirmed Cloud Chamber current behavior:

- Standard baseline assumptions in docs/code are 64x64x75, 100 m horizontal
  spacing, 40 m nominal vertical spacing, 18 km top, 21600 s runtime, 3600 s
  output cadence, and NetCDF output.
- Quick-look uses 10800 s runtime and 900 s output cadence.
- Deep / overnight currently increases horizontal resolution to 192x192 over
  the same physical domain and output cadence to 300 s.

Local observation, not a portable benchmark:

- A manually adjusted deep-style local run with 160x160x75, 40 m horizontal
  spacing, 21600 s runtime, 600 s output cadence, and 3 s timestep completed
  successfully but took roughly overnight-scale wall time and produced multiple
  GB of NetCDF output.

Draft compute-tier implication:

- Realistic LES inputs should not be decoupled from compute tiers. A credible
  location/date/surface/radiation setup can easily increase field needs,
  output size, and wall-clock time.
- Mac-local tiers should remain conservative and labeled as estimates until
  validated.
- If future realistic cases require >128x128 horizontal grids, many fields,
  radiation, or 12-24 h runtimes, Cloud Chamber should classify them as
  workstation/remote candidates rather than default local experiments.

## Draft Input Architecture

Draft PM input, not final:

```text
Realistic LES Input Contract
  Experiment intent
    scenario family
    physical question
    expected diagnostic story

  Atmospheric profile
    source: generated reference | observed sounding | edited observed sounding
    file: input_sounding
    station/location metadata
    station elevation
    valid time/date
    source/provider
    source units and converted units
    wind handling: from sounding | reference wind | generated profile
    validation: moisture/stability/cap sanity checks

  Place and time
    latitude
    longitude
    date
    start time
    time zone / UTC handling
    radiation enabled?

  Radiation
    radopt
    dtrad
    required runtime data files
    compatible microphysics
    output_radten / output_sfcparams requirements

  Surface and land
    surface model
    ocean model
    land/water flag
    land-use index
    season
    skin/deep temperature
    roughness/stress path
    surface flux path
    wet-surface proxy, if used

  Spatial surface/terrain inputs
    none | idealized pattern | preprocessed map | Fortran hook
    provenance and limitations

  Domain and compute tier
    nx/ny/nz
    dx/dy/dz
    ztop
    timax
    dt
    output cadence
    expected output fields
    expected output volume
    expected wall-clock class

  Output and diagnostics contract
    required CM1 fields
    required surface/radiation diagnostics
    expected result-card diagnostics
    Explore field availability
```

## Recommended Staging

Draft PM input, not final:

### Stage 1: Observed Sounding Import Architecture

Goal:

Support realistic one-dimensional atmospheric profiles while keeping the
validated package path stable.

Why first:

Cloud Chamber already generates `input_sounding`, and CM1 supports external
soundings.

Build boundary:

- generated file work
- metadata preservation from the first version:
  - station/location
  - station elevation
  - valid time/date
  - source/provider
  - source units and converted CM1 units
  - wind profile handling
- validation/sanity checks
- docs/tests with tiny fixtures
- no new map/GIS/radiation claims

### Stage 2: Location / Date / Radiation Research Package

Goal:

Validate a controlled shallow-cumulus package with active radiation and explicit
place/time metadata.

Why second:

CM1 has namelist support, but runtime files and scientific interaction with
idealized forcing must be validated.

Build boundary:

- likely package-generation additions after PM approval
- runtime file checklist expansion
- manual local smoke run
- no arbitrary real-location weather claim

### Stage 3: Land / Surface Reference Case

Goal:

Investigate `les_ShallowCuLand` as a second trusted source-of-truth case for
land/diurnal shallow cumulus.

Why third:

It is a CM1 LES reference case based on ARM-SGP, but its forcing and diurnal
implementation need inspection before product work.

### Stage 4: Surface Moisture / Wet-Surface Proxy

Goal:

Represent simple surface moisture availability or latent-flux sensitivity
honestly.

Build boundary:

- namelist/config-only if using constant fluxes or uniform values
- strong caveats: proxy, not hydrology

### Stage 5: GIS / Imagery / Terrain Spike

Goal:

Determine whether realistic spatial surface/terrain inputs can be built without
maintaining CM1 Fortran variants.

Why later:

CM1 documentation points to `init_surface.F` and `init_terrain.F` for arbitrary
spatial fields. This is a larger architecture decision.

## Immediate Product Call

Draft PM input, not final:

- Do not implement Bench Mode UI yet.
- Do not implement GIS/map inputs yet.
- Do not implement #153 surface heterogeneity yet.
- Do not expose raw CM1 namelist fields as primary user controls.
- The next implementation should be a realistic input contract and observed
  sounding path with metadata/provenance, reviewed before UI expansion.

## Recommended Next Issues

These are recommended issue candidates only. This memo does not create GitHub
issues automatically.

### Define Realistic LES Input Contract Schema

Goal:

Define the backend/schema contract for realistic LES inputs before adding UI.

Scope:

- Add a documented schema or contract for realistic LES input metadata:
  atmospheric profile, place/time, radiation intent, surface assumptions,
  compute tier, required runtime files, and output/diagnostic requirements.
- Preserve provenance fields for source data, units, conversions, inferred
  values, and caveats.
- Keep the current accepted Baseline package path unchanged.

Non-goals:

- No UI.
- No new scenario family.
- No CM1 package behavior change until the contract is reviewed.
- No GIS/map input support.

Why now:

The research shows multiple realism levels are possible, but they require
different implementation mechanisms. A schema first prevents hidden namelist
tweaks from becoming product promises.

Dependencies:

- PM review of this memo.
- Current scenario/package generation tests remain green.

### Add Observed Sounding Import Research / Prototype

Goal:

Prototype conversion of an observed or detailed sounding into CM1
`input_sounding` while preserving metadata and scientific caveats.

Scope:

- Accept tiny fixture soundings in tests.
- Preserve station/location, elevation, valid time/date, source/provider,
  source units, converted units, and wind-handling metadata.
- Validate profile sanity enough to fail clearly before package generation.
- Document whether the prototype uses `isnd = 17` with reference/generated wind
  or `isnd = 7` with sounding winds.

Non-goals:

- No production UI.
- No arbitrary web data fetching.
- No radiation/location controls beyond preserving metadata.
- No claim that any observed sounding is automatically numerically stable.

Why now:

External soundings are the closest realistic-input step to current Cloud
Chamber because the generator already writes `input_sounding`.

Dependencies:

- Realistic LES input contract schema.
- Inspection of CM1 `base.F` external-sounding reader expectations if the file
  format requirements remain ambiguous.

### Audit / Package CM1 les_ShallowCuLand As A Reference Case

Goal:

Determine whether CM1 `les_ShallowCuLand` can become a trusted land/diurnal
reference path for Cloud Chamber.

Scope:

- Compare `les_ShallowCuLand` namelist and runtime files against the accepted
  Baseline package path.
- Identify how its documented land/diurnal behavior is implemented, especially
  because the local example has `radopt = 0`.
- Document required generated files, runtime files, output fields, and expected
  local compute/storage tier.

Non-goals:

- No UI.
- No scenario-family expansion.
- No tuning.
- No CM1 run in CI.

Why now:

`les_ShallowCuLand` is the strongest local CM1 reference candidate for
realistic land/diurnal shallow cumulus, but its forcing path is not yet clear
enough to productize.

Dependencies:

- Realistic LES input contract schema.
- PM decision that land/diurnal shallow cumulus is the next realism target.

### Validate Location / Date / Start-Time / Radiation Packaging

Goal:

Validate a controlled package path for CM1 radiation and place/time metadata.

Scope:

- Use a tiny/manual package validation path after PM approval.
- Determine required RRTMG or NASA-Goddard runtime files.
- Confirm compatibility with the chosen microphysics and output fields.
- Document whether radiation should combine with, replace, or remain separate
  from current idealized testcase forcing.

Non-goals:

- No general real-world weather claims.
- No GIS/map inputs.
- No arbitrary location UI.
- No changes to current package generation until validation succeeds.

Why now:

CM1 clearly exposes radiation and place/time namelist parameters, but the
scientific and runtime-file implications need a focused validation before UI.

Dependencies:

- Realistic LES input contract schema.
- Runtime file checklist decision for radiation data.
- Manual local CM1 validation outside CI.

### Define Surface Flux / Wet-Surface Proxy Scenario Architecture

Goal:

Decide how Cloud Chamber should represent surface moisture or wet-surface
effects without overclaiming hydrology.

Scope:

- Map product language such as "wet surface" or "moisture source" to supported
  CM1 controls such as constant latent heat flux, moisture availability, or
  reference-case surface settings.
- Document units, assumptions, diagnostics, and caveats.
- Decide which outputs are required to inspect surface-flux behavior.

Non-goals:

- No GIS/imagery wetness maps.
- No dynamic soil hydrology claim.
- No arbitrary parameter sweep.
- No new scenario family before PM approval.

Why now:

Surface moisture is a core user-facing concept, but the CM1-supported MVP path
is probably a proxy. It should be designed explicitly before implementation.

Dependencies:

- Realistic LES input contract schema.
- Output/visualization prioritization from #210.

## Handoff To Output / Visualization Spike

#210 should use this memo to prioritize output fields, derived diagnostics, and
visualization-ready payloads for realistic-input runs. In particular, #210
should consider:

- observed sounding runs: preserve and expose source profile metadata, vertical
  coordinates, wind-handling caveats, and sounding-derived stability/moisture
  diagnostics where supported
- location/date/radiation runs: request and document radiation-relevant outputs
  such as radiative tendencies, surface parameters, and top-of-atmosphere or
  surface radiation diagnostics when `radopt >= 1`
- surface flux / wet-surface proxy runs: prioritize surface sensible/latent
  flux fields, 2 m temperature/moisture, surface diagnostics, and caveats that
  distinguish proxy behavior from real soil hydrology
- land/diurnal reference cases: prioritize fields that show diurnal timing,
  boundary-layer growth, cloud onset, cloud top/base, surface fluxes, and
  whether the land/diurnal forcing is directly supported or inferred

This handoff is intentionally short. It does not decide #210's output contract
or visualization implementation.

## Unknowns To Resolve Before Building

- How does `les_ShallowCuLand` implement land/diurnal behavior while its
  example namelist has `radopt = 0`?
- Does the local CM1 build have all radiation runtime files needed for RRTMG in
  a shallow-cumulus LES package?
- Does combining active radiation with the current `testcase = 3` forcing make
  scientific sense?
- Should observed wind profiles use `isnd = 7`, or should Cloud Chamber keep
  `isnd = 17` and generate/retain reference wind profiles?
- What validation should Cloud Chamber apply to observed sounding profiles
  before launching CM1?
- Can realistic land/surface patterns be represented without Fortran edits, or
  should Cloud Chamber explicitly avoid arbitrary GIS inputs for MVP?
- What output fields are required for realistic-input diagnostics, and how much
  do they increase local output volume?
- How much can Explore handle for large multi-file NetCDF results before
  backend downsampling/caching becomes mandatory?

## Non-Recommendations

This spike does not recommend:

- exposing raw namelist fields as primary user controls
- claiming arbitrary real-world weather simulation
- implementing Bench Mode UI before the realistic input contract is reviewed
- implementing GIS/map inputs before a preprocessing and CM1 initialization
  strategy exists
- implementing #153 surface heterogeneity as the next step
- importing satellite/map imagery directly into CM1 without a preprocessing and
  validation architecture
- editing CM1 Fortran as part of the current package generator
- adding scenario families before the realistic-input contract is reviewed
- treating preview or visualization as CM1 output

## Bottom Line

Confirmed facts show CM1 has many of the building blocks for more realistic LES
inputs: external soundings, radiation with place/time, surface models, constant
fluxes, selected built-in land/coastline patterns, NetCDF outputs, and relevant
diagnostic fields. Cloud Chamber currently supports only a narrow
external-sounding, `les_ShallowCu`-derived, idealized package path.

The safest next product step is not a UI for "realistic location." It is a
reviewed input architecture that decides which realism level Cloud Chamber is
actually promising:

```text
observed sounding
-> optional place/time/radiation
-> documented uniform or idealized surface assumptions
-> validated compute tier
-> explicit caveats
```

GIS/map/imagery realism should remain a later spike unless the project is ready
to own external preprocessing and possibly CM1 initialization-code workflows.
