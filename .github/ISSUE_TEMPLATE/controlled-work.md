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

- `NORTH_STAR.md`
- `docs/product/PRODUCT_VISION.md`
- approved decision, issue, or evidence:

## Stable vision

What remains unchanged regardless of the outcome of this issue?

## Scope

### Allowed files or systems

List the exact files, directories, APIs, workflows, or systems that may change.

### Explicitly out of scope

List nearby work that must not be included.

## Decisions already made

State the product, scientific, UX, or implementation decisions that this issue supplies to the implementer.

Do not ask Codex to infer these decisions from old issues, scenarios, roadmaps, or research notes.

## Decisions still open

List anything the implementer must stop and ask about rather than decide.

## Non-implications

What does completing this issue **not** establish?

Examples:

- this does not make the current experiment the whole product;
- this does not promote a mechanism into a supported recipe;
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
