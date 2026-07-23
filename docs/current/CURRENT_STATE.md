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
└── Supercells
```

Each World owns stable World and Simulation identities. Those product
identities resolve to local retained run and result assets; they are not the
same thing as CM1 run IDs, result IDs, or filesystem paths.

**Fun With Soundings** is approved as a separate atmospheric workbench, not a
Cloud World. It is not currently accessible as a first-class application
destination. Issue #395 remains open for that work.

## Accessible Cloud Worlds

| World | Current content | Current surfaces | Current limitation |
| --- | --- | --- | --- |
| **Trade Cumulus** | Canonical BOMEX Baseline and More Moisture retained Simulations | Overview, Simulations, Saved Views placeholder, featured Comparison, Lab, and Explore | Saved Views are not durable; ordinary World-aware Compare is not implemented; Lab still embeds transitional Build and Results |
| **Mountain Waves** | Dry Ridge and Boulder Windstorm retained Simulations | Overview, Simulations, variation Lab, and Explore | Variation is World-specific rather than shared; no ordinary Compare or Saved Views |
| **Supercells** | Quarter-Circle Supercell retained Simulation | Overview, Simulations, and Explore | No variation Lab, ordinary Compare, or Saved Views |

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

These run IDs identify current local artifacts, not permanent product identity.
The large NetCDF histories remain outside Git under the runtime home.

## Transitional Capabilities

Working infrastructure remains available even where its product placement is
not final:

- observed-sounding search, screening, caching, and package configuration;
- CM1 package generation and provenance review;
- local CM1 launch, serial queueing, progress, cancellation, and ingest;
- Results records with local notes, tags, diagnostics, and cleanup;
- generic field and result inspection;
- trusted-LAN execution for supported paths;
- runtime-integrity and field-quality handling.

Some of this infrastructure appears inside the current Trade Cumulus Lab.
That transitional placement does not make Build or Results the final World Lab
information architecture, and it does not make Fun With Soundings accessible.

## Current Gaps

The implemented application does not yet provide:

- durable Saved Views;
- ordinary World-aware Compare beyond the featured Trade Cumulus Comparison;
- one shared World-aware variation workflow across all accessible Worlds;
- a first-class Fun With Soundings entrance;
- durable persistence for complete Explore or comparison workspaces.

Per-Simulation Notes are durable content, but camera, time, Lens, overlay,
selection, and other complete Explore workspace state are not yet persisted.
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
