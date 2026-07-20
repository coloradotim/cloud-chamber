---
name: Controlled work item
about: Define bounded implementation or recovery work before assigning it to Codex
title: ""
labels: ""
assignees: ""
---

## Outcome

What concrete result should exist when this issue is complete?

## Why this work is authorized

What approved product decision, recovery step, bug, operational need, or research question authorizes this work?

Relevant authority:

- `AGENTS.md`
- `NORTH_STAR.md`
- `docs/product/PRODUCT_VISION.md`
- explicit approved PM decisions:
- `docs/product/APPLICATION_SEMANTICS.md`
- `docs/DOCUMENTATION_STATUS.md`

## Stable vision

What remains unchanged regardless of the outcome of this issue?

## Scope

### Allowed files or systems

List the exact repository paths, directories, APIs, workflows, or systems that
may change. Use file paths rather than broad areas whenever possible.

### Explicitly out of scope

List nearby work that must not be included.

## Decisions already made

State the product, scientific, UX, or implementation decisions that this issue supplies to the implementer.

Do not ask Codex to infer these decisions from old issues, scenarios, roadmaps, or research notes.

## Supporting documents and evidence to inspect

List each implementation fact, document, issue, run record, or other source the
implementer must inspect. For each one, state whether it is authoritative,
current descriptive, an implemented contract, research evidence, a proposal,
historical, superseded, or unresolved. Do not treat it as a decision already
made unless an authority above explicitly supplies that decision.

## Decisions still open

List anything the implementer must stop and ask about rather than decide.

## Non-implications

What does completing this issue **not** establish?

Examples:

- this does not make the current scientific case, simulation, or run the whole product;
- this does not promote a mechanism into a supported Recipe;
- this does not make one cloud regime the permanent default;
- this does not define the MVP or final application structure.

## Acceptance criteria

- [ ]
- [ ]
- [ ]

## Verification

Required commands:

```text
scripts/check.sh
```

Additional tests or manual checks:

## Artifact and data restrictions

Do not commit:

- CM1 source or binaries;
- NetCDF output;
- generated run directories;
- runtime data or sounding caches;
- machine-private paths or settings;
- logs, screenshots, videos, traces, or large generated artifacts unless explicitly approved.

## Stop conditions

Stop and ask before:

- changing product direction or scientific interpretation not supplied above;
- changing recipe or scenario status;
- broadening the allowed file set;
- changing destructive cleanup or real CM1 execution behavior;
- creating, closing, rewriting, or reprioritizing another issue;
- creating follow-up issues;
- enabling auto-merge.

## Review posture

- Manual review required.
- Auto-merge must remain disabled.
