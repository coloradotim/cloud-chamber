import json
from pathlib import Path

import pytest
import xarray as xr

from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.output_products import (
    default_output_product_manifest_path,
    output_product_manifest_from_json,
)
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


def write_model_netcdf(
    path: Path,
    *,
    times: list[float],
    qc_values: list[float],
    w_values: list[float],
    include_qc: bool = True,
    include_w: bool = True,
) -> None:
    data_vars = {}
    if include_qc:
        data_vars["qc"] = (
            ("time", "z", "y", "x"),
            [
                [[[qc_value for _x in range(4)] for _y in range(3)] for _z in range(2)]
                for qc_value in qc_values
            ],
            {"units": "kg/kg"},
        )
    if include_w:
        data_vars["w"] = (
            ("time", "z", "y", "x"),
            [
                [[[w_value for _x in range(4)] for _y in range(3)] for _z in range(2)]
                for w_value in w_values
            ],
            {"units": "m/s"},
        )
    xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": times,
            "z": [500.0, 1500.0],
            "y": [0.0, 200.0, 400.0],
            "x": [0.0, 200.0, 400.0, 600.0],
        },
    ).to_netcdf(path, engine="scipy")


def write_stats_netcdf(path: Path) -> None:
    xr.Dataset(
        data_vars={"mass": (("time",), [1.0], {"units": "kg"})},
        coords={"time": [0.0]},
    ).to_netcdf(path, engine="scipy")


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
    product_manifest_path = default_output_product_manifest_path(run_dir)
    assert result.processed_artifacts == [str(product_manifest_path)]
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
    assert result.diagnostics_summary == "no cloud formed; no rain detected"
    assert result.diagnostics is not None
    assert result.diagnostics.cloud.formed is False
    assert result.diagnostics.rain.field_absent is True
    assert result.process_diagnostics is not None
    assert (
        result.process_diagnostics.interpretation_support.thermal_fate_label
        == "Thermal without cloud"
    )
    assert result.process_diagnostics.interpretation_support.confidence == "supported"
    assert result.process_diagnostics.deep_breakthrough.status == "unsupported_missing_fields"
    assert result.warnings == [
        "CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG"
    ]
    assert (run_dir / RESULT_METADATA_FILENAME).exists()
    assert product_manifest_path.exists()
    product_manifest = output_product_manifest_from_json(product_manifest_path.read_text())
    assert product_manifest.result_id == result.result_id
    assert product_manifest.run_id == result.run_id
    assert product_manifest.source_result_metadata_path == str(run_dir / RESULT_METADATA_FILENAME)
    assert product_manifest.source_run_manifest_path == str(manifest_path)
    assert [entry.time_index for entry in product_manifest.time_index] == [0]
    assert product_manifest.time_index[0].source_file == str(netcdf_path)
    assert product_manifest.time_index[0].local_time_index == 0


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


def test_ingests_multifile_model_output_sequence_and_excludes_stats(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-multifile")
    run_dir = manifest_path.parent
    first = run_dir / "cm1out_000001.nc"
    second = run_dir / "cm1out_000002.nc"
    stats = run_dir / "cm1out_stats.nc"
    write_model_netcdf(first, times=[300.0], qc_values=[0.0], w_values=[-5.0])
    write_model_netcdf(second, times=[600.0], qc_values=[2e-6], w_values=[7.0])
    write_stats_netcdf(stats)
    complete_manifest(
        manifest_path,
        OutputMetadata(netcdf_paths=[str(second), str(stats), str(first)]),
    )

    result = ingest_completed_run(manifest_path)

    assert result.model_output_paths == [str(first), str(second)]
    assert result.stats_netcdf_paths == [str(stats)]
    assert result.model_output_file_count == 2
    assert result.time_steps == 2
    assert result.first_output_time_seconds == 300.0
    assert result.last_output_time_seconds == 600.0
    assert result.time_coordinate_source == "netcdf_time_coordinate"
    assert result.time_coordinate_fallback_used is False
    assert result.diagnostics is not None
    assert result.diagnostics.cloud.formed is True
    assert result.diagnostics.cloud.first_cloud_time_seconds == 600.0
    assert len(result.diagnostics.cloud.qc_max_time_series) == 2
    assert result.diagnostics.cloud.max_qc_kg_kg == 2e-6
    assert result.diagnostics.cloud.time_of_max_qc_seconds == 600.0
    assert result.diagnostics.vertical_velocity.min_w_m_s == -5.0
    assert result.diagnostics.vertical_velocity.max_w_m_s == 7.0


def test_ingests_multifile_with_multiple_timesteps_per_file(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-multistep")
    run_dir = manifest_path.parent
    first = run_dir / "cm1out_000001.nc"
    second = run_dir / "cm1out_000002.nc"
    write_model_netcdf(first, times=[0.0, 300.0], qc_values=[0.0, 0.0], w_values=[-1.0, 2.0])
    write_model_netcdf(
        second,
        times=[600.0, 900.0],
        qc_values=[0.0, 4e-6],
        w_values=[3.0, 4.0],
    )
    complete_manifest(
        manifest_path,
        OutputMetadata(netcdf_paths=[str(second), str(first)]),
    )

    result = ingest_completed_run(manifest_path)

    assert result.model_output_file_count == 2
    assert result.time_steps == 4
    assert result.first_output_time_seconds == 0.0
    assert result.last_output_time_seconds == 900.0
    assert result.diagnostics is not None
    assert len(result.diagnostics.cloud.qc_max_time_series) == 4
    assert result.diagnostics.cloud.formed is True
    assert result.diagnostics.cloud.first_cloud_time_seconds == 900.0
    assert result.diagnostics.vertical_velocity.time_of_max_w_seconds == 900.0


def test_ingest_records_corrupt_model_file_caveat_and_uses_remaining_outputs(
    tmp_path: Path,
) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-corrupt")
    run_dir = manifest_path.parent
    first = run_dir / "cm1out_000001.nc"
    corrupt = run_dir / "cm1out_000002.nc"
    write_model_netcdf(first, times=[300.0], qc_values=[0.0], w_values=[1.0])
    corrupt.write_text("not netcdf")
    complete_manifest(
        manifest_path,
        OutputMetadata(netcdf_paths=[str(corrupt), str(first)]),
    )

    result = ingest_completed_run(manifest_path)

    assert result.model_output_paths == [str(first)]
    assert result.model_output_file_count == 1
    assert len(result.skipped_netcdf_paths) == 1
    assert str(corrupt) in result.skipped_netcdf_paths[0]
    assert any("skipped_netcdf_output" in warning for warning in result.warnings)


def test_ingest_fails_when_only_stats_netcdf_exists(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    stats = manifest_path.parent / "cm1out_stats.nc"
    write_stats_netcdf(stats)
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(stats)]))

    with pytest.raises(ResultIngestError, match="No CM1 model-field NetCDF output files"):
        ingest_completed_run(manifest_path)


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
    assert result.diagnostics_summary == "no cloud formed; no rain detected"
    assert result.diagnostics is not None
    assert result.diagnostics.cloud.available is False
    assert result.warnings == ["Expected fields missing from NetCDF metadata: qc"]
