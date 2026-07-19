# Ingest, Results, And Runtime Cleanup Lifecycle Audit

This audit records the current implementation contract for generated packages,
local CM1 runs, ingested result metadata, Result Cards, Explore data, and
runtime cleanup.

It is evidence, not a redesign. The code paths cited below are the current
source of truth.

## Evidence Map

- Package generation: `generate_dry_run_package` in
  `app/backend/cloud_chamber/dry_run_package.py`.
- Run manifest state schema: `RunManifest`, `LifecycleState`, `ProductState`,
  and `UserMetadata` in `app/backend/cloud_chamber/run_manifest.py`.
- Local launch/status/output detection: `LocalRunManager.launch`,
  `LocalRunManager._refresh_active`, `_detect_output_metadata`, and
  `_runtime_warnings_from_stderr` in
  `app/backend/cloud_chamber/local_run_manager.py`.
- Result ingest: `ingest_completed_run`, `list_result_metadata`, and
  `get_result_metadata` in `app/backend/cloud_chamber/result_ingest.py`.
- Result Card / notebook state: `list_result_cards`, `update_result_card`,
  `save_result_card`, and `_card_from_metadata_path` in
  `app/backend/cloud_chamber/result_cards.py`.
- Explore data: `field_catalog`, `field_slice`, `point_cloud`, and
  `view_defaults` in `app/backend/cloud_chamber/visualization_data.py`.
- Runtime inventory and deletion: `runtime_storage_inventory`,
  `delete_runtime_run`, `_entry_from_manifest`, and `_classify_run` in
  `app/backend/cloud_chamber/runtime_storage.py`.
- API routing: `/api/dry-run-package`, `/api/runs/launch`,
  `/api/runs/status`, `/api/results/ingest`, `/api/results`,
  `/api/results/{result_id}`, `/api/results/{result_id}/delete-preview`,
  `/api/results/{result_id}/delete`,
  `/api/results/{result_id}/visualization/*`, `/api/storage/inventory`, and
  `/api/storage/delete-run` in `app/backend/cloud_chamber/app.py`.
- Frontend ownership and joins: `requestDryRunPackage`, `launchLocalRun`,
  `ingestCompletedRun`, `fetchResults`, `patchResultCard`,
  `saveResultCard`, `fetchStorageInventory`, `requestRunDeletePreview`,
  `confirmRunDelete`, `requestResultDeletePreview`, `confirmResultDelete`,
  `LocalPipelinePanel`, and `ResultNotebookCard` in `app/frontend/src/App.tsx`.

## Current Lifecycle Table

| Stage | Files/records created | UI page that owns it | Actions available | Cleanup behavior | Notes/caveats |
| --- | --- | --- | --- | --- | --- |
| Generated package | `~/CloudChamber/runs/<run-id>/run_manifest.json`, `case_manifest.json`, `namelist.input`, `input_sounding`, `dry_run_report.json`, `runtime_file_checklist.json` | Build creates it and inventories it | Launch from Build or stored-package actions; review generated paths/details; preview cleanup for non-ingested packages | Category `dry_run_only`; eligible for Build preview/delete unless a future guard blocks it | Manifest is `lifecycle_state=packaged` and `product_state=packaged_dry_run_output`; it is not a CM1 result. |
| Launched/running run | Same run directory plus `logs/stdout.log`, `logs/stderr.log`; manifest execution command/log paths/timestamps; staged runtime files such as `LANDUSE.TBL` if needed | Build launches, polls, and inventories it | Refresh status; cancel active run through backend API | Category `running`; backend refuses deletion | One local process is allowed at a time by `LocalRunManager`. |
| Completed run with output | Manifest updated to `lifecycle_state=completed`, `product_state=completed_cm1_result`, exit code, finish time, detected NetCDF/raw artifact paths, runtime warnings | Build can show completed output before ingest | Ingest completed output; preview cleanup only while non-ingested | Category `completed_with_output`; eligible for Build preview/delete unless the run is active or otherwise unsafe | Output detection looks for NetCDF patterns and raw CM1 `.dat/.ctl` patterns in the run directory. |
| Completed run without usable output | Manifest updated to `lifecycle_state=completed`, `product_state=process_completed_no_output`, `validation_status=needs_review` | Build | Inspect logs; cleanup review | Category `completed_no_output`; eligible for Build preview/delete | Cannot be ingested by current NetCDF ingest because it lacks model-field NetCDF. |
| Failed/canceled run | Manifest updated to `failed` or `canceled`, failed/canceled product state, exit code/timestamps when available | Build | Inspect logs; cleanup review | Category `failed` or `canceled`; eligible for Build preview/delete unless the run is active or otherwise unsafe | Failed launch after queued state can leave logs/manifest but no useful output. |
| Ingested result | `result_metadata.json` written inside the same run directory | Results owns review and cleanup; Explore uses it | Open in Results, open in Explore, edit notebook fields, preview/delete result and local run data | Result delete resolves `result_id` to the managed run directory, lists user-facing cleanup categories, and deletes the whole run directory after confirmation | Ingest does not move metadata to a separate database. It derives metadata from local NetCDF files and keeps source paths pointing at the run directory. |
| Editable notebook entry | Optional `result_card.json` beside `result_metadata.json` in the run directory | Results / Notebook | Rename, edit tags/notes, save changes | Explicit Results deletion removes this file when it deletes the selected result's run directory | `result_card.json` stores user-editable state: `name`, `tags`, `notes`, and compatibility fields such as `saved`, `protected`, and `updated_at` in older cards. |
| Legacy saved/protected metadata | `result_card.json` or older manifest `user.saved` may still carry `saved=true` / `protected=true` | Compatibility / historical local state | Not a current user-facing mode | No longer blocks explicit non-running run/result deletion after preview/confirmation | The current product model is: ingested results appear in Results; notebook edits save changes; deletion copy explains that run-directory deletion removes local result metadata. |
| Cleanup-eligible non-ingested run | No new file; eligibility is derived from manifest category and result join | Build | Dry-run delete preview, then confirmed delete | Deletes the entire selected `~/CloudChamber/runs/<run-id>/` directory | Applies to generated packages, failed/canceled runs, completed-no-output runs, and completed-with-output runs not yet ingested. |
| Deleted run directory | Run directory removed with `shutil.rmtree` | Build for non-ingested runs; Results for ingested results | None after deletion except refresh | Removed from inventory and Results/Explore if their metadata lived there | If metadata/card lived only in the deleted directory, Results and Explore can no longer load that result. |

## Direct Answers

### 1. After package generation, what files/directories exist and where are they stored?

`generate_dry_run_package` creates one directory under
`<runtime_home>/runs/<run-id>`, normally `~/CloudChamber/runs/<run-id>`. It
writes:

- `run_manifest.json`
- `case_manifest.json`
- `namelist.input`
- `input_sounding`
- `dry_run_report.json`
- `runtime_file_checklist.json`

The manifest records `lifecycle_state=packaged` and
`product_state=packaged_dry_run_output`.

### 2. After launch, what files/directories exist and what state is recorded?

`LocalRunManager.launch` requires a packaged manifest, stages required runtime
files from the configured local CM1 run directory, creates `logs/stdout.log` and
`logs/stderr.log`, records the CM1 command, and updates the manifest through
queued/running states. The product state is
`queued_running_cm1_process`.

### 3. After CM1 completion, what output files are expected and how are they identified?

`LocalRunManager._refresh_active` detects output after the process exits.
`_detect_output_metadata` identifies NetCDF artifacts by `*.nc`, `*.nc4`,
`*.cdf`, and `*.netcdf`, and raw CM1 artifacts by `cm1out_*.dat` and
`cm1out_*.ctl`. If exit code is 0 and output exists, the manifest becomes
`lifecycle_state=completed` and `product_state=completed_cm1_result`.

Runtime warning caveats are derived from stderr floating-point flags such as
`IEEE_INVALID_FLAG`, `IEEE_DIVIDE_BY_ZERO`, `IEEE_OVERFLOW_FLAG`, and
`IEEE_UNDERFLOW_FLAG`.

### 4. After ingest, what new files/records are created?

`ingest_completed_run` creates one `result_metadata.json` file in the completed
run directory. It does not create a database record, copy NetCDF output, or
write a `result_card.json` by itself.

### 5. Where does `result_metadata.json` live?

It lives inside the original run directory:

```text
~/CloudChamber/runs/<run-id>/result_metadata.json
```

`list_result_metadata` finds results by scanning
`<runtime_home>/runs/*/result_metadata.json`.

### 6. Where does `result_card.json` live?

It also lives inside the original run directory:

```text
~/CloudChamber/runs/<run-id>/result_card.json
```

It is optional. It is written when `update_result_card` or `save_result_card`
updates editable notebook state.

### 7. What does Results read from?

The Results API lists Result Cards by scanning run directories for
`result_metadata.json` and deriving a product-facing card from each metadata
file plus optional sibling `result_card.json`. Results does not read from a
central database today.

### 8. What does Explore read from?

Explore first uses Result Card data from `/api/results`. Its field catalog,
slice, point-cloud, defaults, and selected-region endpoints then call
`get_result_metadata`, which again scans for `result_metadata.json`. The
visualization endpoints open the NetCDF paths referenced by the result metadata
using backend xarray code.

### 9. Does Explore require the original run directory / NetCDF files to remain on disk?

Yes. Explore requires:

- `result_metadata.json` to remain discoverable under `~/CloudChamber/runs/*`;
- the NetCDF files referenced by `model_output_paths` / `netcdf_paths` to remain
  readable on disk.

If the original run directory is deleted, Explore loses both the metadata and
the source NetCDF files.

### 10. What does runtime cleanup delete?

`delete_runtime_run` deletes one directory:

```text
~/CloudChamber/runs/<run-id>/
```

using `shutil.rmtree`. The UI delete preview text correctly says this removes
generated package files, copied runtime files, CM1 output, logs, and local
metadata stored under the selected run directory. It does not target the repo,
runtime home itself, home directory, or external CM1 install.

For ingested results, `delete_ingested_result` first resolves
`result_id -> result_metadata.json -> run directory`, reuses the same path and
running-run safety checks, returns user-facing cleanup categories, and then
deletes the same managed run directory only after confirmation.

### 11. What exactly does the current `saved` field do?

There are two current saved fields:

1. `RunManifest.user.saved` in `run_manifest.json`.
   - Used by backend runtime inventory classification.
   - If true, `_classify_run` returns `saved_or_protected`.
   - It no longer blocks explicit non-running deletion after preview and
     confirmation.
2. `ResultCardState.saved` in `result_card.json`.
   - Kept for compatibility with older result-card state.
   - `save_result_card` sets `saved=true` and `protected=true`.
   - It does not update `run_manifest.json`.

So `saved` is currently split between manifest-level local-run protection and
Result Card notebook state.

### 12. What exactly does the current `protected` field do?

`protected` exists on Result Card state and Result Card responses. Saving a card
sets `protected=true`, and `_card_from_metadata` returns `protected` as
`state.protected or state.saved`.

The backend cleanup guard does not currently read `result_card.json`, and
Result Card protection is not a current user-facing deletion mode. Running runs
and unsafe paths remain blocked; old saved/protected metadata does not block an
intentional delete after preview and confirmation.

### 13. What happens if a run directory is deleted after ingest?

The run directory deletion removes:

- `run_manifest.json`
- CM1 inputs
- logs
- NetCDF/raw output
- `result_metadata.json`
- `result_card.json`

After refresh, Results no longer lists that result because it scans run
directories for `result_metadata.json`. Explore cannot load it because
`get_result_metadata` cannot find the metadata, and even a stale UI card would
point to missing NetCDF files.

### 14. What breaks if metadata lives inside the deleted run directory?

Deleting the run directory deletes the only implemented durable record for:

- result identity;
- source output paths;
- diagnostics;
- process diagnostics;
- visualization field availability;
- editable notebook state, if `result_card.json` exists.

That means Results, Explore, visualization-ready data, and
selected-region diagnostics all break for that result unless the run directory
and NetCDF files remain available.

### 15. What user-facing labels/actions currently map to these backend fields?

- `Ready-to-run package` maps to runtime category `dry_run_only`, derived from
  manifest lifecycle `packaged`.
- `Running CM1 process` maps to runtime category `running`, derived from
  manifest lifecycle `queued` or `running`.
- `Ready to ingest` maps to runtime category `completed_with_output` when no
  associated Result Card exists.
- `Saved/protected` is legacy compatibility metadata, not the current
  user-facing Results mode.
- `Open result` and `Open in Explore` require an associated Result Card.
- `Ingest output` requires category `completed_with_output`, a
  manifest path, and no associated Result Card.
- `Preview cleanup` in Build is for non-ingested package/run directories and is
  disabled while a run is running.
- `Preview delete result and local run data` in Results is for ingested results
  and resolves the selected result to its backing run directory.

## Mismatches And Caveats

### Ingested vs notebook entry

Current code already makes an ingested result appear in Results as a Result Card
because Result Cards are derived from `result_metadata.json`. However, there is
no separate durable notebook store. The card is not independent of the run
directory.

### Save changes vs cleanup retention

The desired distinction:

```text
Save changes = title/notes/tags edits.
Cleanup = explicit delete of the selected run directory and everything inside it.
```

`PATCH /api/results/{result_id}` writes name/tags/notes to `result_card.json`,
which matches "save changes." The older
`POST /api/results/{result_id}/save` endpoint remains for compatibility, but the
current UI does not expose it as a separate save/protect mode.

### Run directory as result store

The current storage architecture makes local run directories the store for both
bulky output and notebook metadata. That is simple and local-first, but it
means cleanup is not just "delete bulky output." It also deletes the Result
Card and diagnostics unless those are moved or copied elsewhere first.

## Current Storage Coupling

Current compatibility finding:

- Ingest creates metadata that appears in the current Results surface.
- Title, notes, and tags are current local Result Card sidecar state.
- Legacy saved/protected fields may exist in old local metadata, but they are no
  longer the current user-facing retention mode.
- Because `result_metadata.json` and `result_card.json` live inside the run
  directory, deleting the managed run directory also removes the current
  discoverable metadata, editable card state, diagnostics, and source output
  for that result.

This audit records the current storage coupling. It does not choose a future
notebook, database, archive, metadata-only cleanup, or storage-retention model.
