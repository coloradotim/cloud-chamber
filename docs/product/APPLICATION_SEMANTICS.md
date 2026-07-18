# Cloud Chamber Application Semantics

**Status:** Approved product-semantic authority

This document defines the foundational product vocabulary for Cloud Chamber.

It exists to keep the product centered on the experience described by the North Star:

> Enter a cloud world, watch a simulation evolve, reveal hidden processes through lenses, change meaningful conditions, compare what happened, and understand the cloud better.

The controlling product authority remains:

1. `NORTH_STAR.md`
2. `docs/product/PRODUCT_VISION.md`
3. explicit approved PM decisions

This document does not select the first cloud world, approve any recipe, define the MVP, choose final schemas, prescribe final application architecture, or establish a roadmap.

## 1. Product-semantic model

Cloud Chamber is organized around cloud worlds, recipes, simulations, lenses, comparisons, exploration, and experiments.

The core relationship is:

```text
Cloud world
  defines a particular cloud setting and experience

Recipe
  provides a complete, known-working, modifiable simulation design
  for creating and exploring a particular kind of cloud in that world;
  it may be explicit, selected by default, or hidden beneath the experience

Simulation
  is one evolving modeled cloud or cloud field produced from a recipe
  and the user's selected changes

Lens
  is a reusable way to reveal a hidden atmospheric process,
  structure, or quantity within a simulation

Saved view
  preserves a specific time, place, angle, and combination of lenses
  so the user can return to it

Comparison
  places two or more simulations or saved views together
  with the meaningful difference made clear

Exploration
  is the ordinary activity of watching, revealing, changing,
  comparing, and following curiosity

Experiment
  is an exploration made deliberate through a specific question
  or controlled comparison
```

Supporting scientific and technical concepts sit beneath this product model:

```text
Atmospheric condition
Control
Atmospheric process
Diagnostic
Observation
Run
Model data
Explanation
```

These supporting concepts are essential, but they do not define the emotional or product center.

## 2. Canonical definitions

### Cloud world

**Type:** Core product concept

A **cloud world** is a defined cloud setting and experience.

It combines:

- a recognizable atmospheric setting;
- the kinds of clouds that form there;
- the processes that make the setting scientifically interesting;
- the meaningful changes a user can make;
- the characteristic visual experience;
- the questions and comparisons that make the world worth exploring.

A cloud world is not one exact atmosphere, one recipe, one sounding, one simulation, one run, or one scientific classification by itself.

A cloud world may be associated with a cloud regime, location type, forcing mechanism, lifecycle transition, or family of related conditions. The product concept is broader than any one of those classifications because it includes both the physical setting and the intended user experience.

Examples may eventually include continental fair-weather cumulus, marine trade cumulus, coastal stratocumulus, deep precipitating convection, or orographic cloud. This document does not approve any of them.

A cloud world is the durable product setting within which multiple recipes, simulations, lenses, comparisons, and experiments may make sense.

### Recipe

**Type:** Core product and curation concept

A **recipe** is a complete, known-working, modifiable simulation design for creating and exploring a particular kind of cloud within a cloud world.

A recipe may include:

- initial atmospheric conditions;
- surface and terrain;
- boundary conditions;
- forcing;
- initiation mechanism;
- radiation;
- turbulence treatment;
- cloud and precipitation physics;
- domain dimensions;
- horizontal and vertical grid;
- time step or time-step strategy;
- simulation duration;
- output cadence;
- numerical controls;
- meaningful user controls;
- useful lenses;
- expected broad cloud behavior;
- practical compute options.

A recipe is not merely a sounding, namelist, scenario template, saved configuration, or preset. It is also not one particular simulation or experiment.

The recipe defines how Cloud Chamber creates a credible and explorable version of part of a cloud world. It may contain lower- and higher-fidelity variants or allow selected changes while preserving the coherence of the setup.

A recipe should be specific rather than defensive. It should explain what it represents, how it works, what the user may meaningfully change, and what broad behavior to expect. Generic warning language is not part of the definition.

A cloud world may support several recipes that differ in atmosphere, forcing, physics, domain, resolution, compute cost, or intended exploration while remaining recognizably part of the same world.

A recipe does not have to be an explicit user choice. Cloud Chamber may expose several recipes, select a default recipe, or hide the recipe beneath a direct “enter this cloud world” experience. The semantic relationship remains: supported simulations are grounded in known-working recipe designs.

### Simulation

**Type:** Core product concept

A **simulation** is one modeled atmospheric evolution produced from a recipe and the user's selected changes.

It is the evolving cloud or cloud field the user watches.

A simulation has:

- a particular recipe and selected conditions;
- a modeled timeline;
- evolving cloud structure;
- associated model data;
- available lenses;
- possible saved views;
- possible comparisons to other simulations.

A simulation is not the same as a recipe, run, output directory, saved view, or experiment.

Its identity comes from the modeled atmospheric evolution, not from one process, file set, storage location, or execution attempt. One simulation may involve more than one technical run, restart, checkpoint, execution attempt, or data source without becoming a different simulation.

A deliberate branch or materially different physical or numerical variant is normally a separate simulation so it can be examined and compared as a distinct outcome.

### Lens

**Type:** Core product and scientific-visualization concept

A **lens** is a reusable way to reveal a normally hidden atmospheric process, structure, or quantity.

Examples might include:

- updraft;
- downdraft;
- entrainment;
- liquid versus ice;
- precipitation development;
- cold-pool structure.

A lens may use:

- a direct model field;
- a derived diagnostic;
- a scientifically meaningful proxy;
- thresholds;
- visual encoding;
- explanatory context.

A lens is not merely a raw field selector or a saved camera position. It expresses how Cloud Chamber makes something invisible visible and understandable.

The same lens may apply across several cloud worlds, although its implementation, thresholds, or explanation may differ by world or recipe.

### Saved view

**Type:** Core product concept

A **saved view** is a preserved, revisit-able way of examining one simulation or comparison.

It may preserve:

- the simulation or simulations;
- an instant, time interval, or animation range;
- camera or projection;
- selected place, region, cross-section, or tracked feature;
- active lenses;
- synchronized comparison state;
- cloud opacity, thresholds, and display settings;
- annotations.

A saved view is not every temporary camera or display state. It becomes a saved view only when the user chooses to preserve a meaningful examination state for later return, comparison, explanation, or notebook use.

A saved view is not the simulation itself and does not alter the underlying model data.

### Comparison

**Type:** Core product concept

A **comparison** is two or more simulations or saved views examined together so the meaningful difference and resulting response are clear.

A comparison may relate:

- whole simulations;
- saved views;
- moments or time intervals;
- selected regions or features;
- diagnostics;
- visible cloud behavior;
- hidden atmospheric processes revealed through lenses.

It may identify:

- the reference simulation or view;
- one or more variants;
- the condition intentionally changed;
- what was held sufficiently comparable;
- relevant time and spatial alignment;
- active lenses;
- notable similarities and differences.

A comparison is not merely several unrelated outputs placed side by side. It is a central way Cloud Chamber helps users notice what changed.

A comparison may be casual and exploratory or may form part of a deliberate experiment. Only a formal experiment requires a deliberately controlled contrast.

### Exploration

**Type:** Core product activity

**Exploration** is the ordinary activity of watching a simulation, revealing hidden processes, changing meaningful conditions, comparing outcomes, and following curiosity.

Exploration does not require:

- a formal hypothesis;
- a predefined success criterion;
- a stored project structure;
- an academic workflow;
- a deliberate experiment.

The user may begin by watching, notice something unexpected, enable a lens, change a condition, or compare another simulation.

Exploration is the default mode of Cloud Chamber.

### Experiment

**Type:** Product and scientific activity

An **experiment** is an exploration made deliberate through a specific question or controlled comparison.

An experiment identifies:

- what the user wants to understand;
- what condition or factor is changed;
- what remains sufficiently comparable;
- which simulations or views are compared;
- what outcome would answer the question.

An experiment is not synonymous with a run, recipe, simulation, or formal research project.

Not every exploration becomes an experiment. An experiment is useful when deliberate structure adds clarity.

### Atmospheric condition

**Type:** Supporting scientific concept

An **atmospheric condition** is something physically true of the modeled setting.

Examples include:

- temperature profile;
- moisture profile;
- inversion strength;
- wind shear;
- surface temperature;
- surface heat or moisture flux;
- aerosol assumptions;
- large-scale subsidence.

An atmospheric condition is not an engine parameter, user-interface control, or numerical setting, even though those may be used to represent or change it.

### Control

**Type:** Supporting product concept

A **control** is the regime-aware way Cloud Chamber lets a user change a meaningful atmospheric condition or recipe choice.

Examples might include:

- weaken the inversion;
- moisten the boundary layer;
- increase surface heat flux;
- strengthen wind shear;
- change the forcing duration;
- choose a finer-resolution mode.

A control is not necessarily a direct CM1 parameter. It may map to several profiles, fields, files, or model settings.

Controls belong to cloud worlds and recipes. Cloud Chamber should not force all cloud worlds into one universal control set.

Recipe contents should distinguish among:

- fixed foundations needed for coherence;
- meaningful controls intended for ordinary exploration;
- advanced controls for deeper experimentation;
- implementation details normally hidden from the user.

### Atmospheric process

**Type:** Supporting scientific concept

An **atmospheric process** is something physically happening within a cloud world or simulation.

Examples include:

- buoyant ascent;
- condensation;
- entrainment and detrainment;
- turbulent mixing;
- collision-coalescence;
- ice growth;
- precipitation loading;
- evaporation;
- downdraft formation;
- cold-pool spread.

Atmospheric processes are central to the product because they are what Cloud Chamber aims to reveal.

An atmospheric process is not the same as a model field, diagnostic, lens, explanation, or technical execution process.

### Diagnostic

**Type:** Supporting scientific and implementation concept

A **diagnostic** is a defined calculation, summary, classification, or derived quantity used to expose or characterize an atmospheric condition or process.

Examples may include:

- cloud-top height;
- maximum vertical velocity;
- rain production;
- cold-pool intensity;
- entrainment proxy;
- liquid and ice partition;
- selected-region summaries.

A diagnostic is not raw model data and is not automatically an explanation.

A diagnostic should remain traceable to the model data, method, assumptions, units, thresholds, and relevant limitations used to calculate it.

Operational runtime health and data-integrity checks are not atmospheric diagnostics and should be described separately in implementation documentation.

### Observation

**Type:** Supporting product concept

An **observation** is something noticed or identified in a simulation, saved view, or comparison.

An observation may come from:

- watching visible cloud behavior;
- using a lens;
- examining a diagnostic;
- comparing simulations or views;
- a user's note or annotation;
- authored explanatory material.

An observation is not automatically an explanation or proof of causation. It records or communicates what appears to have happened before assigning why it happened.

Cloud Chamber may support observations through ordinary notes, annotations, captions, or authored content. This semantic model does not require observations to become formal database records or automated scientific claims.

### Run

**Type:** Supporting implementation concept

A **run** is the technical execution used to calculate all or part of a simulation.

A run may involve:

- a simulation engine;
- one concrete executable configuration;
- runtime settings;
- an execution attempt;
- produced model data.

A run is not the product object the user is meant to care about. It is supporting machinery beneath the simulation.

A successful run does not by itself establish that the simulation is useful, scientifically coherent, visually worthwhile, or correctly interpreted.

### Model data

**Type:** Supporting scientific and implementation concept

**Model data** is the output produced by a run.

It may include:

- three-dimensional and two-dimensional model fields;
- time series;
- profiles;
- surface fields;
- logs and execution metadata;
- derived datasets.

Model data is not the same as a simulation, lens, diagnostic, saved view, comparison, or explanation.

The product should preserve enough provenance to identify how the model data was produced and what assumptions or limitations affect its use.

### Explanation

**Type:** Supporting product concept

An **explanation** is a clear account of why a cloud or cloud field appears to have behaved as it did.

An explanation may connect:

- what changed;
- which atmospheric process responded;
- how the visible cloud changed;
- what a lens or diagnostic revealed;
- what remains uncertain.

An explanation is not raw model data and is not scientific truth merely because Cloud Chamber presents it.

Explanations may be authored, recipe-backed, user-written, or eventually assisted by software. This semantic model does not require automated explanation.

Understanding is a product outcome, not a required stored object or automated reasoning system.

## 3. Product-quality obligations

Beauty and wonder are not semantic entities, but they are explicit quality obligations.

A supported cloud world and recipe should ultimately be evaluated across several dimensions rather than by successful execution alone:

- **Scientific coherence:** the setup represents a meaningful atmospheric system.
- **Operational reliability:** the recipe can be run and reproduced as intended.
- **Visual integrity:** the representation remains honest about what the model produced.
- **Watchability:** the cloud has form, movement, temporal life, and a worthwhile visual experience.
- **Process visibility:** useful lenses reveal the important hidden processes.
- **Explorability:** the user has meaningful conditions to change.
- **Comparability:** changes can be examined without obscuring what differed.
- **Explanatory usefulness:** the experience helps the user understand the cloud better.
- **Known limits:** assumptions and constraints are stated where they materially affect interpretation.

These dimensions should be expressed specifically. They should not become repeated generic warnings or a disclaimer-heavy experience.

## 4. Relationship to scientific modeling language

Cloud Chamber should use normal atmospheric-modeling concepts rather than inventing unnecessary substitutes.

A recipe may contain:

```text
Initial conditions
Boundary conditions
Surface and terrain
Forcing
Initiation
Model physics
Domain
Grid
Time step
Simulation duration
Output strategy
```

These are ingredients of the complete simulation design.

The product-semantic layer adds:

```text
Cloud world
Meaningful controls
Expected broad behavior
Useful lenses
Compute options
Watchability and explanatory goals
```

The recipe is therefore broader than an atmospheric setup but more specific than a cloud world.

A concise distinction is:

> The cloud world defines what kind of atmospheric place and experience this is.  
> The recipe defines exactly how Cloud Chamber creates a credible and explorable version of it.  
> The simulation is one evolving cloud produced from that recipe and the user's selected changes.

## 5. Current implementation mapping

Current implementation terms should map into this model in one direction. They do not define it.

| Current term or surface | Semantic interpretation |
| --- | --- |
| `scenarios/` templates | Partial implementation of recipe ingredients or run setup; not automatically approved recipes |
| `run_recipe` values | Current implementation labels; they do not establish the canonical meaning of recipe |
| Build | Current UI surface for selecting conditions and producing runs; not a core product concept |
| Results | Current UI surface for locating ingested output; not the semantic center of the product |
| Explore | Current UI surface for visualization and diagnostics; partial implementation of simulation viewing and lenses |
| dry-run package | Current execution artifact beneath a run |
| `run_manifest.json` | Current run lifecycle and provenance implementation |
| CM1 process | Current engine execution detail beneath a run |
| completed output | Current lifecycle state of model data |
| `result_metadata.json` | Current metadata used to locate and characterize model data |
| `result_card.json` | Current partial implementation of user notes and saved context |
| result card | Historical/current UI term; not a foundational product object |
| notebook | Possible future organizational capability; not defined here as a fixed sidecar or result-attached object |
| Thermal Fate | Superseded product framing; may remain in historical or bounded research context only |
| Golden Path | Superseded PM terminology; do not use as active product architecture |
| completed run | Ambiguous; qualify as run completion, available model data, or simulation readiness as appropriate |

Generated packages, manifests, ingest states, runtime storage, frontend/backend boundaries, and LAN execution remain important implementation concepts. They belong in current architecture and lifecycle documentation, not in the foundational product-semantic spine.

## 6. Usage rules

### Cloud world

Use for the defined cloud setting and experience.

Do not use as a synonym for one simulation, one recipe, one case file, or one scientific regime label.

### Recipe

Use for a complete, known-working, modifiable simulation design within a cloud world.

Do not use for every saved configuration, namelist, scenario template, or generation path.

### Simulation

Use for the evolving modeled cloud or cloud field the user watches.

Do not use interchangeably with run, model data, recipe, or experiment.

### Lens

Use for a reusable way of revealing a hidden process, structure, or quantity.

Do not use for every display toggle, raw field selector, or saved camera angle.

### Saved view

Use for a deliberately preserved time, place, angle, region, and lens configuration.

Do not treat every temporary visualization state as a saved product object.

### Exploration

Use for the ordinary act of watching, changing, revealing, comparing, and following curiosity.

Do not require an exploration to be formalized, stored, or treated as an experiment.

### Experiment

Use when an exploration has a specific question or controlled comparison.

Do not use as a synonym for every simulation or run.

### Observation

Use for something noticed or identified in a simulation, saved view, or comparison.

Do not treat an observation as an explanation or causal conclusion merely because it is visually compelling.

### Result

Avoid as a canonical product object unless qualified.

The word may refer to an outcome in ordinary prose, but it should not define product identity through an ingest state.

### Scenario

Use only for current implementation templates or clearly qualified planning cases.

Do not use as a synonym for cloud world, recipe, simulation, or experiment.

### Process

Prefer atmospheric meaning in product and scientific language.

Use execution, run, or job for technical solver activity.

## 7. Decisions left open

This document does not decide:

- which cloud worlds are built first;
- which recipes become supported;
- how recipes are versioned;
- which recipe ingredients are user-facing;
- which controls are ordinary or advanced;
- final navigation or user-interface structure;
- how simulations, saved views, comparisons, or notes are persisted;
- whether notebook capabilities are built;
- whether explanations are authored, generated, assisted, or user-written;
- final schemas, APIs, databases, storage, or compute architecture;
- whether engines other than CM1 are supported;
- the experimentation strategy;
- the MVP;
- implementation migration or retirement work.

## 8. Working test

A future product decision should be expressible in this language without referring first to the current implementation.

Ask:

1. Which cloud world does this serve?
2. Is this part of a recipe, one simulation, or the machinery beneath a run?
3. What meaningful condition can the user change?
4. Which atmospheric process becomes visible?
5. Which lens reveals it?
6. What can the user preserve as a saved view?
7. What observation can the user make?
8. What simulations, moments, regions, diagnostics, or views can be compared?
9. Is the activity ordinary exploration or a deliberate experiment?
10. Does the work create a cloud worth watching, reveal something normally hidden, enable a meaningful change, improve comparison, or help explain what happened?

If the answer depends primarily on current package generation, ingest states, UI tabs, file paths, or backend ownership, the product semantics are being pulled back toward the current implementation.
