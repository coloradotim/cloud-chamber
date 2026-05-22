# Codex Project Setup Notes

## Recommended New Repo

```text
cloud-chamber
```

## Local Directory

Recommended:

```text
/Users/timpeterson/Documents/Codex/cloud-chamber
```

## Initial Files To Add

Copy these startup docs into the repo root or `docs/startup/`:

```text
README.md
AGENTS.md
docs/product-vision.md
docs/cloud-chamber-product-spec.md
docs/architecture-and-data-model.md
docs/roadmap-and-issues.md
```

## Suggested Skeleton

```text
cloud-chamber/
  AGENTS.md
  README.md
  app/
    frontend/
    backend/
  docs/
    product-vision.md
    cloud-chamber-product-spec.md
    architecture-and-data-model.md
    roadmap-and-issues.md
    data-policy.md
  scenarios/
    lower-atmosphere/
      baseline-shallow-cumulus/
      dry-failed-cumulus/
      capped-suppressed/
      humid-vigorous/
      low-stratus/
  local-data/              # ignored
  scripts/
    cm1/
```

## .gitignore Must Include

```gitignore
# Local CM1 data and generated artifacts
local-data/
data/generated/
data/local/
*.nc
*.ctl
*.dat
cm1.exe
LANDUSE.TBL

# Python / node basics
.venv/
__pycache__/
node_modules/
dist/
.env
.env.local
```

## First Technical Decision

Choose app architecture:

Recommended:

```text
React/Vite frontend + Python FastAPI local backend
```

Reason:

- Python handles xarray/netCDF easily.
- React handles UI and 3-D viewer.
- Local backend can launch/manage CM1 processes.

Alternative later:

```text
Tauri/Electron wrapper
```

Do not package too early.

## CM1 Local Path

Likely current local CM1 path:

```text
/Users/timpeterson/cm1r21.1/run
```

Do not hard-code this in app logic. Store in local settings.

## First Development Principles

1. No generated output in git.
2. Every run has a manifest.
3. Every visualization field has provenance.
4. Preview and CM1 result are always distinct.
5. Start with fake fixtures before requiring real CM1 in tests.
6. Use local paths/settings, not global assumptions.
7. Prefer one end-to-end scenario before many partial features.

## Codex Workflow

- Start from current `main`.
- Work on a branch for each issue or tightly related issue set.
- Open a PR; do not push directly to `main`.
- Keep work scoped to the GitHub issue.
- Add tests and docs with implementation changes.
- Do not commit generated CM1 artifacts.
- For Codex issue work, enable auto-merge after required CI checks pass unless the user explicitly asks for manual review or the PR is high-risk/destructive.
- Treat destructive cleanup, generated-data policy changes, scientific interpretation changes, and real CM1 execution changes as high-risk unless the user says otherwise.

See also the root `AGENTS.md`.
