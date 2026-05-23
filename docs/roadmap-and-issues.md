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
-> 3-D visualization
```

CM1 remains the source of truth. Preview estimates are guidance only, and visualization is an interpretation of CM1-derived data.

Cloud Chamber is a personal, scientifically honest CM1 cloud playground: curated lower-atmosphere experiments, meaningful controls, local-first CM1 runs, replayable saved results, and a beautiful 3-D viewer.

Replay / inspect / save is core MVP. Duplicate / tweak / rerun is later.

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
-> open 3-D visualizer
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
- #71 adds the first frontend Results Library shell over the #70 API: a scan-friendly results table, selected result detail/notebook card, diagnostics/caveats/output summaries, saved/protected state, and editable name/tags/notes. It must not implement replay or 3-D visualization.
- #98 refactors the frontend into a guided MVP workspace: `Build`, `Results`, `Inspect`, and `Visualize`. The default landing path should be `Results -> validated quick-look baseline -> Open 3-D`, with user-facing result labels in the primary UI and raw lifecycle/provenance labels under technical details.
- #83 makes NetCDF ingest evaluate the full CM1 model-output sequence instead of only the first file. It must classify `cm1out_*.nc` model-field files separately from `cm1out_stats.nc`, record total output files/time steps and first/last time, and run diagnostics across the full sequence before concluding whether clouds formed.
- #84 follows the full-sequence ingest evidence from #83: `dry-run-157b09a178e1` evaluated 25 model-output files, but the run still had no cloud, no vertical motion, and NaN/Infinity caveats. The next Baseline Shallow Cumulus package keeps the BOMEX-style quick-look approach but switches to fixed small ocean roughness. A fixed-roughness validation run completed and produced NetCDF output, but still showed no cloud or vertical motion, so #84 remains the active calibration path for deeper CM1 namelist/sounding work.
- #87 supersedes incremental tuning of the invalid quick-look derivative. It recovers Baseline Shallow Cumulus from CM1's local `les_ShallowCu` reference case, preserving the reference grid, runtime, domain top, damping, surface/ocean/flux settings, and stress path while keeping NetCDF output as the intentional ingest-path change. The first reference-derived validation run completed and ingested successfully with `cloud formed; rain detected`, so quick-look scaling should resume from this recovered baseline one change at a time.
- The updated #84 scope derives the first quick-look Baseline Shallow Cumulus variant from the validated #87 baseline by changing only runtime timing: `timax = 10800.0` and `tapfrq = 900.0`. All reference-derived grid/domain/surface/damping/boundary settings and NetCDF output remain preserved. The first quick-look validation run completed and ingested successfully with `cloud formed; rain detected`, 13 model-output time steps, first cloud at 1800 seconds, package size 206 MB, and preserved reference-derived settings.
- #102 switches Baseline Shallow Cumulus package generation onto CM1's external `input_sounding` route (`isnd = 17`) while preserving the validated `les_ShallowCu` grid/domain/runtime/surface/damping/boundary settings and wind profile. The validation run completed and ingested successfully with `cloud formed; rain detected`, 13 model-output time steps, first cloud at 1800 seconds, `max_qc_kg_kg = 0.001976807601749897`, and `max_w_m_s = 6.270190238952637`. This creates the prerequisite profile path for Dry Failed Cumulus moisture experiments.
- #103 implements Dry Failed Cumulus as the first moisture-limited contrast case from the accepted external-sounding baseline. The generated package preserves the Baseline Shallow Cumulus namelist family and changes only the lower-atmosphere moisture profile for the `low_level_humidity = drier` control. The validation run `dry-run-dry-failed-cumulus-20260522192000` completed and ingested successfully with 13 model-output time steps, `no cloud formed; no rain detected`, `max_qc_kg_kg = 0.0`, `max_w_m_s = 1.949130654335022`, and `min_w_m_s = -1.0865488052368164`. This establishes the first useful lab pair: Baseline forms cloud; Dry Failed has thermals without meaningful cloud water.

## M4 3-D Visualizer MVP

Goal: deliver the main payoff: inspect CM1 cloud evolution in 3-D.

Deliverables:

- 3-D scene shell.
- orbit/pan/zoom/reset camera.
- time slider/replay.
- field selector.
- horizontal/vertical slices.
- cloud-water isosurface or opacity approximation.
- simple lighting.

Implementation anchor:

- #31 has been superseded by staged visualizer implementation issues. It captured the right broad goal, but was too large to implement safely as one PR.
- #72 defines and implements the backend visualization-ready data contract. The browser should not parse raw NetCDF directly; it should consume fields and JSON slice payloads from backend endpoints. The MVP supports `qc` and `w`, native grids (`zh/yh/xh` for `qc`, `zf/yh/xh` for `w`), provenance/rendering labels, finite/non-finite stats, and vertical unit display metadata without interpolation.
- #73 builds the 2-D field inspection MVP on top of the #72 fields/slice API before the full 3-D viewer so field orientation, time indexing, vertical coordinates, scaling, and basic cloud evolution can be checked. It opens from the Results Library detail, enables field/time selection, shows horizontal and vertical slices, and keeps the browser away from raw NetCDF parsing.
- #77 builds the 3-D scene shell from the Results Library detail: scene container, orbit/pan/zoom controls, reset camera, time slider shell, field selector shell, loading/empty/error states, and provenance/rendering labels. It does not render cloud water, slices, or raw NetCDF data in the browser.
- #78 renders the first cloud-water field from visualization-ready data as a thresholded `qc` point cloud. The backend selects native-grid points and the browser renders only that payload; no raw NetCDF parsing, interpolation, isosurface extraction, ray marching, or cinematic lighting belongs in this step.
- #79 adds horizontal and vertical slice planes using the same provenance-labeled #72 slice API and native-grid caveats. Slice-plane time stays synced with the point cloud, supports `qc` and `w`, and remains an inspection overlay rather than raw NetCDF parsing or volumetric rendering.
- #98 also makes Inspect and Visualize inherit the selected result and default to an interesting time: first cloud when available, otherwise max cloud-water time if available, otherwise latest output. Technical rendering/provenance details stay available but secondary.
- #100 sharpens the first usable inspection path: Results should surface the validated quick-look baseline, successful cloud-forming runs with caveats should read as `Minor caveat` rather than failed review states, the 2-D inspector should show slice heatmaps before raw matrix values, and the 3-D viewer should open with visible cloud-water points plus readable slice context.
- #80 plans visual polish, fly-through/move-through, cinematic export, and thumbnail/preview policy after the practical 3-D MVP. It must not add rendering dependencies or implementation code.

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
-> #80 visual polish / fly-through / export later
```

The 3-D visualizer should open from saved or ingested results, should not require rerunning CM1, and should label visual output as an interpretation of CM1-derived data with clear provenance and rendering-method labels.

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
- M5 should start only after the inspectable result loop is useful: NetCDF ingest, diagnostics, result cards, Results Library UI, visualization-ready data, 2-D field inspection, 3-D scene shell, thresholded cloud-water rendering, and slice planes.

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
- M4 3-D Visualizer MVP
- M5 Visual Polish + Export

Issue work should remain scoped, testable, and honest about whether it is preview guidance, generated CM1 configuration, running/completed CM1 result, or visualization interpretation.
