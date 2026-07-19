# Surface-Forced Tall 002 Default-Control Stability Diagnosis

> **Status: Historical diagnosis with a superseded recommendation.** The final
> [issue #336 PM
> disposition](https://github.com/coloradotim/cloud-chamber/issues/336#issuecomment-4995992707)
> retained the safer-timestep lesson but superseded this document's recommendation
> for a cold-start `surface_forced_tall_003` matrix and closed the broader forensic
> campaign as not planned.

Related issues: `#336`, `#318`

Campaign ID: `surface_forced_tall_002`

Primary report: `docs/research/surface-forced-campaigns/surface_forced_tall_002.md`

Prior investigation: `docs/research/surface-forced-campaigns/surface_forced_tall_002_terminal_failure.md`

Follow-up probe: `docs/research/surface-forced-campaigns/surface_forced_tall_002_lower_timestep_restart_probe.md`

## Summary

The existing artifacts are sufficient to choose the next rerun path, but they
are not sufficient to declare a stabilized CM1 configuration.

The `surface_forced_tall_002` default-control run fails upstream of Cloud
Chamber ingest. The failure is reproduced by the matching
`surface_forced_tall_001` default-control run. The first bad persisted CM1
statistics record is `21480 s`; stdout narrows the visible collapse to between
`357.182 min` and `357.234 min`; the final `21600 s` output frame contains
terminal multi-field non-finite contamination.

The completed lower-timestep restart probe supports the targeted numerical
diagnosis path. It crossed the old failure interval and finished cleanly, but it
changed a material numerical setting and used a restart shortcut. Therefore the
campaign evidence must come from a new four-row Phase 1 matrix,
`surface_forced_tall_003`, not from patching `surface_forced_tall_002`.

## Artifact Scope

Runtime artifacts were inspected read-only. Local machine paths are omitted.

Primary failed run:

```text
surface_forced_tall_002-phase1_control_default_flux-4b99360e46
```

Matched failed reproduction:

```text
surface_forced_tall_001-phase1_control_default_flux-08be7858a2
```

Matched `surface_forced_tall_002` comparators:

```text
surface_forced_tall_002-phase1_control_high_sensible-56821294e3
surface_forced_tall_002-phase1_control_high_moisture-6d46cf11d1
surface_forced_tall_002-phase1_control_high_both-1c5b253ffb
```

Files inspected:

```text
namelist.input
cm1_config.txt
cm1out_stats.nc
cm1out_*.nc
logs/stdout.log
logs/stderr.log
run_manifest.json
```

No CM1 rerun was launched for this note.

## Configuration Comparison

The four `surface_forced_tall_002` Phase 1 rows use the same numerical,
microphysics, grid, domain, cadence, and output settings. The generated
namelist diffs show only the intended surface-flux changes:

```text
default vs high sensible: cnst_shflx changes from 8.0e-3 to 4.0e-2
default vs high moisture: cnst_lhflx changes from 5.2e-5 to 1.0e-4
```

The shared relevant settings include:

```text
dtl = 3.000
adapt_dt = 1
cm1setup = 1
hadvordrs/vadvordrs/hadvordrv/vadvordrv = 5
advwenos/advwenov = 2
idiff = 0
difforder = 6
sgsmodel = 1
tconfig = 1
doimpl = 1
psolver = 3
ptype = 5
isfcflx = 1
sfcmodel = 1
cecd = 3
set_flx = 1
```

Therefore, the default-control failure is not explained by a different domain,
timestep setting, microphysics option, turbulence option, output cadence, or
diagnostic-field request. It is a row-specific model-state failure under the
default flux values.

## Failure Timing

The last clearly finite persisted CM1 stats record is:

```text
mtime = 21420 s
```

The first persisted invalid CM1 stats record is:

```text
mtime = 21480 s
```

The first visible stdout collapse occurs between:

```text
357.182 min and 357.234 min
```

At the first invalid stats record, many diagnostics are already unusable:

```text
maxqv, minqv, maxqc, maxqr, maxqi, maxqs, maxqg
pratemax
rhmax, rhmin
kmhmax, kmvmax
```

The model then continues to `21600 s`, writes a terminal output frame, exits
with code `0`, and reports normal termination even though stderr reports fatal
floating-point flags.

## Last Healthy Stats Signal

The standout finite precursor is a near-terminal spike in turbulence
coefficients in the default-control row:

| Run | Time | `kmhmax/kmvmax` | `khhmax/khvmax` |
| --- | ---: | ---: | ---: |
| default control | `21420 s` | about `7.52e5 m^2/s` | about `2.25e6 m^2/s` |
| high sensible | `21420 s` | about `3.64e3 m^2/s` | about `1.09e4 m^2/s` |
| high moisture | `21420 s` | about `1.07e4 m^2/s` | about `3.22e4 m^2/s` |
| high both | `21420 s` | about `2.34e3 m^2/s` | about `7.02e3 m^2/s` |

This does not prove that turbulence closure is the root cause. The high-moisture
comparator briefly reaches large turbulence coefficients earlier in the run and
recovers. It does show that the failed default-control run enters an extreme
localized turbulence/diffusion state immediately before the persisted stats
collapse.

## Saved-Output Physical Clues

The final healthy saved output at `20700 s` is finite for the tracked fields.
The bad final output at `21600 s` is broadly non-finite:

```text
rain, prate, hfx, qfx, psfc, u10, v10, t2, q2,
th, prs, qv, qc, qr, qi, qs, qg,
uinterp, vinterp, winterp
```

Some staggered turbulence fields retain small finite zero-valued slices at the
domain boundary, but the physical state is not usable.

The pre-failure maxima in saved output are localized. For example, in the
default-control run:

```text
qv max: 0.03076 kg/kg at 17100 s, z about 20 m
qc max: 0.00595 kg/kg at 17100 s, z about 20 m
kmh/khh saved-output max: near the lower boundary
```

The high-moisture comparator has even larger saved-output low-level `qv` and
`qc` maxima and survives. That means low-level water content alone is not a
sufficient explanation. The evidence points to a coupled local
surface-layer/moisture/turbulence/microphysics failure near the endpoint.

## CM1 Guidance Relevant To The Next Probe

CM1 r21.1 `README.namelist` says that with `psolver = 2,3,4,5,6`, the large
timestep is limited by the fastest non-acoustic speed, and gives a rough
convective-storm estimate:

```text
dtl = min(dx, dy, dz) / 67
```

It also says that adaptive timestep runs still need a reasonable `dtl` target.

For this campaign:

```text
dx = 100 m
dy = 100 m
near-surface dz = 40 m
dtl = 3 s
adapt_dt = 1
```

Because the vertical grid is stretched and the near-surface spacing is small,
the current `3 s` target is not obviously conservative for this tall observed
surface-forced configuration. This is a numerical-stability concern, not proof
that timestep caused the failure.

CM1 also documents artificial diffusion options:

```text
idiff = 1
difforder = 6
kdiff6 between about 0.02 and 0.24
```

The current run has `idiff = 0`; `kdiff6 = 0.040` is present in the namelist but
not active under `idiff = 0`.

## Diagnosis

Current classification:

```text
Cloud Chamber ingest defect: unlikely
NetCDF final-write-only defect: unlikely
CM1 lifecycle failure: no, process exits 0
CM1 runtime-integrity failure: yes
Root CM1 subsystem: unresolved
Most likely failure area: localized surface-layer / saturation-adjustment /
moisture / turbulence instability near the endpoint
```

The existing evidence is enough to rule out product-copy, result-card, campaign
gate, and ingest/reporting explanations. It is not enough to choose a permanent
numerical configuration.

## Recommended Rerun Path

### Step 1: Targeted default-control numerical diagnosis

Completed as a diagnostic restart probe. The lower adaptive timestep-target
variant used:

```text
same sounding
same forcing values
same domain/grid/output fields
same microphysics/turbulence/surface model
dtl target lowered from 3.0 s to 1.0 s
adaptive timestep still enabled
```

It restarted from `10800 s`, crossed the previous `357.182-357.234 min` collapse
window with finite CFL/ks diagnostics, wrote finite saved output through
`21600 s`, and produced no invalid/divide-by-zero/overflow stderr flags. It
should not be treated as campaign evidence until it is rerun from the same
initial conditions used by the matrix.

If the lower-timestep default control still fails, the next diagnostic probes
should be considered in this order:

1. keep the lower timestep and activate modest sixth-order diffusion, for
   example `idiff = 1`, `difforder = 6`, `kdiff6 = 0.040`;
2. if needed, test a turbulence-configuration variant that directly addresses
   the lower-boundary coefficient spike.

Each probe must record exactly which numerical settings changed and must keep
surface forcing, sounding, domain, grid, output cadence, and required fields
fixed.

### Step 2: Campaign rerun scope

The probe changed `dtl`, a material numerical setting. Do not compare the
stabilized default-control probe against the old comparator rows as campaign
evidence. Create:

```text
surface_forced_tall_003
```

and rerun the four Phase 1 rows from cold start under the same updated
assumptions:

```text
default
high sensible only
high moisture only
high sensible + high moisture
```

### Step 3: Phase 2 remains blocked

Do not queue Phase 2/3 or start #307 differential forcing until the Phase 1
matrix has:

```text
runtime_integrity trusted or explicitly caveated-but-acceptable
surface-flux response verified
low-level early response verified
no terminal multi-field contamination
```

## #318 Update

#318 should continue to classify the current campaign as blocked. The update
from this diagnosis and the follow-up lower-timestep restart probe is:

```text
The default-control failure is reproducible in existing _001 and _002 artifacts,
is upstream of ingest, and is most consistent with a localized late-run CM1
runtime-integrity failure around the surface-layer/moisture/turbulence path.
The lower-timestep restart probe crossed the old failure interval and completed
with finite saved output and no stats sentinels, which strongly implicates the
timestep/numerical path. Because the probe changed dtl and used a restart, the
next campaign action is a cold-start four-row surface_forced_tall_003 Phase 1
matrix before Phase 2 evidence is trusted.
```
