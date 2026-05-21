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

## Runtime Tiers

Cloud Chamber should support run-size presets that make local cost and confidence visible:

- **Quick look**: roughly 10-20 minutes when feasible on the local Mac; used for sanity checks, setup inspection, and rough cloud behavior.
- **Standard**: normal personal exploration run; used for useful saved results and diagnostics.
- **Deep / overnight**: longer richer runs that may take hours or overnight; used for prettier, more detailed, or higher-confidence result exploration.

Runtime estimates are approximate until locally validated. The MVP should assume a 2024 MacBook Air with 8GB RAM, one local CM1 run at a time, conservative output handling, and backend-side processing/downsampling.

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

The dry-run package flow must be followed directly by local CM1 launch/monitoring work. Dry-run generation is a stepping stone, not a dead end.

## M1.5 Golden Path Manual CM1 Validation

Goal: prove the Baseline Shallow Cumulus package path against a real local CM1 run before broadening product scope.

Deliverables:

- Golden Path validation plan.
- run-size preset notes from local/manual execution.
- generated package inspection checklist.
- launch/log/status checklist.
- first diagnostics capture: first cloud time, cloud base/top, max updraft, cloud-water summary, and rain onset if present.
- result-card/notebook acceptance notes.
- visual inspection notes.

This milestone remains local/manual/offline. CI should not run real CM1.

## M2 Local CM1 Run Manager

Goal: make Cloud Chamber actually launch and monitor local CM1 runs.

Deliverables:

- Local CM1 launcher.
- stdout/stderr capture.
- lifecycle state management.
- cancel/failure handling.
- overwrite protection.
- local/manual validation path.

## M3 Results Library + Experiment Notebook

Goal: turn CM1 outputs into replayable, inspectable, searchable experiment notebook entries.

Deliverables:

- NetCDF ingest.
- run metadata extraction.
- diagnostics summary.
- logs/result status.
- save/name/tag/search/filter/delete.
- result-card / experiment-notebook model.
- open saved result in visualizer.
- duplicate/tweak/rerun foundation later, after replay/inspect/save is reliable.

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
