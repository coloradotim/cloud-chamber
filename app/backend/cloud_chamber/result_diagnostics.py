"""First-pass diagnostics for ingested CM1 NetCDF results."""

from __future__ import annotations

from collections.abc import Mapping
from math import hypot, isfinite
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

QC_CLOUD_THRESHOLD_KG_KG = 1e-6
QR_RAIN_THRESHOLD_KG_KG = 1e-7
MINIMUM_CLOUD_GRID_CELLS = 10
MEANINGFUL_UPDRAFT_THRESHOLD_M_S = 0.5
HYDROMETEOR_CLOUD_TOP_FIELDS = ("qr", "qi", "qs", "qg")
DIFFERENTIAL_SURFACE_FORCING_MODE = "differential_surface_forcing_patch_v0"

TIME_DIMENSION_CANDIDATES = ("time", "mtime", "t")
VERTICAL_COORDINATE_CANDIDATES = ("z", "zh", "zf", "height", "height_m")
LOW_LEVEL_RESPONSE_LAYER_BOTTOM_M = 0.0
LOW_LEVEL_RESPONSE_LAYER_TOP_M = 1000.0
LOW_LEVEL_RESPONSE_EARLY_TARGET_SECONDS = 3600.0
LOW_LEVEL_RESPONSE_EARLY_MIN_SECONDS = 1800.0
LOW_LEVEL_RESPONSE_EARLY_MAX_SECONDS = 5400.0
LOW_LEVEL_RESPONSE_METHOD = "0_1km_thickness_weighted_domain_mean_early_30_90min"
LOW_LEVEL_THERMODYNAMIC_FIELD_CANDIDATES = (
    "th",
    "theta",
    "temperature",
    "t",
)
THERMAL_FATE_CONFIDENCE_VALUES = (
    "supported",
    "candidate",
    "insufficient_evidence",
    "unsupported_missing_fields",
)

FieldQualityState = Literal["trusted", "caveated", "untrusted", "unavailable"]
FramePosition = Literal["single", "initial", "intermediate", "terminal"]


class _LowLevelLayerStats(TypedDict):
    mean: float | None
    finite_count: int
    non_finite_count: int
    total_count: int


class FieldFrameQualityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_index: int
    time_seconds: float | None = None
    position: FramePosition
    finite_count: int = 0
    non_finite_count: int = 0
    total_count: int = 0
    entirely_non_finite: bool = False


class FieldFrameQualitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_times_seconds: list[float | None] = Field(default_factory=list)
    affected_frames: list[FieldFrameQualityRecord] = Field(default_factory=list)
    affected_frame_indices: list[int] = Field(default_factory=list)
    affected_frame_times_seconds: list[float | None] = Field(default_factory=list)
    initial_frame_affected: bool = False
    terminal_frame_affected: bool = False
    affected_frame_count: int = 0
    entirely_non_finite_frame_count: int = 0
    partially_non_finite_frame_count: int = 0
    finite_frame_count: int = 0
    total_frame_count: int = 0
    finite_point_fraction: float | None = None
    chronology_available: bool = True
    chronology_caveats: list[str] = Field(default_factory=list)
    first_finite_frame_time_seconds: float | None = None
    last_finite_frame_time_seconds: float | None = None


class FieldQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    source_field: str
    quality_state: FieldQualityState
    reason: str | None = None
    finite_count: int = 0
    non_finite_count: int = 0
    total_count: int = 0
    finite_fraction: float | None = None
    frame_quality: FieldFrameQualitySummary | None = None
    caveats: list[str] = Field(default_factory=list)


class TimeValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_seconds: float | None
    value: float | None


class CloudTopSupportRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_seconds: float | None
    top_m: float | None = None
    top_defining_species: list[str] = Field(default_factory=list)
    supporting_species: list[str] = Field(default_factory=list)
    threshold_kg_kg: float = QC_CLOUD_THRESHOLD_KG_KG
    qualifying_cell_count: int = 0
    continuity_supported: bool = False
    support_rule: str = "minimum_10_cells_per_level_connected_to_lowest_supported_hydrometeor_level"


class TimeDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    fallback_used: bool
    coordinate_name: str | None = None


class CloudDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    formed: bool = False
    qc_threshold_kg_kg: float = QC_CLOUD_THRESHOLD_KG_KG
    minimum_cloud_grid_cells: int = MINIMUM_CLOUD_GRID_CELLS
    first_cloud_time_seconds: float | None = None
    cloud_base_m: float | None = None
    cloud_top_m: float | None = None
    cloud_base_time_series: list[TimeValue] = Field(default_factory=list)
    cloud_top_time_series: list[TimeValue] = Field(default_factory=list)
    liquid_cloud_base_m: float | None = None
    liquid_cloud_top_m: float | None = None
    liquid_cloud_base_time_series: list[TimeValue] = Field(default_factory=list)
    liquid_cloud_top_time_series: list[TimeValue] = Field(default_factory=list)
    hydrometeor_envelope_base_m: float | None = None
    hydrometeor_envelope_top_m: float | None = None
    hydrometeor_envelope_top_time_series: list[TimeValue] = Field(default_factory=list)
    hydrometeor_envelope_source_fields: list[str] = Field(default_factory=list)
    raw_hydrometeor_envelope_base_m: float | None = None
    raw_hydrometeor_envelope_top_m: float | None = None
    raw_hydrometeor_envelope_top_time_series: list[TimeValue] = Field(default_factory=list)
    raw_hydrometeor_envelope_top_support_time_series: list[CloudTopSupportRecord] = Field(
        default_factory=list
    )
    coherent_cloud_object_base_m: float | None = None
    coherent_cloud_object_top_m: float | None = None
    coherent_cloud_object_top_time_series: list[TimeValue] = Field(default_factory=list)
    coherent_cloud_object_top_support_time_series: list[CloudTopSupportRecord] = Field(
        default_factory=list
    )
    coherent_cloud_object_source_fields: list[str] = Field(default_factory=list)
    max_qc_kg_kg: float | None = None
    time_of_max_qc_seconds: float | None = None
    max_qc_height_time_series: list[TimeValue] = Field(default_factory=list)
    qc_max_time_series: list[TimeValue] = Field(default_factory=list)
    cloud_fraction_time_series: list[TimeValue] = Field(default_factory=list)
    cloud_present_time_steps: list[float | None] = Field(default_factory=list)
    available: bool = True


class VerticalVelocityDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_w_m_s: float | None = None
    time_of_max_w_seconds: float | None = None
    min_w_m_s: float | None = None
    time_of_min_w_seconds: float | None = None
    max_w_height_time_series: list[TimeValue] = Field(default_factory=list)
    w_max_time_series: list[TimeValue] = Field(default_factory=list)
    w_min_time_series: list[TimeValue] = Field(default_factory=list)
    units: str | None = None
    available: bool = True


class RainDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    present: bool = False
    qr_threshold_kg_kg: float = QR_RAIN_THRESHOLD_KG_KG
    first_rain_time_seconds: float | None = None
    max_qr_kg_kg: float | None = None
    time_of_max_qr_seconds: float | None = None
    qr_max_time_series: list[TimeValue] = Field(default_factory=list)
    user_message: str = "Rain-water field unavailable."
    available: bool = True
    field_absent: bool = False


class SurfaceRainDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    present: bool = False
    max_surface_rain: float | None = None
    time_of_max_surface_rain_seconds: float | None = None
    surface_rain_max_time_series: list[TimeValue] = Field(default_factory=list)
    units: str | None = None
    user_message: str = "Surface rain unavailable."
    available: bool = False
    field_absent: bool = True


class ReflectivityDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_dbz: float | None = None
    time_of_max_dbz_seconds: float | None = None
    dbz_max_time_series: list[TimeValue] = Field(default_factory=list)
    units: str | None = None
    user_message: str = "Reflectivity unavailable."
    available: bool = False
    field_absent: bool = True


class SurfaceFluxFieldDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_field: str
    available: bool = False
    field_absent: bool = True
    min_value: float | None = None
    max_value: float | None = None
    mean_value: float | None = None
    units: str | None = None
    finite_count: int = 0
    non_finite_count: int = 0
    total_count: int = 0
    finite_fraction: float | None = None
    frame_quality: FieldFrameQualitySummary | None = None
    caveats: list[str] = Field(default_factory=list)


class SurfaceFluxDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hfx: SurfaceFluxFieldDiagnostics = Field(
        default_factory=lambda: SurfaceFluxFieldDiagnostics(source_field="hfx")
    )
    qfx: SurfaceFluxFieldDiagnostics = Field(
        default_factory=lambda: SurfaceFluxFieldDiagnostics(source_field="qfx")
    )


class LowLevelResponseFieldDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_field: str | None = None
    available: bool = False
    early_response_available: bool = False
    full_run_response_available: bool = False
    field_absent: bool = True
    layer_bottom_m: float = LOW_LEVEL_RESPONSE_LAYER_BOTTOM_M
    layer_top_m: float = LOW_LEVEL_RESPONSE_LAYER_TOP_M
    vertical_coordinate_name: str | None = None
    vertical_coordinate_units: str | None = None
    vertical_coordinate_method: str | None = None
    time_dimension: str | None = None
    first_time_index: int | None = None
    final_time_index: int | None = None
    first_time_seconds: float | None = None
    final_time_seconds: float | None = None
    first_mean_value: float | None = None
    final_mean_value: float | None = None
    delta_value: float | None = None
    early_response_start_time_index: int | None = None
    early_response_end_time_index: int | None = None
    early_response_start_time_seconds: float | None = None
    early_response_end_time_seconds: float | None = None
    early_response_start_mean_value: float | None = None
    early_response_end_mean_value: float | None = None
    early_response_delta: float | None = None
    early_response_start_finite_count: int = 0
    early_response_start_non_finite_count: int = 0
    early_response_start_total_count: int = 0
    early_response_end_finite_count: int = 0
    early_response_end_non_finite_count: int = 0
    early_response_end_total_count: int = 0
    full_run_delta: float | None = None
    units: str | None = None
    first_finite_count: int = 0
    first_non_finite_count: int = 0
    first_total_count: int = 0
    final_finite_count: int = 0
    final_non_finite_count: int = 0
    final_total_count: int = 0
    caveats: list[str] = Field(default_factory=list)


class LowLevelResponseDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    qv: LowLevelResponseFieldDiagnostics = Field(
        default_factory=lambda: LowLevelResponseFieldDiagnostics(source_field="qv")
    )
    theta_or_temperature: LowLevelResponseFieldDiagnostics = Field(
        default_factory=LowLevelResponseFieldDiagnostics
    )


class DifferentialPatchGeometryDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern_sha256: str | None = None
    shape: str | None = None
    center_x_m: float | None = None
    center_y_m: float | None = None
    radius_x_m: float | None = None
    radius_y_m: float | None = None
    taper_width_m: float | None = None
    ramp_seconds: float | None = None


class PatchSpatialFieldDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_field: str
    available: bool = False
    field_absent: bool = True
    units: str | None = None
    quality_state: FieldQualityState = "unavailable"
    quality_reason: str | None = None
    finite_count: int = 0
    non_finite_count: int = 0
    total_count: int = 0
    finite_fraction: float | None = None
    time_index: int | None = None
    time_seconds: float | None = None
    time_selection_method: str = "field_maximum_time"
    vertical_coordinate_name: str | None = None
    vertical_level_index: int | None = None
    vertical_level_height_m: float | None = None
    max_value: float | None = None
    max_x_m: float | None = None
    max_y_m: float | None = None
    max_distance_from_patch_center_m: float | None = None
    max_inside_patch_radius: bool | None = None
    max_region: str | None = None
    center_value: float | None = None
    core_mean: float | None = None
    taper_mean: float | None = None
    background_mean: float | None = None
    center_to_background_ratio: float | None = None
    core_to_background_ratio: float | None = None
    core_finite_count: int = 0
    taper_finite_count: int = 0
    background_finite_count: int = 0
    inside_patch_mean: float | None = None
    outside_patch_mean: float | None = None
    center_to_outside_ratio: float | None = None
    inside_finite_count: int = 0
    outside_finite_count: int = 0
    total_finite_count: int = 0
    method: str = "patch_center_core_taper_background_spatial_summary"
    geometry_note: str = "centered_circle_with_raised_cosine_edge_taper_v0"
    caveats: list[str] = Field(default_factory=list)


class PatchConvergenceDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    available: bool = False
    source_fields: list[str] = Field(default_factory=list)
    units: str = "s^-1"
    quality_state: FieldQualityState = "unavailable"
    quality_reason: str | None = None
    finite_count: int = 0
    non_finite_count: int = 0
    total_count: int = 0
    finite_fraction: float | None = None
    time_index: int | None = None
    time_seconds: float | None = None
    time_selection_method: str = "maximum_finite_convergence_time"
    vertical_coordinate_name: str | None = None
    vertical_level_index: int | None = None
    vertical_level_height_m: float | None = None
    max_convergence_s_1: float | None = None
    max_convergence_x_m: float | None = None
    max_convergence_y_m: float | None = None
    max_convergence_distance_from_patch_center_m: float | None = None
    max_convergence_inside_patch_radius: bool | None = None
    max_convergence_region: str | None = None
    max_convergence_time_series: list[TimeValue] = Field(default_factory=list)
    core_mean_convergence_s_1: float | None = None
    taper_mean_convergence_s_1: float | None = None
    background_mean_convergence_s_1: float | None = None
    core_to_background_convergence_ratio: float | None = None
    core_finite_count: int = 0
    taper_finite_count: int = 0
    background_finite_count: int = 0
    inside_patch_mean_convergence_s_1: float | None = None
    outside_patch_mean_convergence_s_1: float | None = None
    method: str = "lowest_level_collocated_finite_difference_negative_divergence"
    geometry_note: str = "centered_circle_with_raised_cosine_edge_taper_v0"
    caveats: list[str] = Field(default_factory=list)


class LocalizedResponseDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    available: bool = False
    support_state: str = "unavailable"
    geometry: DifferentialPatchGeometryDiagnostics | None = None
    hfx_footprint: PatchSpatialFieldDiagnostics = Field(
        default_factory=lambda: PatchSpatialFieldDiagnostics(source_field="hfx")
    )
    qfx_footprint: PatchSpatialFieldDiagnostics = Field(
        default_factory=lambda: PatchSpatialFieldDiagnostics(source_field="qfx")
    )
    near_surface_convergence: PatchConvergenceDiagnostics = Field(
        default_factory=PatchConvergenceDiagnostics
    )
    updraft: PatchSpatialFieldDiagnostics = Field(
        default_factory=lambda: PatchSpatialFieldDiagnostics(source_field="w")
    )
    cloud_water: PatchSpatialFieldDiagnostics = Field(
        default_factory=lambda: PatchSpatialFieldDiagnostics(source_field="qc")
    )
    rain_water_aloft: PatchSpatialFieldDiagnostics = Field(
        default_factory=lambda: PatchSpatialFieldDiagnostics(source_field="qr")
    )
    surface_rain: PatchSpatialFieldDiagnostics = Field(
        default_factory=lambda: PatchSpatialFieldDiagnostics(source_field="rain")
    )
    reflectivity: PatchSpatialFieldDiagnostics = Field(
        default_factory=lambda: PatchSpatialFieldDiagnostics(source_field="dbz")
    )
    caveats: list[str] = Field(default_factory=list)


class ResultDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cloud: CloudDiagnostics
    vertical_velocity: VerticalVelocityDiagnostics
    rain: RainDiagnostics
    surface_rain: SurfaceRainDiagnostics = Field(default_factory=SurfaceRainDiagnostics)
    reflectivity: ReflectivityDiagnostics = Field(default_factory=ReflectivityDiagnostics)
    surface_fluxes: SurfaceFluxDiagnostics = Field(default_factory=SurfaceFluxDiagnostics)
    low_level_response: LowLevelResponseDiagnostics = Field(
        default_factory=LowLevelResponseDiagnostics
    )
    localized_response: LocalizedResponseDiagnostics = Field(
        default_factory=LocalizedResponseDiagnostics
    )
    time: TimeDiagnostics
    field_quality_assessed: bool = False
    field_quality: dict[str, FieldQuality] = Field(default_factory=dict)
    caveats: list[str] = Field(default_factory=list)


class ProcessDiagnosticState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    summary: str | None = None
    direct_fields: list[str] = Field(default_factory=list)
    derived_diagnostics: list[str] = Field(default_factory=list)
    proxy_diagnostics: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class InterpretationSupport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    main_limiting_factor: str = "unknown"
    thermal_fate_label: str = "Insufficient evidence"
    confidence: str = "insufficient_evidence"
    caveats: list[str] = Field(default_factory=list)


class ProcessDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thermal_fate: ProcessDiagnosticState
    cloud_lifecycle: ProcessDiagnosticState
    updrafts: ProcessDiagnosticState
    moisture_saturation: ProcessDiagnosticState
    cap_inversion: ProcessDiagnosticState
    buoyancy: ProcessDiagnosticState
    deep_breakthrough: ProcessDiagnosticState
    precipitation_feedback: ProcessDiagnosticState
    local_region_support: ProcessDiagnosticState
    interpretation_support: InterpretationSupport


def compute_process_diagnostics(
    diagnostics: ResultDiagnostics,
    *,
    scenario_id: str,
    controls: dict[str, str | float | bool],
    variables: list[str],
) -> ProcessDiagnostics:
    """Compute conservative Thermal Fate process summaries from supported diagnostics."""

    available_fields = set(variables)
    if "qc" not in available_fields and "ql" in available_fields:
        available_fields.add("qc")
        caveats = ["cloud_liquid_ql_mapped_to_canonical_qc_diagnostics"]
    else:
        caveats = []
    if not diagnostics.cloud.available:
        caveats.append("thermal_fate_missing_qc")
    if not diagnostics.vertical_velocity.available:
        caveats.append("thermal_fate_missing_w")
    if "qv" not in available_fields:
        caveats.append("moisture_saturation_unsupported_missing_qv")
    if "th" not in available_fields:
        caveats.append("buoyancy_unsupported_missing_th")

    updraft_meaningful = (
        diagnostics.vertical_velocity.available
        and diagnostics.vertical_velocity.max_w_m_s is not None
        and diagnostics.vertical_velocity.max_w_m_s >= MEANINGFUL_UPDRAFT_THRESHOLD_M_S
    )
    has_cloud = diagnostics.cloud.available and diagnostics.cloud.formed
    has_rain = diagnostics.rain.available and diagnostics.rain.present

    label = "Insufficient evidence"
    confidence = "insufficient_evidence"
    main_limiting_factor = "unknown"
    summary = "Available diagnostics are insufficient for a Thermal Fate label."

    if not diagnostics.cloud.available or not diagnostics.vertical_velocity.available:
        confidence = "unsupported_missing_fields"
        summary = "Thermal Fate label unavailable because required qc or w fields are missing."
    elif not updraft_meaningful and not has_cloud:
        label = "No meaningful thermal"
        confidence = "supported"
        summary = "No meaningful updraft or cloud-water signal was detected."
    elif updraft_meaningful and not has_cloud:
        label = "Thermal without cloud"
        confidence = "supported"
        main_limiting_factor = "moisture"
        summary = "Meaningful vertical motion occurred, but cloud water stayed below threshold."
        caveats.append("moisture_limitation_inferred_without_saturation_deficit")
    elif _is_capped_scenario(scenario_id, controls):
        label = "Capped / suppressed cumulus"
        confidence = "candidate"
        main_limiting_factor = "cap/stability"
        summary = (
            "Cloud and vertical motion are present in a stronger-cap scenario; "
            "cap limitation remains a candidate until baseline comparison or "
            "cap diagnostics support it."
        )
        caveats.append("cap_limitation_candidate_requires_baseline_comparison")
    elif has_cloud and _cloud_top_increases(diagnostics.cloud.cloud_top_time_series):
        label = "Growing cumulus"
        confidence = "candidate"
        summary = (
            "Cloud formed and coherent cloud-object top increased over available output times."
        )
    elif has_cloud:
        label = "Fair-weather cumulus"
        confidence = "candidate"
        summary = "Cloud formed with available updraft and cloud-water diagnostics."

    thermal_fate = ProcessDiagnosticState(
        status=confidence,
        summary=summary,
        direct_fields=_present(["qc", "w", "qr"], available_fields),
        derived_diagnostics=[
            "cloud_formed",
            "first_cloud_time",
            "cloud_base_top",
            "cloud_fraction_time_series",
            "qc_max_time_series",
            "w_max_min_time_series",
            "rain_summary",
        ],
        caveats=_dedupe(caveats),
    )
    cloud_lifecycle = ProcessDiagnosticState(
        status="supported" if diagnostics.cloud.available else "unsupported_missing_fields",
        summary="Cloud lifecycle uses qc threshold, base/top, cloud fraction, and qc series.",
        direct_fields=_present(["qc"], available_fields),
        derived_diagnostics=[
            "cloud_base_time_series",
            "cloud_top_time_series",
            "max_qc_height_time_series",
            "cloud_fraction_time_series",
        ],
        caveats=[] if diagnostics.cloud.available else ["missing_qc_field"],
    )
    updrafts = ProcessDiagnosticState(
        status="supported"
        if diagnostics.vertical_velocity.available
        else "unsupported_missing_fields",
        summary="Updraft diagnostics use w max/min and max-height summaries.",
        direct_fields=_present(["w"], available_fields),
        derived_diagnostics=["w_max_time_series", "w_min_time_series", "max_w_height_time_series"],
        caveats=[] if diagnostics.vertical_velocity.available else ["missing_w_field"],
    )
    moisture_saturation = ProcessDiagnosticState(
        status="unsupported_missing_fields",
        summary=(
            "Saturation deficit/RH diagnostics are not yet implemented from "
            "qv/thermodynamic fields."
        ),
        direct_fields=_present(["qv"], available_fields),
        caveats=["moisture_saturation_unsupported_missing_qv"],
    )
    cap_inversion = ProcessDiagnosticState(
        status="candidate"
        if _is_capped_scenario(scenario_id, controls)
        else "insufficient_evidence",
        summary=(
            "Capped scenario metadata suggests cap/stability interpretation, but cap-relative "
            "diagnostics are not computed yet."
        )
        if _is_capped_scenario(scenario_id, controls)
        else "Cap/inversion diagnostics require cap metadata from generated soundings.",
        proxy_diagnostics=["scenario_control:cap_strength=stronger"]
        if _is_capped_scenario(scenario_id, controls)
        else [],
        caveats=["cap_inversion_metadata_not_computed"],
    )
    buoyancy = ProcessDiagnosticState(
        status="unsupported_missing_fields",
        summary=(
            "Buoyancy/theta-v diagnostics are not implemented until required "
            "thermodynamic fields exist."
        ),
        direct_fields=_present(["th", "theta_v"], available_fields),
        caveats=["buoyancy_unsupported_missing_thermodynamic_fields"],
    )
    deep_breakthrough = ProcessDiagnosticState(
        status="unsupported_missing_fields",
        summary=(
            "Deep-breakthrough diagnostics require CAPE/CIN/LFC/EL and sustained-updraft metadata."
        ),
        caveats=["deep_breakthrough_unsupported_missing_cape_cin_lfc_el"],
    )
    precipitation_feedback = ProcessDiagnosticState(
        status="candidate" if has_rain else "unsupported_missing_fields",
        summary=(
            "Rain water is present, but downdraft/cold-pool feedback diagnostics "
            "are not implemented."
            if has_rain
            else (
                "Precipitation-feedback diagnostics require rain and near-surface "
                "thermodynamic fields."
            )
        ),
        direct_fields=_present(["qr", "w"], available_fields),
        derived_diagnostics=["rain_onset", "min_w"] if has_rain else [],
        caveats=["precipitation_feedback_requires_downdraft_and_cold_pool_diagnostics"],
    )
    local_region_support = ProcessDiagnosticState(
        status="insufficient_evidence",
        summary="Global process metadata is ready for future selected-region diagnostics.",
        caveats=["selected_region_diagnostics_not_computed_in_global_ingest"],
    )

    return ProcessDiagnostics(
        thermal_fate=thermal_fate,
        cloud_lifecycle=cloud_lifecycle,
        updrafts=updrafts,
        moisture_saturation=moisture_saturation,
        cap_inversion=cap_inversion,
        buoyancy=buoyancy,
        deep_breakthrough=deep_breakthrough,
        precipitation_feedback=precipitation_feedback,
        local_region_support=local_region_support,
        interpretation_support=InterpretationSupport(
            main_limiting_factor=main_limiting_factor,
            thermal_fate_label=label,
            confidence=confidence,
            caveats=_dedupe(caveats),
        ),
    )


def compute_baseline_diagnostics(
    dataset: Any,
    inherited_caveats: list[str],
    *,
    run_configuration: Mapping[str, Any] | None = None,
) -> ResultDiagnostics:
    """Compute MVP Baseline Shallow Cumulus diagnostics from an xarray dataset."""
    caveats = list(inherited_caveats)
    cloud_liquid_source = "qc"
    if "qc" not in dataset.data_vars and "ql" in dataset.data_vars:
        dataset = dataset.rename({"ql": "qc"})
        cloud_liquid_source = "ql"
        caveats.append("cloud_liquid_ql_mapped_to_canonical_qc_diagnostics")
    time_context = _time_context(dataset, _primary_time_dimension(dataset))
    cloud = _cloud_diagnostics(dataset, time_context, caveats)
    vertical_velocity = _vertical_velocity_diagnostics(dataset, time_context, caveats)
    rain = _rain_diagnostics(dataset, time_context, caveats)
    surface_rain = _surface_rain_diagnostics(dataset, time_context, caveats)
    reflectivity = _reflectivity_diagnostics(dataset, time_context, caveats)
    surface_fluxes = _surface_flux_diagnostics(dataset, time_context, caveats)
    low_level_response = _low_level_response_diagnostics(dataset, time_context, caveats)
    field_quality = _field_quality_map(dataset, time_context)
    if cloud_liquid_source == "ql" and "qc" in field_quality:
        qc_quality = field_quality["qc"]
        field_quality["qc"] = qc_quality.model_copy(
            update={
                "source_field": "ql",
                "caveats": _dedupe(
                    [
                        *qc_quality.caveats,
                        "cloud_liquid_ql_mapped_to_canonical_qc_diagnostics",
                    ]
                ),
            }
        )
    localized_response = _localized_response_diagnostics(
        dataset,
        time_context,
        run_configuration=run_configuration,
        field_quality=field_quality,
        caveats=caveats,
    )
    return ResultDiagnostics(
        cloud=cloud,
        vertical_velocity=vertical_velocity,
        rain=rain,
        surface_rain=surface_rain,
        reflectivity=reflectivity,
        surface_fluxes=surface_fluxes,
        low_level_response=low_level_response,
        localized_response=localized_response,
        time=time_context.diagnostics,
        field_quality_assessed=True,
        field_quality=field_quality,
        caveats=_dedupe(caveats),
    )


FIELD_QUALITY_SOURCES = {
    "qc": {
        "source_field": "qc",
        "missing": "missing_qc_field",
        "partial": "non_finite_values_detected_in_qc",
        "entire": "qc_field_entirely_non_finite",
    },
    "w": {
        "source_field": "w",
        "missing": "missing_w_field",
        "partial": "non_finite_values_detected_in_w",
        "entire": "w_field_entirely_non_finite",
    },
    "qr": {
        "source_field": "qr",
        "missing": "qr_field_absent",
        "partial": "non_finite_values_detected_in_qr",
        "entire": "qr_field_entirely_non_finite",
    },
    "surface_rain": {
        "source_field": "rain",
        "missing": "surface_rain_field_absent",
        "partial": "non_finite_values_detected_in_surface_rain",
        "entire": "surface_rain_field_entirely_non_finite",
    },
    "dbz": {
        "source_field": "dbz",
        "missing": "dbz_field_absent",
        "partial": "non_finite_values_detected_in_dbz",
        "entire": "dbz_field_entirely_non_finite",
    },
    "hfx": {
        "source_field": "hfx",
        "missing": "hfx_field_absent",
        "partial": "non_finite_values_detected_in_hfx",
        "entire": "hfx_field_entirely_non_finite",
    },
    "qfx": {
        "source_field": "qfx",
        "missing": "qfx_field_absent",
        "partial": "non_finite_values_detected_in_qfx",
        "entire": "qfx_field_entirely_non_finite",
    },
}


def _field_quality_map(dataset: Any, time: _TimeContext) -> dict[str, FieldQuality]:
    quality_sources = dict(FIELD_QUALITY_SOURCES)
    for field in HYDROMETEOR_CLOUD_TOP_FIELDS:
        if field in dataset.data_vars:
            quality_sources[field] = {
                "source_field": field,
                "missing": f"{field}_field_absent",
                "partial": f"non_finite_values_detected_in_{field}",
                "entire": f"{field}_field_entirely_non_finite",
            }
    for field in ("uinterp", "vinterp", "u", "v"):
        if field in dataset.data_vars:
            quality_sources[field] = {
                "source_field": field,
                "missing": f"{field}_field_absent",
                "partial": f"non_finite_values_detected_in_{field}",
                "entire": f"{field}_field_entirely_non_finite",
            }
    return {
        field: _field_quality(dataset, field, config, time)
        for field, config in quality_sources.items()
    }


def _field_quality(
    dataset: Any,
    field: str,
    config: dict[str, str],
    time: _TimeContext,
) -> FieldQuality:
    source_field = config["source_field"]
    if source_field not in dataset.data_vars:
        return FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="unavailable",
            reason=config["missing"],
            caveats=[config["missing"]],
        )
    data_array = dataset[source_field]
    finite_count = _finite_count(data_array)
    non_finite_count = _non_finite_count(data_array)
    total_count = _total_count(data_array)
    finite_fraction = _finite_fraction(finite_count, total_count)
    frame_quality = _field_frame_quality(data_array, time)
    reason = _field_quality_reason(
        field,
        config,
        finite_count=finite_count,
        non_finite_count=non_finite_count,
        frame_quality=frame_quality,
    )
    caveats = _field_quality_caveats(config, reason, non_finite_count)
    if finite_count == 0:
        return FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="untrusted",
            reason=config["entire"],
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            finite_fraction=finite_fraction,
            frame_quality=frame_quality,
            caveats=caveats,
        )
    if reason is not None and "_terminal_output_frame_entirely_non_finite" in reason:
        return FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="untrusted",
            reason=reason,
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            finite_fraction=finite_fraction,
            frame_quality=frame_quality,
            caveats=caveats,
        )
    if non_finite_count > 0:
        return FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="caveated",
            reason=reason or config["partial"],
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            finite_fraction=finite_fraction,
            frame_quality=frame_quality,
            caveats=caveats,
        )
    return FieldQuality(
        field=field,
        source_field=source_field,
        quality_state="trusted",
        finite_count=finite_count,
        non_finite_count=non_finite_count,
        total_count=total_count,
        finite_fraction=finite_fraction,
        frame_quality=frame_quality,
    )


def _field_quality_reason(
    source_field: str,
    config: dict[str, str],
    *,
    finite_count: int,
    non_finite_count: int,
    frame_quality: FieldFrameQualitySummary,
) -> str | None:
    if finite_count == 0:
        return config["entire"]
    if non_finite_count <= 0:
        return None
    if not frame_quality.chronology_available:
        return f"{source_field}_frame_chronology_unavailable"
    terminal_entire = any(
        frame.position == "terminal" and frame.entirely_non_finite
        for frame in frame_quality.affected_frames
    )
    if terminal_entire:
        return f"{source_field}_terminal_output_frame_entirely_non_finite"
    initial_entire = any(
        frame.position == "initial" and frame.entirely_non_finite
        for frame in frame_quality.affected_frames
    )
    non_initial_entire = any(
        frame.position in {"intermediate", "single"} and frame.entirely_non_finite
        for frame in frame_quality.affected_frames
    )
    if non_initial_entire:
        return f"{source_field}_intermediate_output_frame_entirely_non_finite"
    if initial_entire and frame_quality.entirely_non_finite_frame_count == 1:
        return f"{source_field}_initial_output_frame_entirely_non_finite"
    return config["partial"]


def _field_quality_caveats(
    config: dict[str, str],
    reason: str | None,
    non_finite_count: int,
) -> list[str]:
    caveats: list[str] = []
    if non_finite_count > 0:
        caveats.append(config["partial"])
    if reason is not None and reason != config["partial"]:
        caveats.append(reason)
    return _dedupe(caveats)


def _field_frame_quality(data_array: Any, time: _TimeContext) -> FieldFrameQualitySummary:
    slices = _time_slices(data_array, time.dimension)
    total_frame_count = len(slices)
    frame_times_seconds = [time.at(index) for index in range(total_frame_count)]
    frame_positions, chronology_caveats = _frame_positions_from_times(frame_times_seconds)
    affected_frames: list[FieldFrameQualityRecord] = []
    finite_frame_count = 0
    first_finite_time: float | None = None
    last_finite_time: float | None = None
    finite_point_count = 0
    total_point_count = 0

    for index, frame in enumerate(slices):
        finite_count = _finite_count(frame)
        total_count = _total_count(frame)
        non_finite_count = total_count - finite_count
        finite_point_count += finite_count
        total_point_count += total_count
        time_seconds = time.at(index)
        if finite_count > 0:
            finite_frame_count += 1
            if first_finite_time is None:
                first_finite_time = time_seconds
            last_finite_time = time_seconds
        if non_finite_count > 0:
            affected_frames.append(
                FieldFrameQualityRecord(
                    frame_index=index,
                    time_seconds=time_seconds,
                    position=frame_positions[index],
                    finite_count=finite_count,
                    non_finite_count=non_finite_count,
                    total_count=total_count,
                    entirely_non_finite=finite_count == 0,
                )
            )

    return _frame_quality_summary_from_records(
        affected_frames,
        frame_times_seconds=frame_times_seconds,
        finite_frame_count=finite_frame_count,
        total_frame_count=total_frame_count,
        finite_point_count=finite_point_count,
        total_point_count=total_point_count,
        chronology_caveats=chronology_caveats,
        first_finite_frame_time_seconds=first_finite_time,
        last_finite_frame_time_seconds=last_finite_time,
    )


def _frame_quality_summary_from_records(
    affected_frames: list[FieldFrameQualityRecord],
    *,
    frame_times_seconds: list[float | None],
    finite_frame_count: int,
    total_frame_count: int,
    finite_point_count: int,
    total_point_count: int,
    chronology_caveats: list[str],
    first_finite_frame_time_seconds: float | None,
    last_finite_frame_time_seconds: float | None,
) -> FieldFrameQualitySummary:
    return FieldFrameQualitySummary(
        frame_times_seconds=frame_times_seconds,
        affected_frames=affected_frames,
        affected_frame_indices=[frame.frame_index for frame in affected_frames],
        affected_frame_times_seconds=[frame.time_seconds for frame in affected_frames],
        initial_frame_affected=any(
            frame.position in {"initial", "single"} for frame in affected_frames
        ),
        terminal_frame_affected=any(
            frame.position in {"terminal", "single"} for frame in affected_frames
        ),
        entirely_non_finite_frame_count=sum(
            1 for frame in affected_frames if frame.entirely_non_finite
        ),
        partially_non_finite_frame_count=sum(
            1 for frame in affected_frames if not frame.entirely_non_finite
        ),
        affected_frame_count=len(affected_frames),
        finite_frame_count=finite_frame_count,
        total_frame_count=total_frame_count,
        finite_point_fraction=_finite_fraction(finite_point_count, total_point_count),
        chronology_available=not chronology_caveats,
        chronology_caveats=chronology_caveats,
        first_finite_frame_time_seconds=first_finite_frame_time_seconds,
        last_finite_frame_time_seconds=last_finite_frame_time_seconds,
    )


def _frame_positions_from_times(
    frame_times_seconds: list[float | None],
) -> tuple[list[FramePosition], list[str]]:
    total_frame_count = len(frame_times_seconds)
    if total_frame_count <= 1:
        return (["single"], [])

    finite_times = [
        (index, time_seconds)
        for index, time_seconds in enumerate(frame_times_seconds)
        if time_seconds is not None and isfinite(time_seconds)
    ]
    chronology_caveats: list[str] = []
    if len(finite_times) != total_frame_count:
        chronology_caveats.append("frame_chronology_unavailable_missing_time")
    else:
        seen_times = {time_seconds for _, time_seconds in finite_times}
        if len(seen_times) != total_frame_count:
            chronology_caveats.append("frame_chronology_unavailable_duplicate_time")

    if chronology_caveats:
        return (
            [
                _frame_position_from_index(index, total_frame_count)
                for index in range(total_frame_count)
            ],
            chronology_caveats,
        )

    positions: list[FramePosition] = ["intermediate"] * total_frame_count
    for rank, (index, _) in enumerate(sorted(finite_times, key=lambda item: item[1])):
        positions[index] = _frame_position_from_index(rank, total_frame_count)
    return positions, []


def _frame_position_from_index(index: int, total_frame_count: int) -> FramePosition:
    if total_frame_count <= 1:
        return "single"
    if index == 0:
        return "initial"
    if index == total_frame_count - 1:
        return "terminal"
    return "intermediate"


class _TimeContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dimension: str | None
    values: list[float | None]
    diagnostics: TimeDiagnostics

    def at(self, index: int) -> float | None:
        if index < len(self.values):
            return self.values[index]
        return float(index)


class _VerticalSelection(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    array: Any
    coordinate_name: str | None = None
    index: int | None = None
    height_m: float | None = None


def _cloud_diagnostics(dataset: Any, time: _TimeContext, caveats: list[str]) -> CloudDiagnostics:
    if "qc" not in dataset.data_vars:
        caveats.append("missing_qc_field")
        return CloudDiagnostics(available=False)

    qc = dataset["qc"]
    _record_units_caveat(qc, "qc", "kg/kg", caveats)
    if _non_finite_count(qc) > 0:
        caveats.append("non_finite_values_detected_in_qc")
    if not _has_finite_values(qc):
        caveats.append("qc_field_entirely_non_finite")
        return CloudDiagnostics(available=False)

    cloud_extent, envelope_source_fields = _cloud_extent_array(dataset, qc, caveats)
    envelope_source_arrays = _hydrometeor_source_arrays(dataset, qc, envelope_source_fields)
    series_arrays = _time_slices(qc, time.dimension)
    cloud_extent_series_arrays = _time_slices(cloud_extent, time.dimension)
    envelope_source_series_arrays = {
        field: _time_slices(array, time.dimension)
        for field, array in envelope_source_arrays.items()
    }
    qc_max_series: list[TimeValue] = []
    cloud_fraction_series: list[TimeValue] = []
    cloud_base_series: list[TimeValue] = []
    cloud_top_series: list[TimeValue] = []
    liquid_cloud_base_series: list[TimeValue] = []
    liquid_cloud_top_series: list[TimeValue] = []
    raw_envelope_top_series: list[TimeValue] = []
    raw_envelope_support_series: list[CloudTopSupportRecord] = []
    coherent_cloud_top_series: list[TimeValue] = []
    coherent_cloud_support_series: list[CloudTopSupportRecord] = []
    max_qc_height_series: list[TimeValue] = []
    cloud_present_steps: list[float | None] = []
    first_cloud_time: float | None = None
    max_qc: float | None = None
    time_of_max_qc: float | None = None

    for index, array in enumerate(series_arrays):
        time_seconds = time.at(index)
        slice_max = _finite_max(array)
        cloudy_count = _threshold_count(array, QC_CLOUD_THRESHOLD_KG_KG)
        finite_count = _finite_count(array)
        cloud_fraction = (cloudy_count / finite_count) if finite_count else None
        extent_array = (
            cloud_extent_series_arrays[index] if index < len(cloud_extent_series_arrays) else array
        )
        extent_source_arrays = {
            field: slices[index] if index < len(slices) else array
            for field, slices in envelope_source_series_arrays.items()
        }
        liquid_cloud_base, liquid_cloud_top = _cloud_base_top(array, caveats)
        raw_base, raw_top, raw_support = _cloud_top_with_level_support(
            extent_array,
            source_arrays=extent_source_arrays,
            caveats=caveats,
            time_seconds=time_seconds,
            minimum_cells=1,
            require_connected_levels=False,
        )
        coherent_base, coherent_top, coherent_support = _cloud_top_with_level_support(
            extent_array,
            source_arrays=extent_source_arrays,
            caveats=caveats,
            time_seconds=time_seconds,
            minimum_cells=MINIMUM_CLOUD_GRID_CELLS,
            require_connected_levels=True,
        )
        qc_max_series.append(TimeValue(time_seconds=time_seconds, value=slice_max))
        cloud_fraction_series.append(TimeValue(time_seconds=time_seconds, value=cloud_fraction))
        cloud_base_series.append(TimeValue(time_seconds=time_seconds, value=coherent_base))
        cloud_top_series.append(TimeValue(time_seconds=time_seconds, value=coherent_top))
        liquid_cloud_base_series.append(
            TimeValue(time_seconds=time_seconds, value=liquid_cloud_base)
        )
        liquid_cloud_top_series.append(TimeValue(time_seconds=time_seconds, value=liquid_cloud_top))
        raw_envelope_top_series.append(TimeValue(time_seconds=time_seconds, value=raw_top))
        raw_envelope_support_series.append(raw_support)
        coherent_cloud_top_series.append(TimeValue(time_seconds=time_seconds, value=coherent_top))
        coherent_cloud_support_series.append(coherent_support)
        max_qc_height_series.append(
            TimeValue(time_seconds=time_seconds, value=_height_of_level_max(array, caveats))
        )
        if cloudy_count >= MINIMUM_CLOUD_GRID_CELLS:
            cloud_present_steps.append(time_seconds)
            if first_cloud_time is None:
                first_cloud_time = time_seconds
        if slice_max is not None and (max_qc is None or slice_max > max_qc):
            max_qc = slice_max
            time_of_max_qc = time_seconds

    liquid_cloud_base, liquid_cloud_top = _cloud_base_top(qc, caveats)
    raw_base, raw_top, raw_support = _cloud_top_with_level_support(
        cloud_extent,
        source_arrays=envelope_source_arrays,
        caveats=caveats,
        time_seconds=None,
        minimum_cells=1,
        require_connected_levels=False,
    )
    coherent_base, coherent_top, coherent_support = _cloud_top_with_level_support(
        cloud_extent,
        source_arrays=envelope_source_arrays,
        caveats=caveats,
        time_seconds=None,
        minimum_cells=MINIMUM_CLOUD_GRID_CELLS,
        require_connected_levels=True,
    )
    return CloudDiagnostics(
        formed=first_cloud_time is not None,
        first_cloud_time_seconds=first_cloud_time,
        cloud_base_m=coherent_base,
        cloud_top_m=coherent_top,
        cloud_base_time_series=cloud_base_series,
        cloud_top_time_series=cloud_top_series,
        liquid_cloud_base_m=liquid_cloud_base,
        liquid_cloud_top_m=liquid_cloud_top,
        liquid_cloud_base_time_series=liquid_cloud_base_series,
        liquid_cloud_top_time_series=liquid_cloud_top_series,
        hydrometeor_envelope_base_m=raw_base,
        hydrometeor_envelope_top_m=raw_top,
        hydrometeor_envelope_top_time_series=raw_envelope_top_series,
        hydrometeor_envelope_source_fields=envelope_source_fields,
        raw_hydrometeor_envelope_base_m=raw_base,
        raw_hydrometeor_envelope_top_m=raw_top,
        raw_hydrometeor_envelope_top_time_series=raw_envelope_top_series,
        raw_hydrometeor_envelope_top_support_time_series=raw_envelope_support_series,
        coherent_cloud_object_base_m=coherent_base,
        coherent_cloud_object_top_m=coherent_top,
        coherent_cloud_object_top_time_series=coherent_cloud_top_series,
        coherent_cloud_object_top_support_time_series=coherent_cloud_support_series,
        coherent_cloud_object_source_fields=coherent_support.supporting_species,
        max_qc_kg_kg=max_qc,
        time_of_max_qc_seconds=time_of_max_qc,
        max_qc_height_time_series=max_qc_height_series,
        qc_max_time_series=qc_max_series,
        cloud_fraction_time_series=cloud_fraction_series,
        cloud_present_time_steps=cloud_present_steps,
    )


def _vertical_velocity_diagnostics(
    dataset: Any,
    time: _TimeContext,
    caveats: list[str],
) -> VerticalVelocityDiagnostics:
    if "w" not in dataset.data_vars:
        caveats.append("missing_w_field")
        return VerticalVelocityDiagnostics(available=False)

    w = dataset["w"]
    units = _attr_string(w, "units")
    _record_units_caveat(w, "w", "m/s", caveats)
    if _non_finite_count(w) > 0:
        caveats.append("non_finite_values_detected_in_w")
    if not _has_finite_values(w):
        caveats.append("w_field_entirely_non_finite")
        return VerticalVelocityDiagnostics(available=False, units=units)

    max_series: list[TimeValue] = []
    min_series: list[TimeValue] = []
    max_height_series: list[TimeValue] = []
    max_w: float | None = None
    time_of_max_w: float | None = None
    min_w: float | None = None
    time_of_min_w: float | None = None

    for index, array in enumerate(_time_slices(w, time.dimension)):
        time_seconds = time.at(index)
        slice_max = _finite_max(array)
        slice_min = _finite_min(array)
        max_series.append(TimeValue(time_seconds=time_seconds, value=slice_max))
        min_series.append(TimeValue(time_seconds=time_seconds, value=slice_min))
        max_height_series.append(
            TimeValue(time_seconds=time_seconds, value=_height_of_level_max(array, caveats))
        )
        if slice_max is not None and (max_w is None or slice_max > max_w):
            max_w = slice_max
            time_of_max_w = time_seconds
        if slice_min is not None and (min_w is None or slice_min < min_w):
            min_w = slice_min
            time_of_min_w = time_seconds

    return VerticalVelocityDiagnostics(
        max_w_m_s=max_w,
        time_of_max_w_seconds=time_of_max_w,
        min_w_m_s=min_w,
        time_of_min_w_seconds=time_of_min_w,
        max_w_height_time_series=max_height_series,
        w_max_time_series=max_series,
        w_min_time_series=min_series,
        units=units,
    )


def _rain_diagnostics(dataset: Any, time: _TimeContext, caveats: list[str]) -> RainDiagnostics:
    if "qr" not in dataset.data_vars:
        caveats.append("qr_field_absent")
        return RainDiagnostics(available=False, field_absent=True)

    qr = dataset["qr"]
    _record_units_caveat(qr, "qr", "kg/kg", caveats)
    if _non_finite_count(qr) > 0:
        caveats.append("non_finite_values_detected_in_qr")
    if not _has_finite_values(qr):
        caveats.append("qr_field_entirely_non_finite")
        return RainDiagnostics(available=False)

    max_series: list[TimeValue] = []
    first_rain_time: float | None = None
    max_qr: float | None = None
    time_of_max_qr: float | None = None

    for index, array in enumerate(_time_slices(qr, time.dimension)):
        time_seconds = time.at(index)
        slice_max = _finite_max(array)
        max_series.append(TimeValue(time_seconds=time_seconds, value=slice_max))
        if first_rain_time is None and _threshold_count(array, QR_RAIN_THRESHOLD_KG_KG) > 0:
            first_rain_time = time_seconds
        if slice_max is not None and (max_qr is None or slice_max > max_qr):
            max_qr = slice_max
            time_of_max_qr = time_seconds

    present = first_rain_time is not None
    return RainDiagnostics(
        present=present,
        first_rain_time_seconds=first_rain_time,
        max_qr_kg_kg=max_qr,
        time_of_max_qr_seconds=time_of_max_qr,
        qr_max_time_series=max_series,
        user_message=("Rain water aloft detected." if present else "No rain water aloft detected."),
    )


def _surface_rain_diagnostics(
    dataset: Any, time: _TimeContext, caveats: list[str]
) -> SurfaceRainDiagnostics:
    if "rain" not in dataset.data_vars:
        caveats.append("surface_rain_field_absent")
        return SurfaceRainDiagnostics()

    surface_rain = dataset["rain"]
    units = _attr_string(surface_rain, "units")
    if _non_finite_count(surface_rain) > 0:
        caveats.append("non_finite_values_detected_in_surface_rain")
    if not _has_finite_values(surface_rain):
        caveats.append("surface_rain_field_entirely_non_finite")
        return SurfaceRainDiagnostics(available=False, field_absent=False, units=units)

    max_series: list[TimeValue] = []
    max_surface_rain: float | None = None
    time_of_max_surface_rain: float | None = None

    for index, array in enumerate(_time_slices(surface_rain, time.dimension)):
        time_seconds = time.at(index)
        slice_max = _finite_max(array)
        max_series.append(TimeValue(time_seconds=time_seconds, value=slice_max))
        if slice_max is not None and (max_surface_rain is None or slice_max > max_surface_rain):
            max_surface_rain = slice_max
            time_of_max_surface_rain = time_seconds

    present = max_surface_rain is not None and max_surface_rain > 0.0
    return SurfaceRainDiagnostics(
        present=present,
        max_surface_rain=max_surface_rain,
        time_of_max_surface_rain_seconds=time_of_max_surface_rain,
        surface_rain_max_time_series=max_series,
        units=units,
        user_message=(
            "Surface rain reached the ground." if present else "No surface rain reached the ground."
        ),
        available=True,
        field_absent=False,
    )


def _reflectivity_diagnostics(
    dataset: Any, time: _TimeContext, caveats: list[str]
) -> ReflectivityDiagnostics:
    if "dbz" not in dataset.data_vars:
        caveats.append("dbz_field_absent")
        return ReflectivityDiagnostics()

    dbz = dataset["dbz"]
    units = _attr_string(dbz, "units")
    if _non_finite_count(dbz) > 0:
        caveats.append("non_finite_values_detected_in_dbz")
    if not _has_finite_values(dbz):
        caveats.append("dbz_field_entirely_non_finite")
        return ReflectivityDiagnostics(available=False, field_absent=False, units=units)

    max_series: list[TimeValue] = []
    max_dbz: float | None = None
    time_of_max_dbz: float | None = None

    for index, array in enumerate(_time_slices(dbz, time.dimension)):
        time_seconds = time.at(index)
        slice_max = _finite_max(array)
        max_series.append(TimeValue(time_seconds=time_seconds, value=slice_max))
        if slice_max is not None and (max_dbz is None or slice_max > max_dbz):
            max_dbz = slice_max
            time_of_max_dbz = time_seconds

    return ReflectivityDiagnostics(
        max_dbz=max_dbz,
        time_of_max_dbz_seconds=time_of_max_dbz,
        dbz_max_time_series=max_series,
        units=units,
        user_message=(
            "Reflectivity field available." if max_dbz is not None else "Reflectivity unavailable."
        ),
        available=True,
        field_absent=False,
    )


def _surface_flux_diagnostics(
    dataset: Any,
    time: _TimeContext,
    caveats: list[str],
) -> SurfaceFluxDiagnostics:
    return SurfaceFluxDiagnostics(
        hfx=_surface_flux_field_diagnostics(dataset, "hfx", time, caveats),
        qfx=_surface_flux_field_diagnostics(dataset, "qfx", time, caveats),
    )


def _surface_flux_field_diagnostics(
    dataset: Any,
    field: str,
    time: _TimeContext,
    caveats: list[str],
) -> SurfaceFluxFieldDiagnostics:
    if field not in dataset.data_vars:
        return SurfaceFluxFieldDiagnostics(
            source_field=field,
            field_absent=True,
            caveats=[f"{field}_field_absent"],
        )

    data_array = dataset[field]
    units = _attr_string(data_array, "units")
    finite_count = _finite_count(data_array)
    non_finite_count = _non_finite_count(data_array)
    total_count = _total_count(data_array)
    finite_fraction = _finite_fraction(finite_count, total_count)
    frame_quality = _field_frame_quality(data_array, time)
    config = FIELD_QUALITY_SOURCES[field]
    reason = _field_quality_reason(
        field,
        config,
        finite_count=finite_count,
        non_finite_count=non_finite_count,
        frame_quality=frame_quality,
    )
    field_caveats = _field_quality_caveats(config, reason, non_finite_count)
    caveats.extend(field_caveats)
    if finite_count == 0:
        return SurfaceFluxFieldDiagnostics(
            source_field=field,
            available=False,
            field_absent=False,
            units=units,
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            finite_fraction=finite_fraction,
            frame_quality=frame_quality,
            caveats=_dedupe(field_caveats),
        )

    return SurfaceFluxFieldDiagnostics(
        source_field=field,
        available=True,
        field_absent=False,
        min_value=_finite_min(data_array),
        max_value=_finite_max(data_array),
        mean_value=_finite_mean(data_array),
        units=units,
        finite_count=finite_count,
        non_finite_count=non_finite_count,
        total_count=total_count,
        finite_fraction=finite_fraction,
        frame_quality=frame_quality,
        caveats=_dedupe(field_caveats),
    )


def _low_level_response_diagnostics(
    dataset: Any,
    time: _TimeContext,
    caveats: list[str],
) -> LowLevelResponseDiagnostics:
    return LowLevelResponseDiagnostics(
        qv=_low_level_response_field_diagnostics(
            dataset,
            source_field="qv",
            time=time,
            caveats=caveats,
        ),
        theta_or_temperature=_low_level_response_field_diagnostics(
            dataset,
            source_field=_first_present(
                LOW_LEVEL_THERMODYNAMIC_FIELD_CANDIDATES, list(dataset.data_vars)
            ),
            time=time,
            caveats=caveats,
            missing_reason="theta_or_temperature_field_absent",
        ),
    )


def _localized_response_diagnostics(
    dataset: Any,
    time: _TimeContext,
    *,
    run_configuration: Mapping[str, Any] | None,
    field_quality: Mapping[str, FieldQuality],
    caveats: list[str],
) -> LocalizedResponseDiagnostics:
    patch_payload = _surface_forcing_patch_payload(run_configuration)
    if patch_payload is None:
        return LocalizedResponseDiagnostics(
            support_state="unavailable_not_differential_surface_forcing",
            caveats=["localized_response_requires_differential_surface_forcing_patch"],
        )

    geometry = _patch_geometry_diagnostics(patch_payload)
    if geometry.center_x_m is None or geometry.center_y_m is None:
        return LocalizedResponseDiagnostics(
            support_state="unavailable_missing_patch_center",
            geometry=geometry,
            caveats=["localized_response_missing_patch_center"],
        )
    if geometry.radius_x_m is None or geometry.radius_y_m is None:
        return LocalizedResponseDiagnostics(
            support_state="unavailable_missing_patch_radius",
            geometry=geometry,
            caveats=["localized_response_missing_patch_radius"],
        )

    local_caveats: list[str] = []
    hfx = _patch_spatial_field_diagnostics(dataset, "hfx", time, geometry, field_quality)
    qfx = _patch_spatial_field_diagnostics(dataset, "qfx", time, geometry, field_quality)
    convergence = _patch_convergence_diagnostics(dataset, time, geometry, field_quality)
    updraft = _patch_spatial_field_diagnostics(
        dataset,
        "w",
        time,
        geometry,
        field_quality,
        vertical="max",
        prefer="max",
        minimum_signal=MEANINGFUL_UPDRAFT_THRESHOLD_M_S,
    )
    cloud_water = _patch_spatial_field_diagnostics(
        dataset,
        "qc",
        time,
        geometry,
        field_quality,
        vertical="max",
        prefer="max",
        minimum_signal=QC_CLOUD_THRESHOLD_KG_KG,
    )
    rain_water = _patch_spatial_field_diagnostics(
        dataset,
        "qr",
        time,
        geometry,
        field_quality,
        vertical="max",
        prefer="max",
        minimum_signal=QR_RAIN_THRESHOLD_KG_KG,
    )
    surface_rain = _patch_spatial_field_diagnostics(
        dataset,
        "rain",
        time,
        geometry,
        field_quality,
        minimum_signal=0.0,
    )
    reflectivity = _patch_spatial_field_diagnostics(
        dataset,
        "dbz",
        time,
        geometry,
        field_quality,
        vertical="max",
        prefer="max",
        minimum_signal=0.0,
    )
    for diagnostic in (
        hfx,
        qfx,
        convergence,
        updraft,
        cloud_water,
        rain_water,
        surface_rain,
        reflectivity,
    ):
        local_caveats.extend(diagnostic.caveats)

    emitted_footprint_available = hfx.available or qfx.available
    response_available = any(
        diagnostic.available
        for diagnostic in (
            convergence,
            updraft,
            cloud_water,
            rain_water,
            surface_rain,
            reflectivity,
        )
    )
    if emitted_footprint_available and response_available:
        support_state = "footprint_and_response_diagnostics_available"
    elif emitted_footprint_available:
        support_state = "footprint_available_response_diagnostics_limited"
    else:
        support_state = "unavailable_missing_emitted_surface_flux_fields"

    caveats.extend(local_caveats)
    return LocalizedResponseDiagnostics(
        available=emitted_footprint_available,
        support_state=support_state,
        geometry=geometry,
        hfx_footprint=hfx,
        qfx_footprint=qfx,
        near_surface_convergence=convergence,
        updraft=updraft,
        cloud_water=cloud_water,
        rain_water_aloft=rain_water,
        surface_rain=surface_rain,
        reflectivity=reflectivity,
        caveats=_dedupe(local_caveats),
    )


def _surface_forcing_patch_payload(
    run_configuration: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    if not run_configuration:
        return None
    if run_configuration.get("surface_flux_mode") != DIFFERENTIAL_SURFACE_FORCING_MODE:
        return None
    patch = run_configuration.get("surface_forcing_patch")
    return patch if isinstance(patch, Mapping) else None


def _patch_geometry_diagnostics(
    patch: Mapping[str, Any],
) -> DifferentialPatchGeometryDiagnostics:
    return DifferentialPatchGeometryDiagnostics(
        pattern_sha256=_string_or_none(patch.get("pattern_sha256")),
        shape=_string_or_none(patch.get("shape")),
        center_x_m=_to_float_or_none(patch.get("center_x_m")),
        center_y_m=_to_float_or_none(patch.get("center_y_m")),
        radius_x_m=_to_float_or_none(patch.get("radius_x_m")),
        radius_y_m=_to_float_or_none(patch.get("radius_y_m")),
        taper_width_m=_to_float_or_none(patch.get("taper_width_m")),
        ramp_seconds=_to_float_or_none(patch.get("ramp_seconds")),
    )


def _patch_spatial_field_diagnostics(
    dataset: Any,
    field: str,
    time: _TimeContext,
    geometry: DifferentialPatchGeometryDiagnostics,
    field_quality: Mapping[str, FieldQuality],
    *,
    vertical: Literal["none", "lowest", "max"] = "none",
    prefer: Literal["max", "min"] = "max",
    minimum_signal: float | None = None,
) -> PatchSpatialFieldDiagnostics:
    quality = _localized_field_quality(field, field_quality)
    if field not in dataset.data_vars:
        return PatchSpatialFieldDiagnostics(
            source_field=field,
            field_absent=True,
            quality_state="unavailable",
            quality_reason=f"{field}_field_absent",
            caveats=[f"{field}_localized_response_field_absent"],
        )
    quality_caveats = _localized_quality_caveats(field, quality)
    if quality is not None and quality.quality_state == "untrusted":
        return PatchSpatialFieldDiagnostics(
            source_field=field,
            field_absent=False,
            units=_attr_string(dataset[field], "units"),
            quality_state=quality.quality_state,
            quality_reason=quality.reason,
            finite_count=quality.finite_count,
            non_finite_count=quality.non_finite_count,
            total_count=quality.total_count,
            finite_fraction=quality.finite_fraction,
            caveats=_dedupe([*quality_caveats, f"{field}_localized_response_untrusted_field"]),
        )
    data_array = dataset[field]
    x_name = _first_present(("x", "xh", "lon", "i"), list(data_array.dims))
    y_name = _first_present(("y", "yh", "lat", "j"), list(data_array.dims))
    if x_name is None or y_name is None:
        return PatchSpatialFieldDiagnostics(
            source_field=field,
            field_absent=False,
            units=_attr_string(data_array, "units"),
            quality_state=_localized_quality_state(quality),
            quality_reason=_localized_quality_reason(quality),
            caveats=[
                *quality_caveats,
                f"{field}_localized_response_missing_horizontal_dimensions",
            ],
        )

    time_index = _time_index_for_field_max(data_array, time, field, prefer=prefer)
    if time_index is None:
        return PatchSpatialFieldDiagnostics(
            source_field=field,
            field_absent=False,
            units=_attr_string(data_array, "units"),
            quality_state=_localized_quality_state(quality),
            quality_reason=_localized_quality_reason(quality),
            caveats=[*quality_caveats, f"{field}_localized_response_no_finite_values"],
        )
    array = _select_time_slice(data_array, time.dimension, time_index)
    vertical_selection = _select_vertical_for_localized_response(
        array, vertical=vertical, prefer=prefer
    )
    array = vertical_selection.array
    if x_name not in array.dims or y_name not in array.dims:
        return PatchSpatialFieldDiagnostics(
            source_field=field,
            field_absent=False,
            units=_attr_string(data_array, "units"),
            quality_state=_localized_quality_state(quality),
            quality_reason=_localized_quality_reason(quality),
            time_index=time_index,
            time_seconds=time.at(time_index),
            vertical_coordinate_name=vertical_selection.coordinate_name,
            vertical_level_index=vertical_selection.index,
            vertical_level_height_m=vertical_selection.height_m,
            caveats=[
                *quality_caveats,
                f"{field}_localized_response_horizontal_slice_unavailable",
            ],
        )

    x_values, x_caveat = _horizontal_values(array, x_name)
    y_values, y_caveat = _horizontal_values(array, y_name)
    coordinate_caveats = [caveat for caveat in (x_caveat, y_caveat) if caveat]
    if x_values is None or y_values is None:
        return PatchSpatialFieldDiagnostics(
            source_field=field,
            field_absent=False,
            units=_attr_string(data_array, "units"),
            quality_state=_localized_quality_state(quality),
            quality_reason=_localized_quality_reason(quality),
            time_index=time_index,
            time_seconds=time.at(time_index),
            vertical_coordinate_name=vertical_selection.coordinate_name,
            vertical_level_index=vertical_selection.index,
            vertical_level_height_m=vertical_selection.height_m,
            caveats=_dedupe([*quality_caveats, *coordinate_caveats]),
        )
    cells = _horizontal_cells(
        array,
        x_name=x_name,
        y_name=y_name,
        x_values=x_values,
        y_values=y_values,
    )
    total_count = int(array.sizes[x_name]) * int(array.sizes[y_name])
    finite_count = len(cells)
    non_finite_count = max(0, total_count - finite_count)
    if not cells:
        return PatchSpatialFieldDiagnostics(
            source_field=field,
            field_absent=False,
            units=_attr_string(data_array, "units"),
            quality_state=_localized_quality_state(quality),
            quality_reason=_localized_quality_reason(quality),
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            finite_fraction=_finite_fraction(finite_count, total_count),
            time_index=time_index,
            time_seconds=time.at(time_index),
            vertical_coordinate_name=vertical_selection.coordinate_name,
            vertical_level_index=vertical_selection.index,
            vertical_level_height_m=vertical_selection.height_m,
            caveats=[*quality_caveats, f"{field}_localized_response_no_finite_horizontal_values"],
        )

    best = (
        max(cells, key=lambda cell: cell[2])
        if prefer == "max"
        else min(cells, key=lambda cell: cell[2])
    )
    if minimum_signal is not None and prefer == "max" and best[2] <= minimum_signal:
        return PatchSpatialFieldDiagnostics(
            source_field=field,
            field_absent=False,
            units=_attr_string(data_array, "units"),
            quality_state=_localized_quality_state(quality),
            quality_reason=_localized_quality_reason(quality),
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            finite_fraction=_finite_fraction(finite_count, total_count),
            time_index=time_index,
            time_seconds=time.at(time_index),
            vertical_coordinate_name=vertical_selection.coordinate_name,
            vertical_level_index=vertical_selection.index,
            vertical_level_height_m=vertical_selection.height_m,
            max_value=best[2],
            total_finite_count=len(cells),
            caveats=[*quality_caveats, f"{field}_localized_response_no_signal_above_threshold"],
        )
    core_values: list[float] = []
    taper_values: list[float] = []
    background_values: list[float] = []
    center_value: float | None = None
    center_distance: float | None = None
    for x_value, y_value, value in cells:
        distance = _patch_distance(x_value, y_value, geometry)
        if center_distance is None or distance < center_distance:
            center_distance = distance
            center_value = value
        region = _patch_region(x_value, y_value, geometry)
        if region == "core":
            core_values.append(value)
        elif region == "taper":
            taper_values.append(value)
        else:
            background_values.append(value)

    background_mean = _mean(background_values)
    core_mean = _mean(core_values)
    return PatchSpatialFieldDiagnostics(
        source_field=field,
        available=True,
        field_absent=False,
        units=_attr_string(data_array, "units"),
        quality_state=_localized_quality_state(quality),
        quality_reason=_localized_quality_reason(quality),
        finite_count=finite_count,
        non_finite_count=non_finite_count,
        total_count=total_count,
        finite_fraction=_finite_fraction(finite_count, total_count),
        time_index=time_index,
        time_seconds=time.at(time_index),
        vertical_coordinate_name=vertical_selection.coordinate_name,
        vertical_level_index=vertical_selection.index,
        vertical_level_height_m=vertical_selection.height_m,
        max_value=best[2],
        max_x_m=best[0],
        max_y_m=best[1],
        max_distance_from_patch_center_m=_patch_distance(best[0], best[1], geometry),
        max_inside_patch_radius=_inside_patch_radius(best[0], best[1], geometry),
        max_region=_patch_region(best[0], best[1], geometry),
        center_value=center_value,
        core_mean=core_mean,
        taper_mean=_mean(taper_values),
        background_mean=background_mean,
        center_to_background_ratio=(
            center_value / background_mean if center_value is not None and background_mean else None
        ),
        core_to_background_ratio=(
            core_mean / background_mean if core_mean is not None and background_mean else None
        ),
        core_finite_count=len(core_values),
        taper_finite_count=len(taper_values),
        background_finite_count=len(background_values),
        inside_patch_mean=core_mean,
        outside_patch_mean=background_mean,
        center_to_outside_ratio=(
            center_value / background_mean if center_value is not None and background_mean else None
        ),
        inside_finite_count=len(core_values),
        outside_finite_count=len(background_values),
        total_finite_count=len(cells),
        caveats=quality_caveats,
    )


def _patch_convergence_diagnostics(
    dataset: Any,
    time: _TimeContext,
    geometry: DifferentialPatchGeometryDiagnostics,
    field_quality: Mapping[str, FieldQuality],
) -> PatchConvergenceDiagnostics:
    wind_fields = _localized_convergence_wind_fields(dataset)
    if wind_fields is None:
        return PatchConvergenceDiagnostics(
            caveats=["localized_response_convergence_requires_u_and_v_fields"]
        )
    u, v = wind_fields
    source_fields = [str(u.name or "u"), str(v.name or "v")]
    source_qualities = [
        quality
        for source_field in source_fields
        if (quality := field_quality.get(source_field)) is not None
    ]
    quality_state = _combined_quality_state(source_qualities)
    quality_reason = _combined_quality_reason(source_qualities)
    quality_caveats = _combined_quality_caveats(source_qualities)
    if any(quality.quality_state == "untrusted" for quality in source_qualities):
        return PatchConvergenceDiagnostics(
            source_fields=source_fields,
            quality_state=quality_state,
            quality_reason=quality_reason,
            finite_count=sum(quality.finite_count for quality in source_qualities),
            non_finite_count=sum(quality.non_finite_count for quality in source_qualities),
            total_count=sum(quality.total_count for quality in source_qualities),
            finite_fraction=_finite_fraction(
                sum(quality.finite_count for quality in source_qualities),
                sum(quality.total_count for quality in source_qualities),
            ),
            caveats=_dedupe(
                [*quality_caveats, "localized_response_convergence_untrusted_wind_field"]
            ),
        )
    if u.dims != v.dims:
        return PatchConvergenceDiagnostics(
            source_fields=source_fields,
            quality_state=quality_state,
            quality_reason=quality_reason,
            caveats=["localized_response_convergence_u_v_dimension_mismatch"],
        )
    x_name = _first_present(("x", "xh", "lon", "i"), list(u.dims))
    y_name = _first_present(("y", "yh", "lat", "j"), list(u.dims))
    if x_name is None or y_name is None:
        return PatchConvergenceDiagnostics(
            source_fields=source_fields,
            quality_state=quality_state,
            quality_reason=quality_reason,
            caveats=["localized_response_convergence_missing_horizontal_dimensions"],
        )

    selected: (
        tuple[int, tuple[float, float, float], list[tuple[float, float, float]], _VerticalSelection]
        | None
    ) = None
    max_time_series: list[TimeValue] = []
    selected_counts: tuple[int, int] = (0, 0)
    coordinate_caveats: list[str] = []
    for time_index, u_time_slice in enumerate(_time_slices(u, time.dimension)):
        v_time_slice = _select_time_slice(v, time.dimension, time_index)
        u_selection = _select_vertical_for_localized_response(
            u_time_slice,
            vertical="lowest",
            prefer="max",
        )
        v_selection = _select_vertical_for_localized_response(
            v_time_slice,
            vertical="lowest",
            prefer="max",
        )
        x_values, x_caveat = _horizontal_values(u_selection.array, x_name)
        y_values, y_caveat = _horizontal_values(u_selection.array, y_name)
        coordinate_caveats = [caveat for caveat in (x_caveat, y_caveat) if caveat]
        if x_values is None or y_values is None:
            return PatchConvergenceDiagnostics(
                source_fields=source_fields,
                quality_state=quality_state,
                quality_reason=quality_reason,
                time_index=time_index,
                time_seconds=time.at(time_index),
                vertical_coordinate_name=u_selection.coordinate_name,
                vertical_level_index=u_selection.index,
                vertical_level_height_m=u_selection.height_m,
                caveats=_dedupe([*quality_caveats, *coordinate_caveats]),
            )
        if len(x_values) < 3 or len(y_values) < 3:
            return PatchConvergenceDiagnostics(
                source_fields=source_fields,
                quality_state=quality_state,
                quality_reason=quality_reason,
                time_index=time_index,
                time_seconds=time.at(time_index),
                vertical_coordinate_name=u_selection.coordinate_name,
                vertical_level_index=u_selection.index,
                vertical_level_height_m=u_selection.height_m,
                caveats=[
                    *quality_caveats,
                    "localized_response_convergence_requires_at_least_3x3_horizontal_grid",
                ],
            )
        convergence_cells, finite_count, total_count = _convergence_cells(
            u_selection.array,
            v_selection.array,
            x_name=x_name,
            y_name=y_name,
            x_values=x_values,
            y_values=y_values,
        )
        time_best = max(convergence_cells, key=lambda cell: cell[2]) if convergence_cells else None
        max_time_series.append(
            TimeValue(time_seconds=time.at(time_index), value=time_best[2] if time_best else None)
        )
        if time_best is not None and (selected is None or time_best[2] > selected[1][2]):
            selected = (time_index, time_best, convergence_cells, u_selection)
            selected_counts = (finite_count, total_count)

    if selected is None:
        return PatchConvergenceDiagnostics(
            source_fields=source_fields,
            quality_state=quality_state,
            quality_reason=quality_reason,
            max_convergence_time_series=max_time_series,
            caveats=[
                *quality_caveats,
                "localized_response_convergence_no_finite_collocated_values",
            ],
        )

    time_index, best, convergence_cells, vertical_selection = selected
    finite_count, total_count = selected_counts
    core_values = [
        value
        for x_value, y_value, value in convergence_cells
        if _patch_region(x_value, y_value, geometry) == "core"
    ]
    taper_values = [
        value
        for x_value, y_value, value in convergence_cells
        if _patch_region(x_value, y_value, geometry) == "taper"
    ]
    background_values = [
        value
        for x_value, y_value, value in convergence_cells
        if _patch_region(x_value, y_value, geometry) == "background"
    ]
    core_mean = _mean(core_values)
    background_mean = _mean(background_values)
    return PatchConvergenceDiagnostics(
        available=True,
        source_fields=source_fields,
        quality_state=quality_state,
        quality_reason=quality_reason,
        finite_count=finite_count,
        non_finite_count=max(0, total_count - finite_count),
        total_count=total_count,
        finite_fraction=_finite_fraction(finite_count, total_count),
        time_index=time_index,
        time_seconds=time.at(time_index),
        vertical_coordinate_name=vertical_selection.coordinate_name,
        vertical_level_index=vertical_selection.index,
        vertical_level_height_m=vertical_selection.height_m,
        max_convergence_s_1=best[2],
        max_convergence_x_m=best[0],
        max_convergence_y_m=best[1],
        max_convergence_distance_from_patch_center_m=_patch_distance(best[0], best[1], geometry),
        max_convergence_inside_patch_radius=_inside_patch_radius(best[0], best[1], geometry),
        max_convergence_region=_patch_region(best[0], best[1], geometry),
        max_convergence_time_series=max_time_series,
        core_mean_convergence_s_1=core_mean,
        taper_mean_convergence_s_1=_mean(taper_values),
        background_mean_convergence_s_1=background_mean,
        core_to_background_convergence_ratio=(
            core_mean / background_mean if core_mean is not None and background_mean else None
        ),
        core_finite_count=len(core_values),
        taper_finite_count=len(taper_values),
        background_finite_count=len(background_values),
        inside_patch_mean_convergence_s_1=core_mean,
        outside_patch_mean_convergence_s_1=background_mean,
        caveats=quality_caveats,
    )


def _localized_convergence_wind_fields(dataset: Any) -> tuple[Any, Any] | None:
    if "uinterp" in dataset.data_vars and "vinterp" in dataset.data_vars:
        return dataset["uinterp"], dataset["vinterp"]
    if "u" in dataset.data_vars and "v" in dataset.data_vars:
        return dataset["u"], dataset["v"]
    return None


def _low_level_response_field_diagnostics(
    dataset: Any,
    *,
    source_field: str | None,
    time: _TimeContext,
    caveats: list[str],
    missing_reason: str | None = None,
) -> LowLevelResponseFieldDiagnostics:
    if source_field is None or source_field not in dataset.data_vars:
        reason = missing_reason or f"{source_field or 'unknown'}_field_absent"
        return LowLevelResponseFieldDiagnostics(
            source_field=source_field,
            field_absent=True,
            caveats=[reason],
        )

    data_array = dataset[source_field]
    units = _attr_string(data_array, "units")
    field_caveats: list[str] = []
    vertical_name = _first_present(VERTICAL_COORDINATE_CANDIDATES, list(data_array.dims))
    if vertical_name is None:
        reason = f"{source_field}_low_level_response_missing_vertical_dimension"
        caveats.append(reason)
        return LowLevelResponseFieldDiagnostics(
            source_field=source_field,
            field_absent=False,
            units=units,
            caveats=[reason],
        )
    if vertical_name not in data_array.coords:
        reason = f"{source_field}_low_level_response_missing_vertical_coordinate"
        caveats.append(reason)
        return LowLevelResponseFieldDiagnostics(
            source_field=source_field,
            field_absent=False,
            vertical_coordinate_name=vertical_name,
            units=units,
            caveats=[reason],
        )
    vertical_coord = data_array.coords[vertical_name]
    vertical_units = _attr_string(vertical_coord, "units")
    normalized_units = _normalized_height_units(vertical_units)
    if normalized_units is None:
        reason = f"{source_field}_low_level_response_vertical_units_not_supported:{vertical_units}"
        caveats.append(reason)
        return LowLevelResponseFieldDiagnostics(
            source_field=source_field,
            field_absent=False,
            vertical_coordinate_name=vertical_name,
            vertical_coordinate_units=vertical_units,
            units=units,
            caveats=[reason],
        )
    if vertical_units is None:
        field_caveats.append(
            f"{source_field}_low_level_response_vertical_units_missing_assumed_meters"
        )

    vertical_values = [
        _height_in_meters(_to_float_or_none(value), vertical_units)
        for value in vertical_coord.values.tolist()
    ]
    weighted_levels = _low_level_weighted_levels(vertical_values)
    if not weighted_levels:
        reason = f"{source_field}_low_level_response_no_levels_in_0_1_km"
        caveats.append(reason)
        return LowLevelResponseFieldDiagnostics(
            source_field=source_field,
            field_absent=False,
            vertical_coordinate_name=vertical_name,
            vertical_coordinate_units=vertical_units,
            vertical_coordinate_method=LOW_LEVEL_RESPONSE_METHOD,
            units=units,
            caveats=_dedupe([*field_caveats, reason]),
        )
    if time.dimension is None or time.dimension not in data_array.dims:
        reason = f"{source_field}_low_level_response_requires_time_dimension"
        caveats.append(reason)
        return LowLevelResponseFieldDiagnostics(
            source_field=source_field,
            field_absent=False,
            vertical_coordinate_name=vertical_name,
            vertical_coordinate_units=vertical_units,
            vertical_coordinate_method=LOW_LEVEL_RESPONSE_METHOD,
            units=units,
            caveats=_dedupe([*field_caveats, reason]),
        )
    time_size = int(data_array.sizes[time.dimension])
    if time_size < 2:
        reason = f"{source_field}_low_level_response_requires_at_least_two_time_steps"
        caveats.append(reason)
        time_index = 0 if time_size else None
        layer_stats = (
            _low_level_layer_stats(
                data_array.isel({time.dimension: 0}),
                vertical_name=vertical_name,
                weighted_levels=weighted_levels,
            )
            if time_size
            else _empty_low_level_layer_stats()
        )
        return LowLevelResponseFieldDiagnostics(
            source_field=source_field,
            field_absent=False,
            vertical_coordinate_name=vertical_name,
            vertical_coordinate_units=vertical_units,
            vertical_coordinate_method=LOW_LEVEL_RESPONSE_METHOD,
            time_dimension=time.dimension,
            first_time_index=time_index,
            final_time_index=time_index,
            first_time_seconds=time.at(0) if time_size else None,
            final_time_seconds=time.at(time_size - 1) if time_size else None,
            first_mean_value=layer_stats["mean"],
            final_mean_value=layer_stats["mean"],
            units=units,
            first_finite_count=layer_stats["finite_count"],
            first_non_finite_count=layer_stats["non_finite_count"],
            first_total_count=layer_stats["total_count"],
            final_finite_count=layer_stats["finite_count"],
            final_non_finite_count=layer_stats["non_finite_count"],
            final_total_count=layer_stats["total_count"],
            caveats=_dedupe([*field_caveats, reason]),
        )

    first_time_index = 0
    final_time_index = time_size - 1
    early_time_index = _low_level_early_response_end_index(time, time_size)
    first_stats = _low_level_layer_stats(
        data_array.isel({time.dimension: first_time_index}),
        vertical_name=vertical_name,
        weighted_levels=weighted_levels,
    )
    final_stats = _low_level_layer_stats(
        data_array.isel({time.dimension: final_time_index}),
        vertical_name=vertical_name,
        weighted_levels=weighted_levels,
    )
    early_stats = (
        _low_level_layer_stats(
            data_array.isel({time.dimension: early_time_index}),
            vertical_name=vertical_name,
            weighted_levels=weighted_levels,
        )
        if early_time_index is not None
        else None
    )
    if (
        first_stats["non_finite_count"] > 0
        or final_stats["non_finite_count"] > 0
        or (early_stats is not None and early_stats["non_finite_count"] > 0)
    ):
        field_caveat = f"non_finite_values_detected_in_{source_field}_low_level_response"
        field_caveats.append(field_caveat)
        caveats.append(field_caveat)

    first_mean = first_stats["mean"]
    final_mean = final_stats["mean"]
    early_mean = early_stats["mean"] if early_stats is not None else None
    first_endpoint_available = first_stats["finite_count"] > 0 and first_mean is not None
    early_endpoint_available = (
        early_stats is not None and early_stats["finite_count"] > 0 and early_mean is not None
    )
    final_endpoint_available = final_stats["finite_count"] > 0 and final_mean is not None

    if not first_endpoint_available:
        reason = f"{source_field}_low_level_response_start_endpoint_entirely_non_finite"
        field_caveats.extend(
            [reason, f"{source_field}_low_level_response_endpoint_entirely_non_finite"]
        )
        caveats.extend([reason, f"{source_field}_low_level_response_endpoint_entirely_non_finite"])
        return LowLevelResponseFieldDiagnostics(
            source_field=source_field,
            field_absent=False,
            vertical_coordinate_name=vertical_name,
            vertical_coordinate_units=vertical_units,
            vertical_coordinate_method=LOW_LEVEL_RESPONSE_METHOD,
            time_dimension=time.dimension,
            first_time_index=first_time_index,
            final_time_index=final_time_index,
            first_time_seconds=time.at(first_time_index),
            final_time_seconds=time.at(final_time_index),
            units=units,
            first_finite_count=first_stats["finite_count"],
            first_non_finite_count=first_stats["non_finite_count"],
            first_total_count=first_stats["total_count"],
            final_finite_count=final_stats["finite_count"],
            final_non_finite_count=final_stats["non_finite_count"],
            final_total_count=final_stats["total_count"],
            caveats=_dedupe(field_caveats),
        )

    if early_time_index is None:
        reason = f"{source_field}_low_level_response_missing_early_output_30_90min"
        field_caveats.append(reason)
        caveats.append(reason)
    elif not early_endpoint_available:
        reason = f"{source_field}_low_level_response_early_endpoint_entirely_non_finite"
        field_caveats.append(reason)
        caveats.append(reason)
    if not final_endpoint_available:
        reason = f"{source_field}_low_level_response_final_endpoint_entirely_non_finite"
        field_caveats.append(reason)
        caveats.append(reason)

    early_delta = (
        early_mean - first_mean
        if early_endpoint_available
        and early_mean is not None
        and first_mean is not None
        and early_time_index is not None
        else None
    )
    full_run_has_distinct_endpoint = (
        final_time_index != early_time_index
        if early_time_index is not None
        else final_time_index != 0
    )
    full_run_delta = (
        final_mean - first_mean
        if final_endpoint_available and first_mean is not None and final_mean is not None
        else None
    )
    early_response_available = early_delta is not None
    full_run_response_available = full_run_delta is not None and full_run_has_distinct_endpoint
    return LowLevelResponseFieldDiagnostics(
        source_field=source_field,
        available=early_response_available,
        early_response_available=early_response_available,
        full_run_response_available=full_run_response_available,
        field_absent=False,
        vertical_coordinate_name=vertical_name,
        vertical_coordinate_units=vertical_units,
        vertical_coordinate_method=LOW_LEVEL_RESPONSE_METHOD,
        time_dimension=time.dimension,
        first_time_index=first_time_index,
        final_time_index=final_time_index,
        first_time_seconds=time.at(first_time_index),
        final_time_seconds=time.at(final_time_index),
        first_mean_value=first_mean,
        final_mean_value=final_mean,
        delta_value=early_delta,
        early_response_start_time_index=first_time_index if early_delta is not None else None,
        early_response_end_time_index=early_time_index if early_delta is not None else None,
        early_response_start_time_seconds=(
            time.at(first_time_index) if early_delta is not None else None
        ),
        early_response_end_time_seconds=(
            time.at(early_time_index)
            if early_delta is not None and early_time_index is not None
            else None
        ),
        early_response_start_mean_value=first_mean if early_delta is not None else None,
        early_response_end_mean_value=early_mean if early_delta is not None else None,
        early_response_delta=early_delta,
        early_response_start_finite_count=(
            first_stats["finite_count"] if early_delta is not None else 0
        ),
        early_response_start_non_finite_count=(
            first_stats["non_finite_count"] if early_delta is not None else 0
        ),
        early_response_start_total_count=(
            first_stats["total_count"] if early_delta is not None else 0
        ),
        early_response_end_finite_count=(
            early_stats["finite_count"]
            if early_stats is not None and early_delta is not None
            else 0
        ),
        early_response_end_non_finite_count=(
            early_stats["non_finite_count"]
            if early_stats is not None and early_delta is not None
            else 0
        ),
        early_response_end_total_count=(
            early_stats["total_count"] if early_stats is not None and early_delta is not None else 0
        ),
        full_run_delta=full_run_delta if full_run_response_available else None,
        units=units,
        first_finite_count=first_stats["finite_count"],
        first_non_finite_count=first_stats["non_finite_count"],
        first_total_count=first_stats["total_count"],
        final_finite_count=final_stats["finite_count"],
        final_non_finite_count=final_stats["non_finite_count"],
        final_total_count=final_stats["total_count"],
        caveats=_dedupe(field_caveats),
    )


def _low_level_weighted_levels(
    vertical_values: list[float | None],
) -> list[tuple[int, float]]:
    valid_levels = sorted(
        (index, value) for index, value in enumerate(vertical_values) if value is not None
    )
    if not valid_levels:
        return []
    if len(valid_levels) == 1:
        index, value = valid_levels[0]
        if LOW_LEVEL_RESPONSE_LAYER_BOTTOM_M <= value <= LOW_LEVEL_RESPONSE_LAYER_TOP_M:
            return [(index, LOW_LEVEL_RESPONSE_LAYER_TOP_M - LOW_LEVEL_RESPONSE_LAYER_BOTTOM_M)]
        return []

    weighted: list[tuple[int, float]] = []
    for position, (index, value) in enumerate(valid_levels):
        if position == 0:
            next_value = valid_levels[position + 1][1]
            lower = value - (next_value - value) / 2.0
        else:
            previous_value = valid_levels[position - 1][1]
            lower = (previous_value + value) / 2.0
        if position == len(valid_levels) - 1:
            previous_value = valid_levels[position - 1][1]
            upper = value + (value - previous_value) / 2.0
        else:
            next_value = valid_levels[position + 1][1]
            upper = (value + next_value) / 2.0
        clipped_lower = max(lower, LOW_LEVEL_RESPONSE_LAYER_BOTTOM_M)
        clipped_upper = min(upper, LOW_LEVEL_RESPONSE_LAYER_TOP_M)
        thickness = clipped_upper - clipped_lower
        if thickness > 0:
            weighted.append((index, thickness))
    return weighted


def _low_level_early_response_end_index(time: _TimeContext, time_size: int) -> int | None:
    start_time = time.at(0)
    if start_time is None:
        return None
    candidates: list[tuple[float, int]] = []
    for index in range(1, time_size):
        end_time = time.at(index)
        if end_time is None:
            continue
        elapsed = end_time - start_time
        if LOW_LEVEL_RESPONSE_EARLY_MIN_SECONDS <= elapsed <= LOW_LEVEL_RESPONSE_EARLY_MAX_SECONDS:
            candidates.append((abs(elapsed - LOW_LEVEL_RESPONSE_EARLY_TARGET_SECONDS), index))
    if not candidates:
        return None
    return min(candidates)[1]


def _empty_low_level_layer_stats() -> _LowLevelLayerStats:
    return {"mean": None, "finite_count": 0, "non_finite_count": 0, "total_count": 0}


def _low_level_layer_stats(
    data_array: Any,
    *,
    vertical_name: str,
    weighted_levels: list[tuple[int, float]],
) -> _LowLevelLayerStats:
    weighted_sum = 0.0
    total_weight = 0.0
    finite_count = 0
    non_finite_count = 0
    total_count = 0
    for vertical_index, thickness_m in weighted_levels:
        layer = data_array.isel({vertical_name: vertical_index})
        for value in layer.values.reshape(-1).tolist():
            total_count += 1
            parsed = _to_float_or_none(value)
            if parsed is None or not isfinite(parsed):
                non_finite_count += 1
                continue
            finite_count += 1
            weighted_sum += parsed * thickness_m
            total_weight += thickness_m
    return {
        "mean": weighted_sum / total_weight if total_weight else None,
        "finite_count": finite_count,
        "non_finite_count": non_finite_count,
        "total_count": total_count,
    }


def _cloud_extent_array(dataset: Any, qc: Any, caveats: list[str]) -> tuple[Any, list[str]]:
    """Return the field used for cloud base/top diagnostics.

    Liquid cloud water remains the source of truth for cloud formation and max-qc
    diagnostics. For top diagnostics, deep-convection output can put the upper
    cloud in ice/snow/graupel fields, so the raw trace envelope should include
    compatible hydrometeor mixing-ratio fields when they are present.
    """

    extent = qc
    included_fields: list[str] = ["qc"]
    for field_name in HYDROMETEOR_CLOUD_TOP_FIELDS:
        if field_name not in dataset.data_vars:
            continue
        field = dataset[field_name]
        if field.dims != qc.dims:
            caveats.append(f"cloud_top_skipped_{field_name}_dimension_mismatch")
            continue
        extent = extent + field
        included_fields.append(field_name)
    if len(included_fields) > 1:
        caveat = "cloud_top_uses_total_hydrometeor_fields:" + ",".join(included_fields)
        if caveat not in caveats:
            caveats.append(caveat)
    return extent, included_fields


def _hydrometeor_source_arrays(dataset: Any, qc: Any, source_fields: list[str]) -> dict[str, Any]:
    arrays: dict[str, Any] = {}
    for field in source_fields:
        if field == "qc":
            arrays[field] = qc
        elif field in dataset.data_vars:
            arrays[field] = dataset[field]
    return arrays


def _cloud_top_with_level_support(
    data_array: Any,
    *,
    source_arrays: dict[str, Any],
    caveats: list[str],
    time_seconds: float | None,
    minimum_cells: int,
    require_connected_levels: bool,
) -> tuple[float | None, float | None, CloudTopSupportRecord]:
    vertical_name = _first_present(VERTICAL_COORDINATE_CANDIDATES, list(data_array.dims))
    if vertical_name is None:
        caveats.append("cloud_object_top_unavailable_missing_vertical_coordinate")
        return None, None, CloudTopSupportRecord(time_seconds=time_seconds)
    if require_connected_levels:
        caveat = "coherent_cloud_object_support_uses_grid_cell_count_not_physical_area"
        if caveat not in caveats:
            caveats.append(caveat)

    vertical_values = _vertical_values(data_array, vertical_name, caveats)
    supported_levels: list[int] = []
    level_counts: dict[int, int] = {}
    for index in range(int(data_array.sizes[vertical_name])):
        count = _threshold_count(
            data_array.isel({vertical_name: index}),
            QC_CLOUD_THRESHOLD_KG_KG,
        )
        level_counts[index] = count
        if count >= minimum_cells:
            supported_levels.append(index)

    if not supported_levels:
        return None, None, CloudTopSupportRecord(time_seconds=time_seconds)

    connected_levels = (
        _lowest_connected_level_block(supported_levels)
        if require_connected_levels
        else supported_levels
    )
    detached_levels = [level for level in supported_levels if level not in connected_levels]
    if detached_levels and require_connected_levels:
        caveat = "detached_hydrometeor_layer_not_counted_as_coherent_cloud_object"
        if caveat not in caveats:
            caveats.append(caveat)

    level_entries: list[tuple[int, float]] = []
    for index in connected_levels:
        if index >= len(vertical_values):
            continue
        vertical_value = vertical_values[index]
        if vertical_value is not None:
            level_entries.append((index, vertical_value))
    if not level_entries:
        return None, None, CloudTopSupportRecord(time_seconds=time_seconds)

    top_index, top_value = max(level_entries, key=lambda entry: entry[1])
    level_values = [value for _index, value in level_entries]
    top_defining_species = _top_defining_species(
        source_arrays,
        vertical_name=vertical_name,
        vertical_index=top_index,
    )
    supporting_species = _supporting_species(
        source_arrays,
        vertical_name=vertical_name,
        vertical_indices=connected_levels,
    )
    if require_connected_levels and "qc" not in supporting_species:
        caveat = "coherent_cloud_object_without_liquid_cloud_water_support"
        if caveat not in caveats:
            caveats.append(caveat)

    return (
        min(level_values),
        max(level_values),
        CloudTopSupportRecord(
            time_seconds=time_seconds,
            top_m=top_value,
            top_defining_species=top_defining_species,
            supporting_species=supporting_species,
            threshold_kg_kg=QC_CLOUD_THRESHOLD_KG_KG,
            qualifying_cell_count=level_counts.get(top_index, 0),
            continuity_supported=bool(connected_levels),
        ),
    )


def _lowest_connected_level_block(supported_levels: list[int]) -> list[int]:
    sorted_levels = sorted(supported_levels)
    connected = [sorted_levels[0]]
    for level in sorted_levels[1:]:
        if level == connected[-1] + 1:
            connected.append(level)
        else:
            break
    return connected


def _top_defining_species(
    source_arrays: dict[str, Any],
    *,
    vertical_name: str,
    vertical_index: int,
) -> list[str]:
    species: list[str] = []
    for field, array in source_arrays.items():
        if vertical_name not in array.dims or vertical_index >= int(array.sizes[vertical_name]):
            continue
        count = _threshold_count(
            array.isel({vertical_name: vertical_index}),
            QC_CLOUD_THRESHOLD_KG_KG,
        )
        if count > 0:
            species.append(field)
    return species


def _supporting_species(
    source_arrays: dict[str, Any],
    *,
    vertical_name: str,
    vertical_indices: list[int],
) -> list[str]:
    species: list[str] = []
    for field, array in source_arrays.items():
        if vertical_name not in array.dims:
            continue
        for vertical_index in vertical_indices:
            if vertical_index >= int(array.sizes[vertical_name]):
                continue
            count = _threshold_count(
                array.isel({vertical_name: vertical_index}),
                QC_CLOUD_THRESHOLD_KG_KG,
            )
            if count > 0:
                species.append(field)
                break
    return species


def _cloud_base_top(qc: Any, caveats: list[str]) -> tuple[float | None, float | None]:
    vertical_name = _first_present(VERTICAL_COORDINATE_CANDIDATES, list(qc.dims))
    if vertical_name is None:
        caveats.append("cloud_base_top_unavailable_missing_vertical_coordinate")
        return None, None
    vertical_values: list[float | None]
    if vertical_name not in qc.coords:
        caveats.append("cloud_base_top_vertical_coordinate_inferred_from_index")
        vertical_values = [float(index) for index in range(int(qc.sizes[vertical_name]))]
    else:
        vertical_coord = qc.coords[vertical_name]
        vertical_values = [
            _height_in_meters(_to_float_or_none(value), _attr_string(vertical_coord, "units"))
            for value in vertical_coord.values.tolist()
        ]
        units = _attr_string(vertical_coord, "units")
        if units is None:
            caveats.append("cloud_base_top_vertical_units_missing_assumed_meters")
        elif _normalized_height_units(units) is None:
            caveats.append(f"cloud_base_top_vertical_units_not_meters:{units}")
    cloudy_by_vertical = (qc >= QC_CLOUD_THRESHOLD_KG_KG).any(
        dim=[dimension for dimension in qc.dims if dimension != vertical_name],
    )
    cloudy_values: list[float] = []
    for index, present in enumerate(cloudy_by_vertical.values.tolist()):
        vertical_value = vertical_values[index]
        if bool(present) and vertical_value is not None:
            cloudy_values.append(vertical_value)
    if not cloudy_values:
        return None, None
    return min(cloudy_values), max(cloudy_values)


def _height_of_level_max(data_array: Any, caveats: list[str]) -> float | None:
    vertical_name = _first_present(VERTICAL_COORDINATE_CANDIDATES, list(data_array.dims))
    if vertical_name is None:
        caveats.append("max_height_unavailable_missing_vertical_coordinate")
        return None
    vertical_values = _vertical_values(data_array, vertical_name, caveats)
    best_value: float | None = None
    best_height: float | None = None
    for index in range(int(data_array.sizes[vertical_name])):
        level_value = _finite_max(data_array.isel({vertical_name: index}))
        if level_value is not None and (best_value is None or level_value > best_value):
            best_value = level_value
            best_height = vertical_values[index]
    return best_height


def _vertical_values(data_array: Any, vertical_name: str, caveats: list[str]) -> list[float | None]:
    if vertical_name not in data_array.coords:
        caveats.append("vertical_coordinate_inferred_from_index")
        return [float(index) for index in range(int(data_array.sizes[vertical_name]))]
    vertical_coord = data_array.coords[vertical_name]
    vertical_values = [
        _height_in_meters(_to_float_or_none(value), _attr_string(vertical_coord, "units"))
        for value in vertical_coord.values.tolist()
    ]
    units = _attr_string(vertical_coord, "units")
    if units is None:
        caveats.append("vertical_units_missing_assumed_meters")
    elif _normalized_height_units(units) is None:
        caveats.append(f"vertical_units_not_meters:{units}")
    return vertical_values


def _height_in_meters(value: float | None, units: str | None) -> float | None:
    if value is None:
        return None
    normalized = _normalized_height_units(units)
    if normalized == "km":
        return value * 1000.0
    return value


def _normalized_height_units(units: str | None) -> str | None:
    if units is None:
        return "m"
    normalized = units.strip().lower()
    if normalized in {"m", "meter", "meters"}:
        return "m"
    if normalized in {"km", "kilometer", "kilometers"}:
        return "km"
    return None


def _time_context(dataset: Any, time_dimension: str | None) -> _TimeContext:
    if time_dimension is None:
        return _TimeContext(
            dimension=None,
            values=[0.0],
            diagnostics=TimeDiagnostics(
                source="single_output_no_time_dimension", fallback_used=True
            ),
        )
    size = int(dataset.sizes[time_dimension])
    if time_dimension in dataset.coords:
        values = [
            _to_float_or_none(value) for value in dataset.coords[time_dimension].values.tolist()
        ]
        return _TimeContext(
            dimension=time_dimension,
            values=values,
            diagnostics=TimeDiagnostics(
                source="netcdf_time_coordinate",
                fallback_used=False,
                coordinate_name=time_dimension,
            ),
        )
    return _TimeContext(
        dimension=time_dimension,
        values=[float(index) for index in range(size)],
        diagnostics=TimeDiagnostics(
            source="inferred_output_index",
            fallback_used=True,
            coordinate_name=time_dimension,
        ),
    )


def _primary_time_dimension(dataset: Any) -> str | None:
    for candidate in TIME_DIMENSION_CANDIDATES:
        if candidate in dataset.sizes:
            return candidate
    for data_array in dataset.data_vars.values():
        for candidate in TIME_DIMENSION_CANDIDATES:
            if candidate in data_array.dims:
                return candidate
    return None


def _time_slices(data_array: Any, time_dimension: str | None) -> list[Any]:
    if time_dimension is None or time_dimension not in data_array.dims:
        return [data_array]
    return [
        data_array.isel({time_dimension: index})
        for index in range(data_array.sizes[time_dimension])
    ]


def _select_time_slice(data_array: Any, time_dimension: str | None, time_index: int) -> Any:
    if time_dimension is None or time_dimension not in data_array.dims:
        return data_array
    return data_array.isel({time_dimension: time_index})


def _time_index_for_field_max(
    data_array: Any,
    time: _TimeContext,
    field: str,
    *,
    prefer: Literal["max", "min"],
) -> int | None:
    slices = _time_slices(data_array, time.dimension)
    best_index: int | None = None
    best_value: float | None = None
    for index, array in enumerate(slices):
        value = _finite_max(array) if prefer == "max" else _finite_min(array)
        if value is None:
            continue
        if best_value is None:
            best_index = index
            best_value = value
            continue
        if prefer == "max" and value > best_value:
            best_index = index
            best_value = value
        elif prefer == "min" and value < best_value:
            best_index = index
            best_value = value
    if best_index is None:
        return None
    if time.dimension is not None and time.dimension in data_array.dims:
        return best_index
    return 0


def _select_vertical_for_localized_response(
    data_array: Any,
    *,
    vertical: Literal["none", "lowest", "max"],
    prefer: Literal["max", "min"],
) -> _VerticalSelection:
    vertical_name = _first_present(VERTICAL_COORDINATE_CANDIDATES, list(data_array.dims))
    if vertical == "none" or vertical_name is None:
        return _VerticalSelection(array=data_array)
    if vertical == "lowest":
        return _VerticalSelection(
            array=data_array.isel({vertical_name: 0}),
            coordinate_name=vertical_name,
            index=0,
            height_m=_localized_vertical_height_m(data_array, vertical_name, 0),
        )
    best_index = 0
    best_value: float | None = None
    for index in range(int(data_array.sizes[vertical_name])):
        level = data_array.isel({vertical_name: index})
        value = _finite_max(level) if prefer == "max" else _finite_min(level)
        if value is None:
            continue
        if best_value is None:
            best_index = index
            best_value = value
            continue
        if prefer == "max" and value > best_value:
            best_index = index
            best_value = value
        elif prefer == "min" and value < best_value:
            best_index = index
            best_value = value
    return _VerticalSelection(
        array=data_array.isel({vertical_name: best_index}),
        coordinate_name=vertical_name,
        index=best_index,
        height_m=_localized_vertical_height_m(data_array, vertical_name, best_index),
    )


def _localized_vertical_height_m(data_array: Any, vertical_name: str, index: int) -> float | None:
    if vertical_name not in data_array.coords:
        return None
    coordinate = data_array.coords[vertical_name]
    values = coordinate.values.tolist()
    if index >= len(values):
        return None
    return _height_in_meters(_to_float_or_none(values[index]), _attr_string(coordinate, "units"))


def _horizontal_values(data_array: Any, dimension: str) -> tuple[list[float] | None, str | None]:
    if dimension not in data_array.coords:
        return None, f"localized_response_{dimension}_coordinate_missing"
    coordinate = data_array.coords[dimension]
    units = _attr_string(coordinate, "units")
    if units is None:
        return None, f"localized_response_{dimension}_coordinate_units_missing"
    if _normalized_height_units(units) is None:
        return None, f"localized_response_{dimension}_coordinate_units_not_supported:{units}"
    values = [
        _height_in_meters(_to_float_or_none(value), units) for value in coordinate.values.tolist()
    ]
    if any(value is None for value in values):
        return None, f"localized_response_{dimension}_coordinate_values_not_finite"
    return [float(value) for value in values if value is not None], None


def _convergence_cells(
    u_slice: Any,
    v_slice: Any,
    *,
    x_name: str,
    y_name: str,
    x_values: list[float],
    y_values: list[float],
) -> tuple[list[tuple[float, float, float]], int, int]:
    convergence_cells: list[tuple[float, float, float]] = []
    total_count = max(0, len(x_values) - 2) * max(0, len(y_values) - 2)
    for y_index in range(1, len(y_values) - 1):
        for x_index in range(1, len(x_values) - 1):
            u_left = _array_value_2d(u_slice, x_name, y_name, x_index - 1, y_index)
            u_right = _array_value_2d(u_slice, x_name, y_name, x_index + 1, y_index)
            v_down = _array_value_2d(v_slice, x_name, y_name, x_index, y_index - 1)
            v_up = _array_value_2d(v_slice, x_name, y_name, x_index, y_index + 1)
            if None in {u_left, u_right, v_down, v_up}:
                continue
            dx = x_values[x_index + 1] - x_values[x_index - 1]
            dy = y_values[y_index + 1] - y_values[y_index - 1]
            if dx == 0 or dy == 0:
                continue
            divergence = ((u_right - u_left) / dx) + ((v_up - v_down) / dy)  # type: ignore[operator]
            convergence_cells.append((x_values[x_index], y_values[y_index], -divergence))
    return convergence_cells, len(convergence_cells), total_count


def _horizontal_cells(
    data_array: Any,
    *,
    x_name: str,
    y_name: str,
    x_values: list[float],
    y_values: list[float],
) -> list[tuple[float, float, float]]:
    cells: list[tuple[float, float, float]] = []
    if x_name not in data_array.dims or y_name not in data_array.dims:
        return cells
    for y_index, y_value in enumerate(y_values):
        for x_index, x_value in enumerate(x_values):
            value = _array_value_2d(data_array, x_name, y_name, x_index, y_index)
            if value is not None:
                cells.append((x_value, y_value, value))
    return cells


def _array_value_2d(
    data_array: Any,
    x_name: str,
    y_name: str,
    x_index: int,
    y_index: int,
) -> float | None:
    try:
        value = data_array.isel({x_name: x_index, y_name: y_index}).values.item()
    except (IndexError, ValueError, TypeError, AttributeError):
        return None
    parsed = _to_float_or_none(value)
    if parsed is None or not isfinite(parsed):
        return None
    return parsed


def _patch_distance(
    x_m: float,
    y_m: float,
    geometry: DifferentialPatchGeometryDiagnostics,
) -> float:
    center_x = geometry.center_x_m or 0.0
    center_y = geometry.center_y_m or 0.0
    return hypot(x_m - center_x, y_m - center_y)


def _inside_patch_radius(
    x_m: float,
    y_m: float,
    geometry: DifferentialPatchGeometryDiagnostics,
) -> bool:
    radius = min(
        geometry.radius_x_m if geometry.radius_x_m is not None else 0.0,
        geometry.radius_y_m if geometry.radius_y_m is not None else 0.0,
    )
    return radius > 0.0 and _patch_distance(x_m, y_m, geometry) <= radius


def _patch_region(
    x_m: float,
    y_m: float,
    geometry: DifferentialPatchGeometryDiagnostics,
) -> Literal["core", "taper", "background"]:
    radius = min(
        geometry.radius_x_m if geometry.radius_x_m is not None else 0.0,
        geometry.radius_y_m if geometry.radius_y_m is not None else 0.0,
    )
    taper_width = geometry.taper_width_m or 0.0
    distance = _patch_distance(x_m, y_m, geometry)
    if radius > 0.0 and distance <= radius:
        return "core"
    if taper_width > 0.0 and distance <= radius + taper_width:
        return "taper"
    return "background"


def _localized_field_quality(
    source_field: str,
    field_quality: Mapping[str, FieldQuality],
) -> FieldQuality | None:
    key = "surface_rain" if source_field == "rain" else source_field
    return field_quality.get(key)


def _localized_quality_state(quality: FieldQuality | None) -> FieldQualityState:
    return quality.quality_state if quality is not None else "caveated"


def _localized_quality_reason(quality: FieldQuality | None) -> str | None:
    return quality.reason if quality is not None else "field_quality_not_assessed"


def _localized_quality_caveats(
    source_field: str,
    quality: FieldQuality | None,
) -> list[str]:
    if quality is None:
        return [f"field_quality_not_assessed:{source_field}"]
    if quality.quality_state == "trusted":
        return []
    return [
        *quality.caveats,
        f"field_quality_{quality.quality_state}:{quality.field}",
    ]


def _combined_quality_state(qualities: list[FieldQuality]) -> FieldQualityState:
    states = [quality.quality_state for quality in qualities]
    if not states:
        return "caveated"
    if "untrusted" in states:
        return "untrusted"
    if "caveated" in states:
        return "caveated"
    if "unavailable" in states:
        return "unavailable"
    return "trusted"


def _combined_quality_reason(qualities: list[FieldQuality]) -> str | None:
    return next((quality.reason for quality in qualities if quality.reason), None)


def _combined_quality_caveats(qualities: list[FieldQuality]) -> list[str]:
    if not qualities:
        return ["field_quality_not_assessed:localized_convergence_winds"]
    return _dedupe(
        [
            caveat
            for quality in qualities
            if quality.quality_state != "trusted"
            for caveat in [
                *quality.caveats,
                f"field_quality_{quality.quality_state}:{quality.field}",
            ]
        ]
    )


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _record_units_caveat(
    data_array: Any, field_name: str, expected_units: str, caveats: list[str]
) -> None:
    units = _attr_string(data_array, "units")
    if units is None:
        caveats.append(f"{field_name}_units_missing_assumed_{expected_units}")
    elif units != expected_units:
        caveats.append(f"{field_name}_units_not_expected:{units}")


def _attr_string(data_array: Any, name: str) -> str | None:
    value = data_array.attrs.get(name)
    if value is None:
        return None
    return str(value)


def _finite_values(data_array: Any) -> list[float]:
    values: list[float] = []
    for value in data_array.values.reshape(-1).tolist():
        parsed = _to_float_or_none(value)
        if parsed is not None and isfinite(parsed):
            values.append(parsed)
    return values


def _finite_count(data_array: Any) -> int:
    return len(_finite_values(data_array))


def _finite_max(data_array: Any) -> float | None:
    values = _finite_values(data_array)
    return max(values) if values else None


def _finite_min(data_array: Any) -> float | None:
    values = _finite_values(data_array)
    return min(values) if values else None


def _finite_mean(data_array: Any) -> float | None:
    values = _finite_values(data_array)
    return sum(values) / len(values) if values else None


def _threshold_count(data_array: Any, threshold: float) -> int:
    return sum(1 for value in _finite_values(data_array) if value >= threshold)


def _non_finite_count(data_array: Any) -> int:
    count = 0
    for value in data_array.values.reshape(-1).tolist():
        parsed = _to_float_or_none(value)
        if parsed is None or not isfinite(parsed):
            count += 1
    return count


def _total_count(data_array: Any) -> int:
    return int(data_array.values.size)


def _finite_fraction(finite_count: int, total_count: int) -> float | None:
    if total_count <= 0:
        return None
    return finite_count / total_count


def _has_finite_values(data_array: Any) -> bool:
    return _finite_count(data_array) > 0


def _to_float_or_none(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _string_or_none(value: object) -> str | None:
    return str(value) if value is not None else None


def _first_present(candidates: tuple[str, ...], names: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in names:
            return candidate
    return None


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _present(names: list[str], available_fields: set[str]) -> list[str]:
    return [name for name in names if name in available_fields]


def _is_capped_scenario(
    scenario_id: str,
    controls: dict[str, str | float | bool],
) -> bool:
    return scenario_id == "capped-suppressed-cumulus" or controls.get("cap_strength") == "stronger"


def _cloud_top_increases(series: list[TimeValue]) -> bool:
    values = [point.value for point in series if point.value is not None]
    return len(values) >= 2 and values[-1] > values[0]
