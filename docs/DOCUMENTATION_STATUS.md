# Cloud Chamber Documentation Status and Authority

## Authority and status

The Cloud Chamber documentation tree contains current technical information, research evidence, historical decisions, proposals, and superseded product direction.

A document’s presence under `docs/` does not make it current authority.

Use the hierarchy below.

## 1. Controlling product authority

Use this product-authority order:

1. [North Star](../NORTH_STAR.md)
2. [Product Vision](product/PRODUCT_VISION.md)
3. explicit approved PM decisions for bounded stage and implementation work
4. approved product-architecture documents:
   - [Application Semantics](product/APPLICATION_SEMANTICS.md)
   - [MVP](product/MVP.md)
   - [Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md)
5. bounded approved product documents such as [Trade Cumulus Product Slice](product/TRADE_CUMULUS_PRODUCT_SLICE.md)
6. current implementation documentation and code
7. research and run evidence

The North Star and Product Vision are the highest product authority.

Application Semantics is the approved semantic authority for Cloud World, Recipe, Simulation, Lens, Saved View, Comparison, Exploration, Experiment, and supporting terms.

The MVP is approved controlling scope for Cloud Chamber as a single-user personal cloud laboratory and growing cloud-world atlas. PR #384 established the MVP. Issue #396 amended its homepage, Fun With Soundings, Trade Cumulus Lab, variation, and original implementation-roadmap details.

The Current Product Sequence records later approved sequencing across the current World portfolio. It supersedes only conflicting implementation-order language in the older MVP and documentation-status roadmaps. It does not reopen the MVP thesis or Application Semantics.

The current approved destination model is:

```text
Cloud Chamber
├── Trade Cumulus — Cloud World
├── Mountain Waves — Cloud World
├── Supercells — approved Cloud World; implementation governed by #423
└── Fun With Soundings — Atmospheric workbench
    ├── Find Soundings
    ├── Candidates
    ├── Build & Run
    └── Past Experiments
```

Cloud Worlds are not organized for the sole user under Installed, Draft, candidate, graduated, or development-state categories. Technical content availability remains an operational state.

A World should expose only surfaces it actually implements. Do not create empty Lab, Compare, Saved View, or other placeholders merely to make all Worlds look structurally identical.

Fun With Soundings is a first-class workbench and is not a Cloud World.

The Trade Cumulus Product Slice remains a bounded scientific/product document. It is subordinate to the North Star, Product Vision, approved PM decisions, Application Semantics, the MVP, and the Current Product Sequence. It does not make a Recipe, Control, Lens, Comparison, or scientific claim supported merely by being documented.

PM decisions and product documents do not silently rewrite higher authority. Changes require explicit PM approval.

## 2. Repository and agent authority

- [AGENTS.md](../AGENTS.md)

`AGENTS.md` defines how agents and contributors must operate during the gated program. It does not replace product authority.

## 3. Current descriptive documents

- [Current State](current/CURRENT_STATE.md)
- [Current Architecture](current/CURRENT_ARCHITECTURE.md)
- [Ingest, Results, And Runtime Cleanup Lifecycle](current/INGEST_RESULTS_STORAGE_LIFECYCLE.md)
- [README](../README.md)

These documents describe current software and operations.

They may identify legacy behavior, unresolved questions, and implementation constraints. They do not establish final product design.

Do not update Current State or Current Architecture to describe an approved future capability before its implementation merges. Update them later when the repository’s actual descriptive state changes.

## 4. Development and operational documentation

- [Development](development/DEVELOPMENT.md)
- [Testing](development/TESTING.md)
- [CI and Branch Protection](development/CI_AND_BRANCH_PROTECTION.md)
- [Trusted LAN Worker](development/LAN_WORKER.md)

Use operational instructions where they remain accurate.

Stage 1 operational-documentation recovery, the disposition audit, and the highest-risk archive moves are complete.

Stage 2 semantic architecture is complete.

Stage 3 contract classification is complete.

For documents not handled by those programs:

- prefer commands, paths, APIs, test procedures, and implemented behavior that can be verified;
- do not execute old product priorities, scenario sequencing, or roadmap language without a current approved issue;
- resolve product conflicts in favor of the authority order above.

## 5. Architecture and data-model documents

Architecture documents may describe real implemented systems and useful constraints. They may also contain product assumptions inherited from earlier directions.

Interpret them as:

> This is what the current software does or was designed to do.

Do not automatically interpret them as:

> This is what the eventual product must be.

Architecture changes remain subject to approved product authority and bounded implementation issues.

## 6. Implemented contracts

The active `docs/contracts/` directory contains current implemented contracts verified against code and tests:

- [Output Product Specification](contracts/output-product-specification.md)
- [Sounding Candidate Screening Contract](contracts/sounding-candidate-screening.md)

These contracts describe interfaces and current behavior. They do not define the final product hierarchy or make Cloud Worlds, Recipes, Simulations, Comparisons, or workbench experiments scientifically supported.

Historical and proposal contracts live under `docs/archive/contracts/`.

## 7. Research and experiment evidence

Documents under `research/` record investigations, validation attempts, run outcomes, literature findings, and design exploration.

Research is evidence. It is not automatically:

- product direction;
- a supported Recipe;
- roadmap priority;
- proof that an experimental mechanism should be a default;
- proof that a sounding experiment belongs to a Cloud World;
- proof that a Cloud World should be categorized by development state.

Negative, failed, contradictory, and superseded evidence should be preserved.

## 8. Historical and superseded product direction

Known high-risk archived examples include:

- [Thermal Fate product vision](archive/product-direction/product-vision-thermal-fate-legacy.md);
- [Cloud Chamber product spec](archive/product-direction/cloud-chamber-product-spec-legacy.md);
- [Architecture and data model](archive/product-direction/architecture-and-data-model-legacy.md);
- [Configurable observed-sounding roadmap](archive/roadmaps/configurable-observed-sounding-roadmap-legacy.md);
- [Thermal Fate process diagnostics](archive/product-direction/thermal-fate-diagnostics-legacy.md);
- [Guided experiment notebook UX reset](archive/ux/guided-experiment-notebook-reset-legacy.md);
- [Codex project setup notes](archive/setup/codex-project-setup-legacy.md);
- [legacy roadmap and startup issues](archive/roadmaps/roadmap-and-issues-legacy.md);
- [deep-convection package design proposal](archive/proposals/deep-convection-package-design-legacy.md).

Active-path documents may still contain superseded framing. Until bounded work changes them:

- do not use them as controlling product authority;
- do not update them merely for cosmetic consistency;
- do not execute their roadmap language;
- do not delete them without approved disposition.

## Document status vocabulary

| Status | Meaning |
|---|---|
| **Authoritative** | Controls product or repository behavior |
| **Current descriptive** | Accurately describes present software or operations |
| **Implemented contract** | Describes a verified current interface |
| **Research evidence** | Records investigation or experiment results |
| **Proposal** | Suggests future behavior not yet approved or implemented |
| **Historical** | Preserved for project context |
| **Superseded** | Conflicts with or has been replaced by current authority |
| **Unresolved** | Requires product, scientific, or implementation review |

These labels are interpretive aids. The repository has not moved or relabeled every file.

## Recommended reading paths

### Understand the product

1. [North Star](../NORTH_STAR.md)
2. [Product Vision](product/PRODUCT_VISION.md)
3. [Application Semantics](product/APPLICATION_SEMANTICS.md)
4. [MVP](product/MVP.md)
5. [Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md)
6. relevant bounded World/product decision records
7. [Current State](current/CURRENT_STATE.md)
8. [Current Architecture](current/CURRENT_ARCHITECTURE.md)

### Contribute during the gated program

1. [AGENTS.md](../AGENTS.md)
2. approved PM decisions in issue #364 and the controlling bounded issue
3. [Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md)
4. [MVP](product/MVP.md)
5. [Application Semantics](product/APPLICATION_SEMANTICS.md)
6. relevant current operational documentation
7. current code and tests

Ignore conflicting product-direction language in lower-authority documents and ask for direction when a conflict affects the task.

### Understand a scientific or CM1 experiment

1. Identify the relevant research and run records.
2. Determine whether it is a canonical source, controlled adaptation, exploratory sounding experiment, technical mechanism, or hypothesis.
3. Confirm the actual configuration, output, integrity, and provenance.
4. Do not assume that a Result belongs to a Cloud World.
5. Do not assume that an experiment is a supported Recipe or product default.

### Understand current implementation

Use current source code, tests, runtime contracts, Current State, and merged PR history together.

Do not rely on one old product specification or roadmap.

## 9. Current implementation sequence

The controlling sequence is maintained in [Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md).

The currently approved order is:

```text
#420 — higher-resolution presentation runs for the current Trade Cumulus and
       Mountain Waves built-in Simulations

→ #423 — build Supercells as the third three-dimensional Cloud World

→ #421 — produce and adopt the higher-resolution, denser-cadence,
         longer-duration Supercell presentation run

→ return to shared functionality across the three-World application
```

After #421, PM will freshly scope the next program from the implemented product. The intended areas are:

- durable World-aware Explore state, resume, and Saved Views;
- ordinary related-Simulation Compare and saved Comparisons;
- a fresh review of variations across Trade Cumulus, Mountain Waves, and Supercells;
- later notes, content durability, cleanup, repair, Activity/History consistency, and personal acceptance.

The older bodies of issues #389, #390, and #391 remain useful prior plans, but they are not current assignment authority until PM reviews and updates or replaces them for the three-World application.

Issue #364 records major activation, exit, and roadmap changes. Current issue bodies and latest PM comments control each bounded implementation scope. Older comments are historical when a later PM comment explicitly supersedes them.

## Program note

The documentation tree has not been comprehensively reorganized.

Completed or approved program work includes:

- operational-documentation recovery;
- semantic architecture;
- contract classification;
- canonical BOMEX and Trade Cumulus evidence;
- the Trade Cumulus Updraft Lens, fixed scale, and first featured Comparison;
- approved MVP authority and World-scoped foundation;
- Mountain Waves benchmark, visualization, World, Explore, and variation work;
- Supercell benchmark selection, exact reproduction, examination validation, and the approved Supercells World decision;
- active presentation-quality run work for current Worlds;
- active Supercells implementation and approved later high-resolution Supercell run.

Remaining repository moves, rewrites, archives, and implementation work must occur through bounded approved issues.

No bulk documentation or product rewrite is authorized by this status document.