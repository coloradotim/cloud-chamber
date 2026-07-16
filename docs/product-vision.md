# Cloud Chamber Product Vision

## Product Name

**Cloud Chamber**

## North Star

Cloud Chamber is a **cloud-making sandbox that uses real atmospheres as raw
material**.

The organizing question is:

> Given the soundings available, which ones can make interesting clouds, what
> setup should I use, and how far do I need to push them?

Short version:

> Find a promising atmosphere, choose an honest cloud recipe, run CM1, and watch
> something interesting evolve.

Cloud Chamber should help produce and understand:

1. growing cumulus and congestus;
2. deep convective towers;
3. precipitation and reflectivity;
4. useful suppression/cap cases when cloud growth is not a good bet.

CM1 is the high-fidelity simulation engine. Cloud Chamber owns opportunity
finding, recipe and run-setup recommendations, local execution, result
organization, interpretation, and visualization.

The product is not a forecast or warning service. It is for personal cloud
exploration, learning, and visual experimentation.

## Core Product Promise

Cloud Chamber should answer:

```text
What are the coolest cloud-making opportunities in the sounding history I have?
What can we do with this specific atmosphere?
Which recipe and run setup should I use?
Is this scout worth continuing?
```

The product should not require the user to be an expert sounding analyst before
receiving a useful recommendation.

## What Cloud Chamber Is

Cloud Chamber is:

- a local-first CM1 cloud workbench;
- an opinionated sounding–recipe opportunity finder;
- a recipe and run-setup recommender;
- a visible scout-to-full-run workflow;
- a run manager with progress, ETA, stop, ingest, and cleanup;
- a notebook of completed cloud runs;
- a visual environment for watching cloud evolution;
- a place to ask “what happened here?” after an interesting run.

## What Cloud Chamber Is Not

Cloud Chamber is not:

- a replacement for CM1;
- a weather forecast site;
- an operational warning tool;
- a publication or peer-review workflow;
- a generic namelist editor;
- a browser-based model solver;
- a system that treats idealized initiation as dishonest;
- a diagnostics project whose main output is more diagnostics.

## Primary Workflow

```text
Find promising sounding–recipe pairs
→ Recommend a concrete run setup
→ Queue a meaningful scout through Build
→ Automatically promote a promising scout to a full run
→ Explore the evolving cloud
```

### Find

Support two entry modes:

1. **Show me something cool** — rank the best cloud-making opportunities across
   a selectable recent or historical sounding scope.
2. **Find / inspect** — search by date range, region, cloud target, saved
   candidate, or specific sounding.

The ranked object is:

```text
sounding + recipe + run setup
```

A sounding may be boring under free evolution and excellent under explicit
initiation. Rank the useful combination, not the sounding in isolation.

### Recommend

For each opportunity, show:

- target visible outcome;
- opportunity score;
- likely cloud ceiling;
- main obstacle;
- recommended recipe;
- recommended scout setup;
- why free evolution may be a poor choice;
- stronger alternative;
- skip recommendation where appropriate.

The product should be comfortable saying:

```text
Natural evolution is likely boring.
Best bet: Deep-Tower Benchmark.
```

or:

```text
Skip this sounding for cloud-making.
Use it only if you want to study suppression.
```

### Scout

A scout is a real CM1 run large and long enough to answer whether the opportunity
deserves more compute. It is recipe-specific; “scout” does not mean
meteorologically useless.

The scout should resolve to one decision:

```text
continue automatically
scale one run-shape parameter
change one recipe parameter
switch recipe
skip sounding
stop broken run
```

### Full Run

A promising scout may automatically queue or continue a full run through the
existing Build workflow.

The promotion must be visible and reversible. Show:

- promotion reason;
- model duration;
- progress and ETA;
- stop/cancel control;
- cleanup behavior;
- relationship to the scout.

### Explore

Explore is the visual payoff. It should make it easy to:

- replay cloud growth;
- inspect cloud water, ice, vertical velocity, rain, and reflectivity;
- understand why a cloud grew, stalled, precipitated, or collapsed;
- inspect technical evidence on demand;
- eventually make the cloud presentation beautiful.

Diagnostics support the visible story; they are not the primary experience.

## Analyzer Role

The sounding analyzer should estimate two separate dimensions:

1. **Growth ceiling** — what cloud the atmosphere may sustain once useful ascent
   exists.
2. **Initiation difficulty** — how much help the selected CM1 setup probably
   needs to create that ascent.

It should rank separately for:

- growing cumulus/congestus;
- deep tower after initiation;
- precipitation;
- suppression/cap-learning value;
- likely boring/skip.

Useful inputs may include CAPE/CIN/LFC/EL where reliable, moisture depth, LCL,
lapse rates, cap structure, midlevel humidity, precipitable water, freezing
level, profile quality, wind completeness, recipe compatibility, and package
readiness.

Missing diagnostics should reduce confidence, not silently become negative
atmospheric evidence.

## Cloud Recipes

A **recipe** is an honestly labeled way to help a real atmosphere produce or
reveal a cloud outcome. A **run setup** is the domain, grid, duration, cadence,
numerical settings, forcing strength, and other concrete CM1 configuration used
to execute the recipe.

The initial recipe catalog is:

### 1. Daytime Evolution

Simplified normal heated-day evolution using active place/time forcing where
supported. Intended for boundary-layer growth, growing cumulus, and congestus.

### 2. Broad Warm/Moist Surface Region

A broad idealized lower-boundary heating/moistening region intended to organize
boundary-layer ascent and growing clouds.

### 3. Explicit Thermal Initiation

A clearly labeled supplied thermal or warm-bubble setup intended to test what an
atmosphere can sustain when initiation is provided.

### 4. Deep-Tower Benchmark

A stronger controlled trigger intended to reveal the sounding's convective
ceiling. Restore and modernize the proven Deep Convection Trial from PR #270.

### 5. Suppression / Cap Challenge

A controlled ladder of heating, moistening, or initiation intended to show what
is required to break through a cap—or when current supported recipes cannot.

These are starting tools, not rigid product families and never “the experiment.”
The catalog should grow from useful cloud-making questions.

## Recipe Contract

Every recipe must define:

- target visible outcome and learning question;
- suitable sounding traits;
- poor/skip traits;
- exact added assumptions;
- meaningful scout setup;
- full-run setup;
- supported aggressiveness levels;
- checkpoint timing;
- automatic-promotion criteria;
- escalation order;
- stop/switch criteria;
- expected visible outcomes;
- limitations and user-facing label.

A mechanism implementation without this operating contract is incomplete.

## Scientific Honesty

Scientific honesty means:

- distinguish recommendation from CM1 result;
- show which mechanisms and assumptions were added;
- preserve enough configuration/provenance to reproduce the run;
- fail clearly when a requested mechanism did not execute;
- expose broken or non-finite output;
- do not use forecast language;
- do not imply an idealized trigger represents an observed real-world boundary.

Scientific honesty does **not** require weak forcing, untriggered evolution, tiny
runs, or publication-style validation before exploratory use.

Use two normal modes:

### Exploratory

Bold labeled assumptions. Optimize for learning and visible cloud outcome.

### Compared

Compare two or a few runs when an actual result creates a useful question.

Heavy trust/diagnostic work is reserved for broken, suspicious, or
configuration-inconsistent output.

## Product Workspaces

### Build

Build owns:

- cloud-opportunity discovery;
- sounding and recipe recommendations;
- concrete run setup;
- scout and full-run plan;
- package generation;
- local/LAN execution where supported;
- queue, progress, ETA, stop, ingest, and cleanup.

### Results

Results is the notebook of ingested cloud runs. It should emphasize what cloud
formed and make useful runs easy to name, tag, revisit, and relate to their scout
and recipe.

### Explore

Explore is the synchronized visual and explanatory view of one result. It should
prioritize cloud evolution and keep technical detail available without making it
the main event.

## Run Latency

CM1 execution is not an instant slider. Cloud Chamber should make latency useful:

- recommend a setup worth the time;
- show ETA;
- checkpoint meaningful scouts;
- stop poor bets;
- automatically continue promising clouds;
- let the user leave and return later.

## Product Language

Use:

- cloud opportunity;
- recipe;
- run setup;
- scout;
- growing cumulus;
- congestus;
- deep tower;
- daytime evolution;
- explicit initiation supplied;
- broad warm/moist region;
- likely ceiling;
- main obstacle;
- continue / switch / skip;
- What happened here?

Raw CM1 variables and namelist values belong in technical views.

## Trust Distinctions

Always distinguish:

```text
Analyzer/recommendation estimate
Generated CM1 configuration
Packaged run
Queued/running CM1 process
Completed CM1 result
Ingested result metadata
Visualization interpretation
```

Never imply that a recommendation is CM1 output or that a package is a completed
cloud result.

## Current Golden Path

The current hero workflow is no longer Baseline Shallow Cumulus.

The new Golden Path is:

```text
Show me something cool
→ receive a ranked sounding–recipe opportunity
→ queue the recommended scout
→ watch it earn or fail promotion
→ open a visibly interesting cloud result in Explore
```

Baseline Shallow Cumulus remains a useful reference and learning case. It is not
the product's aspirational ceiling.

## Success Criteria

Cloud Chamber succeeds when a user can:

1. search a useful sounding-history scope;
2. see ranked cloud-making opportunities;
3. understand why a recipe is recommended;
4. avoid a likely boring sounding/setup;
5. queue a meaningful scout through Build;
6. see progress and ETA;
7. let a promising scout visibly promote to a full run;
8. stop or clean up when desired;
9. ingest and open the result;
10. watch growing or deep cloud evolution in Explore;
11. learn which assumptions or atmospheric limits shaped the result.

Within a small set of scouts, the product should produce an interesting cloud or
save substantial compute with a decisive switch/skip recommendation.

## Current Strategic Sources

- [Cloud-First Product Reset](cloud-first-product-reset.md)
- [Current Roadmap](current-roadmap.md)
- [Architecture and Data Model](architecture-and-data-model.md)
- [Product Spec](cloud-chamber-product-spec.md)
