# Cloud Chamber Current Product Sequence

**Status:** Approved PM sequencing direction.

## Purpose and authority

This document records the current implementation sequence now that Cloud Chamber has established its first three Cloud Worlds.

It is subordinate to:

1. `NORTH_STAR.md`;
2. `docs/product/PRODUCT_VISION.md`;
3. explicit later PM decisions;
4. `docs/product/APPLICATION_SEMANTICS.md`;
5. `docs/product/MVP.md`.

Where this document conflicts with historical implementation ordering in `docs/product/MVP.md` or `docs/DOCUMENTATION_STATUS.md`, this document controls the **current sequence only**. It does not reopen the MVP thesis, product semantics, or the approved meaning of Cloud Worlds, Simulations, Lenses, Explore, Compare, Saved Views, or variations.

Current issue bodies and the latest explicit PM comments control each bounded implementation task.

## Product-drift check

```text
Stable vision:
Cloud Chamber remains Tim's personal laboratory for creating beautiful,
scientifically meaningful cloud worlds, seeing invisible atmospheric
processes, changing the atmosphere, and learning from the response.

Current task:
Finish the first three-World Explore foundation, make examination state
persistent, support ordinary comparison, and then reconsider variations
against the actual product.

Non-implications:
This does not create public users, collaboration, a marketplace, a generic
visualization framework, a universal CM1 editor, operational forecasting, or
an automatic roadmap for every open issue.

Portfolio effect:
The work deepens the existing cloud-world atlas before another World is added.
```

## Current product portfolio

Cloud Chamber has the following first-class destinations:

```text
Cloud Chamber
├── Trade Cumulus — Cloud World
├── Mountain Waves — Cloud World
├── Supercells — Cloud World
└── Fun With Soundings — atmospheric workbench
```

The three Worlds share product vocabulary and core workspace behavior, but they are not required to have identical geometry, Lenses, controls, comparison questions, or variation surfaces.

- **Trade Cumulus** is a three-dimensional shallow-cloud World.
- **Mountain Waves** is currently a terrain-aware two-dimensional World.
- **Supercells** is a three-dimensional deep-convection World.
- **Fun With Soundings** remains a non-World workbench for observed atmospheres and broader experiments.

A World appears as a World. Do not expose candidate, installed, draft, graduated, or authoring-maturity taxonomy to the sole user.

## Completed foundation and current transition

The presentation-quality and third-World program established:

```text
#420 — higher-resolution presentation runs for the four existing
       Trade Cumulus and Mountain Waves Simulations — complete

#423 — Supercells as the third three-dimensional Cloud World — complete

#421 — higher-resolution, denser-cadence, longer-duration Supercell
       presentation run — final adoption review in PR #430
```

The completed work preserves stable World and Simulation identities while allowing backing run assets to improve.

PR #430 must complete its bounded review corrections and merge before #421 is treated as complete. No additional CM1 run is required unless a later explicit PM decision authorizes one.

## Immediate bounded follow-ups

After PR #430 merges, execute:

```text
#429 — add slice-position navigation and missing 3-D camera controls to
       Supercells Explore

→ #428 — commonalize live Context and below-the-fold Science, Notes, and
         Details across all three Worlds
```

### #429 — complete Supercells spatial navigation

Issue #429 closes a bounded usability gap in the accepted Supercells workspace:

- move horizontal and vertical evidence planes by native physical coordinate;
- keep the represented 2-D and 3-D planes synchronized;
- preserve user-selected slice positions during playback;
- expose zoom and vertical-pan controls already supported by the shared 3-D viewer behavior;
- preserve per-Lens camera and slice state.

It does not reopen Supercell Lens questions, scales, scientific fields, or rendering design.

### #428 — shared Explore information architecture

Issue #428 should establish one recognizable information hierarchy across Trade Cumulus, Mountain Waves, and Supercells:

```text
above the fold
  coordinated viewer(s) + controls + timeline + concise live Context

below the fold
  Science | Notes | Details
```

World-specific scientific content remains legitimate. Shared structure must not erase scientific or geometric differences.

Per-Simulation Notes introduced through this work must be treated as the first bounded durable-content contract, not as disposable frontend-only state or a general annotation platform. The contract should use stable World and Simulation identity, persist across reloads, fail visibly, and leave a clear extension path for later Saved Views and Saved Comparisons without implementing those features now.

Issue #428 must not serialize complete Explore state, implement resume, create Saved Views, or establish a generic annotation framework. Those belong to the next program after the shared information architecture is stable.

## Next program: personal scientific memory

After #429 and #428, establish one versioned, World-aware Explore-state contract before implementing Compare.

The contract should represent, as applicable:

- World and stable Simulation identity;
- model time or playback range;
- Lens or Field state;
- three-dimensional camera and viewport;
- active plan or section orientation and physical coordinate;
- selected point or region;
- overlays and meaningful display settings;
- Context collapse state and active secondary-information section;
- title and optional note;
- schema version and bounded migration or failure behavior.

Implement in this order:

```text
serializable Explore state
→ ordinary last-active-state resume
→ explicitly named Saved Views
```

Ordinary resume and Saved Views are related but distinct. The contract must work for all three Worlds without pretending their state is identical.

Use this default-state precedence:

```text
explicit Saved View
> last active state
> curated Simulation/Lens default
> technical fallback
```

Provide a clear return to the curated default state.

## Then: ordinary Compare and Saved Comparisons

Build ordinary Compare from two compatible Explore states rather than creating a parallel examination model.

The current MVP decisions remain useful:

- configuration and lineage differences appear before interpretation;
- time links by modeled seconds rather than frame index;
- planes link by physical coordinate rather than array index;
- cameras link only through an honest compatible mapping;
- Lenses and scales link only when compatible;
- aligned, independent, and mixed states are supported;
- no interpolation is presented as model output.

Implement in this order:

```text
ordinary World-aware Compare
→ Saved Comparisons that reopen as live examinations
```

Trade Cumulus, Mountain Waves, and Supercells ask different comparison questions and may support different linked states.

## Variations require a fresh review

Do **not** execute the older general variation roadmap or copy current Trade Cumulus and Mountain Waves controls into Supercells without reconsideration.

Review the variation model against the actual three-World product after Saved Views and ordinary Compare establish the required state and lineage contracts.

Decide, World by World:

- which Simulations are eligible parents;
- which physical and numerical settings are worth exposing;
- which settings require profiles, grouped controls, or advanced disclosure;
- appropriate default duration, grid, and output cadence for ordinary experiments;
- how runtime and retained-storage cost are estimated and communicated;
- which differences are required for lineage and Compare;
- what makes a completed Result eligible to become a named Simulation;
- which controls are genuinely shared and which are World-specific;
- whether one shared variation shell with World-specific contracts is preferable;
- what Supercells variations should initially permit.

The user may change several supported settings in one variation. Do not reduce the experience to one-variable wizards or imply one-factor causation when several values changed.

Existing issues #389, #390, and #391 are prior bounded plans. They must be updated or replaced before assignment; their older bodies are not current implementation authority.

## Later durability and acceptance work

After Saved Views, Compare, and refreshed variation direction are established, revisit:

- Saved Comparison notes and explanations;
- Activity and History consistency across Worlds;
- the Result-to-Simulation promotion lifecycle;
- protected built-in and user-created retained assets;
- visible storage cost and dependency-aware deletion;
- repair or reimport of missing retained assets;
- version migration for durable state;
- measured performance and personal acceptance on the target machine.

Do not create the entire follow-on backlog in advance. Create or rewrite the next bounded issue when preceding implementation and PM review provide the necessary evidence.

## Deferred World expansion

Do not begin Squall Line issue #414 under this sequence.

A fourth World should not be activated merely because the Supercell program completed. PM must first decide that adding another scientific regime is more valuable than making the existing three Worlds durable, comparable, and experimentally useful.

## Sequencing rules

- One major implementation issue remains active at a time unless Tim explicitly authorizes overlap.
- Expensive CM1 execution and application implementation may overlap only when ownership and runtime constraints do not conflict.
- Presentation-run upgrades preserve stable World and Simulation identities unless a later PM decision says otherwise.
- Shared functionality must be built against the actual three-World application, not generalized only from Trade Cumulus.
- World-specific scientific and visual differences remain legitimate; shared shells must not erase them.
- Do not assign #389, #390, #391, or derived work without fresh scope review.
- Manual PM review and disabled auto-merge remain required.

## Updating this document

Update this document when PM changes the active sequence or approves the next shared-functionality program.

Routine implementation completion must not silently expand product scope. Current implementation facts belong in descriptive documentation after the relevant PRs merge.