# Supercell Presentation Run Report

## Status

Issue #421 is active after the accepted Supercells World implementation in
issue #423 and merged PR #427.

Current state:

```text
source_and_product_contract_reviewed
presentation_configuration_selected
characterization_completed_and_native_validated
final_process_completed_and_native_validated
bounded_product_adoption_ready_for_manual_review
```

The one authorized characterization and one authorized final process both
completed normally. No retry, tuning process, or third CM1 process was started.

## Stable product identity

The presentation run will back the existing stable product identity:

```text
world_id: supercells
simulation_id: supercells_quarter_circle_reference
display_name: Quarter-Circle Supercell
```

The run does not create another built-in Simulation or a second Supercell
scientific setup.

## Accepted source

```text
source run: quarter-circle-supercell-official-20260722T142521Z
source case: cm1_r21_1_quarter_circle_supercell_official_v0
CM1 release: 21.1
official commit: 0f734f64efa89a684963a66d2ac32db67617912b
```

Gate B accepted the source run as a coherent persistent rotating supercell.
Gate C and the merged World implementation established the native fields needed
by Rotating Updraft, Cloud and Precipitation, and Low-Level Interactions.

## Selected presentation configuration

| Property | Gate B source | Presentation run |
|---|---:|---:|
| Domain | 120 x 120 x 20 km | unchanged |
| Grid | 120 x 120 x 40 | 240 x 240 x 60 |
| Horizontal spacing | 1,000 m | 500 m |
| Vertical spacing | 500 m | 333.333333 m |
| Scalar cells | 576,000 | 3,456,000 |
| Large timestep | 6 s | 3 s |
| Duration | 7,200 s | 10,800 s |
| Saved-output cadence | 900 s | 120 s |
| Saved histories | 9 | 91 |

The presentation run preserves the accepted analytic thermodynamic profile,
quarter-circle hodograph, deterministic warm bubble, translating frame,
boundaries, damping, numerics, and Morrison microphysics.

Presentation-driven changes are limited to:

- grid and timestep;
- duration and saved-output cadence;
- NetCDF output transport;
- a narrower retained output inventory.

## Output contract

Required three-dimensional fields:

```text
th prs qv
qc qr qi qs qg
nci ncs ncr ncg
dbz
uinterp vinterp winterp
xvort yvort zvort
```

Required two-dimensional fields:

```text
rain prate uh cref
```

The package disables native staggered `u`, `v`, and `w` duplicates, turbulence
output (`tke`, `km`, `kh`), and the unused stock swath fields. It retains total
potential temperature, pressure, and water vapor as a small thermodynamic
inspection margin without enabling a new Lens or cold-pool claim.

## Resource plan before execution

The final run has:

- six times the source scalar-cell count;
- three times the source integration work from timestep and duration;
- eighteen times the approximate integration workload before output overhead;
- 91 histories instead of 9.

The complete required numeric history floor is calculated without compression
credit. It is approximately 24.0 GB before NetCDF metadata, statistics, logs,
and reports. Launch requires that floor plus at least 5 GiB free.

The Gate B source completed in 552.652 seconds. Direct workload scaling gives an
initial final-run estimate near 2.8 hours before dense-output and mature-storm
overhead. The planning band is 3-6 hours.

One 300-second characterization process is authorized at the exact final grid,
timestep, and field inventory. It writes only the initial and 300-second
histories. Its sole purpose is to verify memory, field output, output size, and
measured cost before the full process. It is not a tuning run.

No automatic retry is authorized for either process.

## Characterization evidence

The exact-final-grid characterization used the final 240 x 240 x 60 grid,
3-second timestep, and required output inventory for 300 model seconds. It
completed normally with:

| Evidence | Measured value |
|---|---:|
| Runtime | 295.448 s |
| Peak resident memory | 1,595,932,672 bytes |
| Saved histories | 2 |
| History bytes | 55,154,210 bytes |
| Retained run bytes | 55,728,945 bytes |
| Free space after validation | 36,319,924,224 bytes |

Both expected histories at 0 and 300 seconds were present. Every required
field had the expected dimensions and units and contained only finite values.
CM1 emitted its normal completion marker. Standard error contained only the
known nonfatal `IEEE_UNDERFLOW_FLAG`.

Simple measured-time scaling projects the 10,800-second integration to about
2.95 hours before the denser mature-storm output overhead. The final planning
band is therefore 3-4 hours. The actual characterization files demonstrate
NetCDF4 storage reduction, but final launch eligibility continues to assume no
compression and retains the 22.34 GiB numeric floor plus 5 GiB reserve.

Decision:

```text
advance_to_single_final_presentation_process_without_configuration_change
```

## Final execution evidence

The final process used the exact characterized configuration and completed
normally:

| Evidence | Measured value |
|---|---:|
| Runtime | 12,327.202 s (3 h 25 min 27 s) |
| Peak resident memory | 1,720,270,848 bytes |
| Saved histories | 91 |
| Numbered history bytes | 8,870,127,252 bytes |
| Retained run bytes | 8,873,437,520 bytes |
| Free space after validation | 26,913,161,216 bytes |

The output contains the complete 0–10,800 second history at an exact 120-second
cadence. Every required field has the expected dimensions and units and only
finite values. CM1 exited with status 0 and emitted its normal-completion
marker. Standard error contained only the known nonfatal
`IEEE_UNDERFLOW_FLAG`.

Exactly two CM1 processes were used:

1. one 300-second exact-configuration characterization;
2. one 10,800-second final presentation run.

There was no automatic or manual retry and no configuration change between the
two processes.

## Scientific review

Native-grid review uses `winterp` at the nearest native level to 3.25 km, the
established signed vertical-velocity palette, and a black total-condensate
boundary at 0.05 g/kg. It does not interpolate values or identify cell
lineage.

Matched 60-, 90-, and 120-minute comparisons show that 500 m horizontal
spacing resolves materially finer updraft, downdraft, and condensate structure
than the accepted 1 km Gate B source. The 120-second output cadence replaces
the source run's 15-minute jumps with a continuous presentation sequence.

Representative later evolution:

| Time | Native evidence |
|---|---|
| 120 min | Strong southern core remains embedded in a broad field of secondary convection. |
| 140 min | Persistent southern convection continues while northern structures reorganize. |
| 160 min | Renewed intense rotation reaches 1,827.9 m^2/s^2 maximum 2–5 km AGL UH. |
| 180 min | Multiple active structures span the domain; the strongest native updraft is outside the fixed storm-focused viewport. |

The longer duration adds useful evolution, but the later field is not treated
as one tracked storm. The report does not assign split, merger, or parent-child
lineage to the multiple convective structures.

## Product adoption

The validated run is wired to the existing stable product identity on this
manual-review branch:

```text
world_id: supercells
simulation_id: supercells_quarter_circle_reference
backing_run_id: quarter-circle-supercell-presentation-v1-20260723
default_explore_time: 4,440 s
```

The World inventory remains metadata-only. It validates compact promotion
evidence and file fingerprints without opening 91 NetCDF histories. A selected
Explore frame opens only its selected history.

Two bounded visualization products are available:

- **Storm region:** a fixed 80 x 80 km native-grid inspection window spanning
  x = -40 to 40 km and y = -45 to 35 km.
- **Full domain:** deterministic every-other-cell sampling of the complete
  120 x 120 km domain, yielding a 1 km display grid without interpolation.

The storm region is deliberately fixed across time. It does not follow or
recenter on a cell. Full domain remains necessary for later outer-domain
structures. Selected-point evidence uses the strongest-updraft column visible
in the active viewport, while provenance records that selection rule.

The default 74-minute frame gives the Explore workspace an immediately useful
mature-storm state while preserving all 91 outputs on the shared timeline.
Adjacent-frame prefetch prioritizes the next frame during playback.

Measured local endpoint behavior:

| Request | Latency | Serialized payload |
|---|---:|---:|
| World inventory, cold | 20 ms | 1,790 bytes |
| World inventory, warm | 1 ms | 1,790 bytes |
| Rotating Updraft, storm region | 0.93 s | 3.09 MB |
| Cloud and Precipitation, storm region | 0.69 s | 3.20 MB |
| Low-Level Interactions, storm region | 0.62 s | 3.02 MB |
| Lens frames, full domain | 0.42–0.54 s | 1.82–1.98 MB |

Desktop Playwright review at 1920 x 1080 exercised all three Lenses, storm and
full-domain viewports, selected-point Context, section orientation, maximize
and restore, and continuous playback through frame 91. The 3-D and slice views
remained synchronized and the browser console contained no application errors.

## Review packet

The external review packet contains:

- `matched-gate-b-presentation.png`;
- `presentation-later-evolution.png`;
- `cadence-comparison.gif`;
- `presentation-frame-diagnostics.json`;
- `native-review-summary.json`;
- final desktop screenshots for all three Lenses, both viewports, selected
  point evidence, vertical sections, maximize/restore, and the 180-minute
  endpoint.

The committed renderer reproduces the native scientific images from the
preserved Gate B and presentation runs. Native CM1 output and generated media
remain outside the repository.

## Limitations and disposition

- The simulation remains in a translating model frame with native
  model-relative winds.
- The fixed storm region excludes some later outer-domain activity by design;
  Full domain is the authoritative overview.
- Full-domain visualization samples every other native horizontal cell and can
  miss a single-cell native extremum. Native validation retains all cells.
- The upper Rayleigh-damping layer remains part of the accepted configuration;
  upper-domain interpretation should retain that caveat.
- Low-Level Interactions coordinates ascent, descent, condensate, rain, and
  flow but does not diagnose a cold pool.
- The run supports visual examination, not tornado diagnosis, forecasting, or
  publication-grade storm tracking.

Final disposition for manual PM review:

```text
advance_to_manual_presentation_run_review
```
