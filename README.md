# Cloud Chamber

## See clouds from the inside

Cloud Chamber exists because clouds are beautiful, dynamic, and mostly hidden from us.

> **Cloud Chamber is intended to become a place where people can create beautiful, scientifically meaningful cloud worlds, see the invisible processes inside them, change the atmosphere, and learn by watching the clouds respond.**

That is the product vision, not a description of the software as it exists today.

Today, Cloud Chamber is a working but uneven collection of CM1 experiment-building, run-management, sounding, diagnostics, and visualization capabilities shaped by several earlier product directions. Some of those capabilities are strong foundations. Others are incomplete, misframed, or may not belong in the eventual product.

The long-term vision is a scientific cloud laboratory: a collection of explorable cloud worlds where users can watch clouds form and evolve, reveal the normally invisible processes inside them, change meaningful atmospheric conditions, and understand how the clouds respond.

Read the controlling product documents:

- [North Star](NORTH_STAR.md)
- [Product Vision](docs/product/PRODUCT_VISION.md)

## Repository status

Cloud Chamber is currently in **product and repository recovery**.

The repository contains substantial working simulation, run-management, data, and visualization infrastructure. It also contains scenarios, workflows, terminology, and planning documents inherited from several earlier product directions.

The current application is therefore **evidence and capability, not the final product design**.

Do not infer the long-term product from:

- the current default scenario;
- the current Build, Results, or Explore workflow;
- existing sounding scores or recommendation language;
- a particular trigger or forcing mechanism;
- an old roadmap, product specification, or issue;
- one successful or unsuccessful CM1 experiment.

See [Current State](docs/current/CURRENT_STATE.md) for a candid description of what exists today and what remains under review.

## What works today

Cloud Chamber currently provides useful foundations for future product development:

- local CM1 package generation and execution;
- serial run queueing, progress reporting, cancellation, and automatic ingest;
- optional trusted-LAN execution support;
- persistent result records with names, tags, notes, provenance, and cleanup controls;
- backend-owned NetCDF ingest and bounded visualization-ready data products;
- saved-output playback and time-based result inspection;
- 2-D slices and 3-D inspection of CM1-derived fields;
- separate treatment of cloud water, ice and other hydrometeors, rain water aloft, surface rain, and reflectivity;
- observed-sounding ingest, caching, diagnostics, and experiment configuration;
- runtime-integrity and field-quality checks that distinguish a completed process from trustworthy scientific output.

These capabilities are not all guaranteed to appear in the eventual product in their current form. They should be preserved while their future roles are evaluated.

## What is not settled

The following remain open product and scientific questions:

- the first cloud world or cloud worlds to support;
- what constitutes a validated Cloud Chamber recipe;
- how observed atmospheres should enter regime-specific experiments;
- which controls belong to each cloud regime;
- practical and high-fidelity compute tiers;
- how beautiful cloud appearance and scientific field inspection should work together;
- the role of Build, Results, and Explore in the eventual experience;
- the experimentation path;
- the MVP.

Existing scenarios and implementation choices do not answer those questions by themselves.

## Documentation

Start here:

- [Documentation status and authority](docs/DOCUMENTATION_STATUS.md)
- [Current State](docs/current/CURRENT_STATE.md)
- [Current Architecture](docs/current/CURRENT_ARCHITECTURE.md)
- [Development](docs/development/DEVELOPMENT.md)
- [Testing](docs/development/TESTING.md)
- [CI and Branch Protection](docs/development/CI_AND_BRANCH_PROTECTION.md)

The read-only documentation disposition audit is complete and approved. The highest-risk superseded product-direction documents are preserved under `docs/archive/`, current operational docs are maintained under `docs/current/` and `docs/development/`, and the repository intentionally has no controlling roadmap during recovery. The [documentation status and authority guide](docs/DOCUMENTATION_STATUS.md) explains how to interpret remaining documents during recovery.

## Development

From the repository root, start the local frontend and backend:

```sh
scripts/dev.sh start
```

Other server controls:

```sh
scripts/dev.sh status
scripts/dev.sh restart
scripts/dev.sh stop
scripts/dev.sh logs
```

Run the canonical local validation gate before opening a pull request:

```sh
scripts/check.sh
```

For mocked browser workflow checks:

```sh
scripts/check-e2e.sh
```

The frontend normally runs at `http://localhost:5173` and the backend at `http://127.0.0.1:8000`.

Real CM1 execution requires an external local CM1 installation and local Cloud Chamber settings. See [Development](docs/development/DEVELOPMENT.md) for setup details.

## Runtime data

Runtime data belongs outside the repository by default:

```text
~/CloudChamber/
  settings.json
  runs/
  cache/
  logs/
```

`./local-data/` may be used as a gitignored development override.

Do not commit:

- CM1 source or binaries;
- NetCDF output;
- generated run directories;
- `LANDUSE.TBL`;
- downloaded sounding caches;
- local settings or machine-private paths;
- screenshots, videos, traces, logs, or large processed visualization artifacts.

## Contributing during recovery

Read [AGENTS.md](AGENTS.md) before nontrivial work.

Use the [controlled-work issue template](.github/ISSUE_TEMPLATE/controlled-work.md) to define bounded work before implementation, and the [Codex task prompt template](docs/templates/codex-task-prompt.md) to translate an approved issue into execution instructions.

During repository recovery:

- all pull requests require manual review;
- auto-merge is disabled;
- agents do not create follow-up issues autonomously;
- product, scientific, recipe, scenario, roadmap, and major UX decisions require explicit direction;
- existing issues and documents are not presumed to be current product authority.
