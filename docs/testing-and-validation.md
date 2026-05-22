# Testing And Validation

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer. Tests must preserve that distinction.

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

NetCDF ingest tests use tiny synthetic NetCDF files in temporary run directories. They should assert valid metadata extraction, result metadata serialization, missing-output failures, malformed-NetCDF failures, missing expected field warnings, and that raw `.dat/.ctl` artifacts are cataloged but not treated as NetCDF input. These tests must not use real CM1 output.

Multi-file NetCDF ingest tests should use tiny generated fixtures under temporary run directories. They should cover CM1-style sequences such as `cm1out_000001.nc`, `cm1out_000002.nc`, and `cm1out_stats.nc`; verify model-field files are sorted by output index; exclude or separately classify stats NetCDF files; count total model output files and time steps; preserve first/last output time; record direct-vs-inferred time handling; tolerate corrupt individual output files with caveats when enough valid files remain; and ensure diagnostics time series span the full model-field sequence. A full-run no-cloud result is meaningful only after all usable model-output files have been evaluated.

Baseline Shallow Cumulus diagnostics tests use tiny synthetic NetCDF fixtures only. They cover no-cloud and cloud-formed cases, the `qc >= 1e-6 kg/kg` threshold, the minimum 10 cloudy grid-cell rule, first cloud time, cloud base/top from vertical coordinates, max `qc`, `qc` max time series, cloud fraction time series, max/min `w`, optional `qr` rain detection with `qr >= 1e-7 kg/kg`, missing `qc`/`w`/`qr`, NaN/infinity handling, entirely non-finite fields, NetCDF time-coordinate use, and inferred output-index fallback. These diagnostics are learning summaries, not morphology validation.

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
