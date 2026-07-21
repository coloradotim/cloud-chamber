# Moist Orographic-Cloud Run Report

Status: one source-locked CM1 process completed and evaluated.

Review correction status: the exact preserved output was reevaluated offline with the
hash-pinned v2 evaluator. No CM1 process or run manager was started.

Final disposition: `advance_as_candidate_world_evidence`

## Decision and boundary

The decision question was whether pinned CM1 r21.1 can begin from a source-backed,
unsaturated two-dimensional atmosphere and produce coherent cloud condensate through
terrain-forced gravity-wave ascent, with physically legible descent and evaporation.

It can. The run produced a compact windward cloud by 200 s, a separate lee-wave cloud
by 1,200 s, and a persistent, terrain-relative lee cloud through the 4,000 s endpoint.
The run remained nonprecipitating, numerically stable, finite, clear at initialization
and in the upstream/periodic-edge sectors, and practical on the local machine.

This evidence does not define or approve a Cloud World, Recipe, Control, Lens,
Comparison, generic terrain feature, or product surface. It supports consideration of
a later bounded candidate product slice only.

## Source lock and references

The pre-execution source lock is:

```text
docs/research/mountain-waves/moist-reference-case-selection.md
SHA-256: 939c4b7c6b067c125402383e7ed966b6e09eed2f5e0c0762ca6331a6f381b20b
```

It selected the Toy (2011) 11 January 1972 Boulder moist mountain-wave experiment.
The exact observed profile is the NOAA IGRA record headed
`#USM00072476 1972 01 11 12`, extracted-record SHA-256
`33953228bc6bcdf7d65c5cf800b5f8bed9a71aedda910edb4d32a28bef37e652`.

Primary references:

- Michael D. Toy, 2011, [Incorporating Condensational Heating into a Nonhydrostatic Atmospheric Model Based on a Hybrid Isentropic-Sigma Vertical Coordinate](https://doi.org/10.1175/MWR-D-10-05015.1).
- Michael D. Toy and David A. Randall, 2009, [Design of a Nonhydrostatic Atmospheric Model Based on a Generalized Vertical Coordinate](https://doi.org/10.1175/2009MWR2834.1).
- J. D. Doyle et al., 2000, [An Intercomparison of Model-Predicted Wave Breaking for the 11 January 1972 Boulder Windstorm](https://doi.org/10.1175/1520-0493(2000)128%3C0901:AIOMPW%3E2.0.CO;2).
- Dale R. Durran and Joseph B. Klemp, 1983, [A Compressible Model for the Simulation of Moist Mountain Waves](https://doi.org/10.1175/1520-0493(1983)111%3C2341:ACMFTS%3E2.0.CO;2).
- NOAA NCEI, [IGRA v2.2 station USM00072476 period-of-record data](https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/access/data-por/USM00072476-data.txt.zip) and [sounding format](https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/doc/igra2-data-format.txt).

The complete source-to-CM1 difference table remains in the hash-pinned selection
artifact. The material differences are the source-supported 25 km sensitivity top,
CM1 Gal-Chen coordinate, CM1 Smagorinsky closure, CM1 water-only reversible physics,
direct deterministic processing of the archived IGRA observation, a half-grid terrain
centering offset, the pinned CM1 2 s integration step, and 200 s evidence cadence.

## Package and process identity

```text
case_id: cm1_r21_1_toy2011_boulder_moist_wave_4000s_v1
run_id: moist-mountain-wave-toy-1972-20260721T215226Z
implementation commit: ebdbb528c92c57d3d4a19080b4bddc4820b0bc6a
offline evaluator commit: 133e4840d9bba9cf0e5199eabc8ae36146ff21d7
CM1 release: 21.1
CM1 tag commit: 0f734f64efa89a684963a66d2ac32db67617912b
CM1 executable SHA-256: 5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1
CM1 source-manifest SHA-256: fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e
```

The executable exposed both NetCDF C and Fortran linkage. Critical source and CM1
documentation hashes matched the preserved Gate B provenance.

Runtime input identities:

| Input | SHA-256 | Disposition |
| --- | --- | --- |
| `namelist.input` | `d94f54d5e60627daf9020aa9eceaecd4f3b35fa1c81590186c72c7ccf99a10be` | Consumed configuration |
| `input_sounding` | `cb43243d04e328e9dd1a08ff52139f5a6096dcbe89f7b0d0e4aeb536f6a33b22` | Consumed, 38 exact rows |
| `perts.dat` | `10d4fd60cac78acc2a19fe4a84b5d3c12c7e8a2ab58789faecebc40bf23e1028` | Consumed, one 880-byte float32 record |

The runtime checklist contained exactly `input_sounding` and `perts.dat`. No land,
radiation, aerosol, microphysics lookup, or external-grid file was consumed.
`run_recipe`, `recipe_id`, and `cloud_world_id` were null.

Exactly one full 4,000 s CM1 process ran. No shortened smoke process, tuning process,
retry, alternate executable, LAN worker, or second process ran.

## Corrected offline reevaluation

The PM/scientific review authorized one evaluator-only correction against the exact
preserved run. The v2 path verifies the source lock and 30 pinned artifacts before and
after reading output: both manifests, generated namelist, sounding, terrain record,
execution preflight, stdout/stderr, stats NetCDF, and all 21 numbered histories. The
before/after hash maps are identical. The path is pinned to the run ID above, rejects
any other run, and does not import, construct, or invoke a run manager.

```text
evidence version: moist_mountain_wave_gate_d_e_v2
offline evaluator commit: 133e4840d9bba9cf0e5199eabc8ae36146ff21d7
corrected evidence SHA-256: 4d68ab004ad62ac7bb4d1668743caa67f64ed341f1e025bdbc427fe668af08ad
original implementation commit retained: ebdbb528c92c57d3d4a19080b4bddc4820b0bc6a
preserved artifact count: 30
preserved artifacts unchanged: true
run manager constructed or invoked: false
```

## Generated configuration and audit

The generated namelist retained all 342 assignments from the pinned official
mountain-wave namelist and changed 28 source-locked or explicit output mappings:

```text
nx 100 -> 220                 nz 100 -> 125
dx 200 -> 1000 m              dy 200 -> 1000 m
timax 2160 -> 4000 s          tapfrq 216 -> 200 s
cm1setup 0 -> 1               apmasscon 1 -> 0
imoist 0 -> 1                 sgsmodel 1 -> 2
tconfig 1 -> 2                irdamp 1 -> 0
ptype 5 -> 6                  icor 1 -> 0
lspgrad 1 -> 0                wbc/ebc 2 -> 1
isnd 9 -> 7                   iwnd 6 -> 0
itern 1 -> 4                  fcor 0.00010 -> 0
v_t 7 -> 0 m/s                ztop 18000 -> 25000 m
output_format 1 -> 2          output_filetype 1 -> 2
output_interp 1 -> 0          output_rain 1 -> 0
output_dbz 1 -> 0
```

Locked values that already matched the official file included `ny=1`, `dz=200 m`,
`dtl=2 s`, `eqtset=2`, `efall=0`, periodic singleton-y boundaries, free-slip rigid
bottom/top, no surface flux/PBL, no random or thermal initialization, and native plus
scalar-interpolated wind output.

The horizontal domain is 220 km. The active top is 25 km with 125 uniform nominal
levels. Terrain is
`2000 / (1 + ((x - 500 m) / 10000 m)^2)` meters. Binary readback recovered the exact
2,000 m crest at `x=500 m`, with maximum float32 roundtrip error below 0.0005 m.

The 850 hPa sounding header and 37 profile rows were finite and strictly increasing in
height; the last row was 25,846 m above the model reference, above the active top. The
maximum source RH was 95%, and all rows without reported RH followed the locked CM1
0.01% RH mapping. Initial condensate categories were absent by construction.

## Predeclared criteria and result

The source lock required all of the following. The result is recorded beside each
criterion rather than replacing it with a new post-run threshold.

1. **Normal completion, 21 exact finite histories:** passed. Times were 0 through
   4,000 s at exact 200 s intervals; every required field was finite at every time.
2. **Terrain, physical-height, and active-top integrity:** passed. Terrain error was
   `9.54e-5 m`, physical-height transform error was `0.0041 m`, minimum scalar spacing
   was `183.996 m`, and final nominal `zf` and runtime `ztop` were both `25,000.002 m`
   at every history, agreeing with configured `125 x 200 m = 25,000 m`.
3. **Initial and upstream clear air:** passed. Initial maximum `ql` was zero. The
   maximum `ql` in the `-100..-60 km`, below-12-km upstream sector was zero at every
   history.
4. **Interior formation with ascent and saturation:** passed. First condensate above
   `1e-6 kg/kg` appeared at 200 s in one 15-cell component at `x=-7.5..-0.5 km` and
   `z=3.52..3.87 km`; 12 of those same first-frame interior cells were simultaneously
   ascending and at least 99% RH. The first-frame peak itself was at `x=-2.5 km`,
   `z=3.60 km`, with `w=0.371 m/s` and RH `100.67%`.
5. **Coherence, persistence, and material peak:** passed. The cloud was coherent for
   every history from 200 through 4,000 s. Peak `ql` reached `6.4445e-4 kg/kg`
   (`0.6445 g/kg`), above the predeclared `0.2 g/kg` material check.
6. **Descent and evaporation:** passed. The corrected method selects clear cells one
   scalar-grid cell immediately east of cloud, with `w<0`, RH below one, and `ql` below
   the locked cloud floor. At 1,200 s it retains 18 cells in 11 connected groups across
   `x=-5.5..18.5 km`, `z=2.62..4.73 km`; median `w` was `-2.26 m/s`, median RH was
   96.34%, and `ql=0`. At 4,000 s it retains 30 cells in 15 groups across
   `x=17.5..27.5 km`, `z=2.38..8.33 km`; median `w=-4.18 m/s`, median RH 93.60%, and
   `ql=0`. Cumulative CM1 condensation was `6.9582e7` mass units and evaporation was
   `5.9357e7`, so active evaporation was substantial rather than inferred only from a
   color boundary.
7. **Terrain/wave locking:** passed. The early windward component remained tied to the
   mountain. By 1,600 s the dominant component was the lee cloud at `x=14.5..19.5 km`;
   its centroid stayed between 17.2 and 19.1 km through 4,000 s while it grew. It did
   not translate from a boundary.
8. **Interpretable moist wave without contaminating edge/top/startup effects:** passed.
   Alternating ascent/descent bands remained legible. Edge-sector maximum `ql` was
   `7.28e-13 kg/kg`, below even the numerical clear floor. Top-layer maximum `ql` was
   zero; maximum top-layer `|w|` was `0.569 m/s`, 4.3% of the domain maximum.
9. **Honest native geometry and practical local cost:** passed. The run completed in
   65.07 s, used 44 MB total, and emitted 30.34 MB of numbered model NetCDF.
10. **Runtime-only visual review:** passed. Equal-scale and expanded-height views both
    show the terrain, windward streamer, separate lee cloud, and alternating wave
    ascent/descent without inventing a three-dimensional volume.

## Lifecycle and runtime integrity

```text
started:  2026-07-21T21:52:59.086107Z
finished: 2026-07-21T21:54:04.155245Z
exit code: 0
wall clock: 65.069138 s
normal termination marker: present
maximum CFL: 0.145988
maximum w: 13.121550 m/s
minimum w: -6.565818 m/s
maximum RH: 1.000004
precipitation rate: 0 at every stats time
rain-process accumulator: 0
```

The 2,001-record stats NetCDF was finite. Total mass changed by `-3.006e-5` relative;
total moisture changed by `-3.104e-5` relative. Vapor decreased as liquid increased,
consistent with the selected reversible moisture treatment.

Stderr contained only CM1's `IEEE_UNDERFLOW_FLAG` notice. There was no invalid,
divide-by-zero, or overflow flag; all required histories and all stats variables were
finite, maximum CFL remained 0.146, and CM1 terminated normally. The underflow is
retained as a runtime caveat rather than treated as a fatal integrity failure.

Runtime evidence identities:

| Artifact | SHA-256 |
| --- | --- |
| Final run manifest | `026a3887f4120fa3e2e6663d8a486a28f83338ff5b3be09639cd245fd8ba1845` |
| Case manifest | `208d05ba72149a53f423ef13fa97cab4e298f374f20f30e6ea9c12fc6e016a78` |
| Repeated execution preflight | `917f2f17c33f602760801c4447e014ef09e0f6031a2218b9dba4a49a2e0b9185` |
| Stdout | `42a120685c18d29d855cdea5039f54a3530157f2d36497cd41318f1af97fc0cb` |
| Stderr | `6e8658cbd2bf71044b960ff59b4371a98438c32a7d4cb54ab562294b8cc4f05d` |
| Stats NetCDF | `46cf824b20ab0c4b00806cd9ec2b0e52833e35d1913e2fa4d9205e12a523ff7a` |
| Original v1 evaluator evidence | `354b99419cdae3d27374080807f92c2c078b7ec87b1d17cae86b09e017d013d0` |
| Corrected v2 offline evaluator evidence | `4d68ab004ad62ac7bb4d1668743caa67f64ed341f1e025bdbc427fe668af08ad` |

## Native output inventory

Each numbered file contains one time. Coordinates are `xh(220)`, `xf(221)`, `yh(1)`,
`yf(2)`, `zh(125)`, and `zf(126)`, all reported in kilometers; time is in seconds.

| Group | Native shape | Units / staggering |
| --- | --- | --- |
| `zs` | `(1,1,220)` | m, scalar horizontal grid |
| `zhval`, `th`, `prs`, `qv`, `ql` | `(1,125,1,220)` | physical m, K, Pa, kg/kg, kg/kg; scalar grid |
| `uinterp`, `vinterp`, `winterp` | `(1,125,1,220)` | m/s, scalar grid |
| `u` | `(1,125,1,221)` | m/s, x-face staggered |
| `v` | `(1,125,2,220)` | m/s, y-face staggered |
| `w` | `(1,126,1,220)` | m/s, full-level staggered |
| `kmh`, `kmv`, `khh`, `khv` | `(1,126,1,220)` | m2/s, full-level SGS diagnostics |

Surface wind/stress/pressure variables and scalar `ztop` were also emitted. No rain,
ice, snow, graupel, or reflectivity field was present, as required by `ptype=6`.

| File | Time (s) | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `cm1out_000001.nc` | 0 | 877,496 | `a62959ceaae1c108ea0d2eb3805809615faf233a0e35096eeeceac18329ae9a5` |
| `cm1out_000002.nc` | 200 | 1,406,783 | `79a4d4a95534b29dbd98286d1086dbf2a168af4484862b994e30e09af3b76c0a` |
| `cm1out_000003.nc` | 400 | 1,460,096 | `bbe5d4d40bcf59acb4c87d44a2aa73060d5dca9eb72572ccc58ec87a6b33ecf3` |
| `cm1out_000004.nc` | 600 | 1,464,637 | `b5bcad79828812d1f81b1d1972622d492e7967e97dc35a9c6b505301033e16c1` |
| `cm1out_000005.nc` | 800 | 1,455,818 | `5dd3efac88159d955e6e4e2880ca3faf06c7024c3ffc9de4c6f45ba43e5493df` |
| `cm1out_000006.nc` | 1000 | 1,466,280 | `cf5aeb035f784fc8f252f08a92b6bb6a78740431b6060a20bdbc30a3d6540699` |
| `cm1out_000007.nc` | 1200 | 1,471,806 | `48091a925b4e9a9219c6f1e07902ea1a09a8f427113b5f25589d0a2ef322019e` |
| `cm1out_000008.nc` | 1400 | 1,467,851 | `183ceae29cd44cc767a8987db4f218c9479d283d8f7330547d65992e02094752` |
| `cm1out_000009.nc` | 1600 | 1,466,002 | `294fe39221cfe6af1d48ea65093bc0698d903bc848535d349371f898cf66b6d6` |
| `cm1out_000010.nc` | 1800 | 1,475,479 | `316fb4c2c0bb2c93ef588eeae50516b78c2bca6087bc85cf62da7596c9a526b6` |
| `cm1out_000011.nc` | 2000 | 1,474,791 | `41a9a6c8fdd7a81e3ea1074fb2cb717a312a46602e814e58c57f5eb1b81fd2ce` |
| `cm1out_000012.nc` | 2200 | 1,476,258 | `e7ce11ae105ea035d9dc0f408647507a3ed51a7165eb75fae2fc38e3549d1572` |
| `cm1out_000013.nc` | 2400 | 1,479,651 | `93d0b34b075a194f5c621c7f8d5b0ca8de82f51170fad30456962fdacaf298e7` |
| `cm1out_000014.nc` | 2600 | 1,482,511 | `9410bcb03d2ff9f251356f01f9d19391eaa6d254f1bf6497f27901e461ff75e8` |
| `cm1out_000015.nc` | 2800 | 1,484,687 | `49956dcf04d32f2569e8d585e4d76af23e4765012c8111a63b1d426b93fe0d73` |
| `cm1out_000016.nc` | 3000 | 1,484,529 | `724a5acf714b2fa1a55e497a9a3c5343dea4608863db7a1702af5187d7b7063d` |
| `cm1out_000017.nc` | 3200 | 1,485,877 | `9bc9e235bacfc73424651bf547c68c56cf24d3422741f5d732660ff647db4290` |
| `cm1out_000018.nc` | 3400 | 1,486,332 | `82d3a544ff5026ad74ec066c90adcddf17251ef161bccb0053684b57c3f20375` |
| `cm1out_000019.nc` | 3600 | 1,490,416 | `9caac2cd58d33852934579dc2973c183113383f23665f2ed8b17795759e67613` |
| `cm1out_000020.nc` | 3800 | 1,490,540 | `c6920f6d47eb6b0fb8a2cfd7ca8ac901a49e92802d40f9f1f161937eadb76023` |
| `cm1out_000021.nc` | 4000 | 1,492,797 | `0f8f31f2bf91ca80d430b326025cc734f4295e1ad6c687d2bae7f02ae0fe2b43` |

## Cloud evolution and moist feedback

| Time (s) | Max ql (g/kg) | Cloud cells | Largest component | Dominant centroid x / z (km) |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | none |
| 200 | 0.0305 | 15 | 15 | -3.77 / 3.69 |
| 600 | 0.0809 | 52 | 41 | -6.18 / 3.76 |
| 1,200 | 0.1780 | 127 | 88 | -7.41 / 3.54 |
| 1,600 | 0.2793 | 199 | 105 | 16.81 / 4.93 |
| 2,400 | 0.4560 | 286 | 197 | 18.01 / 5.40 |
| 3,200 | 0.5885 | 341 | 265 | 18.82 / 5.55 |
| 4,000 | 0.6445 | 386 | 336 | 19.07 / 5.56 |

The switch in dominant centroid at 1,600 s is not a cloud translating across the
periodic domain. The native frames show the earlier windward layer and the separately
formed lee-wave component; the latter becomes the largest connected component.

Cloud-weighted mean `w` remained positive at every cloudy history. At 4,000 s it was
`0.389 m/s`; 189 cloud cells were both ascending and at least 99% RH. The peak-`ql`
cell itself can lie near the overturning/descending side of the mature cloud, but the
weighted field and boundary profiles preserve the expected formation in ascent and
evaporation in descent. Latent heating strengthens the wave without obscuring the
alternating vertical-motion pattern.

## Boundary, top, and startup assessment

- Every history reports final nominal `zf=25,000.002 m` and runtime
  `ztop=25,000.002 m`; both agree with configured `nz x dz=25,000 m` and the source
  lock. The evaluator fails closed on disagreement at any time.
- Actual staggered `u`, `v`, and bottom `w` retain lower-boundary tangency metrics at
  every history. The initial residual RMS was `0.0284 m/s` with predicted/observed
  correlation `0.99984`; at 4,000 s RMS was `0.0558 m/s` with correlation `0.99985`.
  The maximum absolute residual across all histories was `0.3323 m/s`.
- The native initial upstream profile in the locked `-100..-60 km`, below-12-km
  sector contains 2,400 cells. Initial `u` ranged from `-3.63` to `35.60 m/s`, with
  median `25.89 m/s`; `v=0`, and median `w=0`. All 59 calculated layer values of
  `N^2` were positive, with median `1.056e-4 s^-2` and range
  `9.64e-6..1.759e-3 s^-2`. Per-time upstream wind summaries are retained through
  4,000 s.
- The periodic west/east seam remained clear. No cloud originated in the outer 10 km
  edge sectors or the far-upstream source sector.
- The first native frame at 0 s had `ql=0` everywhere and maximum RH 94.93%. Cloud
  first appeared at 200 s over the windward slope, so it was not initialized or
  broadly produced by sounding adjustment.
- There was no Rayleigh absorber, matching the selected 25 km source sensitivity
  case. Wave motion reached the upper domain, but the top 2 km remained cloud-free and
  its maximum `|w|` was small relative to the interior maximum. Top behavior therefore
  does not compromise the below-9-km cloud interpretation over 4,000 s.
- Total mass and moisture drift were about 0.003%, with no precipitation sink. This is
  small relative to the condensate signal and does not change the disposition.

## Runtime-only visual review

Two runtime-only browser renders were inspected directly from the native NetCDF:

1. an expanded-height four-frame view for detailed wave/cloud inspection; and
2. an equal physical x/z scale view cropped to `x=-30..50 km`, `z=0..12 km`.

Both views used red for ascent, blue for descent, and outlined cells for
`ql >= 0.001 g/kg`. The equal-scale view is the more honest geometry check: it shows a
broad mountain, a shallow windward streamer, and a substantial but not artificially
stretched lee-wave cloud. The 4,000 s dominant component spans approximately
`x=13.5..26.5 km` and `z=2.42..8.45 km`. Browser inspection at desktop size found all
four canvases correctly proportioned and no console errors. These temporary diagnostic
renders were generated outside the application visualization machinery by reading the
native NetCDF directly; they are not output from the merged Gate C route or any Cloud
Chamber product surface. The HTML, JSON, and PNG review artifacts remain runtime-only
and are not committed.

## Limitations and unresolved questions

- This is one two-dimensional historical windstorm case, not a general validation of
  moist orographic cloud behavior.
- CM1's Smagorinsky closure and Gal-Chen coordinate are close mappings, not pointwise
  reproductions of Toy's model.
- The source-supported 25 km top removes the unspecified upper stretching but retains
  more reflection risk than the 48 km main configuration.
- The profile is deterministically reconstructed from the archived observation rather
  than the authors' private processed sounding, so quantitative amplitudes should not
  be treated as a paper reproduction.
- The cloud grows through the 4,000 s checkpoint rather than reaching a steady mature
  state. A future product-slice decision would need to choose what portion of this
  evolution is experientially useful; this report does not make that decision.
- The observed shallow low-level wind reversal is retained. Cloud-bearing flow from
  roughly 2.5 to 8.5 km is left-to-right in the runtime review frame at about
  16-36 m/s.

## Final disposition

`advance_as_candidate_world_evidence`

The source lock is defensible, the only authorized process passed integrity checks,
and the native evidence shows clear-air formation, coherent persistence, terrain/wave
locking, active descent/evaporation, and a visually legible gravity-wave cloud system.
This disposition records feasibility evidence only. It does not approve the candidate
World or authorize another CM1 process.
