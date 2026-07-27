# Cloud Chamber Current State

**Status:** Current descriptive implementation snapshot

## Purpose

This document describes the software and repository as they exist today. It is
not a roadmap or a substitute for product authority.

Read higher-authority documents first:

1. [North Star](../../NORTH_STAR.md)
2. [Product Vision](../product/PRODUCT_VISION.md)
3. [Application Semantics](../product/APPLICATION_SEMANTICS.md)
4. [MVP](../product/MVP.md)

Where current implementation is incomplete, this document records the gap
without changing the approved product direction.

## Current Application

Cloud Chamber is a local, single-user atmospheric laboratory. Its primary
entrance is a Cloud Worlds home with three accessible Worlds:

```text
Cloud Chamber
├── Trade Cumulus
├── Mountain Waves
├── Supercells
└── Fun With Soundings — atmospheric workbench
```

Each World owns stable World and Simulation identities. Those product
identities resolve to local retained run and result assets; they are not the
same thing as CM1 run IDs, result IDs, or filesystem paths.

**Fun With Soundings** is accessible as a separate atmospheric workbench, not
a Cloud World. Its stable route is `/fun-with-soundings`, with a direct
non-World Explore route at `/fun-with-soundings/explore/{result_id}`.

## Fun With Soundings

The workbench organizes the existing observed-atmosphere path into five jobs:

```text
Find Soundings → Candidates → Build & Run → Runs → Explore
```

Atmosphere selection remains visible across Find, Candidates, and Build & Run.
The implementation reuses the existing package, local and LAN-worker execution,
serial queue, ingest, storage, cleanup, and visualization paths.

The workbench preserves explicit lifecycle language:

- a **Run** is technical CM1 execution;
- an ingested non-World record is an **Experiment**;
- a World-owned **Simulation** is shown only when current World inventory
  verifies stable Simulation identity and matching run and result links;
- ambiguous, stale, or unavailable ownership evidence remains visibly legacy
  or unassigned.

The Runs job shows Soundings execution without claiming other use of the shared
CM1 runner as workbench-owned. Past Experiments supports Soundings,
legacy/unassigned, and verified World ownership views. A verified Simulation
opens in its World; other retained Experiments open directly in non-World
Explore.

## Accessible Cloud Worlds

| World | Current content | Current surfaces | Current limitation |
| --- | --- | --- | --- |
| **Trade Cumulus** | Canonical BOMEX Baseline and More Moisture retained Simulations | Overview, Simulations, featured and ordinary Compare, Lab, Explore resume, and Saved Views | Lab still embeds transitional Build and Results; Saved Comparisons are absent |
| **Mountain Waves** | Dry Ridge and Boulder Windstorm retained Simulations | Overview, Simulations, ordinary Compare, variation Lab, Explore resume, and Saved Views | Variation remains World-specific; Saved Comparisons are absent |
| **Supercells** | Quarter-Circle and Straight-Line Hodograph retained Simulations | Overview, Simulations, ordinary Compare, Explore resume, and Saved Views | No variation Lab or Saved Comparisons |

The World Overview and Simulations surfaces use stable content identities and
explicit availability states. Missing, invalid, or conflicting retained
content fails closed instead of silently substituting a different run.

## Explore Experiences

The three Explore implementations share Cloud Chamber's interaction and visual
vocabulary while preserving the geometry and evidence native to each regime.

### Trade Cumulus

Trade Cumulus Explore combines:

- a true three-dimensional shallow-cloud point field;
- native horizontal and vertical scalar slices;
- direct Field inspection and an Updraft Lens;
- a cloud boundary and horizontal-wind evidence;
- fixed World-owned scientific scales;
- synchronized time, slice position, selected-point evidence, and Context.

### Mountain Waves

Mountain Waves output is native two-dimensional x-z data. Explore therefore
uses:

- one large terrain-aware x-z scientific view;
- direct Field inspection;
- Wave Structure and Wave Cloud Lenses;
- expanded-height and true-physical-scale geometry;
- terrain, wind, cloud-point, boundary, saturation, and potential-temperature
  evidence where applicable;
- fixed World-owned scales, timeline, selected-point evidence, and Context.

There is no fake singleton-y three-dimensional extrusion.

### Supercells

Supercells Explore coordinates:

- a three-dimensional storm view;
- native horizontal x-y and vertical x-z and y-z sections;
- Rotating Updraft, Cloud and Precipitation, and Low-Level Interactions Lenses;
- storm-region and full-domain inspection;
- fixed World-owned scales and World-specific overlays;
- synchronized camera, slice position, timeline, selected-point evidence, and
  Context.

The sections use native model coordinates. Moving between a Lens and a direct
slice preserves the selected orientation and position where the underlying
data permits.

## Curated Explore Defaults

Each Cloud World now owns typed authored Explore presentations. Initial open
and **Return to curated view** consume the same definitions; component
initialization is not a second source of scientific defaults.

| World and view | Authored presentation |
| --- | --- |
| Trade Cumulus Field | Simulation-specific modeled time and vertical x-z plane, cloud-liquid field, overview camera, accepted cloud opacity and point size |
| Trade Cumulus Updraft Lens | The same Simulation-specific time and plane, `trade_cumulus_updraft_velocity_v1`, overview camera, cloud boundary, perturbation wind, and accepted Lens opacity |
| Dry Ridge Field or Wave Structure Lens | 2,160 s, full domain, expanded height; Field retains its selected supported field, while Wave Structure uses vertical velocity, horizontal wind, and potential-temperature contours |
| Boulder Windstorm Field, Wave Structure, or Wave Cloud Lens | 7,200 s, focus region, expanded height; Field retains its selected supported field, while each Lens restores its accepted overlays and fixed scale |
| Supercells Rotating Updraft | 4,440 s, storm region, horizontal x-y at z = 3.167 km, look-along-y camera, and the accepted rotation and updraft-helicity evidence |
| Supercells Cloud and Precipitation | 4,440 s, storm region, vertical x-z at y = 0.75 km, look-along-y camera, and the accepted hydrometeor-category presentation |
| Supercells Low-Level Interactions | 4,440 s, storm region, horizontal x-y at z = 1.167 km, low-level camera, and the accepted rain, precipitating-condensate, wind, and vertical-motion evidence |

Return restores the authored state for the currently active Field or Lens. It
does not switch views unexpectedly, change Simulation, erase Notes, or start
playback. It also restores modeled time, physical plane, viewport, geometry,
camera, layers, overlays, display settings, selection, Context, and the
secondary Science section where those dimensions apply.

The resolver reports authored-default application, partial incompatibility, or
a technical fallback. Missing times, planes, fields, scales, or layers are
explained visibly; fallback does not rewrite the authored definition or claim
that a substituted scientific presentation is equivalent.

## Durable Explore State And Saved Views

Each supported Simulation now stores the last coherent Explore examination and
an explicitly managed list of named Saved Views. The common envelope is
versioned and keyed to stable World and Simulation identity; Trade Cumulus,
Mountain Waves, and Supercells retain explicit World-specific payloads rather
than one flattened control inventory.

Startup precedence is:

```text
explicitly opened Saved View
> last active state
> curated Simulation / active Field-or-Lens default
> technical fallback
```

Resume waits for a coherent loaded target and does not persist transient
loading, playback-running, maximize-only, or error state. User interaction made
before a delayed resume response wins. Resume writes are serialized and
coalesced so an older request cannot overwrite newer examination state.

Saved Views can be created, listed, opened as live examinations, renamed, and
deleted. Open remains visibly in progress until the required scientific
evidence loads. Restoration status is recorded only after that result is known;
a metadata-write failure is reported without invalidating the usable restored
view. Missing retained output preserves the Saved View record and marks it
unavailable.

State is stored locally at:

```text
<runtime-home>/explore-state/<world_id>/<simulation_id>.json
```

Writes are atomic and bounded. Unsupported schemas, invalid values, oversized
files, and persistence failures are visible local failures. Per-Simulation
Notes remain separate and are not copied into Saved Views.

## Ordinary Compare

Each accessible World can compare two compatible retained Simulations through
one ordinary Compare workflow. The pair-review step presents lineage,
configuration differences, retained-output compatibility, and caveats before
loading frames. The live workspace supports aligned, independent, and mixed
coordination of modeled time, Field or Lens, physical slice plane, compatible
camera state, and selected-point evidence.

Compare coordinates existing Simulation and Explore state without creating a
new scientific object. Its state is transient: it does not create a Saved
Comparison or alter either Simulation or its Saved Views.

Supercells now exercises the complete workflow with a controlled real pair:
Quarter-Circle Supercell and Straight-Line Hodograph Supercell. The two
Simulations retain matched thermodynamics, trigger, grid, timing, output
inventory, model translation, and numerical options while changing hodograph
curvature. Compare maps physical coordinates and local native evidence; it
does not claim that storm structures on the two sides have object lineage.

## Shared Scientific Presentation

Current Explore surfaces use:

- fixed-across-time, World-owned scales rather than per-frame autoscaling;
- concise legends with explicit units and displayed frame extrema;
- backend-derived, bounded payloads rather than browser-side NetCDF parsing;
- native coordinates and declared derived quantities;
- selected-point evidence tied to actual payload values;
- persistent playback and saved-output controls;
- explicit loading, missing-content, and failure states.

Each Explore now places concise, context-sensitive explanation and current
selected-point evidence in one collapsible **Context** inspector. Supporting
content follows the shared below-the-fold **Science | Notes | Details**
structure. Science remains World-specific, Notes persist by stable World and
Simulation identity, and Details contain technical and provenance evidence.

World-specific Lenses combine fields and overlays to answer a bounded
scientific question. A Lens is an interpretation layer, not a new model field
or a claim of unsupported process evidence.

## Retained Presentation Simulations

The built-in World content currently resolves to retained presentation-quality
CM1 output:

| World | Stable Simulation | Current retained run |
| --- | --- | --- |
| Trade Cumulus | Canonical BOMEX Baseline | `trade-cumulus-presentation-v1-baseline-20260722` |
| Trade Cumulus | More Moisture | `trade-cumulus-presentation-v1-more-moisture-20260722` |
| Mountain Waves | Dry Ridge | `dry-mountain-wave-presentation-v1-20260722` |
| Mountain Waves | Boulder Windstorm | `moist-mountain-wave-presentation-v1-20260722` |
| Supercells | Quarter-Circle Supercell | `quarter-circle-supercell-presentation-v1-20260723` |
| Supercells | Straight-Line Hodograph Supercell | `straight-line-supercell-presentation-v1-20260726` |

These run IDs identify current local artifacts, not permanent product identity.
The large NetCDF histories remain outside Git under the runtime home.

## Transitional Capabilities

Working infrastructure remains available even where its product placement is
not final:

- observed-sounding search, screening, caching, and package configuration,
  now organized in Fun With Soundings;
- CM1 package generation and provenance review;
- local CM1 launch, serial queueing, progress, cancellation, and ingest;
- Results records with local notes, tags, diagnostics, and cleanup;
- generic field and result inspection;
- trusted-LAN execution for supported paths;
- runtime-integrity and field-quality handling.

Some of this infrastructure appears inside the current Trade Cumulus Lab.
That transitional placement does not make Build or Results the final World Lab
information architecture.

## Current Gaps

The implemented application does not yet provide:

- one shared World-aware variation workflow across all accessible Worlds;
- Saved Comparisons or durable comparison workspaces.

Per-Simulation Notes and Explore state are separate durable contracts. Saved
Views persist the live scientific examination dimensions owned by issue #432;
they do not create Saved Comparisons or certify scientific validity.
Older issues #389, #390, and #391 are closed as superseded by the current
three-World implementation sequence; they should not be read as active roadmap
authority.

## Local-First Runtime

The current technical flow is:

```text
React / TypeScript / Vite frontend
-> Python / FastAPI backend
-> generated CM1 package and manifest
-> external CM1 process
-> local NetCDF histories and runtime evidence
-> backend validation, ingest, diagnostics, and visualization payloads
-> browser inspection
```

Runtime assets default to `~/CloudChamber`. The application depends on those
local assets for retained Simulations and generated Experiments. Deleting a run
can remove the corresponding output and result sidecars; the repository is not
a durable store for those artifacts.

## Interpretation Rules

- **Accessible** means the user can reach the World or surface in the current
  application.
- **Implemented** means a capability exists in the current software; it does
  not elevate that capability above product authority.
- **Retained Simulation** means validated output is available locally for a
  stable Simulation identity.
- **Presentation run** describes the current backing artifact, not the stable
  Simulation identity.
- **Lens** means a World-owned scientific interpretation of available evidence,
  not a new prognostic field.
- **Transitional** does not mean disposable; it means the eventual product
  placement remains incomplete.
- Research pages and one-off validation artifacts are evidence, not product
  routes.

## Updating This Document

Update this file when the material descriptive state changes. Do not use it to
approve a new World, Recipe, scientific interpretation, or implementation
sequence.
