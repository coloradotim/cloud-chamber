"""Observed-sounding diagnostic features for candidate screening.

These diagnostics are pre-run evidence derived from an observed sounding. They
are not forecasts and they are not CM1 outcomes.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.observed_sounding import ObservedSoundingLevel, ObservedSoundingRecord

DIAGNOSTIC_VERSION = "sounding-diagnostics-v1"

SupportState = Literal["supported", "weak", "unavailable"]


class SoundingDiagnosticFeature(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    value: float | int | str | bool | None
    units: str | None = None
    support_state: SupportState
    method: str
    assumptions: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class SoundingDataQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score_0_to_100: float
    usable_level_count: int
    usable_levels_below_1km: int
    usable_levels_below_3km: int
    usable_levels_below_6km: int
    caveats: list[str] = Field(default_factory=list)


class SoundingDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnostic_version: str = DIAGNOSTIC_VERSION
    station_id: str
    station_name: str | None = None
    valid_time_utc: datetime
    feature_values: dict[str, SoundingDiagnosticFeature]
    unavailable_features: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    data_quality: SoundingDataQuality
    provenance: dict[str, str]


def compute_sounding_diagnostics(record: ObservedSoundingRecord) -> SoundingDiagnostics:
    """Compute bounded, caveated diagnostics from an observed sounding record."""

    levels = sorted(record.levels, key=lambda level: float(level.model_z_m))
    assumptions = [
        "Diagnostics are computed from the observed sounding profile before a CM1 run.",
        "Candidate diagnostics are pre-run evidence, not forecasts or CM1 outcomes.",
    ]
    caveats = list(record.validation.caveats)
    data_quality = _data_quality(levels)
    features: dict[str, SoundingDiagnosticFeature] = {}

    def add(feature: SoundingDiagnosticFeature) -> None:
        features[feature.key] = feature

    add(
        _feature(
            "data_completeness_score",
            "Data completeness",
            data_quality.score_0_to_100,
            "0-100",
            "derived from usable levels, profile depth, model-bottom coverage, "
            "and wind availability",
        )
    )
    add(
        _feature(
            "lowest_level_m_agl",
            "Lowest usable level",
            _lowest(levels),
            "m AGL",
            "minimum finite model_z_m in the normalized sounding",
        )
    )
    add(
        _feature(
            "profile_top_m_agl",
            "Profile top",
            _top(levels),
            "m AGL",
            "maximum finite model_z_m in the normalized sounding",
        )
    )
    add(
        _feature(
            "usable_levels_below_1km",
            "Usable levels below 1 km",
            data_quality.usable_levels_below_1km,
            "count",
            "count of finite levels from 0-1000 m AGL",
        )
    )
    add(
        _feature(
            "usable_levels_below_3km",
            "Usable levels below 3 km",
            data_quality.usable_levels_below_3km,
            "count",
            "count of finite levels from 0-3000 m AGL",
        )
    )
    add(
        _feature(
            "usable_levels_below_6km",
            "Usable levels below 6 km",
            data_quality.usable_levels_below_6km,
            "count",
            "count of finite levels from 0-6000 m AGL",
        )
    )
    add(
        _feature(
            "has_temperature",
            "Temperature available",
            _has_temperature(levels),
            None,
            "checks finite temperature values",
        )
    )
    add(
        _feature(
            "has_moisture",
            "Moisture available",
            _has_moisture(levels),
            None,
            "checks finite qv values",
        )
    )
    add(
        _feature(
            "has_pressure",
            "Pressure available",
            _has_pressure(levels),
            None,
            "checks finite pressure values",
        )
    )
    add(
        _feature(
            "has_height",
            "Height available",
            _has_height(levels),
            None,
            "checks finite model_z_m values",
        )
    )
    add(
        _feature(
            "has_observed_wind_profile",
            "Observed wind profile available",
            _has_wind(levels),
            None,
            "checks finite observed u/v components at all usable levels",
        )
    )

    surface = _lowest_level(levels)
    surface_dewpoint = (
        _dewpoint_c_from_qv(surface.pressure_pa, surface.qv_g_kg)
        if surface is not None and _finite(surface.pressure_pa, surface.qv_g_kg)
        else None
    )
    surface_ttd = (
        surface.temperature_c - surface_dewpoint
        if surface is not None
        and surface_dewpoint is not None
        and math.isfinite(surface.temperature_c)
        else None
    )
    add(
        _feature(
            "surface_or_lowest_temperature_c",
            "Surface or lowest temperature",
            _level_value(surface, "temperature_c"),
            "C",
            "lowest finite normalized level",
        )
    )
    add(
        _feature(
            "surface_or_lowest_dewpoint_c",
            "Surface or lowest dewpoint",
            _round(surface_dewpoint, 2),
            "C",
            "derived from lowest-level qv and pressure",
        )
    )
    add(
        _feature(
            "surface_t_td_spread_c",
            "Surface T-Td spread",
            _round(surface_ttd, 2),
            "C",
            "temperature minus derived dewpoint at the lowest usable level",
        )
    )
    add(
        _feature(
            "estimated_lcl_height_m_agl",
            "Estimated LCL",
            _round(125.0 * surface_ttd, 1) if surface_ttd is not None else None,
            "m AGL",
            "simple LCL proxy: 125 m per C of T-Td spread",
            assumptions=["Uses a rough LCL proxy; not a full parcel calculation."],
        )
    )
    low_level_qv = _mean_qv(levels, 0.0, 100.0)
    if low_level_qv is None:
        low_level_qv = _level_value(surface, "qv_g_kg")
    add(
        _feature(
            "low_level_qv_g_kg",
            "Low-level qv",
            low_level_qv,
            "g/kg",
            "mean qv from 0-100 m, falling back to the lowest usable level",
        )
    )
    add(
        _feature(
            "mean_qv_0_500m_g_kg",
            "Mean qv 0-500 m",
            _mean_qv(levels, 0.0, 500.0),
            "g/kg",
            "mean finite qv over levels from 0-500 m AGL",
        )
    )
    add(
        _feature(
            "mean_qv_0_1000m_g_kg",
            "Mean qv 0-1000 m",
            _mean_qv(levels, 0.0, 1000.0),
            "g/kg",
            "mean finite qv over levels from 0-1000 m AGL",
        )
    )
    add(
        _feature(
            "mean_qv_0_3000m_g_kg",
            "Mean qv 0-3000 m",
            _mean_qv(levels, 0.0, 3000.0),
            "g/kg",
            "mean finite qv over levels from 0-3000 m AGL",
        )
    )
    add(
        _feature(
            "moisture_depth_m",
            "Moisture depth",
            _moisture_depth(levels, min_qv_g_kg=6.0),
            "m",
            "highest model level with qv >= 6 g/kg",
        )
    )
    low_qv = _numeric(features["low_level_qv_g_kg"].value)
    qv_3km = _numeric(features["mean_qv_0_3000m_g_kg"].value)
    add(
        _feature(
            "qv_drop_0_3000m_g_kg",
            "Qv drop 0-3000 m",
            _round(low_qv - qv_3km, 3) if low_qv is not None and qv_3km is not None else None,
            "g/kg",
            "low-level qv minus mean qv from 0-3000 m",
        )
    )
    add(
        _feature(
            "precipitable_water_proxy_or_unavailable",
            "Precipitable water proxy",
            _precipitable_water_mm(levels),
            "mm",
            "hydrostatic pressure integration proxy from qv and pressure",
            assumptions=[
                "Treats qv as mixing ratio and converts to specific humidity "
                "for a simple column-water proxy."
            ],
            support_state="weak",
        )
    )

    add(
        _feature(
            "lapse_rate_0_1000m_c_per_km",
            "Lapse rate 0-1000 m",
            _lapse_rate(levels, 0.0, 1000.0),
            "C/km",
            "linear interpolation in height between 0 and 1000 m AGL",
        )
    )
    add(
        _feature(
            "lapse_rate_0_3000m_c_per_km",
            "Lapse rate 0-3000 m",
            _lapse_rate(levels, 0.0, 3000.0),
            "C/km",
            "linear interpolation in height between 0 and 3000 m AGL",
        )
    )
    add(
        _feature(
            "midlevel_lapse_rate_700_500_hpa_c_per_km",
            "Midlevel lapse rate 700-500 hPa",
            _pressure_lapse_rate(levels, 70000.0, 50000.0),
            "C/km",
            "temperature and height interpolated in log-pressure between 700 and 500 hPa",
        )
    )
    inversion_strength, inversion_base, inversion_top = _inversion_proxy(levels)
    add(
        _feature(
            "inversion_strength_c",
            "Inversion strength",
            inversion_strength,
            "C",
            "largest adjacent warming layer between 300 and 5000 m AGL",
        )
    )
    add(
        _feature(
            "inversion_base_m_agl",
            "Inversion base",
            inversion_base,
            "m AGL",
            "base of the largest adjacent warming layer between 300 and 5000 m AGL",
        )
    )
    add(
        _feature(
            "inversion_top_m_agl",
            "Inversion top",
            inversion_top,
            "m AGL",
            "top of the largest adjacent warming layer between 300 and 5000 m AGL",
        )
    )
    add(
        _feature(
            "cap_strength_proxy",
            "Cap strength proxy",
            inversion_strength,
            "C",
            "same proxy as inversion strength; not a full CIN calculation",
        )
    )
    add(
        _feature(
            "cap_height_m_agl",
            "Cap height proxy",
            inversion_base,
            "m AGL",
            "base of the strongest low-level inversion proxy",
        )
    )
    add(
        _unavailable(
            "eml_cap_proxy_or_unavailable",
            "EML/cap proxy",
            "EML diagnostics require validated elevated mixed-layer criteria.",
        )
    )

    for key, label, units in (
        ("surface_based_cape_j_kg", "Surface-based CAPE", "J/kg"),
        ("surface_based_cin_j_kg", "Surface-based CIN", "J/kg"),
        ("mixed_layer_cape_j_kg", "Mixed-layer CAPE", "J/kg"),
        ("mixed_layer_cin_j_kg", "Mixed-layer CIN", "J/kg"),
        ("lfc_height_m_agl", "LFC height", "m AGL"),
        ("el_height_m_agl", "EL height", "m AGL"),
    ):
        add(
            _unavailable(
                key,
                label,
                "Parcel diagnostics require a tested parcel model and "
                "virtual-temperature assumptions.",
                units=units,
            )
        )
    add(
        _feature(
            "parcel_assumptions",
            "Parcel assumptions",
            "not_implemented",
            None,
            "records parcel-diagnostic status",
            support_state="unavailable",
            caveats=["parcel_diagnostics_not_implemented"],
        )
    )

    add(
        _feature(
            "wind_available",
            "Wind available",
            _has_wind(levels),
            None,
            "finite observed u/v components at all usable levels",
        )
    )
    add(
        _feature(
            "wind_profile_depth_m",
            "Wind profile depth",
            _wind_profile_depth(levels),
            "m",
            "top minus bottom of levels with finite observed u/v",
        )
    )
    add(
        _feature(
            "bulk_shear_0_1km_m_s",
            "Bulk shear 0-1 km",
            _bulk_shear(levels, 0.0, 1000.0),
            "m/s",
            "vector wind difference between interpolated 0 and 1000 m winds",
        )
    )
    add(
        _feature(
            "bulk_shear_0_3km_m_s",
            "Bulk shear 0-3 km",
            _bulk_shear(levels, 0.0, 3000.0),
            "m/s",
            "vector wind difference between interpolated 0 and 3000 m winds",
        )
    )
    add(
        _feature(
            "bulk_shear_0_6km_m_s",
            "Bulk shear 0-6 km",
            _bulk_shear(levels, 0.0, 6000.0),
            "m/s",
            "vector wind difference between interpolated 0 and 6000 m winds",
        )
    )
    add(
        _feature(
            "mean_wind_0_6km_m_s",
            "Mean wind 0-6 km",
            _mean_wind_speed(levels, 0.0, 6000.0),
            "m/s",
            "speed of the mean u/v vector over levels from 0-6000 m",
        )
    )
    add(
        _feature(
            "storm_motion_assumption",
            "Storm-motion assumption",
            "not_implemented",
            None,
            "storm-motion assumptions are intentionally absent in v1",
            support_state="unavailable",
            caveats=["storm_motion_not_implemented"],
        )
    )
    add(
        _unavailable(
            "srh_0_1km_m2_s2",
            "SRH 0-1 km",
            "SRH requires a defensible storm-motion assumption.",
            units="m2/s2",
        )
    )
    add(
        _unavailable(
            "srh_0_3km_m2_s2",
            "SRH 0-3 km",
            "SRH requires a defensible storm-motion assumption.",
            units="m2/s2",
        )
    )
    add(
        _feature(
            "hodograph_caveats",
            "Hodograph caveats",
            "storm_relative_quantities_unavailable",
            None,
            "records hodograph diagnostic caveats",
            support_state="unavailable",
            caveats=["storm_motion_not_implemented", "srh_not_computed"],
        )
    )

    midlevel_qv = _mean_qv(levels, 2000.0, 5000.0)
    add(
        _feature(
            "midlevel_dry_layer_proxy",
            "Midlevel dry-layer proxy",
            _round(max(0.0, low_qv - midlevel_qv), 3)
            if low_qv is not None and midlevel_qv is not None
            else None,
            "g/kg",
            "low-level qv minus mean qv from 2000-5000 m",
        )
    )
    add(
        _feature(
            "dry_microburst_inverted_v_proxy",
            "Dry microburst / inverted-V proxy",
            _dry_microburst_proxy(surface_ttd, features.get("midlevel_dry_layer_proxy")),
            "0-100",
            "rough proxy from surface T-Td spread and low-to-midlevel qv drop",
            support_state="weak",
            assumptions=[
                "Proxy only; microburst behavior requires precipitation and downdraft diagnostics."
            ],
        )
    )
    add(
        _feature(
            "freezing_level_m_agl",
            "Freezing level",
            _freezing_level(levels),
            "m AGL",
            "height where temperature first crosses 0 C by linear interpolation",
        )
    )
    add(
        _unavailable(
            "wet_bulb_zero_m_agl_or_unavailable",
            "Wet-bulb zero",
            "Wet-bulb diagnostics require a tested wet-bulb calculation.",
            units="m AGL",
        )
    )
    add(
        _unavailable(
            "warm_nose_depth_m_or_unavailable",
            "Warm-nose depth",
            "Warm-nose diagnostics require phase-aware winter validation.",
            units="m",
        )
    )
    add(
        _unavailable(
            "subfreezing_surface_layer_depth_m_or_unavailable",
            "Subfreezing surface-layer depth",
            "Winter surface-layer diagnostics require phase-aware validation.",
            units="m",
        )
    )

    unavailable = sorted(
        key for key, feature in features.items() if feature.support_state == "unavailable"
    )
    all_caveats = sorted(
        {*caveats, *data_quality.caveats, *(c for f in features.values() for c in f.caveats)}
    )
    return SoundingDiagnostics(
        station_id=record.station_id,
        station_name=record.station_name,
        valid_time_utc=record.valid_time_utc,
        feature_values=features,
        unavailable_features=unavailable,
        assumptions=assumptions,
        caveats=all_caveats,
        data_quality=data_quality,
        provenance={
            "source_provider": record.source_provider,
            "source_format": record.source_format,
            "uploaded_filename": record.uploaded_filename,
            "station_metadata_source": record.provenance.get("station_metadata_source", "unknown"),
            "diagnostic_claim": (
                "computed from observed sounding profile; CM1 output remains source of truth"
            ),
        },
    )


def _feature(
    key: str,
    label: str,
    value: float | int | str | bool | None,
    units: str | None,
    method: str,
    *,
    assumptions: list[str] | None = None,
    caveats: list[str] | None = None,
    support_state: SupportState | None = None,
) -> SoundingDiagnosticFeature:
    state: SupportState = "supported" if value is not None else "unavailable"
    if value is not None and support_state is not None:
        state = support_state
    if isinstance(value, float) and not math.isfinite(value):
        value = None
        state = "unavailable"
    feature_caveats = list(caveats or [])
    if state == "unavailable" and not feature_caveats:
        feature_caveats.append(f"{key}_unavailable")
    return SoundingDiagnosticFeature(
        key=key,
        label=label,
        value=_round(value, 3) if isinstance(value, float) else value,
        units=units,
        support_state=state,
        method=method,
        assumptions=assumptions or [],
        caveats=feature_caveats,
    )


def _unavailable(
    key: str, label: str, caveat: str, *, units: str | None = None
) -> SoundingDiagnosticFeature:
    return _feature(
        key,
        label,
        None,
        units,
        "not implemented in sounding-diagnostics-v1",
        support_state="unavailable",
        caveats=[caveat],
    )


def _data_quality(levels: list[ObservedSoundingLevel]) -> SoundingDataQuality:
    usable = [level for level in levels if _finite(level.model_z_m)]
    below_1 = _count_levels(usable, 1000.0)
    below_3 = _count_levels(usable, 3000.0)
    below_6 = _count_levels(usable, 6000.0)
    top = _top(usable) or 0.0
    lowest = _lowest(usable) or 9999.0
    wind_bonus = 20.0 if _has_wind(usable) else 0.0
    score = min(
        100.0,
        min(25.0, len(usable) * 2.5)
        + min(20.0, below_3 * 2.0)
        + min(25.0, top / 18000.0 * 25.0)
        + (10.0 if lowest <= 50.0 else max(0.0, 10.0 - lowest / 50.0))
        + wind_bonus,
    )
    caveats: list[str] = []
    if not _has_wind(usable):
        caveats.append("observed_wind_profile_missing_or_incomplete")
    if below_1 < 2:
        caveats.append("sparse_low_level_profile_below_1km")
    if top < 6000.0:
        caveats.append("profile_top_below_6km")
    return SoundingDataQuality(
        score_0_to_100=round(score, 1),
        usable_level_count=len(usable),
        usable_levels_below_1km=below_1,
        usable_levels_below_3km=below_3,
        usable_levels_below_6km=below_6,
        caveats=caveats,
    )


def _count_levels(levels: list[ObservedSoundingLevel], top_m: float) -> int:
    return sum(1 for level in levels if 0.0 <= level.model_z_m <= top_m)


def _lowest_level(levels: list[ObservedSoundingLevel]) -> ObservedSoundingLevel | None:
    finite = [level for level in levels if _finite(level.model_z_m)]
    return finite[0] if finite else None


def _lowest(levels: list[ObservedSoundingLevel]) -> float | None:
    level = _lowest_level(levels)
    return _round(level.model_z_m, 1) if level is not None else None


def _top(levels: list[ObservedSoundingLevel]) -> float | None:
    finite = [level.model_z_m for level in levels if _finite(level.model_z_m)]
    return _round(max(finite), 1) if finite else None


def _level_value(level: ObservedSoundingLevel | None, field: str) -> float | None:
    if level is None:
        return None
    value = getattr(level, field)
    return float(value) if isinstance(value, int | float) and math.isfinite(value) else None


def _has_temperature(levels: list[ObservedSoundingLevel]) -> bool:
    return any(_finite(level.temperature_c) for level in levels)


def _has_moisture(levels: list[ObservedSoundingLevel]) -> bool:
    return any(_finite(level.qv_g_kg) for level in levels)


def _has_pressure(levels: list[ObservedSoundingLevel]) -> bool:
    return any(_finite(level.pressure_pa) for level in levels)


def _has_height(levels: list[ObservedSoundingLevel]) -> bool:
    return any(_finite(level.model_z_m) for level in levels)


def _has_wind(levels: list[ObservedSoundingLevel]) -> bool:
    return bool(levels) and all(_finite(level.u_wind_m_s, level.v_wind_m_s) for level in levels)


def _mean_qv(levels: list[ObservedSoundingLevel], bottom_m: float, top_m: float) -> float | None:
    values = [
        level.qv_g_kg
        for level in levels
        if bottom_m <= level.model_z_m <= top_m and _finite(level.qv_g_kg)
    ]
    return _mean(values)


def _moisture_depth(levels: list[ObservedSoundingLevel], *, min_qv_g_kg: float) -> float | None:
    moist = [
        level.model_z_m
        for level in levels
        if _finite(level.model_z_m, level.qv_g_kg) and level.qv_g_kg >= min_qv_g_kg
    ]
    return _round(max(moist), 1) if moist else None


def _lapse_rate(levels: list[ObservedSoundingLevel], bottom_m: float, top_m: float) -> float | None:
    bottom = _interpolate_by_height(levels, bottom_m, "temperature_c")
    top = _interpolate_by_height(levels, top_m, "temperature_c")
    if bottom is None or top is None or math.isclose(bottom_m, top_m):
        return None
    return _round((bottom - top) / ((top_m - bottom_m) / 1000.0), 2)


def _pressure_lapse_rate(
    levels: list[ObservedSoundingLevel], bottom_pressure_pa: float, top_pressure_pa: float
) -> float | None:
    bottom_t = _interpolate_by_pressure(levels, bottom_pressure_pa, "temperature_c")
    top_t = _interpolate_by_pressure(levels, top_pressure_pa, "temperature_c")
    bottom_z = _interpolate_by_pressure(levels, bottom_pressure_pa, "model_z_m")
    top_z = _interpolate_by_pressure(levels, top_pressure_pa, "model_z_m")
    if bottom_t is None or top_t is None or bottom_z is None or top_z is None:
        return None
    if math.isclose(top_z, bottom_z):
        return None
    return _round((bottom_t - top_t) / ((top_z - bottom_z) / 1000.0), 2)


def _inversion_proxy(
    levels: list[ObservedSoundingLevel],
) -> tuple[float | None, float | None, float | None]:
    best_strength: float | None = None
    best_base: float | None = None
    best_top: float | None = None
    low_levels = [
        level
        for level in levels
        if 300.0 <= level.model_z_m <= 5000.0 and _finite(level.model_z_m, level.temperature_c)
    ]
    for lower, upper in zip(low_levels, low_levels[1:], strict=False):
        warming = upper.temperature_c - lower.temperature_c
        if warming > 0.0 and (best_strength is None or warming > best_strength):
            best_strength = warming
            best_base = lower.model_z_m
            best_top = upper.model_z_m
    return (
        _round(best_strength, 2) if best_strength is not None else 0.0,
        _round(best_base, 1) if best_base is not None else None,
        _round(best_top, 1) if best_top is not None else None,
    )


def _precipitable_water_mm(levels: list[ObservedSoundingLevel]) -> float | None:
    pressure_levels = sorted(
        [level for level in levels if _finite(level.pressure_pa, level.qv_g_kg)],
        key=lambda level: level.pressure_pa,
        reverse=True,
    )
    if len(pressure_levels) < 2:
        return None
    total = 0.0
    for lower, upper in zip(pressure_levels, pressure_levels[1:], strict=False):
        r1 = lower.qv_g_kg / 1000.0
        r2 = upper.qv_g_kg / 1000.0
        q1 = r1 / (1.0 + r1)
        q2 = r2 / (1.0 + r2)
        dp = abs(lower.pressure_pa - upper.pressure_pa)
        total += ((q1 + q2) / 2.0) * dp / 9.80665
    return _round(total, 2)


def _wind_profile_depth(levels: list[ObservedSoundingLevel]) -> float | None:
    wind_levels = [
        level.model_z_m
        for level in levels
        if _finite(level.model_z_m, level.u_wind_m_s, level.v_wind_m_s)
    ]
    if len(wind_levels) < 2:
        return None
    return _round(max(wind_levels) - min(wind_levels), 1)


def _bulk_shear(levels: list[ObservedSoundingLevel], bottom_m: float, top_m: float) -> float | None:
    bottom = _interpolate_wind(levels, bottom_m)
    top = _interpolate_wind(levels, top_m)
    if bottom is None or top is None:
        return None
    return _round(math.hypot(top[0] - bottom[0], top[1] - bottom[1]), 2)


def _mean_wind_speed(
    levels: list[ObservedSoundingLevel], bottom_m: float, top_m: float
) -> float | None:
    wind_components: list[tuple[float, float]] = []
    for level in levels:
        if not bottom_m <= level.model_z_m <= top_m:
            continue
        u_wind = level.u_wind_m_s
        v_wind = level.v_wind_m_s
        if u_wind is None or v_wind is None or not _finite(u_wind, v_wind):
            continue
        wind_components.append((float(u_wind), float(v_wind)))
    if not wind_components:
        return None
    mean_u = sum(u_wind for u_wind, _ in wind_components) / len(wind_components)
    mean_v = sum(v_wind for _, v_wind in wind_components) / len(wind_components)
    return _round(math.hypot(mean_u, mean_v), 2)


def _dry_microburst_proxy(
    surface_ttd: float | None, midlevel_dry_layer_feature: SoundingDiagnosticFeature | None
) -> float | None:
    if surface_ttd is None or midlevel_dry_layer_feature is None:
        return None
    dry_drop = _numeric(midlevel_dry_layer_feature.value)
    if dry_drop is None:
        return None
    spread_score = max(0.0, min(100.0, surface_ttd / 25.0 * 100.0))
    dry_score = max(0.0, min(100.0, dry_drop / 8.0 * 100.0))
    return _round((spread_score + dry_score) / 2.0, 1)


def _freezing_level(levels: list[ObservedSoundingLevel]) -> float | None:
    finite = [level for level in levels if _finite(level.model_z_m, level.temperature_c)]
    for lower, upper in zip(finite, finite[1:], strict=False):
        if lower.temperature_c == 0.0:
            return _round(lower.model_z_m, 1)
        if (lower.temperature_c > 0.0 >= upper.temperature_c) or (
            lower.temperature_c < 0.0 <= upper.temperature_c
        ):
            fraction = (0.0 - lower.temperature_c) / (upper.temperature_c - lower.temperature_c)
            return _round(lower.model_z_m + fraction * (upper.model_z_m - lower.model_z_m), 1)
    return None


def _interpolate_by_height(
    levels: list[ObservedSoundingLevel], height_m: float, field: str
) -> float | None:
    finite = [level for level in levels if _finite(level.model_z_m, getattr(level, field))]
    if not finite:
        return None
    if height_m < finite[0].model_z_m:
        return (
            float(getattr(finite[0], field))
            if height_m <= 0.0 and finite[0].model_z_m <= 100.0
            else None
        )
    if height_m > finite[-1].model_z_m:
        return None
    for lower, upper in zip(finite, finite[1:], strict=False):
        if math.isclose(height_m, lower.model_z_m, abs_tol=1e-6):
            return float(getattr(lower, field))
        if lower.model_z_m <= height_m <= upper.model_z_m:
            if math.isclose(lower.model_z_m, upper.model_z_m):
                return None
            fraction = (height_m - lower.model_z_m) / (upper.model_z_m - lower.model_z_m)
            return float(getattr(lower, field)) + fraction * (
                float(getattr(upper, field)) - float(getattr(lower, field))
            )
    if math.isclose(height_m, finite[-1].model_z_m, abs_tol=1e-6):
        return float(getattr(finite[-1], field))
    return None


def _interpolate_by_pressure(
    levels: list[ObservedSoundingLevel], pressure_pa: float, field: str
) -> float | None:
    finite = [
        level
        for level in sorted(levels, key=lambda item: item.pressure_pa, reverse=True)
        if _finite(level.pressure_pa, getattr(level, field)) and level.pressure_pa > 0.0
    ]
    if not finite:
        return None
    pressures = [level.pressure_pa for level in finite]
    if pressure_pa > max(pressures) or pressure_pa < min(pressures):
        return None
    target = math.log(pressure_pa)
    for lower, upper in zip(finite, finite[1:], strict=False):
        if lower.pressure_pa >= pressure_pa >= upper.pressure_pa:
            lower_log = math.log(lower.pressure_pa)
            upper_log = math.log(upper.pressure_pa)
            if math.isclose(lower_log, upper_log):
                return None
            fraction = (target - lower_log) / (upper_log - lower_log)
            return float(getattr(lower, field)) + fraction * (
                float(getattr(upper, field)) - float(getattr(lower, field))
            )
    return None


def _interpolate_wind(
    levels: list[ObservedSoundingLevel], height_m: float
) -> tuple[float, float] | None:
    u = _interpolate_by_height(levels, height_m, "u_wind_m_s")
    v = _interpolate_by_height(levels, height_m, "v_wind_m_s")
    if u is None or v is None:
        return None
    return u, v


def _dewpoint_c_from_qv(pressure_pa: float, qv_g_kg: float) -> float | None:
    mixing_ratio = qv_g_kg / 1000.0
    if mixing_ratio <= 0.0:
        return None
    epsilon = 0.622
    vapor_pressure_hpa = (mixing_ratio * pressure_pa / 100.0) / (epsilon + mixing_ratio)
    if vapor_pressure_hpa <= 0.0:
        return None
    ln_ratio = math.log(vapor_pressure_hpa / 6.112)
    return 243.5 * ln_ratio / (17.67 - ln_ratio)


def _mean(values: list[float]) -> float | None:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else None


def _numeric(value: float | int | str | bool | None) -> float | None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return None
    return float(value) if math.isfinite(float(value)) else None


def _finite(*values: object) -> bool:
    return all(isinstance(value, int | float) and math.isfinite(float(value)) for value in values)


def _round(value: float | int | None, digits: int) -> float | None:
    if value is None or not math.isfinite(float(value)):
        return None
    return round(float(value), digits)
