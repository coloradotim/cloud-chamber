# BOMEX Setup and CM1 Mapping

## Status and Scope

This document records the pre-implementation mapping for
`bomex_trade_cumulus_baseline_v0`. The identifier is a provisional Stage 4
technical identifier, not an approved Cloud World or product Recipe.

Mapping gate disposition: **pass**. Every material component of the canonical,
steady, nonprecipitating BOMEX LES case is represented by direct CM1 r21.1
configuration or an existing case-specific source capability. No CM1 source
customization or generalized forcing infrastructure is required.

## Scientific Authority

The controlling scientific source is Siebesma et al. (2003), *A Large Eddy
Simulation Intercomparison Study of Shallow Cumulus Convection*, Journal of the
Atmospheric Sciences 60, 1201-1219:

- DOI: <https://doi.org/10.1175/1520-0469(2003)60%3C1201:ALESIS%3E2.0.CO;2>
- publisher record: <https://journals.ametsoc.org/view/journals/atsc/60/10/1520-0469_2003_60_1201_alesis_2.0.co_2.xml>
- public institutional record: <https://pure.mpg.de/view/item_995314>

Appendix B supplies the domain, initial profiles, forcing profiles, surface
fluxes, geostrophic wind, Coriolis parameter, perturbations, and six-hour
duration. Appendix A identifies all-or-nothing condensation as the prevalent
grid-cell condensation treatment in the intercomparison.

CM1 implementation authority is the configured CM1 r21.1 source and
documentation, cross-checked against NCAR's `21.1` tag at commit
`0f734f64efa89a684963a66d2ac32db67617912b`:

- CM1: <https://www.mmm.ucar.edu/models/cm1>
- source tag: <https://github.com/NCAR/CM1/tree/21.1>
- namelist documentation: <https://cm1.readthedocs.io/en/latest/README.namelist/>

## Configured CM1 Provenance

The exact absolute local paths remain in generated runtime-only package
metadata and are omitted here under the repository's machine-private-path
restriction.

| Evidence | Configured value |
| --- | --- |
| Source tree | `cm1_root` from runtime `settings.json`; final component `cm1r21.1` |
| Run directory | `cm1_run_dir` from runtime `settings.json` |
| Release evidence | source `README.md`: `CM1 Numerical Model, Release 21.1`, 24 March 2024 |
| Source-control alignment | all 91 local original `src/*.F` files byte-match NCAR tag `21.1` |
| Source manifest method | SHA-256 each sorted original `src/*.F`, then SHA-256 the newline-delimited manifest |
| Source manifest SHA-256 | `fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e` |
| `README.namelist` SHA-256 | `7b95be56db51f5c9396c59dca252cf96b918a312cc70107451f91149a34ab3b5` |
| Configured `cm1.exe` SHA-256 | `5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1` |
| Bundled BOMEX namelist SHA-256 | `4aa2f7cfad8c918801e0768c2618a37740e3966bc8f47205e5fafda3e506f965` |
| Bundled BOMEX README SHA-256 | `368c6ca53445f920f0e89d6e4273111f0378785e393e1efa63a7758f2dc5ae56` |

Directly relevant source hashes:

| Source file | SHA-256 |
| --- | --- |
| `src/base.F` | `9c88a1021ddde22d02680786246c52bcffb040cbd72c3c4708f24fe24eec32ef` |
| `src/init3d.F` | `9c45c0982ba194ea6ea74afd6a2516445cdd011fc90902091d089f4cb92dfd28` |
| `src/sfcphys.F` | `7cb54de579b8bb038285430890e075ab19ed2e6d93158bd50d656209d64696a7` |
| `src/testcase_simple_phys.F` | `ce0a74ba558634cf712669aae3cbee2eafeb4e23a116e0fe3d819886938ffc72` |
| `src/adv_routines.F` | `265723c8b19e300592ddbad3839ee689aa4933ac2f0ae236c61f4d5d40ef7f00` |
| `src/solve1.F` | `515346f18268aea39e7a919536ee6187386e5db6d184e6e4c597509c701e2076` |
| `src/param.F` | `cac64a6cb4363c6b88367b5cb9391f1bcf2130c63ffedef6e5973c03b190c349` |
| `src/domaindiag.F` | `a926b4938c6b576e2ec634c14dbf177f8bdcc557ddefa3b8155326e5f8ef7dff` |
| `src/mp_driver.F` | recorded in generated package metadata |
| `src/kessler.F` | recorded in generated package metadata |

The local build Makefile differs from the release tag only for local NetCDF
build configuration. The scientific Fortran sources above match the official
tag byte-for-byte. Package generation rechecks all pinned evidence and fails
closed on a mismatch.

## Source-to-CM1 Mapping

The scientific-source column refers to Siebesma et al. Appendix B unless a CM1
source file is named explicitly.

| Component | Scientific source and exact value or formula | CM1 representation | Classification | Approximation or uncertainty | Verification method |
| --- | --- | --- | --- | --- | --- |
| Liquid-water potential temperature | `theta_l=298.7 K` at 0 and 520 m; `302.4 K` at 1480 m; `308.2 K` at 2000 m; `311.85 K` at 3000 m; linear interpolation | `isnd=19`; exact knots and interpolation in `src/base.F` | existing CM1 source capability | CM1 initializes its prognostic thermodynamic variables from the analytic profile | Source review, startup diagnostics, and initial domain-mean profile |
| Total water | `q_t=17.0 g/kg` at 0 m, `16.3` at 520 m, `10.7` at 1480 m, `4.2` at 2000 m, `3.0` at 3000 m; linear interpolation | `isnd=19`; exact knots in `src/base.F` | existing CM1 source capability | Initial cloud liquid is zero, so initialized vapor is equivalent to total water | Source review and initial `qv` profile |
| Wind | `u=-8.75 m/s` through 700 m, then linear to `-4.61 m/s` at 3000 m; `v=0` | `iwnd=9` in `src/base.F` | existing CM1 source capability | None material | Source review and initial `u`, `v` profiles |
| Surface sensible heat flux | `8.0e-3 K m/s` | `set_flx=1`, `cnst_shflx=8.0e-3` | direct namelist support | Kinematic flux, as specified by the case | Namelist review and `thflux`/`hfx` output |
| Surface moisture flux | `5.2e-5 m/s` in specific-humidity units | `set_flx=1`, `cnst_lhflx=5.2e-5` | direct namelist support | CM1 documents units as `g/g m/s`, numerically equivalent | Namelist review and `qvflux`/`qfx` output |
| Momentum | Friction velocity `u*=0.28 m/s`; stress aligned against low-level wind | `set_ust=1`, `cnst_ust=0.28`, `bbc=3`; BOMEX `testcase=3` surface logic | existing CM1 source capability | CM1 applies the case-specific vector stress formula in `src/sfcphys.F` | Source review and `ust`, stress diagnostics |
| Subsidence | `w_ls=0` at 0 m, `-0.0065 m/s` at 1500 m, `0` at 2100 m; piecewise linear | `testcase=3` builds `wprof`; large-scale vertical advection is active | existing CM1 source capability | None material | Source review and domain diagnostic `wprof` |
| Thermodynamic advection | All large-scale thermodynamic advection other than specified subsidence and radiation is zero | No added horizontal thermodynamic-advection tendency | existing CM1 source capability | Subsidence acts through CM1's large-scale vertical-advection path | Source review and tendency diagnostics |
| Moisture advection | `dq_t/dt=-1.2e-8 s^-1` through 300 m, linearly to zero at 500 m | `testcase=3` `qvfrc` profile | existing CM1 source capability | Applied to vapor; with reversible condensation, this is the CM1 translation of total-water drying | Source review and `qvb_frc` diagnostic |
| Radiation | `-2 K/day` through 1500 m, linearly to zero at 2100 m | `testcase=3` `thfrc` profile with `radopt=0` | existing CM1 source capability | Prescribed tendency, not interactive radiative transfer | Source review and `ptb_frc` diagnostic |
| Coriolis and pressure gradient | `f=0.376e-4 s^-1`; `u_g=-10+1.8e-3 z m/s`, `v_g=0` | `icor=1`, `lspgrad=2`, `fcor=0.376e-4`; `testcase=3` geostrophic profile | existing CM1 source capability | None material | Namelist/source review and `ug`, `vg`, momentum diagnostics |
| Lateral boundaries | Doubly periodic LES domain | `wbc=ebc=sbc=nbc=1` | direct namelist support | None | Namelist review |
| Upper boundary and damping | Rigid LES top; canonical source does not prescribe implementation-specific damping | `tbc=1` free-slip; `irdamp=1`, `zd=2500 m`, `rdalpha=1/300 s^-1` in top 500 m | direct namelist support | CM1-specific numerical treatment inherited from the authoritative bundled BOMEX case | Namelist review; verify damping remains above half-domain preflight limit |
| Turbulence closure | Prognostic 1.5-order TKE is within the intercomparison family; initial TKE `1-z/3000 m2/s2` | `sgsmodel=1`, `tconfig=1`, `testcase=3` TKE initialization | existing CM1 source capability | CM1's Deardorff-family implementation is one valid intercomparison-style closure, not a claim of model identity | Namelist/source review and `tke`, `km`, `kh` outputs |
| Cloud microphysics | Steady nonprecipitating case; Appendix A describes all-or-nothing condensation | `ptype=6`, `v_t=0`: CM1 source labels this reversible moist thermodynamics; only `qv` and `ql` are prognosed and zero fall speed makes fallout zero | direct namelist support | Deliberate correction to the bundled example's `ptype=5`; that example's `iautoc=0` does not disable Morrison precipitation | Source review, generated namelist assertion, `ql` availability, zero rain/fallout evidence |
| Initial perturbations | Random `theta` amplitude +/-0.1 K and moisture amplitude +/-0.025 g/kg in lowest 40 levels | `iinit=0`, `irandp=1`; `testcase=3` deterministic default random seed and exact amplitudes in `src/init3d.F` | existing CM1 source capability | Deterministic for the pinned executable/source | Source review and repeatable input hashes/startup output |
| Domain | `64 x 64 x 75` points; `6.4 x 6.4 x 3.0 km` | `nx=64`, `ny=64`, `nz=75` | direct namelist support | None | Namelist review and NetCDF dimensions |
| Grid | `dx=dy=100 m`, `dz=40 m`, uniform | `dx=100`, `dy=100`, `dz=40`, all stretch flags zero, `ztop=3000` | direct namelist support | None | Namelist review and NetCDF coordinates |
| Time step | Intercomparison time steps varied by model | `dtl=3 s`, `adapt_dt=1`, matching bundled CM1 BOMEX case | direct namelist support | Model-specific adaptive strategy; three seconds is a target, not a scientific source value | Startup/output log review and numerical-integrity checks |
| Smoke duration | Operational gate only | `timax=600 s` | direct namelist support | Duration-only variant; not science evidence | Smoke/full configuration comparison |
| Full duration | Six hours | `timax=21600 s` | direct namelist support | None | Manifest, namelist, output endpoint |
| Output cadence | Must support repeated evolution inspection | Three-dimensional output every `300 s`; domain diagnostics every `60 s` | direct namelist support | Five-minute 3-D cadence is a watchability/storage tradeoff, not canonical science | Output count, time coordinates, storage estimate versus actual |
| Required fields | Cloud liquid, vapor, thermodynamics, motion, pressure, surface fluxes, cloud fraction, liquid-water path, profiles, turbulent fluxes, cloud bounds, and integrity | NetCDF `ql`, `qv`, `th`, `prs`, `u`, `v`, `w`, `tke`, `km`, `kh`, `cwp`, surface fields, plus domain diagnostics including forcing and resolved flux profiles | direct namelist support | `ql` is mapped to Cloud Chamber's canonical cloud-liquid `qc` diagnostic alias. Under `ptype=6`, CM1's `cwp` is cloud liquid integrated through the column and therefore the scientific liquid-water path; CM1's emitted `lwp` is hard-zero because its source calculation requires rain allocation. Radiative-scheme `cldfra` is not used because `radopt=0`. | Automated switch tests, ingest field catalog, BOMEX evidence calculation, non-finite scan |

## Explicit Approximations and Limitations

1. CM1's case-specific analytic `isnd=19`, `iwnd=9`, and `testcase=3` code is
   used instead of external sounding and forcing files. A generated profile
   audit file records the canonical knots but is not consumed by CM1.
2. The prescribed `-2 K/day` tendency is implemented by CM1's BOMEX idealized
   forcing path, not an interactive radiation scheme.
3. Upper Rayleigh damping is a CM1 numerical treatment inherited from the
   bundled case, not a published BOMEX physical forcing.
4. Cloud fraction is derived from grid-cell `ql >= 1e-6 kg/kg`; it is not the
   inactive radiation scheme's `cldfra` field.
5. Five-minute 3-D output is selected to expose repeated cloud growth and decay
   while keeping the projected local output below available storage. The smoke
   run will supply an empirical bytes-per-frame estimate before the six-hour
   launch.
6. For reversible nonprecipitating `ptype=6`, CM1's `cwp` output is used as
   liquid-water path. The separately emitted `lwp` field is unavailable as
   scientific evidence because CM1 only accumulates it when both cloud and rain
   arrays are allocated.

These translations preserve the canonical BOMEX question. They do not approve
the case as a product Recipe or establish a generalized forcing architecture.
