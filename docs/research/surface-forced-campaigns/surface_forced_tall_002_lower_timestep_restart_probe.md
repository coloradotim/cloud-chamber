# Surface-Forced Tall 002 Lower-Timestep Restart Probe

Related issues: `#336`, `#318`

Campaign ID: `surface_forced_tall_002`

Probe run ID:

```text
surface_forced_tall_002-phase1_control_default_flux-dtl1_restart_probe
```

This note records a local diagnostic probe. It is not campaign evidence and it
does not make `surface_forced_tall_002` pass Phase 1.

## Summary

A lower-timestep restart probe carried the failed default-control state from the
`10800 s` restart checkpoint through `21600 s` without reproducing the terminal
multi-field numerical failure.

The original default-control run collapsed between `357.182 min` and
`357.234 min`. In the lower-timestep restart probe, the same model-time window
remained finite:

```text
357.166656 min: cflmax 0.4886, ksmax 0.0083, dt 2.0000
357.200012 min: cflmax 0.4886, ksmax 0.0083, dt 2.0000
357.233337 min: cflmax 0.4887, ksmax 0.0084, dt 2.0000
```

The probe finished with a normal stdout termination marker. Stderr reported
only `IEEE_UNDERFLOW_FLAG`, not invalid, divide-by-zero, or overflow flags.
All saved model-output frames from `11700 s` through `21600 s` were finite for
the tracked fields:

```text
qv, qc, qr, th, w, hfx, qfx, rain, dbz
```

`cm1out_stats.nc` contained `181` records from `10800 s` through `21600 s` and
no non-finite or sentinel statistics entries.

## Probe Setup

The probe used the existing default-control restart set:

```text
cm1rst_000001_*.dat
```

Copied inputs:

```text
namelist.input
input_sounding
LANDUSE.TBL
cm1_config.txt
cm1rst_000001_*.dat
```

Namelist changes:

```text
dtl      3.000    -> 1.000
irst     0        -> 1
rstnum   1        -> 1
run_time -999.9   -> 10800.0
```

Held fixed:

```text
sounding
surface heat flux
surface moisture flux
domain
grid
vertical stretching
model top
Rayleigh damping
microphysics
turbulence settings
surface model
output fields
output cadence
adaptive timestep enabled
```

Because `adapt_dt = 1`, this was not a fixed one-second timestep run. CM1
adapted to about `2.0 s` through the probe. The result should therefore be
described as a lower adaptive timestep-target probe, not a fixed timestep run.

## Output Evidence

The probe wrote normal-sized output files:

```text
cm1out_000014.nc through cm1out_000025.nc
cm1out_stats.nc
```

The final model-output frame was `cm1out_000025.nc` at `21600 s`. It was finite
for all tracked fields:

| Field | Finite count | Total count | Final-frame max |
| --- | ---: | ---: | ---: |
| `qv` | `1,638,400` | `1,638,400` | `0.0190186 kg/kg` |
| `qc` | `1,638,400` | `1,638,400` | `0.00226064 kg/kg` |
| `qr` | `1,638,400` | `1,638,400` | `0.0012692 kg/kg` |
| `th` | `1,638,400` | `1,638,400` | `430.29 K` |
| `w` | `1,654,784` | `1,654,784` | `6.04097 m/s` |
| `hfx` | `16,384` | `16,384` | `8.96993` |
| `qfx` | `16,384` | `16,384` | `5.79741e-5` |
| `rain` | `16,384` | `16,384` | `0.0503309` |
| `dbz` | `1,638,400` | `1,638,400` | `45.4486 dBZ` |

The final frame was not dynamically inert. It included finite rain water aloft,
finite surface rain, finite reflectivity, and a finite updraft maximum above
`6 m/s`.

The saved-output sequence also crossed several cloud/rain-active checkpoints
cleanly:

| Time | `max_qv` | `max_qc` | `max_qr` | `max_w` | `max_dbz` |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `18900 s` | `0.0330145` | `0.00804449` | `0.000130872` | `3.97059` | `7.26053` |
| `19800 s` | `0.0183238` | `0.00202592` | `0.000180616` | `5.55417` | `33.4126` |
| `20700 s` | `0.0190468` | `0.00128255` | `0.00159798` | `3.63463` | `37.1338` |
| `21600 s` | `0.0190186` | `0.00226064` | `0.0012692` | `6.04097` | `45.4486` |

This matters because the successful probe was not merely a quiet no-weather
case. It carried a cloud/rain/reflectivity-active state through the previous
failure window.

## Interpretation

The probe strongly suggests that the original terminal failure is sensitive to
the CM1 timestep path. It does not prove that `dtl` is the only required
stabilization, and it does not prove that a cold-start lower-timestep run will
always complete.

The probe is nevertheless enough to choose the next defensible campaign path:

```text
do not patch surface_forced_tall_002 into a passing campaign
do not queue Phase 2/3 yet
do not start differential forcing from this evidence
create surface_forced_tall_003 with a lower timestep target
rerun all four Phase 1 rows from cold start under the same numerical settings
```

Because `dtl` is a material numerical setting, a stabilized default-control row
cannot be compared as campaign evidence against the old high-sensible,
high-moisture, or high-both rows. The comparison matrix must be rerun
like-with-like.

## Recommended Next Step

Create and run `surface_forced_tall_003` Phase 1 with the same physical matrix
and a lower adaptive timestep target:

```text
default
high sensible only
high moisture only
high sensible + high moisture
```

The report should explicitly preserve:

```text
dtl target
adaptive timestep setting
runtime floating-point warnings
runtime-integrity state
surface-flux response state
low-level early-response state
field-quality state
```

Phase 2 remains blocked until the new four-row Phase 1 passes runtime-integrity,
surface-flux response, and low-level early-response gates.

