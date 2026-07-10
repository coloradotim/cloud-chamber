# Cloud Chamber Architecture And Data Model

## Architecture Overview

Cloud Chamber should be local-first.

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local
experiment builder, run manager, result notebook, diagnostics layer, and
visualizer.

The current user-facing architecture is:

```text
Build = configure and launch one CM1 run
Results = notebook for completed/ingested runs
Explore = inspect one result with CM1-derived evidence
```

Runtime inventory and cleanup are not a separate top-level workspace. Build owns
active, incomplete, and non-ingested package/run work; Results owns ingested
notebook entries and explicit ingested-result cleanup.

Observed-sounding presets seed a CM1-facing configuration, but they should not
be modeled as rigid product cages. The data model may keep internal
`package_family` values where they preserve compatibility, while the product
model treats those values as implementation/provenance metadata beneath a
configurable run builder.

The first MVP target is a 2024 MacBook Air with 8GB RAM. Design for one local CM1 run at a time, conservative output handling, and backend-side processing/downsampling. Optional cloud compute can be researched later, but it is not part of the core architecture.

Replay / inspect / save is core MVP. Duplicate / tweak / rerun is later and should not drive the first result storage model.

Active sequencing lives in [Current Roadmap](current-roadmap.md). Historical
issue sequencing in the archived roadmap should not drive new architecture
decisions.

Recommended architecture:

```text
Frontend UI
  ↓
Local app/server API
  ↓
Scenario/config generator
  ↓
Run manager
  ↓
CM1 process
  ↓
Output watcher / ingester
  ↓
Local result store
  ↓
Thermal Fate diagnostics
  ↓
3-D visualizer
```

The Thermal Fate diagnostics layer sits between ingest/result metadata and
visualization. It should distinguish global run diagnostics, local
selected-region diagnostics, comparison diagnostics, and visualizer
interpretation. The browser should continue to receive bounded summaries,
visualization-ready slices/points, and provenance labels rather than raw NetCDF.
Explore's Thermal Fate Inspector follows that boundary: slice-cell or bounded
region selections are sent to the backend selected-region diagnostics endpoint,
and the frontend renders only the returned local summaries, conservative label,
confidence, caveats, selected native-grid bounds, domain comparison, and
provenance.

The [Cloud Chamber output product specification](contracts/output-product-specification.md)
defines the next data-contract layer between raw CM1 NetCDF output, result
metadata, derived scientific products, visualization-ready payloads, future
render-ready products, and external export bundles. Future backend ingest,
Results, Explore, runtime cleanup, Diagnostics Lab, and Render Studio work should use
that contract instead of inventing ad hoc output discovery or browser-side
NetCDF parsing.

The [Cloud Chamber realistic LES input specification](contracts/realistic-les-input-specification.md)
defines the input-side contract before realistic sounding, place/time,
radiation, surface, terrain/GIS, compute-tier, or Bench Mode work. Future
package-generation changes should preserve observed sounding metadata,
place/time/source provenance, conversion choices, and caveats before exposing
new product controls.

The v1 observed-sounding implementation is a local upload path for extracted
NOAA/NCEI IGRA station sounding-data text files. The backend owns parsing,
validation, unit conversion, vertical-datum handling, and CM1 `input_sounding`
rendering. The frontend sends uploaded text to the backend, receives a bounded
review payload, and passes the selected sounding record into dry-run package
generation; it does not parse sounding files into CM1-ready data itself.

The IGRA recent catalog/cache layer is separate from package generation. The
backend can refresh the NOAA/NCEI IGRA recent station-period directory, parse
station metadata, filter to the v1 Great Plains / Midwest region bounds
(`35.0` to `50.0` latitude, `-106.0` to `-82.0` longitude), and cache selected
or batched station-period ZIP/text files under
`<runtime-home>/cache/igra/recent/`. Runtime cache metadata is stored in
`catalog.json` and `cache_manifest.json`; downloaded ZIPs and extracted station
text stay under per-station cache directories. The command-line cache surface
can also summarize available sounding times from cached station text. The browser
does not parse remote HTML, station archives, or station text files.
When cached station metadata is available, the observed-sounding parser can use
it for station name, location, and elevation instead of relying only on built-in
fixture metadata.

The sounding-candidate screening and analysis layer consumes only cached station
text plus cache metadata. It reuses the canonical observed-sounding parser,
computes transparent low-order features such as low-level moisture, estimated
LCL, low-level lapse-rate, inversion/cap proxy, moisture depth, profile
coverage, observed-wind availability, bulk-shear proxies when winds exist,
dry-layer/inverted-V proxies, and freezing-level context, and emits pre-run
story-specific candidate matches. Stable story identifiers are
`shallow_cumulus_candidate`, `dry_failed_candidate`,
`capped_suppressed_candidate`, `humid_rainy_candidate`, `needs_review`, and
`poor_or_incomplete_candidate`; severe/deep-convection story identifiers remain
pre-run hypotheses for Deep Convection Trial routing. The auditable scoring
contract lives in
[contracts/sounding-candidate-screening.md](contracts/sounding-candidate-screening.md).
Analysis can target story, story family, support state, package readiness,
station search, and backend-owned sort keys because the useful sounding depends
on the experiment question; a shallow-cumulus search and a humid/rainy search
should not imply the same ranked list. Missing feature values stay unavailable
and sort last instead of being treated as zero. Saved candidates and working-set
tags are runtime-local cache state under
`<runtime-home>/cache/sounding-candidates/`; they are not Result Cards and are
not committed. When a saved candidate is used to generate a package, its
screening summary may be copied into
`run_manifest.json`, `case_manifest.json`, and `dry_run_report.json` as
provenance. The screening score remains a candidate-selection aid; CM1 output
remains the source of truth.

The sounding-diagnostics layer is a backend-only feature extractor for observed
soundings. It produces bounded `SoundingDiagnostics` payloads with
`diagnostic_version`, station/time provenance, `feature_values`,
`unavailable_features`, data-quality summaries, assumptions, and caveats. Each
feature records its key, label, value, units, support state, method,
assumptions, and caveats so missing data weakens or blocks evidence instead of
being treated as physically meaningful. V1 supports profile quality,
cloud-base/moisture proxies, low-level and midlevel lapse-rate proxies,
inversion/cap proxies, bulk-shear and mean-wind diagnostics when observed winds
exist, dry-layer/microburst/freezing-level proxies, and explicit unavailable
states for unimplemented parcel, storm-relative, wet-bulb, and winter-phase
diagnostics. The browser should consume these diagnostics only through bounded
backend JSON; it must not parse station text or compute CAPE/CIN/SRH locally.

Sounding story families are architecture planning input until a backend
screening and package-readiness path supports them. The expanded taxonomy in
[research/expanded-sounding-candidate-taxonomy.md](research/expanded-sounding-candidate-taxonomy.md)
defines readiness states for severe/deep-convection, boundary-layer, low-cloud,
and winter/cold-season stories so APIs can distinguish screenable environments
from runnable configuration paths. Until a story has backend features, scoring
tests, evidence, caveats, and package-readiness support, it must not be emitted
as an enabled package-ready label. The first implemented severe/deep-convection
path is the deep-convection observed-sounding preset, backed internally by
`package_family = deep_convection_trial`, which treats selected observed
soundings as pre-run hypotheses for an idealized triggered CM1 experiment.

The Build UI consumes this layer through bounded JSON only. `Upload a Sounding`
loads saved candidates immediately when that experiment is selected, before any
catalog refresh or analysis action. It can also call the recent-catalog/cache
and candidate-analysis endpoints, display the backend-filtered candidate list,
save candidates into working-set tags, and pass a selected candidate's
`selected_sounding_payload` into the existing observed-sounding package review.
The frontend does not read cached station text directly, compute the story
scores, or sort raw feature values itself. Candidate status is separate from
run/result status: saved candidates are pre-run hypotheses, while generated
packages, launched runs, and ingested results remain separate lifecycle objects.

Deep-convection observed-sounding packages extend the same dry-run package
contract rather than creating a separate workflow. The package records
`package_family = deep_convection_trial`, a deep-convection display label,
`input_source = observed_sounding`, `trigger_type = warm_bubble`, trigger
metadata, expected output fields, package-family smoke validation status,
package caveats, and any candidate-screening payload on the run manifest, case
manifest, and dry-run report. The generated namelist uses the observed
`input_sounding` route (`isnd = 7`), requires complete usable observed u/v winds,
selects CM1's built-in three-warm-bubble initialization (`iinit = 3`) with
`testcase = 0`, uses a storm-scale idealized domain for storm growth, and
enables rain-water-aloft, surface-rain, reflectivity, vorticity, and
updraft-helicity output. Manual smoke evidence applies to the package path and
basic run/ingest health; each observed sounding remains an experiment whose
outcome must be inspected after CM1 completes. The trigger is described as
fixed v1 package metadata rather than a primary product control. Ingest copies
the package-family and trigger metadata into result metadata and Result Cards so
Results and Explore do not lose the distinction between an observed-sounding
quick look and a deep-convection configured run.

## Suggested Stack

This is not final, but a reasonable starting point:

### Frontend

- React + TypeScript
- Vite or Next.js local app
- Three.js / React Three Fiber for 3-D visualizer later
- Zustand or similar small state store

### Local Backend

Options:

1. Python FastAPI local server
2. Node/Electron/Tauri local app shell
3. Hybrid: Python backend for CM1/run/data handling + React frontend

Recommendation:

Start with **Python FastAPI + React/Vite**.

Reason:

- Python is better for NetCDF/xarray preprocessing.
- React is good for UI/visualization.
- Local server avoids browser filesystem limitations.
- Use `uv` for Python dependency/project workflows when backend implementation expands.

Later, package with Tauri/Electron if needed.

## Major Components

### Scenario Catalog

Stores scenario definitions, starting presets, and run-configuration defaults.

Responsibilities:

- list scenarios
- expose controls
- map friendly controls to CM1 configuration
- define expected outputs
- define visualization defaults
- define run-configuration presets as editable starting points
- define recommended story threads or comparison patterns around a baseline
- define the physical question and learning goals

Baseline Shallow Cumulus is the first hero case. Warm rain remains early but does not block the Golden Path.

Scenario templates are validated before package generation. The schema supports
stable IDs, display names, descriptions, physical questions, learning goals,
friendly controls, advanced/developer-only settings, run-configuration defaults,
optional starting presets, expected diagnostics, CM1 mapping notes,
visualization defaults, warnings, limitations, and validation policy. Invalid
templates should fail with actionable validation messages before any CM1-facing
files are generated.

The local FastAPI backend exposes the implemented catalog through `GET /api/scenarios`. The response should include the Golden Path scenario ID and product-facing scenario summaries only; advanced/developer controls can remain in the template but should not appear in the primary Scenario Builder flow.

### Configuration Builder

Turns a scenario + user controls into:

- `namelist.input`
- `input_sounding`
- `case_manifest.json`
- run manifest
- dry-run report
- visualization defaults

For the Baseline Shallow Cumulus Golden Path, the generated package should preserve the physical question, curated controls, selected run configuration or legacy preset, expected diagnostics, expected output fields, and provenance labels before CM1 starts.

The CM1 input generation contract is deterministic and testable before full package generation. It documents the expected generated files and preserves product-facing controls separately from raw namelist/developer settings.

For Baseline Shallow Cumulus, the recovery package is derived from CM1's local `les_ShallowCu` reference case. It preserves `testcase = 3`, the reference grid, runtime, domain top, Rayleigh damping, surface/ocean/flux settings, surface stress path, and wind profile as much as possible. The external-sounding reproduction changes the thermodynamic source from the built-in BOMEX analytic sounding (`isnd = 19`) to CM1's `input_sounding` route (`isnd = 17`) so the current moisture-contrast scaffold has a validated profile path. The intentional Cloud Chamber output-path change remains NetCDF output (`output_format = 2`) so the completed run can flow into ingest and diagnostics.

The earlier Cloud Chamber quick-look derivative is not scientifically accepted: full-sequence ingest evaluated all 25 model-output files, but the run produced no cloud, no vertical motion, and NaN/Infinity caveats; a fixed-roughness follow-up still failed in the same way. Quick-look scaling should happen only after the reference-derived package works, and future changes should be introduced one at a time with manual CM1 validation.

The first reference-derived validation run, `dry-run-les-shallowcu-20260522140642`, completed locally with NetCDF output and ingested 7 model-output time steps over 21600 seconds. It produced cloud water and vertical velocity diagnostics, so the architecture should treat the reference-derived package as the recovery baseline and the earlier compact derivative as invalid evidence rather than a tuning base.

Current legacy run-size presets are generated package promises for the existing
baseline/scaffold implementation, not the future architecture. The
standard/reference package preserves `timax = 21600.0`, `tapfrq = 3600.0`, and
the 64 x 64 x 75 / 100 m horizontal grid. The first quick-look variant
preserves every reference-derived science/numerics setting and changes only
`timax = 10800.0` and `tapfrq = 900.0`. The Deep Overnight variant is the
expensive opt-in preset: it preserves the physical 6.4 km x 6.4 km domain and
the accepted scenario controls, but increases horizontal resolution to 192 x
192 at about 33.333 m, saves output every 300 s, and keeps the Standard solver
timestep. Vertical spacing, domain top, surface stress/roughness path,
moisture/sounding, surface fluxes, turbulence/SGS settings, damping settings,
boundary conditions, NetCDF output, and reference `LANDUSE.TBL` staging should
remain unchanged for that historical/current implementation path.

Forward observed-sounding run configuration should use guarded fields for
duration, grid/detail, domain size, output cadence, output field density,
forcing, requested fields, advanced CM1-facing values, and a pre-run validation
report. Raw numerical timestep is not a normal v1 control. Presets should seed
those fields and expose their derived CM1-facing values in advanced metadata so
dry-run reports and Build UI can show exactly what will be written without
requiring raw namelist editing.

The first quick-look validation run, `dry-run-quicklook-les-shallowcu-20260522151536`, preserved those settings, completed locally, and ingested 13 model-output time steps over 10800 seconds. Diagnostics still reported cloud formation, vertical motion, and rain, so the architecture can treat this runtime-only quick-look preset as the first validated shorter Baseline Shallow Cumulus variant.

The external-sounding reproduction run, `dry-run-external-sounding-baseline-20260522185000`,
preserved the same quick-look timing and used `isnd = 17` with a generated
numeric `input_sounding`. It completed locally, produced NetCDF, ingested 13
model-output time steps over 10800 seconds, and retained cloud formation,
vertical motion, and rain. The architecture can now treat external-sounding
Baseline Shallow Cumulus as the accepted profile path for one-factor moisture
experiments.

Observed IGRA packages reuse that accepted external-sounding route. The
observed record is stored with package metadata and includes station id/name,
latitude/longitude/elevation when known, selected valid time, uploaded
filename, source provider/format, source units, converted CM1 units,
model-bottom elevation above mean sea level, levels relative to the station
surface, validation status, and caveats. For v1, the thermodynamic, moisture,
and wind profile is generated into `input_sounding`: observed wind
direction/speed is converted to CM1 `u`/`v`, and observed-sounding packages use
CM1's `isnd = 7` mode so those wind columns initialize the run. Missing station
elevation, profiles that do not cover the model depth, or incomplete observed
wind profiles must block package generation or surface an explicit
`needs_review` caveat instead of silently normalizing to sea level or falling
back to reference winds.

Dry Failed Cumulus should branch from this validated reference-derived family,
not from the invalid compact quick-look derivative. Architecturally, it is a
moisture-limited contrast case: preserve the validated grid/domain, surface
forcing, stress/roughness path, damping, turbulence/SGS settings, boundary
conditions, NetCDF output, runtime-file staging, and quick-look timing, then
change only the lower-atmosphere moisture/sounding path once that path has been
validated. The intended product control is `low-level humidity = drier`; raw
sounding or namelist edits belong in developer implementation details.

Because the accepted baseline originally relied on the CM1 `les_ShallowCu`
built-in sounding behavior, Cloud Chamber must preserve evidence for the
external `input_sounding` reproduction before drying the profile. Only after
that reproduction succeeds should Dry Failed reduce low-level moisture. A run
with no cloud and no meaningful vertical motion, or no cloud with severe
NaN/Infinity caveats, is not a valid Dry Failed Cumulus result.

The first accepted Dry Failed implementation uses the same generated namelist as
the accepted external-sounding baseline and changes only the generated
lower-atmosphere moisture profile for `low_level_humidity = drier`. Validation
run `dry-run-dry-failed-cumulus-20260522192000` completed locally, produced
NetCDF, ingested 13 model-output time steps, and produced no cloud/rain while
retaining meaningful vertical motion. This establishes the first two-outcome
lab pair: Baseline forms cloud; Dry Failed has thermals without meaningful
cloud water.

Baseline humidity ladder variants reuse the accepted external-sounding
Baseline Shallow Cumulus namelist family. The package generator records the
selected `low_level_humidity` control and a moisture-profile variant, then
changes only the generated `input_sounding` moisture values for `drier` or
`more_humid`. The namelist, runtime preset, NetCDF output, and runtime-file
staging remain the same for the selected preset.

Capped / Suppressed Cumulus also branches from the accepted external-sounding
Baseline Shallow Cumulus family, but it is not a moisture experiment. The first
implementation (#140) preserves the accepted baseline grid/domain, vertical
spacing, domain top, runtime/cadence model, surface/ocean/flux settings,
surface stress/roughness path, Rayleigh damping, turbulence/SGS settings,
boundary conditions, NetCDF output, `LANDUSE.TBL` staging, low-level humidity,
surface heating, and the baseline wind profile. It changes only the
potential-temperature / stability structure near the capping layer in the
generated external `input_sounding`.

Architecturally, the product control is `cap_strength = stronger`. Cap height
stays at the accepted baseline for the first implementation; lower cap height
is later work. The scenario does not reuse the invalid compact quick-look
derivative, does not dry the low-level moisture profile, and does not vary
surface heating. The package contract records the selected `cap_strength` and
`stability_profile = stronger_cap` while preserving the baseline moisture
profile. Its result-card interpretation should use cap-limited candidate
language unless current diagnostics directly support a stronger process claim.

The first stronger-cap validation run,
`dry-run-capped-suppressed-20260526015634`, completed and ingested with 13
model-output time steps. It reduced cloud top, max `qc`, cloud fraction, max/min
`w`, and max `qr` relative to the accepted external-sounding baseline while
still producing rain. That is enough to treat it as an accepted-with-notes
cap/stability contrast candidate, not enough to claim rain suppression or a
fully diagnosed cap-limitation mechanism.

Current lower-atmosphere scaffold defaults are historical/current
implementation evidence:

```text
domain/grid: 64 x 64 x 75
horizontal spacing: 100 m
nominal vertical spacing: 40 m
domain top: 18000 m
runtime: 21600 s
output cadence: 3600 s
```

Baseline Shallow Cumulus quick-look timing:

```text
runtime: 10800 s
output cadence: 900 s
unchanged: reference-derived grid/domain/surface/damping/boundary settings
```

Configuration-specific deviations from these defaults must be explicit in the
scenario template, generated report, or pre-run validation report.

Dry-run package generation uses the validated scenario template and CM1 input contract to create a reviewable package under the configured runtime home, normally `~/CloudChamber/runs/<run-id>/`. The package writer should refuse to overwrite existing run directories, validate controls before writing, and produce only package inputs/reports, not CM1 output.

The implemented dry-run API is `POST /api/dry-run-package`. It currently accepts
scenario ID, selected product controls, and a legacy run-size preset, then
returns the package paths and dry-run report summary for UI review. The forward
API should accept a selected run configuration with optional preset provenance.
It must not launch CM1, write NetCDF, or place generated packages inside the
source tree during tests.

The Build workspace is the first guided app-side launchpad over the existing
backend contracts:

```text
POST /api/dry-run-package
-> POST /api/runs/queue
-> GET /api/runs/queue
-> GET /api/runs/status?manifest_path=...
-> POST /api/results/ingest
-> GET /api/results
```

The browser receives only API summaries: run/package paths, lifecycle/product
states, stdout/stderr log paths and short tails, output artifact counts, runtime
warnings, storage inventory entries, progress metadata, associated result-card
identities when available, and the ingested result ID. Progress metadata is a
bounded status summary: elapsed wall time from manifest execution timestamps,
total configured model time from `namelist.input` `timax` with package-preset
fallback, latest model time from CM1 stdout model-minute progress lines when
available, percent/ETA only when those inputs are present, and clear unavailable
copy otherwise. It does not read local files directly, does not parse NetCDF in
the browser, and does not imply that a dry-run package is already a completed or
ingested result.

Build is intentionally not modeled as one single active package. Local runtime
state can contain multiple package/run folders in different lifecycle stages:
packaged-only, running, completed with output, completed without usable output,
failed, ingested, legacy saved/protected metadata, or missing/malformed manifest.
Build shows only active or incomplete package/run work that still needs launch,
status review, troubleshooting, or ingest. Fully ingested results belong in
Results. The launchpad uses the runtime storage inventory to show
eligible states and offers only safe state-appropriate transitions:

- create a new package through `POST /api/dry-run-package`;
- queue an eligible packaged run through `POST /api/runs/queue`;
- refresh and advance the serial local queue through `GET /api/runs/queue`;
- refresh current status through `GET /api/runs/status`;
- ingest completed output through `POST /api/results/ingest`;
- open associated results in Results or Explore;
- preview and confirm cleanup for non-ingested package/run directories.

The local serial queue is persisted under the configured runtime home, outside
the repo. It may contain several packaged runs, but it must launch only one
local CM1 process at a time. Queue refresh is intentionally stateful: it checks
the active run, records terminal status, auto-ingests completed NetCDF-producing
runs when ingest succeeds, and then starts the next queued package. If ingest
fails, output is left in place and manual retry remains available. After
successful auto-ingest, the queue entry is finalized, but the Mac-local run
directory is retained because it backs Results and Explore; destructive cleanup
still belongs to the explicit Results cleanup flow.

Runtime status refresh may reconcile a stale local manifest only when stdout
contains normal CM1 termination evidence and output artifacts exist under the
run directory. This repairs backend-restart cases where a completed local run
was still labeled running, while avoiding silent completion claims for unknown
or still-active runs.

LAN worker status follows the same bounded progress contract when the worker
status refresh can inspect remote `namelist.input` and `logs/stdout.log`. Older
or just-started worker sidecars may have no progress payload; Build should show
model-time progress as unavailable rather than infer it from raw counts.

Results owns cleanup for ingested results. It resolves the selected result to
its managed run directory, previews user-facing cleanup categories, and requires
explicit confirmation before deleting the result and local run data. Non-ingested
run-directory cleanup stays in Build. Running or otherwise unsafe runs remain
blocked by backend storage safety checks.

### Preview Engine

Fast reduced/light predictor.

Responsibilities:

- estimate likely cloud/no-cloud behavior
- estimate LCL/cloud base trend
- warn about cap/moisture/dry-air constraints
- label as preview only

This is not the truth source.

### Run Manager

Responsibilities:

- create run directory
- copy CM1 runtime files
- launch CM1 process
- capture stdout/stderr
- track status
- detect completion/failure
- expose logs
- prevent accidental overwrite

The first implemented local run manager is intentionally conservative:

- one local CM1 process may be active at a time;
- launch requires valid local CM1 settings and a generated `run_manifest.json`;
- command construction points at the configured local `cm1.exe`;
- stdout and stderr are written into the run package `logs/` directory for later result notebook provenance;
- lifecycle states move through queued, running, completed, failed, or canceled;
- launch refuses packages that already contain output-like files such as NetCDF,
  `cm1out_*.dat`, or `cm1out_*.ctl`;
- launch refuses placeholder-only `namelist.input` or notes-only `input_sounding` files;
- launch rejects Rayleigh damping settings that start too low and would damp more than half the vertical domain;
- launch stages required local runtime files such as `LANDUSE.TBL` from the configured CM1 run directory into the generated package directory;
- process exit code 0 is not enough to mark a usable completed CM1 result; NetCDF or raw CM1 `.dat/.ctl` output artifacts must exist before `completed_cm1_result` is used;
- status responses expose enough UI-safe metadata for the guided app flow: lifecycle/product/validation state, command/log paths, short stdout/stderr tails, output-artifact counts, runtime warnings, and timestamps;
- tests inject fake subprocesses, so CI never needs a real CM1 executable.

Real CM1 execution remains a manual/local responsibility until the user has local settings and runtime files in place. The manager must fail clearly when CM1 paths are missing rather than pretending a run started. If the process exits successfully but no NetCDF or raw CM1 `.dat/.ctl` output exists, the manifest remains `completed` at the process level but uses `validation_status: needs_review` and `product_state: process_completed_no_output`.

The first successful Baseline Shallow Cumulus smoke run produced GrADS/direct-access CM1 artifacts (`cm1out_*.dat` plus `.ctl` descriptors) rather than NetCDF. That proves local execution but is not full ingest. The manifest should catalog those raw artifacts separately from NetCDF paths and processed visualization artifacts. Floating-point exception flags reported in stderr should be surfaced as runtime warnings/caveats, not automatically treated as launch failure.

### Runtime Storage Inventory And Cleanup

Cloud Chamber runtime cleanup operates only under the configured runtime home, normally `~/CloudChamber`. The backend storage service inventories `~/CloudChamber/runs/<run-id>/` directories, reads `run_manifest.json` when available, reports total runtime-home size, the 50 GB MVP warning threshold, whether the runtime home is above that threshold, per-run size, lifecycle/provenance metadata, output artifact counts, and conservative categories:

```text
dry_run_only
running
completed_with_output
completed_no_output
failed
canceled
saved_or_protected
missing_manifest
malformed_manifest
unknown
```

Malformed or missing manifests are reported without crashing inventory. Largest runs are surfaced by size so the user can see what is consuming disk.

The 50 GB warning threshold is a configurable product default, not a scientific limit. Crossing the threshold should point the user to the largest-run inventory and safe cleanup actions. It must not trigger automatic deletion.

Deletion is explicit and scoped to one selected run directory. The cleanup service refuses path traversal, symlink escapes, the runtime home itself, the user's home directory, the source repo by construction, configured CM1 root/run paths, and running runs. Legacy saved/protected metadata no longer blocks an explicit delete after preview and confirmation. A dry-run delete returns the selected path and estimated size reclaimed without deleting files; a real delete requires explicit confirmation.

Deleting a run removes local generated CM1 inputs, copied runtime files, logs, raw CM1 output, NetCDF output, processed artifacts, and any local metadata stored inside that run directory. It does not delete repo files or the external CM1 installation.

The current code-backed lifecycle contract is documented in [Ingest, Results,
And Runtime Cleanup Lifecycle Audit](ingest-results-storage-lifecycle.md). As of
that audit, `result_metadata.json` and `result_card.json` live inside the
selected run directory, so deleting the whole directory also removes the
implemented Result/Explore record. Results makes that consequence explicit
before confirmation instead of treating legacy saved/protected flags as the
primary product model.

### Output Ingester

Responsibilities:

- inspect preferred NetCDF outputs
- catalog raw CM1 `.dat/.ctl` artifacts until NetCDF ingest is verified
- extract NetCDF metadata and fields
- produce app-friendly artifacts
- compute diagnostics
- create thumbnails/previews
- record provenance

The first implemented ingest step creates `result_metadata.json` in the completed run directory. It reads NetCDF with xarray and records result ID, run ID, scenario, physical question, controls, selected run configuration or legacy run-size preset, source lifecycle/product/provenance state, raw CM1 artifacts, NetCDF paths, processed artifact placeholders, dimensions, coordinates, variables, units, time coordinate, grid shape, warnings, and timestamps.

The next implemented step attaches first-pass diagnostics to that result metadata.
Diagnostics read NetCDF fields through the backend and summarize `qc`, `w`,
optional `qr` rain water aloft, optional surface `rain`, and optional `dbz`
reflectivity without parsing raw `.dat/.ctl` artifacts. Raw `.dat/.ctl`
artifacts remain cataloged on the run metadata but are not parsed as ingest
input.

CM1 may write a completed run as a sequence of NetCDF model-output files such
as `cm1out_000001.nc` through `cm1out_000025.nc`. Cloud Chamber must ingest the
model-field sequence, not just the first NetCDF file, before making cloud,
rain-water, surface-rain, or reflectivity statements. Stats files such as
`cm1out_stats.nc` are NetCDF artifacts but are not model-field time-series
inputs for `qc`, `w`, `qr`, surface `rain`, or `dbz` diagnostics.

Result metadata records model-output paths separately from stats NetCDF paths, skipped/corrupt files, contributing model-output file count, total time steps, first/last output time, and whether time came directly from a NetCDF coordinate or an inferred fallback.

Ingest also writes the first output-product summary fields into result
metadata: interesting-time records, per-field default time choices, a compact
science summary for Results filtering/sorting, and caveats from interesting-time
resolution. These fields are derived from CM1 diagnostics and the output-product
manifest time index. They do not replace raw NetCDF output, and they do not give
the browser permission to infer file/time mapping or parse NetCDF directly.
Result metadata also records the input source that created the run. Generated
reference scenarios use `input_source = generated_reference`; uploaded IGRA
packages use `input_source = observed_sounding` and preserve the selected
observed-sounding metadata, including station ID/name, elevation, valid time,
source format, and current caveats such as wind metadata that is not yet used by
CM1.

### Result Cards / Experiment Notebook Entries

The backend result-card layer is the product-facing view over ingested metadata.
It does not rerun CM1 and does not parse raw output directly. It summarizes:

- run ID, scenario, selected run configuration or legacy preset, and physical question;
- diagnostics summary, first cloud time, max `qc`, max/min `w`, rain water
  aloft, surface rain, reflectivity, and caveats;
- output file summary, including NetCDF/model-output/stat/raw/processed counts and time-step range;
- input source and observed-sounding metadata when the run came from an uploaded sounding;
- compact `science_summary`, `interesting_times`, and `default_time_by_field` values for Results filtering, sorting, and sensible Explore defaults;
- provenance labels that distinguish completed CM1 result, ingested metadata, and notebook entry;
- editable notebook fields: name, tags, and notes.

When a result came from an uploaded observed sounding, Result Cards use
`Uploaded Sounding` as the product-facing experiment identity and default
notebook name while preserving the underlying generated scenario ID as technical
lineage. Results filters treat uploaded-sounding results as their own
scenario-like product category so they do not collapse into the baseline
scenario bucket.

Editable notebook state is stored as `result_card.json` beside `result_metadata.json`.
Legacy `saved` and `protected` fields may remain in older `result_card.json`
files for compatibility, but they are not current user-facing Results modes.
CM1 output remains local/generated and uncommitted. See the lifecycle audit for
the current relationship between result metadata, notebook edits, and run
directory cleanup.

Current diagnostics compute:

- cloud formed yes/no using `qc >= 1e-6 kg/kg` and a minimum 10 cloudy grid-cell rule;
- first cloud time from the NetCDF time coordinate when available, otherwise inferred output index;
- first-pass cloud base/top from available vertical coordinates;
- max `qc`, time of max `qc`, `qc` max time series, cloud fraction time series, and cloud-present time steps;
- max/min `w`, time of max/min `w`, and `w` max/min time series;
- optional rain-water-aloft summary from `qr >= 1e-7 kg/kg`;
- optional surface-rain summary from the CM1 `rain` field;
- optional reflectivity summary from the CM1 `dbz` field.

Diagnostics preserve runtime warnings from the run manifest/result metadata. CM1 floating-point exception flags are caveats, not automatic failure. The diagnostics also count non-finite values in target fields where practical, ignore NaN/infinity for finite summaries, and record field-specific caveats if `qc`, `w`, `qr`, surface `rain`, or `dbz` are missing or entirely non-finite.

This result metadata is not a Result Card UI and not visualization-ready data. It is the backend bridge that later result cards and inspectors can consume.

### Thermal Fate Diagnostics

Thermal Fate diagnostics are the process layer between ingested result metadata
and visualization. They should answer what happened to thermals without making
unsupported claims.

The layer should distinguish:

```text
global run diagnostics
local selected-region diagnostics
comparison diagnostics
visualizer interpretation
```

Global diagnostics summarize the whole completed CM1 result. Local
selected-region diagnostics support the future `What happened here?` inspector
for points, columns, or boxes. Comparison diagnostics explain what changed
between saved results such as Baseline vs Dry Failed, Baseline vs Capped, and
future surface-heating or deep-breakthrough variants.

The data model should make room for process groups even before every group is
implemented:

```text
thermal_fate
cloud_lifecycle
updrafts
moisture_saturation
cap_inversion
buoyancy
deep_breakthrough
precipitation_feedback
local_region_support
interpretation_support
```

Deep-breakthrough and precipitation-feedback diagnostics should be represented
as unavailable, candidate, or supported states until required fields and
derived diagnostics exist. The browser should see bounded summaries and
visualization-ready payloads only; backend xarray/NetCDF code owns direct field
access, processing, and downsampling.

The first implemented process-diagnostics layer attaches `process_diagnostics`
to `result_metadata.json` during NetCDF ingest. It preserves the existing
cloud/rain/updraft diagnostics and adds conservative Thermal Fate interpretation
support:

- moisture-limited `Thermal without cloud` when meaningful `w` exists but `qc`
  stays below the cloud threshold;
- `Capped / suppressed cumulus` as a candidate when the scenario/control path is
  the stronger-cap case;
- `Growing cumulus` as a candidate when cloud-top time series rises;
- `Fair-weather cumulus` as a candidate for cloud-forming shallow cases without
  stronger process evidence;
- unavailable/caveated placeholders for buoyancy, deep breakthrough, and
  precipitation feedback until required fields and diagnostics exist.

Result cards expose the conservative `thermal_fate_label`,
`thermal_fate_confidence`, and `main_limiting_factor` fields without replacing
the existing cloud, rain-water, surface-rain, reflectivity, and updraft summary.

The selected-region diagnostics API builds on that global metadata for the
Thermal Fate Inspector. `GET /api/results/{result_id}/diagnostics/selected-region`
accepts a bounded native-grid point, column, or box request and returns:

- region bounds, native-grid coordinate metadata, and cell count;
- local max/min `w` time series and summary;
- local max `qc`, first local cloud time, cloud fraction, cloud base/top, and
  max-height time series;
- local `qr` rain-water onset and max rain-water-aloft summary when `qr` exists;
- comparison-to-domain ratios or time deltas where global diagnostics are
  available;
- a conservative local Thermal Fate label with confidence and caveats.

The endpoint returns summaries only. It does not return large raw arrays, does
not perform cloud-object tracking, and does not let the browser parse raw
NetCDF.

Explore process overlays consume the existing result-card process fields and
visualization-ready field/slice/point payloads. They should present supported
or candidate process modes when backend evidence exists and explicit
unavailable/caveated states when fields such as `qv`, buoyancy inputs,
CAPE/CIN/LFC/EL, or cold-pool diagnostics are absent. The frontend can select
process modes and display annotations, but it must not compute the scientific
classification itself or parse raw NetCDF.

### Result Library

Responsibilities:

- list runs/results
- rename/tag/annotate
- search/filter
- open visualizer
- duplicate setup
- delete local output safely

For MVP, replayable and inspectable ingested results with editable notebook fields are more important than rerunning a saved setup. Duplicate/tweak/rerun can build on the same metadata later.

### 3-D Visualizer

Responsibilities:

- load processed field data
- display volume/slices/isosurfaces
- time playback
- projection/view controls
- lighting controls
- field controls
- rendering labels/provenance

#31 has been superseded by staged visualizer implementation issues. The architecture should not treat a single broad visualizer issue as the implementation plan anymore.

The staged dependency path is:

```text
NetCDF ingest (#68)
-> diagnostics (#69)
-> result cards / notebook entries (#70)
-> Results Library UI (#71)
-> visualization-ready data contract (#72)
-> 2-D field inspection (#73)
-> 3-D scene shell (#77)
-> cloud-water rendering (#78)
-> slice planes (#79)
-> Thermal Fate process contract and diagnostics (#148/#149/#151)
-> renderer upgrade decision after process needs are clear (#112)
-> visual polish / fly-through / export later (#80)
```

The renderer is downstream of the process-diagnostics contract. If a rendering
upgrade does not help expose thermal fate, selected-region evidence, or
comparison diagnostics, it should wait.

The 3-D viewer should open from saved or ingested results and consume visualization-ready backend data. It should not parse raw NetCDF directly in the browser. Rendering remains a visualizer interpretation of CM1-derived output and must carry source model, run/result, field, processing, and rendering-method provenance.

The first 3-D scene shell is the frontend interaction/container layer. It opens
from a Result Card / Experiment Notebook entry, requests the visualization-ready
field catalog, and exposes:

- scene container;
- projection mode controls;
- zoom control;
- reset view action;
- time slider shell;
- field selector shell;
- loading, empty, and error states;
- provenance and rendering-method labels.

3-D scalar rendering starts as backend-prepared thresholded point clouds for
selected native-grid fields, not isosurfaces or a volume renderer. The backend
owns field selection and thresholding through:

- `GET /api/results/{result_id}/visualization/point-cloud`

The point-cloud endpoint reads the selected NetCDF output time, uses native
coordinates for the selected field, returns `[x, y, z, value]` points where the
field meets the requested threshold, and records source count, returned count,
thresholded-value range, full selected-field min/max/mean stats, active `z`
range where applicable, max-value location, full coordinate extents,
downsampling status, coordinate units, and provenance. If source points exceed
`max_points`, the backend applies deterministic stride downsampling and labels
it. Surface `rain` is represented as a floor layer rather than a vertical cloud
volume. The frontend renders only returned visualization-ready points and must
label the result as a CM1-derived interpretation.

The first supported 3-D fields are `qc` cloud water, `qr` rain water, `qv` water
vapor, `dbz` reflectivity, and surface `rain` when present. Potential
temperature, direct temperature, and `w` vertical velocity remain slice-first
inspection fields until future issues define field-specific 3-D rendering that
does not overclaim physical meaning. Reflectivity uses a fixed weather-radar
dBZ scale from 0 to 60+ dBZ rather than a dynamic per-run color range; shallow
cumulus may legitimately show weak or sparse reflectivity even when rain water
is present.

The frontend point projection uses those full coordinate extents, not the
min/max of returned cloudy points. Scientific views should include side/elevation
projections where model height `z` is the visual vertical axis, plus top-down and
oblique overview modes. The domain box, floor, axes, and points must share the
same transform so horizontal `y` does not masquerade as height. Oblique overview
is an interpretation for orientation, not a literal atmospheric photograph.

The frontend viewport should be a fixed scientific workbench inside the unified
Explore workflow: shared field/time/slice controls, a stable render viewport,
the matching 2-D slice inspector, selected-point explanation, and secondary
technical details. The domain box, floor/grid, slice planes, and point cloud
share one data-layer transform. Zoom scales that data layer while preserving
aspect ratio; axes, scale markers, and annotations remain readable and do not
become part of the zoomed data layer. Until a true camera is implemented,
controls should be described as view/projection controls rather than orbit or
pan camera controls. Scale markers should expose horizontal distance, visible
height, the domain floor, and active cloud-water `z` range.

3-D slice planes reuse the same backend slice endpoint as the 2-D inspector:

- horizontal plane: `orientation=horizontal`;
- vertical plane: `orientation=vertical_x` or `orientation=vertical_y`;
- fields: native-grid slice-capable fields from the catalog, including `qc`,
  `w`, `qr`, `qv`, `dbz`, direct temperature, potential temperature, and
  surface `rain` where supported;
- time: synced with the visualizer time state and the 3-D scalar layer.

The browser receives JSON slice payloads with field metadata, min/max stats,
dimension order, selected native-grid location, caveats, and provenance labels.
The scene may draw simple inspection planes from those payloads, but it must not
parse raw NetCDF in the browser, interpolate native grids, ray march, or invent
synthetic cloud physics.

The 3-D viewer can expose slice-plane controls over this same contract. A
horizontal `z` plane moves up/down by changing the vertical level index. A
vertical `x-z` plane moves through `y`; a vertical `y-z` plane moves through
`x`. Each movement issues a normal visualization-ready slice request with a new
`orientation` and `level_index`. The control is a native-grid selector, not a
camera rotation, browser-side NetCDF parser, or interpolated resampling step.

Post-MVP visual polish is a later rendering layer, not part of the data-source
contract. Volumetric ray marching, shadows, edge brightening, cloud-base
darkening, fly-through/move-through camera modes, cinematic export, and
generated thumbnails should build on the same ingested result and
visualization-ready data contracts. They must continue to label rendered output
as an interpretation of CM1-derived data and carry source model, run/result,
field, processing method, rendering method, and caveats.

Future export artifacts should be treated as local/generated outputs unless a
specific policy says otherwise. Generated thumbnails, preview frames, videos,
large processed visualization data, and browser-ready render caches should not
be committed. If small visual fixtures are needed for tests, they should be
intentionally tiny and documented separately from real CM1 output.

### Visualization-Ready Field Slices

The backend owns NetCDF/xarray field selection. Browsers should request
visualization-ready payloads from ingested results instead of opening raw CM1
NetCDF files.

Implemented MVP endpoints:

- `GET /api/results/{result_id}/visualization/fields`
- `GET /api/results/{result_id}/visualization/slice`
- `GET /api/results/{result_id}/visualization/point-cloud`

The field catalog exposes available visualizable fields, starting with `qc`
and `w` and expanding to supported fields such as `qr`, `qv`, `dbz`, surface
`rain`, potential temperature, and direct temperature when present. It maps raw
CM1 field names to product canonical names such as `cloud_water`,
`vertical_velocity`, `rain_water`, `water_vapor`, and `reflectivity`, includes
native dimensions, coordinate names, units, time values, source
model/run/result provenance, processing method, and rendering method labels.

The slice endpoint returns JSON numeric arrays for the slice-first MVP. It
supports horizontal slices and vertical `x`/`y` slices on native grids:

- `qc`: `time, zh, yh, xh`
- `w`: `time, zf, yh, xh`
- `qr`, `qv`, `dbz`, direct temperature, and potential temperature: native
  `time, z, y, x` style grids when those fields are present
- surface `rain`: horizontal floor map only

It does not interpolate staggered fields. Payloads include the selected time,
orientation, level/index, dimension order, shape, min/max/mean, finite and
non-finite counts, caveats, and provenance. Non-finite values are represented
as `null` in JSON arrays and counted in stats.

Vertical coordinate units are preserved. When a vertical coordinate is in
kilometers, payloads may include a safe meter display conversion while still
recording the native units and native value.

Future 3-D block data should use JSON metadata plus binary `float32` arrays
with explicit downsampling/max-voxel controls. That binary block contract should
build on the same provenance labels and native-grid rules, but it is not needed
for the first 2-D inspector.

### Task-Based Frontend Workspaces

The frontend uses a task-based workspace shell with three top-level sections:
`Build`, `Results`, and `Explore`.

```text
Build
  Create and run experiments.

Results
  Review, save, and manage experiment results.

Explore
  Inspect and visualize the selected result's CM1 fields.
```

`Results` is the default landing section so the selected result context is
obvious before field inspection or 3-D visualization. It is the Experiment
Notebook: a scan-friendly list of result cards plus selected notebook detail and
actions. Ingested-result cleanup lives on the selected notebook entry as a
secondary/danger preview action, and deleting a result removes the result plus
the local managed run data after explicit confirmation.

The notebook renders result-card metadata as mobile-first experiment notebook
entries rather than an admin table. The primary view should surface the result
story, cloud/rain outcomes, first cloud time, `qc` and `w` summaries,
caveats/warnings, notebook edit state, and actions to open the selected result
in Explore. Technical metadata such as raw run IDs, lifecycle/product states,
controls used, provenance labels, and detailed caveats remains in disclosure so
it is available without overwhelming the first read.

`Explore` is one desktop workflow for one selected result, not separate
implementation destinations. The selected result ID flows from Results Notebook
into Explore; that workspace then requests backend-prepared field catalogs,
defaults, point-cloud payloads, slices, and selected-point diagnostics for the
same result. The browser does not open NetCDF files or classify the physics
itself.

Explore's UI contract is explanation-first. The selected result summary,
cloud/no-cloud state, field-loading state, shared field/time/slice controls,
3-D scalar-field context, visible slice plane, 2-D slice inspector, and `What
happened here?` selected-point panel are primary state. The 3-D context renders
only supported scalar/floor layers such as `qc`, `qr`, `qv`, `dbz`, and surface
`rain`; motion and thermodynamic fields such as `w`, potential temperature, and
temperature are inspected through synchronized native-grid slices. Technical
Thermal Fate process modes, native-grid caveats, rendering/projection details, and
provenance stay available in disclosure so the browser remains a presentation
layer over backend diagnostics instead of a scientific classifier.

User-facing state labels are separate from technical provenance. The primary UI
may translate raw states like `ingested_result_metadata` or
`completed_cm1_result` into `Ingested`, `Completed CM1 result`, `Saved`, or
`Needs review`. The raw lifecycle, product state, source model, processing
method, rendering method, and native-grid caveats remain available under
technical details so scientific honesty is preserved without making the main
workflow read like a manifest.

Successful cloud-forming results can show `Minor caveat` in the primary UI when
warnings or coordinate notes exist but the run is still inspectable. `Needs
review` should be reserved for failed, no-cloud, missing-diagnostics, or
incomplete states where the result needs closer attention before it is treated
as a validated learning case.

Dry Failed Cumulus is the exception to the naive "no cloud means review" rule:
when the run is accepted, ingested, and has meaningful vertical motion without
meaningful `qc`, it is a valid moisture-limited contrast. Results should show
that result honestly as a no-cloud notebook entry; it should not expose a fixed
Baseline-vs-Dry-Failed comparison workspace until a real user-driven comparison
workflow exists.

The first field inspector is a frontend consumer of the visualization-ready
fields/slice API. It opens from a Result Card / Experiment Notebook entry and
does not read raw NetCDF or parse CM1 files in the browser.

The inspector requests:

- the field catalog for the selected result;
- one horizontal slice for the selected field/time/vertical level;
- one vertical slice for the selected field/time and `vertical_x` or
  `vertical_y` orientation.

It displays field name, units, native grid, selected time, min/max, finite and
non-finite counts, heatmap slices, caveats, and provenance labels. The raw JSON
numeric slice values remain available under technical details for audit and
debugging, but the primary inspection surface should be a readable heatmap.
Errors from unavailable fields or invalid slice selections remain UI-level
inspection errors; they do not alter the underlying result metadata or imply a
failed CM1 run.

The 2-D inspector and 3-D visualizer both choose an initial interesting time
from result diagnostics: first cloud time when present, otherwise time of max
cloud water when available, otherwise the latest output time. This prevents the
validated Baseline Shallow Cumulus quick-look result from opening at an empty
`t=0` frame when clouds form later.

When present, `science_summary` and `default_time_by_field` provide the
metadata-backed version of that startup choice. Cloud-forming fields can open at
their supported diagnostic landmark, while no-cloud or missing-field cases
declare an explicit fallback or unavailable state. Explore can still request
bounded field/slice/point-cloud payloads for rendering, but it should not reopen
or concatenate the full raw NetCDF sequence just to decide which timestep is
interesting.

The 3-D viewer keeps the same data-source contract while improving first-look
readability: cloud-water points should be visible at the default time, slice
planes should provide spatial context without overwhelming the point cloud, and
long provenance/rendering labels should sit in technical details rather than in
the main scene controls.

The backend also exposes an interesting-view defaults contract for UI startup:

```text
GET /api/results/{result_id}/visualization/defaults
```

The response reports per-field native-grid defaults for `qc` and `w`, including
time index/seconds, horizontal level index, vertical `x`/`y` slice indices,
source label, max value when available, caveats, and provenance. These defaults
are computed from backend xarray access to ingested NetCDF output. The endpoint
also accepts an optional `time_index` so the visualizer can ask for selected-time
max `qc` or selected-time max `w` slice locations instead of reusing a global
max from a different output time. The browser uses those defaults to pick
cloud-centered or updraft-centered views but still requests normal slice/point-
cloud payloads for rendering. The defaults endpoint does not interpolate fields,
parse raw NetCDF in the browser, or change result metadata.

This is not a 3-D viewer, replay engine, or rendering pipeline. It is the
orientation/scaling check that should happen before 3-D visualizer work.

## Data Flow

### Create Run

```text
scenario + controls
→ config builder
→ run directory
→ run manifest
```

Run-configuration metadata should flow through this path: scenario templates
define editable configuration defaults and optional starting presets, generated
run packages record the selected duration, grid/detail, domain, output cadence,
output field density, forcing, requested fields, advanced CM1-facing values,
and validation report, run manifests preserve them during execution, and result
metadata keeps them available for later inspection. Legacy run-size preset names
may remain as compatibility provenance.

If size/runtime estimates are not validated yet, manifests and reports should record that explicitly rather than presenting guessed precision.

### Execute Run

```text
run manifest
→ CM1 command
→ logs + NetCDF output
→ status update
```

### Ingest Run

```text
NetCDF output
→ metadata
→ diagnostics
→ visualization artifacts
→ result manifest
```

### Visualize Run

```text
result manifest
→ selected field/time
→ visualizer data loader
→ 3-D view
```

### Result Notebook Entry

Conceptually, a saved result can be represented as a notebook-style entry:

```text
result notebook entry
  result_manifest.json
  run_manifest.json
  diagnostics_summary.json
  key_frames.json
  user_notes.md or notes field
  visualization_defaults.json
```

These file names are conceptual for now. Implementation should choose concrete schemas when the result model is built.

The result manifest should be able to answer:

```text
What scenario was this?
What physical question was tested?
What controls were used?
What run configuration was selected?
What did CM1 do?
What diagnostics summarize the cloud evolution?
Can I replay it?
Can I open it in the 3-D visualizer?
Can I find it again later?
```

## Storage Layout

Default runtime data belongs outside the repo:

```text
~/CloudChamber/
  settings.json
  runs/
  cache/
  logs/
```

The repo may support `./local-data/` as a gitignored development override, but the default should remain `~/CloudChamber`.

The top-level `data/` directory, if present, is reserved for documented tiny fixtures or placeholders only. It is not a runtime storage location.

Optional ignored local development layout:

```text
local-data/
  cm1-runs/
    <run-id>/
      namelist.input
      input_sounding
      run-manifest.json
      cm1.stdout.log
      cm1.stderr.log
      cm1out_*.nc
  processed/
    <run-id>/
      result-manifest.json
      fields/
      thumbnails/
  library/
    index.json
```

## Settings Model

Settings should support:

- Cloud Chamber runtime home, defaulting to `~/CloudChamber`.
- CM1 root path.
- CM1 run directory path.
- optional cache/log directories.
- environment override such as `CLOUD_CHAMBER_CM1_ROOT`.
- optional runtime-home override `CLOUD_CHAMBER_RUNTIME_HOME` for tests/local development.
- saved config in `~/CloudChamber/settings.json`.

Likely local CM1 probe paths may include:

```text
/Users/timpeterson/cm1r21.1
/Users/timpeterson/cm1r21.1/run
```

These are probes/defaults, not hard-coded requirements. If CM1 is missing, Cloud Chamber should fail clearly with settings guidance rather than silently pretending work succeeded.

The backend settings model loads saved JSON config from the runtime home, lets `CLOUD_CHAMBER_CM1_ROOT` override saved CM1 root paths, infers `<cm1_root>/run` when only a root is provided, and reports a ready/missing CM1 discovery status without launching CM1 or writing runtime data into the repo.

Committed scenario templates:

```text
scenarios/
  lower-atmosphere/
    baseline-shallow-cumulus/
    dry-failed-cumulus/
    capped-suppressed/
    humid-vigorous/
    low-stratus/
    warm-rain/
```

## Run Manifest Concept

Run manifests should record the scenario template, adjusted controls, generated CM1-facing files, runtime paths, lifecycle state, validation status, timestamps, and later output paths. A manifest should not require NetCDF output to exist.

Run manifests should also record the selected run configuration, optional
legacy run-size preset, physical question, expected diagnostics, and
visualization defaults when those concepts are available from the scenario
template.

The backend run-manifest schema records run ID, scenario reference/version, adjusted controls, generated CM1 input paths, CM1 root/run paths, app metadata, timestamps, lifecycle state, validation status, output paths, user notes/tags, and provenance labels. It serializes/deserializes as JSON and does not require NetCDF output.

Output metadata distinguishes:

- `raw_cm1_artifacts`: local CM1 `.dat/.ctl` files such as `cm1out_000001_s.dat`, `cm1out_s.ctl`, `cm1out_stats.dat`, and `cm1out_metadata.ctl`;
- `netcdf_paths`: preferred self-describing CM1 output files such as `.nc`, `.nc4`, `.cdf`, or `.netcdf`;
- `processed_artifacts`: future Cloud Chamber-derived browser/diagnostic artifacts;
- `runtime_warnings`: caveats captured from logs, such as CM1 floating-point exception flags.

Raw `.dat/.ctl` artifact detection is an honest catalog, not full ingest, diagnostics extraction, or visualization preprocessing.

Lifecycle states:

```text
created
packaged
queued
running
completed
failed
canceled
ingested
saved
```

`packaged` means Cloud Chamber generated a dry-run package. It is not equivalent to queued, running, or completed CM1 output.

`ingested` means Cloud Chamber has derived metadata or browser-friendly artifacts from completed CM1 output. `saved` means the user has a named/tagged experiment notebook entry. Neither state changes the underlying CM1 output provenance.

## Process Control

The app should support:

- start run
- tail logs
- cancel run if possible
- mark failed
- retry run
- ingest completed run

Avoid complex job scheduling at first. One local run at a time is fine for MVP.

## CM1 Runtime Assumptions

CM1 is external to the app.

User provides path like:

```text
/Users/timpeterson/cm1r21.1/run
```

The app checks:

- `cm1.exe`
- `LANDUSE.TBL`
- NetCDF support
- required Python/xarray/netCDF dependencies

Do not vendor CM1.

The app should avoid assuming large in-memory NetCDF processing. Ingestion should prefer selected fields, selected frames, chunking, downsampling, or other backend-side reductions before browser visualization.

## NetCDF And Visualization Data Contract

NetCDF is Cloud Chamber's preferred ingest path because it is self-describing, portable, and well suited for Python/xarray diagnostics. CM1 can also write GrADS/direct-access `.dat/.ctl` output. Cloud Chamber should catalog those raw files, but the main product should not become a full `.dat/.ctl` parser unless NetCDF proves blocked or impractical.

The current Baseline Shallow Cumulus generator sets CM1 `output_format = 2`, which CM1 documents as NetCDF output. The first successful local smoke run used the prior `.dat/.ctl` path, so the next manual validation should confirm whether the generated NetCDF configuration works with the local CM1 build.

Raw NetCDF is authoritative CM1 output, but it is not ideal for direct browser rendering. The ingestion layer should create explicit metadata and browser-friendly derivatives that preserve provenance:

- source model
- run ID
- scenario ID
- field name and units
- time coordinate
- processing method
- rendering method

Generated visualization artifacts are interpretations of CM1 data and must be labeled that way.

The practical path before 3-D rendering is to define the visualization-ready data contract, then build a 2-D field inspector that can verify orientation, time indexing, field availability, units, and scaling. The 3-D scene shell, cloud-water rendering, and slice planes should build on that same contract.

## Visualization Data Strategy

Raw NetCDF is not ideal for direct browser rendering, and the browser should
not parse raw CM1 output. The local backend should load CM1 NetCDF through
xarray, select only the requested field/time/slice, and return a bounded,
provenance-labeled payload.

Recommended staged path:

1. Load/inspect NetCDF in backend.
2. Extract selected fields and time frames.
3. Return interesting native-grid defaults for `qc`/`w` field/time/slice
   startup state.
4. Return JSON 2-D slices for the slice-first MVP.
5. Downsample or chunk as needed for future larger payloads.
6. Use JSON metadata plus binary `float32` arrays for future 3-D blocks.
7. Load fields into the 2-D inspector or later Three.js/WebGL viewer.

Potential processed formats:

- JSON numeric arrays for MVP 2-D slices
- JSON metadata + binary `float32` arrays for future 3-D blocks
- Zarr later
- compressed chunks later
- PNG/texture stacks for MVP if easier

## Provenance Labels

Every visual field should know:

```text
source_model: CM1
run_id
scenario_id
field_name
units
time_seconds
processing_method
rendering_method
```

Rendering method examples:

- raw slice
- interpolated slice
- max projection
- mean projection
- isosurface
- volume opacity interpretation

Result-card metadata should include the same provenance labels used by visualization data so the Results Library and visualizer tell the same truth about the source model, run, processing, and rendering method.

## Testing Strategy

Early tests should cover:

- scenario schema validation
- config generation
- run manifest creation
- fake CM1 run process
- output detection
- ingestion from tiny fixture NetCDF
- result manifest generation
- visualizer metadata loading
- no generated outputs committed

Golden Path implementation tests should use fake/minimal fixtures for scenario schema, package generation, manifest lifecycle, result-card serialization, and visualization metadata. Real CM1 validation remains local/manual/offline.

## Safety / Guardrails

- Generated outputs ignored by git.
- Confirm before deleting local runs.
- Do not overwrite run directories.
- Clear labels for preview vs CM1 result.
- No hidden fake clouds.
