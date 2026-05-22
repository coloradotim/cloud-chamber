"""Runtime storage inventory and safe cleanup helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.run_manifest import (
    LifecycleState,
    ProductState,
    RunManifest,
    RunManifestError,
    load_run_manifest,
)
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
    if entry.protected and not force_saved:
        raise RuntimeStorageError(
            f"Refusing to delete saved/protected run without force_saved: {run_id}"
        )
    if not dry_run and not confirm:
        raise RuntimeStorageError("Real delete requires confirm=true.")

    if dry_run:
        return DeleteRunResult(
            run_id=run_id,
            run_directory=str(run_dir),
            dry_run=True,
            deleted=False,
            size_bytes=entry.size_bytes,
            message="Dry run only; no files were deleted.",
        )

    shutil.rmtree(run_dir)
    return DeleteRunResult(
        run_id=run_id,
        run_directory=str(run_dir),
        dry_run=False,
        deleted=True,
        size_bytes=entry.size_bytes,
        message="Run directory deleted.",
    )


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
        manifest = load_run_manifest(manifest_path)
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
        category=_classify_run(manifest),
        manifest_path=str(manifest_path),
    )


def _classify_run(manifest: RunManifest) -> str:
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
