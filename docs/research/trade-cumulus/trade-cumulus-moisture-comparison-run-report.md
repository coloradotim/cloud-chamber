# Trade Cumulus Moisture Comparison Run Report

## Status and authority

Implementation evidence state: `matched_runs_valid`.

This report records research and implementation evidence for the bounded Stage
5B-2 matched pair. It does not graduate the Trade Cumulus Control, Lens, Recipe,
World, or MVP; establish one-to-one identity between individual LES clouds;
approve a synchronized Comparison design; select a vertical-velocity color
scale; or supply final product explanation copy.

The deliberate question remains: how does stronger surface moisture supply
change the trade-cumulus field? The measured response below comes from one
deterministic LES realization per Control state.

## Sources, provenance, and identifiers

All four packages and runs were generated from clean Cloud Chamber commit
`49da1defc9914d3cc903ed9589c1312ddd843726`.

| Evidence | Value |
| --- | --- |
| Product slice | `trade_cumulus_v1` |
| Comparison group | `trade_cumulus_moisture_v1` |
| Case | `bomex_trade_cumulus_baseline_v0` |
| Recipe candidate | `canonical_bomex_baseline` |
| Run recipe | `null` |
| Control | `surface_moisture_supply` |
| CM1 release | `21.1` |
| CM1 official tag commit | `0f734f64efa89a684963a66d2ac32db67617912b` |
| CM1 source manifest SHA-256 | `fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e` |
| CM1 executable SHA-256 | `5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1` |
| Bundled BOMEX namelist SHA-256 | `4aa2f7cfad8c918801e0768c2618a37740e3966bc8f47205e5fafda3e506f965` |
| Fixed-assumptions SHA-256, both states | `71d746b110fb1310ebb6dafbef4cfa4bd44c379fc6964ed1787deaf45e422535` |
| Baseline science-settings SHA-256 | `b73d57b22c7e1e5b42688989d5c6c6752640c9e0c5c3b80de651cd36d53cf5e5` |
| More Moisture science-settings SHA-256 | `4365be4e5283531aeaea99c81c5003b2b743ebc726bb98cde913e966bc9af672` |

Scientific configuration sources are the CM1 r21.1 bundled shallow-cumulus
case and the BOMEX references recorded in each package manifest. The generated
full-run `input_sounding` hash was identical for both states:
`703cdbd38f9ef13712b86e1cc8d7aa19f40478947325d75b5266fafa94d6f645`.
The full-run namelist hashes were
`79ac6e7995733446cb372db54822b8fc60cc3c83ccb615fcfde70190ffbf8ea8`
for Baseline and
`88d88fe14783e4d76452bcbb3f5060d53c4e38f001c5abe7588f21348136e63f`
for More Moisture.

## Fixed and changed assumptions

The package comparison proved that the generated scientific namelists differ
only at `cnst_lhflx` after excluding package identity and provenance fields.
Baseline used `5.2e-5 g/g m/s`; More Moisture used `7.8e-5 g/g m/s`.
`changed_assumptions` contains only the Control identifier, Control state, and
surface moisture flux. The equal fixed-assumptions hashes cover the canonical
profiles, deterministic perturbation, `64 x 64 x 75` grid, `100 x 100 x 40 m`
spacing, `6.4 x 6.4 x 3.0 km` domain, surface sensible heat flux, friction
velocity, large-scale forcing, `ptype=6`, zero terminal velocity, adaptive
timestep target, required fields, and `120/60 s` output cadences.

The smoke/full package comparison found duration and consequent output count as
the only run-length differences. All packages used the same CM1 source,
executable, and Cloud Chamber commit.

## Run inventory

| State | Length | Run ID | Result ID |
| --- | --- | --- | --- |
| Baseline | smoke | `trade-cumulus-5b-smoke-baseline-20260720T162342Z` | `result-trade-cumulus-5b-smoke-baseline-20260720T162342Z` |
| More Moisture | smoke | `trade-cumulus-5b-smoke-more_moisture-20260720T162342Z` | `result-trade-cumulus-5b-smoke-more_moisture-20260720T162342Z` |
| Baseline | full | `trade-cumulus-5b-full-baseline-20260720T162342Z` | `result-trade-cumulus-5b-full-baseline-20260720T162342Z` |
| More Moisture | full | `trade-cumulus-5b-full-more_moisture-20260720T162342Z` | `result-trade-cumulus-5b-full-more_moisture-20260720T162342Z` |

## Smoke outcomes

The smokes ran sequentially and both passed before either full run launched.

| State | Model / diagnostic frames | Integrity | Required-field non-finite count | Emitted `qvflux` (g/g m/s) | Wall / CM1 time (s) | Output bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Baseline | 6 / 11 | trusted | 0 | `5.1999999414e-5` | 34.155 / 33.830 | 64,748,298 |
| More Moisture | 6 / 11 | trusted | 0 | `7.7999997302e-5` | 34.167 / 33.757 | 64,759,552 |

Both smokes completed with exit code zero, normal termination, successful
ingest, all required fields present, exact expected counts, no integrity
caveats, and no gate failures.

The observed smoke outputs estimated a 4,129,014,983-byte full pair. The launch
gate required 5,161,268,729 bytes after adding 25% headroom; 37,503,324,160
bytes were available after the smokes.

## Full-run outcomes

| State | Model / diagnostic frames | Integrity | Required-field non-finite count | Emitted `qvflux` (g/g m/s) | Wall / CM1 time (s) | Output bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Baseline | 181 / 361 | underflow-only caveat | 0 | `5.1999999414e-5` | 1,317.343 / 1,316.619 | 2,458,804,996 |
| More Moisture | 181 / 361 | underflow-only caveat | 0 | `7.7999997302e-5` | 1,394.962 / 1,394.195 | 2,530,095,437 |

Both six-hour runs completed sequentially with exit code zero, normal
termination, successful ingest, all required fields present, exact expected
counts, and no fatal or field-contamination evidence. The visible runtime
integrity caveat is limited to `IEEE_UNDERFLOW_FLAG`. No invalid,
divide-by-zero, overflow, stats-collapse, terminal-contamination, or gate
failure evidence was found.

Actual full-pair storage was 4,988,900,433 bytes. More Moisture used 71,290,441
additional bytes (+2.899%) and 77.619 additional wall-clock seconds (+5.892%).

## Stage 4 consistency

The new 120-second Baseline was compared with preserved result
`result-bomex-370-full-20260719` at all 37 exact common times from 0 through
21,600 seconds in 600-second increments. Coordinates and dimensions were
aligned explicitly. Tolerances were `atol=1e-10` and `rtol=1e-6`.

| Field | Maximum absolute difference | Maximum relative difference |
| --- | ---: | ---: |
| `ql` | 0 | 0 |
| `qv` | 0 | 0 |
| `th` | 0 | 0 |
| centered `w` | 0 | 0 |
| `cwp` | 0 | 0 |

The Stage 4 consistency gate passed with no first failure.

## Paired scalar metrics

Except where the method column says otherwise, aggregate cloud metrics use the
final three hours (`time >= 10800 s`). Percent deltas use Baseline as the
denominator and are reported only where meaningful. All entries have trusted
metric quality.

| Metric | Method / units | Baseline | More Moisture | Absolute delta | Percent delta |
| --- | --- | ---: | ---: | ---: | ---: |
| First isolated cloud liquid | first `ql >= 1e-6 kg/kg`, s | 1,080 | 1,080 | 0 | 0% |
| First coherent cloud | first frame with >=10 cloud cells, s | 1,320 | 1,200 | -120 | -9.091% |
| Mean total cloud cover | cloudy columns, % | 10.596 | 12.711 | +2.115 points | +19.956% |
| Cloud-fraction-profile peak | time-mean profile, % | 6.528 | 6.832 | +0.304 points | +4.652% |
| Cloud-fraction peak height | first peak, m | 620 | 620 | 0 | 0% |
| Domain-mean CWP mean | kg/m2 | 0.006352 | 0.009071 | +0.002719 | +42.812% |
| Domain-mean CWP minimum | kg/m2 | 0.001920 | 0.002379 | +0.000458 | +23.867% |
| Domain-mean CWP maximum | kg/m2 | 0.014611 | 0.020274 | +0.005663 | +38.757% |
| CWP growth/decay peaks | Stage 4 method, full run | 15 | 20 | +5 | +33.333% |
| Coherent cloud base | lowest supported level, m | 540 | 500 | -40 | -7.407% |
| Coherent cloud top mean | m | 1,668 | 1,805 | +137 | +8.194% |
| Coherent cloud top minimum | m | 1,140 | 1,300 | +160 | +14.035% |
| Coherent cloud top maximum | final-three-hour, m | 2,020 | 2,060 | +40 | +1.980% |
| Coherent cloud top maximum | full run, m | 2,020 | 2,220 | +200 | +9.901% |
| Maximum cloud liquid | raw `ql`, kg/kg | 0.002691 | 0.002942 | +0.000251 | +9.311% |
| Raw `w` minimum | m/s | -5.459 | -6.179 | -0.720 | +13.187% |
| Raw `w` maximum | m/s | 9.112 | 9.357 | +0.245 | +2.691% |
| Cloudy cells with positive centered `w` | pooled cloudy scalar cells, % | 90.379 | 90.451 | +0.072 points | +0.080% |
| Mean `qv`, 0-1000 m | thickness-weighted, kg/kg | 0.015947 | 0.016048 | +0.000101 | +0.634% |
| Mean `th`, 0-1000 m | thickness-weighted, K | 299.285 | 299.402 | +0.117 | +0.039% |

### Time-series markers

The complete 120-second series are retained in runtime evidence and are paired
by exact model time without interpolation. These markers summarize the cloud
series.

| Time (s) | CWP Baseline / More (kg/m2) | Cover Baseline / More (%) | Coherent top Baseline / More (m) |
| ---: | ---: | ---: | ---: |
| 10,800 | 0.007629 / 0.010541 | 12.939 / 13.599 | 1,740 / 1,860 |
| 14,400 | 0.006099 / 0.006887 | 10.254 / 12.158 | 1,660 / 1,660 |
| 18,000 | 0.011132 / 0.006576 | 10.059 / 11.938 | 1,780 / 1,860 |
| 21,600 | 0.007434 / 0.004003 | 10.400 / 12.305 | 1,620 / 1,660 |

| Time (s) | 0-1000 m `qv` Baseline / More (kg/kg) | 0-1000 m `th` Baseline / More (K) |
| ---: | ---: | ---: |
| 10,800 | 0.016016 / 0.016076 | 299.232 / 299.318 |
| 14,400 | 0.015978 / 0.016081 | 299.266 / 299.367 |
| 18,000 | 0.015934 / 0.016040 | 299.301 / 299.428 |
| 21,600 | 0.015891 / 0.016007 | 299.332 / 299.490 |

### Vertical-profile markers

Full final-frame `qv`, `th`, `u`, and `v` profiles and final-three-hour cloud
fraction and cloud-conditioned centered-`w` profiles are retained in runtime
evidence.

| Profile marker | Baseline | More Moisture |
| --- | ---: | ---: |
| Time-mean cloud-fraction peak | 6.528% at 620 m | 6.832% at 620 m |
| Cloud-conditioned centered `w` at 620 m | 0.562 m/s | 0.649 m/s |
| Maximum of cloud-conditioned centered-`w` profile | 1.394 m/s at 2,100 m | 1.263 m/s at 1,260 m |
| Final domain-mean `qv` at 620 m | 0.015809 kg/kg | 0.015889 kg/kg |
| Final domain-mean `th` at 620 m | 299.271 K | 299.433 K |
| Final domain-mean `u` at 580 m | -7.455 m/s | -7.496 m/s |
| Final domain-mean `v` at 580 m | -0.857 m/s | -0.961 m/s |

## Forcing and field trust

The emitted sensible heat flux was identical at
`0.00800000038 K m/s`; friction velocity was identical at
`0.2800000012 m/s`. The emitted surface moisture flux was constant within each
run and matched its intended Control value. Large-scale and transport fields
`ptb_frc`, `ptb_vturbr`, `qvb_frc`, `qvb_vturbr`, `qvflux`, `qvfr`, `thflux`,
`ufr`, `ug`, `upwp`, `ust`, `vfr`, `vg`, `vpwp`, `wprof`, and `wpwp` were
available in both results. Prescribed `ptb_frc`, `qvb_frc`, `ug`, `vg`, and
`wprof` ranges were unchanged.

All required fields had zero non-finite values in all four results. The full
runs expose the same 64 ingested fields, and neither full result has a missing
required field.

## Updraft Lens preparation and live checks

The merged Baseline Lens default is time index `152` (`18,240 s`) and vertical
x-z plane index `5` at `y=-2.650000095 km`. The same indices were applied to
More Moisture. Both results provide `ql`, centered `w`, centered `u/v`, and
`cwp` on exactly matching scalar-grid coordinates.

| Preparation value | Pair value |
| --- | ---: |
| Joint symmetric `w` range | -1.0 to +1.0 m/s |
| Joint perturbation-wind p95 reference | 0.9 m/s |
| Joint total-wind p95 reference | 8.8 m/s |
| Wind target / actual level | 600 / 580.000043 m |
| Wind stride | 8 |
| Cloud threshold | `1e-6 kg/kg` |

Playwright opened both full results in the live Explore implementation. At the
matched indices, both Updraft Lens views rendered the black cloud boundary,
horizontal perturbation arrows, working total-wind toggle, and the existing
3-D scalar field, threshold, opacity, and point-size controls. The fixed
individual-result `w` scales displayed as +/-0.9 m/s for Baseline and
+/-1.1 m/s for More Moisture. Desktop checks used a 1440 x 1000 viewport; an
additional 390 x 844 check had no horizontal document overflow and retained a
legible, proportioned slice. Screenshot-pixel analysis of the WebGL canvas
found 1,100 sampled colors with nonzero luminance variance. No console error,
page error, or failed request was recorded. Screenshots were not committed.

## Vertical-velocity calibration carryover

This report-only calibration responds to the PM evidence-carryover comment for
queued issue #379. It uses the exact merged
`center_vertical_velocity_to_scalar_grid` calculation over every full-run
scalar cell, without interpolation. It is calibration evidence only; no color
breakpoint or product decision is selected here.

| Dataset | Finite centered `w` cells | Minimum / maximum (m/s) | Negative / positive cells | Cloudy positive cells |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 55,603,200 | -5.438223 / 9.082246 | 29,142,402 / 26,153,598 | 388,608 |
| More Moisture | 55,603,200 | -6.159492 / 9.343031 | 29,197,064 / 26,098,936 | 511,313 |
| Pair combined | 111,206,400 | -6.159492 / 9.343031 | 58,339,466 / 52,252,534 | 899,921 |

Negative-subset quantiles, in m/s:

| Dataset | p1 | p5 | p10 | p25 | p50 | p75 | p90 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | -0.662683 | -0.394454 | -0.296529 | -0.169646 | -0.072893 | -0.021260 | -0.004710 | -0.001585 | -0.000151 |
| More Moisture | -0.786535 | -0.466533 | -0.353980 | -0.208470 | -0.093865 | -0.028284 | -0.006086 | -0.001980 | -0.000170 |
| Pair combined | -0.729601 | -0.432517 | -0.326226 | -0.188851 | -0.082705 | -0.024392 | -0.005320 | -0.001760 | -0.000160 |

Positive-subset quantiles, in m/s:

| Dataset | p1 | p5 | p10 | p25 | p50 | p75 | p90 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.000140 | 0.001356 | 0.003995 | 0.018010 | 0.064116 | 0.159325 | 0.323232 | 0.505377 | 1.051013 |
| More Moisture | 0.000155 | 0.001641 | 0.005014 | 0.023763 | 0.083693 | 0.200694 | 0.394275 | 0.596454 | 1.216397 |
| Pair combined | 0.000147 | 0.001485 | 0.004450 | 0.020558 | 0.073159 | 0.179692 | 0.360132 | 0.553657 | 1.133881 |

Positive-`w` quantiles for cloudy cells (`ql >= 1e-6 kg/kg`), in m/s:

| Dataset | p25 | p50 | p75 | p90 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.347638 | 0.715970 | 1.342463 | 2.223742 | 2.924758 | 4.492927 |
| More Moisture | 0.410502 | 0.829783 | 1.516918 | 2.481667 | 3.241838 | 4.826632 |
| Pair combined | 0.381276 | 0.778887 | 1.441908 | 2.373120 | 3.111509 | 4.699079 |

The existing pair-joint absolute-`w` p99 is `0.947341 m/s`; the merged rounded
reference is `1.0 m/s`, yielding the existing `[-1.0, +1.0] m/s` preparation
range.

## Direct observations and limits

Under the fixed methods, More Moisture had the same first isolated-cloud time,
an earlier first coherent-cloud frame, higher final-three-hour mean cloud
cover and CWP, a higher mean coherent cloud top, a higher near-surface `qv`
mean, and different cloud-cycle and vertical-velocity measurements. The exact
time markers also show that the CWP ordering is not uniform at every saved
time. Process cost and output size were higher for More Moisture by the amounts
reported above.

These are direct measurements from one deterministic realization per state.
Individual clouds are not paired one-to-one, sampling variability has not been
estimated, and the underflow-only runtime caveat remains visible for both full
runs. The comparison establishes neither general response uncertainty nor a
product disposition.

## Runtime-local evidence

Relative to the configured Cloud Chamber runtime home:

- `comparisons/trade-cumulus-moisture-20260720T162342Z/comparison_evidence.json`
- `comparisons/trade-cumulus-moisture-20260720T162342Z/vertical_velocity_calibration.json`
- each run directory listed above contains `trade_cumulus_moisture_run_evidence.json`, manifests, logs, and ingested result metadata

No generated package, NetCDF output, runtime JSON, log, screenshot, trace, CM1
source, executable, or local setting is committed with this report.

PM disposition pending
