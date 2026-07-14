# Surface-Forced Tall 002 Terminal Failure Investigation

Campaign ID: `surface_forced_tall_002`
Related issue: `#333`
Report: `docs/research/surface-forced-campaigns/surface_forced_tall_002.md`

## Summary

The Phase 1 default-control run fails numerically near the end of the 6-hour
integration. This is not an ingest-only defect and not just a misleading
diagnostic label.

The run produces finite saved CM1 output through `20700 s`, then CM1's own
statistics become invalid before the final `21600 s` output is written. The
final output file contains all-non-finite values for many core fields. CM1 still
exits with code `0` and prints `Program terminated normally`, so launcher status
alone is not sufficient evidence of a scientifically usable run.

Phase 2 and Phase 3 should remain blocked. Differential forcing should not be
started from this evidence. The current blocker is that the default Phase 1
control does not remain trustworthy through the declared endpoint.

## Artifacts Inspected

Runtime artifacts were inspected read-only from the existing local campaign
workspace. The committed evidence here intentionally avoids machine-private
runtime paths.

Primary run:

```text
surface_forced_tall_002-phase1_control_default_flux-4b99360e46
```

Comparators:

```text
surface_forced_tall_002-phase1_control_high_sensible-56821294e3
surface_forced_tall_002-phase1_control_high_moisture-6d46cf11d1
surface_forced_tall_002-phase1_control_high_both-1c5b253ffb
surface_forced_tall_001-phase1_control_default_flux-08be7858a2
```

Files inspected:

```text
cm1out_*.nc
cm1out_stats.nc
logs/stdout.log
logs/stderr.log
run_manifest.json
namelist.input
cm1_config.txt
```

## Findings

### Saved Output Failure Time

The first saved CM1 output file with non-finite key fields is:

```text
cm1out_000025.nc at 21600 s
```

All earlier saved outputs through `cm1out_000024.nc` at `20700 s` are finite for
the tracked key fields.

At `21600 s`, the default-control output has all-non-finite values for:

```text
rain, prate, hfx, qfx, u10, v10, t2, q2, th, prs, qv, qc, qr, qi, qs, qg,
uinterp, vinterp, winterp, u, v
```

`w`, `kmh`, `kmv`, `khh`, and `khv` are partly finite but materially
contaminated. `kmh` and `kmv` include `Infinity`.

### Internal Failure Time

`cm1out_stats.nc` shows the first invalid persisted statistics record at:

```text
mtime = 21480 s = 358.000 min
```

The last clearly finite stats record before collapse is:

```text
mtime = 21420 s = 357.000 min
```

`logs/stdout.log` narrows the collapse further. The first obviously broken CFL
line appears between the `357.182 min` and `357.234 min` model-step prints:

```text
357.182 min: cflmax 0.7602, ksmax 0.0122
357.234 min: cflmax 0.0000, ksmax 0.0000
```

After that, CM1 stats show sentinel extrema for velocity and hydrometeor fields:

```text
UMAX  -0.100000E+31
UMIN   0.100000E+31
MAXqv -0.100000E+31
MINqv  0.100000E+31
MAXqc -0.100000E+31
MAXqr -0.100000E+31
KMHMAX Infinity
CFLMAX 0.000000 with zeroed location indices
```

This means the model state or diagnostic buffers are already invalid before
`cm1out_000025.nc` is written.

### Runtime Completion Status

The run manifest reports:

```text
exit_code = 0
lifecycle_state = completed
```

CM1 stdout ends with:

```text
Program terminated normally
```

But stderr reports:

```text
IEEE_INVALID_FLAG
IEEE_DIVIDE_BY_ZERO
IEEE_OVERFLOW_FLAG
IEEE_UNDERFLOW_FLAG
```

That combination should be treated as a completed process with untrusted science
output, not as a clean completed result.

### Reproducibility From Existing Artifacts

The same failure appears in the previous campaign attempt:

```text
surface_forced_tall_001-phase1_control_default_flux-08be7858a2
```

It has the same first bad saved frame, the same `21600 s` terminal contamination,
the same `satadj2` sequence near `357 min`, and the same IEEE invalid /
divide-by-zero / overflow / underflow warning set.

This is enough to call the failure reproducible across existing artifacts,
without queueing another full campaign.

### Comparator Runs

The three `surface_forced_tall_002` non-default Phase 1 runs complete without
non-finite key fields in the saved `cm1out_*.nc` files:

```text
phase1_control_high_sensible
phase1_control_high_moisture
phase1_control_high_both
```

Their runtime/grid/numerical setup matches the default control:

```text
duration: 21600 s
output cadence: 900 s
restart cadence: 10800 s
timestep: 3 s with adaptive dt enabled
grid: 128 x 128 x 100
dx/dy: 100 m
model top: 18 km
vertical stretch: enabled
Rayleigh damping start: 12 km
microphysics/turbulence/surface model settings: same
```

The meaningful differences are the intended surface heat/moisture forcing
values.

Therefore the failure is not explained by a different domain, cadence, timestep,
microphysics option, or output configuration in the default row.

### Precursors Before Collapse

The default-control run shows several warning signs before the terminal collapse:

```text
max qv reaches about 0.093 kg/kg at 274 min
max qc reaches about 0.0238 kg/kg at 274 min
max qv reaches about 0.082 kg/kg at 312 min
kmh/kmv reaches about 751619 m^2/s at 357 min
khh/khv reaches about 2.25e6 m^2/s at 357 min
```

Immediately before collapse, stdout prints a long `satadj2` sequence with large
values:

```text
satadj2 iteration 51..84: about 707 and 197500 in the printed columns
```

Those values are not enough by themselves to identify the exact CM1 subsystem
that fails, but they strongly suggest the bad final frame is preceded by a
model-state instability around saturation adjustment / moisture / turbulence,
not by a pure NetCDF write or Cloud Chamber ingest problem.

## Answers To #333 Questions

### When does the first non-finite value appear?

For saved output, the first non-finite key-field evidence appears in
`cm1out_000025.nc` at `21600 s`.

For internal CM1 statistics, the first persisted invalid record is
`cm1out_stats.nc` at `21480 s`.

Stdout narrows the first visible collapse to the interval:

```text
357.182 min to 357.234 min
```

### Which field fails first?

The existing output cadence cannot isolate a single first field. By the first
bad persisted stats record, velocity extrema, qv, qc, qr, hydrometeor extrema,
surface precipitation rate, RH, and turbulence coefficients have already failed
together or are reporting sentinel values.

The earliest distinctive precursor in stdout is the `satadj2` sequence before
the CFL collapse. The most suspicious science fields before collapse are the
large `maxqv` spikes and very large eddy viscosity/diffusivity values.

### Does the process complete normally?

At the process level, yes: CM1 exits with code `0` and prints normal
termination. Scientifically, no: the final state is not trustworthy because the
model reports IEEE exceptions and writes non-finite terminal output.

### Is this an ingest defect?

No, not primarily. Cloud Chamber ingest correctly reports the terminal
non-finite fields. The bad state is visible in CM1 stdout and `cm1out_stats.nc`
before the final NetCDF file is written.

### Is this a corrupted final output write?

Unlikely as the primary cause. The final write contains bad values, but CM1's
own per-minute stats have already collapsed before the writeout. A final-write
bug cannot be ruled out completely without CM1-side debugging, but the evidence
points upstream of NetCDF serialization.

### Does reducing timestep or changing numerical controls prevent it?

Not answered from existing artifacts. That requires a targeted diagnostic rerun.
Because that would touch real CM1 execution, it should be done deliberately and
not as part of a blind full-campaign rerun.

## Classification

Current Phase 1 classification should remain:

```text
inconclusive_missing_evidence
```

More specifically:

```text
low_level_early_response: verified
finite hfx/qfx directional response: strongly supported
default-control endpoint integrity: failed
overall Phase 1 gate: blocked
```

This is not evidence that uniform forcing is physically inadequate. It is
evidence that the default-control run becomes numerically untrustworthy before
the declared 6-hour endpoint.

## Recommended Next Action

Do not queue Phase 2 or Phase 3. Do not start differential forcing from #307.

Run a targeted default-control numerical diagnosis before any new campaign rows:

1. Reuse the default-control package assumptions, but shorten output cadence or
   add higher-frequency stats around `21000-21600 s` if possible.
2. Rerun only the default control as a diagnostic, not as Phase 1 evidence, with
   the same numerical settings to confirm the collapse timing from a clean run.
3. If reproduced, run one minimal numerical-control variant, such as a reduced
   timestep or stricter adaptive timestep cap, to test whether the endpoint
   survives.
4. If a numerical-control change is required, create `surface_forced_tall_003`
   and rerun all four Phase 1 rows under the same updated assumptions:

```text
default
high sensible
high moisture
high both
```

Do not compare a newly stabilized default control against experiments that used
different timestep, diffusion, damping, microphysics, or solver settings.

If a CM1-side inspection shows this is an output/write-only defect, regenerate or
rerun only the default control and reevaluate the existing four-run Phase 1 gate.
Current evidence does not favor that path.

## Product Follow-Up

Cloud Chamber should eventually treat this pattern as a stronger runtime
integrity signal:

- process exit `0` plus `Program terminated normally` is not enough;
- IEEE invalid/divide-by-zero/overflow flags should visibly caveat or fail
  endpoint trust;
- CM1 stats sentinel extrema such as `-1e30`, `1e30`, `Infinity`, or
  zero-location CFL collapse should be promoted to run-integrity evidence.

That follow-up should not weaken the existing #329 field-quality handling; it
should make the launcher/result status more honest when CM1 reports normal
process completion but the physics state is invalid.
