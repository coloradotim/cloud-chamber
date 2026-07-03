# Cloud Chamber Realistic LES Input Specification

Issue: #213

Status: draft v1 product/data contract

Source context:

- #209 realistic LES input architecture research
- current external-sounding Baseline Shallow Cumulus package path
- current scenario/package generation, Result Card, Explore, Storage, and test
  contracts
- [Cloud Chamber output product specification](output-product-specification.md)
  as the output-side companion contract

This specification defines what Cloud Chamber means by realistic LES input
data before adding observed sounding import, location/date/radiation controls,
surface-flux controls, GIS/map inputs, new scenario families, or Bench Mode UI.

It is a product/data contract only. It does not implement new package
generation behavior.

## Executive Contract

Cloud Chamber should not jump directly from accepted idealized shallow-cumulus
cases to arbitrary real-world LES. The first realistic-input path is:

```text
observed or detailed sounding metadata
-> explicit conversion into CM1 input_sounding
-> preserved place/time/source metadata
-> documented wind handling, smoothing, interpolation, and caveats
-> unchanged validated package path until manual validation approves changes
```

Location, date, start time, radiation, surface conditions, wet-surface proxies,
and GIS/map inputs are separate capability layers. They must be represented
honestly in metadata before they become product controls.

Strong product calls:

- Do not implement Bench Mode UI yet.
- Do not implement GIS/map inputs yet.
- Do not implement #153 surface heterogeneity yet.
- Do not expose raw CM1 namelist fields as primary product controls.
- First implementation should be observed/detailed sounding import with
  metadata/provenance.
- Location/date/start-time/radiation likely comes after observed sounding
  metadata, and requires runtime-file and scientific validation.
- Surface flux or wet-surface behavior must be labeled as a proxy unless CM1
  support justifies stronger wording.
- GIS/map/imagery-derived surfaces are future work and likely require external
  preprocessing, CM1 initialization hooks, or Fortran paths.

## Capability Status Legend

Each input group uses these statuses:

| Status | Meaning |
| --- | --- |
| Currently supported by Cloud Chamber | Implemented in current Cloud Chamber package generation, metadata, docs, or tests. |
| Confirmed CM1 capability | Supported by CM1 documentation or local examples inspected in #209. |
| Likely CM1 capability needing validation | Plausible from CM1 docs/examples, but not yet validated in a Cloud Chamber package. |
| Namelist/config-only | Can likely be represented in `namelist.input` without new generated data files. |
| Generated input file required | Requires a generated file such as `input_sounding`. |
| Runtime file required | Requires staging external CM1 runtime files such as lookup tables or radiation data. |
| Fortran edit required | Requires editing or maintaining CM1 initialization/source files. |
| External preprocessing required | Requires GIS/raster/conversion/analysis outside current package generation. |
| Future / unsupported | Not part of near-term Cloud Chamber product support. |

## Contract Skeleton

Realistic LES input metadata should eventually be representable as a structured
record like this. This is documentary, not an implemented schema:

```json
{
  "contract_version": 1,
  "intent": {},
  "atmospheric_profile": {},
  "place_time": {},
  "radiation": {},
  "surface_land": {},
  "spatial_surface_terrain": {},
  "domain_runtime_compute": {},
  "output_diagnostics": {},
  "provenance": {},
  "caveats": []
}
```

This record should travel with generated package reviews, run manifests or case
manifests when implemented, Result Cards, and output products where relevant.

## A. Experiment Intent

Experiment intent answers:

```text
What physical question is this run trying to answer, and how ready is the input
package to support that question?
```

Required fields:

- scenario family;
- physical question;
- expected diagnostic story;
- readiness/confidence state;
- known caveats.

Draft shape:

```json
{
  "scenario_family": "shallow_cumulus",
  "physical_question": "How does an observed boundary-layer profile change cloud onset and depth?",
  "expected_diagnostic_story": [
    "cloud formed / no cloud",
    "first cloud time",
    "max qc",
    "max/min w",
    "rain onset if available"
  ],
  "readiness_state": "contract_defined",
  "confidence": "needs_local_validation",
  "known_caveats": [
    "observed sounding conversion not yet validated for arbitrary profiles"
  ]
}
```

Capability distinctions:

| Item | Status |
| --- | --- |
| Scenario family, physical question, expected diagnostics | Currently supported by Cloud Chamber scenario templates for curated cases. |
| Readiness/confidence and known caveats | Currently present in docs and package reviews, but not yet a realistic-input schema. |
| CM1 support | Not a CM1 concept; this is product metadata. |
| Implementation path | Metadata/config only. |
| Future / unsupported | Arbitrary scenario-family expansion before this contract is reviewed. |

Rules:

- Product-facing intent must stay atmospheric, not namelist-shaped.
- Readiness must not imply scientific acceptance before local/manual validation.
- Result Cards should preserve the intent so Results and Explore can explain
  what the run was meant to test.

## B. Atmospheric Profile / Sounding

The atmospheric profile is the first supported realistic-input path.

Required fields:

- source type: `generated_reference`, `observed_sounding`,
  `edited_observed_sounding`;
- source/provider;
- station/location;
- station elevation;
- valid time/date;
- source units;
- converted CM1 units;
- vertical coordinate type: `height`, `pressure`, `mixed`, `inferred`;
- thermodynamic profile fields;
- moisture profile fields;
- wind profile fields;
- wind handling: `from_sounding`, `reference_wind`, `generated_profile`;
- smoothing/interpolation/truncation choices;
- validation/sanity checks;
- caveats.

Draft shape:

```json
{
  "source_type": "observed_sounding",
  "source_provider": "manual_fixture_or_observed_archive",
  "station": {
    "id": "TBD",
    "name": "TBD",
    "latitude": null,
    "longitude": null,
    "elevation_m": null
  },
  "valid_time": {
    "date": "YYYY-MM-DD",
    "time_utc": "HH:MM:SSZ",
    "time_zone": "UTC",
    "source_time_text": "TBD"
  },
  "source_units": {
    "height": "m",
    "pressure": "hPa",
    "temperature": "C",
    "mixing_ratio": "g/kg",
    "wind_speed": "m/s",
    "wind_direction": "degrees"
  },
  "converted_cm1_units": {
    "height": "m",
    "potential_temperature": "K",
    "water_vapor_mixing_ratio": "kg/kg",
    "wind_components": "m/s"
  },
  "vertical_coordinate_type": "height",
  "profile_fields": {
    "thermodynamic": ["theta_or_temperature"],
    "moisture": ["qv_or_mixing_ratio"],
    "wind": ["u", "v"]
  },
  "wind_handling": "observed_sounding_winds",
  "conversion_choices": {
    "smoothing": "none_or_documented_method",
    "interpolation": "native_to_cm1_required_levels",
    "truncation": "model_top_or_valid_profile_top"
  },
  "validation": {
    "passed": false,
    "checks": []
  },
  "caveats": []
}
```

Capability distinctions:

| Item | Status |
| --- | --- |
| Generated reference sounding through `input_sounding` | Currently supported by Cloud Chamber for the accepted external-sounding baseline path. |
| CM1 external sounding input | Confirmed CM1 capability through external `input_sounding` paths such as `isnd = 7` and `isnd = 17`. |
| Observed/detailed sounding conversion | Supported for local uploaded IGRA station text after package-review validation. |
| `input_sounding` | Generated input file required. |
| Observed winds from sounding | Supported for uploaded observed-sounding packages: direction/speed converts to CM1 `u`/`v` and packages use `isnd = 7`. |
| Smoothing/interpolation/truncation | Product/backend metadata required; implementation must be explicit. |
| Arbitrary online sounding fetch | Future / unsupported until source, provenance, and failure behavior are designed. |

Rules:

- Preserve station/location, elevation, valid time/date, source/provider,
  source units, converted units, wind handling, conversion choices, and caveats
  from the first implementation.
- If radiation remains disabled, place/time metadata still travels as sounding
  provenance.
- Do not silently replace missing observed winds with reference winds; block or
  caveat clearly and record `wind_handling`.
- If pressure-to-height or temperature-to-potential-temperature conversion is
  inferred, record the method and caveat.
- Validation should fail clearly before package generation for obviously bad
  profiles, missing required fields, non-monotonic vertical coordinates, or
  unusable moisture/temperature values.

## C. Place And Time

Place/time metadata is required even before active radiation is implemented,
because observed soundings and future radiation controls need provenance.

Required fields:

- latitude;
- longitude;
- elevation if applicable;
- date;
- day of year;
- start time;
- time zone / UTC handling;
- run duration.

Draft shape:

```json
{
  "latitude": 36.68,
  "longitude": -98.35,
  "elevation_m": null,
  "date": "YYYY-MM-DD",
  "day_of_year": null,
  "start_time_local": null,
  "start_time_utc": "HH:MM:SSZ",
  "time_zone": "UTC",
  "run_duration_seconds": 21600,
  "used_by_cm1": false,
  "caveats": [
    "place_time_preserved_as_metadata_only_when_radiation_disabled"
  ]
}
```

Capability distinctions:

| Item | Status |
| --- | --- |
| Static generated date/location values | Currently supported by Cloud Chamber namelist rendering, but not product-controlled. |
| Location/date/start-time for radiation | Confirmed CM1 capability when radiation is active. |
| Metadata-only place/time from sounding | Product metadata path; should be supported first with observed sounding import. |
| Simple latitude/longitude/date/start-time values | Namelist/config-only when used by radiation. |
| Runtime file needs | None for metadata-only; radiation may require runtime files. |
| Arbitrary real-weather location claim | Future / unsupported. |

Rules:

- Time zone handling must be explicit. Preserve source-local time and UTC when
  known.
- Day of year should be derived from date when possible, not manually edited.
- `used_by_cm1` distinguishes metadata-only place/time from active radiation
  controls.
- Place/time should not imply realistic weather unless sounding, radiation,
  surface, and boundary assumptions support that claim.

## D. Radiation / Diurnal Behavior

Radiation controls are a second-stage capability after observed sounding
metadata. They require runtime and scientific validation.

Required fields:

- radiation enabled?
- `radopt`;
- `dtrad`;
- required runtime files;
- compatible microphysics;
- requested output fields/diagnostics;
- caveats about idealized forcing vs active radiation.

Draft shape:

```json
{
  "enabled": false,
  "radopt": 0,
  "dtrad_seconds": 300.0,
  "required_runtime_files": [],
  "compatible_microphysics": {
    "ptype": 5,
    "status": "likely_compatible_needs_validation"
  },
  "requested_outputs": [],
  "used_place_time": false,
  "caveats": [
    "radiation_disabled_current_baseline_forcing"
  ]
}
```

Capability distinctions:

| Item | Status |
| --- | --- |
| `radopt = 0` in current baseline packages | Currently supported by Cloud Chamber. |
| CM1 `radopt` options and place/time parameters | Confirmed CM1 capability. |
| RRTMG with current shallow-cumulus package | Likely CM1 capability needing validation. |
| `radopt`, `dtrad`, latitude/longitude/date/time | Namelist/config-only. |
| RRTMG/NASA-Goddard data files | Runtime file required when radiation is active. |
| Combining active radiation with idealized reference forcings | Unknown / needs experiment. |
| Radiation-driven realistic weather claim | Future / unsupported without validation. |

Rules:

- Do not enable radiation just because place/time metadata exists.
- Active radiation should request radiation-relevant outputs through the output
  product contract.
- Package review should explain whether radiation is disabled, metadata-only,
  or active in CM1.
- If radiation is active, runtime-file staging and microphysics compatibility
  must be validated before launch.

## E. Surface And Land Assumptions

Surface and land assumptions describe how Cloud Chamber represents the lower
boundary. They must avoid overclaiming hydrology or real land-surface behavior.

Required fields:

- surface model;
- land/water flag;
- land-use index;
- season;
- skin/deep temperature;
- roughness/stress path;
- surface sensible heat flux path;
- surface latent heat flux path;
- surface moisture/wetness proxy if any;
- surface assumptions/caveats.

Draft shape:

```json
{
  "surface_model": "cm1_simple",
  "land_water_flag": "water_or_reference_value",
  "land_use_index": 16,
  "season": 1,
  "skin_temperature_k": 299.28,
  "deep_temperature_k": 297.28,
  "roughness_stress_path": {
    "set_znt": 0,
    "set_ust": 1,
    "description": "reference stress/roughness path"
  },
  "surface_flux_path": {
    "sensible": "constant_or_reference",
    "latent": "constant_or_reference"
  },
  "wet_surface_proxy": {
    "enabled": false,
    "meaning": "none"
  },
  "caveats": []
}
```

Capability distinctions:

| Item | Status |
| --- | --- |
| Current ocean/simple surface settings and constant fluxes | Currently supported by Cloud Chamber baseline-family packages. |
| Surface models, land/water flag, land-use index, season, constant fluxes | Confirmed CM1 capability. |
| Uniform land or simple flux variants | Namelist/config-only, but needs scenario validation. |
| `LANDUSE.TBL` and radiation support data | Runtime file required where used. |
| Wet-surface / moisture-source proxy | Likely namelist/config-only if represented as constant latent flux or uniform moisture availability, but needs scientific validation. |
| Literal transpiration, soil hydrology, or real wetland behavior | Future / unsupported unless model support is added and documented. |

Rules:

- Use "surface moisture proxy" or "latent-flux proxy" unless CM1 support
  justifies stronger language.
- Preserve units and paths for sensible/latent heat flux controls.
- Result metadata should carry surface assumptions so Results and Explore can
  explain what was actually varied.

## F. Spatial Surface / Terrain Inputs

Spatial surface and terrain inputs are future work. They should not be exposed
as GIS/map controls until the preprocessing and CM1 initialization path is
known.

Required fields:

- input mode: `none`, `idealized_pattern`, `preprocessed_map`, `fortran_hook`;
- what is namelist-only;
- what requires generated files;
- what requires runtime files;
- what requires Fortran edits;
- what requires external preprocessing;
- provenance and limitations.

Draft shape:

```json
{
  "mode": "none",
  "namelist_only": [],
  "generated_files": [],
  "runtime_files": [],
  "fortran_edits": [],
  "external_preprocessing": [],
  "provenance": {},
  "limitations": [
    "no_realistic_gis_surface_input_currently_supported"
  ]
}
```

Capability distinctions:

| Item | Status |
| --- | --- |
| No spatial surface/terrain input | Currently supported by Cloud Chamber baseline-family packages. |
| Simple idealized patterns such as coastline or rough/smooth split | Confirmed or likely CM1 capability from examples/docs, needs Cloud Chamber validation. |
| Custom terrain through CM1 initialization hooks | Confirmed CM1 capability requiring Fortran edit or generated initialization path. |
| Arbitrary spatial surface categories | Fortran edit required and external preprocessing required. |
| GIS/map/imagery-derived surface realism | Future / unsupported for MVP. |

Rules:

- Do not call map-inspired or idealized patterns "real GIS".
- Any future map input must preserve source, projection, resolution,
  resampling, classification, and caveats.
- If Fortran initialization hooks are required, that is a high-risk architecture
  decision and not a normal package-generation tweak.

## G. Domain / Grid / Runtime / Compute Tier

Realistic inputs must be tied to compute and storage expectations. Better input
metadata can increase required fields, output volume, and wall-clock time.

Required fields:

- `nx`, `ny`, `nz`;
- `dx`, `dy`, `dz`;
- `ztop`;
- `timax`;
- `dt`;
- output cadence;
- expected output fields;
- expected output volume;
- expected wall-clock class;
- compute tier: `mac_quick_look`, `mac_serious_small`, `workstation`,
  `remote_hpc_future`.

Draft shape:

```json
{
  "grid": {
    "nx": 64,
    "ny": 64,
    "nz": 75,
    "dx_m": 100.0,
    "dy_m": 100.0,
    "dz_m": 40.0,
    "ztop_m": 18000.0
  },
  "runtime": {
    "timax_seconds": 21600.0,
    "dt_seconds": 3.0,
    "output_cadence_seconds": 3600.0
  },
  "expected_output": {
    "fields": ["qc", "w", "qv"],
    "volume_class": "small_to_medium",
    "estimated_size_gb": null
  },
  "compute_tier": {
    "id": "mac_serious_small",
    "expected_wall_clock_class": "minutes_to_hours",
    "confidence": "estimate_until_validated"
  }
}
```

Capability distinctions:

| Item | Status |
| --- | --- |
| Quick-look, standard, and deep run-size presets | Currently supported by Cloud Chamber scenario templates/package generation. |
| Local Mac deep runs with larger grids and more output | Supported but expensive; estimates need validation per scenario. |
| Additional output fields for realistic cases | Likely CM1 capability needing output/product validation. |
| Workstation/remote/HPC tiers | Future / unsupported as local product flow. |

Rules:

- Compute tiers are product promises, not decoration.
- Size and runtime estimates should be labeled as estimates until measured.
- Realistic inputs that require many fields, high resolution, or long runtime
  should not default to Mac quick-look.
- Expected output fields should hand off to the output product specification.

## H. Output / Diagnostics Requirements

Input specs must define what output and diagnostics are needed to decide
whether the run answered its physical question.

Required fields:

- required CM1 fields;
- required derived diagnostics;
- required surface/radiation diagnostics;
- required result-card fields;
- required Explore field availability;
- handoff to the output product specification.

Draft shape:

```json
{
  "required_cm1_fields": ["qc", "w", "qv"],
  "optional_cm1_fields": ["qr", "dbz", "rain"],
  "required_derived_diagnostics": [
    "cloud_formed",
    "first_cloud_time",
    "max_qc",
    "max_w",
    "min_w"
  ],
  "surface_radiation_diagnostics": {
    "required_when_radiation_enabled": [
      "radiative_tendencies",
      "surface_parameters"
    ],
    "required_when_surface_flux_varies": [
      "surface_sensible_heat_flux",
      "surface_latent_heat_flux"
    ]
  },
  "result_card_fields": [
    "input_source_summary",
    "sounding_source",
    "place_time_summary",
    "surface_assumption_summary",
    "caveats"
  ],
  "explore_field_availability": ["qc", "w", "qv"],
  "output_product_contract": "docs/contracts/output-product-specification.md"
}
```

Capability distinctions:

| Item | Status |
| --- | --- |
| Cloud/rain/updraft diagnostics from `qc`, `w`, optional `qr` | Currently supported by Cloud Chamber for ingested results. |
| Visualization-ready slices and scalar fields | Currently supported through backend APIs for selected fields. |
| Radiation and surface diagnostics | Confirmed CM1 output capability, but Cloud Chamber realistic-run requirements need validation. |
| Profile/time-height products | Defined in the output product specification; not yet implemented. |
| Browser-side raw NetCDF diagnostics | Future / unsupported; explicitly disallowed. |

Rules:

- Realistic input modes must state output requirements before implementation.
- Radiation and surface experiments should request fields that make the forcing
  inspectable.
- Result Cards must preserve input provenance and caveats, not just output
  diagnostics.
- Explore field availability should follow backend output-product contracts.

## First Supported Realistic-Input Path

The first implementation after this spec should be:

```text
observed/detailed sounding metadata + CM1 input_sounding conversion path
```

Minimum supported behavior:

- accept a tiny, testable observed/detailed sounding fixture or source record;
- preserve station/location, elevation, valid time/date, source/provider,
  source units, converted CM1 units, wind handling, smoothing/interpolation
  choices, and caveats;
- convert or render the profile into the CM1 `input_sounding` path;
- keep current validated non-sounding package settings unchanged until local
  validation approves changes;
- keep radiation disabled unless explicitly validated later;
- record place/time metadata as provenance even when not used by CM1 radiation;
- add tests with tiny fixtures only;
- do not add UI until the data contract and package behavior are reviewed.

## Product Boundaries

### Do Not Jump Straight To Real-World/GIS LES

"Realistic" does not mean "simulate any map point as weather." A real-world
LES claim would require coherent observed profiles, surface assumptions,
radiation, terrain/surface preprocessing, boundary assumptions, output fields,
diagnostics, and caveats.

### Do Not Implement Bench Mode UI Yet

Bench Mode should wait until realistic input records, output product records,
and validation categories exist. Otherwise the UI would expose attractive
controls without a trustworthy data contract.

### Do Not Implement #153 Surface Heterogeneity Yet

Surface heterogeneity is not a small UI extension. Arbitrary spatial surface
fields likely require external preprocessing and/or CM1 initialization hooks.

### Surface Moisture Is A Proxy Unless Proven Otherwise

Use honest wording such as:

```text
surface moisture proxy
latent flux proxy
moisture-source proxy
```

Do not call it literal transpiration, wetland hydrology, or soil moisture unless
the CM1 configuration and diagnostics support that claim.

## Relationship To Output Product Specification

This input specification decides what realistic LES input metadata means.

The output-side companion contract,
[Cloud Chamber output product specification](output-product-specification.md),
decides what Cloud Chamber produces from completed CM1 output.

Handoff points:

- input specs declare required CM1 fields and diagnostics;
- output products record field availability, time mapping, derived diagnostics,
  profiles, time-height products, visualization-ready payloads, and caveats;
- Results should show both input provenance and output outcomes;
- Explore should consume output products and selected-place diagnostics, not raw
  input or raw NetCDF;
- Storage should keep input packages, raw output, result metadata, and derived
  products distinguishable.

## PM Decisions Needed

Before implementation, PM/human review should decide:

- Which observed sounding source format is first: pasted text, local file,
  tiny fixture, or a specific provider export.
- Which profile sanity checks are launch blockers versus caveats.
- Where realistic input metadata lives before and after package generation:
  scenario controls, case manifest, run manifest, or a dedicated sidecar.
- How much place/time metadata must be user-facing before radiation is active.
- Whether location/date/radiation validation should target the existing
  shallow-cumulus package, a land reference case, or a separate validation
  package.
- How to word surface moisture controls without implying unsupported hydrology.
- What compute tier labels and output-size estimates are acceptable before
  local validation.

## Acceptance Checklist

- Observed/detailed sounding metadata is the first supported realistic-input
  path.
- Station/location, elevation, valid time/date, source/provider, units,
  converted units, wind handling, smoothing/interpolation choices, and caveats
  are preserved from the beginning.
- Place/time metadata exists even when radiation is disabled.
- Radiation remains a later validated capability, not an automatic consequence
  of location metadata.
- Surface/land assumptions distinguish uniform settings, proxies, runtime
  files, and unsupported real hydrology.
- Spatial GIS/map/terrain inputs are future work requiring preprocessing and/or
  CM1 initialization paths.
- Compute tiers include output volume and wall-clock confidence.
- Output/diagnostic requirements hand off to the output product specification.
- Raw namelist fields stay out of primary product controls.
- No UI, package-generation behavior, scenario family, CM1 source, or real CM1
  execution changes are implied by this spec.
