# Cloud Chamber Documentation Status and Authority

## Authority and Status

The Cloud Chamber documentation tree contains current technical information,
research evidence, historical decisions, proposals, and superseded product
direction. A document's presence under `docs/` does not make it current
authority.

Use the hierarchy below.

## 1. Controlling Product Authority

Use this product-authority order:

1. [North Star](../NORTH_STAR.md)
2. [Product Vision](product/PRODUCT_VISION.md)
3. explicit approved PM decisions for bounded stage and implementation work
4. approved product-architecture documents:
   - [Application Semantics](product/APPLICATION_SEMANTICS.md)
   - [MVP](product/MVP.md)
   - [Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md)
5. bounded approved World or product documents such as
   [Trade Cumulus Product Slice](product/TRADE_CUMULUS_PRODUCT_SLICE.md)
6. current implementation documentation and code
7. research and run evidence

The North Star and Product Vision are the highest product authority.

Application Semantics defines Cloud World, Recipe, Simulation, Lens, Saved
View, Comparison, Exploration, Experiment, and supporting terms.

The MVP defines Cloud Chamber as a local, single-user personal cloud laboratory
and growing cloud-world atlas. The Current Product Sequence controls later
implementation ordering where it conflicts with the MVP's historical roadmap.
It does not reopen the MVP thesis or Application Semantics.

Current issue bodies and the latest explicit PM comments control each bounded
implementation task.

## 2. Approved Direction Versus Implemented State

Keep product approval separate from software availability:

| Subject | Approved direction | Current implemented state |
| --- | --- | --- |
| Cloud Worlds | A growing collection of explorable cloud regimes | Trade Cumulus, Mountain Waves, and Supercells are accessible |
| Fun With Soundings | A separate first-class atmospheric workbench | Not accessible; sounding and run capabilities remain in transitional paths |
| Saved Views | Durable user-curated views | Placeholder only; no durable Saved Views |
| Compare | Related Simulations can be compared | One featured Trade Cumulus Comparison; no ordinary World-aware Compare |
| Variation | Create a related Simulation from a World Simulation | Working Mountain Waves Lab path; no shared three-World workflow |
| Explore | World-specific science in a shared application vocabulary | Implemented separately for all three accessible Worlds |

The three Worlds share product vocabulary and core workspace behavior but may
legitimately differ in geometry, Lenses, controls, comparison questions, and
variation surfaces.

A World should expose only surfaces it implements. Do not create empty Lab,
Compare, or Saved View placeholders merely to make all Worlds structurally
identical.

Fun With Soundings is an approved first-class workbench, not a Cloud World.
Issue #395 remains queued; approval does not make the workbench accessible in
the current application.

The Trade Cumulus Product Slice remains subordinate to the North Star, Product
Vision, approved PM decisions, Application Semantics, and the MVP. Being
documented does not by itself make a Recipe, Lens, Comparison, or scientific
claim supported.

Do not rewrite approved concepts merely because their implementation is
incomplete. Do not describe approved but inaccessible work as shipped.

## 3. Current Product Sequence

[Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md) is the
repository authority for current implementation ordering. The latest approved
PM comment and issue body still control the exact scope of each bounded task.

The presentation-quality and three-World foundation is complete through #420,
#423, #421, #429, and #428. All three Explore implementations now use one
collapsible Context and shared below-the-fold Science, Notes, and Details
structure. Per-Simulation Notes are the first durable content contract; complete
Explore state and Saved Views remain unimplemented.

The next approved program is personal scientific memory: define one versioned,
World-aware serializable Explore-state contract before ordinary resume, named
Saved Views, or Compare work.

Rewritten issues #394 and #395 and issues #432 through #438 record bounded
follow-on product work for Activity and History, Fun With Soundings, durable
Explore state and Saved Views, Compare and Saved Comparisons, variation
contracts, retained assets, and curated defaults. Their presence does not
activate them or replace the sequencing authority. Issues #389, #390, and #391
were closed as superseded and are not current assignment authority.

Keep detailed ordering in Current Product Sequence and explicit later PM
decisions rather than duplicating a second roadmap here.

## 4. Repository and Agent Authority

- [AGENTS.md](../AGENTS.md)

`AGENTS.md` controls how agents and contributors operate during the current
gated product-architecture program. Repository recovery and semantic
architecture are completed earlier stages; their completion did not end the
requirements for bounded work, manual pull-request review, or disabled
auto-merge.

`AGENTS.md` does not replace product authority.

## 5. Current Descriptive Documents

- [README](../README.md)
- [Current State](current/CURRENT_STATE.md)
- [Current Architecture](current/CURRENT_ARCHITECTURE.md)
- [Ingest, Results, and Runtime Cleanup Lifecycle](current/INGEST_RESULTS_STORAGE_LIFECYCLE.md)

These documents describe current software and operations. They may identify
transitional behavior and implementation limits; they do not establish product
direction.

The current embedding of legacy Build and Results under Trade Cumulus does not
override the approved World Lab or Fun With Soundings concepts.

Do not update Current State or Current Architecture to describe an approved
future capability before its implementation merges. Update them when the
repository's actual descriptive state changes.

## 6. Development and Operational Documentation

- [Development](development/DEVELOPMENT.md)
- [Testing](development/TESTING.md)
- [CI and Branch Protection](development/CI_AND_BRANCH_PROTECTION.md)
- [Trusted LAN Worker](development/LAN_WORKER.md)

Use operational instructions where they remain accurate. Prefer commands,
paths, APIs, and test procedures that can be verified against current code.

Completed earlier-stage programs include:

- repository and operational-documentation recovery;
- documentation disposition audit;
- semantic architecture;
- active contract classification;
- archive moves for the highest-risk superseded product direction.

For documents not handled by those programs:

- do not execute old scenario sequencing or roadmap language;
- resolve product conflicts using the authority order above;
- preserve useful implementation and research evidence;
- request PM direction when a conflict affects bounded work.

## 7. Implemented Contracts

The active `docs/contracts/` directory contains verified current contracts:

- [Output Product Specification](contracts/output-product-specification.md)
- [Sounding Candidate Screening Contract](contracts/sounding-candidate-screening.md)

Implemented contracts describe current interfaces and behavior. They do not
define final product hierarchy or make a World, Recipe, Simulation,
Comparison, or Experiment scientifically supported.

Historical and proposal contracts live under `docs/archive/contracts/`.

## 8. Research and Experiment Evidence

Documents under `research/` record investigations, validation attempts, run
outcomes, literature findings, and design exploration.

Research is evidence. It is not automatically:

- product direction;
- a supported Recipe;
- roadmap priority;
- a default forcing or initiation mechanism;
- proof that a Result belongs to a Cloud World;
- proof that a research route is a product route.

Negative, failed, contradictory, and superseded evidence should be preserved.

## 9. Historical and Superseded Direction

Known high-risk archived examples include:

- [Thermal Fate product vision](archive/product-direction/product-vision-thermal-fate-legacy.md);
- [Cloud Chamber product spec](archive/product-direction/cloud-chamber-product-spec-legacy.md);
- [Architecture and data model](archive/product-direction/architecture-and-data-model-legacy.md);
- [Configurable observed-sounding roadmap](archive/roadmaps/configurable-observed-sounding-roadmap-legacy.md);
- [Thermal Fate process diagnostics](archive/product-direction/thermal-fate-diagnostics-legacy.md);
- [Guided experiment notebook UX reset](archive/ux/guided-experiment-notebook-reset-legacy.md);
- [legacy roadmap and startup issues](archive/roadmaps/roadmap-and-issues-legacy.md);
- [deep-convection package design proposal](archive/proposals/deep-convection-package-design-legacy.md).

Active-path documents may still contain superseded framing. Until bounded work
changes them:

- do not use them as controlling product authority;
- do not execute their roadmap language;
- do not delete them without approved disposition;
- do not update them merely for cosmetic consistency.

## Document Status Vocabulary

| Status | Meaning |
| --- | --- |
| **Authoritative** | Controls product or repository behavior |
| **Current descriptive** | Accurately describes present software or operations |
| **Implemented contract** | Describes a verified current interface |
| **Research evidence** | Records investigation or experiment results |
| **Proposal** | Suggests future behavior not yet approved or implemented |
| **Historical** | Preserved for project context |
| **Superseded** | Conflicts with or has been replaced by current authority |
| **Unresolved** | Requires product, scientific, or implementation review |

These labels are interpretive aids. The repository has not moved or relabeled
every file.

## Recommended Reading Paths

### Understand the Product

1. [North Star](../NORTH_STAR.md)
2. [Product Vision](product/PRODUCT_VISION.md)
3. [Application Semantics](product/APPLICATION_SEMANTICS.md)
4. [MVP](product/MVP.md)
5. [Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md)
6. relevant bounded World and product decisions
7. [Current State](current/CURRENT_STATE.md)
8. [Current Architecture](current/CURRENT_ARCHITECTURE.md)

### Contribute During the Gated Program

1. [AGENTS.md](../AGENTS.md)
2. explicit PM decisions and the controlling bounded issue
3. [Current Product Sequence](product/CURRENT_PRODUCT_SEQUENCE.md)
4. relevant product authority
5. current operational documentation
6. current code and tests

Ignore conflicting lower-authority product language and ask for direction when
a conflict affects the task.

### Understand a Scientific or CM1 Experiment

1. Identify the relevant research and run records.
2. Determine whether the work is canonical, adapted, exploratory, technical, or
   hypothetical.
3. Confirm the actual configuration, output, runtime integrity, and provenance.
4. Do not assume that a Result belongs to a Cloud World.
5. Do not assume that an experiment is a supported Recipe or product default.

### Understand Current Implementation

Use source code, tests, runtime contracts, [Current State](current/CURRENT_STATE.md),
[Current Architecture](current/CURRENT_ARCHITECTURE.md), and merged pull-request
history together.

Do not rely on one old product specification, roadmap, or research page.

## Program Note

The documentation tree has not been comprehensively reorganized. Remaining
moves, rewrites, archives, and implementation work require bounded approved
issues.

This status document records authority and current disposition. It does not
authorize bulk documentation changes or redefine product scope.
