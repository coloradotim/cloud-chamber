# Cloud Chamber MVP

**Status:** PM-authored Stage 7 MVP definition. It becomes controlling MVP scope only after issue #381 exits and this document is explicitly approved and merged through issue #383.

## Purpose

This document defines the first durable version of Cloud Chamber worth building and keeping.

The MVP is not a public launch, a generalized learning platform, or a polished wrapper around the current Build / Results / Explore interface.

It is the smallest coherent version of Cloud Chamber that its sole initial user will repeatedly open, learn from, save work in, and extend with additional cloud worlds.

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

This MVP is grounded in the completed or active evidence program for:

- canonical BOMEX reproduction;
- the Trade Cumulus product slice;
- the Canonical BOMEX Baseline;
- the two-state Surface Moisture Supply Control;
- the Trade Cumulus Updraft Lens;
- the fixed Trade Cumulus vertical-velocity scale;
- the first curated Baseline versus More Moisture Comparison.

Application Semantics already establishes that a Comparison may be casual and exploratory or may form part of a deliberate Experiment. A formal Experiment requires a controlled contrast; ordinary Comparison does not require a validation or graduation gate.

Current application structure is implementation context. It does not define the final MVP journey.

## MVP thesis

Cloud Chamber is the repository owner’s **personal cloud laboratory and growing cloud-world atlas**.

The MVP should make it easy to:

- enter a cloud world without first operating model machinery;
- watch a modeled cloud field evolve;
- reveal hidden atmospheric processes through Lenses;
- inspect scientific detail without losing the visual experience;
- read concise explanations that refresh atmospheric-science knowledge;
- create or ingest a related Simulation and return after the model run finishes;
- compare that Simulation with its parent, reference, or another compatible Simulation;
- see exactly which configuration values differ;
- investigate strong, weak, surprising, mixed, inconclusive, or absent responses;
- save useful views, comparisons, and personal notes for later return;
- preserve worthwhile Simulations as durable content;
- use the Lab to continue building, testing, retaining, or leaving behind cloud-world variations.

Trade Cumulus is the first installed Cloud World. It is not the permanent definition of Cloud Chamber.

The MVP is successful when its owner voluntarily returns to it as an instrument, not merely when a scripted demo passes.

## 1. Sole target user and use context

The initial supported user is exactly one known person: the repository owner.

### Operating context

```text
User: one known local user
Primary machine: MacBook Air
Usage: local desktop browser and local runtime
Background: physics and atmospheric science
Knowledge state: technically capable, but atmospheric concepts may need concise refreshers
Role: both cloud-world author and product user
```

The product may assume comfort with:

- physical quantities and units;
- plots, slices, fields, and model output;
- technical provenance;
- deliberate scientific comparison;
- opening deeper detail when useful.

The product should not assume that every atmospheric concept is fresh in memory.

Explanations should therefore:

- lead with a direct physical account;
- retain field names and units;
- provide short reminders for concepts such as subsidence, entrainment, buoyancy, cloud-water path, perturbation wind, and turbulent transport;
- make exact model and numerical details available on demand;
- avoid both unexplained specialist shorthand and beginner-oriented condescension.

The MVP does not define external personas, classrooms, teams, institutions, or commercial users.

## 2. Product structure

Cloud Chamber has four related product roles.

### Worlds organize atmospheric context

Cloud Worlds are the durable settings the user returns to.

A Cloud World may organize:

- one reference Simulation;
- retained variations and recent runs;
- Recipes and meaningful Controls;
- world-appropriate Lenses;
- Saved Views;
- saved Comparisons;
- featured explanations and Comparisons;
- scientific limits and provenance;
- ordinary history that is useful to retain without featuring.

A World is not a museum containing only formally validated showcase pieces. It is the durable scientific context for related Simulations, examinations, notes, and comparisons.

Worlds are the primary product entrance.

### Lab creates and tracks Simulations

The Lab contains the technical and scientific work used to create new Simulations and future world content.

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

Current Build, Results, run management, ingest, and storage behavior belongs primarily to the Lab.

The Lab remains important because the user is also the cloud-world author. It is not the front door to an already installed world.

### Explore examines one Simulation

Explore is the instrument for watching and investigating one Simulation.

It coordinates:

- three-dimensional cloud structure;
- model time;
- Lenses and native-grid slices;
- scientific evidence;
- authored explanation;
- technical detail and provenance;
- Saved Views.

### Compare examines a relationship

Compare is the instrument for examining two related Simulations or Saved Views together.

It should help answer:

- What configuration values differ?
- What appears to have changed in the cloud field?
- What changed little or not at all?
- Is the response consistent, mixed, surprising, or inconclusive?
- Which views make the response easiest to understand and remember?

Compare is not restricted to a PM-approved or scientifically graduated Control. Technical inspectability is the entry requirement; interpretation is the work the user does inside Compare.

## 3. First installed Cloud World

The first installed world is:

> **Trade Cumulus**

Its initial durable content is:

```text
Trade Cumulus
├── Canonical BOMEX Baseline
├── More Moisture
├── Updraft Lens
├── Saved Views
└── Moisture Comparison
```

The Moisture Comparison implemented through issue #381 is the first **featured saved Comparison**. It proves one authored compare-and-explain presentation. It does not define the full long-term Compare workflow.

### Product identities

The user-facing identities must be stable and independent of timestamped development names such as issue numbers, run IDs, and result IDs.

Technical identifiers remain available in Details and provenance.

Primary names should be:

```text
Cloud World: Trade Cumulus
Reference Simulation: Canonical BOMEX Baseline
Variation: More Moisture
Lens: Updraft Lens
Featured Comparison: How does stronger surface moisture supply change the cloud field?
```

### Precomputed first

The first revisit journey uses installed, precomputed content.

Entering Trade Cumulus must not require:

- launching CM1;
- generating a package;
- waiting for a six-hour simulation;
- finding a timestamped Result;
- understanding runtime storage before seeing a cloud.

The Lab remains available when the user wants to create or test a new variation.

## 4. Essential user journeys

The MVP must support two equally important loops.

### Revisit and explore

```text
Open Cloud Chamber
→ see installed Cloud Worlds
→ enter or resume Trade Cumulus
→ watch the Canonical BOMEX Baseline evolve
→ move through model time
→ activate the Updraft Lens
→ inspect coordinated 3-D and slice views
→ read an explanation beside the evidence
→ save an interesting view and optional note
→ open a saved or featured Comparison
→ return later to the same world and state
```

### Create, return, compare, and remember

```text
Open the Lab from Trade Cumulus
→ start from a reference or prior Simulation
→ change one or more settings
→ launch or ingest the related Simulation
→ leave while the model runs
→ return later and see the completed or caveated result
→ Compare with the parent, reference, or another compatible Simulation
→ inspect the exact configuration difference
→ begin with aligned views where scientifically compatible
→ independently adjust the two views when that better reveals the response
→ write a title and personal note
→ save the Comparison
→ find and reopen it later inside Trade Cumulus
```

The default revisit journey should not pass through Build or Results ceremony.

The Lab journey may use technical machinery because the user is deliberately creating new content.

## 5. Explore is the product center

The integrated Explore workspace is the central MVP instrument.

It should feel like one coherent scientific viewer, not a long page containing multiple loosely related diagnostic components.

### Core hierarchy

The primary desktop workspace should coordinate:

```text
World and Simulation identity

3-D cloud scene                 Explain / Science / Details inspector
Native-grid Lens slice

Persistent timeline and active Lens controls
```

The exact visual layout requires a separate PM-authored UX specification before implementation.

### Coordinated visual state

The three-dimensional scene and two-dimensional slice are two views of the same active examination state.

They share:

- Simulation;
- model time;
- active Lens;
- slice orientation and position;
- cloud threshold;
- Lens scale;
- wind mode;
- cloud-boundary visibility.

Changing time or slice position updates the coordinated views.

The active slice plane remains visible in the three-dimensional scene.

### Persistent timeline

Model time is a primary scientific dimension and should remain available while exploring.

The timeline should provide:

- play and pause;
- frame stepping;
- playback speed;
- current model time;
- saved-output position;
- world-appropriate key moments.

It should not disappear because the user scrolled from the scene to a distant slice or explanation section.

### One Lens context

The active Lens should have one coherent control and legend context.

The product should not present separate full legends for each rendering component when both express the same active scale.

The Lens context may include:

- active Lens name and purpose;
- discrete scale and units;
- current slice minimum and maximum;
- cloud-boundary state;
- wind mode and reference;
- orientation and plane position.

### Inspector structure

The supporting inspector should have three clear layers.

#### Explain

- authored explanation for the Simulation, Lens, Saved View, or Comparison;
- concise physical interpretation of what is visible;
- reminders of relevant atmospheric concepts;
- known uncertainty or limits when material.

#### Science

- world-relevant metrics, profiles, time series, and process evidence;
- cloud amount, cloud depth, cloud-water path, vertical velocity, lifecycle, and forcing for Trade Cumulus;
- evidence tied to the current Simulation and selected state.

#### Details

- exact fields and units;
- model time and slice coordinates;
- Recipe and Control values;
- run, result, asset, and parent identifiers;
- configuration differences;
- hashes and provenance;
- runtime integrity;
- CM1 and NetCDF implementation details.

### World-aware diagnostics

The viewer should emphasize questions that matter inside the active Cloud World.

For Trade Cumulus, primary diagnostics include:

- cloud amount;
- cloud depth;
- cloud-water path;
- cloud lifecycle;
- updraft and downdraft structure;
- mixing and transport;
- surface and large-scale forcing.

Expected absences such as deep convection, precipitation, and reflectivity should not dominate the primary interface merely because generic diagnostics checked for them.

A future precipitating Cloud World may surface those diagnostics prominently.

### Graceful partial failure

Failure of one visual layer must not make the full exploration state appear unusable.

For example, when the three-dimensional cloud point layer fails:

- the domain, Lens plane, native-grid slice, explanation, and scientific evidence remain usable;
- the failure appears as a compact layer-specific message;
- retry applies only to the failed layer;
- the page-level narrative is not replaced by a rendering error.

## 6. Compare is ordinary investigation

Comparison is a normal part of Exploration.

It should be available when two Simulations have enough readable, compatible data to examine the requested views and Lenses. It does not require that the changed condition, response, or interpretation already be validated.

### Technical trust is separate from interpretation

Compare should distinguish:

```text
Can these outputs be read and compared honestly?
What configuration values differ?
What appears to have happened?
Is the result worth saving or featuring?
```

Only the first is an automatic technical gate.

A caveated Simulation may still be useful to compare when the caveat is visible and the required fields remain usable. Missing or untrusted evidence must never be silently converted into a clean comparison.

### Run lineage

A related Simulation should preserve, when known:

- Cloud World;
- source Recipe;
- parent or reference Simulation;
- user question or run note;
- exact changed configuration values;
- an unchanged-configuration fingerprint or summary;
- technical run and result identity.

When the run becomes inspectable, the product should offer an obvious action such as:

```text
Compare to Canonical BOMEX Baseline
```

or:

```text
Compare to parent Simulation
```

The user should not need to reconstruct lineage from filenames, timestamps, or memory.

### Configuration difference

Compare must show the exact differences before interpreting the response.

When one physical condition changed, the interface may foreground that condition without claiming causal proof from one run pair.

When several physical or numerical values changed, the interface must show all material differences and avoid attributing the response to one factor.

Operational differences such as output cadence should remain visible but distinguishable from atmospheric changes.

### Aligned inspection

For compatible Simulations, Compare should begin with aligned views:

- same model time or explicit time mapping;
- same Lens;
- same scale;
- same slice orientation and position;
- same camera and display settings where practical.

This mode supports direct inspection of what differs at a common examination state.

The product must not fake alignment when grids, times, fields, or domains are incompatible.

### Independent examination

The user may unlock the two sides and choose independently:

- model time;
- slice orientation and position;
- camera;
- selected view state.

This mode supports finding the most informative view in each Simulation.

Independently selected views must identify their exact times and positions and must not imply one-to-one identity between individual clouds.

The current issue #381 B5/M5 story is an example of an independently arranged, featured Comparison.

### Saving and featuring

A Comparison may be saved because it is useful, surprising, confusing, inconclusive, or worth revisiting.

Saving means:

> This examination is worth returning to.

It does not mean:

> This change has been scientifically validated.

A saved Comparison may later be pinned or featured within its Cloud World. Feature status controls prominence, not scientific certification.

## 7. Saved Views, saved Comparisons, and resume

The MVP needs durable memory for both single-Simulation and two-Simulation work.

### Saved View

A Saved View preserves, at minimum:

- Cloud World;
- Simulation;
- model time or playback range;
- camera state;
- three-dimensional field;
- threshold, opacity, and point size;
- active Lens;
- slice orientation and position;
- cloud-boundary state;
- horizontal-wind visibility and mode;
- active inspector section;
- optional title;
- optional personal note.

### Saved Comparison

A Saved Comparison preserves, at minimum:

- title and optional personal note;
- Cloud World;
- left and right Simulations;
- parent, reference, or other relationship when known;
- exact configuration difference;
- technical trust summaries;
- aligned or independent mode;
- the complete Saved View state for each side;
- shared or side-specific Lens state;
- selected response metrics or evidence;
- optional authored or personal explanation;
- pinned or featured state;
- created and updated times.

A Saved Comparison is a personal lab-notebook page with live scientific views. It is not a formal claims graph.

### Resume behavior

The product remembers the last active state for each Cloud World.

Returning to a World should resume the prior state unless the user explicitly chooses a reference Simulation, Saved View, or Saved Comparison.

### Scope boundary

The MVP does not require:

- a formal Observation database;
- collaboration;
- comments from other users;
- a claims graph;
- automatic scientific conclusions;
- cloud-object identity tracking.

Saved Views, saved Comparisons, and personal notes are sufficient for the initial knowledge trail.

## 8. First featured Comparison

The first featured Comparison is the Baseline versus More Moisture story implemented through issue #381.

It communicates:

- the one condition changed;
- the major measured responses;
- outcomes that changed little or varied through time;
- what remained fixed by design;
- two illustrative Lens views;
- an authored explanation grounded in full-run evidence.

The illustrative views use different times and positions. They help show the measured response but do not establish it on their own.

The user can open either Simulation in the full Explore workspace.

This featured story is reusable content for the later integrated Compare workspace. It is not the final Compare information architecture and does not limit Comparison to preapproved Controls or curated stories.

## 9. Content durability and recovery

Retained world content must be more durable than ordinary timestamped runtime output.

The MVP requires a bounded Trade Cumulus content mechanism that can:

- give the reference Simulation, More Moisture Simulation, Comparison evidence, Saved Views, saved Comparisons, and authored content stable identities;
- verify expected manifests, files, and hashes;
- preserve parent/reference lineage and configuration differences;
- protect featured and pinned assets from ordinary cleanup;
- make cleanup effects explicit for ordinary retained history;
- detect missing or corrupt content;
- explain which part of the World is unavailable;
- reinstall or repair the known installed content predictably;
- avoid committing multi-gigabyte NetCDF files to Git.

The exact storage and delivery mechanism is an implementation decision for a later bounded issue.

The first solution should support one known local world bundle and ordinary local variations. It should not become a marketplace, remote content service, or generalized plugin registry.

## 10. Continuing cloud-world evolution

A second Cloud World is not required for MVP completion.

The core shell should nevertheless avoid hard-coding Trade Cumulus into every viewer decision.

Adding a later World should primarily involve:

- a scientifically grounded world definition;
- one reference or known-working Simulation;
- retained variations;
- world-appropriate Recipe assumptions;
- meaningful Controls;
- Lenses and their defaults;
- authored explanations;
- Saved Views and saved Comparisons;
- world-specific scientific evidence.

It should not require rebuilding the core Explore or Compare workspace.

This requirement does not authorize:

- a generic plugin platform;
- a Lens registry framework;
- a content marketplace;
- generalized multi-engine architecture;
- speculative remote compute.

## 11. Included MVP capabilities

The MVP includes:

- a Worlds entry surface;
- one installed Trade Cumulus world;
- stable reference and variation identities;
- precomputed local scientific content;
- direct world entry and per-world resume;
- an integrated Explore workspace;
- three-dimensional cloud playback;
- a coordinated native-grid slice;
- the Trade Cumulus Updraft Lens;
- world-owned Lens defaults and scale;
- world-aware scientific evidence;
- authored explanations;
- run lineage for related Simulations;
- Compare to parent or reference;
- exact configuration differences;
- aligned and independent Compare modes;
- the featured Moisture Comparison;
- Saved Views, saved Comparisons, and optional notes;
- durable-content validation and cleanup protection;
- graceful missing-content and partial-layer states;
- continued access to Lab tools;
- technical provenance and runtime integrity on demand.

## 12. Explicit exclusions

The MVP excludes:

- public users or public onboarding;
- accounts, authentication, permissions, or teams;
- collaboration or sharing workflows;
- analytics, telemetry, or growth instrumentation;
- mobile-first scientific exploration;
- cloud hosting or remote compute;
- mandatory live CM1 execution in the revisit journey;
- a polished arbitrary Recipe editor in Worlds;
- a universal free-form control surface outside the Lab;
- another Cloud World before the first shell is sound;
- another Control or Lens merely to demonstrate breadth;
- comparison of unrelated or scientifically incompatible outputs as though they were directly comparable;
- a generalized public Comparison platform;
- generic Lens or visualization plugins;
- automated causal explanation;
- statistical-significance claims without appropriate evidence;
- formal collaborative observations or claims graphs;
- repository-wide retirement of current technical workspaces.

## 13. Quality and trust requirements

### Scientific trust

- Every World and Simulation retains source, Recipe, Control, model, field, lineage, and integrity provenance.
- Authored or personal explanation is distinguishable from backend-derived diagnostics.
- World-aware diagnostics do not present expected exclusions as surprising failures.
- Lens scales and thresholds remain stable and explicit.
- Comparisons state configuration differences before presenting interpretation.
- Aligned views use genuinely compatible coordinates, times, fields, and scales.
- Multiple changed settings are never presented as a one-factor causal contrast.
- Missing or untrusted evidence is never silently converted to zero or certainty.
- Saving or featuring a Comparison is not labeled as scientific validation.

### Interaction quality

- The core exploration loop is coherent on the target MacBook Air.
- Time, scene, Lens slice, explanation, and scientific detail are coordinated.
- Compare makes it easy to move from aligned inspection to independent examination.
- Ordinary exploration does not require repeated movement among Build, Results, and long page sections.
- Product-facing names take precedence over issue, run, and result identifiers.
- Partial rendering failures remain local and recoverable.

### Persistence quality

- Saved Views and saved Comparisons restore the intended state deterministically.
- The last active state is retained per World.
- Parent/reference relationships and configuration differences survive reloads.
- Featured content cannot be removed by ordinary cleanup without an explicit protected-content action.
- Missing or corrupt assets are reported clearly and can be repaired.

### Operational quality

- The installed-world revisit journey works without internet access after required local assets are present.
- The revisit journey does not require CM1 execution.
- Lab tools remain available for future Simulation and world development.
- Returning later reveals whether a local run completed, failed, or remains incomplete.
- Automated tests and one live acceptance pass cover the complete MVP journey.

## 14. Measurable completion criteria

The MVP is complete only when all of the following are demonstrated on the target MacBook Air.

### World entry

- Cloud Chamber opens to a Worlds-oriented entrance rather than requiring Build or Results first.
- Trade Cumulus is visible as installed content.
- Entering the World opens the reference Simulation or the last resumed state without launching CM1.
- Primary UI uses stable World and Simulation names rather than issue/run/result IDs.

### Integrated Explore workspace

- At a `1440 × 900` CSS-pixel desktop viewport, the three-dimensional scene, active slice, persistent timeline, and supporting inspector form one coherent workspace.
- The user does not need a long page-level scroll to move between the scene, slice, time controls, and primary explanation.
- Changing model time updates the scene and active Lens slice without a full page reload.
- Changing the Lens plane updates both the slice and its plane in the scene.
- One coherent Lens legend and control context represents the active Lens.
- Trade Cumulus diagnostics prioritize shallow-cloud questions rather than generic deep-convection or precipitation absence messages.

### Explanation and detail

- Authored explanation is available beside the visual evidence.
- Science and Details views expose the required evidence, configuration, lineage, and provenance without dominating the primary scene.
- Atmospheric refresher text is direct, technically accurate, and optional.

### Lab return and lineage

- A related Trade Cumulus variation can be created or ingested with a parent or reference relationship and an optional question or note.
- Returning to Cloud Chamber shows whether that run completed, failed, or remains incomplete.
- A completed inspectable variation offers Compare to parent or reference without reconstructing the relationship from names.
- Exact changed values and sufficiently comparable fixed settings are visible before interpretation.

### Compare investigation

- Compare can open the existing More Moisture variation against the Canonical BOMEX Baseline as a related pair.
- It begins in an aligned inspection state where the data support honest alignment.
- The user can unlock the two sides and choose independent times, planes, and cameras.
- The interface identifies whether the views are aligned or independently arranged.
- Incompatible alignment is reported rather than faked.
- The featured issue #381 Comparison remains available as one saved, independently arranged story.

### Saved Views, saved Comparisons, and resume

- A user can save a single-Simulation view with a title and optional note.
- A user can save a Comparison with a title, optional note, configuration difference, mode, and both view states.
- Reloading the application restores either saved object deterministically.
- Re-entering Trade Cumulus resumes its last active state.
- Saved-state restoration failures are explicit rather than silently falling back.
- The saved Comparison can be found again from Trade Cumulus and can reopen either underlying Simulation.

### Content durability

- The expected Trade Cumulus installed content is validated by stable identity and hashes.
- Ordinary cleanup does not remove protected featured content.
- Cleanup impact on ordinary retained variations is explicit.
- Missing or corrupt assets produce a bounded repair state rather than a broken or empty World.
- Multi-gigabyte model output remains outside Git.

### Failure isolation

- A failed three-dimensional scalar layer does not disable the Lens slice, timeline, explanation, or scientific evidence.
- Retry targets the failed layer.
- Missing saved-Comparison evidence does not make either underlying Simulation unavailable.

### Lab continuity

- The Lab remains reachable for package generation, runs, ingest, result evaluation, Compare entry, and storage work.
- Lab machinery is not presented as the primary entrance to installed Worlds.

### Verification

- The full revisit and create-return-compare-save journeys have automated coverage where practical.
- One live acceptance pass records startup, World entry, playback, Lens use, Lab return, related-Simulation comparison, Saved View restoration, saved-Comparison restoration, partial-layer failure, and return to either underlying Simulation.
- No new CM1 run is required for MVP acceptance; the existing Baseline and More Moisture pair may exercise the related-Simulation workflow.
- Performance thresholds for initial load, frame changes, Compare transitions, and saved-state restoration are set in the approved UX specification from measured MacBook Air baselines rather than guessed in this document.

## 15. Recommended implementation sequence

Implementation proceeds one bounded issue at a time.

### Increment 1 — Explore and Compare UX specification

Create a PM-authored specification with:

- annotated desktop wireframes for single-Simulation Explore and two-Simulation Compare;
- information hierarchy;
- scene, slice, timeline, and inspector layout;
- aligned and independent Compare behavior;
- configuration-difference presentation;
- Lens controls and legend placement;
- authored and personal explanation placement;
- world-aware diagnostics;
- layer-failure states;
- Save View and Save Comparison behavior;
- exact current elements to remove, retain, or relocate;
- measurable interaction and performance targets based on the target machine.

Do not begin with an open-ended instruction to “clean up Explore” or “generalize Compare.”

### Increment 2 — stable World identities, content, and run lineage

Implement stable World and Simulation identities, the known Trade Cumulus installed bundle, parent/reference relationships, configuration-difference records, manifest/hash validation, cleanup protection, missing-content reporting, and bounded repair.

### Increment 3 — integrated Explore shell

Reorganize existing visual and scientific capabilities into the approved workspace before adding another scientific feature.

### Increment 4 — related-Simulation Compare workflow

Implement Compare to parent/reference, exact configuration differences, technically honest aligned inspection, and independent examination using the approved workspace design.

Reuse issue #381’s evidence and presentation components where they fit. Do not preserve its current Results-driven entry or long standalone-report layout as final information architecture.

### Increment 5 — Saved Views, saved Comparisons, and resume

Persist and restore the approved single- and two-Simulation examination states and optional personal notes.

### Increment 6 — Worlds entry and golden path

Add direct World entry, resume, reference and variation access, saved-state access, and featured Comparison entry.

### Increment 7 — Lab reframing

Retain current technical capabilities while making run lineage, return-after-run, and Compare entry coherent and moving Lab machinery out of the primary installed-World hierarchy.

### Increment 8 — MVP hardening and personal acceptance

Complete content recovery, error states, performance verification, provenance access, automated coverage, and one live personal acceptance pass.

No second Cloud World, Control, or Lens should begin before the first MVP shell passes this gate unless a direct blocking contradiction is found.

## 16. Stage 7 exit and next bounded decision

This MVP definition is approved only when:

- issue #381 has exited successfully;
- the Stage 5 Trade Cumulus slice is accepted for MVP inclusion;
- the completed Stage 5B experiment track is explicitly accepted as satisfying the practical purpose of the old Stage 6 experimentation gate;
- the sole-user, personal-lab scope is approved;
- ordinary Compare is approved as an investigation and memory workflow rather than a validation-only artifact;
- the included, excluded, and completion criteria are approved;
- issue #364 records the decision;
- the next work is one bounded Explore and Compare workspace UX specification.

The MVP approval gate does not authorize broad frontend implementation by itself.

The single next bounded issue after approval should be:

> **Define the integrated Explore and Compare workspace UX for the personal cloud laboratory MVP.**

That issue should produce the visual and interaction specification needed before Codex is asked to reorganize the current Explore implementation or generalize the first featured Comparison.