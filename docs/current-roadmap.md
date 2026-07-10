# Current Roadmap

Status: active roadmap for configurable observed-sounding CM1 runs

This is the active planning source for Cloud Chamber. The previous long
issue-by-issue roadmap is archived at
[archive/roadmap-and-issues-legacy.md](archive/roadmap-and-issues-legacy.md)
for historical reference only.

## North Star

Cloud Chamber is a real local LES experiment bench and notebook.

The product should help a user construct one credible CM1 LES experiment, run
it locally, ingest the completed output, review it as an experiment notebook
entry, and inspect what happened using CM1-derived evidence.

CM1 remains the high-fidelity source of truth. Cloud Chamber owns the local
workflow, metadata, diagnostics, output products, and visualization
interpretations around that source data.

## Current Product Model

- **Build** = configure and launch one CM1 run from a selected atmosphere,
  starting preset, and guarded run settings. Build owns active, incomplete, and
  non-ingested package/run work.
- **Results** = experiment notebook for completed and ingested runs. Results owns
  ingested-result review, notes, and explicit ingested-result cleanup.
- **Explore** = scientific inspection of one result using CM1-derived evidence.

Runtime inventory and cleanup are contextual actions inside Build and Results,
not a separate top-level Storage workspace.

## Hard Product Rules

- LES only for the current planning horizon.
- Local-first: local CM1, local runtime home, local result evidence.
- CM1 output is the source of truth for cloud evolution.
- Always distinguish preview estimate, CM1 run configuration, CM1
  running/completed result, and visualization interpretation.
- The browser must not parse raw NetCDF.
- Generated artifacts do not go in git.
- Quick means quick to execute, not meteorologically too short to be useful.
- A smoke check proves package/run/ingest health; it is not a science result.
- Science runs need enough model time to produce meaningful evolution.
- Grid/detail and output cadence are the primary user-facing cost levers.
- Raw numerical timestep is not a normal v1 user control.
- Presets are starting points. They should expose actual CM1-facing values in an
  advanced drawer instead of becoming rigid product families.
- Warn or caveat unvalidated control combinations instead of hiding every
  control.
- Build owns non-ingested cleanup; Results owns ingested-result cleanup.
- Explore remains scientific inspection, not Render Studio.

## Active Source Documents

Use these docs as the current strategic and contract sources:

- [Realistic LES Input Architecture Research](research/realistic-les-input-architecture.md)
- [Output And Visualization Architecture Research](research/output-and-visualization-architecture.md)
- [Realistic LES Input Specification](contracts/realistic-les-input-specification.md)
- [Output Product Specification](contracts/output-product-specification.md)
- [Sounding Candidate Screening Contract](contracts/sounding-candidate-screening.md)
- [Expanded Sounding Candidate Taxonomy](research/expanded-sounding-candidate-taxonomy.md)
- [Deep Convection Package Design](research/deep-convection-package-design.md)

The research memos are PM input and evidence. The contract docs define the
implementation boundary that future issues should build from.

The expanded sounding taxonomy is product/science planning input for pre-run
candidate stories. It does not make severe, winter, cold-pool, or specialized
boundary-layer stories scientifically validated until their scoring, evidence,
caveats, and package-readiness states are implemented and tested.

The deep-convection package design backs the current deep-convection
observed-sounding preset and package path. User-facing docs should describe this
as a configurable deep-convection run starting point, not as a separate
half-state "Trial" product. Internal metadata such as
`package_family = deep_convection_trial` may remain where renaming would create
more churn than clarity.

## Current State

- Observed-sounding upload and package generation now work through the backend
  parser and CM1 `input_sounding` route. Observed temperature, moisture, and
  complete usable u/v wind profiles are package inputs, not decorative metadata.
- Cached IGRA recent sounding refresh, local cached-sounding inspection,
  candidate screening, saved candidates, and package-ready/blocked candidate
  states exist. Candidate scores are pre-run selection aids, not CM1 outcome
  predictions.
- The deep-convection observed-sounding package path exists and has
  package/run/ingest smoke evidence. It can generate storm-scale CM1 packages
  with fixed v1 warm-bubble trigger metadata and expected deep-output fields,
  but it has not yet been characterized across a broad selected candidate set.
  #285 is needed before treating its defaults as broadly validated. Each
  observed sounding remains its own experiment whose result must be evaluated
  after CM1 runs.
- Build owns active package/run work, including generated packages, queued or
  running local CM1 work, failed or incomplete runs, completed-but-not-ingested
  output, serial local queue state, auto-ingest for completed usable output, and
  LAN-worker status/progress summaries.
- Results owns ingested notebook entries, result-card review, notes/tags, and
  explicit cleanup for ingested results plus their backing local data.
- Explore consumes bounded backend output products, interesting times,
  diagnostics summaries, native-grid slices, and visualization-ready point
  layers. The browser still does not parse raw NetCDF.

## Next Roadmap Lanes

These are candidate implementation lanes for PM review. Do not create them
automatically from this roadmap.

### Cached-Sounding Analysis And Sorting

Goal: make the cached IGRA workbench useful for choosing observed atmospheres
without pretending the score predicts CM1 success.

Scope: richer cached-sounding analysis, transparent sorting/filtering by story,
quality and support-state explanations, saved-candidate ergonomics, and clearer
blocked/package-ready evidence. Keep shallow, humid/rainy, and
deep-convection-oriented candidate stories as pre-run hypotheses.

Non-goals: universal "best sounding" ranking, forecast language, browser-side
station parsing, or unsupported story labels that look package-ready.

Why now: configurable observed-sounding runs need a better way to find and
compare input atmospheres before packaging.

### Configurable Observed-Sounding Run Controls

Goal: let Build start from a sane preset and then adjust run settings that map
to real CM1 configuration.

Scope: controls for model duration, grid/detail, output cadence, forcing, and
requested output fields within guarded bounds. Presets should remain available
as starting points, and an advanced drawer should expose the actual CM1-facing
values those presets imply.

Non-goals: raw numerical timestep as a normal v1 control, raw trigger controls,
new trigger types, or a full Build redesign in one issue.

Why now: the product direction is configurable runs, not rigid scenario or
package-family cages. Grid/detail and output cadence are the main cost levers;
duration controls must preserve enough model time for meaningful evolution.

### Pre-Run Configuration Validation

Goal: validate the selected atmosphere, preset, and adjusted CM1-facing settings
before package generation or launch.

Scope: backend validation for missing required observed fields, incomplete wind
profiles, suspicious duration/cadence combinations, unsupported output-field
requests, runtime-file requirements, cost/storage caveats, and clear dry-run
messages. Unvalidated combinations should warn or caveat when safe rather than
being hidden by default.

Non-goals: running CM1 in CI, declaring scientific success before CM1 output,
or silently patching bad input into something packageable.

Why now: configurable controls need trust boundaries before they become normal
Build workflow.

### Deep-Convection Configuration Validation Across Soundings

Goal: keep the deep-convection observed-sounding preset first-class while
measuring where its current configuration is package-ready, caveated, or
misleading.

Scope: validate complete observed-wind requirements, storm-scale box choices,
duration, grid/detail, domain size, output cadence, expected fields, expected
cost/runtime/output volume, larger-compute suitability notes, and
candidate-provenance copy across selected observed soundings. Separate
package/run/ingest smoke checks from science outcomes.

Non-goals: removing the deep-convection path, exposing raw trigger controls,
adding trigger types, or treating a smoke run as evidence that a specific
observed sounding should produce deep convection.

Why now: deep-convection packaging exists and is useful, but the trust language
must stay honest while configuration coverage expands.

### Surface Sensible/Latent Heat Flux Control Validation

Goal: determine which surface sensible and latent heat flux controls can be
safely exposed for observed-sounding runs.

Scope: audit CM1 reference paths and runtime-file requirements, define supported
and caveated sensible/latent heat flux combinations, document manual smoke-run
expectations, connect findings to pre-run validation, and decide how flux
settings are represented in advanced CM1-facing values.

Non-goals: atmospheric radiation validation, GIS/map realism, arbitrary
real-world terrain/surface initialization, or product promises that the current
CM1 configuration cannot support.

Why now: surface forcing is a direct run-builder control and should be validated
before the UI implies it can be varied safely across observed soundings.

### Atmospheric Radiation And Place-Time Control Validation

Goal: determine which radiation, date/time, and location-derived settings can be
safely exposed for observed-sounding runs.

Scope: audit CM1 radiation/place-time reference paths and runtime-file
requirements, define supported and caveated combinations, document manual
smoke-run expectations, and connect findings to pre-run validation.

Non-goals: arbitrary real-world terrain/surface initialization, GIS/map realism,
or product promises that the current CM1 configuration cannot support.

Why later: observed soundings preserve place/time provenance, but radiation and
place-time behavior should follow surface-flux validation unless a later PM
decision changes that order.

### Evolved-Sounding Output Products

Goal: make completed observed-sounding runs explain how the simulated atmosphere
changed, not only whether cloud water or vertical velocity appeared.

Scope: profile and time-height products, evolved thermodynamic/moisture/wind
summaries, bounded field catalog expansion, provenance, caveats, and tiny
fixture tests. Results and Explore should consume these as backend-prepared
products.

Non-goals: browser-side NetCDF parsing, broad diagnostics-lab UI, or external
export bundles before core result explanation is stable.

Why now: observed-sounding experiments become much more useful when users can
compare the initial profile to CM1-evolved structure.

## Not Now / Parked

These are not rejected forever. They are parked because they depend on product
contracts, output products, validation, or local bench maturity.

- **Bench Mode UI**: wait until realistic input records and output products are
  stable enough to compare experiments honestly.
- **Arbitrary GIS/map/imagery inputs**: wait for preprocessing, CM1
  initialization, and surface-data architecture evidence.
- **#153 surface heterogeneity**: blocked by realistic surface contract and
  validation; do not treat it as the next scenario step.
- **Additional severe-weather or deep-convection products**: the current
  deep-convection observed-sounding preset stays first-class, but additional
  severe-weather promises should wait for validation, evidence, and clear
  caveats.
- **Raw trigger controls and new trigger types**: keep trigger settings as
  fixed package metadata until useful ranges are validated.
- **Rigid experiment-family expansion**: prefer configurable observed-sounding
  runs with presets as starting points over more separate user-facing families.
- **#155 precipitation/cold-pool scenarios**: parked until output products can
  support precipitation, downdraft, and surface-response evidence.
- **#183 3-D vertical velocity layer**: useful later, but blocked by signed-flow
  field-product and rendering decisions.
- **#197 cloud appearance / renderer beauty pass**: parked until output
  products and inspection workflow are stable.
- **#198 cloud + field overlay**: parked until scalar/signed overlay contracts
  are defined.
- **Renderer-style timelapse ambition**: parked until output products mature.
  The near-term #201 scope is limited to saved-output play/pause and scrubbing
  across explicit backend time indices without interpolation, with the main 3-D
  scalar layer animating while synchronized slice/evidence payloads are deferred
  until pause and no default looping.
- **#43 remote/HPC compute**: deferred. The near-term compute extension is a
  trusted LAN worker used as a CM1 compute appliance while the MacBook remains
  the Cloud Chamber system of record.

## Planning Rule

When a future issue conflicts with this roadmap, update this file first or
explicitly document why the roadmap no longer applies. Do not let archived
roadmap material or old issue sequencing drive current planning.
