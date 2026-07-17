# Analyzer Hypothesis And Output-Signature Contract

Status: forward product/data contract

This contract defines the next step after cached-sounding ingredient screening.
It does not replace CM1, does not validate a sounding by itself, and does not
make the browser responsible for meteorology or NetCDF parsing.

Cloud Chamber may rank sounding ingredients without predicting a CM1 outcome.
To predict an observable result, the analyzer must bind the sounding to explicit
run assumptions and a testable run recipe:

```text
Given this sounding plus these explicit run assumptions,
we expect this CM1-observable signature,
with this uncertainty,
and this run recipe is the right way to test it.
```

No assumption set means no predicted output signature. No compatible run recipe
means no testable label.

The run-recipe catalog and initial story-to-recipe mapping are defined in
[Run Recipe And Story-Mapping Contract](run-recipe-and-story-mapping.md). This
contract consumes those recipe IDs rather than redefining the package path.

## Scope Boundary

This is a contract for future analyzer payloads and product copy. It is not a
request to implement new CM1 packages, expose raw namelist controls, or add a
browser parser.

Existing cached-sounding story scores remain ingredient/screening scores. They
rank sounding evidence and help choose atmospheres to try. They do not predict
what the current CM1 package will produce.

Use `match` language only after CM1 output exists and Cloud Chamber is comparing
a predicted signature with the ingested result.

## Core Objects

The analyzer should emit hypotheses rather than standalone story labels:

```yaml
hypotheses:
  - hypothesis_id: string
    story_id: string
    story_label: string
    story_family: string
    ingredient_score_0_to_100: number
    support: supported | weak | unavailable
    confidence: low | medium | high
    evidence:
      - key: string
        label: string
        value: number | string | boolean | null
        units: string | null
        interpretation: string
        support_state: supported | caveated | unavailable
        caveats: [string]
    caveats: [string]
    assumption_set: AssumptionSet | null
    predicted_output_signature: PredictedOutputSignature | null
    recommended_run_recipes:
      - RunRecipeReference
    testability: Testability
```

The analyzer may emit multiple hypotheses for one sounding. A humid lower
atmosphere, a weak deep-convection potential signal, and a capped/suppressed
signal can coexist. Product surfaces must show which hypothesis is active when a
user filters, saves, packages, or later compares a result.

## Assumption Set

An `assumption_set` makes the run context explicit. It is required before the
analyzer may produce a predicted output signature.

```yaml
assumption_set:
  assumption_set_id: string
  label: string
  trigger:
    mode: none | future_explicit_trigger | unavailable
    description: string
    caveats: [string]
  surface_fluxes:
    sensible_heat_flux: prescribed | derived | disabled | unavailable
    latent_heat_flux: prescribed | derived | disabled | unavailable
    source: current_control | recipe_default | differential_surface_patch | future_surface_model | none
    caveats: [string]
  radiation:
    mode: disabled | prescribed_time_place | future_interactive | unavailable
    place_time_required: boolean
    caveats: [string]
  large_scale_forcing:
    lift_or_convergence: none | prescribed | future | unavailable
    description: string
    caveats: [string]
  run_requirements:
    minimum_duration_seconds: number | null
    minimum_domain_width_m: number | null
    minimum_model_top_m: number | null
    maximum_output_cadence_seconds: number | null
    required_output_fields: [string]
  uncertainty:
    level: low | medium | high
    reasons: [string]
```

Assumption sets must distinguish observed evolution under explicit forcing from
current and future forcing modes:

- `observed_surface_forced_evolution`: no artificial atmospheric trigger; useful
  for asking what the initialized atmosphere does under the selected numeric
  uniform lower-boundary heat/moisture forcing, duration, domain, grid, and
  cadence.
- `surface_forced_evolution`: explicit surface sensible/latent heat-flux
  assumptions; useful for boundary-layer growth, shallow cloud, drizzle, or
  suppression hypotheses.
- `differential_surface_forced_evolution`: one idealized lower-boundary
  heat/moisture patch for initiation, localized updraft, and organization
  questions. It is current v0 support, applied through Cloud Chamber's CM1
  source customization path, and still requires CM1-observable diagnostics
  before Results can compare predicted signatures.
- `radiation_place_time_evolution`: radiation/place-time assumptions; future
  contract for fog, nocturnal, winter, and diurnal hypotheses.

## Predicted Output Signature

A `predicted_output_signature` must describe only CM1-observable output fields
or derived diagnostics Cloud Chamber can compute from those fields.

```yaml
predicted_output_signature:
  signature_id: string
  summary: string
  expected_outcomes:
    - outcome_key: string
      label: string
      expected_state: present | absent | uncertain | not_evaluated
      timing_window_seconds:
        start: number | null
        end: number | null
      magnitude:
        min: number | null
        max: number | null
        units: string | null
      required_fields: [string]
      diagnostic_method: string
      uncertainty: low | medium | high
      caveats: [string]
  failure_modes:
    - key: string
      label: string
      required_fields: [string]
      caveats: [string]
```

The signature should use stable precipitation language:

- `qc` = cloud water.
- `w` = vertical velocity / updraft and downdraft structure.
- `qr` = rain water aloft.
- `rain` = surface rain / accumulated precipitation at ground.
- `dbz` = reflectivity.

`qr` is not surface rain. Surface rain must come from CM1 surface rain or
accumulated precipitation output. Reflectivity must come from CM1 reflectivity
output or a clearly labeled supported diagnostic, not from cloud water alone.

## Outcome Types And Required Fields

| Prediction type            | Required fields                                             | Notes                                                                                                                                                                                                                                                  |
| -------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| First cloud / cloud formed | `qc`, time coordinate                                       | Uses backend cloud-water threshold and minimum grid-cell rules.                                                                                                                                                                                        |
| Cloud depth/top            | `qc`, vertical coordinate, time coordinate                  | Must report threshold and cloud-top method.                                                                                                                                                                                                            |
| Shallow cloud persistence  | `qc`, time coordinate                                       | Needs enough duration and cadence to distinguish transient noise from evolution.                                                                                                                                                                       |
| Updraft strength           | `w`, time coordinate                                        | May include height/region caveats when available.                                                                                                                                                                                                      |
| Deep breakthrough          | `qc`, `w`, vertical coordinate, time coordinate             | Current observed-sounding runs can inspect deep-cloud/updraft evidence with the explicit Deep-Tower Benchmark trigger, but broad deep-convection prediction remains caveated until observed-boundary forcing and comparison diagnostics are validated. |
| Rain water aloft           | `qr`, time coordinate                                       | User-facing label should say rain water aloft.                                                                                                                                                                                                         |
| Surface rain               | `rain` or supported surface precipitation field             | Must preserve units and must not be inferred from `qr`.                                                                                                                                                                                                |
| Reflectivity               | `dbz` or supported reflectivity diagnostic                  | Unsupported reflectivity stays unavailable.                                                                                                                                                                                                            |
| Cold-pool or outflow proxy | near-surface thermodynamic/wind fields plus time coordinate | Must be caveated until backend diagnostics are implemented.                                                                                                                                                                                            |
| Suppression / no cloud     | `qc`, `w`, duration/cadence context                         | Requires enough run length and output cadence to say the test was meaningful.                                                                                                                                                                          |

If a required field is absent from the run recipe, the prediction is not
testable and must not be compared as a miss.

## Run Recipe Reference

Recommended recipes connect hypotheses to Build without making compute target
the product axis. The canonical recipe fields and current story mapping live in
[Run Recipe And Story-Mapping Contract](run-recipe-and-story-mapping.md); the
shape below is the analyzer payload reference to that contract.

```yaml
recommended_run_recipes:
  - recipe_id: string
    label: string
    run_recipe: generated_reference_lower_atmosphere
      | observed_surface_forced_evolution
      | future
    run_configuration:
      duration_seconds: number | null
      horizontal_cell_count: number | null
      domain_width_m: number | null
      dx_m: number | null
      model_top_m: number | null
      output_cadence_seconds: number | null
      requested_fields: [string] # current observed runs request the full field set
      forcing: string
    suitability:
      status: testable_now | partially_testable | requires_new_recipe | blocked
      reason: string
      expected_cost_runtime_volume: string | null
      larger_compute_note: string | null
    caveats: [string]
```

Examples:

- A shallow-cumulus hypothesis may be partially testable with the current
  observed surface-forced recipe if `qc` and `w` are available and the run is
  long enough.
- A humid/rainy hypothesis is only testable for rain behavior when `qr`,
  surface `rain`, and/or `dbz` outputs are enabled according to the predicted
  signature.
- A supercell or severe-thunderstorm hypothesis may be inspected with the
  observed-sounding run under selected uniform surface forcing, but deep
  organization claims remain caveated until differential forcing and comparison
  diagnostics exist.
- A surface-flux or radiation/place-time hypothesis requires the matching
  forcing assumptions before predicted output signatures can be emitted.

## Testability

`testability` is the product-safe answer to “can this run test the selected
hypothesis?”

```yaml
testability:
  status: testable_now | partially_testable | requires_recipe | blocked | not_evaluated
  label: string
  explanation: string
  missing_assumptions: [string]
  missing_output_fields: [string]
  blocking_caveats: [string]
```

The UI may still allow deliberate exploration. It must show when the selected
package path is not a test of the selected hypothesis.

## Build, Results, And Explore Flow

Build should consume analyzer hypotheses as pre-run guidance:

- show ingredient/screening scores as ingredient rankings;
- show the active assumption set and recipe fit before package generation;
- warn when a selected package cannot test the active hypothesis;
- copy hypothesis, assumption, recipe-fit, and saved user notes into package
  provenance.

Results should compare only after CM1 output exists:

- preserve the active hypothesis and run recipe used;
- compare predicted output signature against ingested diagnostics only when the
  required output fields and duration/cadence were present;
- use comparison states aligned with #275: `supported`, `partially_supported`,
  `contradicted`, `inconclusive`, or `not_comparable`;
- use field-level states such as `matched`, `partial`, `missed`, `unavailable`,
  or `not_requested` where useful;
- explain missing fields, inadequate cadence/duration, or incompatible recipes
  as `inconclusive` or `not_comparable`, not as scientific failure.

Explore should inspect the CM1-derived evidence:

- open to fields and times relevant to the active prediction when supported;
- expose missing required fields as unavailable/caveated;
- keep `qc`, `w`, `qr`, `rain`, and `dbz` semantics distinct in labels,
  legends, and explanations;
- never parse raw NetCDF in the browser.

## Migration From Current Screening

Current `story_scores` can map into the future hypothesis object as follows:

| Current field              | Future field                |
| -------------------------- | --------------------------- |
| `story`                    | `story_id`                  |
| `label`                    | `story_label`               |
| `score_0_to_100`           | `ingredient_score_0_to_100` |
| `support`                  | `support`                   |
| `reasons` / evidence items | `evidence`                  |
| `caveats`                  | `caveats`                   |
| `recipe_fit_status`        | `testability.status` seed   |

Until assumption sets and predicted output signatures exist, the analyzer should
emit ingredient/screening scores, recipe-fit caveats, and no predicted output
signature.

## Testing Expectations

Tests for the future implementation should prove:

- hypotheses cannot include predicted signatures without assumption sets;
- missing required output fields produce `inconclusive` or field-level
  `unavailable`, not a failed prediction;
- Deep-Tower Benchmark hypotheses remain distinct from observed surface-forced,
  differential-forcing, and radiation/place-time hypotheses;
- `qr`, surface `rain`, and `dbz` are labeled and evaluated separately;
- the browser receives bounded backend JSON and does not parse raw IGRA, ZIP, or
  NetCDF data;
- Build, Results, and Explore copy and consume the same active hypothesis IDs.
