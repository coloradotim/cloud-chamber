# Testing And Validation

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local
experiment builder, run manager, result notebook, diagnostics layer, and
visualizer. Tests must preserve that distinction.

## Fast CI Tests

Fast CI tests run on every pull request and push to `main`.

- Frontend lint, unit tests, and build.
- Backend ruff format/check, mypy, and pytest.
- Shell script syntax checks.
- JSON/YAML sanity checks where practical.
- `scripts/check.sh` executable-bit assertion.
- forbidden tracked artifact checks.

Implemented fast tests cover:

- scenario schema validation
- quick/standard/deep runtime preset metadata validation
- physical question and learning-goal metadata validation
- one-control-at-a-time variation metadata validation
- generated manifests and dry-run packages
- product state/provenance label validation
- CM1 path/settings handling through local runtime settings
- run-package generation using temp directories
- frontend component tests for Scenario Builder behavior, dry-run review, and preview-not-implemented state distinctions
- local CM1 launcher command construction, one-run-at-a-time behavior, manifest state transitions, log capture, cancellation, missing-settings failure, and overwrite protection with fake subprocesses

Future fast tests should cover:

- result-card / experiment-notebook metadata serialization
- visualizer metadata loading when that layer exists

These tests must not require CM1 source, CM1 binaries, NetCDF output, generated run directories, or large local data.

Scenario-template tests should cover both valid templates and targeted invalid templates, including missing product-facing controls, invalid choice defaults, missing runtime profiles, and variation policies that reference unknown controls. These tests validate metadata only; they do not generate CM1 output or launch CM1.

CM1 input contract tests should use structured/snapshot assertions for generated fragments such as namelist defaults and input-sounding notes. These tests must not write generated run packages into the repo, launch CM1, or require real CM1 runtime files.
Baseline Shallow Cumulus input tests should assert the generated `namelist.input` is no longer the old `&cloud_chamber_domain` placeholder fragment and that generated `input_sounding` is numeric/CM1-readable rather than notes-only.

Dry-run package tests should use temporary runtime homes and assert overwrite protection, manifest/report content, CM1-facing input readiness, and absence of NetCDF output. A dry-run package is packaged configuration and metadata only; it is not a launched process or completed CM1 result.

Local launcher tests must inject fake subprocess handles. They should assert command construction, stdout/stderr log capture, one-active-run refusal, queued/running/completed/failed/canceled state transitions, missing-settings failure, and protection against pre-existing output-like files. They must not launch real CM1 or require local runtime files in CI.
They should also assert placeholder-only packages are rejected before launch, Rayleigh damping/domain checks catch damping over more than half the domain, required runtime files such as `LANDUSE.TBL` are staged from temp CM1 run directories, `.dat/.ctl` and NetCDF output artifacts are cataloged separately in the manifest, stderr floating-point flags are surfaced as runtime warnings, and exit code 0 without output becomes `needs_review` rather than `completed_cm1_result`.

Runtime storage tests must use temporary runtime homes only. They should cover total runtime-home size, the 50 GB warning-threshold fields, per-run sizes, largest-run ordering, valid manifest classification, missing and malformed manifests, dry-run delete previews, confirmed deletion of one selected run directory, and refusal cases for running runs, saved/protected runs, path traversal, runtime-home self-targeting, and symlink escapes. They must not read from or delete real `~/CloudChamber`, the source repo, or the external CM1 installation.

Runtime storage UI tests should mock the storage inventory and delete endpoints. They should verify the 50 GB warning state, largest-run table, completed/saved/running/missing-manifest categories, disabled cleanup for running and saved/protected runs, dry-run delete preview, explicit confirmed delete, and visible backend failure messages. Automated UI tests must not delete real local run directories.

## UI Testing Standard

For UI issues, do not rely only on `scripts/check.sh` and component tests. Use
the right layer for the work:

```text
unit/component tests:
  logic, rendering branches, API-shape handling, small component behavior

Playwright/browser tests:
  user workflows, navigation, tab behavior, form flows, save/delete flows,
  console-error hygiene, layout regressions, occlusion/overlay bugs,
  critical Build -> Results -> Explore paths

manual QA:
  qualitative UX and science judgment only
```

Manual QA should not be a broad checklist of objective behaviors. Objective
checks should become automated tests. Manual review should focus on things
automation cannot judge well: visual plausibility, scientific trust, wording
clarity, workflow clarity, whether the page teaches the right lesson, whether a
visualization feels physically believable, whether saved/delete/protection
semantics feel safe, and whether the experience is enjoyable rather than
debug-like.

For any issue that changes navigation, Results, Storage, Compare, Explore,
Build workflow, or visualizer layout:

- add or update unit/component tests for logic;
- add or update Playwright tests for user-path/browser behavior;
- run `scripts/check.sh`;
- run `scripts/check-e2e.sh` when the change affects user workflows or layout;
- use manual QA only for qualitative judgment, not as a substitute for tests.

When manual review is needed, keep it focused:

1. What user goal is being evaluated?
2. What screenshots or flows should be reviewed?
3. What qualitative judgment is needed?
4. Which objective checks should become automated tests?
5. What follow-up issue, if any, is needed?

Good manual QA asks whether the 3-D cloud geometry looks physically plausible
in side `x-z` view, whether Baseline vs Dry Failed teaches the
moisture-limitation story, or whether Storage makes deletion feel safe. Bad
manual QA asks someone to click every tab, verify all standard navigation by
hand, or manually inspect long objective checklists.

The Playwright suite lives under `app/frontend/e2e/`:

- `mocked-smoke/` is deterministic, uses mocked API routes, and is what
  `scripts/check-e2e.sh` runs by default;
- `local-data/` is read-only against a live local backend and may skip when
  required local results or runtime data are absent;
- `visual-manual/` performs partial browser checks for layout-heavy visualizer
  behavior and records the qualitative question that still needs human eyes.

Playwright reports, screenshots, videos, traces, NetCDF files, logs, generated
run directories, and other runtime artifacts are not source fixtures and should
not be committed. Known product follow-ups surfaced while stabilizing the suite
are tracked in #133, #134, #135, #136, and #139; future skips should identify
the missing prerequisite or linked issue rather than hiding a failure.

Codex UI PR summaries should explicitly report:

```text
Unit/component tests added or updated:
Playwright tests added or updated:
Manual QA needed:
  yes/no
  if yes, what qualitative question should Tim review?
Commands run:
  scripts/check.sh
  scripts/check-e2e.sh, if applicable
```

NetCDF ingest tests use tiny synthetic NetCDF files in temporary run directories. They should assert valid metadata extraction, result metadata serialization, missing-output failures, malformed-NetCDF failures, missing expected field warnings, and that raw `.dat/.ctl` artifacts are cataloged but not treated as NetCDF input. These tests must not use real CM1 output.

Multi-file NetCDF ingest tests should use tiny generated fixtures under temporary run directories. They should cover CM1-style sequences such as `cm1out_000001.nc`, `cm1out_000002.nc`, and `cm1out_stats.nc`; verify model-field files are sorted by output index; exclude or separately classify stats NetCDF files; count total model output files and time steps; preserve first/last output time; record direct-vs-inferred time handling; tolerate corrupt individual output files with caveats when enough valid files remain; and ensure diagnostics time series span the full model-field sequence. A full-run no-cloud result is meaningful only after all usable model-output files have been evaluated.

Baseline Shallow Cumulus diagnostics tests use tiny synthetic NetCDF fixtures only. They cover no-cloud and cloud-formed cases, the `qc >= 1e-6 kg/kg` threshold, the minimum 10 cloudy grid-cell rule, first cloud time, cloud base/top from vertical coordinates, max `qc`, `qc` max time series, cloud fraction time series, max/min `w`, optional `qr` rain detection with `qr >= 1e-7 kg/kg`, missing `qc`/`w`/`qr`, NaN/infinity handling, entirely non-finite fields, NetCDF time-coordinate use, and inferred output-index fallback. These diagnostics are learning summaries, not morphology validation.

Result Card / Experiment Notebook tests should use tiny synthetic NetCDF
fixtures and temporary runtime homes. They should cover creating a card from
ingested metadata, listing/getting cards, updating name/tags/notes, saving and
protecting cards, missing diagnostics, provenance labels, output file summary,
and serialization round trips. They must not use real CM1 output.

Visualization-ready data contract tests should use tiny synthetic NetCDF
fixtures and temporary runtime homes only. They should cover the fields endpoint,
`qc` and `w` availability, missing `qc`/`w`, horizontal and vertical slices,
native `zh/yh/xh` and `zf/yh/xh` grids, bad field/time/level errors,
provenance labels, JSON array shape/order, finite and non-finite stats, and
safe vertical kilometer-to-meter display conversion. They must not implement UI,
rendering, interpolation, or large-output processing.

Thermal Fate process-diagnostics tests should use tiny synthetic NetCDF
fixtures and temporary runtime homes only. They should cover thermal-fate labels
and confidence states, supported / candidate / insufficient-evidence language,
global process diagnostics, selected-region diagnostics, comparison diagnostics,
and unavailable/candidate/supported states for deep breakthrough and
precipitation feedback. Surface-heating scenario tests should cover product
metadata and package-generation contracts without exposing raw namelist fields
as the primary UI.

Thermal Fate tests must distinguish direct CM1 fields, derived diagnostics,
proxy diagnostics, and unsupported claims. Missing fields should produce
explicit caveats, not crashes or fabricated values. The browser must not parse
raw NetCDF, and CI must not run real CM1.

2-D field inspector component tests should mock the visualization-ready API
payloads rather than reading NetCDF in the browser. They should cover opening
from a Result Card, field selection, time selection, backend-provided
interesting defaults, a single-primary-slice layout, compare mode, horizontal
and vertical slice heatmaps, units, min/max, finite/non-finite counts,
provenance labels, raw numeric values under technical details, missing fields,
and bad slice requests. They must not add rendering dependencies or test a 3-D
scene.

Guided workspace tests should cover task navigation across the top-level
`Build`, `Results`, and `Explore` sections. They should verify that Results
contains `Notebook`, `Compare`, and `Storage` sub-tabs; Explore contains `2-D
Slices` and `3-D View`; the app still defaults to Results; selected-result
context flows from Results into Explore; and the old implementation pages
(`Compare`, `Storage`, `Inspect`, `Visualize`) are no longer top-level
workspaces. They should also cover prioritizing a validated cloud-forming
quick-look baseline over historical attempts, user-facing status labels
replacing raw internal lifecycle strings, and technical details keeping raw
provenance available without dominating the main view. They should distinguish
successful cloud-forming results with minor caveats from results that truly need
review.

Guided local run workflow tests should mock the backend API sequence rather
than launching CM1: package generation, launch request, running status, completed
status with output-artifact counts, ingest request, and post-ingest actions into
Results and Explore. They should also cover missing local CM1
settings or preflight failures as actionable UI errors. Automated tests must not
execute `cm1.exe`, parse real local NetCDF output in the browser, or write
generated run directories into the repo.

Comparison tests should use mocked Result Card data for the accepted Baseline
Shallow Cumulus quick-look and Dry Failed Cumulus quick-look pair. They should
verify side-by-side scenario names, run-size presets, cloud/rain outcomes, first
cloud time, max `qc`, max/min `w`, caveats, output summaries, saved/protected
state, moisture-limited interpretation, missing-pair handling, and quick actions
that route to Explore / 2-D Slices and Explore / 3-D View.

Side-by-side slice comparison tests should mock the #72 visualization-ready
fields/slice API for both accepted results. They should cover default Baseline
vs Dry Failed selection, `qc` comparison, `w` comparison, missing shared fields,
time-index mismatch labeling where practical, units, min/max, finite/non-finite
counts, provenance labels, and the guarantee that raw NetCDF is not parsed in
the browser.

3-D scene shell component tests should also mock the visualization-ready field
catalog instead of reading NetCDF in the browser. They should cover opening from
a Result Card, scene container rendering, projection/view controls, zoom/reset
view controls, time slider shell, field selector shell, interesting-time/default
slice selection, first-cloud/max-cloud/max-updraft jump controls, domain box,
axes/height/floor labels, scale markers, fixed workbench regions, stable
data-layer transforms, projection descriptions, provenance/rendering details,
and no-field/error states. They must not assert isosurfaces, true camera
orbit/pan behavior, or volumetric effects until later visualizer issues
implement those layers.

Cloud-water point-cloud tests should use tiny synthetic NetCDF fixtures on the
backend and mocked visualization-ready point payloads on the frontend. Backend
tests should cover `qc` points above threshold, no points above threshold,
missing `qc`, bad time/threshold/max-point inputs, deterministic stride
downsampling, stats, full coordinate extents, active `z` range, max-value
location, coordinate units, and provenance labels. Frontend tests should cover
rendered point-cloud state, missing `qc`, no-cloud-above-threshold state,
threshold/time/opacity/point-size controls, side/elevation projection controls
where model `z` is the visual height, domain extent/debug labels,
provenance/rendering labels, and the guarantee that the browser does not parse
raw NetCDF. These tests must not add ray marching, isosurfaces, shadows,
fly-through, export, or generated CM1 output.

Viewport-stability tests should verify that the domain box, floor/grid, slice
planes, and cloud-water point cloud live inside the same zoomable data layer,
that axes/scale markers remain outside that zoomed layer and readable, that the
workbench exposes primary controls, viewport, bottom timeline/slice controls,
and technical details as separate regions, and that reset view restores zoom and
projection defaults. Side views should state that height is vertical, top-down
should state that height is not shown vertically, and oblique should be labeled
an interpretive overview rather than a true perspective camera.

The consolidated Results/Explore shell and fixed visualizer workbench should
also get a real browser smoke check after
layout changes, not only component tests. Open the app, navigate to Results,
open the validated quick-look baseline in Explore / 3-D View, and confirm by screenshot
or direct browser inspection that the render viewport does not cover primary
controls, bottom controls, or technical details. At minimum verify that the
primary control rail, fixed viewport, timeline/slice-position strip, and details
panel are all reachable while cloud-water points and slice planes remain visible
inside the viewport.

3-D slice-plane tests should mock the #72 visualization-ready slice API. They
should cover horizontal and vertical slice planes, `qc` and `w` field selection,
time synchronization with the 3-D point cloud, native-grid caveats/provenance
labels, selected-time max `qc`/`w` default locations, slice-plane show/hide
behavior, view presets, explicit horizontal `z`, vertical `x-z`, and vertical
`y-z` orientation controls, up/down or forward/back level-index movement, and
clear error states for missing fields or bad slice requests. They must not parse
raw NetCDF in the browser, add rendering dependencies, or test ray marching,
cinematic lighting, export, fly-through, or generated CM1 output.
Visual first-impression tests should also keep the validated quick-look baseline
on a cloud-bearing time, show a visible point-cloud state, keep slice planes
optional and secondary, and keep technical provenance reachable without making
it the primary reading path.

CM1 runtime floating-point exception flags such as `IEEE_INVALID_FLAG`, `IEEE_DIVIDE_BY_ZERO`, and `IEEE_OVERFLOW_FLAG` should be preserved as caveats. Automated diagnostics should then check whether target fields contain non-finite values. If `qc`, `w`, and `qr` are finite/usable, diagnostics can complete with the runtime warning still visible. If root-cause investigation requires CM1 source-level debugging, that belongs in a separate issue rather than CI.

Local validation uses `scripts/check.sh` as the canonical gate. CI mirrors it through split equivalent jobs so branch protection can require `Frontend`, `Backend`, and `Scripts and config` independently. Keep the local script and CI jobs in sync as new implemented layers add fast checks.

## Local CM1 Workflow Tests

Use fake or minimal fixtures for:

- scenario schemas
- config generation
- run manifest creation
- fake process execution
- tiny NetCDF ingestion fixtures when that layer exists
- visualizer metadata loading

Small fixtures may be committed when they are intentionally tiny and do not include real generated CM1 output.

Committed NetCDF fixtures must be tiny, synthetic, intentional, and documented under a test fixture path. Real CM1 outputs are local/manual/offline artifacts and must stay out of git.

If a tiny synthetic NetCDF fixture is needed later, create it with a deterministic test helper or fixture-generation script, keep only the smallest fields needed by the test, document the generating command and intended assertions next to the fixture, and confirm it is not copied from a real CM1 run. Do not commit broad sample outputs, local run directories, or generated validation reports.

## Real CM1 Validation

Real CM1 runs are local/manual/offline validation. They are useful for scientific confidence but should not be required in CI.

The Baseline Shallow Cumulus Golden Path is the first manual/local acceptance target. Quick/standard/deep runtime tiers should be validated in CI through schema/config tests, not by running CM1.

Replay / inspect / save is core MVP and should be covered by future metadata, serialization, and UI tests. Duplicate / tweak / rerun is later and should not be required by first result-library tests.

Warm rain remains early, but baseline shallow-cumulus tests and manual validation should not be blocked on warm-rain behavior.

Manual validation should record:

- the physical question being tested
- the scenario controls used
- the CM1 version and local runtime path
- the Cloud Chamber commit
- the run-size preset
- the grid/domain, runtime, and output cadence
- diagnostics such as cloud base, cloud top, first cloud time, rain onset, and updraft strength
- cloud-water max or summary
- log warnings/errors
- limitations and interpretation notes
- visual inspection notes

Validation notes should be written as docs or issue comments when useful. Local validation reports generated by tools should stay gitignored unless a future policy explicitly allows a tiny committed fixture/report.

Manual baseline shallow-cumulus acceptance should capture:

```text
physical question
run-size preset
CM1 version/path
grid/domain
runtime
output cadence
generated CM1-facing files reviewed
first cloud time
cloud base/top
max updraft
cloud water
rain onset if present
logs
result card / notebook fields
visualizer provenance labels
visual inspection notes
```

The first full-sequence NetCDF re-ingest of `dry-run-157b09a178e1` evaluated 25 model-output files from 0 to 7200 seconds and still found no cloud formation, with `max_qc_kg_kg = 0.0`, `max_w_m_s = 0.0`, and NaN/Infinity caveats in target and surface fields. A fixed-roughness quick-look derivative, `dry-run-calibration-20260522132903`, completed with NetCDF output but still found no cloud formation, no vertical motion, and NaN/Infinity caveats. The accepted recovery path is now to start from CM1's `les_ShallowCu` reference case, preserve its science/numerics, validate that reference-derived package locally, and only then reintroduce quick-look scaling one change at a time.

The first reference-derived validation run, `dry-run-les-shallowcu-20260522140642`, completed with `exit_code = 0`, ingested 7 model-output time steps, and produced `cloud formed; rain detected`. Recorded diagnostics included first cloud time at 3600 seconds, `max_qc_kg_kg = 0.002192789688706398`, `max_w_m_s = 6.962291717529297`, `min_w_m_s = -3.7671568393707275`, and a vertical-coordinate caveat because cloud base/top units were reported as kilometers. This is the current baseline evidence for future quick-look downscaling.

The first quick-look variant should be validated as a runtime-only change from that recovered baseline: `timax = 10800.0` and `tapfrq = 900.0`. Tests must assert that the quick-look namelist still preserves the reference-derived grid/domain, surface stress/roughness path, moisture/sounding, surface fluxes, turbulence/SGS settings, damping settings, boundary conditions, NetCDF output, and reference `LANDUSE.TBL` staging behavior. Manual validation should then confirm whether the shorter run still forms useful cloud by the existing diagnostics.

The first quick-look validation run, `dry-run-quicklook-les-shallowcu-20260522151536`, completed with `exit_code = 0`, ingested 13 model-output time steps from 0 to 10800 seconds, and produced `cloud formed; rain detected`. Recorded diagnostics included first cloud time at 1800 seconds, `max_qc_kg_kg = 0.002192789688706398`, `max_w_m_s = 6.866957187652588`, `min_w_m_s = -4.21529483795166`, rain present, package size 206 MB, stderr `IEEE_UNDERFLOW_FLAG`, and the existing vertical-coordinate caveat because cloud base/top units were reported as kilometers.

External-sounding Baseline Shallow Cumulus reproduction should preserve the
validated reference-derived settings and change only the thermodynamic sounding
source from built-in `isnd = 19` to CM1's external `input_sounding` route
(`isnd = 17`). Automated tests should assert that generated packages still
preserve the reference grid/domain, runtime presets, wind profile, surface
flux/stress path, damping, turbulence/SGS settings, boundary conditions,
NetCDF output, and reference `LANDUSE.TBL` staging. Manual validation should
record whether the external-sounding reproduction still completes, produces
NetCDF, ingests the full sequence, forms cloud, and preserves meaningful
vertical motion before Dry Failed Cumulus dries the profile.

The external-sounding reproduction run, `dry-run-external-sounding-baseline-20260522185000`,
completed with `exit_code = 0`, ingested 13 model-output time steps from 0 to
10800 seconds, and produced `cloud formed; rain detected`. Recorded diagnostics
included first cloud time at 1800 seconds, `max_qc_kg_kg =
0.001976807601749897`, `max_w_m_s = 6.270190238952637`, `min_w_m_s =
-4.416495323181152`, rain present, stderr `IEEE_UNDERFLOW_FLAG`, and the
existing vertical-coordinate caveat because cloud base/top units were reported
as kilometers. This accepts the external-sounding baseline path for the next
moisture-limited Dry Failed planning step.

The first Dry Failed Cumulus validation run,
`dry-run-dry-failed-cumulus-20260522192000`, completed with `exit_code = 0`,
ingested 13 model-output time steps from 0 to 10800 seconds, and produced `no
cloud formed; no rain detected`. Recorded diagnostics included `max_qc_kg_kg =
0.0`, cloud fraction `0.0` at every output time, `max_w_m_s =
1.949130654335022`, `min_w_m_s = -1.0865488052368164`, rain absent, stderr
`IEEE_UNDERFLOW_FLAG`, and the existing vertical-coordinate caveat because
cloud base/top units were reported as kilometers. This is accepted as a
moisture-limited failed-cumulus case because vertical motion remains healthy
while cloud water and rain stay absent.

Dry Failed Cumulus validation should happen only after an external-sounding
Baseline Shallow Cumulus reproduction has been accepted. The future Dry Failed
run should be considered useful only if it is moisture-limited and numerically
healthy: CM1 exits cleanly, NetCDF output exists, full-sequence ingest succeeds,
`cloud_formed = false`, `rain_present = false`, `max_qc_kg_kg` stays below the
cloud threshold or fewer than 10 grid cells exceed it, `max_w_m_s` is
meaningfully nonzero, `min_w_m_s` is finite and preferably negative/nonzero,
and `qc`/`w`/`qv`/thermodynamic target fields do not carry severe NaN/Infinity
caveats. No cloud plus no vertical motion is not an accepted Dry Failed result.
No cloud plus NaNs/Infs is not an accepted Dry Failed result.

Baseline humidity ladder tests should assert that `low_level_humidity = drier`,
`baseline`, and `more_humid` emit the intended moisture-profile metadata and
change only the numeric moisture values in `input_sounding`. They should verify
the non-moisture reference settings stay fixed: grid/domain, runtime/cadence for
the selected preset, surface/ocean/flux settings, surface stress/roughness path,
Rayleigh damping, turbulence/SGS settings, boundary conditions, NetCDF output,
and runtime-file staging behavior. These tests must use temp dirs and must not
launch CM1 or commit generated output.

The first local quick-look validation for this ladder ran outside the repo under
the configured runtime home. `dry-run-004bd57bb8cc` validated the drier variant
as a dry/no-cloud contrast with finite vertical motion. `dry-run-4e64317c62ec`
validated the more-humid variant as an earlier/stronger cloud-forming case. The
generated NetCDF output, logs, result metadata, and copied runtime files remain
local generated artifacts and must not be committed.

Future Dry Failed manual validation should record:

```text
run ID and package path
validated baseline commit / package source
external-sounding reproduction evidence
the one intended moisture/sounding change
CM1 command, runtime, exit code, logs, and package size
NetCDF file count and full-sequence ingest status
cloud_formed and first_cloud_time
max_qc and cloud fraction summary
rain_present
max_w and min_w
main limiting factor: low-level moisture / saturation deficit
qc and w 2-D inspection notes
3-D cloud-water point-cloud absence/presence notes
caveats and target-field non-finite checks
```

Do not run Dry Failed CM1 cases in CI and do not commit generated output,
NetCDF files, logs, runtime files, local reports, or copied `LANDUSE.TBL`.

Capped / Suppressed Cumulus package tests use temporary runtime homes and assert
that `cap_strength = stronger` changes only the generated external
`input_sounding` stability structure near the cap while preserving the accepted
external-sounding baseline's grid/domain, runtime preset, surface/ocean/flux
settings, surface stress/roughness path, Rayleigh damping, turbulence/SGS
settings, boundary conditions, NetCDF output, `LANDUSE.TBL` staging behavior,
low-level humidity, and surface heating.

The first Capped / Suppressed stronger-cap validation run,
`dry-run-capped-suppressed-20260526015634`, completed local CM1 from the
generated package with `exit_code = 0`, produced NetCDF output, ingested 13
model-output time steps from 0 to 10800 seconds, and produced `cloud formed;
rain detected`. The package was 196 MB and runtime was about 48.7 minutes on the
local machine. Compared with the accepted external-sounding baseline, it
reduced cloud top from about 2.14 km to about 1.34 km, reduced
`max_qc_kg_kg` from 0.001976807601749897 to 0.0013941252836957574, reduced max
cloud fraction from about 0.01273 to about 0.00847, reduced max/min `w` from
about 6.27 / -4.42 m/s to about 3.52 / -1.67 m/s, and reduced max `qr` from
about `1.3015507647651248e-05` to `4.473397439141991e-06`. Rain still occurred
and first cloud time stayed at 1800 seconds, so the accepted status is
`accepted_with_notes` / cap-limited candidate. Stderr reported
`IEEE_UNDERFLOW_FLAG`; target diagnostics remained finite and usable, and the
existing cloud-base/top vertical-coordinate caveat remains because NetCDF
vertical coordinates are in kilometers.

Future Capped / Suppressed manual validation should record:

```text
run ID and package path
accepted external-sounding baseline source
the one intended cap/stability change
confirmation that low-level humidity remains baseline
confirmation that surface heating remains baseline
confirmation that cap height remains baseline
CM1 command, runtime, exit code, logs, and package size
NetCDF file count and full-sequence ingest status
cloud_formed and first_cloud_time
cloud_top compared with accepted baseline
max_qc and cloud fraction compared with accepted baseline
rain_present compared with accepted baseline
max_w and min_w
main limiting factor: cap / stability
qc and w 2-D inspection notes
3-D limited-growth inspection notes
caveats and target-field non-finite checks
```

Acceptance categories for future Capped / Suppressed validation:

- `accepted`: CM1 completes, NetCDF ingests, vertical motion remains meaningful,
  moisture remains baseline/available, cloud is shallower/weaker/delayed than
  baseline, cloud top is lower when cloud forms, max `qc` and/or cloud fraction
  are reduced, rain is absent or reduced, and no severe target-field caveats
  appear.
- `accepted_with_notes`: the run is healthy and cap effect is present but
  subtle, or rain still occurs while cloud top / max `qc` / cloud fraction are
  clearly reduced.
- `needs_calibration`: the run is too similar to baseline, becomes
  indistinguishable from Dry Failed, or current diagnostics cannot distinguish
  cap limitation clearly.
- `failed`: CM1 fails, NetCDF is missing, ingest fails, vertical motion is
  absent, severe NaN/Infinity caveats appear in target fields, or more than
  cap/stability changed unexpectedly.

Do not run Capped / Suppressed CM1 cases in CI and do not commit generated
output, NetCDF files, logs, runtime files, local reports, or copied
`LANDUSE.TBL`.

### Baseline Shallow Cumulus Manual Smoke-Run Loop

Use this loop after a dry-run package has been generated and before broader CM1 launcher work is trusted. This is a manual/local/offline validation path; do not run it in CI.

1. Generate or identify a Baseline Shallow Cumulus dry-run package under the local runtime home, normally `~/CloudChamber/runs/<run-id>/`.
2. Inspect the package before launch:
   - confirm `run_manifest.json`, `case_manifest.json`, `namelist.input`, `input_sounding`, `dry_run_report.json`, and `runtime_file_checklist.json` exist;
   - confirm the selected run-size preset, physical question, controls, expected diagnostics, and visualization defaults match the intended scenario;
   - confirm `dry_run_report.json` says CM1 was not launched and is not a completed result;
   - confirm `namelist.input` is not the old `&cloud_chamber_domain` placeholder fragment;
   - confirm `input_sounding` is not notes-only;
   - confirm Rayleigh damping matches the selected package mode. Compact quick-look derivatives must not damp more than half the domain; `les_ShallowCu` recovery packages should preserve the reference damping setting.
3. Compare generated files against the local CM1 runtime requirements:
   - check `~/CloudChamber/settings.json`, `CLOUD_CHAMBER_CM1_ROOT`, or the default probe paths;
   - expected local probes include `/Users/timpeterson/cm1r21.1` and `/Users/timpeterson/cm1r21.1/run`;
   - confirm the CM1 run directory contains the local executable, normally `cm1.exe`;
   - confirm required runtime files such as `LANDUSE.TBL` are available locally, but not copied into git.
4. Manually stage the package for CM1 according to the local CM1 build's expected run-directory behavior. Record whether files were copied, symlinked, or run in place.
5. Launch CM1 manually outside CI. Capture the exact command, CM1 version/path, start time, run-size preset, and Cloud Chamber commit.
6. Watch status and logs:
   - record queued/running/completed/failed/canceled observations;
   - preserve stdout/stderr or CM1 log paths for the future result notebook entry;
   - record warnings, errors, elapsed time, and any manual intervention.
7. Detect outputs without committing them:
   - record output directory and file names/counts;
   - confirm whether NetCDF files appeared;
   - if `.dat/.ctl` files appeared, record them as raw CM1 artifacts rather than ingested results;
   - estimate local output size;
   - surface stderr floating-point exception flags as caveats, not automatic failures;
   - leave NetCDF, `.dat/.ctl` output, logs, validation reports, copied runtime files, and generated run folders out of git.
   - if deleting local test runs, use the runtime storage preview first and confirm the selected path is under the configured runtime home.
8. If ingest tooling exists, run it locally and record the ingest status. Until then, note what a future ingest should read and any schema gaps found.
9. Record result-card/notebook acceptance notes:
   - scenario name and physical question;
   - controls used;
   - run-size preset;
   - CM1 version/path metadata;
   - output/log paths;
   - first cloud time, cloud base/top, max vertical velocity, cloud-water summary, and rain onset if present;
   - limitations and interpretation notes.
10. If visualizer tooling exists, open the result and record first visual inspection notes. Until then, record the expected visualizer entry point and provenance labels that should be shown later.

Exact cloud morphology is not a pass/fail criterion. The manual acceptance question is whether the generated package can lead to a scientifically honest local CM1 run whose logs, outputs, diagnostics, and limitations are recorded clearly enough for future replay/inspect/save behavior.

## Generated Output Policy

Never commit:

- CM1 source
- CM1 binaries
- NetCDF output
- generated run directories
- `LANDUSE.TBL`
- `local-data`
- local run folders
- local validation reports
- large processed visualization artifacts

Commit:

- code
- tests
- docs
- schemas
- scenario templates
- tiny fixtures
