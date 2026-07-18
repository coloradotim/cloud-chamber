# Codex Task Prompt Template

Use this template after the controlling GitHub issue has been reviewed and approved.

Replace bracketed placeholders before sending it to Codex.

```text
Work in the GitHub repository:

[OWNER/REPOSITORY]

Controlling issue:

#[ISSUE_NUMBER] — [ISSUE_TITLE]

Read these authority documents before doing any work:

1. NORTH_STAR.md
2. docs/product/PRODUCT_VISION.md
3. AGENTS.md
4. the complete body and comments of issue #[ISSUE_NUMBER]

The issue is the controlling implementation instruction. Existing roadmaps,
scenarios, product specifications, research notes, old issues, and current UI
language may reflect superseded directions. Do not use them to broaden or
reinterpret the task.

============================================================
PRE-FLIGHT: PRESERVE EXISTING GIT WORK
============================================================

Before modifying anything, run and report:

git branch --show-current
git status --short --branch
git remote -v
git log --oneline --decorate -10
git diff --name-only main...HEAD
git worktree list

Do not reset, delete, rename, reuse, or overwrite an existing branch or worktree.

If there are uncommitted changes or unrelated commits, stop and report them.

If the working tree is clean:

git fetch origin
git switch main
git pull --ff-only origin main
git switch -c issue-[ISSUE_NUMBER]-[SHORT-DESCRIPTION]

Before editing, verify:

git log --oneline main..HEAD
git diff --name-only main...HEAD

Both should be empty.

============================================================
STABLE VISION
============================================================

[PASTE THE ISSUE'S STABLE-VISION SECTION]

============================================================
TASK
============================================================

[PASTE THE ISSUE'S OUTCOME AND DECISIONS-ALREADY-MADE SECTIONS]

============================================================
ALLOWED SCOPE
============================================================

Allowed files or systems:

[PASTE THE EXACT ALLOWED SCOPE]

Do not change any file or system outside this list.

============================================================
EXPLICITLY OUT OF SCOPE
============================================================

[PASTE THE ISSUE'S OUT-OF-SCOPE SECTION]

============================================================
NON-IMPLICATIONS
============================================================

[PASTE THE ISSUE'S NON-IMPLICATIONS SECTION]

Do not turn this work into a broader product, science, recipe, scenario,
roadmap, architecture, or UX decision.

============================================================
STOP CONDITIONS
============================================================

Stop and ask before:

[PASTE THE ISSUE'S STOP CONDITIONS]

Also stop if:

- the requested change conflicts with NORTH_STAR.md or the Product Vision;
- the required file set is larger than the approved scope;
- existing behavior or evidence is ambiguous enough to require PM judgment;
- tests can pass only by weakening or deleting coverage;
- GitHub permissions prevent the requested issue or PR action.

Do not create follow-up issues.
Do not enable auto-merge.

============================================================
IMPLEMENTATION
============================================================

Implement only the approved work from issue #[ISSUE_NUMBER].

Use exact supplied text where the issue provides exact content.
Do not paraphrase, improve, expand, or reorganize approved product language.

Preserve the distinction between:

configured experiment
running CM1 process
completed CM1 output
backend-derived diagnostic
visualization interpretation

Do not commit prohibited generated or local artifacts.

============================================================
VERIFICATION
============================================================

Run:

git diff --name-only main...HEAD
git diff --check
scripts/check.sh

Additional required checks:

[PASTE ISSUE-SPECIFIC VERIFICATION]

Confirm the changed-file list matches the approved scope exactly.

============================================================
PULL REQUEST
============================================================

Open a pull request against main.

Title:

[PR TITLE]

The PR body must use the repository pull-request template and include:

- what changed and why;
- the controlling issue;
- exact scope;
- product or science impact;
- what the PR does not establish;
- verification performed;
- risks and review focus;
- artifact confirmation;
- manual-review posture.

Do not merge the PR.
Do not enable auto-merge.

After opening the PR, stop and report:

- branch name;
- PR number and URL;
- exact changed-file list;
- verification results;
- confirmation that auto-merge is disabled;
- confirmation that no other issues, PRs, or repository areas were changed.
```

## Template purpose

The issue defines the work before implementation.

This prompt translates the approved issue into execution instructions and adds Git-state, scope, verification, and pull-request controls.

The pull-request template then records what was actually done for review. It is not the primary mechanism for preventing product drift.
