import json
from pathlib import Path

import pytest

from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.run_manifest import (
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    UserMetadata,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.runtime_storage import (
    RuntimeStorageError,
    delete_runtime_run,
    runtime_storage_inventory,
)
from cloud_chamber.settings import CloudChamberSettings

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    cm1_root = tmp_path / "cm1r21.1"
    cm1_run_dir = cm1_root / "run"
    cm1_run_dir.mkdir(parents=True)
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=cm1_root,
        cm1_run_dir=cm1_run_dir,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def create_run(tmp_path: Path, run_id: str) -> Path:
    result = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path / "CloudChamber",
        run_id=run_id,
    )
    return result.manifest_path


def mark_manifest(
    manifest_path: Path,
    *,
    lifecycle_state: LifecycleState,
    product_state: ProductState,
    saved: bool = False,
    outputs: OutputMetadata | None = None,
) -> None:
    manifest = load_run_manifest(manifest_path)
    updated = manifest.model_copy(
        update={
            "lifecycle_state": lifecycle_state,
            "provenance": ProvenanceMetadata(product_state=product_state),
            "outputs": outputs or manifest.outputs,
            "user": UserMetadata(
                name=manifest.user.name,
                tags=manifest.user.tags,
                notes=manifest.user.notes,
                saved=saved,
            ),
        }
    )
    write_run_manifest(manifest_path, updated)


def test_inventory_reports_total_size_per_run_size_and_largest_runs(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    first_manifest = create_run(tmp_path, "run-small")
    second_manifest = create_run(tmp_path, "run-large")
    first_dir = first_manifest.parent
    second_dir = second_manifest.parent
    (first_dir / "small.bin").write_bytes(b"a" * 10)
    (second_dir / "large.bin").write_bytes(b"b" * 100)

    inventory = runtime_storage_inventory(settings)

    by_id = {entry.run_id: entry for entry in inventory.runs}
    assert inventory.total_size_bytes >= 110
    assert by_id["run-small"].size_bytes >= 10
    assert by_id["run-large"].size_bytes >= 100
    assert inventory.largest_runs[0].size_bytes >= inventory.largest_runs[-1].size_bytes


def test_inventory_classifies_valid_manifest_with_output_artifacts(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = create_run(tmp_path, "run-output")
    run_dir = manifest_path.parent
    raw_path = run_dir / "cm1out_000001_s.dat"
    ctl_path = run_dir / "cm1out_s.ctl"
    raw_path.write_text("fake raw output")
    ctl_path.write_text("fake descriptor")
    mark_manifest(
        manifest_path,
        lifecycle_state=LifecycleState.COMPLETED,
        product_state=ProductState.COMPLETED_CM1_RESULT,
        outputs=OutputMetadata(raw_cm1_artifacts=[str(raw_path), str(ctl_path)]),
    )

    inventory = runtime_storage_inventory(settings)
    entry = next(item for item in inventory.runs if item.run_id == "run-output")

    assert entry.category == "completed_with_output"
    assert entry.scenario_id == "baseline-shallow-cumulus"
    assert entry.lifecycle_state == "completed"
    assert entry.validation_status == "valid"
    assert entry.product_state == "completed_cm1_result"
    assert entry.run_size_preset == "quick_look"
    assert entry.output_artifact_count == 2
    assert entry.output_summary["raw_cm1_artifacts"] == 2


def test_inventory_classifies_missing_and_malformed_manifests(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    runs_dir = settings.runtime_home / "runs"
    missing_dir = runs_dir / "missing-manifest"
    malformed_dir = runs_dir / "malformed-manifest"
    missing_dir.mkdir(parents=True)
    malformed_dir.mkdir(parents=True)
    (malformed_dir / "run_manifest.json").write_text("{")

    inventory = runtime_storage_inventory(settings)
    by_id = {entry.run_id: entry for entry in inventory.runs}

    assert by_id["missing-manifest"].category == "missing_manifest"
    assert by_id["malformed-manifest"].category == "malformed_manifest"
    assert by_id["malformed-manifest"].manifest_error


def test_delete_dry_run_returns_plan_without_deleting(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = create_run(tmp_path, "run-delete")
    run_dir = manifest_path.parent

    result = delete_runtime_run(
        settings,
        run_id="run-delete",
        dry_run=True,
        confirm=False,
    )

    assert result.deleted is False
    assert result.size_bytes > 0
    assert run_dir.exists()


def test_delete_real_run_removes_only_selected_run_directory(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    selected_manifest = create_run(tmp_path, "run-delete")
    other_manifest = create_run(tmp_path, "run-keep")

    result = delete_runtime_run(
        settings,
        run_id="run-delete",
        dry_run=False,
        confirm=True,
    )

    assert result.deleted is True
    assert not selected_manifest.parent.exists()
    assert other_manifest.parent.exists()


def test_delete_refuses_running_run(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = create_run(tmp_path, "run-running")
    mark_manifest(
        manifest_path,
        lifecycle_state=LifecycleState.RUNNING,
        product_state=ProductState.QUEUED_RUNNING_CM1_PROCESS,
    )

    with pytest.raises(RuntimeStorageError, match="running run"):
        delete_runtime_run(settings, run_id="run-running", dry_run=False, confirm=True)


def test_delete_refuses_saved_run_without_force(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = create_run(tmp_path, "run-saved")
    mark_manifest(
        manifest_path,
        lifecycle_state=LifecycleState.COMPLETED,
        product_state=ProductState.COMPLETED_CM1_RESULT,
        saved=True,
    )

    with pytest.raises(RuntimeStorageError, match="saved/protected"):
        delete_runtime_run(settings, run_id="run-saved", dry_run=False, confirm=True)

    result = delete_runtime_run(
        settings,
        run_id="run-saved",
        dry_run=True,
        confirm=False,
        force_saved=True,
    )
    assert result.deleted is False


def test_delete_refuses_path_traversal_and_runtime_home_itself(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)

    with pytest.raises(RuntimeStorageError, match="Invalid run ID"):
        delete_runtime_run(settings, run_id="../outside", dry_run=True, confirm=False)

    with pytest.raises(RuntimeStorageError, match="Run ID"):
        delete_runtime_run(settings, run_id=".", dry_run=True, confirm=False)


def test_delete_refuses_symlink_escape(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    runs_dir = settings.runtime_home / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeStorageError, match="outside runtime home"):
        delete_runtime_run(settings, run_id="escape", dry_run=True, confirm=False)
