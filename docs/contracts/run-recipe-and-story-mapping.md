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
  assumption_mode:
    normal_evolution
    | surface_forced_evolution
    | triggered_deep_potential
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
      mode: none | warm_bubble | future_explicit_trigger | unavailable
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
    run_recipe:
      generated_reference_lower_atmosphere
      | untriggered_observed_evolution
      | triggered_deep_potential
      | future
    run_configuration_defaults:
      duration: string | null
      horizontal_cell_count: string | null
      domain_size: string | null
      output_cadence: string | null
      diagnostic_set: string | null
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

### `normal_evolution`

An untriggered observed-sounding evolution recipe asks what the initialized
atmosphere does under the selected recipe defaults. It must not imply a weather
forecast. If surface fluxes, radiation, or large-scale forcing are recipe
defaults rather than place/time-derived values, predicted signatures must say
so.

### `surface_forced_evolution`

A surface-forced recipe asks what happens when lower-boundary sensible and/or
latent heat flux assumptions are explicit. Humid, drizzle, warm-rain, fog,
post-frontal, and boundary-layer hypotheses need this mode before product copy
can claim normal-evolution precipitation or low-cloud signatures.

### `triggered_deep_potential`

A triggered deep-potential recipe asks whether the sounding supports deep
convection when initiation is supplied. It is the right shape for current
severe/deep-convection candidates, but it is not normal atmospheric evolution.
The trigger must be copied into provenance and Results comparison.

### `elevated_forced_evolution`

An elevated recipe asks whether an above-surface source layer can sustain cloud
or convection. It needs source-layer, forcing, and output assumptions that the
current observed-sounding quick look does not supply.

## Current Recipe Catalog

### `observed_normal_evolution_v1`

```yaml
recipe_id: observed_normal_evolution_v1
display_name: Observed-sounding normal evolution
product_question: What does this observed atmosphere do without an explicit
  deep-convection trigger, under the current observed-sounding LES defaults?
assumption_set_id: normal_evolution_current_observed_sounding_v1
assumption_mode: normal_evolution
run_shape:
  duration_seconds: 21600 | configured
  horizontal_cell_count: 64 | 96 | 128 | 192 | 256 | 384 | configured
  domain_width_m: 6400 | 12800 | 60000 | 120000 | configured
  model_top_m: current observed-sounding LES model top
  output_cadence_seconds: 3600 | 900 | 300 | configured
  diagnostic_set: essential | process | full
forcing:
  trigger: {mode: none}
  surface_sensible_heat_flux: {mode: current_recipe_default}
  surface_latent_heat_flux: {mode: current_recipe_default}
  radiation: {mode: disabled}
  large_scale_lift: {mode: none}
  convergence: {mode: none}
required_inputs:
  observed_temperature_profile: required
  observed_moisture_profile: required
  observed_wind_profile: required
required_outputs:
  fields: [qc, w, qv, th, prs, u, v]
  diagnostics: [first_cloud, max_qc, cloud_top, max_updraft_w]
current_support:
  status: supported
  caveats:
    - Current recipe defaults are not a real place/time surface-energy budget.
    - Scores remain ingredient guidance until a predicted signature exists.
cm1_mapping:
  run_recipe: untriggered_observed_evolution
  run_configuration_defaults:
    duration: short_6h
    horizontal_cell_count: cells_128
    domain_size: wide_12km
    output_cadence: standard_15min
    diagnostic_set: process
```

This recipe can test shallow cloud and dry-failed signatures when the predicted
signature only requires cloud water, vertical velocity, and enough duration and
cadence. It is not enough for product claims about rain reaching the ground
unless the active predicted signature explicitly requires and receives
surface-rain output.

### `observed_capped_evolution_v1`

```yaml
recipe_id: observed_capped_evolution_v1
display_name: Observed-sounding capped evolution
product_question: Does the observed profile limit vertical growth under the
  current untriggered LES defaults?
assumption_set_id: normal_evolution_current_observed_sounding_v1
assumption_mode: normal_evolution
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
  run_recipe: untriggered_observed_evolution
```

This recipe is a specialized view of the current untriggered observed-sounding
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
    - Current surface fluxes are recipe defaults, not validated place/time
      surface-energy inputs.
    - `qr` is rain water aloft, `rain` is surface rain, and `dbz` is
      reflectivity; they must be evaluated separately.
cm1_mapping:
  run_recipe: untriggered_observed_evolution
```

This is the honest bridge for `humid_rainy_candidate`: Cloud Chamber may run a
moist observed-sounding experiment now, but precipitation signatures are only
testable when the required fields are requested, ingested, and clearly labeled.

### `triggered_deep_potential_v1`

```yaml
recipe_id: triggered_deep_potential_v1
display_name: Triggered deep-convection potential
product_question: If initiation is supplied, does this sounding support deep
  convection and storm-scale structure in CM1?
assumption_set_id: triggered_deep_potential_warm_bubble_v1
assumption_mode: triggered_deep_potential
run_shape:
  duration_seconds: 21600 | configured
  horizontal_cell_count: 128 | configured
  domain_width_m: 120000 | 160000 | 240000
  model_top_m: 20000
  output_cadence_seconds: 3600 | 900 | 300 | configured
  diagnostic_set: full
forcing:
  trigger:
    mode: warm_bubble
    description: CM1 built-in three-warm-bubble line initiation.
  surface_sensible_heat_flux: {mode: disabled}
  surface_latent_heat_flux: {mode: disabled}
  radiation: {mode: disabled}
  large_scale_lift: {mode: none}
  convergence: {mode: none}
required_inputs:
  observed_temperature_profile: required
  observed_moisture_profile: required
  observed_wind_profile: required
required_outputs:
  fields: [qc, w, qr, rain, dbz, u, v, th]
  diagnostics:
    - first_deep_convection
    - max_updraft_w
    - cloud_top
    - rain_water_aloft_onset
    - max_surface_rain
    - max_dbz
    - updraft_helicity
current_support:
  status: caveated
  caveats:
    - Package/run/ingest smoke evidence exists, but defaults are not broadly
      characterized across selected candidates.
    - The recipe tests triggered potential, not normal weather evolution.
    - Storm mode, rotation, downdraft, cold pool, and surface rain are outcomes
      to inspect after CM1 completes.
cm1_mapping:
  run_recipe: triggered_deep_potential
  run_configuration_defaults:
    duration: short_6h
    horizontal_cell_count: cells_128
    domain_size: storm_120km
    output_cadence: standard_15min
    diagnostic_set: full
```

This recipe is first-class. Its caveats are scientific trust boundaries, not a
reason to fall back to shallow quick-look for severe/deep-convection stories.

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

The current triggered-deep recipe may be a caveated first experiment, but it
does not contain line forcing or validated cold-pool diagnostics.

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

| Story ID | Primary recipe | Recipe fit | Required assumptions | Required outputs for comparison | Result comparison intent |
| --- | --- | --- | --- | --- | --- |
| `shallow_cumulus_candidate` | `observed_normal_evolution_v1` | `testable_now` when the run is long enough | no explicit trigger; current observed-sounding LES defaults; complete observed temperature/moisture/wind profile | `qc`, `w`, time and vertical coordinates | cloud formation, cloud top/depth, persistence, vertical velocity |
| `dry_failed_candidate` | `observed_normal_evolution_v1` | `testable_now` when duration/cadence can support a no-cloud conclusion | no explicit trigger; current observed-sounding LES defaults; complete observed profile | `qc`, `w`, time coordinate | weak/no cloud with meaningful vertical motion; moisture limitation remains caveated |
| `capped_suppressed_candidate` | `observed_capped_evolution_v1` | `partially_testable` | no explicit trigger; cap comes from observed profile; enough run time to observe delayed growth | `qc`, `w`, `th`, time and vertical coordinates | reduced cloud depth, delayed cloud, or capped vertical motion |
| `humid_rainy_candidate` | `surface_forced_moist_evolution_v1` | `partially_testable` until surface flux controls are validated | explicit current or future surface-flux assumptions; no deep trigger; precipitation fields requested | `qc`, `w`, `qr`, `rain`, `dbz` when precipitation is predicted | cloud, rain water aloft, surface rain, and reflectivity evaluated separately |
| `severe_thunderstorm_environment` | `triggered_deep_potential_v1` | `partially_testable` with current triggered deep-potential caveats | explicit warm-bubble trigger; complete observed wind profile; storm-scale domain | `qc`, `w`, `qr`, `rain`, `dbz`, updraft diagnostics | whether triggered initiation supports deep convection and precipitation signatures |
| `supercell_environment` | `triggered_deep_potential_v1` | `partially_testable` | explicit warm-bubble trigger; complete observed wind profile; storm-scale domain; rotation diagnostics caveated | `qc`, `w`, `qr`, `rain`, `dbz`, `u`, `v`, updraft-helicity when available | deep convection and organization evidence; not a tornado or forecast product |
| `high_cape_pulse_storm` | `triggered_deep_potential_v1` | `partially_testable` | explicit warm-bubble trigger; high-CAPE interpretation caveated until parcel diagnostics are implemented | `qc`, `w`, `qr`, `rain`, `dbz` | strong buoyant updraft and deep cloud under triggered initiation |
| `dry_microburst_inverted_v` | `triggered_deep_potential_v1` | `partially_testable` only if precipitation/downdraft pathway develops | explicit trigger; precipitation aloft; subcloud dry-layer evidence; downdraft diagnostics caveated | `qr`, `rain`, `w`, `th`, near-surface wind fields when implemented | rain water aloft, downdraft/cooling/outflow evidence; not a wind-gust forecast |
| `squall_line_cold_pool_candidate` | `triggered_deep_potential_v1` plus future `squall_line_cold_pool_future` | `partially_testable` for generic triggered deep convection; `requires_recipe` for line/cold-pool claims | explicit trigger now; future line forcing and cold-pool diagnostics for the full story | `qc`, `w`, `qr`, `rain`, `dbz`, `th`, `u`, `v` | current run can inspect storm/deep-cloud evidence; cold-pool/line match is future |
| `elevated_convection` | `elevated_forced_evolution_future` | `requires_recipe` unless a chosen recipe declares source-layer assumptions | elevated source layer, forcing, and surface-decoupling assumptions | `qc`, `w`, `qr`, `rain`, `dbz`, layer diagnostics | future elevated cloud/updraft source-layer comparison |
| `needs_review` | none by default; user selects a concrete hypothesis first | `not_evaluated` | depends on selected hypothesis | depends on selected hypothesis | cannot compare until an active story and recipe are chosen |
| `poor_or_incomplete_candidate` | none | `blocked` | package-readiness blockers must be resolved | none | no runnable recipe until profile/input safety passes |

Deep-convection stories should not silently route to shallow quick-look as if
that tested the deep hypothesis. The user may still deliberately run
`observed_normal_evolution_v1`; Results must then mark the deep hypothesis as
`not_comparable` or `inconclusive` rather than as a failed deep-convection
prediction.

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
- a recipe assumption is missing, such as surface fluxes for drizzle/warm-rain
  claims, warm-bubble trigger provenance for deep potential, or source-layer
  assumptions for elevated convection;
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

Do not use triggered deep-potential trigger-failed language for non-deep recipes
or for deliberate untriggered observed-evolution runs.

## Product Copy Rules

- Say "ingredient score" or "screening score" before a run exists.
- Say "predicted output signature" only after the analyzer has an explicit
  assumption set and compatible recipe.
- Say "not testable with current run recipes" when no current recipe can test
  the selected hypothesis.
- Say "partially testable" when the current recipe can inspect part of the
  hypothesis but lacks required forcing, diagnostics, or validation.
- Say "triggered deep-convection potential" for warm-bubble deep recipes.
- Say "normal evolution" only for untriggered recipes, and disclose any current
  surface/radiation/forcing defaults.
