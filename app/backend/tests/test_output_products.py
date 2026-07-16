from pathlib import Path

import pytest
import xarray as xr

from cloud_chamber.output_products import (
    OutputProductManifest,
    OutputProductManifestError,
    build_interesting_time_product,
    build_output_product_manifest,
    classify_output_paths,
    default_output_product_manifest_path,
    output_product_manifest_from_json,
    resolve_time_index,
    write_output_product_manifest,
)
from cloud_chamber.result_diagnostics import (
    CloudDiagnostics,
    DifferentialPatchGeometryDiagnostics,
    FieldQuality,
    LocalizedResponseDiagnostics,
    PatchSpatialFieldDiagnostics,
    RainDiagnostics,
    ReflectivityDiagnostics,
    ResultDiagnostics,
    SurfaceRainDiagnostics,
    TimeDiagnostics,
    TimeValue,
    VerticalVelocityDiagnostics,
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


def test_interesting_times_preserve_inferred_time_caveats(tmp_path: Path) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=None, values=[0.0, 2e-6])
    manifest = build_manifest(tmp_path, [model])
    diagnostics = ResultDiagnostics(
        cloud=CloudDiagnostics(
            formed=True,
            first_cloud_time_seconds=1.0,
            max_qc_kg_kg=2e-6,
            time_of_max_qc_seconds=1.0,
        ),
        vertical_velocity=VerticalVelocityDiagnostics(
            max_w_m_s=1.5,
            time_of_max_w_seconds=1.0,
            min_w_m_s=-0.5,
            time_of_min_w_seconds=0.0,
            units="m/s",
        ),
        rain=RainDiagnostics(available=False, field_absent=True),
        time=TimeDiagnostics(source="inferred_output_index", fallback_used=True),
        caveats=["diagnostics_used_inferred_time"],
    )

    product = build_interesting_time_product(
        result_id="result-run-output-products",
        diagnostics=diagnostics,
        output_manifest=manifest,
        variables=["qc", "w"],
    )

    records = {record.key: record for record in product.available_interesting_times}
    assert records["first_cloud"].time_index == 1
    assert records["first_cloud"].support_state == "supported"
    assert "time_coordinate_missing" in records["first_cloud"].caveats
    assert "diagnostics_used_inferred_time" in product.caveats
    assert product.default_time_by_field["qc"].time_index == 1
    assert product.science_summary.default_explore_time_index == 1


def test_deep_convection_interesting_times_and_unavailable_diagnostics(
    tmp_path: Path,
) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[0.0, 600.0, 1200.0], values=[0.0, 1.0, 2.0])
    manifest = build_manifest(tmp_path, [model])
    diagnostics = ResultDiagnostics(
        cloud=CloudDiagnostics(
            formed=True,
            first_cloud_time_seconds=600.0,
            cloud_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=3500.0),
                TimeValue(time_seconds=1200.0, value=10200.0),
            ],
            liquid_cloud_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=2500.0),
                TimeValue(time_seconds=1200.0, value=6200.0),
            ],
            hydrometeor_envelope_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=3500.0),
                TimeValue(time_seconds=1200.0, value=10200.0),
            ],
            hydrometeor_envelope_source_fields=["qc", "qi", "qs"],
            raw_hydrometeor_envelope_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=3500.0),
                TimeValue(time_seconds=1200.0, value=10200.0),
            ],
            coherent_cloud_object_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=3500.0),
                TimeValue(time_seconds=1200.0, value=10200.0),
            ],
            coherent_cloud_object_source_fields=["qc", "qi", "qs"],
            max_qc_kg_kg=2e-5,
            time_of_max_qc_seconds=1200.0,
        ),
        vertical_velocity=VerticalVelocityDiagnostics(
            max_w_m_s=14.0,
            time_of_max_w_seconds=600.0,
            min_w_m_s=-6.0,
            time_of_min_w_seconds=1200.0,
            units="m/s",
        ),
        rain=RainDiagnostics(
            present=True,
            first_rain_time_seconds=1200.0,
            max_qr_kg_kg=3e-7,
            time_of_max_qr_seconds=1200.0,
        ),
        time=TimeDiagnostics(source="netcdf_time_coordinate", fallback_used=False),
    )

    product = build_interesting_time_product(
        result_id="result-deep",
        diagnostics=diagnostics,
        output_manifest=manifest,
        variables=["qc", "w", "qr"],
    )

    records = {record.key: record for record in product.available_interesting_times}
    assert records["first_deep_convection"].support_state == "supported"
    assert records["first_deep_convection"].time_index == 2
    assert records["first_deep_convection"].source_field is not None
    assert records["first_deep_convection"].source_field.startswith("coherent_cloud_object:")
    assert records["highest_liquid_cloud_top"].label == "Highest liquid cloud-water top"
    assert records["highest_liquid_cloud_top"].value == 6200.0
    assert records["highest_cloud_top"].label == "Highest coherent cloud-object top"
    assert records["highest_cloud_top"].value == 10200.0
    assert records["highest_raw_hydrometeor_envelope_top"].label == (
        "Highest raw hydrometeor trace top"
    )
    assert records["highest_raw_hydrometeor_envelope_top"].value == 10200.0
    assert records["max_updraft_w"].time_index == 1
    assert product.science_summary.cloud_formed is True
    assert product.science_summary.deep_cloud_formed is True
    assert product.science_summary.strong_updraft_formed is True
    assert product.science_summary.time_of_first_deep_convection_seconds == 1200.0
    assert product.science_summary.highest_cloud_top_m == 10200.0
    assert product.science_summary.highest_liquid_cloud_top_m == 6200.0
    assert product.science_summary.highest_coherent_cloud_object_top_m == 10200.0
    assert product.science_summary.highest_raw_hydrometeor_envelope_top_m == 10200.0
    assert product.science_summary.highest_hydrometeor_envelope_top_m == 10200.0
    assert product.science_summary.coherent_cloud_object_source_fields == ["qc", "qi", "qs"]
    assert product.science_summary.hydrometeor_envelope_source_fields == ["qc", "qi", "qs"]
    assert product.science_summary.default_explore_time_index == 2
    assert product.science_summary.cm1_outcome is None
    availability = {item.key: item for item in product.science_summary.diagnostic_availability}
    assert availability["max_dbz_or_reflectivity_proxy"].support_state == (
        "unsupported_missing_fields"
    )
    assert availability["cold_pool_proxy"].support_state == "unsupported_missing_fields"


def test_sparse_raw_hydrometeor_trace_does_not_support_deep_convection(
    tmp_path: Path,
) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[0.0, 600.0, 1200.0], values=[0.0, 1.0, 2.0])
    manifest = build_manifest(tmp_path, [model])
    diagnostics = ResultDiagnostics(
        cloud=CloudDiagnostics(
            formed=True,
            first_cloud_time_seconds=600.0,
            cloud_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=2500.0),
                TimeValue(time_seconds=1200.0, value=6200.0),
            ],
            liquid_cloud_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=2500.0),
                TimeValue(time_seconds=1200.0, value=6200.0),
            ],
            raw_hydrometeor_envelope_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=2500.0),
                TimeValue(time_seconds=1200.0, value=10200.0),
            ],
            hydrometeor_envelope_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=2500.0),
                TimeValue(time_seconds=1200.0, value=10200.0),
            ],
            hydrometeor_envelope_source_fields=["qc", "qs"],
            coherent_cloud_object_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=2500.0),
                TimeValue(time_seconds=1200.0, value=6200.0),
            ],
            coherent_cloud_object_source_fields=["qc"],
            max_qc_kg_kg=2e-5,
            time_of_max_qc_seconds=1200.0,
        ),
        vertical_velocity=VerticalVelocityDiagnostics(
            max_w_m_s=14.0,
            time_of_max_w_seconds=600.0,
            min_w_m_s=-6.0,
            time_of_min_w_seconds=1200.0,
            units="m/s",
        ),
        rain=RainDiagnostics(
            present=True,
            first_rain_time_seconds=1200.0,
            max_qr_kg_kg=3e-7,
            time_of_max_qr_seconds=1200.0,
        ),
        time=TimeDiagnostics(source="netcdf_time_coordinate", fallback_used=False),
    )

    product = build_interesting_time_product(
        result_id="result-sparse-trace",
        diagnostics=diagnostics,
        output_manifest=manifest,
        variables=["qc", "w", "qr"],
    )

    records = {record.key: record for record in product.available_interesting_times}
    assert records["highest_cloud_top"].value == 6200.0
    assert records["highest_raw_hydrometeor_envelope_top"].value == 10200.0
    assert records["first_deep_convection"].support_state == "unavailable"
    assert product.science_summary.deep_cloud_formed is False
    assert product.science_summary.time_of_first_deep_convection_seconds is None
    assert product.science_summary.highest_cloud_top_m == 6200.0
    assert product.science_summary.highest_raw_hydrometeor_envelope_top_m == 10200.0


def test_science_summary_preserves_localized_response_diagnostics(tmp_path: Path) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[0.0, 600.0], values=[0.0, 1.0])
    manifest = build_manifest(tmp_path, [model])
    diagnostics = ResultDiagnostics(
        cloud=CloudDiagnostics(available=True, formed=False),
        vertical_velocity=VerticalVelocityDiagnostics(max_w_m_s=1.0, units="m/s"),
        rain=RainDiagnostics(available=True, present=False),
        time=TimeDiagnostics(source="netcdf_time_coordinate", fallback_used=False),
        localized_response=LocalizedResponseDiagnostics(
            available=True,
            support_state="supported",
            geometry=DifferentialPatchGeometryDiagnostics(
                pattern_sha256="patch-sha",
                shape="circle",
                center_x_m=0.0,
                center_y_m=0.0,
                radius_x_m=1500.0,
                radius_y_m=1500.0,
                taper_width_m=500.0,
                ramp_seconds=1800.0,
            ),
            hfx_footprint=PatchSpatialFieldDiagnostics(
                source_field="hfx",
                available=True,
                max_value=54.0,
                center_to_outside_ratio=6.0,
                max_distance_from_patch_center_m=0.0,
            ),
            qfx_footprint=PatchSpatialFieldDiagnostics(
                source_field="qfx",
                available=True,
                max_value=1.1e-4,
                center_to_outside_ratio=2.0,
                max_distance_from_patch_center_m=0.0,
            ),
        ),
    )

    product = build_interesting_time_product(
        result_id="result-localized-response",
        diagnostics=diagnostics,
        output_manifest=manifest,
        variables=["qc", "w", "hfx", "qfx"],
    )

    response = product.science_summary.localized_response
    assert response.available is True
    assert response.geometry is not None
    assert response.geometry.pattern_sha256 == "patch-sha"
    assert response.geometry.radius_x_m == 1500.0
    assert response.geometry.taper_width_m == 500.0
    assert response.hfx_footprint.center_to_outside_ratio == 6.0
    assert response.qfx_footprint.center_to_outside_ratio == 2.0


def test_composite_cloud_top_uses_contributing_field_quality(tmp_path: Path) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[0.0, 600.0], values=[0.0, 1.0])
    manifest = build_manifest(tmp_path, [model])
    diagnostics = ResultDiagnostics(
        cloud=CloudDiagnostics(
            formed=True,
            first_cloud_time_seconds=600.0,
            cloud_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=9500.0),
            ],
            coherent_cloud_object_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=9500.0),
            ],
            coherent_cloud_object_source_fields=["qc", "qi"],
            max_qc_kg_kg=2e-5,
            time_of_max_qc_seconds=600.0,
        ),
        vertical_velocity=VerticalVelocityDiagnostics(
            max_w_m_s=14.0,
            time_of_max_w_seconds=600.0,
            units="m/s",
        ),
        rain=RainDiagnostics(available=False, field_absent=True),
        time=TimeDiagnostics(source="netcdf_time_coordinate", fallback_used=False),
        field_quality_assessed=True,
        field_quality={
            "qc": FieldQuality(field="qc", source_field="qc", quality_state="trusted"),
            "qi": FieldQuality(
                field="qi",
                source_field="qi",
                quality_state="untrusted",
                reason="qi_field_entirely_non_finite",
                caveats=["qi_field_entirely_non_finite"],
            ),
        },
    )

    product = build_interesting_time_product(
        result_id="result-untrusted-ice-top",
        diagnostics=diagnostics,
        output_manifest=manifest,
        variables=["qc", "w"],
    )

    records = {record.key: record for record in product.available_interesting_times}
    assert records["highest_cloud_top"].support_state == "unavailable"
    assert "interesting_time_source_field_untrusted" in records["highest_cloud_top"].caveats
    assert product.science_summary.deep_cloud_formed is None
    assert product.science_summary.highest_cloud_top_m is None


def test_precipitation_and_reflectivity_outputs_are_supported_when_diagnosed(
    tmp_path: Path,
) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[0.0, 600.0], values=[0.0, 1.0])
    manifest = build_manifest(tmp_path, [model])
    diagnostics = ResultDiagnostics(
        cloud=CloudDiagnostics(formed=True),
        vertical_velocity=VerticalVelocityDiagnostics(max_w_m_s=4.0, units="m/s"),
        rain=RainDiagnostics(
            present=True,
            first_rain_time_seconds=600.0,
            max_qr_kg_kg=4e-7,
            time_of_max_qr_seconds=600.0,
        ),
        surface_rain=SurfaceRainDiagnostics(
            present=True,
            max_surface_rain=3.5,
            time_of_max_surface_rain_seconds=600.0,
            surface_rain_max_time_series=[
                TimeValue(time_seconds=0.0, value=0.0),
                TimeValue(time_seconds=600.0, value=3.5),
            ],
            units="mm",
            available=True,
            field_absent=False,
        ),
        reflectivity=ReflectivityDiagnostics(
            max_dbz=28.0,
            time_of_max_dbz_seconds=600.0,
            dbz_max_time_series=[
                TimeValue(time_seconds=0.0, value=-5.0),
                TimeValue(time_seconds=600.0, value=28.0),
            ],
            units="dBZ",
            available=True,
            field_absent=False,
        ),
        time=TimeDiagnostics(source="netcdf_time_coordinate", fallback_used=False),
    )

    product = build_interesting_time_product(
        result_id="result-precip-fields",
        diagnostics=diagnostics,
        output_manifest=manifest,
        variables=["qc", "w", "qr", "rain", "dbz"],
    )

    records = {record.key: record for record in product.available_interesting_times}
    assert records["rain_onset"].label == "Rain-water onset"
    assert records["max_qr"].label == "Max rain water aloft"
    assert records["max_surface_rain"].support_state == "supported"
    assert records["max_surface_rain"].value == 3.5
    assert records["max_surface_rain"].units == "mm"
    assert records["max_dbz"].support_state == "supported"
    assert records["max_dbz"].value == 28.0
    assert records["max_dbz"].units == "dBZ"
    assert product.default_time_by_field["rain"].source_interesting_time_key == "max_surface_rain"
    assert product.default_time_by_field["dbz"].source_interesting_time_key == "max_dbz"
    assert product.science_summary.max_rain_or_surface_precip == 3.5
    assert product.science_summary.max_dbz_or_reflectivity_proxy == 28.0
    availability = {item.key: item for item in product.science_summary.diagnostic_availability}
    assert availability["max_rain_or_surface_precip"].support_state == "supported"
    assert availability["max_dbz_or_reflectivity_proxy"].support_state == "supported"


def test_non_deep_summary_does_not_emit_deep_convection_outcome(
    tmp_path: Path,
) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[0.0, 600.0], values=[0.0, 1.0])
    manifest = build_manifest(tmp_path, [model])
    diagnostics = ResultDiagnostics(
        cloud=CloudDiagnostics(
            formed=False,
            max_qc_kg_kg=0.0,
            time_of_max_qc_seconds=0.0,
            cloud_top_time_series=[
                TimeValue(time_seconds=0.0, value=None),
                TimeValue(time_seconds=600.0, value=None),
            ],
        ),
        vertical_velocity=VerticalVelocityDiagnostics(
            max_w_m_s=1.5,
            time_of_max_w_seconds=600.0,
            min_w_m_s=-0.5,
            time_of_min_w_seconds=0.0,
            units="m/s",
        ),
        rain=RainDiagnostics(available=False, field_absent=True),
        time=TimeDiagnostics(source="netcdf_time_coordinate", fallback_used=False),
    )

    product = build_interesting_time_product(
        result_id="result-shallow",
        diagnostics=diagnostics,
        output_manifest=manifest,
        variables=["qc", "w"],
        run_recipe="observed_surface_forced_evolution",
    )

    records = {record.key: record for record in product.available_interesting_times}
    assert records["first_deep_convection"].support_state == "unavailable"
    assert product.science_summary.cm1_outcome is None
    assert product.science_summary.time_of_first_deep_convection_seconds is None


def test_deep_convection_present_but_unsupported_fields_are_caveated(
    tmp_path: Path,
) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[0.0], values=[0.0])
    manifest = build_manifest(tmp_path, [model])
    diagnostics = ResultDiagnostics(
        cloud=CloudDiagnostics(formed=False),
        vertical_velocity=VerticalVelocityDiagnostics(max_w_m_s=0.0, units="m/s"),
        rain=RainDiagnostics(available=False, field_absent=True),
        time=TimeDiagnostics(source="netcdf_time_coordinate", fallback_used=False),
    )

    product = build_interesting_time_product(
        result_id="result-deep",
        diagnostics=diagnostics,
        output_manifest=manifest,
        variables=["qc", "w", "dbz", "th"],
    )

    availability = {item.key: item for item in product.science_summary.diagnostic_availability}
    assert availability["max_dbz_or_reflectivity_proxy"].support_state == (
        "unsupported_missing_diagnostic"
    )
    assert availability["cold_pool_proxy"].support_state == "unsupported_missing_diagnostic"
    assert "max_dbz_or_reflectivity_proxy_diagnostic_not_implemented" in (
        availability["max_dbz_or_reflectivity_proxy"].caveats
    )


def test_interesting_times_expose_untrusted_field_quality(tmp_path: Path) -> None:
    model = tmp_path / "cm1out_000001.nc"
    write_model_netcdf(model, times=[0.0], values=[2e-6])
    manifest = build_manifest(tmp_path, [model])
    diagnostics = ResultDiagnostics(
        cloud=CloudDiagnostics(
            formed=True,
            first_cloud_time_seconds=0.0,
            max_qc_kg_kg=2e-6,
            time_of_max_qc_seconds=0.0,
        ),
        vertical_velocity=VerticalVelocityDiagnostics(max_w_m_s=1.0, units="m/s"),
        rain=RainDiagnostics(available=False, field_absent=True),
        time=TimeDiagnostics(source="netcdf_time_coordinate", fallback_used=False),
        field_quality_assessed=True,
        field_quality={
            "qc": FieldQuality(
                field="qc",
                source_field="qc",
                quality_state="untrusted",
                reason="qc_field_entirely_non_finite",
                finite_count=0,
                non_finite_count=1,
                total_count=1,
                caveats=[
                    "non_finite_values_detected_in_qc",
                    "qc_field_entirely_non_finite",
                ],
            )
        },
    )

    product = build_interesting_time_product(
        result_id="result-field-quality",
        diagnostics=diagnostics,
        output_manifest=manifest,
        variables=["qc", "w"],
    )

    records = {record.key: record for record in product.available_interesting_times}
    assert records["first_cloud"].support_state == "unavailable"
    assert records["first_cloud"].field_quality is not None
    assert records["first_cloud"].field_quality.quality_state == "untrusted"
    assert "interesting_time_source_field_untrusted" in records["first_cloud"].caveats
    assert product.science_summary.field_quality_assessed is True
    assert product.science_summary.field_quality["qc"].quality_state == "untrusted"
