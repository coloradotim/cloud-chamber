# Cloud Chamber Documentation Status and Authority

## Authority and status

The Cloud Chamber documentation tree contains current technical information, research evidence, historical decisions, proposals, and superseded product direction.

During repository recovery, a document’s presence under `docs/` does not make it current authority.

Use the hierarchy below.

## 1. Controlling product authority

These documents define why Cloud Chamber exists and what it is intended to become:

1. [North Star](../NORTH_STAR.md)
2. [Product Vision](product/PRODUCT_VISION.md)

They are the highest product authority in the repository.

No roadmap, issue, scenario, research note, architecture document, product specification, or implementation should silently redefine them.

Changes require explicit PM approval.

## 2. Repository and agent authority

- [AGENTS.md](../AGENTS.md)

`AGENTS.md` defines how agents and contributors must operate during repository recovery.

It does not replace the Product Vision. It prevents lower-level work from rewriting it.

## 3. Current descriptive documents

- [Current State](current/CURRENT_STATE.md)
- [Current Architecture](current/CURRENT_ARCHITECTURE.md)
- [Ingest, Results, And Runtime Cleanup Lifecycle](current/INGEST_RESULTS_STORAGE_LIFECYCLE.md)
- [README](../README.md)

These documents describe the current repository and application.

They may identify legacy behavior, unresolved questions, and capabilities under review. They do not establish the final product design.

## 4. Development and operational documentation

Documents such as these contain setup, testing, CI, runtime, and engineering information:

- [Development](development/DEVELOPMENT.md)
- [Testing](development/TESTING.md)
- [CI and Branch Protection](development/CI_AND_BRANCH_PROTECTION.md)
- [Trusted LAN Worker](development/LAN_WORKER.md)

Use their operational instructions where they remain accurate.

The read-only documentation disposition audit is complete and approved. Batch 3B-1 implemented the approved archive moves for the highest-risk superseded product-direction documents. Batch 3B-2 rebuilt the active architecture, development, testing, CI, lifecycle, and LAN-worker operational docs listed above.

For documents not yet handled by a recovery batch:

- prefer commands, paths, APIs, test procedures, and implemented behavior that can be verified;
- do not treat their product priorities, old priority labels, scenario sequencing, or future-work language as authoritative;
- resolve any conflict in favor of the North Star, Product Vision, Current State, and `AGENTS.md`.

## 5. Architecture and data-model documents

Architecture documents may describe real implemented systems and useful technical constraints.

They may also contain product assumptions inherited from earlier directions.

Interpret them as:

> This is what the current software does or was designed to do.

Do not automatically interpret them as:

> This is what the eventual product must be.

Architecture changes remain subject to the Product Vision and future experimentation and MVP decisions.

## 6. Contracts

Documents under `contracts/` may describe:

- implemented data contracts;
- current API behavior;
- partially implemented interfaces;
- proposed future contracts;
- product semantics that were codified before the current vision.

The approved documentation disposition includes the contracts directory.

Until the approved contract dispositions are implemented, verify a contract against current code before treating it as implemented. Do not use a proposal-only or stale contract to create new product direction.

## 7. Research and experiment evidence

Documents under `research/` record investigations, experiments, validation attempts, run outcomes, literature findings, and design exploration.

Research documents are valuable evidence.

They are not automatically:

- product direction;
- supported recipe definitions;
- roadmap priority;
- proof that an experimental mechanism should become a default;
- proof that one cloud regime should define Cloud Chamber.

Negative, failed, contradictory, and superseded research should be preserved rather than rewritten to make project history appear cleaner.

## 8. Historical and superseded product direction

Several formerly active-path documents containing superseded framing have been quarantined under archive paths.

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

Additional active-path documents may still contain superseded framing and approved disposition recommendations, including:

- scenario and recipe planning contracts tied to older product directions.

These files may contain useful technical or historical content.

Until they are archived, split, or rewritten:

- do not use them as controlling product authority;
- do not update them merely to make them appear consistent with the new vision;
- do not execute their roadmap language without a newly approved issue;
- do not delete them without an approved disposition.

## Document status vocabulary

The documentation audit classified documents using these terms:

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

These labels are interpretive aids. Repository recovery does not yet move or relabel every file.

## Recommended reading paths

### Understand the product

1. [North Star](../NORTH_STAR.md)
2. [Product Vision](product/PRODUCT_VISION.md)
3. [Current State](current/CURRENT_STATE.md)
4. [Current Architecture](current/CURRENT_ARCHITECTURE.md)

### Contribute during recovery

1. [AGENTS.md](../AGENTS.md)
2. [Current State](current/CURRENT_STATE.md)
3. [Development](development/DEVELOPMENT.md)
4. [Testing](development/TESTING.md)
5. [CI and Branch Protection](development/CI_AND_BRANCH_PROTECTION.md)

Ignore conflicting product-direction language in lower-authority documents and ask for direction when a conflict affects the task.

### Understand a scientific or CM1 experiment

1. Identify the relevant research document.
2. Check whether it records a canonical source, a reproduced case, a controlled adaptation, or only a hypothesis.
3. Confirm the actual CM1 configuration and run evidence.
4. Do not assume the experiment is a supported recipe or product default.

### Understand current implementation

Use the current source code, tests, runtime contracts, and Current State document together.

Do not rely on a single old product specification or roadmap.

## Recovery note

The documentation tree has not yet been comprehensively reorganized.

A read-only disposition manifest has evaluated every document and its recommendations have been approved. Those recommendations indicate whether to:

- keep it;
- rewrite it;
- split it;
- archive it;
- delete it;
- or defer judgment.

Batch 3B-1 implemented the approved quarantine of the highest-risk superseded product-direction documents and retired the obsolete roadmap pointer.

Batch 3B-2 rebuilt the current operational documentation set for architecture, development, testing, CI, lifecycle, and LAN-worker setup.

Remaining repository moves, rewrites, splits, archives, deletions, and deferrals from the approved disposition may still exist outside those handled paths.

No bulk document move or rewrite should occur outside the approved disposition implementation.
