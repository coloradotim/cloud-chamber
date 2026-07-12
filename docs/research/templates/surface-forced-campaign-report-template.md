# Surface-Forced Sounding Verification Campaign Report

Campaign ID: `<campaign_id>`
Schema version: `<schema_version>`
Protocol: `docs/research/surface-forced-sounding-verification-protocol.md`
Matrix: `<campaign-matrix>`
Date started: `<YYYY-MM-DD>`
Date completed: `<YYYY-MM-DD or incomplete>`
Cloud Chamber commit: `<commit-sha>`
CM1 version / build: `<cm1-version>`
Execution target: `<target>`

## Executive summary

Summarize what was tested and what the campaign can honestly conclude. Do not claim that a sounding should have produced deep convection. The comparison is conditional on forcing, domain, duration, grid, cadence, output fields, and diagnostics.

## Campaign question

```text
When surface heat/moisture forcing changes, does CM1 produce the expected package, output, and boundary-layer response?

Can an easy deep-candidate sounding deepen past shallow cumulus under uniform lower-boundary forcing, or does the result point toward missing configuration, missing diagnostics, a valid no-initiation outcome, or the need for differential forcing?
```

## Matrix summary

| Matrix ID | Phase | Selection | Forcing | Heat flux (K m/s) | Moisture flux (g/g m/s) | Domain | Horizontal cells | dx/dy | Duration | Cadence | Queue target | Run status | Result ID |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | --- | --- | --- | --- | --- | --- |
| `<matrix_id>` | `<phase>` | `<selection_id>` | `<forcing_id>` | `<value>` | `<value>` | `<domain>` | `<cells>` | `<dx>/<dy>` | `<duration>` | `<cadence>` | `<target>` | `<status>` | `<result_id>` |

## Candidate / sounding inventory

| Selection ID | Role | Station/time | Candidate story | Score | Key evidence | Caveats |
| --- | --- | --- | --- | ---: | --- | --- |
| `<selection_id>` | `<role>` | `<station/time>` | `<story>` | `<score>` | `<evidence>` | `<caveats>` |

## Per-run configuration table

| Matrix ID | Run ID | Result ID | cnst_shflx | cnst_lhflx | nx/ny/nz | dx/dy/dz | Model top | Output cadence | Required fields | Missing fields | Warnings/caveats |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | --- | --- | --- | --- |
| `<matrix_id>` | `<run_id>` | `<result_id>` | `<value K m/s>` | `<value g/g m/s>` | `<nx>/<ny>/<nz>` | `<dx>/<dy>/<dz>` | `<m>` | `<seconds>` | `<fields>` | `<fields>` | `<warnings>` |

## Per-run evidence table

| Matrix ID | hfx | lhfx | Low-level qv response | Low-level theta/temp response | First cloud | Max cloud top | Max qc | Max w | qr | surface rain | dbz | Evidence fields | Initial diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<matrix_id>` | `<present; units; min/max/mean>` | `<present; units; min/max/mean>` | `<value/method/unavailable>` | `<value/method/unavailable>` | `<time/unavailable>` | `<m at time>` | `<kg/kg at time>` | `<m/s at time/height>` | `<present/absent/unavailable>` | `<present/absent/unavailable>` | `<present/absent/unavailable>` | `<fields/diagnostics>` | `<category>` |

## Low-level response method

State exactly how low-level `qv` and theta/temperature response were computed, or mark them unavailable.

Required method fields:

```text
vertical layer:
spatial statistic:
reference time:
evaluation time:
paired control run:
source fields:
units:
```

If the standardized diagnostic is not implemented, write:

```text
unavailable: low_level_response_diagnostic_not_implemented
```

## Phase 1 — forcing-path smoke check

### Required checks

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| selected forcing values preserved in package metadata | `<pass/warn/fail/unavailable>` | `<run ids / fields>` | `<notes>` |
| selected values appear in CM1-facing namelist fields | `<pass/warn/fail/unavailable>` | `<cnst_shflx/cnst_lhflx>` | `<notes>` |
| `hfx` emitted/ingested | `<pass/warn/fail/unavailable>` | `<field/units/min/max/mean>` | `<notes>` |
| `lhfx` emitted/ingested | `<pass/warn/fail/unavailable>` | `<field/units/min/max/mean>` | `<notes>` |
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
inconclusive_missing_evidence
```

## Phase 2 — easy sounding response check

| Run | Boundary-layer response | Cloud top trend | Max w | Deep cloud? | Precipitation evidence | Interpretation |
| --- | --- | --- | ---: | --- | --- | --- |
| `<matrix_id>` | `<summary>` | `<summary>` | `<m/s at time/height>` | `<yes/no/unavailable>` | `<qr/rain/dbz>` | `<interpretation>` |

### Matched comparisons

| Comparison | Control | Experiment | What changed | Required matching fields | Result | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| forcing sensitivity | `phase2_easy_deep_default_12km_6h` | `phase2_easy_deep_strong_12km_6h` | forcing only | same sounding, duration, domain, grid, cadence | `<summary>` | `<interpretation>` |
| duration sensitivity | `phase2_easy_deep_strong_12km_6h` | `phase2_easy_deep_strong_12km_12h` | duration only | same sounding, forcing, domain, grid, cadence | `<summary>` | `<interpretation>` |
| domain/grid bundle sensitivity | `phase2_easy_deep_strong_12km_12h` | `phase2_easy_deep_strong_60km_12h` | domain and resolved spacing | same sounding, forcing, duration, cadence; record dx/dy change | `<summary>` | `<interpretation>` |

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

Comparison gate fields:

```text
sounding provenance
forcing values and CM1-facing values
duration
domain
grid and dx/dy/dz
output cadence
Cloud Chamber commit
CM1 version/build
required fields and missing fields
diagnostic support
```

Unsupported comparisons should be labeled `inconclusive_noncomparable_runs` rather than summarized as evidence.

### Phase 3 diagnosis

Choose one or more:

```text
model_discriminates_between_soundings
all_comparable_soundings_behave_similarly
candidate_selection_needs_refinement
control_case_not_distinct_enough
inconclusive_noncomparable_runs
inconclusive_missing_evidence
```

## Missing fields and diagnostics

| Field / diagnostic | Missing where | Impact |
| --- | --- | --- |
| `<field>` | `<runs>` | `<interpretation impact>` |

## Preliminary diagnosis

| Diagnosis category | Status | Minimum evidence | Campaign evidence |
| --- | --- | --- | --- |
| forcing path not verified | `<status>` | selected values missing from metadata/namelist or no surface-output support | `<evidence>` |
| surface outputs missing | `<status>` | `hfx`/`lhfx` unavailable or not ingested where requested | `<evidence>` |
| boundary-layer response verified | `<status>` | standardized low-level qv/theta response available and directionally plausible | `<evidence>` |
| uniform forcing too weak | `<status>` | stronger forcing changes response under matched duration/domain/grid/cadence, but target depth/signature still absent | `<evidence>` |
| uniform forcing physically limited | `<status>` | verified BL response plus matched stronger/longer/broader runs remain shallow with key diagnostics present | `<evidence>` |
| duration/domain limited | `<status>` | deeper response when duration or domain/grid bundle changes under otherwise comparable assumptions | `<evidence>` |
| candidate selection limited | `<status>` | weak/control and easy candidates do not separate as expected, or selection evidence was poor | `<evidence>` |
| valid no initiation under tested assumptions | `<status>` | forcing path and diagnostics verified; run assumptions documented; no deepening under those assumptions | `<evidence>` |
| inconclusive non-comparable runs | `<status>` | comparison changed too many assumptions or lacks matching fields | `<evidence>` |
| inconclusive missing evidence | `<status>` | required output fields or diagnostics unavailable | `<evidence>` |
| output products/diagnostics missing | `<status>` | fields exist but report cannot summarize needed evidence | `<evidence>` |
| differential forcing follow-up candidate | `<status>` | uniform forcing verified and responsive but does not focus ascent after configuration explanations are checked | `<evidence>` |
| radiation/place-time follow-up candidate | `<status>` | evidence suggests diurnal/place-time forcing is central and current assumptions cannot test it | `<evidence>` |

## Recommendations

Examples:

```text
- Fix package/output wiring before running more cases.
- Adjust default flux values or add stronger labeled examples.
- Prefer Regional 60 km / 12 h for first deep-candidate checks.
- Add low-level qv/theta response output products before next campaign.
- Treat differential forcing (#307) as a follow-up candidate because uniform forcing responds but does not focus ascent.
- Defer screening-hypothesis-vs-CM1-evidence comparison until #275 has required fields and status semantics.
```

## Artifact policy confirmation

Confirm that the committed report includes summaries only, not generated run folders, model output files, large logs, or local-only references.

## Appendix — portable run/result identifiers

| Matrix ID | Run ID | Result ID | Portable provenance notes |
| --- | --- | --- | --- |
| `<matrix_id>` | `<run_id>` | `<result_id>` | `<station/time/candidate provenance>` |
