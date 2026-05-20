# Testing And Validation

CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer. Tests must preserve that distinction.

## Fast CI Tests

Fast CI tests run on every pull request and push to `main`.

- Frontend lint, unit tests, and build.
- Backend ruff format/check, mypy, and pytest.
- Shell script syntax checks.
- JSON/YAML sanity checks where practical.

These tests must not require CM1 source, CM1 binaries, NetCDF output, generated run directories, or large local data.

## Local CM1 Workflow Tests

Use fake or minimal fixtures for:

- scenario schemas
- config generation
- run manifest creation
- fake process execution
- tiny NetCDF ingestion fixtures when that layer exists
- visualizer metadata loading

Small fixtures may be committed when they are intentionally tiny and do not include real generated CM1 output.

## Real CM1 Validation

Real CM1 runs are local/manual/offline validation. They are useful for scientific confidence but should not be required in CI.

Manual validation should record:

- the physical question being tested
- the scenario controls used
- the CM1 version and local runtime path
- diagnostics such as cloud base, cloud top, first cloud time, rain onset, and updraft strength
- limitations and interpretation notes

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
- local validation reports

Commit:

- code
- tests
- docs
- schemas
- scenario templates
- tiny fixtures
