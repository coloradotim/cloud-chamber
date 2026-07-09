import json
from pathlib import Path

import pytest
import xarray as xr

from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.result_cards import (
    RESULT_CARD_FILENAME,
    ResultCardUpdate,
    get_result_card,
    list_result_cards,
    update_result_card,
)
from cloud_chamber.result_ingest import (
    RESULT_METADATA_FILENAME,
    ResultIngestError,
    ingest_completed_run,
)
from cloud_chamber.run_manifest import (
    ExecutionMetadata,
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    UserMetadata,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.runtime_storage import (
    DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES,
    RuntimeStorageError,
    delete_ingested_result,
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


def create_ingested_result(
    tmp_path: Path,
    *,
    run_id: str = "run-result-delete",
    saved: bool = False,
) -> tuple[CloudChamberSettings, str, Path, Path]:
    settings = fake_settings(tmp_path)
    manifest_path = create_run(tmp_path, run_id)
    run_dir = manifest_path.parent
    netcdf_path = run_dir / "cm1out_000001.nc"
    stats_path = run_dir / "cm1out_stats.nc"
    raw_path = run_dir / "cm1out_000001_s.dat"
    ctl_path = run_dir / "cm1out_s.ctl"
    log_dir = run_dir / "logs"
    log_dir.mkdir()
    (log_dir / "stdout.log").write_text("Program terminated normally\n")
    (log_dir / "stderr.log").write_text("IEEE_UNDERFLOW_FLAG\n")
    (run_dir / "worker_status.json").write_text('{"state": "worker_cleanup_complete"}\n')
    raw_path.write_text("fake raw CM1 artifact")
    ctl_path.write_text("fake CM1 descriptor")
    write_model_netcdf(netcdf_path)
    write_stats_netcdf(stats_path)
    mark_manifest(
        manifest_path,
        lifecycle_state=LifecycleState.COMPLETED,
        product_state=ProductState.COMPLETED_CM1_RESULT,
        saved=saved,
        outputs=OutputMetadata(
            raw_cm1_artifacts=[str(raw_path), str(ctl_path)],
            netcdf_paths=[str(netcdf_path), str(stats_path)],
        ),
    )
    result = ingest_completed_run(manifest_path)
    update_result_card(
        settings,
        result.result_id,
        ResultCardUpdate(
            name="Delete me",
            tags=["cleanup"],
            notes="Notebook state should be removed with the run directory.",
        ),
    )
    return settings, result.result_id, run_dir, manifest_path


def write_model_netcdf(path: Path) -> None:
    xr.Dataset(
        data_vars={
            "qc": (
                ("time", "z", "y", "x"),
                [[[[2e-6 for _x in range(2)] for _y in range(2)] for _z in range(2)]],
                {"units": "kg/kg"},
            ),
            "w": (
                ("time", "z", "y", "x"),
                [[[[1.0, 2.0], [3.0, 4.0]], [[1.5, 2.5], [3.5, 4.5]]]],
                {"units": "m/s"},
            ),
        },
        coords={"time": [1800.0], "z": [500.0, 1500.0], "y": [0.0, 200.0], "x": [0.0, 200.0]},
    ).to_netcdf(path, engine="scipy")


def write_stats_netcdf(path: Path) -> None:
    xr.Dataset(
        data_vars={"mass": (("time",), [1.0], {"units": "kg"})},
        coords={"time": [0.0]},
    ).to_netcdf(path, engine="scipy")


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
    assert inventory.warning_threshold_bytes == DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES
    assert inventory.above_warning_threshold is False
    assert inventory.warning_message is None
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


def test_inventory_reconciles_stale_running_manifest_with_completed_output(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = create_run(tmp_path, "run-stale-completed")
    run_dir = manifest_path.parent
    log_dir = run_dir / "logs"
    log_dir.mkdir()
    stdout_log = log_dir / "stdout.log"
    stderr_log = log_dir / "stderr.log"
    stdout_log.write_text("Program terminated normally\n")
    stderr_log.write_text("IEEE_UNDERFLOW_FLAG\n")
    netcdf_path = run_dir / "cm1out_000001.nc"
    netcdf_path.write_text("fake output")
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.RUNNING,
                "provenance": ProvenanceMetadata(
                    product_state=ProductState.QUEUED_RUNNING_CM1_PROCESS
                ),
                "execution": ExecutionMetadata(
                    command=["cm1.exe"],
                    stdout_log=str(stdout_log),
                    stderr_log=str(stderr_log),
                ),
            }
        ),
    )

    inventory = runtime_storage_inventory(settings)
    entry = next(item for item in inventory.runs if item.run_id == "run-stale-completed")

    assert entry.category == "completed_with_output"
    assert entry.lifecycle_state == "completed"
    assert entry.product_state == "completed_cm1_result"
    assert entry.output_artifact_count == 1
    manifest = load_run_manifest(manifest_path)
    assert manifest.outputs.netcdf_paths == [str(netcdf_path)]
    assert manifest.execution.exit_code == 0


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


def test_inventory_warns_at_runtime_storage_threshold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)
    create_run(tmp_path, "run-large")
    monkeypatch.setattr(
        "cloud_chamber.runtime_storage.DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES",
        1,
    )

    inventory = runtime_storage_inventory(settings)

    assert inventory.warning_threshold_bytes == 1
    assert inventory.above_warning_threshold is True
    assert inventory.warning_message is not None
    assert "dry-run cleanup" in inventory.warning_message


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


def test_delete_allows_legacy_saved_run_after_explicit_preview(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = create_run(tmp_path, "run-saved")
    mark_manifest(
        manifest_path,
        lifecycle_state=LifecycleState.COMPLETED,
        product_state=ProductState.COMPLETED_CM1_RESULT,
        saved=True,
    )

    preview = delete_runtime_run(
        settings,
        run_id="run-saved",
        dry_run=True,
        confirm=False,
    )
    assert preview.deleted is False
    assert manifest_path.parent.exists()

    result = delete_runtime_run(settings, run_id="run-saved", dry_run=False, confirm=True)
    assert result.deleted is True
    assert not manifest_path.parent.exists()


def test_ingested_result_delete_preview_resolves_result_run_and_categories(
    tmp_path: Path,
) -> None:
    settings, result_id, run_dir, _manifest_path = create_ingested_result(tmp_path)

    preview = delete_ingested_result(
        settings,
        result_id=result_id,
        dry_run=True,
        confirm=False,
    )

    assert preview.result_id == result_id
    assert preview.run_id == "run-result-delete"
    assert preview.run_directory == str(run_dir)
    assert preview.deleted is False
    assert preview.size_bytes > 0
    assert run_dir.exists()
    assert preview.affected_surfaces == ["Results", "Explore", "Compare", "local inventory"]
    categories = {category.label: category for category in preview.categories}
    assert categories["Result metadata and notebook edits"].present is True
    assert categories["Run manifests, package inputs, and reports"].present is True
    assert categories["CM1 output and stats"].item_count >= 3
    assert categories["Logs and runtime sidecars"].present is True
    assert categories["Derived diagnostics and Explore data"].present is True


def test_delete_ingested_result_removes_result_and_managed_local_run_data(
    tmp_path: Path,
) -> None:
    settings, result_id, run_dir, _manifest_path = create_ingested_result(tmp_path)

    result = delete_ingested_result(
        settings,
        result_id=result_id,
        dry_run=False,
        confirm=True,
    )

    assert result.deleted is True
    assert not run_dir.exists()
    assert list_result_cards(settings) == []
    with pytest.raises(ResultIngestError, match="Result card not found"):
        get_result_card(settings, result_id)
    assert not (run_dir / RESULT_METADATA_FILENAME).exists()
    assert not (run_dir / RESULT_CARD_FILENAME).exists()
    assert not (run_dir / "cm1out_000001.nc").exists()
    assert not (run_dir / "logs" / "stdout.log").exists()
    assert not (run_dir / "derived-products" / "output_product_manifest.json").exists()


def test_delete_ingested_result_blocks_running_result_run(tmp_path: Path) -> None:
    settings, result_id, run_dir, manifest_path = create_ingested_result(
        tmp_path,
        run_id="run-result-running",
    )
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.RUNNING,
                "provenance": ProvenanceMetadata(
                    product_state=ProductState.QUEUED_RUNNING_CM1_PROCESS
                ),
            }
        ),
    )

    with pytest.raises(RuntimeStorageError, match="running run"):
        delete_ingested_result(settings, result_id=result_id, dry_run=False, confirm=True)

    assert run_dir.exists()
    assert get_result_card(settings, result_id).run_id == "run-result-running"


def test_delete_ingested_result_allows_legacy_saved_metadata(tmp_path: Path) -> None:
    settings, result_id, run_dir, _manifest_path = create_ingested_result(
        tmp_path,
        run_id="run-result-saved",
        saved=True,
    )

    preview = delete_ingested_result(
        settings,
        result_id=result_id,
        dry_run=True,
        confirm=False,
    )
    deleted = delete_ingested_result(
        settings,
        result_id=result_id,
        dry_run=False,
        confirm=True,
    )

    assert preview.deleted is False
    assert deleted.deleted is True
    assert not run_dir.exists()


def test_delete_ingested_result_requires_ingested_metadata(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = create_run(tmp_path, "run-not-ingested")

    with pytest.raises(ResultIngestError, match="Result not found"):
        delete_ingested_result(
            settings,
            result_id="result-run-not-ingested",
            dry_run=True,
            confirm=False,
        )

    assert manifest_path.parent.exists()


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
