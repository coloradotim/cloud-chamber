# CI And Branch Protection

Cloud Chamber should be conservative about automated merging because it will eventually control local CM1 run setup and scientific visualization workflows.

## CI Checks

The CI workflow should pass before merge:

- frontend install, lint, test, and build
- backend install, ruff format/check, mypy, and pytest
- script syntax checks
- docs/config JSON and YAML sanity checks
- simple markdown sanity checks

Expected GitHub Actions check names from this workflow are:

- `Frontend`
- `Backend`
- `Scripts and config`

Confirm the exact displayed names from the first PR before adding required checks to branch protection.

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
- Keep feature PR review manual.

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
15. Keep feature PR review manual.
16. Allow conservative Dependabot patch/minor auto-merge only after CI is stable.

## Auto-Merge Guidance

Auto-merge is recommended only for Dependabot patch/minor updates after CI passes.

If a Dependabot auto-merge workflow is added later, it must be conservative:

- Dependabot PRs only.
- Patch/minor updates only.
- Only after CI passes.
- No major version bumps.
- No feature PR auto-merge.
- No Codex feature PR auto-merge.

Do not auto-merge:

- major version bumps
- feature PRs
- Codex feature PRs
- changes that affect generated-data policy, CM1 runtime behavior, scientific interpretation, or visualization semantics

Codex feature PRs should still be reviewed by the user.
