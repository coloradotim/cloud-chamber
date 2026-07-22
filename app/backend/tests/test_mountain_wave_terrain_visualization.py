from pathlib import Path
from typing import Any

import numpy as np
import pytest
import xarray as xr

from cloud_chamber.mountain_wave_case import EXPECTED_OUTPUT_TIMES_SECONDS
from cloud_chamber.mountain_wave_terrain_visualization import (
    MountainWaveTerrainVisualizationError,
    clear_mountain_waves_run_metadata_cache,
    local_agl_m,
    mountain_waves_frame_from_native_outputs,
    terrain_frame_from_native_outputs,
    validate_mountain_waves_native_outputs,
)


def test_native_w_payload_preserves_curved_terrain_and_full_level_placement(
    tmp_path: Path,
) -> None:
    paths, namelist = _write_native_histories(tmp_path)

    frame = terrain_frame_from_native_outputs(
        output_paths=paths,
        namelist_path=namelist,
        field="w",
        time_index=10,
    )

    assert frame.times_seconds == list(EXPECTED_OUTPUT_TIMES_SECONDS)
    assert frame.time_seconds == 2160
    assert frame.singleton_y is True
    assert frame.geometry.singleton_y_m == pytest.approx(0.0)
    assert frame.geometry.terrain_m == pytest.approx([0.0, 400.0, 100.0])
    assert frame.geometry.full_height_m[0] == pytest.approx(frame.geometry.terrain_m)
    assert frame.geometry.full_height_m[-1] == pytest.approx([20_000.0] * 3)
    assert frame.geometry.horizontal_units == "m"
    assert frame.geometry.vertical_units == "m"
    assert np.min(np.asarray(frame.geometry.full_height_m) - frame.geometry.terrain_m) >= 0.0
    assert frame.active_top_evidence.final_nominal_zf_m == pytest.approx(20_000.0)
    assert frame.active_top_evidence.runtime_ztop_m == pytest.approx(20_000.0)
    assert frame.active_top_evidence.nz_times_dz_m == pytest.approx(20_000.0)
    assert frame.active_top_evidence.all_sources_agree is True
    assert frame.vertical_references.model_height_is_msl is False
    assert frame.field.native_dimensions == ["zf", "yh", "xh"]
    assert frame.field.vertical_grid == "physical_full_levels"
    assert len(frame.values) == 3
    assert len(frame.values[0]) == 3
    assert frame.scale.fixed_across_all_times is True
    assert frame.scale.minimum == pytest.approx(-frame.scale.maximum)
    assert frame.provenance.interpolation == "none"
    assert frame.provenance.masked_below_terrain is True


def test_theta_perturbation_uses_native_scalar_cells_and_t0_reference(tmp_path: Path) -> None:
    paths, namelist = _write_native_histories(tmp_path)

    frame = terrain_frame_from_native_outputs(
        output_paths=paths,
        namelist_path=namelist,
        field="theta_perturbation",
        time_index=2,
    )

    assert frame.field.units == "K"
    assert frame.field.native_dimensions == ["zh", "yh", "xh"]
    assert frame.field.vertical_grid == "physical_scalar_levels"
    assert np.asarray(frame.values) == pytest.approx(np.full((2, 3), 0.5))
    assert frame.provenance.reference_history_file == "cm1out_000001.nc"
    assert len(frame.geometry.scalar_height_m) == 2
    assert np.all(
        np.asarray(frame.geometry.scalar_height_m) > np.asarray(frame.geometry.terrain_m)[None, :]
    )


def test_active_top_mismatch_fails_closed(tmp_path: Path) -> None:
    paths, namelist = _write_native_histories(tmp_path, runtime_top_m=19_000.0)

    with pytest.raises(
        MountainWaveTerrainVisualizationError, match="Active-top evidence disagrees"
    ):
        terrain_frame_from_native_outputs(
            output_paths=paths,
            namelist_path=namelist,
            field="w",
            time_index=0,
        )


def test_missing_physical_height_semantics_fail_closed(tmp_path: Path) -> None:
    paths, namelist = _write_native_histories(tmp_path, include_zhval=False)

    with pytest.raises(MountainWaveTerrainVisualizationError, match="zhval"):
        terrain_frame_from_native_outputs(
            output_paths=paths,
            namelist_path=namelist,
            field="w",
            time_index=0,
        )


def test_exact_output_time_sequence_is_required(tmp_path: Path) -> None:
    paths, namelist = _write_native_histories(tmp_path, time_offset_seconds=1)

    with pytest.raises(MountainWaveTerrainVisualizationError, match="exact sequence"):
        terrain_frame_from_native_outputs(
            output_paths=paths,
            namelist_path=namelist,
            field="w",
            time_index=0,
        )


def test_local_agl_uses_local_terrain_and_rejects_below_ground() -> None:
    assert local_agl_m(model_height_m=1_250.0, terrain_height_m=400.0) == pytest.approx(850.0)
    with pytest.raises(MountainWaveTerrainVisualizationError, match="below local terrain"):
        local_agl_m(model_height_m=399.0, terrain_height_m=400.0)


@pytest.mark.parametrize(
    "field, expected_units",
    [
        ("cloud_over_wave", "m/s"),
        ("w", "m/s"),
        ("cloud_liquid", "g/kg"),
        ("relative_humidity", "%"),
        ("theta_perturbation", "K"),
    ],
)
def test_mountain_waves_moist_fields_share_native_geometry_and_fixed_time_scale(
    tmp_path: Path, field: str, expected_units: str
) -> None:
    paths, namelist = _write_world_histories(tmp_path, moist=True)

    frame = mountain_waves_frame_from_native_outputs(
        output_paths=paths,
        namelist_path=namelist,
        field=field,  # type: ignore[arg-type]
        time_index=1,
        run_id="moist-test",
        case_label="Moist test",
        implementation_commit="test-commit",
        dry_case=False,
        caveats=[],
    )

    assert frame.schema_version == "mountain_waves_explore_v1"
    assert frame.times_seconds == [0, 200, 400]
    assert frame.time_seconds == 200
    assert frame.field.units == expected_units
    assert frame.field.vertical_grid == "physical_scalar_levels"
    assert frame.scale.fixed_across_all_times is True
    assert frame.active_top_evidence.inactive_namelist_ztop_m == pytest.approx(19_000.0)
    assert frame.active_top_evidence.all_sources_agree is True
    assert frame.pointer_context is not None
    assert frame.pointer_context.horizontal_wind_m_s[0][0] == pytest.approx(11.0)
    assert frame.pointer_context.potential_temperature_k[0][0] == pytest.approx(285.2)
    assert frame.pointer_context.cloud_liquid_g_kg is not None
    assert frame.pointer_context.relative_humidity_percent is not None
    assert frame.viewport is not None
    assert frame.viewport.default_mode == "focus"
    assert frame.viewport.focus_available is True
    assert frame.viewport.focus.x_minimum_m == pytest.approx(-30_000.0)
    assert frame.viewport.focus.x_maximum_m == pytest.approx(50_000.0)
    assert frame.viewport.focus.z_maximum_m == pytest.approx(12_000.0)
    assert frame.lens is not None
    assert frame.lens.horizontal_wind_reference_m_s == pytest.approx(40.0)
    assert frame.lens.vertical_velocity_neutral_threshold_m_s == pytest.approx(0.1)
    assert frame.lens.potential_temperature_contour_interval_k == pytest.approx(10.0)
    assert frame.lens.potential_temperature_contour_values_k == [290.0]
    if field in {"cloud_over_wave", "w", "theta_perturbation"}:
        assert frame.scale.minimum == pytest.approx(-frame.scale.maximum)
        assert len(frame.scale.breakpoints) == 10
        assert len(frame.scale.colors) == 11
    if field == "cloud_over_wave":
        assert frame.overlay is not None
        assert frame.overlay.units == "g/kg"
        assert frame.overlay.threshold == pytest.approx(0.001)
        assert frame.overlay.maximum > frame.overlay.threshold
    else:
        assert frame.overlay is None


def test_mountain_waves_dry_frame_rejects_moist_fields(tmp_path: Path) -> None:
    paths, namelist = _write_world_histories(tmp_path, moist=False)

    frame = mountain_waves_frame_from_native_outputs(
        output_paths=paths,
        namelist_path=namelist,
        field="theta_perturbation",
        time_index=2,
        run_id="dry-test",
        case_label="Dry test",
        implementation_commit="test-commit",
        dry_case=True,
        caveats=["Dry."],
    )
    assert frame.dry_case is True
    assert frame.field_options == ["w", "theta_perturbation"]
    assert frame.pointer_context is not None
    assert frame.pointer_context.horizontal_wind_m_s[1][2] == pytest.approx(37.0)
    assert frame.pointer_context.potential_temperature_k[0][0] == pytest.approx(285.4)
    assert frame.pointer_context.cloud_liquid_g_kg is None
    assert frame.viewport is not None
    assert frame.viewport.default_mode == "full"
    assert frame.viewport.focus_available is False
    assert frame.lens is not None
    assert frame.lens.horizontal_wind_reference_m_s == pytest.approx(40.0)

    with pytest.raises(MountainWaveTerrainVisualizationError, match="requires moist output"):
        mountain_waves_frame_from_native_outputs(
            output_paths=paths,
            namelist_path=namelist,
            field="relative_humidity",
            time_index=0,
            run_id="dry-test",
            case_label="Dry test",
            implementation_commit="test-commit",
            dry_case=True,
            caveats=[],
        )


def test_cached_run_metadata_opens_only_the_requested_history_after_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, namelist = _write_world_histories(tmp_path, moist=True)
    clear_mountain_waves_run_metadata_cache()
    opened: list[Path] = []
    original_open_dataset = xr.open_dataset

    def counted_open_dataset(path: Any, *args: Any, **kwargs: Any) -> Any:
        opened.append(Path(path))
        return original_open_dataset(path, *args, **kwargs)

    monkeypatch.setattr(
        "cloud_chamber.mountain_wave_terrain_visualization.xr.open_dataset",
        counted_open_dataset,
    )

    validate_mountain_waves_native_outputs(
        output_paths=paths,
        namelist_path=namelist,
        run_id="cached-test",
        implementation_commit="test-commit",
        moist_fields_available=True,
    )
    assert opened == paths

    opened.clear()
    for time_index in (1, 2):
        mountain_waves_frame_from_native_outputs(
            output_paths=paths,
            namelist_path=namelist,
            field="cloud_over_wave",
            time_index=time_index,
            run_id="cached-test",
            case_label="Cached test",
            implementation_commit="test-commit",
            dry_case=False,
            caveats=[],
            measure_serialization=False,
        )
    assert opened == [paths[1], paths[2]]


@pytest.mark.parametrize("corruption", ["dimensions", "units", "nonfinite"])
def test_native_w_contract_validates_dimensions_units_and_finite_values(
    tmp_path: Path, corruption: str
) -> None:
    paths, namelist = _write_world_histories(tmp_path, moist=True)
    path = paths[1]
    with xr.open_dataset(path, decode_times=False) as source:
        dataset = source.load()
    if corruption == "dimensions":
        dataset = dataset.drop_vars("w")
        dataset["w"] = xr.DataArray(
            np.zeros((1, 2, 1, 3)),
            dims=("time", "zh", "yh", "xh"),
            attrs={"units": "m/s"},
        )
    elif corruption == "units":
        dataset["w"].attrs["units"] = "knots"
    else:
        dataset["w"].values[0, 0, 0, 0] = np.nan
    dataset.to_netcdf(path, mode="w")
    clear_mountain_waves_run_metadata_cache()

    with pytest.raises(MountainWaveTerrainVisualizationError, match="w"):
        validate_mountain_waves_native_outputs(
            output_paths=paths,
            namelist_path=namelist,
            run_id="invalid-w",
            implementation_commit="test-commit",
            moist_fields_available=True,
        )


def _write_native_histories(
    root: Path,
    *,
    runtime_top_m: float = 20_000.0,
    include_zhval: bool = True,
    time_offset_seconds: int = 0,
) -> tuple[list[Path], Path]:
    namelist = root / "namelist.input"
    namelist.write_text(
        """ &param0
 nx = 3,
 ny = 1,
 nz = 2,
 dx = 1000.0,
 dy = 1000.0,
 dz = 10000.0,
 /
 &param6
 stretch_z = 0,
 /
"""
    )
    xh_m = np.asarray([-1_000.0, 0.0, 1_000.0])
    xf_m = np.asarray([-1_500.0, -500.0, 500.0, 1_500.0])
    terrain_m = np.asarray([0.0, 400.0, 100.0])
    nominal_scalar_m = np.asarray([5_000.0, 15_000.0])
    nominal_full_m = np.asarray([0.0, 10_000.0, 20_000.0])
    scalar_height_m = (
        terrain_m[None, :] + nominal_scalar_m[:, None] * (20_000.0 - terrain_m[None, :]) / 20_000.0
    )
    paths: list[Path] = []
    for index, expected_time in enumerate(EXPECTED_OUTPUT_TIMES_SECONDS):
        theta = 300.0 + np.arange(6, dtype=np.float64).reshape(2, 1, 3)
        theta += index * 0.25
        w = np.linspace(-1.0, 1.0, 9, dtype=np.float64).reshape(3, 1, 3)
        w *= index + 1
        data_vars: dict[str, tuple[tuple[str, ...], object, dict[str, str]]] = {
            "zs": (("time", "yh", "xh"), terrain_m.reshape(1, 1, 3), {"units": "m"}),
            "th": (("time", "zh", "yh", "xh"), theta[None, ...], {"units": "K"}),
            "w": (("time", "zf", "yh", "xh"), w[None, ...], {"units": "m/s"}),
            "ztop": (("one",), [runtime_top_m], {"units": "m"}),
        }
        if include_zhval:
            data_vars["zhval"] = (
                ("time", "zh", "yh", "xh"),
                scalar_height_m.reshape(1, 2, 1, 3),
                {"units": "m"},
            )
        dataset = xr.Dataset(
            data_vars=data_vars,
            coords={
                "time": (
                    "time",
                    [expected_time + time_offset_seconds],
                    {"units": "seconds"},
                ),
                "xh": ("xh", xh_m / 1_000.0, {"units": "km"}),
                "xf": ("xf", xf_m / 1_000.0, {"units": "km"}),
                "yh": ("yh", [0.0], {"units": "km"}),
                "yf": ("yf", [-0.5, 0.5], {"units": "km"}),
                "zh": ("zh", nominal_scalar_m / 1_000.0, {"units": "km"}),
                "zf": ("zf", nominal_full_m / 1_000.0, {"units": "km"}),
                "one": ("one", [1]),
            },
        )
        path = root / f"cm1out_{index + 1:06d}.nc"
        dataset.to_netcdf(path)
        paths.append(path)
    return paths, namelist


def _write_world_histories(root: Path, *, moist: bool) -> tuple[list[Path], Path]:
    namelist = root / "world-namelist.input"
    namelist.write_text(
        """ &param0
 nx = 3,
 ny = 1,
 nz = 2,
 dx = 100000.0,
 dy = 1000.0,
 dz = 10000.0,
 timax = 400.0,
 tapfrq = 200.0,
 stretch_z = 0,
 ztop = 19000.0,
 /
"""
    )
    xh_m = np.asarray([-100_000.0, 0.0, 100_000.0])
    xf_m = np.asarray([-150_000.0, -50_000.0, 50_000.0, 150_000.0])
    terrain_m = np.asarray([0.0, 400.0, 100.0])
    nominal_scalar_m = np.asarray([5_000.0, 15_000.0])
    nominal_full_m = np.asarray([0.0, 10_000.0, 20_000.0])
    scalar_height_m = (
        terrain_m[None, :] + nominal_scalar_m[:, None] * (20_000.0 - terrain_m[None, :]) / 20_000.0
    )
    paths: list[Path] = []
    for index, time_seconds in enumerate((0, 200, 400)):
        theta = 285.0 + np.arange(6, dtype=np.float64).reshape(2, 1, 3) + index * 0.2
        pressure = np.asarray([55_000.0, 15_000.0])[:, None, None] * np.ones((2, 1, 3))
        scalar_w = np.asarray([[[-0.5, 0.0, 0.5]], [[-1.0, 0.25, 1.0]]], dtype=np.float64) * (
            index + 1
        )
        scalar_u = (
            np.asarray([[[10.0, 15.0, 20.0]], [[25.0, 30.0, 35.0]]], dtype=np.float64) + index
        )
        full_w = np.zeros((3, 1, 3), dtype=np.float64)
        full_w[:2] = scalar_w
        full_w[2] = scalar_w[-1]
        data_vars: dict[str, tuple[tuple[str, ...], object, dict[str, str]]] = {
            "zs": (("time", "yh", "xh"), terrain_m.reshape(1, 1, 3), {"units": "m"}),
            "zhval": (
                ("time", "zh", "yh", "xh"),
                scalar_height_m.reshape(1, 2, 1, 3),
                {"units": "m"},
            ),
            "th": (("time", "zh", "yh", "xh"), theta[None, ...], {"units": "K"}),
            "prs": (
                ("time", "zh", "yh", "xh"),
                pressure[None, ...],
                {"units": "Pa"},
            ),
            "winterp": (
                ("time", "zh", "yh", "xh"),
                scalar_w[None, ...],
                {"units": "m/s"},
            ),
            "uinterp": (
                ("time", "zh", "yh", "xh"),
                scalar_u[None, ...],
                {"units": "m/s"},
            ),
            "w": (("time", "zf", "yh", "xh"), full_w[None, ...], {"units": "m/s"}),
            "ztop": (("one",), [20_000.0], {"units": "m"}),
        }
        if moist:
            ql = np.zeros((2, 1, 3), dtype=np.float64)
            ql[0, 0, 1] = 0.002 * (index + 1)
            qv = np.full((2, 1, 3), 0.0025, dtype=np.float64)
            data_vars["ql"] = (
                ("time", "zh", "yh", "xh"),
                ql[None, ...],
                {"units": "kg/kg"},
            )
            data_vars["qv"] = (
                ("time", "zh", "yh", "xh"),
                qv[None, ...],
                {"units": "kg/kg"},
            )
        dataset = xr.Dataset(
            data_vars=data_vars,
            coords={
                "time": ("time", [time_seconds], {"units": "seconds"}),
                "xh": ("xh", xh_m / 1_000.0, {"units": "km"}),
                "xf": ("xf", xf_m / 1_000.0, {"units": "km"}),
                "yh": ("yh", [0.0], {"units": "km"}),
                "yf": ("yf", [-0.5, 0.5], {"units": "km"}),
                "zh": ("zh", nominal_scalar_m / 1_000.0, {"units": "km"}),
                "zf": ("zf", nominal_full_m / 1_000.0, {"units": "km"}),
                "one": ("one", [1]),
            },
        )
        path = root / f"cm1out_{index + 1:06d}.nc"
        dataset.to_netcdf(path)
        paths.append(path)
    return paths, namelist
