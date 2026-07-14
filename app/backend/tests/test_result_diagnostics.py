from pathlib import Path
from typing import Any

import pytest
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
    hfx_values: list[list[list[float]]] | None = None,
    qfx_values: list[list[list[float]]] | None = None,
    qv_values: list[list[list[list[float]]]] | None = None,
    th_values: list[list[list[list[float]]]] | None = None,
    temperature_values: list[list[list[list[float]]]] | None = None,
    qi_values: list[list[list[list[float]]]] | None = None,
    qs_values: list[list[list[list[float]]]] | None = None,
    qg_values: list[list[list[list[float]]]] | None = None,
    include_time_coord: bool = True,
    time_values: list[float] | None = None,
    z_values: list[float] | None = None,
    z_units: str | None = None,
) -> xr.Dataset:
    coords: dict[str, list[float]] = {
        "z": z_values or [500.0, 1500.0],
        "y": [0.0, 200.0, 400.0],
        "x": [0.0, 200.0, 400.0, 600.0],
    }
    if include_time_coord:
        coords["time"] = time_values or [0.0, 300.0]
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
    if hfx_values is not None:
        data_vars["hfx"] = (
            ("time", "y", "x"),
            hfx_values,
            {"units": "K m/s"},
        )
    if qfx_values is not None:
        data_vars["qfx"] = (
            ("time", "y", "x"),
            qfx_values,
            {"units": "kg/m^2/s"},
        )
    if qv_values is not None:
        data_vars["qv"] = (
            ("time", "z", "y", "x"),
            qv_values,
            {"units": "kg/kg"},
        )
    if th_values is not None:
        data_vars["th"] = (
            ("time", "z", "y", "x"),
            th_values,
            {"units": "K"},
        )
    if temperature_values is not None:
        data_vars["temperature"] = (
            ("time", "z", "y", "x"),
            temperature_values,
            {"units": "K"},
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


def zeros(time_count: int = 2, z_count: int = 2) -> list[list[list[list[float]]]]:
    return [
        [[[0.0 for _x in range(4)] for _y in range(3)] for _z in range(z_count)]
        for _time in range(time_count)
    ]


def surface_values(start: float = 0.0, step: float = 1.0) -> list[list[list[float]]]:
    value = start
    values = []
    for _time in range(2):
        time_values = []
        for _y in range(3):
            row = []
            for _x in range(4):
                row.append(value)
                value += step
            time_values.append(row)
        values.append(time_values)
    return values


def constant_surface_frames(frame_values: list[float]) -> list[list[list[float]]]:
    return [[[value for _x in range(4)] for _y in range(3)] for value in frame_values]


def entirely_non_finite_surface_frame() -> list[list[float]]:
    return [[float("nan") for _x in range(4)] for _y in range(3)]


def time_z_values(values_by_time_z: list[list[float]]) -> list[list[list[list[float]]]]:
    return [
        [[[value for _x in range(4)] for _y in range(3)] for value in time_values]
        for time_values in values_by_time_z
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


def w_field(time_count: int = 2, z_count: int = 2) -> list[list[list[list[float]]]]:
    values = zeros(time_count=time_count, z_count=z_count)
    values[0][0][0][0] = -1.5
    values[0][min(1, z_count - 1)][2][3] = 2.5
    values[1][0][0][0] = -3.0
    values[1][min(1, z_count - 1)][2][3] = 4.0
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

    assert diagnostics.field_quality_assessed is True
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


def test_surface_flux_statistics_preserve_units_and_counts(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "surface_fluxes.nc",
        base_dataset(
            qc_values=zeros(),
            w_values=w_field(),
            hfx_values=surface_values(start=1.0, step=1.0),
            qfx_values=surface_values(start=0.0, step=0.5),
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    hfx = diagnostics.surface_fluxes.hfx
    qfx = diagnostics.surface_fluxes.qfx
    assert hfx.available is True
    assert hfx.field_absent is False
    assert hfx.units == "K m/s"
    assert hfx.min_value == pytest.approx(1.0)
    assert hfx.max_value == pytest.approx(24.0)
    assert hfx.mean_value == pytest.approx(12.5)
    assert hfx.finite_count == 24
    assert hfx.non_finite_count == 0
    assert hfx.total_count == 24
    assert diagnostics.field_quality["hfx"].quality_state == "trusted"
    assert diagnostics.field_quality["hfx"].source_field == "hfx"

    assert qfx.available is True
    assert qfx.field_absent is False
    assert qfx.units == "kg/m^2/s"
    assert qfx.min_value == pytest.approx(0.0)
    assert qfx.max_value == pytest.approx(11.5)
    assert qfx.mean_value == pytest.approx(5.75)
    assert qfx.finite_count == 24
    assert qfx.non_finite_count == 0
    assert qfx.total_count == 24
    assert diagnostics.field_quality["qfx"].quality_state == "trusted"
    assert diagnostics.field_quality["qfx"].source_field == "qfx"


def test_surface_flux_statistics_report_missing_fields_without_global_caveats(
    tmp_path: Path,
) -> None:
    dataset = write_dataset(
        tmp_path / "surface_fluxes_missing.nc",
        base_dataset(qc_values=zeros(), w_values=w_field()),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.surface_fluxes.hfx.available is False
    assert diagnostics.surface_fluxes.hfx.field_absent is True
    assert diagnostics.surface_fluxes.hfx.caveats == ["hfx_field_absent"]
    assert diagnostics.surface_fluxes.qfx.available is False
    assert diagnostics.surface_fluxes.qfx.field_absent is True
    assert diagnostics.surface_fluxes.qfx.caveats == ["qfx_field_absent"]
    assert diagnostics.field_quality["hfx"].quality_state == "unavailable"
    assert diagnostics.field_quality["qfx"].quality_state == "unavailable"
    assert "hfx_field_absent" not in diagnostics.caveats
    assert "qfx_field_absent" not in diagnostics.caveats


def test_surface_flux_statistics_caveat_partially_non_finite_fields(
    tmp_path: Path,
) -> None:
    hfx = surface_values(start=1.0, step=1.0)
    hfx[0][0][0] = float("nan")
    qfx = surface_values(start=0.0, step=0.5)
    qfx[1][2][3] = float("inf")
    dataset = write_dataset(
        tmp_path / "surface_fluxes_partially_non_finite.nc",
        base_dataset(qc_values=zeros(), w_values=w_field(), hfx_values=hfx, qfx_values=qfx),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.surface_fluxes.hfx.available is True
    assert diagnostics.surface_fluxes.hfx.min_value == pytest.approx(2.0)
    assert diagnostics.surface_fluxes.hfx.max_value == pytest.approx(24.0)
    assert diagnostics.surface_fluxes.hfx.finite_count == 23
    assert diagnostics.surface_fluxes.hfx.non_finite_count == 1
    hfx_frame_quality = diagnostics.surface_fluxes.hfx.frame_quality
    assert hfx_frame_quality is not None
    assert hfx_frame_quality.affected_frame_indices == [0]
    assert hfx_frame_quality.partially_non_finite_frame_count == 1
    assert hfx_frame_quality.entirely_non_finite_frame_count == 0
    assert diagnostics.field_quality["hfx"].quality_state == "caveated"
    assert "non_finite_values_detected_in_hfx" in diagnostics.caveats

    assert diagnostics.surface_fluxes.qfx.available is True
    assert diagnostics.surface_fluxes.qfx.min_value == pytest.approx(0.0)
    assert diagnostics.surface_fluxes.qfx.max_value == pytest.approx(11.0)
    assert diagnostics.surface_fluxes.qfx.finite_count == 23
    assert diagnostics.surface_fluxes.qfx.non_finite_count == 1
    assert diagnostics.field_quality["qfx"].quality_state == "caveated"
    assert "non_finite_values_detected_in_qfx" in diagnostics.caveats


@pytest.mark.parametrize(
    ("bad_index", "expected_reason", "expected_state", "initial", "terminal"),
    [
        (0, "hfx_initial_output_frame_entirely_non_finite", "caveated", True, False),
        (
            1,
            "hfx_intermediate_output_frame_entirely_non_finite",
            "caveated",
            False,
            False,
        ),
        (2, "hfx_terminal_output_frame_entirely_non_finite", "untrusted", False, True),
    ],
)
def test_surface_flux_quality_identifies_entirely_non_finite_frame_position(
    tmp_path: Path,
    bad_index: int,
    expected_reason: str,
    expected_state: str,
    initial: bool,
    terminal: bool,
) -> None:
    hfx = constant_surface_frames([1.0, 2.0, 3.0])
    hfx[bad_index] = entirely_non_finite_surface_frame()
    dataset = write_dataset(
        tmp_path / f"surface_flux_bad_frame_{bad_index}.nc",
        base_dataset(
            qc_values=zeros(time_count=3),
            w_values=w_field(time_count=3),
            hfx_values=hfx,
            qfx_values=constant_surface_frames([1.0e-5, 2.0e-5, 3.0e-5]),
            time_values=[0.0, 3600.0, 21600.0],
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    hfx_stats = diagnostics.surface_fluxes.hfx
    assert hfx_stats.available is True
    assert hfx_stats.finite_count == 24
    assert hfx_stats.non_finite_count == 12
    assert hfx_stats.frame_quality is not None
    assert hfx_stats.frame_quality.affected_frame_indices == [bad_index]
    assert hfx_stats.frame_quality.affected_frame_times_seconds == [
        [0.0, 3600.0, 21600.0][bad_index]
    ]
    assert hfx_stats.frame_quality.initial_frame_affected is initial
    assert hfx_stats.frame_quality.terminal_frame_affected is terminal
    assert hfx_stats.frame_quality.entirely_non_finite_frame_count == 1
    hfx_quality = diagnostics.field_quality["hfx"]
    assert hfx_quality.quality_state == expected_state
    assert hfx_quality.reason == expected_reason
    assert expected_reason in hfx_quality.caveats


def test_surface_flux_quality_records_multiple_entirely_non_finite_frames(
    tmp_path: Path,
) -> None:
    hfx = constant_surface_frames([1.0, 2.0, 3.0, 4.0])
    hfx[0] = entirely_non_finite_surface_frame()
    hfx[3] = entirely_non_finite_surface_frame()
    dataset = write_dataset(
        tmp_path / "surface_flux_multiple_bad_frames.nc",
        base_dataset(
            qc_values=zeros(time_count=4),
            w_values=w_field(time_count=4),
            hfx_values=hfx,
            time_values=[0.0, 3600.0, 7200.0, 21600.0],
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    hfx_quality = diagnostics.field_quality["hfx"]
    assert hfx_quality.quality_state == "untrusted"
    assert hfx_quality.reason == "hfx_terminal_output_frame_entirely_non_finite"
    assert hfx_quality.frame_quality is not None
    assert hfx_quality.frame_quality.affected_frame_indices == [0, 3]
    assert hfx_quality.frame_quality.initial_frame_affected is True
    assert hfx_quality.frame_quality.terminal_frame_affected is True
    assert hfx_quality.frame_quality.finite_frame_count == 2


def test_surface_flux_statistics_mark_all_non_finite_fields_unavailable(
    tmp_path: Path,
) -> None:
    all_nan_surface = [entirely_non_finite_surface_frame() for _time in range(2)]
    dataset = write_dataset(
        tmp_path / "surface_fluxes_all_nan.nc",
        base_dataset(
            qc_values=zeros(),
            w_values=w_field(),
            hfx_values=all_nan_surface,
            qfx_values=all_nan_surface,
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.surface_fluxes.hfx.available is False
    assert diagnostics.surface_fluxes.hfx.field_absent is False
    assert diagnostics.surface_fluxes.hfx.finite_count == 0
    assert diagnostics.surface_fluxes.hfx.non_finite_count == 24
    assert diagnostics.surface_fluxes.hfx.total_count == 24
    assert diagnostics.field_quality["hfx"].quality_state == "untrusted"
    assert diagnostics.field_quality["hfx"].reason == "hfx_field_entirely_non_finite"
    assert diagnostics.field_quality["hfx"].frame_quality is not None
    assert diagnostics.field_quality["hfx"].frame_quality.affected_frame_indices == [0, 1]
    assert "hfx_field_entirely_non_finite" in diagnostics.caveats

    assert diagnostics.surface_fluxes.qfx.available is False
    assert diagnostics.surface_fluxes.qfx.field_absent is False
    assert diagnostics.surface_fluxes.qfx.finite_count == 0
    assert diagnostics.surface_fluxes.qfx.non_finite_count == 24
    assert diagnostics.surface_fluxes.qfx.total_count == 24
    assert diagnostics.field_quality["qfx"].quality_state == "untrusted"
    assert "qfx_field_entirely_non_finite" in diagnostics.caveats


def test_low_level_response_computes_weighted_early_and_full_run_deltas(
    tmp_path: Path,
) -> None:
    dataset = write_dataset(
        tmp_path / "low_level_response.nc",
        base_dataset(
            qc_values=zeros(time_count=3, z_count=3),
            w_values=w_field(time_count=3, z_count=3),
            qv_values=time_z_values(
                [
                    [0.010, 0.012, 0.020],
                    [0.011, 0.014, 0.028],
                    [0.012, 0.013, 0.030],
                ]
            ),
            th_values=time_z_values(
                [
                    [300.0, 310.0, 330.0],
                    [302.0, 313.0, 336.0],
                    [303.0, 312.0, 340.0],
                ]
            ),
            time_values=[0.0, 3600.0, 21600.0],
            z_values=[50.0, 250.0, 900.0],
            z_units="m",
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    qv = diagnostics.low_level_response.qv
    thermal = diagnostics.low_level_response.theta_or_temperature
    assert qv.available is True
    assert qv.early_response_available is True
    assert qv.full_run_response_available is True
    assert qv.source_field == "qv"
    assert qv.vertical_coordinate_name == "z"
    assert qv.vertical_coordinate_units == "m"
    assert qv.vertical_coordinate_method == ("0_1km_thickness_weighted_domain_mean_early_30_90min")
    assert qv.first_time_seconds == 0.0
    assert qv.final_time_seconds == 21600.0
    assert qv.early_response_start_time_seconds == 0.0
    assert qv.early_response_end_time_seconds == 3600.0
    assert qv.first_mean_value == pytest.approx(0.0151)
    assert qv.early_response_end_mean_value == pytest.approx(0.0195)
    assert qv.final_mean_value == pytest.approx(0.020075)
    assert qv.delta_value == pytest.approx(0.0044)
    assert qv.early_response_delta == pytest.approx(0.0044)
    assert qv.full_run_delta == pytest.approx(0.004975)
    assert qv.units == "kg/kg"
    assert qv.first_finite_count == 36
    assert qv.early_response_end_finite_count == 36
    assert qv.final_finite_count == 36

    assert thermal.available is True
    assert thermal.early_response_available is True
    assert thermal.full_run_response_available is True
    assert thermal.source_field == "th"
    assert thermal.first_mean_value == pytest.approx(317.0)
    assert thermal.early_response_end_mean_value == pytest.approx(321.125)
    assert thermal.final_mean_value == pytest.approx(322.55)
    assert thermal.delta_value == pytest.approx(4.125)
    assert thermal.early_response_delta == pytest.approx(4.125)
    assert thermal.full_run_delta == pytest.approx(5.55)
    assert thermal.units == "K"


def test_low_level_response_keeps_early_when_final_endpoint_non_finite(
    tmp_path: Path,
) -> None:
    qv_values = time_z_values(
        [
            [0.010, 0.012],
            [0.014, 0.018],
            [float("nan"), float("nan")],
        ]
    )
    dataset = write_dataset(
        tmp_path / "low_level_response_bad_final.nc",
        base_dataset(
            qc_values=zeros(time_count=3),
            w_values=w_field(time_count=3),
            qv_values=qv_values,
            th_values=time_z_values(
                [
                    [299.0, 301.0],
                    [302.0, 306.0],
                    [float("nan"), float("nan")],
                ]
            ),
            time_values=[0.0, 3600.0, 21600.0],
            z_values=[250.0, 750.0],
            z_units="m",
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    qv = diagnostics.low_level_response.qv
    assert qv.available is True
    assert qv.early_response_available is True
    assert qv.full_run_response_available is False
    assert qv.early_response_delta == pytest.approx(0.005)
    assert qv.full_run_delta is None
    assert qv.final_finite_count == 0
    assert "qv_low_level_response_final_endpoint_entirely_non_finite" in qv.caveats


def test_low_level_response_keeps_early_when_no_distinct_final_endpoint(
    tmp_path: Path,
) -> None:
    dataset = write_dataset(
        tmp_path / "low_level_response_no_distinct_final.nc",
        base_dataset(
            qc_values=zeros(),
            w_values=w_field(),
            qv_values=time_z_values([[0.010, 0.012], [0.014, 0.018]]),
            th_values=time_z_values([[299.0, 301.0], [302.0, 306.0]]),
            time_values=[0.0, 3600.0],
            z_values=[250.0, 750.0],
            z_units="m",
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    qv = diagnostics.low_level_response.qv
    assert qv.available is True
    assert qv.early_response_available is True
    assert qv.full_run_response_available is False
    assert qv.early_response_delta == pytest.approx(0.005)
    assert qv.full_run_delta is None


def test_low_level_response_reports_full_run_when_early_endpoint_missing(
    tmp_path: Path,
) -> None:
    dataset = write_dataset(
        tmp_path / "low_level_response_missing_early.nc",
        base_dataset(
            qc_values=zeros(),
            w_values=w_field(),
            qv_values=time_z_values([[0.010, 0.012], [0.020, 0.024]]),
            th_values=time_z_values([[299.0, 301.0], [306.0, 310.0]]),
            time_values=[0.0, 21600.0],
            z_values=[250.0, 750.0],
            z_units="m",
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    qv = diagnostics.low_level_response.qv
    assert qv.available is False
    assert qv.early_response_available is False
    assert qv.full_run_response_available is True
    assert qv.early_response_delta is None
    assert qv.full_run_delta == pytest.approx(0.011)
    assert "qv_low_level_response_missing_early_output_30_90min" in qv.caveats


def test_low_level_response_marks_missing_fields_unavailable(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "low_level_response_missing.nc",
        base_dataset(qc_values=zeros(), w_values=w_field()),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.low_level_response.qv.available is False
    assert diagnostics.low_level_response.qv.field_absent is True
    assert diagnostics.low_level_response.qv.caveats == ["qv_field_absent"]
    thermal = diagnostics.low_level_response.theta_or_temperature
    assert thermal.available is False
    assert thermal.field_absent is True
    assert thermal.caveats == ["theta_or_temperature_field_absent"]


def test_low_level_response_requires_vertical_coordinate(tmp_path: Path) -> None:
    dataset = xr.Dataset(
        data_vars={
            "qv": (
                ("time", "z", "y", "x"),
                time_z_values([[0.010, 0.012], [0.014, 0.018]]),
                {"units": "kg/kg"},
            ),
            "th": (
                ("time", "z", "y", "x"),
                time_z_values([[299.0, 301.0], [302.0, 306.0]]),
                {"units": "K"},
            ),
            "qc": (("time", "z", "y", "x"), zeros(), {"units": "kg/kg"}),
            "w": (("time", "z", "y", "x"), w_field(), {"units": "m/s"}),
        },
        coords={
            "time": [0.0, 300.0],
            "y": [0.0, 200.0, 400.0],
            "x": [0.0, 200.0, 400.0, 600.0],
        },
    )
    dataset = write_dataset(tmp_path / "low_level_response_missing_z_coord.nc", dataset)

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.low_level_response.qv.available is False
    assert diagnostics.low_level_response.qv.caveats == [
        "qv_low_level_response_missing_vertical_coordinate"
    ]
    assert "qv_low_level_response_missing_vertical_coordinate" in diagnostics.caveats


def test_low_level_response_caveats_partially_non_finite_endpoints(tmp_path: Path) -> None:
    qv_values = time_z_values([[0.010, 0.012], [0.014, 0.018]])
    qv_values[1][0][0][0] = float("nan")
    dataset = write_dataset(
        tmp_path / "low_level_response_partially_nan.nc",
        base_dataset(
            qc_values=zeros(),
            w_values=w_field(),
            qv_values=qv_values,
            temperature_values=time_z_values([[289.0, 291.0], [292.0, 296.0]]),
            time_values=[0.0, 3600.0],
            z_values=[250.0, 750.0],
            z_units="m",
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    qv = diagnostics.low_level_response.qv
    assert qv.available is True
    assert qv.final_finite_count == 23
    assert qv.final_non_finite_count == 1
    assert qv.delta_value == pytest.approx(((0.014 * 11 + 0.018 * 12) / 23) - 0.011)
    assert qv.early_response_available is True
    assert qv.full_run_response_available is False
    assert qv.full_run_delta is None
    assert "non_finite_values_detected_in_qv_low_level_response" in diagnostics.caveats
    assert diagnostics.low_level_response.theta_or_temperature.source_field == "temperature"


def test_low_level_response_does_not_use_theta_v_for_heat_gate(tmp_path: Path) -> None:
    dataset = write_dataset(
        tmp_path / "low_level_response_theta_v_only.nc",
        xr.Dataset(
            data_vars={
                "qv": (
                    ("time", "z", "y", "x"),
                    time_z_values([[0.010, 0.012], [0.014, 0.018]]),
                    {"units": "kg/kg"},
                ),
                "theta_v": (
                    ("time", "z", "y", "x"),
                    time_z_values([[299.0, 301.0], [302.0, 306.0]]),
                    {"units": "K"},
                ),
                "qc": (("time", "z", "y", "x"), zeros(), {"units": "kg/kg"}),
                "w": (("time", "z", "y", "x"), w_field(), {"units": "m/s"}),
            },
            coords={
                "time": [0.0, 3600.0],
                "z": [250.0, 750.0],
                "y": [0.0, 200.0, 400.0],
                "x": [0.0, 200.0, 400.0, 600.0],
            },
        ),
    )

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.low_level_response.qv.available is True
    thermal = diagnostics.low_level_response.theta_or_temperature
    assert thermal.available is False
    assert thermal.source_field is None
    assert thermal.field_absent is True
    assert thermal.caveats == ["theta_or_temperature_field_absent"]


def test_missing_qc_and_missing_w_are_graceful(tmp_path: Path) -> None:
    dataset = write_dataset(tmp_path / "missing.nc", base_dataset())

    diagnostics = compute_baseline_diagnostics(dataset, [])

    assert diagnostics.field_quality_assessed is True
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

    assert diagnostics.field_quality_assessed is True
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
