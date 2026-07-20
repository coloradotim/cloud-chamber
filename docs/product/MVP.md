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
- the curated Baseline versus More Moisture Comparison.

Current application structure is implementation context. It does not define the final MVP journey.

## MVP thesis

Cloud Chamber is the repository owner’s **personal cloud laboratory and growing cloud-world atlas**.

The MVP should make it easy to:

- enter a cloud world without first operating model machinery;
- watch a modeled cloud field evolve;
- reveal hidden atmospheric processes through Lenses;
- inspect scientific detail without losing the visual experience;
- read concise explanations that refresh atmospheric-science knowledge;
- save interesting views and return to them later;
- compare validated changes honestly;
- preserve worthwhile simulations as durable content;
- use the Lab to create, evaluate, keep, or abandon the next candidate world.

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

## 2. Product structure: Worlds and Lab

Cloud Chamber has two distinct product contexts.

## Worlds

Worlds contain curated, durable cloud experiences that the user returns to.

A Cloud World may contain:

- one or more validated Simulations;
- a baseline Recipe;
- meaningful Controls;
- world-appropriate Lenses;
- Saved Views;
- curated Comparisons;
- authored explanations;
- scientific limits and provenance.

Worlds are the primary product entrance.

## Lab

The Lab contains the technical and scientific work used to create future world content.

It may contain:

- setup and configuration work;
- package generation;
- local CM1 execution;
- run monitoring;
- ingest;
- result inspection;
- evidence generation;
- storage and cleanup;
- retention, rejection, and promotion decisions.

Current Build, Results, run management, ingest, and storage behavior belongs primarily to the Lab.

The Lab remains important because the user is also the cloud-world author. It is not the front door to an already curated world.

The MVP does not require a polished general-purpose promotion editor. Initial promotion of validated Lab content into a World may remain a controlled repository or local-content operation.

## 3. First installed Cloud World

The first installed world is:

> **Trade Cumulus**

Its initial durable content is:

```text
Trade Cumulus
├── Canonical BOMEX Baseline
├── More Moisture
├── Updraft Lens
└── Curated Moisture Comparison
```

### Product identities

The user-facing identities must be stable and independent of timestamped development names such as issue numbers, run IDs, and result IDs.

Technical identifiers remain available in Details and provenance.

Primary names should be:

```text
Cloud World: Trade Cumulus
Baseline Simulation: Canonical BOMEX Baseline
Control state: More Moisture
Lens: Updraft Lens
Comparison: How does stronger surface moisture supply change the cloud field?
```

### Precomputed first

The golden path uses installed, precomputed content.

Entering Trade Cumulus must not require:

- launching CM1;
- generating a package;
- waiting for a six-hour simulation;
- finding a timestamped Result;
- understanding runtime storage before seeing a cloud.

The Lab remains available when the user wants to create or test new content.

## 4. Essential user journey

The MVP golden path is:

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
→ open the More Moisture Comparison
→ inspect either full Simulation
→ return later to the same world and last view
→ enter the Lab when developing the next Control, Lens, Recipe, or Cloud World
```

The default journey should not pass through Build or Results ceremony.

## 5. Explore is the product center

The integrated Explore workspace is the central MVP instrument.

It should feel like one coherent scientific viewer, not a long page containing multiple loosely related diagnostic components.

### Core hierarchy

The primary desktop workspace should coordinate:

```text
World and Simulation identity

3-D cloud scene                 Explanation / Science / Details inspector
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
- run, result, and asset identifiers;
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

## 6. Saved Views and resume

Saved Views are required MVP behavior.

A Saved View deliberately preserves a useful way of examining a Simulation or Comparison.

### Required Saved View state

A Saved View preserves, at minimum:

- Cloud World;
- Simulation or Comparison;
- model time;
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

### Resume behavior

The product remembers the last active view for each Cloud World.

Returning to a world should resume the prior state unless the user explicitly chooses a baseline or another Saved View.

### Scope boundary

The MVP does not require:

- a formal Observation database;
- collaboration;
- comments from other users;
- a claims graph;
- automatic scientific conclusions;
- cloud-object identity tracking.

Saved Views and notes are sufficient for the initial personal knowledge trail.

## 7. Comparison experience

The first Comparison is the curated Baseline versus More Moisture story.

It should communicate:

- the one condition changed;
- the major measured responses;
- outcomes that changed little or varied through time;
- what remained fixed by design;
- two illustrative Lens views;
- an authored explanation grounded in full-run evidence.

The illustrative views may use different times and positions. They help show the measured response but do not establish it on their own.

The user can open either Simulation in the full Explore workspace.

The MVP does not require arbitrary result pairing or a generalized Comparison builder.

## 8. Content durability and recovery

Curated world content must be more durable than ordinary timestamped runtime output.

The MVP requires a bounded Trade Cumulus content mechanism that can:

- give the Baseline, More Moisture Simulation, Comparison evidence, and authored content stable identities;
- verify expected manifests, files, and hashes;
- protect curated assets from ordinary cleanup;
- detect missing or corrupt content;
- explain which part of the world is unavailable;
- reinstall or repair the known content predictably;
- avoid committing multi-gigabyte NetCDF files to Git.

The exact storage and delivery mechanism is an implementation decision for a later bounded issue.

The first solution should support one known local world bundle. It should not become a marketplace, remote content service, or generalized plugin registry.

## 9. Continuing cloud-world evolution

A second Cloud World is not required for MVP completion.

The core shell should nevertheless avoid hard-coding Trade Cumulus into every viewer decision.

Adding a later world should primarily involve:

- a scientifically validated world definition;
- one or more durable Simulations;
- world-appropriate Recipe assumptions;
- Controls;
- Lenses and their defaults;
- authored explanations;
- Saved Views and Comparisons;
- world-specific scientific evidence.

It should not require rebuilding the core Explore workspace.

This requirement does not authorize:

- a generic plugin platform;
- a Lens registry framework;
- a content marketplace;
- generalized multi-engine architecture;
- speculative support for future collaboration or remote compute.

## 10. Included MVP capabilities

The MVP includes:

- a Worlds entry surface;
- one installed Trade Cumulus world;
- stable Baseline and More Moisture identities;
- precomputed local scientific content;
- direct world entry and per-world resume;
- an integrated Explore workspace;
- three-dimensional cloud playback;
- a coordinated native-grid slice;
- the Trade Cumulus Updraft Lens;
- world-owned Lens defaults and scale;
- world-aware scientific evidence;
- authored explanations;
- the curated Moisture Comparison;
- Saved Views and optional notes;
- durable-content validation and cleanup protection;
- graceful missing-content and partial-layer states;
- continued access to Lab tools;
- technical provenance and runtime integrity on demand.

## 11. Explicit exclusions

The MVP excludes:

- public users or public onboarding;
- accounts, authentication, permissions, or teams;
- collaboration or sharing workflows;
- analytics, telemetry, or growth instrumentation;
- mobile-first scientific exploration;
- cloud hosting or remote compute;
- mandatory live CM1 execution in the golden path;
- arbitrary Recipe creation from the Worlds experience;
- free-form atmospheric parameter editing;
- another Cloud World before the first shell is sound;
- another Control or Lens merely to demonstrate breadth;
- arbitrary result pairing;
- a generalized Comparison platform;
- generic Lens or visualization plugins;
- automated causal explanation;
- statistical-significance claims from one deterministic pair;
- formal collaborative observations or claims graphs;
- repository-wide retirement of current technical workspaces.

## 12. Quality and trust requirements

### Scientific trust

- Every world and Simulation retains source, Recipe, Control, model, field, and integrity provenance.
- Authored explanation is distinguishable from backend-derived diagnostics.
- World-aware diagnostics do not present expected exclusions as surprising failures.
- Lens scales and thresholds remain stable and explicit.
- Comparisons state changed and fixed assumptions clearly.
- Missing or untrusted evidence is never silently converted to zero or certainty.

### Interaction quality

- The core exploration loop is coherent on the target MacBook Air.
- Time, scene, Lens slice, explanation, and scientific detail are coordinated.
- Ordinary exploration does not require repeated movement among Build, Results, and long page sections.
- Product-facing names take precedence over issue, run, and result identifiers.
- Partial rendering failures remain local and recoverable.

### Persistence quality

- Saved Views restore the intended state deterministically.
- The last active state is retained per world.
- Curated content cannot be removed by ordinary cleanup without an explicit protected-content action.
- Missing or corrupt world assets are reported clearly and can be repaired.

### Operational quality

- The installed-world golden path works without internet access after required local assets are present.
- The golden path does not require CM1 execution.
- Lab tools remain available for future content development.
- Automated tests and one live acceptance pass cover the complete MVP journey.

## 13. Measurable completion criteria

The MVP is complete only when all of the following are demonstrated on the target MacBook Air.

### World entry

- Cloud Chamber opens to a Worlds-oriented entrance rather than requiring Build or Results first.
- Trade Cumulus is visible as installed content.
- Entering the world opens the Baseline or the last resumed view without launching CM1.
- Primary UI uses stable world and Simulation names rather than issue/run/result IDs.

### Integrated Explore workspace

- At a `1440 × 900` CSS-pixel desktop viewport, the three-dimensional scene, active slice, persistent timeline, and supporting inspector form one coherent workspace.
- The user does not need a long page-level scroll to move between the scene, slice, time controls, and primary explanation.
- Changing model time updates the scene and active Lens slice without a full page reload.
- Changing the Lens plane updates both the slice and its plane in the scene.
- One coherent Lens legend and control context represents the active Lens.
- Trade Cumulus diagnostics prioritize shallow-cloud questions rather than generic deep-convection or precipitation absence messages.

### Explanation and detail

- Authored explanation is available beside the visual evidence.
- Science and Details views expose the required evidence and provenance without dominating the primary scene.
- Atmospheric refresher text is direct, technically accurate, and optional.

### Saved Views and resume

- A user can save a view with a title and optional note.
- Reloading the application and opening that Saved View restores the scientific and visual state defined in this document.
- Re-entering Trade Cumulus resumes its last active view.
- Saved View restoration failures are explicit rather than silently falling back.

### Comparison

- The curated Baseline versus More Moisture Comparison opens from Trade Cumulus.
- The Comparison states what changed, what responded materially, what changed little or varied, and what stayed fixed.
- Either Simulation can be opened in the integrated Explore workspace.

### Content durability

- The expected Trade Cumulus content bundle is validated by stable identity and hashes.
- Ordinary cleanup does not remove protected world content.
- Missing or corrupt assets produce a bounded repair state rather than a broken or empty world.
- Multi-gigabyte model output remains outside Git.

### Failure isolation

- A failed three-dimensional scalar layer does not disable the Lens slice, timeline, explanation, or scientific evidence.
- Retry targets the failed layer.
- Missing Comparison evidence does not make the Baseline unavailable.

### Lab continuity

- The Lab remains reachable for package generation, runs, ingest, result evaluation, and storage work.
- Lab machinery is not presented as the primary entrance to installed worlds.

### Verification

- The full golden path has automated coverage where practical.
- One live acceptance pass records startup, world entry, playback, Lens use, Saved View restoration, Comparison, partial-layer failure, and Lab return.
- Performance thresholds for initial load, frame changes, and Saved View restoration are set in the approved Explore UX specification from measured MacBook Air baselines rather than guessed in this document.

## 14. Recommended implementation sequence

Implementation proceeds one bounded issue at a time.

### Increment 1 — Explore workspace UX specification

Create a PM-authored specification with:

- annotated desktop wireframe;
- information hierarchy;
- scene/slice/timeline layout;
- inspector behavior;
- Lens controls and legend placement;
- authored-explanation placement;
- world-aware diagnostics;
- layer-failure states;
- Save View behavior;
- exact current elements to remove, retain, or relocate;
- measurable interaction and performance targets based on the target machine.

Do not begin with an open-ended instruction to “clean up Explore.”

### Increment 2 — durable Trade Cumulus world bundle

Implement stable identities, manifest/hash validation, protected content, missing-content reporting, and bounded repair for the known Baseline, More Moisture, Comparison evidence, and authored content.

### Increment 3 — integrated Explore shell

Reorganize existing visual and scientific capabilities into the approved workspace before adding another scientific feature.

### Increment 4 — Saved Views and resume

Persist and restore the approved examination state and optional notes.

### Increment 5 — Worlds entry and golden path

Add direct world entry, resume, saved-view access, and Comparison entry.

### Increment 6 — Lab reframing

Retain current technical capabilities while moving them out of the primary installed-world hierarchy.

### Increment 7 — MVP hardening and personal acceptance

Complete content recovery, error states, performance verification, provenance access, automated coverage, and one live personal acceptance pass.

No second Cloud World, Control, or Lens should begin before the first MVP shell passes this gate unless a direct blocking contradiction is found.

## 15. Stage 7 exit and next bounded decision

This MVP definition is approved only when:

- issue #381 has exited successfully;
- the Stage 5 Trade Cumulus slice is accepted for MVP inclusion;
- the completed Stage 5B experiment track is explicitly accepted as satisfying the practical purpose of the old Stage 6 experimentation gate;
- the sole-user, personal-lab scope is approved;
- the included, excluded, and completion criteria are approved;
- issue #364 records the decision;
- the next work is one bounded Explore workspace UX specification.

The MVP approval gate does not authorize broad frontend implementation by itself.

The single next bounded issue after approval should be:

> **Define the integrated Explore workspace UX for the personal cloud laboratory MVP.**

That issue should produce the visual and interaction specification needed before Codex is asked to reorganize the current Explore implementation.
