# Cloud Chamber Product Spec

Status: current cloud-first product contract

## Product Summary

Cloud Chamber is a local-first **cloud-making sandbox that uses real atmospheres
as raw material**.

The central question is:

> Given the soundings available, which ones can make interesting clouds, what
> setup should I use, and how far do I need to push them?

CM1 is the high-fidelity model. Cloud Chamber owns:

- sounding and cloud-opportunity discovery;
- recipe and run-setup recommendations;
- local CM1 package/run management;
- scout and full-run orchestration;
- result ingest and notebook organization;
- visual exploration and explanation.

Cloud Chamber is for personal learning, cloud experimentation, and visual
exploration. It is not a forecast, warning, or publication workflow.

## Product Goals

The first visible outcome priorities are:

1. growing cumulus and congestus;
2. deep convective towers;
3. precipitation and reflectivity;
4. useful suppression/cap cases when cloud growth is not a good bet.

The product should help the user spend compute on promising atmosphere–recipe
combinations and avoid long runs that are likely to be boring.

## Entry Modes

### Show Me Something Cool

Default discovery mode. Search a selectable recent or historical sounding scope
and rank the best cloud-making opportunities.

“Recent” does not mean only today. The user may return infrequently and should be
able to search a week, month, season, or whole cached history.

### Find / Inspect

Support:

- date/time range;
- region or station set;
- cloud target;
- saved candidate;
- specific sounding;
- “what can we do with this atmosphere?”

## Primary Recommendation Object

Rank:

```text
sounding + recipe + run setup
```

Do not rank a sounding without explaining what Cloud Chamber should do with it.

Suggested contract:

```yaml
cloud_opportunity:
  sounding_id:
  station_id:
  station_name:
  valid_time_utc:
  search_scope:
  cloud_target: growing_cumulus | deep_tower | precipitation | suppression
  recipe_id:
  recipe_label:
  opportunity_score:
  expected_visible_outcome:
  likely_ceiling:
  main_obstacle:
  why_this_pair:
  why_not_free_evolution:
  recommended_run_setup:
  scout_checkpoint_plan:
  automatic_promotion_plan:
  stronger_alternative:
  skip_recommendation:
  confidence:
  assumptions:
  caveats:
```

The score is a recommendation aid, not a forecast probability.

## Analyzer Responsibilities

The sounding analyzer should estimate:

1. **Growth ceiling** — what the atmosphere may sustain once useful ascent
   exists.
2. **Initiation difficulty** — how much help the selected CM1 setup likely needs
   to create that ascent.

Rank separately for:

- growing cumulus/congestus;
- deep tower after initiation;
- precipitation;
- suppression/cap challenge;
- likely boring/skip.

Where methods are supported, useful inputs include:

- low-level moisture and depth;
- LCL and cloud-base accessibility;
- CAPE, CIN, LFC, and EL for relevant parcels;
- cap strength, depth, and height;
- lapse rates;
- midlevel humidity and entrainment risk;
- precipitable water;
- freezing level and mixed-phase depth;
- profile quality and surface representativeness;
- wind completeness when required by a recipe;
- recipe compatibility and package readiness.

Missing advanced diagnostics reduce recommendation confidence. They must not
silently become negative atmospheric evidence.

The analyzer may recommend:

```text
Natural evolution is likely boring.
Use explicit initiation.
```

or:

```text
Skip this sounding for cloud-making.
Use it only for a suppression/cap challenge.
```

## Workflow

```text
Find promising sounding–recipe pairs
→ Recommend a concrete run setup
→ Queue a meaningful scout through Build
→ Automatically promote a promising scout to a full run
→ Ingest
→ Explore the evolving cloud
```

## Build

Build owns all active and incomplete work:

- opportunity search and ranking;
- selected sounding and recipe;
- concrete run setup;
- run plan;
- package generation;
- queue target;
- progress and ETA;
- scout checkpoints;
- visible automatic full-run promotion;
- stop/cancel;
- completed-output ingest;
- cleanup for non-ingested runtime work.

The user should not need to move to another workspace to see or control an
automatically promoted run.

## Results

Results is the notebook of completed and ingested runs.

A result entry should lead with:

- what cloud formed;
- recipe and major added assumptions;
- scout/full-run relationship;
- coherent cloud growth;
- updraft/cloud/rain/reflectivity highlights;
- runtime-integrity or field-quality problems only when relevant;
- notes, tags, and revisitability.

Results owns explicit cleanup of ingested results and their backing local data.

## Explore

Explore is the visual payoff for one selected result.

Core behaviors:

- time replay and scrubbing;
- cloud-water and ice context;
- vertical velocity;
- rain water and surface rain;
- reflectivity;
- slices and selected-region inspection;
- coherent cloud base/top;
- plain-language “what happened here?” explanation;
- technical evidence on demand.

The primary view should make cloud evolution rewarding to watch. Diagnostics
must not crowd out the cloud.

## Recipe Model

A **recipe** is an honestly labeled way to help a real atmosphere produce or
reveal a cloud outcome.

A **run setup** is the concrete domain, grid, vertical top, duration, cadence,
numerical assumptions, forcing, and output configuration used for that recipe.

Recipes are tools. None is “the experiment” or the permanent center of the
product.

## Initial Recipe Catalog

### Daytime Evolution

Question:

> What might this atmosphere do during an ordinary heated daytime evolution
> under explicitly simplified assumptions?

Use active place/time forcing where supported or an honestly labeled evolving
diurnal proxy. Do not relabel constant domain-wide flux as real daytime
evolution.

### Broad Warm/Moist Surface Region

Question:

> Can a broad idealized lower-boundary region organize enough ascent to grow
> visible clouds?

Build on the completed differential surface-forcing mechanism. Choose region
scale for cloud growth, not merely forcing-footprint validation.

### Explicit Thermal Initiation

Question:

> If Cloud Chamber supplies a rising thermal, what kind of cloud can this
> atmosphere sustain?

Explicit initiation is a normal exploratory recipe when clearly labeled.

### Deep-Tower Benchmark

Question:

> With strong explicit initiation, what is the atmosphere's convective ceiling?

Restore and modernize the successful PR #270 Deep Convection Trial using stock
CM1 `iinit = 3` unless current evidence requires a justified equivalent.

### Suppression / Cap Challenge

Question:

> How much heating, moistening, or initiation is needed before this atmosphere
> produces cloud or breaks through its cap?

## Recipe Contract

Every recipe must define:

- target visible outcome and learning question;
- suitable and poor sounding traits;
- skip conditions;
- exact added mechanism and assumptions;
- meaningful scout setup;
- full-run setup;
- supported aggressiveness levels;
- checkpoint times;
- automatic-promotion criteria;
- escalation order;
- stop/switch behavior;
- expected visible outcomes;
- visible limitations.

A mechanism implementation without this operating contract is incomplete.

## Run Setup

Run setup should expose product-level choices first:

- target cloud mode;
- recipe and aggressiveness;
- domain and grid detail;
- model top/vertical shape;
- duration;
- output cadence;
- expected cost and ETA;
- relevant forcing/trigger controls.

Raw namelist and numerical values belong in advanced/technical views. Timestep is
an advanced assumption, not a normal v1 primary control.

Presets are starting hypotheses, not rigid cages. Real CM1 outcomes should change
them.

## Scout Contract

A scout is a real CM1 run large and long enough to decide whether to invest more
compute.

At recipe-specific checkpoints, inspect only decision-changing evidence:

- requested mechanism actually applied;
- runtime integrity not broken;
- boundary layer or trigger responding;
- meaningful updraft developing;
- coherent cloud water appearing and growing;
- cloud capped, dying, or deepening;
- precipitation or reflectivity beginning where relevant.

Every scout resolves to:

```text
continue automatically to full run
scale one run-shape parameter
change one recipe parameter
switch recipe
skip sounding
stop broken run
```

## Automatic Full-Run Promotion

Automatic promotion is allowed when a recipe's criteria are met.

Requirements:

- visible in Build;
- bounded;
- promotion reason preserved;
- duration/progress/ETA shown;
- stoppable and cleanable;
- scout relationship preserved;
- use a trustworthy checkpoint/restart when supported, otherwise create a related
  full-run package.

No hidden background runs or unbounded batches.

## Scientific Honesty

Always distinguish:

```text
Analyzer/recommendation estimate
CM1 run configuration
Packaged run
Queued/running CM1 process
Completed CM1 result
Ingested result metadata
Visualization interpretation
```

Strong idealized assumptions are acceptable when clearly labeled.

Required honesty:

- state what forcing or trigger was added;
- preserve enough configuration/provenance to reproduce the run;
- fail clearly when the requested mechanism did not execute;
- surface non-finite or numerically suspicious output;
- distinguish coherent cloud from sparse hydrometeor trace;
- avoid forecast language;
- do not imply an idealized mechanism represents a specific observed boundary.

Scientific honesty does not require weak forcing, untriggered runs, tiny domains,
or publication-style validation before exploratory use.

## Evidence Modes

### Exploratory

Bold labeled assumptions. Optimize for visible outcome and learning.

### Compared

Compare two or a few runs when an actual result creates a useful question.

### Broken Or Suspicious

Apply heavier diagnostics/trust work when output is non-finite, numerically
unstable, missing a requested mechanism, missing evidence needed for a decision,
or inconsistent with configuration.

There is no current publication-style validated-claim product mode.

## Diagnostic Burden

Before adding a diagnostic, name the decision it changes:

```text
continue
scale
change recipe parameter
switch recipe
skip sounding
stop broken run
```

If it changes none of those decisions, it should not be the next task.

When a run is merely boring, first change sounding, recipe, scale, duration, or
trigger.

## Runtime And Storage

Default runtime home:

```text
~/CloudChamber/
```

Runtime state includes packages, queue state, logs, CM1 outputs, ingested result
metadata, cache, and generated visualization products. These remain outside git.

The browser consumes bounded backend-prepared data and does not parse raw
NetCDF.

CM1 source, binaries, NetCDF output, generated runs, logs, machine-private
settings, and large artifacts must not be committed.

## Failure And Trust States

Process exit zero does not guarantee scientifically usable output. Preserve:

- lifecycle state;
- runtime integrity;
- required field availability;
- field quality where output is non-finite or missing;
- clear failed/canceled/incomplete states.

Do not force every normal exploratory result through extensive trust reporting.
Surface trust information when it affects whether the cloud can be interpreted.

## Current Strategic Work

### #346 — Cloud Opportunities And Scout-To-Full-Run

Primary product lane: ranking sounding–recipe–run-setup opportunities, meaningful
scouts, visible promotion, and at least one interesting cloud or decisive skip.

### #341 — Explicit Thermal / Deep-Tower Recipes

Restore the proven Deep Convection Trial from PR #270 and make deep cloud results
available through the current Build/Results/Explore architecture.

### #287 — Daytime Evolution

Implement active place/time daytime evolution or an honestly labeled evolving
proxy and use a real sounding early.

The completed differential surface-forcing mechanism is one available recipe
tool, not the product center.

## Non-Goals For The Current Horizon

- operational forecasting;
- organized mesoscale-convection products;
- publication-style experiment validation;
- universal raw namelist editing;
- arbitrary GIS/terrain/land-surface realism;
- formal comparison as a prerequisite to exploration;
- diagnostics or provenance as standalone product goals;
- renderer features disconnected from an interesting cloud result.

## Success Criteria

Cloud Chamber should let a user:

1. search a useful sounding history;
2. see the best cloud-making opportunities;
3. understand the recommended recipe and run setup;
4. avoid likely boring soundings/setups;
5. queue a meaningful scout;
6. see progress and ETA;
7. let a promising scout visibly promote to a full run;
8. stop or clean it up;
9. ingest and revisit the result;
10. watch growing or deep cloud evolution;
11. learn which atmosphere and assumptions shaped the result.

Within a small number of scouts, the product should produce an interesting cloud
or save substantial compute with a decisive switch/skip recommendation.

## Strategic Sources

- [Cloud-First Product Reset](cloud-first-product-reset.md)
- [Product Vision](product-vision.md)
- [Current Roadmap](current-roadmap.md)
- [Agent Operating Rules](../AGENTS.md)
- [Architecture And Data Model](architecture-and-data-model.md)
- [Output Product Specification](contracts/output-product-specification.md)
- [Sounding Candidate Screening Contract](contracts/sounding-candidate-screening.md)
