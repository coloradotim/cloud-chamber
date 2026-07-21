# Cloud Chamber MVP

**Status:** Approved controlling MVP scope. PR #384 established the personal-laboratory MVP, and issue #396 amends its homepage, Fun With Soundings, Trade Cumulus Lab, and implementation-roadmap details. The amendment does not reopen the North Star, Product Vision, Application Semantics, or the core Explore / Compare / persistence decisions.

## Purpose

This document defines the first durable version of Cloud Chamber worth building and keeping.

Cloud Chamber is not being designed for a public launch, classroom, team, or generalized scientific-computing market. It is the smallest coherent product that its sole initial user will repeatedly open, learn from, save work in, and extend.

The governing question is:

> What would make Cloud Chamber a durable personal cloud laboratory rather than a sequence of successful technical experiments?

## Authority and evidence

Controlling authority remains:

1. `NORTH_STAR.md`
2. `docs/product/PRODUCT_VISION.md`
3. explicit approved PM decisions
4. `docs/product/APPLICATION_SEMANTICS.md`
5. this approved MVP definition
6. bounded product documents such as `docs/product/TRADE_CUMULUS_PRODUCT_SLICE.md`
7. current implementation documentation and code
8. research and run evidence

This MVP is grounded in:

- canonical BOMEX reproduction;
- the Trade Cumulus product slice;
- the Canonical BOMEX Baseline;
- the Surface Moisture Supply comparison;
- the Trade Cumulus Updraft Lens;
- the fixed Trade Cumulus vertical-velocity scale;
- the first featured Baseline versus More Moisture Comparison merged through PR #385;
- the World-scoped foundation merged through PR #387;
- the existing observed-sounding, candidate-screening, run, ingest, and Result workflows that will be preserved under Fun With Soundings.

Application Semantics establishes that a Comparison may be casual and exploratory or may form part of a deliberate Experiment. A formal Experiment requires a controlled contrast; ordinary Comparison does not require validation or graduation.

Current Build / Results / Explore structure is implementation context. It does not define the final MVP journey.

## MVP thesis

Cloud Chamber is the repository owner’s **personal cloud laboratory and growing cloud-world atlas**.

The MVP should make it easy to:

- enter a Cloud World without first operating model machinery;
- watch a modeled cloud field evolve;
- reveal hidden atmospheric processes through Lenses;
- inspect scientific detail without losing the visual experience;
- read concise explanations that refresh atmospheric-science knowledge;
- start from an existing Simulation, change one or more supported settings, and launch a related run;
- leave while a model runs and return later without reconstructing context;
- compare a Simulation with its parent, reference, or another compatible Simulation;
- see exactly which configuration values differ;
- investigate strong, weak, surprising, mixed, inconclusive, or absent responses;
- save useful views, comparisons, and personal notes;
- preserve worthwhile Simulations as durable content;
- use observed soundings and broader experiments without forcing them into a Cloud World;
- continue building, testing, archiving, or leaving behind scientific directions.

Trade Cumulus is the first Cloud World in the MVP. It is not the permanent definition of Cloud Chamber.

Fun With Soundings is the first non-World workbench. It preserves flexible atmospheric experimentation that should not be buried inside a particular World.

The MVP succeeds when its owner voluntarily returns to it as an instrument, not merely when a scripted demo passes.

## 1. Sole target user and use context

The initial supported user is exactly one known person: the repository owner.

```text
User: one known local user
Primary machine: MacBook Air
Usage: local desktop browser and local runtime
Background: physics and atmospheric science
Knowledge state: technically capable, but atmospheric concepts may need concise refreshers
Role: both Cloud World author and product user
```

The product may assume comfort with physical quantities, units, plots, slices, model output, and technical provenance. It should not assume every atmospheric concept is fresh in memory.

Explanations should:

- lead with a direct physical account;
- retain field names and units;
- provide concise reminders for concepts such as subsidence, entrainment, buoyancy, cloud-water path, perturbation wind, and turbulent transport;
- make exact model and numerical details available on demand;
- avoid both unexplained specialist shorthand and beginner-oriented condescension.

The MVP does not define external personas, classrooms, institutions, teams, or commercial users.

## 2. Product information architecture

### Cloud Chamber home is the primary entrance

The primary entrance is **Cloud Chamber home**.

The initial first-class destinations are:

```text
Cloud Chamber
├── Trade Cumulus — Cloud World
└── Fun With Soundings — Atmospheric workbench
```

Both destinations should be visible directly at a `1440 × 900` desktop viewport. Fun With Soundings must not be buried in settings, a secondary tools drawer, or Trade Cumulus.

Cloud Worlds remain core product concepts. Explore, Compare, Lab, Saved Views, saved Comparisons, notes, and Simulations belong within a World when the work has a coherent World context.

Fun With Soundings is not a World. It is a workbench for observed atmospheres, candidate screening, broader experiments, and unassigned or legacy Result history.

### A Cloud World is simply a Cloud World

For the sole user, a Cloud World is a Cloud World regardless of how much content has been authored or whether it is the current focus of work.

Do not organize Worlds in the product under:

- Installed Worlds;
- Draft Worlds;
- candidate versus graduated Worlds;
- product-development lifecycle categories.

Technical availability remains legitimate operational information. A World may report that content is available, partial, missing, corrupt, or in conflict. Those are content states, not user-facing classes of World.

A future World should appear alongside other Cloud Worlds without requiring a separate development-state shelf.

### Trade Cumulus World structure

```text
Trade Cumulus
├── Overview
├── Simulations
├── Saved Views
├── Comparisons
└── Lab
    ├── Activity
    ├── Create Variation
    └── History
```

### A Cloud World is durable context, not a validation museum

A World may organize:

- a reference Simulation;
- retained or automatically associated variations;
- active and historical run attempts;
- Recipes and Controls where they apply;
- world-appropriate Lenses;
- Saved Views;
- saved Comparisons;
- featured explanations and Comparisons;
- ordinary history worth retaining without featuring;
- the World’s Lab.

Saving or featuring controls return and prominence. It does not certify a scientific conclusion.

### Explore and Compare are workspace states

**Explore** examines one Simulation.

**Compare** examines the relationship between two related Simulations or Saved Views.

They are opened from a World, Simulation, completed Lab item, Saved View, or saved Comparison. They are not permanent global navigation peers.

### Fun With Soundings structure

```text
Fun With Soundings
├── Find Soundings
├── Candidates
├── Build & Run
└── Past Experiments
```

Fun With Soundings preserves flexible experiment work without implying that every sounding or Result belongs to a Cloud World.

## 3. Simulation, Run, Result, and lineage

Explore presents a **Simulation**, not a technical Run or Result.

The ordinary World lineage is:

```text
Cloud World
→ parent or reference Simulation
→ selected supported changes
→ technical Run
→ completed model output
→ Result metadata and assets
→ Simulation
→ Explore or Compare
```

A Run is execution machinery. A Result is the ingested technical record. A Simulation is the modeled atmospheric evolution the user returns to.

Every related World Simulation retains, when known:

- Cloud World;
- source Recipe;
- parent or reference Simulation;
- optional user question or run note;
- exact changed physical and numerical values;
- sufficiently comparable fixed settings or an unchanged-configuration fingerprint;
- technical run, Result, source-model, field, and integrity identity;
- Control identity and values when an explicit Control applies.

A Simulation does not require a graduated Control to be explored or compared.

The user should not reconstruct lineage from filenames, timestamps, issue numbers, tags, or memory.

### World variation identity

A variation intentionally created from an existing World Simulation belongs to that World from inception.

Its stable Simulation identity exists before package creation. When a technically inspectable Result is ingested for that identity, the Simulation becomes explorable automatically.

No separate Retain, promotion, or graduation ceremony is required.

Failed or non-inspectable attempts remain in World Lab Activity and History but cannot masquerade as available Simulations.

### Non-World experiment identity

A Fun With Soundings experiment remains an experiment unless the user later deliberately associates it with a World through a separately approved workflow.

The product must not silently infer World membership from cloud type, sounding shape, scenario name, or Result content.

## 4. Trade Cumulus

Trade Cumulus is the first Cloud World in the MVP.

Its initial durable content is:

```text
Trade Cumulus
├── Canonical BOMEX Baseline
├── More Moisture
├── Updraft Lens
├── Saved Views
└── Featured Moisture Comparison
```

The Moisture Comparison merged through PR #385 is the first **featured saved Comparison**. It proves one authored compare-and-explain presentation. It does not define the complete Compare workflow.

User-facing identities are stable and independent of timestamped run and Result names. Technical identifiers remain available in Details and provenance.

### Precomputed revisit path

The revisit journey uses local precomputed content.

Entering Trade Cumulus must not require:

- launching CM1;
- generating a package;
- waiting for a six-hour Simulation;
- finding a timestamped Result;
- understanding runtime storage before seeing a cloud.

Trade Cumulus Lab remains available when the user wants to create a variation.

## 5. Fun With Soundings

Fun With Soundings is a first-class atmospheric workbench.

It exists because observed soundings and broad atmosphere-first experiments may produce:

- shallow clouds;
- deep convection;
- dry thermals;
- capped or elevated responses;
- no cloud;
- a failed or incoherent experiment.

That flexibility is useful. It should not be forced into Trade Cumulus or mislabeled as a Cloud World.

### Find Soundings

Preserve and clarify current capabilities for:

- IGRA catalog loading and refresh;
- cached station-file management;
- station search and selection;
- sounding time selection;
- supported local/source-path selection;
- manual sounding upload where implemented;
- parsing;
- profile and data-quality preview.

Lead with the selected atmospheric source, station, time, availability, and next action rather than internal scenario IDs or machine paths.

### Candidates

Preserve and clarify:

- candidate screening;
- story/family/support/readiness filters;
- station-history scope;
- latest-per-station behavior;
- sorting and result limits;
- candidate detail;
- saving/removing candidates;
- selecting a candidate for setup;
- run-plan and batch-queue preparation.

Use progressive disclosure so power remains available without presenting every filter as equally important.

### Build & Run

Preserve the current useful observed-sounding workflow:

- selected sounding or candidate;
- bounded supported run configuration;
- pre-run validation;
- dry-run package creation;
- run plan and batch queue;
- local execution;
- LAN-worker launch, refresh, collect, finalize, and cleanup;
- ingest;
- storage status and deletion preview.

Present the workflow as:

```text
Atmosphere
→ Experiment setup
→ Review
→ Create package
→ Run and monitor
```

Do not turn it into a universal CM1 namelist editor.

### Past Experiments

Past Experiments is the home for:

- observed-sounding Results;
- unassigned experiments;
- legacy scenario Results that do not belong to a World;
- broad technical Result inspection;
- legacy tags and Result notes until superseded;
- storage and cleanup access.

Default to sounding-related experiments, with a clear option to show legacy and unassigned work.

A World-owned Simulation encountered through the broad archive must display its World ownership and open in its World. Fun With Soundings must not appear to own it.

Non-World Result Explore uses an experiment/workbench context, not a Trade Cumulus breadcrumb.

## 6. Essential user journeys

### Revisit and explore Trade Cumulus

```text
Open Cloud Chamber
→ see Trade Cumulus and Fun With Soundings
→ enter or resume Trade Cumulus
→ watch the Canonical BOMEX Baseline evolve
→ move through model time
→ activate the Updraft Lens or inspect a Field Slice
→ inspect coordinated 3-D and slice views
→ read explanation and science beside the evidence
→ write a Simulation note or save a view
→ open a saved or featured Comparison
→ return later to the same World and state
```

### Create a Trade Cumulus variation

```text
Open a Trade Cumulus Simulation
→ Create Variation
→ inherit its exact configuration
→ name the variation and optionally write a question
→ change one or more supported settings
→ inspect every material configuration difference
→ review and launch through existing execution machinery
→ leave while the model runs
→ return to Trade Cumulus Lab Activity
→ see running, completed, caveated, failed, or incomplete state
→ Explore the inspectable Simulation
→ Compare to its parent or Canonical BOMEX Baseline
```

No later promotion action is required for an inspectable variation that was created with valid Trade Cumulus identity and lineage.

### Investigate through Compare

```text
Open Compare from a Simulation, World, or completed Lab item
→ choose parent, reference, or another compatible Simulation
→ inspect exact differences and technical trust
→ begin aligned where scientifically honest
→ link or unlink time, camera, plane, and Lens/scale
→ independently arrange views when useful
→ write a note
→ save the Comparison
→ reopen it later
```

### Work with observed soundings

```text
Open Fun With Soundings
→ find, load, or upload a sounding
→ inspect its profile and quality
→ screen or select a candidate
→ configure a bounded experiment
→ create a package
→ run locally or through the current worker
→ return later
→ ingest and inspect the Result
→ find it again in Past Experiments
```

### Begin another Cloud World

```text
Open Cloud Chamber home
→ create or add a Cloud World
→ enter its Lab
→ develop its first scientifically grounded Simulation
→ continue, archive work, or leave it alone
```

The product does not label the World “draft” merely because it is early.

## 7. Trade Cumulus overview requirements

The overview should provide:

- **Resume:** last active Simulation, Saved View, or saved Comparison;
- **Simulations:** reference and related variations;
- **Saved Views:** preserved single-Simulation examinations;
- **Comparisons:** saved and featured Comparisons;
- **Lab status:** active, completed, caveated, failed, or incomplete work needing attention;
- **Create Variation:** a direct path from the reference or another eligible Simulation.

A representative structure is:

```text
Trade Cumulus

Resume
Canonical BOMEX Baseline — 04:18:00 — Updraft Lens

Simulations
Canonical BOMEX Baseline
More Moisture
Recent variations

Saved Views
...

Comparisons
Featured: More Moisture versus Baseline
Saved: ...

Lab
1 run in progress
2 completed items ready to inspect
Create Variation
```

## 8. Trade Cumulus Lab contract

The final Lab is not the legacy global Build / Results interface placed inside a World.

It is:

```text
Trade Cumulus Lab
├── Activity
├── Create Variation
└── History
```

### Activity

Activity is the default actionable work queue.

It groups relevant records by state:

- Needs attention;
- Running;
- Completed awaiting ingest;
- Completed or caveated and ready to inspect;
- Failed or incomplete;
- Recently completed.

Each card leads with:

- intended Simulation/variation name;
- parent or reference;
- optional question;
- exact material difference summary;
- lifecycle, ingest, and technical-trust state;
- last update;
- next useful actions.

Possible actions include:

- View status;
- Ingest;
- Explore;
- Compare to parent;
- Compare to Canonical BOMEX Baseline;
- Review failure;
- Open technical details.

Do not display actions that cannot complete.

### Create Variation

Create Variation starts from an eligible Trade Cumulus Simulation.

The editor:

- clones the parent configuration exactly;
- requires a variation name;
- accepts an optional question;
- exposes only package-supported settings;
- groups settings into Atmosphere and forcing, Numerics and domain, Outputs, and advanced supported settings;
- shows a live categorized diff;
- validates output and Lens compatibility;
- writes stable identity and lineage before execution;
- uses the existing local and LAN-worker run machinery.

When the Result becomes inspectable, it appears automatically as the intended Simulation.

### History

History contains only Trade Cumulus-related work:

- retained or automatically associated Simulations;
- lineaged but non-inspectable attempts;
- failed and incomplete attempts;
- prior World run history.

It does not contain unrelated sounding, deep-convection, or legacy Results merely because they exist globally.

Useful filters include:

- lifecycle/status;
- parent/reference;
- inspectable versus non-inspectable;
- technical trust;
- date;
- search over Simulation name, question, and technical IDs.

Technical detail remains available on demand instead of permanently consuming half the page.

## 9. Explore workspace contract

Explore is the central instrument for one Simulation.

At `1440 × 900`, it should form one coherent workspace rather than a long page of implementation-specific components.

### Core hierarchy

```text
World / Simulation identity                Compare   Save View   More

3-D cloud scene                    Explain | Science | Notes | Details
Active Field Slice or Lens slice

Persistent timeline and active view controls
```

The 3-D scene and active slice are visible simultaneously. The inspector is visible by default and collapsible.

### Coordinated visual state

The 3-D scene and slice share:

- Simulation;
- model time;
- active Lens or selected Field Slice;
- slice orientation and physical position;
- cloud threshold where applicable;
- Lens scale;
- wind mode;
- cloud-boundary visibility.

Changing time or slice position updates coordinated views. A slice-based Lens displays its active plane in 3-D.

### Persistent timeline

The timeline provides:

- play and pause;
- previous/next saved frame;
- playback speed;
- current model time;
- saved-output position;
- world-appropriate key moments.

### Field Slice versus Lens

A **Field Slice** answers:

> Show this field on this plane.

It owns a field, orientation, position, units, scale, and native-value inspection.

A **Lens** is a curated process view. It may combine:

- one or more fields;
- derived diagnostics or proxies;
- world-specific scales and thresholds;
- contours, vectors, or overlays;
- useful defaults;
- explanation and interpretation guidance.

The Updraft Lens combines vertical velocity, the fixed Trade Cumulus scale, cloud-liquid boundary, perturbation horizontal wind, defaults, and explanation. It is not merely a `w` slice.

### One Lens context

One coherent Lens control and legend context serves the scene and slice. Do not repeat full legends for components expressing the same scale.

### Inspector

**Explain**

- authored explanation;
- physical interpretation;
- concise refresher content;
- material limits.

**Science**

- world-relevant metrics, profiles, time series, and process evidence;
- selected-state evidence where useful.

**Notes**

- editable Simulation note;
- Saved View note when relevant;
- clear saved and unsaved state.

**Details**

- exact fields and units;
- time and slice coordinates;
- Recipe and applicable Control values;
- parent/reference identity;
- configuration differences;
- run, Result, and asset IDs;
- hashes, provenance, runtime integrity, CM1, and NetCDF details.

### World-aware diagnostics

Trade Cumulus emphasizes cloud amount, depth, cloud-water path, lifecycle, updraft/downdraft structure, mixing/transport, and surface/large-scale forcing.

Expected absence of deep convection, precipitation, and reflectivity should not dominate its primary interface.

### Partial failure

Failure of one visual layer remains local. A failed 3-D layer does not disable the slice, timeline, explanation, science, notes, or Details. Retry targets the failed layer.

## 10. Compare workspace contract

Compare is ordinary investigation, not a validation-only report.

It is available when two Simulations have enough readable, compatible data to examine requested views or Lenses. A caveated Simulation may still be useful when caveats remain visible.

### Entry

From a completed World Lab item:

1. Compare to parent;
2. Compare to World reference;
3. Explore on its own.

From Explore, candidate order is:

1. parent;
2. World reference;
3. recent related Simulations;
4. Saved Views from related Simulations;
5. other compatible same-World Simulations.

From the World, Comparisons offers saved/featured Comparisons and New Comparison.

From a Saved View, Compare this view preserves it as one side.

Cross-World comparison is outside the MVP.

### Preview

Before opening, show:

- stable member identities;
- relationship;
- every material configuration difference;
- output/operational differences separately;
- trust and caveats;
- alignment compatibility.

Several changed settings must never become a one-factor causal claim.

### Aligned and Independent presets

```text
View preset: Aligned | Independent

Link:
Time
Camera
Slice plane
Lens and scale
```

Aligned enables every compatible link. Independent disables links. Mixed states are supported.

The user may manipulate either side; linked state causes the other to follow.

### Linking semantics

- Time links by modeled seconds, not frame index.
- Different cadences use nearest saved times and expose offsets without interpolation claims.
- Slice planes link by physical coordinate, not array index.
- Cameras link by normalized domain-relative orientation, target, and zoom.
- Lens and scale link only when scientifically compatible.
- Disabled links explain why.
- The interface identifies aligned, independent, or mixed state.
- Alignment is never faked.

### Featured Comparison

The PR #385 B5/M5 story reopens inside the ordinary Compare shell with its exact independent times, planes, cameras, scale, display state, evidence, and authored explanation.

## 11. Notes, Saved Views, saved Comparisons, and resume

### Notes

The MVP requires:

1. Simulation note;
2. Saved View title and optional note;
3. Saved Comparison title and optional note.

A working Compare note may autosave locally during the session. Saving the Comparison makes it durable.

No formal Observation database, claims graph, collaboration model, or generalized notebook ontology is required.

### Saved View

A Saved View preserves:

- World and Simulation;
- model time or playback range;
- camera;
- 3-D field and display settings;
- active Lens or Field Slice;
- slice orientation and position;
- cloud-boundary and wind state;
- active inspector section and collapse state;
- title and optional note.

### Saved Comparison

A Saved Comparison preserves:

- title and optional note;
- World;
- left and right Simulations or Saved Views;
- relationship;
- exact configuration-difference snapshot;
- technical-trust snapshot;
- aligned, independent, or mixed state;
- every link toggle;
- complete left and right view state;
- shared or side-specific Lens/Field Slice state;
- selected evidence;
- optional explanation;
- pinned or featured state;
- created and updated times.

Saving means:

> This examination is worth returning to.

It does not mean:

> This change has been scientifically validated.

Featuring changes prominence, not scientific status.

### Resume

The product remembers last active state for each World and relevant workbench context.

Returning to Trade Cumulus resumes its valid state unless the user explicitly chooses another object.

Returning to Fun With Soundings resumes the last workbench section and safely restorable selection where practical.

Restoration failures are explicit rather than silent.

## 12. Technical trust and interpretation

The product separates:

1. Can outputs be read and compared honestly?
2. What configuration values differ?
3. What appears to have happened?
4. How confident is the user?
5. Is the examination worth saving or featuring?

Only the first is an automatic technical gate.

Authored or personal explanation is distinguishable from backend-derived diagnostics. Missing or untrusted evidence is never converted silently to zero or certainty.

## 13. Content durability and recovery

World content must be more durable than ordinary timestamped output.

The MVP requires a bounded Trade Cumulus content mechanism that can:

- give reference, variation, featured Comparison, Saved View, saved Comparison, and authored-content assets stable identities;
- verify manifests, files, hashes, readability, required fields, and Lens prerequisites;
- preserve lineage and configuration differences;
- protect featured and pinned content from ordinary cleanup;
- make cleanup impact explicit for ordinary variations;
- detect missing or corrupt content;
- identify which World capability is unavailable;
- repair or reimport known local content predictably;
- keep multi-gigabyte output outside Git.

Saved objects preserve references when model content is missing so repair can restore them.

The first solution is local. It is not a marketplace, remote service, or plugin registry.

## 14. Continuing product evolution

A second Cloud World is not required for MVP completion.

Adding a later World should primarily involve:

- a scientifically grounded definition;
- one reference or known-working Simulation;
- related variations;
- Recipe assumptions;
- Controls where useful;
- Lenses and Field Slice defaults;
- explanations;
- Saved Views and Comparisons;
- world-specific evidence.

It should not require rebuilding the core home, World, Explore, or Compare shell.

The sole-user product should not categorize the World by authoring maturity.

Fun With Soundings may help discover atmosphere/experiment directions that later motivate a World, but automatic promotion is not part of the MVP.

This does not authorize a generic plugin platform, marketplace, generalized multi-engine architecture, or speculative remote compute.

## 15. Included MVP capabilities

The MVP includes:

- Cloud Chamber home;
- Trade Cumulus as a first-class Cloud World destination;
- Fun With Soundings as a first-class atmospheric workbench;
- no user-facing Installed/Draft World taxonomy;
- stable World and Simulation identities;
- precomputed local Trade Cumulus content;
- Trade Cumulus Overview, Simulations, Saved Views, Comparisons, and Lab;
- Trade Cumulus Lab Activity, Create Variation, and History;
- variation creation from any eligible Trade Cumulus Simulation;
- exact parent cloning and configuration differences;
- return-after-run lifecycle;
- one-Simulation Explore;
- three-dimensional playback;
- coordinated Field Slice and Lens rendering;
- persistent timeline;
- Trade Cumulus Updraft Lens;
- world-aware science and authored explanation;
- ordinary same-World Compare;
- linked, independent, and mixed Compare controls;
- featured Moisture Comparison;
- Simulation notes;
- Saved Views, saved Comparisons, and resume;
- observed-sounding search, screening, Build & Run, and Past Experiments;
- legacy and unassigned Result access outside Trade Cumulus;
- local content validation, protection, and repair;
- graceful missing-content and partial-layer states;
- technical provenance and integrity on demand.

## 16. Explicit exclusions

The MVP excludes:

- public users or onboarding;
- accounts, authentication, permissions, teams, collaboration, or sharing;
- analytics, telemetry, or growth instrumentation;
- mobile-first scientific exploration;
- cloud hosting or remote compute;
- mandatory live CM1 execution in the revisit journey;
- universal free-form CM1 namelist editing;
- automatic assignment of sounding experiments to a World;
- Installed/Draft/candidate/graduated World homepage taxonomy;
- another World merely to demonstrate breadth;
- another Control or Lens merely to demonstrate breadth;
- cross-World or incompatible comparison presented as direct comparison;
- generalized public Comparison tooling;
- generic Lens or visualization plugins;
- automated causal explanation;
- statistical-significance claims without appropriate evidence;
- a formal Observation database or claims graph;
- a generalized promotion/demotion framework;
- a content marketplace or registry.

## 17. Quality and trust requirements

### Scientific trust

- Configuration differences appear before interpretation.
- Multiple changes are never presented as a one-factor causal contrast.
- Aligned views use genuinely compatible coordinates, times, fields, and scales.
- Lens scales and thresholds remain stable and explicit.
- Saving or featuring is never labeled scientific validation.
- Expected absences are not treated as surprising failures.
- World membership is explicit and never silently inferred for sounding experiments.

### Interaction quality

- The home makes Trade Cumulus and Fun With Soundings equally discoverable.
- The core World, Explore, and Compare loop is coherent on the target MacBook Air.
- The Trade Cumulus Lab is an actionable World workflow, not a global database page.
- Fun With Soundings preserves expert capability through progressive disclosure.
- Product-facing names take precedence over issue/run/Result IDs.
- Partial failures remain local and recoverable.

### Persistence quality

- Saved Views and Comparisons restore deterministically.
- Last active state is retained for Trade Cumulus and relevant workbench context.
- Lineage, differences, trust, notes, and link state survive reloads.
- Featured content cannot be removed by ordinary cleanup without an explicit protected-content action.
- Missing/corrupt assets are reported and repairable.

### Operational quality

- Trade Cumulus revisit works offline after required local assets are present.
- Existing local and LAN-worker technical execution paths remain available.
- Returning later reveals queued, running, completed, caveated, failed, or incomplete state.
- Historical Results and sounding caches are not lost during UI reorganization.

## 18. Measurable completion criteria

The MVP is complete only when the following are demonstrated on the target MacBook Air.

### Home and destinations

- Cloud Chamber opens to a home showing Trade Cumulus and Fun With Soundings.
- Both are visible without category expansion or scrolling at `1440 × 900`.
- No Installed/Draft World taxonomy appears.
- Trade Cumulus opens in World context.
- Fun With Soundings opens in workbench context.
- Stable product names lead.

### Trade Cumulus Explore

- At `1440 × 900`, 3-D scene, active slice, timeline, and inspector form one workspace without long page scrolling.
- 3-D and active Lens/Field Slice are visible together.
- Time and plane changes update coordinated views.
- One Lens context serves scene and slice.
- Explain, Science, Notes, and Details are available.
- A Simulation note can be written and restored.
- Layer failures remain local.

### Ordinary non-featured variation

A fixture or ingested Result represents a technically inspectable, non-featured Trade Cumulus variation that:

- starts from an existing Simulation;
- requires no validation or graduation;
- retains lineage;
- changes at least two material physical or numerical values;
- is not the featured Baseline/More Moisture pair.

For this case:

- the parent configuration was cloned before changes;
- every difference is visible;
- the variation appears in Activity during lifecycle;
- inspectable output appears automatically as the named Simulation;
- Compare opens through lineage;
- no one-factor causation is implied;
- the Comparison can be saved and reopened.

No new CM1 run is required for acceptance.

### Compare linking

- A new related Compare opens with every compatible link enabled.
- Manipulating either linked timeline or camera moves the other.
- Time links use modeled seconds; plane links use physical coordinates.
- Time, Camera, Slice Plane, and Lens/Scale links toggle independently.
- Mixed states are supported and saved.
- Incompatible links explain why.
- PR #385 B5/M5 reopens exactly in its independent state.

### Saved states and resume

- A Saved View restores complete state and note.
- A saved Comparison restores both views, links, differences, trust, title, and note.
- Trade Cumulus resumes its last valid state.
- Fun With Soundings resumes its safe workbench context.
- Restoration failures are explicit.

### Trade Cumulus Lab

- Lab defaults to Activity.
- Activity groups actionable lifecycle state.
- Cards show variation identity, parent/reference, question, differences, trust, and actions.
- History contains only Trade Cumulus-related work.
- Duplicate Lab-history and global Experiment Notebook presentations are gone.
- Technical details are on demand.
- Create Variation is visible from eligible Simulations and Lab.
- Failed/non-inspectable attempts remain history without appearing available.

### Fun With Soundings

- IGRA/catalog/cache/station/time/upload/parse capabilities remain available where implemented.
- Candidate screening, filters, detail, save/select, and run-plan behavior remain available.
- Package, preflight, local/worker lifecycle, ingest, and storage behavior remain available.
- The current step, selected atmosphere, and next action are clear.
- Sounding Results are easy to find.
- Legacy/unassigned Results remain accessible.
- World-owned Simulations show ownership and open in their World.
- Non-World Result Explore uses workbench context.
- No historical Result or sounding cache is deleted by the UX migration.

### Content and recovery

- Trade Cumulus content is validated by stable identity and hashes.
- Ordinary cleanup does not remove protected content.
- Cleanup preview identifies dependent saved objects.
- Missing/corrupt assets produce bounded repair states.
- Local verified repair restores saved references.
- Multi-gigabyte output remains outside Git.

### Verification

- Automated coverage exercises home, World, workbench, Explore, Compare, persistence, variation lifecycle, Lab Activity/History, sounding workflow, and durability where practical.
- One live acceptance pass records the complete personal journey.
- Performance thresholds are based on measured MacBook Air behavior rather than guessed targets.
- No acceptance criterion requires running CM1.

## 19. Bounded implementation roadmap

Implementation proceeds one active issue at a time. Queued issues remain visible so sequencing is not hidden.

### Increment 1 — World-scoped foundation — complete

**Issue #386 / PR #387**

Established:

- Cloud World and Trade Cumulus shell;
- stable Simulation identity and lineage foundation;
- configuration differences;
- existing Explore and featured Comparison under World context;
- Field Slice versus Lens language.

### Increment 2 — integrated Explore

**Issue #388**

Implement the approved one-Simulation MacBook Air workspace.

### Increment 3 — ordinary Compare

**Issue #389**

Implement candidate selection, difference preview, Aligned/Independent presets, individual links, and the shared Compare shell.

### Increment 4 — Saved Views, saved Comparisons, notes, and resume

**Issue #390**

Persist and restore one- and two-Simulation examination state and notes.

### Increment 5 — Fun With Soundings

**Issue #395**

Create the first-class homepage workbench while preserving and reorganizing observed-sounding and broad experiment workflows.

### Increment 6 — Trade Cumulus Lab Activity and History

**Issue #394**

Replace the transitional global Result notebook inside Trade Cumulus with a World-specific actionable Lab and history.

### Increment 7 — Create Variation and return after the run

**Issue #391**

Start from any eligible Trade Cumulus Simulation, change one or more supported settings, preserve lineage, run, return, and Explore or Compare without a promotion ceremony.

### Increment 8 — durable World content and repair

**Issue #392**

Implement installed-content manifests, protection, dependency-aware cleanup, and local repair.

### Increment 9 — hardening and personal acceptance

**Issue #393**

Measure, correct only blocking defects, and record the final personal MVP acceptance disposition.

Roadmap changes require an explicit PM decision in issue #364 and corresponding authority update when product scope changes.

## 20. MVP authority and implementation gate

PR #384 approved the controlling MVP. PR #387 completed Increment 1.

Issue #396 amends the controlling scope to include:

- Cloud Chamber home rather than a Worlds-only homepage;
- first-class Fun With Soundings;
- no Installed/Draft World taxonomy;
- Trade Cumulus Lab Activity / Create Variation / History;
- automatic World membership for valid parent-based variations;
- the nine-increment roadmap above.

The amendment authorizes only the bounded issues recorded in the roadmap. It does not authorize simultaneous implementation, broad frontend cleanup, or unrelated product expansion.
