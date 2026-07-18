# CI And Branch Protection

**Status:** Current workflow and recovery review guide

This document describes the repository's current CI workflow and recovery-mode review posture.
It does not define final engineering process or product direction.

## Current CI Workflow

The GitHub Actions workflow at `.github/workflows/ci.yml` currently runs on:

- every pull request;
- pushes to `main`.

The displayed jobs are:

- `Frontend`
- `Backend`
- `Scripts and config`

## Frontend Job

The current frontend job:

- runs on `ubuntu-latest`;
- uses Node 22;
- installs dependencies with `npm ci` in `app/frontend`;
- runs `npm run lint`;
- runs `npm run test`;
- runs `npm run build`.

## Backend Job

The current backend job:

- runs on `ubuntu-latest`;
- uses Python 3.12;
- installs backend dependencies with `python -m pip install -e ".[dev]"` in `app/backend`;
- runs `python -m ruff format --check .`;
- runs `python -m ruff check .`;
- runs `python -m mypy .`;
- runs `python -m pytest`.

## Scripts And Config Job

The current scripts/config job:

- verifies `scripts/check.sh` is executable;
- runs Bash syntax checks over `scripts/*.sh`;
- rejects tracked generated/local artifacts such as runtime data, CM1 output, NetCDF files,
  videos, and large visualization artifacts;
- validates selected JSON, YAML, issue-template front matter, and Markdown sanity rules.

The current explicit YAML/front-matter list includes:

- `.github/workflows/ci.yml`
- `.github/dependabot.yml`
- `.github/ISSUE_TEMPLATE/feature.md`
- `.github/ISSUE_TEMPLATE/bug.md`
- `.github/ISSUE_TEMPLATE/docs.md`
- `.github/ISSUE_TEMPLATE/cm1-scenario.md`
- `.github/ISSUE_TEMPLATE/visualization.md`

The current local and CI sanity lists do not explicitly include
`.github/ISSUE_TEMPLATE/controlled-work.md`. This document records that omission; this PR does
not change scripts or workflow configuration.

## Relationship To `scripts/check.sh`

`scripts/check.sh` is the canonical local fast gate. CI has substantial but imperfect parity:

- both run frontend lint/test/build;
- both run backend ruff, mypy, and pytest;
- both run shell syntax checks;
- both reject forbidden tracked artifacts;
- both run basic docs/config sanity checks.

Differences currently include:

- CI installs dependencies from scratch with Node 22 and Python 3.12;
- local `scripts/check.sh` uses `app/backend/.venv/bin/python` when present or `BACKEND_PYTHON`
  when configured; local-file overrides need an absolute path because the script changes
  working directories;
- CI splits checks into required-status-friendly jobs rather than invoking only
  `scripts/check.sh`;
- the exact environment, cache state, and dependency install path differ.

CI success is necessary before review, but it is not sufficient during repository recovery.

## Branch Protection And Review Posture

During repository recovery:

- pull requests require manual review;
- auto-merge remains disabled;
- CI success does not authorize product, scientific, recipe, scenario, architecture, or roadmap
  decisions by itself;
- generated artifacts and machine-local state remain prohibited;
- direct pushes to `main` are not the normal working path.

GitHub settings are repository configuration rather than source files. Verify current settings
in GitHub before treating any branch-protection behavior as enforced.

Reasonable branch-protection settings for `main`, when manually configured, include:

- require pull requests before merging;
- require status checks to pass;
- require the current CI jobs when their names are confirmed in GitHub;
- block force pushes;
- restrict deletions.

Those settings are operational guardrails. They do not change product direction.
