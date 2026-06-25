# Cloud Chamber Roadmap And Startup Issues

Cloud Chamber should move toward the first usable product spine, not scaffolding for scaffolding's sake:

```text
scenario template
-> user-adjusted experiment config
-> validation
-> run manifest
-> generated CM1 run package
-> dry-run report
-> local CM1 launch
-> ingest
-> result diagnostics
-> Thermal Fate inspection
-> provenance-labeled visualization
```

CM1 remains the source of truth. Preview estimates are guidance only, and visualization is an interpretation of CM1-derived data.

Cloud Chamber is a personal, scientifically honest guided experiment notebook:
curated scenario families, meaningful controls, local-first CM1 runs,
replayable saved results, process diagnostics, selected-region inspection,
comparison across variants, and beautiful visualization.

The current UX reset reframes the visible product as a guided experiment
notebook:

```text
Cloud Chamber is a guided experiment notebook for understanding why clouds formed, failed, stayed shallow, or grew stronger.
```

See [UX Reset: Guided Experiment Notebook](ux-reset-guided-experiment-notebook.md).
Future UX implementation should follow that reset before renderer upgrades or
future scenario-family expansion.

Explore's key user-facing concept is `What happened here?`: click a spot or
region in a completed cloud result, then receive a clear explanation backed by
CM1-derived diagnostics. Thermal Fate and selected-region diagnostics remain
the scientific model behind that answer, not the first-read UI structure.

Replay / inspect / save is core MVP. Duplicate / tweak / rerun is later.

## UX Reset Track

The UX reset is now the roadmap gate for future user-facing work. It keeps the
three top-level workspaces but changes their visible contract:

```text
Build:
  Choose/setup a guided experiment and safely create/launch a local CM1 package.

Results:
  The experiment notebook and comparison home.

Explore:
  A focused visualization plus explanation screen for one selected result.
  The core interaction is What happened here? -- select a cloud, updraft,
  clear-air thermal, or no-cloud region and receive a CM1-backed explanation of
  what happened there and why.
```

Thermal Fate remains the internal scientific diagnostic/explanation model. It
powers explanations, confidence/caveat labels, comparison summaries,
selected-region diagnostics, and technical provenance. It should not dominate
the primary visible UI as a process-taxonomy cockpit.

Immediate UX reset sequence:

```text
#168 Codify Cloud Chamber UX reset decisions in product docs
-> #169 Fix Explore selected-result and field-loading trust states
-> #170 Refine Cloud Chamber navigation and layout style
-> #171 Redesign Results as a scan-friendly experiment notebook
-> #175 Make What happened here? the core Explore interaction
-> #172 Redesign Explore around one primary visualization and one explanation panel
-> #173 Redesign Build as guided experiment selection, not a form-first setup page
-> #112 Revisit renderer upgrade only after the simplified Explore UX is defined
-> #153/#154/#155 Future scenario-family expansion after the app is compelling and trustworthy
```

This track comes before renderer upgrades and before expanding the future
scenario-family roadmap. Objective behavior should be covered by automated
tests; manual QA for this reset is qualitative only.

#172 depends on #175's interaction model. Explore redesign should preserve
`What happened here?` as the central action instead of becoming a generic
visualization-plus-panel redesign.

#172 applies that model to the current Explore shell: the page should read as
`Explore this result`, keep the selected result and cloud/no-cloud trust state
obvious, make the primary CM1-derived visual surface dominant, and keep a
visible `What happened here?` explanation panel beside the view. Process modes,
projection/rendering controls, slice-plane controls, and detailed provenance
remain available but secondary behind disclosure.

#170 establishes the shared atmospheric notebook visual system that later UX
reset issues should inherit. The app shell should feel calm, pale, and
notebook-like; blue / blue-gray is the primary accent; green is reserved for
success states; warnings and destructive actions use subtle amber/red; and dark
surfaces are limited to visualization plotting areas when they improve CM1
field readability. Later Results and Explore redesign issues should build on
these tokens and should not reintroduce black/green terminal chrome.

#171 redesigns Results as a mobile-first experiment notebook rather than a
dense admin table. Notebook should use scan-friendly experiment cards and a
selected result detail card; cloud/rain outcomes, key diagnostics, caveats,
saved/protected state, and open/compare actions belong in the first read, while
raw run IDs, lifecycle/product states, controls, provenance, and detailed
warnings belong under technical details.

## Thermal Fate Roadmap

Thermal Fate is the internal organizing scientific model: Cloud Chamber should
explain why air rises, why some thermals do or do not form cloud, why some
clouds stay shallow, why others grow taller, why some break through into deep
convection, and how precipitation feedback can reorganize or suppress
convection.

Thermal Fate remains the internal scientific model behind the guided experiment
notebook UX. The visible app should use the UX reset track above before
returning to renderer upgrades or future scenario-family expansion. The
diagnostic execution sequence is:

```text
#148 Thermal Fate Framework / process contract
-> #149 global/process diagnostics
-> #151 selected-region backend diagnostics
-> #150 Thermal Fate overlays in Explore
-> #152 Thermal Fate Inspector UI
-> #168-#173 guided experiment notebook UX reset
-> #112 renderer upgrade after simplified Explore UX is defined
-> #153 surface-heating scenario family
-> #154 deep-convection breakthrough scenario family
-> #155 precipitation feedback / cold-pool scenario family
```

Renderer upgrades follow process needs. They should not drive the product
direction before Cloud Chamber can explain thermal fate with CM1-derived
diagnostics, selected-region evidence, comparison, and caveats.

#149 adds the first backend global/process diagnostics bridge. It attaches
`process_diagnostics` to ingested result metadata, exposes conservative
Thermal Fate labels/confidence/main-limiting-factor fields on result cards, and
keeps deep-breakthrough, buoyancy, precipitation-feedback, and selected-region
diagnostics unavailable or candidate/caveated until their required fields and
follow-up issues exist.

#151 adds the backend selected-region diagnostics bridge for the user-facing
`What happened here?` interaction. It lets the app ask that question for
bounded point, column, and box regions, returning CM1-derived local summaries,
conservative labels, provenance, caveats, and comparison-to-domain values
without returning large raw arrays or moving NetCDF parsing into the browser.

#150 adds the first Explore process-overlay layer. The 2-D and 3-D Explore
views can show Thermal Fate process modes, direct-field evidence, candidate or
unsupported states, and caveats while preserving the existing slice/point-cloud
workflows. Selected-region click/brush inspection remains #152.

#152 adds the first backend-supported selected-region UI foundation. Under the
UX reset, future Explore work should promote that capability into the primary
`What happened here?` interaction: click a cloud, updraft, clear-air thermal, or
no-cloud region, mark the selected spot or region, and render an explanation
with evidence, uncertainty, caveats, and technical details on demand. The
browser still does not parse raw NetCDF or compute scientific classification.

## Golden Path: Baseline Shallow Cumulus

Baseline Shallow Cumulus is the first complete product loop:

```text
Pick Baseline Shallow Cumulus
-> adjust curated controls
-> choose run-size preset
-> validate setup
-> generate CM1 run package
-> launch local CM1
-> monitor logs/status
-> ingest NetCDF output
-> create result card / experiment notebook entry
-> replay cloud evolution
-> open Explore
-> save/name/tag result
```

The Golden Path should test a clear physical question, expose curated lower-atmosphere controls, preserve CM1 as the source of truth, and make exact cloud morphology an inspection result rather than a brittle pass/fail expectation.

Physical question:

```text
How do low-level moisture, surface heating, cap strength, cap height, dry air aloft, and mixing/entrainment affect shallow-cumulus formation, timing, depth, updraft strength, and cloud-water evolution?
```

Expected generated CM1-facing files:

```text
run_manifest.json
case_manifest.json or scenario metadata
namelist.input
input_sounding or equivalent profile file
runtime file checklist
dry-run report
visualization defaults
```

Expected diagnostics:

```text
cloud formed / failed
first cloud time
cloud base
cloud top
max vertical velocity
cloud-water summary
rain onset if present
main limiting factor / interpretation note
```

## Runtime Tiers

Cloud Chamber should support run-size presets that make local cost and confidence visible:

- **Quick look**: roughly 10-20 minutes when feasible on the local Mac; used for sanity checks, setup inspection, and rough cloud behavior.
- **Standard**: normal personal exploration run; used for useful saved results and diagnostics.
- **Deep / overnight**: longer richer runs that may take hours or overnight; used for prettier, more detailed, or higher-confidence result exploration.

Runtime estimates are approximate until locally validated. The MVP should assume a 2024 MacBook Air with 8GB RAM, one local CM1 run at a time, conservative output handling, and backend-side processing/downsampling.

Runtime tier metadata should be represented in scenario templates, generated package reports, run manifests, result metadata, and result cards. Unknown estimates should be labeled as unknown until locally validated.

## Product State And Provenance Contract

Implementation issues should preserve these product states and labels:

```text
Preview estimate
Generated CM1 configuration
Packaged dry-run output
Queued/running CM1 process
Completed CM1 result
Failed/canceled CM1 run
Ingested result metadata
Visualizer interpretation
Saved result/notebook entry
```

The UI and docs should not call a preview, dry-run package, or visualization interpretation a completed CM1 result.

## M0 Repo Foundation

Goal: make the repo safe, clear, and reviewable.

Why it matters: without docs, generated-data rules, CI, and Codex working rules, the project will drift and repeat the mistake of building the wrong center of gravity.

Deliverables:

- Normalized docs.
- `AGENTS.md`.
- Generated-data policy.
- `.gitignore` protections.
- CI check names: `Frontend`, `Backend`, `Scripts and config`.
- Local validation script.
- Issue/PR templates.

## M1 Scenario Package Spine

Goal: create the first usable path from scenario idea to generated CM1 run package.

Why it matters: this is the first product spine, not scaffolding. A user should be able to choose a scenario, adjust controls, validate settings, and generate a safe dry-run package.

Deliverables:

- Settings model and CM1 path discovery.
- Scenario template schema.
- Initial lower-atmosphere templates including warm rain.
- Run manifest schema.
- Dry-run CM1 package generator.
- CM1 input generation contract and mapping tests.
- Scenario Builder shell.
- Dry-run review/report UI.
- Preview placeholder.
- Manual local validation loop documentation.

Implementation anchors:

- #20 should carry run-size presets, physical questions, learning goals, expected diagnostics, and one-control variation metadata.
- #21 should mark Baseline Shallow Cumulus as the first hero case and keep warm rain early but non-blocking.
- #22 should preserve lifecycle/provenance distinctions.
- #23 should include run-size preset, physical question, expected diagnostics, visualization defaults, and explicit unknown estimate fields in dry-run reports.
- #24 should map curated atmospheric controls to CM1-facing configuration without exposing raw namelist fields as the primary user language.
- #25, #26, and #27 should use Golden Path wording and never imply a preview or dry-run package is a completed CM1 result.

The dry-run package flow must be followed directly by local CM1 launch/monitoring work. Dry-run generation is a stepping stone, not a dead end.

## M1.5 Golden Path Manual CM1 Validation

Goal: prove the Baseline Shallow Cumulus package path against a real local CM1 run before broadening product scope.

Deliverables:

- Golden Path validation plan.
- run-size preset notes from local/manual execution.
- generated package inspection checklist.
- launch/log/status checklist.
- output and NetCDF detection checklist.
- ingest readiness checklist.
- result-card/notebook acceptance checklist.
- first visualizer inspection checklist.
- first diagnostics capture: first cloud time, cloud base/top, max updraft, cloud-water summary, and rain onset if present.
- result-card/notebook acceptance notes.
- visual inspection notes.

This milestone remains local/manual/offline. CI should not run real CM1.

Manual validation path:

```text
Generate Baseline Shallow Cumulus dry-run package
-> inspect generated manifests, namelist, sounding notes, report, and runtime checklist
-> compare package against local CM1 root/run-dir probes
-> manually stage package into the local CM1 run workflow
-> launch CM1 outside CI
-> capture logs/status/runtime/output paths
-> detect NetCDF or raw CM1 .dat/.ctl output without committing it
-> record diagnostics and limitations
-> document ingest/result-card/visualizer readiness notes
```

Expected local probes include `CLOUD_CHAMBER_CM1_ROOT`, `~/CloudChamber/settings.json`, `/Users/timpeterson/cm1r21.1`, and `/Users/timpeterson/cm1r21.1/run`. Generated CM1 outputs, logs, NetCDF files, `.dat/.ctl` files, validation reports, copied runtime files, `LANDUSE.TBL`, and local run folders must stay gitignored.

The direct follow-up is #29: automate the local CM1 launcher and status/log monitor with one local run at a time, explicit failure/cancel states, and tests that use fake subprocesses rather than real CM1.

### Dry Failed Cumulus Planning

Dry Failed Cumulus is the first planned contrast case after the validated
Baseline Shallow Cumulus quick-look loop. It should teach moisture limitation:

```text
How does insufficient low-level moisture prevent shallow cumulus formation even when boundary-layer thermals and vertical motion are present?
```

The target contrast is:

```text
Baseline Shallow Cumulus:
  cloud formed
  rain detected
  qc and w both active

Dry Failed Cumulus:
  thermals / vertical motion remain
  little or no qc
  no rain
  main limiting factor is low-level moisture / saturation deficit
```

No cloud by itself is not success. A useful Dry Failed Cumulus run must complete
cleanly, produce NetCDF, ingest the full output sequence, keep `cloud_formed =
false` and `rain_present = false`, retain meaningful nonzero `w`, and avoid
severe NaN/Infinity caveats in target fields. No cloud plus no vertical motion
is not Dry Failed Cumulus.

Planning sequence:

1. #102 validates external-sounding Baseline Shallow Cumulus reproduction from the
   accepted `les_ShallowCu` reference-derived setup.
2. #103 implements Dry Failed Cumulus as a moisture-limited variant from that
   external-sounding baseline, changing only low-level moisture first.

The old compact quick-look derivative that produced no cloud, no vertical
motion, and NaN/Infinity caveats is invalid evidence and must not be used as a
scenario base.

### Capped / Suppressed Cumulus Planning

Capped / Suppressed Cumulus is the next planned contrast after Dry Failed
Cumulus. Dry Failed tests moisture limitation. Capped / Suppressed should test
stability and inhibition:

```text
How does a stronger cap suppress or limit shallow-cumulus growth even when moisture and boundary-layer thermals are available?
```

The first target is not total no-cloud failure. The target is shallow or weak
cloud limited by a stronger cap:

```text
Baseline:
  moisture + thermals + normal cap -> cloud grows

Dry Failed:
  thermals + cap okay, but too dry -> no meaningful cloud

Capped / Suppressed:
  moisture + thermals okay, but stronger cap -> shallow/limited cloud
```

The first implementation, #140, starts from the accepted external-sounding
Baseline Shallow Cumulus path and varies only:

```text
cap_strength = stronger
```

It keeps `cap_height`, `low_level_humidity`, and `surface_heating` at the
accepted baseline. The CM1-facing adjustment is a stronger stable layer in the
generated external `input_sounding` potential-temperature profile near the cap.
Do not use the old compact quick-look derivative, do not tune moisture, and do
not vary cap height in the first implementation.

Expected diagnostics:

```text
cloud_formed: true or weak/limited; false only if w remains healthy and moisture is not the limiting factor
first_cloud_time: delayed relative to baseline, or null if fully suppressed
cloud_top: lower than baseline
max_qc: lower than baseline
cloud_fraction: lower than baseline
rain_present: preferably false or reduced
max_w: meaningfully nonzero
min_w: finite, preferably negative/nonzero
main_limiting_factor: cap/stability
```

Potential future diagnostics include `cloud_top_time_series`,
`max_qc_height_time_series`, cloud-fraction time-series comparison, cap-level or
inversion metadata from the generated sounding, and `max_w_below_cap` if
practical. If current diagnostics cannot clearly determine whether the cap
limited vertical growth, create a follow-up diagnostics issue rather than
overclaiming.

## M2 Local CM1 Run Manager

Goal: make Cloud Chamber actually launch and monitor local CM1 runs.

Deliverables:

- Local CM1 launcher from generated run manifests.
- one-local-run-at-a-time guard.
- stdout/stderr capture into run package logs.
- lifecycle state management for queued/running/completed/failed/canceled.
- cancel/failure handling with clear manifest state.
- overwrite protection for output-like files.
- local/manual validation path.

Implementation anchor:

- #29 should assume one local CM1 run at a time, account for long/overnight runs, and preserve logs for result notebook entries.

The first implementation uses fake subprocesses in automated tests and does not require real CM1 in CI. Real execution remains local/manual and depends on the user's configured CM1 root/run directory.

#56 found that the original dry-run package was still placeholder-only. The follow-up package-readiness work must keep #56 open/blocked until Baseline Shallow Cumulus packages generate CM1-facing inputs, reject placeholder-only packages before launch, stage local runtime files such as `LANDUSE.TBL`, and then retry the manual smoke run.

#56 produced the first accepted-with-notes local CM1 execution from a Cloud Chamber-generated Baseline Shallow Cumulus package. That run produced `cm1out_*.dat` and `.ctl` artifacts rather than NetCDF, so #62 bridges M2 to M3 by cataloging raw CM1 output artifacts honestly while keeping NetCDF as the preferred ingest path.

#60 distinguishes process completion from usable CM1 result completion: exit code 0 without NetCDF or raw CM1 `.dat/.ctl` output should be `needs_review`, not an accepted result.

## M3 Results Library + Experiment Notebook

Goal: turn CM1 outputs into replayable, inspectable, searchable experiment notebook entries.

Deliverables:

- NetCDF ingest.
- Raw CM1 `.dat/.ctl` artifact cataloging as a transitional/fallback record, not full ingest.
- run metadata extraction.
- diagnostics summary.
- logs/result status.
- runtime storage inventory and explicit safe run cleanup under the configured runtime home.
- save/name/tag/search/filter/delete.
- result-card / experiment-notebook model.
- open saved result in visualizer.
- duplicate/tweak/rerun foundation later, after replay/inspect/save is reliable.

Implementation anchor:

- #30 should make replayable/inspectable saved result cards the core behavior. Duplicate/tweak/rerun should remain optional or later.
- #64 adds the storage bridge needed after the first successful 852 MB smoke run: inventory runtime-home usage, warn at the 50 GB MVP threshold, classify runs conservatively, and delete only explicitly selected run directories under `~/CloudChamber/runs/`. Cleanup must never target the repo, home directory, runtime home itself, or the external CM1 installation, and threshold warnings must never auto-delete anything.
- #68 establishes the backend NetCDF ingest bridge: read completed-run NetCDF output with xarray, write `result_metadata.json`, preserve raw `.dat/.ctl` artifact cataloging without parsing it, and leave diagnostics/result-card UI/visualization-ready data to follow-up issues.
- #69 adds first Baseline Shallow Cumulus diagnostics to ingested NetCDF result metadata: cloud formed yes/no with `qc >= 1e-6 kg/kg` and at least 10 cloudy grid cells, first cloud time, cloud base/top when vertical coordinates are available, `qc` summaries/time series/cloud fraction, `w` max/min summaries/time series, optional `qr` rain detection with `qr >= 1e-7 kg/kg`, and caveats for missing, inferred, or non-finite fields.
- #70 adds the backend Result Card / Experiment Notebook API over ingested metadata: list/get cards, update name/tags/notes, save/protect results, and summarize run ID, scenario, run-size preset, physical question, diagnostics, caveats, and output files without rerunning CM1.
- #71 adds the first frontend Results Library shell over the #70 API: result cards, selected result detail/notebook card, diagnostics/caveats/output summaries, saved/protected state, and editable name/tags/notes. It must not implement replay or 3-D visualization.
- #98 refactors the frontend into a guided MVP workspace and #131 consolidates it into the task-based `Build`, `Results`, and `Explore` model. The default landing path should be `Results -> validated quick-look baseline -> Open in Explore`, with user-facing result labels in the primary UI and raw lifecycle/provenance labels under technical details.
- #108 makes the Build workspace a guided local run loop: create package, launch local CM1, refresh status/log tails, review output-artifact counts, ingest completed NetCDF output, and open the resulting card in Results or Explore. Automated tests must mock these API responses and never run real CM1.
- #173 reframes Build as a guided experiment setup plus local run launchpad rather than a one-package-at-a-time wizard. It shows local packages/runs/results across pipeline states, moves eligible packages forward through existing backend APIs, and routes cleanup to Results / Storage.
- #109 adds runtime storage management under Results / Storage over the runtime storage backend: total runtime-home usage, 50 GB warning-threshold state, largest run directories, result-card names when associated, saved/protected state, output summaries, dry-run delete preview, explicit confirmed deletion, and disabled cleanup for running or saved/protected runs.
- #189 is the next lifecycle-cleanup gate after #173/#190: Storage should read as runtime inventory for the same package/run/result lifecycle that Build launches and Results reviews. It joins result-card names to run directories, shows ready-to-run/running/completed/ready-to-ingest/ingested/saved/malformed states clearly, exposes safe non-destructive actions, and keeps deletion behind Storage preview/confirmation without forcing users to manage local folders by raw run ID.
- #83 makes NetCDF ingest evaluate the full CM1 model-output sequence instead of only the first file. It must classify `cm1out_*.nc` model-field files separately from `cm1out_stats.nc`, record total output files/time steps and first/last time, and run diagnostics across the full sequence before concluding whether clouds formed.
- #84 follows the full-sequence ingest evidence from #83: `dry-run-157b09a178e1` evaluated 25 model-output files, but the run still had no cloud, no vertical motion, and NaN/Infinity caveats. The next Baseline Shallow Cumulus package keeps the BOMEX-style quick-look approach but switches to fixed small ocean roughness. A fixed-roughness validation run completed and produced NetCDF output, but still showed no cloud or vertical motion, so #84 remains the active calibration path for deeper CM1 namelist/sounding work.
- #87 supersedes incremental tuning of the invalid quick-look derivative. It recovers Baseline Shallow Cumulus from CM1's local `les_ShallowCu` reference case, preserving the reference grid, runtime, domain top, damping, surface/ocean/flux settings, and stress path while keeping NetCDF output as the intentional ingest-path change. The first reference-derived validation run completed and ingested successfully with `cloud formed; rain detected`, so quick-look scaling should resume from this recovered baseline one change at a time.
- The updated #84 scope derives the first quick-look Baseline Shallow Cumulus variant from the validated #87 baseline by changing only runtime timing: `timax = 10800.0` and `tapfrq = 900.0`. All reference-derived grid/domain/surface/damping/boundary settings and NetCDF output remain preserved. The first quick-look validation run completed and ingested successfully with `cloud formed; rain detected`, 13 model-output time steps, first cloud at 1800 seconds, package size 206 MB, and preserved reference-derived settings.
- #102 switches Baseline Shallow Cumulus package generation onto CM1's external `input_sounding` route (`isnd = 17`) while preserving the validated `les_ShallowCu` grid/domain/runtime/surface/damping/boundary settings and wind profile. The validation run completed and ingested successfully with `cloud formed; rain detected`, 13 model-output time steps, first cloud at 1800 seconds, `max_qc_kg_kg = 0.001976807601749897`, and `max_w_m_s = 6.270190238952637`. This creates the prerequisite profile path for Dry Failed Cumulus moisture experiments.
- #103 implements Dry Failed Cumulus as the first moisture-limited contrast case from the accepted external-sounding baseline. The generated package preserves the Baseline Shallow Cumulus namelist family and changes only the lower-atmosphere moisture profile for the `low_level_humidity = drier` control. The validation run `dry-run-dry-failed-cumulus-20260522192000` completed and ingested successfully with 13 model-output time steps, `no cloud formed; no rain detected`, `max_qc_kg_kg = 0.0`, `max_w_m_s = 1.949130654335022`, and `min_w_m_s = -1.0865488052368164`. This establishes the first useful lab pair: Baseline forms cloud; Dry Failed has thermals without meaningful cloud water.
- #107 adds the first comparison workflow over those accepted result cards under Results / Compare: Baseline Shallow Cumulus quick-look vs Dry Failed Cumulus quick-look. The first version is a side-by-side result-card comparison with cloud/rain outcomes, first cloud time, max `qc`, max/min `w`, caveats, output/time-step summaries, saved/protected state, and quick actions into Explore. It keeps technical provenance secondary.
- #116 adds side-by-side 2-D slice comparison for that accepted lab pair using the existing #72/#73 visualization-ready fields/slice API. It compares `qc` and `w`, supports shared output-index selection, shows units/stats/provenance, and keeps raw NetCDF parsing out of the browser.
- #110 adds the disciplined Baseline Shallow Cumulus low-level humidity ladder. `drier`, `baseline`, and `more_humid` preserve the accepted external-sounding namelist family and change only the generated `input_sounding` moisture profile for one-control-at-a-time learning. Initial local quick-look validation completed and ingested: `drier` produced no cloud/rain with meaningful vertical motion, while `more_humid` produced earlier cloud, rain, stronger `qc`, and stronger updrafts.
- #140 implements the first Capped / Suppressed Cumulus stronger-cap package from the accepted external-sounding baseline. The package preserves the namelist family and changes only potential-temperature / stability near the cap for `cap_strength = stronger`. Validation run `dry-run-capped-suppressed-20260526015634` completed and ingested 13 model-output time steps with `cloud formed; rain detected`, but cloud top, max `qc`, cloud fraction, max/min `w`, and max rain water were all reduced relative to the accepted baseline. Treat it as `accepted_with_notes` / cap-limited candidate until process diagnostics can directly explain the cap limitation.

## M4 Unified Explore MVP

Goal: deliver the main payoff as a stable selected-result Explore loop: see the
cloud context, inspect synchronized slices, click a cell/region, and ask `What
happened here?`

Deliverables:

- selected-result trust and field-loading states.
- unified desktop Explore workflow.
- 3-D `qc` cloud-water context as an interpretation of CM1 output.
- shared time / field / slice controls.
- horizontal/vertical native-grid slices.
- selected-cell `What happened here?` explanation.
- technical details and provenance on demand.

Implementation anchor:

- #31 has been superseded by staged visualizer implementation issues. It captured the right broad goal, but was too large to implement safely as one PR.
- #72 defines and implements the backend visualization-ready data contract. The browser should not parse raw NetCDF directly; it should consume fields and JSON slice payloads from backend endpoints. The MVP supports `qc` and `w`, native grids (`zh/yh/xh` for `qc`, `zf/yh/xh` for `w`), provenance/rendering labels, finite/non-finite stats, and vertical unit display metadata without interpolation.
- #73 built the first 2-D slice inspector on top of the #72 fields/slice API before the full 3-D viewer so field orientation, time indexing, vertical coordinates, scaling, and basic cloud evolution could be checked. It opens from selected result context, enables field/time selection, shows horizontal and vertical slices, and keeps the browser away from raw NetCDF parsing.
- #77 built the first 3-D scene shell from the selected result context: scene container, projection/view controls, zoom, reset view, time slider shell, field selector shell, loading/empty/error states, and provenance/rendering labels. It did not render cloud water, slices, or raw NetCDF data in the browser.
- #78 renders the first cloud-water field from visualization-ready data as a thresholded `qc` point cloud. The backend selects native-grid points and the browser renders only that payload; no raw NetCDF parsing, interpolation, isosurface extraction, ray marching, or cinematic lighting belongs in this step.
- #79 adds horizontal and vertical slice planes using the same provenance-labeled #72 slice API and native-grid caveats. Slice-plane time stays synced with the point cloud, supports `qc` and `w`, and remains an inspection overlay rather than raw NetCDF parsing or volumetric rendering.
- #98 also makes Explore inherit the selected result and default to an interesting time: first cloud when available, otherwise max cloud-water time if available, otherwise latest output. Technical rendering/provenance details stay available but secondary.
- #100 sharpens the first usable inspection path: Results should surface the validated quick-look baseline, successful cloud-forming runs with caveats should read as `Minor caveat` rather than failed review states, the 2-D inspector should show slice heatmaps before raw matrix values, and the 3-D viewer should open with visible cloud-water points plus readable slice context.
- #105 makes Explore physically interpretable rather than debug-like: the backend provides native-grid default view locations for `qc` and `w`, slice inspection defaults to one primary heatmap with `Horizontal` / `Vertical X` / `Vertical Y` / `Compare` modes, the 3-D context adds domain box/axes/height/floor/time/threshold context, slice planes are available as native-grid inspection aids, and view presets expose Cloud overview, Vertical cross-section, Top-down slice, and Inspect updraft slice.
- #115 fixes the 3-D visualizer coordinate projection so point placement uses full NetCDF coordinate extents rather than returned cloudy-point extents. Side x-z and y-z views make model height the visual vertical axis, top-down x-y shows footprint, oblique remains an interpretive overview, and selected-time max `qc`/`w` defaults keep slice planes centered on the current cloud or updraft location.
- #119 stabilizes the 3-D visualizer viewport around an explicit plotting group shared by the domain box, floor/grid, scale markers, slice planes, and point cloud. The MVP controls should be view/projection mode, zoom, and reset view rather than fake orbit/pan camera controls, with projection descriptions and scale markers visible at normal browser zoom.
- #121 adds explicit 3-D slice-plane controls: horizontal `z` slices can move up/down, vertical `x-z` slices can move through `y`, and vertical `y-z` slices can move through `x`. These controls reuse the backend slice API and remain native-grid selectors, not interpolation or true camera rotation.
- #125 refactors the visualizer into a fixed scientific workbench: primary visual controls sit beside the viewport, timeline and slice-position controls sit below the render, technical details move to a secondary panel, and axes/scale/annotation labels stay readable outside the zoomed data layer. Browser visual checks are required for layout changes so the scene cannot cover controls again.
- #172 redesigns Explore around one primary visualization plus one explanation panel. The visible interaction should be `What happened here?`; technical Thermal Fate/process controls, rendering details, and provenance stay accessible without dominating the first read.
- #184 consolidates the former `2-D Slices` / `3-D View` scaffold into one desktop Explore workflow. The current target is compact selected-result context, shared field/time/slice controls, 3-D `qc` cloud-water context, a visible native-grid slice plane, the matching 2-D slice inspector, and selected-cell `What happened here?` diagnostics. `w` and other broader fields are inspected through slices, not through fake 3-D point rendering.
- #185 cleans the Explore test suite after #184 so tests protect the unified workflow rather than the old separate `2-D Slices` / `3-D View` scaffold.
- #177 keeps older visualizer-roadmap language from pulling near-term work back toward renderer polish before the UX/product loop is stable.
- #196 cleans up process evidence focus states in Explore. The primary `Explanation focus` control should be result-aware and show only supported or useful candidate modes; missing/future diagnostics remain visible under a collapsed `Not available for this result` section with evidence requirements and caveats.
- #112 is the renderer-upgrade decision point after the simplified Explore loop is stable.
- #80 plans visual polish, fly-through/move-through, cinematic export, and thumbnail/preview policy later. It must not add rendering dependencies or implementation code.

Recommended implementation order:

```text
#68 NetCDF ingest
-> #69 diagnostics
-> #70 result cards / notebook entries
-> #71 Results Library UI
-> #72 visualization-ready data contract
-> #73 2-D field inspection
-> #77 3-D scene shell
-> #78 cloud-water rendering
-> #79 slice planes
-> #169 selected-result trust states
-> #170/#171 notebook visual system and Results
-> #175 What happened here? interaction model
-> #172/#184 unified Explore explanation workflow
-> #185 Explore test cleanup
-> #112 renderer upgrade decision later
-> #80 visual polish / fly-through / export later
```

Explore should open from saved or ingested results, should not require rerunning CM1, and should label visual output as an interpretation of CM1-derived data with clear provenance and rendering-method labels.

## M5 Visual Polish + Export

Goal: improve visual quality and communication once the CM1/results pipeline is solid.

Deliverables:

- volumetric ray marching.
- shadows.
- edge brightening.
- cloud-base darkening.
- fly-through/move-through.
- cinematic export.
- thumbnails/previews with strict generated-artifact policy.

Implementation anchor:

- #80 plans post-MVP visual polish, fly-through/move-through, cinematic export, and generated thumbnail/preview policy. These are later features, not prerequisites for the first inspectable CM1 result loop.
- Rendering remains an interpretation of CM1-derived data. Future polish must preserve provenance labels for source model, run/result, field, processing method, rendering method, units, and caveats.
- Candidate post-MVP work includes volumetric ray marching, shadows, edge brightening, cloud-base darkening, fly-through or move-through camera modes, cinematic still/video export, and generated thumbnails/previews for saved results.
- Generated visual artifacts remain local/generated outputs by default. Do not commit thumbnails, videos, render caches, large processed visualization data, or generated previews unless a future issue defines a strict tiny-fixture policy.
- M5 and broader renderer/scenario expansion should start only after the local product loop is useful and stable: Build can package/launch/ingest, Results can review/save/compare, Storage can manage runtime files safely, unified Explore can explain selected results/regions, and tests cover the current loop with mocked local state.

## Initial Lower-Atmosphere Scenario Set

M1 should include:

1. Baseline shallow cumulus.
2. Dry failed cumulus.
3. Capped/suppressed cumulus.
4. Humid vigorous cumulus / humid low-cloud contrast.
5. Low stratus / low-cloud layer.
6. Warm rain / precipitating shallow cloud.

Baseline shallow cumulus is the first hero case. Warm rain remains early, but it should not block the baseline Golden Path.

Initial lower-atmosphere templates live under `scenarios/lower-atmosphere/` and should validate against the scenario schema before any package generation work uses them. The templates include teaching goals, expected diagnostics, run-size preset notes, limitations, and one-control variation metadata.

Initial controls should be atmospheric and curated, such as low-level humidity, surface heating, surface moisture, cap strength, cap height, dry air aloft, and mixing/entrainment. Raw namelist fields belong in advanced/developer views.

First variations should favor one-control-at-a-time changes around baseline rather than arbitrary large parameter sweeps.

Future scenario roadmap:

- Dry Failed Cumulus: moisture-limited failed cumulus with thermals and
  meaningful vertical motion but little/no `qc`.
- Terrain/orographic cloud.
- Layered atmosphere.
- Fog / near-surface cloud.
- Mixed-phase / ice.
- More precipitation workflows beyond warm rain.

## Startup Backlog

The canonical startup backlog now lives in GitHub issues and milestones:

- M0 Repo Foundation
- M1 Scenario Package Spine
- M1.5 Golden Path Manual CM1 Validation
- M2 Local CM1 Run Manager
- M3 Results Library + Experiment Notebook
- M4 Unified Explore MVP
- M5 Visual Polish + Export

Issue work should remain scoped, testable, and honest about whether it is preview guidance, generated CM1 configuration, running/completed CM1 result, or visualization interpretation.
