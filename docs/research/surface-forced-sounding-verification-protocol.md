# Surface-Forced Sounding Verification Protocol

Status: protocol/template for issue #310

## Purpose

This protocol defines how Cloud Chamber should verify observed-sounding CM1 runs that use numeric uniform lower-boundary heat/moisture forcing.

The immediate question is not “can we make a storm happen?” The first question is:

```text
When surface heat/moisture forcing changes, does CM1 show the expected package, output, and boundary-layer response?
```

Only after that is answered should a campaign ask:

```text
Can a selected real sounding deepen past shallow cumulus under uniform surface forcing, or does it need a different initiation/forcing mechanism?
```

## Problem being diagnosed

A sounding-driven run that only produces shallow cumulus can mean several different things:

1. **Implementation issue** — selected surface-flux values did not reach CM1, CM1 ignored them, or relevant output fields were not emitted/ingested.
2. **Configuration issue** — forcing, duration, domain/grid bundle, or output cadence was not suitable for the question.
3. **Uniform-forcing limitation** — the boundary layer responds, but horizontally uniform forcing does not focus enough ascent to reach the LFC.
4. **Valid model outcome** — the sounding did not initiate or deepen under the selected assumptions.
5. **Diagnostics issue** — CM1 produced relevant structure, but Cloud Chamber did not ingest or summarize the fields needed to see it.

The campaign must separate those cases. It must not collapse every no-storm outcome into failure.

## Current experiment model

The active observed-sounding run mode is:

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
- Differential surface forcing is a separate v0 patch recipe. It adds an
  idealized lower-boundary heat/moisture perturbation through CM1 source
  customization, not through a real land-surface or radiation model.

## Campaign principles

- Candidate labels are pre-run hypotheses, not predictions.
- The selected run assumptions determine what can be tested.
- CM1 output is the evidence source.
- Missing fields make a question unavailable or inconclusive.
- A shallow-only outcome is not automatically a failed sounding or failed model.
- No generated runtime artifacts belong in git.
- Comparisons are valid only when the runs are comparable for the stated question.

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
comparison_types
phase1_required_comparison_types
runs
required_summary_fields
```

`schema_version` is required so future runner changes can reject or migrate older matrices intentionally.

### ID rules

- `campaign.campaign_id` must be unique within the runtime campaign workspace.
- Each `selection_sets[].selection_id` must be unique.
- Each `forcing_sets[].forcing_id` must be unique.
- Each `comparison_types[].comparison_type` must be unique.
- Each `runs[].matrix_id` must be unique.
- Each run must reference an existing `selection_id` and `forcing_id`.
- `phase1_required_comparison_types` must name the Phase 1 comparison types
  required before surface-flux response can be considered verified. For the
  current protocol those are `heat_flux_sensitivity`,
  `moisture_flux_sensitivity`, and `combined_flux_sensitivity`.
- Use `matrix_id` as the canonical run-matrix identifier. Do not introduce `run_matrix_id` in the same schema.

### Source union

Each selection source must be exactly one of:

```text
saved_candidate:
  saved_candidate_id

cached_recommendation:
  candidate_id
  optional station_id / valid_time_utc for disambiguation

uploaded_or_local_igra:
  local_text_path or runtime_file_ref
  selected_valid_time_utc
```

Committed matrices must not contain machine-private absolute paths. If a local path is needed, keep the real path in runtime-local state and use a portable placeholder or runtime file reference in committed examples.

### Override precedence

Resolve each run in this order:

```text
run_defaults
→ referenced forcing_set
→ run-specific overrides
```

Run-specific values win over forcing-set values. Forcing-set values win over defaults. The resolved configuration must be copied into package/run/result metadata and the campaign report.

### Stable resume / idempotency identity

A runner should derive a stable run identity from at least:

```text
campaign_id
matrix_id
resolved selection identity
resolved forcing values
resolved duration/domain/grid/cadence
Cloud Chamber commit if the runner locks campaigns to a code version
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
run_canceled
skipped
blocked
```

The report should preserve the source manifest state when available.

### Runner implementation

The checked-in runner is `scripts/run_surface_forced_campaign.py`. It is a thin
orchestration layer over existing backend package generation, local serial
queueing, trusted LAN worker execution, result ingest, and result metadata
summaries. It does not run CM1 in tests and does not invent diagnostics from
missing fields.

Supported modes:

```bash
scripts/run_surface_forced_campaign.py --matrix <campaign.yaml>
scripts/run_surface_forced_campaign.py --matrix <campaign.yaml> --plan
scripts/run_surface_forced_campaign.py --matrix <campaign.yaml> --package --resume
scripts/run_surface_forced_campaign.py --matrix <campaign.yaml> --queue
scripts/run_surface_forced_campaign.py --matrix <campaign.yaml> --status
scripts/run_surface_forced_campaign.py --matrix <campaign.yaml> --ingest
scripts/run_surface_forced_campaign.py --matrix <campaign.yaml> --report
```

If no mode flag is supplied, the runner defaults to `--plan`. `--queue` is the
first mode that can start CM1 execution and is deliberately staged:

- optional matrix rows are excluded unless the operator passes `--include-optional`
  or explicitly selects the optional row with `--matrix-id`;
- Phase 1 rows may queue before evidence exists;
- Phase 2 and later rows remain `blocked` until the Phase 1 gate returns
  `forcing_path_verified_for_campaign`;
- an operator may continue after an inconclusive gate with
  `--override-phase-gate --override-reason <reason>`, and the override must be
  preserved in campaign state and reports;
- LAN queueing honors `execution.max_concurrent_runs` and leaves excess rows
  blocked rather than launching multiple remote runs.

`--status` refreshes trusted LAN worker state for LAN rows without overwriting
the remote state with an unchanged local packaged manifest. `--ingest` collects
LAN output only after the worker reports the result is ready, then waits for
collection to update the local manifest with completed CM1 output before calling
result ingest.

The runner writes resumable campaign state under the configured runtime home:

```text
<runtime-home>/campaigns/<campaign_id>/campaign-state.json
```

Generated packages, NetCDF outputs, logs, worker settings, and runtime folders
remain runtime artifacts and must not be committed. Markdown reports may be
written to `docs/research/surface-forced-campaigns/` when the campaign matrix
explicitly names that committed report path.

## Comparison contract

The schema distinguishes **comparison type definitions** from **comparison instances**.

A comparison type definition describes the experiment design:

```yaml
comparison_type: forcing_sensitivity_same_duration
varied_fields: [surface_heat_flux_k_m_s, surface_moisture_flux_g_g_m_s]
required_equal_fields: [selection_id, duration, domain_size, horizontal_cell_count, nx, ny, nz, dx_m, dy_m, dz_m, stretch_z, str_bot_m, str_top_m, dz_bot_m, dz_top_m, model_top_m, output_cadence, cloud_chamber_commit, cm1_version, required_output_fields]
required_available_fields: [qc, w, hfx, qfx]
required_diagnostic_support: [cloud, vertical_velocity, surface_fluxes, low_level_response]
noncomparable_status: inconclusive_noncomparable_runs
```

A comparison instance appears on a run:

```yaml
comparison:
  type: forcing_sensitivity_same_duration
  control_matrix_id: phase2_easy_deep_default_12km_6h
```

The experiment run is the current run's `matrix_id`. If a report needs an explicit field, use:

```text
experiment_matrix_id = current run matrix_id
```

Do not require globally equal fields for all comparisons. Each comparison type must state which fields are allowed to vary and which fields must match. For example:

- heat-flux sensitivity varies only `surface_heat_flux_k_m_s` and CM1 `cnst_shflx`;
- moisture-flux sensitivity varies only `surface_moisture_flux_g_g_m_s` and CM1 `cnst_lhflx`;
- duration sensitivity varies duration/runtime only;
- domain/grid bundle sensitivity allows domain, `nx/ny/nz`, `dx/dy/dz`, model top, expected output volume, and cost/runtime to differ;
- cross-sounding discrimination allows selection/sounding identity and candidate metadata to differ, while forcing and run-shape assumptions should remain equal.

If a comparison violates its type contract, mark it `inconclusive_noncomparable_runs` rather than summarizing it as evidence.

## Phase 1 gate contract

Phase 1 must be allowed to stop the campaign before expensive later phases. The gate must distinguish wiring from atmospheric response.

### Gate states

```text
forcing_wiring_not_verified
surface_flux_response_verified
surface_flux_response_not_verified
surface_flux_response_inconclusive_missing_evidence
surface_flux_response_inconclusive_noncomparable
forcing_wiring_verified_but_response_not_verified
forcing_path_verified_for_campaign
inconclusive_missing_evidence
operator_override_continue
```

### Required gate behavior

- Missing selected/product forcing metadata: `forcing_wiring_not_verified`; block automatic continuation.
- Missing CM1-facing `cnst_shflx` or `cnst_lhflx`: `forcing_wiring_not_verified`; block automatic continuation.
- Missing `hfx` or `qfx` when requested: `inconclusive_missing_evidence`; block automatic continuation.
- Missing or unavailable standardized low-level response diagnostic:
  `forcing_wiring_verified_but_response_not_verified`; block automatic continuation
  after surface-flux response is verified.
- Matched Phase 1 emitted `hfx`/`qfx` values are present, trusted, unit-comparable, and every required Phase 1 comparison type is present: `surface_flux_response_verified`; continue to low-level response checks.
- Missing one of the required `heat_flux_sensitivity`, `moisture_flux_sensitivity`, or `combined_flux_sensitivity` comparisons: `surface_flux_response_inconclusive_missing_evidence`; block automatic continuation.
- Missing, untrusted, or not-ingested matched Phase 1 `hfx`/`qfx` statistics: `surface_flux_response_inconclusive_missing_evidence`; block automatic continuation.
- Mismatched `hfx`/`qfx` units or structurally non-comparable Phase 1 runs: `surface_flux_response_inconclusive_noncomparable`; block automatic continuation.
- Emitted means for intentionally varied fluxes do not move in the expected direction for the prescribed run-to-run forcing changes: `surface_flux_response_not_verified`; block automatic continuation. In the heat-only comparison, `hfx` increase is required and `qfx` change is informational. In the moisture-only comparison, `qfx` increase is required and `hfx` change is informational. In the combined comparison, both `hfx` and `qfx` increases are required.
- Heat-only run does not show a directionally consistent theta/temperature response when the diagnostic is available: `forcing_wiring_verified_but_response_not_verified`; block automatic continuation by default.
- Moisture-only run does not show a directionally consistent `qv` response when the diagnostic is available: `forcing_wiring_verified_but_response_not_verified`; block automatic continuation by default.

Only use `forcing_path_verified_for_campaign` when all of the following are true:

```text
selected values preserved
CM1-facing values preserved
emitted hfx/qfx evidence reflects prescribed changes
heat-only run shows directionally consistent theta/temp response
moisture-only run shows directionally consistent qv response
missing required fields do not affect those checks
```

An operator override may continue the campaign, but the report must preserve the override and must not label the forcing path or boundary-layer response as verified.

## Mapping report fields to current metadata

Where possible, #311 should map report fields to existing backend structures instead of inventing names:

- `ResultMetadata`: result ID, run ID, scenario/recipe IDs, observed sounding, run configuration, expected/required/missing fields, warnings, caveats, candidate screening, result state.
- `ScienceSummary`: first cloud time, liquid cloud-water top, coherent cloud-object top, raw hydrometeor trace top, deep-cloud state, max `qc`, max `w`, rain-water timing, default interesting time, support state where available.
- `ResultDiagnostics` and output-product payloads: field availability, units, min/max/mean when derivable, missing-field support states.

If the backend cannot provide a field, the report must say `unavailable` and identify the missing diagnostic rather than inventing a value.

Cloud Chamber commit and CM1 version/build are required per run in the summary contract unless #311 enforces them as immutable campaign-level values and validates every run against them.

## Low-level response diagnostic contract

Low-level `qv` and theta/temperature response is a backend-owned diagnostic.
The campaign runner must use this standardized output rather than improvising a
browser-side or report-local calculation.

```text
vertical layer: 0-1000 m AGL, using available model vertical coordinate
spatial statistic: thickness-weighted domain mean from vertical cell centers
reference time: first output time, preferably model time 0 or earliest available output
early evaluation time: output closest to 60 minutes after reference, bounded to 30-90 minutes
full-run evaluation time: final output time for the run
early response: early_evaluation_time_mean - reference_time_mean
full-run response: final_time_mean - reference_time_mean
forcing sensitivity: response difference against the paired control run with same sounding, duration, domain, grid, and cadence
units: preserve source field units; convert only if the backend has a documented conversion
```

The result metadata and science-summary payload preserve source field, units,
vertical-coordinate method, early-response endpoint indices/times/means/delta,
full-run endpoint indices/times/means/delta, and finite/non-finite endpoint
counts. Missing `qv`, missing theta/temperature, missing vertical coordinates,
unsupported vertical units, insufficient output times in the 30-90 minute early
window, or entirely non-finite endpoints produce explicit unavailable states.
Early-response availability and full-run-response availability are independent:
a valid early forcing response can remain available when the final endpoint is
missing, not distinct from the early endpoint, or entirely non-finite. Likewise,
a full-run delta can be reported as atmospheric-evolution evidence when the
early response window is missing, but it must not satisfy the Phase 1 gate.

For Phase 1 gate evaluation, heat-only comparisons require the
early theta/temperature response delta to increase against the matched control;
moisture-only comparisons require the early `qv` response delta to increase
against the matched control; combined comparisons require both. Full-run deltas
remain experiment evidence but must not be the only Phase 1 forcing-path gate.
Early endpoints must have at least 95% finite coverage at both the reference
and early evaluation time. Partially non-finite endpoints above that threshold
are reported as caveated; below that threshold they are missing evidence for the
gate, not a scientific non-response.
Non-varied low-level response changes are informational unless a later protocol
defines a field-specific stability tolerance. `theta_v` is moisture-coupled and
must not silently substitute for the thermal response gate unless a future
protocol explicitly requests virtual-potential-temperature response.

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
- Ingested metadata reports `hfx` and `qfx` separately when present.
- Heat/moisture changes produce directionally consistent `hfx`/`qfx` changes where derivable.
- Low-level thermal/moisture fields respond in the expected direction if derivable by the standardized low-level response diagnostic.
- Cloud timing, coherent cloud-object top, raw hydrometeor trace top, `qc`, or `w` response is summarized, even if weak.

Interpretation:

| Finding | Diagnosis |
| --- | --- |
| selected values missing from metadata/namelist | implementation failure |
| surface fields missing from output/ingest | output-product or CM1 output request gap |
| hfx/qfx present but not reflecting prescribed changes | surface forcing wiring not verified |
| hfx/qfx reflect prescribed changes but low-level theta/qv response absent | forcing wiring verified but atmospheric response not verified |
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

The 12 km to 60 km step is not a pure domain-size test when `horizontal_cell_count` is the same. With fixed `cells_128`, both the domain and horizontal spacing change. Treat this as a **domain/grid configuration bundle** and record resolved `nx/ny/nz`, `dx/dy/dz`, model top, cadence, expected output volume, and output volume. Do not conclude that “domain size caused deepening” unless a comparable grid design supports that claim.

Required evidence:

- Boundary-layer response compared with the matched Phase 2 control and Phase 1 behavior.
- Max coherent cloud-object top, raw hydrometeor trace top, and the time of each maximum.
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
| regional run differs from wide 12 km run | run-shape bundle matters; inspect domain, dx/dy, model top, cadence, and output volume before assigning cause |
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
- expected output volume;
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

After the first campaign, assign one or more categories:

```text
forcing_path_not_verified
surface_outputs_missing
boundary_layer_response_verified
forcing_wiring_verified_but_response_not_verified
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

Recommendations usually include one of:

- fix package/namelist/output wiring;
- adjust default surface flux values;
- adjust duration/domain/grid recommendations;
- add missing output products/diagnostics;
- proceed to differential surface forcing as a follow-up candidate;
- refine candidate screening;
- defer screening-hypothesis-vs-CM1-evidence comparison until better evidence exists.

## Required per-run metadata

Each run should record at minimum:

```text
schema_version
campaign_id
matrix_id
stable_resume_identity
run_id
result_id if ingested
package_status
run_status
ingest_status
queue_target
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
stretch_z / str_bot_m / str_top_m / dz_bot_m / dz_top_m
model_top_m
domain_size and resolved domain width
expected_output_volume
cloud_chamber_commit
cm1_version
required output fields
missing output fields
diagnostic_support
interesting_time_support_state
warnings / caveats
```

## Required evidence fields

The report should extract these from ingested metadata/output products when available:

```text
hfx_present
hfx_units
hfx_min / hfx_max / hfx_mean when derivable
hfx_finite_count / hfx_non_finite_count / hfx_total_count
qfx_present
qfx_units
qfx_min / qfx_max / qfx_mean when derivable
qfx_finite_count / qfx_non_finite_count / qfx_total_count
surface_moisture_flux_output_field
low_level_qv_response with early delta, method, or unavailable reason
low_level_qv_early_response_delta
low_level_qv_full_run_delta
low_level_qv_response_method
low_level_qv_response_source_field
low_level_qv_response_units
low_level_qv_early_response_start_mean / low_level_qv_early_response_end_mean
low_level_qv_early_response_start_time_seconds / low_level_qv_early_response_end_time_seconds
low_level_qv_response_first_mean / low_level_qv_response_final_mean
low_level_qv_response_first_time_seconds / low_level_qv_response_final_time_seconds
low_level_qv_response_first_finite_count / low_level_qv_response_final_finite_count
low_level_theta_or_temperature_response with early delta, method, or unavailable reason
low_level_theta_or_temperature_early_response_delta
low_level_theta_or_temperature_full_run_delta
low_level_theta_or_temperature_response_method
low_level_theta_or_temperature_response_source_field
low_level_theta_or_temperature_response_units
low_level_theta_or_temperature_early_response_start_mean / low_level_theta_or_temperature_early_response_end_mean
low_level_theta_or_temperature_early_response_start_time_seconds / low_level_theta_or_temperature_early_response_end_time_seconds
low_level_theta_or_temperature_response_first_mean / low_level_theta_or_temperature_response_final_mean
low_level_theta_or_temperature_response_first_time_seconds / low_level_theta_or_temperature_response_final_time_seconds
low_level_theta_or_temperature_response_first_finite_count / low_level_theta_or_temperature_response_final_finite_count
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
interesting_time_support_state
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
