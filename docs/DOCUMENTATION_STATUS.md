# Cloud Chamber Documentation Status and Authority

## Authority and status

The Cloud Chamber documentation tree contains current technical information, research evidence, historical decisions, proposals, and superseded product direction.

A document’s presence under `docs/` does not make it current authority.

## 1. Controlling product authority

Use this order:

1. [North Star](../NORTH_STAR.md)
2. [Product Vision](product/PRODUCT_VISION.md)
3. explicit approved PM decisions for bounded stage and implementation work
4. approved product-architecture documents:
   - [Application Semantics](product/APPLICATION_SEMANTICS.md)
   - [MVP](product/MVP.md)
   - [Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md)
5. bounded approved World or product documents
6. current implementation documentation and code
7. research and run evidence

The North Star and Product Vision are the highest product authority.

Application Semantics controls the meaning of Cloud World, Recipe, Simulation, Lens, Saved View, Comparison, Exploration, Experiment, and supporting terms.

The MVP controls Cloud Chamber’s approved scope as a single-user personal cloud laboratory and growing cloud-world atlas. The Current Product Sequence controls later implementation ordering where it conflicts with the MVP’s historical roadmap. It does not reopen the MVP thesis or Application Semantics.

Current issue bodies and the latest explicit PM comments control bounded implementation scope.

## 2. Current approved destination model

```text
Cloud Chamber
├── Trade Cumulus — Cloud World
├── Mountain Waves — Cloud World
├── Supercells — Cloud World
└── Fun With Soundings — atmospheric workbench
```

The three Worlds share product vocabulary and core workspace behavior but may legitimately differ in geometry, Lenses, controls, comparison questions, and variation surfaces.

A World should expose only surfaces it actually implements. Do not create empty Lab, Compare, Saved View, or other placeholders merely to make all Worlds structurally identical.

Cloud Worlds are not organized for the sole user under Installed, Draft, candidate, graduated, or development-state categories. Technical content availability remains an operational state.

Fun With Soundings is a first-class workbench and is not a Cloud World.

The [Trade Cumulus Product Slice](product/TRADE_CUMULUS_PRODUCT_SLICE.md) remains a bounded scientific/product document subordinate to higher authority. Its presence does not by itself establish a Recipe, Control, Lens, Comparison, or scientific claim.

## 3. Repository and agent authority

- [AGENTS.md](../AGENTS.md)

`AGENTS.md` defines how agents and contributors must operate. It does not replace product authority.

## 4. Current descriptive documents

- [Current State](current/CURRENT_STATE.md)
- [Current Architecture](current/CURRENT_ARCHITECTURE.md)
- [Ingest, Results, And Runtime Cleanup Lifecycle](current/INGEST_RESULTS_STORAGE_LIFECYCLE.md)
- [README](../README.md)

These documents describe current software and operations. They may identify legacy behavior, unresolved questions, and implementation constraints. They do not establish final product design.

Do not update Current State or Current Architecture to describe an approved future capability before its implementation merges. Update them when the repository’s actual descriptive state changes.

Current State and Current Architecture now require a bounded factual refresh after the completed World and presentation-run work. Until that update merges, use current code, tests, merged PR history, and the Current Product Sequence together rather than treating their older Build/Results/Explore framing as complete.

## 5. Development and operational documentation

- [Development](development/DEVELOPMENT.md)
- [Testing](development/TESTING.md)
- [CI and Branch Protection](development/CI_AND_BRANCH_PROTECTION.md)
- [Trusted LAN Worker](development/LAN_WORKER.md)

Use operational instructions where they remain accurate.

Operational-documentation recovery, the documentation disposition audit, semantic architecture, and active-contract classification are complete.

For documents not handled by those programs:

- prefer verifiable commands, paths, APIs, test procedures, and implemented behavior;
- do not execute old product priorities, scenario sequencing, or roadmap language without a current approved issue;
- resolve product conflicts in favor of the authority order above.

## 6. Architecture and data-model documents

Architecture documents may describe real implemented systems and useful constraints while also containing product assumptions inherited from earlier directions.

Interpret them as:

> This is what the current software does or was designed to do.

Do not automatically interpret them as:

> This is what the eventual product must be.

Architecture changes remain subject to approved product authority and bounded implementation issues.

## 7. Implemented contracts

The active `docs/contracts/` directory contains current implemented contracts verified against code and tests:

- [Output Product Specification](contracts/output-product-specification.md)
- [Sounding Candidate Screening Contract](contracts/sounding-candidate-screening.md)

These contracts describe interfaces and current behavior. They do not define the final product hierarchy or make a Cloud World, Recipe, Simulation, Comparison, or workbench experiment scientifically supported.

Historical and proposal contracts live under `docs/archive/contracts/`.

## 8. Research and experiment evidence

Documents under `research/` record investigations, validation attempts, run outcomes, literature findings, and design exploration.

Research is evidence. It is not automatically:

- product direction;
- a supported Recipe;
- roadmap priority;
- proof that an experimental mechanism should be a default;
- proof that a sounding experiment belongs to a Cloud World;
- proof that a new Cloud World should be activated.

Negative, failed, contradictory, and superseded evidence should be preserved.

## 9. Historical and superseded product direction

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
6. relevant bounded World and product decisions
7. [Current State](current/CURRENT_STATE.md)
8. [Current Architecture](current/CURRENT_ARCHITECTURE.md)

### Contribute

1. [AGENTS.md](../AGENTS.md)
2. explicit PM decisions and the controlling bounded issue
3. [Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md)
4. [MVP](product/MVP.md)
5. [Application Semantics](product/APPLICATION_SEMANTICS.md)
6. relevant operational documentation
7. current code and tests

Ignore conflicting lower-authority roadmap language and ask for direction when a conflict affects the task.

### Understand a scientific or CM1 experiment

1. Identify the relevant research and run records.
2. Determine whether the work is a canonical source, controlled adaptation, exploratory sounding experiment, technical mechanism, or hypothesis.
3. Confirm the actual configuration, output, integrity, and provenance.
4. Do not assume that a Result belongs to a Cloud World.
5. Do not assume that an experiment is a supported Recipe or product default.

### Understand current implementation

Use current source code, tests, runtime contracts, Current State, Current Architecture, and merged PR history together. Do not rely on one old product specification or roadmap.

## 10. Current implementation sequence

The controlling sequence is maintained in [Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md).

The presentation-quality and third-World foundation is:

```text
#420 — Trade Cumulus and Mountain Waves presentation runs — complete
#423 — Supercells World and Explore — complete
#421 — high-resolution Supercell presentation run — final adoption review
```

After #421 merges, the immediate bounded follow-ups are:

```text
#429 — Supercells slice-position and 3-D camera navigation
→ #428 — shared Context and Science | Notes | Details information architecture
```

Issue #428 may establish durable per-Simulation Notes as the first bounded durable-content contract. It must not also implement complete Explore-state persistence, resume, Saved Views, Saved Comparisons, or a generic annotation framework.

The next program should then establish:

```text
versioned World-aware Explore state
→ last-state resume
→ Saved Views
→ ordinary World-aware Compare
→ Saved Comparisons
→ fresh three-World variation review
```

Later work should reconcile Activity and History, Result-to-Simulation promotion, retained-asset protection, storage and dependency-aware deletion, repair, state migration, performance, and personal acceptance.

Issues #389, #390, and #391 remain useful prior plans but are not current assignment authority until PM updates or replaces them for the three-World application.

Squall Line issue #414 remains blocked. Completion of the Supercell program does not automatically activate a fourth World.

## Program note

Completed or approved work includes:

- operational-documentation recovery;
- semantic architecture and contract classification;
- canonical BOMEX and Trade Cumulus evidence;
- Trade Cumulus World, Updraft Lens, fixed scale, featured Comparison, and presentation runs;
- Mountain Waves benchmark, visualization, World, Explore, variation, and presentation runs;
- Supercell benchmark selection, exact reproduction, examination validation, World, Explore, and presentation run pending final adoption corrections;
- approved MVP authority and World-scoped foundation.

Remaining repository moves, rewrites, archives, and implementation work must occur through bounded approved issues.

No bulk documentation or product rewrite is authorized by this status document.