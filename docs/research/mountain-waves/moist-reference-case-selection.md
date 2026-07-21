# Moist Mountain-Wave Reference Case Selection

Status: source locked for the single process conditionally authorized by issue #407.

This artifact selects one bounded scientific case. It does not define or approve a
Cloud World, Recipe, Control, Lens, Comparison, product surface, or reusable terrain
architecture.

## Decision question

Can CM1 r21.1 reproduce a source-backed, initially clear, two-dimensional
orographic-cloud response in which cloud condensate forms in terrain-forced ascent,
persists as a coherent wave feature, and reduces or evaporates in descending flow,
without cloudy initialization or an invented humidity profile?

## Candidate comparison

The search was deliberately limited to three primary-source cases.

| Candidate | Recoverable setup | Initially clear / zero condensate | Native 2-D | CM1 r21.1 mapping | Disposition |
| --- | --- | --- | --- | --- | --- |
| Toy (2011), 11 January 1972 Boulder windstorm moist mountain-wave experiment | Domain, grid, Agnesi terrain, boundaries, duration checkpoints, nonprecipitating moisture treatment, and the exact upstream observation are recoverable through Toy (2011), Toy and Randall (2009), Toy's 2008 dissertation, Doyle et al. (2000), and the NOAA IGRA observation. | Yes. Toy explicitly states that the horizontally uniform initial atmosphere is unsaturated; NOAA reports a maximum 95% RH in the retained moist profile, and the source experiment adds moisture but no initial cloud. | Yes, `x-z`. | External `input_sounding`, deterministic `itern=4` terrain, and CM1's reversible water-only physics require no source change. | **Selected.** It directly demonstrates layered windward, hydraulic-jump, and lee-wave cloud formation from clear air. |
| Durran and Klemp (1983), observed-moisture Boulder windstorm | Most numerical settings and the observed-moisture result are published. The source reports model clouds similar to observations and no precipitation in the drier observed-moisture case. | Yes for the observed-moisture experiment. | Yes. | Dynamics and warm-cloud physics are representable. | Rejected as the implementation reference because the temperature and wind profiles used by Peltier and Clark are published graphically rather than as an exact numerical ledger. It remains supporting mechanism evidence. |
| Miglietta and Rotunno (2005), moist nearly neutral ridge flow | The idealized ridge and sensitivity family are well documented. | No. The experiment begins saturated and explicitly varies initial cloud water. | Yes. | Representable only by beginning cloudy or by changing the source case. | Rejected because it cannot answer the clear-air-to-cloud decision question. |

Primary references:

- Michael D. Toy, 2011, [Incorporating Condensational Heating into a Nonhydrostatic Atmospheric Model Based on a Hybrid Isentropic-Sigma Vertical Coordinate](https://doi.org/10.1175/MWR-D-10-05015.1), *Monthly Weather Review*, 139, 2940-2954.
- Michael D. Toy and David A. Randall, 2009, [Design of a Nonhydrostatic Atmospheric Model Based on a Generalized Vertical Coordinate](https://doi.org/10.1175/2009MWR2834.1), *Monthly Weather Review*, 137, 2305-2330.
- J. D. Doyle et al., 2000, [An Intercomparison of Model-Predicted Wave Breaking for the 11 January 1972 Boulder Windstorm](https://doi.org/10.1175/1520-0493(2000)128%3C0901:AIOMPW%3E2.0.CO;2), *Monthly Weather Review*, 128, 901-914.
- Dale R. Durran and Joseph B. Klemp, 1983, [A Compressible Model for the Simulation of Moist Mountain Waves](https://doi.org/10.1175/1520-0493(1983)111%3C2341:ACMFTS%3E2.0.CO;2), *Monthly Weather Review*, 111, 2341-2361.
- M. M. Miglietta and R. Rotunno, 2005, [Simulations of Moist Nearly Neutral Flow over a Ridge](https://doi.org/10.1175/JAS3410.1), *Journal of the Atmospheric Sciences*, 62, 1410-1427.

The exact observed profile comes from NOAA NCEI's [IGRA v2.2 period-of-record file for station USM00072476](https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/access/data-por/USM00072476-data.txt.zip), using only the sounding headed `#USM00072476 1972 01 11 12`. The extracted 79-line source record has SHA-256:

```text
33953228bc6bcdf7d65c5cf800b5f8bed9a71aedda910edb4d32a28bef37e652
```

The field interpretation follows NOAA's [IGRA v2.2 sounding-data format](https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/doc/igra2-data-format.txt). The downloaded format document used for this lock has SHA-256:

```text
dfd7b4d2dd18a255477455a7caefd12cb21c30549a1e70cbc3a51db9f41c1dfe
```

The period-of-record zip is updated by NOAA as new soundings arrive, so its whole-file
hash is not the immutable identity. The extracted historical record above is.

## Selected case identity

```text
case_id: cm1_r21_1_toy2011_boulder_moist_wave_4000s_v1
scientific case: Toy (2011) 11 January 1972 Boulder moist mountain-wave experiment
checkpoint: 4000 s
technical purpose: one clear-upstream moist orographic-cloud feasibility run
```

Toy (2011) publishes cloud fields at 1,200, 4,000, and 8,000 s. The selected
4,000-second checkpoint is long enough to include the initial layered windward clouds
and developed downstream wave response while remaining inside the approximately
three-hour window for which Toy's source-backed 25 km-top sensitivity configuration
was reported to agree closely with the 48 km configuration below 25 km.

## Numerical ledger

Every material value below has one classification:

- **direct source**: stated in the primary paper, dissertation, or observation;
- **exact derivation**: calculated without a free parameter from direct-source values;
- **CM1 mapping**: required to express the source case in pinned CM1 r21.1;
- **operational evidence choice**: affects output or evaluation, not the physical case.

### Domain and terrain

| Item | Locked value | Classification and evidence |
| --- | --- | --- |
| Dimensionality | `nx=220`, `ny=1`, `nz=125`; one `x-z` plane | Direct source: Toy (2011) and Toy (2008) specify a two-dimensional experiment; 220 km / 1 km and 25 km / 0.2 km give the exact counts. |
| Horizontal domain | 220 km centered on the ridge; scalar `xh` from -109.5 to +109.5 km | Direct source extent and spacing; CM1 centered-origin mapping with `iorigin=2`. |
| Horizontal spacing | `dx=1000 m`; singleton `dy=1000 m` | Direct source `dx`; `dy` is an inactive singleton-dimension CM1 mapping. |
| Vertical domain | Uniform `dz=200 m`, active top 25,000 m | Direct source sensitivity configuration: 125 levels in the lowest 25 km; Toy (2008) reports nearly identical sub-25-km results with the top at 25 km for the experiment period. |
| Timestep | Fixed `dtl=2 s` | CM1 mapping: the pinned official `nh_mountain_waves` case uses 2 s with the same 200 m vertical spacing and vertically implicit acoustic solver. It is not a claim about Toy's model timestep. |
| Duration | `timax=4000 s` | Direct source checkpoint in Toy (2011) Fig. 1a. |
| Terrain | `z_s(x)=2000/[1+((x-500)/10000)^2]` m | Direct source height 2 km, half-width 10 km, and witch-of-Agnesi form. The +500 m center is the CM1 half-cell mapping that places the continuous ridge crest on one centered scalar point. |
| Terrain implementation | `itern=4`, one little-endian IEEE-754 float32 direct-access record, shape `(ny,nx)` with `x` fastest | CM1 mapping from r21.1 `src/init_terrain.F`; generated `perts.dat` remains runtime-only and is hash/readback audited. |
| Maximum analytic slope | `0.1299038106` | Exact derivation from the Agnesi curve: `9 h/(8 sqrt(3) a)`. |
| Crest grid compression | bottom-layer thickness at the 2 km crest is 92% of the flat value, or 184 m | Exact derivation from CM1's Gal-Chen transform: `(ztop-h)/ztop`. No undocumented CM1 slope tolerance is asserted. |

### Initial atmosphere

The model reference surface is the observed 850 hPa level at 1,514 m MSL, mapped to
`z=0`, following Toy's stated 850 hPa reference pressure. Pressure-level records from
850 through 17 hPa are retained; the last row maps to 25,846 m and therefore satisfies
CM1's requirement that the final sounding row exceed the 25 km model top.

| Item | Locked construction | Classification and evidence |
| --- | --- | --- |
| Pressure / height | Reported IGRA pressure and geopotential height; model height is `reported_height - 1514 m` | Direct observation plus exact offset. |
| Temperature | Reported IGRA temperature in tenths C, converted by `T_K=T_C+273.15` | Direct observation plus exact unit conversion. |
| Potential temperature | `theta=T_K*(100000/p)^(Rd/Cp)` with CM1 constants `Rd=287.04`, `Cp=1004 J kg-1 K-1` | Exact derivation and CM1 input mapping. |
| Water vapor where RH is reported | `qv=RH*0.622*es(T)/(p-es(T))`, using CM1 r21.1's Bolton liquid saturation formula | Direct observed RH plus exact CM1-compatible derivation. |
| Water vapor where RH is absent | Input `qv=0`; r21.1 replaces values below `1e-12 kg/kg` with 0.01% liquid RH during `isnd=7` initialization | Required CM1 mapping, explicitly audited. It does not create condensate. |
| Wind | Cross-ridge `u=-speed*sin(direction)` from reported meteorological direction and speed; `v=0` | Exact derivation of the observed eastward component; direct 2-D mapping. |
| Surface state | `p=850 hPa`; `T=272.55 K`; `theta=285.5125 K`; `qv=1.767594 g/kg`; `u=-4.2858 m/s` | Direct 850 hPa observation plus exact conversions. The weak easterly first level is retained rather than tuned away. |
| Maximum source RH | 95% at reported 544 hPa / model 3,438 m | Direct observation. The source-backed minimum unsaturated margin is 5 percentage points. |
| Initial condensate | `ql=0` everywhere; no `qc`, `qr`, `qi`, `qs`, or `qg` category exists in the chosen two-variable scheme | Direct source intent and CM1 `isnd=7` / `ptype=6` mapping. Any positive initial `ql` blocks acceptance. |
| Stability | Whatever follows from the retained observed `theta(z)` profile after r21.1 hydrostatic interpolation | Direct observation and exact CM1 behavior; no analytic stability is substituted. |

CM1 r21.1 reads the generated external sounding as:

```text
surface pressure (mb), surface theta (K), surface qv (g/kg)
z (m), theta (K), qv (g/kg), u (m/s), v (m/s)
```

It linearly interpolates wind to staggered physical heights. For thermodynamics, it
constructs hydrostatic pressure, converts the supplied `qv` rows to RH, linearly
interpolates `theta` and RH to each column's terrain-aware physical scalar heights,
then reconstructs hydrostatic pressure and `qv`. Package audit records every emitted
row and verifies finite values, strict height ordering, final height above the active
top, exact source-record identity, and a maximum source RH of 95%.

### Moist physics

| Setting | Locked value | Classification and evidence |
| --- | --- | --- |
| Moist equations | `imoist=1`, `eqtset=2` | Required CM1 mapping; equation set 2 conserves moist mass and energy including hydrometeor heat capacity. |
| Microphysics | `ptype=6`, Rotunno-Emanuel water-only with `qv` and `ql` | Required CM1 mapping to Toy's nonprecipitating vapor/cloud-water treatment. |
| Liquid fall speed | `v_t=0 m/s`; `efall=0` | Required CM1 mapping for reversible, nonprecipitating condensate with conserved total water. |
| Saturation adjustment | Active r21.1 `satadj` for `ptype=6` | Required CM1 behavior; latent heating accompanies conversion between `qv` and `ql`. |
| Precipitation and ice | Absent | Direct source behavior for this experiment. No rain, ice, snow, graupel, reflectivity, or lookup table is added. |
| Runtime files | `input_sounding` and `perts.dat` only, in addition to `namelist.input` | Exact consumed-file mapping. No `LANDUSE.TBL`, radiation table, aerosol table, or surface file is consumed. |

### Boundaries, damping, and diffusion

| Item | Locked value | Classification and evidence |
| --- | --- | --- |
| West/east | `wbc=ebc=1`, periodic | Direct source. The upstream-sector test therefore concerns the clear source region, not an open-boundary inflow. |
| South/north | `sbc=nbc=1`, periodic singleton `y` | Required 2-D CM1 mapping. |
| Bottom / top | `bbc=tbc=1`, free slip; terrain impermeability remains active | Direct source free-slip lower boundary and rigid lid; CM1 mapping. |
| Inflow nudging / mass limiter | `nudgeobc=0`, `roflux=0`, `apmasscon=0` | Direct/CM1 mapping; these open-boundary mechanisms are inapplicable to the periodic domain. |
| Rayleigh damping | `irdamp=0`, `hrdamp=0` | Direct source 25 km-top sensitivity configuration: no absorbing layer. Top evidence remains an explicit acceptance check. |
| Rotation / large-scale pressure gradient | `icor=0`, `lspgrad=0` | Direct source: no rotation. |
| Turbulence | `cm1setup=1`, `sgsmodel=2`, `tconfig=2`, no PBL or surface fluxes | CM1 mapping to the source's modified Smagorinsky first-order closure. CM1's closure is not numerically identical and is disclosed below. |
| Advection / pressure solver | Pinned official mountain-wave defaults: fifth-order scalar/velocity advection and `psolver=3` | CM1 mapping. These are implementation numerics, not claimed source equivalence. |
| Initial perturbation | `iinit=0`, `irandp=0` | Direct source mechanism: terrain interacting with the horizontally uniform sounding is the forcing. |

### Output and evidence lock

| Item | Locked value | Classification and rationale |
| --- | --- | --- |
| Native history | NetCDF, one file per time, `output_format=2`, `output_filetype=2`, no nominal-height interpolation | Operational evidence choice required for native terrain-aware evaluation. |
| Cadence | 200 s from 0 through 4,000 s inclusive; 21 expected histories | Operational evidence choice. It resolves the published 1,200 and 4,000 s checkpoints and provides repeated formation/evaporation evidence. |
| Required fields | `zs`, `zhval`, `th`, `prs`, `qv`, `ql`, scalar-interpolated and native `u/v/w`, plus available SGS diagnostics and CM1 stats/logs | Operational evidence choice tied to the predeclared questions. |
| Numerical clear floor | `ql <= 1e-12 kg/kg` at initial time | CM1 mapping to the scheme's small-value scale; any larger initial value is recorded and blocks a clear initialization finding. |
| Interpretable cloud floor | `ql >= 1e-6 kg/kg` (0.001 g/kg) | Case-specific operational evidence choice, ten million times the numerical floor and equal to Cloud Chamber's existing explicit cloud-water visibility floor. It is not a universal cloud definition. |
| Material peak check | `max(ql) >= 2e-4 kg/kg` (0.2 g/kg) | Case-specific primary-source check: Durran and Klemp's observed-moisture Boulder figure distinguishes cloud water above 0.2 g/kg. It supplements, rather than replaces, the lower formation floor. |
| Coherence | At least one four-neighbor-connected `x-z` component of 8 cells at or above the interpretable floor | Operational evidence choice that excludes isolated pixels at this exact 1 km by 0.2 km grid. |
| Persistence | A coherent component at or above the floor at 3 consecutive saved times (at least 400 s from first to third frame) | Operational evidence choice. It rejects a one-frame transient without making a universal lifetime claim. |
| Interior formation region | `-40 <= x <= 60 km`, below 12 km MSL-equivalent model height | Operational region centered on the 0.5 km crest and covering the source-described windward, jump, and lee-wave cloud response. |
| Upstream clear sector | `-100 <= x <= -60 km`, below 12 km | Operational contamination check far upstream of the ridge and away from the periodic seam. |
| Edge sectors | outermost 10 km on each side | Operational periodic-seam contamination check. |

Relative humidity is recomputed from native `qv`, `prs`, and temperature derived from
native `th` and `prs`, using the same Bolton liquid-saturation formula as r21.1.
Physical heights come from native `zhval`; `zs` and the final `zf` coordinate independently
check terrain and active-top integrity.

## Predeclared criteria

### Successful feasibility evidence

All of the following are required:

1. CM1 exits zero, reports normal completion, and emits all 21 exact times with finite required fields.
2. Native terrain matches the generated Agnesi record, physical heights are monotonic, and the active top is 25 km.
3. Initial `ql` is at or below `1e-12 kg/kg` everywhere; the initial and upstream source sectors are below the interpretable cloud floor.
4. The first `ql >= 1e-6 kg/kg` occurs in the interior region, not an edge sector, and is colocated with positive terrain-forced `w` and RH approaching or reaching one.
5. At least one 8-cell connected cloud component persists for three consecutive histories and the run reaches the 0.2 g/kg material-peak check.
6. A cloud-bearing ascent phase is followed spatially or temporally by a contiguous descending phase in which RH falls below saturation and `ql` falls below the interpretable floor. The evaluator must retain the numeric profiles; a label alone is insufficient.
7. The dominant cloud response remains organized relative to the ridge and wave pattern rather than appearing as a boundary-originating translated patch.
8. Wave structure remains interpretable after latent heating; edge, periodic seam, top, and startup evidence do not compromise the central result.
9. Native geometry and cloud fields are sufficient for honest terrain-aware inspection, and measured runtime/storage remain practical on the local machine.
10. Runtime-only visual review shows a legible cloud response with potential experiential value.

### Inconclusive evidence

The result is inconclusive if required fields/times are absent, source and runtime RH
contradict, condensate remains between numerical and interpretable floors, cadence
cannot establish persistence or evaporation, edge/top/startup effects overlap the
central interpretation, or evaluator and source behavior disagree.

### Rejection evidence

Reject or defer if the run starts cloudy, forms cloud first at a periodic edge, never
forms a coherent interior cloud, does not reach a materially legible condensate scale,
cannot show a descent/evaporation phase, becomes numerically unstable, loses terrain
or coordinate integrity, or costs disproportionately more than the evidence is worth.

## Source-to-CM1 differences

| Source behavior | CM1 implementation | Reason | Expected consequence | Acceptable for this gate? |
| --- | --- | --- | --- | --- |
| Toy compares hybrid-isentropic and terrain-following sigma coordinates. | CM1 uses its Gal-Chen terrain-following coordinate. | Pinned r21.1 capability; the source explicitly includes the sigma-coordinate comparison. | Moisture transport details may differ, but clear-air formation and terrain-wave organization remain directly testable. | Yes. |
| Main published run has a 48 km top and 205 levels, stretched above 35 km. | Source-supported sensitivity configuration uses a 25 km top and 125 uniform 200 m levels. | Exact high-level stretching is not numerically published; Toy (2008) reports nearly identical below-25-km results over the experiment period with the 25 km top. | Greater risk of top reflection, explicitly evaluated; much lower local cost. | Yes, only if top evidence remains separated from cloud interpretation. |
| Source model uses a modified Smagorinsky closure with Richardson dependence. | CM1 `cm1setup=1`, `sgsmodel=2`, `tconfig=2`. | Closest source-faithful built-in closure without source modification. | Turbulent mixing magnitudes are not expected to match pointwise; early laminar cloud formation and gross wave locking remain assessable. | Yes for feasibility, not quantitative validation. |
| Source uses a reversible, nonprecipitating condensation treatment. | CM1 `ptype=6`, `v_t=0`, saturation adjustment, `qv+ql`. | Simplest built-in water-only reversible treatment. | Condensation/evaporation and latent heating are represented; no rain or ice can obscure the mechanism. | Yes. |
| Source paper inherits its processed sounding from earlier work. | Package uses the exact NOAA IGRA observation identified by station/time and deterministic conversions. | Supplies an auditable numerical profile instead of digitizing a figure. | Minor processing differences from the authors' private/intercomparison profile may alter detailed wave amplitude; the reported layers, clear RH margin, and source identity are preserved. | Yes for feasibility; disclose in result interpretation. |
| Source ridge is centered continuously. | Ridge center is +0.5 grid cell so one scalar point samples the exact 2 km crest. | Required discrete-grid mapping. | Only a half-cell coordinate-origin shift in a periodic domain. | Yes. |
| Toy's timestep is not published as a transferable CM1 value. | `dtl=2 s`, the pinned official CM1 mountain-wave value for 200 m vertical spacing. | Required CM1 numerical mapping. | Affects cost and numerical integration, not the specified atmospheric state. | Yes if CFL/runtime diagnostics are clean. |
| Paper figures are sparse in time. | Native output every 200 s. | Required persistence, formation, and evaporation evidence. | More storage only; no physical tendency changes. | Yes. |
| Source renderer/coordinate plots are not Cloud Chamber contracts. | Runtime-only terrain-aware cross sections use native `zs`, `zhval`, `ql`, `qv`, `w`, and `th`. | Required review evidence. | No model consequence and no frontend/product implication. | Yes. |

No material difference is intentionally left undocumented. If implementation or CM1
startup reveals another active difference, execution is blocked rather than silently
accepting it.

## Conditional execution gate

The one process authorized by issue #407 may start only after:

- this artifact and the complete package/evaluator implementation are committed;
- focused tests and `scripts/check.sh` pass;
- the worktree is clean at that exact implementation commit;
- the pinned CM1 r21.1 source, executable, documentation, critical-source hashes, and NetCDF linkage match Gate B provenance;
- generated sounding and terrain hashes/readback audits pass;
- the complete namelist audit contains only the locked differences above;
- the consumed runtime-file checklist contains exactly `input_sounding` and `perts.dat`;
- expected histories, output size, and twice-required free space pass;
- no CM1/MPI process is active;
- the target contains no output-like file; and
- no prior execution exists for this technical case identity.

The authorization remains exactly one full 4,000-second process: no smoke, tuning,
retry, alternate executable, LAN worker, or second process.
