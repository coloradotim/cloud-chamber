# Cloud Chamber Playwright E2E

These browser checks are intentionally split into three categories.

## Categories

- `mocked-smoke/`: deterministic browser smoke tests with mocked API routes. These are safe to run repeatedly and should pass without local CM1, local NetCDF, or `~/CloudChamber` runtime data.
- `local-data/`: read-only checks against the local backend/runtime home. These may skip when local run/result data is absent or the backend is unavailable.
- `visual-manual/`: partial browser checks for layout-heavy visualization behavior. They catch obvious DOM/layout regressions, but still leave some scientific/visual judgment to human inspection.

## Commands

From `app/frontend`:

```sh
npm run test:e2e
npm run test:e2e:headed
npm run test:e2e:report
```

From the repo root:

```sh
scripts/check-e2e.sh
```

`scripts/check-e2e.sh` runs only the mocked smoke tests by default. Use the npm
scripts when you want the full local-data and visual/manual suite.

## Safety Rules

- Do not run real CM1 from Playwright.
- Do not mutate real notebook data from unmocked tests.
- Do not delete real run directories from unmocked tests.
- Destructive/editing tests must use mocked API routes.
- Do not commit Playwright reports, screenshots, videos, traces, NetCDF files,
  logs, generated CM1 output, or local run folders.

Known product follow-ups linked by this suite include #133, #134, #135, #136,
and #139.
