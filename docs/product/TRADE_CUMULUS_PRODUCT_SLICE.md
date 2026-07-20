# Trade Cumulus Product Slice

**Status:** Approved Stage 5 product-architecture definition

## Purpose

This document defines one concrete Cloud Chamber product slice around the canonical BOMEX evidence completed in Stage 4.

It answers:

> What is the smallest coherent Trade Cumulus experience Cloud Chamber should validate next?

It defines:

- one candidate Cloud World;
- one candidate baseline Recipe;
- one meaningful Control;
- one foundational Lens with regime-specific defaults;
- one matched Comparison;
- the evidence required before any of them becomes supported.

It does not define final interface structure, implementation architecture, persistence, MVP scope, or a generic framework for every future Cloud World, Recipe, Control, or Lens.

## Authority and evidence

Controlling authority remains:

1. `NORTH_STAR.md`
2. `docs/product/PRODUCT_VISION.md`
3. explicit approved PM decisions
4. `docs/product/APPLICATION_SEMANTICS.md`

This product slice is grounded in:

- `docs/research/bomex/bomex-setup-and-cm1-mapping.md`;
- `docs/research/bomex/bomex-run-report.md`;
- the implementation and run evidence merged through PR #372.

The Stage 4 result established that Cloud Chamber can produce, ingest, inspect, and watch a scientifically recognizable canonical BOMEX trade-cumulus simulation at practical local cost.

That evidence supports candidate product architecture. It does not by itself establish supported product status.

## Product-slice map

```text
Trade Cumulus Cloud World
→ Canonical BOMEX baseline Recipe
→ Baseline Simulation
→ Updraft Lens
→ Surface moisture supply Control
→ More-moisture Simulation
→ Matched Comparison
→ deliberate question and explanation
```

Exploration remains the default activity. The matched Comparison becomes an Experiment only when the user deliberately asks how stronger surface moisture supply changed the cloud field.

## 1. Cloud World candidate: Trade Cumulus

### User promise

A person enters a steady maritime trade-wind atmosphere and watches a field of shallow cumulus clouds repeatedly form, grow, mix, decay, and reform.

The world should make it possible to:

- watch a population of clouds rather than one artificially triggered tower;
- see rising and sinking air in relation to visible cloud;
- change one meaningful lower-boundary condition;
- compare how the cloud field responds;
- understand the response without first learning CM1 configuration.

### Scientific boundary

The candidate world is:

- idealized;
- nonprecipitating;
- horizontally periodic;
- driven by prescribed surface and large-scale forcing;
- based on the canonical BOMEX trade-cumulus system;
- intended to reveal shallow-cloud lifecycle, transport, mixing, and cloud-field response.

It is not:

- a forecast;
- a reconstruction of one real place or date;
- a land-surface simulation;
- a precipitating-cloud world;
- one current Build, Results, or Explore page;
- a claim that every shallow maritime cloud behaves like BOMEX.

### Entry behavior

A user should be able to enter this world directly at the baseline experience.

The underlying Recipe may be selected automatically or remain hidden. The user should not be forced through Recipe-selection ceremony before seeing the cloud field.

## 2. Candidate baseline Recipe: Canonical BOMEX Baseline

The Stage 4 configuration identified by:

```text
bomex_trade_cumulus_baseline_v0
```

is the candidate baseline Recipe foundation.

The user-facing Recipe name is:

> **Canonical BOMEX Baseline**

The candidate Recipe inherits the source-traceable scientific and CM1 configuration recorded in the Stage 4 mapping and run report, including:

- canonical BOMEX thermodynamic, moisture, and wind profiles;
- prescribed surface sensible heat and moisture fluxes;
- friction velocity and momentum treatment;
- subsidence, radiative cooling, moisture drying, geostrophic wind, and Coriolis forcing;
- periodic lateral boundaries;
- reversible nonprecipitating moist thermodynamics;
- canonical domain and grid;
- six-hour duration;
- deterministic initial perturbation behavior;
- cloud-liquid, motion, thermodynamic, forcing, transport, and integrity evidence.

The physical baseline remains canonical BOMEX. The first product-facing validation changes the saved three-dimensional output cadence from five minutes to two minutes. That is an experience and storage choice, not a change to the modeled atmospheric system.

### Candidate status

The baseline is a **candidate Recipe**, not yet a supported Recipe.

It already has:

- primary scientific source traceability;
- deterministic CM1 representation;
- one complete six-hour run;
- recognizable cloud-field behavior;
- practical runtime and storage evidence;
- usable cloud-water, motion, forcing, and transport fields.

It still needs:

- matched two-minute-output evidence;
- one validated meaningful Control;
- one validated Lens experience;
- one honest Comparison and explanation.

## 3. First Control: Surface moisture supply

The first Control is:

> **Surface moisture supply**

It represents the rate at which the idealized lower boundary supplies water vapor to the boundary layer.

The first validation exposes exactly two states:

| State | Product meaning | CM1-facing moisture flux |
| --- | --- | ---: |
| Baseline | Canonical BOMEX surface moisture supply | `5.2e-5 g/g m/s` |
| More moisture | Fifty percent stronger surface moisture supply | `7.8e-5 g/g m/s` |

The product should present understandable states, not a raw free-form CM1 parameter.

The exact value and unit must remain available in technical details and provenance.

### Fixed assumptions

The first matched comparison changes only surface moisture supply.

It holds fixed:

- initial thermodynamic, moisture, and wind profiles;
- deterministic perturbation seed and method;
- sensible heat flux;
- friction velocity and momentum treatment;
- large-scale subsidence, cooling, drying, and geostrophic forcing;
- Coriolis treatment;
- turbulence and moist-thermodynamic configuration;
- boundaries, domain, grid, time-step strategy, and duration;
- requested fields and output cadence;
- CM1 source, executable, and Cloud Chamber implementation.

### Expected interpretation

The Control asks whether stronger lower-boundary moisture supply produces an observable change in:

- lower-atmosphere moisture;
- cloud onset;
- cloud cover;
- cloud-liquid water path;
- cloud depth and persistence;
- updraft-cloud relationship;
- repeated cloud-field evolution.

These are expected places to inspect, not guaranteed outcomes.

A trustworthy weak or absent response remains valid evidence.

### Bounded correction rule

The first experiment uses the fifty-percent increase above.

If the result is scientifically trustworthy but visually indistinguishable or excessively disruptive, the PM may authorize one bounded magnitude adjustment.

Do not create a parameter sweep or expose a continuous slider during this validation.

Failure of this first Control does not automatically invalidate the Trade Cumulus Cloud World or Canonical BOMEX Baseline.

## 4. Base cloud view

The base view shows the evolving three-dimensional cloud-liquid field using `ql` as the supported cloud-water field for this Recipe.

It should preserve:

- the full cloud-field context;
- repeated growth and decay through model time;
- changing cloud depth and spatial distribution;
- native model provenance and known representation limits.

The base view is the visible cloud. A Lens adds a deliberate way of seeing an otherwise hidden process.

## 5. First Lens: Updraft Lens

### Purpose

The Updraft Lens reveals rising and sinking air and relates it to the visible cloud.

It should help a person ask:

- Where is air rising beneath or inside the cloud?
- Which clouds still have active upward support?
- Where is air sinking around or between clouds?
- How does stronger surface moisture supply change the relationship between updrafts and cloud liquid?

The Lens uses vertical velocity `w` as its primary quantity and cloud liquid `ql` as its visible-cloud boundary.

It does not prove causation by itself. It supports observation and explanation.

### Lens-owned defaults

A Lens owns more than a field name.

For a supported World and Recipe, it may own defaults for:

- primary and supporting fields;
- palette;
- value range;
- geometry and orientation;
- default time and region;
- overlays;
- interpretation;
- caveats.

These defaults are specific to the Lens, Cloud World, and Recipe.

An Updraft Lens for Trade Cumulus is not required to use the same defaults as an Updraft Lens for deep convection.

### Default slice geometry

The Trade Cumulus Updraft Lens starts with a **vertical slice**.

The default plane should align with the low-level mean wind. For canonical BOMEX, that is an x-z slice.

For a single Simulation:

1. select an active postspinup time from the final three hours, defaulting to the frame with the highest domain-mean cloud-water path;
2. select the cross-wind coordinate containing the strongest coherent overlap between cloud liquid and positive vertical velocity;
3. do not select a plane solely because it contains one absolute-maximum `w` cell.

If no qualifying overlap exists, fall back first to a plane through the largest coherent cloud-liquid object, then to the domain midpoint.

### Vertical-velocity palette

Use a divergent palette with a physically meaningful zero:

```text
negative vertical velocity → blue
near zero → neutral
positive vertical velocity → red
```

The default range must:

- be symmetric about zero;
- be robust to isolated extrema;
- remain fixed through playback;
- be visibly labeled in `m/s`.

For a Comparison, derive one shared symmetric range from both Simulations and keep it fixed across both views and all synchronized frames.

Do not rescale each frame independently.

### Slice rendering

The slice must:

- preserve the physical horizontal-to-vertical aspect ratio;
- render adjacent native-grid cells without visual gutters;
- avoid default smoothing or interpolation that invents unresolved structure;
- allow the user to inspect the native cell values and scale.

For canonical BOMEX, a full-domain x-z view should reflect the approximately `6.4 km : 3.0 km` physical proportion rather than stretching the slice into a thin horizontal strip.

### Cloud-boundary overlay

Draw the visible cloud boundary in black using:

```text
ql >= 1e-6 kg/kg
```

This is the same supported cloud-liquid threshold used by the Stage 4 BOMEX evidence.

The contour should make the relationship among updraft, downdraft, cloud base, cloud body, and surrounding clear air visible.

Do not use a different undocumented definition of cloud for display.

For a Comparison, both Simulations must use the same cloud threshold.

### Horizontal-flow context in the 3-D view

The Updraft Lens provides an optional sparse horizontal-wind overlay in the three-dimensional cloud view. It is shown by default when the Lens is active and may be hidden by the user.

Default behavior:

- place arrows on a horizontal plane near the supported cloud base, initially the model level closest to `600 m`;
- sample sparsely enough to preserve cloud visibility;
- default to horizontal perturbation wind, with the horizontal domain mean at that level removed;
- provide total horizontal wind as an explicit alternative;
- show a vector scale legend;
- keep arrow density, mode, height, and scale stable through playback.

For a Comparison, both Simulations must use the same arrow mode, height, density, and scale.

This is flow context within the Updraft Lens. It does not establish a generalized vector-rendering platform or a separate Wind Lens.

## 6. First matched Comparison

The first deliberate question is:

> **How does stronger surface moisture supply change the trade-cumulus field?**

The Comparison contains:

- one Canonical BOMEX Baseline Simulation;
- one More Moisture Simulation;
- the meaningful changed condition stated plainly;
- synchronized model time;
- a shared default vertical plane;
- a shared `w` range;
- a shared cloud threshold;
- shared horizontal-wind overlay settings;
- the same scientific and numerical assumptions except for surface moisture supply.

### Reference ownership

The baseline is the reference Simulation.

Its default time and plane are selected once and inherited by the variant.

Do not independently pick the most flattering time or plane from each Simulation.

The user may move the shared time or plane, but the Comparison should remain synchronized.

### Honest comparability

The two runs use the same deterministic perturbation seed and differ only in surface moisture supply.

Even so, large-eddy simulations can diverge through time.

The product must not imply that one individual baseline cloud retains one-to-one identity with one individual variant cloud through the full six hours.

Compare:

- field-level behavior;
- cloud population and lifecycle;
- process patterns;
- aggregate and time-dependent response;
- representative aligned views.

## 7. Output cadence and required evidence

The first product-facing matched experiment uses:

```text
simulation duration: 6 hours
three-dimensional model-field cadence: 120 seconds
domain-diagnostic cadence: 60 seconds
expected three-dimensional frames per run: 181
```

Both baseline and variant must be run at the same cadence.

The existing five-minute Stage 4 baseline remains valid scientific evidence but is not the matched frame-by-frame Comparison source.

At minimum, preserve evidence for:

- `ql`;
- `qv`;
- `th` or equivalent thermodynamic state;
- `prs`;
- `u`, `v`, and `w`;
- `cwp`;
- surface sensible and moisture fluxes;
- cloud fraction by height and time;
- cloud base and top;
- liquid-water path;
- cloud-conditioned and raw vertical velocity;
- domain-mean thermodynamic profiles;
- relevant resolved and subgrid transport diagnostics;
- runtime integrity and non-finite checks;
- exact changed and fixed assumptions;
- compute and storage cost.

## 8. Explanation requirement

The matched product experiment must support one concise, evidence-grounded explanation that connects:

```text
what changed
→ how lower-atmosphere moisture responded
→ how cloud amount, depth, persistence, or timing responded
→ what the Updraft Lens revealed
→ what remains uncertain
```

The explanation may be authored from the evidence.

Automated causal reasoning is not required.

## 9. Candidate status and graduation

| Product element | Current status |
| --- | --- |
| Trade Cumulus Cloud World | Candidate |
| Canonical BOMEX Baseline Recipe | Candidate |
| Surface moisture supply Control | Experimental |
| Updraft Lens for Trade Cumulus | Candidate |
| Baseline versus More Moisture Comparison | Planned validation |

The slice may advance only when the matched implementation demonstrates:

1. trustworthy baseline and variant runs;
2. an interpretable response to the Control;
3. a readable, stable, scientifically honest Updraft Lens;
4. synchronized and honestly comparable views;
5. an explanation grounded in visible and quantitative evidence;
6. practical local runtime and storage;
7. no hidden dependence on current observed-sounding ranking, warm-bubble initiation, or generic `run_recipe` ceremony.

Possible PM dispositions after the matched experiment are:

```text
advance_trade_cumulus_slice
one_bounded_control_or_lens_correction
reject_first_control_but_retain_world_candidate
reject_trade_cumulus_near_term_slice
```

## 10. Saved Views and ordinary Exploration

Exploration remains the normal activity.

A person should be able to watch the baseline, move through time, inspect clouds, turn on the Updraft Lens, and change the shared slice without declaring an Experiment.

A later Saved View may preserve:

- time or playback range;
- vertical-plane orientation and position;
- `w` range;
- cloud-boundary state;
- horizontal-wind mode, height, density, and scale;
- camera and display choices;
- synchronized Comparison state.

This document does not require Saved View persistence in the first implementation.

## 11. Single next bounded implementation

After this document is approved, the single next issue should be:

> **Stage 5B: validate the Trade Cumulus moisture comparison and Updraft Lens**

That issue should proceed in order:

1. improve the Updraft Lens slice and 3-D flow-context behavior against the existing ingested BOMEX result;
2. generate and execute matched 120-second-cadence baseline and More Moisture runs;
3. ingest both results;
4. evaluate scientific response, Lens usability, Comparison honesty, watchability, compute, and storage;
5. make one PM disposition from the approved list.

Do not create that implementation issue automatically before this product definition is approved.

## Non-implications

This document does not:

- declare Trade Cumulus the MVP;
- approve the candidate World or Recipe as supported;
- define final navigation or interface layout;
- require side-by-side rather than another honest Comparison presentation;
- establish a generic Lens schema;
- establish a generalized vector renderer;
- expose a free-form moisture-flux slider;
- approve other Controls;
- add precipitation;
- define Saved View persistence;
- choose another cloud regime;
- make the current Build, Results, or Explore structure final;
- reopen the approved application semantics.

The purpose is to define one evidence-backed product slice clearly enough that the next implementation can test a real Cloud Chamber experience rather than another technical mechanism.
