# Archived Contract: Run Recipe And Story-Mapping

> **Status: Historical mixed proposal contract**
>
> This document is preserved as historical design and implementation context. It is not an active implemented contract and does not establish current product direction, supported Recipe status, roadmap priority, MVP scope, or final application architecture. Current product semantics are defined in `docs/product/APPLICATION_SEMANTICS.md`.

# Run Recipe And Story-Mapping Contract

Status: forward product/data contract

This contract defines the bridge between cached-sounding hypotheses and CM1 run
configuration. It sits between
[Sounding Candidate Screening](sounding-candidate-screening.md) and
[Analyzer Hypothesis And Output-Signature](analyzer-hypothesis-output-signature.md).

The product question is:

```text
Given this sounding hypothesis, which explicit CM1 run recipe can test it,
with what assumptions, outputs, caveats, and comparison rules?
```

Ingredient screening by itself does not predict CM1 output. A run recipe by
itself does not validate a hypothesis. Results comparison is meaningful only
when the saved hypothesis, run recipe, assumptions, output fields, duration,
cadence, and ingested diagnostics line up.

## Scope Boundary

This is a docs and data-contract issue. It does not implement package
generation, add raw namelist editing, run CM1 in CI, add a generic Compare tab,
or commit generated artifacts.

The current implementation uses `run_recipe` plus explicit run-configuration
fields. Product surfaces should describe the user-facing recipe and question;
there is no separate package-family compatibility layer in the forward
contract.

## Core Terms

- **Ingredient score**: pre-run sounding evidence used to decide what atmosphere
  is interesting to try. It is not an outcome prediction.
- **Hypothesis**: a story-specific interpretation of the sounding, plus
  evidence, caveats, and eventually an active assumption set.
- **Run recipe**: a named CM1 configuration path with declared assumptions,
  shape, required inputs, required outputs, current support status, and CM1
  mapping metadata.
- **Assumption set**: the explicit run context under which a predicted output
  signature is allowed. No assumption set means no predicted signature.
- **Recipe fit**: whether a recipe can test a selected hypothesis now,
  partially, only after a future recipe, or not at all.
- **Predicted output signature**: a CM1-observable set of expected diagnostics
  that Results may compare against only after compatible output exists.
- **Comparison state**: the #275 predicted-vs-actual result state:
  `supported`, `partially_supported`, `contradicted`, `inconclusive`, or
  `not_comparable`.

## Run Recipe Object

Run recipes should be represented as structured backend-owned data.

```yaml
run_recipe:
  recipe_id: string
  display_name: string
  product_question: string
  compatible_story_ids: [string]
  assumption_set_id: string
  assumption_mode: observed_surface_forced_evolution
    | surface_forced_evolution
    | differential_surface_forced_evolution
    | explicit_thermal_initiation
    | elevated_forced_evolution
    | future
  run_shape:
    duration_seconds: number | null
    horizontal_cell_count: number | null
    domain_x_m: number | null
    domain_y_m: number | null
    dx_m: number | null
    dy_m: number | null
    model_top_m: number | null
    output_cadence_seconds: number | null
    diagnostic_set: essential | process | full | null
  forcing:
    trigger:
      mode: none | future_explicit_trigger | unavailable
      description: string
    surface_sensible_heat_flux:
      mode: current_recipe_default | prescribed | disabled | future | unavailable
      units: string | null
      value: number | null
      caveats: [string]
    surface_latent_heat_flux:
      mode: current_recipe_default | prescribed | disabled | future | unavailable
      units: string | null
      value: number | null
      caveats: [string]
    radiation:
      mode: disabled | prescribed_time_place | future_interactive | unavailable
      place_time_required: boolean
      caveats: [string]
    large_scale_lift:
      mode: none | prescribed | future | unavailable
      caveats: [string]
    convergence:
      mode: none | prescribed | future | unavailable
      caveats: [string]
  required_inputs:
    observed_temperature_profile: required | optional | unavailable
    observed_moisture_profile: required | optional | unavailable
    observed_wind_profile: required | optional | unavailable
    place_time: required | optional | future | unavailable
    surface_context: required | optional | future | unavailable
  required_outputs:
    fields: [string]
    diagnostics: [string]
  current_support:
    status: supported | caveated | blocked | future
    caveats: [string]
  cm1_mapping:
    run_recipe: generated_reference_lower_atmosphere
      | observed_surface_forced_evolution
      | differential_surface_forced_evolution
      | deep_tower_benchmark
      | future
    run_configuration_defaults:
      duration: string | null
      horizontal_cell_count: string | null
      domain_size: string | null
      output_cadence: string | null
      requested_fields: [string]
    namelist_summary: [string]
    runtime_files_needed: [string]
  comparison_contract:
    comparable_when: [string]
    not_comparable_when: [string]
    missing_field_state: inconclusive
```

The schema is intentionally product-shaped. Raw CM1 namelist keys remain
advanced metadata under `cm1_mapping` or a later recipe-detail API.

## Assumption Modes

### `observed_surface_forced_evolution`

An observed surface-forced recipe asks what the initialized atmosphere does
under explicit run-shape and lower-boundary forcing assumptions. It must not
imply a weather forecast. If surface fluxes, radiation, or large-scale forcing
are recipe defaults rather than place/time-derived values, predicted signatures
must say so.

### `surface_forced_evolution`

A surface-forced recipe asks what happens when lower-boundary sensible and/or
latent heat flux assumptions are explicit. Humid, drizzle, warm-rain, fog,
post-frontal, and boundary-layer hypotheses need this mode before product copy
can claim surface-forced precipitation or low-cloud signatures.

### `differential_surface_forced_evolution`

A differential surface-forced recipe asks whether one localized lower-boundary
heat/moisture patch can focus convergence, updraft initiation, cloud growth, and
later rain/reflectivity differently from the surrounding surface. It is a
current v0 patch experiment, not a real land-surface, radiation, GIS, front, or
dryline model. Cloud Chamber applies it through explicit CM1 source
customization at launch and must not silently fall back to uniform forcing.

### `radiation_place_time_evolution`

A future radiation/place-time recipe asks whether diurnal radiation, location,
date/time, and surface context support fog, low cloud, suppression, or later
boundary-layer growth. It follows surface-flux validation unless product
direction changes.

### `elevated_forced_evolution`

An elevated recipe asks whether an above-surface source layer can sustain cloud
or convection. It needs source-layer, forcing, and output assumptions that the
current observed-sounding run builder does not supply.

### Removed Or Not Active

Artificial atmospheric perturbation recipes from the earlier deep-potential
direction are not current product paths. Current observed-sounding experiments
use no artificial atmospheric trigger and rely on explicit surface-forcing and
run-shape assumptions. Differential surface forcing is a current lower-boundary
patch recipe, not an atmospheric-trigger recipe.

## Current Recipe Catalog

### `observed_surface_forced_evolution_v0`

```yaml
recipe_id: observed_surface_forced_evolution_v0
display_name: Observed-sounding surface-forced evolution v0
product_question: What does this observed atmosphere do under the selected
  numeric uniform lower-boundary heat/moisture forcing?
assumption_set_id: observed_surface_forced_evolution_v0_assumptions
assumption_mode: observed_surface_forced_evolution
run_shape:
  duration_seconds: 21600 | configured
  horizontal_cell_count: 64 | 96 | 128 | 192 | 256 | 384 | configured
  domain_width_m: 6400 | 12800 | 60000 | 120000 | configured
  model_top_m: current observed-sounding LES model top
  output_cadence_seconds: 3600 | 900 | 300 | configured
  requested_fields: full_output_field_set
forcing:
  trigger: { mode: none }
  surface_sensible_heat_flux:
    { mode: prescribed, units: K m/s, value: configured }
  surface_latent_heat_flux:
    { mode: prescribed, units: g/g m/s, value: configured }
  radiation: { mode: disabled }
  large_scale_lift: { mode: none }
  convergence: { mode: none }
required_inputs:
  observed_temperature_profile: required
  observed_moisture_profile: required
  observed_wind_profile: required
required_outputs:
  fields: [qv, qc, w, qr, rain, dbz, u, v, th, prs, hfx, qfx]
  diagnostics: [first_cloud, max_qc, cloud_top, max_updraft_w]
current_support:
  status: supported
  caveats:
    - Numeric fluxes are uniform proxy controls, not a real place/time
      surface-energy budget.
    - Radiation, terrain, GIS surface initialization, and large-scale forcing
      are not part of v0.
    - Scores remain ingredient guidance until a predicted signature exists.
cm1_mapping:
  run_recipe: observed_surface_forced_evolution
  run_configuration_defaults:
    duration: short_6h
    horizontal_cell_count: cells_128
    domain_size: wide_12km
    output_cadence: standard_15min
    requested_fields: full_output_field_set
```

This v0 recipe can inspect shallow cloud, humid/rainy, capped, and deep-candidate
signals when the predicted signature can be evaluated from full CM1 output fields
and enough duration/cadence. Deep organization, cold-pool, and storm-mode claims
remain caveated until comparison diagnostics and the selected forcing recipe can
support those claims.

### `differential_surface_forced_evolution_v0`

```yaml
recipe_id: differential_surface_forced_evolution_v0
display_name: Differential surface-forced evolution v0
product_question: What happens when one part of the lower boundary is heated
  and/or moistened more strongly than its surroundings?
assumption_set_id: differential_surface_forced_evolution_v0_assumptions
assumption_mode: differential_surface_forced_evolution
run_shape:
  duration_seconds: 21600 | configured
  horizontal_cell_count: 64 | 96 | 128 | 192 | 256 | 384 | configured
  domain_width_m: 6400 | 12800 | 60000 | 120000 | configured
  model_top_m: current observed-sounding LES model top
  output_cadence_seconds: 3600 | 900 | 300 | configured
  requested_fields: full_output_field_set
forcing:
  trigger: {mode: none}
  surface_sensible_heat_flux:
    mode: prescribed_background_plus_patch
    units: K m/s
    value: configured
  surface_latent_heat_flux:
    mode: prescribed_background_plus_patch
    units: g/g m/s
    value: configured
  surface_patch:
    shape: circle
    center: domain_center_v0
    radius_m: configured
    taper: raised_cosine
    ramp_seconds: configured
  radiation: {mode: disabled}
  large_scale_lift: {mode: none}
  convergence: {mode: emergent_from_surface_patch}
required_inputs:
  observed_temperature_profile: required
  observed_moisture_profile: required
  observed_wind_profile: required
required_outputs:
  fields: [qv, qc, w, qr, rain, dbz, u, v, th, prs, hfx, qfx, updraft_helicity]
  diagnostics:
    - emitted_surface_flux_contrast
    - convergence_or_divergence_response
    - localized_updraft_response
    - coherent_cloud_object_top
    - rain_water_aloft_onset
    - max_surface_rain
    - max_dbz
current_support:
  status: local_footprint_smoke_validated
  caveats:
    - The v0 patch is centered, circular, and idealized.
    - It is not a real land-surface, soil-moisture, vegetation, radiation,
      terrain, GIS, front, or dryline model.
    - Cloud Chamber copies the local external CM1 source tree into an isolated
      runtime build tree, patches that copy, rebuilds CM1, and launches the
      copied custom executable.
    - Differential surface forcing is local-only; LAN worker source
      customization remains unsupported.
    - Missing, malformed, or hash-mismatched patch files block the run rather
      than silently falling back to uniform forcing.
    - A runtime-local CM1 compile plus emitted hfx/qfx forcing-footprint smoke
      has verified the v0 local execution path. Per-run localized-response
      diagnostics now preserve patch geometry, emitted footprint, convergence
      when u/v are available, and patch-to-response distance metrics; #307
      still needs matched dynamic-response validation before closure.
    - Surface-driven convergence, localized updrafts, coherent cloud growth,
      rain-water aloft, surface rain, and reflectivity remain diagnostics to
      inspect, not guaranteed outcomes.
cm1_mapping:
  run_recipe: differential_surface_forced_evolution
  runtime_files_needed:
    - surface_forcing_patch.json
    - cloud_chamber_surface_forcing_patch.dat
    - cm1_source_customization.json
```

## Domain And Duration Expectations

Observed surface-forced experiments use the selected run configuration as a
real assumption. Cloud Chamber must not silently coerce a selected larger domain
into a smaller one.

- `local_6km`: cheap boundary-layer experiment. Useful for smoke/scout runs and
  local cloud/moisture response; not a storm-organization domain.
- `wide_12km`: stronger local experiment. Useful for observed winds and local
  cloud/updraft response; still limited for storm organization.
- `regional_60km`: larger boundary-layer/initiation experiment. More suitable
  for deep-candidate exploration when cost/output volume is acceptable.
- `regional_120km`: expensive regional experiment. More suitable for organized
  convection, cold-pool, or outflow exploration when outputs and diagnostics can
  support those claims.

Short/smoke runs check package health and early response only. Six-hour and
longer science runs can support stronger evolution claims, but no-storm results
remain caveated by selected forcing, domain, grid, duration, output cadence, and
diagnostic availability.

### `observed_capped_evolution_v1`

```yaml
recipe_id: observed_capped_evolution_v1
display_name: Observed-sounding capped evolution
product_question: Does the observed profile limit vertical growth under the
  current no-artificial-trigger surface-forced defaults?
assumption_set_id: observed_surface_forced_evolution_v0_assumptions
assumption_mode: observed_surface_forced_evolution
required_outputs:
  fields: [qc, w, th, qv]
  diagnostics: [first_cloud, cloud_top, max_qc, max_updraft_w]
current_support:
  status: caveated
  caveats:
    - The cap comes from the input sounding; there is no separate cap-control
      recipe yet.
    - Comparison needs enough model time and cadence to distinguish delayed
      growth from missing output.
cm1_mapping:
  run_recipe: observed_surface_forced_evolution
```

This recipe is a specialized view of the current observed-sounding
path. It can support a capped/suppressed comparison only when the run is long
enough and the signature does not require unsupported forcing.

### `surface_forced_moist_evolution_v1`

```yaml
recipe_id: surface_forced_moist_evolution_v1
display_name: Moist surface-forced evolution
product_question: Does a moist observed lower atmosphere produce cloud, rain
  water aloft, surface rain, or reflectivity under explicit surface-forcing
  assumptions?
assumption_set_id: surface_forced_current_recipe_v1
assumption_mode: surface_forced_evolution
required_outputs:
  fields: [qc, w, qr, rain, dbz]
  diagnostics:
    - first_cloud
    - max_qc
    - max_updraft_w
    - rain_water_aloft_onset
    - max_surface_rain
    - max_dbz
current_support:
  status: caveated
  caveats:
    - Current surface fluxes are numeric uniform proxy values, not validated
      place/time surface-energy inputs.
    - `qr` is rain water aloft, `rain` is surface rain, and `dbz` is
      reflectivity; they must be evaluated separately.
cm1_mapping:
  run_recipe: observed_surface_forced_evolution
```

This is the honest bridge for `humid_rainy_candidate`: Cloud Chamber may run a
moist observed-sounding experiment now, but precipitation signatures are only
testable when the required fields are requested, ingested, and clearly labeled.

### `deep_tower_benchmark_v0`

```yaml
recipe_id: deep_tower_benchmark_v0
display_name: Deep-Tower Benchmark
product_question: What convective ceiling does this observed atmosphere show
  under explicit idealized thermal initiation?
assumption_set_id: deep_tower_benchmark_v0_assumptions
assumption_mode: explicit_thermal_initiation
required_outputs:
  fields: [qv, qc, w, qr, rain, dbz, u, v, th, updraft_helicity]
  diagnostics:
    - first_cloud
    - first_deep_convection
    - max_updraft_w
    - rain_water_aloft_onset
    - max_surface_rain
    - max_dbz
current_support:
  status: supported
  caveats:
    - The trigger is CM1's stock `iinit = 3` three-warm-bubble line; it is not
      a real front, dryline, terrain feature, or observed boundary.
    - Surface heat/moisture fluxes, radiation, terrain, GIS surface
      initialization, and large-scale forcing are disabled in v0.
cm1_mapping:
  run_recipe: deep_tower_benchmark
```

Deep-convection candidate stories route to this benchmark when an observed
sounding has a complete rendered wind profile. The result can inspect whether
deep cloud, strong updraft, rain-water aloft, surface rain, and reflectivity
occur under the explicit trigger. Surface-forced and differential surface patch
recipes remain separate lower-boundary initiation questions.

### `squall_line_cold_pool_future`

```yaml
recipe_id: squall_line_cold_pool_future
display_name: Squall-line / cold-pool evolution
assumption_mode: future
required_outputs:
  fields: [qc, w, qr, rain, dbz, th, u, v]
  diagnostics:
    - organized_line_structure
    - cold_pool_proxy
    - outflow_boundary
    - surface_rain
current_support:
  status: future
cm1_mapping:
  run_recipe: future
```

The current observed-sounding surface-forced recipe may be a caveated first
experiment, but it does not contain line forcing or validated cold-pool
diagnostics.

### `elevated_forced_evolution_future`

```yaml
recipe_id: elevated_forced_evolution_future
display_name: Elevated-source-layer evolution
assumption_mode: elevated_forced_evolution
required_outputs:
  fields: [qc, w, qr, rain, dbz, th, u, v]
  diagnostics:
    - source_layer_cloud_or_updraft
    - surface_decoupling
    - precipitation_onset
current_support:
  status: future
cm1_mapping:
  run_recipe: future
```

Elevated convection is not comparable unless the recipe can represent the
source layer and forcing assumptions being tested.

## Initial Story-To-Recipe Mapping

| Story ID                          | Primary recipe                                                                           | Recipe fit                                                                                        | Required assumptions                                                                                                                  | Required outputs for comparison                                                 | Result comparison intent                                                                                                                                     |
| --------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `shallow_cumulus_candidate`       | `observed_surface_forced_evolution_v0`                                                   | `testable_now` when the run is long enough                                                        | no artificial trigger; numeric uniform surface heat/moisture fluxes; complete observed temperature/moisture/wind profile              | `qv`, `qc`, `w`, time and vertical coordinates                                  | cloud formation, cloud top/depth, persistence, vertical velocity                                                                                             |
| `dry_failed_candidate`            | `observed_surface_forced_evolution_v0`                                                   | `testable_now` when duration/cadence can support a no-cloud conclusion                            | no artificial trigger; numeric uniform surface heat/moisture fluxes; complete observed temperature/moisture/wind profile              | `qv`, `qc`, `w`, time coordinate                                                | weak/no cloud with meaningful vertical motion; moisture limitation remains caveated                                                                          |
| `capped_suppressed_candidate`     | `observed_capped_evolution_v1`                                                           | `partially_testable`                                                                              | no explicit trigger; cap comes from observed profile; enough run time to observe delayed growth                                       | `qc`, `w`, `th`, time and vertical coordinates                                  | reduced cloud depth, delayed cloud, or capped vertical motion                                                                                                |
| `humid_rainy_candidate`           | `surface_forced_moist_evolution_v1`                                                      | `partially_testable` until surface-flux smoke evidence is broad                                   | numeric uniform surface-flux assumptions; no artificial trigger; precipitation fields requested                                       | `qc`, `w`, `qr`, `rain`, `dbz` when precipitation is predicted                  | cloud, rain water aloft, surface rain, and reflectivity evaluated separately                                                                                 |
| `severe_thunderstorm_environment` | `deep_tower_benchmark_v0` plus future observed-boundary and differential forcing recipes | `partially_testable`                                                                              | explicit CM1 `iinit = 3` thermal trigger; surface fluxes disabled; complete observed wind profile; domain/duration/resolution caveats | `qc`, `w`, `qr`, `rain`, `dbz`, `u`, `v`, `th`, updraft diagnostics             | whether the observed environment can support deep cloud, rain, and strong updrafts under the benchmark trigger; not an observed initiation or forecast claim |
| `supercell_environment`           | `deep_tower_benchmark_v0` plus future observed-boundary and storm-mode recipes           | `partially_testable`                                                                              | explicit CM1 `iinit = 3` thermal trigger; surface fluxes disabled; complete observed wind profile; rotation diagnostics caveated      | `qc`, `w`, `qr`, `rain`, `dbz`, `u`, `v`, `th`, updraft-helicity when available | deep convection and organization evidence under the benchmark trigger; not a tornado or forecast product                                                     |
| `high_cape_pulse_storm`           | `observed_surface_forced_evolution_v0` plus future differential forcing                  | `partially_testable`                                                                              | no artificial trigger; high-CAPE interpretation caveated until parcel diagnostics are implemented                                     | `qc`, `w`, `qr`, `rain`, `dbz`                                                  | strong buoyant updraft and deep cloud if CM1 produces them under selected forcing                                                                            |
| `dry_microburst_inverted_v`       | `observed_surface_forced_evolution_v0` plus future downdraft diagnostics                 | `partially_testable` only if precipitation/downdraft pathway develops                             | precipitation aloft; subcloud dry-layer evidence; downdraft diagnostics caveated                                                      | `qr`, `rain`, `w`, `th`, near-surface wind fields when implemented              | rain water aloft, downdraft/cooling/outflow evidence; not a wind-gust forecast                                                                               |
| `squall_line_cold_pool_candidate` | `observed_surface_forced_evolution_v0` plus future `squall_line_cold_pool_future`        | `partially_testable` for generic deep-cloud evidence; `requires_recipe` for line/cold-pool claims | no line trigger now; future line forcing and cold-pool diagnostics for the full story                                                 | `qc`, `w`, `qr`, `rain`, `dbz`, `th`, `u`, `v`                                  | current run can inspect storm/deep-cloud evidence; cold-pool/line match is future                                                                            |
| `elevated_convection`             | `elevated_forced_evolution_future`                                                       | `requires_recipe` unless a chosen recipe declares source-layer assumptions                        | elevated source layer, forcing, and surface-decoupling assumptions                                                                    | `qc`, `w`, `qr`, `rain`, `dbz`, layer diagnostics                               | future elevated cloud/updraft source-layer comparison                                                                                                        |
| `needs_review`                    | none by default; user selects a concrete hypothesis first                                | `not_evaluated`                                                                                   | depends on selected hypothesis                                                                                                        | depends on selected hypothesis                                                  | cannot compare until an active story and recipe are chosen                                                                                                   |
| `poor_or_incomplete_candidate`    | none                                                                                     | `blocked`                                                                                         | package-readiness blockers must be resolved                                                                                           | none                                                                            | no runnable recipe until profile/input safety passes                                                                                                         |

Deep-convection stories should not silently promise observed initiation. The
current observed-sounding run path can inspect deep-cloud/updraft evidence with
the explicit Deep-Tower Benchmark trigger; Results must keep observed-boundary,
differential-initiation, storm-mode, cold-pool, and severe-weather claims
caveated unless the required fields and diagnostics exist.

## Pre-Run Validation Feed (#284)

Pre-run validation should evaluate the active hypothesis and selected recipe
together. It should fail, warn, or caveat before package generation when:

- no compatible recipe exists for the selected hypothesis;
- the recipe requires observed temperature, moisture, or wind profiles that are
  missing, incomplete, nonfinite, too shallow, or unsafe after model-z
  conversion;
- the predicted output signature requires fields that the recipe will not
  request;
- duration, model top, domain width, or output cadence are too weak for the
  selected signature;
- a recipe assumption is missing, such as numeric surface fluxes for
  drizzle/warm-rain claims, differential forcing for initiation claims, or
  source-layer assumptions for elevated convection;
- expected cost, runtime, or output volume should be surfaced before launch.

Validation should distinguish:

```text
package cannot be generated
package can run but cannot test this hypothesis
package can partially test this hypothesis with caveats
package can test this hypothesis under explicit assumptions
```

Those are product trust states, not scientific outcomes.

## Results Comparison Feed (#275)

Results should preserve and compare the tuple:

```text
hypothesis_id
story_id
recipe_id
assumption_set_id
predicted_output_signature_id
required_output_fields
ingested_diagnostics
```

Comparison rules:

- If the run recipe is incompatible with the active hypothesis, use
  `not_comparable`.
- If required output fields, duration, cadence, or diagnostics are missing, use
  `inconclusive` and field-level `unavailable` or `not_requested`.
- If some expected signatures are present and others are missing or caveated,
  use `partially_supported`.
- Use `supported` only when the compatible recipe produced the required
  evidence under the saved assumptions.
- Use `contradicted` only when the compatible recipe, required outputs, and
  enough run context exist and the evidence clearly goes against the predicted
  signature.
- Keep `qr` as rain water aloft, `rain` as surface rain or accumulated
  precipitation at ground, and `dbz` as reflectivity.

Do not use trigger-failed language for observed-sounding runs. If deep cloud or
strong updraft does not occur, describe the observed CM1 outcome under the saved
forcing and run-shape assumptions. No storm under observed surface-forced v0 is
not, by itself, a failed sounding hypothesis or disproven deep-convection
potential.

## Product Copy Rules

- Say "ingredient score" or "screening score" before a run exists.
- Say "predicted output signature" only after the analyzer has an explicit
  assumption set and compatible recipe.
- Say "not testable with current run recipes" when no current recipe can test
  the selected hypothesis.
- Say "partially testable" when the current recipe can inspect part of the
  hypothesis but lacks required forcing, diagnostics, or validation.
- Say "observed-sounding run" or "surface-forced observed evolution" for current
  Build packages, and disclose the numeric surface/radiation/forcing assumptions.
