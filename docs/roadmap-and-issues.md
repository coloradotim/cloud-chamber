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
- save/name/tag/search/filter/delete.
- result-card / experiment-notebook model.
- open saved result in visualizer.
- duplicate/tweak/rerun foundation later, after replay/inspect/save is reliable.

Implementation anchor:

- #30 should make replayable/inspectable saved result cards the core behavior. Duplicate/tweak/rerun should remain optional or later.

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

- #31 should open from saved results, support time replay and camera exploration, avoid requiring reruns, and display provenance/rendering-method labels.

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
