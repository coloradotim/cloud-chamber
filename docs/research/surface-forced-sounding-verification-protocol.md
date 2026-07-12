# Surface-Forced Sounding Verification Protocol

Status: protocol/template for issue #310

## Purpose

This protocol defines how Cloud Chamber should verify observed-sounding CM1 runs that use numeric uniform lower-boundary heat/moisture forcing.

The immediate science/product question is not “can we make a storm happen?” The first question is:

```text
When surface heat/moisture forcing changes, does CM1 show the expected package, output, and boundary-layer response?
```

Only after that question is answered should a campaign ask:

```text
Can a selected real sounding deepen past shallow cumulus under uniform surface forcing, or does it need a different initiation/forcing mechanism?
```

## Problem being diagnosed

If a sounding-driven run only produces shallow cumulus, that result can mean very different things:

1. **Implementation issue** — the selected surface-flux values did not reach CM1, CM1 ignored them, or the relevant output fields were not emitted/ingested.
2. **Configuration issue** — forcing, duration, domain/grid bundle, or output cadence was not suitable for the question.
3. **Uniform-forcing limitation** — the boundary layer responds, but horizontally uniform forcing does not focus enough ascent to reach the LFC.
4. **Valid model outcome** — the sounding did not initiate or deepen under the selected assumptions.
5. **Diagnostics issue** — CM1 produced relevant structure, but Cloud Chamber did not ingest or summarize the fields needed to see it.

The campaign must separate those cases. It must not collapse every no-storm outcome into failure.

## Current experiment model

The current active observed-sounding run mode is surface-forced observed evolution:

```text
selected observed sounding
+ uniform lower-boundary heat/moisture flux values
+ selected duration/domain/grid/cadence
+ full available output fields
= one CM1 experiment to inspect after completion
```

Current assumptions:

- Observed temperature, moisture, and usable u/v wind profile are required by the current package path.
- No artificial atmospheric trigger is applied.
- Surface heat/moisture forcing is uniform across the domain and constant through model time.
- Radiation is disabled.
- Large-scale forcing/convergence is not implemented.
- Terrain, GIS surface data, soil moisture, vegetation, wet ground, transpiration, and real place/time surface-energy budgets are not implemented.
- Differential surface forcing is future work tracked separately.

## Campaign principles

- Candidate labels are pre-run hypotheses, not predictions.
- The selected run assumptions determine what can be tested.
- CM1 output is the evidence source.
- Missing fields make a question unavailable or inconclusive.
- A shallow-only outcome is not automatically a failed sounding or failed model.
- No generated runtime artifacts belong in git.
- Comparisons are valid only when the fields intended to stay fixed are actually fixed, and when output fields and diagnostic support are comparable enough for the stated question.

## Matrix contract for campaign runners

The example YAML in `docs/research/templates/surface-forced-campaign-matrix.example.yaml` is a template, but the structure below is the contract that #311 should implement.

### Required top-level fields

```text
schema_version
campaign
execution
selection_sets
run_defaults
forcing_sets
runs
comparison_types
required_summary_fields
```

`schema_version` is required so future runner changes can reject or migrate older matrices intentionally.

### Required ID rules

- `campaign.campaign_id` must be unique within the runtime campaign workspace.
- Each `selection_sets[].selection_id` must be unique.
- Each `forcing_sets[].forcing_id` must be unique.
- Each `runs[].matrix_id` must be unique.
- Each run must reference an existing `selection_id` and `forcing_id`.
- Use `matrix_id` as the canonical run-matrix identifier. Do not introduce a second name such as `run_matrix_id` in the same schema.

### Source union

Each selection source must be exactly one of:

```text
saved_candidate:
  saved_candidate_id

cached_recommendation:
  candidate_id
  optional station_id / valid_time_utc for disambiguation

uploaded_or_local_igra:
  runtime_file_ref
  selected_valid_time_utc
```

Committed matrices should not contain machine-private absolute paths. If a local path is needed, keep the real path in runtime-local state and use a portable runtime file reference in committed examples.

### Candidate provenance

The runner and report must preserve enough provenance to identify the real sounding and why it was selected:

```text
candidate_id
selection_source_type
selection_source_reference
station_id
station_name
valid_time_utc
candidate_story
candidate_score
candidate_evidence
candidate_caveats
```

A story label without candidate identity, source reference, evidence, and caveats is not enough for a verification report.

### Override precedence

When resolving a run, apply settings in this order:

```text
run_defaults
→ referenced forcing_set
→ run-specific overrides
```

Run-specific values win over forcing-set values. Forcing-set values win over defaults. The resolved configuration should be copied into package/run/result metadata and the campaign report.

### Stable resume / idempotency identity

A runner should derive a stable run identity from at least:

```text
campaign_id
matrix_id
resolved selection identity
resolved forcing values
resolved duration/domain/grid/cadence
Cloud Chamber commit if the runner chooses to lock campaigns to a code version
```

A resumed campaign must not create duplicate packages for the same resolved identity unless the operator explicitly requests a rerun.

### Lifecycle/status values

A campaign runner may map to existing run-manifest states, but report status should normalize to:

```text
planned
packaged
queued
running
completed_not_ingested
ingested
package_failed
run_failed
ingest_failed
skipped
blocked
```

The report should preserve the source manifest state when available. The report must show package status, run status, and ingest status separately so missing result evidence cannot be mistaken for a scientific no-initiation outcome.

### Comparison contract

Do not use one global “all fields must match” list for every pair. Each comparison type must define:

```text
comparison_type
control_matrix_id
experiment_matrix_id
varied_fields
required_equal_fields
required_available_fields
required_diagnostic_support
noncomparable_status
```

Examples:

```text
forcing_sensitivity:
  varied_fields: surface_heat_flux_k_m_s, surface_moisture_flux_g_g_m_s
  required_equal_fields: selection_id, duration, domain_size, horizontal_cell_count, nx, ny, nz, dx_m, dy_m, dz_m, model_top_m, output_cadence, Cloud Chamber commit, CM1 version

duration_sensitivity:
  varied_fields: duration
  required_equal_fields: selection_id, forcing values, domain_size, horizontal_cell_count, nx, ny, nz, dx_m, dy_m, dz_m, model_top_m, output_cadence, Cloud Chamber commit, CM1 version

domain_grid_bundle_sensitivity:
  varied_fields: domain_size, nx, ny, nz, dx_m, dy_m, dz_m, model_top_m, output volume
  required_equal_fields: selection_id, forcing values, duration, output_cadence, Cloud Chamber commit, CM1 version

cross_sounding_discrimination:
  varied_fields: selection_id, station/time/candidate identity
  required_equal_fields: forcing values, duration, domain_size, horizontal_cell_count, nx, ny, nz, dx_m, dy_m, dz_m, model_top_m, output_cadence, Cloud Chamber commit, CM1 version
```

All comparisons must also check required output fields, missing-field availability, and diagnostic support. Unsupported comparisons should be labeled `inconclusive_noncomparable_runs` rather than summarized as evidence.

### Stage gates

Phase 1 must be allowed to stop the campaign before expensive later phases.

Default gate policy:

```text
selected_and_cm1_facing_forcing_metadata_missing:
  result: fail
  automatic_continuation: blocked

hfx_or_lhfx_missing_when_requested:
  result: inconclusive_missing_evidence
  automatic_continuation: blocked

low_level_response_diagnostic_missing:
  result: inconclusive_missing_evidence
  automatic_continuation: blocked

forcing_metadata_present_and_surface_outputs_available_or_explicitly_not_supported:
  result: partial_verification
  automatic_continuation: blocked unless operator override is recorded

forcing_metadata_present_surface_outputs_available_and_low_level_response_available:
  result: forcing_path_verified_for_campaign
  automatic_continuation: allowed
```

An operator may explicitly override a blocked gate, but the report must preserve the override and must not label forcing path or boundary-layer response as verified. The runner should default to planning/reporting blocked later phases rather than queueing them when gates fail.

### Execution safety

Planning must be the default runner behavior. Queueing must require an explicit runner mode or flag. Do not let a committed YAML file silently launch or queue work.

Suggested modes for #311:

```text
plan
package
queue
status
ingest
report
resume
```

### Mapping report fields to current metadata

Where possible, #311 should map report fields to existing backend structures instead of inventing names:

- `ResultMetadata`: result ID, run ID, scenario/recipe IDs, observed sounding, run configuration, expected/required/missing fields, warnings, caveats, candidate screening, result state.
- `ScienceSummary`: first cloud time, cloud top/deep-cloud state, max `qc`, max `w`, rain-water timing, default interesting time, support state where available.
- `ResultDiagnostics` and output-product payloads: field availability, units, min/max/mean when derivable, missing-field support states.

If the existing backend cannot provide a field, the report must say `unavailable` and identify the missing diagnostic rather than inventing a value.

## Low-level response diagnostic contract

Low-level `qv` and theta/temperature response must be standardized before the campaign runner summarizes them.

Preferred method for #311:

```text
vertical layer: 0-1000 m AGL, using available model vertical coordinate
spatial statistic: domain mean unless a later issue adds selected-column context
reference time: first output time, preferably model time 0 or earliest available output
evaluation time: final output time for the run unless the report explicitly names another time
per-run response: evaluation_time_mean - reference_time_mean
forcing sensitivity: response difference against the paired control run with same sounding, duration, domain, grid, and cadence
units: preserve source field units; convert only if the backend has a documented conversion
```

If a standardized backend diagnostic is not implemented, report these fields as:

```text
unavailable: low_level_response_diagnostic_not_implemented
```

The campaign runner must not improvise a browser-side or ad hoc calculation without documenting the layer, statistic, reference time, paired control, units, and source fields.

## Phase 1 — Forcing-path smoke check

Goal: prove that numeric surface forcing is wired through package generation, CM1 output, ingest, and summary.

Use one simple/control sounding with usable winds and complete low-level data. Run a small forcing matrix:

```text
control/default flux
higher sensible heat only
higher moisture flux only
higher sensible + higher moisture
```

Required evidence:

- Run manifest and dry-run report preserve selected product values.
- CM1-facing namelist values preserve `cnst_shflx` and `cnst_lhflx`.
- Surface output switches are requested where supported.
- Ingested metadata reports `hfx` and `lhfx` separately when present.
- Low-level thermal/moisture fields respond in the expected direction if derivable by the standardized low-level response diagnostic.
- Cloud timing, cloud top, `qc`, or `w` response is summarized, even if weak.

Interpretation:

| Finding | Diagnosis |
| --- | --- |
| selected values missing from metadata/namelist | implementation failure |
| surface fields missing from output/ingest | output-product or CM1 output request gap |
| hfx/lhfx present but low-level theta/qv response absent | CM1 setup/units/surface-model issue, too-short run, or missing response diagnostic |
| low-level response exists but no deepening | continue to Phase 2/3; not a failure by itself |

## Phase 2 — Easy sounding response check

Goal: test whether an easy deep-candidate sounding can deepen under uniform surface forcing.

Select one sounding with the most favorable available ingredients:

- high CAPE or strong instability proxy;
- low CIN or weak cap if available;
- relatively low LFC / LCL if available;
- deep moisture;
- complete wind profile;
- good low-level coverage.

Suggested starter matrix:

```text
Wide 12 km / 6 h / default flux
Wide 12 km / 6 h / stronger flux
Wide 12 km / 12 h / stronger flux
Regional 60 km / 12 h / stronger flux
Regional 120 km / 12 h / stronger flux if feasible
```

This matched matrix separates questions:

1. **Default 6 h vs strong 6 h** tests forcing sensitivity with duration and run shape held constant.
2. **Strong 6 h vs strong 12 h** tests duration sensitivity with forcing and 12 km run shape held constant.
3. **Strong 12 km vs strong 60 km** tests a broader run-shape bundle.

The 12 km to 60 km step is not a pure domain-size test when `horizontal_cell_count` is the same. With fixed `cells_128`, both the domain and horizontal spacing change. Treat this as a **domain/grid configuration bundle** and record resolved `nx/ny/nz`, `dx/dy/dz`, model top, cadence, and output volume. Do not conclude that “domain size caused deepening” unless a comparable grid design supports that claim.

Required evidence:

- Boundary-layer response compared with the matched Phase 2 control and Phase 1 behavior.
- Max cloud top and time of max cloud top.
- Max `w`, plus time and height of max `w` if available.
- Max `qc` and time of max `qc`.
- Cloud depth or classification when supported.
- `qr`, surface `rain`, and `dbz` availability and outcomes separately.
- Whether the result appears shallow, congestus-like, or deep.
- Whether missing outputs prevent interpretation.

Interpretation:

| Finding | Diagnosis |
| --- | --- |
| no boundary-layer response | return to Phase 1 implementation/config diagnosis |
| strong 6 h deepens relative to default 6 h | forcing sensitivity is supported |
| strong 12 h deepens relative to strong 6 h | duration sensitivity is supported |
| regional run differs from wide 12 km run | run-shape bundle matters; inspect domain, dx/dy, model top, and output cadence before assigning cause |
| shallow cumulus only, even with stronger forcing and longer duration | possible uniform-forcing limitation, configuration gap, or valid no-initiation outcome |
| deep cloud/updraft but no precipitation fields | output/microphysics/diagnostic gap or dry outcome |
| deep evidence present but not summarized | Results/Explore diagnostic gap |

## Phase 3 — Cross-sounding discrimination check

Goal: test whether CM1 response differs across sounding classes under comparable forcing and run-shape assumptions.

Suggested candidate set:

```text
low-CIN / easy deep candidate
strongly capped deep candidate
humid/rainy candidate
inverted-V / dry microburst-ish candidate
weak or marginal control sounding
```

Run the same forcing/domain/duration/grid/cadence setup across the set. Do not tune each case until after the first comparison pass.

Before comparing two runs, check:

- sounding identity/provenance and selected valid time;
- selected forcing values and resolved CM1-facing values;
- duration;
- domain;
- horizontal cell count and resolved `dx/dy`;
- vertical grid and model top;
- output cadence;
- CM1 version/build and Cloud Chamber commit;
- required fields and missing fields;
- diagnostic support states.

If these are not comparable enough for the stated question, label the comparison `inconclusive_noncomparable_runs` instead of summarizing it as evidence.

Required evidence:

- Same resolved run-shape bundle for each sounding or explicit non-comparable caveat.
- Same output/diagnostic fields or explicit unavailable fields.
- Same summary metrics.
- Candidate story/evidence carried through metadata.
- Which differences are model output differences vs missing-field differences.

Interpretation:

| Finding | Diagnosis |
| --- | --- |
| every comparable sounding behaves nearly the same | forcing/config may be too generic or diagnostics too coarse |
| only easy deep case deepens | model path may be working; candidate selection matters |
| capped case stays shallow while easy case deepens | useful discrimination |
| all comparable cases shallow despite clear BL response | possible uniform-forcing limitation, but not proof by itself |
| comparisons are not comparable | inconclusive; fix matrix or report non-comparability |

## Phase 4 — Next-step diagnosis

After the first campaign, assign the result to one or more categories:

```text
forcing_path_not_verified
surface_outputs_missing
boundary_layer_response_verified
uniform_forcing_too_weak
uniform_forcing_physics_limited
run_duration_or_domain_limited
candidate_selection_limited
output_products_or_diagnostics_missing
valid_no_initiation_under_tested_assumptions
inconclusive_noncomparable_runs
inconclusive_missing_evidence
differential_forcing_followup_candidate
radiation_or_place_time_followup_candidate
```

Minimum evidence rules:

- `uniform_forcing_too_weak` requires a matched comparison where stronger forcing produces a stronger boundary-layer/cloud response than default forcing under the same sounding, duration, domain, grid, and cadence, but still does not reach the target depth/signature.
- `uniform_forcing_physics_limited` requires verified low-level response plus matched stronger/longer/broader runs that remain shallow, with no missing key diagnostics that would change interpretation. This should usually be phrased as a candidate conclusion, not a final proof.
- `run_duration_or_domain_limited` requires a matched comparison showing deeper or more organized response when duration or the domain/grid bundle changes, while forcing and sounding are held constant.
- `valid_no_initiation_under_tested_assumptions` requires the forcing path and key diagnostics to be verified, comparable run assumptions to be documented, and no evidence of deepening under those assumptions. It does not disprove the sounding's broader deep-convection potential.
- `inconclusive_missing_evidence` applies when required fields, low-level response diagnostics, or output products are missing.
- `inconclusive_noncomparable_runs` applies when the matrix changes more than the stated comparison allows.
- `differential_forcing_followup_candidate` is appropriate when uniform forcing is verified and responsive but does not focus ascent; do not call differential forcing “needed” unless supported configuration explanations have been ruled out.

The campaign should end with explicit next-step recommendations, usually one of:

- fix package/namelist/output wiring;
- adjust default surface flux values;
- adjust duration/domain/grid recommendations;
- add missing output products/diagnostics;
- proceed to differential surface forcing as a follow-up candidate;
- refine candidate screening;
- defer screening-hypothesis-vs-CM1-evidence comparison until better evidence exists.

## Required per-run metadata

Each run should record, at minimum:

```text
schema_version
campaign_id
matrix_id
stable_resume_identity
run_id
result_id if ingested
station_id
station_name
valid_time_utc
candidate_id if any
selection_source_type
selection_source_reference
candidate story / active story
candidate score
candidate evidence
candidate caveats
selected surface_heat_flux_k_m_s and units
selected surface_moisture_flux_g_g_m_s and units
resolved CM1 cnst_shflx and units
resolved CM1 cnst_lhflx and units
duration
output cadence
horizontal_cell_count
nx / ny / nz
dx_m / dy_m / dz_m
model_top_m
domain_size and resolved domain width
queue target
package status
run status
ingest status
required output fields
missing output fields
warnings / caveats
```

## Required evidence fields

The report should extract these from ingested metadata/output products when available:

```text
hfx_present
hfx_units
hfx_min / hfx_max / hfx_mean when derivable
lhfx_present
lhfx_units
lhfx_min / lhfx_max / lhfx_mean when derivable
low_level_qv_response with method or unavailable reason
low_level_theta_or_temperature_response with method or unavailable reason
first_cloud_time
max_cloud_top_m and time
max_qc and time
cloud_depth_or_classification when supported
max_w_m_s, time, and height when supported
qr / rain water aloft availability and outcome
surface rain availability and outcome
dbz / reflectivity availability and outcome
first deep cloud time if available
deep cloud flag if available
interesting time support state
exact result fields or diagnostics used as evidence
missing fields
warnings
caveats
```

If an item cannot be derived, the report must say `unavailable`, not zero and not failed.

## Campaign matrix guidance

Start small. The first useful campaign should be a diagnostic minimum, not a broad sweep.

Suggested first campaign:

```text
control sounding:
  default flux
  high sensible only
  high moisture only
  high sensible + high moisture

easy deep candidate:
  wide 12 km / 6 h / default flux
  wide 12 km / 6 h / high heat + high moisture
  wide 12 km / 12 h / high heat + high moisture
  regional 60 km / 12 h / high heat + high moisture

weak control sounding:
  regional 60 km / 12 h / high heat + high moisture
```

This is enough to identify whether the path is responsive before spending time on larger regional runs. Add `regional 120 km / 12 h / high heat + high moisture` only when cost/output volume is acceptable.

## Artifact policy

Do not commit:

- generated CM1 packages;
- NetCDF output;
- local runtime folders;
- copied runtime tables;
- stdout/stderr logs;
- screenshots, traces, videos;
- local settings or SSH configuration;
- machine-private absolute paths.

A committed campaign report may include:

- run IDs;
- result IDs;
- station/time provenance;
- selected configuration values;
- summarized diagnostics;
- caveats and unavailable fields;
- portable provenance identifiers.

Local filesystem pointers belong in runtime-local JSON/state, not committed Markdown.

## Relationship to future work

This protocol feeds:

- campaign runner/report tooling;
- differential surface forcing;
- screening-hypothesis-vs-CM1-evidence comparison;
- radiation/place-time validation;
- candidate screening calibration.

It does not replace those issues. It creates the lab notebook structure needed before they can be trusted.
