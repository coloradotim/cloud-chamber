# AGENTS.md - Cloud Chamber

## Project Identity

Cloud Chamber is a local-first **cloud-making sandbox that uses real atmospheres
as raw material**.

The organizing product question is:

> Given the soundings available, which ones can make interesting clouds, what
> setup should I use, and how far do I need to push them?

CM1 is the high-fidelity simulation engine. Cloud Chamber is the opportunity
finder, recipe and run-setup recommender, local run manager, result notebook,
diagnostics layer, and visualizer around CM1.

The immediate visible priorities are growing cumulus/congestus, deep convective
towers, and then precipitation. Cloud Chamber is not a forecast or warning
product.

## Product Rule

CM1 is the source of truth for cloud evolution. The app should not pretend to be
CM1.

Reduced/light models and analyzer scores may be used for:

- opportunity ranking;
- recipe and run-setup recommendations;
- preview and explanation;
- scout continuation decisions;
- rough guidance and sanity checks.

They are decision aids, not simulated cloud output.

## Cloud-Making Operating Mode

This mode applies when the user or issue asks to find promising soundings, make
interesting clouds, build a cloud recipe, run a scout, continue a promising run,
or improve the cloud-making workflow. Issue #346 and its related recipe work are
explicitly in this mode.

Cloud-Making Mode overrides generic conservative defaults that would otherwise
fragment or delay the outcome.

### Outcome Priority

Optimize for:

```text
visible cloud outcome + useful learning per unit of user time and compute
```

A useful result may be:

- growing cumulus or congestus;
- a deep tower;
- precipitation or reflectivity;
- a decisive recommendation to switch recipe or skip a poor sounding;
- evidence that a run is actually broken or numerically suspicious.

Package plumbing, provenance, diagnostics, and docs support those outcomes. They
are not the outcome themselves.

### Bounded Big Swings

- Strong idealized assumptions are allowed when clearly labeled.
- Scientific honesty means naming the added mechanism and limitations; it does
  not mean always choosing the weakest forcing, smallest domain, shortest run,
  or least effective trigger.
- Prefer a meaningful three-run scout or one bold vertical slice over a chain of
  prerequisite issues.
- Run real CM1 early enough to influence the implementation.
- If a run is merely boring, change the sounding, recipe, scale, duration, or
  trigger before adding diagnostics.
- Restore or reuse working cloud-making paths from repository history instead of
  rebuilding them from scratch because later docs became more conservative.

### Scout And Full Run

Scouts must be meaningful for the recipe. When a scout meets explicit promotion
criteria, it may visibly and automatically queue or continue a full run through
the existing Build workflow.

The user must be able to see:

- the promoted run;
- the reason for promotion;
- configured duration;
- progress and ETA;
- stop/cancel and cleanup controls.

Do not launch hidden or unbounded batches.

### Diagnostic Burden

Before adding a diagnostic, identify which decision it changes:

```text
continue
scale up
change one recipe parameter
switch recipe
skip sounding
stop broken run
```

If it changes none of those decisions, do not make it the next task.

Heavy trust and diagnostic work is appropriate when output is non-finite,
numerically suspicious, missing the requested mechanism, missing evidence needed
for the decision, or inconsistent with its configuration. It is not required
merely because the result is shallow, surprising, or exploratory.

### Issue Scope In Cloud-Making Mode

Scope work to one **user outcome**, not one tiny implementation layer. A vertical
slice may legitimately include analyzer logic, recipe configuration, Build UI,
queue behavior, result copy, tests, docs, and a real CM1 scout when all are
needed to produce the outcome.

Do not create prerequisite or follow-up issues automatically. Create one only
when the current work is genuinely blocked or the discovered work is an
independent product decision. Do not use issue creation as a substitute for
finishing the current outcome.

Comparison is secondary. Compare two or a few runs when an actual cloud result
creates a useful question; do not require formal matched campaigns before making
interesting clouds.

## Durable Distinction

Always distinguish:

```text
Analyzer/recommendation estimate
CM1 run configuration
Packaged run
Queued/running CM1 process
Completed/ingested CM1 result
Visualization interpretation
```

## Guardrails

Do not commit:

- CM1 source;
- CM1 binaries;
- NetCDF output;
- generated run directories;
- `LANDUSE.TBL`;
- local data;
- machine-private settings or paths;
- large processed visualization artifacts.

Do commit:

- code;
- tests;
- docs;
- schemas;
- recipe definitions;
- tiny fixtures.

## Development Expectations

- Use GitHub issues and PRs.
- Work on branches; do not push directly to `main`.
- Keep work scoped to the issue's user outcome.
- Add tests for new behavior.
- Update docs when architecture, workflow, recipe behavior, or product direction
  changes.
- Use local fake fixtures in CI; do not require real CM1 in automated tests.
- Run real CM1 outside CI when the issue explicitly requires cloud-making or
  runtime validation.
- Do not weaken scientific honesty, but do not confuse honesty with weak
  experiments.
- Enable auto-merge after required CI checks pass unless the user asks for
  manual review or the change is destructive/high-risk.
- Destructive cleanup, generated-data policy changes, unbounded compute, and
  backwards-incompatible data changes are high-risk.
- Real CM1 execution is not an automatic stop condition when the user or issue
  has explicitly authorized a bounded scout or cloud-making run.

## Initial Architecture Bias

Prefer:

```text
React/Vite frontend + Python FastAPI local backend
```

until a stronger reason appears.

## Local CM1 Runtime

CM1 remains external to the repo.

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

## Product Language

Use cloud and atmosphere language first:

- cloud opportunity;
- recipe;
- run setup;
- growing cumulus;
- congestus;
- deep tower;
- daytime evolution;
- explicit thermal initiation;
- broad warm/moist region;
- suppression / cap challenge;
- likely ceiling;
- main obstacle;
- scout;
- continue / switch / skip;
- cloud base and coherent cloud top;
- updraft strength;
- cloud water and ice;
- rain onset and reflectivity;
- What happened here?

Raw namelist settings and raw CM1 variable names belong in technical, advanced,
or developer views.

Do not use forecast or warning language. Do not imply that an idealized trigger
represents a real front, dryline, terrain feature, or observed initiating
mechanism.

## Testing Notes

Use fake/small fixtures to test:

- recommendation and recipe contracts;
- scenario/run schemas;
- config generation;
- run manifest creation;
- scout/full-run relationship;
- fake process execution;
- NetCDF ingestion from tiny fixtures;
- visualizer metadata loading.

Do not require full CM1 runs in CI. Real cloud-making evidence belongs in local
manual/runtime verification and the PR description or approved research note,
not in git as generated model output.

## Before Major Changes

Ask before changing product direction **outside** the approved cloud-first reset.
The direction in `docs/cloud-first-product-reset.md` and #346 is already approved.
Do not repeatedly ask for confirmation to implement it.

When adding a physical mechanism or recipe, document:

1. the cloud outcome or learning question;
2. the added assumption or mechanism;
3. the useful user control or supported aggressiveness level;
4. the meaningful scout and full-run setup;
5. the continue/change/stop decision evidence;
6. the limitations that must be visible.

---

## Coding Agent Working Style

This section governs Codex, Claude Code, and similar coding agents.

### Intent First, Without Stalling

For a non-trivial task:

1. State the user outcome you understand.
2. Identify only material unresolved decisions.
3. Make reasonable bounded assumptions for everything else.
4. Propose the execution direction briefly and proceed when the issue/user intent
   is already clear.

Do not ask every conceivable question. Do not require another go-ahead when the
user has already approved the product direction or the issue has explicit
acceptance criteria.

A clarification is appropriate when different answers would materially change
the product outcome, delete user data, create unbounded compute, or make the
requested work unsafe. It is not appropriate merely because implementation has
multiple reasonable choices.

### Autonomy

Once intent is clear, execute as fully as possible:

- write the code;
- add or update tests;
- run meaningful local CM1 scouts when in scope;
- inspect the outcome and adjust the implementation or run setup;
- run `scripts/check.sh` and fix failures;
- update relevant docs;
- open a PR with clear verification and real-run evidence when applicable.

Do not ask permission to run tests, lint, type checks, Playwright, or bounded CM1
scouts that the issue explicitly requests.

Do not automatically open issues for every bug, missing test, doc gap, or idea.
Fix it in the current outcome when reasonably related. Open a separate issue only
for a real blocker or independent product decision.

### Branching And PRs

- Branch from current `main`.
- Name branches `issue-NNN-short-description`.
- One user outcome per branch. A cloud-making vertical slice may span multiple
  technical layers.
- Keep unrelated opportunistic cleanup out of the PR.
- PR descriptions must include:
  - the user outcome;
  - what changed and why;
  - how to verify it locally;
  - real CM1 runs and visible outcomes when cloud-making is in scope;
  - known limitations that affect the next decision.
- Enable auto-merge after CI unless the task is destructive/high-risk or the user
  asks for manual review.

### Commit Style

- Conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`.
- Subject line: imperative, at most 72 characters.
- Body: include the issue number and why the change matters.
- Keep commits logically coherent. Do not split a vertical slice into artificial
  commits merely to appear small.

### Quality Bar

Every PR must pass `scripts/check.sh` before merge:

- Frontend: lint, test, build.
- Backend: ruff format, ruff check, mypy, pytest.
- No unexplained new warnings.

New behavior requires tests. UI changes that affect user-visible workflow must
update the relevant docs.

Tests and type safety support iteration; they must not become a reason to avoid a
meaningful real run.

### GitHub Issues

When opening an issue:

- use the correct labels;
- write it around a user-visible outcome or concrete bug;
- include enough context for future work;
- avoid turning implementation layers into separate roadmap items;
- use `priority:p1` for core-workflow blockers and approved immediate product
  work; `priority:p2` otherwise.

### What Agents Must Ask Before Doing

Always ask before:

- deleting or overwriting user-owned runtime data beyond an explicit cleanup
  request;
- launching an unbounded or unexpectedly expensive batch;
- changing product direction outside the approved cloud-first model;
- making backwards-incompatible manifest/result changes without a migration;
- removing or weakening tests rather than fixing the underlying issue.

Do **not** pause merely because work touches:

- real CM1 execution explicitly requested by the issue;
- additive schemas;
- recipe assumptions within the approved catalog;
- recommendation or interpretation copy consistent with the approved product
  model;
- a bounded scout and visible automatic full-run promotion.

### Environment Assumptions

Coding sessions may assume:

- `scripts/dev.sh start` can run the frontend at `localhost:5173` and backend at
  `127.0.0.1:8000`;
- `~/CloudChamber/settings.json` contains local CM1 paths when CM1 work is in
  scope;
- `uv` or the documented pip fallback is available;
- the Playwright E2E suite may live at `~/e2e/`.

### Playwright E2E

For user-visible workflow changes:

- check existing Playwright coverage;
- update or add the smallest useful end-to-end test;
- verify the actual UI when practical;
- never delete or skip tests merely to make CI pass.

### Documentation Standard

- `docs/cloud-first-product-reset.md` is the current organizing product decision.
- `docs/current-roadmap.md` is the active priority source.
- `docs/product-vision.md` describes the durable product model.
- `docs/development.md` is the canonical dev setup.
- `docs/architecture-and-data-model.md` must reflect schema/API changes.
- Inline comments explain why, not what.

### Maintainability Bias

Prefer:

- explicit over clever;
- small, testable functions over tangled ones;
- types in TypeScript and Python;
- clear errors that name the problem and suggest a fix;
- fail loudly on bad state rather than silently degrade.

Maintainability serves cloud-making iteration. When two designs are roughly
equivalent, choose the one that is easier to change after real CM1 evidence.
