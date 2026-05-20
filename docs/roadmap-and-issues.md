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

## M2 Local CM1 Run Manager

Goal: make Cloud Chamber actually launch and monitor local CM1 runs.

Deliverables:

- Local CM1 launcher.
- stdout/stderr capture.
- lifecycle state management.
- cancel/failure handling.
- overwrite protection.
- local/manual validation path.

## M3 Results Ingest + Library

Goal: turn CM1 outputs into reusable, searchable experiments.

Deliverables:

- NetCDF ingest.
- run metadata extraction.
- diagnostics summary.
- logs/result status.
- save/name/tag/search/filter/delete.
- duplicate/tweak/rerun foundation.

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
- M2 Local CM1 Run Manager
- M3 Results Ingest + Library
- M4 3-D Visualizer MVP
- M5 Visual Polish + Export

Issue work should remain scoped, testable, and honest about whether it is preview guidance, generated CM1 configuration, running/completed CM1 result, or visualization interpretation.
