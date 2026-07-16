# Cloud-First Product Reset

Status: approved product direction

## Organizing Principle

Cloud Chamber is a **cloud-making sandbox that uses real atmospheres as raw material**.

The central product question is:

> Given the soundings available, which ones can make interesting clouds, what
> setup should I use, and how far do I need to push them?

The first visible outcomes to optimize for are:

1. growing cumulus and congestus;
2. deep convective towers;
3. precipitation and reflectivity.

Organized convection is not a current product priority. Cloud Chamber is not a
forecast or warning product, and it is not trying to reproduce a publication
workflow.

## Why This Reset Is Necessary

Cloud Chamber accumulated useful infrastructure, but the work drifted away from
its experiential goal. Several reinforcing biases caused that drift:

1. **The product ranked soundings, not useful things to do with them.**
   A sounding can be poor for free evolution and excellent with explicit
   initiation. A generic story label does not answer whether a run is worth the
   time.

2. **Natural or weak forcing became the implied scientific default.**
   Real cloud initiation often depends on sunlight, boundary-layer evolution,
   terrain, boundaries, convergence, or other heterogeneity. A horizontally
   homogeneous untriggered CM1 domain should not be treated as the moral baseline
   for every atmosphere.

3. **Scientific honesty was confused with weak assumptions.**
   Honesty means naming the assumption. It does not mean always selecting the
   smallest domain, weakest forcing, shortest run, or least effective trigger.

4. **Issues rewarded narrow plumbing slices.**
   Package provenance, validation, trust gates, and diagnostics became the
   deliverables instead of supporting a visible atmospheric outcome.

5. **Diagnostics were added without a decision burden.**
   A diagnostic is valuable when it changes continue/change/stop behavior or
   reveals broken output. It is not automatically valuable because it can be
   computed.

6. **Working cloud-making capability was removed during a conservative reset.**
   PR #270 proved that the Deep Convection Trial could produce a strong tower
   from a real Fort Worth sounding using stock CM1 `iinit = 3`. Later planning
   demoted that evidence while prioritizing untriggered evolution.

7. **Agent rules rewarded fragmentation and permission-seeking.**
   One-issue-per-branch, strict issue scope, mandatory questions, automatic
   follow-up issue creation, and pausing before every real CM1 change made sense
   as generic safeguards but became harmful defaults for exploratory cloud work.

## Product Model

The primary ranked object is:

```text
sounding + recipe + run setup
```

The analyzer should not only say that a sounding contains ingredients. It should
say what Cloud Chamber can plausibly do with that atmosphere.

Example:

```text
Best opportunity: Growing tower
Sounding: Norman / Max Westheimer, 00Z
Recommended recipe: Broad warm/moist surface region
Why: Good moisture and growth potential; spontaneous initiation looks weak
Expected visible result: Growing cumulus to congestus
Natural free evolution: Likely shallow or delayed
Stronger alternative: Explicit thermal initiation
Run setup: 12.8 km, 100 m grid, 4 h scout, 5 min output
```

Cloud Chamber should also say:

```text
Skip this sounding for cloud-making.
Strong cap and dry low levels make all current supported recipes poor bets.
Use it only if you want to explore suppression.
```

## Entry Modes

Support both entry modes without forcing the user to know meteorology first.

### Show Me Something Cool

This is the primary default entry point.

Cloud Chamber searches the available cached history—not only today—and returns
ranked sounding–recipe–run-setup opportunities. The user may select time range,
region, cloud target, or compute appetite, but useful defaults should work without
those choices.

### Find / Inspect

Support queries such as:

```text
What can we do with this sounding?
Show me deep-tower opportunities from the last month.
Find growing-cumulus opportunities in my whole cache.
Which saved atmosphere is worth revisiting?
```

The user may not visit Cloud Chamber every day. Historical and selectable-range
search is first-class.

## Workflow

```text
Find promising sounding–recipe pairs
→ Recommend a concrete run setup
→ Queue a meaningful scout through Build
→ Automatically promote a promising scout to a full run
→ Explore the evolving cloud
```

### Find

Search and rank cloud opportunities. Do not dump a station list and ask the user
to interpret it.

### Recommend

Give one best bet, a clear reason, an expected visible outcome, a run setup, and
one stronger alternative. Recommend against free evolution when it is likely to
waste time.

### Scout

Run real CM1 with a recipe-specific setup large and long enough to answer whether
the opportunity deserves more compute. A scout is not automatically tiny or
short.

### Full Run

When a scout earns continuation, queue or continue the full run visibly through
the existing Build workflow. The user sees duration, progress, ETA, and the
promotion reason, and can stop or clean it up.

### Explore

The payoff is watching and understanding cloud evolution. Diagnostics support
the visual story; they are not the product center.

## Cloud Opportunity Contract

A useful recommendation payload should include:

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
  assumptions:
  caveats:
```

The opportunity score is a product recommendation, not a forecast probability.
It should improve as real CM1 outcomes accumulate, but it does not need
publication-style validation before becoming useful.

## Sounding Selection

The analyzer should estimate two separate things:

1. **Growth ceiling** — what the atmosphere may sustain once a useful updraft
   exists.
2. **Initiation difficulty** — how much help is likely needed to create that
   updraft in the selected CM1 setup.

Those two axes are more actionable than one generic severe/shallow score.

### Useful Ingredients

Where the profile supports reliable calculation, consider:

- low-level moisture and depth;
- LCL and cloud-base accessibility;
- CAPE, CIN, LFC, and EL for relevant parcel choices;
- cap strength, depth, and height;
- low- and mid-level lapse rates;
- midlevel relative humidity and dry-air entrainment risk;
- precipitable water;
- freezing-level and mixed-phase depth;
- sounding vertical completeness and surface representativeness;
- observed wind completeness where the run recipe requires it;
- known recipe compatibility and package readiness.

Do not make missing advanced diagnostics silently equivalent to a poor
atmosphere. Preserve missing-data confidence separately.

### Target-Specific Ranking

Rank separately for:

- growing cumulus/congestus;
- deep-tower potential after initiation;
- precipitation potential;
- suppression/cap-learning value;
- likely boring/skip.

### Skip Logic

Cloud Chamber should recommend skipping a cloud-making run when the current
recipe catalog offers no plausible useful outcome for the requested target.
Examples include very dry low levels, overwhelming inhibition, inadequate
profile quality, or a model/run shape that cannot represent the target.

A skip recommendation saves compute and user attention. It is a success, not a
failure.

## Initial Recipe Catalog

These recipes are starting tools, not the final catalog and not separate product
centers.

### 1. Daytime Evolution

Question:

> What might this atmosphere do during an ordinary heated daytime evolution
> under Cloud Chamber's explicitly simplified assumptions?

Suitable for boundary-layer growth, growing cumulus, and congestus opportunities.
Use active place/time forcing where supported. If a simplified diurnal proxy is
used, label it clearly. Do not call constant domain-wide flux a real daytime
cycle.

### 2. Broad Warm/Moist Surface Region

Question:

> Can a broad heated or moistened lower-boundary region organize enough ascent to
> grow visible clouds?

This should build on the completed differential-forcing mechanism but use scales
chosen for cloud growth, not merely a 1.5 km plumbing footprint.

### 3. Explicit Thermal Initiation

Question:

> If Cloud Chamber supplies a rising thermal, what kind of cloud can this
> atmosphere sustain?

This is normal exploratory behavior. The UI label supplies the honesty.

### 4. Deep-Tower Benchmark

Question:

> With strong explicit initiation, what is this atmosphere's convective ceiling?

Restore and modernize the proven Deep Convection Trial from PR #270. This is the
most direct initial path to reliably producing deep, visually interesting cloud
results.

### 5. Suppression / Cap Challenge

Question:

> How much heating, moistening, or initiation is needed before this atmosphere
> produces a cloud or breaks through its cap?

This recipe turns otherwise poor cloud candidates into useful learning cases.

## Recipe Operating Contract

Every recipe must define:

- visible target and learning question;
- suitable sounding traits;
- poor/skip traits;
- exact added mechanism and assumptions;
- scout run setup;
- full-run setup;
- default and stronger supported levels;
- checkpoint timing;
- promotion criteria;
- escalation order;
- stop/switch criteria;
- expected visible outcomes;
- limitations and honest user label.

A recipe name without this operating contract is not complete.

## Initial Run-Shape Hypotheses

These are starting hypotheses for real CM1 testing, not frozen validated presets.
The implementation should change them when actual cloud results justify it.

| Target / recipe | Meaningful scout starting point | Full-run direction |
| --- | --- | --- |
| Growing cumulus / Daytime Evolution | 12.8 km domain, ~100 m horizontal spacing, tall current vertical grid, 3–4 simulated hours, 5–10 min output | Continue to 6–8 h when cloud water and coherent top are growing |
| Growing cumulus / Broad warm-moist region | 12.8–25.6 km domain, 100–200 m spacing, 2.5–3 km core region plus taper, 3–4 h | Broaden toward 3–5 km or extend duration before making a tiny patch dramatically hotter |
| Explicit thermal | Use a supported stock-CM1 initiation setup, 20+ km cloud-resolving domain where practical, tall model top, early dense output | Continue or refine when the initiated cloud grows coherently |
| Deep-tower benchmark | First restore the proven PR #270 configuration and Fort Worth case; then test a higher-resolution cloud-focused run shape | Refine horizontal/vertical detail and output cadence after the deep path works in current Build |
| Suppression / cap challenge | Recipe-specific heating/trigger ladder with explicit levels and early checkpoints | Continue only when one level produces meaningful ascent or cloud growth |

Raw timestep is an advanced numerical assumption. Use the safer supported value
for the selected run shape and preserve it in provenance.

## Scout Checkpoints And Decisions

Checkpoints are recipe-specific.

### Daytime Evolution

Typical decision windows: roughly 90 minutes, 3 hours, then full-day continuation.

Continue when the boundary layer responds and coherent cloud water begins to
appear or grow. Switch recipe or skip when forcing is active but the atmosphere
remains strongly capped/dry with no useful trend.

### Broad Warm/Moist Region

Typical decision windows: 60, 120, and 180 minutes.

Continue when the forced region produces meaningful sustained ascent and growing
cloud water. Broaden the region before blindly escalating amplitude. Switch to
explicit initiation when growth potential looks good but initiation remains weak.

### Explicit Thermal / Deep-Tower Benchmark

Typical decision windows: 15, 30, 60, and 90 minutes.

Continue when the trigger is applied, updraft strengthens, coherent cloud grows,
and mixed-phase/precipitation evidence begins where expected. Change sounding or
run shape promptly if the trigger works but the atmosphere cannot sustain a
useful cloud.

### Decision Set

Every scout should resolve to one visible action:

```text
continue automatically to full run
scale up one run-shape parameter
change one recipe parameter
switch recipe
skip this sounding
stop because the run is broken or suspicious
```

## Automatic Promotion

Automatic scout-to-full-run promotion is allowed and expected when a recipe's
criteria are met.

Promotion must:

- appear in the existing Build run plan and queue;
- show configured model duration, progress, and ETA;
- preserve the scout relationship and promotion reason;
- allow stop/cancel and cleanup;
- avoid hidden or unbounded batches;
- use a trustworthy restart/checkpoint when supported, otherwise create a related
  full-run package.

## Evidence Modes

Use two normal modes:

### Exploratory

Bold, labeled assumptions. Optimize for visible outcome and learning. Preserve
enough configuration and provenance to reproduce the run.

### Compared

Compare two or a few runs when a result creates a useful question. Matching is a
tool, not a universal prerequisite.

### Broken Or Suspicious

Heavy trust and diagnostic work belongs here: non-finite output, missing requested
mechanism, numerical instability, missing fields needed for the decision, or a
result that contradicts its configured setup.

There is no separate publication-style "validated claim" workflow in the current
product model.

## Diagnostic Burden

Before adding a diagnostic, state which decision it changes:

```text
continue
scale
change recipe parameter
switch recipe
skip sounding
stop broken run
```

If it changes none of those decisions, do not make it the next task.

When a run is simply boring, first consider changing the sounding, recipe,
scale, duration, or trigger. Do not automatically add more diagnostics.

## UX Direction

The primary Build experience should be able to say:

```text
Here are the best cloud-making opportunities in your available sounding history.
This one is the best bet for a growing tower.
Use this recipe and run setup.
Natural evolution is likely boring; explicit initiation is recommended.
```

The user should not need to read a sounding diagram expertly before receiving a
useful recommendation.

Build owns the scout/full-run queue, ETA, stop, and cleanup workflow. Results owns
the notebook entry. Explore should make cloud evolution visually rewarding and
technically inspectable without burying the user under diagnostics.

## Agent Operating Rules

For cloud-making work:

- optimize visible cloud outcome and information gained per unit of user time;
- take bounded big swings;
- run meaningful CM1 early;
- allow strong idealized assumptions when clearly labeled;
- do not create prerequisite issues unless genuinely blocked;
- do not let old roadmap sequencing override current user intent;
- keep one outcome-oriented vertical slice together when code, UI, run setup, and
  real execution are all required;
- change sounding, recipe, scale, duration, or trigger before adding diagnostics
  to a merely boring run;
- compare second, not first;
- keep generated model artifacts outside git.

## Stop Doing

- Stop treating free evolution as the default test of every sounding.
- Stop treating Baseline Shallow Cumulus as the product hero outcome.
- Stop creating a validation issue before every useful real run.
- Stop requiring formal campaign comparison before shipping a recipe.
- Stop adding diagnostics without a concrete next-run decision.
- Stop ranking soundings without recommending a recipe and run setup.
- Stop discarding working trigger paths because they are idealized.
- Stop optimizing issue closure over cloud-making progress.

## Immediate Repo Direction

1. **#346:** build cloud-opportunity ranking and the visible scout-to-full-run
   workflow.
2. **#341:** restore the proven explicit thermal/deep-tower path from PR #270.
3. **#287:** implement a real daytime-evolution recipe using active place/time
   forcing or an honestly labeled evolving proxy.
4. Treat the completed differential surface-forcing work as one available recipe
   mechanism, not a roadmap center.
5. Improve visual cloud presentation after current Build can reliably produce or
   recommend interesting cloud runs.
6. Create small comparisons only when actual results make the comparison useful.

## Success Measure

Within a small number of real scouts, Cloud Chamber should either:

- produce a clearly growing, visually interesting cloud worth continuing;
- produce a deep tower or precipitation-bearing result;
- or save the user substantial compute by making a decisive skip/switch
  recommendation before a long boring run.

Infrastructure is successful only when it improves one of those outcomes.
