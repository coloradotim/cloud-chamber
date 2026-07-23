"""Selected-region diagnostics for Thermal Fate Inspector payloads.

The browser sends a bounded region request. This module opens CM1 NetCDF on the
backend, slices native-grid fields, and returns small diagnostic summaries.
"""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.result_diagnostics import (
    QC_CLOUD_THRESHOLD_KG_KG,
    QR_RAIN_THRESHOLD_KG_KG,
    TimeValue,
)
from cloud_chamber.result_ingest import get_result_metadata
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.visualization_data import (
    ProvenancePayload,
    VisualizationDataError,
    _close_all,
    _coordinate_units,
    _coordinate_values,
    _field_dimensions,
    _open_dataset_for_time,
    _open_dataset_sequence,
    _provenance,
    _time_value_seconds,
)

RegionType = Literal["point", "column", "box"]
ThermalFateConfidence = Literal[
    "supported", "candidate", "insufficient_evidence", "unsupported_missing_fields"
]


class SelectedRegionError(RuntimeError):
    """Raised when selected-region diagnostics cannot be produced."""


class SelectedRegionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region_type: RegionType
    x_index: int | None = None
    y_index: int | None = None
    z_index: int | None = None
    x_start: int | None = None
    x_end: int | None = None
    y_start: int | None = None
    y_end: int | None = None
    z_start: int | None = None
    z_end: int | None = None
    neighborhood: int = 0


class AxisSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: str
    start_index: int
    end_index: int
    start_coordinate: float | str | None = None
    end_coordinate: float | str | None = None
    units: str | None = None


class RegionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region_type: RegionType
    requested: SelectedRegionRequest
    x: AxisSelection | None = None
    y: AxisSelection | None = None
    vertical: AxisSelection | None = None
    native_grid: str | None = None
    cell_count: int | None = None


class LocalDiagnosticSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    available: bool = True
    local_max_w_m_s: float | None = None
    time_of_local_max_w_seconds: float | None = None
    local_min_w_m_s: float | None = None
    time_of_local_min_w_seconds: float | None = None
    local_w_max_time_series: list[TimeValue] = Field(default_factory=list)
    local_w_min_time_series: list[TimeValue] = Field(default_factory=list)
    local_max_qc_kg_kg: float | None = None
    time_of_local_max_qc_seconds: float | None = None
    first_local_cloud_time_seconds: float | None = None
    local_cloud_fraction_time_series: list[TimeValue] = Field(default_factory=list)
    local_qc_max_time_series: list[TimeValue] = Field(default_factory=list)
    local_cloud_base_time_series: list[TimeValue] = Field(default_factory=list)
    local_cloud_top_time_series: list[TimeValue] = Field(default_factory=list)
    local_max_qc_height_time_series: list[TimeValue] = Field(default_factory=list)
    local_max_w_height_time_series: list[TimeValue] = Field(default_factory=list)
    local_rain_present: bool = False
    first_local_rain_time_seconds: float | None = None
    local_max_qr_kg_kg: float | None = None
    time_of_local_max_qr_seconds: float | None = None
    local_qr_max_time_series: list[TimeValue] = Field(default_factory=list)


class DomainComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_max_w_fraction_of_domain: float | None = None
    local_max_qc_fraction_of_domain: float | None = None
    local_first_cloud_time_delta_seconds: float | None = None
    local_cloud_top_fraction_of_domain: float | None = None
    local_first_rain_time_delta_seconds: float | None = None
    caveats: list[str] = Field(default_factory=list)


class SelectedRegionInterpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thermal_fate_label: str
    confidence: ThermalFateConfidence
    main_limiting_factor: str = "unknown"
    summary: str
    caveats: list[str] = Field(default_factory=list)


class SelectedRegionDiagnosticsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    region: RegionMetadata
    diagnostics: LocalDiagnosticSummary
    comparison_to_domain: DomainComparison
    interpretation: SelectedRegionInterpretation
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


def selected_region_diagnostics(
    settings: CloudChamberSettings,
    result_id: str,
    request: SelectedRegionRequest,
) -> SelectedRegionDiagnosticsResponse:
    """Return bounded local diagnostics for a selected native-grid region."""

    if request.neighborhood < 0:
        raise SelectedRegionError("neighborhood must be greater than or equal to 0.")

    metadata = get_result_metadata(settings, result_id)
    if _has_one_file_per_time(metadata):
        try:
            return _selected_region_diagnostics_from_files(metadata, request)
        except VisualizationDataError as exc:
            raise SelectedRegionError(str(exc)) from exc

    dataset, close_datasets = _open_dataset_sequence(metadata)
    try:
        caveats = list(metadata.warnings)
        cloud_liquid_field = _cloud_liquid_field(dataset)
        if cloud_liquid_field is None:
            caveats.append("missing_qc_field")
        if "w" not in dataset.data_vars:
            caveats.append("missing_w_field")

        reference_field = cloud_liquid_field or ("w" if "w" in dataset.data_vars else None)
        if reference_field is None:
            raise SelectedRegionError("Selected-region diagnostics require qc or w fields.")
        region = _region_metadata(dataset, request, reference_field)
        diagnostics = _local_diagnostics(dataset, request, caveats)
        comparison = _comparison_to_domain(metadata, diagnostics)
        interpretation = _interpret_region(diagnostics, caveats)
        return _selected_region_response(
            metadata,
            region,
            diagnostics,
            comparison,
            interpretation,
            caveats,
        )
    except VisualizationDataError as exc:
        raise SelectedRegionError(str(exc)) from exc
    finally:
        _close_all(close_datasets)


def _has_one_file_per_time(metadata: Any) -> bool:
    return (
        metadata.time_steps is not None
        and metadata.time_steps > 1
        and len(metadata.model_output_paths) == metadata.time_steps
    )


def _selected_region_diagnostics_from_files(
    metadata: Any,
    request: SelectedRegionRequest,
) -> SelectedRegionDiagnosticsResponse:
    caveats = list(metadata.warnings)
    diagnostics = LocalDiagnosticSummary()
    region: RegionMetadata | None = None

    for time_index in range(int(metadata.time_steps or 0)):
        dataset, close_datasets, _ = _open_dataset_for_time(metadata, time_index)
        try:
            if region is None:
                cloud_liquid_field = _cloud_liquid_field(dataset)
                reference_field = cloud_liquid_field or ("w" if "w" in dataset.data_vars else None)
                if reference_field is None:
                    raise SelectedRegionError("Selected-region diagnostics require qc or w fields.")
                region = _region_metadata(dataset, request, reference_field)
                if cloud_liquid_field is None:
                    caveats.append("missing_qc_field")
                if "w" not in dataset.data_vars:
                    caveats.append("missing_w_field")
            _merge_local_diagnostics(
                diagnostics,
                _local_diagnostics(dataset, request, caveats),
            )
        finally:
            _close_all(close_datasets)

    if region is None:
        raise SelectedRegionError("Selected-region diagnostics found no retained model output.")
    comparison = _comparison_to_domain(metadata, diagnostics)
    interpretation = _interpret_region(diagnostics, caveats)
    return _selected_region_response(
        metadata,
        region,
        diagnostics,
        comparison,
        interpretation,
        caveats,
    )


def _merge_local_diagnostics(
    target: LocalDiagnosticSummary,
    source: LocalDiagnosticSummary,
) -> None:
    target.available = target.available and source.available
    target.local_w_max_time_series.extend(source.local_w_max_time_series)
    target.local_w_min_time_series.extend(source.local_w_min_time_series)
    target.local_qc_max_time_series.extend(source.local_qc_max_time_series)
    target.local_cloud_fraction_time_series.extend(source.local_cloud_fraction_time_series)
    target.local_cloud_base_time_series.extend(source.local_cloud_base_time_series)
    target.local_cloud_top_time_series.extend(source.local_cloud_top_time_series)
    target.local_max_qc_height_time_series.extend(source.local_max_qc_height_time_series)
    target.local_max_w_height_time_series.extend(source.local_max_w_height_time_series)
    target.local_qr_max_time_series.extend(source.local_qr_max_time_series)

    if source.local_max_w_m_s is not None and (
        target.local_max_w_m_s is None or source.local_max_w_m_s > target.local_max_w_m_s
    ):
        target.local_max_w_m_s = source.local_max_w_m_s
        target.time_of_local_max_w_seconds = source.time_of_local_max_w_seconds
    if source.local_min_w_m_s is not None and (
        target.local_min_w_m_s is None or source.local_min_w_m_s < target.local_min_w_m_s
    ):
        target.local_min_w_m_s = source.local_min_w_m_s
        target.time_of_local_min_w_seconds = source.time_of_local_min_w_seconds
    if source.local_max_qc_kg_kg is not None and (
        target.local_max_qc_kg_kg is None or source.local_max_qc_kg_kg > target.local_max_qc_kg_kg
    ):
        target.local_max_qc_kg_kg = source.local_max_qc_kg_kg
        target.time_of_local_max_qc_seconds = source.time_of_local_max_qc_seconds
    if (
        target.first_local_cloud_time_seconds is None
        and source.first_local_cloud_time_seconds is not None
    ):
        target.first_local_cloud_time_seconds = source.first_local_cloud_time_seconds
    if source.local_max_qr_kg_kg is not None and (
        target.local_max_qr_kg_kg is None or source.local_max_qr_kg_kg > target.local_max_qr_kg_kg
    ):
        target.local_max_qr_kg_kg = source.local_max_qr_kg_kg
        target.time_of_local_max_qr_seconds = source.time_of_local_max_qr_seconds
    target.local_rain_present = target.local_rain_present or source.local_rain_present
    if (
        target.first_local_rain_time_seconds is None
        and source.first_local_rain_time_seconds is not None
    ):
        target.first_local_rain_time_seconds = source.first_local_rain_time_seconds


def _selected_region_response(
    metadata: Any,
    region: RegionMetadata,
    diagnostics: LocalDiagnosticSummary,
    comparison: DomainComparison,
    interpretation: SelectedRegionInterpretation,
    caveats: list[str],
) -> SelectedRegionDiagnosticsResponse:
    return SelectedRegionDiagnosticsResponse(
        result_id=metadata.result_id,
        run_id=metadata.run_id,
        scenario_id=metadata.scenario_id,
        region=region,
        diagnostics=diagnostics,
        comparison_to_domain=comparison,
        interpretation=interpretation,
        provenance=_provenance(
            metadata,
            processing_method="backend_xarray_selected_region_diagnostics",
            rendering_method="thermal_fate_inspector_summary",
            provenance_label=(
                "CM1-derived selected-region diagnostics; native-grid summary; "
                "browser receives bounded payload only"
            ),
        ),
        caveats=_dedupe(
            [
                *caveats,
                "native_grid_region_summary_no_interpolation",
                "selected_region_is_not_cloud_object_tracking",
            ]
        ),
    )


def _local_diagnostics(
    dataset: Any,
    request: SelectedRegionRequest,
    caveats: list[str],
) -> LocalDiagnosticSummary:
    summary = LocalDiagnosticSummary()
    cloud_liquid_field = _cloud_liquid_field(dataset)
    if cloud_liquid_field is not None:
        _add_qc_summary(dataset, cloud_liquid_field, request, summary, caveats)
    else:
        summary.available = False
    if "w" in dataset.data_vars:
        _add_w_summary(dataset, request, summary, caveats)
    else:
        summary.available = False
    if "qr" in dataset.data_vars:
        _add_qr_summary(dataset, request, summary, caveats)
    return summary


def _add_qc_summary(
    dataset: Any,
    field_name: str,
    request: SelectedRegionRequest,
    summary: LocalDiagnosticSummary,
    caveats: list[str],
) -> None:
    data_array = dataset[field_name]
    dims = _field_dimensions(data_array)
    if not dims.time or not dims.vertical or not dims.y or not dims.x:
        summary.available = False
        caveats.append("local_qc_missing_required_dimensions")
        return
    selection = _selection_for_field(dataset, data_array, request)
    max_value: float | None = None
    max_time: float | None = None
    for time_index in range(int(data_array.sizes[dims.time])):
        time_seconds = _time_value_seconds(dataset, dims.time, time_index)
        region = data_array.isel({dims.time: time_index, **selection})
        finite_values, non_finite = _finite_values(region)
        if non_finite:
            caveats.append("non_finite_values_detected_in_local_qc")
        slice_max = max(finite_values) if finite_values else None
        cloudy_count = sum(1 for value in finite_values if value >= QC_CLOUD_THRESHOLD_KG_KG)
        cloud_fraction = cloudy_count / len(finite_values) if finite_values else None
        cloud_base, cloud_top = _local_base_top(region, dims.vertical, dataset, caveats)
        max_height = _height_of_local_max(region, dims.vertical, dataset)
        summary.local_qc_max_time_series.append(
            TimeValue(time_seconds=time_seconds, value=slice_max)
        )
        summary.local_cloud_fraction_time_series.append(
            TimeValue(time_seconds=time_seconds, value=cloud_fraction)
        )
        summary.local_cloud_base_time_series.append(
            TimeValue(time_seconds=time_seconds, value=cloud_base)
        )
        summary.local_cloud_top_time_series.append(
            TimeValue(time_seconds=time_seconds, value=cloud_top)
        )
        summary.local_max_qc_height_time_series.append(
            TimeValue(time_seconds=time_seconds, value=max_height)
        )
        if cloudy_count >= 1 and summary.first_local_cloud_time_seconds is None:
            summary.first_local_cloud_time_seconds = time_seconds
        if slice_max is not None and (max_value is None or slice_max > max_value):
            max_value = slice_max
            max_time = time_seconds
    summary.local_max_qc_kg_kg = max_value
    summary.time_of_local_max_qc_seconds = max_time


def _cloud_liquid_field(dataset: Any) -> str | None:
    for field_name in ("qc", "ql"):
        if field_name in dataset.data_vars:
            return field_name
    return None


def _add_w_summary(
    dataset: Any,
    request: SelectedRegionRequest,
    summary: LocalDiagnosticSummary,
    caveats: list[str],
) -> None:
    data_array = dataset["w"]
    dims = _field_dimensions(data_array)
    if not dims.time or not dims.vertical or not dims.y or not dims.x:
        summary.available = False
        caveats.append("local_w_missing_required_dimensions")
        return
    selection = _selection_for_field(dataset, data_array, request)
    max_value: float | None = None
    max_time: float | None = None
    min_value: float | None = None
    min_time: float | None = None
    for time_index in range(int(data_array.sizes[dims.time])):
        time_seconds = _time_value_seconds(dataset, dims.time, time_index)
        region = data_array.isel({dims.time: time_index, **selection})
        finite_values, non_finite = _finite_values(region)
        if non_finite:
            caveats.append("non_finite_values_detected_in_local_w")
        slice_max = max(finite_values) if finite_values else None
        slice_min = min(finite_values) if finite_values else None
        summary.local_w_max_time_series.append(
            TimeValue(time_seconds=time_seconds, value=slice_max)
        )
        summary.local_w_min_time_series.append(
            TimeValue(time_seconds=time_seconds, value=slice_min)
        )
        summary.local_max_w_height_time_series.append(
            TimeValue(
                time_seconds=time_seconds,
                value=_height_of_local_max(region, dims.vertical, dataset),
            )
        )
        if slice_max is not None and (max_value is None or slice_max > max_value):
            max_value = slice_max
            max_time = time_seconds
        if slice_min is not None and (min_value is None or slice_min < min_value):
            min_value = slice_min
            min_time = time_seconds
    summary.local_max_w_m_s = max_value
    summary.time_of_local_max_w_seconds = max_time
    summary.local_min_w_m_s = min_value
    summary.time_of_local_min_w_seconds = min_time


def _add_qr_summary(
    dataset: Any,
    request: SelectedRegionRequest,
    summary: LocalDiagnosticSummary,
    caveats: list[str],
) -> None:
    data_array = dataset["qr"]
    dims = _field_dimensions(data_array)
    if not dims.time or not dims.vertical or not dims.y or not dims.x:
        caveats.append("local_qr_missing_required_dimensions")
        return
    selection = _selection_for_field(dataset, data_array, request)
    max_value: float | None = None
    max_time: float | None = None
    for time_index in range(int(data_array.sizes[dims.time])):
        time_seconds = _time_value_seconds(dataset, dims.time, time_index)
        region = data_array.isel({dims.time: time_index, **selection})
        finite_values, non_finite = _finite_values(region)
        if non_finite:
            caveats.append("non_finite_values_detected_in_local_qr")
        slice_max = max(finite_values) if finite_values else None
        summary.local_qr_max_time_series.append(
            TimeValue(time_seconds=time_seconds, value=slice_max)
        )
        if any(value >= QR_RAIN_THRESHOLD_KG_KG for value in finite_values):
            summary.local_rain_present = True
            if summary.first_local_rain_time_seconds is None:
                summary.first_local_rain_time_seconds = time_seconds
        if slice_max is not None and (max_value is None or slice_max > max_value):
            max_value = slice_max
            max_time = time_seconds
    summary.local_max_qr_kg_kg = max_value
    summary.time_of_local_max_qr_seconds = max_time


def _selection_for_field(
    dataset: Any,
    data_array: Any,
    request: SelectedRegionRequest,
) -> dict[str, slice]:
    dims = _field_dimensions(data_array)
    if not dims.vertical or not dims.y or not dims.x:
        raise SelectedRegionError(f"Field {data_array.name} lacks native spatial dimensions.")
    y_size = int(data_array.sizes[dims.y])
    x_size = int(data_array.sizes[dims.x])
    z_size = int(data_array.sizes[dims.vertical])
    y_start, y_end, x_start, x_end = _horizontal_bounds(request, y_size, x_size)
    if request.region_type == "point":
        if request.z_index is None:
            raise SelectedRegionError("point regions require z_index.")
        z_start, z_end = _neighborhood_bounds(
            request.z_index, request.neighborhood, z_size, "z_index"
        )
    elif request.region_type == "column":
        z_start, z_end = 0, z_size - 1
    elif request.region_type == "box":
        z_start, z_end = _box_bounds(request.z_start, request.z_end, z_size, "z")
    else:
        raise SelectedRegionError(f"Unsupported region_type: {request.region_type}")
    return {
        dims.vertical: slice(z_start, z_end + 1),
        dims.y: slice(y_start, y_end + 1),
        dims.x: slice(x_start, x_end + 1),
    }


def _horizontal_bounds(
    request: SelectedRegionRequest,
    y_size: int,
    x_size: int,
) -> tuple[int, int, int, int]:
    if request.region_type in {"point", "column"}:
        if request.x_index is None or request.y_index is None:
            raise SelectedRegionError(f"{request.region_type} regions require x_index and y_index.")
        y_start, y_end = _neighborhood_bounds(
            request.y_index,
            request.neighborhood,
            y_size,
            "y_index",
        )
        x_start, x_end = _neighborhood_bounds(
            request.x_index,
            request.neighborhood,
            x_size,
            "x_index",
        )
        return y_start, y_end, x_start, x_end
    if request.region_type == "box":
        x_start, x_end = _box_bounds(request.x_start, request.x_end, x_size, "x")
        y_start, y_end = _box_bounds(request.y_start, request.y_end, y_size, "y")
        return y_start, y_end, x_start, x_end
    raise SelectedRegionError(f"Unsupported region_type: {request.region_type}")


def _neighborhood_bounds(index: int, radius: int, size: int, label: str) -> tuple[int, int]:
    _validate_raw_index(index, size, label)
    return max(0, index - radius), min(size - 1, index + radius)


def _box_bounds(start: int | None, end: int | None, size: int, label: str) -> tuple[int, int]:
    if start is None or end is None:
        raise SelectedRegionError(f"box regions require {label}_start and {label}_end.")
    _validate_raw_index(start, size, f"{label}_start")
    _validate_raw_index(end, size, f"{label}_end")
    if end < start:
        raise SelectedRegionError(f"{label}_end must be greater than or equal to {label}_start.")
    return start, end


def _validate_raw_index(index: int, size: int, label: str) -> None:
    if index < 0 or index >= size:
        raise SelectedRegionError(f"{label}={index} is outside valid range 0..{size - 1}.")


def _region_metadata(
    dataset: Any,
    request: SelectedRegionRequest,
    reference_field: str,
) -> RegionMetadata:
    data_array = dataset[reference_field]
    dims = _field_dimensions(data_array)
    selection = _selection_for_field(dataset, data_array, request)
    vertical_selection = _axis_selection(dataset, str(dims.vertical), selection[str(dims.vertical)])
    y_selection = _axis_selection(dataset, str(dims.y), selection[str(dims.y)])
    x_selection = _axis_selection(dataset, str(dims.x), selection[str(dims.x)])
    cell_count = (
        (vertical_selection.end_index - vertical_selection.start_index + 1)
        * (y_selection.end_index - y_selection.start_index + 1)
        * (x_selection.end_index - x_selection.start_index + 1)
    )
    return RegionMetadata(
        region_type=request.region_type,
        requested=request,
        x=x_selection,
        y=y_selection,
        vertical=vertical_selection,
        native_grid="/".join(str(dimension) for dimension in (dims.vertical, dims.y, dims.x)),
        cell_count=cell_count,
    )


def _axis_selection(dataset: Any, dimension: str, selected: slice) -> AxisSelection:
    start = int(selected.start or 0)
    end = int((selected.stop or start + 1) - 1)
    values = _coordinate_values(dataset, dimension)
    return AxisSelection(
        dimension=dimension,
        start_index=start,
        end_index=end,
        start_coordinate=values[start] if start < len(values) else None,
        end_coordinate=values[end] if end < len(values) else None,
        units=_coordinate_units(dataset, dimension),
    )


def _finite_values(data_array: Any) -> tuple[list[float], int]:
    finite_values: list[float] = []
    non_finite_count = 0
    for raw_value in data_array.values.reshape(-1).tolist():
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            non_finite_count += 1
            continue
        if math.isfinite(value):
            finite_values.append(value)
        else:
            non_finite_count += 1
    return finite_values, non_finite_count


def _local_base_top(
    data_array: Any,
    vertical_dimension: str,
    dataset: Any,
    caveats: list[str],
) -> tuple[float | None, float | None]:
    values = data_array.values
    if vertical_dimension not in data_array.dims:
        return None, None
    vertical_axis = data_array.dims.index(vertical_dimension)
    active_levels: list[int] = []
    for native_index in _indices_for_shape(data_array.shape):
        try:
            value = float(values[native_index])
        except (TypeError, ValueError):
            continue
        if math.isfinite(value) and value >= QC_CLOUD_THRESHOLD_KG_KG:
            active_levels.append(int(native_index[vertical_axis]))
    if not active_levels:
        return None, None
    coordinate_values = _coordinate_values(dataset, vertical_dimension)
    heights = [_coordinate_float(coordinate_values, level) for level in active_levels]
    units = _coordinate_units(dataset, vertical_dimension)
    if units and units.lower() in {"km", "kilometer", "kilometers"}:
        heights = [height * 1000.0 for height in heights]
    elif units and units.lower() not in {"m", "meter", "meters"}:
        caveats.append(f"local_cloud_base_top_vertical_units_not_meters:{units}")
    return min(heights), max(heights)


def _height_of_local_max(data_array: Any, vertical_dimension: str, dataset: Any) -> float | None:
    values = data_array.values
    if vertical_dimension not in data_array.dims:
        return None
    vertical_axis = data_array.dims.index(vertical_dimension)
    best_value: float | None = None
    best_level: int | None = None
    for native_index in _indices_for_shape(data_array.shape):
        try:
            value = float(values[native_index])
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value):
            continue
        if best_value is None or value > best_value:
            best_value = value
            best_level = int(native_index[vertical_axis])
    if best_level is None:
        return None
    coordinate_values = _coordinate_values(dataset, vertical_dimension)
    height = _coordinate_float(coordinate_values, best_level)
    units = _coordinate_units(dataset, vertical_dimension)
    if units and units.lower() in {"km", "kilometer", "kilometers"}:
        return height * 1000.0
    return height


def _indices_for_shape(shape: tuple[int, ...]) -> list[tuple[int, ...]]:
    ranges = [range(int(size)) for size in shape]
    if not ranges:
        return [()]
    indices: list[tuple[int, ...]] = [()]
    for axis_range in ranges:
        indices = [(*prefix, index) for prefix in indices for index in axis_range]
    return indices


def _coordinate_float(values: list[float | str | None], index: int) -> float:
    if index < len(values):
        try:
            value = values[index]
            return float(value) if value is not None else float(index)
        except (TypeError, ValueError):
            return float(index)
    return float(index)


def _comparison_to_domain(
    metadata: Any,
    local: LocalDiagnosticSummary,
) -> DomainComparison:
    caveats: list[str] = []
    diagnostics = metadata.diagnostics
    if diagnostics is None:
        return DomainComparison(caveats=["domain_diagnostics_unavailable"])
    cloud = diagnostics.cloud
    vertical = diagnostics.vertical_velocity
    rain = diagnostics.rain
    return DomainComparison(
        local_max_w_fraction_of_domain=_safe_ratio(local.local_max_w_m_s, vertical.max_w_m_s),
        local_max_qc_fraction_of_domain=_safe_ratio(local.local_max_qc_kg_kg, cloud.max_qc_kg_kg),
        local_first_cloud_time_delta_seconds=_safe_delta(
            local.first_local_cloud_time_seconds,
            cloud.first_cloud_time_seconds,
        ),
        local_cloud_top_fraction_of_domain=_safe_ratio(
            _last_non_null(local.local_cloud_top_time_series),
            cloud.cloud_top_m,
        ),
        local_first_rain_time_delta_seconds=_safe_delta(
            local.first_local_rain_time_seconds,
            rain.first_rain_time_seconds,
        ),
        caveats=caveats,
    )


def _interpret_region(
    diagnostics: LocalDiagnosticSummary,
    caveats: list[str],
) -> SelectedRegionInterpretation:
    has_w = diagnostics.local_max_w_m_s is not None
    has_qc = diagnostics.local_max_qc_kg_kg is not None
    if not has_w or not has_qc:
        return SelectedRegionInterpretation(
            thermal_fate_label="Insufficient evidence",
            confidence="unsupported_missing_fields",
            summary="Selected-region label unavailable because local qc or w is missing.",
            caveats=_dedupe(caveats),
        )
    local_max_w = diagnostics.local_max_w_m_s
    meaningful_w = local_max_w is not None and local_max_w >= 0.5
    cloud = diagnostics.first_local_cloud_time_seconds is not None
    if not meaningful_w and not cloud:
        return SelectedRegionInterpretation(
            thermal_fate_label="No meaningful thermal",
            confidence="supported",
            summary="No meaningful local updraft or cloud-water signal was detected.",
            caveats=_dedupe(caveats),
        )
    if meaningful_w and not cloud:
        return SelectedRegionInterpretation(
            thermal_fate_label="Thermal without cloud",
            confidence="supported",
            main_limiting_factor="moisture",
            summary="Local updraft occurred, but local cloud water stayed below threshold.",
            caveats=_dedupe([*caveats, "moisture_limitation_inferred_without_saturation_deficit"]),
        )
    if cloud and _brief_cloud(diagnostics.local_cloud_fraction_time_series):
        return SelectedRegionInterpretation(
            thermal_fate_label="Brief / diluted cloud",
            confidence="candidate",
            main_limiting_factor="dilution/entrainment",
            summary="Local cloud water appeared briefly or weakly before fading.",
            caveats=_dedupe([*caveats, "brief_cloud_is_proxy_without_entrainment_diagnostics"]),
        )
    if cloud and _cloud_top_increases(diagnostics.local_cloud_top_time_series):
        return SelectedRegionInterpretation(
            thermal_fate_label="Growing cumulus",
            confidence="candidate",
            summary="Local cloud formed and local cloud-top height increased over time.",
            caveats=_dedupe(caveats),
        )
    return SelectedRegionInterpretation(
        thermal_fate_label="Fair-weather cumulus",
        confidence="candidate",
        summary="Local cloud formed with available updraft and cloud-water diagnostics.",
        caveats=_dedupe(caveats),
    )


def _brief_cloud(series: list[TimeValue]) -> bool:
    cloudy = [item.value for item in series if item.value is not None and item.value > 0.0]
    return len(cloudy) == 1 or (len(cloudy) > 1 and cloudy[-1] == 0.0 and max(cloudy) < 0.25)


def _cloud_top_increases(series: list[TimeValue]) -> bool:
    values = [item.value for item in series if item.value is not None]
    return len(values) >= 2 and values[-1] > values[0]


def _safe_ratio(local: float | None, domain: float | None) -> float | None:
    if local is None or domain is None or domain == 0:
        return None
    return local / domain


def _safe_delta(local: float | None, domain: float | None) -> float | None:
    if local is None or domain is None:
        return None
    return local - domain


def _last_non_null(series: list[TimeValue]) -> float | None:
    for item in reversed(series):
        if item.value is not None:
            return item.value
    return None


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
