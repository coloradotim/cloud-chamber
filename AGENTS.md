# AGENTS.md - Cloud Chamber

## Project Identity

Cloud Chamber is a local-first configuration, run-management, and visualization environment for CM1 cloud experiments.

The goal is to make CM1 usable and beautiful for guided cloud-physics exploration.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.

## Product Rule

CM1 is the high-fidelity model. The app should not pretend to be CM1.

Reduced/light models may be used only for:

- preview
- explanation
- rough guidance
- sanity checks

They are not the source of truth for cloud evolution.

## Durable Distinction

Always distinguish:

```text
Preview estimate
CM1 run configuration
CM1 running/completed result
Visualization interpretation
```

## Guardrails

Do not commit:

- CM1 source
- CM1 binaries
- NetCDF output
- generated run directories
- LANDUSE.TBL
- local-data
- large processed visualization artifacts

Do commit:

- code
- tests
- docs
- schemas
- scenario templates
- tiny fixtures

## Development Expectations

- Use GitHub issues and PRs.
- Work on branches; do not push directly to `main`.
- Keep work scoped to the issue.
- Add tests for new behavior.
- Update docs when architecture/workflow changes.
- Use local fake fixtures in CI; do not require real CM1 in automated tests.
- Do not weaken scientific honesty to make UI look better.
- For Codex issue work, enable auto-merge after required CI checks pass unless the user explicitly asks for manual review or the PR is high-risk/destructive.
- Treat destructive cleanup, generated-data policy changes, scientific interpretation changes, and real CM1 execution changes as high-risk unless the user says otherwise.

## Initial Architecture Bias

Prefer:

```text
React/Vite frontend + Python FastAPI local backend
```

until a stronger reason appears.

## Local CM1 Runtime

CM1 should remain external to the repo.

Likely local path for Tim:

```text
/Users/timpeterson/cm1r21.1/run
```

Treat this as a local setting, not a hard-coded app constant.

Default Cloud Chamber runtime data belongs outside the repo:

```text
~/CloudChamber/
```

`./local-data/` is only a gitignored development override.

## UI Language

Use atmospheric language first:

- lower-atmosphere humidity
- surface moisture
- surface heating
- cap strength
- cap height
- dry air aloft
- mixing / entrainment
- cloud base
- cloud top
- first cloud time
- rain onset

Raw namelist settings belong in advanced/developer views.

## Testing Notes

Use fake/small fixtures to test:

- scenario schemas
- config generation
- run manifest creation
- fake process execution
- NetCDF ingestion from tiny fixtures
- visualizer metadata loading

Do not require full CM1 runs in CI.

## Before Major Changes

If changing product direction, ask first.

If adding physics/science behavior, document:

1. what physical question it supports
2. what user control it enables
3. what diagnostics validate it
4. what limitations must be disclosed

---

## Claude Code — Working Style and Expectations

This section governs how Claude Code operates on this project. It extends
the rules above; nothing here overrides the product rule, guardrails, or
scientific-honesty requirements.

### Intent First

Before writing any code on a non-trivial task, Claude Code must:

1. State what it understands the goal to be.
2. Ask every question needed to fully understand intent — user workflow,
   edge cases, acceptance criteria, what "done" looks like.
3. Propose an approach and wait for a go-ahead before executing.

For small, obviously-scoped tasks (typo fixes, single-line changes, adding
a missing test for existing behavior) it may proceed directly.

When in doubt, ask. A short clarifying exchange is cheaper than a wrong
implementation.

### Autonomy

Once intent is confirmed, Claude Code should execute as fully as possible
without interruption:

- Write the code.
- Write or update tests.
- Run `scripts/check.sh` and fix any failures before committing.
- Update relevant docs if architecture or workflow changed.
- Open a PR with a clear description.
- Create GitHub issues for anything discovered during work that is out of
  scope for the current task (bugs, missing tests, doc gaps, a11y issues).
  Do not silently leave TODOs for things that deserve tracking.

Do not ask for permission to run the linter, run tests, fix a type error,
or update a doc string. Those are part of the job.

### Branching and PRs

- Branch off `main`. Name branches `issue-NNN-short-description`.
- One issue per branch. Keep PRs scoped.
- PR description must include:
  - What changed and why.
  - How to verify it locally (specific commands or UI steps).
  - Any known limitations or follow-up issues opened.
- Enable auto-merge after CI passes unless the task is high-risk (see
  Guardrails above) or the user asks for manual review.

### Commit Style

- Conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`.
- Subject line: imperative, ≤72 chars.
- Body: include the issue number and a sentence on why, not just what.
- Atomic commits — one logical change per commit. Do not bundle unrelated
  fixes.

### Quality Bar

Every PR must pass `scripts/check.sh` cleanly before merge:

- Frontend: lint, test, build.
- Backend: ruff format, ruff check, mypy, pytest.
- No new warnings introduced without explanation.

New behavior requires new tests. Refactors must not reduce test coverage.
UI changes that affect user-visible text or workflow must include an update
to the relevant doc in `docs/`.

### GitHub Issues

When Claude Code opens an issue it must:

- Use the correct label set (see repo labels).
- Write a description a future developer can act on without context:
  summary, observed behavior, expected behavior, reproduction steps or
  fix hint.
- Tag `priority:p1` for bugs that break core workflows; `priority:p2` for
  everything else unless the user says otherwise.
- Reference the PR or commit that surfaced it.

### What Claude Code Must Not Do Without Asking

Even with full autonomy confirmed, always pause and ask before:

- Changing product direction or adding a new top-level workspace/view.
- Changing scientific interpretation, diagnostic labels, or provenance
  language.
- Modifying data deletion logic or storage cleanup policy.
- Touching real CM1 execution paths.
- Changing the run manifest schema or result card schema in a
  backwards-incompatible way.
- Removing or weakening a test rather than fixing the underlying issue.

### Environment Assumptions

Claude Code sessions assume:

- `scripts/dev.sh start` has been run (frontend at `localhost:5173`,
  backend at `127.0.0.1:8000`).
- `~/CloudChamber/settings.json` exists with local CM1 paths if CM1
  work is in scope.
- `uv` or the pip fallback described in `docs/development.md` is
  available for backend work.
- The Playwright E2E suite lives at `~/e2e/` (separate from the repo)
  and can be run with `npx playwright test` from that directory.

### Playwright E2E

When fixing a UI bug or adding a UI feature:

- Check whether an existing Playwright test covers it.
- If yes, verify the test passes after the change.
- If no, add a test or open an issue noting the gap.
- Never delete or skip a Playwright test to make CI pass. Fix the
  underlying issue or open an issue and mark the test `.skip` with a
  comment referencing it.

### Documentation Standard

- `docs/development.md` is the canonical dev setup reference. Keep it
  current.
- `docs/architecture-and-data-model.md` must reflect any schema or
  API contract changes.
- `docs/roadmap-and-issues.md` should be updated when milestones
  shift significantly.
- Inline code comments explain *why*, not *what*. Remove comments that
  just restate the code.

### Maintainability Bias

Prefer:

- Explicit over clever.
- Small, testable functions over large ones.
- Types everywhere in TypeScript and Python.
- Clear error messages that name the problem and suggest a fix.
- Fail loudly on bad state rather than silently degrade.

When two approaches are roughly equivalent, choose the one that is easier
to delete or replace later.
