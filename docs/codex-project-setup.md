# Codex Project Setup Notes

## Repository

```text
cloud-chamber
```

Likely local directory:

```text
/Users/timpeterson/Documents/Codex/cloud-chamber
```

## Current Strategic Files

Read these before product work:

```text
README.md
AGENTS.md
docs/cloud-first-product-reset.md
docs/product-vision.md
docs/current-roadmap.md
docs/cloud-chamber-product-spec.md
docs/architecture-and-data-model.md
```

`AGENTS.md` is the operational authority for coding-agent behavior. The
cloud-first reset and current roadmap are the strategic authority.

## App Architecture

```text
React/Vite frontend + Python FastAPI local backend
```

Why:

- Python handles xarray/NetCDF and local CM1 orchestration.
- React handles Build, Results, Explore, and visual interaction.
- The local backend can launch and manage CM1 processes.

Do not package a desktop wrapper until the local workflow creates a clear need.

## CM1 Local Path

Likely current local CM1 path:

```text
/Users/timpeterson/cm1r21.1/run
```

Do not hard-code it. Store local paths in `~/CloudChamber/settings.json`.

## Runtime And Git Policy

Runtime data belongs outside the repo:

```text
~/CloudChamber/
```

Never commit:

- generated CM1 runs;
- NetCDF output;
- CM1 source or binaries;
- logs;
- machine-private settings or paths;
- large visualization artifacts.

Keep tiny fixtures, code, tests, docs, schemas, and recipe definitions in git.

## Development Principles

1. CM1 output is the source of truth for cloud evolution.
2. Analyzer/recommendation, configuration, active process, completed result, and
   visualization interpretation remain distinct.
3. Build should recommend useful sounding–recipe–run-setup combinations rather
   than requiring the user to interpret soundings alone.
4. Strong idealized cloud recipes are acceptable when clearly labeled.
5. Real CM1 scouts are part of cloud-making implementation; automated CI still
   uses tiny fake fixtures.
6. Use the existing Build queue/progress/ETA/stop/cleanup workflow for scouts and
   visible automatic full-run promotion.
7. Prefer one outcome-oriented vertical slice over many partial plumbing issues.

## Codex Workflow

- Start from current `main`.
- Work on a branch named for the user outcome or issue.
- Do not push directly to `main`.
- Read `AGENTS.md`, especially **Cloud-Making Operating Mode**.
- Scope work to one user outcome, not one implementation layer.
- Ask only material unresolved questions; do not wait for another go-ahead when
  the issue and approved product direction are explicit.
- Add tests and update docs with implementation changes.
- Run meaningful bounded CM1 scouts early when cloud-making is in scope.
- If a run is boring, change sounding, recipe, scale, duration, or trigger before
  adding diagnostics.
- Create a separate issue only for a real blocker or independent product
  decision.
- Run `scripts/check.sh` and relevant E2E checks before opening a PR.
- Open a PR that describes the cloud/user outcome and real-run evidence where
  applicable.
- Enable auto-merge after CI unless the change is destructive/high-risk or the
  user requests manual review.

## High-Risk Actions

Ask before:

- deleting user runtime data beyond an explicit cleanup request;
- launching an unbounded or unexpectedly expensive batch;
- changing product direction outside the approved cloud-first reset;
- making backwards-incompatible schema changes without migration;
- weakening tests rather than fixing the underlying problem.

Do not pause merely because an approved cloud-making issue touches real CM1,
additive schemas, recipe assumptions, or a bounded scout/full-run workflow.

## Local Checks

```sh
scripts/check.sh
```

Use Playwright for user-visible workflow changes when practical. Real CM1 evidence
belongs in local runtime verification and the PR description; generated output
stays outside git.
