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
       presentation run — complete

#429 — Supercells slice-position navigation and missing camera controls
       — complete

#428 — shared live Context, below-the-fold Science | Notes | Details, and
       durable per-Simulation Notes across all three Worlds — complete

#395 — first-class Fun With Soundings workbench with five jobs, atmosphere
       continuity, Past Experiments, and direct non-World Explore — complete

#438 — typed World-aware curated Explore defaults, complete current-view
       Return to curated view, and visible bounded fallback — complete

#432 — versioned World-aware Explore state, last-active resume, and named
       Saved Views across Trade Cumulus, Mountain Waves, and Supercells
       — complete

#433 — ordinary World-aware Compare across all three Worlds, including the
       real controlled Supercells pair — complete

#434 — durable World-owned Saved Comparisons that reopen as live dual
       examinations — complete

#435 — approved Cloud World variation contracts and variation-program
       sequencing — complete

#394 — one owner-aware Activity and History model across current Worlds and
       Fun With Soundings — complete
```

The completed work preserves stable World and Simulation identities while allowing backing run assets to improve.

The shared Explore information architecture is:

```text
above the fold
  coordinated viewer(s) + controls + timeline + concise live Context

below the fold
  Science | Notes | Details
```

World-specific scientific content remains legitimate. Shared structure must not erase scientific or geometric differences.

Per-Simulation Notes are a bounded durable-content contract. They use stable
World and Simulation identity, persist across reloads, and fail visibly. They
remain separate from complete Explore state and Saved Views rather than
becoming a generic annotation framework.

Curated Explore defaults now define the intentional source-controlled
presentation for each supported Simulation and Field or Lens. Initial open and
Return to curated view consume the same definitions. Return restores the
current Field or Lens without changing Simulation, erasing Notes, or starting
playback. A visible technical fallback remains distinct from an authored
scientific presentation.

## Completed program: personal scientific memory and lifecycle

Issues #432, #433, and #434 establish durable Explore state, ordinary Compare,
and Saved Comparisons. Issue #435 approves the Cloud World variation contracts.
Issue #394 then reconciles lifecycle browsing before the shared variation
envelope is implemented.

The implemented contract represents, as applicable:

- World and stable Simulation identity;
- model time or playback range;
- Lens or Field state;
- three-dimensional camera and viewport;
- active plan or section orientation and physical coordinate;
- selected point or region;
- overlays and meaningful display settings;
- Context collapse state and active secondary-information section;
- Saved View title and optional short description;
- schema version and bounded migration or failure behavior.

Implementation followed this order:

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

The curated-default tier and complete return behavior are implemented through
#438. Issue #432 owns the durable state above that tier; it must consume rather
than recreate these defaults.

State is stored in bounded local libraries at
`<runtime-home>/explore-state/<world_id>/<simulation_id>.json`. Saved Views
reopen as live examinations, support rename and delete, preserve records when
backing output is unavailable, and report healthy, partially restorable, or
unavailable restoration. Notes remain separate.

Activity and History now consume one owner-aware lifecycle projection over
World inventory, run manifests, the queue, Results, runtime storage, and saved
state dependencies. Activity shows current actionable work. History preserves
the durable record and all known technical attempts. World ownership fails
closed, and approved-contract output can become automatically available without
a separate promotion ceremony.

## Completed program: World-aware Compare and Saved Comparisons

Issue #433 establishes ordinary Compare across the three accessible Worlds.
It builds comparison from two compatible Explore states rather than creating a
parallel examination model.

The current MVP decisions remain useful:

- configuration and lineage differences appear before interpretation;
- time links by modeled seconds rather than frame index;
- planes link by physical coordinate rather than array index;
- cameras link only through an honest compatible mapping;
- Lenses and scales link only when compatible;
- aligned, independent, and mixed states are supported;
- no interpolation is presented as model output.

The implemented sequence is:

```text
ordinary World-aware Compare
→ Saved Comparisons that reopen as live examinations
```

Trade Cumulus, Mountain Waves, and Supercells ask different comparison questions and may support different linked states.
Issue #433 establishes ordinary Compare. Issue #434 adds Saved Comparisons as
immutable World-owned workspace snapshots with editable metadata, direct live
reopen, current-descriptor reconciliation, missing-dependency recovery, and
reverse dependency lookup. They remain separate from per-Simulation Saved
Views and Notes.

The Supercells acceptance endpoint is the real retained Quarter-Circle
Supercell and Straight-Line Hodograph Supercell pair. It exercises all three
Lenses, physical horizontal and vertical sections, selected native evidence,
compatible camera mapping, aligned and independent operation, request
cancellation, and one-sided failure recovery. The controlled pair changes
hodograph curvature while retaining the other presentation-run contract.
Coordinates and local evidence are comparable; storm objects are not assigned
cross-Simulation lineage.

## Current implementation sequence

The approved sequence is:

```text
#394 — shared Activity and History — complete
#436 — retained-asset inventory and prelaunch disk budget — complete
#447 — shared variation envelope and Mountain Waves migration — next
#448 — queued after #447
#449 — queued after #448
```

Issue #435 is complete and
`docs/product/CLOUD_WORLD_VARIATION_CONTRACTS.md` now controls the bounded
variation-contract decisions. Issue #436 adds the read-only retained-asset
inventory, World run-cost profiles, immutable launch-review snapshots, and
immediate prelaunch disk gate. Issue #447 is the next queued major increment.
The current bodies and latest explicit PM comments for #447, #448, and #449
control their exact scope when activated.

Do not copy current Trade Cumulus or Mountain Waves controls into another World
without its approved contract. The user may change several supported settings
in one variation. Do not reduce the experience to one-variable wizards or imply
one-factor causation when several values changed.

Existing issues #389, #390, and #391 are superseded and are not current
implementation authority.

## Later durability and acceptance work

After the explicit sequence above, PM may choose bounded work such as:

- destructive cleanup;
- protection editing;
- backing selection;
- repair or reimport of missing retained assets;
- personal acceptance.

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
