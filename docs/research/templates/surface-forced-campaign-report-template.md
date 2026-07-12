# Surface-Forced Sounding Verification Campaign Report

Campaign ID: `<campaign_id>`
Protocol: `docs/research/surface-forced-sounding-verification-protocol.md`
Matrix: `<campaign-matrix-path>`
Date started: `<YYYY-MM-DD>`
Date completed: `<YYYY-MM-DD or incomplete>`
Cloud Chamber commit: `<commit-sha>`
CM1 version / build: `<cm1-version>`
Runtime target: `<local | lan>`

## Executive summary

Summarize what was tested and what the campaign can honestly conclude. Do not claim that a sounding should have produced deep convection. The comparison is conditional on forcing, domain, duration, grid, cadence, output fields, and diagnostics.

## Campaign question

```text
When surface heat/moisture forcing changes, does CM1 produce the expected package, output, and boundary-layer response?

Can an easy deep-candidate sounding deepen past shallow cumulus under uniform lower-boundary forcing, or does the result point toward missing configuration, missing diagnostics, or the need for differential forcing?
```

## Matrix summary

| Matrix ID | Phase | Selection | Forcing | Domain | Duration | Queue target | Run status | Result ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<matrix_id>` | `<phase>` | `<selection_id>` | `<forcing_id>` | `<domain>` | `<duration>` | `<target>` | `<status>` | `<result_id>` |

## Candidate / sounding inventory

| Selection ID | Role | Station/time | Candidate story | Score | Key evidence | Caveats |
| --- | --- | --- | --- | ---: | --- | --- |
| `<selection_id>` | `<role>` | `<station/time>` | `<story>` | `<score>` | `<evidence>` | `<caveats>` |

## Per-run evidence table

| Matrix ID | hfx/lhfx present | Low-level qv response | Low-level theta/temp response | Max cloud top | Max w | Max qc | qr | surface rain | dbz | Missing fields | Initial diagnosis |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| `<matrix_id>` | `<yes/no/unavailable>` | `<summary>` | `<summary>` | `<m/unavailable>` | `<m/s/unavailable>` | `<kg/kg/unavailable>` | `<present/absent/unavailable>` | `<present/absent/unavailable>` | `<present/absent/unavailable>` | `<fields>` | `<category>` |

## Phase 1 — forcing-path smoke check

### Required checks

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| selected forcing values preserved in package metadata | `<pass/warn/fail/unavailable>` | `<run ids / fields>` | `<notes>` |
| selected values appear in CM1-facing namelist fields | `<pass/warn/fail/unavailable>` | `<cnst_shflx/cnst_lhflx>` | `<notes>` |
| hfx/lhfx or equivalent fields emitted/ingested | `<pass/warn/fail/unavailable>` | `<fields>` | `<notes>` |
| low-level qv response changes with moisture forcing | `<pass/warn/fail/unavailable>` | `<summary>` | `<notes>` |
| low-level theta/temp response changes with heat forcing | `<pass/warn/fail/unavailable>` | `<summary>` | `<notes>` |

### Phase 1 diagnosis

Choose one or more:

```text
forcing_path_not_verified
surface_outputs_missing
boundary_layer_response_verified
surface_model_or_units_question
run_too_short_for_response
```

## Phase 2 — easy sounding response check

| Run | Boundary-layer response | Cloud top trend | Max w | Deep cloud? | Precipitation evidence | Interpretation |
| --- | --- | --- | ---: | --- | --- | --- |
| `<matrix_id>` | `<summary>` | `<summary>` | `<m/s>` | `<yes/no/unavailable>` | `<qr/rain/dbz>` | `<interpretation>` |

### Phase 2 diagnosis

Choose one or more:

```text
easy_candidate_deepened_under_uniform_forcing
easy_candidate_remained_shallow_despite_response
run_duration_or_domain_limited
uniform_forcing_too_weak
uniform_forcing_physics_limited
missing_deep_diagnostics
```

## Phase 3 — cross-sounding discrimination check

| Selection | Same forcing/domain? | Response relative to easy candidate | Interpretation |
| --- | --- | --- | --- |
| `<selection_id>` | `<yes/no>` | `<summary>` | `<interpretation>` |

### Phase 3 diagnosis

Choose one or more:

```text
model_discriminates_between_soundings
all_soundings_behave_similarly
candidate_selection_needs_refinement
control_case_not_distinct_enough
```

## Missing fields and diagnostics

| Field / diagnostic | Missing where | Impact |
| --- | --- | --- |
| `<field>` | `<runs>` | `<interpretation impact>` |

## Preliminary diagnosis

| Diagnosis category | Status | Evidence |
| --- | --- | --- |
| forcing path not verified | `<status>` | `<evidence>` |
| surface outputs missing | `<status>` | `<evidence>` |
| boundary-layer response verified | `<status>` | `<evidence>` |
| uniform forcing too weak | `<status>` | `<evidence>` |
| uniform forcing physically limited | `<status>` | `<evidence>` |
| duration/domain limited | `<status>` | `<evidence>` |
| candidate selection limited | `<status>` | `<evidence>` |
| output products/diagnostics missing | `<status>` | `<evidence>` |
| differential forcing needed | `<status>` | `<evidence>` |
| radiation/place-time needed | `<status>` | `<evidence>` |

## Recommendations

Examples:

```text
- Fix package/output wiring before running more cases.
- Adjust default flux values or add stronger labeled examples.
- Prefer Regional 60 km / 12 h for first deep-candidate checks.
- Add low-level qv/theta response output products before next campaign.
- Proceed to differential forcing (#307) because uniform forcing responds but does not focus ascent.
- Defer predicted-vs-actual comparison until #275 has required fields and status semantics.
```

## Artifact policy confirmation

Confirm that the committed report includes summaries only, not generated run folders, model output files, large logs, or local machine settings.

## Appendix — run IDs and local pointers

| Matrix ID | Run ID | Result ID | Local notes |
| --- | --- | --- | --- |
| `<matrix_id>` | `<run_id>` | `<result_id>` | `<notes>` |
