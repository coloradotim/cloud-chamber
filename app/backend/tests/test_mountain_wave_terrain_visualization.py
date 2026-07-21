from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from cloud_chamber.mountain_wave_case import EXPECTED_OUTPUT_TIMES_SECONDS
from cloud_chamber.mountain_wave_terrain_visualization import (
    MountainWaveTerrainVisualizationError,
    local_agl_m,
    terrain_frame_from_native_outputs,
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
                "zh": ("zh", nominal_scalar_m / 1_000.0, {"units": "km"}),
                "zf": ("zf", nominal_full_m / 1_000.0, {"units": "km"}),
                "one": ("one", [1]),
            },
        )
        path = root / f"cm1out_{index + 1:06d}.nc"
        dataset.to_netcdf(path)
        paths.append(path)
    return paths, namelist
