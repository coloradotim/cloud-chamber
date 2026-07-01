"""Observed sounding parsing and CM1 input_sounding normalization."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class ObservedSoundingError(ValueError):
    """Raised when an observed sounding cannot be parsed or validated."""


class StationMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str
    station_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    elevation_m_msl: float | None = None
    source: str = "IGRA station metadata fixture"


class SoundingTimeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str
    valid_time_utc: datetime
    source_time_text: str
    num_levels: int
    pressure_source: str
    non_pressure_source: str


class ObservedSoundingLevel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pressure_pa: float
    source_height_m_msl: float
    model_z_m: float
    temperature_c: float
    potential_temperature_k: float
    qv_g_kg: float
    wind_direction_degrees: float | None = None
    wind_speed_m_s: float | None = None
    u_wind_m_s: float | None = None
    v_wind_m_s: float | None = None


class ObservedSoundingValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    errors: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class ObservedSoundingRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str = "observed_sounding"
    source_provider: str = "NOAA/NCEI IGRA"
    source_format: str = "igra_station_text"
    uploaded_filename: str
    station_id: str
    station_name: str | None = None
    station_latitude: float | None = None
    station_longitude: float | None = None
    station_elevation_m_msl: float
    valid_time_utc: datetime
    source_time_text: str
    source_units: dict[str, str]
    converted_cm1_units: dict[str, str]
    source_vertical_coordinate_type: str
    model_bottom_elevation_m_msl: float
    levels: list[ObservedSoundingLevel]
    wind_handling: str
    conversion_choices: dict[str, str]
    validation: ObservedSoundingValidation
    provenance: dict[str, str]

    @model_validator(mode="after")
    def validate_ready_record(self) -> ObservedSoundingRecord:
        if self.validation.status == "blocked":
            raise ValueError("blocked observed sounding records cannot be packaged")
        return self


class ObservedSoundingUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_provider: str
    source_format: str
    uploaded_filename: str
    available_soundings: list[SoundingTimeSummary]
    selected_sounding: ObservedSoundingRecord


class _IgraHeader(TypedDict):
    line_index: int
    station_id: str
    valid_time_utc: datetime
    source_time_text: str
    num_levels: int
    pressure_source: str
    non_pressure_source: str
    latitude: float | None
    longitude: float | None


_MISSING_VALUES = {-8888, -9999}
_CM1_MODEL_TOP_M = 18000.0
_OBSERVED_SOUNDING_TOP_BUFFER_M = 2000.0

_STATION_METADATA: dict[str, StationMetadata] = {
    "USM00072558": StationMetadata(
        station_id="USM00072558",
        station_name="Valley, Nebraska",
        latitude=41.3200,
        longitude=-96.3669,
        elevation_m_msl=351.5,
        source="IGRA station-list fixture for USM00072558",
    )
}


def parse_igra_station_text(
    text: str,
    *,
    uploaded_filename: str,
    selected_time_utc: datetime | None = None,
) -> ObservedSoundingUploadResponse:
    """Parse NOAA/NCEI IGRA station sounding-data text.

    The fixed-width fields follow NOAA/NCEI's IGRA v2.2 sounding data format.
    V1 intentionally supports only uploaded/extracted IGRA station text files.
    """

    lines = text.splitlines()
    headers = _scan_headers(lines)
    if not headers:
        raise ObservedSoundingError("No IGRA sounding headers were found in the uploaded file.")

    available = [
        SoundingTimeSummary(
            station_id=header["station_id"],
            valid_time_utc=header["valid_time_utc"],
            source_time_text=header["source_time_text"],
            num_levels=header["num_levels"],
            pressure_source=header["pressure_source"],
            non_pressure_source=header["non_pressure_source"],
        )
        for header in headers
    ]
    selected = _select_header(headers, selected_time_utc)
    raw_levels = lines[
        selected["line_index"] + 1 : selected["line_index"] + 1 + selected["num_levels"]
    ]
    record = _normalize_sounding(
        header=selected,
        raw_levels=raw_levels,
        uploaded_filename=uploaded_filename,
    )
    return ObservedSoundingUploadResponse(
        source_provider="NOAA/NCEI IGRA",
        source_format="igra_station_text",
        uploaded_filename=uploaded_filename,
        available_soundings=available,
        selected_sounding=record,
    )


def observed_sounding_from_payload(payload: object) -> ObservedSoundingRecord:
    try:
        return ObservedSoundingRecord.model_validate(payload)
    except ValidationError as exc:
        raise ObservedSoundingError(str(exc)) from exc


def render_observed_input_sounding(record: ObservedSoundingRecord) -> str:
    """Render a CM1-readable input_sounding file from a validated observed record."""

    levels = record.levels
    if not levels:
        raise ObservedSoundingError("Observed sounding record has no usable levels.")
    surface = levels[0]
    body: list[ObservedSoundingLevel] = levels
    if surface.model_z_m > 0:
        surface = surface.model_copy(update={"model_z_m": 0.0})
        body = [surface, *levels]
    lines = [
        f"{surface.pressure_pa / 100.0:10.2f} "
        f"{surface.potential_temperature_k:12.4f} {surface.qv_g_kg:12.5f}",
    ]
    lines.extend(
        f"{level.model_z_m:10.1f} {level.potential_temperature_k:12.4f} "
        f"{level.qv_g_kg:12.5f} {0.0:8.2f} {0.0:7.2f}"
        for level in body
    )
    return "\n".join(lines) + "\n"


def _scan_headers(lines: list[str]) -> list[_IgraHeader]:
    headers: list[_IgraHeader] = []
    for index, line in enumerate(lines):
        if not line.startswith("#"):
            continue
        if len(line) < 71:
            raise ObservedSoundingError("Malformed IGRA header record.")
        station_id = line[1:12].strip()
        year = _parse_int(line[13:17], "YEAR")
        month = _parse_int(line[18:20], "MONTH")
        day = _parse_int(line[21:23], "DAY")
        hour = _parse_int(line[24:26], "HOUR")
        release_time = line[27:31].strip()
        num_levels = _parse_int(line[32:36], "NUMLEV")
        pressure_source = line[37:45].strip()
        non_pressure_source = line[46:54].strip()
        latitude = _parse_scaled_int(line[55:62], 10000.0)
        longitude = _parse_scaled_int(line[63:71], 10000.0)
        if hour == 99:
            raise ObservedSoundingError("Selected IGRA sounding has missing nominal hour.")
        valid_time = datetime(year, month, day, hour, tzinfo=UTC)
        headers.append(
            {
                "line_index": index,
                "station_id": station_id,
                "valid_time_utc": valid_time,
                "source_time_text": (
                    f"{year:04d}-{month:02d}-{day:02d} {hour:02d} UTC; release {release_time}"
                ),
                "num_levels": num_levels,
                "pressure_source": pressure_source,
                "non_pressure_source": non_pressure_source,
                "latitude": latitude,
                "longitude": longitude,
            }
        )
    return headers


def _select_header(headers: list[_IgraHeader], selected_time_utc: datetime | None) -> _IgraHeader:
    if selected_time_utc is None:
        return max(headers, key=lambda header: header["valid_time_utc"])
    normalized = selected_time_utc.astimezone(UTC)
    for header in headers:
        if header["valid_time_utc"] == normalized:
            return header
    raise ObservedSoundingError("Selected sounding time was not found in the uploaded file.")


def _normalize_sounding(
    *,
    header: _IgraHeader,
    raw_levels: list[str],
    uploaded_filename: str,
) -> ObservedSoundingRecord:
    station_id = str(header["station_id"])
    station = _STATION_METADATA.get(station_id)
    errors: list[str] = []
    caveats: list[str] = [
        "Observed IGRA sounding winds preserved as metadata; current CM1 "
        "package uses reference/generated wind handling.",
        "IGRA quality/source flags are preserved only as source-format provenance in v1.",
        "Place/time are preserved as metadata; radiation remains disabled in "
        "the generated package.",
    ]
    if station is None or station.elevation_m_msl is None:
        errors.append("station_site_elevation_missing")
        station = StationMetadata(station_id=station_id)
    else:
        caveats.append("station elevation joined from IGRA station metadata fixture")

    source_latitude = _coalesce_float(header.get("latitude"), station.latitude)
    source_longitude = _coalesce_float(header.get("longitude"), station.longitude)
    levels = _parse_levels(raw_levels, station.elevation_m_msl or 0.0, errors, caveats)
    _validate_levels(levels, errors, caveats)

    validation = ObservedSoundingValidation(
        status="blocked" if errors else ("needs_review" if caveats else "ready"),
        errors=errors,
        caveats=caveats,
    )
    if validation.status == "blocked":
        raise ObservedSoundingError("Observed sounding is blocked: " + ", ".join(validation.errors))
    return ObservedSoundingRecord(
        uploaded_filename=Path(uploaded_filename).name,
        station_id=station_id,
        station_name=station.station_name,
        station_latitude=source_latitude,
        station_longitude=source_longitude,
        station_elevation_m_msl=station.elevation_m_msl or 0.0,
        valid_time_utc=header["valid_time_utc"],
        source_time_text=str(header["source_time_text"]),
        source_units={
            "pressure": "Pa",
            "source_height": "m MSL",
            "temperature": "degrees C",
            "relative_humidity": "percent",
            "dewpoint_depression": "degrees C",
            "wind_speed": "m/s",
            "wind_direction": "degrees from north",
        },
        converted_cm1_units={
            "height": "m above sounding/site surface",
            "potential_temperature": "K",
            "water_vapor_mixing_ratio": "g/kg",
            "wind_components": "m/s",
        },
        source_vertical_coordinate_type="geopotential_height_msl",
        model_bottom_elevation_m_msl=station.elevation_m_msl or 0.0,
        levels=levels,
        wind_handling=("observed_winds_metadata_only; generated CM1 namelist keeps isnd=17/iwnd=9"),
        conversion_choices={
            "height": "IGRA GPH meters MSL converted to model_z_m relative to station elevation",
            "theta": "temperature and pressure converted to potential temperature",
            "moisture": "dewpoint depression preferred; relative humidity used if needed",
            "surface": "lowest usable level is copied to z=0 when above station surface",
            "wind": "observed winds retained in metadata; CM1 run uses reference wind handling",
        },
        validation=validation,
        provenance={
            "format_reference": "NOAA/NCEI IGRA v2.2 sounding data format",
            "station_metadata_source": station.source,
            "input_claim": (
                "Observed IGRA sounding used as the initial vertical profile for an "
                "idealized CM1 LES domain anchored to the sounding/site elevation."
            ),
        },
    )


def _parse_levels(
    raw_levels: list[str],
    station_elevation_m_msl: float,
    errors: list[str],
    caveats: list[str],
) -> list[ObservedSoundingLevel]:
    levels: list[ObservedSoundingLevel] = []
    used_relative_humidity = False
    for line in raw_levels:
        if len(line) < 51:
            continue
        pressure_raw = _optional_int(line[9:15])
        height_raw = _optional_int(line[16:21])
        temperature_raw = _optional_int(line[22:27])
        rh_raw = _optional_int(line[28:33])
        dewpoint_depression_raw = _optional_int(line[34:39])
        wind_direction_raw = _optional_int(line[40:45])
        wind_speed_raw = _optional_int(line[46:51])
        if pressure_raw is None or height_raw is None or temperature_raw is None:
            continue
        pressure_pa = float(pressure_raw)
        height_m_msl = float(height_raw)
        temperature_c = temperature_raw / 10.0
        qv_g_kg: float | None = None
        if dewpoint_depression_raw is not None:
            dewpoint_c = temperature_c - dewpoint_depression_raw / 10.0
            qv_g_kg = _mixing_ratio_from_dewpoint(pressure_pa / 100.0, dewpoint_c)
        elif rh_raw is not None:
            used_relative_humidity = True
            qv_g_kg = _mixing_ratio_from_relative_humidity(
                pressure_pa / 100.0,
                temperature_c,
                rh_raw / 10.0,
            )
        if qv_g_kg is None:
            continue
        model_z_m = height_m_msl - station_elevation_m_msl
        wind_speed = wind_speed_raw / 10.0 if wind_speed_raw is not None else None
        wind_direction = float(wind_direction_raw) if wind_direction_raw is not None else None
        u_wind, v_wind = _wind_components(wind_direction, wind_speed)
        levels.append(
            ObservedSoundingLevel(
                pressure_pa=pressure_pa,
                source_height_m_msl=height_m_msl,
                model_z_m=model_z_m,
                temperature_c=temperature_c,
                potential_temperature_k=_potential_temperature(temperature_c, pressure_pa),
                qv_g_kg=qv_g_kg,
                wind_direction_degrees=wind_direction,
                wind_speed_m_s=wind_speed,
                u_wind_m_s=u_wind,
                v_wind_m_s=v_wind,
            )
        )
    levels = sorted(levels, key=lambda level: level.model_z_m)
    deduped: list[ObservedSoundingLevel] = []
    for level in levels:
        if deduped and math.isclose(level.model_z_m, deduped[-1].model_z_m, abs_tol=0.01):
            continue
        deduped.append(level)
    if used_relative_humidity:
        caveats.append(
            "relative humidity used for moisture conversion where dewpoint depression was missing"
        )
    if not deduped:
        errors.append("no_usable_pressure_height_temperature_moisture_levels")
    return _truncate_for_cm1_domain(deduped, caveats)


def _truncate_for_cm1_domain(
    levels: list[ObservedSoundingLevel],
    caveats: list[str],
) -> list[ObservedSoundingLevel]:
    if not levels:
        return levels
    top_limit = _CM1_MODEL_TOP_M + _OBSERVED_SOUNDING_TOP_BUFFER_M
    kept = [level for level in levels if level.model_z_m <= top_limit]
    if kept and kept[-1].model_z_m < _CM1_MODEL_TOP_M:
        for level in levels:
            if level.model_z_m > kept[-1].model_z_m:
                kept.append(level)
                break
    if len(kept) < len(levels):
        caveats.append(
            "profile truncated above CM1 model top plus buffer; upper observed "
            "levels retained as source metadata only"
        )
    return kept


def _validate_levels(
    levels: list[ObservedSoundingLevel],
    errors: list[str],
    caveats: list[str],
) -> None:
    if len(levels) < 5:
        errors.append("too_few_usable_vertical_levels")
        return
    if levels[0].model_z_m < -50.0:
        errors.append("lowest_usable_level_below_station_surface")
    if levels[0].model_z_m > 500.0:
        errors.append("lowest_usable_level_too_far_above_model_bottom")
    elif levels[0].model_z_m > 0.0:
        caveats.append(
            f"surface value copied to z=0 from lowest usable level at {levels[0].model_z_m:.1f} m"
        )
    if levels[-1].model_z_m < _CM1_MODEL_TOP_M:
        errors.append("profile_top_too_low_for_selected_domain")
    last_z = -math.inf
    for level in levels:
        if level.model_z_m <= last_z:
            errors.append("non_monotonic_converted_model_z")
            break
        last_z = level.model_z_m
        if not all(
            math.isfinite(value)
            for value in (
                level.pressure_pa,
                level.model_z_m,
                level.temperature_c,
                level.potential_temperature_k,
                level.qv_g_kg,
            )
        ):
            errors.append("non_finite_required_profile_values")
            break
        if level.qv_g_kg < 0:
            errors.append("negative_moisture_value")
            break
        if not (-100.0 <= level.temperature_c <= 60.0):
            errors.append("implausible_temperature_value")
            break
        if not (150.0 <= level.potential_temperature_k <= 500.0):
            errors.append("implausible_potential_temperature_value")
            break
        if level.qv_g_kg > 40.0:
            errors.append("implausible_moisture_value")
            break


def _parse_int(text: str, field_name: str) -> int:
    try:
        return int(text.strip())
    except ValueError as exc:
        raise ObservedSoundingError(f"Malformed IGRA {field_name} field.") from exc


def _parse_scaled_int(text: str, scale: float) -> float | None:
    value = _optional_int(text)
    if value is None:
        return None
    return value / scale


def _optional_int(text: str) -> int | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        value = int(stripped)
    except ValueError:
        return None
    if value in _MISSING_VALUES:
        return None
    return value


def _coalesce_float(*values: object) -> float | None:
    for value in values:
        if isinstance(value, int | float):
            return float(value)
    return None


def _potential_temperature(temperature_c: float, pressure_pa: float) -> float:
    return float((temperature_c + 273.15) * (100000.0 / pressure_pa) ** 0.2854)


def _saturation_vapor_pressure_hpa(temperature_c: float) -> float:
    return 6.112 * math.exp((17.67 * temperature_c) / (temperature_c + 243.5))


def _mixing_ratio_from_dewpoint(pressure_hpa: float, dewpoint_c: float) -> float:
    vapor_pressure = _saturation_vapor_pressure_hpa(dewpoint_c)
    return 621.97 * vapor_pressure / max(pressure_hpa - vapor_pressure, 1.0)


def _mixing_ratio_from_relative_humidity(
    pressure_hpa: float,
    temperature_c: float,
    relative_humidity_percent: float,
) -> float:
    vapor_pressure = (relative_humidity_percent / 100.0) * _saturation_vapor_pressure_hpa(
        temperature_c
    )
    return 621.97 * vapor_pressure / max(pressure_hpa - vapor_pressure, 1.0)


def _wind_components(
    wind_direction_degrees: float | None,
    wind_speed_m_s: float | None,
) -> tuple[float | None, float | None]:
    if wind_direction_degrees is None or wind_speed_m_s is None:
        return None, None
    radians = math.radians(wind_direction_degrees)
    return -wind_speed_m_s * math.sin(radians), -wind_speed_m_s * math.cos(radians)
