# Cloud Chase 002: Fort Worth Detail Run

Issue: #350

## Fixed Setup

- Sounding: Fort Worth, TX, `USM00072249`, valid
  `1997-05-27T00:00:00Z`.
- Recipe: `deep_tower_benchmark_v0`.
- Initiation: stock CM1 `iinit = 3`, the built-in three-warm-bubble line
  trigger.
- Lower boundary: surface heat and moisture fluxes disabled.
- Sounding, microphysics, and trigger assumptions match the successful
  Cloud Chase 001 Fort Worth scout.

This was a resolution/detail probe for the already successful Fort Worth
deep-tower result. It was not a new sounding-selection test.

## Target Detail Shape

- Domain: 120 km by 120 km.
- Horizontal grid: 256 by 256 cells, 468.75 m dx/dy.
- Vertical grid: 100 levels, 250 m spacing, 25 km model top.
- Rayleigh damping: starts at 21 km.
- Output cadence: 5 minutes.
- Initial bounded duration: 60 simulated minutes.
- Expected saved frames: 13.

The run shape was intentionally above the prior scout's 20 km model top and put
Rayleigh damping above the prior 17.25 km coherent cloud top.

## Attempt 1: 3 s Timestep

Run ID: `cloud_chase_002-fort_worth_detail_60min`

- Runtime and integrity: CM1 ran for about 57.7 wall-clock minutes and reached
  13.0 simulated minutes, then stopped after `CFLMAX` exceeded 1.5. Runtime
  integrity is failed, not complete.
- Saved output: three model-output frames before failure.
- Coherent cloud top: existing partial diagnostics were not a stable coherent
  cloud-top result. The coherent object briefly reached the top-adjacent layer
  in the partial sequence and then collapsed to a shallow object by the last
  saved frame.
- Upper-cloud headroom: poor. The hydrometeor envelope reached about
  24.875 km in a 25 km domain, leaving only about 125 m of headroom.
- Maximum updraft: about 106.09 m/s in the saved partial diagnostics; the final
  CM1 stdout report before failure still showed `WMAX` about 102.43 m/s.
- Precipitation and reflectivity: no surface precipitation before failure.
  CM1 stdout showed rain water aloft by the terminal stats report, while the
  saved partial diagnostics only supported trace rain water aloft. Maximum
  reflectivity in the partial saved diagnostics was about 50.95 dBZ.
- Visibly better than the scout: not as a usable product result. The partial
  run was more intense and finer-gridded, but it was numerically unstable and
  upper-boundary limited before producing a useful 60-minute detail sequence.
- Worth the compute: no. The failure arrived before the run could produce a
  trustworthy visual-detail result.

## Attempt 2: 1.5 s Timestep

Run ID: `cloud_chase_002-fort_worth_detail_60min_dtl1p5`

- Runtime and integrity: stopped at user request after about 40.8 wall-clock
  minutes because the compute value was too low. CM1 had reached only about
  238.5 simulated seconds, before the first 5-minute output frame.
- Saved output: the initial model-output frame and stats file only.
- Coherent cloud top: unavailable as an interpretable saved-output diagnostic.
  The CM1 stdout stats near 4 simulated minutes reported `QCTOP` near
  24.875 km, but that is not a coherent-cloud product diagnostic.
- Upper-cloud headroom: still concerning. The stdout `QCTOP` signal already
  reached the top-adjacent layer before a useful saved frame existed.
- Maximum updraft: about 6.32 m/s in the latest stdout stats before stop.
- Precipitation and reflectivity: no saved diagnostic evidence beyond the
  initial frame. The latest stdout stats showed no surface precipitation.
- Visibly better than the scout: no interpretable visual result. The corrected
  timestep appeared numerically calmer, but the local wall-clock slope made the
  run non-useful before it produced a viewable 5-minute frame.
- Worth the compute: no. The projected local runtime for a 60-minute detail run
  was too high relative to the evidence it was likely to add.

## Recommendation

Do not extend or rerun the current 256 by 256 by 100 Fort Worth detail shape on
the current local compute path. The next Fort Worth visual-detail attempt should
keep the same sounding, Deep-Tower Benchmark trigger, disabled surface fluxes,
25 km top, and damping above 21 km, but use a compute-balanced detail shape
before launching another real CM1 run.
