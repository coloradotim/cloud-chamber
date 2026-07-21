# CM1 r21.1 Dry Mountain-Wave Run Report

## Status and boundary

Gate B executed the exact official-duration dry mountain-wave package once.
CM1 completed normally and wrote the expected native NetCDF histories. The
first evaluator correctly stopped when its expectation for runtime `ztop`
conflicted with the output. PM then authorized one bounded evaluator correction
and offline reevaluation of that exact preserved run.

The corrected evaluator follows CM1 r21.1 source behavior: with `stretch_z=0`,
`src/param.F` normalizes runtime `ztop` to `dz*nk=20,000 m` before
`src/writeout_nc.F` writes it. The unchanged `ztop=18,000 m` assignment remains
only in the official-input audit. Physical-height reconstruction uses the final
nominal `zf` and fails closed unless it, runtime `ztop`, and configured `nz*dz`
all agree.

The preserved inputs were SHA-256 verified before and after evaluation. No
package was regenerated, no scientific setting changed, and no second CM1
process ran. The corrected evaluator passed all 11 original histories.

This work reproduces a source-bundled dry benchmark. It does not approve a
Cloud World, Recipe, Simulation, moist mountain case, cloud response, terrain
visualization, browser contract, or product direction.

## Decision question

The configured runtime faithfully executed the official case at practical
local cost. The corrected offline evaluation finds complete and finite native
output, internally consistent terrain coordinates, credible lower-boundary
tangency, and a coherent central terrain-forced gravity-wave response. Separate
west/east evidence indicates expected downstream signal at the east boundary
without material upstream, Rayleigh-layer, or top contamination of the central
solution. Gate B therefore advances the candidate to terrain-aware
visualization work within the limits stated below.

## Implementation and evidence identity

| Item | Value |
| --- | --- |
| Case and scenario ID | `cm1_r21_1_dry_mountain_wave_official_v0` |
| Run ID | `dry-mountain-wave-official-20260721T183530Z` |
| Package/run implementation commit | `9ff73ff244c393bee2a2e93a851ad1ba2dc16287` |
| Corrected evaluator commit | `cb504a223c98dbae5080783c7dbd9e4670f89c63` |
| Offline reevaluation time | `2026-07-21T19:17:19.861560Z` |
| Reevaluation mode | pinned SHA-256 before and after offline evaluation; no launch operation |
| Report provenance | This report is committed after the evaluator correction and does not change the recorded package/run implementation commit. |
| Run Recipe | `null` |
| Recipe ID | `null` |
| Cloud World ID | absent |
| Runtime package status before launch | packaged, preflight passed, no output-like files |
| Final runtime lifecycle | completed, exit code 0 |

Runtime files remain outside the repository. No machine-private path, NetCDF,
log, plot, screenshot, executable, CM1 source, or generated run directory is
committed.

### Preserved reevaluation inputs

The evaluator required every logical input below to match its pinned original
SHA-256 both before and after analysis. The evaluator evidence and summary JSON
are outputs of reevaluation and are intentionally not inputs to this identity
check.

| Preserved input | SHA-256 |
| --- | --- |
| `run_manifest.json` | `a72c2a9ba795b76cc779013817937bf34735835a74ad29c29efaf6df3ee1c13b` |
| `case_manifest.json` | `5a9d7ccc1dc9299c725eec4a3bd2c8e53163d918fe5d6ed7247527cd262c6356` |
| `namelist.input` | `bf202fb8e50abb903d50cb1cbeb86fb114efc88ff8049ab41ebf5bdd550b43be` |
| `input_sounding` | `75cf557b6258ab90943ee4368d3106a79ff63189e1d15aa0a6dcd2a051a033b3` |
| `runtime_file_checklist.json` | `0a96a368c90454d8555f80ccb8f746da656276247a80f4dcb505e978f3586d63` |
| `official_namelist_diff.json` | `7fda4d5ee51747e6b14f620ba087eb1b91f8a416cc8f635c5e2d9befefbeae92` |
| `official_namelist_diff.txt` | `f9beafaddd3f156303a0375416db9f1620c912c754a29b760c0bbf2aa3254bfe` |
| `storage_estimate.json` | `2d9593624eefd69607b5204967c50d1bebed536fdd63b22e0baa3a4a938a9784` |
| `execution_preflight.json` | `efc0dad92ba42e2cdaa4fb08905d08ca921a482b94356cd8ca9d50ff8d6a7286` |
| `logs/stdout.log` | `1018a9415063bbe9d5fcf87f1587f8086f614ddff9c1a1c44e74293cbb4e2fd0` |
| `logs/stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `cm1out_stats.nc` | `f26c12eee2cd9a23b2049374cd691394fae4b4793b56501bd97a633052148f58` |
| `cm1out_000001.nc` | `e894f6310f92827d8d0b8f15e11a36df7516d3f1113213a8bfca719c483faffe` |
| `cm1out_000002.nc` | `65d0e0eeb98c2e23309625a8931765e76d862c8e64d3d5bcfaf6abb86c16f73f` |
| `cm1out_000003.nc` | `457cc4b4da864a6cb41c2fe3199e4a2620025ee0994a4765b892661fc17ba3d2` |
| `cm1out_000004.nc` | `00a16c0c2d2390d8820d89502a506f967f5cd1ad3107084ab5436a24a517df9a` |
| `cm1out_000005.nc` | `0a3afb2fa258ad981e24fa4a4012d227fc4c7db34826d044e188856608d8398d` |
| `cm1out_000006.nc` | `dce854fd5cb90869edf5aa81f7ed50b56dd9ded8e704b9e815fd081860e01a3f` |
| `cm1out_000007.nc` | `e1dd0fb3f90f52a19e0ccda13194123b69511da6f76a529a5a48b30a63bff7df` |
| `cm1out_000008.nc` | `872bd649656084f82eca4409afbb2f4c509a424dcabbbd9a6c52266fd12a969e` |
| `cm1out_000009.nc` | `7a8553bfe14d751108db47a5696272c46842f1ec31db0f49ec17c05d2f563462` |
| `cm1out_000010.nc` | `a580260ddc8bcc1ab1c768bab510b6017513b686ed40b0a544220df3e83bddda` |
| `cm1out_000011.nc` | `b51ee4ca777bd825a5c4f52c92c6e39dd913071affb3c2694d36845cd687ded2` |

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

After commit `cb504a223c98dbae5080783c7dbd9e4670f89c63`, the preserved files were
reevaluated with:

```text
scripts/run_dry_mountain_wave_benchmark.py --evaluate-preserved
```

This mutually exclusive CLI mode loads only the exact completed run, verifies
the pinned identities before and after analysis, and returns before any local
run manager is constructed. No CM1 or MPI process was active before or after
the reevaluation.

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
| Transform-top source | final nominal `zf` |
| Final nominal `zf` | 20,000.0 m |
| Runtime NetCDF scalar `ztop` | 20,000.0 m |
| Configured `nz*dz` | `100 * 200 m = 20,000.0 m` |
| Active-source checks | all three sources agree in all 11 histories |
| Inactive official namelist assignment | `ztop=18,000.0 m`; audit only |

The corrected evaluator derives the terrain transform from the final nominal
`zf`, independently checks runtime `ztop` and configured `nz*dz`, and rejects
any disagreement. All three active sources resolve to 20 km in every preserved
history. This matches `src/param.F`, which assigns `ztop=dz*nk` for
`stretch_z<1`, and `src/writeout_nc.F`, which writes that normalized runtime
value. The 18 km input remains unchanged in the complete official namelist and
is correctly excluded from the transform.

## Base state and lower boundary

At time zero the upstream and domain-mean flow was exactly `u=10 m/s`, `v=0`.
The initial stability calculation over the west 20 percent used
`N^2=(g/theta_mid)*(delta theta/delta physical height)` and found a median
`0.00010000003 s^-2`, with range `0.00009999107` to `0.00010000844 s^-2`,
consistent with configured `N=0.01 s^-1`. Pressure decreased in all 9,900
tested vertical differences. All thermodynamic fields were finite.

At 2,160 s, upstream mean `u` was `10.0217 m/s`; domain-mean `u` had changed by
`+0.0312 m/s` and domain-mean `v` by `-0.0188 m/s`. The small background change,
together with finite hydrostatic fields and the coherent forced response, does
not indicate a material unexplained balance failure.

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
terrain-forced gravity-wave response. The corrected evaluator reproduced these
metrics from the hash-pinned native files.

## Boundary and damping assessment

The evaluator partitions the horizontal domain into separate west 20 percent,
central 60 percent, and east 20 percent zones. It evaluates each below 14 km,
then separately evaluates the full Rayleigh layer at or above 14 km and the top
2 km. This separation prevents expected downstream signal at the east open
boundary from being conflated with upstream reflection.

| Time (s) | Central `w` RMS below 14 km | West `w` RMS below 14 km | East `w` RMS below 14 km | Rayleigh-layer `w` RMS | Top-2-km `w` RMS |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.12383 | 0.00214 | 0.00232 | 0.00000 | 0.00000 |
| 432 | 0.31715 | 0.02149 | 0.06940 | 0.01077 | 0.00929 |
| 1080 | 0.42589 | 0.04992 | 0.25152 | 0.03526 | 0.01295 |
| 2160 | 0.54084 | 0.08917 | 0.51870 | 0.15562 | 0.05446 |

| Time (s) | Central theta-prime RMS below 14 km | West theta-prime RMS below 14 km | East theta-prime RMS below 14 km | Rayleigh-layer theta-prime RMS | Top-2-km theta-prime RMS |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| 432 | 0.12166 | 0.01992 | 0.04783 | 0.00268 | 0.00095 |
| 1080 | 0.20223 | 0.03212 | 0.11766 | 0.01205 | 0.00356 |
| 2160 | 0.31485 | 0.09413 | 0.37064 | 0.08792 | 0.02709 |

No official pointwise or RMS tolerance exists, so these values are interpreted
structurally rather than converted into a fabricated pass threshold. The west
response remains substantially below the central response through the final
time, which provides no sign of material upstream reflection. East-zone growth
tracks the observed downstream and vertical propagation of the coherent wave.
At the final time, Rayleigh-layer `w` RMS is about 29 percent of central
below-layer RMS and top-2-km `w` RMS is about 10 percent; the corresponding
theta-prime values remain similarly reduced aloft. Together with the persistent
central tilted bands, this evidence supports the bounded judgment that lateral,
Rayleigh-layer, and top-boundary behavior does not materially compromise the
central dry-wave response.

## Cloud Chamber implications and limits

- The current configured CM1 runtime can execute this official dry terrain
  case quickly and write complete native NetCDF output.
- The dedicated package path successfully preserves the full official
  namelist, provenance, inactive settings, runtime-file exclusions, and the
  one-process boundary.
- The native files preserve terrain, physical scalar heights, nominal full
  levels, and staggered velocity sufficient for corrected offline evaluation.
- Current flat-grid ingest and browser views remain unsuitable as acceptance
  evidence and were not used.
- Nothing here validates moisture, condensation, lenticular cloud formation,
  three-dimensional terrain, a user control, a Recipe, or a Mountain Wave
  Cloud World.

## Remaining limitations

- The source bundle supplies no pointwise reference field or formal numerical
  tolerance, so this is a structural reproduction judgment rather than a
  convergence or checksum benchmark.
- The case is dry and two-dimensional. It does not validate moisture,
  condensation, lenticular clouds, finite three-dimensional terrain, or a
  product experience.
- Current flat-grid browser payloads were not used and remain outside this
  gate's acceptance evidence.

## Final disposition

The corrected evaluator passes the exact preserved files, all active-top
sources agree, and the central dry-wave response remains coherent and
interpretable without material boundary or damping compromise. Runtime and
storage cost are practical. This disposition authorizes only the next bounded
terrain-aware visualization study; it does not approve a moist case or product
implementation.

```text
advance_to_terrain_visualization
```
