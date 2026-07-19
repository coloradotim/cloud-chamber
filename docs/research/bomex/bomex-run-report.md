# Canonical BOMEX Baseline Run Report

## Status and Boundaries

This report evaluates `bomex_trade_cumulus_baseline_v0` as Stage 4 scientific
evidence. It does not approve a Cloud World, product Recipe, default case, MVP,
or final application architecture.

The complete source definition and CM1 translation are recorded in
[`bomex-setup-and-cm1-mapping.md`](bomex-setup-and-cm1-mapping.md). The primary
scientific authority is Siebesma et al. (2003), *A Large Eddy Simulation
Intercomparison Study of Shallow Cumulus Convection*:

- DOI: <https://doi.org/10.1175/1520-0469(2003)60%3C1201:ALESIS%3E2.0.CO;2>
- publisher record: <https://journals.ametsoc.org/view/journals/atsc/60/10/1520-0469_2003_60_1201_alesis_2.0.co_2.xml>
- public institutional record: <https://pure.mpg.de/view/item_995314>

## Evidence Chain

| State | Evidence |
| --- | --- |
| Canonical source specification | Steady, nonprecipitating BOMEX LES case; `64 x 64 x 75`, `100 x 100 x 40 m`, six hours, prescribed profiles and forcing from Siebesma et al. Appendix B |
| CM1 translation | CM1 r21.1 analytic BOMEX paths `testcase=3`, `isnd=19`, `iwnd=9`; reversible moist `ptype=6`, zero terminal velocity, periodic lateral boundaries, prescribed fluxes and tendencies |
| Cloud Chamber implementation | Deterministic isolated package generator, duration-only smoke/full variants, pinned provenance, hashes, current local execution, ingest, integrity, diagnostics, and visualization payloads |
| Measured run evidence | One 10-minute smoke run followed by one complete six-hour run; both ingested; all required fields finite; full run carries an underflow-only runtime caveat |
| Interpretation | A recognizable, sustained, low-cover shallow trade-cumulus field formed with published-order cloud structure and locally practical cost |
| Product authority | None; PM review remains required |

## Configuration and Provenance

The executed run manifests recorded app commit
`6808e5f5962bb42b58c450d3e564a4a00f58fdeb`, but package generation occurred
from a dirty worktree containing the then-uncommitted BOMEX implementation.
That commit is the Stage 3 merge base and cannot by itself reproduce these
packages. It is retained here as the original manifest value, not treated as
valid implementation provenance.

The corrected package generator now fails closed unless tracked and untracked
worktree state is clean. Package-only smoke and full variants were regenerated
from clean implementation commit
`84126c75c2db31deb8ba0a3e3bb447a1f94dad27`. Their namelist, profile audit,
runtime checklist, case manifest, and normalized science hashes match the
executed packages byte-for-byte. This clean-commit equivalence establishes
reproducible implementation provenance without repeating either CM1 run.

Both executed and regenerated packages use configured CM1 release `21.1`. All
91 original configured `src/*.F` files matched official NCAR tag `21.1` commit
`0f734f64efa89a684963a66d2ac32db67617912b` byte-for-byte.

| Evidence | SHA-256 |
| --- | --- |
| CM1 source manifest | `fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e` |
| CM1 executable | `5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1` |
| CM1 `README.namelist` | `7b95be56db51f5c9396c59dca252cf96b918a312cc70107451f91149a34ab3b5` |
| Normalized non-duration science settings | `c65b5d4052ff78fe00d447050e2e72a3b62c3a074bee3a17b31cb0a669333e0b` |
| Generated profile audit, both variants | `703cdbd38f9ef13712b86e1cc8d7aa19f40478947325d75b5266fafa94d6f645` |
| Runtime checklist, both variants | `f0967d30d8b26bcc4a9e205a4d658ec7ee3a7d12f6c1a60d3e8dea3f82a8d22d` |
| Smoke namelist | `52435321e13a9a4a53f14a172af942d60a3df3d8679e5bcdcf4aeceecbb929f2` |
| Smoke case manifest | `d206efc5692be15cb277add2a5d2bba0c9ff96897c85314775f15258ad386753` |
| Full namelist | `0928f137668663fec38276ea02dc76b2eb2390b6a8904e409249f113055bc8e2` |
| Full case manifest | `14acd71d736c998e3946c473b7c09c63414a48fdbac3632bbd10c2b20843b5c8` |

The normalized science hash and profile hash are identical. Direct generated
namelist comparison found only `timax=600 s` versus `timax=21600 s`; the output
count changes consequently. The clean regeneration produced no differing
scientific or package artifact hash, so no rerun threshold was triggered. No
observed sounding, sounding candidate, analyzer, `run_recipe`, or warm-bubble
initiation path was used.

## Smoke Gate

| Item | Result |
| --- | --- |
| Run ID | `bomex-370-smoke-20260719` |
| Result ID | `result-bomex-370-smoke-20260719` |
| Duration and cadence | 600 s; 300 s model output; 60 s domain diagnostics |
| Completion | Exit 0; normal CM1 termination; empty stderr |
| Runtime integrity | `trusted`; no warning or fatal flags |
| Output | 3/3 model frames, 11 domain-diagnostic frames, one stats file; 30,264,681 bytes total NetCDF |
| Runtime | 32.15 s wall clock; 31.13 s CM1-reported |
| Ingest and fields | Ingest succeeded; no required fields missing; no non-finite values in required fields |
| Forcing evidence | Surface heat `0.008 K m/s`, moisture `5.2e-5 g/g m/s`, `u*=0.28 m/s`, cooling minimum `-2 K/day`, drying minimum `-1.2e-8 s^-1`, subsidence minimum `-0.006413 m/s`, geostrophic wind and Coriolis diagnostics present |
| Gate disposition | Pass; science run authorized without a post-smoke modeling correction |

The absence of cloud after ten minutes was expected and was not used as science
evidence. The smoke gate established package, forcing, execution, output,
ingest, and numerical integrity only.

## Six-Hour Science Run

| Item | Result |
| --- | --- |
| Run ID | `bomex-370-full-20260719` |
| Result ID | `result-bomex-370-full-20260719` |
| Domain and grid | `6.4 x 6.4 x 3.0 km`; `64 x 64 x 75`; `100 x 100 x 40 m` |
| Time integration | Six hours; 3 s target with adaptive time stepping |
| Output cadence | 300 s model fields and 60 s domain diagnostics |
| Completion and ingest | Exit 0; normal termination; ingest succeeded |
| Output inventory | 73/73 model frames, 361 domain-diagnostic frames, one stats file |
| Runtime | 1,161.81 s wall clock; 1,160.75 s CM1-reported, approximately 19.4 minutes |
| Compute environment | One local CM1 process on Apple M3 hardware with 8 GiB memory |
| Storage | Prelaunch estimate approximately 0.96 GB; actual 1,041,678,203 bytes (1.042 GB, 0.970 GiB), 8.5% above estimate and within the available local space |

## Scientific Recognizability

### Cloud onset and spinup

The first isolated `ql >= 1e-6 kg/kg` cells appeared at 20 minutes. The current
coherent-cloud diagnostic, which requires at least ten qualifying cells,
declared onset at 25 minutes. Siebesma et al. reports first clouds after about
30 minutes. The simulation then produced a startup wave: domain-mean
liquid-water path reached 8.53 g/m2 and total cover 16.28% at 40 minutes, then
fell to 1.18 g/m2 and 9.62% at one hour. This reproduces the published sequence
of a synchronized first cloud wave followed by a roughly one-hour minimum.

### Cloud layer and cover

During the final three hours:

- mean total cloud cover was `10.61%`, with frame means from `8.13%` to
  `13.18%`; the published model means span `8-17%` with a `13%` ensemble mean;
- the evaluator retained the per-level cloud-fraction profile for all 37 frames
  from hour three through hour six, averaged each level across those frames,
  and found the resulting time-mean profile peak at `6.5344%` at `620 m`, close
  to the published approximately `6%` maximum near cloud base; the distinct
  maximum instantaneous per-frame profile peak was `8.9600%`;
- supported cloud base averaged `569 m` and ranged from `540-580 m`, close to
  the published approximately `500 m` cloud base;
- supported cloud top averaged `1,784 m` and ranged from `1,500-2,140 m`.
  Siebesma et al. treats cloud samples above about `2,000 m` as sparse, so the
  highest cells are retained as real output but not treated as a robust mean
  cloud-top target.

### Liquid water and vertical motion

CM1 `cwp` is the scientific liquid-water path for this nonprecipitating
reversible-moist case. Final-three-hour domain-mean LWP was `6.35 g/m2`, ranged
from `1.95-14.16 g/m2`, and had a maximum individual-column value of
`1.492 kg/m2`. The time variation is low and intermittent as in the published
intercomparison; no exact numeric acceptance band was inferred from its plotted
LWP envelope.

The final-three-hour cloud-conditioned vertical velocity was `1.11 m/s` at the
lowest supported 540 m level and peaked at `1.38 m/s` near 1,220 m. Published
cloud-ensemble values are about `0.6 m/s` near base and peak around `1 m/s`, so
the CM1 cloud ensemble is somewhat stronger but of the same order. Raw extrema
of `+8.28` and `-5.23 m/s` are localized grid-cell values and are not compared
with ensemble means.

### Mean thermodynamic structure

The final profile retained a mixed subcloud layer, conditionally unstable cloud
layer, and inversion. From hour three to hour six, the 100-500 m layer warmed at
an extrapolated `1.09-1.25 K/day` and dried at `1.25-1.27 g/kg/day`; these are
the same order as the approximately `1 K/day` and `1 g/kg/day` last-three-hour
tendencies discussed for the intercomparison. At 1,000 m the corresponding
changes were approximately `0.01 K/day` and `-0.44 g/kg/day`. Moistening near
1,500 m reflects turbulent redistribution into the inversion. No mean-profile
collapse or destructive secular drift appeared over six hours.

## Forcing and Process Evidence

The initial and final domain-diagnostic files preserve the intended forcing:

- `thflux=0.008 K m/s`, `qvflux=5.2e-5 g/g m/s`, and `ust=0.28 m/s`;
- `wprof` spans `0` to `-0.006413 m/s`, the discrete-grid representation of
  the `-0.0065 m/s` subsidence knot;
- `ptb_frc` spans `0` to `-2.3148148e-5 K/s`, exactly `-2 K/day`;
- `qvb_frc` spans `0` to `-1.2e-8 s^-1`;
- `ug` spans `-9.964` to `-4.636 m/s` on scalar levels and `vg=0`;
- resolved or SGS turbulent-process diagnostics include `upwp`, `vpwp`,
  `wpwp`, `ufr`, `vfr`, `qvfr`, `ptb_vturbr`, and `qvb_vturbr`.

These fields make surface production, subsidence, prescribed cooling and
drying, geostrophic adjustment, vertical transport, condensation, and cloud
layer evolution observable. They preserve the distinction between configured
forcing, completed CM1 fields, backend-derived diagnostics, and visual
interpretation.

## Repeated Evolution and Watchability

Cloud liquid persisted in 69 of 73 five-minute frames after first appearance.
The domain-mean LWP series contains 12 local growth-decay maxima; 10 retain at
least `1 g/m2` prominence. This includes repeated cycles during the final three
hours, not only the startup wave. Final-three-hour frames contain roughly
1,302-3,260 cloudy grid cells above the threshold.

Current backend visualization machinery exposes:

- a `73 x 75` `ql` time-height cloud-fraction payload with no non-finite cells;
- a 73-point `cwp` domain-mean LWP series;
- domain-mean `th`, `qv`, `u`, and `v` profiles;
- native-grid `ql` slices and thresholded point clouds;
- `w` slices, with signed-flow 3-D rendering explicitly unavailable.

At hours 3, 4.5, and 6, the `ql` point-cloud payload contained 2,761, 1,553, and
2,654 active native-grid points, with changing vertical extents. The preferred
large-result field is now the canonical `ql` cloud-water alias rather than a
zero-rain field. The changing sparse cloud population, vertical growth, and
repeated LWP cycles make the result visually worth watching at five-minute
cadence. This is backend inspection evidence, not approval of a final visual
experience.

## Integrity, Missing Fields, and Potentially Misleading Evidence

All required fields were present and had zero non-finite values. Cloud liquid
(`ql`), vertical velocity, surface fluxes, and rain each had trusted field
quality over all 73 frames. Surface rain remained exactly zero, as required by
the nonprecipitating case. Rainwater and reflectivity are intentionally absent.

The full run emitted only `IEEE_UNDERFLOW_FLAG` on stderr. CM1 reported normal
termination; exit code was zero; no fatal flags, stats-sentinel collapse,
terminal non-finite field, or all-non-finite frame was found. The result is
therefore `caveated`, not `trusted`, under the current runtime-integrity
contract. Underflow-only arithmetic is not evidence of scientific failure, but
the caveat remains visible.

CM1 also emits an `lwp` variable that is hard-zero under `ptype=6` because its
source calculation requires both cloud and rain arrays. It is potentially
misleading and is not used. CM1 `cwp`, which integrates cloud liquid through the
column, is LWP for this no-rain case. The evidence schema, required-field check,
and visualization catalog record this distinction explicitly.

## Departures and Unresolved Uncertainty

- **Canonical-source ambiguity:** no consequential source disagreement was
  found. Intercomparison spread remains the correct comparison basis rather
  than one exact-model target.
- **CM1 representation:** CM1's Deardorff-family closure, adaptive timestep,
  upper 500 m Rayleigh damping, analytic case implementation, and reversible
  all-or-nothing microphysics are explicit model-specific translations.
- **Cloud Chamber implementation:** `ql` is aliased to canonical cloud water;
  cloud fraction uses `ql >= 1e-6 kg/kg`; `cwp` is used as no-rain LWP. These are
  documented diagnostic choices, not changes to the simulated state.
- **Unresolved science:** this is one deterministic realization from one LES
  model. It does not quantify seed sensitivity, model uncertainty, or product
  response to controls. The somewhat stronger cloud-conditioned velocity and
  sparse cells above 2 km should remain visible in later review.

## PM Recommendation

The run reproduces the canonical spinup sequence, final-three-hour cloud-cover
range, near-base cloud-fraction maximum, shallow cloud layer, repeated cloud
growth and decay, and physically defensible mean structure at practical local
cost. Required forcing and process fields are observable, and the remaining
limitations are explicit CM1/diagnostic caveats rather than a failed scientific
question. This supports carrying the evidence into Stage 5 consideration
without approving a Cloud World, Recipe, or product direction.

advance_as_stage5_candidate_evidence
