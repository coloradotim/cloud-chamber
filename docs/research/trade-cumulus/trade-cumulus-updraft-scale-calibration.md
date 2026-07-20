# Trade Cumulus Updraft Scale Calibration

## Status and authority boundary

This document records calibration and implementation evidence for the candidate
Trade Cumulus Updraft Lens. It is not general product authority and does not
graduate the Cloud World, Recipe, Control, Lens, or MVP. The exact scale
decision came from the PM activation comment on issue #379; issue #377 supplied
the numerical evidence. No CM1 run occurred under issue #379.

## Decision and fixed scale

The PM-approved world-owned scale is
`trade_cumulus_updraft_velocity_v1` (`fixed_discrete`, `m/s`). It is specific to
Trade Cumulus and uses these exact half-open intervals:

| Vertical velocity | Color     | Interpretation                 |
| ----------------- | --------- | ------------------------------ |
| `< -1.0`          | `#4b0082` | strongest or clipped downdraft |
| `-1.0 to < -0.5`  | `#0057d9` | downdraft                      |
| `-0.5 to < -0.1`  | `#00c9d8` | weak downdraft                 |
| `-0.1 to < 0.1`   | `#ffffff` | near-neutral motion            |
| `0.1 to < 0.5`    | `#00d63b` | weak updraft                   |
| `0.5 to < 1.0`    | `#8fe000` | moderate updraft               |
| `1.0 to < 2.0`    | `#ffe000` | active updraft                 |
| `2.0 to < 3.0`    | `#ff9800` | strong updraft                 |
| `3.0 to < 5.0`    | `#ff3b00` | very strong updraft            |
| `>= 5.0`          | `#c40000` | exceptional or clipped updraft |

Values below `-1.0 m/s` and at or above `5.0 m/s` use endpoint colors. Clipping
counts remain in the Lens payload for technical diagnostics; the visible legend
reports the current slice minimum and maximum instead. The neutral interval is
exactly `[-0.1, 0.1) m/s`.

## Evidence sources

The read-only calibration inputs were:

- `result-bomex-370-full-20260719`, the preserved Stage 4 BOMEX result;
- `result-trade-cumulus-5b-full-baseline-20260720T162342Z`, the #377 Baseline;
- `result-trade-cumulus-5b-full-more_moisture-20260720T162342Z`, the #377 More Moisture Simulation.

The #377 matched-run report supplied the distribution evidence and traceability.
Figure 5 of [Morrison et al. (2026)](https://doi.org/10.1175/BAMS-D-25-0026.1)
supplied discrete signed-flow visual logic only. Its stronger congestus velocity
range and cloud-water boundary were not copied.

## Calibration method

Every saved model-output frame was read without scientific interpolation or
subsampling. The merged public
`center_vertical_velocity_to_scalar_grid(...)` method was applied exactly: a
vertical-face `w` grid with one extra level was centered by the arithmetic mean
of each adjacent face pair; an already scalar-level grid was used directly.
Finite statistics used the resulting scalar cells. Cloud-conditioned statistics
used the unchanged `ql >= 1e-6 kg/kg` mask.

Low clipping is `w < -1.0 m/s`; high clipping is `w >= 5.0 m/s`. Missing and
non-finite values are excluded from finite and clipping denominators.

## Distribution context from Stage 5B-2

The #377 pair-wide finite count was `111,206,400`, with extrema
`-6.159492 / 9.343031 m/s`.

Negative-subset quantiles (`m/s`):

| Dataset       |        p1 |        p5 |       p10 |       p25 |       p50 |       p75 |       p90 |       p95 |       p99 |
| ------------- | --------: | --------: | --------: | --------: | --------: | --------: | --------: | --------: | --------: |
| Baseline      | -0.662683 | -0.394454 | -0.296529 | -0.169646 | -0.072893 | -0.021260 | -0.004710 | -0.001585 | -0.000151 |
| More Moisture | -0.786535 | -0.466533 | -0.353980 | -0.208470 | -0.093865 | -0.028284 | -0.006086 | -0.001980 | -0.000170 |
| Pair          | -0.729601 | -0.432517 | -0.326226 | -0.188851 | -0.082705 | -0.024392 | -0.005320 | -0.001760 | -0.000160 |

Positive-subset quantiles (`m/s`):

| Dataset       |       p1 |       p5 |      p10 |      p25 |      p50 |      p75 |      p90 |      p95 |      p99 |
| ------------- | -------: | -------: | -------: | -------: | -------: | -------: | -------: | -------: | -------: |
| Baseline      | 0.000140 | 0.001356 | 0.003995 | 0.018010 | 0.064116 | 0.159325 | 0.323232 | 0.505377 | 1.051013 |
| More Moisture | 0.000155 | 0.001641 | 0.005014 | 0.023763 | 0.083693 | 0.200694 | 0.394275 | 0.596454 | 1.216397 |
| Pair          | 0.000147 | 0.001485 | 0.004450 | 0.020558 | 0.073159 | 0.179692 | 0.360132 | 0.553657 | 1.133881 |

Positive-`w` cloudy-cell quantiles (`m/s`):

| Dataset       |      p25 |      p50 |      p75 |      p90 |      p95 |      p99 |
| ------------- | -------: | -------: | -------: | -------: | -------: | -------: |
| Baseline      | 0.347638 | 0.715970 | 1.342463 | 2.223742 | 2.924758 | 4.492927 |
| More Moisture | 0.410502 | 0.829783 | 1.516918 | 2.481667 | 3.241838 | 4.826632 |
| Pair          | 0.381276 | 0.778887 | 1.441908 | 2.373120 | 3.111509 | 4.699079 |

The selected round categories suppress weak background motion around zero while
separating weak, active, strong, very strong, and exceptional Trade Cumulus
updrafts. They were not copied from the stronger congestus reference.

## Clipping results

All finite-cell measurements:

| Dataset            | Frames | Finite cells |      Min / max (m/s) |      Low count (%) |   High count (%) | Max-frame low / high (%) |
| ------------------ | -----: | -----------: | -------------------: | -----------------: | ---------------: | -----------------------: |
| Stage 4            |     73 |   22,425,600 | -5.225891 / 8.258350 |  32,979 (0.147060) |   899 (0.004009) |      0.574219 / 0.035156 |
| #377 Baseline      |    181 |   55,603,200 | -5.438223 / 9.082246 |  80,258 (0.144341) | 2,343 (0.004214) |      0.574219 / 0.045898 |
| #377 More Moisture |    181 |   55,603,200 | -6.159492 / 9.343031 | 138,533 (0.249146) | 4,217 (0.007584) |      0.814453 / 0.069987 |
| #377 pair          |    362 |  111,206,400 | -6.159492 / 9.343031 | 218,791 (0.196743) | 6,560 (0.005899) |      0.814453 / 0.069987 |

Cloud-conditioned finite-cell measurements using `ql >= 1e-6 kg/kg`:

| Dataset            | Cloudy finite cells |    Low count (%) |   High count (%) | Max-frame low / high (%) |
| ------------------ | ------------------: | ---------------: | ---------------: | -----------------------: |
| Stage 4            |             172,011 | 1,087 (0.631936) |   899 (0.522641) |      5.268390 / 3.292683 |
| #377 Baseline      |             427,626 | 2,643 (0.618063) | 2,343 (0.547909) |      5.268390 / 4.728370 |
| #377 More Moisture |             561,978 | 4,120 (0.733125) | 4,217 (0.750385) |      4.653313 / 4.599914 |
| #377 pair          |             989,604 | 6,763 (0.683405) | 6,560 (0.662891) |      5.268390 / 4.728370 |

## Interval occupancy

Each cell gives count and percent of all finite scalar-centered `w` cells.

| Interval (m/s)   |                 Stage 4 |           #377 Baseline |      #377 More Moisture |               #377 pair |
| ---------------- | ----------------------: | ----------------------: | ----------------------: | ----------------------: |
| `< -1.0`         |      32,979 (0.147060%) |      80,258 (0.144341%) |     138,533 (0.249146%) |     218,791 (0.196743%) |
| `-1.0 to < -0.5` |     258,887 (1.154426%) |     645,777 (1.161403%) |   1,059,776 (1.905962%) |   1,705,553 (1.533682%) |
| `-0.5 to < -0.1` |  4,507,240 (20.098637%) | 11,258,020 (20.247072%) | 12,878,434 (23.161318%) | 24,136,454 (21.704195%) |
| `-0.1 to < 0.1`  | 13,648,140 (60.859643%) | 33,685,549 (60.582033%) | 29,736,796 (53.480368%) | 63,422,345 (57.031201%) |
| `0.1 to < 0.5`   |  3,441,252 (15.345195%) |  8,602,994 (15.472120%) | 10,015,809 (18.013008%) | 18,618,803 (16.742564%) |
| `0.5 to < 1.0`   |     414,452 (1.848120%) |   1,027,287 (1.847532%) |   1,336,424 (2.403502%) |   2,363,711 (2.125517%) |
| `1.0 to < 2.0`   |     102,878 (0.458752%) |     253,876 (0.456585%) |     355,714 (0.639737%) |     609,590 (0.548161%) |
| `2.0 to < 3.0`   |      12,571 (0.056056%) |      31,385 (0.056445%) |      49,601 (0.089205%) |      80,986 (0.072825%) |
| `3.0 to < 5.0`   |       6,302 (0.028102%) |      15,711 (0.028256%) |      27,896 (0.050170%) |      43,607 (0.039213%) |
| `>= 5.0`         |         899 (0.004009%) |       2,343 (0.004214%) |       4,217 (0.007584%) |       6,560 (0.005899%) |

## Visual-reference boundary

The AMS figure supports a discrete signed-flow palette, visible near-zero class,
and black cloud boundary as visual logic. It does not numerically govern this
scale. Its precipitating cumulus congestus has stronger motion and uses a
different cloud-water boundary definition.

## Limits

This calibration covers one preserved Stage 4 result and one deterministic
Stage 5B-2 realization per Control state. It does not establish universal
shallow-cloud statistics, response uncertainty, causation, or suitability for
deep convection or another Cloud World. The cloud threshold remains exactly
`ql >= 1e-6 kg/kg`.

## Verification targets

The fixed scale must remain identical across eligible Trade Cumulus results,
saved frames, planes, orientations, two-dimensional and three-dimensional
views, and future synchronized Comparisons. Endpoint clipping telemetry must
remain available in the payload, missing values must remain distinct from
neutral motion, and no per-result percentile may control the Lens color scale.

All PM clipping stop thresholds passed: each #377 full-run finite-side fraction
was below 1%, every saved-frame finite-side fraction was below 5%, each #377
full-run cloudy-side fraction was below 5%, and every saved-frame cloudy-side
fraction was below 15%.
