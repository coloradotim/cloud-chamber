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
    "elevated_convection",
    "dry_microburst_inverted_v",
    "high_cape_pulse_storm",
    "squall_line_cold_pool_candidate",
    "needs_review",
    "poor_or_incomplete_candidate",
]
TargetStoryId = Literal[
    "shallow_cumulus_candidate",
    "dry_failed_candidate",
    "capped_suppressed_candidate",
    "humid_rainy_candidate",
    "severe_thunderstorm_environment",
    "supercell_environment",
    "elevated_convection",
    "dry_microburst_inverted_v",
    "high_cape_pulse_storm",
    "squall_line_cold_pool_candidate",
    "needs_review",
    "poor_or_incomplete_candidate",
]
Confidence = Literal["low", "medium", "high"]
Support = Literal["supported", "weak", "unavailable"]
StoryFamily = Literal["current_les", "deep_convection", "winter_future", "review"]
ReadinessState = Literal[
    "package_ready_now",
    "runnable_caveated",
    "future_package_needed",
    "blocked_or_review",
]
CurrentPackageReadiness = Literal["yes", "caveated", "no"]

STORY_LABELS: dict[StoryId, str] = {
    "shallow_cumulus_candidate": "Cloud-forming shallow cumulus candidate",
    "dry_failed_candidate": "Dry failed cumulus candidate",
    "capped_suppressed_candidate": "Capped / suppressed cumulus candidate",
    "humid_rainy_candidate": "Humid / rainy candidate",
    "severe_thunderstorm_environment": "Severe thunderstorm environment",
    "supercell_environment": "Supercell environment",
    "elevated_convection": "Elevated convection environment",
    "dry_microburst_inverted_v": "Dry microburst inverted-V environment",
    "high_cape_pulse_storm": "High-CAPE pulse-storm environment",
    "squall_line_cold_pool_candidate": "Squall-line / cold-pool candidate",
    "needs_review": "Needs review",
    "poor_or_incomplete_candidate": "Poor or incomplete data",
}


class StoryReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_family: StoryFamily
    readiness_state: ReadinessState
    package_readiness_label: str
    screenable_from_sounding_now: bool = True
    runnable_with_current_observed_sounding_package: CurrentPackageReadiness
    specialized_package_recommended: bool = False
    future_package_required: bool = False
    package_readiness_caveats: list[str] = Field(default_factory=list)


STORY_READINESS: dict[StoryId, StoryReadiness] = {
    "shallow_cumulus_candidate": StoryReadiness(
        story_family="current_les",
        readiness_state="package_ready_now",
        package_readiness_label="Current observed-sounding LES package",
        runnable_with_current_observed_sounding_package="yes",
    ),
    "dry_failed_candidate": StoryReadiness(
        story_family="current_les",
        readiness_state="package_ready_now",
        package_readiness_label="Current observed-sounding LES package",
        runnable_with_current_observed_sounding_package="yes",
    ),
    "capped_suppressed_candidate": StoryReadiness(
        story_family="current_les",
        readiness_state="runnable_caveated",
        package_readiness_label="Caveated current LES package",
        runnable_with_current_observed_sounding_package="caveated",
        specialized_package_recommended=True,
        package_readiness_caveats=[
            "Current package can explore the profile, but cap/stability validation "
            "remains caveated."
        ],
    ),
    "humid_rainy_candidate": StoryReadiness(
        story_family="current_les",
        readiness_state="runnable_caveated",
        package_readiness_label="Caveated current LES package",
        runnable_with_current_observed_sounding_package="caveated",
        specialized_package_recommended=True,
        package_readiness_caveats=[
            "Current package can explore moist profiles, but rain production remains a CM1 outcome."
        ],
    ),
    "severe_thunderstorm_environment": StoryReadiness(
        story_family="deep_convection",
        readiness_state="runnable_caveated",
        package_readiness_label="Caveated profile exploration",
        runnable_with_current_observed_sounding_package="caveated",
        specialized_package_recommended=True,
        package_readiness_caveats=[
            "This is an environment screen, not a storm forecast.",
            "A specialized deep-convection package is recommended before interpreting outcomes.",
        ],
    ),
    "supercell_environment": StoryReadiness(
        story_family="deep_convection",
        readiness_state="future_package_needed",
        package_readiness_label="Future deep-convection package required",
        runnable_with_current_observed_sounding_package="no",
        specialized_package_recommended=True,
        future_package_required=True,
        package_readiness_caveats=[
            "Supercell exploration needs storm-mode controls and diagnostics not in "
            "the current package."
        ],
    ),
    "elevated_convection": StoryReadiness(
        story_family="deep_convection",
        readiness_state="future_package_needed",
        package_readiness_label="Future elevated-convection package required",
        runnable_with_current_observed_sounding_package="no",
        specialized_package_recommended=True,
        future_package_required=True,
        package_readiness_caveats=[
            "Elevated convection needs forcing and parcel diagnostics not in the current package."
        ],
    ),
    "dry_microburst_inverted_v": StoryReadiness(
        story_family="deep_convection",
        readiness_state="runnable_caveated",
        package_readiness_label="Caveated profile exploration",
        runnable_with_current_observed_sounding_package="caveated",
        specialized_package_recommended=True,
        package_readiness_caveats=[
            "Current package can inspect the profile, but it is not a validated microburst package."
        ],
    ),
    "high_cape_pulse_storm": StoryReadiness(
        story_family="deep_convection",
        readiness_state="runnable_caveated",
        package_readiness_label="Caveated profile exploration",
        runnable_with_current_observed_sounding_package="caveated",
        specialized_package_recommended=True,
        package_readiness_caveats=[
            "Current package can inspect the profile, but it cannot confirm "
            "CAPE-driven pulse storms."
        ],
    ),
    "squall_line_cold_pool_candidate": StoryReadiness(
        story_family="deep_convection",
        readiness_state="future_package_needed",
        package_readiness_label="Future cold-pool package required",
        runnable_with_current_observed_sounding_package="no",
        specialized_package_recommended=True,
        future_package_required=True,
        package_readiness_caveats=[
            "Squall-line and cold-pool exploration needs a specialized package and diagnostics."
        ],
    ),
    "needs_review": StoryReadiness(
        story_family="review",
        readiness_state="blocked_or_review",
        package_readiness_label="Review before package generation",
        runnable_with_current_observed_sounding_package="caveated",
        package_readiness_caveats=["Review the profile and caveats before package generation."],
    ),
    "poor_or_incomplete_candidate": StoryReadiness(
        story_family="review",
        readiness_state="blocked_or_review",
        package_readiness_label="Blocked until data improves",
        screenable_from_sounding_now=False,
        runnable_with_current_observed_sounding_package="no",
        package_readiness_caveats=[
            "Package generation is blocked until parser/profile issues are fixed."
        ],
    ),
}


class StoryScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story: StoryId
    label: str
    score_0_to_100: float
    support: Support
    story_family: StoryFamily = "current_les"
    readiness_state: ReadinessState = "package_ready_now"
    package_readiness_label: str = "Current observed-sounding LES package"
    screenable_from_sounding_now: bool = True
    runnable_with_current_observed_sounding_package: CurrentPackageReadiness = "yes"
    specialized_package_recommended: bool = False
    future_package_required: bool = False
    package_readiness_caveats: list[str] = Field(default_factory=list)
    required_diagnostics_used: list[str] = Field(default_factory=list)
    unavailable_diagnostics: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
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
    story_family: StoryFamily = "current_les"
    readiness_state: ReadinessState = "package_ready_now"
    package_readiness_label: str = "Current observed-sounding LES package"
    specialized_package_recommended: bool = False
    future_package_required: bool = False
    required_diagnostics_used: list[str] = Field(default_factory=list)
    unavailable_diagnostics: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
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
    story_family: StoryFamily = "current_les"
    readiness_state: ReadinessState = "package_ready_now"
    package_readiness_label: str = "Current observed-sounding LES package"
    specialized_package_recommended: bool = False
    future_package_required: bool = False
    required_diagnostics_used: list[str] = Field(default_factory=list)
    unavailable_diagnostics: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
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
        story_family=request.candidate.story_family,
        readiness_state=request.candidate.readiness_state,
        package_readiness_label=request.candidate.package_readiness_label,
        specialized_package_recommended=request.candidate.specialized_package_recommended,
        future_package_required=request.candidate.future_package_required,
        required_diagnostics_used=request.candidate.required_diagnostics_used,
        unavailable_diagnostics=request.candidate.unavailable_diagnostics,
        assumptions=request.candidate.assumptions,
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
        story_family=primary.story_family,
        readiness_state=primary.readiness_state,
        package_readiness_label=primary.package_readiness_label,
        specialized_package_recommended=primary.specialized_package_recommended,
        future_package_required=primary.future_package_required,
        required_diagnostics_used=primary.required_diagnostics_used,
        unavailable_diagnostics=primary.unavailable_diagnostics,
        assumptions=primary.assumptions,
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
    diagnostics = compute_sounding_diagnostics(record)
    features: dict[str, float | int | str | bool | None] = {
        key: feature.value for key, feature in diagnostics.feature_values.items()
    }
    features["observed_wind_available"] = bool(
        features.get("has_observed_wind_profile") or features.get("wind_available")
    )
    features["sounding_diagnostic_version"] = diagnostics.diagnostic_version
    return features


def _score_features(
    features: dict[str, float | int | str | bool | None], *, package_ready: bool
) -> tuple[list[StoryScore], list[EvidenceItem]]:
    qv = _numeric_feature(features, "mean_qv_0_1000m_g_kg")
    qv_3km = _numeric_feature(features, "mean_qv_0_3000m_g_kg")
    lcl = _numeric_feature(features, "estimated_lcl_height_m_agl")
    lapse = _numeric_feature(features, "lapse_rate_0_1000m_c_per_km")
    lapse_3km = _numeric_feature(features, "lapse_rate_0_3000m_c_per_km")
    midlevel_lapse = _numeric_feature(features, "midlevel_lapse_rate_700_500_hpa_c_per_km")
    cap = _numeric_feature(features, "cap_strength_proxy")
    cap_height = _numeric_feature(features, "cap_height_m_agl")
    inversion_strength = _numeric_feature(features, "inversion_strength_c")
    moisture_depth = _numeric_feature(features, "moisture_depth_m")
    completeness = _numeric_feature(features, "data_completeness_score")
    midlevel_dry = _numeric_feature(features, "midlevel_dry_layer_proxy")
    surface_ttd = _numeric_feature(features, "surface_t_td_spread_c")
    qv_drop = _numeric_feature(features, "qv_drop_0_3000m_g_kg")
    dry_microburst_proxy = _numeric_feature(features, "dry_microburst_inverted_v_proxy")
    shear_0_1 = _numeric_feature(features, "bulk_shear_0_1km_m_s")
    shear_0_3 = _numeric_feature(features, "bulk_shear_0_3km_m_s")
    shear_0_6 = _numeric_feature(features, "bulk_shear_0_6km_m_s")
    freezing_level = _numeric_feature(features, "freezing_level_m_agl")
    wind_available = features.get("observed_wind_available") is True
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

    moist = _score_high(qv, low=4.0, high=10.0)
    dry = _score_low(qv, low=3.0, high=8.0)
    low_lcl = _score_low(lcl, low=400.0, high=1800.0)
    high_lcl = _score_high(lcl, low=900.0, high=2500.0)
    thermal = _score_high(lapse, low=4.0, high=8.0)
    weak_cap = _score_low(cap, low=0.5, high=4.0)
    strong_cap = _score_high(cap, low=1.5, high=5.0)
    deep_moisture = _score_high(moisture_depth, low=800.0, high=2500.0)
    shallow_moisture = _score_low(moisture_depth, low=500.0, high=1800.0)
    data_quality = _score_high(completeness, low=40.0, high=90.0)
    dry_layer = _score_high(midlevel_dry, low=2.0, high=8.0)
    deep_layer_moisture = _score_high(qv_3km, low=4.0, high=10.0)
    steep_lower_troposphere = _score_high(lapse_3km, low=5.0, high=8.0)
    steep_midlevel = _score_high(midlevel_lapse, low=5.5, high=8.5)
    strong_deep_shear = _score_high(shear_0_6, low=12.0, high=30.0)
    strong_low_shear = _score_high(shear_0_1, low=5.0, high=15.0)
    strong_three_km_shear = _score_high(shear_0_3, low=10.0, high=25.0)
    moderate_cap = _score_peak(cap, low=0.5, peak=2.0, high=5.0)
    elevated_cap = _score_high(inversion_strength, low=2.0, high=7.0)
    elevated_cap_height = _score_peak(cap_height, low=700.0, peak=1500.0, high=3000.0)
    dry_surface = _score_high(surface_ttd, low=10.0, high=25.0)
    strong_qv_drop = _score_high(qv_drop, low=2.0, high=8.0)
    dry_microburst = _score_high(dry_microburst_proxy, low=35.0, high=85.0)
    pulse_storm_shear = _score_low(shear_0_6, low=8.0, high=22.0)
    warm_cloud_layer = _score_high(freezing_level, low=2500.0, high=4500.0)
    feature_coverage = (
        (len(story_feature_names) - len(missing_story_features)) / len(story_feature_names)
        if story_feature_names
        else 1.0
    )

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
            (moist, 0.16),
            (low_lcl, 0.12),
            (deep_layer_moisture, 0.12),
            (steep_lower_troposphere, 0.18),
            (steep_midlevel, 0.12),
            (strong_deep_shear, 0.18),
            (moderate_cap, 0.06),
            (data_quality, 0.06),
        ]
    )
    supercell = _weighted_score(
        [
            (moist, 0.12),
            (low_lcl, 0.10),
            (steep_midlevel, 0.14),
            (strong_deep_shear, 0.26),
            (strong_three_km_shear, 0.16),
            (strong_low_shear, 0.12),
            (moderate_cap, 0.05),
            (data_quality, 0.05),
        ]
    )
    elevated = _weighted_score(
        [
            (elevated_cap, 0.28),
            (elevated_cap_height, 0.22),
            (deep_layer_moisture, 0.18),
            (steep_midlevel, 0.17),
            (strong_three_km_shear, 0.10),
            (data_quality, 0.05),
        ]
    )
    dry_microburst_score = _weighted_score(
        [
            (dry_microburst, 0.30),
            (dry_surface, 0.18),
            (dry_layer, 0.18),
            (strong_qv_drop, 0.16),
            (thermal, 0.12),
            (data_quality, 0.06),
        ]
    )
    pulse = _weighted_score(
        [
            (moist, 0.20),
            (low_lcl, 0.16),
            (deep_layer_moisture, 0.16),
            (steep_lower_troposphere, 0.22),
            (pulse_storm_shear, 0.14),
            (weak_cap, 0.06),
            (data_quality, 0.06),
        ]
    )
    squall_line = _weighted_score(
        [
            (moist, 0.12),
            (deep_layer_moisture, 0.10),
            (steep_lower_troposphere, 0.14),
            (strong_deep_shear, 0.20),
            (strong_three_km_shear, 0.14),
            (dry_layer, 0.10),
            (warm_cloud_layer, 0.08),
            (data_quality, 0.12),
        ]
    )
    if not wind_available:
        severe *= 0.72
        supercell *= 0.55
        squall_line *= 0.65
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
            shallow * data_quality / 100.0 * feature_coverage,
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
            humid_rainy * data_quality / 100.0 * feature_coverage,
            reasons=["high low-level moisture, low LCL, deep moisture, weak-cap proxies"],
            caveats=[
                "Humid/rainy is heavily caveated because forcing remains idealized.",
                *missing_caveats,
            ],
        ),
        _story_score(
            "severe_thunderstorm_environment",
            severe,
            reasons=[
                "moisture, lapse-rate, cap, and deep-shear proxies resemble a "
                "severe-thunderstorm environment"
            ],
            caveats=_deep_convection_caveats(
                features,
                [
                    "mean_qv_0_1000m_g_kg",
                    "estimated_lcl_height_m_agl",
                    "lapse_rate_0_3000m_c_per_km",
                    "bulk_shear_0_6km_m_s",
                ],
            ),
            required_diagnostics=[
                "mean_qv_0_1000m_g_kg",
                "estimated_lcl_height_m_agl",
                "lapse_rate_0_3000m_c_per_km",
                "bulk_shear_0_6km_m_s",
            ],
            assumptions=[
                "Severe screening uses sounding proxies because CAPE, CIN, LFC, "
                "EL, and SRH are unavailable.",
                "This is an environment screen, not a storm forecast.",
            ],
        ),
        _story_score(
            "supercell_environment",
            supercell,
            reasons=[
                "strong deep-layer and low-level shear proxies with moisture/instability context"
            ],
            caveats=_deep_convection_caveats(
                features,
                [
                    "mean_qv_0_1000m_g_kg",
                    "estimated_lcl_height_m_agl",
                    "midlevel_lapse_rate_700_500_hpa_c_per_km",
                    "bulk_shear_0_1km_m_s",
                    "bulk_shear_0_3km_m_s",
                    "bulk_shear_0_6km_m_s",
                ],
                extra=["storm_relative_helicity_unavailable"],
            ),
            required_diagnostics=[
                "mean_qv_0_1000m_g_kg",
                "midlevel_lapse_rate_700_500_hpa_c_per_km",
                "bulk_shear_0_1km_m_s",
                "bulk_shear_0_3km_m_s",
                "bulk_shear_0_6km_m_s",
            ],
            assumptions=[
                "Supercell screening is caveated because SRH and storm-motion "
                "diagnostics are unavailable.",
                "Current package generation is not a validated supercell scenario.",
            ],
        ),
        _story_score(
            "elevated_convection",
            elevated,
            reasons=["inversion/cap, elevated moisture, midlevel lapse-rate, and shear proxies"],
            caveats=_deep_convection_caveats(
                features,
                [
                    "inversion_strength_c",
                    "cap_height_m_agl",
                    "mean_qv_0_3000m_g_kg",
                    "midlevel_lapse_rate_700_500_hpa_c_per_km",
                ],
                extra=["elevated_parcel_diagnostics_unavailable"],
            ),
            required_diagnostics=[
                "inversion_strength_c",
                "cap_height_m_agl",
                "mean_qv_0_3000m_g_kg",
                "midlevel_lapse_rate_700_500_hpa_c_per_km",
            ],
            assumptions=[
                "Elevated-convection screening uses crude cap/moisture proxies "
                "without parcel diagnostics.",
                "Current package generation is not a validated elevated-convection scenario.",
            ],
        ),
        _story_score(
            "dry_microburst_inverted_v",
            dry_microburst_score,
            reasons=["large low-level T-Td spread, dry-layer, qv-drop, and lapse-rate proxies"],
            caveats=_deep_convection_caveats(
                features,
                [
                    "dry_microburst_inverted_v_proxy",
                    "surface_t_td_spread_c",
                    "midlevel_dry_layer_proxy",
                    "qv_drop_0_3000m_g_kg",
                    "lapse_rate_0_1000m_c_per_km",
                ],
            ),
            required_diagnostics=[
                "dry_microburst_inverted_v_proxy",
                "surface_t_td_spread_c",
                "midlevel_dry_layer_proxy",
                "qv_drop_0_3000m_g_kg",
                "lapse_rate_0_1000m_c_per_km",
            ],
            assumptions=[
                "Dry-microburst screening is a sounding-shape hypothesis, not a "
                "microburst forecast.",
                "Current package generation is not a validated microburst scenario.",
            ],
        ),
        _story_score(
            "high_cape_pulse_storm",
            pulse,
            reasons=["moist, low-LCL, steep-lapse, weak-shear proxies resemble pulse-storm setups"],
            caveats=_deep_convection_caveats(
                features,
                [
                    "mean_qv_0_1000m_g_kg",
                    "estimated_lcl_height_m_agl",
                    "lapse_rate_0_3000m_c_per_km",
                    "bulk_shear_0_6km_m_s",
                ],
                extra=["cape_unavailable"],
            ),
            required_diagnostics=[
                "mean_qv_0_1000m_g_kg",
                "estimated_lcl_height_m_agl",
                "lapse_rate_0_3000m_c_per_km",
                "bulk_shear_0_6km_m_s",
            ],
            assumptions=[
                "High-CAPE pulse-storm screening uses moisture and lapse-rate "
                "proxies because CAPE is unavailable.",
                "Current package generation is not a validated pulse-storm scenario.",
            ],
        ),
        _story_score(
            "squall_line_cold_pool_candidate",
            squall_line,
            reasons=["moisture, shear, lapse-rate, dry-layer, and freezing-level proxies"],
            caveats=_deep_convection_caveats(
                features,
                [
                    "mean_qv_0_1000m_g_kg",
                    "lapse_rate_0_3000m_c_per_km",
                    "bulk_shear_0_3km_m_s",
                    "bulk_shear_0_6km_m_s",
                    "freezing_level_m_agl",
                ],
                extra=["cold_pool_diagnostics_unavailable"],
            ),
            required_diagnostics=[
                "mean_qv_0_1000m_g_kg",
                "lapse_rate_0_3000m_c_per_km",
                "bulk_shear_0_3km_m_s",
                "bulk_shear_0_6km_m_s",
                "freezing_level_m_agl",
            ],
            assumptions=[
                "Squall-line screening cannot validate cold-pool behavior before a CM1 run.",
                "Current package generation is not a validated squall-line or cold-pool scenario.",
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
            supports_story=["shallow_cumulus_candidate", "humid_rainy_candidate"],
            caveats=_feature_caveats(features, "mean_qv_0_1000m_g_kg"),
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
                "high_cape_pulse_storm",
                "squall_line_cold_pool_candidate",
                "needs_review",
            ],
            caveats=_feature_caveats(features, "lapse_rate_0_3000m_c_per_km"),
        ),
        EvidenceItem(
            label="Midlevel lapse rate",
            value=features.get("midlevel_lapse_rate_700_500_hpa_c_per_km"),
            units="C/km",
            interpretation="Midlevel lapse-rate context helps screen deep-convection environments.",
            supports_story=[
                "severe_thunderstorm_environment",
                "supercell_environment",
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
            label="Bulk shear 0-6 km",
            value=features.get("bulk_shear_0_6km_m_s"),
            units="m/s",
            interpretation="Deep-layer shear is pre-run evidence for organized-convection screens.",
            supports_story=[
                "severe_thunderstorm_environment",
                "supercell_environment",
                "squall_line_cold_pool_candidate",
            ],
            caveats=_feature_caveats(features, "bulk_shear_0_6km_m_s"),
        ),
        EvidenceItem(
            label="Bulk shear 0-3 km",
            value=features.get("bulk_shear_0_3km_m_s"),
            units="m/s",
            interpretation="Lower-tropospheric shear adds context for organized-storm screens.",
            supports_story=["supercell_environment", "squall_line_cold_pool_candidate"],
            caveats=_feature_caveats(features, "bulk_shear_0_3km_m_s"),
        ),
        EvidenceItem(
            label="Dry microburst proxy",
            value=features.get("dry_microburst_inverted_v_proxy"),
            units="0-100",
            interpretation=(
                "High values indicate an inverted-V-like dry subcloud profile hypothesis."
            ),
            supports_story=["dry_microburst_inverted_v"],
            caveats=_feature_caveats(features, "dry_microburst_inverted_v_proxy"),
        ),
        EvidenceItem(
            label="Freezing level",
            value=features.get("freezing_level_m_agl"),
            units="m AGL",
            interpretation="Freezing-level context helps precipitation and cold-pool screens.",
            supports_story=["severe_thunderstorm_environment", "squall_line_cold_pool_candidate"],
            caveats=_feature_caveats(features, "freezing_level_m_agl"),
        ),
        EvidenceItem(
            label="Observed wind availability",
            value=features.get("observed_wind_available"),
            interpretation=(
                "Observed winds are required for the current external-sounding package path."
            ),
            supports_story=["poor_or_incomplete_candidate", "needs_review"],
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
        _story_score("elevated_convection", 0.0),
        _story_score("dry_microburst_inverted_v", 0.0),
        _story_score("high_cape_pulse_storm", 0.0),
        _story_score("squall_line_cold_pool_candidate", 0.0),
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
    required_diagnostics: list[str] | None = None,
    assumptions: list[str] | None = None,
) -> StoryScore:
    rounded = round(max(0.0, min(100.0, score)), 1)
    support: Support
    if rounded >= 65.0:
        support = "supported"
    elif rounded >= 35.0:
        support = "weak"
    else:
        support = "unavailable"
    readiness = STORY_READINESS[story]
    normalized_caveats = caveats or []
    unavailable_diagnostics = [
        caveat.removeprefix("missing_or_unavailable_feature:")
        for caveat in normalized_caveats
        if caveat.startswith("missing_or_unavailable_feature:")
    ]
    return StoryScore(
        story=story,
        label=STORY_LABELS[story],
        score_0_to_100=rounded,
        support=support,
        story_family=readiness.story_family,
        readiness_state=readiness.readiness_state,
        package_readiness_label=readiness.package_readiness_label,
        screenable_from_sounding_now=readiness.screenable_from_sounding_now,
        runnable_with_current_observed_sounding_package=(
            readiness.runnable_with_current_observed_sounding_package
        ),
        specialized_package_recommended=readiness.specialized_package_recommended,
        future_package_required=readiness.future_package_required,
        package_readiness_caveats=readiness.package_readiness_caveats,
        required_diagnostics_used=[
            name
            for name in (required_diagnostics or [])
            if not _diagnostic_missing_from_caveats(normalized_caveats, name)
        ],
        unavailable_diagnostics=unavailable_diagnostics,
        assumptions=assumptions or [],
        reasons=reasons or [],
        caveats=[*normalized_caveats, *readiness.package_readiness_caveats],
    )


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


def _deep_convection_caveats(
    features: dict[str, float | int | str | bool | None],
    required_features: list[str],
    *,
    extra: list[str] | None = None,
) -> list[str]:
    missing = [
        f"missing_or_unavailable_feature:{name}"
        for name in required_features
        if _numeric_feature(features, name) is None
    ]
    caveats = [
        "screening_guidance_only_not_storm_forecast",
        "cm1_output_remains_source_of_truth",
        *missing,
        *(extra or []),
    ]
    return caveats


def _diagnostic_missing_from_caveats(caveats: list[str], name: str) -> bool:
    return f"missing_or_unavailable_feature:{name}" in caveats


def _score_high(value: float | None, *, low: float, high: float) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(100.0, (value - low) / (high - low) * 100.0))


def _score_low(value: float | None, *, low: float, high: float) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(100.0, (high - value) / (high - low) * 100.0))


def _score_peak(value: float | None, *, low: float, peak: float, high: float) -> float:
    if value is None:
        return 0.0
    if value <= low or value >= high:
        return 0.0
    if math.isclose(value, peak):
        return 100.0
    if value < peak:
        return max(0.0, min(100.0, (value - low) / (peak - low) * 100.0))
    return max(0.0, min(100.0, (high - value) / (high - peak) * 100.0))


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
