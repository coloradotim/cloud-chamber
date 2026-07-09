"""Heuristic screening for cached IGRA sounding candidates.

These candidates are pre-run hypotheses for choosing observed soundings to try
in CM1. They are not outcome predictions; CM1 output remains the source of
truth.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.igra_catalog import IGRACacheEntry, read_igra_cache_manifest
from cloud_chamber.observed_sounding import (
    ObservedSoundingError,
    ObservedSoundingRecord,
    StationMetadata,
    parse_igra_station_text,
    summarize_igra_station_text,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.sounding_diagnostics import compute_sounding_diagnostics

SCREENING_VERSION = "sounding-screening-v1"

StoryId = Literal[
    "shallow_cumulus_candidate",
    "dry_failed_candidate",
    "capped_suppressed_candidate",
    "humid_rainy_candidate",
    "severe_thunderstorm_environment",
    "supercell_environment",
    "high_cape_pulse_storm",
    "dry_microburst_inverted_v",
    "squall_line_cold_pool_candidate",
    "elevated_convection",
    "needs_review",
    "poor_or_incomplete_candidate",
]
TargetStoryId = Literal[
    "deep_convection_trial",
    "shallow_cumulus_candidate",
    "dry_failed_candidate",
    "capped_suppressed_candidate",
    "humid_rainy_candidate",
    "severe_thunderstorm_environment",
    "supercell_environment",
    "high_cape_pulse_storm",
    "dry_microburst_inverted_v",
    "squall_line_cold_pool_candidate",
    "elevated_convection",
    "needs_review",
    "poor_or_incomplete_candidate",
]
Confidence = Literal["low", "medium", "high"]
Support = Literal["supported", "weak", "unavailable"]

STORY_LABELS: dict[StoryId, str] = {
    "shallow_cumulus_candidate": "Cloud-forming shallow cumulus candidate",
    "dry_failed_candidate": "Dry failed cumulus candidate",
    "capped_suppressed_candidate": "Capped / suppressed cumulus candidate",
    "humid_rainy_candidate": "Humid / rainy candidate",
    "severe_thunderstorm_environment": "Severe thunderstorm environment",
    "supercell_environment": "Supercell-like environment",
    "high_cape_pulse_storm": "High-CAPE pulse-storm candidate",
    "dry_microburst_inverted_v": "Dry microburst / inverted-V candidate",
    "squall_line_cold_pool_candidate": "Squall-line / cold-pool candidate",
    "elevated_convection": "Elevated convection candidate",
    "needs_review": "Needs review",
    "poor_or_incomplete_candidate": "Poor or incomplete data",
}

DEEP_CONVECTION_STORY_IDS: tuple[StoryId, ...] = (
    "severe_thunderstorm_environment",
    "supercell_environment",
    "high_cape_pulse_storm",
    "dry_microburst_inverted_v",
    "squall_line_cold_pool_candidate",
    "elevated_convection",
)


class StoryScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story: StoryId
    label: str
    score_0_to_100: float
    support: Support
    reasons: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    value: float | int | str | bool | None
    units: str | None = None
    interpretation: str
    supports_story: list[StoryId] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class SoundingCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    station_id: str
    station_name: str | None = None
    station_latitude: float | None = None
    station_longitude: float | None = None
    station_elevation_m_msl: float | None = None
    valid_time_utc: datetime
    source_time_text: str
    source_file_name: str
    source_file_hash: str
    source_format: str = "igra_station_text"
    source_provider: str = "NOAA/NCEI IGRA"
    primary_story: StoryId
    primary_story_label: str
    story_scores: list[StoryScore]
    rank_score: float
    confidence: Confidence
    package_ready: bool
    features: dict[str, float | int | str | bool | None]
    evidence: list[EvidenceItem]
    caveats: list[str] = Field(default_factory=list)
    selected_sounding_payload: dict[str, Any] | None = None
    screening_version: str = SCREENING_VERSION
    created_at: datetime


class ScreeningInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str
    station_name: str | None = None
    cached_text_path: str
    source_file_name: str
    cached_status: str
    sounding_count: int | None = None
    latest_valid_time_utc: datetime | None = None
    caveats: list[str] = Field(default_factory=list)


class ScreeningResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    screening_version: str = SCREENING_VERSION
    generated_at: datetime
    candidates: list[SoundingCandidate]
    caveats: list[str] = Field(default_factory=list)


class SavedSoundingCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    saved_candidate_id: str
    candidate: SoundingCandidate
    selected_sounding_payload: dict[str, Any] | None
    screening_version: str = SCREENING_VERSION
    primary_story: StoryId
    story_scores: list[StoryScore]
    features: dict[str, float | int | str | bool | None]
    evidence: list[EvidenceItem]
    caveats: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime
    last_used_at: datetime | None = None
    linked_run_ids: list[str] = Field(default_factory=list)
    linked_result_ids: list[str] = Field(default_factory=list)


class SaveCandidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate: SoundingCandidate
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


def list_screening_inputs(settings: CloudChamberSettings) -> list[ScreeningInput]:
    """List cached station text files available for screening."""

    inputs: list[ScreeningInput] = []
    for entry in _cached_text_entries(settings):
        if entry.cached_text_path is None:
            continue
        text_path = Path(entry.cached_text_path)
        sounding_count: int | None = None
        latest_valid_time_utc: datetime | None = None
        caveats: list[str] = []
        try:
            summaries = summarize_igra_station_text(text_path.read_text())
            sounding_count = len(summaries)
            if summaries:
                latest_valid_time_utc = max(summary.valid_time_utc for summary in summaries)
        except (OSError, ObservedSoundingError) as exc:
            caveats.append(str(exc))
        inputs.append(
            ScreeningInput(
                station_id=entry.station_id,
                station_name=entry.station_name,
                cached_text_path=entry.cached_text_path,
                source_file_name=text_path.name,
                cached_status=entry.cached_status,
                sounding_count=sounding_count,
                latest_valid_time_utc=latest_valid_time_utc,
                caveats=caveats,
            )
        )
    return inputs


def screen_cached_soundings(
    settings: CloudChamberSettings,
    *,
    station_id: str | None = None,
    latest_per_station: int = 5,
    limit: int = 50,
    target_story: TargetStoryId | None = None,
) -> ScreeningResult:
    """Screen cached IGRA soundings and return story-matched hypotheses."""

    if latest_per_station < 1:
        raise ValueError("latest_per_station must be at least 1")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    candidates: list[SoundingCandidate] = []
    caveats: list[str] = []
    for entry in _cached_text_entries(settings):
        if station_id is not None and entry.station_id != station_id:
            continue
        if entry.cached_text_path is None:
            continue
        path = Path(entry.cached_text_path)
        try:
            text = path.read_text()
            summaries = summarize_igra_station_text(text)
        except (OSError, ObservedSoundingError) as exc:
            caveats.append(f"{entry.station_id}:{path.name}:{exc}")
            continue
        summaries = sorted(summaries, key=lambda summary: summary.valid_time_utc, reverse=True)
        for summary in summaries[:latest_per_station]:
            candidates.append(
                _candidate_from_cached_sounding(
                    entry=entry,
                    source_text=text,
                    source_path=path,
                    selected_time=summary.valid_time_utc,
                )
            )
    ranked = sorted(
        candidates,
        key=lambda candidate: (
            candidate.package_ready,
            _candidate_story_score(candidate, target_story)
            if target_story is not None
            else candidate.primary_story != "poor_or_incomplete_candidate",
            _candidate_story_score(candidate, target_story)
            if target_story is not None
            else candidate.rank_score,
            candidate.valid_time_utc,
        ),
        reverse=True,
    )
    return ScreeningResult(
        generated_at=datetime.now(UTC),
        candidates=ranked[:limit],
        caveats=caveats,
    )


def _candidate_story_score(candidate: SoundingCandidate, story: TargetStoryId | None) -> float:
    if story is None:
        return candidate.rank_score
    if story == "deep_convection_trial":
        return (
            max(
                (
                    score.score_0_to_100
                    for score in candidate.story_scores
                    if score.story in DEEP_CONVECTION_STORY_IDS
                ),
                default=0.0,
            )
            if candidate.package_ready
            else 0.0
        )
    for score in candidate.story_scores:
        if score.story == story:
            return score.score_0_to_100 if candidate.package_ready else 0.0
    return 0.0


def save_candidate(
    settings: CloudChamberSettings,
    request: SaveCandidateRequest,
) -> SavedSoundingCandidate:
    saved = SavedSoundingCandidate(
        saved_candidate_id=request.candidate.candidate_id,
        candidate=request.candidate,
        selected_sounding_payload=request.candidate.selected_sounding_payload,
        primary_story=request.candidate.primary_story,
        story_scores=request.candidate.story_scores,
        features=request.candidate.features,
        evidence=request.candidate.evidence,
        caveats=request.candidate.caveats,
        tags=request.tags,
        notes=request.notes,
        created_at=datetime.now(UTC),
    )
    existing = [
        candidate
        for candidate in list_saved_candidates(settings)
        if candidate.saved_candidate_id != saved.saved_candidate_id
    ]
    _write_saved_candidates(settings, [*existing, saved])
    return saved


def list_saved_candidates(settings: CloudChamberSettings) -> list[SavedSoundingCandidate]:
    path = _saved_candidates_path(settings)
    if not path.exists():
        return []
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, list):
        raise ValueError(f"Saved candidates file must contain a JSON list: {path}")
    return [SavedSoundingCandidate.model_validate(item) for item in loaded]


def delete_saved_candidate(settings: CloudChamberSettings, saved_candidate_id: str) -> bool:
    existing = list_saved_candidates(settings)
    kept = [
        candidate for candidate in existing if candidate.saved_candidate_id != saved_candidate_id
    ]
    if len(kept) == len(existing):
        return False
    _write_saved_candidates(settings, kept)
    return True


def _candidate_from_cached_sounding(
    *,
    entry: IGRACacheEntry,
    source_text: str,
    source_path: Path,
    selected_time: datetime,
) -> SoundingCandidate:
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    created_at = datetime.now(UTC)
    station_metadata = _station_metadata_from_cache_entry(entry)
    station_latitude: float | None
    station_longitude: float | None
    station_elevation: float | None
    try:
        parsed = parse_igra_station_text(
            source_text,
            uploaded_filename=source_path.name,
            selected_time_utc=selected_time,
            station_metadata=station_metadata,
        )
        record = parsed.selected_sounding
        features = _features_from_record(record)
        story_scores, evidence = _score_features(features, package_ready=True)
        caveats = list(record.validation.caveats)
        if features.get("near_surface_discontinuity_flag") is True:
            caveats.append("near_surface_discontinuity_caveat")
        selected_payload = record.model_dump(mode="json")
        source_time_text = record.source_time_text
        station_latitude = record.station_latitude
        station_longitude = record.station_longitude
        station_elevation = record.station_elevation_m_msl
        package_ready = True
    except ObservedSoundingError as exc:
        features = {
            "data_completeness_score": 0.0,
            "package_error": str(exc),
        }
        story_scores, evidence = _poor_candidate_scores(str(exc))
        caveats = [str(exc)]
        selected_payload = None
        source_time_text = selected_time.isoformat().replace("+00:00", "Z")
        station_latitude = entry.latitude
        station_longitude = entry.longitude
        station_elevation = entry.elevation_m_msl
        package_ready = False
    primary = max(story_scores, key=lambda score: score.score_0_to_100)
    rank_score = _rank_score(primary, package_ready)
    return SoundingCandidate(
        candidate_id=_candidate_id(entry.station_id, selected_time, source_path.name, source_hash),
        station_id=entry.station_id,
        station_name=entry.station_name,
        station_latitude=station_latitude,
        station_longitude=station_longitude,
        station_elevation_m_msl=station_elevation,
        valid_time_utc=selected_time,
        source_time_text=source_time_text,
        source_file_name=source_path.name,
        source_file_hash=source_hash,
        primary_story=primary.story,
        primary_story_label=primary.label,
        story_scores=story_scores,
        rank_score=rank_score,
        confidence=_confidence(rank_score, package_ready, features),
        package_ready=package_ready,
        features=features,
        evidence=evidence,
        caveats=caveats,
        selected_sounding_payload=selected_payload,
        created_at=created_at,
    )


def _features_from_record(
    record: ObservedSoundingRecord,
) -> dict[str, float | int | str | bool | None]:
    levels = record.levels
    surface = levels[0]
    lowest = surface.model_z_m
    top = levels[-1].model_z_m
    surface_dewpoint = _dewpoint_c_from_qv(surface.pressure_pa, surface.qv_g_kg)
    ttd = surface.temperature_c - surface_dewpoint if surface_dewpoint is not None else None
    lcl = 125.0 * ttd if ttd is not None else None
    qv_0_500 = _mean_qv(levels, 0.0, 500.0)
    qv_0_1000 = _mean_qv(levels, 0.0, 1000.0)
    qv_0_3000 = _mean_qv(levels, 0.0, 3000.0)
    qv_near_surface = _mean_qv(levels, 0.0, 100.0) or surface.qv_g_kg
    lapse_0_1000 = _lapse_rate(levels, 0.0, 1000.0)
    lapse_0_3000 = _lapse_rate(levels, 0.0, 3000.0)
    inversion_strength, inversion_base, inversion_top = _inversion_proxy(levels)
    moisture_depth = _moisture_depth(levels, min_qv_g_kg=6.0)
    near_surface_jump = _near_surface_jump(levels)
    usable_below_3km = sum(1 for level in levels if 0.0 <= level.model_z_m <= 3000.0)
    observed_wind_available = all(
        level.u_wind_m_s is not None and level.v_wind_m_s is not None for level in levels
    )
    completeness = min(
        100.0,
        25.0
        + min(25.0, usable_below_3km * 2.5)
        + (25.0 if top >= 18000.0 else max(0.0, top / 18000.0 * 25.0))
        + (25.0 if lowest <= 50.0 else max(0.0, 25.0 - lowest / 20.0)),
    )
    if near_surface_jump["flag"]:
        completeness = min(completeness, 70.0)
    qv_drop = (
        round(qv_near_surface - qv_0_3000, 3)
        if qv_0_3000 is not None and qv_near_surface is not None
        else None
    )
    midlevel_qv = _mean_qv(levels, 2000.0, 5000.0)
    midlevel_dry_layer = (
        round(max(0.0, qv_near_surface - midlevel_qv), 3)
        if midlevel_qv is not None and qv_near_surface is not None
        else None
    )
    features: dict[str, float | int | str | bool | None] = {
        "data_completeness_score": round(completeness, 1),
        "surface_or_lowest_pressure_hpa": round(surface.pressure_pa / 100.0, 1),
        "surface_or_lowest_temperature_c": round(surface.temperature_c, 2),
        "surface_or_lowest_dewpoint_c": (
            round(surface_dewpoint, 2) if surface_dewpoint is not None else None
        ),
        "surface_t_td_spread_c": round(ttd, 2) if ttd is not None else None,
        "estimated_lcl_height_m_agl": round(lcl, 1) if lcl is not None else None,
        "low_level_qv_g_kg": round(qv_near_surface, 3),
        "mean_qv_0_500m_g_kg": round(qv_0_500, 3) if qv_0_500 is not None else None,
        "mean_qv_0_1000m_g_kg": round(qv_0_1000, 3) if qv_0_1000 is not None else None,
        "moisture_depth_m": round(moisture_depth, 1) if moisture_depth is not None else None,
        "qv_drop_0_3000m_g_kg": qv_drop,
        "lapse_rate_0_1000m_c_per_km": (
            round(lapse_0_1000, 2) if lapse_0_1000 is not None else None
        ),
        "lapse_rate_0_3000m_c_per_km": (
            round(lapse_0_3000, 2) if lapse_0_3000 is not None else None
        ),
        "inversion_strength_c": round(inversion_strength, 2),
        "inversion_base_m_agl": round(inversion_base, 1) if inversion_base is not None else None,
        "inversion_top_m_agl": round(inversion_top, 1) if inversion_top is not None else None,
        "cap_strength_proxy": round(inversion_strength, 2),
        "cap_height_m_agl": round(inversion_base, 1) if inversion_base is not None else None,
        "midlevel_dry_layer_proxy": midlevel_dry_layer,
        "profile_top_m_agl": round(top, 1),
        "lowest_level_m_agl": round(lowest, 1),
        "usable_levels_below_3km": usable_below_3km,
        "observed_wind_available": observed_wind_available,
        "near_surface_jump_depth_m": near_surface_jump["depth_m"],
        "near_surface_temperature_jump_c": near_surface_jump["temperature_jump_c"],
        "near_surface_qv_jump_g_kg": near_surface_jump["qv_jump_g_kg"],
        "near_surface_discontinuity_flag": near_surface_jump["flag"],
    }
    diagnostics = compute_sounding_diagnostics(record)
    for key in (
        "mean_qv_0_3000m_g_kg",
        "precipitable_water_proxy_or_unavailable",
        "midlevel_lapse_rate_700_500_hpa_c_per_km",
        "has_observed_wind_profile",
        "wind_profile_depth_m",
        "bulk_shear_0_1km_m_s",
        "bulk_shear_0_3km_m_s",
        "bulk_shear_0_6km_m_s",
        "mean_wind_0_6km_m_s",
        "dry_microburst_inverted_v_proxy",
        "freezing_level_m_agl",
        "surface_based_cape_j_kg",
        "mixed_layer_cape_j_kg",
        "surface_based_cin_j_kg",
        "mixed_layer_cin_j_kg",
        "lfc_height_m_agl",
        "el_height_m_agl",
        "srh_0_1km_m2_s2",
        "srh_0_3km_m2_s2",
    ):
        diagnostic = diagnostics.feature_values.get(key)
        features[key] = diagnostic.value if diagnostic is not None else None
    features["observed_wind_available"] = bool(
        features.get("observed_wind_available") or features.get("has_observed_wind_profile")
    )
    return features


def _score_features(
    features: dict[str, float | int | str | bool | None], *, package_ready: bool
) -> tuple[list[StoryScore], list[EvidenceItem]]:
    qv = _numeric_feature(features, "mean_qv_0_1000m_g_kg")
    qv_500 = _numeric_feature(features, "mean_qv_0_500m_g_kg")
    lcl = _numeric_feature(features, "estimated_lcl_height_m_agl")
    lapse = _numeric_feature(features, "lapse_rate_0_1000m_c_per_km")
    lapse_0_3km = _numeric_feature(features, "lapse_rate_0_3000m_c_per_km")
    midlevel_lapse = _numeric_feature(features, "midlevel_lapse_rate_700_500_hpa_c_per_km")
    cap = _numeric_feature(features, "cap_strength_proxy")
    moisture_depth = _numeric_feature(features, "moisture_depth_m")
    completeness = _numeric_feature(features, "data_completeness_score")
    midlevel_dry = _numeric_feature(features, "midlevel_dry_layer_proxy")
    qv_drop = _numeric_feature(features, "qv_drop_0_3000m_g_kg")
    precipitable_water = _numeric_feature(features, "precipitable_water_proxy_or_unavailable")
    shear_0_1km = _numeric_feature(features, "bulk_shear_0_1km_m_s")
    shear_0_3km = _numeric_feature(features, "bulk_shear_0_3km_m_s")
    shear_0_6km = _numeric_feature(features, "bulk_shear_0_6km_m_s")
    freezing_level = _numeric_feature(features, "freezing_level_m_agl")
    dry_microburst_proxy = _numeric_feature(features, "dry_microburst_inverted_v_proxy")
    sbcape = _numeric_feature(features, "surface_based_cape_j_kg")
    mlcape = _numeric_feature(features, "mixed_layer_cape_j_kg")
    sbcin = _numeric_feature(features, "surface_based_cin_j_kg")
    mlcin = _numeric_feature(features, "mixed_layer_cin_j_kg")
    lfc = _numeric_feature(features, "lfc_height_m_agl")
    el = _numeric_feature(features, "el_height_m_agl")
    surface_ttd = _numeric_feature(features, "surface_t_td_spread_c")
    observed_wind_available = features.get("observed_wind_available") is True
    story_feature_names = [
        "mean_qv_0_1000m_g_kg",
        "estimated_lcl_height_m_agl",
        "lapse_rate_0_1000m_c_per_km",
        "cap_strength_proxy",
        "moisture_depth_m",
        "midlevel_dry_layer_proxy",
    ]
    missing_story_features = [
        name for name in story_feature_names if _numeric_feature(features, name) is None
    ]
    missing_caveats = [f"missing_or_unavailable_feature:{name}" for name in missing_story_features]
    deep_feature_names = [
        "mean_qv_0_1000m_g_kg",
        "estimated_lcl_height_m_agl",
        "lapse_rate_0_3000m_c_per_km",
        "midlevel_lapse_rate_700_500_hpa_c_per_km",
        "surface_based_cape_j_kg",
        "mixed_layer_cape_j_kg",
        "surface_based_cin_j_kg",
        "bulk_shear_0_6km_m_s",
        "moisture_depth_m",
    ]
    missing_deep_features = [
        name for name in deep_feature_names if _numeric_feature(features, name) is None
    ]
    deep_caveats = [f"missing_or_unavailable_feature:{name}" for name in missing_deep_features]
    if not observed_wind_available:
        deep_caveats.append("observed_wind_required_for_deep_convection_trial")

    moist = _score_high(qv, low=4.0, high=10.0)
    dry = _score_low(qv, low=3.0, high=8.0)
    storm_moisture = _weighted_score(
        [
            (_score_high(qv, low=8.0, high=14.0), 0.55),
            (_score_high(qv_500, low=8.0, high=14.0), 0.25),
            (_score_high(precipitable_water, low=18.0, high=38.0), 0.20),
        ]
    )
    low_lcl = _score_low(lcl, low=400.0, high=1800.0)
    high_lcl = _score_high(lcl, low=900.0, high=2500.0)
    thermal = _score_high(lapse, low=4.0, high=8.0)
    deep_lapse = _weighted_score(
        [
            (_score_high(lapse_0_3km, low=5.5, high=8.0), 0.55),
            (_score_high(midlevel_lapse, low=5.5, high=7.5), 0.45),
        ]
    )
    weak_cap = _score_low(cap, low=0.5, high=4.0)
    strong_cap = _score_high(cap, low=1.5, high=5.0)
    not_strong_cap = _score_low(cap, low=2.0, high=6.0)
    deep_moisture = _score_high(moisture_depth, low=800.0, high=2500.0)
    shallow_moisture = _score_low(moisture_depth, low=500.0, high=1800.0)
    data_quality = _score_high(completeness, low=40.0, high=90.0)
    dry_layer = _score_high(midlevel_dry, low=2.0, high=8.0)
    qv_drop_score = _score_high(qv_drop, low=3.0, high=8.0)
    deep_shear = _score_high(shear_0_6km, low=10.0, high=24.0)
    supercell_deep_shear = _score_high(shear_0_6km, low=16.0, high=30.0)
    low_level_shear = _score_high(shear_0_1km, low=4.0, high=14.0)
    three_km_shear = _score_high(shear_0_3km, low=8.0, high=20.0)
    pulse_shear = _score_low(shear_0_6km, low=8.0, high=22.0)
    effective_cape = max(value for value in (sbcape or 0.0, mlcape or 0.0))
    effective_cin = min(value for value in (sbcin or 0.0, mlcin or 0.0))
    cape_score = _score_high(effective_cape, low=750.0, high=2500.0)
    high_cape_score = _score_high(effective_cape, low=1500.0, high=3500.0)
    cin_score = _score_low(abs(effective_cin), low=25.0, high=250.0)
    low_lfc = _score_low(lfc, low=750.0, high=3000.0)
    deep_el = _score_high(el, low=7000.0, high=12000.0)
    initiation_support = _weighted_score(
        [
            (_score_high(effective_cape, low=250.0, high=1000.0), 0.50),
            (low_lcl, 0.25),
            (storm_moisture, 0.15),
            (deep_moisture, 0.05),
            (not_strong_cap, 0.05),
        ]
    )
    if initiation_support < 45.0:
        deep_caveats.append("weak_deep_initiation_screen_for_deep_convection_trial")
    instability = _weighted_score(
        [
            (cape_score, 0.55),
            (cin_score, 0.25),
            (low_lfc, 0.10),
            (deep_el, 0.10),
        ]
    )
    deep_environment = _weighted_score(
        [
            (instability, 0.45),
            (deep_lapse, 0.25),
            (deep_shear, 0.20),
            (deep_moisture, 0.10),
        ]
    )
    dry_microburst = _weighted_score(
        [
            (_score_high(dry_microburst_proxy, low=35.0, high=80.0), 0.35),
            (_score_high(surface_ttd, low=10.0, high=28.0), 0.20),
            (qv_drop_score, 0.20),
            (deep_lapse, 0.15),
            (_score_high(freezing_level, low=2500.0, high=4500.0), 0.10),
        ]
    )
    feature_coverage = (
        (len(story_feature_names) - len(missing_story_features)) / len(story_feature_names)
        if story_feature_names
        else 1.0
    )
    deep_feature_coverage = (
        (len(deep_feature_names) - len(missing_deep_features)) / len(deep_feature_names)
        if deep_feature_names
        else 1.0
    )
    wind_factor = 1.0 if observed_wind_available else 0.25
    lowest_level = _numeric_feature(features, "lowest_level_m_agl")
    surface_coverage_factor = 1.0
    if lowest_level is None:
        surface_coverage_factor = 0.5
        deep_caveats.append("surface_level_unavailable_for_deep_convection_trial")
    elif lowest_level > 250.0:
        surface_coverage_factor = 0.25
        deep_caveats.append("lowest_usable_level_too_high_for_deep_convection_trial")
    elif lowest_level > 100.0:
        surface_coverage_factor = 0.65
        deep_caveats.append("lowest_usable_level_caveat_for_deep_convection_trial")

    shallow = _weighted_score(
        [(moist, 0.28), (low_lcl, 0.22), (deep_moisture, 0.18), (weak_cap, 0.14), (thermal, 0.18)]
    )
    dry_failed = _weighted_score(
        [
            (dry, 0.25),
            (high_lcl, 0.22),
            (shallow_moisture, 0.18),
            (dry_layer, 0.15),
            (thermal, 0.20),
        ]
    )
    capped = _weighted_score([(moist, 0.25), (low_lcl, 0.20), (strong_cap, 0.35), (thermal, 0.20)])
    humid_rainy = _weighted_score(
        [(moist, 0.32), (low_lcl, 0.22), (deep_moisture, 0.26), (weak_cap, 0.20)]
    )
    severe = _weighted_score(
        [
            (instability, 0.32),
            (storm_moisture, 0.16),
            (low_lcl, 0.08),
            (deep_lapse, 0.16),
            (deep_shear, 0.18),
            (not_strong_cap, 0.04),
            (deep_moisture, 0.06),
        ]
    )
    supercell = _weighted_score(
        [
            (instability, 0.24),
            (storm_moisture, 0.12),
            (deep_lapse, 0.12),
            (supercell_deep_shear, 0.28),
            (three_km_shear, 0.12),
            (low_level_shear, 0.08),
            (not_strong_cap, 0.04),
        ]
    )
    high_cape_pulse = _weighted_score(
        [
            (high_cape_score, 0.35),
            (cin_score, 0.16),
            (storm_moisture, 0.18),
            (low_lcl, 0.08),
            (deep_lapse, 0.15),
            (pulse_shear, 0.05),
            (not_strong_cap, 0.03),
        ]
    )
    squall_line = _weighted_score(
        [
            (instability, 0.24),
            (storm_moisture, 0.12),
            (deep_lapse, 0.14),
            (deep_shear, 0.24),
            (three_km_shear, 0.12),
            (deep_moisture, 0.08),
            (dry_layer, 0.06),
        ]
    )
    elevated = _weighted_score(
        [
            (cape_score, 0.22),
            (strong_cap, 0.20),
            (storm_moisture, 0.16),
            (deep_lapse, 0.14),
            (deep_shear, 0.16),
            (deep_moisture, 0.12),
        ]
    )
    # Deep-convection stories already score buoyancy explicitly through the
    # instability terms above. Do not use EL/deep-buoyancy as a second hard
    # multiplier: many observed soundings provide useful CAPE/shear evidence
    # while EL remains unavailable from the simple screening diagnostics.
    deep_factor = (
        data_quality
        / 100.0
        * deep_feature_coverage
        * wind_factor
        * surface_coverage_factor
        * (0.30 + 0.70 * initiation_support / 100.0)
    )
    shallow_score = shallow * data_quality / 100.0 * feature_coverage
    humid_score = humid_rainy * data_quality / 100.0 * feature_coverage
    if observed_wind_available and effective_cape >= 1000.0 and deep_environment >= 55.0:
        # The broad shallow/humid stories are easy to satisfy in moist warm-season
        # profiles. When the same sounding has meaningful CAPE, shear, and deep
        # lapse-rate support, keep those broad labels available but let the
        # Deep Convection Trial story become the useful product recommendation.
        shallow_score = min(shallow_score, 62.0)
        humid_score = min(humid_score, 62.0)
    elif observed_wind_available and effective_cape >= 250.0 and deep_environment >= 55.0:
        # Moist profiles can still be shallow-cloud-capable, but when the same
        # sounding has supported deep-convection evidence we should not let the
        # broad shallow/humid labels hide the more useful package story.
        shallow_score = min(shallow_score, 82.0)
        humid_score = min(humid_score, 82.0)
    poor = 100.0 if not package_ready else min(34.0, max(0.0, 100.0 - data_quality))
    if not package_ready:
        poor = 100.0
    needs_review = min(
        100.0,
        max(
            15.0,
            60.0 - data_quality / 2.0,
            len(missing_story_features) * 18.0,
            70.0 - data_quality if data_quality < 70.0 else 0.0,
        ),
    )
    if not package_ready:
        needs_review = min(needs_review, 80.0)
    scores = [
        _story_score(
            "shallow_cumulus_candidate",
            shallow_score,
            reasons=["moderate moisture, plausible LCL, thermal lapse-rate and cap proxies"],
            caveats=missing_caveats,
        ),
        _story_score(
            "dry_failed_candidate",
            dry_failed * data_quality / 100.0 * feature_coverage,
            reasons=["dryness/high LCL proxies with possible thermal lapse-rate support"],
            caveats=missing_caveats,
        ),
        _story_score(
            "capped_suppressed_candidate",
            capped * data_quality / 100.0 * feature_coverage,
            reasons=["moisture/LCL support with an inversion or cap proxy"],
            caveats=missing_caveats,
        ),
        _story_score(
            "humid_rainy_candidate",
            humid_score,
            reasons=["high low-level moisture, low LCL, deep moisture, weak-cap proxies"],
            caveats=[
                "Humid/rainy is heavily caveated because forcing remains idealized.",
                *missing_caveats,
            ],
        ),
        _story_score(
            "severe_thunderstorm_environment",
            _deep_story_score(
                severe * deep_factor, observed_wind_available=observed_wind_available
            ),
            reasons=[
                "deep-convection proxy from simple CAPE/CIN, moisture, "
                "LCL, lapse-rate, and shear evidence"
            ],
            caveats=[
                "deep-convection candidate scores are pre-run hypotheses; "
                "simple CAPE/CIN estimates are screening evidence only",
                *deep_caveats,
            ],
        ),
        _story_score(
            "supercell_environment",
            _deep_story_score(
                supercell * deep_factor, observed_wind_available=observed_wind_available
            ),
            reasons=[
                "supercell-like proxy from simple CAPE/CIN, moisture, and 0-6 km/low-level shear"
            ],
            caveats=[
                "storm rotation and organization are CM1 outcomes to inspect after the run",
                "SRH is unavailable because storm-motion assumptions are not implemented yet",
                *deep_caveats,
            ],
        ),
        _story_score(
            "high_cape_pulse_storm",
            _deep_story_score(
                high_cape_pulse * deep_factor, observed_wind_available=observed_wind_available
            ),
            reasons=[
                "pulse-storm proxy from high simple CAPE, rich moisture, "
                "steep lapse rates, low LCL, and weaker deep shear"
            ],
            caveats=[
                "CAPE is a simple screening estimate; CM1 output remains the outcome",
                *deep_caveats,
            ],
        ),
        _story_score(
            "dry_microburst_inverted_v",
            _deep_story_score(
                dry_microburst * deep_factor, observed_wind_available=observed_wind_available
            ),
            reasons=[
                "dry-microburst proxy from surface spread, qv drop, "
                "midlevel dryness, and lapse-rate evidence"
            ],
            caveats=[
                "microburst behavior requires precipitation and evaporative "
                "cooling to develop in CM1",
                *deep_caveats,
            ],
        ),
        _story_score(
            "squall_line_cold_pool_candidate",
            _deep_story_score(
                squall_line * deep_factor, observed_wind_available=observed_wind_available
            ),
            reasons=[
                "squall-line proxy from simple CAPE/CIN, moisture, "
                "lapse-rate, deep shear, and dry-layer context"
            ],
            caveats=[
                "line/cold-pool-specific package support may come later; "
                "v1 runs as Deep Convection Trial",
                *deep_caveats,
            ],
        ),
        _story_score(
            "elevated_convection",
            _deep_story_score(
                elevated * deep_factor, observed_wind_available=observed_wind_available
            ),
            reasons=[
                "elevated-convection proxy from simple CAPE, cap, moisture, "
                "lapse-rate, and shear evidence"
            ],
            caveats=[
                "elevated inflow/source-layer behavior may need a specialized package later",
                *deep_caveats,
            ],
        ),
        _story_score(
            "needs_review",
            needs_review,
            reasons=["heuristic screening is uncertain; CM1 run is required"],
            caveats=missing_caveats,
        ),
        _story_score(
            "poor_or_incomplete_candidate",
            poor,
            reasons=["profile completeness or package-readiness issues"],
            caveats=(["package_generation_blocked"] if not package_ready else missing_caveats),
        ),
    ]
    evidence = [
        EvidenceItem(
            label="Low-level qv",
            value=features.get("low_level_qv_g_kg"),
            units="g/kg",
            interpretation=(
                "Near-surface moisture helps distinguish moist, dry, and humid candidates."
            ),
            supports_story=[
                "shallow_cumulus_candidate",
                "dry_failed_candidate",
                "humid_rainy_candidate",
            ],
            caveats=_feature_caveats(features, "low_level_qv_g_kg"),
        ),
        EvidenceItem(
            label="Mean qv 0-500 m",
            value=features.get("mean_qv_0_500m_g_kg"),
            units="g/kg",
            interpretation="Moisture close to cloud base supports cloud-forming hypotheses.",
            supports_story=["shallow_cumulus_candidate", "humid_rainy_candidate"],
            caveats=_feature_caveats(features, "mean_qv_0_500m_g_kg"),
        ),
        EvidenceItem(
            label="Mean qv 0-1 km",
            value=features.get("mean_qv_0_1000m_g_kg"),
            units="g/kg",
            interpretation="Higher low-level moisture supports cloud-forming and humid candidates.",
            supports_story=[
                "shallow_cumulus_candidate",
                "humid_rainy_candidate",
                "severe_thunderstorm_environment",
                "supercell_environment",
                "high_cape_pulse_storm",
                "squall_line_cold_pool_candidate",
            ],
            caveats=_feature_caveats(features, "mean_qv_0_1000m_g_kg"),
        ),
        EvidenceItem(
            label="Near-surface continuity",
            value="large jump" if features.get("near_surface_discontinuity_flag") else "ok",
            interpretation=(
                "Large temperature or moisture jumps in the first shallow layer can make "
                "pre-run scores overconfident."
            ),
            supports_story=["needs_review", "poor_or_incomplete_candidate"],
            caveats=["near_surface_discontinuity_caveat"]
            if features.get("near_surface_discontinuity_flag") is True
            else [],
        ),
        EvidenceItem(
            label="Surface T-Td spread",
            value=features.get("surface_t_td_spread_c"),
            units="C",
            interpretation=(
                "Larger temperature-dewpoint spread raises LCL and supports dry-failed hypotheses."
            ),
            supports_story=["dry_failed_candidate"],
            caveats=_feature_caveats(features, "surface_t_td_spread_c"),
        ),
        EvidenceItem(
            label="Estimated LCL",
            value=features.get("estimated_lcl_height_m_agl"),
            units="m AGL",
            interpretation="Lower LCL makes shallow cloud formation more plausible.",
            supports_story=[
                "shallow_cumulus_candidate",
                "dry_failed_candidate",
                "humid_rainy_candidate",
            ],
            caveats=_feature_caveats(features, "estimated_lcl_height_m_agl"),
        ),
        EvidenceItem(
            label="Low-level lapse rate",
            value=features.get("lapse_rate_0_1000m_c_per_km"),
            units="C/km",
            interpretation="Steeper low-level lapse rate suggests thermals may develop.",
            supports_story=[
                "shallow_cumulus_candidate",
                "dry_failed_candidate",
                "capped_suppressed_candidate",
            ],
            caveats=_feature_caveats(features, "lapse_rate_0_1000m_c_per_km"),
        ),
        EvidenceItem(
            label="Lapse rate 0-3 km",
            value=features.get("lapse_rate_0_3000m_c_per_km"),
            units="C/km",
            interpretation=(
                "Lower-atmosphere stability gives context for thermal growth and cap effects."
            ),
            supports_story=[
                "capped_suppressed_candidate",
                "severe_thunderstorm_environment",
                "supercell_environment",
                "high_cape_pulse_storm",
                "squall_line_cold_pool_candidate",
                "elevated_convection",
                "needs_review",
            ],
            caveats=_feature_caveats(features, "lapse_rate_0_3000m_c_per_km"),
        ),
        EvidenceItem(
            label="Midlevel lapse rate 700-500 hPa",
            value=features.get("midlevel_lapse_rate_700_500_hpa_c_per_km"),
            units="C/km",
            interpretation="Steeper midlevel lapse rates support deep-convection trial hypotheses.",
            supports_story=[
                "severe_thunderstorm_environment",
                "supercell_environment",
                "high_cape_pulse_storm",
                "squall_line_cold_pool_candidate",
                "elevated_convection",
            ],
            caveats=_feature_caveats(features, "midlevel_lapse_rate_700_500_hpa_c_per_km"),
        ),
        EvidenceItem(
            label="Cap strength proxy",
            value=features.get("cap_strength_proxy"),
            units="C",
            interpretation="A stronger inversion proxy supports capped/suppressed hypotheses.",
            supports_story=["capped_suppressed_candidate"],
            caveats=_feature_caveats(features, "cap_strength_proxy"),
        ),
        EvidenceItem(
            label="Cap height proxy",
            value=features.get("cap_height_m_agl"),
            units="m AGL",
            interpretation=(
                "Cap height helps judge whether inhibition sits in a useful lower-atmosphere range."
            ),
            supports_story=["capped_suppressed_candidate"],
            caveats=_feature_caveats(features, "cap_height_m_agl"),
        ),
        EvidenceItem(
            label="Moisture depth",
            value=features.get("moisture_depth_m"),
            units="m",
            interpretation=(
                "Deeper moisture supports humid/cloud-forming hypotheses; shallow moisture "
                "supports dry-failed hypotheses."
            ),
            supports_story=[
                "shallow_cumulus_candidate",
                "dry_failed_candidate",
                "humid_rainy_candidate",
            ],
            caveats=_feature_caveats(features, "moisture_depth_m"),
        ),
        EvidenceItem(
            label="Midlevel dry-layer proxy",
            value=features.get("midlevel_dry_layer_proxy"),
            units="g/kg",
            interpretation=(
                "A stronger near-surface to midlevel moisture drop supports dry-failed hypotheses."
            ),
            supports_story=[
                "dry_failed_candidate",
                "dry_microburst_inverted_v",
                "squall_line_cold_pool_candidate",
            ],
            caveats=_feature_caveats(features, "midlevel_dry_layer_proxy"),
        ),
        EvidenceItem(
            label="Surface-based CAPE",
            value=features.get("surface_based_cape_j_kg"),
            units="J/kg",
            interpretation=(
                "Simple pre-run parcel estimate; higher values support deep-convection trials."
            ),
            supports_story=[
                "severe_thunderstorm_environment",
                "supercell_environment",
                "high_cape_pulse_storm",
                "squall_line_cold_pool_candidate",
            ],
            caveats=_feature_caveats(features, "surface_based_cape_j_kg"),
        ),
        EvidenceItem(
            label="Surface-based CIN",
            value=features.get("surface_based_cin_j_kg"),
            units="J/kg",
            interpretation=(
                "Simple pre-run parcel estimate; strong inhibition lowers trial confidence."
            ),
            supports_story=[
                "severe_thunderstorm_environment",
                "supercell_environment",
                "high_cape_pulse_storm",
                "elevated_convection",
            ],
            caveats=_feature_caveats(features, "surface_based_cin_j_kg"),
        ),
        EvidenceItem(
            label="Bulk shear 0-1 km",
            value=features.get("bulk_shear_0_1km_m_s"),
            units="m/s",
            interpretation=(
                "Low-level shear gives context for organized or rotating deep-convection trials."
            ),
            supports_story=["supercell_environment"],
            caveats=_feature_caveats(features, "bulk_shear_0_1km_m_s"),
        ),
        EvidenceItem(
            label="Bulk shear 0-3 km",
            value=features.get("bulk_shear_0_3km_m_s"),
            units="m/s",
            interpretation="0-3 km shear helps screen organized deep-convection candidates.",
            supports_story=[
                "supercell_environment",
                "squall_line_cold_pool_candidate",
                "elevated_convection",
            ],
            caveats=_feature_caveats(features, "bulk_shear_0_3km_m_s"),
        ),
        EvidenceItem(
            label="Bulk shear 0-6 km",
            value=features.get("bulk_shear_0_6km_m_s"),
            units="m/s",
            interpretation=(
                "Deep-layer shear is a key pre-run clue for organized storm experiments."
            ),
            supports_story=[
                "severe_thunderstorm_environment",
                "supercell_environment",
                "squall_line_cold_pool_candidate",
                "elevated_convection",
            ],
            caveats=_feature_caveats(features, "bulk_shear_0_6km_m_s"),
        ),
        EvidenceItem(
            label="Dry microburst / inverted-V proxy",
            value=features.get("dry_microburst_inverted_v_proxy"),
            units="0-100",
            interpretation=(
                "High values mark dry low levels and moisture drop that may matter if "
                "precipitation develops."
            ),
            supports_story=["dry_microburst_inverted_v"],
            caveats=_feature_caveats(features, "dry_microburst_inverted_v_proxy"),
        ),
        EvidenceItem(
            label="Freezing level",
            value=features.get("freezing_level_m_agl"),
            units="m AGL",
            interpretation=(
                "Freezing-level height gives context for precipitation and downdraft potential."
            ),
            supports_story=[
                "severe_thunderstorm_environment",
                "dry_microburst_inverted_v",
                "squall_line_cold_pool_candidate",
            ],
            caveats=_feature_caveats(features, "freezing_level_m_agl"),
        ),
        EvidenceItem(
            label="Observed wind availability",
            value=features.get("observed_wind_available"),
            interpretation=(
                "Observed winds are required for trustworthy Deep Convection Trial packages."
            ),
            supports_story=[
                "severe_thunderstorm_environment",
                "supercell_environment",
                "squall_line_cold_pool_candidate",
                "elevated_convection",
                "poor_or_incomplete_candidate",
                "needs_review",
            ],
            caveats=[]
            if features.get("observed_wind_available") is True
            else ["observed_wind_unavailable"],
        ),
        EvidenceItem(
            label="Profile top",
            value=features.get("profile_top_m_agl"),
            units="m AGL",
            interpretation=(
                "Sufficient profile depth is required before a sounding is package-ready."
            ),
            supports_story=["poor_or_incomplete_candidate", "needs_review"],
            caveats=_feature_caveats(features, "profile_top_m_agl"),
        ),
        EvidenceItem(
            label="Lowest usable level",
            value=features.get("lowest_level_m_agl"),
            units="m AGL",
            interpretation=(
                "Profiles that begin too far above the station surface are blocked or caveated."
            ),
            supports_story=["poor_or_incomplete_candidate", "needs_review"],
            caveats=_feature_caveats(features, "lowest_level_m_agl"),
        ),
        EvidenceItem(
            label="Profile completeness",
            value=features.get("data_completeness_score"),
            units="0-100",
            interpretation="Lower completeness weakens screening confidence.",
            supports_story=["poor_or_incomplete_candidate", "needs_review"],
            caveats=_feature_caveats(features, "data_completeness_score"),
        ),
        EvidenceItem(
            label="Package readiness",
            value="ready" if package_ready else "blocked",
            interpretation=(
                "Package-ready candidates can enter the current observed-sounding package path; "
                "blocked candidates need parser, metadata, or profile fixes first."
            ),
            supports_story=["poor_or_incomplete_candidate", "needs_review"],
            caveats=[] if package_ready else ["package_generation_blocked"],
        ),
    ]
    return sorted(scores, key=lambda score: score.score_0_to_100, reverse=True), evidence


def _poor_candidate_scores(reason: str) -> tuple[list[StoryScore], list[EvidenceItem]]:
    scores = [
        _story_score(
            "poor_or_incomplete_candidate",
            100.0,
            reasons=["sounding could not be normalized for package generation"],
            caveats=[reason],
        ),
        _story_score(
            "needs_review",
            50.0,
            reasons=["source sounding may still be useful after parser or metadata improvements"],
            caveats=[reason],
        ),
        _story_score("shallow_cumulus_candidate", 0.0),
        _story_score("dry_failed_candidate", 0.0),
        _story_score("capped_suppressed_candidate", 0.0),
        _story_score("humid_rainy_candidate", 0.0),
        _story_score("severe_thunderstorm_environment", 0.0),
        _story_score("supercell_environment", 0.0),
        _story_score("high_cape_pulse_storm", 0.0),
        _story_score("dry_microburst_inverted_v", 0.0),
        _story_score("squall_line_cold_pool_candidate", 0.0),
        _story_score("elevated_convection", 0.0),
    ]
    evidence = [
        EvidenceItem(
            label="Package normalization",
            value="blocked",
            interpretation=reason,
            supports_story=["poor_or_incomplete_candidate", "needs_review"],
        )
    ]
    return scores, evidence


def _story_score(
    story: StoryId,
    score: float,
    *,
    reasons: list[str] | None = None,
    caveats: list[str] | None = None,
) -> StoryScore:
    rounded = round(max(0.0, min(100.0, score)), 1)
    support: Support
    if rounded >= 65.0:
        support = "supported"
    elif rounded >= 35.0:
        support = "weak"
    else:
        support = "unavailable"
    return StoryScore(
        story=story,
        label=STORY_LABELS[story],
        score_0_to_100=rounded,
        support=support,
        reasons=reasons or [],
        caveats=caveats or [],
    )


def _deep_story_score(score: float, *, observed_wind_available: bool) -> float:
    """Let strong deep-convection evidence win over broad moist/shallow labels."""

    if observed_wind_available and score >= 65.0:
        return min(100.0, score + 5.0)
    return score


def _confidence(
    rank_score: float, package_ready: bool, features: dict[str, float | int | str | bool | None]
) -> Confidence:
    completeness = _feature(features, "data_completeness_score")
    if not package_ready or completeness < 60.0 or rank_score < 45.0:
        return "low"
    if completeness >= 85.0 and rank_score >= 70.0:
        return "high"
    return "medium"


def _rank_score(primary: StoryScore, package_ready: bool) -> float:
    if not package_ready or primary.story == "poor_or_incomplete_candidate":
        return 0.0
    return round(primary.score_0_to_100, 2)


def _station_metadata_from_cache_entry(entry: IGRACacheEntry) -> StationMetadata:
    return StationMetadata(
        station_id=entry.station_id,
        station_name=entry.station_name,
        latitude=entry.latitude,
        longitude=entry.longitude,
        elevation_m_msl=entry.elevation_m_msl,
        source="IGRA recent cache station metadata",
    )


def _candidate_id(station_id: str, valid_time: datetime, filename: str, source_hash: str) -> str:
    raw = f"{station_id}|{valid_time.isoformat()}|{filename}|{source_hash}"
    return "sounding-candidate-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _cached_text_entries(settings: CloudChamberSettings) -> list[IGRACacheEntry]:
    return [
        entry
        for entry in read_igra_cache_manifest(settings).entries
        if entry.cached_status == "cached_extracted" and entry.cached_text_path
    ]


def _saved_candidates_path(settings: CloudChamberSettings) -> Path:
    return settings.cache_dir.expanduser() / "sounding-candidates" / "saved_candidates.json"


def _write_saved_candidates(
    settings: CloudChamberSettings, candidates: list[SavedSoundingCandidate]
) -> None:
    path = _saved_candidates_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [candidate.model_dump(mode="json") for candidate in candidates]
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _feature(features: dict[str, float | int | str | bool | None], name: str) -> float:
    value = features.get(name)
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return 0.0
    return float(value)


def _numeric_feature(
    features: dict[str, float | int | str | bool | None], name: str
) -> float | None:
    value = features.get(name)
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return None
    return float(value)


def _feature_caveats(features: dict[str, float | int | str | bool | None], name: str) -> list[str]:
    return [] if _numeric_feature(features, name) is not None else [f"{name}_unavailable"]


def _near_surface_jump(levels: list[Any]) -> dict[str, float | bool | None]:
    usable = sorted(
        [level for level in levels if math.isfinite(float(level.model_z_m))],
        key=lambda level: float(level.model_z_m),
    )
    if len(usable) < 2:
        return {
            "depth_m": None,
            "temperature_jump_c": None,
            "qv_jump_g_kg": None,
            "flag": False,
        }
    lower, upper = usable[0], usable[1]
    depth = float(upper.model_z_m) - float(lower.model_z_m)
    if depth <= 0.0:
        return {
            "depth_m": round(depth, 1),
            "temperature_jump_c": None,
            "qv_jump_g_kg": None,
            "flag": True,
        }
    temperature_jump = abs(float(upper.temperature_c) - float(lower.temperature_c))
    qv_jump = abs(float(upper.qv_g_kg) - float(lower.qv_g_kg))
    flag = depth <= 150.0 and (temperature_jump >= 5.0 or qv_jump >= 5.0)
    return {
        "depth_m": round(depth, 1),
        "temperature_jump_c": round(temperature_jump, 2),
        "qv_jump_g_kg": round(qv_jump, 3),
        "flag": flag,
    }


def _score_high(value: float | None, *, low: float, high: float) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(100.0, (value - low) / (high - low) * 100.0))


def _score_low(value: float | None, *, low: float, high: float) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(100.0, (high - value) / (high - low) * 100.0))


def _weighted_score(parts: list[tuple[float, float]]) -> float:
    return sum(score * weight for score, weight in parts)


def _mean_qv(levels: list[Any], bottom_m: float, top_m: float) -> float | None:
    values = [
        float(level.qv_g_kg) for level in levels if bottom_m <= float(level.model_z_m) <= top_m
    ]
    if not values:
        return None
    return sum(values) / len(values)


def _lapse_rate(levels: list[Any], bottom_m: float, top_m: float) -> float | None:
    low = _nearest_level(levels, bottom_m)
    high = _nearest_level(levels, top_m)
    if low is None or high is None or math.isclose(high.model_z_m, low.model_z_m):
        return None
    temperature_delta = float(high.temperature_c) - float(low.temperature_c)
    height_delta = float(high.model_z_m) - float(low.model_z_m)
    return -1.0 * temperature_delta / height_delta * 1000.0


def _nearest_level(levels: list[Any], height_m: float) -> Any | None:
    if not levels:
        return None
    return min(levels, key=lambda level: abs(float(level.model_z_m) - height_m))


def _inversion_proxy(levels: list[Any]) -> tuple[float, float | None, float | None]:
    best_strength = 0.0
    best_base: float | None = None
    best_top: float | None = None
    low_levels = [level for level in levels if 300.0 <= level.model_z_m <= 5000.0]
    for lower, upper in zip(low_levels, low_levels[1:], strict=False):
        warming = upper.temperature_c - lower.temperature_c
        if warming > best_strength:
            best_strength = warming
            best_base = lower.model_z_m
            best_top = upper.model_z_m
    return best_strength, best_base, best_top


def _moisture_depth(levels: list[Any], *, min_qv_g_kg: float) -> float | None:
    moist_levels = [
        float(level.model_z_m) for level in levels if float(level.qv_g_kg) >= min_qv_g_kg
    ]
    if not moist_levels:
        return None
    return max(moist_levels)


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
