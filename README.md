# Cloud Chamber

## See clouds from the inside

Cloud Chamber is a local, single-user atmospheric laboratory for exploring
scientifically meaningful cloud simulations. The current application provides
three Cloud Worlds:

| Cloud World | Current experience |
| --- | --- |
| **Trade Cumulus** | A three-dimensional shallow-cloud field with two retained Simulations, an Updraft Lens, direct field inspection, and one featured moisture Comparison. |
| **Mountain Waves** | A terrain-aware native two-dimensional x-z World with dry and moist Simulations, Field views, Wave Structure and Wave Cloud Lenses, and a working variation Lab. |
| **Supercells** | A coordinated three-dimensional storm view plus native x-y, x-z, and y-z evidence for a retained quarter-circle Supercell Simulation and three storm Lenses. |

The home also provides **Fun With Soundings**, a first-class non-World
atmospheric workbench. Its stable `/fun-with-soundings` route organizes work as
**Find Soundings**, **Candidates**, **Build & Run**, **Runs**, and **Explore**.
Direct non-World Explore routes use
`/fun-with-soundings/explore/{result_id}`. The selected atmosphere remains
visible as the user moves from source evidence through experiment setup.

The workbench reuses the existing package, queue, worker, ingest, storage, and
visualization services. **Runs** means technical execution; completed retained
work is an **Experiment** unless a current Cloud World inventory verifies its
stable **Simulation** identity and exact run/result linkage.

Cloud Chamber is not a forecasting product. It uses idealized and source-backed
CM1 experiments to make cloud structure and normally invisible atmospheric
processes visible.

## Current boundaries

The implemented application does not yet provide:

- one shared variation workflow across all three Worlds.

These are current limitations, not decisions to remove the corresponding
approved product concepts.

All three Cloud Worlds now persist the last coherent Explore state and named
Saved Views by stable World and Simulation identity. Saved Views reopen as live
examinations, support rename and delete, and report bounded incompatibility when
retained output changes or is unavailable. Per-Simulation Notes remain a
separate durable-content contract.

Ordinary Compare is available for real retained pairs in all three Worlds.
Coherent, stopped workspaces can be saved as immutable World-owned Saved
Comparisons and reopened directly as live examinations. Saved Comparisons are
local to the configured runtime home and do not synchronize between devices.

## Product authority

Read these documents before nontrivial product work:

1. [North Star](NORTH_STAR.md)
2. [Product Vision](docs/product/PRODUCT_VISION.md)
3. [Application Semantics](docs/product/APPLICATION_SEMANTICS.md)
4. [MVP](docs/product/MVP.md)
5. [Documentation Status and Authority](docs/DOCUMENTATION_STATUS.md)

Current software is described in:

- [Current State](docs/current/CURRENT_STATE.md)
- [Current Architecture](docs/current/CURRENT_ARCHITECTURE.md)

## Run locally

Prerequisites:

- Git and Bash;
- Node.js with npm; CI currently uses Node 22;
- Python 3.12 or newer;
- `lsof`.

Install frontend dependencies:

```sh
cd app/frontend
npm install
```

Install backend dependencies:

```sh
cd app/backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

From the repository root, start both servers:

```sh
scripts/dev.sh start
```

The default addresses are:

- frontend: `http://localhost:5173`
- backend: `http://127.0.0.1:8000`

Other server commands:

```sh
scripts/dev.sh status
scripts/dev.sh restart
scripts/dev.sh logs
scripts/dev.sh stop
```

Run the repository verification gate before opening a pull request:

```sh
scripts/check.sh
```

Run mocked browser checks separately:

```sh
scripts/check-e2e.sh
```

See [Development](docs/development/DEVELOPMENT.md) and
[Testing](docs/development/TESTING.md) for the complete operational contract.

## CM1 and runtime assets

CM1 is external to this repository. Real execution requires a compatible local
CM1 installation, a configured `cm1.exe`, and the required runtime files.
Automated tests use tiny fixtures and fake processes; CI does not run CM1.

Cloud Chamber stores local runtime state outside Git by default:

```text
~/CloudChamber/
  settings.json
  runs/
  cache/
  explore-state/
  saved-comparisons/
  logs/
```

Explore state is stored under
`<runtime-home>/explore-state/<world_id>/<simulation_id>.json`. Each file
contains one versioned, World-specific last-active state plus that Simulation's
named Saved Views; writes are atomic and failures remain local to the state
controls.

Saved Comparisons are stored at
`<runtime-home>/saved-comparisons/<world_id>.json`. Each bounded World library
contains immutable dual-Explore snapshots plus editable title, question, and
restoration metadata.

The retained NetCDF histories that back built-in Simulations are large local
assets under the runtime home. Stable World and Simulation identities resolve
to those run assets; the assets themselves are not stored in Git.

Do not commit:

- CM1 source or binaries;
- NetCDF output or generated run directories;
- `LANDUSE.TBL`;
- downloaded sounding caches;
- local settings or machine-private paths;
- logs, screenshots, videos, traces, or large processed visualization
  artifacts.

## Repository guides

- [Development](docs/development/DEVELOPMENT.md)
- [Testing](docs/development/TESTING.md)
- [CI and Branch Protection](docs/development/CI_AND_BRANCH_PROTECTION.md)
- [Ingest, Results, and Runtime Cleanup Lifecycle](docs/current/INGEST_RESULTS_STORAGE_LIFECYCLE.md)

Read [AGENTS.md](AGENTS.md) before agent-assisted work. Cloud Chamber is in a
gated product-architecture program after the completed repository-recovery and
semantic-architecture stages. Work remains bounded, pull requests require
manual review, and auto-merge remains disabled.
