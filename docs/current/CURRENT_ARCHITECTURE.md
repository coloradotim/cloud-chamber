# Cloud Chamber Current Architecture

**Status:** Current descriptive implementation snapshot

This document describes the repository and application architecture that exist
today. It is not a final product architecture, scientific specification, or
roadmap.

The controlling documents remain:

1. [North Star](../../NORTH_STAR.md)
2. [Product Vision](../product/PRODUCT_VISION.md)
3. [Application Semantics](../product/APPLICATION_SEMANTICS.md)
4. [MVP](../product/MVP.md)
5. [Current State](CURRENT_STATE.md)

## System Shape

Cloud Chamber is a local-first React/Vite application backed by FastAPI and an
external CM1 installation:

```text
React / TypeScript / Vite
          |
          v
FastAPI World, run, result, and visualization APIs
          |
          +--> local runtime metadata and retained presentation inventory
          |
          +--> backend NetCDF readers and derived scientific payloads
          |
          +--> generated packages, queue, and external cm1.exe
```

The browser does not parse raw NetCDF. The backend owns native-file access,
validation, cropping, slicing, point selection, derived values, and payload
bounds.

## Product Routes

The frontend is a state-driven React application under `app/frontend`. Its
primary product routes resolve these locations:

```text
Cloud Worlds home
World overview and section
Trade Cumulus Explore and featured Comparison
Mountain Waves World and Explore
Supercells World and Explore
```

The Cloud Worlds home obtains inventory from `GET /api/worlds`. World-specific
inventory endpoints provide stable content identity and availability:

```text
GET /api/worlds/trade-cumulus
GET /api/worlds/mountain-waves
GET /api/worlds/supercells
```

Fun With Soundings does not yet have a first-class product route.

Legacy Build, Results, generic Explore, scenario, sounding, run, and result
paths remain in the application. The current World home can fall back to those
legacy surfaces when World inventory cannot load, and Trade Cumulus Lab embeds
some of them. This is transitional compatibility, not the intended final
navigation model.

## World and Simulation Identity

World and Simulation identity is owned by backend inventory code, separate from
runtime artifacts:

```text
stable World ID
  -> stable Simulation ID
     -> current retained run/result identity
        -> local run directory and NetCDF histories
```

Trade Cumulus, Mountain Waves, and Supercells each have explicit inventory and
availability logic. A built-in Simulation is available only when its expected
artifacts, lineage, geometry, fields, and time inventory satisfy that World's
contract. Invalid or conflicting content is reported rather than replaced with
an arbitrary compatible-looking run.

World responses are kept lightweight. Deep validation is performed at
promotion or discovery boundaries and cached against artifact fingerprints
where implemented, rather than reopening every history during ordinary World
polling.

## Explore Architecture

The Explore implementations reuse common application vocabulary but adapt to
different native data geometry.

### Trade Cumulus

Trade Cumulus coordinates a direct Three.js cloud-point view with native scalar
slices, an Updraft Lens, Context, controls, and a timeline. Its visualization
APIs provide:

- field catalogs and defaults;
- bounded three-dimensional point clouds;
- native horizontal and vertical slices;
- Updraft Lens frames and fixed defaults;
- wind vectors and selected-point evidence.

Point budgets and rendering levels of detail keep large retained runs usable.
Playback waits for coordinated payloads and rejects stale responses so rapid
time changes do not build an unbounded request backlog.

### Mountain Waves

Mountain Waves output is native x-z with singleton y. Its Explore path returns
terrain-aware two-dimensional frames rather than extruding the data into a fake
three-dimensional field:

```text
GET /api/worlds/mountain-waves/simulations/{simulation_id}/frame
```

The backend owns native geometry, terrain, field extraction, overlay evidence,
fixed Simulation scales, and point evidence. Expanded-height and
true-physical-scale display modes are frontend geometry choices over the same
physical coordinates.

Run metadata, times, geometry, and fixed scales are cached by artifact
fingerprint. After validation, a frame request reads the selected history
rather than traversing the complete time series.

### Supercells

Supercells Explore coordinates:

- a bounded three-dimensional storm payload;
- native x-y, x-z, and y-z sections;
- World-specific Lens payloads and overlays;
- one shared time, camera, orientation, and slice-position state;
- selected-point evidence and Context.

Frames are served through:

```text
GET /api/worlds/supercells/simulations/{simulation_id}/frame
```

The backend caches validated run inventory using artifact fingerprints. A
selected frame opens its corresponding history only. The frontend keeps a
small frame cache and prefetches adjacent frames for playback.

### Shared information architecture

All three Explore implementations compose the shared
`IntegratedExploreWorkspace`, `ExploreInspector`, `ExploreContextContent`,
`ExploreSelectedEvidence`, and `ExploreSecondarySections` contracts.

The shared structure is:

```text
coordinated scientific viewer(s) + controls + timeline + collapsible Context

Science | Notes | Details
```

Context owns concise current-view explanation and immediate selected-point
evidence. Science owns World-specific retained-history evidence, Notes owns
user-authored per-Simulation content, and Details owns technical and provenance
information. World-specific geometry and science remain in their World
components rather than being forced through one generic renderer.

## Scientific Payload Rules

Explore payloads preserve several implementation boundaries:

- native coordinates remain authoritative;
- user-visible units are explicit and may be converted only at the display
  boundary;
- fixed scale identities and ranges belong to the World or Simulation and do
  not autoscale independently at each frame;
- slices are extracted on native planes;
- crops reduce the domain without inventing coordinates;
- three-dimensional payloads use declared point budgets and levels of detail;
- cloud points represent cloudy native cells, not droplets or synthetic
  particles;
- derived contours, boundaries, vectors, and state labels identify their
  source fields and thresholds;
- selected-point values come from native or explicitly derived data.

Browser views are therefore bounded interpretations of CM1-derived output, not
raw model files.

## Timeline and Frame Loading

All three product Explore paths expose saved model outputs on a persistent
timeline with previous, play or pause, next, slider, and speed controls.

Fixed scales and static geometry are computed once per validated retained run
or cached against its fingerprint. Frame-specific APIs then return only the
requested time's bounded scientific payloads. Frontend request coordination
prevents stale frames from replacing newer selections. Supercells additionally
keeps a bounded client frame cache and adjacent-frame prefetch.

The implementations are not yet one shared playback engine, but the product
behavior and visual grammar are aligned.

## State Distinctions

The current code keeps these states distinct:

| State | Current meaning |
| --- | --- |
| Stable World or Simulation identity | Product-owned identity independent of a current run |
| Configured package | CM1-facing inputs exist, but no CM1 output is implied |
| Queued or running process | An external CM1 execution is waiting or active |
| Completed process | CM1 exited; scientific output may still be missing or invalid |
| Completed output | Expected output artifacts exist |
| Runtime-integrity assessment | Backend trust state based on runtime and field evidence |
| Promoted retained Simulation | Validated output is bound to a stable Simulation identity |
| Ingested result metadata | Backend-created metadata exists beside a run |
| Editable result sidecar | Optional local name, tag, or note state exists |
| Backend-derived diagnostic | A quantity was calculated from CM1-derived data |
| Visualization interpretation | A bounded browser payload or Lens represents available evidence |

Process success, output existence, promotion, ingest, integrity, and browser
visibility are separate facts.

## Run and Result Runtime

CM1 remains external to the repository. Package generation writes reviewable
inputs and manifests under:

```text
<runtime-home>/runs/<run-id>/
```

The local run manager launches the configured `cm1.exe`, records process and
log state, and inventories output. The serial queue runs one local process at a
time and can ingest successful output-producing runs. A bounded trusted-LAN
path can execute a copied package while the primary Cloud Chamber host remains
the system of record.

Result ingest writes `result_metadata.json` inside the original run directory.
Editable name, tags, and notes may be stored in a sibling `result_card.json`.
Deleting that run directory can remove the package, logs, NetCDF output, result
metadata, and notebook state together.

See [Ingest, Results, and Runtime Cleanup Lifecycle](INGEST_RESULTS_STORAGE_LIFECYCLE.md).

## Persistence and Asset Boundaries

The runtime home defaults to `~/CloudChamber` and stores:

- settings and CM1 discovery;
- generated packages and manifests;
- local NetCDF histories;
- queue and process state;
- logs;
- sounding caches;
- retained presentation-run assets;
- result metadata and editable result sidecars;
- per-Simulation notes keyed by stable World and Simulation identity;
- validation and derived caches.

Large CM1 histories and generated visualization artifacts are not stored in
Git. Built-in World content therefore depends on local retained assets being
present and valid.

Per-Simulation Notes are the first bounded durable product-content contract:

```text
GET /api/worlds/{world_id}/simulations/{simulation_id}/note
PUT /api/worlds/{world_id}/simulations/{simulation_id}/note

<runtime-home>/simulation-notes/<world_id>/<simulation_id>.json
```

The backend validates stable identities and bounded text, and writes updates
atomically through a temporary file, filesystem synchronization, and replace.
Blank content clears the note. Read and write failures stay local to Notes and
are reported in the interface. Notes do not become run identity, result
metadata, or a general annotation model.

Saved Views and complete Explore workspace state are not durably persisted.
The only product Comparison currently exposed is the featured Trade Cumulus
pair. World-aware variation exists for Mountain Waves but is not yet one shared
cross-World system.

## Product and Research Boundaries

Product World APIs live under `/api/worlds/...`. Research endpoints such as
`/api/research/mountain-wave-terrain` and
`/api/research/storm-examination` remain separate evidence and validation
surfaces.

Research pages may prove geometry, fields, or scientific encodings that later
support product work. Their routes, temporary controls, and one-off narrative
do not become product architecture merely because the underlying science is
reused.

## Current Architectural Limits

- World shells and Explore implementations share vocabulary but still contain
  World-specific state and rendering code.
- Durable Saved Views and general World-aware Compare are absent.
- Variation is implemented only for Mountain Waves.
- Legacy run, result, and sounding surfaces remain interleaved with the newer
  World application.
- Filesystem-backed runtime metadata is local and not a durable multi-device
  store.

These are implementation facts, not decisions to narrow the approved product.
