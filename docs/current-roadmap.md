# Current Roadmap

Status: active cloud-first roadmap

This is the current planning source for Cloud Chamber. Historical issue sequencing
and archived roadmaps are evidence only; they do not override the product reset
in [cloud-first-product-reset.md](cloud-first-product-reset.md).

## North Star

Cloud Chamber is a **cloud-making sandbox that uses real atmospheres as raw
material**.

The organizing question is:

> Given the soundings available, which ones can make interesting clouds, what
> setup should I use, and how far do I need to push them?

The current visible outcome priorities are:

1. growing cumulus and congestus;
2. deep convective towers;
3. precipitation and reflectivity.

Cloud Chamber is local-first and CM1 remains the source of truth for cloud
evolution. The product is not operational forecasting and is not a
publication-style validation workflow.

## Current Product Model

### Build

Build should own the full active cloud-making workflow:

- search recent and historical sounding opportunities;
- answer “show me something cool” and “what can we do with this sounding?”;
- rank sounding + recipe + run setup combinations;
- recommend a concrete scout;
- package and queue through the existing run plan;
- show progress and ETA;
- visibly auto-promote a promising scout to a full run;
- allow stop/cancel, ingest, and cleanup.

### Results

Results is the notebook of completed and ingested cloud runs. It should emphasize
what cloud formed, the recipe/setup used, and the relationship between scout and
full run.

### Explore

Explore is the visual payoff: replay and inspect cloud water, ice, vertical
motion, rain, reflectivity, and the evolving cloud story. Technical evidence
belongs on demand, not as the primary experience.

## Hard Product Rules

- CM1 output is the source of truth for cloud evolution.
- Always distinguish recommendation, configuration, packaged run, active process,
  completed result, and visualization interpretation.
- The browser does not parse raw NetCDF.
- Generated CM1 artifacts and machine-private paths do not go in git.
- A scout must be meaningful for its recipe; quick must not mean useless.
- Strong idealized assumptions are allowed when clearly labeled.
- Scientific honesty does not require weak or untriggered setups.
- Natural/free evolution is one recipe, not the default test of every sounding.
- The product may recommend skipping a sounding for a requested cloud target.
- Diagnostics need a concrete continue/change/stop decision.
- Compare runs only when the comparison answers a useful question.
- Real CM1 evidence is part of cloud-making implementation, not a deferred final
  validation ceremony.
- A promising scout may automatically promote through the visible Build queue.
- Automatic work must remain bounded, visible, stoppable, and cleanable.
- Raw timestep remains an advanced numerical assumption, not a normal primary
  control.

## Current State

Cloud Chamber already has substantial infrastructure:

- cached and uploaded IGRA sounding ingestion;
- sounding candidate analysis and saved candidates;
- observed temperature, moisture, and wind profile packaging;
- configurable domain/grid/duration/cadence and surface forcing;
- local queue, LAN-worker support where compatible, progress/status, ingest, and
  cleanup;
- runtime-integrity and field-quality handling;
- Results notebook entries and Explore field products;
- a completed differential surface-forcing recipe mechanism with safe local
  custom-CM1 execution and localized-response diagnostics;
- repository history proving a successful Deep Convection Trial from a real
  sounding using stock CM1 `iinit = 3`.

The main missing product capability is not more generic plumbing. It is an
opinionated layer that turns available atmospheres into useful cloud recipes and
run setups, then follows promising scouts into visible clouds.

## Immediate P1 Work

### #346 — Cloud Opportunities And Scout-To-Full-Run

This is the primary product lane.

Deliver:

- “Show me something cool” across selectable sounding history;
- search by time range, region, target, saved candidate, or specific sounding;
- ranking of sounding + recipe + run setup;
- growth-ceiling and initiation-difficulty reasoning;
- decisive skip recommendations;
- recipe-specific scout setup and checkpoints;
- visible automatic promotion into the existing Build queue;
- at least one interesting cloud result or a decisive compute-saving switch/skip
  outcome during implementation.

This issue is intentionally a vertical slice. Do not split analyzer, UI, queue,
recipe, and real-run work into prerequisite issues unless genuinely blocked.

### #341 — Restore Explicit Thermal / Deep-Tower Recipes

Restore and modernize the proven Deep Convection Trial from PR #270.

Start from working evidence:

- Fort Worth `1997-05-27T00Z`;
- CM1 `iinit = 3` three-warm-bubble initiation;
- strong deep convection with `54.126 m/s` maximum updraft and `64.522 dBZ`.

The first objective is a visibly interesting current-product CM1 result, not a
new trigger diagnostics framework.

Expose a first-class Deep-Tower Benchmark and, where stock CM1 cleanly supports
it, a less aggressive Explicit Thermal recipe or level.

## P2 Recipe Work

### #287 — Daytime Evolution

Implement an actual evolving heated-day recipe using active place/time radiation
where supported, or an explicitly labeled simplified diurnal forcing schedule.

Do not complete this as a validation memo. Run a meaningful atmosphere early and
use it to determine whether normal daytime evolution is a good cloud opportunity
or whether the recommender should switch to explicit initiation.

### Broad Warm/Moist Surface Region

The differential surface mechanism is complete under closed issue #307. Use it
through #346 when the recommender identifies a cloud opportunity.

The next useful scale is likely broader than the 1.5 km footprint smoke. Test
roughly 2.5–3 km before dramatically increasing amplitude, and increase one
run-shape choice at a time when a real result justifies it.

### Suppression / Cap Challenge

Add this as a recommendation/recipe under #346 when the analyzer can identify a
sounding that is valuable specifically for learning how much help is needed to
break through a cap.

Do not create a standalone issue until a real candidate and useful run ladder are
clear.

## Opportunity And Recipe Model

The analyzer/recommender should separate:

- **growth ceiling** — what the atmosphere may sustain after useful ascent exists;
- **initiation difficulty** — how much help the selected CM1 setup probably needs.

Rank separately for:

- growing cumulus/congestus;
- deep tower after initiation;
- precipitation;
- suppression/cap challenge;
- likely boring/skip.

The initial recipe catalog is:

1. Daytime Evolution;
2. Broad Warm/Moist Surface Region;
3. Explicit Thermal Initiation;
4. Deep-Tower Benchmark;
5. Suppression / Cap Challenge.

Each recipe needs an operating contract: suitable soundings, assumptions, scout,
full run, aggressiveness levels, checkpoints, promotion, escalation, stop/switch,
and expected visible outcome.

## Agent Execution Rules

For cloud-making work:

- optimize visible outcome and information per unit time;
- take bounded big swings;
- run meaningful CM1 early;
- allow strong labeled idealizations;
- do not create prerequisite issues unless blocked;
- change sounding, recipe, scale, duration, or trigger before adding diagnostics
  to a merely boring run;
- keep one user outcome together across technical layers;
- compare second;
- keep model artifacts outside git.

`AGENTS.md` defines the full operating rules.

## Recently Retired Roadmap Work

The following issues were closed during the reset because they would keep pulling
the project toward mechanisms, formal comparisons, or old campaign gates:

- **#307** — completed differential surface-forcing mechanism. It is now one
  recipe tool, not the roadmap center.
- **#345** — formal matched initiation campaign. Compare later only when actual
  cloud results create a useful question.
- **#336** — forensic numerical investigation. Use safer supported numerical
  settings and revisit only if a current promising run fails.
- **#275** — generalized predicted-vs-actual verdict system. Recommendation
  calibration is secondary to useful cloud opportunities.

## Stop Doing

- Stop treating Baseline Shallow Cumulus as the hero outcome.
- Stop treating natural free evolution as the default test of a sounding.
- Stop ranking soundings without recommending what to do with them.
- Stop turning every mechanism into the center of the roadmap.
- Stop opening a validation issue before a useful real run.
- Stop requiring formal matched campaigns before shipping a recipe.
- Stop adding diagnostics that do not change a run decision.
- Stop shrinking experiments because their assumptions are idealized.
- Stop optimizing issue closure instead of cloud-making progress.

## Parked / Later

These may become useful after the opportunity and recipe loop works:

- organized/mesoscale convection products;
- terrain, GIS, or real land-surface initialization;
- arbitrary user-drawn forcing maps;
- general result-vs-result comparison surfaces;
- broad export/reporting systems;
- renderer-only feature work disconnected from a useful cloud result;
- remote/HPC orchestration beyond the existing trusted LAN-worker direction;
- publication-style validation or forecast verification.

Visual quality is not parked indefinitely. Once #341/#346 reliably produce an
interesting cloud, appearance and replay improvements that make that cloud lovely
and rewarding to watch should move up immediately.

## Planning Rule

When an issue conflicts with this roadmap, update the roadmap or explicitly state
why the issue should override it.

Do not let archived docs, old issue sequencing, or conservative package history
override the approved cloud-first product direction.

A roadmap item is successful only when it improves one of these outcomes:

```text
interesting cloud produced
promising cloud continued
poor bet skipped
broken run identified
cloud easier to see and understand
```
