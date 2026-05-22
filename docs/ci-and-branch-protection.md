# CI And Branch Protection

Cloud Chamber should be conservative about automated merging because it will eventually control local CM1 run setup and scientific visualization workflows.

## CI Checks

The CI workflow should pass before merge:

- frontend install, lint, test, and build
- backend install, ruff format/check, mypy, and pytest
- script syntax checks
- `scripts/check.sh` executable-bit assertion
- forbidden tracked artifact checks
- docs/config JSON and YAML sanity checks
- simple markdown sanity checks

Expected GitHub Actions check names from this workflow are:

- `Frontend`
- `Backend`
- `Scripts and config`

Confirm the exact displayed names from the first PR before adding required checks to branch protection.

`scripts/check.sh` is the canonical local validation gate. CI uses split equivalent jobs instead of calling only that script so required checks stay granular and readable in branch protection. When future fast checks are added locally, mirror them in CI or explicitly document why they only run in one place.

## Recommended GitHub Settings

Configure these manually in GitHub for `main`:

- Protect `main`.
- Require pull request before merging.
- Require status checks to pass.
- Require branches to be up to date before merging if practical.
- Require the CI workflow checks.
- Disallow force pushes to `main`.
- Disallow direct pushes to `main` if practical.
- Enable auto-merge only after required checks pass.
- Allow Codex issue PRs to auto-merge after required checks pass unless the user marks a PR for manual review or the change is high-risk/destructive.

## Manual GitHub Settings After First CI Run

After the first PR exists and GitHub Actions has reported checks:

1. Open the first PR and note the exact GitHub Actions check names.
2. Go to Settings -> General -> Pull Requests.
3. Enable "Allow auto-merge."
4. Enable "Automatically delete head branches."
5. Prefer squash merge only.
6. Go to Settings -> Rules -> Rulesets.
7. Create a branch ruleset named "Protect main."
8. Target the default branch / main.
9. Require pull request before merging.
10. Require status checks to pass.
11. Require branches to be up to date before merging if practical.
12. Add the exact CI check names from the first PR.
13. Block force pushes.
14. Restrict deletions.
15. Allow Codex issue PRs to auto-merge after required checks pass unless the user marks a PR for manual review or the change is high-risk/destructive.
16. Allow conservative Dependabot patch/minor auto-merge only after CI is stable.

## Auto-Merge Guidance

Auto-merge is recommended for routine Codex issue PRs after required CI passes. This is the default workflow for this repo so issue work closes cleanly without a second manual merge step.

Do not enable auto-merge when the user explicitly asks for manual review, or when the PR is high-risk/destructive. High-risk examples include:

- destructive cleanup behavior
- generated-data policy changes
- CM1 runtime execution semantics
- scientific interpretation or diagnostic definitions
- visualization semantics that could misrepresent CM1 output
- major dependency version bumps

Dependabot auto-merge, if added later, must remain conservative:

- Dependabot PRs only.
- Patch/minor updates only.
- Only after CI passes.
- No major version bumps.

Do not auto-merge:

- major version bumps
- PRs the user marked for manual review
- high-risk/destructive changes unless the user says to proceed
