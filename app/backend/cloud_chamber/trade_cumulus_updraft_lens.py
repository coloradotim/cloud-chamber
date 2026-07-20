"""Bounded Trade Cumulus Updraft Lens data products."""

from __future__ import annotations

import importlib
import math
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.result_ingest import ResultMetadata, get_result_metadata
from cloud_chamber.settings import CloudChamberSettings

CASE_ID = "bomex_trade_cumulus_baseline_v0"
CLOUD_THRESHOLD_KG_KG = 1e-6
W_PERCENTILE = 99
W_MIN_RANGE_M_S = 0.5
W_ROUNDING_M_S = 0.1
WIND_TARGET_LEVEL_M = 600
WIND_STRIDE = 8
WIND_PERCENTILE = 95
WIND_MIN_REFERENCE_M_S = 0.5
WIND_ARROW_DOMAIN_FRACTION = 0.08
MIN_COHERENT_CLOUD_CELLS = 10

WindMode = Literal["perturbation", "total"]
LensOrientation = Literal["horizontal", "vertical_x", "vertical_y"]
LensDimension = Literal["x", "y", "z"]


class TradeCumulusUpdraftLensError(RuntimeError):
    """Raised when the bounded Updraft Lens product cannot be produced."""


class UpdraftLensProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_model: str
    result_id: str
    run_id: str
    scenario_id: str
    processing_method: str
    rendering_method: str
    provenance_label: str


class TradeCumulusUpdraftLensDefaults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    case_id: str
    eligible: bool
    primary_field: Literal["w"] = "w"
    cloud_field: Literal["ql"] = "ql"
    orientation: Literal["vertical_x"] = "vertical_x"
    default_time_index: int
    default_time_seconds: float | None
    default_time_method: str
    default_plane_dimension: Literal["y"] = "y"
    default_plane_index: int
    default_plane_coordinate: float | None
    default_plane_units: str | None
    default_plane_method: str
    cloud_threshold_kg_kg: float = CLOUD_THRESHOLD_KG_KG
    w_range_min_m_s: float
    w_range_max_m_s: float
    w_range_method: str
    wind_target_level_m: float = WIND_TARGET_LEVEL_M
    wind_actual_level_m: float
    wind_level_index: int
    wind_default_mode: Literal["perturbation"] = "perturbation"
    wind_stride: int = WIND_STRIDE
    wind_shown_by_default: bool = True
    perturbation_wind_reference_m_s: float
    total_wind_reference_m_s: float
    wind_arrow_domain_fraction: float = WIND_ARROW_DOMAIN_FRACTION
    provenance: UpdraftLensProvenance
    caveats: list[str] = Field(default_factory=list)


class UpdraftLensWindVector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_km: float
    y_km: float
    z_km: float
    u_m_s: float
    v_m_s: float
    magnitude_m_s: float


class TradeCumulusUpdraftLensFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    time_index: int
    time_seconds: float | None
    orientation: LensOrientation
    plane_dimension: LensDimension
    plane_index: int
    plane_coordinate: float | None
    plane_units: str | None
    dimension_order: list[LensDimension]
    x_indices: list[int]
    x_values_km: list[float]
    y_indices: list[int]
    y_values_km: list[float]
    z_indices: list[int]
    z_values_km: list[float]
    w_values_m_s: list[list[float | None]]
    cloud_mask: list[list[bool]]
    cloud_threshold_kg_kg: float = CLOUD_THRESHOLD_KG_KG
    w_range_min_m_s: float
    w_range_max_m_s: float
    w_range_method: str
    wind_mode: WindMode
    wind_target_level_m: float = WIND_TARGET_LEVEL_M
    wind_actual_level_m: float
    wind_level_index: int
    wind_stride: int = WIND_STRIDE
    wind_reference_m_s: float
    wind_arrow_domain_fraction: float = WIND_ARROW_DOMAIN_FRACTION
    domain_mean_u_m_s: float
    domain_mean_v_m_s: float
    wind_vectors: list[UpdraftLensWindVector]
    provenance: UpdraftLensProvenance
    caveats: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class _FrameLocation:
    global_index: int
    path: Path
    local_index: int
    time_seconds: float | None


@dataclass(frozen=True)
class _CachedDefaults:
    response: TradeCumulusUpdraftLensDefaults
    frames: tuple[_FrameLocation, ...]


_DEFAULTS_CACHE: OrderedDict[tuple[object, ...], _CachedDefaults] = OrderedDict()
_MAX_CACHE_ENTRIES = 8


def trade_cumulus_updraft_lens_eligible(metadata: ResultMetadata) -> bool:
    """Return eligibility from approved case identifiers only."""
    return metadata.scenario_id == CASE_ID or metadata.run_configuration.get("case_id") == CASE_ID


def trade_cumulus_updraft_lens_defaults(
    settings: CloudChamberSettings,
    result_id: str,
) -> TradeCumulusUpdraftLensDefaults:
    metadata = get_result_metadata(settings, result_id)
    return _cached_defaults(metadata).response


def trade_cumulus_updraft_lens_frame(
    settings: CloudChamberSettings,
    result_id: str,
    *,
    time_index: int,
    orientation: LensOrientation = "vertical_x",
    plane_index: int,
    wind_mode: WindMode,
) -> TradeCumulusUpdraftLensFrame:
    metadata = get_result_metadata(settings, result_id)
    cached = _cached_defaults(metadata)
    if time_index < 0 or time_index >= len(cached.frames):
        raise TradeCumulusUpdraftLensError(
            f"time_index must be between 0 and {max(0, len(cached.frames) - 1)}."
        )
    if plane_index < 0:
        raise TradeCumulusUpdraftLensError("plane_index must be non-negative.")
    if orientation not in {"horizontal", "vertical_x", "vertical_y"}:
        raise TradeCumulusUpdraftLensError(f"Unsupported orientation: {orientation}")
    if wind_mode not in {"perturbation", "total"}:
        raise TradeCumulusUpdraftLensError(f"Unsupported wind_mode: {wind_mode}")

    frame = cached.frames[time_index]
    dataset = _open_dataset(frame.path)
    try:
        ql, dimensions = _scalar_ql(dataset, frame.local_index)
        w = _center_w(dataset, frame.local_index, dimensions, ql.shape)
        nz, ny, nx = ql.shape
        plane_size = {
            "horizontal": nz,
            "vertical_x": ny,
            "vertical_y": nx,
        }[orientation]
        if plane_index >= plane_size:
            raise TradeCumulusUpdraftLensError(
                f"plane_index must be between 0 and {max(0, plane_size - 1)}."
            )

        x_values = _coordinate_as(dataset, dimensions[2], "km", nx)
        y_values = _coordinate_as(dataset, dimensions[1], "km", ny)
        z_values = _coordinate_as(dataset, dimensions[0], "km", nz)
        if orientation == "horizontal":
            plane_dimension: LensDimension = "z"
            dimension_order: list[LensDimension] = ["y", "x"]
            plane_coordinate = _finite_float(z_values[plane_index])
            w_slice = w[plane_index, :, :]
            cloud_slice = ql[plane_index, :, :] >= CLOUD_THRESHOLD_KG_KG
        elif orientation == "vertical_x":
            plane_dimension = "y"
            dimension_order = ["z", "x"]
            plane_coordinate = _finite_float(y_values[plane_index])
            w_slice = w[:, plane_index, :]
            cloud_slice = ql[:, plane_index, :] >= CLOUD_THRESHOLD_KG_KG
        else:
            plane_dimension = "x"
            dimension_order = ["z", "y"]
            plane_coordinate = _finite_float(x_values[plane_index])
            w_slice = w[:, :, plane_index]
            cloud_slice = ql[:, :, plane_index] >= CLOUD_THRESHOLD_KG_KG

        u, v = _center_horizontal_wind(dataset, frame.local_index, dimensions, ql.shape)
        wind_level_index = cached.response.wind_level_index
        level_u = u[wind_level_index]
        level_v = v[wind_level_index]
        mean_u = _finite_mean(level_u)
        mean_v = _finite_mean(level_v)
        shown_u = level_u - mean_u if wind_mode == "perturbation" else level_u
        shown_v = level_v - mean_v if wind_mode == "perturbation" else level_v
        wind_reference = (
            cached.response.perturbation_wind_reference_m_s
            if wind_mode == "perturbation"
            else cached.response.total_wind_reference_m_s
        )
        wind_vectors = _wind_vectors(
            shown_u,
            shown_v,
            x_values,
            y_values,
            cached.response.wind_actual_level_m / 1000.0,
        )

        return TradeCumulusUpdraftLensFrame(
            result_id=metadata.result_id,
            time_index=time_index,
            time_seconds=frame.time_seconds,
            orientation=orientation,
            plane_dimension=plane_dimension,
            plane_index=plane_index,
            plane_coordinate=plane_coordinate,
            plane_units="km",
            dimension_order=dimension_order,
            x_indices=list(range(nx)),
            x_values_km=[float(value) for value in x_values],
            y_indices=list(range(ny)),
            y_values_km=[float(value) for value in y_values],
            z_indices=list(range(nz)),
            z_values_km=[float(value) for value in z_values],
            w_values_m_s=_json_float_matrix(w_slice),
            cloud_mask=cloud_slice.astype(bool).tolist(),
            w_range_min_m_s=cached.response.w_range_min_m_s,
            w_range_max_m_s=cached.response.w_range_max_m_s,
            w_range_method=cached.response.w_range_method,
            wind_mode=wind_mode,
            wind_actual_level_m=cached.response.wind_actual_level_m,
            wind_level_index=wind_level_index,
            wind_reference_m_s=wind_reference,
            domain_mean_u_m_s=mean_u,
            domain_mean_v_m_s=mean_v,
            wind_vectors=wind_vectors,
            provenance=_provenance(metadata, "trade_cumulus_updraft_lens_frame"),
            caveats=[
                "vertical_velocity_centered_to_cloud_liquid_scalar_levels",
                "cloud_boundary_uses_fixed_1e-6_kg_kg_threshold",
                "horizontal_wind_vectors_sampled_on_scalar_grid",
            ],
        )
    finally:
        dataset.close()


def clear_trade_cumulus_updraft_lens_cache() -> None:
    """Clear the bounded process cache for deterministic tests."""
    _DEFAULTS_CACHE.clear()


def _cached_defaults(metadata: ResultMetadata) -> _CachedDefaults:
    if not trade_cumulus_updraft_lens_eligible(metadata):
        raise TradeCumulusUpdraftLensError(
            f"Result {metadata.result_id} is not eligible for the Trade Cumulus Updraft Lens."
        )
    paths = _source_paths(metadata)
    key = (
        metadata.result_id,
        metadata.scenario_id,
        metadata.run_configuration.get("case_id"),
        metadata.updated_at.isoformat(),
        tuple(_path_state(path) for path in paths),
    )
    cached = _DEFAULTS_CACHE.get(key)
    if cached is not None:
        _DEFAULTS_CACHE.move_to_end(key)
        return cached
    computed = _compute_defaults(metadata, paths)
    _DEFAULTS_CACHE[key] = computed
    _DEFAULTS_CACHE.move_to_end(key)
    while len(_DEFAULTS_CACHE) > _MAX_CACHE_ENTRIES:
        _DEFAULTS_CACHE.popitem(last=False)
    return computed


def _compute_defaults(metadata: ResultMetadata, paths: list[Path]) -> _CachedDefaults:
    frames: list[_FrameLocation] = []
    cwp_scores: list[float | None] = []
    absolute_w: list[np.ndarray[Any, np.dtype[np.floating[Any]]]] = []
    perturbation_speeds: list[np.ndarray[Any, np.dtype[np.floating[Any]]]] = []
    total_speeds: list[np.ndarray[Any, np.dtype[np.floating[Any]]]] = []
    wind_level_index: int | None = None
    wind_actual_level_m: float | None = None
    first_dimensions: tuple[str, str, str] | None = None
    global_index = 0

    for path in paths:
        dataset = _open_dataset(path)
        try:
            local_count = _time_count(dataset)
            for local_index in range(local_count):
                ql, dimensions = _scalar_ql(dataset, local_index)
                w = _center_w(dataset, local_index, dimensions, ql.shape)
                if first_dimensions is None:
                    first_dimensions = dimensions
                elif dimensions != first_dimensions:
                    raise TradeCumulusUpdraftLensError(
                        "Trade Cumulus source files do not share one scalar-grid layout."
                    )
                frame_time = _time_seconds(dataset, local_index, metadata, global_index)
                frames.append(
                    _FrameLocation(
                        global_index=global_index,
                        path=path,
                        local_index=local_index,
                        time_seconds=frame_time,
                    )
                )
                cwp_scores.append(_domain_mean_cwp(dataset, local_index))
                finite_absolute_w = np.abs(w[np.isfinite(w)])
                if finite_absolute_w.size:
                    absolute_w.append(finite_absolute_w.astype(np.float32, copy=False))

                if wind_level_index is None:
                    z_values_m = _coordinate_as(dataset, dimensions[0], "m", ql.shape[0])
                    wind_level_index = int(np.argmin(np.abs(z_values_m - WIND_TARGET_LEVEL_M)))
                    wind_actual_level_m = float(z_values_m[wind_level_index])
                u, v = _center_horizontal_wind(dataset, local_index, dimensions, ql.shape)
                level_u = u[wind_level_index]
                level_v = v[wind_level_index]
                mean_u = _finite_mean(level_u)
                mean_v = _finite_mean(level_v)
                total_speed = np.hypot(level_u, level_v)
                perturbation_speed = np.hypot(level_u - mean_u, level_v - mean_v)
                finite_total = total_speed[np.isfinite(total_speed)]
                finite_perturbation = perturbation_speed[np.isfinite(perturbation_speed)]
                if finite_total.size:
                    total_speeds.append(finite_total.astype(np.float32, copy=False))
                if finite_perturbation.size:
                    perturbation_speeds.append(finite_perturbation.astype(np.float32, copy=False))
                global_index += 1
        finally:
            dataset.close()

    if not frames or first_dimensions is None:
        raise TradeCumulusUpdraftLensError("No readable model-output frames are available.")
    if wind_level_index is None or wind_actual_level_m is None:
        raise TradeCumulusUpdraftLensError("No supported wind level is available.")

    default_time_index, default_time_method, time_caveats = _select_default_time(
        metadata, frames, cwp_scores
    )
    selected_frame = frames[default_time_index]
    selected_dataset = _open_dataset(selected_frame.path)
    try:
        selected_ql, dimensions = _scalar_ql(selected_dataset, selected_frame.local_index)
        selected_w = _center_w(
            selected_dataset,
            selected_frame.local_index,
            dimensions,
            selected_ql.shape,
        )
        default_plane_index, default_plane_method = _select_default_plane(selected_ql, selected_w)
        y_values = _coordinate_values(selected_dataset, dimensions[1], selected_ql.shape[1])
        default_plane_coordinate = _finite_float(y_values[default_plane_index])
        default_plane_units = _coordinate_units(selected_dataset, dimensions[1])
    finally:
        selected_dataset.close()

    w_range = _rounded_reference(absolute_w, W_PERCENTILE, W_MIN_RANGE_M_S)
    perturbation_reference = _rounded_reference(
        perturbation_speeds, WIND_PERCENTILE, WIND_MIN_REFERENCE_M_S
    )
    total_reference = _rounded_reference(total_speeds, WIND_PERCENTILE, WIND_MIN_REFERENCE_M_S)
    response = TradeCumulusUpdraftLensDefaults(
        result_id=metadata.result_id,
        case_id=CASE_ID,
        eligible=True,
        default_time_index=default_time_index,
        default_time_seconds=frames[default_time_index].time_seconds,
        default_time_method=default_time_method,
        default_plane_index=default_plane_index,
        default_plane_coordinate=default_plane_coordinate,
        default_plane_units=default_plane_units,
        default_plane_method=default_plane_method,
        w_range_min_m_s=-w_range,
        w_range_max_m_s=w_range,
        w_range_method=("all_frames_p99_absolute_centered_w_rounded_up_0.1_m_s_with_0.5_m_s_floor"),
        wind_actual_level_m=wind_actual_level_m,
        wind_level_index=wind_level_index,
        perturbation_wind_reference_m_s=perturbation_reference,
        total_wind_reference_m_s=total_reference,
        provenance=_provenance(metadata, "trade_cumulus_updraft_lens_defaults"),
        caveats=[
            *time_caveats,
            "candidate_trade_cumulus_lens_not_a_supported_product",
            "fixed_scales_are_derived_from_this_result_only",
        ],
    )
    return _CachedDefaults(response=response, frames=tuple(frames))


def _select_default_time(
    metadata: ResultMetadata,
    frames: list[_FrameLocation],
    cwp_scores: list[float | None],
) -> tuple[int, str, list[str]]:
    eligible_scores = [
        (score, frame.global_index)
        for frame, score in zip(frames, cwp_scores, strict=True)
        if frame.time_seconds is not None
        and frame.time_seconds >= 10_800
        and score is not None
        and math.isfinite(score)
    ]
    if eligible_scores:
        best_score = max(score for score, _ in eligible_scores)
        best_index = min(index for score, index in eligible_scores if score == best_score)
        return best_index, "max_finite_domain_mean_cwp_at_or_after_10800_seconds", []

    diagnostic_index = _diagnostic_cloud_liquid_time_index(metadata, frames)
    if diagnostic_index is not None:
        return (
            diagnostic_index,
            "diagnostics_supported_time_of_max_cloud_liquid",
            ["domain_mean_cwp_default_unavailable"],
        )

    finite_times = [
        (frame.time_seconds, frame.global_index)
        for frame in frames
        if frame.time_seconds is not None and math.isfinite(frame.time_seconds)
    ]
    if finite_times:
        latest_time = max(time for time, _ in finite_times)
        final_three_hour_start = latest_time - 10_800
        final_frames = [
            (time, index) for time, index in finite_times if time >= final_three_hour_start
        ]
        if final_frames:
            selected_time = max(time for time, _ in final_frames)
            selected_index = min(index for time, index in final_frames if time == selected_time)
            return (
                selected_index,
                "latest_output_in_final_three_hours",
                ["domain_mean_cwp_and_supported_cloud_liquid_defaults_unavailable"],
            )
    return (
        frames[-1].global_index,
        "latest_available_output",
        ["output_times_and_science_defaults_unavailable"],
    )


def _diagnostic_cloud_liquid_time_index(
    metadata: ResultMetadata, frames: list[_FrameLocation]
) -> int | None:
    for field_name in ("ql", "qc"):
        field_default = metadata.default_time_by_field.get(field_name)
        if (
            field_default is not None
            and field_default.support_state == "supported"
            and field_default.time_index is not None
            and 0 <= field_default.time_index < len(frames)
        ):
            return field_default.time_index
    for record in metadata.interesting_times:
        record_time = record.time_seconds
        if (
            record.key == "max_qc"
            and record.support_state == "supported"
            and record_time is not None
        ):
            return min(
                frames,
                key=lambda frame: abs((frame.time_seconds or 0.0) - record_time),
            ).global_index
    return None


def _select_default_plane(ql: np.ndarray[Any, Any], w: np.ndarray[Any, Any]) -> tuple[int, str]:
    cloud_mask = np.isfinite(ql) & (ql >= CLOUD_THRESHOLD_KG_KG)
    structure = np.asarray([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8)
    ndimage = importlib.import_module("scipy.ndimage")
    scored: list[tuple[float, int]] = []
    coherent_sizes: list[tuple[int, int]] = []
    for y_index in range(ql.shape[1]):
        plane_mask = cloud_mask[:, y_index, :]
        labels, count = ndimage.label(plane_mask, structure=structure)
        plane_score = 0.0
        finite_component_score_found = False
        for label_index in range(1, count + 1):
            component = labels == label_index
            cell_count = int(np.count_nonzero(component))
            if cell_count < MIN_COHERENT_CLOUD_CELLS:
                continue
            coherent_sizes.append((cell_count, y_index))
            contribution = np.where(
                component,
                np.maximum(w[:, y_index, :], 0.0) * ql[:, y_index, :],
                0.0,
            )
            score = float(np.sum(contribution))
            if math.isfinite(score):
                plane_score += score
                finite_component_score_found = True
        if finite_component_score_found:
            scored.append((plane_score, y_index))
    if scored:
        best_score = max(score for score, _ in scored)
        return (
            min(y_index for score, y_index in scored if score == best_score),
            "greatest_coherent_positive_w_times_ql_score",
        )
    if coherent_sizes:
        largest = max(size for size, _ in coherent_sizes)
        return (
            min(y_index for size, y_index in coherent_sizes if size == largest),
            "largest_coherent_cloud_component_fallback",
        )
    return ql.shape[1] // 2, "domain_midpoint_fallback"


def _scalar_ql(dataset: Any, time_index: int) -> tuple[np.ndarray[Any, Any], tuple[str, str, str]]:
    if "ql" not in dataset.data_vars:
        raise TradeCumulusUpdraftLensError("Eligible result is missing required ql output.")
    data = _select_time(dataset["ql"], time_index)
    dimensions = _scalar_dimensions(data)
    values = np.asarray(data.transpose(*dimensions).values, dtype=float)
    return values, dimensions


def _center_w(
    dataset: Any,
    time_index: int,
    scalar_dimensions: tuple[str, str, str],
    scalar_shape: tuple[int, ...],
) -> np.ndarray[Any, Any]:
    if "w" not in dataset.data_vars:
        raise TradeCumulusUpdraftLensError("Eligible result is missing required w output.")
    data = _select_time(dataset["w"], time_index)
    vertical = _dimension_for_axis(data.dims, "z")
    y_dimension = _dimension_for_axis(data.dims, "y")
    x_dimension = _dimension_for_axis(data.dims, "x")
    values = np.asarray(data.transpose(vertical, y_dimension, x_dimension).values, dtype=float)
    if values.shape[1:] != scalar_shape[1:]:
        raise TradeCumulusUpdraftLensError("w horizontal grid does not match the ql scalar grid.")
    if values.shape[0] == scalar_shape[0] + 1:
        return np.asarray(0.5 * (values[:-1] + values[1:]), dtype=float)
    if values.shape[0] == scalar_shape[0]:
        return values
    raise TradeCumulusUpdraftLensError(
        "w vertical grid must match ql or have exactly one additional vertical face."
    )


def _center_horizontal_wind(
    dataset: Any,
    time_index: int,
    scalar_dimensions: tuple[str, str, str],
    scalar_shape: tuple[int, ...],
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    del scalar_dimensions
    if "u" not in dataset.data_vars or "v" not in dataset.data_vars:
        raise TradeCumulusUpdraftLensError("Eligible result is missing required u/v wind output.")
    u_data = _select_time(dataset["u"], time_index)
    v_data = _select_time(dataset["v"], time_index)
    u = _transpose_zyx(u_data)
    v = _transpose_zyx(v_data)
    if u.shape[0] != scalar_shape[0] or u.shape[1] != scalar_shape[1]:
        raise TradeCumulusUpdraftLensError("u vertical/y grid does not match ql.")
    if v.shape[0] != scalar_shape[0] or v.shape[2] != scalar_shape[2]:
        raise TradeCumulusUpdraftLensError("v vertical/x grid does not match ql.")
    if u.shape[2] == scalar_shape[2] + 1:
        u = 0.5 * (u[:, :, :-1] + u[:, :, 1:])
    elif u.shape[2] != scalar_shape[2]:
        raise TradeCumulusUpdraftLensError(
            "u x grid must match ql or have exactly one additional x face."
        )
    if v.shape[1] == scalar_shape[1] + 1:
        v = 0.5 * (v[:, :-1, :] + v[:, 1:, :])
    elif v.shape[1] != scalar_shape[1]:
        raise TradeCumulusUpdraftLensError(
            "v y grid must match ql or have exactly one additional y face."
        )
    return u, v


def _wind_vectors(
    u: np.ndarray[Any, Any],
    v: np.ndarray[Any, Any],
    x_km: np.ndarray[Any, Any],
    y_km: np.ndarray[Any, Any],
    z_km: float,
) -> list[UpdraftLensWindVector]:
    vectors: list[UpdraftLensWindVector] = []
    for y_index in range(0, u.shape[0], WIND_STRIDE):
        for x_index in range(0, u.shape[1], WIND_STRIDE):
            u_value = float(u[y_index, x_index])
            v_value = float(v[y_index, x_index])
            if not math.isfinite(u_value) or not math.isfinite(v_value):
                continue
            magnitude = math.hypot(u_value, v_value)
            if magnitude == 0:
                continue
            vectors.append(
                UpdraftLensWindVector(
                    x_km=float(x_km[x_index]),
                    y_km=float(y_km[y_index]),
                    z_km=z_km,
                    u_m_s=u_value,
                    v_m_s=v_value,
                    magnitude_m_s=magnitude,
                )
            )
    return vectors


def _source_paths(metadata: ResultMetadata) -> list[Path]:
    raw_paths = metadata.model_output_paths or metadata.netcdf_paths
    paths = [Path(path).expanduser() for path in raw_paths]
    if not paths:
        raise TradeCumulusUpdraftLensError("No NetCDF model-output paths are available.")
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise TradeCumulusUpdraftLensError(f"Model-output file is unavailable: {missing[0].name}")
    return paths


def _path_state(path: Path) -> tuple[str, int, int]:
    stat = path.stat()
    return str(path), stat.st_size, stat.st_mtime_ns


def _open_dataset(path: Path) -> Any:
    xarray = importlib.import_module("xarray")
    try:
        return xarray.open_dataset(path, decode_times=False)
    except Exception as exc:
        raise TradeCumulusUpdraftLensError(
            f"Could not open model-output file {path.name}: {exc}"
        ) from exc


def _time_count(dataset: Any) -> int:
    for candidate in ("time", "mtime", "t"):
        if candidate in dataset.sizes:
            return int(dataset.sizes[candidate])
    return 1


def _select_time(data_array: Any, index: int) -> Any:
    for candidate in ("time", "mtime", "t"):
        if candidate in data_array.dims:
            return data_array.isel({candidate: index})
    if index != 0:
        raise TradeCumulusUpdraftLensError("Source field has no selectable time dimension.")
    return data_array


def _time_seconds(
    dataset: Any, local_index: int, metadata: ResultMetadata, global_index: int
) -> float | None:
    for candidate in ("time", "mtime", "t"):
        if candidate in dataset.coords:
            values = np.asarray(dataset.coords[candidate].values).reshape(-1)
            if local_index < values.size:
                return _finite_float(values[local_index])
    if (
        metadata.first_output_time_seconds is not None
        and metadata.last_output_time_seconds is not None
    ):
        count = max(1, (metadata.time_steps or 1) - 1)
        fraction = min(global_index, count) / count
        return metadata.first_output_time_seconds + fraction * (
            metadata.last_output_time_seconds - metadata.first_output_time_seconds
        )
    return None


def _domain_mean_cwp(dataset: Any, local_index: int) -> float | None:
    if "cwp" not in dataset.data_vars:
        return None
    values = np.asarray(_select_time(dataset["cwp"], local_index).values, dtype=float)
    finite = values[np.isfinite(values)]
    return float(np.mean(finite)) if finite.size else None


def _scalar_dimensions(data_array: Any) -> tuple[str, str, str]:
    return (
        _dimension_for_axis(data_array.dims, "z"),
        _dimension_for_axis(data_array.dims, "y"),
        _dimension_for_axis(data_array.dims, "x"),
    )


def _dimension_for_axis(dimensions: tuple[str, ...], axis: str) -> str:
    candidates = {
        "z": ("zh", "zf", "z", "height", "height_m", "height_km"),
        "y": ("yh", "yf", "y"),
        "x": ("xh", "xf", "x"),
    }[axis]
    for candidate in candidates:
        if candidate in dimensions:
            return candidate
    raise TradeCumulusUpdraftLensError(f"Field is missing a supported {axis} dimension.")


def _transpose_zyx(data_array: Any) -> np.ndarray[Any, Any]:
    dimensions = (
        _dimension_for_axis(data_array.dims, "z"),
        _dimension_for_axis(data_array.dims, "y"),
        _dimension_for_axis(data_array.dims, "x"),
    )
    return np.asarray(data_array.transpose(*dimensions).values, dtype=float)


def _coordinate_values(dataset: Any, name: str, expected_size: int) -> np.ndarray[Any, Any]:
    if name not in dataset.coords:
        return np.arange(expected_size, dtype=float)
    values = np.asarray(dataset.coords[name].values, dtype=float).reshape(-1)
    if values.size != expected_size:
        raise TradeCumulusUpdraftLensError(f"Coordinate {name} does not match its field dimension.")
    return values


def _coordinate_as(
    dataset: Any, name: str, target_units: Literal["m", "km"], expected_size: int
) -> np.ndarray[Any, Any]:
    values = _coordinate_values(dataset, name, expected_size)
    return _values_as(values, _coordinate_units(dataset, name), target_units)


def _values_as(
    values: np.ndarray[Any, Any],
    source_units: str | None,
    target_units: Literal["m", "km"],
) -> np.ndarray[Any, Any]:
    normalized = (source_units or "").strip().lower()
    if target_units == "m" and normalized in {"km", "kilometer", "kilometers"}:
        return values * 1000.0
    if target_units == "km" and normalized in {"m", "meter", "meters"}:
        return values / 1000.0
    return values


def _coordinate_units(dataset: Any, name: str) -> str | None:
    if name not in dataset.coords:
        return None
    units = dataset.coords[name].attrs.get("units")
    return str(units) if units is not None else None


def _rounded_reference(
    arrays: list[np.ndarray[Any, Any]], percentile: float, minimum: float
) -> float:
    if not arrays:
        return minimum
    values = np.concatenate(arrays)
    if not values.size:
        return minimum
    selected = float(np.percentile(values, percentile))
    if not math.isfinite(selected):
        return minimum
    rounded = math.ceil(selected / W_ROUNDING_M_S - 1e-12) * W_ROUNDING_M_S
    return max(minimum, round(rounded, 10))


def _finite_mean(values: np.ndarray[Any, Any]) -> float:
    finite = values[np.isfinite(values)]
    return float(np.mean(finite)) if finite.size else 0.0


def _finite_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _json_float_matrix(values: np.ndarray[Any, Any]) -> list[list[float | None]]:
    return [[_finite_float(value) for value in row] for row in np.asarray(values).tolist()]


def _provenance(metadata: ResultMetadata, product: str) -> UpdraftLensProvenance:
    return UpdraftLensProvenance(
        source_model=metadata.source_model,
        result_id=metadata.result_id,
        run_id=metadata.run_id,
        scenario_id=metadata.scenario_id,
        processing_method=f"backend_xarray_{product}",
        rendering_method="json_native_grid_trade_cumulus_updraft_lens",
        provenance_label=(
            "CM1-derived Trade Cumulus candidate Lens; native scalar grid; no interpolation"
        ),
    )
