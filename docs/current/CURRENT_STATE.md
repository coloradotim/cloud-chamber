# Cloud Chamber Current State

**Status:** Descriptive repository snapshot

## Purpose

This document describes the software and repository as they exist today.

It is not:

- a product vision;
- a roadmap;
- an MVP definition;
- a decision about which current capabilities should remain;
- a decision about which scenarios or experiments should become supported recipes;
- a decision about the final application structure.

The controlling product documents are:

1. [North Star](../../NORTH_STAR.md)
2. [Product Vision](../product/PRODUCT_VISION.md)

Where this document describes current implementation that does not match the Product Vision, the mismatch is intentional and should remain visible.

## Current repository condition

Cloud Chamber has been developed through several different product framings.

The repository currently contains language, workflows, scenarios, contracts, issues, and implementation choices associated with ideas including:

- Baseline Shallow Cumulus as a Golden Path;
- Thermal Fate as an organizing concept;
- configurable observed-sounding runs;
- sounding screening and recommendation;
- surface-forcing experiments;
- explicit thermal and deep-convection initiation;
- cloud-opportunity and scout-to-full-run workflows.

These framings overlap and sometimes conflict.

Their presence in the repository records project history and implementation context. It does not establish current product direction.

## Current application structure

The application is local-first and uses an external CM1 installation.

The current technical flow is broadly:

```text
React / TypeScript frontend
→ Python / FastAPI backend
→ experiment configuration and package generation
→ external CM1 execution
→ runtime and NetCDF ingest
→ persistent result metadata
→ backend-derived diagnostics and visualization data
→ browser-based inspection
```

The current interface is organized around three top-level areas:

- **Build**
- **Results**
- **Explore**

This is the present interface structure. No decision has been made that it is the final product structure.

## Implemented capabilities

### Experiment configuration and packaging

The repository currently supports combinations of:

- committed scenario templates;
- observed IGRA sounding input;
- CM1-facing package and manifest generation;
- run duration, domain, grid, cadence, and output selection;
- surface heat and moisture forcing;
- supported idealized initiation modes;
- provenance and configuration review before execution.

The exact options available depend on the selected workflow and current implementation path.

### CM1 execution and run management

The application currently includes:

- local CM1 launch;
- serial local run queueing;
- progress and estimated completion reporting;
- cancellation where technically practical;
- automatic ingest for completed output-producing runs;
- optional trusted-LAN execution for supported paths;
- runtime logs and lifecycle state;
- checks that distinguish process completion from trustworthy scientific output.

### Results and storage

The application currently includes:

- persistent result records;
- editable result names, tags, and notes;
- run, scenario, sounding, configuration, and source provenance;
- explicit result and runtime cleanup controls;
- field-quality and runtime-integrity metadata;
- result summaries derived by the backend.

### Scientific fields and diagnostics

Current ingest and diagnostic code handles a range of CM1-derived information, including where available:

- cloud water;
- vertical velocity;
- water vapor and thermodynamic fields;
- rain water aloft;
- surface rain;
- reflectivity;
- ice and other hydrometeor species;
- surface heat and moisture fluxes;
- cloud-top and hydrometeor-envelope distinctions;
- selected-region or selected-point summaries;
- sounding-derived diagnostics and screening fields.

Availability and trust vary by run configuration, output fields, and data quality.

### Visualization

The current application includes:

- 2-D field slices;
- initial 3-D field inspection;
- cloud-water visualization;
- output-time selection;
- saved-output timelapse playback;
- camera and field controls;
- selected-region and selected-point inspection.

The current visualizer does not yet provide the complete experience described in the Product Vision.

### Observed-sounding support

The repository currently includes:

- IGRA sounding parsing and normalization;
- observed thermodynamic and wind-profile handling;
- local sounding cache workflows;
- sounding-derived diagnostics;
- candidate screening, sorting, saving, tagging, and notes;
- package configuration from selected observed soundings.

The existence of these capabilities does not decide how important observed soundings will be in the eventual product.

### Experiment and scenario content

The repository currently contains:

- a lower-atmosphere scenario catalog;
- shallow-cumulus contrast scenarios;
- low-cloud and warm-rain placeholders;
- uniform and differential surface-forcing work;
- observed-sounding evolution paths;
- explicit thermal-initiation work;
- deep-convection benchmark work;
- research notes and run records from successful, unsuccessful, and inconclusive experiments.

The scientific and product status of these items has not yet been reviewed under the new Product Vision.

## Current documentation condition

The documentation tree contains a mixture of:

- current operational instructions;
- implemented technical contracts;
- research evidence;
- design proposals;
- historical roadmaps;
- superseded product direction;
- documents that combine several of those roles.

Batch 1 established the North Star, Product Vision, and repository-recovery `AGENTS.md`.

A full file-by-file documentation audit has not yet been completed.

Until that audit is complete:

- lower-authority documents may contain useful facts;
- their product framing may be stale;
- their roadmap language should not be executed without new approval;
- their presence should not be interpreted as a decision to keep or remove the described capability.

See [Documentation Status and Authority](../DOCUMENTATION_STATUS.md).

## Current recovery status

Completed:

- approved North Star;
- approved Product Vision;
- recovery-mode `AGENTS.md`;
- closure of selected superseded product-direction issues and pull requests.

In progress:

- replacement README;
- this descriptive Current State document;
- documentation status and authority guide;
- concise pull-request template update;
- controlled-work issue template;
- reusable Codex task prompt template.

Not yet completed:

- full documentation disposition;
- scenario dependency and status review;
- application semantic map;
- CM1 experimentation strategy;
- MVP definition;
- final application architecture or workflow decisions.

## Questions that remain open

No final decision has yet been made about:

- which cloud regime or regimes should be developed first;
- which current scenarios have scientific or product value;
- what a supported Cloud Chamber recipe requires;
- how observed soundings should be used;
- which current forcing and initiation mechanisms should remain available;
- which diagnostics should be central to the user experience;
- which current capabilities should be retained, changed, or removed;
- whether Build, Results, and Explore should remain the top-level structure;
- what compute and fidelity tiers the product should support;
- what belongs in the MVP;
- how comparison should work;
- how cloud appearance and invisible-process visualization should be combined.

Those questions should be answered through explicit product decisions and the forthcoming experimentation strategy, not inferred from current code or repository history.

## Interpretation rules

When using this document:

- **Implemented** means the capability exists in some current form. It does not mean the capability is approved for the eventual product.
- **Current** means present in the repository or application now. It does not mean preferred.
- **Historical** does not mean useless.
- **Under review** does not mean targeted for removal.
- A successful experiment does not establish a general recipe.
- An unsuccessful experiment does not establish that the underlying cloud regime or mechanism lacks value.
- Existing architecture creates constraints and opportunities, but does not by itself decide the product.

## Updating this document

Update this document only to reflect material changes in the descriptive state of the repository or application.

Do not use an update to this document to make product decisions.

Any proposed edit should make clear whether it is:

- correcting a factual description;
- recording an implemented capability;
- recording removal of an implemented capability;
- recording repository-recovery progress;
- or attempting to make a product decision that belongs elsewhere.
