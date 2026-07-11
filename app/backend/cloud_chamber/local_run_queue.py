"""Serial local CM1 run queue and auto-ingest coordinator."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.local_run_manager import LocalRunManagerError, RunStatus
from cloud_chamber.pre_run_validation import report_blocks_execution
from cloud_chamber.result_ingest import ResultIngestError, ingest_completed_run
from cloud_chamber.run_manifest import (
    LifecycleState,
    ProductState,
    RunManifestError,
    load_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings


class LocalRunQueueError(RuntimeError):
    """Raised when the serial run queue cannot be updated safely."""


class LocalRunManagerLike(Protocol):
    def launch(self, manifest_path: Path) -> RunStatus: ...

    def status(self, manifest_path: Path) -> RunStatus: ...


class RunQueueEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    manifest_path: str
    state: str
    queued_at: str
    updated_at: str
    started_at: str | None = None
    finished_at: str | None = None
    result_id: str | None = None
    message: str | None = None
    error: str | None = None
    cleanup_status: str | None = None


class RunQueueState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1"
    entries: list[RunQueueEntry] = Field(default_factory=list)
    active_run_id: str | None = None
    queued_count: int = 0
    updated_at: str


class _RunQueueStore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1"
    entries: list[RunQueueEntry] = Field(default_factory=list)


OPEN_ENTRY_STATES = {"queued", "running"}
TERMINAL_ENTRY_STATES = {
    "ingested",
    "ingest_failed",
    "completed_no_output",
    "failed",
    "canceled",
    "launch_failed",
}


class LocalRunQueueManager:
    """Persist and advance one-at-a-time local CM1 package launches."""

    def __init__(
        self,
        *,
        settings: CloudChamberSettings,
        run_manager: LocalRunManagerLike,
    ) -> None:
        self._settings = settings
        self._run_manager = run_manager

    def enqueue(self, manifest_path: Path) -> RunQueueState:
        manifest_path = manifest_path.expanduser()
        try:
            manifest = load_run_manifest(manifest_path)
        except (OSError, RunManifestError) as exc:
            raise LocalRunQueueError(f"Unable to read run manifest for queueing: {exc}") from exc
        if manifest.lifecycle_state != LifecycleState.PACKAGED:
            raise LocalRunQueueError(
                "Only packaged runs can be queued for local CM1 execution; "
                f"found {manifest.lifecycle_state.value}."
            )
        if report_blocks_execution(manifest.pre_run_validation_report):
            raise LocalRunQueueError(
                "Pre-run validation blocked queueing this package for CM1 execution."
            )

        entries = self._load_entries()
        existing = _matching_open_entry(entries, manifest_path)
        if existing is None:
            now = _now()
            entries.append(
                RunQueueEntry(
                    run_id=manifest.run_id,
                    manifest_path=str(manifest_path),
                    state="queued",
                    queued_at=now,
                    updated_at=now,
                    message="Queued for serial local CM1 execution.",
                )
            )
            self._save_entries(entries)
        return self.refresh()

    def refresh(self) -> RunQueueState:
        entries = self._load_entries()
        active = _first_entry_with_state(entries, "running")
        if active is not None:
            self._refresh_active_entry(active)

        if _first_entry_with_state(entries, "running") is None:
            next_entry = _first_entry_with_state(entries, "queued")
            if next_entry is not None:
                self._launch_entry(next_entry)

        self._save_entries(entries)
        return self._state(entries)

    def _refresh_active_entry(self, entry: RunQueueEntry) -> None:
        try:
            status = self._run_manager.status(Path(entry.manifest_path))
        except LocalRunManagerError as exc:
            entry.error = str(exc)
            entry.message = "Unable to refresh the active local CM1 run."
            entry.updated_at = _now()
            return

        if status.lifecycle_state in {LifecycleState.QUEUED, LifecycleState.RUNNING}:
            entry.message = "CM1 is running; waiting for terminal status before auto-ingest."
            entry.updated_at = _now()
            return

        self._finalize_terminal_entry(entry, status)

    def _launch_entry(self, entry: RunQueueEntry) -> None:
        try:
            status = self._run_manager.launch(Path(entry.manifest_path))
        except LocalRunManagerError as exc:
            now = _now()
            entry.state = "launch_failed"
            entry.error = str(exc)
            entry.message = "Local CM1 launch failed; fix settings and queue this package again."
            entry.finished_at = now
            entry.updated_at = now
            return

        now = _now()
        entry.state = "running"
        entry.started_at = now
        entry.updated_at = now
        entry.message = f"Running local CM1 process for {status.run_id}."
        entry.error = None

    def _finalize_terminal_entry(self, entry: RunQueueEntry, status: RunStatus) -> None:
        now = _now()
        entry.finished_at = now
        entry.updated_at = now
        try:
            manifest = load_run_manifest(status.manifest_path)
        except (OSError, RunManifestError) as exc:
            entry.state = "failed"
            entry.error = f"Unable to read terminal run manifest: {exc}"
            entry.message = "Run reached terminal status, but the manifest could not be trusted."
            return

        if status.lifecycle_state == LifecycleState.COMPLETED:
            if manifest.provenance.product_state == ProductState.COMPLETED_CM1_RESULT:
                self._auto_ingest_entry(entry, status.manifest_path)
                return
            entry.state = "completed_no_output"
            entry.message = "CM1 completed without output that can be auto-ingested."
            return

        if status.lifecycle_state == LifecycleState.CANCELED:
            entry.state = "canceled"
            entry.message = "Local CM1 run was canceled; serial queue can continue."
            return

        entry.state = "failed"
        entry.message = "Local CM1 run failed; serial queue can continue after recording failure."
        entry.error = f"Run ended with lifecycle state {status.lifecycle_state.value}."

    def _auto_ingest_entry(self, entry: RunQueueEntry, manifest_path: Path) -> None:
        try:
            result = ingest_completed_run(manifest_path)
        except ResultIngestError as exc:
            entry.state = "ingest_failed"
            entry.error = str(exc)
            entry.message = (
                "CM1 output exists, but automatic ingest failed; manual retry is available."
            )
            return

        entry.state = "ingested"
        entry.result_id = result.result_id
        entry.error = None
        entry.cleanup_status = "queue_finalized_result_backing_run_retained"
        entry.message = (
            "Result auto-ingested. The queue entry is finalized; the local run directory is "
            "retained because it backs Results and Explore."
        )

    def _load_entries(self) -> list[RunQueueEntry]:
        path = self._queue_path()
        if not path.exists():
            return []
        try:
            store = _RunQueueStore.model_validate_json(path.read_text())
        except ValueError as exc:
            raise LocalRunQueueError(f"Run queue file is unreadable: {path}") from exc
        return store.entries

    def _save_entries(self, entries: list[RunQueueEntry]) -> None:
        path = self._queue_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        store = _RunQueueStore(entries=entries)
        path.write_text(store.model_dump_json(indent=2) + "\n")

    def _queue_path(self) -> Path:
        return self._settings.runtime_home.expanduser() / "run-queue.json"

    @staticmethod
    def _state(entries: list[RunQueueEntry]) -> RunQueueState:
        active = _first_entry_with_state(entries, "running")
        return RunQueueState(
            entries=entries,
            active_run_id=active.run_id if active else None,
            queued_count=len([entry for entry in entries if entry.state == "queued"]),
            updated_at=_now(),
        )


def _matching_open_entry(
    entries: list[RunQueueEntry],
    manifest_path: Path,
) -> RunQueueEntry | None:
    manifest_text = str(manifest_path)
    for entry in entries:
        if entry.manifest_path == manifest_text and entry.state in OPEN_ENTRY_STATES:
            return entry
    return None


def _first_entry_with_state(entries: list[RunQueueEntry], state: str) -> RunQueueEntry | None:
    return next((entry for entry in entries if entry.state == state), None)


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
