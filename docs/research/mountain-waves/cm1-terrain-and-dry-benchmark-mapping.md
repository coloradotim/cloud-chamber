# CM1 Terrain And Dry Mountain-Wave Benchmark Mapping

**Status:** Research evidence for Gate A of issue #400; not product authority

## 1. Decision question and scope

This artifact answers one bounded question:

> Does the exact CM1 r21.1 configuration used by Cloud Chamber provide a sufficiently understood and reproducible dry terrain-wave foundation to justify a later local reproduction run?

The answer is **yes, subject to the bounded packaging and output changes specified in Section 9**. The official case is sufficiently explicit to reproduce its dry dynamics. Its terrain, coordinate transform, base state, wind, boundaries, numerics, and output intent can be traced to the r21.1 source. Current Cloud Chamber code cannot emit the case through its generic package path or represent native terrain-following output honestly in its existing browser payloads; that does not prevent a later run-and-evaluate gate that works directly from native CM1 output.

This is Gate A research evidence only:

- No CM1 process ran.
- No generated package, `perts.dat`, model output, or other runtime artifact was created.
- No Cloud World, Recipe, Control, Lens, Comparison, scenario, route, moist profile, or cloud-producing case is approved.
- No terrain implementation or generic terrain architecture is proposed.
- A successful dry reproduction would establish only a trustworthy terrain-wave execution foundation. It would not establish a future Mountain Wave Clouds experience or validate moist cloud physics.

The four evidence classes are kept separate throughout:

1. official CM1 r21.1 behavior;
2. repository-recorded provenance for Tim's configured runtime;
3. current Cloud Chamber implementation behavior;
4. later work that has not been implemented or run.

## 2. Configured CM1 provenance

Cloud Chamber's prior BOMEX evidence records the configured runtime as CM1 release **21.1**, aligned to official tag `21.1` at commit [`0f734f64efa89a684963a66d2ac32db67617912b`](https://github.com/NCAR/CM1/tree/0f734f64efa89a684963a66d2ac32db67617912b). That official commit is the source authority used for the mechanics in this artifact.

Repository-recorded configured-runtime provenance is:

| Item | Recorded identity |
| --- | --- |
| CM1 release | `21.1` |
| Official source commit | `0f734f64efa89a684963a66d2ac32db67617912b` |
| Configured source-manifest SHA-256 | `fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e` |
| Configured executable SHA-256 | `5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1` |
| Configured `README.namelist` SHA-256 | `7b95be56db51f5c9396c59dca252cf96b918a312cc70107451f91149a34ab3b5` |
| Configured `src/base.F` SHA-256 | `9c88a1021ddde22d02680786246c52bcffb040cbd72c3c4708f24fe24eec32ef` |
| Cloud Chamber commit used for the prior clean BOMEX package regeneration | `84126c75c2db31deb8ba0a3e3bb447a1f94dad27` |

The prior mapping reports that all 91 configured `src/*.F` files byte-matched the official tag. See [the BOMEX source mapping](../bomex/bomex-setup-and-cm1-mapping.md) and [run report](../bomex/bomex-run-report.md). Those records attest to an earlier verification of the configured local source and executable. This desk-research gate did **not** inspect, copy, or rehash Tim's local CM1 tree or executable.

No configured-runtime hash for `README.terrain` was previously recorded. This artifact therefore uses the tag-pinned official file as documentary evidence and does not imply a new local attestation. The repository contains neither CM1 source nor the executable; official GitHub content and configured-runtime provenance are distinct evidence.

## 3. CM1 r21.1 terrain representation

### Activation, ownership, and grid location

`terrain_flag=.true.` activates terrain-aware model paths. `terrain_flag=.false.` is the documented flat-lower-boundary mode. The terrain itself is the two-dimensional real array `zs(ib:ie,jb:je)` in [`src/init_terrain.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/init_terrain.F#L28-L38). Its units are meters and its horizontal location is the scalar grid, the same placement as potential temperature, water vapor, and pressure. CM1 owns and distributes this array at initialization; it is fixed in time.

`itern` selects one of the r21.1 source branches, but it does not expose the terrain dimensions as namelist parameters. For `itern=1`, `2`, and `3`, the equations and constants are compiled into `src/init_terrain.F`. For `itern=4`, the terrain is supplied by a binary file.

### Built-in options

Let `xh(i)` and `yh(j)` be scalar-point coordinates in meters.

| `itern` | Exact r21.1 construction | Parameter ownership and lineage |
| --- | --- | --- |
| `0` | No branch changes `zs`; documented as `zs=0` / no terrain. | Namelist selects absence of terrain. |
| `1` | `zs(i,j) = 400 / (1 + ((xh(i) - xc) / 1000)^2)`, where `xc = 0 + 0.5*dx`. The ridge is invariant in `y`. | Height 400 m, half-width 1,000 m, and location are hard-coded. Source identifies Durran and Klemp (1983). |
| `2` | With `xval = dx*(i - ni/2)`, `zs(i,j) = 250 exp(-(xval/5000)^2) cos^2(pi*xval/4000)`. The ridge is invariant in `y`. | All dimensions are hard-coded. Source identifies the Schaer case and Klemp et al. (2003). |
| `3` | With `r = sqrt((xh(i)-0.25*maxx)^2 + (yh(j)-0.25*maxy)^2)`, `zs(i,j) = 500 (1 + (r/20000)^2)^(-3/2)`. | Height 500 m, radial scale 20,000 m, and center are hard-coded. Source identifies Doernbrack et al. (2005). |
| `4` | Reads the complete `zs(nx,ny)` field from record 1 of `perts.dat`. | File-defined terrain; the namelist only selects the branch. |

These equations are direct source behavior at [`src/init_terrain.F` lines 63-154](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/init_terrain.F#L63-L154). The r21.1 namelist documentation also warns that the user must change `zs` in `init_terrain.F` for source-defined terrain. A future controlled change to built-in terrain height or width would therefore require a source customization. `itern=4` is the bounded route that can vary terrain without changing CM1 source, but it introduces an exact binary artifact contract.

### `itern=4` / `perts.dat` contract

The r21.1 source:

1. allocates `zs_all(nx,ny)`;
2. has MPI rank 0 open `perts.dat` as Fortran `form='unformatted'`, `access='direct'`, with `recl=4*nx*ny`;
3. reads direct-access record 1 with loop order `((zs_all(i,j),i=1,nx),j=1,ny)`;
4. broadcasts `nx*ny` values as `MPI_REAL`;
5. maps the global field to each process's local `zs` indices; and
6. deallocates the global array.

This is an `x`-fastest, then `y`, full-domain record of `nx*ny` real values. The source's `recl=4*nx*ny` explicitly assumes four bytes per element in the direct-access record. It supplies no self-describing header, endian marker, real-kind marker, checksum, or byte-order conversion. A later Cloud Chamber-generated `perts.dat` would therefore need a pinned four-byte real representation, verified byte ordering, exact dimensions and loop ordering, an artifact hash, and a pre-run readback check against expected terrain extrema and locations. None of that is needed by the official `itern=1` case.

## 4. Terrain-following coordinate and lower-boundary interaction

### Coordinate transform and physical levels

CM1 r21.1 uses the fixed Gal-Chen and Somerville terrain-following transform documented in the [CM1 governing equations](https://www2.mmm.ucar.edu/people/bryan/cm1/cm1_equations.pdf):

```text
sigma = z_t (z - z_s) / (z_t - z_s)
```

where `z_s(x,y)` is terrain height and `z_t` is the constant model-top height. The computational lower boundary is `sigma=0`; the top is `sigma=z_t`. Solving for physical height gives the exact constructions implemented in `src/init_terrain.F`:

```text
zh(x,y,k) = zs(x,y) + sigma(k)  * (z_t - zs(x,y)) / z_t
zf(x,y,k) = zs(x,y) + sigmaf(k) * (z_t - zs(x,y)) / z_t
```

`zh` is the physical height of scalar levels and `zf` is the physical height of full or `w` levels. Model surfaces follow terrain most strongly at the bottom and converge to a constant-height top. They are stationary, not moving terrain. With `stretch_z=0`, `src/param.F` normalizes the runtime `ztop` to `dz*nk`; therefore `z_t=ztop=maxz=sigmaf(nz+1)=nz*dz`. Thus the official case's active top and runtime NetCDF `ztop` are both **20,000 m**. The unchanged `ztop=18,000 m` text in the supplied namelist is inactive configuration retained only in the official-input audit.

The evaluator derives the transform top from the final nominal `zf` level and independently verifies that it agrees with the runtime NetCDF `ztop` and configured `nz*dz`. Any disagreement among these active sources is a fail-closed evaluation error. The inactive 18 km namelist entry is recorded separately and never participates in terrain-coordinate reconstruction.

CM1 derives terrain gradients and metric terms after constructing `zs`, `zh`, and `zf`. The governing-equation form is:

```text
Gx = ((sigma - z_t) / (z_t - z_s)) * dz_s/dx
Gy = ((sigma - z_t) / (z_t - z_s)) * dz_s/dy
Gz = z_t / (z_t - z_s)
```

The source computes `gz=z_t/(z_t-zs)`, its reciprocal, staggered variants, and three-dimensional `gx`/`gy` terms from `zs` gradients. These are active model metrics, not plotting metadata.

### Impermeability and configured bottom boundary

At the physical terrain surface, no normal flow means:

```text
w = u * dz_s/dx + v * dz_s/dy
```

Equivalently, transformed vertical velocity is zero at `sigma=0`. This does **not** mean Cartesian `w=0` on a slope. CM1 enforces the tangency condition in [`bcwsfc`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/bc.F#L1151-L1178), where the lowest-level `w` is set from horizontally averaged `u`, `v`, terrain gradients, and `gz`. Terrain redirects the flow through this kinematic boundary and the terrain-coordinate dynamics.

The official case sets `bbc=1`, documented as **free slip**, and `isfcflx=0`, `sfcmodel=0`. It therefore has:

- an impermeable, terrain-tangent lower boundary;
- no no-slip condition;
- no surface momentum drag or semi-slip stress;
- no surface heat or moisture flux; and
- no land-surface model.

This is an idealized dry dynamical interaction, not a representation of a rough, thermally active mountain surface.

### Base state over terrain

CM1's base state is hydrostatic. For `isnd=9`, thermodynamic state is evaluated at each column's physical `zh(i,j,k)`, not merely at a one-dimensional nominal level. The case hard-codes `N^2=0.0001 s^-2` below 40 km, surface potential temperature 288 K, and zero water vapor, cloud water, and relative humidity. Because the 20 km domain lies below the 40 km transition, the whole modeled column uses `N=0.01 s^-1`.

For `iwnd=6`, `testcase=0` falls through to the source default `u=10 m s^-1`, `v=0`. Those constant values are assigned on the native staggered grids. A height-varying wind option would be evaluated with terrain-aware physical heights where its source branch uses height; this case's wind is constant, so interpolation over terrain does not alter it.

### Distortion and interpolation limitations

The r21.1 terrain guide does not publish a numeric maximum-slope criterion. The transform compresses vertical spacing by `(z_t-z_s)/z_t` and introduces terrain-gradient metric terms, so steep or poorly resolved terrain can distort grid cells and increase metric-error risk. Any later custom terrain must therefore be evaluated with grid-slope and minimum-physical-layer-spacing diagnostics rather than an invented CM1 tolerance.

Official documentation calls `output_interp=1` a quick, coarse aid: it creates a second output set interpolated to nominal heights, doubles output volume, and is not preferred for publication-quality analysis. Native terrain-following fields plus physical-height information remain the authoritative evaluation source.

## 5. Official `nh_mountain_waves` configuration mapping

The controlling configuration is the tag-pinned [`run/config_files/nh_mountain_waves/namelist.input`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/run/config_files/nh_mountain_waves/namelist.input). Each material row has exactly one classification.

| Setting | Exact value | Scientific or operational role | Classification | Evidence |
| --- | --- | --- | --- | --- |
| Dimensions | `nx=100`, `ny=1`, `nz=100` | Two-dimensional `x-z` ridge-flow case with a singleton `y` scalar dimension. | direct official benchmark setting | `param0` |
| Uniform grid | `dx=dy=dz=200 m`; `stretch_x=stretch_y=stretch_z=0` | 20 km `x` extent, nominal 0.2 km `y` extent, and 20 km model top; no active stretching. | direct official benchmark setting | `param1`, `param4-6`, terrain guide |
| Inactive stretched-grid top input | Supplied namelist text has `ztop=18000 m` while `stretch_z=0` | Not the active top. `param.F` normalizes runtime `ztop=maxz=nz*dz=20000 m`, which is also written to NetCDF; the 18 km input remains only in the official-input audit. | CM1 implementation behavior | `param6`, `param.F`, `writeout_nc.F` |
| Origin | `iorigin=2` | Centered horizontal coordinates: nominal `x=-10` to `+10 km`. | direct official benchmark setting | `param2`, `README.namelist` |
| Time integration | `dtl=2 s`, `adapt_dt=0`, `timax=2160 s` | Fixed long timestep; 36-minute official-duration integration. | direct official benchmark setting | `param1-2` |
| History cadence | `tapfrq=216 s` | History at 3.6-minute intervals, including initial output when normal CM1 scheduling applies. | operational/output choice | `param1`, `README.namelist` |
| Restart cadence | `rstfrq=-3600 s` | Negative frequency disables restart output. | operational/output choice | `param1`, `README.namelist` |
| Stats cadence | `statfrq=-60 s` | Negative value requests stats every timestep; magnitude is not a 60-second cadence. | operational/output choice | `param1`, `README.namelist` |
| Terrain activation | `terrain_flag=.true.`, `itern=1` | Activates the built-in 400 m bell ridge with 1 km half-width and `xc=0.5*dx=100 m`. | direct official benchmark setting | `param0`, `param2`, `init_terrain.F` |
| Base-state sounding | `isnd=9`; `N^2=0.0001 s^-2` below 40 km; `theta_sfc=288 K`; dry hydrostatic state | Constant `N=0.01 s^-1` throughout this 20 km domain. | direct official benchmark setting | `param2`, `base.F` |
| Wind | `iwnd=6`, `testcase=0` -> `u=10 m s^-1`, `v=0` | Uniform upstream cross-ridge flow. | direct official benchmark setting | `param2`, `base.F` |
| Moisture and microphysics | `imoist=0`; `qv=qc=rh=0`; microphysics selectors present but inactive | Dry equations; no clouds or latent heating. | direct official benchmark setting | `param2`, `base.F` |
| Initial perturbations | `iinit=0`, `irandp=0` | No thermal or random initial perturbation; terrain is the forcing. | direct official benchmark setting | `param2` |
| Horizontal advection | fifth order for scalar and velocity horizontal/vertical advection; `advwenos=2`, `advwenov=0`, `weno_order=5` | Scalar WENO on final Runge-Kutta step; no velocity WENO. | direct official benchmark setting | `param2`, `README.namelist` |
| Mass conservation | `apmasscon=1` | Applies CM1's open-boundary mass-conservation adjustment. | direct official benchmark setting | `param2`, `README.namelist` |
| Dynamics/turbulence mode | `cm1setup=0` | Integrates the adiabatic, inviscid Euler configuration with no subgrid model or explicit diffusion; numerical-method diffusion can still occur. | direct official benchmark setting | `param2`, `README.namelist` |
| Explicit diffusion | `idiff=0`, `mdiff=0`; `kdiff2`, `kdiff6`, `difforder` consequently inactive | No explicit artificial diffusion from these selectors. | direct official benchmark setting | `param2-3` |
| Inactive turbulence selectors | `ipbl=0`, `horizturb=0`; `sgsmodel=1`, `tconfig=1`, `bcturbs=1`, `doimpl=1` | No PBL path is selected, and `cm1setup=0` causes CM1 to ignore the LES closure and vertical-turbulence controls. | CM1 implementation default | `param2`, `README.namelist` |
| Pressure solver | `psolver=3` | Compressible Klemp-Wilhelmson time splitting with vertically implicit acoustic solve and horizontally explicit calculations. | direct official benchmark setting | `param2`, `README.namelist` |
| Acoustic controls | `kdiv=0.10`, `alph=0.60` | Divergence damping and off-centering for the active `psolver=3` acoustic integration. | direct official benchmark setting | `param3`, `README.namelist` |
| Lateral boundaries | `wbc=ebc=2`; `sbc=nbc=1`; `nudgeobc=0`; `roflux=0` | Open-radiative west/east, periodic singleton-y boundaries, no inflow nudging or outward-flux limiter. | direct official benchmark setting | `param2`, `README.namelist` |
| Bottom/top wind boundaries | `bbc=tbc=1` | Free slip; lower terrain remains impermeable/tangent through terrain boundary logic. | direct official benchmark setting | `param2`, `README.namelist`, `bc.F` |
| Upper radiation | `irbc=4` | Durran-Klemp upper radiative boundary option. | direct official benchmark setting | `param2`, `README.namelist` |
| Rayleigh damping | `irdamp=1`, `zd=14000 m`, `rdalpha=1/300 s^-1` | Damps toward the base state in the upper 6 km of the active 20 km domain. | direct official benchmark setting | `param2-3`, active-grid interpretation |
| Horizontal damping | `hrdamp=0`; `xhd=100000 m` inactive | No horizontal Rayleigh damping. | direct official benchmark setting | `param2-3` |
| Rotation and pressure gradient | `icor=1`, `lspgrad=1`, `fcor=1e-4 s^-1` | Coriolis and large-scale pressure-gradient paths are enabled. Whether their tendencies leave the uniform base flow balanced is execution evidence. | direct official benchmark setting | `param2-3`; balance behavior requires run confirmation |
| Equation set | `eqtset=2` with `imoist=0` | Moist-equation selector is not materially active in the dry case. | CM1 implementation default | `param2`, input logic |
| Surface/radiation | `isfcflx=0`, `sfcmodel=0`, `oceanmodel=0`, `radopt=0` | No surface heat/moisture exchange, drag model, ocean model, or radiation. | direct official benchmark setting | `param11-12` |
| Native output format | `output_format=1`, `output_filetype=1` | Official bundle requests GrADS single-file output, which current Cloud Chamber cannot ingest. | operational/output choice | `param9`, writeout code |
| Interpolated output | `output_interp=1` | Adds nominal-height `_i` output; supplemental and documented as coarse. | operational/output choice | `param9`, terrain guide |
| Terrain/height output | `output_zs=1`, `output_zh=1` | Writes terrain `zs` and physical scalar-level height field `zhval`. | operational/output choice | `param9`, `writeout.F` |
| Core state output | `output_th=output_prs=output_u=output_v=output_w=1`; interpolated velocity copies also enabled | Supports dry-wave evaluation, though the later gate may make an output-only NetCDF selection. | operational/output choice | `param9` |
| Expected official history files | `cm1out_s.dat/.ctl`, `cm1out_u.dat/.ctl`, `cm1out_v.dat/.ctl`, `cm1out_w.dat/.ctl`, and supplemental `cm1out_i.dat/.ctl` | GrADS scalar/staggered native files plus nominal-height interpolation. | operational/output choice | `writeout.F`, terrain guide |
| Expected official stats/log files | `cm1out_stats.dat` plus CM1 text output; exact created inventory depends on normal execution | Stats and runtime evidence, not atmospheric history fields. | requires later verification | `README.namelist`, future execution |
| Dry-inapplicable output | Rain/swath, `qv`, hydrometeor `q`, reflectivity, TKE, and diffusivity switches remain enabled | These inherited switches do not make the dry state moist and add little decision value. | CM1 implementation default | `param9`; actual emitted variables require run inspection |
| Stats selectors | Many stats switches enabled; parcels disabled with `iprcl=0`; domain diagnostics disabled | Stats can support integrity checks, while moisture/cloud entries are dry-inapplicable. | CM1 implementation default | `param10`, `param13-14` |
| Runtime input files | Built-in `itern=1`, `isnd=9`, no land model | No `perts.dat`, `input_sounding`, `LANDUSE.TBL`, or `input_grid_z` is scientifically consumed. | direct official benchmark setting | terrain/base/input source |
| Exact output inventory and termination | Not available from source alone | Filenames, emitted dry-inapplicable fields, finite values, and normal completion must be captured from an actual configured run. | requires later verification | future execution evidence |

The official source calls `itern=1` bell-shaped terrain and cites Durran and Klemp (1983). The case is a source-bundled example with a clear literature lineage, but neither the namelist nor source provides a numeric pass/fail tolerance against a published reference field. Configuration presence is not itself validation.

## 6. Expected dry-wave evidence

### A. Quantitative source-backed targets

A faithful package and run must reproduce these exact invariants before interpretation:

- grid: `100 x 1 x 100`, 200 m uniform spacing, 20 km `x` extent and 20 km top;
- terrain: `zs=400/[1+((x-100 m)/1000 m)^2]`, maximum 400 m at the scalar point nearest `x=100 m`, half-height 1 km from that center;
- base state: `theta_sfc=288 K`, `N^2=1.0e-4 s^-2`, zero moisture through the domain;
- upstream flow: `u=10 m s^-1`, `v=0` before terrain disturbance;
- integration: 2 s timestep through 2,160 s;
- damping: onset at 14 km with coefficient `1/300 s^-1`; and
- the derived nondimensional mountain height `Nh/U = 0.4`, recorded as a configuration check rather than an acceptance tolerance.

The inspected official sources do not provide a downloadable r21.1 reference field, pointwise error norm, amplitude tolerance, or phase-error threshold for this exact bundled run. No such threshold is invented here.

### B. Qualitative and structural expectations

Evaluation should document, with native-grid cross sections and numeric summaries:

- terrain height and center agree with the analytic source expression;
- undisturbed upstream `u` and stratification remain recognizable away from boundaries and the hill;
- terrain-tangent flow generates alternating vertical-velocity structure above and downstream of the ridge;
- potential-temperature surfaces are displaced consistently with the gravity-wave pattern;
- wave phase and vertical structure are coherent in the central domain rather than isolated numerical pixels;
- the response propagates vertically/downstream as expected for the open, stratified flow; and
- the lower boundary satisfies terrain tangency rather than an incorrect Cartesian `w=0` interpretation.

The Durran-Klemp paper establishes the model and bell-terrain lineage and includes linear-wave examples, but matching its figures quantitatively would require reconstructing the paper's exact analytical/numerical setup and comparison metric. That is beyond the source-bundled reproduction gate unless PM later approves a separate validation question.

### C. Runtime and numerical-integrity checks

The later run must show:

- source and executable hashes match the recorded configured runtime;
- the generated namelist parses and the CM1 startup log echoes the intended values;
- normal CM1 termination with exit code zero;
- expected history times from 0 through 2,160 s, with no missing or duplicate times;
- finite `zs`, `zhval`, `th`, `prs`, `u`, `v`, and `w` values at every captured time;
- dimensions/staggering match r21.1 definitions;
- terrain is static and physical heights are monotonic in each column;
- mass/pressure diagnostics do not show runaway drift; and
- no runtime-integrity caveat is silently ignored.

### D. Contamination checks

Review must distinguish central wave structure from:

- west/east open-boundary transients or reflection;
- top-boundary reflection;
- Rayleigh-layer attenuation below/near 14 km;
- startup adjustment from imposing terrain under a uniform base flow;
- artifacts from the 200 m grid and terrain-coordinate metrics; and
- artifacts introduced by optional nominal-height interpolation.

The primary scientific review should use the central domain and native terrain-following fields. Interpolated `_i` output, if retained, is a supplemental cross-check only.

## 7. Required output and evaluation plan

### Minimum later output

The later gate should make one explicit operational change to the official bundle: write one NetCDF file per history time (`output_format=2`, `output_filetype=2`) so filenames are compatible with Cloud Chamber's current `cm1out_######.nc` sequence contract. This changes storage/transport, not the dry scientific configuration. Keep the official 216 s cadence.

| CM1 name | Native location | Use | Current ingest | Current honest rendering |
| --- | --- | --- | --- | --- |
| `zs` | 2-D scalar horizontal grid, meters | Verify terrain shape/location and construct physical heights. | Retained in recognized NetCDF metadata as a data variable. | No. It is absent from the field catalog and generic surface rendering assumes a flat floor. |
| coordinate `zh` | 1-D scalar vertical coordinate | In terrain NetCDF this contains nominal `sigma(k)`, not physical height by column. | Retained as a coordinate. | Misleading if treated as physical altitude over terrain. |
| coordinate `zf` | 1-D full-level vertical coordinate | Nominal `sigmaf(k)` for `w` staggering; its last value is the active 20 km top. | Retained as a coordinate. | Misleading if treated as physical altitude over terrain except for the constant-height top. |
| scalar `ztop` | Runtime NetCDF scalar | Contains the normalized 20 km active top for this unstretched run. | Retained if present. | Independently cross-check against the final nominal `zf` and configured `nz*dz`; fail closed on disagreement. |
| `zhval` | 3-D scalar grid, meters | Physical height `zh(x,y,k)` for `th`, `prs`, and scalar-interpolated evaluation. | Retained in metadata but not specially interpreted. | No; no field definition or terrain-aware mesh path. |
| `th` | 3-D scalar grid | Potential-temperature displacement and wave phase. | Recognized. | Values can be sliced, but current altitude placement uses the nominal 1-D coordinate. |
| `prs` | 3-D scalar grid | Hydrostatic/field integrity and pressure response. | Recognized. | Same flat-grid placement limitation. |
| `u` | 3-D `u`-staggered grid | Upstream-flow and horizontal response checks. | Recognized. | Same terrain-height limitation, plus staggering must remain explicit. |
| `v` | 3-D `v`-staggered grid | Verify the nominally 2-D case remains consistent in `y`. | Recognized. | Same terrain-height limitation. |
| `w` | 3-D full-level grid | Primary terrain-forced wave structure and boundary tangency. | Recognized. | Current payload uses nominal `zf`; physical `zf(x,y,k)` is not directly output by `output_zh`. |
| `cm1out_stats` | Stats stream | CFL, mass, extrema, and termination context. | Classified separately from model history. | No browser rendering required. |

For native output, `output_zs=1` emits `zs` in meters and `output_zh=1` emits a three-dimensional variable named `zhval`, described as height on model levels. The NetCDF coordinate variables still write one-dimensional `zh=sigma` and `zf=sigmaf` when terrain is active. This naming distinction is essential.

CM1 does not expose a corresponding three-dimensional `zfval` through `output_zh`. The later evaluator can reconstruct physical full-level heights exactly from verified `zs`, nominal `zf`/`sigmaf`, and the active top from the last nominal `zf` value using the r21.1 equation. It must independently confirm that the final nominal `zf`, runtime NetCDF `ztop`, and configured `nz*dz` all resolve to 20,000 m. The derivation must be tested against `zf_physical(:,:,1)=zs` and `zf_physical(:,:,nz+1)=20,000 m` before evaluating `w` in physical space.

### Native versus interpolated output

- **Required:** native `zs`, `zhval`, `th`, `prs`, `u`, `v`, `w`, nominal coordinates, active `maxz`/top-level evidence, times, log, and stats.
- **Supplemental:** `output_interp=1` output for a visual cross-check only. Current filename classification excludes `_i` files, and official documentation warns that this interpolation is coarse.
- **Not decision-reducing:** dry-inapplicable rain, hydrometeor, reflectivity, cloud, TKE, diffusivity, parcel, or budget output.

The official GrADS choice is not required to preserve scientific equivalence. The exact later package should record the official namelist and a machine-readable output-only deviation list. Native NetCDF values, not browser views, are the acceptance evidence.

## 8. Current Cloud Chamber compatibility and gaps

### Package generation and manifests

Current generic rendering in `app/backend/cloud_chamber/cm1_input_contract.py` hard-codes `terrain_flag=.false.` and `itern=0`, and is built around the current moist scenario contract. `app/backend/cloud_chamber/dry_run_package.py` cannot emit the official dry terrain namelist without customization. As with BOMEX, a dedicated bounded case generator would be required; widening the generic scenario framework is unnecessary for the dry gate.

The current package contract always produces `namelist.input`, `input_sounding`, a run manifest, and `runtime_file_checklist.json`. Local preflight rejects placeholder sounding notes and expects the generated input contract. Official `isnd=9` does not scientifically consume `input_sounding`. A dedicated gate must either include a clearly audited but non-consumed numeric file to satisfy current launch plumbing or make one bounded preflight adaptation; it must not pretend that file defines the base state.

Run manifests already support generated-input paths and a runtime-file checklist. They do not carry a terrain-specific artifact schema or physical-coordinate interpretation.

### Runtime staging and execution

`app/backend/cloud_chamber/local_run_manager.py` reads `runtime_file_checklist.json` and stages listed files from configured runtime candidates. `scripts/lan_worker_run.py` similarly copies the package and resolves the checklist on the worker. The official built-in `itern=1` case needs no `LANDUSE.TBL`, `perts.dat`, or external grid/sounding file, so local and LAN staging have no additional scientific runtime file to supply.

If a later approved case used `itern=4`, current generic generation would not create or declare `perts.dat`. The existing staging mechanism could copy a named file once it was explicitly listed, but honest support would also require generation/readback metadata, dimensions, encoding, checksum, and source candidates. That is outside this gate.

### Ingest and output naming

Current model-output classification in `result_ingest.py` and `output_products.py` accepts only `^cm1out_\d+\.nc(?:4)?$`. Therefore:

- the official GrADS files are not ingestible;
- NetCDF `output_filetype=1` would create `cm1out.nc`, which also does not match;
- NetCDF `output_filetype=2` creates matching `cm1out_######.nc` files; and
- interpolated `cm1out_######_i.nc` files are classified as other artifacts.

For matching model NetCDF files, ingest records all `dataset.data_vars` and coordinates in metadata. It would preserve the presence, dimensions, and units of `zs` and `zhval`; it does not persist or expose them as terrain semantics by itself.

### Field catalog and browser payloads

`app/backend/cloud_chamber/visualization_data.py` recognizes fields including `th`, `prs`, `u`, `v`, and `w`, but has no `zs` or `zhval` field definition. Its coordinate resolution selects one-dimensional axis candidates such as `xh`, `yh`, `zh`, and `zf`.

Consequences:

- slices show native array planes against nominal one-dimensional vertical coordinates;
- profiles and time-height products aggregate against nominal vertical levels;
- point-cloud construction maps vertical positions from a one-dimensional `zh`/`zf` coordinate;
- terrain-following scalar and velocity cells would be plotted at flat-grid heights;
- the Three.js viewer constructs axis-aligned bounds and a flat floor; and
- even if `zs` were exposed as a generic surface field, current placement would not produce a terrain-aware atmospheric mesh.

Current Cloud Chamber can **retain enough raw NetCDF information for a dedicated evaluator**, but it cannot render terrain-following output honestly in existing slices, profiles, time-height products, point clouds, or 3-D views.

### Smallest honest later technical boundary

The dry reproduction does not require a browser terrain feature. Its smallest boundary is:

1. a dedicated, test-covered generator for the exact official scientific case;
2. an output-only change to a recognized NetCDF sequence;
3. existing local/LAN launch and manifest provenance with no extra runtime files;
4. direct native-NetCDF evaluation of `zs`, `zhval`, `th`, `prs`, `u`, `v`, and `w` using terrain-aware physical heights; and
5. a source-traceable report rather than existing flat-grid visualization payloads.

Terrain-aware browser contracts and rendering belong to a later product-approved prototype, not the reproduction gate.

## 9. Proposed bounded dry-reproduction gate

This is a ready-to-scope execution plan, not an authorization or a created issue.

### Exact allowed configuration

- Start from official r21.1 `run/config_files/nh_mountain_waves/namelist.input` at commit `0f734f64efa89a684963a66d2ac32db67617912b`.
- Preserve every scientific setting classified as a direct official benchmark setting in Section 5.
- Permit only declared operational output changes: `output_format=2`, `output_filetype=2`, retain `tapfrq=216 s`, require `output_zs`, `output_zh`, `output_th`, `output_prs`, `output_u`, `output_v`, and `output_w`, and disable dry-inapplicable output if the generated diff records each change.
- Prefer `output_interp=0` for the minimum run. If PM requires comparison to the official bundle's interpolated output, enable it only as supplemental output.
- No moisture, microphysics activation, terrain modification, profile tuning, product UI, or visualization implementation.

### One package and one run

The case is only 100 x 1 x 100 for 2,160 s at a 2 s timestep. A separate scientific smoke run would alter duration and add little confidence beyond package validation. Use:

1. package-only validation, including parser/preflight checks and an exact namelist diff; then
2. one official-duration run.

Do not execute a shortened CM1 smoke process unless PM explicitly approves it after a preflight concern.

### Pre-run checks

- Clean branch/worktree and exact allowed changed paths for the later gate.
- Confirm CM1 release, source commit relationship, source-manifest hash, executable hash, and `README.namelist` hash against Section 2.
- Confirm the configured build supports NetCDF.
- Verify the generated namelist against the tag-pinned official file and classify every difference as the approved output-only change.
- Confirm `terrain_flag=.true.`, `itern=1`, `isnd=9`, `iwnd=6`, `imoist=0`, `nx=100`, `ny=1`, `nz=100`, `dx=dy=dz=200`, `dtl=2`, and `timax=2160`.
- Confirm the runtime checklist is empty of scientifically consumed external files; specifically, no `LANDUSE.TBL` or `perts.dat`.
- Record that any packaged `input_sounding` is not consumed by `isnd=9`.
- Calculate expected output bytes from actual selected variables, dimensions, precision, history count, and NetCDF overhead; verify free space is at least twice that estimate.

For scale, the required six three-dimensional fields plus `zs` comprise about 70,300 four-byte values per history time, or approximately 3.1 MB over 11 times before coordinates, metadata, logs, stats, and NetCDF overhead. The actual package report, not this estimate, controls the storage preflight.

### Runtime and scientific evidence

- Capture command, environment summary without machine-private paths, source/executable identities, wall time, exit code, stdout/stderr, and normal-termination marker.
- Verify exactly expected history times and files.
- Run finite/count/range checks for all required fields.
- Verify analytic `zs`, physical `zhval`, reconstructed physical `zf`, monotonic columns, dimensions, staggering, and static terrain. Record the inactive 18 km input separately, require the final nominal `zf`, runtime NetCDF `ztop`, and configured `nz*dz` to agree at the 20 km active top, and reject any evaluator if those active sources disagree.
- Record upstream `u`, dry stability, and moisture absence.
- Produce native-grid `w` and `th` cross sections in physical height for initial, early, middle, and final times.
- Record extrema and locations by time without turning them into unsupported pass thresholds.
- Review central-domain phase/structure, downstream and vertical propagation, top damping, and lateral-boundary contamination.
- Compare optional interpolated output only to diagnose interpolation effects, never as the sole evidence.
- Report stats/mass/CFL behavior and any runtime caveat.

### Stopping and correction rules

Stop without rerunning if any of these occurs:

- provenance does not match the recorded configured runtime;
- the generated namelist contains an unapproved scientific difference;
- required terrain/height/state output is absent or not finite;
- physical-height reconstruction cannot be independently checked;
- CM1 does not terminate normally;
- boundary/damping contamination prevents central-domain interpretation; or
- evidence suggests a source, compiler, or output-contract discrepancy.

Return the evidence to PM. One bounded correction may be proposed only after identifying a single causal defect. Any correction, altered configuration, or rerun requires explicit PM approval. No iterative tuning, alternative terrain, moist extension, or product implementation is authorized.

## 10. Risks, uncertainties, and items requiring execution evidence

| Risk or uncertainty | Current evidence and required resolution |
| --- | --- |
| Official case is 2-D; a future experience would likely be 3-D | `ny=1` verifies ridge-normal dry dynamics only. It says nothing about finite ridge geometry, lateral flow, 3-D turbulence, or a future World. |
| Dry benchmark is not a cloud case | Success would validate terrain-wave mechanics and execution, not moisture, condensation, lenticular clouds, or a useful product experience. |
| Open-boundary sensitivity | Source identifies west/east radiative boundaries, but reflection and inflow behavior require time-evolving output review. |
| Upper boundary and damping sensitivity | `irbc=4` plus Rayleigh damping above 14 km is explicit; whether the central wave is materially contaminated is run evidence. |
| Terrain-coordinate distortion | The analytic 400 m / 1 km hill and 20 km top are known, but r21.1 publishes no numeric distortion tolerance. Physical layer spacing and metric behavior must be inspected. |
| `output_interp` limitations | Official documentation says it is coarse and doubles output. It is not acceptable as the only scientific representation. |
| Physical-height semantics | Native NetCDF provides 1-D nominal `zh`/`zf`, 2-D `zs`, and 3-D scalar `zhval`; full-level physical heights for `w` must be reconstructed and checked. |
| Active-top interpretation | The supplied namelist retains an inactive 18 km `ztop`, but `param.F` normalizes runtime `ztop` to the 20 km unstretched-grid top. Evaluation derives the transform top from the final nominal `zf` and requires agreement with runtime `ztop` and configured `nz*dz`. |
| Current flat-grid application assumptions | Ingest retains metadata, but existing slices, profiles, time-height payloads, point clouds, and Three.js placement do not use terrain-aware physical heights. |
| Official example versus validated benchmark | The bundled case is source-traceable and literature-linked, but no official r21.1 field checksum or quantitative tolerance was found. The later gate establishes reproducibility and structural fidelity, not formal solution convergence. |
| Configured runtime behavior | Prior repository evidence records source/executable identity, but actual terrain run behavior, NetCDF availability, output inventory, numerical ranges, and termination remain unverified until Tim's configured runtime executes the case. |
| Coriolis/pressure-gradient balance | The switches and base wind are known. Confirmation that no unwanted balanced-flow transient materially affects the result requires output. |
| Inert namelist values | Several values remain present while their controlling switches are off. Startup echo and generated diff should confirm active interpretation rather than deleting settings casually. |

## 11. Disposition

`advance_to_dry_reproduction`

The exact CM1 r21.1 terrain mechanics and official dry case are sufficiently understood to specify one bounded, official-duration reproduction. The terrain equation, coordinate transform, lower-boundary condition, dry hydrostatic base state, uniform wind, boundary/damping choices, and required native outputs all trace to primary source. Current Cloud Chamber gaps are also bounded: a dedicated package, NetCDF sequence output, and terrain-aware offline evaluator are required; a generic terrain framework and browser implementation are not.

This disposition does **not** establish that the configured runtime has executed the case, that the source-bundled example meets an unstated quantitative benchmark tolerance, that current Cloud Chamber visualization is terrain-aware, that a three-dimensional or moist case is selected, or that a Mountain Wave Clouds World, Recipe, Control, Lens, Comparison, or product direction is approved.

## Sources

### Official CM1 r21.1

- NCAR, [CM1 repository, tag `21.1` / commit `0f734f64`](https://github.com/NCAR/CM1/tree/0f734f64efa89a684963a66d2ac32db67617912b).
- NCAR, [`src/init_terrain.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/init_terrain.F).
- NCAR, [`src/base.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/base.F).
- NCAR, [`src/input.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/input.F).
- NCAR, [`src/param.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/param.F).
- NCAR, [`src/bc.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/bc.F).
- NCAR, [`src/writeout.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/writeout.F).
- NCAR, [`src/writeout_nc.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/writeout_nc.F).
- NCAR, [`run/config_files/nh_mountain_waves/namelist.input`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/run/config_files/nh_mountain_waves/namelist.input).
- NCAR, [`README.terrain`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/README.terrain).
- NCAR, [`README.namelist`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/README.namelist).
- George H. Bryan, [The governing equations for CM1](https://www2.mmm.ucar.edu/people/bryan/cm1/cm1_equations.pdf), especially the terrain-coordinate transform and metric terms.

### Primary scientific literature

- Gal-Chen, T., and R. C. J. Somerville, 1975: [On the use of a coordinate transformation for the solution of the Navier-Stokes equations](https://doi.org/10.1016/0021-9991(75)90037-6). *Journal of Computational Physics*, **17**, 209-228.
- Durran, D. R., and J. B. Klemp, 1983: [A Compressible Model for the Simulation of Moist Mountain Waves](https://doi.org/10.1175/1520-0493(1983)111%3C2341:ACMFTS%3E2.0.CO;2). *Monthly Weather Review*, **111**, 2341-2361. This is the lineage named for `itern=1`; the r21.1 bundled case itself is dry.
- Klemp, J. B., W. C. Skamarock, and O. Fuhrer, 2003: [Numerical Consistency of Metric Terms in Terrain-Following Coordinates](https://doi.org/10.1175/1520-0493(2003)131%3C1229:NCOMTI%3E2.0.CO;2). *Monthly Weather Review*, **131**, 1229-1239. Named by the `itern=2` source branch.
- Doernbrack, A., J. D. Doyle, T. P. Lane, R. D. Sharman, and P. K. Smolarkiewicz, 2005: [On physical realizability and uncertainty of numerical solutions](https://doi.org/10.1002/asl.100). *Atmospheric Science Letters*, **6**, 118-122. Named by the `itern=3` source branch.

### Cloud Chamber repository evidence

- [BOMEX setup and CM1 mapping](../bomex/bomex-setup-and-cm1-mapping.md).
- [BOMEX run report](../bomex/bomex-run-report.md).
- `app/backend/cloud_chamber/cm1_input_contract.py`
- `app/backend/cloud_chamber/dry_run_package.py`
- `app/backend/cloud_chamber/run_manifest.py`
- `app/backend/cloud_chamber/local_run_manager.py`
- `scripts/lan_worker_run.py`
- `app/backend/cloud_chamber/result_ingest.py`
- `app/backend/cloud_chamber/output_products.py`
- `app/backend/cloud_chamber/visualization_data.py`
- `app/frontend/src/True3DViewer.tsx`
