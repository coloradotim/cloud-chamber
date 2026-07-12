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
2. **Configuration issue** — forcing, duration, domain, grid, or output cadence was not suitable for the question.
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
- Ingested metadata reports `hfx`/`lhfx` when present.
- Low-level thermal/moisture fields respond in the expected direction if derivable.
- Cloud timing, cloud top, `qc`, or `w` response is summarized, even if weak.

Interpretation:

| Finding | Diagnosis |
| --- | --- |
| selected values missing from metadata/namelist | implementation failure |
| surface fields missing from output/ingest | output-product or CM1 output request gap |
| hfx/lhfx present but low-level theta/qv response absent | CM1 setup/units/surface-model issue or too-short run |
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
Wide 12 km / 12 h / stronger flux
Regional 60 km / 12 h / stronger flux
Regional 120 km / 12 h / stronger flux if feasible
```

Required evidence:

- Boundary-layer response compared with Phase 1.
- Max cloud top and time of cloud top.
- Max `w` and height/time of max `w` if available.
- Max `qc` and cloud depth.
- `qr`, surface `rain`, and `dbz` presence separately.
- Whether the result appears shallow, congestus-like, or deep.
- Whether missing outputs prevent interpretation.

Interpretation:

| Finding | Diagnosis |
| --- | --- |
| no boundary-layer response | return to Phase 1 implementation/config diagnosis |
| shallow cumulus only, even with stronger forcing | likely uniform-forcing limitation or too-stable sounding |
| deeper cloud only at longer duration or larger domain | defaults likely too short/small/weak |
| deep cloud/updraft but no precipitation fields | output/microphysics/diagnostic gap or dry outcome |
| deep evidence present but not summarized | Results/Explore diagnostic gap |

## Phase 3 — Cross-sounding discrimination check

Goal: test whether CM1 response differs across sounding classes under the same forcing setup.

Suggested candidate set:

```text
low-CIN / easy deep candidate
strongly capped deep candidate
humid/rainy candidate
inverted-V / dry microburst-ish candidate
weak or marginal control sounding
```

Run the same forcing/domain/duration setup across the set. Do not tune each case until after the first comparison pass.

Required evidence:

- Same run matrix for each sounding.
- Same output/diagnostic fields.
- Same summary metrics.
- Candidate story/evidence carried through metadata.
- Which differences are model output differences vs missing-field differences.

Interpretation:

| Finding | Diagnosis |
| --- | --- |
| every sounding behaves nearly the same | forcing/config may be too generic or diagnostics too coarse |
| only easy deep case deepens | model path may be working; candidate selection matters |
| capped case stays shallow while easy case deepens | useful discrimination |
| all cases shallow despite clear BL response | likely need differential forcing or larger-scale lift/convergence |

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
differential_forcing_needed
radiation_or_place_time_needed
```

The campaign should end with explicit next-step recommendations, usually one of:

- fix package/namelist/output wiring;
- adjust default surface flux values;
- adjust duration/domain/grid recommendations;
- add missing output products/diagnostics;
- proceed to differential surface forcing;
- refine candidate screening;
- defer deep-convection comparison until better evidence exists.

## Required per-run metadata

Each run should record, at minimum:

```text
campaign_id
matrix_id
run_id
result_id if ingested
station_id
station_name
valid_time_utc
candidate_id if any
candidate story / active story
candidate score and caveats
source path: cached / saved / uploaded
surface_heat_flux_k_m_s
surface_moisture_flux_g_g_m_s
CM1 cnst_shflx
CM1 cnst_lhflx
duration
domain
grid cells
output cadence
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
hfx/lhfx present
qv low-level response
theta/temp low-level response
first cloud time
max cloud top
max qc
max w
qr / rain water aloft present
surface rain present
dbz / reflectivity present
first deep cloud time if available
deep cloud flag if available
interesting time support state
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
  wide 12 km / 12 h / stronger flux
  regional 60 km / 12 h / stronger flux

weak control sounding:
  regional 60 km / 12 h / stronger flux
```

This is enough to identify whether the path is responsive before spending time on larger regional runs.

## Artifact policy

Do not commit:

- generated CM1 packages;
- NetCDF output;
- local runtime folders;
- copied runtime tables;
- stdout/stderr logs;
- screenshots, traces, videos;
- local settings or SSH configuration.

A committed campaign report may include:

- run IDs;
- result IDs;
- station/time provenance;
- selected configuration values;
- summarized diagnostics;
- caveats and unavailable fields;
- links or paths that are safe for local use if they do not expose local secrets.

## Relationship to future work

This protocol feeds:

- campaign runner/report tooling;
- differential surface forcing;
- predicted-vs-actual comparison;
- radiation/place-time validation;
- candidate screening calibration.

It does not replace those issues. It creates the lab notebook structure needed before they can be trusted.
