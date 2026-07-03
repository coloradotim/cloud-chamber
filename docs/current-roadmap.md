# Current Roadmap

Status: active roadmap after input/output contracts

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

- **Build** = construct and run one credible LES experiment.
- **Results** = experiment notebook for ingested and completed runs.
- **Explore** = scientific inspection of one result using CM1-derived evidence.
- **Storage** = lifecycle-aware runtime inventory and destructive cleanup.

## Hard Product Rules

- LES only for the current planning horizon.
- Local-first: local CM1, local runtime home, local result evidence.
- The browser must not parse raw NetCDF.
- Generated artifacts do not go in git.
- Contracts before UI.
- Output products before renderer ambition.
- Observed or detailed sounding before GIS/map realism.
- Storage owns destructive cleanup.
- Explore remains scientific inspection, not Render Studio.

## Active Source Documents

Use these docs as the current strategic and contract sources:

- [Realistic LES Input Architecture Research](research/realistic-les-input-architecture.md)
- [Output And Visualization Architecture Research](research/output-and-visualization-architecture.md)
- [Realistic LES Input Specification](contracts/realistic-les-input-specification.md)
- [Output Product Specification](contracts/output-product-specification.md)

The research memos are PM input and evidence. The contract docs define the
implementation boundary that future issues should build from.

## Active Execution Sequence

1. Implement output product manifest plus robust file/time index mapping.
2. Add interesting-time output products.
3. Prototype observed/detailed sounding import with metadata and provenance
   using tiny fixtures.
4. Add profile/time-height derived product skeletons.
5. Expand the field catalog for realistic LES outputs.
6. Audit and validate land/radiation reference paths.
7. Prototype external visualization/diagnostics exports.
8. Only then decide Render Studio or Diagnostics Lab product surfaces.

This order is intentional. It keeps the product grounded in trustworthy local
LES inputs and bounded output products before adding broader UI surfaces,
renderer technology, or new scenario families.

## Recently Completed

#204/#205/#218 cleaned up the Build/Results/Storage lifecycle model.

- **Build** shows active and incomplete package/run/ingest pipeline work.
- **Results** owns ingested notebook review.
- **Storage** owns explicit destructive cleanup.

## Recommended Issue Candidates

These are candidate implementation issues for PM review. Do not create them
automatically from this roadmap.

### Implement Output Product Manifest And Time Index

Goal: create the first local output product manifest with robust global
time-index to source-file mapping.

Scope: product manifest skeleton, source file fingerprints, model-output versus
stats-file distinction, global/local time index mapping, provenance, caveats,
and tests with tiny fixtures.

Non-goals: new renderer UI, external exports, CM1 package generation changes,
or real CM1 execution in CI.

Why now: this is the backend foundation for deep-output Explore performance,
interesting times, profiles, time-height products, and future render-ready
artifacts.

Dependencies: [Output Product Specification](contracts/output-product-specification.md).

### Add Interesting-Time Output Products

Goal: make first cloud, max cloud water, max updraft, rain onset, and related
time landmarks reusable by Results, Explore, comparison, and future time-based
views.

Scope: metadata-backed or bounded-product-backed interesting-time records,
tests using tiny synthetic outputs, and documentation of fallback/caveat rules.

Non-goals: timelapse UI, renderer animation, or new diagnostics lab surfaces.

Why now: users need meaningful time defaults before time-heavy UI work.

Dependencies: output product manifest and time-index mapping.

### Prototype Observed Sounding Import With Metadata

Goal: prove the first realistic-input path using observed or detailed sounding
fixtures while preserving source metadata and conversion caveats.

Scope: tiny fixture import, station/location/elevation, valid time/date, source,
units, observed wind conversion to CM1 `u`/`v`, conversion metadata,
package-review provenance, and a local Build upload path for extracted IGRA
station sounding-data files.

Non-goals: Bench Mode UI, arbitrary GIS/map inputs, surface heterogeneity, or
unvalidated scenario families.

Why now: observed soundings are the closest realistic input layer to the
existing external `input_sounding` path.

Dependencies:
[Realistic LES Input Specification](contracts/realistic-les-input-specification.md).

### Expand Field Catalog For Realistic LES Outputs

Goal: make realistic LES output fields discoverable and honestly classified
before Explore, diagnostics, or future render/export tools expose them.

Scope: field catalog expansion for realistic-output fields such as `qv`,
theta/temperature/pressure, surface sensible and latent fluxes, surface
diagnostics, radiation terms when present, `lwp`, `CAPE`, `CIN`, `LCL`, and
`LFC` when present. Include capability classification, units, coordinates,
native-grid metadata, supported product types, provenance, caveats, and tiny
fixture or metadata-backed tests.

Non-goals: package-generation changes, browser NetCDF parsing, arbitrary raw
field dump UI, renderer work, or new scenario families.

Why now: realistic inputs will only be useful if Results and Explore can
explain which model fields exist, what Cloud Chamber can safely do with them,
and which fields are merely present versus scientifically supported.

Dependencies: output product manifest, time-index mapping, and the
[Output Product Specification](contracts/output-product-specification.md).

### Define Profile And Time-Height Output Products

Goal: specify and add skeleton derived products that make realistic-input runs
explainable beyond point clouds and slices.

Scope: profile/time-height product shapes, bounded APIs, provenance, caveats,
and tiny fixture tests.

Non-goals: Diagnostics Lab UI, Panel/hvPlot integration, or broad scientific
diagnostic expansion.

Why now: profiles and time-height products are the bridge between raw fields
and scientific explanations for realistic LES inputs.

Dependencies: output product manifest, time-index mapping, and field catalog.

### Audit Land/Radiation Reference Paths

Goal: determine what Cloud Chamber can safely borrow from CM1 land/diurnal LES
reference cases before exposing location/date/radiation controls.

Scope: package audit, runtime-file requirements, namelist differences,
validation checklist, and a manual smoke-run plan.

Non-goals: GIS/map realism, arbitrary real-world locations, or UI controls.

Why now: location/date/radiation should come after observed sounding metadata
and before any map-like product promise.

Dependencies: realistic LES input contract and observed sounding prototype.

### Prototype External Visualization / Diagnostics Exports

Goal: test whether Cloud Chamber should hand selected output products to
external visualization or diagnostics tools after the internal product
contracts exist.

Scope: prototype export manifests or small bundles for tools such as VAPOR,
ParaView/VTK, xarray-style notebooks, or future local diagnostics sidecars.
Use bounded output products rather than raw browser-side NetCDF parsing, and
document provenance, caveats, file sizes, and cleanup expectations.

Non-goals: immediate product UI, renderer dependencies, Render Studio,
Diagnostics Lab, or committing generated export artifacts.

Why later: exports are valuable only after output product manifests,
time-index mapping, field catalogs, interesting times, and profile/time-height
products define what Cloud Chamber can safely hand off.

Dependencies: output product manifest, expanded field catalog, profile/time-
height products, and explicit PM review of external-tool direction.

## Not Now / Parked

These are not rejected forever. They are parked because they depend on product
contracts, output products, validation, or local bench maturity.

- **Bench Mode UI**: wait until realistic input records and output products are
  stable enough to compare experiments honestly.
- **Arbitrary GIS/map/imagery inputs**: wait for preprocessing, CM1
  initialization, and surface-data architecture evidence.
- **#153 surface heterogeneity**: blocked by realistic surface contract and
  validation; do not treat it as the next scenario step.
- **#154 deep convection**: parked until the shallow-LES bench and output
  products are mature.
- **#155 precipitation/cold-pool scenarios**: parked until output products can
  support precipitation, downdraft, and surface-response evidence.
- **#183 3-D vertical velocity layer**: useful later, but blocked by signed-flow
  field-product and rendering decisions.
- **#197 cloud appearance / renderer beauty pass**: parked until output
  products and inspection workflow are stable.
- **#198 cloud + field overlay**: parked until scalar/signed overlay contracts
  are defined.
- **#201 timelapse UI before time products**: parked until interesting-time and
  time-index products exist.
- **#43 remote/HPC compute**: deferred. The near-term compute extension is a
  trusted LAN worker used as a CM1 compute appliance while the MacBook remains
  the Cloud Chamber system of record.

## Planning Rule

When a future issue conflicts with this roadmap, update this file first or
explicitly document why the roadmap no longer applies. Do not let archived
roadmap material or old issue sequencing drive current planning.
