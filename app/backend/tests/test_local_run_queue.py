from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.local_run_manager import LocalRunManagerError, RunStatus
from cloud_chamber.local_run_queue import LocalRunQueueManager
from cloud_chamber.result_ingest import ResultIngestError
from cloud_chamber.run_manifest import (
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"


class FakeRunManager:
    def __init__(self) -> None:
        self.launched: list[Path] = []
        self.completed: set[Path] = set()
        self.launch_error: LocalRunManagerError | None = None

    def launch(self, manifest_path: Path) -> RunStatus:
        if self.launch_error:
            raise self.launch_error
        self.launched.append(manifest_path)
        return status_for_manifest(manifest_path, LifecycleState.RUNNING)

    def status(self, manifest_path: Path) -> RunStatus:
        if manifest_path in self.completed:
            return status_for_manifest(manifest_path, LifecycleState.COMPLETED, exit_code=0)
        return status_for_manifest(manifest_path, LifecycleState.RUNNING)


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=tmp_path / "CloudChamber",
        cm1_root=tmp_path / "cm1",
        cm1_run_dir=tmp_path / "cm1" / "run",
        cache_dir=tmp_path / "CloudChamber" / "cache",
        log_dir=tmp_path / "CloudChamber" / "logs",
    )


def create_manifest(tmp_path: Path, run_id: str) -> Path:
    result = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path / "CloudChamber",
        run_id=run_id,
    )
    return result.manifest_path


def mark_completed_with_output(manifest_path: Path) -> None:
    manifest = load_run_manifest(manifest_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    netcdf_path.write_text("fake output")
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.COMPLETED,
                "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
                "outputs": OutputMetadata(netcdf_paths=[str(netcdf_path)]),
            }
        ),
    )


def status_for_manifest(
    manifest_path: Path,
    lifecycle_state: LifecycleState,
    *,
    exit_code: int | None = None,
) -> RunStatus:
    manifest = load_run_manifest(manifest_path)
    return RunStatus(
        run_id=manifest.run_id,
        lifecycle_state=lifecycle_state,
        manifest_path=manifest_path,
        command=("cm1.exe",),
        stdout_log=Path("stdout.log"),
        stderr_log=Path("stderr.log"),
        exit_code=exit_code,
    )


def test_queue_runs_packages_serially_and_auto_ingests_completed_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = create_manifest(tmp_path, "run-queue-first")
    second = create_manifest(tmp_path, "run-queue-second")
    fake_manager = FakeRunManager()
    ingested_paths: list[Path] = []

    def fake_ingest(manifest_path: Path) -> object:
        ingested_paths.append(manifest_path)
        return SimpleNamespace(result_id=f"result-{load_run_manifest(manifest_path).run_id}")

    monkeypatch.setattr("cloud_chamber.local_run_queue.ingest_completed_run", fake_ingest)
    queue = LocalRunQueueManager(settings=fake_settings(tmp_path), run_manager=fake_manager)

    first_state = queue.enqueue(first)
    second_state = queue.enqueue(second)

    assert first_state.active_run_id == "run-queue-first"
    assert second_state.active_run_id == "run-queue-first"
    assert second_state.queued_count == 1
    assert [path.name for path in fake_manager.launched] == ["run_manifest.json"]

    mark_completed_with_output(first)
    fake_manager.completed.add(first)
    refreshed = queue.refresh()

    entries = {entry.run_id: entry for entry in refreshed.entries}
    assert entries["run-queue-first"].state == "ingested"
    assert entries["run-queue-first"].result_id == "result-run-queue-first"
    assert (
        entries["run-queue-first"].cleanup_status == "queue_finalized_result_backing_run_retained"
    )
    assert entries["run-queue-second"].state == "running"
    assert refreshed.active_run_id == "run-queue-second"
    assert ingested_paths == [first]
    assert fake_manager.launched == [first, second]


def test_queue_records_ingest_failure_and_still_starts_next_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = create_manifest(tmp_path, "run-ingest-fails")
    second = create_manifest(tmp_path, "run-after-ingest-failure")
    fake_manager = FakeRunManager()

    def fake_ingest(_manifest_path: Path) -> object:
        raise ResultIngestError("diagnostics missing")

    monkeypatch.setattr("cloud_chamber.local_run_queue.ingest_completed_run", fake_ingest)
    queue = LocalRunQueueManager(settings=fake_settings(tmp_path), run_manager=fake_manager)
    queue.enqueue(first)
    queue.enqueue(second)
    mark_completed_with_output(first)
    fake_manager.completed.add(first)

    refreshed = queue.refresh()

    entries = {entry.run_id: entry for entry in refreshed.entries}
    assert entries["run-ingest-fails"].state == "ingest_failed"
    assert entries["run-ingest-fails"].error == "diagnostics missing"
    assert entries["run-after-ingest-failure"].state == "running"
    assert refreshed.active_run_id == "run-after-ingest-failure"


def test_queue_marks_missing_active_manifest_failed_and_starts_next_package(
    tmp_path: Path,
) -> None:
    first = create_manifest(tmp_path, "run-missing-active-manifest")
    second = create_manifest(tmp_path, "run-after-missing-active-manifest")
    fake_manager = FakeRunManager()
    queue = LocalRunQueueManager(settings=fake_settings(tmp_path), run_manager=fake_manager)
    queue.enqueue(first)
    queue.enqueue(second)
    first.unlink()

    refreshed = queue.refresh()

    entries = {entry.run_id: entry for entry in refreshed.entries}
    assert entries["run-missing-active-manifest"].state == "failed"
    assert entries["run-missing-active-manifest"].message == (
        "Active local CM1 queue entry is missing its run manifest; marking failed "
        "so the serial queue can continue."
    )
    assert "missing its run manifest" in (entries["run-missing-active-manifest"].error or "")
    assert entries["run-after-missing-active-manifest"].state == "running"
    assert refreshed.active_run_id == "run-after-missing-active-manifest"


def test_queue_records_launch_failures_when_local_launch_remains_blocked(tmp_path: Path) -> None:
    first = create_manifest(tmp_path, "run-launch-fails")
    second = create_manifest(tmp_path, "run-waits")
    fake_manager = FakeRunManager()
    fake_manager.launch_error = LocalRunManagerError("CM1 is not ready")
    queue = LocalRunQueueManager(settings=fake_settings(tmp_path), run_manager=fake_manager)

    failed_state = queue.enqueue(first)
    queued_state = queue.enqueue(second)

    entries = {entry.run_id: entry for entry in queued_state.entries}
    assert failed_state.entries[0].state == "launch_failed"
    assert failed_state.entries[0].message == (
        "Local CM1 launch failed; fix settings and queue this package again."
    )
    assert entries["run-launch-fails"].state == "launch_failed"
    assert entries["run-waits"].state == "launch_failed"
    assert queued_state.active_run_id is None


def test_queue_recovers_running_entry_from_manifest_after_stale_launch_failure(
    tmp_path: Path,
) -> None:
    manifest_path = create_manifest(tmp_path, "run-recovered-from-stale-queue")
    fake_manager = FakeRunManager()
    settings = fake_settings(tmp_path)
    queue = LocalRunQueueManager(settings=settings, run_manager=fake_manager)
    queue.enqueue(manifest_path)

    manifest = load_run_manifest(manifest_path)
    started_at = datetime.now(UTC)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.RUNNING,
                "provenance": ProvenanceMetadata(
                    product_state=ProductState.QUEUED_RUNNING_CM1_PROCESS
                ),
                "execution": manifest.execution.model_copy(update={"started_at": started_at}),
            }
        ),
    )
    queue_path = settings.runtime_home / "run-queue.json"
    queue_store = json.loads(queue_path.read_text())
    queue_store["entries"][0]["state"] = "launch_failed"
    queue_store["entries"][0]["error"] = "Another local CM1 run is already active"
    queue_store["entries"][0]["finished_at"] = datetime.now(UTC).isoformat()
    queue_path.write_text(json.dumps(queue_store) + "\n")

    refreshed = queue.refresh()

    entry = refreshed.entries[0]
    assert refreshed.active_run_id == "run-recovered-from-stale-queue"
    assert entry.state == "running"
    assert entry.error is None
    assert entry.finished_at is None
    assert entry.started_at == started_at.isoformat().replace("+00:00", "Z")
    assert entry.message == ("CM1 is running; waiting for terminal status before auto-ingest.")
