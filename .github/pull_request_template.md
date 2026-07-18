## Summary

What changed and why?

## Scope

Related issue:

Files or systems changed:

Explicitly out of scope:

## Product and science impact

Does this change any of the following?

- product direction;
- scientific interpretation;
- recipe or scenario status;
- user-facing scientific language;
- destructive cleanup behavior;
- real CM1 execution behavior;
- a backwards-incompatible manifest, result, or scenario schema.

If yes, identify where the decision was explicitly approved.

What does this PR **not** establish?

Write `None` where applicable.

## Verification

Commands and manual checks performed:

```text
scripts/check.sh
```

For UI workflow changes, include:

```text
scripts/check-e2e.sh
```

## Risks and review focus

What should the reviewer inspect closely?

## Artifact check

- [ ] No CM1 source or binaries were committed.
- [ ] No NetCDF output, generated run directories, runtime data, or sounding caches were committed.
- [ ] No machine-private paths, settings, logs, screenshots, videos, traces, or large generated artifacts were committed unless explicitly approved.

## Merge posture

- [ ] Manual review required.
- [ ] Auto-merge is not enabled.
