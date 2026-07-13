# Surface-Forced Sounding Verification Campaign Report

Campaign ID: `<campaign_id>`
Schema version: `<schema_version>`
Protocol: `docs/research/surface-forced-sounding-verification-protocol.md`
Matrix: `<campaign-matrix>`
Date started: `<YYYY-MM-DD>`
Date completed: `<YYYY-MM-DD or incomplete>`
Cloud Chamber commit: `<commit-sha or campaign-level immutable value>`
CM1 version / build: `<cm1-version or campaign-level immutable value>`
Execution target: `<target>`

## Executive summary

Summarize what was tested and what the campaign can honestly conclude. Do not claim that a sounding should have produced deep convection. The comparison is conditional on forcing, domain, duration, grid, cadence, output fields, diagnostics, and build/runtime context.

## Campaign question

```text
When surface heat/moisture forcing changes, does CM1 produce the expected package, output, and boundary-layer response?

Can an easy deep-candidate sounding deepen past shallow cumulus under uniform lower-boundary forcing, or does the result point toward missing configuration, missing diagnostics, a valid no-initiation outcome, or the need for differential forcing?
```

## Matrix summary

| Matrix ID | Phase | Selection | Forcing | Heat flux | Moisture flux | Domain | Cells | dx/dy | Duration | Cadence | Queue target | Package status | Run status | Ingest status | Result ID |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| `<matrix_id>` | `<phase>` | `<selection_id>` | `<forcing_id>` | `<K m/s>` | `<g/g m/s>` | `<domain>` | `<cells>` | `<dx>/<dy>` | `<duration>` | `<cadence>` | `<target>` | `<status>` | `<status>` | `<status>` | `<result_id>` |

## Candidate / sounding inventory

| Selection ID | Source type | Source reference | Candidate ID | Role | Station/time | Candidate story | Score | Key evidence | Caveats |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `<selection_id>` | `<saved/cached/uploaded>` | `<reference>` | `<candidate_id>` | `<role>` | `<station/time>` | `<story>` | `<score>` | `<evidence>` | `<caveats>` |

## Per-run configuration table

| Matrix ID | Run ID | Result ID | Queue target | cnst_shflx | cnst_lhflx | nx/ny/nz | dx/dy/dz | Model top | Output cadence | Expected output volume | Commit | CM1 version | Required fields | Missing fields | Diagnostic support | Diagnostic trust | Interesting-time support | Warnings/caveats |
| --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<matrix_id>` | `<run_id>` | `<result_id>` | `<target>` | `<K m/s>` | `<g/g m/s>` | `<nx>/<ny>/<nz>` | `<dx>/<dy>/<dz>` | `<m>` | `<seconds>` | `<summary>` | `<sha>` | `<version>` | `<fields>` | `<fields>` | `<support>` | `<trusted/caveated/untrusted/unavailable by field>` | `<support>` | `<warnings>` |

## Per-run evidence table

| Matrix ID | hfx | qfx | low_level_qv_early_response_delta | low_level_qv_full_run_delta | low_level_theta_or_temperature_early_response_delta | low_level_theta_or_temperature_full_run_delta | first_cloud_time | max_cloud_top_m | max_qc | max_w_m_s | cloud_depth_or_classification | qr | surface rain | dbz | Diagnostic trust | Field-quality warnings | Evidence fields | Initial diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<matrix_id>` | `<present; units; min/max/mean>` | `<present; units; min/max/mean>` | `<early value/method/unavailable>` | `<full-run value/unavailable>` | `<early value/method/unavailable>` | `<full-run value/unavailable>` | `<time/unavailable>` | `<m at time>` | `<kg/kg at time>` | `<m/s at time/height>` | `<class/depth/unavailable>` | `<present/absent/unavailable>` | `<present/absent/unavailable>` | `<present/absent/unavailable>` | `<trusted/caveated/untrusted/unavailable by field>` | `<non-finite or other severe field-quality warnings>` | `<fields/diagnostics>` | `<category>` |

If `qc`, `w`, `qr`, surface `rain`, or `dbz` is entirely non-finite or materially contaminated by non-finite values, the run summary must mark the affected diagnostic as untrusted or caveated. Do not present surface rain, cloud top, updraft, rain-water-aloft, or reflectivity as clean evidence when the source field quality does not support that conclusion.

## Low-level response method

State exactly how backend-owned low-level `qv` and theta/temperature response
were computed, or mark them unavailable.

Required method fields:

```text
vertical layer:
spatial statistic:
reference time:
early response window:
full-run response:
paired control run:
source fields:
units:
finite/non-finite endpoint counts:
```

Phase 1 gate checks use the early response window. Full-run deltas remain useful
atmospheric-evolution evidence, but they are not clean forcing-path verification
after cloud, precipitation, entrainment, and downdraft feedbacks may have
developed.

## Phase 1 — forcing-path smoke check

### Wiring checks

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| selected forcing values preserved in package metadata | `<pass/warn/fail/unavailable>` | `<run ids / fields>` | `<notes>` |
| selected values appear in CM1-facing namelist fields | `<pass/warn/fail/unavailable>` | `<cnst_shflx/cnst_lhflx>` | `<notes>` |
| `hfx` emitted/ingested | `<pass/warn/fail/unavailable>` | `<field/units/min/max/mean/counts>` | Preserve output units separately from selected namelist controls. |
| `qfx` emitted/ingested | `<pass/warn/fail/unavailable>` | `<field/units/min/max/mean/counts>` | Preserve output units separately from selected namelist controls; do not assume `qfx` equals `cnst_lhflx`. |
| matched emitted surface-flux response | `<surface_flux_response_verified/not_verified/inconclusive>` | `<required comparison types; matched hfx/qfx means and units>` | Require heat-only, moisture-only, and combined comparisons. Compare emitted `hfx` to emitted `hfx`, and emitted `qfx` to emitted `qfx`; non-varied flux changes are informational unless a protocol-specific tolerance makes them required. |

### Atmospheric response checks

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| heat-only run shows directionally consistent early theta/temp response | `<pass/warn/fail/unavailable>` | `<summary>` | `<notes>` |
| moisture-only run shows directionally consistent early qv response | `<pass/warn/fail/unavailable>` | `<summary>` | `<notes>` |

### Phase 1 gate result

Choose one:

```text
forcing_wiring_not_verified
forcing_wiring_verified_but_response_not_verified
forcing_path_verified_for_campaign
inconclusive_missing_evidence
operator_override_continue
```

If an operator override continued the campaign, record why and do not label the forcing path or boundary-layer response as verified.

## Phase 2 — easy sounding response check

| Run | Boundary-layer response | Cloud top trend | max_w_m_s | Deep cloud? | Precipitation evidence | Interpretation |
| --- | --- | --- | ---: | --- | --- | --- |
| `<matrix_id>` | `<summary>` | `<summary>` | `<m/s at time/height>` | `<yes/no/unavailable>` | `<qr/rain/dbz>` | `<interpretation>` |

### Matched comparisons

Rows below are examples generated from each run's `comparison.type` and `comparison.control_matrix_id`; do not hardcode these if the matrix changes.

| Comparison type | Control | Experiment | What changed | Required equal fields | Required available fields | Result | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `forcing_sensitivity_same_duration` | `<control_matrix_id>` | `<current_matrix_id>` | forcing only | sounding, duration, domain/grid bundle, cadence, build, required fields | hfx, qfx, qv/theta response, qc, w | `<summary>` | `<interpretation>` |
| `duration_sensitivity_same_forcing` | `<control_matrix_id>` | `<current_matrix_id>` | duration only | sounding, forcing, domain/grid bundle, cadence, build, required fields | hfx, qfx, qv/theta response, qc, w | `<summary>` | `<interpretation>` |
| `domain_grid_bundle_sensitivity` | `<control_matrix_id>` | `<current_matrix_id>` | domain/grid bundle | sounding, forcing, duration, cadence, build, required fields | hfx, qfx, qv/theta response, qc, w | `<summary>` | `<interpretation>` |

Do not describe the 12 km to 60 km step as a pure domain test unless grid spacing and other run-shape assumptions are comparable.

### Phase 2 diagnosis

Choose one or more:

```text
easy_candidate_deepened_under_uniform_forcing
easy_candidate_remained_shallow_despite_response
run_duration_or_domain_limited
uniform_forcing_too_weak
uniform_forcing_physics_limited
valid_no_initiation_under_tested_assumptions
inconclusive_noncomparable_runs
inconclusive_missing_evidence
missing_deep_diagnostics
```

## Phase 3 — cross-sounding discrimination check

| Selection | Comparable to easy candidate? | Comparison gate result | Response relative to easy candidate | Interpretation |
| --- | --- | --- | --- | --- |
| `<selection_id>` | `<yes/no>` | `<same forcing/domain/grid/cadence/build/fields?>` | `<summary>` | `<interpretation>` |

Unsupported comparisons should use `inconclusive_noncomparable_runs`.

## Preliminary diagnosis

| Diagnosis category | Status | Evidence |
| --- | --- | --- |
| forcing path not verified | `<status>` | `<evidence>` |
| surface outputs missing | `<status>` | `<evidence>` |
| boundary-layer response verified | `<status>` | `<evidence>` |
| forcing wiring verified but response not verified | `<status>` | `<evidence>` |
| uniform forcing too weak | `<status>` | `<evidence>` |
| uniform forcing physically limited | `<status>` | `<evidence>` |
| duration/domain limited | `<status>` | `<evidence>` |
| candidate selection limited | `<status>` | `<evidence>` |
| output products/diagnostics missing | `<status>` | `<evidence>` |
| valid no-initiation under tested assumptions | `<status>` | `<evidence>` |
| inconclusive non-comparable runs | `<status>` | `<evidence>` |
| inconclusive missing evidence | `<status>` | `<evidence>` |
| differential forcing follow-up candidate | `<status>` | `<evidence>` |
| radiation/place-time follow-up candidate | `<status>` | `<evidence>` |

## Recommendations

Examples:

```text
- Fix package/output wiring before running more cases.
- Resolve missing or not-verified low-level qv/theta response evidence before
  continuing the campaign automatically.
- Adjust default flux values or add stronger labeled examples.
- Prefer Regional 60 km / 12 h for first deep-candidate checks.
- Proceed to differential forcing (#307) as a follow-up candidate because uniform forcing responds but does not focus ascent.
- Defer screening-hypothesis-vs-CM1-evidence comparison until #275 has required fields and status semantics.
```

## Artifact policy confirmation

Confirm that the committed report includes summaries only, not generated run folders, model output files, large logs, absolute local paths, or local settings.

## Appendix — run IDs and portable references

| Matrix ID | Run ID | Result ID | Portable notes |
| --- | --- | --- | --- |
| `<matrix_id>` | `<run_id>` | `<result_id>` | `<portable provenance only>` |
