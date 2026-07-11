"""Visualization-ready CM1 field data contracts.

This module keeps raw NetCDF/xarray access on the backend. Frontend inspectors
and visualizers receive small, provenance-labeled payloads rather than parsing
CM1 output directly in the browser.
"""

from __future__ import annotations

import importlib
import itertools
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.output_products import (
    OutputProductManifestError,
    default_output_product_manifest_path,
    output_product_manifest_from_json,
    resolve_time_index,
)
from cloud_chamber.result_diagnostics import QC_CLOUD_THRESHOLD_KG_KG
from cloud_chamber.result_ingest import (
    ResultMetadata,
    get_result_metadata,
)
from cloud_chamber.settings import CloudChamberSettings

VisualizationOrientation = Literal["horizontal", "vertical_x", "vertical_y"]
VisualizationEncoding = Literal["json"]
OutputProductKind = Literal["vertical_profile", "time_height", "time_series", "future_diagnostic"]
OutputProductStatus = Literal["available", "unavailable"]
ProfileAggregationMethod = Literal["domain_mean", "domain_min", "domain_max", "selected_column"]
TimeHeightAggregationMethod = Literal["cloud_fraction", "domain_mean", "domain_min", "domain_max"]
TimeSeriesAggregationMethod = Literal["cloud_fraction", "domain_mean", "domain_min", "domain_max"]


@dataclass(frozen=True)
class FieldDefinition:
    canonical_field_name: str
    display_name: str
    field_family: str
    frontend_consumer_guidance: str
    point_cloud_allowed: bool = False
    profile_candidate: bool = True
    time_height_candidate: bool = True
    render_ready_candidate: bool = False
    external_export_candidate: bool = True
    caveats: tuple[str, ...] = ()


FIELD_DEFINITIONS: dict[str, FieldDefinition] = {
    "qc": FieldDefinition(
        "cloud_water",
        "Cloud water",
        "cloud_hydrometeor",
        "Supported for native slices, selected-place diagnostics, and 3-D scalar points.",
        point_cloud_allowed=True,
        render_ready_candidate=True,
    ),
    "w": FieldDefinition(
        "vertical_velocity",
        "Vertical velocity",
        "motion",
        "Slice/profile-first field; signed-flow 3-D rendering is not supported yet.",
        caveats=("signed_flow_field_slice_only",),
    ),
    "u": FieldDefinition(
        "east_west_wind",
        "East-west wind",
        "wind",
        (
            "Native-grid wind component; supported for slices, profiles, and time-height "
            "summaries without vector interpolation."
        ),
        caveats=(
            "native_staggered_wind_component",
            "u_native_x_staggered_grid",
            "signed_flow_field_slice_only",
            "no_vector_interpolation",
            "wind_component_not_wind_gust_outflow_or_rotation_diagnostic",
        ),
    ),
    "v": FieldDefinition(
        "north_south_wind",
        "North-south wind",
        "wind",
        (
            "Native-grid wind component; supported for slices, profiles, and time-height "
            "summaries without vector interpolation."
        ),
        caveats=(
            "native_staggered_wind_component",
            "v_native_y_staggered_grid",
            "signed_flow_field_slice_only",
            "no_vector_interpolation",
            "wind_component_not_wind_gust_outflow_or_rotation_diagnostic",
        ),
    ),
    "qr": FieldDefinition(
        "rain_water",
        "Rain water aloft",
        "precipitation_aloft",
        "Rain water aloft; supported for native slices and 3-D scalar points.",
        point_cloud_allowed=True,
        render_ready_candidate=True,
        caveats=("rain_water_aloft_not_surface_rain",),
    ),
    "qv": FieldDefinition(
        "water_vapor",
        "Water vapor",
        "thermodynamic",
        "Thermodynamic scalar; supported for native slices and caveated 3-D scalar points.",
        point_cloud_allowed=True,
        render_ready_candidate=True,
        caveats=("water_vapor_is_context_not_cloud_or_precipitation",),
    ),
    "t": FieldDefinition(
        "temperature",
        "Temperature",
        "thermodynamic",
        "Slice/profile-first thermodynamic field; not a 3-D scalar render field.",
        caveats=("thermodynamic_field_slice_profile_first",),
    ),
    "temp": FieldDefinition(
        "temperature",
        "Temperature",
        "thermodynamic",
        "Slice/profile-first thermodynamic field; not a 3-D scalar render field.",
        caveats=("thermodynamic_field_slice_profile_first",),
    ),
    "temperature": FieldDefinition(
        "temperature",
        "Temperature",
        "thermodynamic",
        "Slice/profile-first thermodynamic field; not a 3-D scalar render field.",
        caveats=("thermodynamic_field_slice_profile_first",),
    ),
    "th": FieldDefinition(
        "potential_temperature",
        "Potential temperature",
        "thermodynamic",
        "Slice/profile-first thermodynamic field; not a 3-D scalar render field.",
        caveats=("thermodynamic_field_slice_profile_first",),
    ),
    "theta": FieldDefinition(
        "potential_temperature",
        "Potential temperature",
        "thermodynamic",
        "Slice/profile-first thermodynamic field; not a 3-D scalar render field.",
        caveats=("thermodynamic_field_slice_profile_first",),
    ),
    "prs": FieldDefinition(
        "pressure",
        "Pressure",
        "thermodynamic",
        "Slice/profile-first pressure field; useful for profiles and diagnostics.",
        caveats=("pressure_field_slice_profile_first",),
    ),
    "p": FieldDefinition(
        "pressure",
        "Pressure",
        "thermodynamic",
        "Slice/profile-first pressure field; useful for profiles and diagnostics.",
        caveats=("pressure_field_slice_profile_first",),
    ),
    "pressure": FieldDefinition(
        "pressure",
        "Pressure",
        "thermodynamic",
        "Slice/profile-first pressure field; useful for profiles and diagnostics.",
        caveats=("pressure_field_slice_profile_first",),
    ),
    "rain": FieldDefinition(
        "accumulated_surface_rain",
        "Accumulated surface rain",
        "surface_precipitation",
        "Surface-native accumulated precipitation; horizontal slices and floor-layer points only.",
        point_cloud_allowed=True,
        render_ready_candidate=True,
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("surface_rain_not_rain_water_aloft",),
    ),
    "dbz": FieldDefinition(
        "reflectivity",
        "Reflectivity",
        "reflectivity",
        "Reflectivity scalar; supported for native slices and caveated 3-D scalar points.",
        point_cloud_allowed=True,
        render_ready_candidate=True,
    ),
    "hfx": FieldDefinition(
        "surface_sensible_heat_flux",
        "Surface sensible heat flux",
        "surface_flux",
        "Surface-native flux field; horizontal slices and selected-place context only.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("surface_flux_field_not_cloud_outcome",),
    ),
    "sensible_heat_flux": FieldDefinition(
        "surface_sensible_heat_flux",
        "Surface sensible heat flux",
        "surface_flux",
        "Surface-native flux field; horizontal slices and selected-place context only.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("surface_flux_field_not_cloud_outcome",),
    ),
    "lhfx": FieldDefinition(
        "surface_latent_heat_flux",
        "Surface latent heat flux",
        "surface_flux",
        "Surface-native flux field; horizontal slices and selected-place context only.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("surface_flux_field_not_cloud_outcome",),
    ),
    "latent_heat_flux": FieldDefinition(
        "surface_latent_heat_flux",
        "Surface latent heat flux",
        "surface_flux",
        "Surface-native flux field; horizontal slices and selected-place context only.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("surface_flux_field_not_cloud_outcome",),
    ),
    "lwp": FieldDefinition(
        "liquid_water_path",
        "Liquid water path",
        "column_integrated_water",
        "Column-integrated water field; horizontal slices and selected-place context only.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("column_integrated_field_no_vertical_profile",),
    ),
    "cape": FieldDefinition(
        "cape",
        "CAPE",
        "parcel_diagnostic",
        "Surface-native or column diagnostic; cataloged only when CM1 output includes it.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("parcel_diagnostic_field_catalog_only",),
    ),
    "cin": FieldDefinition(
        "cin",
        "CIN",
        "parcel_diagnostic",
        "Surface-native or column diagnostic; cataloged only when CM1 output includes it.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("parcel_diagnostic_field_catalog_only",),
    ),
    "lcl": FieldDefinition(
        "lcl",
        "LCL",
        "parcel_diagnostic",
        "Surface-native or column diagnostic; cataloged only when CM1 output includes it.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("parcel_diagnostic_field_catalog_only",),
    ),
    "lfc": FieldDefinition(
        "lfc",
        "LFC",
        "parcel_diagnostic",
        "Surface-native or column diagnostic; cataloged only when CM1 output includes it.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("parcel_diagnostic_field_catalog_only",),
    ),
    "swten": FieldDefinition(
        "shortwave_radiative_tendency",
        "Shortwave radiative tendency",
        "radiation",
        "Radiation tendency field; slice/profile candidate only when present and labeled.",
        caveats=("radiation_field_cataloged_when_present",),
    ),
    "lwten": FieldDefinition(
        "longwave_radiative_tendency",
        "Longwave radiative tendency",
        "radiation",
        "Radiation tendency field; slice/profile candidate only when present and labeled.",
        caveats=("radiation_field_cataloged_when_present",),
    ),
    "rthraten": FieldDefinition(
        "radiative_heating_tendency",
        "Radiative heating tendency",
        "radiation",
        "Radiation tendency field; slice/profile candidate only when present and labeled.",
        caveats=("radiation_field_cataloged_when_present",),
    ),
    "psfc": FieldDefinition(
        "surface_pressure",
        "Surface pressure",
        "surface_diagnostic",
        "Surface-native diagnostic; horizontal slices and selected-place context only.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("surface_diagnostic_field_not_3d_model_field",),
    ),
    "tsk": FieldDefinition(
        "surface_temperature",
        "Surface temperature",
        "surface_diagnostic",
        "Surface-native diagnostic; horizontal slices and selected-place context only.",
        profile_candidate=False,
        time_height_candidate=False,
        caveats=("surface_diagnostic_field_not_3d_model_field",),
    ),
}

SIGNED_FLOW_FIELDS = {"u", "v", "w"}
SURFACE_POINT_FIELDS = {"rain"}

TIME_DIMENSION_CANDIDATES = ("time", "mtime", "t")
VERTICAL_DIMENSION_CANDIDATES = ("zh", "zf", "z", "height", "height_m", "height_km")
SURFACE_VERTICAL_CANDIDATES = ("zf", "zh", "z", "height", "height_m", "height_km")
Y_DIMENSION_CANDIDATES = ("yh", "yf", "y")
X_DIMENSION_CANDIDATES = ("xh", "xf", "x")


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


class FieldCapabilityMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slice: bool
    point_cloud: bool
    selected_point: bool
    selected_column: bool
    profile_candidate: bool
    time_height_candidate: bool
    render_ready_candidate: bool
    external_export_candidate: bool


class VisualizableField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_field_name: str
    canonical_field_name: str
    display_name: str
    units: str | None = None
    dimensions: list[str]
    shape: list[int]
    native_grid: str
    native_grid_class: str
    coordinate_names: FieldCoordinateMetadata
    time_coordinate_values: list[float | str | None] = Field(default_factory=list)
    time_available: bool = False
    field_family: str
    capabilities: FieldCapabilityMetadata
    frontend_consumer_guidance: str
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


class UnavailableField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_field_name: str
    canonical_field_name: str
    display_name: str
    expected_by_run: bool
    reason: str
    caveats: list[str] = Field(default_factory=list)


class FieldCatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    source_model: str
    available_fields: list[VisualizableField]
    unavailable_fields: list[UnavailableField] = Field(default_factory=list)
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


class OutputProductDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_key: str
    product_kind: OutputProductKind
    status: OutputProductStatus
    raw_field_name: str | None = None
    canonical_field_name: str | None = None
    display_name: str
    units: str | None = None
    aggregation_methods: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)
    reason: str | None = None
    caveats: list[str] = Field(default_factory=list)


class OutputProductCatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    source_model: str
    available_profile_products: list[OutputProductDescriptor]
    available_time_height_products: list[OutputProductDescriptor]
    available_time_series_products: list[OutputProductDescriptor]
    unavailable_products: list[OutputProductDescriptor] = Field(default_factory=list)
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


class OutputTimeAxisMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_indices: list[int]
    time_seconds: list[float | None]
    source_time_values: list[float | str | None]
    source_files: list[str | None]
    local_time_indices: list[int | None]
    time_source: str | None = None
    time_caveats: list[str] = Field(default_factory=list)


class VerticalProfileSelectionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    time_index: int
    time_seconds: float | None = None
    source_file: str | None = None
    local_time_index: int | None = None
    aggregation_method: ProfileAggregationMethod
    x_index: int | None = None
    y_index: int | None = None
    x_coordinate_value: float | str | None = None
    y_coordinate_value: float | str | None = None


class VerticalProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    field: VisualizableField
    selection: VerticalProfileSelectionMetadata
    vertical_dimension: str
    vertical_units: str | None = None
    vertical_coordinate_values: list[float | str | None]
    values: list[float | None]
    finite_counts: list[int]
    non_finite_counts: list[int]
    aggregation_method: ProfileAggregationMethod
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


class TimeHeightSelectionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    aggregation_method: TimeHeightAggregationMethod
    threshold: float | None = None


class TimeHeightResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    field: VisualizableField
    selection: TimeHeightSelectionMetadata
    time_axis: OutputTimeAxisMetadata
    vertical_dimension: str
    vertical_units: str | None = None
    vertical_coordinate_values: list[float | str | None]
    shape: list[int]
    size_class: str
    values: list[list[float | None]]
    finite_counts: list[list[int]]
    non_finite_counts: list[list[int]]
    aggregation_method: TimeHeightAggregationMethod
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


class TimeSeriesSelectionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    aggregation_method: TimeSeriesAggregationMethod
    threshold: float | None = None


class TimeSeriesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    field: VisualizableField
    selection: TimeSeriesSelectionMetadata
    time_axis: OutputTimeAxisMetadata
    units: str | None = None
    values: list[float | None]
    finite_counts: list[int]
    non_finite_counts: list[int]
    aggregation_method: TimeSeriesAggregationMethod
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
    field_min_value: float | None = None
    field_max_value: float | None = None
    field_mean_value: float | None = None
    field_finite_count: int
    field_non_finite_count: int
    min_value: float | None = None
    max_value: float | None = None
    active_z_min: float | None = None
    active_z_max: float | None = None
    max_value_location: dict[str, float] | None = None
    downsampled: bool
    downsample_stride: int


class CoordinateExtent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: float
    max: float
    units: str | None = None


class PointCloudResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    field: VisualizableField
    selection: PointCloudSelectionMetadata
    coordinate_units: dict[str, str | None] = Field(default_factory=dict)
    coordinate_extents: dict[str, CoordinateExtent] = Field(default_factory=dict)
    point_order: list[str]
    points: list[list[float]]
    stats: PointCloudStats
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


class FieldViewDefaults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    time_index: int
    time_seconds: float | None = None
    horizontal_level_index: int
    vertical_x_index: int
    vertical_y_index: int
    source: str
    max_value: float | None = None
    selected_time_index: int | None = None
    selected_time_seconds: float | None = None
    caveats: list[str] = Field(default_factory=list)


class ViewDefaultsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    preferred_field: str | None = None
    fields: dict[str, FieldViewDefaults]
    provenance: ProvenancePayload
    caveats: list[str] = Field(default_factory=list)


def _metadata_visualizable_fields(metadata: ResultMetadata) -> list[VisualizableField]:
    fields: list[VisualizableField] = []
    for field in metadata.fields_detected:
        if _field_definition(field.name) is None:
            continue
        fields.append(_visualizable_field_from_metadata(metadata, field))
    return fields


def _visualizable_field_from_metadata(
    metadata: ResultMetadata,
    field: Any,
) -> VisualizableField:
    definition = _require_field_definition(field.name)
    coordinates = _field_coordinates_from_dimensions(field.dimensions)
    capabilities = _field_capabilities(field.name, coordinates)
    return VisualizableField(
        raw_field_name=field.name,
        canonical_field_name=definition.canonical_field_name,
        display_name=definition.display_name,
        units=field.units,
        dimensions=[str(dimension) for dimension in field.dimensions],
        shape=[int(size) for size in field.shape],
        native_grid=_native_grid_label(coordinates),
        native_grid_class=_native_grid_class(coordinates),
        coordinate_names=coordinates,
        time_coordinate_values=_metadata_time_values(metadata, coordinates.time),
        time_available=coordinates.time is not None,
        field_family=definition.field_family,
        capabilities=capabilities,
        frontend_consumer_guidance=definition.frontend_consumer_guidance,
        provenance=_provenance(
            metadata,
            processing_method="ingested_result_metadata_field_catalog",
            rendering_method="field_catalog_for_visualization",
            provenance_label=(
                "CM1-derived field metadata from result ingest; selected payloads "
                "still come from NetCDF/xarray native-grid views"
            ),
        ),
        caveats=_field_caveats(field.name, coordinates),
    )


def _field_coordinates_from_dimensions(dimensions: list[str]) -> FieldCoordinateMetadata:
    time = _first_present(TIME_DIMENSION_CANDIDATES, dimensions)
    vertical = _first_present(VERTICAL_DIMENSION_CANDIDATES, dimensions)
    y = _first_present(Y_DIMENSION_CANDIDATES, dimensions)
    x = _first_present(X_DIMENSION_CANDIDATES, dimensions)
    return FieldCoordinateMetadata(time=time, vertical=vertical, y=y, x=x)


def _metadata_time_values(
    metadata: ResultMetadata,
    time_coordinate: str | None,
) -> list[float | str | None]:
    if time_coordinate is None or metadata.time_steps is None or metadata.time_steps <= 0:
        return []
    if metadata.first_output_time_seconds is None or metadata.last_output_time_seconds is None:
        return [float(index) for index in range(metadata.time_steps)]
    if metadata.time_steps == 1:
        return [metadata.first_output_time_seconds]
    step = (metadata.last_output_time_seconds - metadata.first_output_time_seconds) / (
        metadata.time_steps - 1
    )
    return [
        metadata.first_output_time_seconds + index * step for index in range(metadata.time_steps)
    ]


def _should_use_metadata_defaults(metadata: ResultMetadata) -> bool:
    # Exact max-location scans are helpful for tiny fixtures but too expensive for
    # deep runs: field defaults must not require opening and scanning gigabytes
    # before Explore can render.
    if len(metadata.model_output_paths) > 8:
        return True
    largest_field_size = 0
    for field in metadata.fields_detected:
        size = 1
        for dimension_size in field.shape:
            size *= max(1, int(dimension_size))
        largest_field_size = max(largest_field_size, size)
    return largest_field_size > 10_000_000


def _metadata_view_defaults(
    metadata: ResultMetadata,
    *,
    time_index: int | None = None,
) -> ViewDefaultsResponse:
    fields: dict[str, FieldViewDefaults] = {}
    for visual_field in _metadata_visualizable_fields(metadata):
        fields[visual_field.raw_field_name] = _metadata_field_view_defaults(
            metadata,
            visual_field,
            selected_time_index=time_index,
        )
    preferred = _preferred_field(metadata, fields)
    return ViewDefaultsResponse(
        result_id=metadata.result_id,
        run_id=metadata.run_id,
        scenario_id=metadata.scenario_id,
        preferred_field=preferred,
        fields=fields,
        provenance=_provenance(
            metadata,
            processing_method="ingested_result_metadata_view_defaults",
            rendering_method="field_slice_and_point_cloud_default_selection",
            provenance_label=(
                "CM1-derived visualization defaults from ingested diagnostics and "
                "metadata; selected payloads still come from NetCDF/xarray"
            ),
        ),
        caveats=_dedupe(
            [
                "default_locations_are_metadata_based_for_large_output",
                "default_locations_fall_back_to_domain_center",
                *(
                    ["default_locations_are_selected_time_native_grid_indices"]
                    if time_index is not None
                    else []
                ),
                *metadata.warnings,
                *(["missing_visualization_field:qc"] if "qc" not in fields else []),
                *(["missing_visualization_field:w"] if "w" not in fields else []),
            ]
        ),
    )


def _metadata_field_view_defaults(
    metadata: ResultMetadata,
    field: VisualizableField,
    *,
    selected_time_index: int | None,
) -> FieldViewDefaults:
    time_size = _metadata_time_size(metadata, field)
    vertical_size = _dimension_size(field, field.coordinate_names.vertical, fallback=1)
    y_size = _dimension_size(field, field.coordinate_names.y, fallback=1)
    x_size = _dimension_size(field, field.coordinate_names.x, fallback=1)
    resolved_time = (
        max(0, min(selected_time_index, time_size - 1))
        if selected_time_index is not None
        else _metadata_interesting_time_index(metadata, field.raw_field_name, time_size)
    )
    return FieldViewDefaults(
        field=field.raw_field_name,
        time_index=resolved_time,
        time_seconds=_metadata_time_seconds(metadata, resolved_time),
        horizontal_level_index=_metadata_horizontal_level_index(metadata, field, vertical_size),
        vertical_x_index=max(0, y_size // 2),
        vertical_y_index=max(0, x_size // 2),
        source=(
            "selected_time_metadata_domain_center"
            if selected_time_index is not None
            else "metadata_interesting_time_domain_center"
        ),
        max_value=_metadata_field_max_value(metadata, field.raw_field_name),
        selected_time_index=selected_time_index,
        selected_time_seconds=_metadata_time_seconds(metadata, selected_time_index)
        if selected_time_index is not None
        else None,
        caveats=_dedupe(
            [
                *_field_caveats(field.raw_field_name, field.coordinate_names),
                "default_location_uses_ingested_metadata_not_full_field_scan",
                *_metadata_default_location_caveats(metadata, field.raw_field_name),
            ]
        ),
    )


def _metadata_time_size(metadata: ResultMetadata, field: VisualizableField) -> int:
    return max(
        1,
        _dimension_size(field, field.coordinate_names.time, fallback=1),
        len(field.time_coordinate_values),
        metadata.time_steps or 0,
        len(metadata.model_output_paths),
    )


def _dimension_size(field: VisualizableField, dimension: str | None, *, fallback: int) -> int:
    if dimension is None:
        return fallback
    for index, field_dimension in enumerate(field.dimensions):
        if field_dimension == dimension and index < len(field.shape):
            return int(field.shape[index])
    return fallback


def _metadata_horizontal_level_index(
    metadata: ResultMetadata,
    field: VisualizableField,
    vertical_size: int,
) -> int:
    if vertical_size <= 1:
        return 0
    if field.raw_field_name not in {"qc", "qr", "dbz"} or metadata.diagnostics is None:
        return max(0, vertical_size // 2)

    target_height_m = _metadata_cloud_focus_height_m(metadata, field.raw_field_name)
    if target_height_m is None:
        return max(0, vertical_size // 2)

    # Metadata-only defaults intentionally avoid opening large output sequences.
    # CM1 deep-trial files currently expose 500 m-ish scalar levels; this maps
    # shallow cloud-water metadata away from the domain midpoint without
    # pretending we know the exact native coordinate.
    estimated_index = math.ceil(max(0.0, target_height_m) / 500.0) - 1
    return max(0, min(vertical_size - 1, estimated_index))


def _metadata_cloud_focus_height_m(metadata: ResultMetadata, field_name: str) -> float | None:
    diagnostics = metadata.diagnostics
    if diagnostics is None or field_name not in {"qc", "qr", "dbz"}:
        return None
    if field_name == "qc" and diagnostics.cloud.time_of_max_qc_seconds is not None:
        height = _time_value_at(
            diagnostics.cloud.max_qc_height_time_series,
            diagnostics.cloud.time_of_max_qc_seconds,
        )
        if height is not None:
            return height
    return diagnostics.cloud.cloud_top_m


def _time_value_at(series: list[Any], target_seconds: float) -> float | None:
    closest: tuple[float, float] | None = None
    for point in series:
        value = getattr(point, "value", None)
        seconds = getattr(point, "time_seconds", None)
        if value is None or seconds is None:
            continue
        try:
            numeric_value = float(value)
            numeric_seconds = float(seconds)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(numeric_value) or not math.isfinite(numeric_seconds):
            continue
        distance = abs(numeric_seconds - target_seconds)
        if closest is None or distance < closest[0]:
            closest = (distance, numeric_value)
    return closest[1] if closest is not None else None


def _metadata_default_location_caveats(
    metadata: ResultMetadata,
    field_name: str,
) -> list[str]:
    caveats = ["default_location_fell_back_to_domain_center"]
    if field_name in {"qc", "qr", "dbz"} and _metadata_cloud_focus_height_m(metadata, field_name):
        caveats.append("default_vertical_level_uses_ingested_cloud_height_estimate")
    return caveats


def _metadata_interesting_time_index(
    metadata: ResultMetadata,
    field_name: str,
    time_size: int,
) -> int:
    seconds: float | None = None
    if metadata.diagnostics is not None:
        if field_name == "qc":
            seconds = metadata.diagnostics.cloud.time_of_max_qc_seconds
        elif field_name == "w":
            seconds = metadata.diagnostics.vertical_velocity.time_of_max_w_seconds
        elif field_name == "qr":
            seconds = metadata.diagnostics.rain.time_of_max_qr_seconds
        elif field_name in {"rain", "dbz", "qv"}:
            seconds = (
                metadata.diagnostics.cloud.time_of_max_qc_seconds
                or metadata.diagnostics.rain.time_of_max_qr_seconds
            )
    if seconds is None:
        return max(0, min(time_size - 1, time_size // 2))
    return _metadata_time_index_for_seconds(metadata, seconds, time_size)


def _metadata_time_index_for_seconds(
    metadata: ResultMetadata,
    seconds: float,
    time_size: int,
) -> int:
    values = _metadata_time_values(metadata, metadata.time_coordinate)
    numeric_values: list[float] = []
    for value in values:
        if value is None:
            numeric_values.append(float(len(numeric_values)))
            continue
        try:
            numeric_values.append(float(value))
        except (TypeError, ValueError):
            numeric_values.append(float(len(numeric_values)))
    if numeric_values:
        best_index = min(
            range(len(numeric_values)),
            key=lambda index: abs(numeric_values[index] - seconds),
        )
        return max(0, min(time_size - 1, best_index))
    return max(0, min(time_size - 1, int(round(seconds))))


def _metadata_time_seconds(metadata: ResultMetadata, time_index: int | None) -> float | None:
    if time_index is None:
        return None
    values = _metadata_time_values(metadata, metadata.time_coordinate)
    if 0 <= time_index < len(values):
        value = values[time_index]
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    return None


def _metadata_field_max_value(metadata: ResultMetadata, field_name: str) -> float | None:
    if metadata.diagnostics is None:
        return None
    if field_name == "qc":
        return metadata.diagnostics.cloud.max_qc_kg_kg
    if field_name == "w":
        return metadata.diagnostics.vertical_velocity.max_w_m_s
    if field_name == "qr":
        return metadata.diagnostics.rain.max_qr_kg_kg
    if field_name == "dbz":
        return metadata.diagnostics.reflectivity.max_dbz
    if field_name == "rain":
        return metadata.diagnostics.surface_rain.max_surface_rain
    return None


def _known_dataset_field_names(dataset: Any) -> list[str]:
    return [str(name) for name in dataset.data_vars if _field_definition(str(name)) is not None]


def field_catalog(settings: CloudChamberSettings, result_id: str) -> FieldCatalogResponse:
    """Return visualizable field metadata for an ingested result."""
    metadata = get_result_metadata(settings, result_id)
    fields = _metadata_visualizable_fields(metadata)
    unavailable_fields = _catalog_unavailable_fields(metadata, fields)
    return FieldCatalogResponse(
        result_id=metadata.result_id,
        run_id=metadata.run_id,
        scenario_id=metadata.scenario_id,
        source_model=metadata.source_model,
        available_fields=fields,
        unavailable_fields=unavailable_fields,
        provenance=_provenance(
            metadata,
            processing_method="ingested_result_metadata_field_catalog",
            rendering_method="field_catalog_for_visualization",
            provenance_label=(
                "CM1-derived field catalog from ingested result metadata; raw NetCDF "
                "opened only for selected native-grid view data payloads"
            ),
        ),
        caveats=_dedupe(_catalog_caveats(metadata, fields, unavailable_fields)),
    )


def output_product_catalog(
    settings: CloudChamberSettings, result_id: str
) -> OutputProductCatalogResponse:
    """Return bounded backend output-product options for an ingested result."""
    metadata = get_result_metadata(settings, result_id)
    catalog = field_catalog(settings, result_id)
    profile_products: list[OutputProductDescriptor] = []
    time_height_products: list[OutputProductDescriptor] = []
    time_series_products: list[OutputProductDescriptor] = []
    for field in catalog.available_fields:
        if field.capabilities.profile_candidate:
            profile_products.append(_profile_product_descriptor(field))
        if field.capabilities.time_height_candidate:
            time_height_products.append(_time_height_product_descriptor(field))
        if _time_series_methods_for_field(field):
            time_series_products.append(_time_series_product_descriptor(field))

    unavailable = [
        OutputProductDescriptor(
            product_key="boundary_layer_depth_time_series",
            product_kind="future_diagnostic",
            status="unavailable",
            display_name="Boundary-layer depth time series",
            aggregation_methods=[],
            required_fields=["theta", "qv", "surface_fluxes"],
            reason="future_diagnostic_method_not_validated",
            caveats=[
                "boundary_layer_depth_proxy_not_implemented",
                "method_must_be_documented_and_tested_before_science_use",
            ],
        )
    ]
    unavailable.extend(_near_surface_wind_unavailable_descriptors(catalog.available_fields))
    unavailable.extend(
        _unavailable_product_descriptor(field) for field in catalog.unavailable_fields
    )
    return OutputProductCatalogResponse(
        result_id=metadata.result_id,
        run_id=metadata.run_id,
        scenario_id=metadata.scenario_id,
        source_model=metadata.source_model,
        available_profile_products=profile_products,
        available_time_height_products=time_height_products,
        available_time_series_products=time_series_products,
        unavailable_products=unavailable,
        provenance=_provenance(
            metadata,
            processing_method="backend_output_product_catalog",
            rendering_method="profile_time_height_time_series_product_options",
            provenance_label=(
                "CM1-derived output-product catalog; backend-owned bounded products; "
                "raw NetCDF stays backend-owned"
            ),
        ),
        caveats=_dedupe(
            [
                *catalog.caveats,
                "diagnostics_lab_ui_not_added",
                "browser_does_not_parse_raw_netcdf",
            ]
        ),
    )


def vertical_profile(
    settings: CloudChamberSettings,
    result_id: str,
    *,
    field: str,
    time_index: int,
    aggregation_method: ProfileAggregationMethod,
    x_index: int | None = None,
    y_index: int | None = None,
) -> VerticalProfileResponse:
    """Return a bounded vertical profile product for a supported field."""
    metadata = get_result_metadata(settings, result_id)
    dataset, close_datasets, local_time_index = _open_dataset_for_time(metadata, time_index)
    try:
        if _field_definition(field) is None:
            raise VisualizationDataError(f"Unsupported profile field: {field}")
        if field not in dataset.data_vars:
            raise VisualizationDataError(
                f"Profile product unavailable; field is missing from this result: {field}"
            )
        data_array = dataset[field]
        dims = _field_dimensions(data_array)
        visual_field = _visualizable_field(metadata, dataset, field)
        if not visual_field.capabilities.profile_candidate:
            raise VisualizationDataError(f"Field {field} is not profile-capable.")
        if not dims.time or not dims.vertical:
            raise VisualizationDataError(f"Field {field} requires time and vertical dimensions.")
        _validate_index(local_time_index, int(data_array.sizes[dims.time]), "time_index")
        at_time = data_array.isel({dims.time: local_time_index})
        profile_values, finite_counts, non_finite_counts = _profile_product_values(
            at_time,
            dims=dims,
            aggregation_method=aggregation_method,
            x_index=x_index,
            y_index=y_index,
        )
        resolved_time = _resolved_output_time(metadata, dataset, dims.time, time_index)
        caveats = _dedupe(
            [
                *_field_caveats(field, visual_field.coordinate_names),
                "json_profile_product_mvp",
                "native_grid_profile_no_interpolation",
                *resolved_time.time_caveats,
                *(
                    ["selected_column_requires_native_x_y_indices"]
                    if aggregation_method == "selected_column"
                    else []
                ),
            ]
        )
        return VerticalProfileResponse(
            result_id=metadata.result_id,
            run_id=metadata.run_id,
            scenario_id=metadata.scenario_id,
            field=visual_field,
            selection=VerticalProfileSelectionMetadata(
                field=field,
                time_index=time_index,
                time_seconds=resolved_time.time_seconds[0],
                source_file=resolved_time.source_files[0],
                local_time_index=resolved_time.local_time_indices[0],
                aggregation_method=aggregation_method,
                x_index=x_index,
                y_index=y_index,
                x_coordinate_value=_coordinate_value(dataset, dims.x, x_index)
                if dims.x and x_index is not None
                else None,
                y_coordinate_value=_coordinate_value(dataset, dims.y, y_index)
                if dims.y and y_index is not None
                else None,
            ),
            vertical_dimension=str(dims.vertical),
            vertical_units=_coordinate_units(dataset, dims.vertical),
            vertical_coordinate_values=_coordinate_values(dataset, dims.vertical),
            values=profile_values,
            finite_counts=finite_counts,
            non_finite_counts=non_finite_counts,
            aggregation_method=aggregation_method,
            provenance=_provenance(
                metadata,
                processing_method="backend_xarray_vertical_profile_product",
                rendering_method="json_vertical_profile",
                provenance_label=(
                    "CM1-derived vertical profile product; backend aggregation; "
                    "native vertical coordinate; no interpolation"
                ),
            ),
            caveats=caveats,
        )
    finally:
        _close_all(close_datasets)


def time_height_product(
    settings: CloudChamberSettings,
    result_id: str,
    *,
    field: str,
    aggregation_method: TimeHeightAggregationMethod,
    threshold: float | None = None,
) -> TimeHeightResponse:
    """Return a bounded time-height product for a supported 3-D field."""
    metadata = get_result_metadata(settings, result_id)
    dataset, close_datasets = _open_dataset_sequence(metadata)
    try:
        if _field_definition(field) is None:
            raise VisualizationDataError(f"Unsupported time-height field: {field}")
        if field not in dataset.data_vars:
            raise VisualizationDataError(
                f"Time-height product unavailable; field is missing from this result: {field}"
            )
        data_array = dataset[field]
        dims = _field_dimensions(data_array)
        visual_field = _visualizable_field(metadata, dataset, field)
        if not visual_field.capabilities.time_height_candidate:
            raise VisualizationDataError(f"Field {field} is not time-height-capable.")
        if not dims.time or not dims.vertical:
            raise VisualizationDataError(f"Field {field} requires time and vertical dimensions.")
        if not dims.y or not dims.x:
            raise VisualizationDataError(
                f"Field {field} requires horizontal dimensions for time-height aggregation."
            )
        resolved_threshold = (
            QC_CLOUD_THRESHOLD_KG_KG
            if aggregation_method == "cloud_fraction" and threshold is None
            else threshold
        )
        values, finite_counts, non_finite_counts = _time_height_product_values(
            data_array,
            dims=dims,
            aggregation_method=aggregation_method,
            threshold=resolved_threshold,
        )
        time_axis = _resolved_output_time_axis(
            metadata,
            dataset,
            dims.time,
            time_size=int(data_array.sizes[dims.time]),
        )
        caveats = _dedupe(
            [
                *_field_caveats(field, visual_field.coordinate_names),
                "json_time_height_product_mvp",
                "native_grid_time_height_no_interpolation",
                *time_axis.time_caveats,
                *(
                    [f"cloud_fraction_threshold_kg_kg:{resolved_threshold:g}"]
                    if aggregation_method == "cloud_fraction" and resolved_threshold is not None
                    else []
                ),
            ]
        )
        return TimeHeightResponse(
            result_id=metadata.result_id,
            run_id=metadata.run_id,
            scenario_id=metadata.scenario_id,
            field=visual_field,
            selection=TimeHeightSelectionMetadata(
                field=field,
                aggregation_method=aggregation_method,
                threshold=resolved_threshold,
            ),
            time_axis=time_axis,
            vertical_dimension=str(dims.vertical),
            vertical_units=_coordinate_units(dataset, dims.vertical),
            vertical_coordinate_values=_coordinate_values(dataset, dims.vertical),
            shape=[len(values), len(values[0]) if values else 0],
            size_class=_array_size_class(len(values) * (len(values[0]) if values else 0)),
            values=values,
            finite_counts=finite_counts,
            non_finite_counts=non_finite_counts,
            aggregation_method=aggregation_method,
            provenance=_provenance(
                metadata,
                processing_method="backend_xarray_time_height_product",
                rendering_method="json_time_height_array",
                provenance_label=(
                    "CM1-derived time-height product; backend aggregation; "
                    "global output time index; no browser NetCDF parsing"
                ),
            ),
            caveats=caveats,
        )
    finally:
        _close_all(close_datasets)


def time_series_product(
    settings: CloudChamberSettings,
    result_id: str,
    *,
    field: str,
    aggregation_method: TimeSeriesAggregationMethod,
    threshold: float | None = None,
) -> TimeSeriesResponse:
    """Return a bounded field time-series product for an evolved run."""
    metadata = get_result_metadata(settings, result_id)
    dataset, close_datasets = _open_dataset_sequence(metadata)
    try:
        if _field_definition(field) is None:
            raise VisualizationDataError(f"Unsupported time-series field: {field}")
        if field not in dataset.data_vars:
            raise VisualizationDataError(
                f"Time-series product unavailable; field is missing from this result: {field}"
            )
        data_array = dataset[field]
        dims = _field_dimensions(data_array)
        visual_field = _visualizable_field(metadata, dataset, field)
        if not dims.time:
            raise VisualizationDataError(f"Field {field} requires a time dimension.")
        if aggregation_method not in _time_series_methods_for_field(visual_field):
            raise VisualizationDataError(
                f"Field {field} does not support {aggregation_method} time-series products."
            )
        resolved_threshold = (
            QC_CLOUD_THRESHOLD_KG_KG
            if aggregation_method == "cloud_fraction" and threshold is None
            else threshold
        )
        values, finite_counts, non_finite_counts = _time_series_product_values(
            data_array,
            dims=dims,
            aggregation_method=aggregation_method,
            threshold=resolved_threshold,
        )
        time_axis = _resolved_output_time_axis(
            metadata,
            dataset,
            dims.time,
            time_size=int(data_array.sizes[dims.time]),
        )
        caveats = _dedupe(
            [
                *_field_caveats(field, visual_field.coordinate_names),
                "json_time_series_product_mvp",
                "native_grid_time_series_no_interpolation",
                *time_axis.time_caveats,
                *(
                    [f"cloud_fraction_threshold_kg_kg:{resolved_threshold:g}"]
                    if aggregation_method == "cloud_fraction" and resolved_threshold is not None
                    else []
                ),
            ]
        )
        return TimeSeriesResponse(
            result_id=metadata.result_id,
            run_id=metadata.run_id,
            scenario_id=metadata.scenario_id,
            field=visual_field,
            selection=TimeSeriesSelectionMetadata(
                field=field,
                aggregation_method=aggregation_method,
                threshold=resolved_threshold,
            ),
            time_axis=time_axis,
            units=visual_field.units,
            values=values,
            finite_counts=finite_counts,
            non_finite_counts=non_finite_counts,
            aggregation_method=aggregation_method,
            provenance=_provenance(
                metadata,
                processing_method="backend_xarray_time_series_product",
                rendering_method="json_time_series",
                provenance_label=(
                    "CM1-derived time-series product; backend aggregation; "
                    "global output time index; no browser NetCDF parsing"
                ),
            ),
            caveats=caveats,
        )
    finally:
        _close_all(close_datasets)


def view_defaults(
    settings: CloudChamberSettings,
    result_id: str,
    *,
    time_index: int | None = None,
) -> ViewDefaultsResponse:
    """Return physically interesting default field/time/slice locations."""
    metadata = get_result_metadata(settings, result_id)
    if _should_use_metadata_defaults(metadata):
        return _metadata_view_defaults(metadata, time_index=time_index)

    dataset, close_datasets = _open_dataset_sequence(metadata)
    try:
        fields: dict[str, FieldViewDefaults] = {}
        for field_name in _known_dataset_field_names(dataset):
            fields[field_name] = _field_view_defaults(
                metadata,
                dataset,
                field_name,
                time_index=time_index,
            )
        preferred = _preferred_field(metadata, fields)
        return ViewDefaultsResponse(
            result_id=metadata.result_id,
            run_id=metadata.run_id,
            scenario_id=metadata.scenario_id,
            preferred_field=preferred,
            fields=fields,
            provenance=_provenance(
                metadata,
                processing_method="backend_xarray_interesting_view_defaults",
                rendering_method="field_slice_and_point_cloud_default_selection",
                provenance_label=(
                    "CM1-derived visualization defaults; max-value native-grid location; "
                    "no interpolation"
                ),
            ),
            caveats=_dedupe(
                [
                    "default_locations_are_native_grid_indices",
                    *(
                        ["default_locations_are_selected_time_native_grid_indices"]
                        if time_index is not None
                        else []
                    ),
                    *metadata.warnings,
                    *(["missing_visualization_field:qc"] if "qc" not in fields else []),
                    *(["missing_visualization_field:w"] if "w" not in fields else []),
                ]
            ),
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
    """Return thresholded native-grid points for supported 3-D scalar visualization."""
    if encoding != "json":
        raise VisualizationDataError("Only encoding=json is supported for MVP point clouds.")
    if _field_definition(field) is None:
        raise VisualizationDataError(f"Unsupported visualization field: {field}")
    if field in SIGNED_FLOW_FIELDS:
        raise VisualizationDataError(
            f"Field {field} requires signed-flow 3-D rendering and is slice-only for now."
        )
    if not math.isfinite(threshold) or threshold < 0:
        raise VisualizationDataError("threshold must be a finite non-negative number.")
    if max_points <= 0:
        raise VisualizationDataError("max_points must be greater than 0.")

    metadata = get_result_metadata(settings, result_id)
    dataset, close_datasets, local_time_index = _open_dataset_for_time(metadata, time_index)
    try:
        if field not in dataset.data_vars:
            raise VisualizationDataError(f"Field is not available for this result: {field}")
        data_array = dataset[field]
        dims = _field_dimensions(data_array)
        if not _field_capabilities(field, dims.coordinates).point_cloud:
            raise VisualizationDataError(
                f"Field {field} is available for 2-D slices but not 3-D point-cloud rendering."
            )
        if not dims.time:
            raise VisualizationDataError(f"Field {field} has no time dimension.")
        is_surface_field = field in SURFACE_POINT_FIELDS and not dims.vertical and dims.y and dims.x
        if not is_surface_field and (not dims.vertical or not dims.y or not dims.x):
            raise VisualizationDataError(f"Field {field} must have native vertical/y/x dimensions.")
        _validate_index(local_time_index, int(data_array.sizes[dims.time]), "time_index")
        at_time = data_array.isel({dims.time: local_time_index})
        source_points = (
            _threshold_surface_points(at_time, dims=dims, dataset=dataset, threshold=threshold)
            if is_surface_field
            else _threshold_points(
                at_time,
                dims=dims,
                dataset=dataset,
                threshold=threshold,
            )
        )
        source_count = len(source_points)
        selected_field_stats = _slice_stats(at_time)
        stride = max(1, math.ceil(source_count / max_points)) if source_count else 1
        returned_points = source_points[::stride][:max_points]
        values = [point[3] for point in source_points]
        vertical_extent = (
            _surface_vertical_extent(dataset)
            if is_surface_field
            else _coordinate_extent(dataset, dims.vertical)
        )
        vertical_extent_name = "z" if is_surface_field else str(dims.vertical)
        coordinate_extents = {
            str(dims.x): _coordinate_extent(dataset, dims.x),
            str(dims.y): _coordinate_extent(dataset, dims.y),
            vertical_extent_name: vertical_extent,
        }
        finite_extents = {
            name: extent for name, extent in coordinate_extents.items() if extent is not None
        }
        active_z_values = [point[2] for point in source_points]
        max_location = _max_point_location(source_points)
        visual_field = _visualizable_field(metadata, dataset, field)
        caveats = _dedupe(
            [
                *_field_caveats(field, visual_field.coordinate_names),
                "native_grid_thresholded_point_cloud",
                f"visualizer_interpretation_of_cm1_{field}",
                *(["surface_field_rendered_on_domain_floor"] if is_surface_field else []),
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
                time_seconds=_time_value_seconds(dataset, dims.time, local_time_index)
                or _metadata_time_seconds(metadata, time_index),
                threshold=threshold,
                max_points=max_points,
            ),
            coordinate_units={
                str(dims.x): _coordinate_units(dataset, dims.x),
                str(dims.y): _coordinate_units(dataset, dims.y),
                vertical_extent_name: vertical_extent.units
                if vertical_extent
                else _coordinate_units(dataset, dims.vertical),
            },
            coordinate_extents=finite_extents,
            point_order=["x", "y", "z", "value"],
            points=returned_points,
            stats=PointCloudStats(
                source_count=source_count,
                returned_count=len(returned_points),
                field_min_value=selected_field_stats.min,
                field_max_value=selected_field_stats.max,
                field_mean_value=selected_field_stats.mean,
                field_finite_count=selected_field_stats.finite_count,
                field_non_finite_count=selected_field_stats.non_finite_count,
                min_value=min(values) if values else None,
                max_value=max(values) if values else None,
                active_z_min=min(active_z_values) if active_z_values else None,
                active_z_max=max(active_z_values) if active_z_values else None,
                max_value_location=max_location,
                downsampled=source_count > max_points,
                downsample_stride=stride,
            ),
            provenance=_provenance(
                metadata,
                processing_method="backend_xarray_native_grid_threshold",
                rendering_method="thresholded_point_cloud",
                provenance_label=(
                    f"CM1-derived {visual_field.display_name.lower()} "
                    f"{'floor layer' if is_surface_field else 'point cloud'}; "
                    "native-grid threshold; visualizer interpretation"
                ),
            ),
            caveats=caveats,
        )
    finally:
        _close_all(close_datasets)


def _field_view_defaults(
    metadata: ResultMetadata,
    dataset: Any,
    field_name: str,
    *,
    time_index: int | None = None,
) -> FieldViewDefaults:
    data_array = dataset[field_name]
    dims = _field_dimensions(data_array)
    caveats = _field_caveats(field_name, dims.coordinates)
    if not dims.time or not dims.vertical or not dims.y or not dims.x:
        return _fallback_view_defaults(
            dataset,
            data_array,
            field_name=field_name,
            dims=dims,
            source="domain_center_missing_required_dimensions",
            caveats=caveats,
            selected_time_index=time_index,
        )

    selected_time_seconds: float | None = None
    search_array = data_array
    if time_index is not None:
        _validate_index(time_index, int(data_array.sizes[dims.time]), "time_index")
        search_array = data_array.isel({dims.time: time_index})
        selected_time_seconds = _time_value_seconds(dataset, dims.time, time_index)
        caveats = [*caveats, "default_location_uses_selected_time_maximum"]
    values = search_array.values
    best_value: float | None = None
    best_index: tuple[int, ...] | None = None
    for native_index in itertools.product(*(range(int(size)) for size in search_array.shape)):
        raw_value = values[native_index]
        try:
            numeric = float(raw_value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(numeric):
            continue
        if best_value is None or numeric > best_value:
            best_value = numeric
            best_index = native_index

    if best_index is None:
        return _fallback_view_defaults(
            dataset,
            data_array,
            field_name=field_name,
            dims=dims,
            source="domain_center_no_finite_values",
            caveats=[*caveats, f"no_finite_values_in_{field_name}"],
            selected_time_index=time_index,
        )

    time_axis = data_array.dims.index(dims.time)
    vertical_axis = data_array.dims.index(dims.vertical)
    y_axis = data_array.dims.index(dims.y)
    x_axis = data_array.dims.index(dims.x)
    if time_index is None:
        resolved_time_index = int(best_index[time_axis])
        resolved_best_index = best_index
    else:
        resolved_time_index = time_index
        axes_without_time = [dimension for dimension in data_array.dims if dimension != dims.time]
        resolved_lookup = dict(zip(axes_without_time, best_index, strict=True))
        resolved_best_index = tuple(
            time_index if dimension == dims.time else int(resolved_lookup[dimension])
            for dimension in data_array.dims
        )
    return FieldViewDefaults(
        field=field_name,
        time_index=resolved_time_index,
        time_seconds=_time_value_seconds(dataset, dims.time, resolved_time_index),
        horizontal_level_index=int(resolved_best_index[vertical_axis]),
        vertical_x_index=int(resolved_best_index[y_axis]),
        vertical_y_index=int(resolved_best_index[x_axis]),
        source=(
            f"selected_time_max_{field_name}_native_grid_location"
            if time_index is not None
            else f"max_{field_name}_native_grid_location"
        ),
        max_value=best_value,
        selected_time_index=time_index,
        selected_time_seconds=selected_time_seconds,
        caveats=_dedupe([*caveats, "default_location_uses_field_maximum"]),
    )


def _fallback_view_defaults(
    dataset: Any,
    data_array: Any,
    *,
    field_name: str,
    dims: _FieldDimensions,
    source: str,
    caveats: list[str],
    selected_time_index: int | None = None,
) -> FieldViewDefaults:
    time_size = int(data_array.sizes[dims.time]) if dims.time else 1
    vertical_size = int(data_array.sizes[dims.vertical]) if dims.vertical else 1
    y_size = int(data_array.sizes[dims.y]) if dims.y else 1
    x_size = int(data_array.sizes[dims.x]) if dims.x else 1
    time_index = (
        max(0, min(selected_time_index, time_size - 1))
        if selected_time_index is not None
        else max(0, time_size - 1)
    )
    return FieldViewDefaults(
        field=field_name,
        time_index=time_index,
        time_seconds=_time_value_seconds(dataset, dims.time, time_index),
        horizontal_level_index=max(0, vertical_size // 2),
        vertical_x_index=max(0, y_size // 2),
        vertical_y_index=max(0, x_size // 2),
        source=source,
        max_value=None,
        selected_time_index=selected_time_index,
        selected_time_seconds=_time_value_seconds(dataset, dims.time, time_index)
        if selected_time_index is not None
        else None,
        caveats=_dedupe([*caveats, "default_location_fell_back_to_domain_center"]),
    )


def _preferred_field(metadata: ResultMetadata, fields: Mapping[str, object]) -> str | None:
    if metadata.run_recipe == "triggered_deep_potential" and "w" in fields:
        return "w"
    return "qc" if "qc" in fields else next(iter(fields), None)


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
    dataset, close_datasets, local_time_index = _open_dataset_for_time(metadata, time_index)
    try:
        if _field_definition(field) is None:
            raise VisualizationDataError(f"Unsupported visualization field: {field}")
        if field not in dataset.data_vars:
            raise VisualizationDataError(f"Field is not available for this result: {field}")
        data_array = dataset[field]
        dims = _field_dimensions(data_array)
        if not dims.time:
            raise VisualizationDataError(f"Field {field} has no time dimension.")
        _validate_index(local_time_index, int(data_array.sizes[dims.time]), "time_index")
        at_time = data_array.isel({dims.time: local_time_index})
        spatial_dims = [dimension for dimension in at_time.dims]
        if len(spatial_dims) == 2 and dims.y and dims.x and not dims.vertical:
            if orientation != "horizontal":
                raise VisualizationDataError(
                    f"Field {field} is a surface field and only supports horizontal slices."
                )
            _validate_index(level_index, 1, "level_index")
            sliced = at_time.transpose(dims.y, dims.x)
            values = _json_values(sliced)
            stats = _slice_stats(sliced)
            visual_field = _visualizable_field(metadata, dataset, field)
            surface_extent = _surface_vertical_extent(dataset)
            selected_value = surface_extent.min if surface_extent else 0.0
            level_units = surface_extent.units if surface_extent else None
            caveats = _dedupe(
                [
                    *_field_caveats(field, visual_field.coordinate_names),
                    "surface_field_no_vertical_dimension",
                    "surface_field_rendered_on_domain_floor",
                    "native_grid_view_no_interpolation",
                    "json_numeric_slice_mvp",
                ]
            )
            return SliceResponse(
                result_id=metadata.result_id,
                run_id=metadata.run_id,
                scenario_id=metadata.scenario_id,
                field=visual_field,
                selection=SliceSelectionMetadata(
                    time_index=time_index,
                    time_seconds=_time_value_seconds(dataset, dims.time, local_time_index)
                    or _metadata_time_seconds(metadata, time_index),
                    orientation=orientation,
                    selected_dimension="surface",
                    selected_index=0,
                    selected_coordinate_value=selected_value,
                    level_units=level_units,
                    level_coordinate_value=selected_value,
                    level_meters=_meters_if_safe(selected_value, level_units),
                ),
                coordinate_units={
                    dimension: _coordinate_units(dataset, dimension) for dimension in sliced.dims
                },
                shape=[int(size) for size in sliced.shape],
                dimension_order=[str(dimension) for dimension in sliced.dims],
                data_encoding=encoding,
                values=values,
                stats=stats,
                provenance=_provenance(metadata),
                caveats=caveats,
            )
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
        selected_coordinate_value = _coordinate_value(dataset, selected_dimension, level_index)
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
            time_seconds=_time_value_seconds(dataset, dims.time, local_time_index)
            or _metadata_time_seconds(metadata, time_index),
            orientation=orientation,
            selected_dimension=selected_dimension,
            selected_index=level_index,
            selected_coordinate_value=selected_coordinate_value,
            level_units=level_units,
            level_coordinate_value=selected_coordinate_value
            if selected_dimension == vertical_dim
            else None,
            level_meters=_meters_if_safe(selected_coordinate_value, level_units)
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


def _open_dataset_for_time(metadata: ResultMetadata, time_index: int) -> tuple[Any, list[Any], int]:
    time_steps = metadata.time_steps
    if time_steps is not None:
        _validate_index(time_index, time_steps, "time_index")
    paths = [Path(path).expanduser() for path in metadata.model_output_paths]
    if (
        time_steps is not None
        and time_steps > 1
        and len(paths) == time_steps
        and 0 <= time_index < len(paths)
    ):
        xarray = importlib.import_module("xarray")
        path = paths[time_index]
        try:
            dataset = xarray.open_dataset(path)
        except Exception as exc:
            raise VisualizationDataError(f"Could not open NetCDF output {path}: {exc}") from exc
        normalized = _normalize_single_time_file(dataset, metadata, time_index)
        close_datasets = [dataset]
        if normalized is not dataset:
            close_datasets.append(normalized)
        return normalized, close_datasets, 0

    dataset, close_datasets = _open_dataset_sequence(metadata)
    return dataset, close_datasets, time_index


def _normalize_time_dimension(dataset: Any, file_index: int) -> Any:
    if "time" not in dataset.dims:
        return dataset.expand_dims(time=[float(file_index)])
    if "time" not in dataset.coords:
        size = int(dataset.sizes["time"])
        return dataset.assign_coords(time=[float(file_index + offset) for offset in range(size)])
    return dataset


def _normalize_single_time_file(dataset: Any, metadata: ResultMetadata, time_index: int) -> Any:
    if "time" not in dataset.dims:
        return dataset.expand_dims(
            time=[_metadata_time_seconds(metadata, time_index) or float(time_index)]
        )
    if "time" not in dataset.coords:
        size = int(dataset.sizes["time"])
        if size == 1:
            return dataset.assign_coords(
                time=[_metadata_time_seconds(metadata, time_index) or float(time_index)]
            )
        return dataset.assign_coords(time=[float(time_index + offset) for offset in range(size)])
    return dataset


def _visualizable_field(
    metadata: ResultMetadata,
    dataset: Any,
    field_name: str,
) -> VisualizableField:
    data_array = dataset[field_name]
    definition = _require_field_definition(field_name)
    coordinates = _field_dimensions(data_array).coordinates
    capabilities = _field_capabilities(field_name, coordinates)
    return VisualizableField(
        raw_field_name=field_name,
        canonical_field_name=definition.canonical_field_name,
        display_name=definition.display_name,
        units=_attr_string(data_array.attrs.get("units")),
        dimensions=[str(dimension) for dimension in data_array.dims],
        shape=[int(size) for size in data_array.shape],
        native_grid=_native_grid_label(coordinates),
        native_grid_class=_native_grid_class(coordinates),
        coordinate_names=coordinates,
        time_coordinate_values=_coordinate_values(dataset, coordinates.time),
        time_available=coordinates.time is not None,
        field_family=definition.field_family,
        capabilities=capabilities,
        frontend_consumer_guidance=definition.frontend_consumer_guidance,
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


def _threshold_surface_points(
    data_array: Any,
    *,
    dims: _FieldDimensions,
    dataset: Any,
    threshold: float,
) -> list[list[float]]:
    if not dims.y or not dims.x:
        return []
    points: list[list[float]] = []
    values = data_array.values
    y_values = _coordinate_values(dataset, dims.y)
    x_values = _coordinate_values(dataset, dims.x)
    y_axis = data_array.dims.index(dims.y)
    x_axis = data_array.dims.index(dims.x)
    z_value = _surface_vertical_extent(dataset).min

    # Iterate in native array order so stride downsampling is deterministic.
    for native_index in itertools.product(*(range(int(size)) for size in data_array.shape)):
        raw_value = values[native_index]
        try:
            numeric = float(raw_value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(numeric) or numeric < threshold:
            continue
        y_index = native_index[y_axis]
        x_index = native_index[x_axis]
        points.append(
            [
                _coordinate_number(x_values, x_index),
                _coordinate_number(y_values, y_index),
                z_value,
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


def _coordinate_extent(dataset: Any, coordinate_name: str | None) -> CoordinateExtent | None:
    values = [
        value
        for value in (_coordinate_number_values(dataset, coordinate_name))
        if math.isfinite(value)
    ]
    if not values or coordinate_name is None:
        return None
    return CoordinateExtent(
        min=min(values),
        max=max(values),
        units=_coordinate_units(dataset, coordinate_name),
    )


def _surface_vertical_extent(dataset: Any) -> CoordinateExtent:
    for coordinate_name in SURFACE_VERTICAL_CANDIDATES:
        extent = _coordinate_extent(dataset, coordinate_name)
        if extent is not None:
            return extent
    return CoordinateExtent(min=0.0, max=1.0, units=None)


def _coordinate_number_values(dataset: Any, coordinate_name: str | None) -> list[float]:
    if coordinate_name is None:
        return []
    return [
        _coordinate_number(_coordinate_values(dataset, coordinate_name), index)
        for index in range(int(dataset.sizes.get(coordinate_name, 0)))
    ]


def _max_point_location(points: list[list[float]]) -> dict[str, float] | None:
    if not points:
        return None
    best = max(points, key=lambda point: point[3])
    return {"x": best[0], "y": best[1], "z": best[2], "value": best[3]}


def _validate_index(index: int, size: int, label: str) -> None:
    if index < 0 or index >= size:
        raise VisualizationDataError(f"{label}={index} is outside valid range 0..{size - 1}.")


def _native_grid_label(coordinates: FieldCoordinateMetadata) -> str:
    spatial = [coordinates.vertical, coordinates.y, coordinates.x]
    if all(spatial):
        return "/".join(str(dimension) for dimension in spatial)
    if not coordinates.vertical and coordinates.y and coordinates.x:
        return f"surface/{coordinates.y}/{coordinates.x}"
    return "unknown_native_grid"


def _native_grid_class(coordinates: FieldCoordinateMetadata) -> str:
    if coordinates.time and coordinates.vertical and coordinates.y and coordinates.x:
        return "volume_3d"
    if coordinates.time and not coordinates.vertical and coordinates.y and coordinates.x:
        return "surface_2d"
    if coordinates.time and coordinates.vertical and not coordinates.y and not coordinates.x:
        return "vertical_profile"
    if coordinates.time and not coordinates.vertical and not coordinates.y and not coordinates.x:
        return "time_series"
    return "unknown"


def _field_capabilities(
    field_name: str,
    coordinates: FieldCoordinateMetadata,
) -> FieldCapabilityMetadata:
    definition = _require_field_definition(field_name)
    grid_class = _native_grid_class(coordinates)
    slice_supported = grid_class in {"volume_3d", "surface_2d"}
    point_cloud_supported = (
        definition.point_cloud_allowed
        and slice_supported
        and field_name.lower() not in SIGNED_FLOW_FIELDS
    )
    selected_point_supported = (
        slice_supported and coordinates.y is not None and coordinates.x is not None
    )
    selected_column_supported = (
        selected_point_supported and coordinates.vertical is not None and grid_class == "volume_3d"
    )
    profile_candidate = (
        definition.profile_candidate
        and coordinates.time is not None
        and coordinates.vertical is not None
    )
    time_height_candidate = (
        definition.time_height_candidate
        and coordinates.time is not None
        and coordinates.vertical is not None
    )
    return FieldCapabilityMetadata(
        slice=slice_supported,
        point_cloud=point_cloud_supported,
        selected_point=selected_point_supported,
        selected_column=selected_column_supported,
        profile_candidate=profile_candidate,
        time_height_candidate=time_height_candidate,
        render_ready_candidate=definition.render_ready_candidate and point_cloud_supported,
        external_export_candidate=(
            definition.external_export_candidate and coordinates.time is not None
        ),
    )


def _profile_product_descriptor(field: VisualizableField) -> OutputProductDescriptor:
    methods: list[str] = ["domain_mean", "domain_min", "domain_max"]
    if field.capabilities.selected_column:
        methods.append("selected_column")
    return OutputProductDescriptor(
        product_key=f"profile:{field.raw_field_name}",
        product_kind="vertical_profile",
        status="available",
        raw_field_name=field.raw_field_name,
        canonical_field_name=field.canonical_field_name,
        display_name=f"{field.display_name} vertical profile",
        units=field.units,
        aggregation_methods=methods,
        required_fields=[field.raw_field_name],
        caveats=_dedupe(["bounded_json_profile", *field.caveats]),
    )


def _time_height_product_descriptor(field: VisualizableField) -> OutputProductDescriptor:
    methods: list[str] = ["domain_mean", "domain_min", "domain_max"]
    if field.canonical_field_name == "cloud_water":
        methods.insert(0, "cloud_fraction")
    return OutputProductDescriptor(
        product_key=f"time_height:{field.raw_field_name}",
        product_kind="time_height",
        status="available",
        raw_field_name=field.raw_field_name,
        canonical_field_name=field.canonical_field_name,
        display_name=f"{field.display_name} time-height",
        units=field.units,
        aggregation_methods=methods,
        required_fields=[field.raw_field_name],
        caveats=_dedupe(["bounded_json_time_height", *field.caveats]),
    )


def _time_series_product_descriptor(field: VisualizableField) -> OutputProductDescriptor:
    methods = _time_series_methods_for_field(field)
    return OutputProductDescriptor(
        product_key=f"time_series:{field.raw_field_name}",
        product_kind="time_series",
        status="available",
        raw_field_name=field.raw_field_name,
        canonical_field_name=field.canonical_field_name,
        display_name=f"{field.display_name} time series",
        units=field.units,
        aggregation_methods=list(methods),
        required_fields=[field.raw_field_name],
        caveats=_dedupe(["bounded_json_time_series", *field.caveats]),
    )


def _unavailable_product_descriptor(field: UnavailableField) -> OutputProductDescriptor:
    return OutputProductDescriptor(
        product_key=f"unavailable:{field.raw_field_name}",
        product_kind="future_diagnostic",
        status="unavailable",
        raw_field_name=field.raw_field_name,
        canonical_field_name=field.canonical_field_name,
        display_name=field.display_name,
        required_fields=[field.raw_field_name],
        reason=field.reason,
        caveats=field.caveats,
    )


def _near_surface_wind_unavailable_descriptors(
    fields: list[VisualizableField],
) -> list[OutputProductDescriptor]:
    descriptors: list[OutputProductDescriptor] = []
    for field in fields:
        if field.canonical_field_name not in {"east_west_wind", "north_south_wind"}:
            continue
        descriptors.append(
            OutputProductDescriptor(
                product_key=f"near_surface_wind_time_series:{field.raw_field_name}",
                product_kind="future_diagnostic",
                status="unavailable",
                raw_field_name=field.raw_field_name,
                canonical_field_name=field.canonical_field_name,
                display_name=f"Near-surface {field.display_name.lower()} time series",
                required_fields=[field.raw_field_name],
                reason="near_surface_wind_diagnostic_not_implemented",
                caveats=[
                    "lowest_level_wind_selection_method_not_finalized",
                    "native_staggered_wind_component",
                    "no_vector_interpolation",
                    "wind_component_not_wind_gust_outflow_or_rotation_diagnostic",
                ],
            )
        )
    return descriptors


def _time_series_methods_for_field(
    field: VisualizableField,
) -> tuple[TimeSeriesAggregationMethod, ...]:
    if not field.time_available:
        return ()
    if field.canonical_field_name == "cloud_water":
        return ("cloud_fraction", "domain_max", "domain_mean")
    if field.native_grid_class in {"volume_3d", "surface_2d"}:
        return ("domain_max", "domain_mean", "domain_min")
    return ()


def _profile_product_values(
    at_time: Any,
    *,
    dims: _FieldDimensions,
    aggregation_method: ProfileAggregationMethod,
    x_index: int | None,
    y_index: int | None,
) -> tuple[list[float | None], list[int], list[int]]:
    if dims.vertical is None:
        raise VisualizationDataError("Profile product requires a vertical dimension.")
    vertical_size = int(at_time.sizes[dims.vertical])
    if aggregation_method == "selected_column":
        if dims.y is None or dims.x is None:
            raise VisualizationDataError("Selected-column profile requires y/x dimensions.")
        if x_index is None or y_index is None:
            raise VisualizationDataError("selected_column profile requires x_index and y_index.")
        _validate_index(y_index, int(at_time.sizes[dims.y]), "y_index")
        _validate_index(x_index, int(at_time.sizes[dims.x]), "x_index")
        selected = at_time.isel({dims.y: y_index, dims.x: x_index}).transpose(dims.vertical)
        values = _json_vector(selected.values)
        finite = [1 if value is not None else 0 for value in values]
        return values, finite, [1 - count for count in finite]

    if dims.y is None or dims.x is None:
        raise VisualizationDataError("Domain profile aggregation requires y/x dimensions.")
    reduced = _reduce_data_array(
        at_time,
        reduce_dims=[dims.y, dims.x],
        aggregation_method=aggregation_method,
    ).transpose(dims.vertical)
    finite_counts, non_finite_counts = _finite_counts(
        at_time.transpose(dims.vertical, dims.y, dims.x).values,
        reduce_axes=(1, 2),
        total_per_cell=int(at_time.sizes[dims.y]) * int(at_time.sizes[dims.x]),
    )
    values = _json_vector(reduced.values)
    if len(values) != vertical_size:
        raise VisualizationDataError("Profile product produced an unexpected vertical shape.")
    return values, _json_int_vector(finite_counts), _json_int_vector(non_finite_counts)


def _time_height_product_values(
    data_array: Any,
    *,
    dims: _FieldDimensions,
    aggregation_method: TimeHeightAggregationMethod,
    threshold: float | None,
) -> tuple[list[list[float | None]], list[list[int]], list[list[int]]]:
    if dims.time is None or dims.vertical is None or dims.y is None or dims.x is None:
        raise VisualizationDataError("Time-height product requires time/z/y/x dimensions.")
    ordered = data_array.transpose(dims.time, dims.vertical, dims.y, dims.x)
    finite_counts, non_finite_counts = _finite_counts(
        ordered.values,
        reduce_axes=(2, 3),
        total_per_cell=int(data_array.sizes[dims.y]) * int(data_array.sizes[dims.x]),
    )
    if aggregation_method == "cloud_fraction":
        if threshold is None or not math.isfinite(threshold):
            raise VisualizationDataError("cloud_fraction requires a finite threshold.")
        values = _fraction_values(ordered.values, threshold=threshold, reduce_axes=(2, 3))
        return (
            _json_matrix(values),
            _json_int_matrix(finite_counts),
            _json_int_matrix(non_finite_counts),
        )
    reduced = _reduce_data_array(
        ordered,
        reduce_dims=[dims.y, dims.x],
        aggregation_method=aggregation_method,
    ).transpose(dims.time, dims.vertical)
    return (
        _json_matrix(reduced.values),
        _json_int_matrix(finite_counts),
        _json_int_matrix(non_finite_counts),
    )


def _time_series_product_values(
    data_array: Any,
    *,
    dims: _FieldDimensions,
    aggregation_method: TimeSeriesAggregationMethod,
    threshold: float | None,
) -> tuple[list[float | None], list[int], list[int]]:
    if dims.time is None:
        raise VisualizationDataError("Time-series product requires a time dimension.")
    reduce_dims = [dimension for dimension in data_array.dims if dimension != dims.time]
    ordered = data_array.transpose(dims.time, *reduce_dims)
    reduce_axes = tuple(range(1, len(ordered.shape)))
    total_per_time = math.prod(int(data_array.sizes[dimension]) for dimension in reduce_dims)
    finite_counts, non_finite_counts = _finite_counts(
        ordered.values,
        reduce_axes=reduce_axes,
        total_per_cell=total_per_time,
    )
    if aggregation_method == "cloud_fraction":
        if threshold is None or not math.isfinite(threshold):
            raise VisualizationDataError("cloud_fraction requires a finite threshold.")
        values = _fraction_values(ordered.values, threshold=threshold, reduce_axes=reduce_axes)
        return (
            _json_vector(values),
            _json_int_vector(finite_counts),
            _json_int_vector(non_finite_counts),
        )
    reduced = _reduce_data_array(
        ordered,
        reduce_dims=reduce_dims,
        aggregation_method=aggregation_method,
    ).transpose(dims.time)
    return (
        _json_vector(reduced.values),
        _json_int_vector(finite_counts),
        _json_int_vector(non_finite_counts),
    )


def _reduce_data_array(
    data_array: Any,
    *,
    reduce_dims: list[str],
    aggregation_method: str,
) -> Any:
    finite = data_array.where(np.isfinite(data_array))
    if aggregation_method == "domain_mean":
        return finite.mean(dim=reduce_dims, skipna=True)
    if aggregation_method == "domain_min":
        return finite.min(dim=reduce_dims, skipna=True)
    if aggregation_method == "domain_max":
        return finite.max(dim=reduce_dims, skipna=True)
    raise VisualizationDataError(f"Unsupported aggregation method: {aggregation_method}")


def _finite_counts(
    values: Any,
    *,
    reduce_axes: tuple[int, ...],
    total_per_cell: int,
) -> tuple[Any, Any]:
    finite_mask = np.isfinite(values)
    finite_counts = finite_mask.sum(axis=reduce_axes)
    non_finite_counts = total_per_cell - finite_counts
    return finite_counts, non_finite_counts


def _fraction_values(values: Any, *, threshold: float, reduce_axes: tuple[int, ...]) -> Any:
    finite_mask = np.isfinite(values)
    cloudy_counts = (finite_mask & (values >= threshold)).sum(axis=reduce_axes)
    finite_counts = finite_mask.sum(axis=reduce_axes)
    return np.divide(
        cloudy_counts,
        finite_counts,
        out=np.full_like(cloudy_counts, np.nan, dtype=float),
        where=finite_counts > 0,
    )


def _resolved_output_time(
    metadata: ResultMetadata,
    dataset: Any,
    time_dimension: str | None,
    time_index: int,
) -> OutputTimeAxisMetadata:
    return _resolved_output_time_axis(
        metadata,
        dataset,
        time_dimension,
        time_size=1,
        requested_indices=[time_index],
    )


def _resolved_output_time_axis(
    metadata: ResultMetadata,
    dataset: Any,
    time_dimension: str | None,
    *,
    time_size: int,
    requested_indices: list[int] | None = None,
) -> OutputTimeAxisMetadata:
    indices = requested_indices if requested_indices is not None else list(range(time_size))
    manifest, manifest_caveats = _load_output_product_manifest(metadata)
    time_seconds: list[float | None] = []
    source_time_values: list[float | str | None] = []
    source_files: list[str | None] = []
    local_time_indices: list[int | None] = []
    sources: list[str] = []
    caveats = list(manifest_caveats)
    for index in indices:
        if manifest is not None:
            try:
                resolved = resolve_time_index(manifest, index)
            except OutputProductManifestError as exc:
                caveats.append(f"output_time_index_resolution_failed:{exc}")
            else:
                time_seconds.append(resolved.time_seconds)
                source_time_values.append(resolved.time_seconds)
                source_files.append(resolved.source_file)
                local_time_indices.append(resolved.local_time_index)
                sources.append(resolved.time_source)
                caveats.extend(resolved.time_caveats)
                continue
        time_seconds.append(_time_value_seconds(dataset, time_dimension, index))
        source_time_values.append(_coordinate_value(dataset, time_dimension, index))
        source_files.append(None)
        local_time_indices.append(index)
        sources.append("dataset_sequence_index")
    return OutputTimeAxisMetadata(
        time_indices=indices,
        time_seconds=time_seconds,
        source_time_values=source_time_values,
        source_files=source_files,
        local_time_indices=local_time_indices,
        time_source=sources[0]
        if sources and all(source == sources[0] for source in sources)
        else None,
        time_caveats=_dedupe(caveats),
    )


def _load_output_product_manifest(metadata: ResultMetadata) -> tuple[Any | None, list[str]]:
    candidate_paths = [
        Path(path).expanduser()
        for path in metadata.processed_artifacts
        if Path(path).name == "output_product_manifest.json"
    ]
    source_paths = [Path(path).expanduser() for path in metadata.model_output_paths]
    if source_paths:
        candidate_paths.append(default_output_product_manifest_path(source_paths[0].parent))
    for path in _dedupe([str(path) for path in candidate_paths]):
        manifest_path = Path(path)
        if not manifest_path.exists():
            continue
        try:
            return output_product_manifest_from_json(manifest_path.read_text()), []
        except Exception as exc:
            return None, [f"output_product_manifest_unreadable:{manifest_path}:{exc}"]
    return None, ["output_product_manifest_not_available"]


def _array_size_class(cell_count: int) -> str:
    if cell_count <= 10_000:
        return "tiny_json"
    if cell_count <= 250_000:
        return "bounded_json"
    return "large_future_binary_or_chunked_candidate"


def _catalog_caveats(
    metadata: ResultMetadata,
    fields: list[VisualizableField],
    unavailable_fields: list[UnavailableField],
) -> list[str]:
    available = {field.raw_field_name for field in fields}
    caveats = list(metadata.warnings)
    for required in ("qc", "w"):
        if required not in available:
            caveats.append(f"missing_visualization_field:{required}")
    caveats.extend(
        f"expected_field_unavailable:{field.raw_field_name}" for field in unavailable_fields
    )
    return caveats


def _catalog_unavailable_fields(
    metadata: ResultMetadata,
    fields: list[VisualizableField],
) -> list[UnavailableField]:
    available_raw = {field.raw_field_name.lower() for field in fields}
    available_canonical = {field.canonical_field_name for field in fields}
    unavailable: list[UnavailableField] = []
    for expected in _dedupe([*metadata.expected_outputs, "qc", "w"]):
        definition = _field_definition(expected)
        if definition is None:
            continue
        if (
            expected.lower() in available_raw
            or definition.canonical_field_name in available_canonical
        ):
            continue
        unavailable.append(
            UnavailableField(
                raw_field_name=expected,
                canonical_field_name=definition.canonical_field_name,
                display_name=definition.display_name,
                expected_by_run=expected in metadata.expected_outputs,
                reason="expected_known_field_missing_from_result_metadata",
                caveats=[
                    "field_not_present_in_ingested_netcdf_metadata",
                    "not_available_for_slice_point_cloud_profile_or_export_products",
                ],
            )
        )
    return unavailable


def _field_caveats(field_name: str, coordinates: FieldCoordinateMetadata) -> list[str]:
    definition = _require_field_definition(field_name)
    normalized = field_name.lower()
    caveats = ["native_grid_view_no_interpolation", *definition.caveats]
    if normalized == "qc" and coordinates.vertical != "zh":
        caveats.append("qc_native_vertical_grid_not_zh")
    if normalized == "w" and coordinates.vertical != "zf":
        caveats.append("w_native_vertical_grid_not_zf")
    if normalized in SURFACE_POINT_FIELDS and not coordinates.vertical:
        caveats.append("surface_field_no_vertical_dimension")
    if _native_grid_class(coordinates) == "surface_2d":
        caveats.append("surface_or_column_2d_field")
    if not _field_capabilities(field_name, coordinates).point_cloud:
        caveats.append("not_supported_for_3d_point_cloud_rendering")
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


def _coordinate_value(
    dataset: Any, coordinate_name: str | None, index: int | None
) -> float | str | None:
    if coordinate_name is None or index is None:
        return None
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


def _json_vector(values: Any) -> list[float | None]:
    return [_finite_json_number(value) for value in np.asarray(values).reshape(-1).tolist()]


def _json_matrix(values: Any) -> list[list[float | None]]:
    array = np.asarray(values)
    if array.ndim != 2:
        raise VisualizationDataError("Expected a 2-D array for JSON matrix encoding.")
    return [[_finite_json_number(value) for value in row] for row in array.tolist()]


def _json_int_vector(values: Any) -> list[int]:
    return [int(value) for value in np.asarray(values).reshape(-1).tolist()]


def _json_int_matrix(values: Any) -> list[list[int]]:
    array = np.asarray(values)
    if array.ndim != 2:
        raise VisualizationDataError("Expected a 2-D array for integer matrix encoding.")
    return [[int(value) for value in row] for row in array.tolist()]


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


def _field_definition(field_name: str) -> FieldDefinition | None:
    return FIELD_DEFINITIONS.get(field_name) or FIELD_DEFINITIONS.get(field_name.lower())


def _require_field_definition(field_name: str) -> FieldDefinition:
    definition = _field_definition(field_name)
    if definition is None:
        raise VisualizationDataError(f"Unsupported visualization field: {field_name}")
    return definition


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
