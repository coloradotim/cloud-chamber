"""Runtime storage inventory and safe cleanup helpers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.local_run_manager import reconcile_completed_run_manifest
from cloud_chamber.result_ingest import (
    RESULT_METADATA_FILENAME,
    ResultIngestError,
    result_metadata_from_json,
)
from cloud_chamber.run_manifest import (
    LifecycleState,
    ProductState,
    RunManifest,
    RunManifestError,
)
from cloud_chamber.run_progress import run_progress_from_manifest
from cloud_chamber.settings import CloudChamberSettings

DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES = 50 * 1024**3


class RuntimeStorageError(RuntimeError):
    """Raised when runtime storage inventory or cleanup cannot proceed."""


class RunStorageEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    scenario_id: str | None = None
    scenario_name: str | None = None
    lifecycle_state: str | None = None
    validation_status: str | None = None
    product_state: str | None = None
    run_size_preset: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    saved: bool = False
    protected: bool = False
    output_artifact_count: int = 0
    output_summary: dict[str, int] = Field(default_factory=dict)
    size_bytes: int
    path: str
    category: str
    manifest_path: str | None = None
    manifest_error: str | None = None
    progress: dict[str, object] | None = None
    worker_state: str | None = None
    worker_message: str | None = None
    worker_started_at: str | None = None
    worker_finished_at: str | None = None
    worker_status_updated_at: str | None = None
    worker_remote_dir: str | None = None
    worker_netcdf_count: int | None = None
    worker_raw_artifact_count: int | None = None
    worker_progress: dict[str, object] | None = None


class RuntimeStorageInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime_home: str
    runs_directory: str
    total_size_bytes: int
    warning_threshold_bytes: int
    above_warning_threshold: bool
    warning_message: str | None = None
    runs: list[RunStorageEntry]
    largest_runs: list[RunStorageEntry]


class DeleteRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    run_directory: str
    dry_run: bool
    deleted: bool
    size_bytes: int
    message: str


class ResultCleanupCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    description: str
    present: bool
    item_count: int


class DeleteResultResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    run_directory: str
    dry_run: bool
    deleted: bool
    size_bytes: int
    message: str
    affected_surfaces: list[str]
    categories: list[ResultCleanupCategory]


def runtime_storage_inventory(settings: CloudChamberSettings) -> RuntimeStorageInventory:
    """Return a conservative inventory of the configured runtime home."""
    runtime_home = settings.runtime_home.expanduser()
    runs_dir = runtime_home / "runs"
    run_entries = [_run_storage_entry(path) for path in _run_directories(runs_dir)]
    largest = sorted(run_entries, key=lambda entry: entry.size_bytes, reverse=True)
    total_size_bytes = _directory_size(runtime_home)
    above_warning_threshold = total_size_bytes >= DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES
    return RuntimeStorageInventory(
        runtime_home=str(runtime_home),
        runs_directory=str(runs_dir),
        total_size_bytes=total_size_bytes,
        warning_threshold_bytes=DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES,
        above_warning_threshold=above_warning_threshold,
        warning_message=(
            "Runtime storage is at or above the 50 GB warning threshold. "
            "Review largest_runs and use dry-run cleanup before deleting selected runs."
            if above_warning_threshold
            else None
        ),
        runs=run_entries,
        largest_runs=largest,
    )


def delete_runtime_run(
    settings: CloudChamberSettings,
    *,
    run_id: str,
    dry_run: bool,
    confirm: bool,
    force_saved: bool = False,
) -> DeleteRunResult:
    """Delete one generated run directory after safety checks."""
    # Backward-compatible request shape: saved/protected is no longer a normal
    # product mode or deletion blocker, but older callers may still send this.
    _ = force_saved
    plan = _runtime_delete_plan(settings, run_id)
    if not dry_run and not confirm:
        raise RuntimeStorageError("Real delete requires confirm=true.")

    if dry_run:
        return DeleteRunResult(
            run_id=run_id,
            run_directory=str(plan.run_dir),
            dry_run=True,
            deleted=False,
            size_bytes=plan.entry.size_bytes,
            message="Dry run only; no files were deleted.",
        )

    shutil.rmtree(plan.run_dir)
    return DeleteRunResult(
        run_id=run_id,
        run_directory=str(plan.run_dir),
        dry_run=False,
        deleted=True,
        size_bytes=plan.entry.size_bytes,
        message="Run directory deleted.",
    )


def delete_ingested_result(
    settings: CloudChamberSettings,
    *,
    result_id: str,
    dry_run: bool,
    confirm: bool,
) -> DeleteResultResult:
    """Delete an ingested result and its managed local run directory."""
    metadata_path = _metadata_path_for_result(settings, result_id)
    try:
        metadata = result_metadata_from_json(metadata_path.read_text())
    except (OSError, ValueError) as exc:
        raise ResultIngestError(f"Result metadata is unreadable: {result_id}") from exc

    run_dir = metadata_path.parent
    if metadata.run_id != run_dir.name:
        raise RuntimeStorageError(
            "Result metadata run_id does not match its local run directory: "
            f"{metadata.run_id} != {run_dir.name}"
        )

    plan = _runtime_delete_plan(settings, metadata.run_id)
    categories = _result_cleanup_categories(run_dir)
    if not dry_run and not confirm:
        raise RuntimeStorageError("Real delete requires confirm=true.")

    deleted = False
    message = "Dry run only; no files were deleted."
    if not dry_run:
        shutil.rmtree(plan.run_dir)
        deleted = True
        message = "Result and local run data deleted."

    return DeleteResultResult(
        result_id=result_id,
        run_id=metadata.run_id,
        run_directory=str(plan.run_dir),
        dry_run=dry_run,
        deleted=deleted,
        size_bytes=plan.entry.size_bytes,
        message=message,
        affected_surfaces=[
            "Results",
            "Explore",
            "local inventory",
        ],
        categories=categories,
    )


class _RuntimeDeletePlan(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_dir: Path
    entry: RunStorageEntry


def _runtime_delete_plan(
    settings: CloudChamberSettings,
    run_id: str,
) -> _RuntimeDeletePlan:
    runtime_home = settings.runtime_home.expanduser()
    runs_dir = runtime_home / "runs"
    run_dir = _safe_run_directory(runtime_home, run_id)

    _refuse_forbidden_target(run_dir, runtime_home, settings)
    if not run_dir.exists():
        raise RuntimeStorageError(f"Run directory does not exist: {run_dir}")
    if not run_dir.is_dir():
        raise RuntimeStorageError(f"Run target is not a directory: {run_dir}")
    if run_dir.is_symlink():
        raise RuntimeStorageError(f"Refusing to delete symlinked run directory: {run_dir}")
    if run_dir.parent.resolve() != runs_dir.resolve():
        raise RuntimeStorageError(f"Run directory is not directly under {runs_dir}: {run_dir}")

    entry = _run_storage_entry(run_dir)
    if entry.category == "running":
        raise RuntimeStorageError(f"Refusing to delete running run: {run_id}")
    return _RuntimeDeletePlan(run_dir=run_dir, entry=entry)


def _run_directories(runs_dir: Path) -> list[Path]:
    if not runs_dir.exists():
        return []
    return sorted(path for path in runs_dir.iterdir() if path.is_dir() or path.is_symlink())


def _run_storage_entry(run_dir: Path) -> RunStorageEntry:
    manifest_path = run_dir / "run_manifest.json"
    size_bytes = _directory_size(run_dir)
    if not manifest_path.exists():
        return RunStorageEntry(
            run_id=run_dir.name,
            size_bytes=size_bytes,
            path=str(run_dir),
            category="missing_manifest",
        )

    try:
        manifest = reconcile_completed_run_manifest(manifest_path)
    except (RunManifestError, OSError, ValueError) as exc:
        return RunStorageEntry(
            run_id=run_dir.name,
            size_bytes=size_bytes,
            path=str(run_dir),
            category="malformed_manifest",
            manifest_path=str(manifest_path),
            manifest_error=str(exc),
        )

    return _entry_from_manifest(run_dir, manifest_path, manifest, size_bytes)


def _entry_from_manifest(
    run_dir: Path,
    manifest_path: Path,
    manifest: RunManifest,
    size_bytes: int,
) -> RunStorageEntry:
    output_summary = {
        "raw_cm1_artifacts": len(manifest.outputs.raw_cm1_artifacts),
        "netcdf_paths": len(manifest.outputs.netcdf_paths),
        "processed_artifacts": len(manifest.outputs.processed_artifacts),
    }
    worker_status = _read_worker_status(run_dir / "worker_status.json")
    return RunStorageEntry(
        run_id=manifest.run_id,
        scenario_id=manifest.scenario.id,
        lifecycle_state=manifest.lifecycle_state.value,
        validation_status=manifest.validation_status.value,
        product_state=manifest.provenance.product_state.value,
        run_size_preset=manifest.run_size_preset,
        created_at=manifest.created_at.isoformat(),
        updated_at=manifest.updated_at.isoformat(),
        saved=manifest.user.saved,
        protected=manifest.user.saved,
        output_artifact_count=sum(output_summary.values()),
        output_summary=output_summary,
        size_bytes=size_bytes,
        path=str(run_dir),
        category=_classify_run(manifest, worker_status),
        manifest_path=str(manifest_path),
        progress=run_progress_from_manifest(manifest),
        worker_state=_string_or_none(worker_status.get("state")),
        worker_message=_string_or_none(worker_status.get("message")),
        worker_started_at=_string_or_none(worker_status.get("started_at")),
        worker_finished_at=_string_or_none(worker_status.get("finished_at")),
        worker_status_updated_at=_string_or_none(worker_status.get("local_status_updated_at")),
        worker_remote_dir=_string_or_none(worker_status.get("remote_dir")),
        worker_netcdf_count=_int_or_none(worker_status.get("netcdf_count")),
        worker_raw_artifact_count=_int_or_none(worker_status.get("raw_artifact_count")),
        worker_progress=_dict_or_none(worker_status.get("progress")),
    )


def _classify_run(manifest: RunManifest, worker_status: dict[str, object] | None = None) -> str:
    if worker_status and worker_status.get("state") == "running":
        return "running"
    if manifest.user.saved:
        return "saved_or_protected"
    if manifest.lifecycle_state in {LifecycleState.QUEUED, LifecycleState.RUNNING}:
        return "running"
    if manifest.lifecycle_state == LifecycleState.PACKAGED:
        return "dry_run_only"
    if manifest.lifecycle_state == LifecycleState.COMPLETED:
        has_output = bool(
            manifest.outputs.raw_cm1_artifacts
            or manifest.outputs.netcdf_paths
            or manifest.outputs.processed_artifacts
        )
        if manifest.provenance.product_state == ProductState.PROCESS_COMPLETED_NO_OUTPUT:
            return "completed_no_output"
        return "completed_with_output" if has_output else "completed_no_output"
    if manifest.lifecycle_state == LifecycleState.FAILED:
        return "failed"
    if manifest.lifecycle_state == LifecycleState.CANCELED:
        return "canceled"
    return "unknown"


def _read_worker_status(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _dict_or_none(value: object) -> dict[str, object] | None:
    return value if isinstance(value, dict) else None


def _metadata_path_for_result(settings: CloudChamberSettings, result_id: str) -> Path:
    runs_dir = settings.runtime_home.expanduser() / "runs"
    if not runs_dir.exists():
        raise ResultIngestError(f"Result not found: {result_id}")

    for metadata_path in sorted(runs_dir.glob(f"*/{RESULT_METADATA_FILENAME}")):
        try:
            metadata = result_metadata_from_json(metadata_path.read_text())
        except (OSError, ValueError):
            continue
        if metadata.result_id == result_id:
            return metadata_path
    raise ResultIngestError(f"Result not found: {result_id}")


def _result_cleanup_categories(run_dir: Path) -> list[ResultCleanupCategory]:
    specs = [
        (
            "Result metadata and notebook edits",
            "Ingested result metadata plus editable notebook sidecar state.",
            ["result_metadata.json", "result_card.json"],
        ),
        (
            "Run manifests, package inputs, and reports",
            "Run manifests, case setup, generated CM1 inputs, dry-run reports, "
            "and file checklists.",
            [
                "run_manifest.json",
                "case_manifest.json",
                "namelist.input",
                "input_sounding",
                "dry_run_report.json",
                "runtime_file_checklist.json",
            ],
        ),
        (
            "CM1 output and stats",
            "Model-output NetCDF, stats files, and raw CM1 artifacts copied into this run.",
            ["cm1out*.nc", "cm1out*.nc4", "cm1out*.dat", "cm1out*.ctl", "*.ctl"],
        ),
        (
            "Logs and runtime sidecars",
            "Local stdout/stderr logs, backend logs, and LAN-worker status sidecars.",
            ["logs/**", "*.log", "stdout.log", "stderr.log", "worker_status.json"],
        ),
        (
            "Derived diagnostics and Explore data",
            "Derived product manifests, cached diagnostics, and visualization backing data.",
            ["derived-products/**", "processed/**", "visualization/**"],
        ),
    ]
    categories: list[ResultCleanupCategory] = []
    for label, description, patterns in specs:
        count = _matching_item_count(run_dir, patterns)
        categories.append(
            ResultCleanupCategory(
                label=label,
                description=description,
                present=count > 0,
                item_count=count,
            )
        )
    return categories


def _matching_item_count(run_dir: Path, patterns: list[str]) -> int:
    matched: set[Path] = set()
    for pattern in patterns:
        for path in run_dir.glob(pattern):
            if path == run_dir:
                continue
            matched.add(path)
    return len(matched)


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _safe_run_directory(runtime_home: Path, run_id: str) -> Path:
    requested = Path(run_id)
    if requested.is_absolute() or any(part in {"", ".", ".."} for part in requested.parts):
        raise RuntimeStorageError(f"Invalid run ID: {run_id}")
    if len(requested.parts) != 1:
        raise RuntimeStorageError(f"Run ID must name one directory under runtime runs: {run_id}")
    return runtime_home / "runs" / run_id


def _refuse_forbidden_target(
    run_dir: Path,
    runtime_home: Path,
    settings: CloudChamberSettings,
) -> None:
    resolved = run_dir.resolve()
    runtime_resolved = runtime_home.resolve()
    forbidden = {
        runtime_resolved,
        Path.home().resolve(),
    }
    if settings.cm1_root is not None:
        forbidden.add(settings.cm1_root.expanduser().resolve())
    if settings.cm1_run_dir is not None:
        forbidden.add(settings.cm1_run_dir.expanduser().resolve())
    if resolved in forbidden:
        raise RuntimeStorageError(f"Refusing to delete protected path: {resolved}")
    try:
        resolved.relative_to(runtime_resolved)
    except ValueError as exc:
        raise RuntimeStorageError(f"Refusing to delete outside runtime home: {resolved}") from exc


def _directory_size(path: Path) -> int:
    if not path.exists() and not path.is_symlink():
        return 0
    if path.is_file() or path.is_symlink():
        return path.lstat().st_size
    total = 0
    for child in path.rglob("*"):
        try:
            total += child.lstat().st_size
        except OSError:
            continue
    return total
