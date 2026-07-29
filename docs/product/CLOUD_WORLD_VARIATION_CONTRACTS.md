# Cloud Chamber Variation Contracts

**Status:** Approved product-architecture authority  
**Scope:** Trade Cumulus, Mountain Waves, and Supercells  
**Authority:** Subordinate to the North Star, Product Vision, explicit PM decisions, Application Semantics, and the approved MVP  
**Implementation status:** This document defines durable product architecture. It does not imply that every approved control or profile is already implemented or characterized.

## Purpose

Cloud Chamber needs one durable answer to a simple product question:

> What does it mean to start from a Simulation, change the atmosphere or the way it is modeled, run the related case, return later, and learn from the response?

This document defines that answer for the actual three-World application.

It decides:

- the shared Create Variation journey;
- the boundary between shared behavior and World-specific science;
- eligible parents;
- scientific, numerical, and observation-plan inheritance;
- stable Simulation identity and technical attempts;
- automatic Result-to-Simulation availability;
- parent reuse;
- cost estimates and run profiles;
- supported control families for each World and Recipe;
- validation and caveat semantics;
- failure, cancellation, incomplete output, and conflict behavior;
- Compare entry;
- disposition of the existing Mountain Waves variation workflow;
- implementation sequence after issue #435.

This is not a minimal first-release scope. It is the durable variation architecture toward which implementation should converge. Successor issues may implement it in bounded increments, but those increments must not redefine the product contract around whichever World happens to be easiest to code first.

---

# 1. Executive decisions

## 1.1 Shared architecture

Cloud Chamber should use:

```text
one shared Create Variation journey and lifecycle envelope
+ explicit typed contracts for each World and Recipe
```

The shared layer owns:

- parent selection and eligibility explanations;
- stable intended Simulation identity;
- name and optional question;
- exact inheritance;
- categorized differences;
- scientific-comparability classification;
- run-profile and cost review;
- deterministic package creation and preflight;
- technical attempts, retries, restarts, failures, and cancellation;
- automatic Simulation availability after strict validation;
- parent-eligibility status;
- Activity, History, Explore, and Compare entry.

The World and Recipe contracts own:

- scientific foundations;
- physical controls and transforms;
- dependencies and invalid combinations;
- numerical realizations;
- required output and Lens contracts;
- scientific previews;
- World-specific validation;
- expected broad behavior and interpretation limits.

Do not create a universal parameter schema, arbitrary JSON form builder, CM1 namelist editor, plugin registry, or flattened scientific-control model.

## 1.2 Recipe boundary

A Recipe is the boundary of coherent variation. It defines a known-working scientific design, its supported transforms, approved numerical realizations, required evidence, and limits.

A control is not supported merely because CM1 accepts the corresponding value. A parent is not eligible merely because its output is readable.

## 1.3 Complete control architecture now; bounded implementation later

The durable contracts include the meaningful control families for each World:

- **Trade Cumulus:** surface heat and moisture supply, boundary-layer moisture, inversion structure, free-tropospheric humidity, wind shear, and large-scale forcing;
- **Mountain Waves:** terrain, wind, stability, and moisture through two distinct Recipes;
- **Supercells:** hodograph geometry, shear magnitude and distribution, thermodynamic environment, and deterministic initiation.

Some controls require bounded package characterization or endpoint runs before implementation may expose their full envelope. That is an enablement gate, not a reason to omit the control from product architecture.

## 1.4 Exact inheritance with explicit layer changes

Create Variation begins as an exact copy of the parent’s:

1. scientific design;
2. numerical realization;
3. observation plan.

Cloud Chamber may recommend a less expensive run profile, but it never changes profile silently. A physical change made while also changing numerical realization is a mixed variation, not a controlled one-factor experiment.

## 1.5 Simulation identity precedes execution

Stable intended Simulation identity is created when the reviewed package is created, before CM1 starts.

The scientific design and numerical realization are immutable for that Simulation. Multiple technical attempts may serve the same Simulation when those layers remain identical.

## 1.6 Observation-only changes are not ordinary variations

Changing only saved-output cadence, retained fields, or the amount of already-defined evolution retained does not create a different atmospheric Simulation.

Those are observation or data-retention actions. They may require another run or restart, but they should not appear as a new physical variation.

A numerical change—grid, timestep, domain, numerical method, source build, or materially different physics—does create a distinct Simulation.

## 1.7 Automatic Simulation availability

A variation created through an approved World contract becomes available automatically after strict specification, package, attempt, output, and World-inspectability validation.

No second **Keep**, **Promote**, **Graduate**, or **Accept** ceremony is required in this one-user laboratory.

Automatic availability means:

> The intended Simulation has honest, inspectable model output.

It does not mean:

> The Simulation is beautiful, important, surprising, presentation quality, causally explanatory, or worth featuring.

## 1.8 Parent eligibility is separate

An available Simulation becomes a reusable parent only when its exact specification is reconstructible, its Recipe/version remains supported, its values remain inside the Recipe’s absolute envelope, and its lineage and caveats can be carried forward honestly.

There is no arbitrary generation limit. Absolute Recipe rules prevent parent-of-parent drift.

## 1.9 World-specific run profiles

Cloud Chamber may reuse the role labels **Quick**, **Standard**, **Presentation**, and **Match parent**, but each World must state exact grid, duration, cadence, expected cost, supported evidence, and limitations.

These are not generic low/medium/high fidelity levels.

## 1.10 Implementation sequence

After approval of this contract:

```text
#394 shared Activity and History lifecycle
→ shared variation envelope and Mountain Waves migration
→ Trade Cumulus variation implementation
→ Supercells variation implementation
→ durability, repair, and measured personal acceptance
```

The product contract is complete even though implementation remains bounded and serial.

---

# 2. Core product model

## 2.1 Shared journey

Every supported World variation follows this recognizable journey:

```text
open an eligible parent Simulation
→ Create Variation
→ inherit the exact parent specification
→ name the intended Simulation
→ optionally record a question
→ change one or more supported settings
→ review exact categorized differences
→ review whether the comparison is controlled, multi-factor, numerical, or mixed
→ choose or retain a run profile
→ review runtime, storage, and scientific limits
→ create a deterministic package
→ launch or queue a technical attempt
→ leave
→ return through Activity
→ validate completed output
→ Explore the available Simulation
→ Compare to its parent or World reference
→ create another variation when parent-eligible
```

A user may change several supported values together. The product must not reduce variation to a one-variable wizard or infer one-factor causation when several values changed.

## 2.2 Common envelope and explicit World payloads

The implementation should follow the same architectural pattern that works for durable Explore state:

```text
small common envelope
+ one explicit World/Recipe-specific payload
```

The common variation envelope represents:

- stable `world_id`;
- stable `recipe_id` and Recipe contract version;
- stable intended `simulation_id`;
- parent and World-reference identities;
- display name and optional question;
- immutable scientific-design hash;
- immutable numerical-realization hash;
- selected observation plan;
- exact categorized differences;
- comparability classification;
- cost estimate, confidence, and evidence basis;
- technical attempt relationships;
- validation decisions;
- availability and parent-eligibility status.

The tagged World payload represents the actual science:

- Trade Cumulus fluxes, profiles, forcing, domain, and required diagnostics;
- Mountain Waves terrain and upstream atmospheric transforms;
- Supercells hodograph, thermodynamic profile, initiation, and storm-domain contract.

## 2.3 Control contract

Every supported control must define:

- product name and physical meaning;
- Recipe-reference value or profile;
- exact transform from the Recipe reference;
- units and user-facing range or curated choices;
- ordinary versus advanced placement;
- dependencies and invalid combinations;
- derived preview quantities;
- difference category;
- required output and Lens implications;
- parent-eligibility implications;
- evidence basis and characterization state.

Controls resolve to absolute Recipe-referenced values or authored profiles. They do not compound relative multipliers from generation to generation.

### Product approval versus implementation enablement

Approval of this document approves the control family, transform, and design envelope as product architecture. A control or endpoint becomes available in the application only after its deterministic generator, validation, cost estimate, and bounded endpoint characterization pass.

Implementation may not silently narrow an approved envelope because an endpoint is inconvenient. A failed characterization returns the material scientific or numerical conflict to PM review and records the replacement decision explicitly. Conversely, lack of an existing run does not demote a scientifically approved control to speculative product scope.

## 2.4 Ordinary and advanced controls

**Ordinary controls** answer common, legible questions within the World.

**Advanced controls** remain curated transforms with explicit physical meaning. They are not raw per-level sounding tables or namelist keys.

Arbitrary profile editing belongs in Recipe authoring or Fun With Soundings, not in ordinary World variation.

---

# 3. Configuration inheritance and comparison semantics

## 3.1 Three inherited layers

### Scientific design

The physical problem being modeled:

- initial thermodynamic and moisture structure;
- wind environment;
- surface or terrain;
- large-scale forcing;
- initiation;
- model physics;
- fixed Recipe assumptions;
- selected physical controls.

### Numerical realization

How that problem is calculated:

- domain and boundaries;
- horizontal and vertical grid;
- timestep or timestep strategy;
- numerical options;
- source/executable identity where material;
- physics implementation when the Recipe permits alternatives.

### Observation plan

What portion of the calculated evolution is retained:

- target duration or extension target;
- saved-output cadence;
- diagnostic cadence;
- retained field inventory;
- restart/checkpoint retention.

A named run profile may bundle a numerical realization and observation plan, but the underlying distinction remains explicit in lineage and Compare.

## 3.2 Exact parent inheritance

Opening Create Variation initially reproduces all three parent layers exactly.

When the parent uses a costly Presentation profile, the editor may say:

> Standard is recommended for ordinary experiments.

It may not switch to Standard until the user explicitly chooses it and reviews the resulting numerical and observation differences.

## 3.3 Relationship classifications

Every parent/child relationship receives one of these classifications:

| Classification | Required relationship | What the user may infer |
| --- | --- | --- |
| **Controlled physical variation** | One physical control differs; numerical realization and observation plan are matched | A bounded one-factor question is supported |
| **Multi-factor physical variation** | Several physical controls differ; numerical realization and observation plan are matched | Exploratory response; no single-factor causal claim |
| **Numerical sensitivity** | Scientific design matches; numerical realization differs | Sensitivity to resolution, domain, timestep, or another numerical choice |
| **Mixed variation** | Scientific design and numerical realization both differ | Useful related comparison, not a controlled physical experiment |
| **Replicate/realization** | Scientific design and numerical realization match; only deterministic perturbation realization differs | Samples realization sensitivity; not a changed environmental condition |
| **Observation-only attempt** | Scientific and numerical layers match; only retention differs | Same intended atmospheric evolution, not another Simulation |

## 3.4 Duration and extension

A longer deterministic continuation of an existing Simulation is an **extension** of the same Simulation when:

- the scientific and numerical specification is unchanged;
- restart lineage is exact;
- overlapping saved times remain identical within the model’s deterministic contract;
- the extended output passes validation.

A from-scratch longer attempt may also serve the same Simulation, but it does not silently replace accepted output. The product should prefer checkpoint-based extension where supported.

Create Variation requires at least one physical or numerical difference. A duration-, cadence-, or field-only request should route to an eventual **Extend or retain more output** action rather than fabricate another variation.

## 3.5 Recipe versioning

Selecting among approved run profiles does not create another Recipe version.

A new Recipe version is required when a change alters the fixed scientific foundation, control meanings or transforms, required physics, validation contract, or expected interpretation enough that old and new parents cannot be inherited under one coherent specification.

---

# 4. Simulation identity and technical attempts

## 4.1 Intended Simulation

The intended Simulation exists before execution and carries:

- World and Recipe/version;
- immutable scientific specification;
- immutable numerical realization;
- parent and reference;
- exact differences;
- optional question;
- expected fields, geometry, and Lenses;
- initial observation plan;
- source and executable requirements.

Packaging creates the stable intended identity. Merely typing in the editor does not.

## 4.2 Attempt identity

Each package/launch/restart is a technical **attempt** beneath the Simulation.

| Event | Identity result |
| --- | --- |
| Queue or process retry with identical normalized scientific and numerical content | New attempt, same Simulation |
| Package regeneration caused only by location, timestamp, or equivalent nonmaterial metadata | New attempt, same Simulation |
| Checkpoint restart that continues the same numerical evolution | Restart attempt, same Simulation |
| Output-only rerun with different cadence or fields | Alternate observation attempt, same Simulation |
| Change to a physical control | New Simulation |
| Change to grid, timestep, domain, numerical method, or material source build | New Simulation |
| Change to Recipe physics | New Simulation under the appropriate Recipe/version |
| Conflicting output claiming an existing attempt identity | Conflict; fail closed |

## 4.3 Accepted backing output

The first attempt that passes the complete approved contract may become the Simulation’s backing output automatically.

A later valid attempt remains an alternate attempt until a deliberate repair, extension, or backing-selection action is approved. It never silently overwrites or rebinds the accepted Simulation.

Built-in authored Simulations may undergo deliberate presentation-asset upgrades while retaining stable Simulation identity. That is product content curation, not ordinary variation behavior.

---

# 5. Lifecycle and automatic availability

## 5.1 Distinct lifecycle facts

The backend must keep these facts distinct even when the UI groups them:

```text
intended Simulation exists
package exists
attempt queued
attempt running
process completed
expected output exists
technical integrity passed
World inspectability passed
Simulation is available
Simulation is parent-eligible
```

Do not flatten the lifecycle to one vague status string.

## 5.2 Validation stages

### A. Specification validation

Before package creation:

- parent is eligible;
- Recipe/version is supported;
- transforms resolve from the Recipe reference;
- values fall inside the absolute Recipe envelope;
- dependencies and combinations are valid;
- at least one physical or numerical Simulation difference exists;
- the chosen run profile can support the requested controls and Lenses;
- expected cost and required free space can be calculated.

### B. Deterministic package validation

Before launch:

- generated inputs reproduce the reviewed specification;
- source/executable requirements pass;
- all consumed files and hashes are recorded;
- no preexisting output conflicts;
- intended Simulation, package, and attempt identities agree;
- free-space gate passes immediately before launch.

### C. Attempt integrity

After execution:

- process start, finish, and exit evidence are present;
- normal-termination requirements pass;
- fatal floating-point flags are absent;
- generated inputs still match the reviewed package;
- restart or cancellation state is unambiguous;
- outputs remain contained in the retained attempt directory.

### D. Output completeness

- exact expected history inventory;
- exact modeled times;
- readable NetCDF;
- required dimensions, coordinates, units, and fields;
- finite required data;
- no conflicting, escaped, or silently substituted artifacts.

### E. World inspectability

- native geometry can be represented honestly;
- promised Fields and Lenses have their prerequisites;
- fixed scales and overlays resolve;
- the retained timeline supports the selected profile’s stated use;
- World-specific configuration readback and physical invariants pass;
- material boundary or damping contamination is absent or classified explicitly.

### F. Automatic Simulation availability

If A–E pass under an approved World contract, the intended Simulation becomes available automatically in its World.

A nonblocking caveat may produce **Available with caveats**. It does not force the output into an unpromoted holding area.

## 5.3 What validation does not judge

Automatic validation does not decide:

- whether the response is strong;
- whether a cloud formed;
- whether a supercell remained organized;
- whether a wave broke;
- whether the result is beautiful;
- whether the question was answered;
- whether the result supports a causal explanation;
- whether the Simulation should be pinned or featured.

Weak, absent, mixed, or disappointing responses may be scientifically useful outcomes.

## 5.4 Unpromoted experiments

The term **unpromoted experiment** is reserved for:

- non-World work;
- legacy or unassigned output;
- work produced outside an approved World contract;
- output whose intended World/Recipe identity cannot be verified;
- contract-invalid custom work retained for diagnosis;
- future Recipe-authoring experiments that have not yet become supported World content.

An approved-contract variation that passes A–E is a Simulation without another user ceremony.

---

# 6. Parent eligibility

Simulation availability and parent eligibility are separate decisions.

An available Simulation is parent-eligible only when:

1. its complete scientific and numerical specification is reconstructible;
2. its Recipe identity and contract version remain supported;
3. all absolute control values remain inside the current Recipe envelope;
4. its numerical realization is approved for inheritance or can be explicitly switched with honest difference reporting;
5. generated-input and source identities remain verifiable;
6. no blocking provenance, geometry, boundary, or output conflict exists;
7. accumulated lineage and caveats can be carried forward exactly;
8. required source assets remain present.

There is no arbitrary parent-generation limit. A fifth-generation child may remain eligible. A first-generation child may be ineligible.

## 6.1 Caveat effects

| Condition | Available Simulation | Parent-eligible |
| --- | --- | --- |
| Nonfatal underflow with finite required fields | Yes | Yes |
| Expected profile-specific resolution limitation | Yes | Yes for that approved profile |
| Multiple supported controls changed | Yes | Yes; inherited as a multi-factor state |
| Interpretive uncertainty | Yes | Yes |
| Boundary influence after the declared useful window | Yes, caveated | Usually no until reviewed |
| Legacy values outside the current Recipe envelope | Yes | No |
| Missing generated-input identity or source assets | Possibly inspectable | No |
| Incomplete required output | No | No |
| Conflicting identity or artifacts | No | No |

Controls always resolve to absolute Recipe coordinates. A 20% increase selected from a child does not multiply the child’s already-increased value unless the user explicitly enters the resulting absolute value and it remains inside the envelope.

---

# 7. Cost and run-profile contract

Every launch review shows:

- World-specific profile name and role;
- grid, spacing, timestep strategy, domain, duration, cadence, frame count, and required fields;
- rounded runtime range;
- rounded retained-storage range;
- required free space including post-run reserve;
- estimate basis:
  - **measured**;
  - **scaled from measured evidence**;
  - **uncharacterized**;
- control-dependent reasons the run may be slower;
- profile-specific scientific and visual limitations.

Runtime is a range, not a precise promise. Storage estimates include headroom for field behavior and compression uncertainty.

The estimator may learn from local completed attempts, but later calibration does not rewrite the estimate that was shown at launch or alter the immutable Simulation specification.

## 7.1 Shared role labels

- **Quick:** least expensive profile that still answers a stated bounded question.
- **Standard:** ordinary experimental default for that Recipe.
- **Presentation:** authored high-fidelity profile intended for detailed viewing and durable reference content.
- **Match parent:** exact inherited numerical realization and observation plan.
- **Extended:** longer or wider profile for a specific question; never a generic “higher” tier.

The UI always displays the exact World-specific contract beside the role.

---

# 8. Trade Cumulus variation contract

## 8.1 Recipe

**Recipe:** Canonical BOMEX Trade Cumulus  
**World reference:** Canonical BOMEX Baseline

The Recipe fixes the canonical BOMEX foundation unless a supported control explicitly changes it:

- thermodynamic, moisture, and wind reference profiles;
- prescribed surface exchange;
- subsidence, cooling, drying, and geostrophic forcing;
- Coriolis and momentum treatment;
- horizontally periodic domain;
- reversible nonprecipitating moist physics;
- deterministic perturbation method;
- required cloud, motion, thermodynamic, forcing, and transport fields;
- fixed Trade Cumulus scales and Updraft Lens contract.

A changed-forcing child is a **BOMEX-based Trade Cumulus sensitivity**, not another canonical BOMEX baseline.

## 8.2 Eligible parents

Eligible:

- Canonical BOMEX Baseline;
- More Moisture;
- later available user Simulations whose exact Recipe specification remains inside this contract.

Ineligible:

- legacy Results without verified stable Simulation and Recipe identity;
- arbitrary observed-sounding experiments;
- profile or forcing configurations outside the Recipe envelope;
- output with missing generated-input or fixed-assumption identity;
- simulations created under a superseded incompatible Recipe contract.

## 8.3 Surface-exchange controls

These are ordinary controls. They are independent, so the user can explore both total forcing and the balance between heat and moisture supply.

| Control | Recipe-reference mapping | Supported envelope | Evidence and product treatment |
| --- | --- | --- | --- |
| **Surface moisture supply** | Absolute factor applied to canonical `5.2e-5 g/g m/s` | `0.50–1.75×`; named stops at `0.50, 0.75, 1.00, 1.25, 1.50, 1.75` | Baseline and `1.50×` are measured. Full envelope requires bounded endpoint characterization. |
| **Surface sensible heating** | Absolute factor applied to canonical `8.0e-3 K m/s` | `0.50–1.50×`; named stops at `0.50, 0.75, 1.00, 1.25, 1.50` | Scientifically grounded but not yet measured in the product. |

The review shows both actual flux values and a concise derived **heat-to-moisture supply balance**. Negative fluxes and values outside the envelope are blocked.

## 8.4 Atmospheric-structure controls

These are ordinary or advanced curated profile transforms. They are calculated from the Recipe reference, not from the latest parent profile.

| Control | Exact transform | Supported envelope | Placement and validation |
| --- | --- | --- | --- |
| **Boundary-layer moisture** | Add a vertically tapered total-water offset below the inversion; zero perturbation above the inversion top | `−1.5 to +1.5 g/kg` | Ordinary. Block initial supersaturation or negative water vapor. |
| **Trade inversion height** | Shift the authored inversion base and top together, remapping the reference profile continuously | `−300 to +400 m` | Ordinary. Preserve minimum cloud layer and free-tropospheric depth. |
| **Trade inversion strength** | Scale the reference liquid-water-potential-temperature jump while preserving the subcloud profile and upper anchor | `0.50–1.50×` | Ordinary. Require static stability and continuous profile. |
| **Free-tropospheric humidity** | Scale the reference relative-humidity deficit above the inversion, then derive qv from pressure and temperature | deficit factor `0.50–2.00×` | Ordinary. Bound RH to `5–95%` and prevent initial cloud outside a separately authored cloudy-initial-state Recipe. |
| **Cloud-layer wind shear** | Scale departures from the 0–3 km layer-mean reference wind while preserving that mean | `0–2.00×` | Advanced. Show resulting shear and wind profile. |

The product shows the resulting profiles, inversion markers, initial relative humidity, static stability, and wind shear before launch.

## 8.5 Large-scale-forcing controls

The large-scale forcings remain physically distinct. The user may change them together through a named **Large-scale forcing strength** control or reveal the individual advanced controls.

| Control | Transform | Supported envelope |
| --- | --- | --- |
| **Large-scale forcing strength** | Scale subsidence, prescribed cooling, and prescribed drying together from the Recipe reference | `0.75–1.25×` ordinary; `0.50–1.50×` advanced |
| **Subsidence strength** | Scale the complete authored subsidence profile | `0.50–1.50×` advanced |
| **Prescribed cooling** | Scale the complete authored cooling profile | `0.50–1.50×` advanced |
| **Prescribed drying** | Scale the complete authored drying profile | `0.50–1.50×` advanced |

Changing individual components is a legitimate multi-factor balance experiment, not an error. The preview must show the complete resulting tendency profiles and must not imply steady-state preservation.

## 8.6 Fixed or separate-Recipe choices

The following do not belong in this Recipe’s variation surface:

| Proposed change | Decision |
| --- | --- |
| Heterogeneous or patch surface forcing | A separate Trade Cumulus Recipe because it changes organization, symmetry, and domain requirements |
| Precipitating microphysics | A separate Recipe or World-level extension; the canonical Recipe remains nonprecipitating |
| Arbitrary sounding-level editing | Recipe authoring or Fun With Soundings, not World variation |
| Free-form CM1 numerics | Replaced by approved run profiles |
| Arbitrary perturbation seed | A future Replicate action, not an environmental Control |

## 8.7 Trade Cumulus run profiles

All profiles retain the required Trade Cumulus Explore and Updraft Lens fields, including cloud liquid, moisture, thermodynamics, winds, turbulence/transport support, surface fluxes, cloud-water path, and required coordinates.

| Role and name | Numerical realization | Observation plan | Expected local cost | Evidence | Scientific use |
| --- | --- | --- | --- | --- | --- |
| **Quick — Three-hour field response** | `64×64×75`; `100×100×40 m`; target `dt=3 s` | `10,800 s`; `180 s`; 61 histories | about `10–20 min`; `0.8–1.1 GB` | Scaled from measured six-hour lower-resolution runs | Cloud onset, early lifecycle, and first response; not a full steady-period assessment |
| **Standard — Four-hour experiment** | `64×64×75`; `100×100×40 m`; target `dt=3 s` | `14,400 s`; `120 s`; 121 histories | about `15–30 min`; `1.6–2.2 GB` | Scaled from measured lower-resolution runs | Ordinary physical experiments and comparisons |
| **Full-cycle — Six-hour experiment** | Same as Standard | `21,600 s`; `120 s`; 181 histories | measured near reference at `22–23 min`; about `2.5–3.2 GB` | Evidence-backed for Baseline and More Moisture | Canonical six-hour evolution and longer statistics |
| **Presentation — Detailed four-hour field** | `96×96×100`; about `66.7×66.7×30 m`; target `dt=2 s` | `14,400 s`; `60 s`; 241 histories | measured `68–124 min`; `9.08–9.34 GB` | Evidence-backed | Detailed authored cloud structure and smooth playback |
| **Extended — Wide-domain organization** | `128×128×75`; `100×100×40 m`; target `dt=3 s`; 12.8 km horizontal domain | `14,400 s`; `120 s`; 121 histories | provisional `60–120 min`; `6.5–9 GB` | Requires characterization | Domain-size and organization sensitivity; not the ordinary default |

Control choices may alter adaptive timestep behavior. The prelaunch range must widen when prior local evidence shows that a control state runs materially slower.

## 8.8 Trade Cumulus dependencies and comparison rules

- A controlled surface-moisture experiment requires every other physical control and the numerical realization to match.
- Changing Surface moisture supply while switching Presentation to Standard creates a mixed variation.
- When a lower-cost controlled pair is desired, Cloud Chamber should offer to create or select a same-profile reference, not pretend the Presentation parent is numerically matched.
- Atmospheric profile transforms must preserve positive pressure, finite values, static stability where the Recipe requires it, and no unintended initial cloud.
- Inversion changes must retain enough vertical domain above the inversion.
- Large-scale forcing profiles must retain their authored vertical support and smoothness.
- No physical-response threshold is required for availability. No cloud or a weak response may be the result.

## 8.9 Trade Cumulus validation

In addition to shared validation:

- exact fixed-assumption and Recipe-reference identity;
- all selected transforms reproduced in generated profiles and forcing;
- intended surface fluxes confirmed in input and available diagnostics;
- periodic domain and approved nonprecipitating physics;
- required histories and forcing-diagnostic cadence;
- native coordinates and finite required fields;
- Updraft Lens fields, fixed scale, cloud threshold, and wind context;
- profile-derived RH, stability, and inversion checks;
- no silent fallback to another forcing or profile.

## 8.10 Trade Cumulus Compare entry

After availability, offer:

1. parent;
2. Canonical BOMEX Baseline;
3. same-profile related Simulations;
4. other compatible Trade Cumulus Simulations.

Pair review labels the relationship as controlled, multi-factor, numerical, replicate, or mixed before loading frames.

---

# 9. Mountain Waves variation contract

## 9.1 World and Recipe structure

Mountain Waves contains two explicit Recipes:

```text
Mountain Waves
├── Dry Ridge Mechanics
└── Boulder Moist Wave
```

No additional user-facing “Recipe family” concept is needed.

The Recipes share the World, terrain-aware x-z Explore vocabulary, lifecycle, and variation shell. They do not share one interchangeable atmosphere or one universal control set.

Dry Ridge and Boulder Windstorm are not a dry/moist pair. They differ in source atmosphere, terrain, domain, grid, duration, and scientific purpose.

## 9.2 Disposition of existing Mountain Waves variation work

Retain:

- parent-based creation;
- stable intended Simulation identity;
- exact lineage;
- categorized differences;
- deterministic packages;
- queue/run integration;
- Activity and History evidence;
- strict native-output validation;
- automatic Simulation availability;
- accepted-descendant reuse;
- the real Broader Boulder Ridge Simulation.

Replace or revise:

- technical bounds such as 6 km ridges, ±100 m/s winds, arbitrary theta, and arbitrary qv are not product ranges;
- ridge center is not an ordinary scientific control;
- relative multipliers must resolve to absolute Recipe-reference transforms;
- raw per-level sounding editing is removed from ordinary World variation;
- “Make dry” becomes a defined **Boulder dry-air counterpart**, not an implied comparison to Dry Ridge;
- parent eligibility is recalculated under the durable Recipe envelopes;
- numerical and observation profiles are separated from atmospheric controls.

Existing inspectable variations remain Simulations. A retained variation outside the new Recipe envelope is labeled **Legacy-contract Simulation**: Explore and Compare remain available, but it is not parent-eligible.

## 9.3 Shared Mountain Waves previews and constraints

Every Mountain Waves editor shows:

- terrain profile and maximum slope;
- upstream wind, moisture, and potential-temperature profiles;
- dry and, where applicable, moist stability;
- critical or near-critical levels;
- nondimensional mountain height `Nh/U` or its layer-aware analogue;
- nonhydrostatic-width parameter `Na/U` where meaningful;
- expected terrain resolution;
- upstream/downstream domain clearance;
- advective travel and periodic-wrap risk;
- model-top and damping separation;
- expected runtime, storage, and frame count.

Regime labels—linear/weakly nonlinear, breaking likely, blocking likely, trapped/ducted possible—are interpretation aids. They are not automatic causal conclusions.

## 9.4 Dry Ridge Mechanics Recipe

### Purpose

Explore dry, two-dimensional terrain-forced gravity waves, including transitions among weak waves, nonlinear amplification, wave breaking, blocking, critical-level interaction, and trapped-wave structure.

### Parent eligibility

Dry Ridge should become an eligible parent. This is worth implementing because it provides the cheapest, clearest laboratory for mountain-wave mechanics.

Eligibility requires an exact hash-verified generator for the source-defined analytic atmosphere and terrain. Sampling the source formula into an external sounding is not silently treated as exact inheritance unless equivalence is demonstrated and recorded.

### Ordinary controls

| Control | Supported envelope | Product mapping |
| --- | --- | --- |
| **Ridge height** | `100–2,500 m` | Absolute height of the analytic bell ridge |
| **Ridge half-width** | `0.5–20 km` | Absolute half-width of the analytic bell ridge |
| **Cross-ridge wind speed** | `5–30 m/s` at the reference lower level | Uniform-wind state or base value for an authored shear profile |
| **Dry stability** | `N = 0.005–0.020 s⁻¹` | Exact analytic dry theta/pressure profile |

### Advanced controls

| Control | Supported envelope | Product mapping |
| --- | --- | --- |
| **Wind shear through 10 km** | total change `−20 to +20 m/s` | Smooth linear or authored two-layer profile; critical levels shown explicitly |
| **Layered stability** | lower and upper `N = 0.005–0.020 s⁻¹`; transition `2–12 km` | Continuous two-layer analytic profile for propagating versus trapped-wave questions |
| **Stability-transition sharpness** | authored smooth widths `0.5–3 km` | Controls the smooth transition; no arbitrary point edits |

Ridge center remains fixed in the generated domain. Reversing uniform flow over a symmetric ridge is a mirrored coordinate presentation, not a meaningful ordinary control.

### Absolute Recipe envelope

The generator also enforces:

- analytic maximum terrain slope `≤0.50`; warn above `0.35`;
- at least 5 horizontal cells per half-width in Quick and 10 in Standard/Presentation;
- nondimensional mountain height broadly within `0.1–4.0` for supported product interpretation;
- `Na/U` within a domain/profile-supported range, ordinarily `0.25–20`;
- sufficient model top and damping depth for the selected vertical wavelength;
- no unresolved terrain or boundary wrap.

The envelope deliberately includes nonlinear, breaking, and blocked regimes. Those are meaningful outcomes, not invalid simulations.

### Dry Ridge run profiles

The domain and grid count are generated from terrain width, wind, duration, boundary-tail, and wrap constraints. Reference-case costs are:

| Role | Resolution and timing rules | Reference-case cost | Evidence and use |
| --- | --- | --- | --- |
| **Quick — Mechanics check** | target `dx,dz ≤200 m`; at least 5 cells per half-width; target `dt≤2 s`; cadence no coarser than `180–216 s` | measured about `10 s`, `9 MB` for the source case | Fast structure and regime check; sparse playback |
| **Standard — Wave evolution** | target `dx,dz ≤100 m`; at least 10 cells per half-width; target `dt≤1 s`; cadence `60 s` | about `80–110 s`, `45–65 MB` for the source case | Ordinary experiments |
| **Presentation — Smooth wave evolution** | Standard numerical realization; cadence `30 s` | measured about `85 s`, `95 MB` for the source case | Authored playback and detailed inspection |
| **Extended — Long or trapped-wave evolution** | Standard numerical realization; duration determined by at least 12 terrain advective times and boundary-wrap gate | Control-dependent | Ducting, delayed breaking, or longer adjustment |

Duration is generated from the terrain advective time `a/U`, with an absolute floor sufficient to reproduce the reference wave evolution. A wider/slower case is not forced into the 2,160-second source duration if it has not had time to develop.

### Dry Ridge validation

- exact analytic source/profile generator and readback;
- terrain formula, binary identity, and native geometry;
- dry hydrostatic atmosphere and selected stability profile;
- wind and critical-level readback;
- active model top and damping separation;
- domain-tail and periodic-wrap checks;
- required dry Mountain Waves fields and coordinates;
- finite native data and exact times.

Wave amplitude or breaking is not an acceptance threshold.

## 9.5 Boulder Moist Wave Recipe

### Purpose

Explore how terrain, a source-backed upstream atmosphere, wind profile, stability, and moisture interact to produce mountain waves, wave cloud, evaporation, wave amplification, and downslope response.

### Eligible parents

Eligible:

- Boulder Windstorm — Moist Reference;
- Broader Boulder Ridge;
- later available descendants inside the Boulder Recipe envelope.

Dry Ridge is not a parent for this Recipe.

### Terrain controls

| Control | Supported envelope | Notes |
| --- | --- | --- |
| **Ridge height** | `0.5–3.5 km` | Includes weak through strongly nonlinear terrain; derived regime preview required |
| **Ridge half-width** | `5–30 km` | Domain and resolution expand as required |
| **Terrain profile** | authored bell ridge only in this Recipe | Other shapes require another Recipe contract |

Ridge center remains a generated-domain placement decision, not an ordinary Control.

### Wind controls

| Control | Exact transform | Supported envelope |
| --- | --- | --- |
| **0–4 km mean wind** | Translate the complete Recipe-reference cross-ridge wind profile to the selected low-level mean while retaining its resolved smaller-scale structure | `0–50 m/s` |
| **0–10 km shear** | Adjust the complete profile so the resolved wind change from 0 to 10 km equals the selected value | `−30 to +50 m/s` |

Critical levels, direction reversals, layer shear, and maximum wind are shown before launch. Critical levels are allowed because they are central to mountain-wave behavior; unsupported grid/domain combinations are blocked.

### Moisture controls

Moisture transforms use relative humidity derived from pressure and temperature. A raw qv multiplier is not the durable product control.

| Control | Exact transform | Supported envelope |
| --- | --- | --- |
| **0–4 km mean RH** | Shift the Recipe-reference RH profile to the selected layer mean while preserving vertical structure and an authored smooth transition | `0–100%` |
| **4–10 km mean RH** | Independently shift the Recipe-reference RH profile to the selected layer mean with authored smooth transitions at 4 and 10 km | `0–100%` |
| **Boulder dry-air counterpart** | Set qv to zero while retaining Boulder terrain, wind, thermodynamics, physics, domain, and numerics | authored extreme state |

The displayed RH controls are actual layer means rather than generic multipliers. RH is
bounded physically, qv is solved against the final hydrostatic pressure and temperature
profile, and transitions remain smooth.

The dry-air counterpart is a valid controlled moisture contrast with Boulder Moist. It is not Dry Ridge and must never be presented as such.

### Stability controls

| Control | Exact transform | Supported envelope |
| --- | --- | --- |
| **Lower-layer stability** | Scale the Recipe-reference theta gradient below the authored transition while preserving surface theta | `0.50–1.50×` |
| **Midlevel stability** | Scale the Recipe-reference theta gradient through the wave-critical middle layer with continuous anchors | `0.50–1.50×` |
| **Upper-layer stability** | Scale the Recipe-reference upper gradient below damping | `0.50–1.50×` advanced |

The generated profile must remain hydrostatically coherent and statically stable. Arbitrary per-level theta editing is not part of World variation.

### Profile-editor decision

The existing per-level table is not retained as an advanced product control. It allows technically valid but scientifically arbitrary profiles and causes parent-of-parent drift that cannot be bounded by Recipe semantics.

Future custom profile work may occur through Recipe authoring or Fun With Soundings and remain an Experiment until a new Recipe contract is approved.

### Boulder run profiles

Reference geometry is 220 km by 25 km with source-backed terrain and atmosphere. Domain and grid count expand when terrain/wind controls require it.

| Role | Numerical realization | Observation plan | Expected local cost | Evidence and use |
| --- | --- | --- | --- | --- |
| **Quick — Wave/cloud response** | `220×1×125`; `1,000 m × 200 m`; target `dt=2 s` | `4,000 s`; `200 s`; 21 histories | measured about `65 s`, `46 MB` | Fast response and configuration check |
| **Standard — Full Boulder experiment** | same nominal resolution; domain may expand; target `dt=2 s` | `7,200 s`; `120 s`; 61 histories | provisional `2–4 min`, `120–200 MB` near reference | Ordinary terrain, wind, moisture, and stability experiments |
| **Presentation — Detailed Boulder evolution** | `440×1×250`; `500 m × 100 m`; target `dt=1 s` | `7,200 s`; `30 s`; 241 histories | measured about `26 min`, `1.24 GB` | Detailed wave, cloud, and evaporation structure |
| **Extended — Long adjustment** | Standard or Presentation resolution; duration based on advective and boundary constraints | Control-dependent | Requires estimate from selected configuration | Delayed breaking, persistent cloud, or longer downslope evolution |

### Boulder dependencies and invalid combinations

- Moisture transforms are applied after thermodynamic transforms so RH is calculated against the final temperature and pressure.
- Stability transforms are Recipe-referenced and preserve continuity.
- A requested profile that produces static instability, impossible RH, nonfinite values, or unsupported critical-level/domain interaction is blocked.
- Terrain height/width and wind jointly determine nondimensional regime and domain requirements.
- A wide ridge or slow flow may require a larger domain and longer duration; profile selection updates automatically and visibly.
- “Make dry” is never compared to Dry Ridge by default.

### Boulder validation

- source-backed reference identity and exact transform parameters;
- sounding height/pressure identity and hydrostatic consistency;
- RH, qv, theta, and static-stability checks;
- critical-level and wind readback;
- native two-dimensional `v=0` contract;
- terrain formula and binary readback;
- physical terrain-following heights and active top;
- domain and boundary-wrap checks;
- moist Mountain Waves fields, geometry, and Lens prerequisites;
- exact times and finite native data.

Initial saturation, wave breaking, or a weak cloud response is not automatically invalid. It is reported as part of the resulting atmosphere.

## 9.6 Mountain Waves Compare entry

After availability:

1. parent;
2. the Simulation’s Recipe reference;
3. same-Recipe related Simulations;
4. cross-Recipe Mountain Waves Simulations as ordinary structural comparisons.

Cross-Recipe Compare is labeled **Different Recipes** and never presented as a controlled dry/moist experiment.

---

# 10. Supercells variation contract

## 10.1 Recipe

**Recipe:** Idealized Isolated Supercell  
**World reference:** Quarter-Circle Supercell

The Recipe fixes unless an approved control changes them:

- horizontally homogeneous idealized environment;
- source-locked thermodynamic profile family;
- source-locked hodograph/profile generator;
- one deterministic warm-bubble initiation;
- Morrison double-moment microphysics;
- flat terrain and no surface heat/moisture forcing;
- lateral boundaries, damping, and translating frame;
- required three-dimensional and two-dimensional fields;
- the three current Supercells Lenses;
- no storm-object lineage or tornado diagnosis.

Changing microphysics, adding terrain, adding surface fluxes, initiating a line of storms, or using multiple bubbles requires another Recipe.

## 10.2 Eligible parents

Eligible:

- Quarter-Circle Supercell;
- Straight-Line Hodograph Supercell;
- later available descendants inside the Recipe envelope.

Parent eligibility does not require the resulting storm to look classic or to remain intense. It requires exact reconstructibility, contract validity, and honest domain/output evidence.

## 10.3 Kinematic controls

### Hodograph geometry

The product exposes authored hodograph families, not arbitrary wind-profile points:

- **Straight line**;
- **Quarter circle**;
- **Half circle**.

Each profile generator preserves, unless another control changes them:

- the selected 0–6 km endpoint shear vector;
- the selected 0–6 km layer-mean wind;
- constant wind above the selected shear depth;
- model translation.

Straight and Quarter Circle are already represented by the real controlled pair. Half Circle is scientifically grounded and requires bounded package/run characterization before enablement.

### Shear controls

| Control | Exact transform | Supported envelope |
| --- | --- | --- |
| **0–6 km shear magnitude** | Scale hodograph deviations while preserving layer-mean wind and selected geometry | `20–45 m/s`; named stops `20, 25, 32, 35, 40, 45` |
| **Low-level turning depth** | Apply the authored curved portion through the selected depth, with continuous straight shear above | `1–3 km` |
| **Low-level shear concentration** | Redistribute a bounded fraction of total shear below 2 km while preserving total 0–6 km shear and mean wind | `0.20–0.60` of total vector change below 2 km |
| **6–12 km upper-level shear** | Add an authored upper-level vector aligned or crosswise to the 0–6 km shear while preserving lower profile | `0–20 m/s` advanced |

The preview shows the full hodograph, 0–1, 0–3, and 0–6 km shear, selected storm-relative-helicity estimates, layer-mean wind, and translating-frame relationship. Derived metrics are evidence, not Controls.

## 10.4 Thermodynamic controls

Thermodynamic controls use a source-locked analytic profile generator. Cloud Chamber does not expose arbitrary sounding points or a raw CAPE slider detached from a coherent profile.

| Control | Product meaning and generator constraint | Supported envelope |
| --- | --- | --- |
| **Instability** | Adjust positive buoyancy magnitude while preserving the selected authored vertical buoyancy-distribution shape | target surface-based CAPE `1,500–3,500 J/kg` |
| **Buoyancy distribution** | Authored **low-level weighted**, **reference**, or **deep weighted** profile families at the selected CAPE | three curated profiles |
| **Cloud-base height** | Adjust low-level moisture and temperature coherently while solving for the target LCL and preserving hydrostatic structure | target LCL `500–1,500 m AGL` |
| **Midlevel humidity** | Scale RH deficit through the authored 3–7 km layer with smooth transitions | target layer-mean RH `30–80%` |
| **Cap strength** | Adjust the authored stable layer while preserving the rest of the profile and reporting resulting CIN | target CIN `0–100 J/kg` |

The generator reports CAPE, CIN, LCL, freezing level, profile RH, and hydrostatic consistency. Combinations that cannot satisfy the requested metrics within the Recipe’s thermodynamic family are blocked rather than approximated silently.

## 10.5 Deterministic initiation controls

Initiation is a supported Recipe choice, not an atmospheric condition.

| Control | Supported envelope |
| --- | --- |
| **Warm-bubble amplitude** | `0.5–3.0 K` potential-temperature perturbation |
| **Horizontal radius** | `5–15 km` |
| **Vertical radius/depth** | `1–3 km` |
| **Location** | fixed authored interior location; may move only through an explicit advanced coordinate control that preserves boundary clearance |

The product supports one deterministic bubble. Multiple bubbles, random thermal fields, boundary lines, and moving initiation are separate Recipes or experiment structures.

A weak trigger that fails to initiate sustained convection may still produce a valid Simulation. It is not silently retried with stronger forcing.

## 10.6 Fixed choices and separate Recipes

| Proposed change | Decision |
| --- | --- |
| Microphysics scheme | Separate Recipe or explicit physics-sensitivity contract |
| Terrain or surface fluxes | Separate Recipe |
| Multiple storms or line initiation | Separate Recipe |
| Model translation | Hidden derived/fixed numerical choice; kinematic transforms preserve layer-mean wind so translation remains comparable |
| Tornado strength, probability, or forecast | Not a Control |
| Arbitrary sounding or hodograph points | Recipe authoring, not World variation |
| Cross-Simulation storm identity | Not inferred |

## 10.7 Supercells run profiles

Every profile retains the fields required by Rotating Updraft, Cloud and Precipitation, and Low-Level Interactions. Lower-cost profiles change resolution and observation density, not the semantic meaning of the Lenses.

| Role and name | Numerical realization | Observation plan | Expected local cost | Evidence | Lens limits |
| --- | --- | --- | --- | --- | --- |
| **Quick — Two-hour storm response** | `120×120×40`; `1,000×1,000×500 m`; target `dt=6 s` | `7,200 s`; `300 s`; 25 histories | about `10–15 min`; `0.4–0.7 GB` | Runtime measured at `9.2 min` for 9 histories; denser output estimate scaled | All three Lenses show broad resolved structure; low-level detail is explicitly coarse |
| **Standard — Three-hour supercell experiment** | `160×160×50`; `750×750×400 m`; target `dt=4.5 s` | `10,800 s`; `180 s`; 61 histories | provisional `45–75 min`; `2–3 GB` | Scaled from measured Quick and Presentation evidence; requires direct characterization | Ordinary default; all three Lenses supported |
| **Presentation — Detailed three-hour storm** | `240×240×60`; `500×500×333 m`; target `dt=3 s` | `10,800 s`; `120 s`; 91 histories | measured `3.4–3.75 h`; `8.6–8.9 GB` | Evidence-backed | Detailed authored inspection |
| **Extended — Four-hour longevity** | Standard numerical realization by default | `14,400 s`; `180 s`; 81 histories | provisional `60–100 min`; `3–4 GB` | Requires characterization | Longevity, cycling, and later outflow evolution; boundary/domain review required |

The Quick profile does not claim tornado-scale or near-surface vortex resolution. The Presentation profile does not make those claims either.

## 10.8 Supercells dependencies and comparison rules

- A controlled hodograph-shape experiment requires matched shear magnitude, thermodynamics, initiation, numerical realization, and observation plan.
- Shear magnitude is scaled while preserving mean wind and geometry; it is not implemented by multiplying raw u/v values about zero.
- Thermodynamic transforms are solved jointly and may constrain each other.
- Initiation changes are recorded separately from environmental changes.
- Changing hodograph geometry, CAPE, and bubble strength together is a multi-factor experiment.
- Selecting Standard from a Presentation parent while changing an atmospheric control produces a mixed variation.
- The fixed storm inspection region may be unavailable or adjusted for a child. Full Domain remains the honest fallback. No frame-following storm tracker or cross-Simulation storm identity is invented.
- Failure to produce a sustained supercell is a valid response when configuration and output remain coherent.

## 10.9 Supercells validation

In addition to shared validation:

- exact source/customization identity;
- full hodograph readback and derived shear metrics;
- thermodynamic generator readback, hydrostatic consistency, CAPE/CIN/LCL, and RH checks;
- deterministic warm-bubble shape, amplitude, and location;
- domain, boundary, damping, and translating-frame contract;
- required 3-D and 2-D fields, coordinates, units, and finite data;
- native horizontal and vertical sections;
- all three Lens prerequisites and fixed scales;
- exact history times and retained field inventory;
- boundary interaction classified against the declared useful window.

No automatic threshold for updraft strength, UH, reflectivity, precipitation, rotation, or storm longevity determines Simulation availability.

## 10.10 Supercells Compare entry

After availability:

1. parent;
2. Quarter-Circle Supercell reference;
3. same-profile kinematic or thermodynamic relatives;
4. other compatible Supercells Simulations.

Compare maps modeled seconds, physical coordinates, compatible Lenses, and local native evidence. It never assigns object identity to storms, splits, mergers, or later convective structures.

---

# 11. Failure, cancellation, caveat, and missing-content semantics

## 11.1 Packaged but not launched

The intended Simulation and package remain in Activity with:

- name, parent, question, differences, and cost review;
- **Run**, **Delete package**, and technical-detail actions where valid.

It is not an available Simulation.

## 11.2 Queued or running

Activity shows attempt state, start/wait information, and **Cancel** only when cancellation can complete.

The user can leave and return without losing intended identity or context.

## 11.3 Cancellation

Cancellation terminates the attempt, not the intended Simulation.

Partial output remains attached to the attempt for diagnosis. It does not automatically become a Simulation. A later unchanged retry remains beneath the same intended Simulation.

## 11.4 Failed process

A failed attempt remains in History with:

- failure reason;
- logs and output inventory;
- whether retry is allowed;
- whether generated inputs still match;
- exact relationship to other attempts.

Retry does not create another Simulation unless configuration changes.

## 11.5 Completed but incomplete output

Incomplete required histories or fields fail automatic availability.

The attempt may support bounded technical inspection, but the product does not present it in the World’s Simulations collection or let it become a parent.

A restart or retry may later complete the same intended Simulation.

## 11.6 Generated-input mismatch

Any mismatch between reviewed specification, package hashes, launch inputs, and completed-run inputs is a conflict.

Fail closed. Do not infer which configuration “probably” ran.

## 11.7 Caveated but inspectable output

Nonblocking caveats may include:

- known underflow with finite required data;
- profile-specific coarse resolution;
- nearest native plane/time mapping;
- late boundary influence outside the declared useful window;
- known damping-layer overlap;
- interpretive limitations.

The Simulation may become available with visible caveats. Parent eligibility is decided separately.

## 11.8 Conflicting outputs

Two outputs may not silently claim the same attempt or backing identity.

Conflicts preserve all records, fail automatic availability, and require a deliberate repair or backing-selection action outside ordinary variation.

## 11.9 Missing retained output

Stable Simulation identity, lineage, Notes, Saved Views, and Saved Comparisons remain.

The Simulation becomes unavailable rather than disappearing. It is not parent-eligible until output/source assets are repaired or reimported through an approved workflow.

---

# 12. Activity, History, Explore, and Compare contract

This document does not redesign issue #394, but it supplies the lifecycle facts #394 must represent.

## Activity

Activity owns current actionable work:

- packaged;
- queued;
- running;
- completed awaiting validation;
- completed awaiting ingest where applicable;
- available with caveats and ready to inspect;
- failed, cancelled, incomplete, or conflicted;
- recently completed.

Cards lead with intended Simulation identity, not run ID.

## History

History preserves:

- intended Simulation;
- all technical attempts;
- exact configuration and differences;
- question;
- validation decisions;
- availability and parent eligibility;
- retained/missing storage state;
- retry, restart, extension, and alternate-attempt relationships.

## Explore

When automatic availability succeeds, **Explore** is the primary action.

## Compare

Offer **Compare to parent** first and **Compare to World reference** second. Pair review shows configuration layers and relationship classification before interpretation.

## Create another variation

The action appears only when parent eligibility passes. An ineligible Simulation explains why.

---

# 13. Implementation sequence

## 13.1 Approve and record issue #435 decisions

Adopt this document, or an approved decision comment containing the same substantive contract, as the durable three-World variation authority.

Do not create a separate thin “first-controls” document that silently narrows these decisions.

## 13.2 Implement issue #394 next

Issue #394 is the highest-risk-reducing next increment because the three-World product still lacks one coherent lifecycle surface for:

- intended Simulations;
- packages and attempts;
- retries and restarts;
- completed output;
- validation;
- automatic Simulation availability;
- caveats and conflicts;
- parent eligibility;
- unpromoted non-World experiments.

Implement #394 against this contract using existing Mountain Waves records, existing World-owned content, Fun With Soundings experiments, and fixtures. Do not add new scientific controls in #394.

## 13.3 Shared variation envelope and Mountain Waves migration

Next, establish the common typed variation/attempt/validation envelope and migrate the existing Mountain Waves workflow.

This increment should:

- preserve existing real content and run history;
- implement both Mountain Waves Recipe identities;
- add exact Dry Ridge parent generation;
- replace technical bounds with durable control contracts;
- replace raw profile editing with curated transforms;
- prove the shared shell without running a new control campaign unless explicitly authorized.

Mountain Waves is the correct first migration because it already exercises parent inheritance, package creation, execution, automatic availability, and parent reuse.

## 13.4 Trade Cumulus implementation

Implement the complete Trade Cumulus control architecture, not a one-control product dead end.

Engineering may stage the work internally, but the user-facing contract should converge on:

- surface exchange;
- atmospheric structure;
- wind shear;
- large-scale forcing;
- all approved run profiles;
- exact comparison classification.

Before enabling an unmeasured control envelope, perform only the bounded endpoint and Standard-profile characterizations needed to validate package generation, cost, fields, and profile coherence. Do not run an unrestricted sweep.

## 13.5 Supercells implementation

Implement the full kinematic, thermodynamic, and deterministic-initiation contract with source-locked profile generators.

Characterize the Standard profile and the bounded endpoints needed to verify each generator. Do not require Presentation runs for every control combination.

## 13.6 Durability and acceptance

After all three Worlds use the shared contract, complete:

- protected content and dependency-aware cleanup;
- repair/reimport and backing-attempt selection;
- measured cost-model calibration;
- personal end-to-end acceptance on the target machine.

---

# 14. Decisions explicitly rejected

- A universal CM1 parameter editor.
- A generic low/medium/high selector with hidden World differences.
- One variable per wizard as the product model.
- Silent parent-to-child profile downgrades.
- Treating a numerical-profile change as a controlled physical experiment.
- Treating output cadence alone as another Simulation.
- Manual promotion ceremony for every contract-valid World variation.
- Automatic parent eligibility for every readable Simulation.
- Parent-generation caps instead of absolute Recipe envelopes.
- Compounding relative multipliers through lineage.
- Raw Mountain Waves per-level profile editing as an ordinary World control.
- Calling the Boulder dry-air counterpart the Dry Ridge Simulation.
- Restricting Supercells permanently to the existing two hodographs.
- Requiring a strong or visually exciting response for Simulation availability.
- Automatic causal explanation.
- Cross-Simulation storm-object identity.
- A new Cloud World or public/cloud-compute architecture as part of this work.

---

# 15. Evidence status summary

| Area | Evidence-backed now | Characterization required before full enablement |
| --- | --- | --- |
| Trade Cumulus | Baseline/1.5× moisture pair; lower-resolution six-hour runs; Presentation pair; required fields and Updraft Lens | sensible heat, profile transforms, shear, large-scale-forcing endpoints, Standard and Wide-domain direct cost |
| Dry Ridge | source and Presentation numerical profiles; native terrain-aware validation | exact editable source generator; broad control-envelope endpoints; layered wind/stability profiles |
| Boulder Moist | source and Presentation profiles; Broader Boulder Ridge; exact variation lifecycle | durable moisture/stability transforms; full terrain/wind envelope; Standard direct cost |
| Supercells | Quarter/straight controlled pair; official Quick benchmark; Presentation pair; three Lenses | half-circle generator; shear endpoints; thermodynamic generator; initiation envelope; Standard and Extended direct cost |

Characterization validates implementation and envelope safety. It does not reopen the product decision that these are the meaningful control families.

---

# 16. PM questions

No unanswered PM question is required to approve the architecture.

The material choices are made here:

- complete durable control families rather than a minimal first-control scope;
- automatic availability after strict contract validation;
- parent eligibility as a separate gate;
- two Mountain Waves Recipes;
- full Supercells kinematic, thermodynamic, and initiation controls;
- issue #394 next;
- bounded implementation without narrowing the durable product contract.

The remaining work is scientific/package characterization and implementation, not another product-taxonomy cycle.

---

# 17. Evidence references

Repository authority and implementation evidence:

- `NORTH_STAR.md`
- `docs/product/PRODUCT_VISION.md`
- `docs/product/APPLICATION_SEMANTICS.md`
- `docs/product/MVP.md`
- `docs/product/CURRENT_PRODUCT_SEQUENCE.md`
- `docs/product/TRADE_CUMULUS_PRODUCT_SLICE.md`
- `docs/current/CURRENT_STATE.md`
- `docs/current/CURRENT_ARCHITECTURE.md`
- issue #394
- issue #435
- PR #412 — Mountain Waves World and variation lab
- PR #425 — Trade Cumulus and Mountain Waves presentation runs
- PR #430 — Supercells Presentation run
- PR #444 — ordinary World-aware Compare and the controlled Supercells pair
- PR #445 — Saved Comparisons

Primary scientific framing used in the control architecture:

- Siebesma et al. (2003), *A Large Eddy Simulation Intercomparison Study of Shallow Cumulus Convection*.
- Weisman and Rotunno (2000), *The Use of Vertical Wind Shear versus Helicity in Interpreting Supercell Dynamics*.
- Lin and Wang (1996), *Flow Regimes and Transient Dynamics of Two-Dimensional Stratified Flow over an Isolated Mountain Ridge*.
- Durran and Klemp (1983), *A Compressible Model for the Simulation of Moist Mountain Waves*.
- Jiang et al. (2008), *Orographic Clouds in Terrain-Blocked Flows: An Idealized Modeling Study*.
- Current official CM1 release 21.1 namelist and bundled-case documentation.
