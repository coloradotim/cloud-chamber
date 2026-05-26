from pathlib import Path

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
    include_time_coord: bool = True,
) -> xr.Dataset:
    coords: dict[str, list[float]] = {
        "z": [500.0, 1500.0],
        "y": [0.0, 200.0, 400.0],
        "x": [0.0, 200.0, 400.0, 600.0],
    }
    if include_time_coord:
        coords["time"] = [0.0, 300.0]
    else:
        coords["time"] = []
    data_vars = {}
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
    if include_time_coord:
        return xr.Dataset(data_vars=data_vars, coords=coords)
    return xr.Dataset(
        data_vars=data_vars,
        coords={key: value for key, value in coords.items() if key != "time"},
    )


def zeros() -> list[list[list[list[float]]]]:
    return [
        [[[0.0 for _x in range(4)] for _y in range(3)] for _z in range(2)] for _time in range(2)
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
    assert diagnostics.rain.user_message == "Rain detected."


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
    assert diagnostics.rain.user_message == "No rain detected."


def test_qr_missing_is_no_rain_without_failure(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "missing_qr.nc",
        base_dataset(qc_values=zeros(), w_values=w_field()),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.rain.present is False
    assert diagnostics.rain.field_absent is True
    assert diagnostics.rain.user_message == "No rain detected."
    assert "qr_field_absent" in diagnostics.caveats


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
