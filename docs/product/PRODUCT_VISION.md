# Cloud Chamber

## Product Vision

### See clouds from the inside

Cloud Chamber exists because clouds are beautiful, dynamic, and mostly hidden from us.

We can watch a cumulus tower grow, a storm darken, or coastal stratus move inland, but we cannot normally see the machinery inside: the thermals feeding the cloud, the entrainment peeling it apart, the eddies rolling through it, the droplets colliding and coalescing, the ice crystals competing for vapor, the precipitation loading the updraft, or the cold pool forming and spreading beneath the storm.

Cloud Chamber should provide something close to magic vision.

It should let people create scientifically meaningful cloud worlds, watch them evolve, reveal the invisible processes inside them, change the atmosphere, and learn by seeing how the cloud responds.

## The Product Promise

A user should be able to:

1. enter a cloud regime;
2. watch a beautiful cloud or cloud field form and evolve;
3. reveal the hidden motions and processes inside it;
4. change something physically meaningful;
5. compare what happened;
6. understand why the cloud changed.

The central experience is not configuring CM1.

The central experience is seeing and understanding clouds in ways the real sky normally does not allow.

## A World of Clouds

Cloud Chamber is not about one favorite cloud type.

It should grow into a collection of scientifically grounded cloud worlds, including:

- continental fair-weather cumulus;
- marine trade cumulus;
- cumulus congestus;
- deep precipitating convection;
- coastal stratus and stratocumulus;
- stratocumulus breakup and transition;
- sea-breeze or boundary-triggered convection;
- orographic cloud;
- cold-pool-driven convection;
- other regimes that CM1 can represent credibly.

Each cloud world should have its own characteristic beauty, physics, questions, and controls.

Fair-weather cumulus can reveal boundary-layer thermals, entrainment, and repeated growth and decay.

Congestus can reveal thermal succession, dilution, precipitation onset, and the transition toward deeper convection.

Deep convection can reveal organized updrafts, ice processes, precipitation loading, downdrafts, and cold pools.

Coastal stratus can reveal radiative cooling, surface coupling, inversion structure, advection, and breakup.

No one cloud regime defines Cloud Chamber. Any recipe we build first is one entry point into a broader atmospheric laboratory.

## Seeing the Invisible

Cloud Chamber should make normally invisible atmospheric processes visible and understandable.

Depending on the cloud regime and the fidelity of the simulation, the user should be able to reveal:

- updrafts and downdrafts;
- buoyancy;
- turbulent eddies;
- entrainment and detrainment;
- temperature and moisture structure;
- liquid cloud water;
- rain;
- cloud ice, snow, graupel, or hail;
- pressure perturbations;
- precipitation loading;
- evaporation and cooling;
- cold-pool formation and expansion;
- droplet and ice-particle behavior where the model supports it.

The goal is not to place scientific overlays on top of a cloud as decoration.

The goal is to let the user look inside the cloud and understand what it is doing.

## Learning by Changing the Atmosphere

Cloud Chamber should support controlled exploration.

A user might ask:

- What happens when the air above the cloud is drier?
- What does a stronger inversion do to fair-weather cumulus?
- What happens when the surface supplies more moisture than heat?
- How does wind shear reshape a deep convective tower?
- What causes a shallow cloud to become congestus?
- When does rain begin, and how does it change the cloud that produced it?
- What maintains a coastal stratus deck?
- What causes a cold pool to strengthen and spread?
- What additional structures appear when the simulation is run at finer resolution?

The product should connect the experiment to the response:

```text
What changed in the cloud world
→ what atmospheric process responded
→ how the cloud changed
→ what became visible
```

The user should begin from a cloud world that already works, change something meaningful, and learn from the difference.

## Scientifically Grounded Cloud Worlds

Cloud Chamber should be scientifically grounded because the real physics are more interesting than arbitrary animation.

Each cloud world should be based on a complete and defensible atmospheric experiment. That may draw from:

- an official CM1 case;
- a peer-reviewed CM1 study;
- a documented adaptation;
- a real observed atmosphere combined with explicit idealized forcing.

A complete cloud world may include:

- an atmospheric profile;
- a wind profile;
- a surface state;
- surface heat and moisture exchange;
- radiation;
- large-scale tendencies;
- an initiation or forcing mechanism;
- cloud and precipitation physics;
- turbulence treatment;
- a numerical domain and resolution.

A sounding can make the atmosphere less arbitrary, but it is one part of the cloud world rather than a complete weather system.

Observed soundings, aerosol measurements, surface conditions, and cloud observations should be used to constrain experiments—not to turn Cloud Chamber into a forecasting product.

The relevant question is:

> How does this atmosphere behave inside this cloud world?

Not:

> Will this reproduce the weather that occurred?

Idealization is not a defect when it is explicit, purposeful, and physically coherent.

## Beauty Is Part of the Product

Cloud Chamber should make atmospheric simulation visually compelling.

The user should want to watch the cloud.

A successful result should have form, depth, movement, scale, and temporal life. It should reveal both the visible cloud and the hidden atmosphere that creates it.

Possible views include:

- a beautiful volumetric cloud evolving through time;
- transparent or sliced views into the cloud interior;
- particles, vectors, or streamlines revealing airflow;
- liquid, ice, and precipitation shown distinctly;
- close views of turrets, mixing zones, and precipitation shafts;
- ground-level views of spreading cold air;
- side-by-side comparisons between experiments;
- changes in resolution or physics made visible.

Visual quality is not decoration added after the science. It is how the user encounters and understands the science.

The visual representation should remain honest about what the model resolved. Rendering may improve clarity, depth, contrast, motion, and beauty, but it should not silently invent physical structure that was never simulated.

The quality bar is not one specific cloud or published figure. It is the ambition to make every supported cloud regime as compelling as its physics and practical compute allow.

## The Role of Recipes

Cloud Chamber will need cloud recipes, but recipes are not the emotional center of the product.

A recipe is a reliable, scientifically grounded way to create and explore a particular cloud world.

It should define:

- the cloud regime;
- the complete base experiment;
- the expected cloud behavior;
- the expected visual character;
- the meaningful ways the user can modify it;
- the limits of what can be inferred.

Recipes should prevent two bad extremes:

- fixed demonstrations that cannot be explored;
- arbitrary model controls that make it easy to create uninterpretable simulations.

The user should experience a coherent cloud world and meaningful choices, not a wall of namelist options.

## A Spectrum of Fidelity

Cloud Chamber should support different levels of fidelity over time.

Some cloud worlds may be practical to explore quickly. Others may require finer resolution, larger domains, more complete cloud physics, or remote compute to reveal additional structure.

A lower-cost experiment can still be valuable if it is scientifically coherent, visually worthwhile, and honest about its limits.

High-resolution CM1 studies provide a scientific and visual north star. They show what becomes possible when more of the cloud's turbulence and microphysics are resolved. They should inspire the product without narrowing it to one cloud type or making research-scale compute the minimum acceptable experience.

## What Cloud Chamber Is Not

Cloud Chamber is not primarily:

- a weather forecasting system;
- a tool for predicting whether one sounding will produce a storm;
- a universal sounding-ranking system;
- a severe-weather simulator only;
- a cumulus simulator only;
- a gallery of fixed CM1 demonstrations;
- a free-form CM1 namelist editor;
- a mechanism for increasing forcing until an interesting cloud appears;
- a graphics product detached from atmospheric physics.

These capabilities may appear in supporting roles, but none defines the product.

## Enduring Principles

### Wonder comes first

The project exists because clouds are fascinating and because seeing inside them would be extraordinary.

Scientific rigor, recipes, compute, and software architecture should serve that experience.

### The current experiment is never the whole product

A success or failure in one cloud regime should not redefine Cloud Chamber around that result.

### The real physics are the attraction

Scientific grounding should deepen the user's sense of wonder, not bury it under disclaimers.

### Cloud worlds must be explorable

The user should be able to change meaningful conditions and learn from the response.

### Controls belong to regimes

Fair-weather cumulus, coastal stratus, congestus, and deep convection should not be forced into one universal set of controls.

### Seeing is part of understanding

Visualization is a primary product capability, not postprocessing.

### Limits should clarify, not dominate

The product should communicate what is idealized, parameterized, or unresolved in a direct and natural way without making caution the center of the experience.

### One beautiful cloud is not enough

Cloud Chamber should become a varied collection of cloud worlds and atmospheric questions.

## North Star

> **Cloud Chamber lets people create beautiful, scientifically meaningful cloud worlds, see the invisible processes inside them, change the atmosphere, and learn by watching the clouds respond.**

## The Test

A major product decision should bring Cloud Chamber closer to at least one of these outcomes:

- a cloud worth watching;
- an invisible atmospheric process made visible;
- a meaningful experiment the user can perform;
- a clearer explanation of why the cloud behaved as it did;
- a new scientifically defensible cloud world.

Work that does none of these may be necessary infrastructure, but it is not the product and should not be allowed to become the center of the project.

## Scope of This Document

This document defines why Cloud Chamber exists and what experience it should ultimately create.

It does not decide:

- which cloud world to build first;
- the experimentation path;
- the MVP;
- recipe implementation details;
- validation procedures;
- application architecture;
- compute infrastructure;
- interface design.

Those decisions should follow from this vision rather than redefine it.
