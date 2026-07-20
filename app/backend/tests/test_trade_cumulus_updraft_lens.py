from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import xarray as xr

import cloud_chamber.trade_cumulus_updraft_lens as lens
from cloud_chamber.result_ingest import ResultMetadata
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.trade_cumulus_updraft_lens import (
    CASE_ID,
    TradeCumulusUpdraftLensError,
    clear_trade_cumulus_updraft_lens_cache,
    trade_cumulus_updraft_lens_defaults,
    trade_cumulus_updraft_lens_eligible,
    trade_cumulus_updraft_lens_frame,
)


def _dataset(
    *,
    times: list[float] | None = None,
    scalar_w: bool = False,
    include_cwp: bool = True,
) -> xr.Dataset:
    times = times or [10_800.0, 11_100.0]
    nt, nz, ny, nx = len(times), 3, 4, 4
    ql = np.zeros((nt, nz, ny, nx), dtype=float)
    ql[:, :, 1, :] = 2e-6
    w_scalar = np.zeros_like(ql)
    w_scalar[:, :, 1, :] = 2.0
    if scalar_w:
        w = w_scalar
        w_dimensions = ("time", "zh", "yh", "xh")
    else:
        w = np.zeros((nt, nz + 1, ny, nx), dtype=float)
        w[:, :, 1, :] = 2.0
        w_dimensions = ("time", "zf", "yh", "xh")
    u = np.broadcast_to(
        np.arange(nx + 1, dtype=float)[None, None, None, :],
        (nt, nz, ny, nx + 1),
    ).copy()
    v = np.broadcast_to(
        np.arange(ny + 1, dtype=float)[None, None, :, None],
        (nt, nz, ny + 1, nx),
    ).copy()
    data_vars: dict[str, Any] = {
        "ql": (("time", "zh", "yh", "xh"), ql, {"units": "kg/kg"}),
        "w": (w_dimensions, w, {"units": "m/s"}),
        "u": (("time", "zh", "yh", "xf"), u, {"units": "m/s"}),
        "v": (("time", "zh", "yf", "xh"), v, {"units": "m/s"}),
    }
    if include_cwp:
        cwp = np.zeros((nt, ny, nx), dtype=float)
        for index in range(nt):
            cwp[index] = float(index + 1)
        data_vars["cwp"] = (("time", "yh", "xh"), cwp, {"units": "kg/m^2"})
    return xr.Dataset(
        data_vars,
        coords={
            "time": ("time", times, {"units": "s"}),
            "zh": ("zh", [0.2, 0.6, 1.0], {"units": "km"}),
            "zf": ("zf", [0.0, 0.4, 0.8, 1.2], {"units": "km"}),
            "yh": ("yh", [-0.15, -0.05, 0.05, 0.15], {"units": "km"}),
            "xh": ("xh", [-0.15, -0.05, 0.05, 0.15], {"units": "km"}),
            "yf": ("yf", [-0.2, -0.1, 0.0, 0.1, 0.2], {"units": "km"}),
            "xf": ("xf", [-0.2, -0.1, 0.0, 0.1, 0.2], {"units": "km"}),
        },
    )


def _metadata(
    path: Path,
    *,
    scenario_id: str = CASE_ID,
    case_id: str | None = None,
    time_steps: int = 2,
    default_time_by_field: dict[str, Any] | None = None,
) -> ResultMetadata:
    now = datetime(2026, 7, 19, tzinfo=UTC)
    return ResultMetadata(
        result_id="result-trade-cumulus",
        run_id="trade-cumulus",
        scenario_id=scenario_id,
        physical_question="Where does cloud-forming ascent occur?",
        controls={},
        run_configuration={"case_id": case_id} if case_id else {},
        source_lifecycle_state="completed",
        source_product_state="candidate",
        source_model="CM1",
        model_output_paths=[str(path)],
        model_output_file_count=1,
        time_steps=time_steps,
        first_output_time_seconds=10_800,
        last_output_time_seconds=11_100,
        default_time_by_field=default_time_by_field or {},
        created_at=now,
        updated_at=now,
    )


def _install_result(
    tmp_path: Path,
    dataset: xr.Dataset,
    **metadata_options: Any,
) -> tuple[CloudChamberSettings, ResultMetadata]:
    run_dir = tmp_path / "runs" / "trade-cumulus"
    run_dir.mkdir(parents=True)
    path = run_dir / "cm1out.nc"
    dataset.to_netcdf(path)
    metadata = _metadata(path, time_steps=int(dataset.sizes["time"]), **metadata_options)
    (run_dir / "result_metadata.json").write_text(metadata.to_json_text())
    settings = CloudChamberSettings(
        runtime_home=tmp_path,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "cache",
        log_dir=tmp_path / "logs",
    )
    clear_trade_cumulus_updraft_lens_cache()
    return settings, metadata


def test_eligibility_accepts_exact_scenario_id(tmp_path: Path) -> None:
    metadata = _metadata(tmp_path / "output.nc")
    assert trade_cumulus_updraft_lens_eligible(metadata) is True


def test_eligibility_accepts_exact_run_configuration_case_id(tmp_path: Path) -> None:
    metadata = _metadata(tmp_path / "output.nc", scenario_id="historical", case_id=CASE_ID)
    assert trade_cumulus_updraft_lens_eligible(metadata) is True


def test_eligibility_does_not_infer_from_raw_fields(tmp_path: Path) -> None:
    metadata = _metadata(tmp_path / "output.nc", scenario_id="lookalike")
    metadata.variables = ["ql", "w", "u", "v", "cwp"]
    assert trade_cumulus_updraft_lens_eligible(metadata) is False


def test_w_face_grid_is_centered_to_ql_levels() -> None:
    dataset = _dataset()
    ql, dimensions = lens._scalar_ql(dataset, 0)
    centered = lens.center_vertical_velocity_to_scalar_grid(dataset, 0, dimensions, ql.shape)
    assert centered.shape == ql.shape
    assert centered[:, 1, :] == pytest.approx(np.full((3, 4), 2.0))


def test_w_scalar_grid_is_used_directly() -> None:
    dataset = _dataset(scalar_w=True)
    ql, dimensions = lens._scalar_ql(dataset, 0)
    centered = lens.center_vertical_velocity_to_scalar_grid(dataset, 0, dimensions, ql.shape)
    assert centered[:, 1, :] == pytest.approx(np.full((3, 4), 2.0))


def test_w_rejects_unsupported_vertical_stagger() -> None:
    dataset = _dataset().drop_vars("w")
    dataset["w"] = (("time", "bad_z", "yh", "xh"), np.zeros((2, 5, 4, 4)))
    with pytest.raises(TradeCumulusUpdraftLensError, match="supported z dimension"):
        ql, dimensions = lens._scalar_ql(dataset, 0)
        lens.center_vertical_velocity_to_scalar_grid(dataset, 0, dimensions, ql.shape)


def test_default_time_uses_max_domain_mean_cwp_after_three_hours(tmp_path: Path) -> None:
    settings, _ = _install_result(tmp_path, _dataset())
    defaults = trade_cumulus_updraft_lens_defaults(settings, "result-trade-cumulus")
    assert defaults.default_time_index == 1
    assert defaults.default_time_seconds == 11_100


def test_default_time_tie_uses_earlier_frame() -> None:
    metadata = _metadata(Path("output.nc"))
    frames = [
        lens._FrameLocation(0, Path("a.nc"), 0, 10_800),
        lens._FrameLocation(1, Path("b.nc"), 0, 11_100),
    ]
    assert lens._select_default_time(metadata, frames, [2.0, 2.0])[0] == 0


def test_default_time_falls_back_to_supported_cloud_liquid_diagnostic() -> None:
    metadata = _metadata(
        Path("output.nc"),
        default_time_by_field={
            "ql": {
                "field": "ql",
                "time_index": 0,
                "time_seconds": 10_800,
                "source_interesting_time_key": "max_qc",
                "support_state": "supported",
                "caveats": [],
            }
        },
    )
    frames = [
        lens._FrameLocation(0, Path("a.nc"), 0, 10_800),
        lens._FrameLocation(1, Path("b.nc"), 0, 11_100),
    ]
    index, method, caveats = lens._select_default_time(metadata, frames, [None, None])
    assert (index, method) == (0, "diagnostics_supported_time_of_max_cloud_liquid")
    assert "domain_mean_cwp_default_unavailable" in caveats


def test_default_time_falls_back_to_latest_final_three_hour_output() -> None:
    metadata = _metadata(Path("output.nc"))
    frames = [
        lens._FrameLocation(0, Path("a.nc"), 0, None),
        lens._FrameLocation(1, Path("b.nc"), 0, 20_000),
    ]
    index, method, _ = lens._select_default_time(metadata, frames, [None, None])
    assert (index, method) == (1, "latest_output_in_final_three_hours")


def test_plane_uses_greatest_positive_w_times_ql_score() -> None:
    ql = np.zeros((3, 3, 4))
    ql[:, 0, :] = 2e-6
    ql[:, 2, :] = 2e-6
    w = np.zeros_like(ql)
    w[:, 0, :] = -20
    w[:, 2, :] = 1
    assert lens._select_default_plane(ql, w) == (
        2,
        "greatest_coherent_positive_w_times_ql_score",
    )


def test_plane_ignores_small_disconnected_cloud_objects() -> None:
    ql = np.zeros((4, 3, 4))
    ql[0, 0, 0] = 1e-3
    ql[:, 1, :] = 2e-6
    w = np.ones_like(ql)
    assert lens._select_default_plane(ql, w)[0] == 1


def test_plane_score_combines_all_coherent_components_on_each_y_plane() -> None:
    ql = np.zeros((5, 2, 10))
    ql[:, 0, 0:2] = 2e-6
    ql[:, 0, 4:6] = 2e-6
    ql[:, 1, 0:2] = 2e-6
    w = np.zeros_like(ql)
    w[:, 0, :] = 1.0
    w[:, 1, :] = 1.5
    assert lens._select_default_plane(ql, w)[0] == 0


def test_plane_falls_back_to_largest_coherent_cloud_component() -> None:
    ql = np.zeros((4, 3, 4))
    ql[:3, 0, :] = 2e-6
    ql[:, 2, :] = 2e-6
    w = np.full_like(ql, np.nan)
    assert lens._select_default_plane(ql, w) == (
        2,
        "largest_coherent_cloud_component_fallback",
    )


def test_plane_falls_back_to_domain_midpoint_without_coherent_cloud() -> None:
    ql = np.zeros((3, 4, 4))
    w = np.ones_like(ql)
    assert lens._select_default_plane(ql, w) == (2, "domain_midpoint_fallback")


def test_fixed_range_uses_percentile_floor_and_rounding() -> None:
    assert lens.rounded_percentile_reference([np.asarray([0.2, 0.21])], 99, 0.5) == 0.5
    assert lens.rounded_percentile_reference([np.asarray([0.61, 0.62])], 99, 0.5) == 0.7


def test_defaults_return_exact_world_owned_fixed_scale(tmp_path: Path) -> None:
    settings, _ = _install_result(tmp_path, _dataset(scalar_w=True))
    defaults = trade_cumulus_updraft_lens_defaults(settings, "result-trade-cumulus")

    assert defaults.w_scale_id == "trade_cumulus_updraft_velocity_v1"
    assert defaults.w_scale_owner == "trade_cumulus"
    assert lens.TRADE_CUMULUS_UPDRAFT_LENS_ID == "updraft"
    assert defaults.w_scale_type == "fixed_discrete"
    assert defaults.w_scale_units == "m/s"
    assert defaults.w_scale_breakpoints_m_s == [
        -1.0,
        -0.5,
        -0.1,
        0.1,
        0.5,
        1.0,
        2.0,
        3.0,
        5.0,
    ]
    assert defaults.w_scale_colors == [
        "#4b0082",
        "#0057d9",
        "#00c9d8",
        "#ffffff",
        "#00d63b",
        "#8fe000",
        "#ffe000",
        "#ff9800",
        "#ff3b00",
        "#c40000",
    ]
    assert defaults.w_scale_neutral_interval_m_s == [-0.1, 0.1]
    assert defaults.w_scale_source == "pm_approved_issue_379_from_stage5b2_matched_pair"
    assert defaults.w_scale_clipping_behavior == (
        "values_below_-1.0_and_at_or_above_5.0_use_endpoint_colors_and_are_reported_as_clipped"
    )
    assert defaults.w_range_min_m_s == -1.0
    assert defaults.w_range_max_m_s == 5.0
    assert defaults.w_range_method == "fixed_trade_cumulus_updraft_velocity_v1"


def test_defaults_scale_is_independent_of_result_w_distribution(tmp_path: Path) -> None:
    low_dataset = _dataset(scalar_w=True)
    low_dataset["w"].values[:] = -40.0
    middle_dataset = _dataset(scalar_w=True)
    middle_dataset["w"].values[:] = 0.02
    high_dataset = _dataset(scalar_w=True)
    high_dataset["w"].values[:] = 40.0

    low_settings, _ = _install_result(tmp_path / "low", low_dataset)
    low_defaults = trade_cumulus_updraft_lens_defaults(low_settings, "result-trade-cumulus")
    middle_settings, _ = _install_result(tmp_path / "middle", middle_dataset)
    middle_defaults = trade_cumulus_updraft_lens_defaults(middle_settings, "result-trade-cumulus")
    high_settings, _ = _install_result(tmp_path / "high", high_dataset)
    high_defaults = trade_cumulus_updraft_lens_defaults(high_settings, "result-trade-cumulus")

    scale_fields = (
        "w_scale_id",
        "w_scale_owner",
        "w_scale_type",
        "w_scale_units",
        "w_scale_breakpoints_m_s",
        "w_scale_colors",
        "w_scale_neutral_interval_m_s",
        "w_scale_source",
        "w_scale_clipping_behavior",
        "w_range_min_m_s",
        "w_range_max_m_s",
        "w_range_method",
    )
    scale_payloads = [
        defaults.model_dump(include=set(scale_fields))
        for defaults in (low_defaults, middle_defaults, high_defaults)
    ]
    assert scale_payloads[0] == scale_payloads[1] == scale_payloads[2]


def test_u_and_v_faces_are_centered_to_scalar_grid() -> None:
    dataset = _dataset()
    ql, dimensions = lens._scalar_ql(dataset, 0)
    u, v = lens.center_horizontal_wind_to_scalar_grid(dataset, 0, dimensions, ql.shape)
    assert u.shape == ql.shape
    assert v.shape == ql.shape
    assert u[0, 0] == pytest.approx([0.5, 1.5, 2.5, 3.5])
    assert v[0, :, 0] == pytest.approx([0.5, 1.5, 2.5, 3.5])


def test_horizontal_wind_rejects_unsupported_face_stagger() -> None:
    dataset = _dataset().drop_vars("u")
    dataset["u"] = (("time", "zh", "yh", "bad_x"), np.zeros((2, 3, 4, 6)))
    ql, dimensions = lens._scalar_ql(dataset, 0)
    with pytest.raises(TradeCumulusUpdraftLensError, match="supported x dimension"):
        lens.center_horizontal_wind_to_scalar_grid(dataset, 0, dimensions, ql.shape)


def test_frame_switches_between_perturbation_and_total_wind(tmp_path: Path) -> None:
    settings, _ = _install_result(tmp_path, _dataset())
    defaults = trade_cumulus_updraft_lens_defaults(settings, "result-trade-cumulus")
    perturbation = trade_cumulus_updraft_lens_frame(
        settings,
        "result-trade-cumulus",
        time_index=defaults.default_time_index,
        plane_index=defaults.default_plane_index,
        wind_mode="perturbation",
    )
    total = trade_cumulus_updraft_lens_frame(
        settings,
        "result-trade-cumulus",
        time_index=defaults.default_time_index,
        plane_index=defaults.default_plane_index,
        wind_mode="total",
    )
    assert perturbation.domain_mean_u_m_s == pytest.approx(2.0)
    assert total.wind_vectors[0].u_m_s != perturbation.wind_vectors[0].u_m_s
    assert total.wind_reference_m_s == defaults.total_wind_reference_m_s


@pytest.mark.parametrize(
    ("orientation", "plane_index", "plane_dimension", "dimension_order", "shape"),
    [
        ("horizontal", 1, "z", ["y", "x"], (4, 4)),
        ("vertical_x", 1, "y", ["z", "x"], (3, 4)),
        ("vertical_y", 2, "x", ["z", "y"], (3, 4)),
    ],
)
def test_frame_returns_native_grid_for_each_slice_orientation(
    tmp_path: Path,
    orientation: lens.LensOrientation,
    plane_index: int,
    plane_dimension: str,
    dimension_order: list[str],
    shape: tuple[int, int],
) -> None:
    settings, _ = _install_result(tmp_path, _dataset(scalar_w=True))
    frame = trade_cumulus_updraft_lens_frame(
        settings,
        "result-trade-cumulus",
        time_index=1,
        orientation=orientation,
        plane_index=plane_index,
        wind_mode="perturbation",
    )

    assert frame.orientation == orientation
    assert frame.plane_dimension == plane_dimension
    assert frame.dimension_order == dimension_order
    assert np.asarray(frame.w_values_m_s).shape == shape
    assert np.asarray(frame.cloud_mask).shape == shape
    assert frame.plane_units == "km"
    assert frame.x_values_km == pytest.approx([-0.15, -0.05, 0.05, 0.15])
    assert frame.y_values_km == pytest.approx([-0.15, -0.05, 0.05, 0.15])
    assert frame.z_values_km == pytest.approx([0.2, 0.6, 1.0])


def test_wind_stride_bounds_arrow_count_and_skips_zero_vectors() -> None:
    u = np.ones((64, 64))
    v = np.zeros((64, 64))
    vectors = lens._wind_vectors(u, v, np.arange(64), np.arange(64), 0.6)
    assert len(vectors) == 64
    zero_vectors = lens._wind_vectors(
        np.zeros((8, 8)), np.zeros((8, 8)), np.arange(8), np.arange(8), 0.6
    )
    assert zero_vectors == []


def test_wind_references_use_p95_floor() -> None:
    assert lens.rounded_percentile_reference([np.asarray([0.1, 0.2])], 95, 0.5) == 0.5
    assert lens.rounded_percentile_reference([np.asarray([0.81, 0.82])], 95, 0.5) == 0.9


def test_frame_orders_z_ascending_and_serializes_nonfinite_values(tmp_path: Path) -> None:
    dataset = _dataset()
    dataset["w"].values[1, 1, 1, 0] = np.nan
    settings, _ = _install_result(tmp_path, dataset)
    frame = trade_cumulus_updraft_lens_frame(
        settings,
        "result-trade-cumulus",
        time_index=1,
        plane_index=1,
        wind_mode="perturbation",
    )
    assert frame.z_values_km == sorted(frame.z_values_km)
    assert frame.w_values_m_s[0][0] is None or frame.w_values_m_s[1][0] is None


def test_frame_reports_exact_finite_and_clipping_semantics(tmp_path: Path) -> None:
    dataset = _dataset(scalar_w=True)
    dataset["w"].values[1, :, 1, :] = np.asarray(
        [
            [-1.01, -1.0, 4.99, 5.0],
            [np.nan, np.inf, -np.inf, 0.0],
            [-2.0, 8.0, -0.1, 0.1],
        ]
    )
    settings, _ = _install_result(tmp_path, dataset)
    frame = trade_cumulus_updraft_lens_frame(
        settings,
        "result-trade-cumulus",
        time_index=1,
        plane_index=1,
        wind_mode="perturbation",
    )

    assert frame.w_finite_count == 9
    assert frame.w_low_clipped_count == 2
    assert frame.w_high_clipped_count == 2
    assert frame.w_low_clipped_fraction == pytest.approx(2 / 9)
    assert frame.w_high_clipped_fraction == pytest.approx(2 / 9)
    assert frame.w_scale_breakpoints_m_s == [-1.0, -0.5, -0.1, 0.1, 0.5, 1.0, 2.0, 3.0, 5.0]
    assert frame.w_range_method == "fixed_trade_cumulus_updraft_velocity_v1"


def test_frame_uses_null_clipping_fractions_when_no_finite_w_exists(tmp_path: Path) -> None:
    dataset = _dataset(scalar_w=True)
    dataset["w"].values[:] = np.nan
    settings, _ = _install_result(tmp_path, dataset)
    frame = trade_cumulus_updraft_lens_frame(
        settings,
        "result-trade-cumulus",
        time_index=1,
        plane_index=1,
        wind_mode="perturbation",
    )

    assert frame.w_finite_count == 0
    assert frame.w_low_clipped_count == 0
    assert frame.w_high_clipped_count == 0
    assert frame.w_low_clipped_fraction is None
    assert frame.w_high_clipped_fraction is None


def test_invalid_indices_and_wind_mode_are_rejected(tmp_path: Path) -> None:
    settings, _ = _install_result(tmp_path, _dataset())
    with pytest.raises(TradeCumulusUpdraftLensError, match="time_index"):
        trade_cumulus_updraft_lens_frame(
            settings,
            "result-trade-cumulus",
            time_index=-1,
            plane_index=0,
            wind_mode="total",
        )
    with pytest.raises(TradeCumulusUpdraftLensError, match="orientation"):
        trade_cumulus_updraft_lens_frame(
            settings,
            "result-trade-cumulus",
            time_index=0,
            orientation="diagonal",  # type: ignore[arg-type]
            plane_index=0,
            wind_mode="total",
        )
    with pytest.raises(TradeCumulusUpdraftLensError, match="plane_index"):
        trade_cumulus_updraft_lens_frame(
            settings,
            "result-trade-cumulus",
            time_index=0,
            plane_index=99,
            wind_mode="total",
        )


def test_ineligible_result_is_rejected_even_with_required_fields(tmp_path: Path) -> None:
    settings, _ = _install_result(tmp_path, _dataset(), scenario_id="lookalike")
    with pytest.raises(TradeCumulusUpdraftLensError, match="not eligible"):
        trade_cumulus_updraft_lens_defaults(settings, "result-trade-cumulus")


def test_defaults_cache_reuses_computation_and_closes_every_open_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "output.nc"
    source.touch()
    metadata = _metadata(source)
    dataset = _dataset()
    opens = 0
    closes = 0

    class DatasetProxy:
        def __getattr__(self, name: str) -> Any:
            return getattr(dataset, name)

        def __getitem__(self, name: str) -> Any:
            return dataset[name]

        def close(self) -> None:
            nonlocal closes
            closes += 1

    def open_dataset(_path: Path) -> DatasetProxy:
        nonlocal opens
        opens += 1
        return DatasetProxy()

    clear_trade_cumulus_updraft_lens_cache()
    monkeypatch.setattr(lens, "_open_dataset", open_dataset)
    first = lens._cached_defaults(metadata)
    second = lens._cached_defaults(metadata)
    assert first is second
    assert opens == 2
    assert closes == opens
