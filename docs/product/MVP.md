# Cloud Chamber MVP

**Status:** Stage 7A is active and under independent review through issue #383 and PR #384. The Stage 5 product/science exit and the practical purpose of the former Stage 6 experimentation gate are satisfied. This document becomes controlling MVP scope only after explicit PM approval and merge of PR #384.

## Purpose

This document defines the first durable version of Cloud Chamber worth building and keeping.

Cloud Chamber is not being designed for a public launch, a classroom, a team, or a generalized scientific-computing market. It is the smallest coherent version of the product that its sole initial user will repeatedly open, learn from, save work in, and extend with additional cloud worlds.

The governing question is:

> What would make Cloud Chamber a durable personal cloud laboratory rather than a sequence of successful technical experiments?

## Authority and evidence

Controlling authority remains:

1. `NORTH_STAR.md`
2. `docs/product/PRODUCT_VISION.md`
3. explicit approved PM decisions
4. `docs/product/APPLICATION_SEMANTICS.md`
5. this MVP definition, after approval
6. bounded product documents such as `docs/product/TRADE_CUMULUS_PRODUCT_SLICE.md`
7. current implementation documentation and code
8. research and run evidence

This MVP is grounded in:

- canonical BOMEX reproduction;
- the Trade Cumulus product slice;
- the Canonical BOMEX Baseline;
- the Surface Moisture Supply comparison;
- the Trade Cumulus Updraft Lens;
- the fixed Trade Cumulus vertical-velocity scale;
- the first featured Baseline versus More Moisture Comparison merged through PR #385.

Application Semantics already establishes that a Comparison may be casual and exploratory or may form part of a deliberate Experiment. A formal Experiment requires a controlled contrast; ordinary Comparison does not require a validation or graduation gate.

Current Build / Results / Explore structure is implementation context. It does not define the final MVP journey.

## MVP thesis

Cloud Chamber is the repository owner’s **personal cloud laboratory and growing cloud-world atlas**.

The MVP should make it easy to:

- enter a cloud world without first operating model machinery;
- watch a modeled cloud field evolve;
- reveal hidden atmospheric processes through Lenses;
- inspect scientific detail without losing the visual experience;
- read concise explanations that refresh atmospheric-science knowledge;
- create or ingest a related Simulation and return after its model run finishes;
- compare that Simulation with its parent, reference, or another compatible Simulation;
- see exactly which configuration values differ;
- investigate strong, weak, surprising, mixed, inconclusive, or absent responses;
- save useful views, comparisons, and personal notes for later return;
- preserve worthwhile Simulations as durable content;
- continue building, testing, retaining, archiving, or leaving behind cloud-world variations.

Trade Cumulus is the first installed Cloud World. It is not the permanent definition of Cloud Chamber.

The MVP is successful when its owner voluntarily returns to it as an instrument, not merely when a scripted demo passes.

## 1. Sole target user and use context

The initial supported user is exactly one known person: the repository owner.

```text
User: one known local user
Primary machine: MacBook Air
Usage: local desktop browser and local runtime
Background: physics and atmospheric science
Knowledge state: technically capable, but atmospheric concepts may need concise refreshers
Role: both cloud-world author and product user
```

The product may assume comfort with physical quantities, units, plots, slices, model output, and technical provenance. It should not assume every atmospheric concept is fresh in memory.

Explanations should therefore:

- lead with a direct physical account;
- retain field names and units;
- provide concise reminders for concepts such as subsidence, entrainment, buoyancy, cloud-water path, perturbation wind, and turbulent transport;
- make exact model and numerical details available on demand;
- avoid both unexplained specialist shorthand and beginner-oriented condescension.

The MVP does not define external personas, classrooms, teams, institutions, or commercial users.

## 2. Product information architecture

### Worlds is the sole primary product level

The primary product entrance is **Cloud Worlds**.

Explore, Compare, Lab, Saved Views, saved Comparisons, notes, and Simulations live within a Cloud World. They are not global peers to Worlds.

The first structure is:

```text
Cloud Worlds
└── Trade Cumulus
    ├── Overview
    ├── Simulations
    ├── Saved Views
    ├── Comparisons
    └── Lab
```

A future world begins as a draft World with its own Lab:

```text
Cloud Worlds
→ New Cloud World
→ Draft World
→ Lab
```

Global settings, storage diagnostics, and application maintenance may remain available as utilities. They are not primary product destinations.

### A Cloud World is durable context, not a validation museum

A World may organize:

- a reference Simulation;
- retained variations and recent runs;
- Recipes and meaningful Controls where they apply;
- world-appropriate Lenses;
- Saved Views;
- saved Comparisons;
- featured explanations and Comparisons;
- ordinary history worth retaining without featuring;
- the World’s Lab.

A World is not limited to formally validated showcase pieces. Saving or featuring content controls return and prominence; it does not certify a scientific conclusion.

### Each World owns its Lab

The Lab contains the technical and scientific work used to create new Simulations in that World.

It may contain:

- setup and configuration work;
- package generation;
- local CM1 execution;
- run monitoring;
- ingest;
- technical integrity and field trust;
- storage and cleanup;
- run lineage and configuration differences;
- retention, archive, rejection, and feature decisions.

Current Build, Results, run management, ingest, and storage behavior belongs primarily to the active World’s Lab.

### Explore and Compare are workspace states

**Explore** examines one Simulation.

**Compare** examines the relationship between two related Simulations or Saved Views.

They are opened from a World, a Simulation, a completed Lab run, a Saved View, or a saved Comparison. They are not permanent global navigation sections.

## 3. Simulation, Run, and lineage

Explore presents a **Simulation**, not a technical Run.

The normal lineage is:

```text
Cloud World
→ World Lab
→ Recipe, reference Simulation, or prior Simulation
→ selected configuration changes
→ technical Run
→ completed model output
→ Simulation
→ Explore or Compare
```

A Run is execution machinery. A Simulation is the modeled atmospheric evolution the user returns to.

Every related Simulation retains, when known:

- Cloud World;
- source Recipe;
- parent or reference Simulation;
- optional user question or run note;
- exact changed physical and numerical values;
- sufficiently comparable fixed settings or an unchanged-configuration fingerprint;
- technical run, result, source-model, field, and integrity identity;
- Control identity and values **when an explicit Control applies**.

A Simulation does not require a graduated Control in order to be explored or compared.

The user should not reconstruct lineage from filenames, timestamps, issue numbers, or memory.

## 4. First installed Cloud World

The first installed world is:

> **Trade Cumulus**

Its initial durable content is:

```text
Trade Cumulus
├── Canonical BOMEX Baseline
├── More Moisture
├── Updraft Lens
├── Saved Views
└── Featured Moisture Comparison
```

The Moisture Comparison merged through PR #385 is the first **featured saved Comparison**. It proves one authored compare-and-explain presentation. It does not define the full future Compare workflow.

User-facing identities are stable and independent of timestamped run and result names. Technical identifiers remain available in Details and provenance.

### Precomputed first

The revisit journey uses installed, precomputed content.

Entering Trade Cumulus must not require:

- launching CM1;
- generating a package;
- waiting for a six-hour simulation;
- finding a timestamped Result;
- understanding runtime storage before seeing a cloud.

The World’s Lab remains available when the user wants to create or test a new variation.

## 5. Essential user journeys

### Revisit and explore

```text
Open Cloud Chamber
→ see Cloud Worlds
→ enter or resume Trade Cumulus
→ watch the Canonical BOMEX Baseline evolve
→ move through model time
→ activate the Updraft Lens or inspect a Field Slice
→ inspect coordinated 3-D and slice views
→ read explanation and science beside the evidence
→ write a Simulation note or save a view with a note
→ open a saved or featured Comparison
→ return later to the same World and state
```

### Create, leave, return, compare, and remember

```text
Open Trade Cumulus Lab
→ start from the reference or a prior Simulation
→ change one or more settings
→ launch or ingest the related Simulation
→ leave while the model runs
→ return later and see completed, caveated, failed, or incomplete status
→ Compare with the parent, reference, or another compatible Simulation
→ inspect every material configuration difference
→ begin aligned where scientifically honest
→ independently adjust views when useful
→ write a title and personal note
→ save the Comparison
→ find and reopen it later inside Trade Cumulus
```

### Start another World

```text
Open Cloud Worlds
→ create a draft World
→ enter that World’s Lab
→ develop its first scientifically grounded Simulation
→ retain, archive, or leave the draft behind
```

The default revisit journey should not pass through Build or Results ceremony. The Lab journey may use technical machinery because the user is deliberately creating content.

## 6. World overview requirements

The Trade Cumulus overview should provide:

- **Resume:** last active Simulation, Saved View, or saved Comparison;
- **Simulations:** reference, retained variations, and recent inspectable Lab outputs;
- **Saved Views:** preserved single-Simulation examinations;
- **Comparisons:** saved and featured Comparisons;
- **Lab status:** active runs, completed runs awaiting inspection, and entry to the World’s Lab.

A representative structure is:

```text
Trade Cumulus

Resume
Canonical BOMEX Baseline — 04:18:00 — Updraft Lens

Simulations
Canonical BOMEX Baseline
More Moisture
Recent Lab variations

Saved Views
...

Comparisons
Featured: More Moisture versus Baseline
Saved: ...

Lab
1 run in progress
2 completed runs awaiting inspection
```

## 7. Explore workspace contract

Explore is the central MVP instrument for one Simulation.

At a `1440 × 900` CSS-pixel desktop viewport, it should form one coherent workspace rather than a long page of implementation-specific components.

### Core hierarchy

```text
World / Simulation identity                Compare   Save View   More

3-D cloud scene                    Explain | Science | Notes | Details
Active Field Slice or Lens slice

Persistent timeline and active view controls
```

The 3-D scene and active slice are visible at the same time. The supporting inspector is visible by default and collapsible.

### Coordinated visual state

The 3-D scene and slice share:

- Simulation;
- model time;
- active Lens or selected Field Slice;
- slice orientation and position;
- cloud threshold where applicable;
- Lens scale;
- wind mode;
- cloud-boundary visibility.

Changing time or slice position updates the coordinated views. The active plane remains visible in the 3-D scene.

### Persistent timeline

The timeline remains available while exploring and provides:

- play and pause;
- frame stepping;
- playback speed;
- current model time;
- saved-output position;
- world-appropriate key moments.

### Field Slice versus Lens

A **Field Slice** is a generic scientific inspection tool:

> Show this field on this plane.

It owns a field, orientation, position, units, display scale, and native-value inspection.

A **Lens** is a curated way to reveal and interpret a process. It may combine:

- one or more model fields;
- a derived diagnostic or scientifically meaningful proxy;
- world-specific scales and thresholds;
- contours, vectors, or other overlays;
- useful default time, orientation, and region;
- explanation and interpretation guidance.

The Updraft Lens is not merely a `w` slice. It combines vertical velocity, the fixed Trade Cumulus scale, cloud-liquid boundary, perturbation horizontal wind, world-appropriate defaults, and explanation.

A Lens may include a Field Slice but need not be slice-based.

Potential future Lenses such as Buoyancy/Thermal, Moisture Mixing, Cloud Lifecycle, Surface Coupling, Turbulence, Inversion/Entrainment, or Cold Pool are examples only. They are not approved MVP features.

### One Lens context

When a Lens is active, one coherent legend and control context serves the 3-D scene and slice. Do not repeat full legends for each rendering component when they express the same scale.

### Inspector

The inspector has four sections.

**Explain**

- authored explanation;
- physical interpretation of what is visible;
- concise atmospheric-science refreshers;
- material limits or uncertainty.

**Science**

- world-relevant metrics, profiles, time series, and process evidence;
- selected-state evidence where useful.

**Notes**

- an editable general Simulation note;
- the note attached to a Saved View when one is open;
- clear unsaved and saved state.

**Details**

- exact fields and units;
- model time and slice coordinates;
- Recipe and applicable Control values;
- parent/reference identity;
- configuration differences;
- run, result, and asset identifiers;
- hashes, provenance, runtime integrity, CM1, and NetCDF details.

### World-aware diagnostics

Trade Cumulus should emphasize cloud amount, cloud depth, cloud-water path, cloud lifecycle, updraft/downdraft structure, mixing/transport, and surface/large-scale forcing.

Expected absences such as deep convection, precipitation, and reflectivity should not dominate this World’s primary interface.

### Partial failure

Failure of one visual layer must remain local. A failed 3-D cloud layer does not disable the slice, timeline, explanation, science, notes, or Details. Retry targets the failed layer.

## 8. Compare workspace contract

Compare is ordinary investigation, not a validation-only report.

It should be available when two Simulations have enough readable, compatible data to examine the requested views and Lenses. A caveated Simulation may still be useful when caveats are visible and required fields remain usable.

### How Compare opens

**From a completed World Lab run**

Primary suggestions are:

1. Compare to parent Simulation;
2. Compare to the World reference Simulation;
3. Explore on its own.

**From Explore**

The current Simulation is fixed as one side. Candidate ordering is:

1. parent Simulation;
2. World reference Simulation;
3. recent related Simulations;
4. Saved Views from related Simulations;
5. other compatible Simulations in the same World.

**From the World**

The Comparisons section offers saved/featured Comparisons and **New Comparison**.

**From a Saved View**

`Compare this view…` preserves that view as one side.

Cross-World comparison is outside the MVP unless a later concrete need establishes scientific and visual compatibility.

### Preview before opening

The chooser shows the relationship and exact configuration difference before opening Compare.

When several values changed, all material physical and numerical differences are listed. The product must not attribute the response to one factor.

Operational differences such as output cadence are visible but distinguishable from atmospheric changes.

### Aligned and Independent are presets over link controls

The Compare toolbar provides:

```text
View preset: Aligned | Independent

Link:
Time
Camera
Slice plane
Lens and scale
```

The user may manipulate either side. Linked state causes the other side to follow.

**Aligned preset** enables every scientifically compatible link.

**Independent preset** disables links and permits separate examination states.

A mixed state is allowed, for example linked camera and Lens scale with independent time and slice plane.

### Linking semantics

- Time links by modeled seconds, not frame index. Different cadences use nearest available times and expose any offset.
- Slice position links by physical coordinate, not array index.
- Camera links by normalized domain-relative orientation, target, and zoom.
- Lens and scale link when the same Lens and scientifically compatible scale apply.
- A link is disabled with a reason when the Simulations are not compatible enough.
- The interface always identifies whether the current views are aligned, independent, or mixed.

The product must never fake alignment.

### Independent examination

Independent views may use different times, planes, cameras, or selected states. Exact times and positions remain visible, and the product must not imply one-to-one cloud identity.

The PR #385 B5/M5 story is the first independently arranged featured Comparison.

### Compare inspector

Compare uses the same four inspector sections:

- **Explain:** authored or personal interpretation;
- **Science:** selected metrics, similarities, differences, and uncertainty;
- **Notes:** the working Comparison note and saved note;
- **Details:** lineage, exact configuration difference, technical trust, fields, coordinates, provenance, and saved link state.

## 9. Notes, Saved Views, and saved Comparisons

### Notes model

The MVP requires only three note contexts:

1. **Simulation note:** an ongoing general note attached to one Simulation;
2. **Saved View note:** a title and optional note attached to one preserved examination state;
3. **Saved Comparison note:** a title and optional note attached to the preserved two-Simulation examination.

A working Compare note autosaves locally while the session is open. Saving the Comparison makes it durable.

A formal Observation database, claims graph, collaboration model, or generalized notebook ontology is not required.

### Saved View

A Saved View preserves:

- Cloud World and Simulation;
- model time or playback range;
- camera;
- 3-D field and display settings;
- active Lens or Field Slice;
- slice orientation and position;
- cloud-boundary and wind state;
- active inspector section;
- title and optional note.

### Saved Comparison

A Saved Comparison preserves:

- title and optional note;
- Cloud World;
- left and right Simulations or Saved Views;
- parent/reference/other relationship;
- exact configuration difference;
- technical trust summaries;
- Aligned, Independent, or mixed state;
- every individual link toggle;
- the complete view state for each side;
- shared or side-specific Lens/Field Slice state;
- selected evidence;
- optional authored or personal explanation;
- pinned or featured state;
- created and updated times.

Saving means:

> This examination is worth returning to.

It does not mean:

> This change has been scientifically validated.

A featured Comparison is a saved Comparison promoted on the World overview. Featuring changes prominence, not scientific status.

### Resume

The product remembers the last active state for each World. Returning to a World resumes that state unless the user explicitly chooses a reference Simulation, Saved View, or saved Comparison.

## 10. Technical trust and interpretation

The product separates:

1. Can the outputs be read and compared honestly?
2. What configuration values differ?
3. What appears to have happened?
4. How confident is the user in that interpretation?
5. Is the examination worth saving or featuring?

Only the first is an automatic technical gate.

Every World and related Simulation retains:

- scientific source and Recipe context;
- parent/reference lineage;
- exact changed values;
- comparable fixed settings;
- source model, fields, run/result identity, and integrity provenance;
- Control identity only where an explicit Control applies.

Authored or personal explanation is distinguishable from backend-derived diagnostics. Missing or untrusted evidence is never silently converted to zero or certainty.

## 11. Content durability and recovery

Retained World content must be more durable than ordinary timestamped runtime output.

The MVP requires a bounded Trade Cumulus content mechanism that can:

- give the reference Simulation, More Moisture Simulation, featured Comparison evidence, Saved Views, saved Comparisons, and authored content stable identities;
- verify expected manifests, files, and hashes;
- preserve lineage and configuration differences;
- protect featured and pinned assets from ordinary cleanup;
- make cleanup effects explicit for ordinary retained history;
- detect missing or corrupt content;
- explain which part of the World is unavailable;
- reinstall or repair known installed content predictably;
- keep multi-gigabyte model output outside Git.

The first solution supports one known local World bundle and ordinary local variations. It is not a marketplace, remote content service, or generalized plugin registry.

## 12. Continuing cloud-world evolution

A second Cloud World is not required for MVP completion.

Adding a later World should primarily involve:

- a scientifically grounded world definition;
- one reference or known-working Simulation;
- retained variations;
- world-appropriate Recipe assumptions;
- Controls where useful;
- Lenses and Field Slice defaults;
- explanations;
- Saved Views and saved Comparisons;
- world-specific evidence.

It should not require rebuilding the core World, Explore, or Compare shell.

This does not authorize a generic plugin platform, Lens registry framework, marketplace, generalized multi-engine architecture, or speculative remote compute.

## 13. Included MVP capabilities

The MVP includes:

- a Worlds-only primary product entrance;
- one installed Trade Cumulus World and its Lab;
- stable reference and variation identities;
- precomputed local scientific content;
- direct World entry and per-World resume;
- one-Simulation Explore;
- three-dimensional cloud playback;
- coordinated Field Slice and Lens rendering;
- the Trade Cumulus Updraft Lens;
- world-aware science and authored explanation;
- Simulation notes;
- run lineage and exact configuration differences;
- Compare to parent/reference and compatible same-World Simulations;
- linked and independent Compare controls;
- the featured Moisture Comparison;
- Saved Views, saved Comparisons, and notes;
- durable-content validation and cleanup protection;
- graceful missing-content and partial-layer states;
- continued access to World Lab tools;
- technical provenance and integrity on demand.

## 14. Explicit exclusions

The MVP excludes:

- public users or onboarding;
- accounts, authentication, permissions, teams, collaboration, or sharing workflows;
- analytics, telemetry, or growth instrumentation;
- mobile-first scientific exploration;
- cloud hosting or remote compute;
- mandatory live CM1 execution in the revisit journey;
- a polished arbitrary Recipe editor in Worlds;
- a universal free-form control surface outside the Lab;
- another World before the first shell is sound;
- another Control or Lens merely to demonstrate breadth;
- cross-World or incompatible comparison presented as direct comparison;
- a generalized public Comparison platform;
- generic Lens or visualization plugins;
- automated causal explanation;
- statistical-significance claims without appropriate evidence;
- a formal Observation database, claims graph, or collaborative notebook;
- repository-wide retirement of current technical workspaces.

## 15. Quality and trust requirements

### Scientific trust

- Configuration differences appear before interpretation.
- Multiple changed settings are never presented as a one-factor causal contrast.
- Aligned views use genuinely compatible coordinates, times, fields, and scales.
- Lens scales and thresholds remain stable and explicit.
- Saving or featuring is never labeled scientific validation.
- Expected absences are not treated as surprising failures.

### Interaction quality

- The core World, Explore, and Compare loop is coherent on the target MacBook Air.
- The scene, slice, timeline, Lens context, inspector, and notes are coordinated.
- Compare can move among linked, independent, and mixed states without losing clarity.
- Product-facing names take precedence over issue/run/result identifiers.
- Partial rendering failures remain local and recoverable.

### Persistence quality

- Saved Views and saved Comparisons restore deterministically.
- Last active state is retained per World.
- Lineage, configuration differences, technical trust, notes, and link state survive reloads.
- Featured content cannot be removed by ordinary cleanup without an explicit protected-content action.
- Missing or corrupt assets are reported clearly and can be repaired.

### Operational quality

- The installed-World revisit journey works without internet access after required local assets are present.
- Lab tools remain available for future Simulation and World development.
- Returning later reveals whether a run completed, failed, remains incomplete, or completed with caveats.

## 16. Measurable completion criteria

The MVP is complete only when all of the following are demonstrated on the target MacBook Air.

### World entry

- Cloud Chamber opens to Cloud Worlds rather than Build or Results.
- Trade Cumulus exposes Overview, Simulations, Saved Views, Comparisons, and Lab.
- Entering the World opens its reference Simulation or resumes the last state without launching CM1.
- Stable World and Simulation names replace issue/run/result IDs in primary UI.

### Explore

- At `1440 × 900`, the 3-D scene, active slice, timeline, and inspector form one coherent workspace without long page-level scrolling.
- 3-D and active Lens/Field Slice are visible together.
- Time and plane changes update all coordinated views.
- One Lens context serves the scene and slice.
- Explain, Science, Notes, and Details are available beside the visual evidence.
- A Simulation note can be written and restored.

### Ordinary non-featured related Simulation

A bounded local fixture or ingested test result represents a technically inspectable, **non-featured** Trade Cumulus variation that:

- requires no validation or graduation status;
- retains parent/reference lineage;
- changes at least two material physical or numerical values;
- is not the existing Baseline/More Moisture featured pair.

For this case:

- Compare opens from the completed or ingested Simulation through its lineage;
- every material difference is visible before interpretation;
- the product does not attribute the response to one factor;
- alignment is offered only where honest;
- the user can arrange independent views;
- the Comparison can be saved and reopened from Trade Cumulus.

This acceptance case may use a fixture or existing ingested data. It does not require a new CM1 run.

### Compare linking

- A new related-run Compare opens with every compatible link enabled.
- Manipulating either linked timeline or camera moves the other view.
- Time links use modeled seconds; plane links use physical coordinates.
- Individual Time, Camera, Slice Plane, and Lens/Scale links can be toggled.
- Mixed link states are supported and saved.
- Incompatible links are disabled with a reason rather than faked.
- PR #385’s B5/M5 Comparison reopens in its saved independent state.

### Saved states and notes

- A Saved View restores its complete examination state and note.
- A saved Comparison restores both complete view states, link toggles, configuration difference, trust summary, title, and note.
- Re-entering Trade Cumulus resumes its last active state.
- Restoration failures are explicit rather than silently falling back.

### Content and failure handling

- Installed Trade Cumulus content is validated by stable identity and hashes.
- Ordinary cleanup does not remove protected featured content.
- Missing or corrupt assets produce bounded repair states.
- A failed 3-D layer does not disable the slice, timeline, explanation, notes, or science.
- Multi-gigabyte model output remains outside Git.

### Verification

- Automated coverage exercises the revisit and create-return-compare-save journeys where practical.
- One live acceptance pass records World entry, playback, Lens use, Field Slice use, Simulation notes, Lab return, ordinary non-featured Compare, linked and independent controls, Saved View restoration, saved-Comparison restoration, featured Comparison, partial-layer failure, and return to either underlying Simulation.
- Performance thresholds are based on measured MacBook Air behavior in the first implementation issue, not guessed here.

## 17. Bounded implementation sequence

The PM/UX decisions in this document are sufficient to begin bounded implementation. Do not create another general product-strategy or open-ended “polish Explore” document.

Implementation proceeds one issue at a time.

### Increment 1 — World-scoped shell and investigation foundation

Establish:

- Worlds as the primary product entrance;
- the Trade Cumulus World overview and World Lab boundary;
- stable World/Simulation identity and parent/reference lineage;
- exact configuration-difference presentation;
- entry from a completed related Simulation into Compare;
- existing Explore and PR #385 featured Comparison rendered under World context;
- the Field Slice versus Lens product distinction in UI language.

This increment may reuse current components and does not yet implement full persistence or the final integrated visual layout.

### Increment 2 — integrated Explore workspace

Reorganize the existing scene, slice, timeline, inspector, Lens context, Field Slice, and Simulation note into the approved MacBook Air workspace.

### Increment 3 — linked ordinary Compare

Implement Aligned/Independent presets, individual link controls, honest mapping, the configuration chooser, and same-World comparison entry points.

### Increment 4 — Saved Views, saved Comparisons, and resume

Persist and restore view state, two-sided link state, titles, and notes.

### Increment 5 — durable World content and recovery

Complete stable installed-content manifests, cleanup protection, missing-content reporting, and bounded repair.

### Increment 6 — Lab and World hardening

Complete return-after-run status, Lab integration, performance verification, error states, provenance access, automated coverage, and personal acceptance.

No second World, Control, or Lens should begin before the first MVP shell passes this gate unless a direct blocking contradiction is found.

## 18. Stage 7A exit and next bounded decision

The Stage 5 exit and practical Stage 6 disposition are complete. PR #385 has merged the first featured Comparison.

Stage 7A is approved when:

- the sole-user personal-laboratory scope is approved;
- Worlds as the sole primary product level is approved;
- World-owned Lab, Explore, Compare, Field Slice, Lens, notes, Saved Views, and saved Comparisons are approved as defined here;
- ordinary Compare is approved as investigation and memory rather than validation-only behavior;
- the included, excluded, quality, and completion criteria are approved;
- issue #364 records the decision;
- PR #384 is explicitly approved and merged.

After approval, the single next bounded issue is:

> **MVP Increment 1 — establish the World-scoped shell and investigation foundation.**

The MVP approval gate authorizes that bounded issue only. It does not authorize broad frontend cleanup or simultaneous implementation of every increment.