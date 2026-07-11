# Surface Flux Control Validation

Status: research validation for issue #286

PM recommendation: keep metadata-only / not exposed yet.

Cloud Chamber should not expose surface sensible and latent heat flux as normal
Build controls yet. CM1 has the needed constant-flux namelist knobs, and Cloud
Chamber already has a partial generation/output path for surface-flux fields.
The missing trust layer is end-to-end evidence: package generation, CM1 run,
ingest, result metadata, and output-product inspection must show that changed
surface-flux assumptions are active, unit-safe, and understandable before these
become user-facing controls.

This is not a recommendation to drop surface forcing. It is a recommendation to
treat surface forcing as an explicit, caveated lower-boundary proxy until smoke
validation proves the path.

## Evidence Checked

- CM1 r21.1 `README.namelist` documents `isfcflx`, `sfcmodel`, and the
  `sfcmodel = 1` constant-flux controls in the surface-model section.
- CM1 r21.1 `README.namelist` documents `output_sfcflx`,
  `output_sfcparams`, and `output_sfcdiags` in the output section.
- `app/backend/cloud_chamber/cm1_input_contract.py` currently renders the
  non-triggered observed-sounding surface-flux settings and output switches.
- `app/backend/cloud_chamber/visualization_data.py` currently defines surface
  sensible/latent heat flux field aliases when those fields are present.
- Existing docs in `docs/research/realistic-les-input-architecture.md` already
  classify uniform surface fluxes as likely namelist/config-only and spatially
  varying realistic surface inputs as a later architecture lane.

No qualifying local CM1 smoke matrix was found or added in this PR. That missing
manual evidence is the reason this recommendation stops at metadata-only rather
than "expose as controls now."

## Product Question

The user-facing question is:

```text
Given an observed sounding, what happens when the lower boundary supplies a
controlled amount of heat and moisture to the boundary layer?
```

That is different from:

```text
What did the real ground, vegetation, soil moisture, radiation, and terrain do
at this place and time?
```

The first question can plausibly be tested with a uniform constant surface-flux
proxy. The second needs a validated land-surface, radiation, place/time, and
surface-state architecture that Cloud Chamber does not have yet.

## CM1 Controls

CM1 r21.1 documents direct support for surface heat and moisture fluxes:

| Control | CM1 meaning | Validation note |
| --- | --- | --- |
| `isfcflx` | Include surface fluxes of heat and moisture. | Needed for any surface-flux experiment. |
| `sfcmodel` | Surface model used to calculate fluxes and stress. | Constant-flux controls require `sfcmodel = 1`. |
| `oceanmodel` | Ocean/water surface model. | `sfcmodel = 1` requires `oceanmodel = 1`. |
| `set_flx` | Impose constant surface heat fluxes. | Must be `1` for `cnst_shflx` and `cnst_lhflx` to act as prescribed controls. |
| `cnst_shflx` | Constant surface sensible heat flux if `set_flx = 1`. | CM1 documents units as `K m/s`, not W/m2. |
| `cnst_lhflx` | Constant surface latent heat flux if `set_flx = 1`. | CM1 documents units as `g/g m/s`, not W/m2. |
| `set_znt`, `cnst_znt` | Constant roughness-length switch and value. | Relevant to stress and surface-layer interpretation. |
| `set_ust`, `cnst_ust` | Constant friction-velocity switch and value. | Current observed path uses fixed friction velocity. |

CM1 also states that default initial surface conditions are spatially uniform
and that arbitrary spatially varying surface temperature, land/water flag, and
land-use values must be coded in `init_surface.F`. That keeps this validation in
the uniform-proxy lane, not the realistic land-surface lane.

Important unit decision: product controls should not expose `cnst_shflx` and
`cnst_lhflx` as if they are already W/m2. A future UI may show W/m2 or
human-readable strength levels, but the conversion to CM1 namelist values must
be explicit, documented, copied into metadata, and verified against CM1 output.

## Current Cloud Chamber State

Current non-triggered observed-sounding generation already follows a simple
surface-flux path:

| Current setting | Current value |
| --- | --- |
| `isfcflx` | `1` for non-triggered observed evolution |
| `sfcmodel` | `1` for non-triggered observed evolution |
| `oceanmodel` | `1` for non-triggered observed evolution |
| `set_flx` | `1` for non-triggered observed evolution |
| `cnst_shflx` | `8.0e-3` |
| `cnst_lhflx` | `5.2e-5` |
| `set_znt` | `0` |
| `cnst_znt` | `0.00` |
| `set_ust` | `1` |
| `cnst_ust` | `0.28` |

Triggered deep-potential runs currently turn this surface-flux path off and use
the idealized warm-bubble trigger instead. That is appropriate for triggered
potential, but it does not answer the surface-forced moist-evolution question.

The current observed path is therefore best described as:

```text
uniform fixed-surface-temperature, fixed-moisture-availability,
constant sensible/latent flux proxy with fixed friction velocity
```

It is not:

```text
real land-surface heating
real soil moisture
transpiration
real wet-ground behavior
diurnal radiation forcing
place/time surface-energy budget
```

## Runtime Files

For the current `sfcmodel = 1`, `set_flx = 1`, uniform constant-flux path, no new
Cloud Chamber package architecture appears necessary. Cloud Chamber already
stages the existing external runtime-file checklist, including `LANDUSE.TBL`, as
part of the current reference-derived package path.

This finding does not generalize to radiation, realistic land categories,
spatially varying surface fields, or arbitrary GIS-derived surface inputs. Those
paths may require additional runtime files, preprocessing, or CM1 source-level
customization.

## Output Evidence Required

To expose controls safely, a completed result must prove both the forcing and
the atmospheric response. At minimum, the run configuration should request
surface and process outputs:

| Output | Why it matters |
| --- | --- |
| `output_sfcflx` | Records surface fluxes of potential temperature, water vapor, and exchange coefficients when `isfcflx = 1`. |
| `output_sfcparams` | Records parameters used by surface, soil, or ocean models. |
| `output_sfcdiags` | Records surface-layer diagnostics such as 10 m winds, 2 m temperature/moisture, and roughness where available. |
| `output_qv`, `output_th`, `output_prs` | Shows lower-atmosphere thermodynamic response. |
| `output_q`, `output_w`, `output_dbz`, `output_rain` | Shows cloud, updraft, rain water aloft, reflectivity, and surface rain outcomes. |

Cloud Chamber already has field definitions for surface sensible and latent heat
flux aliases such as `hfx`, `lhfx`, `sensible_heat_flux`, and
`latent_heat_flux`, and backend output-product tests cover surface-flux time
series from fixture data. That means the product layer can represent the fields
when they exist. It does not prove that CM1 emits the expected field names and
units for all real runs or that changed flux values produce expected responses.

## Smoke Validation Matrix

The implementation should remain metadata-only until this matrix has local CM1
evidence:

| Run | Change | Required evidence |
| --- | --- | --- |
| Control/default | Current non-triggered observed defaults. | CM1 exits cleanly, ingest succeeds, surface-flux outputs are present when requested, and metadata records the exact flux assumptions. |
| Higher sensible heat flux | Increase the prescribed sensible-flux control only. | Surface sensible flux output changes in the expected direction; lower-boundary theta and boundary-layer response are visible or explicitly absent. |
| Higher latent heat flux | Increase the prescribed latent-flux control only. | Surface moisture-flux output changes in the expected direction; near-surface qv response is visible or explicitly absent. |
| Combined sensible + latent | Increase both prescribed controls. | Both flux outputs change, thermodynamic response is inspectable, and cloud/updraft/precipitation differences are distinguishable from the control run. |

Each smoke record should capture:

- run ID
- sounding station, location, and observed time
- model duration
- domain size, cell count, dx/dy, and model top
- saved-output cadence
- requested diagnostic set
- exact CM1 namelist values for `isfcflx`, `sfcmodel`, `set_flx`,
  `cnst_shflx`, `cnst_lhflx`, `set_znt`, `cnst_znt`, `set_ust`, and `cnst_ust`
- CM1 exit status
- ingest status
- units and max/min/mean time series for surface sensible and latent flux when
  available
- qv/theta response when available
- cloud, updraft, rain-water-aloft, surface-rain, and reflectivity outcomes when
  available
- caveats explaining proxy status and missing fields

The smoke evidence belongs in docs or PR notes as summarized metrics and run
IDs only. Generated packages, NetCDF files, logs, runtime directories,
screenshots, traces, videos, SSH config, and local settings must remain
uncommitted.

## Metadata Requirements

Before controls are exposed, package, run, and result metadata should preserve:

- selected surface-forcing mode, such as `constant_uniform_surface_flux_proxy`
- product-level selected sensible-flux value and unit
- product-level selected latent-flux value and unit
- translated CM1 values for `cnst_shflx` and `cnst_lhflx`
- translation method and assumptions, if product units differ from CM1 units
- `sfcmodel`, `oceanmodel`, `isfcflx`, `set_flx`, roughness, and friction
  velocity settings
- requested surface output switches
- whether flux outputs were actually ingested
- caveats that the run is not a real land-surface, soil-hydrology,
  transpiration, wet-ground, radiation, or place/time energy-budget simulation

Results and Explore should show the same assumption set beside the outcome so a
surface-forced run cannot be mistaken for an unforced observed evolution or a
real-weather reconstruction.

## Product Language

Recommended user-facing wording:

- "surface sensible heat flux"
- "surface latent heat flux proxy"
- "surface moisture-flux proxy"
- "uniform lower-boundary heat/moisture forcing"
- "constant over the domain and model time"

Avoid until a stronger model path is validated:

- "transpiration"
- "soil moisture"
- "wet ground"
- "evaporation from the real surface"
- "real land-surface heating"
- "diurnal heating"
- "place/time surface-energy budget"

## Decision

Keep surface sensible and latent heat flux metadata-only / not exposed yet.

Rationale:

1. CM1 supports a simple constant-flux path, and Cloud Chamber already uses the
   relevant non-triggered observed-run switches.
2. The raw CM1 control units are not the product units users will expect, so a
   safe implementation needs an explicit translation layer and metadata copy.
3. Surface-flux output fields are represented in Cloud Chamber fixtures, but
   real-run smoke evidence has not yet shown that changed prescribed flux values
   are emitted, ingested, and explained correctly.
4. The current path is a uniform proxy, not a realistic land-surface or
   transpiration model.

Next implementation should be a narrow surface-forced proxy path, not a broad
land-surface feature:

- add explicit product-level sensible/latent flux selections;
- translate those selections to CM1 `cnst_shflx` and `cnst_lhflx`;
- request `output_sfcflx`, `output_sfcparams`, and `output_sfcdiags`;
- copy the full assumption set into package/run/result metadata;
- run the smoke matrix above before moving the controls out of advanced or
  metadata-only status.
