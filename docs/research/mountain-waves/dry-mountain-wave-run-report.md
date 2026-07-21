# CM1 r21.1 Dry Mountain-Wave Run Report

## Status and boundary

Gate B executed the exact official-duration dry mountain-wave package once. CM1
completed normally and wrote the expected native NetCDF histories, but the
committed evaluator stopped on a source-interpretation discrepancy:

```text
NetCDF ztop is 20000 m, expected inert value 18000 m.
```

The actual output is consistent with CM1 r21.1 source behavior. In an
unstretched grid, `src/param.F` replaces the namelist value with `dz*nk` before
`src/writeout_nc.F` writes `ztop`. The emitted scalar is therefore the active
20,000 m top, not the inactive 18,000 m namelist entry expected by Gate A and
the evaluator.

Issue #403 requires an evaluator discrepancy to stop the gate and forbids a
correction or second process. No correction is included in this report and no
second CM1 process ran. Read-only inspection of the preserved native files is
recorded below to bound the defect, but it is diagnostic context rather than a
successful evaluator disposition.

This work reproduces a source-bundled dry benchmark. It does not approve a
Cloud World, Recipe, Simulation, moist mountain case, cloud response, terrain
visualization, browser contract, or product direction.

## Decision question

The configured runtime did faithfully execute the official case at practical
local cost. The native output appears complete, finite, terrain-consistent, and
structurally interpretable. However, Gate B cannot make the required trusted
coordinate disposition while its committed evaluator rejects the actual
r21.1 top metadata. The candidate therefore cannot advance in this PR.

## Implementation and evidence identity

| Item | Value |
| --- | --- |
| Case and scenario ID | `cm1_r21_1_dry_mountain_wave_official_v0` |
| Run ID | `dry-mountain-wave-official-20260721T183530Z` |
| Package/run implementation commit | `9ff73ff244c393bee2a2e93a851ad1ba2dc16287` |
| Report provenance | This report is committed later on the same branch and does not change the recorded package/run implementation commit. |
| Run Recipe | `null` |
| Recipe ID | `null` |
| Cloud World ID | absent |
| Runtime package status before launch | packaged, preflight passed, no output-like files |
| Final runtime lifecycle | completed, exit code 0 |

Runtime files remain outside the repository. No machine-private path, NetCDF,
log, plot, screenshot, executable, CM1 source, or generated run directory is
committed.

## CM1 provenance

The package and execution preflight independently verified the configured
runtime against CM1 release 21.1 and official tag commit
`0f734f64efa89a684963a66d2ac32db67617912b`.

| Evidence | SHA-256 |
| --- | --- |
| Configured executable | `5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1` |
| Sorted configured `src/*.F` manifest | `fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e` |
| `README.namelist` | `7b95be56db51f5c9396c59dca252cf96b918a312cc70107451f91149a34ab3b5` |
| Official `nh_mountain_waves/namelist.input` | `9578207be201d0f250f6398414e1afb539e6f1b842c2448a10910b5ffd5c15b5` |
| Generated `namelist.input` | `bf202fb8e50abb903d50cb1cbeb86fb114efc88ff8049ab41ebf5bdd550b43be` |
| `src/init_terrain.F` | `813e579983c0f55347d5eb54828709eedb5911a08587b216ea668c9d03cbca7c` |
| `src/base.F` | `9c88a1021ddde22d02680786246c52bcffb040cbd72c3c4708f24fe24eec32ef` |
| `src/input.F` | `e8b3bb25e0b624d79da7d361a2027431b55f98434abfe19b4385d7c7e1692663` |
| `src/param.F` | `cac64a6cb4363c6b88367b5cb9391f1bcf2130c63ffedef6e5973c03b190c349` |
| `src/bc.F` | `5b7353a08b13eb9f69e4b89e250aec0e7918df3c93bd48c8539ab850787716e3` |
| `src/writeout.F` | `bef128e897d09dbc9ae86ec13bb156794e605a7c2da1596058de53c71d640dbd` |
| `src/writeout_nc.F` | `5023244d7ce4f9a0dde7df9c780cf5c70b675097e8467c4fbfc8125e254f4710` |

The executable linked both NetCDF C and NetCDF-Fortran libraries. Package and
execution preflights found a clean worktree at the implementation commit, no
active CM1 process, matching source and executable provenance, and no prior
Gate B execution.

## Official namelist audit

The generated audit parsed all 342 assignments. Restoring the three approved
values made the generated file byte-equivalent to the official file. The only
material differences were:

| Name | Official | Generated | Classification |
| --- | ---: | ---: | --- |
| `output_format` | `1` | `2` | approved NetCDF transport change |
| `output_filetype` | `1` | `2` | approved numbered-file change |
| `output_interp` | `1` | `0` | approved native-grid-only change |

The complete machine- and human-readable runtime audits also recorded these
mandatory inactive values as unchanged:

| Name | Value |
| --- | ---: |
| `ibalance` | `0` |
| `axisymm` | `0` |
| `imove` | `0` |
| `alphobc` | `60.0` |
| `nudgeobc` | `0` |
| `roflux` | `0` |
| `xhd` | `100000.0` |
| `hrdamp` | `0` |
| `ztop` | `18000.0`, inactive because `stretch_z=0` |

The package retained the small launch-contract `input_sounding` with status
`present_for_launch_contract_not_consumed_by_isnd_9`. The runtime checklist
staged no scientifically consumed external file and explicitly excluded
`LANDUSE.TBL`, `perts.dat`, all three input grids, and an external sounding.

## Storage and execution preflight

| Item | Evidence |
| --- | ---: |
| Expected histories | 11 |
| Expected times | 0 through 2,160 s at 216 s cadence |
| Estimated NetCDF | 21,725,535 bytes |
| Estimated stats and logs | 20,971,520 bytes |
| Estimated package | 2,097,152 bytes |
| Estimated total | 44,794,207 bytes |
| Required free space, 2x estimate | 89,588,414 bytes |
| Available before execution | 28,638,277,632 bytes |

All ten execution-preflight checks passed immediately before launch, including
clean commit identity, complete namelist preservation, exact provenance,
critical source hashes, exact output differences, inactive-value preservation,
the non-consumed sounding label, NetCDF linkage, empty runtime-input checklist,
and the double-estimate storage gate.

## Run lifecycle and cost

Exactly one process started through the existing local run manager using the
redacted logical command `configured_cm1_run_directory/cm1.exe`.

| Item | Result |
| --- | --- |
| Start | `2026-07-21T18:39:22.268150Z` |
| Finish | `2026-07-21T18:39:32.365734Z` |
| Wall clock | 10.097584 s |
| Exit code | 0 |
| Normal-termination marker | present |
| Stderr | 0 bytes |
| Floating-point flags | none |
| Runtime warnings | none |
| Stdout | 2,019,400 bytes |
| Peak memory | unavailable from the current local run manager |

The CM1 stats file contained 1,081 samples from 0 through 2,160 s. `cflmax`
was finite throughout and ranged from `0.1008904` to `0.1412708`. Total mass
ranged from `39,024,488,448` to `39,024,533,504 kg`, a range of 45,056 kg or
approximately `1.15e-6` of the minimum value. No formal benchmark tolerance is
inferred from those descriptive values.

## Native output inventory

CM1 wrote `cm1out_000001.nc` through `cm1out_000011.nc`, exactly matching times
`0, 216, 432, 648, 864, 1080, 1296, 1512, 1728, 1944, 2160 s`. Individual
history files ranged from 235,738 to 426,915 bytes and totaled 4,421,256 bytes.
No history was missing, duplicated, or extra.

The files identify `CM1 version=cm1r21.1`, `CF-1.7`, `nx=100`, `ny=1`,
`nz=100`, `imoist=0`, west/east boundary type 2, north/south type 1,
bottom/top type 1, and `axisymm=0`.

| Required field | Dimensions and shape per history | Units | Staggering | Finite / non-finite per history |
| --- | --- | --- | --- | ---: |
| `zs` | `time,yh,xh`; `1x1x100` | m | scalar horizontal | 100 / 0 |
| `zhval` | `time,zh,yh,xh`; `1x100x1x100` | m | scalar vertical | 10,000 / 0 |
| `th` | `time,zh,yh,xh`; `1x100x1x100` | K | scalar vertical | 10,000 / 0 |
| `prs` | `time,zh,yh,xh`; `1x100x1x100` | Pa | scalar vertical | 10,000 / 0 |
| `u` | `time,zh,yh,xf`; `1x100x1x101` | m/s | x-face | 10,100 / 0 |
| `v` | `time,zh,yf,xh`; `1x100x2x100` | m/s | y-face | 20,000 / 0 |
| `w` | `time,zf,yh,xh`; `1x101x1x100` | m/s | full-level | 10,100 / 0 |

Coordinates were `xh=100`, `xf=101`, `yh=1`, `yf=2`, `zh=100`, and `zf=101`;
horizontal and nominal vertical coordinates use kilometers. Additional emitted
fields were `f_cor`, `sws`, `svs`, `sps`, `sus`, `shs`, `uinterp`, `vinterp`,
`winterp`, and `ztop`. No moisture-like field was emitted. Their presence does
not assign scientific meaning to dry-inapplicable official output switches.

## Terrain and coordinate checks

Read-only diagnostics against the preserved output found:

| Check | Result |
| --- | ---: |
| Analytic terrain | `400 / (1 + ((x - 100 m) / 1000 m)^2)` |
| Terrain maximum and x location | 400.0 m at approximately 100.000001 m |
| Half-height locations | -900.000036 and 1100.000024 m, both 200.0 m |
| Maximum analytic terrain error | 0.00002283 m |
| Terrain time variation | 0.0 m |
| `zhval` transform maximum error | 0.003148 m |
| Minimum physical scalar spacing | 196.0 m |
| Reconstructed full-level bottom error from terrain | 0.0 m |
| Reconstructed top range across columns | 0.0 m |
| Final nominal `zf` / active top | 20,000.0 m |
| Actual NetCDF scalar `ztop` | 20,000.0 m |

The terrain and transformed heights are internally consistent when the active
20 km top is used. The blocking problem is the committed evaluator's assertion
that actual NetCDF `ztop` must equal the inactive 18 km namelist value.

Source inspection explains the output without changing the scientific case:
for `stretch_z<1`, `src/param.F` assigns `ztop=dz*nk`; with `dz=200 m` and
`nk=100`, this is 20 km. `src/writeout_nc.F` then writes that runtime value.
The later bounded correction should preserve final nominal `zf` as the
terrain-transform authority, require the emitted scalar to agree with the
active top for this configuration, and update the synthetic fixture and Gate A
wording. This PR does not implement that correction.

## Base state and lower boundary

At time zero the upstream and domain-mean flow was exactly `u=10 m/s`, `v=0`.
The initial stability calculation over the west 20 percent used
`N^2=(g/theta_mid)*(delta theta/delta physical height)` and found a median
`0.00010000003 s^-2`, with range `0.00009999107` to `0.00010000844 s^-2`,
consistent with configured `N=0.01 s^-1`. Pressure decreased in all 9,900
tested vertical differences. All thermodynamic fields were finite.

At 2,160 s, upstream mean `u` was `10.0217 m/s`; domain-mean `u` had changed by
`+0.0312 m/s` and domain-mean `v` by `-0.0188 m/s`. The small background change
does not by itself indicate an unexplained balance failure, but the blocked
gate does not promote that observation to acceptance evidence.

The lower-boundary calculation used arithmetic face-to-scalar averaging for
`u` and `v`, coordinate gradients for terrain slope, and residual
`w-(u*dzs/dx+v*dzs/dy)`. At representative times:

| Time (s) | Residual RMS (m/s) | P95 abs. (m/s) | Residual range (m/s) | Predicted/observed correlation |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0.03351 | 0.11243 | -0.15604 to 0.15604 | 0.999615 |
| 432 | 0.04012 | 0.11898 | -0.19412 to 0.18064 | 0.999588 |
| 1080 | 0.03883 | 0.11441 | -0.18843 to 0.17427 | 0.999588 |
| 2160 | 0.04020 | 0.11802 | -0.19529 to 0.18027 | 0.999589 |

These diagnostics support credible terrain tangency on the 200 m grid. They do
not establish a formal error tolerance absent from the official case.

## Dry-wave structure

Runtime-only physical-height inspection showed alternating positive and
negative `w` bands rooted at the ridge and tilting downstream with height. The
response expanded vertically and downstream through the official duration
rather than collapsing into isolated cells. No plot is committed.

| Time (s) | Min `w` (m/s), x/z (m) | Max `w` (m/s), x/z (m) | Theta perturbation range (K) | Descriptive sign regions |
| ---: | --- | --- | --- | ---: |
| 0 | -2.636 at 700/294 | 2.636 at -500/294 | 0.000 to 0.000 | 2 |
| 432 | -3.087 at 700/294 | 2.800 at -300/345 | -1.004 to 0.734 | 42 |
| 1080 | -2.991 at 700/294 | 2.701 at -300/345 | -1.069 to 0.737 | 99 |
| 2160 | -3.094 at 700/294 | 2.794 at -300/345 | -1.066 to 1.010 | 171 |

Sign regions used 10 percent of each frame's maximum absolute `w` only as a
descriptive mask, not a pass threshold. The evolving potential-temperature
displacement and the paired ascent/descent bands are consistent with a
terrain-forced gravity-wave response. A corrected evaluator still needs to
make the authoritative structural disposition from the preserved files.

## Boundary and damping assessment

The metric partitions were the outer 20 percent at west/east versus the
central 60 percent, and heights below 14 km versus the Rayleigh layer and top
2 km.

| Time (s) | Central `w` RMS below 14 km | Boundary `w` RMS below 14 km | Rayleigh-layer `w` RMS | Top-2-km `w` RMS |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0.12383 | 0.00223 | 0.00000 | 0.00000 |
| 432 | 0.31715 | 0.05138 | 0.01077 | 0.00929 |
| 1080 | 0.42589 | 0.18132 | 0.03526 | 0.01295 |
| 2160 | 0.54084 | 0.37216 | 0.15562 | 0.05446 |

The central signal remained stronger than the boundary zones, and top-layer
amplitude remained well below central lower-atmosphere amplitude. Boundary and
Rayleigh-layer activity grew with time, so reflection and damping deserve the
intended scientific review. The source bundle supplies no quantitative
acceptance tolerance, and the evaluator discrepancy prevents this gate from
declaring those effects non-material.

## Cloud Chamber implications and limits

- The current configured CM1 runtime can execute this official dry terrain
  case quickly and write complete native NetCDF output.
- The dedicated package path successfully preserves the full official
  namelist, provenance, inactive settings, runtime-file exclusions, and the
  one-process boundary.
- The native files preserve terrain, physical scalar heights, nominal full
  levels, and staggered velocity needed by a later corrected evaluator.
- Current flat-grid ingest and browser views remain unsuitable as acceptance
  evidence and were not used.
- Nothing here validates moisture, condensation, lenticular cloud formation,
  three-dimensional terrain, a user control, a Recipe, or a Mountain Wave
  Cloud World.

## Unresolved questions

1. PM must authorize a bounded code-only correction to the top-metadata
   interpretation. The correction should update the source mapping, evaluator,
   and synthetic test from expected emitted 18 km to expected emitted 20 km for
   `stretch_z=0`, while continuing to derive the transform top from active-grid
   evidence.
2. PM must decide whether the preserved one-run native files may be reevaluated
   after that correction without another CM1 process. No rerun appears
   technically necessary, but this issue does not authorize the correction.
3. The authoritative central-wave and boundary/damping judgment remains
   pending that corrected offline evaluation.

## Final disposition

The one identifiable defect is the committed evaluator's incorrect expectation
for emitted `ztop`. It is source-traceable, bounded, and plausibly correctable
without changing or rerunning the scientific case, but it prevents this PR from
satisfying the Gate B coordinate and structural acceptance criteria.

```text
bounded_dry_case_correction_required
```
