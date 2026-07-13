"""First-pass diagnostics for ingested CM1 NetCDF results."""

from __future__ import annotations

from math import isfinite
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

QC_CLOUD_THRESHOLD_KG_KG = 1e-6
QR_RAIN_THRESHOLD_KG_KG = 1e-7
MINIMUM_CLOUD_GRID_CELLS = 10
MEANINGFUL_UPDRAFT_THRESHOLD_M_S = 0.5
HYDROMETEOR_CLOUD_TOP_FIELDS = ("qr", "qi", "qs", "qg")

TIME_DIMENSION_CANDIDATES = ("time", "mtime", "t")
VERTICAL_COORDINATE_CANDIDATES = ("z", "zh", "height", "height_m")
THERMAL_FATE_CONFIDENCE_VALUES = (
    "supported",
    "candidate",
    "insufficient_evidence",
    "unsupported_missing_fields",
)

FieldQualityState = Literal["trusted", "caveated", "untrusted", "unavailable"]


class FieldQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    source_field: str
    quality_state: FieldQualityState
    reason: str | None = None
    finite_count: int = 0
    non_finite_count: int = 0
    total_count: int = 0
    caveats: list[str] = Field(default_factory=list)


class TimeValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_seconds: float | None
    value: float | None


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


class ResultDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cloud: CloudDiagnostics
    vertical_velocity: VerticalVelocityDiagnostics
    rain: RainDiagnostics
    surface_rain: SurfaceRainDiagnostics = Field(default_factory=SurfaceRainDiagnostics)
    reflectivity: ReflectivityDiagnostics = Field(default_factory=ReflectivityDiagnostics)
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
    caveats: list[str] = []
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
        summary = "Cloud formed and cloud top increased over available output times."
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


def compute_baseline_diagnostics(dataset: Any, inherited_caveats: list[str]) -> ResultDiagnostics:
    """Compute MVP Baseline Shallow Cumulus diagnostics from an xarray dataset."""
    caveats = list(inherited_caveats)
    time_context = _time_context(dataset, _primary_time_dimension(dataset))
    cloud = _cloud_diagnostics(dataset, time_context, caveats)
    vertical_velocity = _vertical_velocity_diagnostics(dataset, time_context, caveats)
    rain = _rain_diagnostics(dataset, time_context, caveats)
    surface_rain = _surface_rain_diagnostics(dataset, time_context, caveats)
    reflectivity = _reflectivity_diagnostics(dataset, time_context, caveats)
    field_quality = _field_quality_map(dataset)
    return ResultDiagnostics(
        cloud=cloud,
        vertical_velocity=vertical_velocity,
        rain=rain,
        surface_rain=surface_rain,
        reflectivity=reflectivity,
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
}


def _field_quality_map(dataset: Any) -> dict[str, FieldQuality]:
    return {
        field: _field_quality(dataset, field, config)
        for field, config in FIELD_QUALITY_SOURCES.items()
    }


def _field_quality(dataset: Any, field: str, config: dict[str, str]) -> FieldQuality:
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
    if finite_count == 0:
        return FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="untrusted",
            reason=config["entire"],
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            caveats=[config["partial"], config["entire"]],
        )
    if non_finite_count > 0:
        return FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="caveated",
            reason=config["partial"],
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            caveats=[config["partial"]],
        )
    return FieldQuality(
        field=field,
        source_field=source_field,
        quality_state="trusted",
        finite_count=finite_count,
        non_finite_count=non_finite_count,
        total_count=total_count,
    )


class _TimeContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dimension: str | None
    values: list[float | None]
    diagnostics: TimeDiagnostics

    def at(self, index: int) -> float | None:
        if index < len(self.values):
            return self.values[index]
        return float(index)


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

    cloud_extent = _cloud_extent_array(dataset, qc, caveats)
    series_arrays = _time_slices(qc, time.dimension)
    cloud_extent_series_arrays = _time_slices(cloud_extent, time.dimension)
    qc_max_series: list[TimeValue] = []
    cloud_fraction_series: list[TimeValue] = []
    cloud_base_series: list[TimeValue] = []
    cloud_top_series: list[TimeValue] = []
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
        cloud_base, cloud_top = _cloud_base_top(extent_array, caveats)
        qc_max_series.append(TimeValue(time_seconds=time_seconds, value=slice_max))
        cloud_fraction_series.append(TimeValue(time_seconds=time_seconds, value=cloud_fraction))
        cloud_base_series.append(TimeValue(time_seconds=time_seconds, value=cloud_base))
        cloud_top_series.append(TimeValue(time_seconds=time_seconds, value=cloud_top))
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

    cloud_base, cloud_top = _cloud_base_top(cloud_extent, caveats)
    return CloudDiagnostics(
        formed=first_cloud_time is not None,
        first_cloud_time_seconds=first_cloud_time,
        cloud_base_m=cloud_base,
        cloud_top_m=cloud_top,
        cloud_base_time_series=cloud_base_series,
        cloud_top_time_series=cloud_top_series,
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


def _cloud_extent_array(dataset: Any, qc: Any, caveats: list[str]) -> Any:
    """Return the field used for cloud base/top diagnostics.

    Liquid cloud water remains the source of truth for cloud formation and max-qc
    diagnostics. For cloud top, deep-convection output can put the upper cloud in
    ice/snow/graupel fields, so the vertical envelope should include compatible
    hydrometeor mixing-ratio fields when they are present.
    """

    extent = qc
    included_fields: list[str] = []
    for field_name in HYDROMETEOR_CLOUD_TOP_FIELDS:
        if field_name not in dataset.data_vars:
            continue
        field = dataset[field_name]
        if field.dims != qc.dims:
            caveats.append(f"cloud_top_skipped_{field_name}_dimension_mismatch")
            continue
        extent = extent + field
        included_fields.append(field_name)
    if included_fields:
        caveat = "cloud_top_uses_total_hydrometeor_fields:qc," + ",".join(included_fields)
        if caveat not in caveats:
            caveats.append(caveat)
    return extent


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


def _has_finite_values(data_array: Any) -> bool:
    return _finite_count(data_array) > 0


def _to_float_or_none(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


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
