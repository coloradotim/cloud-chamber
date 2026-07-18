# AGENTS.md — Cloud Chamber Repository Recovery

## Product authority

Before any nontrivial work, read:

1. `NORTH_STAR.md`
2. `docs/product/PRODUCT_VISION.md`

These are the controlling statements of why Cloud Chamber exists and what product it is intended to become.

Existing issues, scenarios, roadmaps, product specifications, research notes, UI language, and implementation structures may reflect superseded product directions. They are evidence and history, not automatic product authority.

When a lower-level artifact conflicts with the North Star or Product Vision, stop and ask for direction. Do not reconcile the conflict by silently changing the product.

## Repository recovery mode

Cloud Chamber is currently in repository recovery.

Until recovery mode is explicitly ended:

- all pull requests require manual review;
- do not enable auto-merge;
- do not create follow-up issues autonomously;
- do not infer roadmap priority from the open issue backlog;
- do not treat the current app structure as the final product design;
- do not treat current scenarios as validated recipes;
- do not promote research mechanisms, scores, triggers, or one-off runs into product concepts;
- do not revise the North Star or Product Vision;
- do not make product, science, recipe, scenario, roadmap, or UX decisions unless the task explicitly supplies the decision.

## Codex and agent role

During recovery, agents execute bounded decisions. They do not formulate product strategy.

A recovery task must specify:

- the exact files allowed to change;
- the exact intended disposition or replacement content;
- what must not change;
- whether the task is mechanical, descriptive, research, or product work;
- the required manual-review posture.

If a task requires deciding whether a historical document, scenario, issue, experiment, or capability is still valid, stop and ask. That is PM judgment, not mechanical cleanup.

## Product-drift check

Before proposing or implementing a nontrivial change, state:

```text
Stable vision:
What remains unchanged?

Current task:
What specific part of the vision or recovery does this advance?

Non-implications:
What does this work not redefine?

Portfolio effect:
Does this preserve, broaden, or accidentally narrow Cloud Chamber?
```

The current experiment is never the whole product.

## Allowed work during recovery

Allowed when explicitly requested:

- repository inventory and read-only audits;
- exact documentation changes supplied by the PM;
- approved mechanical file moves or link updates;
- tests and fixes required by those exact changes;
- critical fixes preventing data loss, corrupted results, or broken development workflows;
- manually reviewed dependency and security maintenance;
- preservation of existing research and experimental evidence.

## Work that requires explicit approval

Always stop and ask before:

- changing product direction;
- changing scientific interpretation;
- adding or promoting a recipe or scenario;
- changing default cloud regimes, triggers, forcing, or sounding behavior;
- changing user-facing scientific language;
- changing navigation or top-level workspaces;
- changing destructive cleanup behavior;
- touching real CM1 execution paths;
- making backwards-incompatible manifest, result, or scenario-schema changes;
- closing, rewriting, reprioritizing, or creating issues;
- changing authoritative documents.

## Engineering guardrails

Do not commit:

- CM1 source;
- CM1 binaries;
- NetCDF output;
- generated run directories;
- `LANDUSE.TBL`;
- local runtime data;
- downloaded IGRA cache data;
- large processed visualization artifacts;
- machine-private paths or settings.

Use tiny fixtures and fake process execution in automated tests. Do not require real CM1 runs in CI.

Use branches and pull requests. Do not push directly to `main`.

Run `scripts/check.sh` before opening a PR unless the task explicitly explains why it cannot be run.

Do not remove or weaken tests merely to make a change pass.

Preserve the distinction between:

```text
configured experiment
running CM1 process
completed CM1 output
backend-derived diagnostic
visualization interpretation
```

## Current implementation is not current vision

Existing capabilities may remain valuable even when their framing is under review. Preserve working infrastructure unless a reviewed task explicitly removes it.

In particular, do not assume that repository recovery means deleting:

- local CM1 execution;
- run queueing and progress;
- ingest and result persistence;
- observed-sounding support;
- scientific field products;
- result replay and timelapse;
- 2-D or 3-D visualization;
- provenance and runtime-integrity handling.

Their future product roles will be decided after the experimentation path and MVP are defined.
