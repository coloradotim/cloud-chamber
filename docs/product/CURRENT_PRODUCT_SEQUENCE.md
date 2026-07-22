# Cloud Chamber Current Product Sequence

**Status:** Approved PM sequencing direction.

## Purpose and authority

This document records the current implementation sequence and the product areas to revisit after the present Cloud World work is complete.

It is subordinate to:

1. `NORTH_STAR.md`;
2. `docs/product/PRODUCT_VISION.md`;
3. explicit later PM decisions;
4. `docs/product/APPLICATION_SEMANTICS.md`;
5. `docs/product/MVP.md`.

Where this document conflicts with the historical implementation ordering in section 19 of `docs/product/MVP.md` or section 9 of `docs/DOCUMENTATION_STATUS.md`, this document controls the **current sequence only**. It does not reopen the MVP thesis, product semantics, or the approved meaning of Cloud Worlds, Simulations, Lenses, Explore, Compare, Saved Views, or variations.

Current issue bodies and the latest explicit PM comments continue to control the bounded scope of each implementation task.

## Product-drift check

```text
Stable vision:
Cloud Chamber remains Tim's personal laboratory for creating beautiful,
scientifically meaningful cloud worlds, seeing invisible atmospheric
processes, changing the atmosphere, and learning from the response.

Current task:
Improve the presentation quality of the existing Worlds, build Supercells as
the third World, replace its proof-quality output with a higher-resolution
presentation run, and then return to shared product functionality.

Non-implications:
This does not create public users, collaboration, a marketplace, a generic
visualization framework, a universal CM1 editor, operational forecasting, or
an automatic roadmap for every open issue.

Portfolio effect:
The work broadens and strengthens the cloud-world atlas while preserving the
shared personal-laboratory model.
```

## Current product portfolio

Cloud Chamber now has or has explicitly approved the following first-class destinations:

```text
Cloud Chamber
├── Trade Cumulus — Cloud World
├── Mountain Waves — Cloud World
├── Supercells — Cloud World approved; implementation in #423
└── Fun With Soundings — atmospheric workbench
```

The three Worlds share product vocabulary and core workspace behavior, but they are not required to have identical geometry, Lenses, controls, comparison questions, or variation surfaces.

- **Trade Cumulus** is a three-dimensional shallow-cloud World.
- **Mountain Waves** is currently an honest terrain-aware two-dimensional World.
- **Supercells** is an approved three-dimensional deep-convection World.
- **Fun With Soundings** remains a non-World workbench for observed atmospheres and broader experiments.

A World appears as a World. Do not expose candidate, installed, draft, graduated, or authoring-maturity taxonomy to the sole user.

## Immediate implementation sequence

The approved sequence is:

```text
#420 — generate higher-resolution presentation runs for the four existing
       Trade Cumulus and Mountain Waves Simulations

→ #423 — build Supercells as the third three-dimensional Cloud World using
         the current accepted benchmark output

→ #421 — generate and adopt the higher-resolution, denser-cadence,
         longer-duration Supercell presentation run

→ return to shared product functionality across the three-World application
```

### #420 — current presentation runs

Issue #420 may improve and replace the backing output for the current built-in Trade Cumulus and Mountain Waves Simulations. It should preserve their stable product identities while improving spatial detail, animation cadence, and experiential quality.

### #423 — Supercells World

Issue #423 implements the approved `supercells` World, the stable `supercells_quarter_circle_reference` Simulation identity, the integrated three-dimensional Explore workspace, and the three accepted Lenses:

- Rotating Updraft;
- Cloud and Precipitation;
- Low-Level Interactions.

It may use the accepted Gate B benchmark as the initial backing output. It must not bind product identity or frontend routing permanently to that run ID.

### #421 — Supercell presentation run

Issue #421 produces the more detailed, smoother, and longer Supercell output after the production Explore contract exists. If accepted, that output should normally become the backing asset for the same stable Quarter-Circle Supercell identity rather than creating a parallel product path.

This ordering intentionally lets the World implementation establish the required fields, payloads, scales, timeline semantics, and performance behavior before the expensive final run is adopted.

## Direction after #421

After #421 is accepted, return to functionality that makes Cloud Chamber durable and worth revisiting across Worlds.

The next program should cover the areas below, but the exact issue order and scope require a fresh PM decision against the then-current three-World implementation.

### Durable Explore state, resume, and Saved Views

Establish one World-aware, serializable Explore-state contract that can represent the actual implemented geometries and controls, including as applicable:

- World and Simulation identity;
- model time or playback range;
- Lens or Field state;
- three-dimensional camera and viewport;
- active plan or section view and physical coordinates;
- selected point or region;
- overlays and meaningful display settings;
- inspector section and collapse state;
- title and optional note.

Ordinary last-active-state resume and an explicitly named Saved View are related but distinct behaviors.

The contract must work for Trade Cumulus, Mountain Waves, and Supercells without pretending their view state is identical.

### Ordinary Compare and saved Comparisons

Revisit ordinary related-Simulation Compare as a shared World capability.

The current MVP decisions remain useful:

- differences appear before interpretation;
- time links by modeled seconds rather than frame index;
- planes link by physical coordinate rather than array index;
- cameras link only through an honest compatible mapping;
- Lenses and scales link only when compatible;
- aligned, independent, and mixed states are supported;
- no interpolation is presented as model output.

The implementation must be World-aware. Trade Cumulus, Mountain Waves, and Supercells ask different comparison questions and may support different linked states.

Saved Comparisons should follow the ordinary Compare state contract and reopen as live examinations, not screenshots.

### Variations require a fresh review

Do **not** execute the older general variation roadmap or copy the current Trade Cumulus and Mountain Waves variation surfaces into Supercells without reconsideration.

The existing work is valuable implementation evidence, but the variation model should be reviewed against the actual three-World product after #421.

That review must decide, World by World:

- which Simulations are eligible parents;
- which physical and numerical settings are worth exposing;
- which settings require profiles, grouped controls, or advanced disclosure;
- appropriate default duration, grid, and output cadence for ordinary personal experiments;
- how expensive runs are estimated and communicated;
- which differences are required for lineage and Compare;
- what makes a completed Result inspectable as the named Simulation;
- which controls are genuinely shared and which are World-specific;
- whether a shared variation shell with World-specific contracts is better than separate implementations;
- what Supercells variations should initially permit.

The user may change several supported settings in one variation. Do not reduce the experience to one-variable wizards or imply one-factor causation when several values changed.

Existing issues such as #391, #389, and #390 are prior bounded plans. They must be reviewed and updated or replaced before assignment; their older bodies are not automatic current implementation authority.

### Later durability and acceptance work

After Saved Views, Compare, and the refreshed variation direction are established, revisit:

- Simulation notes;
- saved Comparison notes and explanations;
- content protection and dependency-aware cleanup;
- repair of missing retained assets;
- Activity and History consistency across Worlds;
- personal acceptance and measured performance on the target machine.

Do not create the entire follow-on backlog in advance. Create the next bounded issue when the preceding implementation and PM review provide the required evidence.

## Sequencing rules

- One major implementation issue remains active at a time unless Tim explicitly authorizes overlap.
- Expensive CM1 execution work and application implementation may overlap only when their ownership and runtime constraints do not conflict.
- Presentation-run upgrades preserve stable World and Simulation identities unless a later PM decision says otherwise.
- Shared functionality must be built against the actual three-World application, not only generalized from Trade Cumulus.
- World-specific scientific and visual differences remain legitimate; shared shells must not erase them.
- Do not assign #389, #390, #391, or derived follow-on work without a fresh scope review after #421.
- Do not begin Squall Line #414 under this sequence.
- Manual PM review and disabled auto-merge remain required.

## Updating this document

Update this document when PM changes the active sequence or approves the next shared-functionality program.

Do not use routine implementation completion to silently expand product scope. Current implementation status belongs in descriptive documentation after the relevant PRs merge.