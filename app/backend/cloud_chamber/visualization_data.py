"""Visualization-ready CM1 field data contracts.

This module keeps raw NetCDF/xarray access on the backend. Frontend inspectors
and visualizers receive small, provenance-labeled payloads rather than parsing
CM1 output directly in the browser.
"""

from __future__ import annotations

import importlib
import itertools
import math
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.result_ingest import (
    ResultMetadata,
    get_result_metadata,
)
from cloud_chamber.settings import CloudChamberSettings

VisualizationOrientation = Literal["horizontal", "vertical_x", "vertical_y"]
VisualizationEncoding = Literal["json"]

FIELD_DEFINITIONS: dict[str, tuple[str, str]] = {
    "qc": ("cloud_water", "Cloud water"),
    "w": ("vertical_velocity", "Vertical velocity"),
    "qr": ("rain_water", "Rain water"),
    "rain": ("accumulated_surface_rain", "Accumulated surface rain"),
    "dbz": ("reflectivity", "Reflectivity"),
}

TIME_DIMENSION_CANDIDATES = ("time", "mtime", "t")
VERTICAL_DIMENSION_CANDIDATES = ("zh", "zf", "z", "height", "height_m", "height_km")
Y_DIMENSION_CANDIDATES = ("yh", "y")
X_DIMENSION_CANDIDATES = ("xh", "x")


class VisualizationDataError(RuntimeError):
    """Raised when a visualization-ready payload cannot be produced."""


class ProvenancePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_model: str
    result_id: str
    run_id: str
    scenario_id: str
    source_product_state: str
    result_state: str
    processing_method: str
    rendering_method: str
    provenance_label: str


class FieldCoordinateMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time: str | None = None
    vertical: str | None = None
    y: str | None = None
    x: str | None = None


class VisualizableField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_field_name: str
    canonical_field_name: str
    display_name: str
    units: str | None = None
    dimensions: list[str]
    shape: list[int]
    native_grid: str
    coordinate_names: FieldCoordinateMetadata
    time_coordinate_values: list[float | str | None] = Field(default_factory=list)
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


class FieldCatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    source_model: str
    available_fields: list[VisualizableField]
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


class SliceSelectionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_index: int
    time_seconds: float | None = None
    orientation: VisualizationOrientation
    selected_dimension: str
    selected_index: int
    selected_coordinate_value: float | str | None = None
    level_units: str | None = None
    level_coordinate_value: float | str | None = None
    level_meters: float | None = None


class SliceStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: float | None = None
    max: float | None = None
    mean: float | None = None
    finite_count: int
    non_finite_count: int


class SliceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    field: VisualizableField
    selection: SliceSelectionMetadata
    coordinate_units: dict[str, str | None] = Field(default_factory=dict)
    shape: list[int]
    dimension_order: list[str]
    data_encoding: VisualizationEncoding
    values: list[list[float | None]]
    stats: SliceStats
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


class PointCloudSelectionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    time_index: int
    time_seconds: float | None = None
    threshold: float
    max_points: int


class PointCloudStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_count: int
    returned_count: int
    min_value: float | None = None
    max_value: float | None = None
    downsampled: bool
    downsample_stride: int


class PointCloudResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    field: VisualizableField
    selection: PointCloudSelectionMetadata
    coordinate_units: dict[str, str | None] = Field(default_factory=dict)
    point_order: list[str]
    points: list[list[float]]
    stats: PointCloudStats
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


def field_catalog(settings: CloudChamberSettings, result_id: str) -> FieldCatalogResponse:
    """Return visualizable field metadata for an ingested result."""
    metadata = get_result_metadata(settings, result_id)
    dataset, close_datasets = _open_dataset_sequence(metadata)
    try:
        fields = [
            _visualizable_field(metadata, dataset, field_name)
            for field_name in FIELD_DEFINITIONS
            if field_name in dataset.data_vars
        ]
        return FieldCatalogResponse(
            result_id=metadata.result_id,
            run_id=metadata.run_id,
            scenario_id=metadata.scenario_id,
            source_model=metadata.source_model,
            available_fields=fields,
            provenance=_provenance(metadata),
            caveats=_dedupe(_catalog_caveats(metadata, fields)),
        )
    finally:
        _close_all(close_datasets)


def point_cloud(
    settings: CloudChamberSettings,
    result_id: str,
    *,
    field: str,
    time_index: int,
    threshold: float,
    max_points: int,
    encoding: VisualizationEncoding = "json",
) -> PointCloudResponse:
    """Return thresholded native-grid points for cloud-water visualization."""
    if encoding != "json":
        raise VisualizationDataError("Only encoding=json is supported for MVP point clouds.")
    if field != "qc":
        raise VisualizationDataError("Only field=qc is supported for MVP cloud-water rendering.")
    if not math.isfinite(threshold) or threshold < 0:
        raise VisualizationDataError("threshold must be a finite non-negative number.")
    if max_points <= 0:
        raise VisualizationDataError("max_points must be greater than 0.")

    metadata = get_result_metadata(settings, result_id)
    dataset, close_datasets = _open_dataset_sequence(metadata)
    try:
        if field not in dataset.data_vars:
            raise VisualizationDataError("Cloud water field qc is not available for this result.")
        data_array = dataset[field]
        dims = _field_dimensions(data_array)
        if not dims.time:
            raise VisualizationDataError("Field qc has no time dimension.")
        if not dims.vertical or not dims.y or not dims.x:
            raise VisualizationDataError("Field qc must have native vertical/y/x dimensions.")
        _validate_index(time_index, int(data_array.sizes[dims.time]), "time_index")
        at_time = data_array.isel({dims.time: time_index})
        source_points = _threshold_points(
            at_time,
            dims=dims,
            dataset=dataset,
            threshold=threshold,
        )
        source_count = len(source_points)
        stride = max(1, math.ceil(source_count / max_points)) if source_count else 1
        returned_points = source_points[::stride][:max_points]
        values = [point[3] for point in source_points]
        visual_field = _visualizable_field(metadata, dataset, field)
        caveats = _dedupe(
            [
                *_field_caveats(field, visual_field.coordinate_names),
                "native_grid_thresholded_point_cloud",
                "visualizer_interpretation_of_cm1_qc",
                *(
                    ["deterministic_stride_downsampling_applied"]
                    if source_count > max_points
                    else []
                ),
            ]
        )
        return PointCloudResponse(
            result_id=metadata.result_id,
            run_id=metadata.run_id,
            scenario_id=metadata.scenario_id,
            field=visual_field,
            selection=PointCloudSelectionMetadata(
                field=field,
                time_index=time_index,
                time_seconds=_time_value_seconds(dataset, dims.time, time_index),
                threshold=threshold,
                max_points=max_points,
            ),
            coordinate_units={
                str(dims.x): _coordinate_units(dataset, dims.x),
                str(dims.y): _coordinate_units(dataset, dims.y),
                str(dims.vertical): _coordinate_units(dataset, dims.vertical),
            },
            point_order=["x", "y", "z", "value"],
            points=returned_points,
            stats=PointCloudStats(
                source_count=source_count,
                returned_count=len(returned_points),
                min_value=min(values) if values else None,
                max_value=max(values) if values else None,
                downsampled=source_count > max_points,
                downsample_stride=stride,
            ),
            provenance=_provenance(
                metadata,
                processing_method="backend_xarray_native_grid_threshold",
                rendering_method="thresholded_point_cloud",
                provenance_label=(
                    "CM1-derived cloud-water point cloud; native-grid threshold; "
                    "visualizer interpretation"
                ),
            ),
            caveats=caveats,
        )
    finally:
        _close_all(close_datasets)


def field_slice(
    settings: CloudChamberSettings,
    result_id: str,
    *,
    field: str,
    time_index: int,
    orientation: VisualizationOrientation,
    level_index: int,
    encoding: VisualizationEncoding = "json",
) -> SliceResponse:
    """Return a small JSON 2-D slice payload for a visualizable field."""
    if encoding != "json":
        raise VisualizationDataError("Only encoding=json is supported for MVP 2-D slices.")

    metadata = get_result_metadata(settings, result_id)
    dataset, close_datasets = _open_dataset_sequence(metadata)
    try:
        if field not in FIELD_DEFINITIONS:
            raise VisualizationDataError(f"Unsupported visualization field: {field}")
        if field not in dataset.data_vars:
            raise VisualizationDataError(f"Field is not available for this result: {field}")
        data_array = dataset[field]
        dims = _field_dimensions(data_array)
        if not dims.time:
            raise VisualizationDataError(f"Field {field} has no time dimension.")
        _validate_index(time_index, int(data_array.sizes[dims.time]), "time_index")
        at_time = data_array.isel({dims.time: time_index})
        spatial_dims = [dimension for dimension in at_time.dims]
        if len(spatial_dims) != 3:
            raise VisualizationDataError(
                f"Field {field} must have three native spatial dimensions after time selection."
            )

        sliced, selected_dimension = _slice_spatial_array(
            at_time,
            dims,
            orientation=orientation,
            level_index=level_index,
        )
        values = _json_values(sliced)
        stats = _slice_stats(sliced)
        visual_field = _visualizable_field(metadata, dataset, field)
        selected_value = _coordinate_value(dataset, selected_dimension, level_index)
        vertical_dim = dims.vertical
        vertical_units = _coordinate_units(dataset, vertical_dim)
        level_units = _coordinate_units(dataset, selected_dimension)
        caveats = _dedupe(
            [
                *_field_caveats(field, visual_field.coordinate_names),
                "native_grid_view_no_interpolation",
                "json_numeric_slice_mvp",
            ]
        )
        selection = SliceSelectionMetadata(
            time_index=time_index,
            time_seconds=_time_value_seconds(dataset, dims.time, time_index),
            orientation=orientation,
            selected_dimension=selected_dimension,
            selected_index=level_index,
            selected_coordinate_value=selected_value,
            level_units=level_units,
            level_coordinate_value=selected_value if selected_dimension == vertical_dim else None,
            level_meters=_meters_if_safe(selected_value, level_units)
            if selected_dimension == vertical_dim
            else None,
        )
        coordinate_units = {
            dimension: _coordinate_units(dataset, dimension) for dimension in sliced.dims
        }
        if vertical_dim and vertical_units and vertical_dim not in coordinate_units:
            coordinate_units[vertical_dim] = vertical_units
        return SliceResponse(
            result_id=metadata.result_id,
            run_id=metadata.run_id,
            scenario_id=metadata.scenario_id,
            field=visual_field,
            selection=selection,
            coordinate_units=coordinate_units,
            shape=[int(size) for size in sliced.shape],
            dimension_order=[str(dimension) for dimension in sliced.dims],
            data_encoding=encoding,
            values=values,
            stats=stats,
            provenance=_provenance(metadata),
            caveats=caveats,
        )
    finally:
        _close_all(close_datasets)


def _open_dataset_sequence(metadata: ResultMetadata) -> tuple[Any, list[Any]]:
    paths = [Path(path).expanduser() for path in metadata.model_output_paths]
    if not paths:
        paths = [Path(path).expanduser() for path in metadata.netcdf_paths]
    if not paths:
        raise VisualizationDataError("No NetCDF model-output paths are available for this result.")

    xarray = importlib.import_module("xarray")
    opened: list[Any] = []
    normalized: list[Any] = []
    for index, path in enumerate(paths):
        try:
            dataset = xarray.open_dataset(path)
        except Exception as exc:
            raise VisualizationDataError(f"Could not open NetCDF output {path}: {exc}") from exc
        opened.append(dataset)
        normalized.append(_normalize_time_dimension(dataset, index))

    if len(normalized) == 1:
        return normalized[0], opened
    try:
        combined = xarray.concat(normalized, dim="time")
    except Exception as exc:
        _close_all(opened)
        raise VisualizationDataError(f"Could not combine NetCDF output sequence: {exc}") from exc
    return combined, [*opened, combined]


def _normalize_time_dimension(dataset: Any, file_index: int) -> Any:
    if "time" not in dataset.dims:
        return dataset.expand_dims(time=[float(file_index)])
    if "time" not in dataset.coords:
        size = int(dataset.sizes["time"])
        return dataset.assign_coords(time=[float(file_index + offset) for offset in range(size)])
    return dataset


def _visualizable_field(
    metadata: ResultMetadata,
    dataset: Any,
    field_name: str,
) -> VisualizableField:
    data_array = dataset[field_name]
    canonical, display = FIELD_DEFINITIONS[field_name]
    coordinates = _field_dimensions(data_array).coordinates
    return VisualizableField(
        raw_field_name=field_name,
        canonical_field_name=canonical,
        display_name=display,
        units=_attr_string(data_array.attrs.get("units")),
        dimensions=[str(dimension) for dimension in data_array.dims],
        shape=[int(size) for size in data_array.shape],
        native_grid=_native_grid_label(coordinates),
        coordinate_names=coordinates,
        time_coordinate_values=_coordinate_values(dataset, coordinates.time),
        provenance=_provenance(metadata),
        caveats=_field_caveats(field_name, coordinates),
    )


class _FieldDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time: str | None
    vertical: str | None
    y: str | None
    x: str | None
    coordinates: FieldCoordinateMetadata


def _field_dimensions(data_array: Any) -> _FieldDimensions:
    dimensions = [str(dimension) for dimension in data_array.dims]
    time = _first_present(TIME_DIMENSION_CANDIDATES, dimensions)
    vertical = _first_present(VERTICAL_DIMENSION_CANDIDATES, dimensions)
    y = _first_present(Y_DIMENSION_CANDIDATES, dimensions)
    x = _first_present(X_DIMENSION_CANDIDATES, dimensions)
    return _FieldDimensions(
        time=time,
        vertical=vertical,
        y=y,
        x=x,
        coordinates=FieldCoordinateMetadata(time=time, vertical=vertical, y=y, x=x),
    )


def _slice_spatial_array(
    data_array: Any,
    dims: _FieldDimensions,
    *,
    orientation: VisualizationOrientation,
    level_index: int,
) -> tuple[Any, str]:
    if orientation == "horizontal":
        selected_dimension = dims.vertical
    elif orientation == "vertical_x":
        selected_dimension = dims.y
    else:
        selected_dimension = dims.x
    if selected_dimension is None:
        raise VisualizationDataError(f"Cannot slice orientation {orientation}; missing dimension.")
    _validate_index(level_index, int(data_array.sizes[selected_dimension]), "level_index")
    return data_array.isel({selected_dimension: level_index}), selected_dimension


def _threshold_points(
    data_array: Any,
    *,
    dims: _FieldDimensions,
    dataset: Any,
    threshold: float,
) -> list[list[float]]:
    if not dims.vertical or not dims.y or not dims.x:
        return []
    points: list[list[float]] = []
    values = data_array.values
    z_values = _coordinate_values(dataset, dims.vertical)
    y_values = _coordinate_values(dataset, dims.y)
    x_values = _coordinate_values(dataset, dims.x)
    vertical_axis = data_array.dims.index(dims.vertical)
    y_axis = data_array.dims.index(dims.y)
    x_axis = data_array.dims.index(dims.x)

    # Iterate in native array order so stride downsampling is deterministic.
    for native_index in itertools.product(*(range(int(size)) for size in data_array.shape)):
        raw_value = values[native_index]
        try:
            numeric = float(raw_value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(numeric) or numeric < threshold:
            continue
        z_index = native_index[vertical_axis]
        y_index = native_index[y_axis]
        x_index = native_index[x_axis]
        points.append(
            [
                _coordinate_number(x_values, x_index),
                _coordinate_number(y_values, y_index),
                _coordinate_number(z_values, z_index),
                numeric,
            ]
        )
    return points


def _coordinate_number(values: list[float | str | None], index: int) -> float:
    if index < len(values):
        try:
            value = values[index]
            return float(value) if value is not None else float(index)
        except (TypeError, ValueError):
            return float(index)
    return float(index)


def _validate_index(index: int, size: int, label: str) -> None:
    if index < 0 or index >= size:
        raise VisualizationDataError(f"{label}={index} is outside valid range 0..{size - 1}.")


def _native_grid_label(coordinates: FieldCoordinateMetadata) -> str:
    spatial = [coordinates.vertical, coordinates.y, coordinates.x]
    if all(spatial):
        return "/".join(str(dimension) for dimension in spatial)
    return "unknown_native_grid"


def _catalog_caveats(
    metadata: ResultMetadata,
    fields: list[VisualizableField],
) -> list[str]:
    available = {field.raw_field_name for field in fields}
    caveats = list(metadata.warnings)
    for required in ("qc", "w"):
        if required not in available:
            caveats.append(f"missing_visualization_field:{required}")
    return caveats


def _field_caveats(field_name: str, coordinates: FieldCoordinateMetadata) -> list[str]:
    caveats = ["native_grid_view_no_interpolation"]
    if field_name == "qc" and coordinates.vertical != "zh":
        caveats.append("qc_native_vertical_grid_not_zh")
    if field_name == "w" and coordinates.vertical != "zf":
        caveats.append("w_native_vertical_grid_not_zf")
    return caveats


def _provenance(
    metadata: ResultMetadata,
    *,
    processing_method: str = "backend_xarray_native_grid_slice",
    rendering_method: str = "json_2d_slice_for_inspection",
    provenance_label: str = (
        "CM1-derived visualization-ready data; native-grid view; no interpolation"
    ),
) -> ProvenancePayload:
    return ProvenancePayload(
        source_model=metadata.source_model,
        result_id=metadata.result_id,
        run_id=metadata.run_id,
        scenario_id=metadata.scenario_id,
        source_product_state=metadata.source_product_state,
        result_state=metadata.result_state,
        processing_method=processing_method,
        rendering_method=rendering_method,
        provenance_label=provenance_label,
    )


def _coordinate_values(dataset: Any, coordinate_name: str | None) -> list[float | str | None]:
    if coordinate_name is None or coordinate_name not in dataset.coords:
        return []
    values = dataset.coords[coordinate_name].values.reshape(-1).tolist()
    return [_json_scalar(value) for value in values]


def _coordinate_value(dataset: Any, coordinate_name: str, index: int) -> float | str | None:
    values = _coordinate_values(dataset, coordinate_name)
    if index < len(values):
        return values[index]
    return None


def _time_value_seconds(dataset: Any, time_dimension: str | None, index: int) -> float | None:
    if time_dimension is None:
        return None
    value = _coordinate_value(dataset, time_dimension, index)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _coordinate_units(dataset: Any, coordinate_name: str | None) -> str | None:
    if coordinate_name is None or coordinate_name not in dataset.coords:
        return None
    return _attr_string(dataset.coords[coordinate_name].attrs.get("units"))


def _meters_if_safe(value: float | str | None, units: str | None) -> float | None:
    try:
        numeric = float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
    if numeric is None:
        return None
    normalized = units.lower() if units else ""
    if normalized in {"m", "meter", "meters"}:
        return numeric
    if normalized in {"km", "kilometer", "kilometers"}:
        return numeric * 1000.0
    return None


def _json_values(data_array: Any) -> list[list[float | None]]:
    rows: list[list[float | None]] = []
    values = data_array.values.tolist()
    for row in values:
        rows.append([_finite_json_number(value) for value in row])
    return rows


def _slice_stats(data_array: Any) -> SliceStats:
    finite_values: list[float] = []
    non_finite_count = 0
    for value in data_array.values.reshape(-1).tolist():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            non_finite_count += 1
            continue
        if math.isfinite(numeric):
            finite_values.append(numeric)
        else:
            non_finite_count += 1
    mean = (sum(finite_values) / len(finite_values)) if finite_values else None
    return SliceStats(
        min=min(finite_values) if finite_values else None,
        max=max(finite_values) if finite_values else None,
        mean=mean,
        finite_count=len(finite_values),
        non_finite_count=non_finite_count,
    )


def _finite_json_number(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _json_scalar(value: Any) -> float | str | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value) if value is not None else None
    return numeric if math.isfinite(numeric) else None


def _attr_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _first_present(candidates: tuple[str, ...], names: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in names:
            return candidate
    return None


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _close_all(datasets: list[Any]) -> None:
    for dataset in datasets:
        close = getattr(dataset, "close", None)
        if callable(close):
            close()
