# Canonical deep-convection benchmark mapping

## 1. Status and decision question

**Status:** Gate A desk research complete; no CM1 process was started.

**Decision question:** Which exact stock CM1 r21.1 idealized deep-convection case
is the best first mechanics benchmark for a bounded, source-locked reproduction
before any third-World product decisions are made?

**Selection:** the official `run/config_files/supercell/namelist.input` case at
CM1 release 21.1 commit
`0f734f64efa89a684963a66d2ac32db67617912b`. Its official README identifies it
as the Weisman and Rotunno (2000) quarter-circle-hodograph supercell case.

This answers only the canonical-mechanics question authorized by parent decision
record #410.

This selection is a mechanics reference, not a product definition. It does not
approve a Storms World, a World name, a reference Simulation, an observed-weather
reproduction, a Recipe, a Lens, a Control, a Comparison, a variation surface, or
any UX. It also does not establish that the eventual experience should be about
severe weather rather than cloud development and atmospheric process.

The selected case **is**:

- an official, three-dimensional, idealized, stock-CM1 deep-convection case;
- a deterministic warm-bubble initiation in an analytic thermodynamic and wind
  environment;
- a quarter-circle-hodograph supercell mechanics benchmark linked explicitly by
  CM1 to Weisman and Rotunno (2000);
- a practical first test of deep precipitating convection, rotation,
  hydrometeor evolution, and storm organization in the pinned local executable.

The selected case **is not**:

- a historical weather-event simulation or forecast;
- a Fort Worth sounding reproduction;
- an exact reproduction of the 2000 paper's original model physics;
- evidence that the future World should permanently center a supercell;
- permission to tune the trigger, sounding, hodograph, domain, or physics.

The key qualification is important. The official r21.1 case says it is
"following" Weisman and Rotunno (2000) and preserves the paper's recognizable
geometry, environment, trigger, and duration, but it uses the current stock
Morrison double-moment microphysics rather than the paper's warm-rain Kessler
scheme. Gate B therefore tests faithful reproduction of the **official stock
CM1 r21.1 benchmark**, with the paper as its scientific lineage; it cannot claim
publication-grade reproduction of the original numerical experiment.

## 2. Source hierarchy and exact pinned CM1 identity

### Authority hierarchy

Material claims in this mapping use these labels:

- **directly specified by the benchmark source**: stated by the CM1 case README,
  the official case namelist, or the cited benchmark paper;
- **official CM1 implementation choice**: behavior encoded in pinned CM1 r21.1
  source for the selected namelist option;
- **exact derivation**: arithmetic or direct interpretation from pinned values,
  such as `120 * 1000 m = 120 km`;
- **later operational/output choice**: a bounded non-scientific adaptation that
  Gate B would need for Cloud Chamber execution or ingest;
- **unknown pending execution**: an output property that source inspection alone
  cannot establish, including actual dimensions, units, finite values, cost, or
  storm evolution.

Primary scientific literature controls the case's scientific lineage. The
pinned CM1 source, official configuration, README, and `README.namelist` control
the behavior of the available stock case. Cloud Chamber code controls only its
present packaging, execution, ingest, provenance, and visualization
compatibility.

### Pinned source identity

| Identity | Exact value | Evidence |
|---|---|---|
| CM1 release | `21.1`, dated 24 March 2024 | local release README and official release tree |
| Official commit | `0f734f64efa89a684963a66d2ac32db67617912b` | [NCAR/CM1 pinned tree](https://github.com/NCAR/CM1/tree/0f734f64efa89a684963a66d2ac32db67617912b) |
| Local source-manifest SHA-256 | `fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e` | each sorted `src/*.F` hashed as `<sha256>  src/<name>\n`, then the manifest text hashed; matches the repository's existing r21.1 source lock |
| Local executable SHA-256 | `5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1` | `/Users/timpeterson/cm1r21.1/run/cm1.exe`; local-only evidence, not a committed binary |
| `README.namelist` SHA-256 | `7b95be56db51f5c9396c59dca252cf96b918a312cc70107451f91149a34ab3b5` | local pinned distribution; matches existing source-lock evidence |
| Executable form | arm64 Mach-O, dynamically linked to NetCDF, NetCDF-Fortran, gfortran, and quadmath; no MPI library observed | local binary inspection; Gate B must still report the actual command and process behavior |

The local extracted source is not itself a Git checkout. To close that provenance
gap without running CM1, the selected case README and namelist and critical
source files were compared byte-for-byte with raw files at the pinned official
commit. The local files matched.

| Pinned file | SHA-256 |
|---|---|
| `run/config_files/supercell/README` | `3292aef3f7cdc49701015609626f55a3fd64162c88929d0992f9635dfb230200` |
| `run/config_files/supercell/namelist.input` | `3854f731efe6a6a9d56d6aa3db198434ccaba85bc5584b5e8ce1c5edfd3b56a4` |
| `src/base.F` | `9c88a1021ddde22d02680786246c52bcffb040cbd72c3c4708f24fe24eec32ef` |
| `src/init3d.F` | `9c45c0982ba194ea6ea74afd6a2516445cdd011fc90902091d089f4cb92dfd28` |
| `src/param.F` | `cac64a6cb4363c6b88367b5cb9391f1bcf2130c63ffedef6e5973c03b190c349` |
| `src/writeout_nc.F` | `5023244d7ce4f9a0dde7df9c780cf5c70b675097e8467c4fbfc8125e254f4710` |

The selected configuration directory contains only `README` and
`namelist.input`. It has no external sounding, terrain, land-use, lookup-table,
or other case-specific runtime file. Its sounding, wind profile, and trigger are
compiled analytic paths. Surface fluxes, radiation, terrain, and surface models
are off, so `LANDUSE.TBL` is not scientifically required by this case. Gate B
must verify that launch preflight does not invent a required file.

## 3. Candidate comparison

Only two stock r21.1 configurations are serious first mechanics candidates.
Other official cases address hurricanes, radiative-convective equilibrium,
shallow clouds, terrain waves, or numerical tests rather than this bounded
deep-convection question.

### Candidate inventory

| Property | `supercell` | `squall_line` |
|---|---|---|
| Official identity | "Idealized supercell thunderstorm simulation, following Weisman and Rotunno (2000)"; quarter-circle hodograph | "Idealized squall line simulation, mostly following Bryan et al. (2003)"; 1-km weak-shear case |
| Namelist SHA-256 | `3854f731efe6a6a9d56d6aa3db198434ccaba85bc5584b5e8ce1c5edfd3b56a4` | `2f75792a569cf497d76d9df2186692f81a296028e85c162c65cd19df8dfdf5b8` |
| README SHA-256 | `3292aef3f7cdc49701015609626f55a3fd64162c88929d0992f9635dfb230200` | `8b6d6f7aaf9f72eb62f05aafd42a8cbf054425d2a45a8ff83ca3d7d32bff399b` |
| External sounding/runtime files | none; analytic `isnd=5`, `iwnd=2`, `iinit=1` | none; analytic `isnd=5`, `iwnd=1`, `iinit=8` |
| Dimensions | 3-D, `120 x 120 x 40` | 3-D, `300 x 60 x 40` |
| Uniform grid | `1 km x 1 km x 0.5 km` | `1 km x 1 km x 0.5 km` |
| Exact active domain | `120 x 120 x 20 km`; 576,000 scalar cells | `300 x 60 x 20 km`; 720,000 scalar cells |
| Timestep and duration | fixed `6 s`; `7,200 s` (2 h) | fixed `6 s`; `10,800 s` (3 h) |
| Saved-output cadence | `900 s`; expected 9 times including initialization | `900 s`; expected 13 times including initialization |
| Initiation | one centered 1 K ellipsoidal warm bubble, 10 km horizontal radius, 1.4 km vertical radius and center height; deterministic | y-uniform 2 K line thermal, 10 km x-radius, 1.5 km z-radius and center height, plus deterministic pseudo-random +/-0.2 K perturbations inside it |
| Thermodynamics | analytic Weisman-Klemp sounding (`isnd=5`) | same analytic Weisman-Klemp sounding (`isnd=5`) |
| Wind | quarter-circle below 2 km, then u increases to 31 m/s by 6 km while v remains 7 m/s; constant aloft | RKW weak shear: u increases linearly from 0 to 10 m/s over 0-2.5 km; v=0; constant aloft |
| Domain motion | `(umove, vmove)=(12.5, 3.0) m/s` | `(12.5, 0.0) m/s` |
| Horizontal boundaries | open-radiative on all four sides | open-radiative west/east; periodic south/north |
| Upper/lower boundaries and damping | free-slip top/bottom; Rayleigh damping toward base state from 15 to 20 km; no lateral Rayleigh damping | same |
| Coriolis and large-scale forcing | both off | both off |
| Moist physics | Morrison double-moment, hail treatment, six mass species plus four number concentrations | same |
| Numerical core | fixed timestep; fifth-order scalar/velocity advection, scalar WENO on final RK step, no added artificial diffusion, stock SGS closure | same |
| Output format | stock GrADS/direct-access single-file setting; 15-minute history cadence and 60-second statistics | same format/cadences |
| Distinguishing output | vorticity and 2-5 km AGL updraft helicity enabled, plus related swaths; native cold-pool diagnostic off | vorticity and updraft helicity disabled; native cold-pool diagnostic on |
| Expected organization | preferred rotating supercell with mature quarter-circle case maintained through 120 min in the cited study | organized line/cold-pool system; stock README explicitly describes a 1-km weak-shear case |
| Local burden before execution | Fort Worth's same cell count, timestep, duration, and cadence is a direct cost anchor: about 11.45 minutes and 242 MB with its field set; stock output remains execution-dependent | 1.25 times the cells and 1.5 times the model duration imply about 1.875 times the integration work before output effects, and 13 rather than 9 expected history times |
| Disposition | **select** | reject as the first benchmark; retain as a possible later convective-organization benchmark only after a separate decision |

Both cases use the same modern stock Morrison physics and Weisman-Klemp
thermodynamics, and neither requires an external sounding or scientific runtime
file. The comparison therefore turns on organization, cost, trigger/wind,
boundary geometry, and requested observables rather than package recoverability.

### Why the squall-line case is not first

The stock `squall_line` case is scientifically legitimate and may eventually
answer a different question about repeated cells, cold-pool/shear balance, and
line organization. It is not a weaker case in general. It is a weaker **first
mechanics reference for this gate** because:

1. it costs more locally in cells, model duration, and expected frames;
2. its default output omits the rotation diagnostics already enabled in the
   supercell case;
3. Bryan, Wyngaard, and Fritsch (2003) specifically show strong resolution
   sensitivity and question whether 1-km grids resolve equivalent convective
   structures, making the stock "1-km weak-shear" choice a more qualified first
   baseline;
4. the selected supercell case provides one compact, deterministic storm and a
   clearer published structural target over the same two-hour duration already
   exercised locally by Fort Worth.

No product-experience preference is inferred from this selection.

The stock squall-line candidate is now governed separately by the queued
[Squall Line program, issue #413](https://github.com/coloradotim/cloud-chamber/issues/413).
Its Gate A work in
[issue #414](https://github.com/coloradotim/cloud-chamber/issues/414) remains
blocked until the Supercell program reaches Mountain Waves-equivalent maturity.
This artifact neither selects a benchmark for #414 nor activates that work.

## 4. Selected benchmark and rationale

The exact selected benchmark is:

```text
CM1 r21.1
official commit: 0f734f64efa89a684963a66d2ac32db67617912b
configuration: run/config_files/supercell/namelist.input
configuration SHA-256: 3854f731efe6a6a9d56d6aa3db198434ccaba85bc5584b5e8ce1c5edfd3b56a4
case identity: quarter-circle-hodograph idealized supercell
scientific lineage: Weisman and Rotunno (2000)
```

Selection reasons:

- **Recoverable identity:** the official README names the paper and exact
  quarter-circle case, and the namelist and implementation paths are source
  visible and hashable.
- **Stock execution:** no source modification or external scientific input file
  is required.
- **Mechanics coverage:** the case combines a deep moist sounding, curved
  hodograph, deterministic trigger, precipitation, liquid and ice species,
  reflectivity, vorticity, updraft helicity, surface rain, and storm swaths.
- **Bounded cost:** it is 576,000 cells for 1,200 fixed large steps over two
  model hours, with an existing same-size local Fort Worth cost anchor.
- **Observable target:** the paper describes the quarter-circle case as the most
  classic-looking supercell configuration and a strong, steady rotating
  updraft over the mature period. That provides a qualitative benchmark without
  inventing thresholds.

The selection does not claim that Morrison microphysics should become product
authority, that a warm bubble is an observed causal boundary, or that the
quarter-circle profile is representative of all deep convection.

## 5. Primary scientific authority

### Benchmark paper

Weisman, M. L., and R. Rotunno, 2000: "The Use of Vertical Wind Shear versus
Helicity in Interpreting Supercell Dynamics." *Journal of the Atmospheric
Sciences*, 57, 1452-1472.
[AMS article and DOI](https://journals.ametsoc.org/view/journals/atsc/57/9/1520-0469_2000_057_1452_tuovws_2.0.co_2.xml).

The paper directly specifies or reports:

- the Weisman-Klemp thermodynamic profile with approximately 2,200 J/kg CAPE
  and moist conditions throughout the troposphere;
- 35 m/s wind variation from the surface to 6 km for the base set;
- straight, quarter-circle, and more-curved hodographs, with winds constant
  above 6 km for the quarter-circle case;
- 1 km horizontal and 500 m vertical spacing;
- a 120 km by 120 km by 17.5 km domain and two-hour simulations;
- one ellipsoidal warm bubble with 10 km horizontal radius, 1.4 km vertical
  radius, and 1 K maximum perturbation;
- open lateral boundaries, a radiative upper condition, and free slip below;
- a mature rotating-storm comparison at 40, 80, and 120 minutes;
- the quarter-circle case as the most classic-looking configuration in the
  reported set.

The original paper used the Klemp-Wilhelmson cloud model with warm-rain Kessler
microphysics. The r21.1 stock case's Morrison scheme, 20 km active model top,
specific numerics, output inventory, and modern CM1 equation-set choices are
official CM1 implementation choices, not claims from the paper.

### Analytic sounding authority

Weisman, M. L., and J. B. Klemp, 1982: "The Dependence of Numerically Simulated
Convective Storms on Vertical Wind Shear and Buoyancy."
*Monthly Weather Review*, 110, 504-520.
[AMS article and DOI](https://journals.ametsoc.org/abstract/journals/mwre/110/6/1520-0493_1982_110_0504_tdonsc_2_0_co_2.xml).

Pinned `src/base.F` labels `isnd=5` as the Weisman-Klemp analytic sounding and
cites this paper. The exact r21.1 equations and constants below are controlled
by source, not reconstructed from a plotted sounding.

### Alternative-case authority

Bryan, G. H., J. C. Wyngaard, and J. M. Fritsch, 2003: "Resolution Requirements
for the Simulation of Deep Moist Convection." *Monthly Weather Review*, 131,
2394-2416.
[AMS article and DOI](https://journals.ametsoc.org/abstract/journals/mwre/131/10/1520-0493_2003_131_2394_rrftso_2.0.co_2.xml).

This paper supports the scientific identity and resolution caution for the
rejected first alternative. The stock README says `squall_line` "mostly"
follows it; that qualifier must remain.

### Equation-set authority

Bryan, G. H., and J. M. Fritsch, 2002: "A Benchmark Simulation for Moist
Nonhydrostatic Numerical Models." *Monthly Weather Review*, 130, 2917-2928.
[DOI](https://doi.org/10.1175/1520-0493(2002)130%3C2917:ABSFMN%3E2.0.CO;2).

Pinned `README.namelist` cites this work for `eqtset=2`. It is authority for the
energy- and mass-conserving moist equation-set choice, not for the selected
supercell's storm identity.

### CM1 authority

- [Official CM1 home](https://www2.mmm.ucar.edu/people/bryan/cm1/)
- [Pinned supercell configuration](https://github.com/NCAR/CM1/tree/0f734f64efa89a684963a66d2ac32db67617912b/run/config_files/supercell)
- [Pinned `base.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/base.F)
- [Pinned `init3d.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/init3d.F)
- [Pinned `param.F`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/src/param.F)
- [Pinned `README.namelist`](https://github.com/NCAR/CM1/blob/0f734f64efa89a684963a66d2ac32db67617912b/README.namelist)

## 6. Complete configuration and runtime-file mapping

Unless labeled otherwise, values in this section are **directly specified by
the benchmark source**. Source-resolved behavior is labeled **official CM1
implementation choice**.

### Grid, integration, and model movement

| Assignment | Active meaning |
|---|---|
| `nx=120`, `ny=120`, `nz=40` | 3-D scalar grid with 576,000 cells |
| `dx=1000`, `dy=1000`, `dz=500` m | uniform spacing because all stretch switches are off |
| `stretch_x=0`, `stretch_y=0`, `stretch_z=0` | disables the supplied stretched-grid parameters |
| `iorigin=2` | centered horizontal coordinate origin |
| exact horizontal extent | **exact derivation:** 120 km by 120 km, nominally -60 to +60 km around the centered origin |
| exact active vertical extent | **exact derivation:** 40 layers x 500 m = 20 km, with scalar centers expected from 0.25 to 19.75 km and interfaces from 0 to 20 km; actual coordinates must be verified from output |
| `ztop=18000` m | inactive because `stretch_z=0`; it must not be reported as the active top |
| `dtl=6` s, `adapt_dt=0` | fixed large timestep; 1,200 large steps over the run |
| `timax=7200` s, `run_time=-999.9` | two-hour integration; negative `run_time` does not override `timax` |
| `tapfrq=900` s | 15-minute 3-D output; expected 9 times including initialization, pending execution |
| `rstfrq=-3600` s | restart output disabled by the documented negative value |
| `statfrq=60` s | statistics every minute |
| `prclfrq=60` s | parcel-output cadence present but inactive because `iprcl=0` |
| `imove=1`, `umove=12.5`, `vmove=3.0` m/s | constant translating computational domain |
| `do_adapt_move=.false.` | no adaptive domain movement; `adapt_move_frq=3600` is inactive |
| `ppnode=128` | decomposition hint in the stock namelist; actual local non-MPI process behavior is an execution record, not a scientific setting |
| `timeformat=2`, `timestats=1` | CM1 timing/statistics formatting enabled |
| `terrain_flag=.false.`, `itern=0` | flat terrain |
| `procfiles=.false.` | no per-process output files |
| `cm1setup=1`, `testcase=0`, `irst=0`, `rstnum=1`, `iconly=0` | standard atmospheric integration from initialization, not a restart or initialization-only run |

Inactive grid assignments retained in the official file are:

```text
dx_inner=1000, dx_outer=7000, nos_x_len=40000, tot_x_len=120000
dy_inner=1000, dy_outer=7000, nos_y_len=40000, tot_y_len=120000
ztop=18000, str_bot=0, str_top=2000, dz_bot=125, dz_top=500
```

They are parameters for disabled stretch paths and must not be allowed to
silently redefine the uniform active grid.

### Base-state thermodynamics

`isnd=5` selects the analytic Weisman-Klemp sounding. Pinned `src/base.F`
provides this **official CM1 implementation choice**:

```text
z_trop = 12,000 m
theta_trop = 343 K
T_trop = 213 K
theta_surface = 300 K
surface pressure = 100,000 Pa
boundary-layer qv cap = 0.014 kg/kg
```

Below 12 km:

```text
theta(z) = 300 K + (343 K - 300 K) * (z / 12,000 m)^1.25
RH(z) = 1 - 0.75 * (z / 12,000 m)^1.25
```

At and above 12 km:

```text
theta(z) = 343 K * exp[g * (z - 12,000 m) / (213 K * cp)]
RH(z) = 0.25
```

CM1 iterates the hydrostatic pressure, temperature, and water-vapor solution 20
times, calculates saturation mixing ratio over liquid, and caps `qv` at
0.014 kg/kg. These equations and constants are source-controlled. The paper's
approximately 2,200 J/kg CAPE is a benchmark description; Gate B must not claim
an exact r21.1 CAPE without deriving it from the actual initialized state using
a declared method.

There is no external `input_sounding`. The exact base state is recoverable only
when the pinned source identity is part of provenance.

### Wind and storm-relative interpretation

`iwnd=2` selects the source-defined Weisman-Klemp supercell profile. Pinned
`src/base.F` sets:

```text
udep1 = 2,000 m
udep2 = 6,000 m
umax1 = 7 m/s
umax2 = 31 m/s
vmax1 = 7 m/s
```

The ground-relative analytic profile is:

```text
0 <= z <= 2 km:
  angle = 90 degrees * z / 2 km
  u = 7 - 7 cos(angle) m/s
  v = 7 sin(angle) m/s

2 < z <= 6 km:
  u increases linearly from 7 to 31 m/s
  v = 7 m/s

z > 6 km:
  u = 31 m/s
  v = 7 m/s
```

This turns through a quarter circle in the lowest 2 km and then adds
unidirectional u shear to 6 km. CM1's moving-domain values `(12.5, 3.0) m/s`
are subtracted for model-relative flow. Any displayed ground-relative wind must
add them back explicitly. Gate B must report which frame is used for every wind
or storm-motion statement.

The stock source profile's surface-to-6-km vector difference is
`sqrt(31^2 + 7^2) = 31.78 m/s`, an **exact derivation**. That is not the
35 m/s variation specified for the paper's base experiments. The official CM1
README still identifies this as the quarter-circle case following the paper,
but the numerical difference is another reason not to call Gate B an exact
reproduction of the 2000 experiment.

`icor=0` disables Coriolis, so `fcor=0.00005 s^-1` is inactive. `lspgrad=0`
disables large-scale pressure-gradient forcing. These choices keep the idealized
two-hour mechanics interpretation bounded.

### Initiation

`iinit=1` selects one deterministic ellipsoidal warm bubble. Pinned
`src/init3d.F` sets:

```text
x center = horizontal domain center
y center = horizontal domain center
z center = 1,400 m AGL
horizontal radius = 10,000 m
vertical radius = 1,400 m
maximum potential-temperature perturbation = 1 K
```

Inside the ellipsoid, with normalized radius `beta < 1`:

```text
theta perturbation = 1 K * cos(0.5 * pi * beta)^2
```

It is zero outside. `maintain_rh=.false.` means CM1 preserves constant `qv` on
a height level when applying this perturbation rather than preserving constant
RH. `irandp=0` adds no random perturbations, and this `iinit=1` path contains no
random component. `ibalance=0` initializes no balancing pressure perturbation.
The bubble is a standard benchmark initiation device, not an observed front,
dryline, convergence boundary, or measured parcel.

### Numerics, turbulence, and equation set

| Assignment | Active interpretation |
|---|---|
| `hadvordrs=5`, `vadvordrs=5` | fifth-order scalar advection |
| `hadvordrv=5`, `vadvordrv=5` | fifth-order velocity advection |
| `advwenos=2`, `advwenov=0`, `weno_order=5` | fifth-order scalar WENO active on the final Runge-Kutta step; velocity WENO off |
| `apmasscon=1` | domain-average pressure perturbation adjustment for dry-air mass conservation active |
| `idiff=0`, `mdiff=0`, `difforder=6` | additional artificial diffusion off; `mdiff`, `difforder`, `kdiff2`, and `kdiff6` are inactive, while the odd-order advection schemes retain their implicit diffusion |
| `sgsmodel=1`, `tconfig=1`, `bcturbs=1`, `horizturb=0` | TKE subgrid scheme for `cm1setup=1`; same horizontal/vertical turbulence-coefficient treatment, zero-flux upper/lower scalar diffusion boundary, and no separate horizontal-turbulence parameterization |
| `ipbl=0` | no planetary-boundary-layer parameterization |
| `doimpl=1`, `psolver=3`, `alph=0.60` | vertically implicit acoustic treatment and pressure-solver configuration |
| `kdiv=0.10` | divergence damper active with `psolver=3` |
| `eqtset=2` | CM1's energy- and mass-conserving equation-set option, including hydrometeor heat capacity per `README.namelist` |
| `idiss=1` | dissipative heating enabled |
| `efall=0` | energy-fallout term disabled; this does **not** disable hydrometeor sedimentation |
| `rterm=0` | simple idealized radiative relaxation off |
| `cuparam=0` | no cumulus parameterization |
| `roflux=0`, `nudgeobc=0` | no specified open-boundary outward mass flux or boundary nudging |

The active microphysics constant in the remainder of `param3` is
`ndcnst=250 cm^-3`. The following values are retained but inactive under the
selected switches: `kdiff2=75` and `kdiff6=0.040` (`idiff=0`), `v_t=7`
(`ptype` is not 6), `l_h=100`, `lhref1=100`, and `lhref2=1000`
(`horizturb=0`), `l_inf=75` (`ipbl=0`), `nt_c=250` (`ptype` is not 3),
`csound=300` (`psolver` is not 6 or 7), `cstar=30` (`irbc=4`, not 1 or 2),
`xhd=100000` (`hrdamp=0`), and `alphobc=60` (`nudgeobc=0`).

### Moist physics

| Assignment | Active interpretation |
|---|---|
| `imoist=1` | moist integration |
| `ptype=5` | Morrison double-moment microphysics |
| `ihail=1` | the scheme's large precipitating ice category uses hail treatment rather than graupel treatment |
| `ndcnst=250 cm^-3` | constant cloud-droplet concentration because pinned Morrison `graupel_init` sets `INUM=1` |
| `iautoc=1` | inactive for `ptype=5`; `README.namelist` says this switch applies only to the Goddard-LFO `ptype=2` scheme |

Pinned `src/param.F` shows that `ptype=5` with `INUM=1`, together with the
independently enabled `output_qv=1` and `output_q=1`, requests `qv` plus five
condensate mass fields and four number-concentration fields:

| Field | Meaning | Source unit |
|---|---|---|
| `qv` | water-vapor mixing ratio | `kg/kg` |
| `qc` | cloud-water mixing ratio | `kg/kg` |
| `qr` | rain-water mixing ratio | `kg/kg` |
| `qi` | cloud-ice mixing ratio | `kg/kg` |
| `qs` | snow mixing ratio | `kg/kg` |
| `qg` | large precipitating ice mixing ratio, treated as hail because `ihail=1` | `kg/kg` |
| `nci` | cloud-ice number concentration | `#/kg` |
| `ncs` | snow number concentration | `#/kg` |
| `ncr` | rain number concentration | `#/kg` |
| `ncg` | hail-category number concentration | `#/kg` |

There are not separate simultaneous graupel and hail mass fields in this setup.
The single `qg`/`ncg` large-ice category uses hail parameters because
`ihail=1`; calling it both graupel and hail would double-count one category.

The Morrison implementation handles conversion and sedimentation internally.
`output_dbz=1` requests scheme-supported reflectivity, and `output_rain=1`
requests accumulated surface precipitation. Actual variable names, dimensions,
units, stagger placement, fill values, finite ranges, and whether every expected
number concentration appears in NetCDF are **unknown pending execution**.

The `nssl2mom_params` group (`alphah=0`, `alphahl=0.5`, `ccn=0.6e9`,
`cnor=8e6`, `cnoh=4e4`) is inactive because this case uses `ptype=5`, not NSSL
two-moment microphysics. It must remain unchanged in an exact package but must
not be described as active Morrison configuration.

### Boundaries and damping

| Assignment | Active interpretation |
|---|---|
| `wbc=2`, `ebc=2`, `sbc=2`, `nbc=2` | open-radiative boundaries on all four sides |
| `irbc=4` | Durran-Klemp radiative formulation |
| `bbc=1`, `tbc=1` | free-slip lower and upper wind boundaries |
| `irdamp=1` | upper Rayleigh damping toward the base state |
| `rdalpha=1/300 s^-1`, `zd=15000 m` | damping starts at 15 km and occupies the upper 5 km of the active 20 km domain |
| `hrdamp=0` | lateral Rayleigh damping disabled |

The moving domain is intended to keep the primary storm away from open lateral
boundaries, but source mapping cannot prove that it succeeds through 7,200 s.
Gate B must inspect storm position, translated swaths, and boundary proximity.
Strong upper-tropospheric flow or storm propagation into the lateral relaxation
region is an inconclusive condition, not permission to change motion or domain.
The 15-20 km Rayleigh layer can affect the highest hydrometeor and vertical-
velocity levels and must remain visible in interpretation.

### Surface, radiation, and other inactive groups

The following assignments are present but scientifically inactive:

- `radopt=0`: all calendar, location, and radiation cadence values in `param11`
  are inert (`dtrad`, latitude/longitude, and date/time).
- `isfcflx=0`, `sfcmodel=0`, `oceanmodel=0`: land/ocean initialization,
  exchange coefficients, prescribed heat/moisture fluxes, roughness, friction
  velocity, mixed-layer-ocean, and SGS-ramp values in `param12` do not force the
  atmosphere. There is no scientific `LANDUSE.TBL` dependency.
- `iptra=0`: passive-tracer counts and diffusivity (`npt=1`, `pdtra=1`) are
  inactive.
- `iprcl=0`: parcel count and every `param13` parcel-output switch are inactive.
- `dodomaindiag=.false.`: `diagfrq=60` is inactive.
- `doazimavg=.false.`: azimuthal-average settings are inactive.
- all four `do_recycle_*` switches are false, so recycling geometry is inactive.
- all `do_lsnudge*` switches are false, so large-scale nudging values are
  inactive.
- `do_ib=.false.`: immersed-boundary settings are inactive.
- `axisymm=0`: Cartesian 3-D behavior; axisymmetric restrictions do not apply.
- `param7` temperature-boundary constants and `param8` generic `var1` through
  `var20` values are retained but are not material to this atmospheric setup.
- `param17` LES-subdomain geometry values are inert unless a feature using that
  subdomain is enabled; no such feature is active here.
- `param21` hurricane vortex values are unrelated to this case.

For audit completeness, the inactive groups must be preserved exactly as
follows. The values are source identity, not active forcing:

```text
param7:
  bc_temp=1, ptc_top=250, ptc_bot=300, viscosity=25, pr_num=0.72

param8:
  var1 through var20 = 0

param11 with radopt=0:
  dtrad=300, ctrlat=36.68, ctrlon=-98.35
  year=2009, month=5, day=15, hour=21, minute=38, second=0

param12 with isfcflx=0, sfcmodel=0, oceanmodel=0:
  initsfc=1, tsk0=299.28, tmn0=297.28, xland0=2, lu0=16, season=1
  cecd=3, pertflx=0, cnstce=0.001, cnstcd=0.001, isftcflx=0
  iz0tlnd=0, oml_hml0=50, oml_gamma=0.14
  set_flx=0, cnst_shflx=0.24, cnst_lhflx=5.2e-5
  set_znt=0, cnst_znt=0.16, set_ust=0, cnst_ust=0.25
  ramp_sgs=1, ramp_time=1800, t2p_avg=1

param14 with dodomaindiag=false:
  diagfrq=60

param15 with doazimavg=false and do_adapt_move=false:
  azimavgfrq=3600, rlen=300000, adapt_move_frq=3600

param17:
  les_subdomain_shape=1, les_subdomain_xlen=200000
  les_subdomain_ylen=200000, les_subdomain_dlen=200000
  les_subdomain_trnslen=5000

param18 with do_recycle_w/s/e/n=false:
  recycle_width_dx=6, recycle_depth_m=1500
  recycle_cap_loc_m=4000, recycle_inj_loc_m=0

param19 with do_lsnudge and do_lsnudge_u/v/th/qv=false:
  lsnudge_tau=1800, lsnudge_start=3600, lsnudge_end=7200
  lsnudge_ramp_time=600

param20 with do_ib=false:
  ib_init=4, top_cd=0.4, side_cd=0.4

param21:
  hurr_vg=40, hurr_rad=40000, hurr_vgpl=-0.70, hurr_rotate=0
```

### Official output and restart mapping

The stock file requests `output_format=1` (GrADS/direct-access binary) and
`output_filetype=1` (one file), with `output_interp=0`. Cloud Chamber's current
ingest contract recognizes sequence NetCDF. Gate B may therefore make exactly
these **later operational/output choices**:

```text
output_format:   1 -> 2   # NetCDF
output_filetype: 1 -> 2   # one output file per output time
```

No scientific option, grid value, cadence, field switch, or interpolation switch
may change. The exact two-line diff must be recorded and audited before launch.

Official enabled history fields and products are:

```text
output_rain=1
output_sws=1, output_svs=1, output_sps=1, output_srs=1
output_sgs=1, output_sus=1, output_shs=1
output_th=1, output_prs=1, output_tke=1, output_km=1, output_kh=1
output_qv=1, output_q=1, output_dbz=1
output_u=1, output_uinterp=1
output_v=1, output_vinterp=1
output_w=1, output_winterp=1
output_vort=1, output_uh=1
```

The enabled swaths are maximum surface wind, maximum lowest-level vertical
vorticity, minimum lowest-level pressure perturbation, maximum lowest-level
rain/hail-category mixing ratios, maximum 5-km updraft, and maximum integrated
updraft helicity. With `imove=1`, translated surface-rain and surface-wind
products may also be emitted. `output_coldpool=0` leaves CM1's native cold-pool
diagnostic off.

Explicitly disabled history outputs include surface flux/parameter/diagnostic
fields, surface pressure, terrain heights, base-state fields, perturbation
theta/pressure/Exner/density/water vapor/winds, Exner and density, buoyancy,
potential vorticity, PBL/dissipation/fall-speed/number-mean/deformation/radiation
tendencies, CAPE, CIN, LCL, LFC, precipitable water, LWP, all listed budgets,
and pressure-decomposition output. The q number concentrations are still
included through `output_q=1`; `output_nm=0` is a different diagnostic switch.

The exact disabled switch inventory is:

```text
output_coldpool=0
output_sfcflx=0, output_sfcparams=0, output_sfcdiags=0, output_psfc=0
output_zs=0, output_zh=0, output_basestate=0
output_thpert=0, output_prspert=0, output_pi=0, output_pipert=0
output_rho=0, output_rhopert=0, output_qvpert=0, output_buoyancy=0
output_upert=0, output_vpert=0, output_pv=0
output_pblten=0, output_dissten=0, output_fallvel=0, output_nm=0
output_def=0, output_radten=0
output_cape=0, output_cin=0, output_lcl=0, output_lfc=0
output_pwat=0, output_lwp=0
output_thbudget=0, output_qvbudget=0, output_ubudget=0
output_vbudget=0, output_wbudget=0, output_pdcomp=0
```

The stock statistics file enables `w`, levelwise `w`, `u`, `v`, pressure and
Exner perturbations, theta perturbation, q species, TKE, `km`, `kh`, divergence,
RH over liquid and ice, equivalent potential temperature, cloud, surface
pressure, surface wind speed, CFL, vorticity, total mass/moisture/energy,
momentum and mass-flux diagnostics, precipitation concentration, and q sources.
`stat_rmw=0` is the one disabled switch in that group.

The exact statistics switches are:

```text
stat_w=1, stat_wlevs=1, stat_u=1, stat_v=1, stat_rmw=0
stat_pipert=1, stat_prspert=1, stat_thpert=1, stat_q=1
stat_tke=1, stat_km=1, stat_kh=1, stat_div=1
stat_rh=1, stat_rhi=1, stat_the=1, stat_cloud=1
stat_sfcprs=1, stat_wsp=1, stat_cfl=1, stat_vort=1
stat_tmass=1, stat_tmois=1, stat_qmass=1, stat_tenerg=1
stat_mo=1, stat_tmf=1, stat_pcn=1, stat_qsrc=1
```

`iprcl=0` makes the following enabled-looking parcel requests inactive:

```text
prcl_th=1, prcl_t=1, prcl_prs=1, prcl_ptra=1, prcl_q=1, prcl_nc=1
prcl_km=1, prcl_kh=1, prcl_tke=1, prcl_dbz=1, prcl_b=1
prcl_vpg=1, prcl_vort=1, prcl_rho=1, prcl_qsat=1, prcl_sfc=1
nparcels=1
```

Restart output is disabled by negative `rstfrq`. The restart format/filetype and
all `restart_file_*` and `restart_use_theta` values remain present but do not
cause a restart file in this run. Every optional restart field is false.

The exact inactive restart assignments are:

```text
restart_format=1, restart_filetype=2, restart_reset_frqtim=true
restart_file_theta=false, restart_file_dbz=false, restart_file_th0=false
restart_file_prs0=false, restart_file_pi0=false, restart_file_rho0=false
restart_file_qv0=false, restart_file_u0=false, restart_file_v0=false
restart_file_zs=false, restart_file_zh=false, restart_file_zf=false
restart_file_diags=false, restart_use_theta=false
```

Expected NetCDF inventory, exact units, scalar/staggered dimensions, coordinates,
fill behavior, and the number of files are all **unknown pending execution**.
Gate B must validate them rather than copying assumptions into provenance.

## 7. Expected mechanism and observables

### Expected physical sequence

1. The centered 1 K bubble provides a finite, idealized lifting perturbation in
   the moist, moderately unstable Weisman-Klemp environment.
2. The initial updraft tilts horizontal vorticity supplied by the quarter-circle
   and deeper unidirectional shear.
3. Curved low-level shear biases the storm toward one preferred rotating member
   rather than a symmetric pair with equal longevity.
4. Dynamic pressure perturbations and updraft-shear interaction support storm
   propagation and repeated updraft growth on the rotating flank.
5. Morrison microphysics partitions condensed water among cloud water, rain,
   cloud ice, snow, and hail-treated large ice, with precipitation loading,
   fallout, melting, and evaporation affecting downdrafts and outflow.
6. Surface precipitation and cold-pool evolution interact with the storm, while
   the translating domain attempts to retain it away from open boundaries.

Steps 1-3 are tied directly to the source-defined case and benchmark lineage.
The detailed r21.1 hydrometeor and outflow evolution is an implementation result,
not a promise from the 2000 paper.

### Required observables for Gate B

The later report must inspect, at minimum:

- time evolution of maximum and minimum `w`, including height and position;
- cloud and precipitation onset and the vertical/horizontal evolution of `qc`,
  `qr`, `qi`, `qs`, and `qg` without collapsing them into one ambiguous cloud;
- finite, physically interpretable `dbz` and accumulated surface `rain`;
- horizontal winds in a declared model-relative or ground-relative frame;
- potential temperature and pressure structure;
- all three vorticity components and 2-5 km AGL updraft helicity;
- enabled storm swaths, especially updraft, vorticity, pressure, hail-category,
  and updraft-helicity swaths;
- primary-storm structure and position at approximately 40, 80, and 120 minutes;
- proximity to lateral boundaries and the upper damping zone;
- runtime integrity, non-finite values, output completeness, wall time, and disk
  use.

Qualitative agreement means development of deep precipitating rotating
convection with a sustained organized primary updraft during the mature period.
It does not require matching paper figures pixel-for-pixel, and it must not be
declared from one maximum value alone.

## 8. Current Cloud Chamber compatibility and gap analysis

This compatibility assessment is source-locked to Cloud Chamber commit
`a14202cc8af1d7d3438d69b9ca0d0b3852e923ec`, the reviewed `main` base for this
branch. The branch differs from that commit only by this research artifact, so
the classifications below describe application capability at that exact base
rather than capability after later Supercell work.

| Capability | Classification | Evidence and bounded implication |
|---|---|---|
| Generate or stage the exact official case | **bounded adaptation required** | Generic `deep_tower_benchmark` rendering is built around observed `isnd=7`, `iwnd` ignored, and `iinit=3`; it cannot honestly represent analytic `isnd=5`, `iwnd=2`, `iinit=1`. A dedicated source-locked stock-supercell package path is needed. |
| Preserve required sounding/runtime files | **bounded adaptation required** | The case needs no external scientific files, but current generic launch preflight requires `input_sounding`. The dedicated path must record an empty scientific runtime-file inventory and must not invent a fake sounding. |
| Execute pinned r21.1 executable | **already supported** mechanically; **bounded adaptation required** for source lock | The local manager runs `[cm1.exe]` as one subprocess in the package directory. Existing BOMEX and Mountain Waves paths demonstrate fail-closed source/executable hashing; the generic deep-tower path does not establish this exact case identity. |
| Preserve generated-input identity through launch | **bounded adaptation required** | The dedicated package must hash the official source artifacts and generated namelist, recheck them at launch, and carry the approved two-line diff into promoted output provenance. |
| Ingest sequence NetCDF | **already supported** after the approved output-only change; **execution must verify** exact inventory | Ingest recognizes `cm1out_<digits>.nc`, reads NetCDF metadata and diagnostics, and has aliases for `uh`/`updraft_helicity`. Stock GrADS output is not the supported product path. |
| Validate native fields | **bounded adaptation required** | Gate B validation must assert dimensions, units, finite counts, and time coordinates for each required field, not merely field-name presence. |
| Represent the regular flat grid in 3-D and slices | **already supported** for current field subsets; **execution must verify** coordinates | Current visualization preserves native coordinates and staggering caveats. A 120 x 120 x 40 flat grid is structurally compatible. |
| Display `qc`, `qr`, `qv` | **already supported** | These support native slices and 3-D scalar points; `qc` is the canonical cloud-water field. |
| Display `w`, `u`, `v`, `th`, `prs` | **already supported** for slices/profiles; **bounded adaptation required** for richer 3-D motion inspection | Current definitions intentionally keep signed flow and thermodynamic fields slice/profile-first. |
| Display `qi`, `qs`, `qg` independently | **bounded adaptation required** | Diagnostics can include them in a hydrometeor envelope, but the current direct visualization field registry does not expose each species as a first-class field. Hail interpretation must remain tied to `qg` plus `ihail=1`. |
| Display reflectivity and surface rain | **already supported**; **execution must verify** native fields and units | Current result diagnostics support `dbz` and accumulated `rain`. |
| Display vorticity and updraft helicity directly | **bounded adaptation required** | Ingest recognizes updraft-helicity aliases, but current direct visualization field definitions do not expose vorticity or UH as normal scientific views. |
| Preserve exact benchmark provenance | **bounded adaptation required** | Existing source-locked cases provide the pattern. The stock-supercell identity must include release, commit, source manifest, executable, README/config, critical source hashes, exact namelist diff, and empty external-file inventory. |
| Estimate runtime and storage before launch | **already supported** generically; **bounded adaptation required** for a calibrated case estimate | Current package reports cell/time/frame multipliers. Gate B should use the Fort Worth same-size run as the lower empirical anchor and enforce a declared disk headroom check. |

No item is a material blocker. The gaps are bounded packaging, provenance,
validation, and field-exposure adaptations. None requires CM1 source
modification. This conclusion authorizes only a later reproduction gate, not
general storm infrastructure.

## 9. Relation to prior Fort Worth Deep-Tower evidence

The preserved run
`cloud_chase_001-fort_worth_deep_tower_probe` is useful historical evidence but
not benchmark authority.

The evidence chain inspected for this mapping is:

- **PR #270:** introduced the earlier Deep Convection Trial using observed
  Fort Worth thermodynamics and winds through `isnd=7` plus stock `iinit=3`.
  Its separate product-generated smoke record reported 13 history files, normal
  completion with underflow-only stderr, maximum `w` 54.126 m/s, maximum
  reflectivity 64.522 dBZ, liquid and ice species, surface rain, and updraft
  helicity. This proved the older package family, not the selected stock case.
- **Issue #341:** authorized restoration of that explicit thermal path as a
  current recipe and required the Fort Worth evidence to be treated as an
  idealized supplied trigger, not a real initiating boundary.
- **Issue #348:** bounded Cloud Chase 001 around producing one compelling cloud
  through the current Build-to-Explore workflow rather than building a general
  trigger or diagnostic framework.
- **PR #349:** restored the current Deep-Tower Benchmark and preserved the
  nine-frame, two-hour Fort Worth run described below. Its review also records
  that a package-ready sounding is only a candidate, not proof of a strong
  result.

The differing 13-file PR #270 smoke record and nine-file PR #349 current run are
distinct historical executions. Their values must not be combined into one
synthetic run identity.

### What it proves

Repository records and the preserved local artifacts show that the current
local executable and product path completed a 3-D moist deep-convection run with:

```text
grid: 120 x 120 x 40
uniform spacing: 1 km x 1 km x 0.5 km
active model top: 20 km
timestep: 6 s
duration: 7,200 s
saved-output cadence: 900 s
history files: 9, from 0 through 7,200 s
process: one local cm1.exe command
wall time: 686.728251 s (about 11 min 27 s)
preserved directory size: 242 MB, including restart and reports
runtime result: exit 0 and normal termination, with nonfatal IEEE underflow caveat
```

The ingested evidence includes first cloud at 900 s, first deep convection at
1,800 s, maximum `w` 54.126 m/s, minimum `w` -15.888 m/s, maximum `qc`
0.005071 kg/kg, maximum `qr` 0.006555 kg/kg, coherent hydrometeor top 17.25 km,
raw hydrometeor traces to 19.75 km, maximum reflectivity 65.376 dBZ, and maximum
accumulated surface rain 0.721 cm. It proves that a same-size, same-duration,
same-cadence Morrison deep-convection run can complete locally and yield
ingestible `qc`, `qr`, `qi`, `qs`, `qg`, winds, precipitation, and reflectivity
evidence.

### How it differs

Fort Worth used:

- an observed external `input_sounding` with `isnd=7` and observed winds;
- stock `iinit=3`, which places three warm bubbles rather than the selected
  centered `iinit=1` bubble;
- a Cloud Chamber-generated package and output selection;
- a different environmental wind and thermodynamic state;
- existing deep-tower assumptions rather than the source-locked supercell README
  and namelist identity.

It therefore does **not** prove:

- that the analytic Weisman-Klemp base state initializes as mapped;
- that the quarter-circle hodograph or moving frame is correct in output;
- that a mature rotating supercell persists through 120 minutes;
- that the exact official field and swath inventory is emitted in NetCDF;
- that the stock case reproduces the published structural behavior;
- that Fort Worth should be a built-in Simulation, Recipe, or reference World.

After a successful Gate B and a separate PM decision, Fort Worth could be
evaluated as a second observed-atmosphere Simulation, an experiment contrasting
an observed profile with the analytic benchmark, or supporting runtime evidence.
This gate makes no choice among those roles.

## 10. Exact bounded Gate B reproduction plan

### Purpose

Run the exact source-locked stock CM1 r21.1 quarter-circle supercell once through
a dedicated package and report whether it executes faithfully and yields
trustworthy, inspectable deep convection. Do not test whether a third World is
approved.

### Exact inputs and permitted changes

Gate B must use:

```text
CM1 release: 21.1
official commit: 0f734f64efa89a684963a66d2ac32db67617912b
official config: run/config_files/supercell/namelist.input
official config SHA-256: 3854f731efe6a6a9d56d6aa3db198434ccaba85bc5584b5e8ce1c5edfd3b56a4
official README SHA-256: 3292aef3f7cdc49701015609626f55a3fd64162c88929d0992f9635dfb230200
source-manifest SHA-256: fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e
local executable SHA-256: 5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1
scientific external runtime files: none
```

The only permitted namelist changes are:

```diff
- output_format    = 1,
- output_filetype  = 1,
+ output_format    = 2,
+ output_filetype  = 2,
```

They are non-scientific transport choices needed for native sequence-NetCDF
ingest. `output_interp` stays `0`; all output switches and cadences stay stock.
No source file, grid, physics, sounding, wind, initiation, boundary, damping,
motion, duration, timestep, or output field may change.

### Required package and preflight

The dedicated package must:

1. copy or render the full stock namelist with only the approved two-line diff;
2. audit every material assignment against the pinned source file;
3. record the exact original and generated namelist hashes and a machine-readable
   assignment diff;
4. record release, commit, source-manifest, executable, README, config,
   `README.namelist`, and critical source hashes;
5. record that no external scientific runtime file is consumed;
6. omit fake `input_sounding` and unnecessary `LANDUSE.TBL` content;
7. re-hash the executable and all generated inputs immediately before launch;
8. fail closed on any unexpected file, hash, assignment, source, or executable
   mismatch;
9. estimate cost and enforce enough free space for the run plus safe ingest;
10. use tiny fixtures and a fake process in automated tests; the real run is a
    manual Gate B action, never CI.

### Process, duration, output, and resource expectations

- Expected process command: one local process, exactly `[<pinned>/run/cm1.exe]`,
  with no `mpirun`; record the actual command and process ID.
- Expected model duration: 7,200 s with fixed 6 s large timestep.
- Expected history times: 0, 900, 1,800, 2,700, 3,600, 4,500, 5,400, 6,300,
  and 7,200 s; nine sequence-NetCDF history files. Treat the count as expected,
  not proven until execution.
- Expected statistics: one NetCDF statistics stream at 60 s cadence, subject to
  actual CM1 naming.
- Expected restart files: none because `rstfrq` is negative.
- Planning wall-time band: 15-30 minutes. Fort Worth's 11.45 minutes remains the
  same-grid, same-duration integration anchor, but the stock benchmark's larger
  required history inventory materially increases output work. The wider band
  is provisional until Gate B records compute and write timing separately.
- Planning retained-storage band: 650-900 MB for package, history, statistics,
  coordinates and metadata, logs, reports, and other retained provenance
  artifacts. Require at least 2.0 GB free immediately before launch. That
  threshold covers the 900 MB retained upper plan, at least 900 MB of temporary
  finalization and inspection/ingest workspace, and a 200 MB reserve. Fail
  closed below the threshold and report actual bytes by artifact class.

The storage plan starts from the exact active grid and the requested fields,
not the smaller Fort Worth retained directory. Pinned `writeout.F` and
`writeout_nc.F` classify the expected arrays and write these variables as
four-byte NetCDF `NF90_FLOAT` values:

| Expected history payload class | Arrays | Values per array | Bytes per history |
|---|---:|---:|---:|
| Scalar-grid 3-D: `th`, `prs`, ten moisture fields, `dbz`, three interpolated winds, and three vorticity components | 19 | `120 x 120 x 40 = 576,000` | 43,776,000 |
| W-grid 3-D: `tke`, `kmh`, `kmv`, `khh`, `khv` | 5 | `120 x 120 x 41 = 590,400` | 11,808,000 |
| Native staggered `u` | 1 | `121 x 120 x 40 = 580,800` | 2,323,200 |
| Native staggered `v` | 1 | `120 x 121 x 40 = 580,800` | 2,323,200 |
| Native staggered `w` | 1 | `120 x 120 x 41 = 590,400` | 2,361,600 |
| Scalar-grid 2-D: rain and seven swath families, their moving-domain translated forms, and instantaneous 2-5 km AGL updraft helicity | 17 | `120 x 120 = 14,400` | 979,200 |
| **Uncompressed numeric payload lower bound** | **44** | | **63,571,200** |

Across nine expected histories, that is at least **572,140,800 bytes
(572.1 MB; about 545.6 MiB)** before coordinate values, time and moving-domain
scalars, NetCDF structure and attributes, statistics, logs, reports, package
files, or inspection/ingest products. Each sequence file also carries at least
the six scalar and staggered coordinate vectors (`xh`, `xf`, `yh`, `yf`, `zh`,
`zf`) plus `ztop`, time, and moving-domain scalars. Their numeric values are
small relative to the fields, but their attributes and NetCDF container
overhead are not included in the lower bound.

The 650-900 MB retained band reserves additional space for that coordinate and
metadata overhead, the 121 expected 60-second statistics records, source-lock
and package material, stdout/stderr, validation reports, and other provenance
artifacts. Pinned `writeout_nc.F` contains conditional deflate support only
under the compile-time `NCFPLUS` path and per-variable compression flags; the
available evidence does not prove that path for the pinned executable or a
realized compression ratio. The estimate therefore credits **no compression**.
Gate B must replace every planning allowance with measured native-file and
artifact-class sizes.

### Required native output inventory

Each expected history time must be indexed. Across the native outputs, Gate B
must verify:

```text
coordinates and time
th, prs, tke, km, kh
qv, qc, qr, qi, qs, qg
nci, ncs, ncr, ncg
dbz
u, v, w and requested scalar-interpolated forms
all emitted vorticity components
2-5 km AGL updraft helicity
accumulated surface rain
sws, svs, sps, srs, sgs, sus, shs and translated forms where emitted
statistics, stdout, and stderr
```

For every required field, record exact native name, dimensions, shape, units,
staggering or interpolation status, finite/non-finite/fill counts, and global
range. Missing fields or metadata may not be silently replaced by derived
values. Derived values must be separately named, formula-defined, and linked to
native inputs.

### Predeclared success evidence

Gate B succeeds only if all of the following hold:

1. Provenance and generated-input checks match the pinned identities and exact
   two-line output diff.
2. CM1 exits zero, reports normal completion, reaches 7,200 s, and has no fatal
   runtime-integrity evidence or terminal non-finite required field.
3. All nine expected output times and the required native inventory are present,
   dimensionally coherent, correctly attributed, and finite where physically
   required.
4. The initial output and source audit support the mapped analytic base state,
   quarter-circle wind, flat uniform grid, centered warm bubble, and moving
   frame. Any verification derivation is explicit.
5. Deep precipitating convection forms and remains inspectable through the run,
   with cloud and multiple hydrometeor species, strong signed vertical motion,
   reflectivity, and surface precipitation.
6. The storm develops sustained organized rotation during the mature period,
   supported jointly by structure, vorticity, updraft helicity, and updraft
   evolution rather than one extreme value.
7. The primary storm remains sufficiently separated from open boundaries for a
   defensible interpretation, and upper-damping influence is reported.
8. Actual wall time and storage remain within or reasonably near the declared
   planning envelope and are not disproportionate for one reference Simulation.

Success establishes a trustworthy stock-CM1 mechanics reproduction. It does not
establish publication-grade identity or product approval.

### Predeclared inconclusive evidence

The result is inconclusive, with no tuning or automatic rerun, if CM1 completes
but any of these prevents a faithful interpretation:

- expected fields, units, coordinate metadata, interpolation identity, swaths,
  or output times are absent or ambiguous;
- the moving-frame or ground-relative wind interpretation cannot be verified;
- the storm approaches or crosses an open boundary enough to contaminate the
  mature interval;
- upper damping materially obscures the deep-cloud or updraft-top result;
- output conversion changes scientific values or dimensions unexpectedly;
- rotation or storm organization cannot be judged from the requested native
  evidence even though convection occurs;
- nonfatal numerical warnings or localized non-finite values leave the result's
  integrity genuinely uncertain;
- actual resource cost is high enough that the next action requires a PM tradeoff.

An inconclusive result may justify one separately approved bounded mapping or
output correction. It does not authorize scientific tuning.

### Predeclared rejection evidence

Reject the reproduction path and return to PM/scientific review if:

- any source, executable, official config, generated-input, or launch-time hash
  fails;
- a scientific namelist change or CM1 source modification is required;
- CM1 fails, does not reach 7,200 s, or produces fatal/non-finite required output;
- the exact stock case fails to produce deep precipitating convection over the
  official duration despite clean execution and complete outputs;
- the benchmark cannot be distinguished from boundary or damping artifacts;
- actual local cost is plainly disproportionate for the intended reference role.

### Required Gate B report

The report must contain:

1. all source, executable, config, generated-input, and output hashes;
2. the complete audited namelist diff and external-file inventory;
3. command, process count, timestamps, wall time, peak/available disk evidence,
   and bytes by artifact class;
4. exit status, normal-termination evidence, stderr warnings, and runtime-
   integrity assessment;
5. file/time inventory and per-field dimensions, units, staggering, finite
   counts, and ranges;
6. initial-state checks for grid, model top, sounding, hodograph, frame motion,
   and warm bubble;
7. time-evolution evidence for vertical motion, hydrometeors, reflectivity,
   surface rain, vorticity, updraft helicity, and swaths;
8. structural inspection near 40, 80, and 120 minutes, including boundary and
   damping proximity;
9. an explicit comparison of stock r21.1 behavior with the paper's qualitative
   lineage and an explicit reminder of the microphysics/model differences;
10. one disposition: faithful benchmark reproduced, inconclusive bounded
    correction needed, or benchmark path rejected.

There is one planned full-duration run, no smoke run, no parameter sweep, no
automatic tuning, and no automatic retry. A process or artifact failure ends the
gate and is reported as evidence.

## 11. Limitations and unresolved execution questions

This desk mapping cannot answer:

- the exact native NetCDF variable names, shapes, coordinate attributes, units,
  fill values, or compression under the two approved output changes;
- whether CM1 emits exactly nine history files and all requested swaths in this
  NetCDF/filetype combination;
- the exact initialized CAPE and hodograph diagnostics produced on the active
  scalar and staggered grids;
- whether output winds are unambiguously model-relative or ground-relative in
  every emitted product;
- actual wall time, storage, or memory use for this exact stock field inventory;
- whether the translated domain keeps the preferred storm clear of boundaries
  for the full two hours;
- the strength of upper-Rayleigh influence on the highest storm levels;
- whether the modern Morrison stock case retains the paper's mature
  quarter-circle structure closely enough to serve as a useful mechanics
  reference;
- whether current visualization can present the native hail-treated `qg`, other
  ice species, vorticity, and updraft helicity clearly enough without bounded
  adaptation;
- whether the case will be beautiful, legible, interesting to manipulate, or
  appropriate as a final Cloud World.

The paper's 17.5 km domain, Kessler microphysics, 35 m/s surface-to-6-km shear,
and radiative upper condition differ materially from the stock r21.1 case's
exact 20 km active grid, Morrison scheme, 31.78 m/s source-profile vector
difference, free-slip top, and upper Rayleigh layer. The benchmark's scientific
identity is therefore bounded to "the official r21.1 quarter-circle supercell
case following Weisman and Rotunno (2000)." More expansive wording would
overclaim.

## 12. Final disposition

`advance_to_canonical_benchmark_reproduction`

The stock CM1 r21.1 quarter-circle supercell has recoverable scientific lineage,
exact source/configuration identity, no source-modification requirement, a
complete mapping, bounded Cloud Chamber gaps, and a practical same-size local
cost anchor. The next authorized decision, if separately approved, is only the
single exact Gate B reproduction defined above.
