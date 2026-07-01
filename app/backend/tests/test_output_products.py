from pathlib import Path

import pytest
import xarray as xr

from cloud_chamber.output_products import (
    OutputProductManifest,
    OutputProductManifestError,
    build_output_product_manifest,
    classify_output_paths,
    default_output_product_manifest_path,
    output_product_manifest_from_json,
    resolve_time_index,
    write_output_product_manifest,
)


def write_model_netcdf(
    path: Path,
    *,
    times: list[float] | None,
    values: list[float],
) -> None:
    coords = {"z": [0.0], "y": [0.0], "x": [0.0]}
    if times is not None:
        coords["time"] = times
    xr.Dataset(
        data_vars={
            "qc": (
                ("time", "z", "y", "x"),
                [[[[value]]] for value in values],
                {"units": "kg/kg"},
            )
        },
        coords=coords,
    ).to_netcdf(path, engine="scipy")


def write_no_time_dimension_netcdf(path: Path) -> None:
    xr.Dataset(
        data_vars={
            "qc": (
                ("z", "y", "x"),
                [[[0.0]]],
                {"units": "kg/kg"},
            )
        },
        coords={"z": [0.0], "y": [0.0], "x": [0.0]},
    ).to_netcdf(path, engine="scipy")


def write_stats_netcdf(path: Path) -> None:
    xr.Dataset(
        data_vars={"mass": (("time",), [1.0])},
        coords={"time": [0.0]},
    ).to_netcdf(path, engine="scipy")


def build_manifest(tmp_path: Path, paths: list[Path]) -> OutputProductManifest:
    classified = classify_output_paths(paths)
    return build_output_product_manifest(
        result_id="result-run-output-products",
        run_id="run-output-products",
        scenario_id="baseline-shallow-cumulus",
        model_output_paths=classified.model_output_paths,
        stats_netcdf_paths=classified.stats_netcdf_paths,
        raw_cm1_artifacts=classified.other_paths,
        source_result_metadata_path=tmp_path / "result_metadata.json",
        source_run_manifest_path=tmp_path / "run_manifest.json",
        product_root=tmp_path / "derived-products",
    )


def test_single_model_output_file_with_one_timestep(tmp_path: Path) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[300.0], values=[0.0])

    manifest = build_manifest(tmp_path, [model])

    assert manifest.manifest_version == 1
    assert manifest.source_raw_outputs.model_output_files == [str(model)]
    assert manifest.source_raw_outputs.stats_files == []
    assert len(manifest.time_index) == 1
    entry = manifest.time_index[0]
    assert entry.time_index == 0
    assert entry.time_seconds == 300.0
    assert entry.source_file == str(model)
    assert entry.source_file_kind == "model_output_netcdf"
    assert entry.local_time_index == 0
    assert entry.time_source == "netcdf_time_coordinate"
    assert entry.time_caveats == []


def test_single_model_output_file_with_multiple_timesteps(tmp_path: Path) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[0.0, 600.0, 1200.0], values=[0.0, 1.0, 2.0])

    manifest = build_manifest(tmp_path, [model])

    assert [
        (entry.time_index, entry.time_seconds, entry.local_time_index)
        for entry in manifest.time_index
    ] == [
        (0, 0.0, 0),
        (1, 600.0, 1),
        (2, 1200.0, 2),
    ]
    resolved = resolve_time_index(manifest, 2)
    assert resolved.source_file == str(model)
    assert resolved.local_time_index == 2


def test_multi_file_sequence_with_one_timestep_per_file_excludes_stats(tmp_path: Path) -> None:
    first = tmp_path / "cm1out_000001.nc"
    second = tmp_path / "cm1out_000002.nc"
    stats = tmp_path / "cm1out_stats.nc"
    write_model_netcdf(first, times=[900.0], values=[1.0])
    write_model_netcdf(second, times=[1800.0], values=[2.0])
    write_stats_netcdf(stats)

    manifest = build_manifest(tmp_path, [second, stats, first])

    assert manifest.source_raw_outputs.model_output_files == [str(first), str(second)]
    assert manifest.source_raw_outputs.stats_files == [str(stats)]
    assert [entry.time_seconds for entry in manifest.time_index] == [900.0, 1800.0]
    assert resolve_time_index(manifest, 0).source_file == str(first)
    assert resolve_time_index(manifest, 1).source_file == str(second)
    assert all(entry.source_file != str(stats) for entry in manifest.time_index)


def test_inferred_order_based_time_mapping_records_caveats(tmp_path: Path) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=None, values=[0.0, 1.0])

    manifest = build_manifest(tmp_path, [model])

    assert [entry.time_seconds for entry in manifest.time_index] == [0.0, 1.0]
    assert [entry.local_time_index for entry in manifest.time_index] == [0, 1]
    assert {entry.time_source for entry in manifest.time_index} == {"inferred_filename_order"}
    assert "inferred_time_indices_present" in manifest.caveats
    assert "global_time_index_preserves_filename_order_due_to_inferred_times" in manifest.caveats
    assert all("time_coordinate_missing" in entry.time_caveats for entry in manifest.time_index)


def test_no_time_dimension_records_single_inferred_timestep(tmp_path: Path) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_no_time_dimension_netcdf(model)

    manifest = build_manifest(tmp_path, [model])

    assert len(manifest.time_index) == 1
    assert manifest.time_index[0].local_time_index == 0
    assert manifest.time_index[0].time_source == "inferred_filename_order"
    assert "time_coordinate_missing" in manifest.time_index[0].time_caveats


def test_duplicate_and_non_monotonic_direct_times_are_caveated(tmp_path: Path) -> None:
    first = tmp_path / "cm1out_000001.nc"
    second = tmp_path / "cm1out_000002.nc"
    write_model_netcdf(first, times=[600.0], values=[1.0])
    write_model_netcdf(second, times=[300.0, 600.0], values=[2.0, 3.0])

    manifest = build_manifest(tmp_path, [first, second])

    assert [entry.time_seconds for entry in manifest.time_index] == [300.0, 600.0, 600.0]
    assert "non_monotonic_time_coordinates_detected" in manifest.caveats
    assert "duplicate_time_coordinate_detected:600" in manifest.caveats
    duplicate_entries = [entry for entry in manifest.time_index if entry.time_seconds == 600.0]
    assert all("duplicate_time_coordinate" in entry.time_caveats for entry in duplicate_entries)


def test_missing_or_corrupt_file_is_caveated_when_other_outputs_remain(tmp_path: Path) -> None:
    valid = tmp_path / "cm1out_000001.nc"
    corrupt = tmp_path / "cm1out_000002.nc"
    missing = tmp_path / "cm1out_000003.nc"
    write_model_netcdf(valid, times=[300.0], values=[1.0])
    corrupt.write_text("not netcdf")

    manifest = build_output_product_manifest(
        result_id="result-run-output-products",
        run_id="run-output-products",
        model_output_paths=[valid, corrupt, missing],
        product_root=tmp_path / "derived-products",
    )

    assert [entry.source_file for entry in manifest.time_index] == [str(valid)]
    assert any(str(corrupt) in caveat for caveat in manifest.caveats)
    assert f"missing_model_output_file:{missing}" in manifest.caveats


def test_all_unreadable_model_files_fail_cleanly(tmp_path: Path) -> None:
    corrupt = tmp_path / "cm1out_000001.nc"
    corrupt.write_text("not netcdf")

    with pytest.raises(OutputProductManifestError, match="No model-output timesteps"):
        build_output_product_manifest(
            result_id="result-run-output-products",
            run_id="run-output-products",
            model_output_paths=[corrupt],
            product_root=tmp_path / "derived-products",
        )


def test_manifest_can_be_written_and_read_from_runtime_product_path(tmp_path: Path) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[300.0], values=[0.0])
    manifest = build_manifest(tmp_path, [model])
    path = default_output_product_manifest_path(tmp_path)

    write_output_product_manifest(path, manifest)
    round_tripped = output_product_manifest_from_json(path.read_text())

    assert round_tripped == manifest
    assert path == tmp_path / "derived-products" / "output_product_manifest.json"
    assert not any(".git" in part for part in path.parts)


def test_resolve_time_index_rejects_unavailable_index(tmp_path: Path) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[300.0], values=[0.0])
    manifest = build_manifest(tmp_path, [model])

    with pytest.raises(OutputProductManifestError, match="time_index is not available"):
        resolve_time_index(manifest, 2)
