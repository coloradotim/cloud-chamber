# Deep Convection Package Design

Issue: #260

Status: research design, not an implementation contract

This document designs the first Cloud Chamber package family for testing deep
convection from an observed sounding. It is PM/science input for a future
implementation issue. It does not change package generation, UI, candidate
screening, or CM1 execution.

## Product Question

Given an observed sounding, what controlled CM1 experiment should Cloud
Chamber run to test whether the environment can produce deep convection?

The answer is not "run the sounding exactly as observed." A one-dimensional
profile can contain moisture, instability, and shear while still needing a
localized initiating perturbation, boundary, or forcing mechanism to produce
convective clouds in a finite CM1 domain.

## Recommendation

Recommended v1 user-facing package name:

```text
Deep Convection Trial
```

Recommended internal package family:

```text
package_family = deep_convection_trial
```

Recommended v1 design:

```text
Observed sounding + observed winds + warm thermal trigger
```

This is an idealized CM1 experiment for learning and exploration. It tests what
happens when this observed sounding is given a simple trigger.

```text
Find an interesting real sounding
-> choose Deep Convection Trial
-> run an idealized triggered CM1 experiment
-> inspect what happened
-> learn from the mismatch between the sounding hypothesis and model outcome
```

Why this path first:

- CM1 already has warm thermal initialization options (`iinit = 1` warm bubble
  and `iinit = 8` warm line thermal with small random perturbations).
- CM1 already has examples that combine idealized deep convection with
  Morrison microphysics, surface rain, and reflectivity output.
- Cloud Chamber already has an observed-sounding path that writes
  `input_sounding` and uses `isnd = 7`.
- `isnd = 7` reads wind from `input_sounding`; `iwnd` is ignored.
- A warm thermal trigger is easier to explain and validate than convergence forcing,
  cold-pool insertion, or radiation-driven diurnal initiation.

Implementation note from #261: stock CM1 r21.1 does not expose the `iinit = 1`
warm-bubble geometry/amplitude as namelist-tunable fields. The first Cloud
Chamber implementation uses CM1's built-in `iinit = 8` warm line thermal because
it is a stronger supported trigger without requiring Fortran edits.

## PM Decisions For V1 Implementation

These are the product/science decisions for the implementation issue:

- **Deep Convection Trial is a first-class package option in Build** after a
  user selects or uploads an observed sounding, or chooses a saved sounding
  candidate.
- **For deep-convection candidate stories, Deep Convection Trial is the
  recommended/default package option.** The current shallow observed-sounding
  quick look can remain available, but it is not the main path for
  severe/deep-convection candidates.
- **Quick Look should be small enough to try locally when possible.** It is a
  fast experiment to see whether the package runs, initiates, and produces
  interpretable output.
- **Standard and Deep tiers should clearly recommend the LAN worker.** Those
  tiers are where wider domains, longer runtime, and denser output become more
  useful.
- **The warm thermal trigger should be visible to the user** as the initiation
  method. Users should know they are asking CM1 to try an idealized triggered
  experiment.
- **Exact numeric trigger parameters can remain package metadata in v1.**
  Do not expose raw trigger controls until useful ranges are validated and
  namelist/source-code support is explicit.
- **Manual QA is for package health, tuning, domain/runtime calibration, and
  result interpretability.** It is not a gate on whether severe/deep-convection
  soundings are allowed to use this package.

## Confirmed Facts

Confirmed from local CM1 `README.namelist` and example configuration files:

- `isnd = 7` reads the external `input_sounding` file.
- With `isnd = 7`, CM1 also obtains the wind profile from `input_sounding`;
  `iwnd` is ignored.
- `iinit = 1` is a warm bubble.
- `iinit = 2` is a cold pool.
- `iinit = 8` is a line thermal with random perturbations.
- `iinit = 9` is forced convergence.
- `iinit = 10` is momentum forcing.
- The stock CM1 `supercell` example uses `testcase = 0`, `iinit = 1`,
  `ptype = 5`, `output_rain = 1`, and `output_dbz = 1`.
- `output_dbz` is available for Morrison microphysics (`ptype = 5`) and also
  outputs composite reflectivity.
- CM1 exposes severe-relevant swath/cold-pool diagnostics such as surface
  rainfall, surface wind swath, low-level pressure perturbation swath, maximum
  rainwater at the lowest model level, maximum w at 5 km AGL, updraft helicity
  swath, and cold-pool intensity/depth when the corresponding outputs are
  enabled.

Confirmed Cloud Chamber support today:

- Cloud Chamber can ingest an extracted IGRA station text file.
- Cloud Chamber can write thermodynamic, moisture, and wind profiles into
  `input_sounding`.
- Cloud Chamber observed-sounding packages use `isnd = 7`.
- Current observed-sounding packages are still shallow-LES oriented. They are
  not deep-convection packages.

## V1 Package Definition

Recommended stable metadata:

```json
{
  "package_family": "deep_convection_trial",
  "input_source": "observed_sounding",
  "specialized_package_for": "severe/deep_convection",
  "trigger_type": "warm_thermal_line",
  "candidate_screening_hypothesis": {},
  "limitations": [],
  "expected_outputs": [],
  "expected_diagnostics": []
}
```

Recommended Build copy:

```text
Deep Convection Trial
Try this observed sounding with an idealized warm thermal trigger and see
whether deep convection develops.
```

Recommended limitations:

- The warm thermal is an idealized trigger, not an observed storm initiation
  mechanism.
- It can over-trigger marginal environments.
- V1 does not represent surface heating/radiation, boundaries, terrain,
  land-surface heterogeneity, or mesoscale lift.
- Storm structure is something to inspect after the run, not something assumed
  from the sounding label.
- A failed run can mean the environment, trigger, domain, resolution, runtime,
  or physics configuration was not sufficient. It is not automatically proof
  that the sounding could not convect.

## Initiation Options Compared

### Warm Line-Thermal Trigger

Decision for v1: use this.

Likely CM1 settings:

```text
testcase = 0
isnd = 7
iwnd = 0 or ignored by CM1 because isnd = 7
iinit = 8
irandp = 0 initially
```

Pros:

- Strong idealized deep-convection trigger available in stock CM1.
- Confirmed CM1 option.
- Easy to explain to users.
- Easy to verify in generated namelist tests.
- Minimal new generated files beyond `input_sounding`.
- Fits current observed-sounding package architecture.
- Does not require Cloud Chamber to edit CM1 Fortran source.

Cons:

- Artificial.
- May initiate storms in marginal environments that would need a real boundary
  or stronger forcing.
- Does not represent a front, dryline, outflow boundary, or terrain effect.
- Stock CM1 line-thermal geometry/strength are source-code behavior rather
  than Cloud Chamber product controls in v1.

V1 trigger metadata should include:

```json
{
  "trigger_type": "warm_thermal_line",
  "trigger_parameters": {
    "cm1_iinit": 8,
    "cm1_trigger": "CM1 built-in line thermal with small random perturbations",
    "raw_controls_exposed": false
  }
}
```

Future work can add a custom warm-bubble or point-thermal package if Cloud
Chamber intentionally owns the required CM1 Fortran/configuration changes.

### Forced Convergence / Momentum Forcing

Decision for v1: defer.

Relevant CM1 options:

```text
iinit = 9   forced convergence
iinit = 10  momentum forcing
```

Pros:

- Closer to a boundary/convergence initiation story than a warm bubble.
- Potentially useful for dryline, front, and mesoscale lift experiments.

Cons:

- More configuration surface area.
- Harder to explain and validate.
- May need additional forcing parameters and careful domain placement.
- More likely to imply a real-world boundary that the input sounding alone does
  not provide.

Specialized package that may come later:

```text
Deep Convection Trial - Convergence Trigger
```

### Surface-Heating / Diurnal Forcing

Decision for v1: defer.

Pros:

- Conceptually tied to morning soundings and afternoon convection.
- Helps answer "what happens after daytime heating?" once land/radiation paths
  are validated.

Cons:

- Requires land-surface, surface flux, date/time, solar angle, and possibly
  radiation validation.
- Requires longer runtime.
- The current realistic-input contract says date/location/radiation are
  metadata first and validated controls later.

Specialized package that may come later:

```text
Observed Sounding Diurnal Trial
```

### Cold-Pool / Boundary Trigger

Decision for v1: defer.

Relevant CM1 option:

```text
iinit = 2  cold pool
```

Pros:

- Useful for squall-line, outflow boundary, and secondary initiation stories.

Cons:

- Specialized.
- Not a generic first severe/deep-convection package.
- Could confuse the story if the candidate sounding does not include evidence
  for an outflow boundary.

Specialized package that may come later:

```text
Boundary / Cold-Pool Initiation Trial
```

### No Trigger / Observed Sounding Only

Decision for v1: do not use as the main package.

Pros:

- Simplest.
- Honest test of whether the configured environment self-initiates.

Cons:

- Likely to produce no storm even in environments that are physically
  storm-capable but need lift.
- Poor default user experience for severe-looking soundings.
- Easy to misinterpret as "CM1 says no storm."

Recommendation:

Offer later as an advanced control or comparison run, not the default package.

## CM1 Package Settings To Implement Later

### Sounding and Winds

Decision: use the current `isnd = 7` path and require observed wind support.

Rules:

- The package must use the observed sounding as `input_sounding`.
- Observed winds must be written to `input_sounding`.
- If wind is missing or unparseable, this package should be blocked or clearly
  marked unavailable until a wind-capable sounding is selected.
- Do not substitute a generated wind profile silently.

Why:

- Deep-convection organization and storm mode depend strongly on vertical wind
  shear.
- CM1 `isnd = 7` reads wind from `input_sounding`; this matches the current
  Cloud Chamber observed-sounding direction.

### Case and Initialization

Recommended starting point:

```text
testcase = 0
isnd = 7
iinit = 8
ptype = 5
radopt = 0
output_rain = 1
output_dbz = 1
```

This borrows the broad pattern from the CM1 `supercell` example while replacing
the analytic Weisman-Klemp sounding/wind with an observed `input_sounding`.

Implementation must validate:

- whether the built-in warm line thermal initiates interpretable convection for
  selected real soundings;
- whether `ibalance` should remain `0` for this package family;
- whether `iorigin = 2` remains the right domain origin;
- whether storm motion (`imove`, `umove`, `vmove`) should be off initially or
  configured from mean wind.

### Surface Flux And Radiation

Decision: keep radiation off for v1.

```text
radopt = 0
```

Decision: do not make surface flux the initiating mechanism for v1.

Surface flux may be inherited as a controlled background choice only if it is
already supported by the package architecture and documented as a proxy. It
should not be sold as real land-surface heating.

Why:

- The first package should isolate the question: can this observed profile
  support deep convective growth when triggered?
- Radiation/date/location controls are not yet validated as product controls.
- Diurnal realism belongs in a later package family.

### Domain And Resolution

Decision: define separate validation tiers. Do not promise that a MacBook
quick-look is a definitive deep-convection run.

Recommended v1 tiers:

| Tier | Purpose | Draft Shape |
| --- | --- | --- |
| Quick-look | smoke test package health and early response | short runtime, coarse domain, reduced output cadence |
| Standard | first useful deep-convection inspection | larger/deeper domain, more output times |
| Deep/LAN worker | meaningful storm evolution if quick-look is promising | LAN worker recommended, longer runtime, more complete output |

Draft implementation targets needing validation:

- Horizontal domain should be much wider than current shallow-cumulus quick-look
  packages. A single triggered storm should not immediately feel boxed in.
- Vertical domain should reach the upper troposphere. The current Cloud Chamber
  shallow package already uses an 18 km top; this is a plausible starting point
  for deep-convection trials.
- Horizontal resolution should be chosen for local performance first, then
  refined. The CM1 stock supercell example uses 1 km horizontal spacing and
  500 m vertical spacing; Cloud Chamber shallow LES uses much finer spacing
  over a much smaller domain. The deep-convection package should not blindly
  reuse either without validation.
- Output cadence should be frequent enough to see initiation, updraft growth,
  precipitation onset, and reflectivity evolution. A 5 to 15 minute cadence is
  the likely initial design range, with exact values selected by runtime tests.

Open design risk:

```text
Cloud Chamber's LES identity and local compute limits are in tension with
severe-storm domain size. The first package should be honest about being an
idealized local trial, not a production storm-scale NWP simulation.
```

### Boundary Conditions

Decision: start from CM1 deep-convection example practice, then validate.

The CM1 `supercell` example uses open/radiative lateral boundary style settings
and `testcase = 0`. A future implementation should compare those settings with
Cloud Chamber's current shallow-cumulus boundary settings and document every
change in the package report.

### Microphysics

Decision: use Morrison microphysics first.

```text
ptype = 5
```

Why:

- Already used in current Cloud Chamber packages.
- Used in the CM1 supercell example.
- Supports reflectivity output.
- Supports rain and cloud fields Cloud Chamber already visualizes.

Future option:

- Evaluate NSSL or other schemes only after the v1 package loop works and
  output products are stable.

## Expected Outputs

Required v1 model outputs:

- `qc` cloud water;
- `qr` rain water;
- `qv` water vapor;
- `w`, `u`, `v`;
- potential temperature or temperature-related field;
- pressure or pressure perturbation if available;
- surface rain (`rn` and translated `rn2` when relevant);
- reflectivity (`dbz`) and composite reflectivity (`cref`) when present;
- height coordinates and grid metadata.

Recommended severe/deep-convection outputs to evaluate:

- low-level surface wind swath;
- pressure perturbation swath;
- maximum rainwater at the lowest model level;
- maximum w at 5 km AGL;
- updraft helicity swath;
- cold-pool intensity/depth;
- buoyancy if available and scientifically validated.

Expected output products:

- interesting times:
  - first cloud;
  - first deep cloud;
  - max cloud water;
  - max updraft;
  - first surface rain;
  - max reflectivity or first meaningful reflectivity;
- field catalog with capability classification;
- vertical profile/time-height products for updraft, cloud water, rain water,
  reflectivity, and thermodynamic context;
- selected-region diagnostics for updraft core, cloud, rain shaft, cold-pool
  region, and clear-air environment when supported.

## Expected Diagnostics

V1 should support, or explicitly caveat if not available:

- cloud formed;
- deep cloud formed;
- first cloud time;
- first deep-cloud time;
- cloud top;
- max `qc`;
- max/min `w`;
- updraft depth;
- rain present;
- rain onset;
- max `qr`;
- max surface rain;
- max `dbz` and composite reflectivity;
- whether output fields stayed finite;
- whether observed wind was present and used;
- whether the trigger was artificial;
- whether domain/runtime/output cadence were limiting.

Future diagnostics:

- CAPE/CIN/LCL/LFC from the observed sounding;
- bulk shear layers;
- storm-relative helicity;
- updraft helicity;
- cold-pool strength/depth;
- precipitation feedback;
- boundary/outflow diagnostics.

## Candidate Screening Handoff

Deep-convection sounding candidates should route to Deep Convection Trial.
Candidate labels are hypotheses for choosing interesting experiments; CM1 output
decides what actually happened.

```text
sounding candidate hypothesis
-> deep_convection_trial package
-> CM1 run result
-> output products and diagnostics decide what actually happened
```

Candidate metadata should be copied into package metadata:

```json
{
  "candidate_screening_hypothesis": {
    "story": "severe_thunderstorm_environment",
    "score": 0.0,
    "evidence": [],
    "caveats": []
  }
}
```

Candidate package routing:

| Candidate story | Intended package | Useful caveat |
| --- | --- | --- |
| `severe_thunderstorm_environment` | Deep Convection Trial | This sounding has ingredients worth trying in a triggered deep-convection run. |
| `supercell_environment` | Deep Convection Trial | Rotating storm structure is an outcome to inspect after the run, not something assumed before the run. |
| `high_cape_pulse_storm` | Deep Convection Trial | Storm organization depends on what CM1 produces. |
| `dry_microburst_inverted_v` | Deep Convection Trial | Downdraft or microburst behavior requires precipitation and evaporative cooling to develop. |
| `squall_line_cold_pool_candidate` | Deep Convection Trial as a first experiment | Line/cold-pool-specific packages may come later. |
| `elevated_convection` | Deep Convection Trial as a first experiment | Elevated inflow/source-layer behavior may need a specialized package later. |

Candidate copy examples:

```text
Severe thunderstorm environment
This sounding has ingredients worth trying in a triggered deep-convection run.

Supercell-like environment
Instability and wind structure make this a fun candidate for a Deep Convection
Trial. Rotation/organization is something to inspect after the run.

Dry microburst / inverted-V
Dry low levels may make downdrafts interesting if precipitation develops.
```

If observed wind is missing, deep-convection trial package generation should be
blocked or clearly unavailable. Wind is not optional for a package whose
learning value depends on storm organization and shear.

## Manual QA Plan

Manual QA for #261 should focus on package health, tuning, domain/runtime
calibration, and whether Results/Explore make the outcome interpretable:

1. Choose one observed sounding with strong deep-convection screening evidence.
2. Generate a `Deep Convection Trial` quick-look package.
3. Inspect `input_sounding`:
   - station metadata preserved;
   - surface anchored correctly;
   - thermodynamic profile present;
   - moisture profile present;
   - wind profile present and in CM1 `u`/`v` units.
4. Inspect `namelist.input`:
   - `testcase = 0`;
   - `isnd = 7`;
   - `iinit = 8`;
   - microphysics, output rain, and reflectivity fields enabled;
   - trigger parameters recorded in the package report.
5. Run quick-look locally or on the LAN worker.
6. Ingest output.
7. Confirm Results says this was an observed-sounding Deep Convection Trial,
   not a shallow-cumulus baseline.
8. Open Explore and verify:
   - available fields include cloud water, rain water, water vapor, vertical
     velocity, reflectivity, and surface rain when present;
   - interesting times include initiation/updraft/rain/reflectivity events when
     supported;
   - caveats disclose the idealized warm thermal trigger.
9. Compare against at least one weak or capped sounding to see how the same
   package behaves in a less favorable environment.
10. Do not commit generated output.

Manual acceptance categories:

| Category | Meaning |
| --- | --- |
| accepted | CM1 completes, output ingests, observed winds are used, trigger is recorded, and diagnostics show a physically interpretable result. |
| accepted_with_notes | Run is healthy but storm response is weak, too strong, or sensitive to trigger settings. |
| needs_calibration | Run completes but trigger/domain/runtime makes the result unhelpful or misleading. |
| failed | CM1 fails, output is missing, observed wind is not used, severe field caveats appear, or package metadata misrepresents the experiment. |

## Implementation Follow-Up

Implementation issue:

```text
#261 - Implement CM1 deep-convection package v1 from observed sounding
```

Scope:

- Add `deep_convection_trial` package family metadata.
- Add package generation path using observed `input_sounding`, observed winds,
  warm thermal trigger, Morrison microphysics, rain/reflectivity outputs, and
  clear experiment limitations.
- Add tiny fixture tests for namelist/package metadata.
- Add manual QA instructions for one real sounding smoke run.

Non-goals for #261:

- no radiation/date/location realism;
- no GIS/map inputs;
- no CAPE/CIN/SRH implementation unless already tested independently;
- no browser NetCDF parsing;
- no renderer upgrade.

## Open PM Decisions

- What is the first acceptable runtime target for quick-look: local MacBook,
  LAN worker, or both?
- How much trigger parameter control should be exposed to users versus kept
  as package metadata?

## Source References

Source breadcrumbs for future implementation:

- `/Users/timpeterson/cm1r21.1/README.namelist`: `isnd = 7` uses external
  `input_sounding`; wind profile is also read from `input_sounding`; `iwnd` is
  ignored.
- `/Users/timpeterson/cm1r21.1/README.namelist`: `iinit = 1` warm bubble,
  `iinit = 2` cold pool, `iinit = 8` warm line thermal with random
  perturbations, `iinit = 9` forced convergence, and `iinit = 10` momentum
  forcing.
- `/Users/timpeterson/cm1r21.1/run/config_files/supercell/namelist.input`:
  stock CM1 supercell example uses `testcase = 0`, `iinit = 1`, `ptype = 5`,
  `output_rain = 1`, and `output_dbz = 1`.
- `/Users/timpeterson/cm1r21.1/README.namelist`: `output_rain`,
  severe-relevant swath outputs, `output_coldpool`, and `output_dbz`
  definitions; `output_dbz` is available for Morrison microphysics
  (`ptype = 5`).
- `app/backend/cloud_chamber/cm1_input_contract.py`: current Cloud Chamber
  observed-sounding package path renders `isnd = 7`; the Deep Convection Trial
  implementation selects `iinit = 8`, writes observed sounding metadata into
  package configuration, and treats trigger details as package metadata.
- `app/backend/cloud_chamber/dry_run_package.py`: current package generation
  writes `input_sounding`, `namelist.input`, package reports, and run/case
  manifests.
