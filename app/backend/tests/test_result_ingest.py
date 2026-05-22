import json
from pathlib import Path

import pytest
import xarray as xr

from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.result_ingest import (
    RESULT_METADATA_FILENAME,
    ResultIngestError,
    get_result_metadata,
    ingest_completed_run,
    list_result_metadata,
    result_metadata_from_json,
)
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


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=tmp_path / "cm1r21.1",
        cm1_run_dir=tmp_path / "cm1r21.1" / "run",
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def create_manifest(tmp_path: Path, run_id: str = "run-ingest") -> Path:
    result = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path / "CloudChamber",
        run_id=run_id,
    )
    return result.manifest_path


def complete_manifest(
    manifest_path: Path,
    outputs: OutputMetadata,
) -> None:
    manifest = load_run_manifest(manifest_path)
    updated = manifest.model_copy(
        update={
            "lifecycle_state": LifecycleState.COMPLETED,
            "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
            "outputs": outputs,
        }
    )
    write_run_manifest(manifest_path, updated)


def write_tiny_netcdf(
    path: Path,
    *,
    include_qc: bool = True,
    include_w: bool = True,
) -> None:
    data_vars = {}
    if include_qc:
        data_vars["qc"] = (
            ("time", "z", "y", "x"),
            [[[[0.0, 0.1], [0.2, 0.3]], [[0.4, 0.5], [0.6, 0.7]]]],
            {"units": "kg/kg"},
        )
    if include_w:
        data_vars["w"] = (
            ("time", "z", "y", "x"),
            [[[[0.0, 1.0], [2.0, 3.0]], [[4.0, 5.0], [6.0, 7.0]]]],
            {"units": "m/s"},
        )
    dataset = xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": [0.0],
            "z": [125.0, 250.0],
            "y": [0.0, 200.0],
            "x": [0.0, 200.0],
        },
    )
    dataset.to_netcdf(path, engine="scipy")


def test_ingests_valid_tiny_netcdf_metadata(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    run_dir = manifest_path.parent
    netcdf_path = run_dir / "cm1out_000001.nc"
    raw_path = run_dir / "cm1out_000001_s.dat"
    write_tiny_netcdf(netcdf_path)
    raw_path.write_text("raw CM1 artifact")
    complete_manifest(
        manifest_path,
        OutputMetadata(
            raw_cm1_artifacts=[str(raw_path)],
            netcdf_paths=[str(netcdf_path)],
            runtime_warnings=[
                "CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG"
            ],
        ),
    )

    result = ingest_completed_run(manifest_path)

    assert result.result_id == "result-run-ingest"
    assert result.run_id == "run-ingest"
    assert result.scenario_id == "baseline-shallow-cumulus"
    assert result.physical_question
    assert result.run_size_preset == "quick_look"
    assert result.source_lifecycle_state == "completed"
    assert result.source_product_state == "completed_cm1_result"
    assert result.source_model == "CM1"
    assert result.netcdf_paths == [str(netcdf_path)]
    assert result.raw_cm1_artifacts == [str(raw_path)]
    assert result.processed_artifacts == []
    assert result.visualization_ready_artifacts == []
    assert result.dimensions == {"time": 1, "z": 2, "y": 2, "x": 2}
    assert result.coordinates == ["time", "z", "y", "x"]
    assert result.variables == ["qc", "w"]
    assert result.time_coordinate == "time"
    assert result.time_steps == 1
    assert result.grid_shape == [2, 2, 2]
    assert [(field.name, field.units) for field in result.fields_detected] == [
        ("qc", "kg/kg"),
        ("w", "m/s"),
    ]
    assert result.diagnostics_summary is None
    assert result.warnings == [
        "CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG"
    ]
    assert (run_dir / RESULT_METADATA_FILENAME).exists()


def test_result_metadata_serializes_and_lists_from_runtime_home(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = create_manifest(tmp_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    write_tiny_netcdf(netcdf_path)
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(netcdf_path)]))

    result = ingest_completed_run(manifest_path)
    round_tripped = result_metadata_from_json(result.to_json_text())
    listed = list_result_metadata(settings)
    found = get_result_metadata(settings, result.result_id)

    assert round_tripped == result
    assert listed == [result]
    assert found == result


def test_missing_netcdf_output_fails_gracefully(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    raw_path = manifest_path.parent / "cm1out_000001_s.dat"
    raw_path.write_text("raw CM1 artifact")
    complete_manifest(
        manifest_path,
        OutputMetadata(raw_cm1_artifacts=[str(raw_path)]),
    )

    with pytest.raises(ResultIngestError, match="No NetCDF output artifacts"):
        ingest_completed_run(manifest_path)


def test_packaged_manifest_is_not_ingested(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    write_tiny_netcdf(netcdf_path)

    with pytest.raises(ResultIngestError, match="Only completed CM1 runs"):
        ingest_completed_run(manifest_path)


def test_malformed_netcdf_fails_gracefully(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    netcdf_path.write_text("not a netcdf file")
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(netcdf_path)]))

    with pytest.raises(ResultIngestError, match="Could not open NetCDF output"):
        ingest_completed_run(manifest_path)


def test_missing_expected_fields_are_warnings_not_claimed_diagnostics(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    write_tiny_netcdf(netcdf_path, include_qc=False, include_w=True)
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(netcdf_path)]))

    result = ingest_completed_run(manifest_path)

    assert result.variables == ["w"]
    assert result.diagnostics_summary is None
    assert result.warnings == ["Expected fields missing from NetCDF metadata: qc"]
