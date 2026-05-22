"""First-pass diagnostics for ingested CM1 NetCDF results."""

from __future__ import annotations

from math import isfinite
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

QC_CLOUD_THRESHOLD_KG_KG = 1e-6
QR_RAIN_THRESHOLD_KG_KG = 1e-7
MINIMUM_CLOUD_GRID_CELLS = 10

TIME_DIMENSION_CANDIDATES = ("time", "mtime", "t")
VERTICAL_COORDINATE_CANDIDATES = ("z", "zh", "height", "height_m")


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
    max_qc_kg_kg: float | None = None
    time_of_max_qc_seconds: float | None = None
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
    user_message: str = "No rain detected."
    available: bool = True
    field_absent: bool = False


class ResultDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cloud: CloudDiagnostics
    vertical_velocity: VerticalVelocityDiagnostics
    rain: RainDiagnostics
    time: TimeDiagnostics
    caveats: list[str] = Field(default_factory=list)


def compute_baseline_diagnostics(dataset: Any, inherited_caveats: list[str]) -> ResultDiagnostics:
    """Compute MVP Baseline Shallow Cumulus diagnostics from an xarray dataset."""
    caveats = list(inherited_caveats)
    time_context = _time_context(dataset, _primary_time_dimension(dataset))
    cloud = _cloud_diagnostics(dataset, time_context, caveats)
    vertical_velocity = _vertical_velocity_diagnostics(dataset, time_context, caveats)
    rain = _rain_diagnostics(dataset, time_context, caveats)
    return ResultDiagnostics(
        cloud=cloud,
        vertical_velocity=vertical_velocity,
        rain=rain,
        time=time_context.diagnostics,
        caveats=_dedupe(caveats),
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

    series_arrays = _time_slices(qc, time.dimension)
    qc_max_series: list[TimeValue] = []
    cloud_fraction_series: list[TimeValue] = []
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
        qc_max_series.append(TimeValue(time_seconds=time_seconds, value=slice_max))
        cloud_fraction_series.append(TimeValue(time_seconds=time_seconds, value=cloud_fraction))
        if cloudy_count >= MINIMUM_CLOUD_GRID_CELLS:
            cloud_present_steps.append(time_seconds)
            if first_cloud_time is None:
                first_cloud_time = time_seconds
        if slice_max is not None and (max_qc is None or slice_max > max_qc):
            max_qc = slice_max
            time_of_max_qc = time_seconds

    cloud_base, cloud_top = _cloud_base_top(qc, caveats)
    return CloudDiagnostics(
        formed=first_cloud_time is not None,
        first_cloud_time_seconds=first_cloud_time,
        cloud_base_m=cloud_base,
        cloud_top_m=cloud_top,
        max_qc_kg_kg=max_qc,
        time_of_max_qc_seconds=time_of_max_qc,
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
        user_message="Rain detected." if present else "No rain detected.",
    )


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
        vertical_values = [_to_float_or_none(value) for value in vertical_coord.values.tolist()]
        units = _attr_string(vertical_coord, "units")
        if units is None:
            caveats.append("cloud_base_top_vertical_units_missing_assumed_meters")
        elif units not in {"m", "meter", "meters"}:
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
