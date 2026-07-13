from pathlib import Path
from typing import Any

import xarray as xr

from cloud_chamber.result_diagnostics import (
    compute_baseline_diagnostics,
    compute_process_diagnostics,
)


def write_dataset(path: Path, dataset: xr.Dataset) -> xr.Dataset:
    dataset.to_netcdf(path, engine="scipy")
    return xr.open_dataset(path)


def base_dataset(
    *,
    qc_values: list[list[list[list[float]]]] | None = None,
    w_values: list[list[list[list[float]]]] | None = None,
    qr_values: list[list[list[list[float]]]] | None = None,
    rain_values: list[list[list[float]]] | None = None,
    dbz_values: list[list[list[list[float]]]] | None = None,
    qi_values: list[list[list[list[float]]]] | None = None,
    qs_values: list[list[list[list[float]]]] | None = None,
    qg_values: list[list[list[list[float]]]] | None = None,
    include_time_coord: bool = True,
    z_values: list[float] | None = None,
    z_units: str | None = None,
) -> xr.Dataset:
    coords: dict[str, list[float]] = {
        "z": z_values or [500.0, 1500.0],
        "y": [0.0, 200.0, 400.0],
        "x": [0.0, 200.0, 400.0, 600.0],
    }
    if include_time_coord:
        coords["time"] = [0.0, 300.0]
    else:
        coords["time"] = []
    data_vars: dict[str, Any] = {}
    if qc_values is not None:
        data_vars["qc"] = (
            ("time", "z", "y", "x"),
            qc_values,
            {"units": "kg/kg"},
        )
    if w_values is not None:
        data_vars["w"] = (
            ("time", "z", "y", "x"),
            w_values,
            {"units": "m/s"},
        )
    if qr_values is not None:
        data_vars["qr"] = (
            ("time", "z", "y", "x"),
            qr_values,
            {"units": "kg/kg"},
        )
    if rain_values is not None:
        data_vars["rain"] = (
            ("time", "y", "x"),
            rain_values,
            {"units": "mm"},
        )
    if dbz_values is not None:
        data_vars["dbz"] = (
            ("time", "z", "y", "x"),
            dbz_values,
            {"units": "dBZ"},
        )
    if qi_values is not None:
        data_vars["qi"] = (
            ("time", "z", "y", "x"),
            qi_values,
            {"units": "kg/kg"},
        )
    if qs_values is not None:
        data_vars["qs"] = (
            ("time", "z", "y", "x"),
            qs_values,
            {"units": "kg/kg"},
        )
    if qg_values is not None:
        data_vars["qg"] = (
            ("time", "z", "y", "x"),
            qg_values,
            {"units": "kg/kg"},
        )
    if include_time_coord:
        dataset = xr.Dataset(data_vars=data_vars, coords=coords)
    else:
        dataset = xr.Dataset(
            data_vars=data_vars,
            coords={key: value for key, value in coords.items() if key != "time"},
        )
    if z_units is not None:
        dataset["z"].attrs["units"] = z_units
    return dataset


def zeros(z_count: int = 2) -> list[list[list[list[float]]]]:
    return [
        [[[0.0 for _x in range(4)] for _y in range(3)] for _z in range(z_count)]
        for _time in range(2)
    ]


def with_cloud(cloudy_cells: int = 12) -> list[list[list[list[float]]]]:
    values = zeros()
    filled = 0
    for y_index in range(3):
        for x_index in range(4):
            for z_index in range(2):
                if filled < cloudy_cells:
                    values[1][z_index][y_index][x_index] = 2e-6 + filled * 1e-6
                    filled += 1
    return values


def w_field() -> list[list[list[list[float]]]]:
    values = zeros()
    values[0][0][0][0] = -1.5
    values[0][1][2][3] = 2.5
    values[1][0][0][0] = -3.0
    values[1][1][2][3] = 4.0
    return values


def test_cloud_top_uses_ice_and_snow_hydrometeor_envelope(tmp_path: Path) -> None:
    qc_values = zeros(z_count=4)
    qi_values = zeros(z_count=4)
    qs_values = zeros(z_count=4)
    for y_index in range(3):
        for x_index in range(4):
            qc_values[1][1][y_index][x_index] = 2e-6
            qi_values[1][2][y_index][x_index] = 3e-6
            qs_values[1][3][y_index][x_index] = 4e-6
    dataset = write_dataset(
        tmp_path / "deep_cloud.nc",
        base_dataset(
            qc_values=qc_values,
            qi_values=qi_values,
            qs_values=qs_values,
            z_values=[500.0, 1500.0, 7500.0, 10500.0],
        ),
    )
    caveats: list[str] = []

    diagnostics = compute_baseline_diagnostics(dataset, caveats)

    assert diagnostics.cloud.formed is True
    assert diagnostics.cloud.cloud_base_m == 1500.0
    assert diagnostics.cloud.cloud_top_m == 10500.0
    assert [point.value for point in diagnostics.cloud.cloud_top_time_series] == [
        None,
        10500.0,
    ]
    assert diagnostics.cloud.max_qc_kg_kg == 2e-6
    assert "cloud_top_uses_total_hydrometeor_fields:qc,qi,qs" in diagnostics.caveats


def test_no_cloud_case(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "no_cloud.nc", base_dataset(qc_values=zeros(), w_values=w_field())
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.cloud.formed is False
    assert diagnostics.cloud.first_cloud_time_seconds is None
    assert diagnostics.cloud.cloud_present_time_steps == []
    assert diagnostics.cloud.qc_max_time_series[-1].value == 0.0


def test_cloud_formed_requires_ten_grid_cells_and_reports_base_top(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "cloud.nc",
        base_dataset(qc_values=with_cloud(12), w_values=w_field()),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.cloud.formed is True
    assert diagnostics.cloud.first_cloud_time_seconds == 300.0
    assert diagnostics.cloud.cloud_base_m == 500.0
    assert diagnostics.cloud.cloud_top_m == 1500.0
    assert [point.value for point in diagnostics.cloud.cloud_base_time_series] == [None, 500.0]
    assert [point.value for point in diagnostics.cloud.cloud_top_time_series] == [None, 1500.0]
    assert [point.value for point in diagnostics.cloud.max_qc_height_time_series] == [
        500.0,
        1500.0,
    ]
    assert [point.value for point in diagnostics.vertical_velocity.max_w_height_time_series] == [
        1500.0,
        1500.0,
    ]
    assert diagnostics.cloud.cloud_present_time_steps == [300.0]


def test_cloud_base_top_converts_km_vertical_coordinate_to_meters(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "cloud_km.nc",
        base_dataset(
            qc_values=with_cloud(12),
            w_values=w_field(),
            z_values=[0.5, 1.5],
            z_units="km",
        ),
    )
    caveats: list[str] = []

    diagnostics = compute_baseline_diagnostics(dataset, caveats)

    assert diagnostics.cloud.cloud_base_m == 500.0
    assert diagnostics.cloud.cloud_top_m == 1500.0
    assert [point.value for point in diagnostics.cloud.cloud_base_time_series] == [None, 500.0]
    assert [point.value for point in diagnostics.cloud.cloud_top_time_series] == [None, 1500.0]
    assert [point.value for point in diagnostics.cloud.max_qc_height_time_series] == [
        500.0,
        1500.0,
    ]
    assert "cloud_base_top_vertical_units_not_meters:km" not in caveats
    assert "vertical_units_not_meters:km" not in caveats


def test_fewer_than_ten_cloudy_grid_cells_does_not_count_as_cloud_formed(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "thin_cloud.nc",
        base_dataset(qc_values=with_cloud(9), w_values=w_field()),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.cloud.formed is False
    assert diagnostics.cloud.first_cloud_time_seconds is None
    assert diagnostics.cloud.max_qc_kg_kg is not None
    assert diagnostics.cloud.max_qc_kg_kg > 1e-6


def test_qc_max_time_and_cloud_fraction_series(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "qc_summary.nc",
        base_dataset(qc_values=with_cloud(12), w_values=w_field()),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.cloud.max_qc_kg_kg == 1.3e-5
    assert diagnostics.cloud.time_of_max_qc_seconds == 300.0
    assert [point.time_seconds for point in diagnostics.cloud.qc_max_time_series] == [0.0, 300.0]
    assert [point.value for point in diagnostics.cloud.cloud_fraction_time_series] == [0.0, 0.5]


def test_vertical_velocity_summary(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "w_summary.nc",
        base_dataset(qc_values=zeros(), w_values=w_field()),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.vertical_velocity.max_w_m_s == 4.0
    assert diagnostics.vertical_velocity.time_of_max_w_seconds == 300.0
    assert diagnostics.vertical_velocity.min_w_m_s == -3.0
    assert diagnostics.vertical_velocity.time_of_min_w_seconds == 300.0
    assert [point.value for point in diagnostics.vertical_velocity.w_max_time_series] == [2.5, 4.0]
    assert [point.value for point in diagnostics.vertical_velocity.w_min_time_series] == [
        -1.5,
        -3.0,
    ]


def test_qr_rain_present_and_threshold(tmp_path: Path) -> None:
    qr = zeros()
    qr[1][0][0][0] = 2e-7
    dataset = write_dataset(
        tmp_path / "rain.nc",
        base_dataset(qc_values=zeros(), w_values=w_field(), qr_values=qr),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.rain.present is True
    assert diagnostics.rain.first_rain_time_seconds == 300.0
    assert diagnostics.rain.max_qr_kg_kg == 2e-7
    assert diagnostics.rain.time_of_max_qr_seconds == 300.0
    assert diagnostics.rain.user_message == "Rain water aloft detected."
    assert diagnostics.surface_rain.available is False
    assert diagnostics.surface_rain.field_absent is True
    assert diagnostics.reflectivity.available is False
    assert diagnostics.reflectivity.field_absent is True


def test_qr_present_but_no_rain(tmp_path: Path) -> None:
    qr = zeros()
    qr[1][0][0][0] = 5e-8
    dataset = write_dataset(
        tmp_path / "no_rain.nc",
        base_dataset(qc_values=zeros(), w_values=w_field(), qr_values=qr),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.rain.present is False
    assert diagnostics.rain.max_qr_kg_kg == 5e-8
    assert diagnostics.rain.user_message == "No rain water aloft detected."


def test_qr_missing_is_no_rain_without_failure(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "missing_qr.nc",
        base_dataset(qc_values=zeros(), w_values=w_field()),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.rain.present is False
    assert diagnostics.rain.field_absent is True
    assert diagnostics.rain.user_message == "Rain-water field unavailable."
    assert "qr_field_absent" in diagnostics.caveats


def test_surface_rain_and_reflectivity_are_distinct_outputs(tmp_path: Path) -> None:
    rain = [[[0.0 for _x in range(4)] for _y in range(3)] for _time in range(2)]
    rain[1][1][2] = 4.2
    dbz = zeros()
    dbz[0][0][0][0] = -8.0
    dbz[1][1][2][3] = 32.0
    dataset = write_dataset(
        tmp_path / "surface_rain_and_dbz.nc",
        base_dataset(
            qc_values=zeros(),
            w_values=w_field(),
            rain_values=rain,
            dbz_values=dbz,
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.rain.available is False
    assert diagnostics.rain.field_absent is True
    assert diagnostics.surface_rain.available is True
    assert diagnostics.surface_rain.present is True
    assert diagnostics.surface_rain.max_surface_rain == 4.2
    assert diagnostics.surface_rain.time_of_max_surface_rain_seconds == 300.0
    assert diagnostics.surface_rain.units == "mm"
    assert diagnostics.surface_rain.user_message == "Surface rain reached the ground."
    assert diagnostics.reflectivity.available is True
    assert diagnostics.reflectivity.max_dbz == 32.0
    assert diagnostics.reflectivity.time_of_max_dbz_seconds == 300.0
    assert diagnostics.reflectivity.units == "dBZ"


def test_missing_qc_and_missing_w_are_graceful(tmp_path: Path) -> None:
    dataset = write_dataset(tmp_path / "missing.nc", base_dataset())

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.cloud.available is False
    assert diagnostics.vertical_velocity.available is False
    assert "missing_qc_field" in diagnostics.caveats
    assert "missing_w_field" in diagnostics.caveats


def test_non_finite_values_are_ignored_and_recorded(tmp_path: Path) -> None:
    qc = with_cloud(12)
    qc[1][0][0][0] = float("nan")
    w = w_field()
    w[1][0][0][0] = float("inf")
    dataset = write_dataset(
        tmp_path / "non_finite.nc",
        base_dataset(qc_values=qc, w_values=w),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.cloud.max_qc_kg_kg == 1.3e-5
    assert diagnostics.vertical_velocity.max_w_m_s == 4.0
    assert "non_finite_values_detected_in_qc" in diagnostics.caveats
    assert "non_finite_values_detected_in_w" in diagnostics.caveats
    qc_quality = diagnostics.field_quality["qc"]
    w_quality = diagnostics.field_quality["w"]
    assert qc_quality.quality_state == "caveated"
    assert qc_quality.finite_count == 47
    assert qc_quality.non_finite_count == 1
    assert qc_quality.total_count == 48
    assert w_quality.quality_state == "caveated"
    assert w_quality.finite_count == 47
    assert w_quality.non_finite_count == 1
    assert w_quality.total_count == 48


def test_entirely_non_finite_target_field_fails_gracefully(tmp_path: Path) -> None:
    qc = [
        [[[float("nan") for _x in range(4)] for _y in range(3)] for _z in range(2)]
        for _time in range(2)
    ]
    dataset = write_dataset(
        tmp_path / "all_nan.nc",
        base_dataset(qc_values=qc, w_values=w_field()),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.cloud.available is False
    assert diagnostics.cloud.max_qc_kg_kg is None
    assert "qc_field_entirely_non_finite" in diagnostics.caveats
    qc_quality = diagnostics.field_quality["qc"]
    assert qc_quality.quality_state == "untrusted"
    assert qc_quality.reason == "qc_field_entirely_non_finite"
    assert qc_quality.finite_count == 0
    assert qc_quality.non_finite_count == 48
    assert qc_quality.total_count == 48


def test_field_quality_marks_all_non_finite_core_result_fields_untrusted(
    tmp_path: Path,
) -> None:
    all_nan_field = [
        [[[float("nan") for _x in range(4)] for _y in range(3)] for _z in range(2)]
        for _time in range(2)
    ]
    all_nan_surface = [[[float("nan") for _x in range(4)] for _y in range(3)] for _time in range(2)]
    dataset = write_dataset(
        tmp_path / "all_core_fields_nan.nc",
        base_dataset(
            qc_values=all_nan_field,
            w_values=all_nan_field,
            qr_values=all_nan_field,
            rain_values=all_nan_surface,
            dbz_values=all_nan_field,
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    expected_totals = {
        "qc": 48,
        "w": 48,
        "qr": 48,
        "surface_rain": 24,
        "dbz": 48,
    }
    for field, total in expected_totals.items():
        quality = diagnostics.field_quality[field]
        assert quality.quality_state == "untrusted"
        assert quality.finite_count == 0
        assert quality.non_finite_count == total
        assert quality.total_count == total
    assert diagnostics.cloud.available is False
    assert diagnostics.vertical_velocity.available is False
    assert diagnostics.rain.available is False
    assert diagnostics.surface_rain.available is False
    assert diagnostics.reflectivity.available is False


def test_netcdf_time_coordinate_and_inferred_fallback(tmp_path: Path) -> None:
    with_time = write_dataset(
        tmp_path / "with_time.nc",
        base_dataset(qc_values=with_cloud(12), w_values=w_field(), include_time_coord=True),
    )
    without_time = write_dataset(
        tmp_path / "without_time.nc",
        base_dataset(qc_values=with_cloud(12), w_values=w_field(), include_time_coord=False),
    )

    direct = compute_baseline_diagnostics(with_time, [])
    inferred = compute_baseline_diagnostics(without_time, [])

    assert direct.time.source == "netcdf_time_coordinate"
    assert direct.time.fallback_used is False
    assert inferred.time.source == "inferred_output_index"
    assert inferred.time.fallback_used is True
    assert inferred.cloud.first_cloud_time_seconds == 1.0


def test_process_diagnostics_label_moisture_limited_thermal_without_cloud(
    tmp_path: Path,
) -> None:
    dataset = write_dataset(
        tmp_path / "dry_thermal.nc",
        base_dataset(qc_values=zeros(), w_values=w_field()),
    )
    diagnostics = compute_baseline_diagnostics(dataset, [])

    process = compute_process_diagnostics(
        diagnostics,
        scenario_id="dry-failed-cumulus",
        controls={"low_level_humidity": "drier"},
        variables=["qc", "w"],
    )

    assert process.interpretation_support.thermal_fate_label == "Thermal without cloud"
    assert process.interpretation_support.confidence == "supported"
    assert process.interpretation_support.main_limiting_factor == "moisture"
    assert "moisture_limitation_inferred_without_saturation_deficit" in (
        process.interpretation_support.caveats
    )
    assert process.deep_breakthrough.status == "unsupported_missing_fields"
    assert process.precipitation_feedback.status == "unsupported_missing_fields"


def test_process_diagnostics_marks_capped_result_as_candidate(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "capped.nc",
        base_dataset(qc_values=with_cloud(12), w_values=w_field()),
    )
    diagnostics = compute_baseline_diagnostics(dataset, [])

    process = compute_process_diagnostics(
        diagnostics,
        scenario_id="capped-suppressed-cumulus",
        controls={"cap_strength": "stronger"},
        variables=["qc", "w"],
    )

    assert process.interpretation_support.thermal_fate_label == "Capped / suppressed cumulus"
    assert process.interpretation_support.confidence == "candidate"
    assert process.interpretation_support.main_limiting_factor == "cap/stability"
    assert process.cap_inversion.status == "candidate"
    assert "cap_limitation_candidate_requires_baseline_comparison" in (
        process.interpretation_support.caveats
    )


def test_process_diagnostics_handles_missing_required_fields(tmp_path: Path) -> None:
    dataset = write_dataset(tmp_path / "missing.nc", base_dataset())
    diagnostics = compute_baseline_diagnostics(dataset, [])

    process = compute_process_diagnostics(
        diagnostics,
        scenario_id="baseline-shallow-cumulus",
        controls={},
        variables=[],
    )

    assert process.interpretation_support.thermal_fate_label == "Insufficient evidence"
    assert process.interpretation_support.confidence == "unsupported_missing_fields"
    assert process.thermal_fate.status == "unsupported_missing_fields"
    assert process.cloud_lifecycle.status == "unsupported_missing_fields"
    assert process.updrafts.status == "unsupported_missing_fields"


def test_process_diagnostics_marks_growing_cumulus_candidate(tmp_path: Path) -> None:
    qc = zeros()
    for y_index in range(3):
        for x_index in range(4):
            qc[0][0][y_index][x_index] = 2e-6
            qc[1][1][y_index][x_index] = 4e-6
    dataset = write_dataset(
        tmp_path / "growing.nc",
        base_dataset(qc_values=qc, w_values=w_field()),
    )
    diagnostics = compute_baseline_diagnostics(dataset, [])

    process = compute_process_diagnostics(
        diagnostics,
        scenario_id="baseline-shallow-cumulus",
        controls={},
        variables=["qc", "w"],
    )

    assert process.interpretation_support.thermal_fate_label == "Growing cumulus"
    assert process.interpretation_support.confidence == "candidate"
