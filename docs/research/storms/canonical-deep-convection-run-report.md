# Canonical Deep-Convection Run Report

## 1. Status, decision question, and non-product boundary

**Status:** the one authorized Gate B CM1 process completed normally, but the
native-output evaluator stopped fail-closed on a coordinate-spacing comparison
defect before it could serialize the complete scientific evidence.

**Disposition:** `bounded_benchmark_correction_required`.

The decision question was whether the stock CM1 r21.1 quarter-circle benchmark
could be reproduced faithfully and evaluated as a trustworthy deep,
precipitating, rotating storm at practical local cost. Execution and much of
the mechanical output validation succeeded, but the evaluator did not complete.
This gate therefore does not make the storm-structure judgment.

This is a source-bundled research benchmark reproduction. It is not a Recipe,
a user-created variation, a Simulation installed in a Cloud World, a World or
UX decision, or approval of a general storm framework.

## 2. Controlling Gate A artifact and accepted identity

- Case ID: `cm1_r21_1_quarter_circle_supercell_official_v0`
- Scenario ID: `cm1_r21_1_quarter_circle_supercell_official_v0`
- Run ID: `quarter-circle-supercell-official-20260722T142521Z`
- Gate A artifact: `docs/research/storms/canonical-deep-convection-benchmark-mapping.md`
- Gate A artifact SHA-256: `a9a4b3829ed9d6c03238702613f20ce8ee0721fe7f999b158311df7253427965`
- Accepted identity: official CM1 r21.1 quarter-circle-hodograph supercell case
- Gate A disposition: `advance_to_canonical_benchmark_reproduction`

The run reproduced the official stock CM1 r21.1 case following Weisman and
Rotunno (2000). It was not intended to reproduce the paper's original numerical
implementation exactly.

## 3. Implementation and report commits

The package, preflight, process, and evaluator used implementation commit
`b465c35aa39a54bca46a869668da38caa45d2556`. The worktree was clean and matched
that commit immediately before launch.

This report was written after the process and evaluator stop in a separate
report commit. It does not alter the executed package, evaluator, or retained
output. The draft PR records the report commit separately from the implementation
commit.

## 4. CM1 provenance and controlling hashes

- CM1 release: `21.1`
- Official commit: `0f734f64efa89a684963a66d2ac32db67617912b`
- Source manifest: `fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e`
- Executable: `5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1`
- `README.namelist`: `7b95be56db51f5c9396c59dca252cf96b918a312cc70107451f91149a34ab3b5`
- Official supercell namelist: `3854f731efe6a6a9d56d6aa3db198434ccaba85bc5584b5e8ce1c5edfd3b56a4`
- Official supercell README: `3292aef3f7cdc49701015609626f55a3fd64162c88929d0992f9635dfb230200`
- `src/base.F`: `9c88a1021ddde22d02680786246c52bcffb040cbd72c3c4708f24fe24eec32ef`
- `src/init3d.F`: `9c45c0982ba194ea6ea74afd6a2516445cdd011fc90902091d089f4cb92dfd28`
- `src/param.F`: `cac64a6cb4363c6b88367b5cb9391f1bcf2130c63ffedef6e5973c03b190c349`
- `src/writeout.F`: `bef128e897d09dbc9ae86ec13bb156794e605a7c2da1596058de53c71d640dbd`
- `src/writeout_nc.F`: `5023244d7ce4f9a0dde7df9c780cf5c70b675097e8467c4fbfc8125e254f4710`

All pinned identities matched during package creation and again in the explicit
launch preflight. The executable was linked to NetCDF and NetCDF-Fortran.

## 5. Complete official-versus-generated namelist diff

All 343 official assignments were audited. There were 341 unchanged assignments
and exactly two approved output-transport differences:

```diff
- output_format   = 1
- output_filetype = 1
+ output_format   = 2
+ output_filetype = 2
```

Restoring those two values made the generated file byte-identical to the pinned
official namelist. `output_interp=0` remained unchanged. No scientific,
numerical, grid, timing, boundary, damping, translation, physics, trigger,
sounding, output-field, statistics, or inactive assignment changed.

Generated-input SHA-256 values were recorded and rechecked immediately before
launch:

| Input | SHA-256 |
|---|---|
| `namelist.input` | `addcd4234b14b84501f0e9ecfe0a6fbb6fad278122b77e84d6852a3bf8464a5c` |
| `official_namelist_diff.json` | `d31be4c2ff1087a0d87e19c81f9df049f03d22ebe9a23611728b2ac15204b757` |
| `official_namelist_diff.txt` | `57e34467e3573aa0058817911255de81e03259b26f4424a592a4e7415c723bed` |
| `runtime_file_checklist.json` | `a7314707c851104bd751be7b0ecdf9fffbda01c16e6b076304e10678932b3bfe` |
| `storage_estimate.json` | `d4cdb66b590e6c4234415f581190f8ea45f274d0443abb3da51ef244470b69a2` |

## 6. External scientific runtime-file inventory

The external scientific runtime-file inventory was empty. No `input_sounding`,
`LANDUSE.TBL`, `perts.dat`, terrain file, input grid, or microphysics lookup
table was created, staged, or consumed.

The sounding, quarter-circle wind profile, and deterministic warm bubble came
from the hash-pinned CM1 `isnd=5`, `iwnd=2`, and `iinit=1` analytic source paths.

## 7. Package, storage, and free-space preflight

The package-specific uncompressed numeric history floor was 572,140,800 bytes
for nine expected histories. It was derived from the complete requested field
inventory and dimensional classes, with no compression credit. The retained
planning band was 650-900 MB. The launch required at least 2 GiB free and had
25,423,867,904 bytes free at the final preflight.

Package-only validation and the separate explicit launch preflight both passed.
Every preflight check was true: clean implementation commit, Gate A and CM1
hashes, NetCDF linkage, exact two-setting diff, native `output_interp`, generated
input hashes, empty external-file inventory, exact expected times, storage floor,
no compression credit, free space, no active CM1 or MPI process, no prior
execution, and no output in the target package.

## 8. Run identity, command, process, and lifecycle

- Command: `<configured CM1 run directory>/cm1.exe`
- Execution: one direct, non-MPI local process
- Process ID: `92376`
- Start: `2026-07-22T14:26:04.871635Z`
- Finish: `2026-07-22T14:35:17.523418Z`
- Wall time: 552.652 seconds (9.211 minutes)
- CM1-reported compute time: 550.421875 seconds
- Exit code: `0`
- Lifecycle: packaged -> running -> completed
- Normal-termination marker: present

No smoke process, shortened process, retry, rerun, tuning process, MPI process,
or second CM1 process was started.

## 9. File and time inventory

The process emitted exactly nine numbered histories, one statistics NetCDF,
stdout, and stderr. No restart file was emitted.

| File | Native time (s) | Bytes |
|---|---:|---:|
| `cm1out_000001.nc` | 0 | 544,019 |
| `cm1out_000002.nc` | 900 | 14,496,437 |
| `cm1out_000003.nc` | 1,800 | 16,672,636 |
| `cm1out_000004.nc` | 2,700 | 19,307,201 |
| `cm1out_000005.nc` | 3,600 | 21,456,397 |
| `cm1out_000006.nc` | 4,500 | 24,082,000 |
| `cm1out_000007.nc` | 5,400 | 26,801,263 |
| `cm1out_000008.nc` | 6,300 | 29,309,646 |
| `cm1out_000009.nc` | 7,200 | 31,509,304 |
| `cm1out_stats.nc` | 0-7,200 at 60-second cadence | 1,052,565 |

Numbered histories retained 184,178,903 bytes; statistics retained 1,052,565
bytes; logs retained 779,923 bytes. All package and run files together retained
186,144,198 bytes. Compression was observed only after execution and was not
credited by preflight.

## 10. Native variable inventory and integrity

Before reaching the spacing check, the evaluator opened every numbered history
and successfully completed these checks in memory:

- every required coordinate and native field was present;
- native dimensions and units matched the declared contract;
- history times were exactly 0 through 7,200 seconds at 900-second cadence;
- every required field had zero non-finite values;
- scalar and staggered coordinate arrays were invariant across histories;
- coordinate sizes were exactly `xh=120`, `xf=121`, `yh=120`, `yf=121`,
  `zh=40`, and `zf=41`.

The emitted history inventory included `th`, `prs`, `tke`, horizontal and
vertical `km`/`kh`, `qv`, `qc`, `qr`, `qi`, `qs`, `qg`, `nci`, `ncs`, `ncr`,
`ncg`, `dbz`, native `u`/`v`/`w`, scalar `uinterp`/`vinterp`/`winterp`, all three
vorticity components, 2-5 km updraft helicity, accumulated rain, and the
requested native and translated swath products.

The evaluator had not yet serialized the per-field shape, precision, fill,
finite-count, and global-range table when it stopped. The statistics-specific
evaluator stage also had not started. A subsequent read-only inventory confirmed
that `cm1out_stats.nc` opens, contains 121 finite time coordinates from 0 to
7,200 seconds at 60-second cadence, and exposes 146 variables. Those facts do
not substitute for the incomplete required evaluator output.

## 11. Grid, active top, coordinates, and moving domain

The emitted scalar grid is 120 x 120 x 40 with corresponding staggered
dimensions. Coordinates are float32 values in kilometers. A read-only inventory
confirmed `zf` from 0 to 20 km, so the active unstretched model top is 20 km;
the inactive `ztop=18 km` assignment did not control the emitted grid. Terrain
was flat.

The intended uniform spacing is 1 km x 1 km x 0.5 km. After normalization to
meters, float32 representation produced these differences:

| Coordinates | Minimum delta (m) | Maximum delta (m) |
|---|---:|---:|
| `xh`, `xf`, `yh`, `yf` | 999.9980926513672 | 1000.0038146972656 |
| `zh`, `zf` | 499.9990463256836 | 500.0009536743164 |

The evaluator incorrectly required the normalized delta sets to equal exactly
`[1000.0]` and `[500.0]`. It therefore raised `Emitted coordinate spacing is not
exact` even though the observed millimeter-scale spread is consistent with the
precision of native float32 kilometer coordinates.

Native `u`, `v`, and `w` remain staggered on `xf`, `yf`, and `zf`; `uinterp`,
`vinterp`, and `winterp` are scalar-grid products. Native winds are in the
translating model frame. Ground-relative horizontal winds require adding
`(12.5, 3.0) m/s`.

## 12. Analytic thermodynamic, hodograph, frame, and trigger verification

Package provenance and source hashes establish use of the pinned analytic
Weisman-Klemp thermodynamic profile, quarter-circle wind profile, moving-domain
subtraction, and deterministic source-defined warm bubble. The generated
namelist preserved `isnd=5`, `iwnd=2`, `iinit=1`, `irandp=0`, `ibalance=0`,
`imove=1`, `umove=12.5`, and `vmove=3.0`.

The evaluator computed initial-state and trigger evidence in memory before the
spacing check, but did not serialize it. This report therefore does not promote
an emitted CAPE/CIN value, sampled trigger amplitude, detailed thermodynamic
profile, or emitted surface-to-6-km shear measurement. The source-defined bubble
identity remains the Gate A identity: domain center, 1,400 m AGL, 10,000 m
horizontal radius, 1,400 m vertical radius, 1 K maximum potential-temperature
perturbation, no random perturbation, no pressure balancing, and
`maintain_rh=false`.

## 13. Deep cloud, hydrometeors, precipitation, reflectivity, and motion

The evaluator computed frame evidence before the spacing check but did not
serialize the report-ready time series. Consequently this gate does not report
or judge vertical-motion extrema, cloud onset and extent, individual `qc`, `qr`,
`qi`, `qs`, and hail-treated `qg` evolution, number concentrations, reflectivity,
surface precipitation, hydrometeor tops, or swaths.

No single value was extracted after the stop to stand in for the required
complete evolution assessment.

## 14. Vorticity, updraft helicity, swaths, and organized rotation

The required joint rotation assessment was not completed. No judgment is made
from one vertical-vorticity maximum, updraft-helicity value, reflectivity value,
or updraft maximum. Sustained organized rotation remains unresolved pending a
bounded evaluator correction and authorized evaluation of the already retained
output.

## 15. Structural checkpoints near 45, 75/90, and 120 minutes

The required histories exist at 45, 75, 90, and 120 minutes, but the evaluator
did not serialize the structural checkpoint evidence. This report therefore
makes no claim about storm morphology or continuity at those times.

The 15-minute history cadence does not support claims of exact 40- or 80-minute
figure reproduction.

## 16. Lateral boundaries, translation, and upper damping

The source-locked configuration preserved open lateral boundaries, the
`(12.5, 3.0) m/s` moving frame, and Rayleigh damping beginning at 15 km. The
evaluator did not complete the required spatial checks for storm distance from
the lateral boundaries or vertical motion and condensate within the 15-20 km
damping layer. Boundary and damping contamination therefore remain unresolved.

## 17. Runtime integrity, storage, warnings, and cost

The one process reached 7,200 seconds, exited 0, emitted the normal-termination
marker, and retained all expected histories and statistics. Required history
fields were finite through the evaluator stage that completed. Wall time was
552.652 seconds and total retained package/run size was 186,144,198 bytes. Peak
memory was not captured by the launcher.

Stderr contained only:

```text
Note: The following floating-point exceptions are signalling: IEEE_UNDERFLOW_FLAG
```

No invalid-operation, divide-by-zero, overflow, fatal-error, or abnormal-
termination evidence was present.

## 18. Qualitative lineage and stock-versus-paper differences

The official case README links the benchmark to Weisman and Rotunno (2000), and
the analytic sounding lineage is Weisman and Klemp (1982). This run reproduced
the stock CM1 r21.1 configuration, not the paper's exact numerical experiment.
The stock case's current microphysics, grid, model top, upper-boundary treatment,
wind variation, and saved times remain distinct from the original paper.

## 19. Cloud Chamber implications and limits

The run establishes that the configured local CM1 r21.1 executable can package
and complete this exact official benchmark at practical local runtime and
storage cost while emitting the expected native artifact classes. It does not
yet establish that the result is a trustworthy deep rotating storm suitable for
examination, because the required scientific evaluator did not finish.

This result does not select or define a Cloud World, Recipe, reference
Simulation, trigger, sounding, Lens, variation surface, or UX. It does not
authorize Squall Line work or a generic storm framework.

## 20. Unresolved questions and bounded correction

One bounded implementation correction is required: coordinate-spacing
validation must compare normalized native coordinates using a tolerance
appropriate to their declared float32 kilometer precision while continuing to
fail on scientifically material nonuniformity or wrong spacing.

After that correction, the evaluator must run against the already retained
output and serialize all required native, statistics, initial-state, evolution,
rotation, boundary, damping, runtime, and cost evidence. Whether that evaluation
may proceed, and whether any new CM1 process is authorized, require explicit PM
direction. This report does not authorize a rerun.

## 21. Final disposition

`bounded_benchmark_correction_required`
