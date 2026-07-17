import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient
from igra_fixtures import IGRA_FIXTURE

import cloud_chamber.sounding_candidates as sounding_candidates
from cloud_chamber.app import app
from cloud_chamber.dry_run_package import generate_dry_run_package, read_dry_run_report
from cloud_chamber.igra_catalog import IGRACacheEntry, IGRACacheManifest, igra_cache_manifest_path
from cloud_chamber.observed_sounding import parse_igra_station_text
from cloud_chamber.run_manifest import load_run_manifest
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.sounding_candidates import (
    SaveCandidateRequest,
    ScreeningResult,
    SoundingCandidate,
    StoryId,
    StoryScore,
    Support,
    TargetStoryId,
    UpdateSavedCandidateRequest,
    _features_from_record,
    _score_features,
    _sort_analysis_candidates,
    analyze_cached_soundings,
    list_saved_candidates,
    list_screening_inputs,
    save_candidate,
    screen_cached_soundings,
    update_saved_candidate,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"
type FeatureValue = float | int | str | bool | None


def _settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def _write_cached_igra_station(
    settings: CloudChamberSettings,
    *,
    station_id: str = "USM00072558",
    station_name: str = "Valley, Nebraska",
    text: str = IGRA_FIXTURE,
) -> Path:
    station_dir = settings.cache_dir / "igra" / "recent" / "stations" / station_id
    station_dir.mkdir(parents=True, exist_ok=True)
    text_path = station_dir / f"{station_id}-data.txt"
    zip_path = station_dir / f"{station_id}-data-beg2025.txt.zip"
    text_path.write_text(text)
    zip_path.write_bytes(b"tiny fixture placeholder")
    entry = IGRACacheEntry(
        station_id=station_id,
        station_name=station_name,
        latitude=41.32,
        longitude=-96.3669,
        elevation_m_msl=351.0,
        filename=zip_path.name,
        source_url=f"https://example.test/{zip_path.name}",
        region_tags=["great_plains_midwest"],
        cached_status="cached_extracted",
        cached_zip_path=str(zip_path),
        cached_text_path=str(text_path),
        downloaded_at=datetime(2026, 7, 1, tzinfo=UTC),
        extracted_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    path = igra_cache_manifest_path(settings)
    existing_entries: list[IGRACacheEntry] = []
    if path.exists():
        existing = IGRACacheManifest.model_validate_json(path.read_text())
        existing_entries = [
            existing_entry
            for existing_entry in existing.entries
            if existing_entry.station_id != station_id
        ]
    manifest = IGRACacheManifest(
        cache_root=str(settings.cache_dir / "igra" / "recent"),
        entries=[*existing_entries, entry],
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2) + "\n")
    return text_path


def _analysis_candidate(
    candidate_id: str,
    *,
    primary_score: float = 90.0,
    primary_support: Support = "supported",
    deep_score: float = 70.0,
    deep_support: Support = "supported",
    deep_story: StoryId = "supercell_environment",
) -> SoundingCandidate:
    story_scores = [
        StoryScore(
            story="humid_rainy_candidate",
            label="Humid / rainy candidate",
            score_0_to_100=primary_score,
            support=primary_support,
        ),
        StoryScore(
            story=deep_story,
            label="Supercell-like environment",
            score_0_to_100=deep_score,
            support=deep_support,
        ),
    ]
    return SoundingCandidate(
        candidate_id=candidate_id,
        station_id=f"USM0000{len(candidate_id):04d}",
        station_name=candidate_id,
        valid_time_utc=datetime(2026, 7, 1, tzinfo=UTC),
        source_time_text="2026-07-01 00 UTC",
        source_file_name=f"{candidate_id}.txt",
        source_file_hash=f"hash-{candidate_id}",
        primary_story="humid_rainy_candidate",
        primary_story_label="Humid / rainy candidate",
        story_family="lower_atmosphere",
        story_scores=story_scores,
        rank_score=primary_score,
        confidence="high",
        package_ready=True,
        features={},
        evidence=[],
        created_at=datetime(2026, 7, 1, tzinfo=UTC),
    )


def _patch_screened_candidates(
    monkeypatch: pytest.MonkeyPatch,
    candidates: list[SoundingCandidate],
) -> None:
    def fake_screen_cached_soundings(
        settings: CloudChamberSettings,
        *,
        station_id: str | None = None,
        station_ids: list[str] | None = None,
        history_scope: str = "latest_per_station",
        latest_per_station: int | None = 5,
        limit: int | None = 50,
        target_story: TargetStoryId | None = None,
    ) -> ScreeningResult:
        _ = settings, station_id, station_ids, history_scope, latest_per_station, target_story
        return ScreeningResult(
            generated_at=datetime(2026, 7, 1, tzinfo=UTC),
            candidates=candidates if limit is None else candidates[:limit],
            caveats=[],
        )

    monkeypatch.setattr(
        sounding_candidates, "screen_cached_soundings", fake_screen_cached_soundings
    )


def test_screening_inputs_list_cached_station_text(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    text_path = _write_cached_igra_station(settings)

    inputs = list_screening_inputs(settings)

    assert len(inputs) == 1
    assert inputs[0].station_id == "USM00072558"
    assert inputs[0].cached_text_path == str(text_path)


def test_screen_cached_soundings_returns_ranked_package_ready_candidates(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(settings)

    result = screen_cached_soundings(settings, latest_per_station=2, limit=10)

    assert result.screening_version == "sounding-screening-v2"
    assert len(result.candidates) == 2
    candidate = result.candidates[0]
    assert candidate.station_id == "USM00072558"
    assert candidate.source_format == "igra_station_text"
    assert candidate.package_ready is True
    assert candidate.selected_sounding_payload is not None
    assert candidate.primary_story in {
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
    }
    assert set(candidate.features) >= {
        "mean_qv_0_1000m_g_kg",
        "estimated_lcl_height_m_agl",
        "lapse_rate_0_1000m_c_per_km",
        "cap_strength_proxy",
        "bulk_shear_0_6km_m_s",
        "midlevel_lapse_rate_700_500_hpa_c_per_km",
        "profile_top_m_agl",
    }
    assert candidate.evidence
    assert candidate.story_scores[0].score_0_to_100 >= candidate.story_scores[-1].score_0_to_100


def test_near_surface_discontinuity_is_caveated_and_downgrades_data_quality() -> None:
    record = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding
    levels = list(record.levels)
    levels[0] = levels[0].model_copy(
        update={"model_z_m": 0.0, "temperature_c": 30.5, "qv_g_kg": 28.0}
    )
    levels[1] = levels[1].model_copy(
        update={"model_z_m": 80.0, "temperature_c": 22.2, "qv_g_kg": 16.8}
    )
    discontinuous = record.model_copy(update={"levels": levels})

    features = _features_from_record(discontinuous)
    _scores, evidence = _score_features(features, package_ready=True)

    assert features["near_surface_discontinuity_flag"] is True
    assert features["near_surface_temperature_jump_c"] == pytest.approx(8.3)
    assert features["near_surface_qv_jump_g_kg"] == pytest.approx(11.2)
    data_completeness = features["data_completeness_score"]
    assert isinstance(data_completeness, int | float)
    assert data_completeness <= 70.0
    continuity = next(item for item in evidence if item.label == "Near-surface continuity")
    assert continuity.value == "large jump"
    assert "near_surface_discontinuity_caveat" in continuity.caveats


def test_observed_wind_available_requires_complete_finite_profile() -> None:
    record = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding
    levels = list(record.levels)
    missing_wind_index = next(
        index for index, level in enumerate(levels) if level.model_z_m >= 3000.0
    )
    levels[missing_wind_index] = levels[missing_wind_index].model_copy(update={"u_wind_m_s": None})
    partial_wind_record = record.model_copy(update={"levels": levels})

    features = _features_from_record(partial_wind_record)
    scores, _evidence = _score_features(features, package_ready=True)

    assert features["has_partial_observed_wind_profile"] is True
    assert features["has_observed_wind_profile"] is False
    assert features["observed_wind_available"] is False
    supercell = next(score for score in scores if score.story == "supercell_environment")
    assert supercell.support == "unavailable"
    assert "complete_observed_wind_profile_required_for_input_sounding" in supercell.caveats


def test_screen_cached_soundings_can_target_one_story(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(settings)

    result = screen_cached_soundings(
        settings,
        latest_per_station=2,
        limit=10,
        target_story="capped_suppressed_candidate",
    )

    assert result.candidates
    target_scores = [
        next(
            score.score_0_to_100
            for score in candidate.story_scores
            if score.story == "capped_suppressed_candidate"
        )
        for candidate in result.candidates
    ]
    assert target_scores == sorted(target_scores, reverse=True)


def test_analyze_cached_soundings_filters_and_sorts_multiple_cached_blocks(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(
        settings,
        station_id="USM00072558",
        station_name="Valley, Nebraska",
    )
    _write_cached_igra_station(
        settings,
        station_id="USM00072426",
        station_name="Wilmington, Ohio",
    )
    seed = analyze_cached_soundings(
        settings,
        history_scope="latest_per_station",
        latest_per_station=1,
        limit=10,
    )
    target_story = seed.candidates[0].primary_story
    target_support = next(
        score.support for score in seed.candidates[0].story_scores if score.story == target_story
    )

    result = analyze_cached_soundings(
        settings,
        history_scope="latest_per_station",
        latest_per_station=1,
        limit=10,
        story_filter=target_story,
        support=target_support,
        readiness="package_ready",
        sort_by="station_name",
    )

    assert result.total_candidate_count == 2
    assert result.filtered_candidate_count == 2
    assert result.filters.story_filter == target_story
    assert result.filters.support == target_support
    assert result.sort_by == "station_name"
    assert [candidate.station_name for candidate in result.candidates] == [
        "Valley, Nebraska",
        "Wilmington, Ohio",
    ]
    assert all(candidate.package_ready for candidate in result.candidates)
    for candidate in result.candidates:
        story_score = next(score for score in candidate.story_scores if score.story == target_story)
        assert story_score.support == target_support


def test_analyze_cached_soundings_default_recommendations_are_explained_and_diverse(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(
        settings,
        station_id="USM00072558",
        station_name="Valley, Nebraska",
    )
    _write_cached_igra_station(
        settings,
        station_id="USM00072426",
        station_name="Wilmington, Ohio",
    )

    result = analyze_cached_soundings(settings, latest_per_station=2, limit=4)

    assert len(result.candidates) == 4
    assert {candidate.station_id for candidate in result.candidates[:2]} == {
        "USM00072426",
        "USM00072558",
    }
    assert all(candidate.interest_summary for candidate in result.candidates)
    assert all(candidate.interest_reasons for candidate in result.candidates)
    assert all(candidate.discovery_bucket for candidate in result.candidates)


def test_analyze_cached_soundings_all_cached_uses_exact_selected_soundings(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(
        settings,
        station_id="USM00072558",
        station_name="Valley, Nebraska",
    )
    _write_cached_igra_station(
        settings,
        station_id="USM00072426",
        station_name="Wilmington, Ohio",
    )

    all_selected = analyze_cached_soundings(
        settings,
        history_scope="all_cached",
        latest_per_station=None,
        limit=1,
    )

    assert all_selected.total_candidate_count == 4
    assert len(all_selected.candidates) == 1
    assert all_selected.filter_trace.selected_station_count == 2
    assert all_selected.filter_trace.selected_cached_soundings == 4
    assert all_selected.filter_trace.history_scope == "all_cached"
    assert all_selected.filter_trace.latest_per_station is None
    assert all_selected.filter_trace.stage_counts["limited"] == 1

    wilmington_only = analyze_cached_soundings(
        settings,
        station_ids=["USM00072426"],
        history_scope="all_cached",
        latest_per_station=None,
        limit=10,
    )

    assert wilmington_only.total_candidate_count == 2
    assert {candidate.station_id for candidate in wilmington_only.candidates} == {"USM00072426"}
    assert wilmington_only.filters.station_ids == ["USM00072426"]
    assert wilmington_only.filter_trace.selected_station_count == 1
    assert wilmington_only.filter_trace.selected_cached_soundings == 2


def test_analyze_cached_soundings_latest_scope_is_explicit_per_selected_station(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(
        settings,
        station_id="USM00072558",
        station_name="Valley, Nebraska",
    )
    _write_cached_igra_station(
        settings,
        station_id="USM00072426",
        station_name="Wilmington, Ohio",
    )

    result = analyze_cached_soundings(
        settings,
        station_ids=["USM00072558", "USM00072426"],
        history_scope="latest_per_station",
        latest_per_station=1,
        limit=10,
    )

    assert result.total_candidate_count == 2
    assert result.filters.station_ids == ["USM00072558", "USM00072426"]
    assert result.filters.history_scope == "latest_per_station"
    assert result.filters.latest_per_station == 1
    assert result.filter_trace.selected_station_count == 2
    assert result.filter_trace.selected_cached_soundings == 2
    assert result.filter_trace.history_scope == "latest_per_station"
    assert result.filter_trace.latest_per_station == 1


def test_analysis_sorts_physical_fields_with_missing_values_last(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(settings)
    parsed_candidate = analyze_cached_soundings(
        settings,
        history_scope="latest_per_station",
        latest_per_station=1,
    ).candidates[0]
    low_lcl = parsed_candidate.model_copy(
        update={
            "candidate_id": "low-lcl",
            "station_id": "LOW00000000",
            "features": {
                **parsed_candidate.features,
                "estimated_lcl_height_m_agl": 600.0,
            },
        }
    )
    high_lcl = parsed_candidate.model_copy(
        update={
            "candidate_id": "high-lcl",
            "station_id": "HIGH0000000",
            "features": {
                **parsed_candidate.features,
                "estimated_lcl_height_m_agl": 1800.0,
            },
        }
    )
    missing_lcl = parsed_candidate.model_copy(
        update={
            "candidate_id": "missing-lcl",
            "station_id": "MISS0000000",
            "features": {
                **parsed_candidate.features,
                "estimated_lcl_height_m_agl": None,
            },
        }
    )

    sorted_candidates = _sort_analysis_candidates(
        [missing_lcl, high_lcl, low_lcl],
        sort_by="estimated_lcl_height_m_agl",
        sort_direction="asc",
        story_filter="all",
    )

    assert [candidate.candidate_id for candidate in sorted_candidates] == [
        "low-lcl",
        "high-lcl",
        "missing-lcl",
    ]


def test_analysis_family_filter_includes_supported_secondary_deep_story(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = _analysis_candidate(
        "primary-humid-supported-secondary-supercell",
        primary_score=92.0,
        deep_score=74.0,
        deep_support="supported",
    )
    _patch_screened_candidates(monkeypatch, [candidate])

    result = analyze_cached_soundings(
        _settings(tmp_path),
        story_family="deep_convection",
        support="all",
    )

    assert [item.candidate_id for item in result.candidates] == [
        "primary-humid-supported-secondary-supercell"
    ]
    assert result.filtered_candidate_count == 1
    assert result.candidates[0].primary_story == "humid_rainy_candidate"
    assert result.candidates[0].active_story == "supercell_environment"
    assert result.candidates[0].display_story == "Supercell-like environment"
    assert result.candidates[0].matched_story_ids == ["supercell_environment"]
    assert result.candidates[0].active_story_score == 74.0
    assert result.candidates[0].active_story_support == "supported"


def test_analysis_family_support_filter_uses_deep_family_scores(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    supported = _analysis_candidate(
        "secondary-deep-supported",
        primary_score=92.0,
        deep_score=74.0,
        deep_support="supported",
    )
    weak = _analysis_candidate(
        "secondary-deep-weak",
        primary_score=96.0,
        deep_score=48.0,
        deep_support="weak",
    )
    _patch_screened_candidates(monkeypatch, [weak, supported])

    result = analyze_cached_soundings(
        _settings(tmp_path),
        story_family="deep_convection",
        support="supported",
    )

    assert [item.candidate_id for item in result.candidates] == ["secondary-deep-supported"]
    assert result.filtered_candidate_count == 1
    assert result.candidates[0].active_story == "supercell_environment"
    assert result.filter_trace.stage_counts["story_family"] == 2
    assert result.filter_trace.stage_counts["support"] == 1
    assert result.filter_trace.top_excluded_reasons[0].reason == "Evidence tier: strong signal"
    assert result.filter_trace.top_excluded_reasons[0].count == 1


def test_analysis_deep_family_best_match_sort_uses_best_deep_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    humid_but_weaker_deep = _analysis_candidate(
        "humid-high-weaker-deep",
        primary_score=99.0,
        deep_score=67.0,
        deep_support="supported",
    )
    lower_primary_better_deep = _analysis_candidate(
        "humid-lower-better-deep",
        primary_score=76.0,
        deep_score=91.0,
        deep_support="supported",
    )
    _patch_screened_candidates(monkeypatch, [humid_but_weaker_deep, lower_primary_better_deep])

    result = analyze_cached_soundings(
        _settings(tmp_path),
        story_family="deep_convection",
        sort_by="best_match",
    )

    assert [item.candidate_id for item in result.candidates] == [
        "humid-lower-better-deep",
        "humid-high-weaker-deep",
    ]
    assert [item.active_story_score for item in result.candidates] == [91.0, 67.0]


def test_analysis_filter_trace_preserves_distinct_candidate_rows_after_grouping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    station_a = _analysis_candidate(
        "station-a-secondary-deep",
        primary_score=91.0,
        deep_score=75.0,
    ).model_copy(update={"station_id": "USM00070001", "station_name": "Station A"})
    station_b = _analysis_candidate(
        "station-b-secondary-deep",
        primary_score=89.0,
        deep_score=72.0,
    ).model_copy(update={"station_id": "USM00070002", "station_name": "Station B"})
    no_deep_match = _analysis_candidate(
        "station-c-no-deep-match",
        primary_score=95.0,
        deep_score=0.0,
        deep_support="unavailable",
    ).model_copy(update={"station_id": "USM00070003", "station_name": "Station C"})
    _patch_screened_candidates(monkeypatch, [station_a, station_b, no_deep_match])

    result = analyze_cached_soundings(
        _settings(tmp_path),
        story_family="deep_convection",
        limit=10,
    )

    assert [item.station_id for item in result.candidates] == ["USM00070001", "USM00070002"]
    assert result.filter_trace.analyzed_soundings == 3
    assert result.filter_trace.story_score_records == 6
    assert result.filter_trace.stage_counts["story_family"] == 2
    assert result.filter_trace.stage_counts["limited"] == 2
    assert [(item.station_id, item.count) for item in result.filter_trace.station_distribution] == [
        ("USM00070001", 1),
        ("USM00070002", 1),
    ]
    assert result.filter_trace.top_excluded_reasons[0].reason == (
        "Story family: deep-convection stories"
    )


def test_screen_cached_soundings_caveats_unreadable_files(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    text_path = _write_cached_igra_station(settings)
    text_path.unlink()

    result = screen_cached_soundings(settings)

    assert result.candidates == []
    assert result.caveats
    assert "USM00072558" in result.caveats[0]


@pytest.mark.parametrize(
    ("features", "package_ready", "expected_story"),
    [
        (
            {
                "data_completeness_score": 95.0,
                "low_level_qv_g_kg": 8.0,
                "mean_qv_0_500m_g_kg": 8.0,
                "mean_qv_0_1000m_g_kg": 8.0,
                "surface_t_td_spread_c": 4.0,
                "estimated_lcl_height_m_agl": 500.0,
                "lapse_rate_0_1000m_c_per_km": 7.0,
                "lapse_rate_0_3000m_c_per_km": 5.5,
                "cap_strength_proxy": 0.5,
                "cap_height_m_agl": 1100.0,
                "moisture_depth_m": 1800.0,
                "midlevel_dry_layer_proxy": 1.0,
                "observed_wind_available": True,
                "profile_top_m_agl": 18000.0,
                "lowest_level_m_agl": 0.0,
            },
            True,
            "shallow_cumulus_candidate",
        ),
        (
            {
                "data_completeness_score": 95.0,
                "low_level_qv_g_kg": 2.0,
                "mean_qv_0_500m_g_kg": 2.0,
                "mean_qv_0_1000m_g_kg": 2.0,
                "surface_t_td_spread_c": 18.0,
                "estimated_lcl_height_m_agl": 2300.0,
                "lapse_rate_0_1000m_c_per_km": 7.5,
                "lapse_rate_0_3000m_c_per_km": 6.0,
                "cap_strength_proxy": 0.5,
                "cap_height_m_agl": 1100.0,
                "moisture_depth_m": 400.0,
                "midlevel_dry_layer_proxy": 9.0,
                "observed_wind_available": True,
                "profile_top_m_agl": 18000.0,
                "lowest_level_m_agl": 0.0,
            },
            True,
            "dry_failed_candidate",
        ),
        (
            {
                "data_completeness_score": 95.0,
                "low_level_qv_g_kg": 8.0,
                "mean_qv_0_500m_g_kg": 8.0,
                "mean_qv_0_1000m_g_kg": 8.0,
                "surface_t_td_spread_c": 4.0,
                "estimated_lcl_height_m_agl": 500.0,
                "lapse_rate_0_1000m_c_per_km": 7.0,
                "lapse_rate_0_3000m_c_per_km": 3.0,
                "cap_strength_proxy": 5.0,
                "cap_height_m_agl": 1200.0,
                "moisture_depth_m": 1300.0,
                "midlevel_dry_layer_proxy": 2.0,
                "observed_wind_available": True,
                "profile_top_m_agl": 18000.0,
                "lowest_level_m_agl": 0.0,
            },
            True,
            "capped_suppressed_candidate",
        ),
        (
            {
                "data_completeness_score": 95.0,
                "low_level_qv_g_kg": 11.0,
                "mean_qv_0_500m_g_kg": 11.0,
                "mean_qv_0_1000m_g_kg": 11.0,
                "surface_t_td_spread_c": 2.0,
                "estimated_lcl_height_m_agl": 250.0,
                "lapse_rate_0_1000m_c_per_km": 5.0,
                "lapse_rate_0_3000m_c_per_km": 4.5,
                "cap_strength_proxy": 0.0,
                "cap_height_m_agl": None,
                "moisture_depth_m": 3000.0,
                "midlevel_dry_layer_proxy": 0.5,
                "observed_wind_available": True,
                "profile_top_m_agl": 18000.0,
                "lowest_level_m_agl": 0.0,
            },
            True,
            "humid_rainy_candidate",
        ),
        (
            {
                "data_completeness_score": 15.0,
                "low_level_qv_g_kg": 8.0,
                "mean_qv_0_500m_g_kg": 8.0,
                "mean_qv_0_1000m_g_kg": 8.0,
                "surface_t_td_spread_c": 4.0,
                "estimated_lcl_height_m_agl": 500.0,
                "lapse_rate_0_1000m_c_per_km": 7.0,
                "lapse_rate_0_3000m_c_per_km": 5.5,
                "cap_strength_proxy": 0.5,
                "cap_height_m_agl": 1100.0,
                "moisture_depth_m": 1800.0,
                "midlevel_dry_layer_proxy": 1.0,
                "observed_wind_available": True,
                "profile_top_m_agl": 18000.0,
                "lowest_level_m_agl": 0.0,
            },
            True,
            "needs_review",
        ),
        (
            {
                "data_completeness_score": 15.0,
                "mean_qv_0_1000m_g_kg": None,
                "estimated_lcl_height_m_agl": None,
                "lapse_rate_0_1000m_c_per_km": None,
                "cap_strength_proxy": None,
                "moisture_depth_m": None,
                "midlevel_dry_layer_proxy": None,
                "observed_wind_available": False,
                "profile_top_m_agl": 800.0,
                "lowest_level_m_agl": 700.0,
            },
            False,
            "poor_or_incomplete_candidate",
        ),
    ],
)
def test_story_scoring_selects_expected_hypothesis(
    features: dict[str, float | int | str | bool | None],
    package_ready: bool,
    expected_story: str,
) -> None:
    scores, evidence = _score_features(features, package_ready=package_ready)

    assert scores[0].story == expected_story
    assert evidence


def test_story_scoring_missing_moisture_is_not_confident_dry() -> None:
    scores, evidence = _score_features(
        {
            "data_completeness_score": 90.0,
            "mean_qv_0_1000m_g_kg": None,
            "estimated_lcl_height_m_agl": None,
            "lapse_rate_0_1000m_c_per_km": 7.0,
            "cap_strength_proxy": 0.5,
            "moisture_depth_m": None,
            "midlevel_dry_layer_proxy": None,
        },
        package_ready=True,
    )

    dry_score = next(score for score in scores if score.story == "dry_failed_candidate")
    needs_review = next(score for score in scores if score.story == "needs_review")
    assert dry_score.support == "unavailable"
    assert dry_score.score_0_to_100 < needs_review.score_0_to_100
    assert "missing_or_unavailable_feature:mean_qv_0_1000m_g_kg" in dry_score.caveats
    assert any(item.label == "Mean qv 0-1 km" and item.caveats for item in evidence)


def test_deep_convection_scoring_finds_moist_sheared_profiles() -> None:
    scores, evidence = _score_features(
        {
            "data_completeness_score": 98.0,
            "low_level_qv_g_kg": 15.0,
            "mean_qv_0_500m_g_kg": 15.0,
            "mean_qv_0_1000m_g_kg": 14.5,
            "mean_qv_0_3000m_g_kg": 10.0,
            "precipitable_water_proxy_or_unavailable": 42.0,
            "surface_t_td_spread_c": 4.5,
            "estimated_lcl_height_m_agl": 562.5,
            "lapse_rate_0_1000m_c_per_km": 8.0,
            "lapse_rate_0_3000m_c_per_km": 7.5,
            "midlevel_lapse_rate_700_500_hpa_c_per_km": 7.2,
            "cap_strength_proxy": 0.5,
            "cap_height_m_agl": 1400.0,
            "moisture_depth_m": 4200.0,
            "midlevel_dry_layer_proxy": 3.0,
            "qv_drop_0_3000m_g_kg": 5.0,
            "observed_wind_available": True,
            "bulk_shear_0_1km_m_s": 9.0,
            "bulk_shear_0_3km_m_s": 18.0,
            "bulk_shear_0_6km_m_s": 31.0,
            "dry_microburst_inverted_v_proxy": 20.0,
            "freezing_level_m_agl": 4200.0,
            "surface_based_cape_j_kg": 2800.0,
            "mixed_layer_cape_j_kg": 2400.0,
            "surface_based_cin_j_kg": -35.0,
            "mixed_layer_cin_j_kg": -45.0,
            "lfc_height_m_agl": 1100.0,
            "el_height_m_agl": 12500.0,
            "profile_top_m_agl": 18000.0,
            "lowest_level_m_agl": 0.0,
        },
        package_ready=True,
    )

    score_by_story = {score.story: score for score in scores}
    assert scores[0].story in {
        "severe_thunderstorm_environment",
        "supercell_environment",
        "squall_line_cold_pool_candidate",
    }
    assert score_by_story["supercell_environment"].support == "supported"
    assert score_by_story["severe_thunderstorm_environment"].support == "supported"
    assert any(item.label == "Bulk shear 0-6 km" for item in evidence)
    assert any(item.label == "Midlevel lapse rate 700-500 hPa" for item in evidence)


def test_deep_convection_scoring_prioritizes_high_cape_story_over_shallow() -> None:
    scores, _evidence = _score_features(
        {
            "data_completeness_score": 100.0,
            "low_level_qv_g_kg": 20.0,
            "mean_qv_0_500m_g_kg": 19.0,
            "mean_qv_0_1000m_g_kg": 18.4,
            "mean_qv_0_3000m_g_kg": 10.0,
            "precipitable_water_proxy_or_unavailable": 45.0,
            "surface_t_td_spread_c": 8.0,
            "estimated_lcl_height_m_agl": 1000.0,
            "lapse_rate_0_1000m_c_per_km": 8.0,
            "lapse_rate_0_3000m_c_per_km": 7.5,
            "midlevel_lapse_rate_700_500_hpa_c_per_km": 7.3,
            "cap_strength_proxy": 0.0,
            "cap_height_m_agl": None,
            "moisture_depth_m": 2800.0,
            "midlevel_dry_layer_proxy": 4.0,
            "qv_drop_0_3000m_g_kg": 8.0,
            "observed_wind_available": True,
            "bulk_shear_0_1km_m_s": 5.0,
            "bulk_shear_0_3km_m_s": 12.0,
            "bulk_shear_0_6km_m_s": 21.0,
            "dry_microburst_inverted_v_proxy": 30.0,
            "freezing_level_m_agl": 4200.0,
            "surface_based_cape_j_kg": 2100.0,
            "mixed_layer_cape_j_kg": 1900.0,
            "surface_based_cin_j_kg": 0.0,
            "mixed_layer_cin_j_kg": -1.0,
            "lfc_height_m_agl": 0.0,
            "el_height_m_agl": 12500.0,
            "profile_top_m_agl": 18000.0,
            "lowest_level_m_agl": 0.0,
        },
        package_ready=True,
    )

    score_by_story = {score.story: score for score in scores}
    assert scores[0].story == "severe_thunderstorm_environment"
    assert score_by_story["severe_thunderstorm_environment"].support == "supported"
    assert score_by_story["shallow_cumulus_candidate"].score_0_to_100 < (
        score_by_story["severe_thunderstorm_environment"].score_0_to_100
    )


def test_deep_convection_scoring_does_not_require_el_when_cape_and_shear_are_supported() -> None:
    scores, _evidence = _score_features(
        {
            "data_completeness_score": 100.0,
            "low_level_qv_g_kg": 14.5,
            "mean_qv_0_500m_g_kg": 14.5,
            "mean_qv_0_1000m_g_kg": 14.4,
            "mean_qv_0_3000m_g_kg": 9.5,
            "precipitable_water_proxy_or_unavailable": 35.0,
            "surface_t_td_spread_c": 4.6,
            "estimated_lcl_height_m_agl": 575.0,
            "lapse_rate_0_1000m_c_per_km": 6.0,
            "lapse_rate_0_3000m_c_per_km": 6.4,
            "midlevel_lapse_rate_700_500_hpa_c_per_km": 7.25,
            "cap_strength_proxy": 0.7,
            "cap_height_m_agl": 1400.0,
            "moisture_depth_m": 1680.0,
            "midlevel_dry_layer_proxy": 3.0,
            "qv_drop_0_3000m_g_kg": 5.0,
            "observed_wind_available": True,
            "bulk_shear_0_1km_m_s": 9.0,
            "bulk_shear_0_3km_m_s": 18.0,
            "bulk_shear_0_6km_m_s": 36.0,
            "dry_microburst_inverted_v_proxy": 20.0,
            "freezing_level_m_agl": 4200.0,
            "surface_based_cape_j_kg": 1050.0,
            "mixed_layer_cape_j_kg": 870.0,
            "surface_based_cin_j_kg": 0.0,
            "mixed_layer_cin_j_kg": -0.5,
            "lfc_height_m_agl": 0.0,
            "el_height_m_agl": None,
            "profile_top_m_agl": 18000.0,
            "lowest_level_m_agl": 0.1,
        },
        package_ready=True,
    )

    score_by_story = {score.story: score for score in scores}
    assert scores[0].story in {
        "severe_thunderstorm_environment",
        "supercell_environment",
        "squall_line_cold_pool_candidate",
    }
    assert score_by_story["severe_thunderstorm_environment"].support == "supported"
    assert score_by_story["shallow_cumulus_candidate"].score_0_to_100 < (
        score_by_story["severe_thunderstorm_environment"].score_0_to_100
    )


def test_deep_convection_scoring_does_not_overpromote_low_cape_humid_profiles() -> None:
    scores, _evidence = _score_features(
        {
            "data_completeness_score": 98.0,
            "low_level_qv_g_kg": 18.0,
            "mean_qv_0_500m_g_kg": 18.0,
            "mean_qv_0_1000m_g_kg": 17.0,
            "mean_qv_0_3000m_g_kg": 16.0,
            "precipitable_water_proxy_or_unavailable": 45.0,
            "surface_t_td_spread_c": 2.0,
            "estimated_lcl_height_m_agl": 300.0,
            "lapse_rate_0_1000m_c_per_km": 6.5,
            "lapse_rate_0_3000m_c_per_km": 7.0,
            "midlevel_lapse_rate_700_500_hpa_c_per_km": 7.0,
            "cap_strength_proxy": 0.0,
            "cap_height_m_agl": None,
            "moisture_depth_m": 4000.0,
            "midlevel_dry_layer_proxy": 3.0,
            "qv_drop_0_3000m_g_kg": 3.0,
            "observed_wind_available": True,
            "bulk_shear_0_1km_m_s": 7.0,
            "bulk_shear_0_3km_m_s": 15.0,
            "bulk_shear_0_6km_m_s": 28.0,
            "dry_microburst_inverted_v_proxy": 15.0,
            "freezing_level_m_agl": 4200.0,
            "surface_based_cape_j_kg": 120.0,
            "mixed_layer_cape_j_kg": 80.0,
            "surface_based_cin_j_kg": 0.0,
            "mixed_layer_cin_j_kg": 0.0,
            "lfc_height_m_agl": 0.0,
            "el_height_m_agl": 12500.0,
            "profile_top_m_agl": 18000.0,
            "lowest_level_m_agl": 0.0,
        },
        package_ready=True,
    )

    score_by_story = {score.story: score for score in scores}
    assert scores[0].story == "humid_rainy_candidate"
    assert score_by_story["humid_rainy_candidate"].support == "supported"
    assert score_by_story["severe_thunderstorm_environment"].support == "weak"
    assert score_by_story["high_cape_pulse_storm"].support == "weak"


def test_deep_convection_scoring_penalizes_profiles_that_start_well_above_surface() -> None:
    scores, _evidence = _score_features(
        {
            "data_completeness_score": 100.0,
            "low_level_qv_g_kg": 18.0,
            "mean_qv_0_500m_g_kg": 18.0,
            "mean_qv_0_1000m_g_kg": 18.0,
            "mean_qv_0_3000m_g_kg": 11.0,
            "precipitable_water_proxy_or_unavailable": 45.0,
            "surface_t_td_spread_c": 8.0,
            "estimated_lcl_height_m_agl": 1000.0,
            "lapse_rate_0_1000m_c_per_km": 8.0,
            "lapse_rate_0_3000m_c_per_km": 7.5,
            "midlevel_lapse_rate_700_500_hpa_c_per_km": 7.3,
            "cap_strength_proxy": 0.0,
            "cap_height_m_agl": None,
            "moisture_depth_m": 2800.0,
            "midlevel_dry_layer_proxy": 4.0,
            "qv_drop_0_3000m_g_kg": 8.0,
            "observed_wind_available": True,
            "bulk_shear_0_1km_m_s": 5.0,
            "bulk_shear_0_3km_m_s": 12.0,
            "bulk_shear_0_6km_m_s": 21.0,
            "dry_microburst_inverted_v_proxy": 30.0,
            "freezing_level_m_agl": 4200.0,
            "surface_based_cape_j_kg": 2100.0,
            "mixed_layer_cape_j_kg": 1900.0,
            "surface_based_cin_j_kg": 0.0,
            "mixed_layer_cin_j_kg": -1.0,
            "lfc_height_m_agl": 0.0,
            "el_height_m_agl": 12500.0,
            "profile_top_m_agl": 18000.0,
            "lowest_level_m_agl": 452.0,
        },
        package_ready=True,
    )

    severe = next(score for score in scores if score.story == "severe_thunderstorm_environment")
    assert severe.support == "unavailable"
    assert "lowest_usable_level_too_high_for_observed_surface_forcing" in severe.caveats


def test_deep_convection_scoring_requires_observed_wind_support() -> None:
    scores, _evidence = _score_features(
        {
            "data_completeness_score": 98.0,
            "low_level_qv_g_kg": 15.0,
            "mean_qv_0_500m_g_kg": 15.0,
            "mean_qv_0_1000m_g_kg": 14.5,
            "mean_qv_0_3000m_g_kg": 10.0,
            "precipitable_water_proxy_or_unavailable": 42.0,
            "surface_t_td_spread_c": 4.5,
            "estimated_lcl_height_m_agl": 562.5,
            "lapse_rate_0_1000m_c_per_km": 8.0,
            "lapse_rate_0_3000m_c_per_km": 7.5,
            "midlevel_lapse_rate_700_500_hpa_c_per_km": 7.2,
            "cap_strength_proxy": 0.5,
            "cap_height_m_agl": 1400.0,
            "moisture_depth_m": 4200.0,
            "midlevel_dry_layer_proxy": 3.0,
            "qv_drop_0_3000m_g_kg": 5.0,
            "observed_wind_available": False,
            "bulk_shear_0_1km_m_s": 9.0,
            "bulk_shear_0_3km_m_s": 18.0,
            "bulk_shear_0_6km_m_s": 31.0,
            "dry_microburst_inverted_v_proxy": 20.0,
            "freezing_level_m_agl": 4200.0,
            "surface_based_cape_j_kg": 2800.0,
            "mixed_layer_cape_j_kg": 2400.0,
            "surface_based_cin_j_kg": -35.0,
            "mixed_layer_cin_j_kg": -45.0,
            "lfc_height_m_agl": 1100.0,
            "el_height_m_agl": 12500.0,
            "profile_top_m_agl": 18000.0,
            "lowest_level_m_agl": 0.0,
        },
        package_ready=True,
    )

    supercell = next(score for score in scores if score.story == "supercell_environment")
    severe = next(score for score in scores if score.story == "severe_thunderstorm_environment")
    assert supercell.support == "unavailable"
    assert severe.support == "unavailable"
    assert "complete_observed_wind_profile_required_for_input_sounding" in supercell.caveats


def test_deep_tower_opportunity_separates_success_from_miss_features() -> None:
    fort_worth_like: dict[str, FeatureValue] = {
        "data_completeness_score": 100.0,
        "low_level_qv_g_kg": 22.094,
        "mean_qv_0_500m_g_kg": 22.094,
        "mean_qv_0_1000m_g_kg": 20.398,
        "mean_qv_0_3000m_g_kg": 14.623,
        "precipitable_water_proxy_or_unavailable": 43.11,
        "surface_t_td_spread_c": 6.0,
        "estimated_lcl_height_m_agl": 750.1,
        "lapse_rate_0_1000m_c_per_km": 8.36,
        "lapse_rate_0_3000m_c_per_km": 6.88,
        "midlevel_lapse_rate_700_500_hpa_c_per_km": 7.97,
        "cap_strength_proxy": 0.0,
        "cap_height_m_agl": None,
        "moisture_depth_m": 1893.8,
        "midlevel_dry_layer_proxy": 10.0,
        "qv_drop_0_3000m_g_kg": 7.471,
        "observed_wind_available": True,
        "bulk_shear_0_1km_m_s": 8.0,
        "bulk_shear_0_3km_m_s": 15.0,
        "bulk_shear_0_6km_m_s": 19.88,
        "dry_microburst_inverted_v_proxy": 50.0,
        "freezing_level_m_agl": 4200.0,
        "surface_based_cape_j_kg": 1781.0,
        "mixed_layer_cape_j_kg": 1820.3,
        "surface_based_cin_j_kg": 0.0,
        "mixed_layer_cin_j_kg": -5.3,
        "lfc_height_m_agl": 2.8,
        "el_height_m_agl": 98.2,
        "profile_top_m_agl": 19311.8,
        "lowest_level_m_agl": 2.8,
        "near_surface_discontinuity_flag": False,
    }
    north_platte_like = {
        **fort_worth_like,
        "low_level_qv_g_kg": 16.199,
        "mean_qv_0_500m_g_kg": 15.723,
        "mean_qv_0_1000m_g_kg": 14.83,
        "mean_qv_0_3000m_g_kg": 11.052,
        "precipitable_water_proxy_or_unavailable": 27.56,
        "surface_t_td_spread_c": 9.8,
        "estimated_lcl_height_m_agl": 1225.1,
        "lapse_rate_0_1000m_c_per_km": 9.59,
        "lapse_rate_0_3000m_c_per_km": 8.09,
        "midlevel_lapse_rate_700_500_hpa_c_per_km": 7.58,
        "cap_strength_proxy": 0.4,
        "cap_height_m_agl": 1473.2,
        "moisture_depth_m": 1542.2,
        "qv_drop_0_3000m_g_kg": 5.148,
        "bulk_shear_0_1km_m_s": 2.19,
        "bulk_shear_0_3km_m_s": 9.47,
        "bulk_shear_0_6km_m_s": 22.39,
        "dry_microburst_inverted_v_proxy": 69.6,
        "surface_based_cape_j_kg": 1081.7,
        "mixed_layer_cape_j_kg": 994.6,
        "mixed_layer_cin_j_kg": -1.7,
        "lfc_height_m_agl": 0.2,
        "el_height_m_agl": 9390.3,
        "profile_top_m_agl": 19917.2,
        "lowest_level_m_agl": 0.2,
    }

    _score_features(fort_worth_like, package_ready=True)
    _score_features(north_platte_like, package_ready=True)

    fort_score = cast(float, fort_worth_like["deep_tower_opportunity"])
    north_platte_score = cast(float, north_platte_like["deep_tower_opportunity"])
    assert fort_score == pytest.approx(81.7)
    assert fort_worth_like["deep_tower_opportunity_support"] == "supported"
    assert north_platte_score == pytest.approx(46.1)
    assert north_platte_like["deep_tower_opportunity_support"] == "weak"
    assert fort_score > north_platte_score + 30.0


def test_analysis_deep_family_best_match_uses_deep_tower_opportunity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    high_story_low_opportunity = _analysis_candidate(
        "high-story-low-opportunity",
        deep_score=91.0,
        deep_support="supported",
    ).model_copy(update={"features": {"deep_tower_opportunity": 41.0}})
    lower_story_better_opportunity = _analysis_candidate(
        "lower-story-better-opportunity",
        deep_score=72.0,
        deep_support="supported",
    ).model_copy(update={"features": {"deep_tower_opportunity": 82.0}})
    _patch_screened_candidates(
        monkeypatch,
        [high_story_low_opportunity, lower_story_better_opportunity],
    )

    result = analyze_cached_soundings(
        _settings(tmp_path),
        story_family="deep_convection",
        sort_by="best_match",
    )

    assert [item.candidate_id for item in result.candidates] == [
        "lower-story-better-opportunity",
        "high-story-low-opportunity",
    ]
    assert [item.active_story_score for item in result.candidates] == [72.0, 91.0]
    assert [item.ingredient_score for item in result.candidates] == [82.0, 41.0]


def test_story_scores_and_evidence_are_traceable_to_soundings() -> None:
    scores, evidence = _score_features(
        {
            "data_completeness_score": 95.0,
            "low_level_qv_g_kg": 11.0,
            "mean_qv_0_500m_g_kg": 11.0,
            "mean_qv_0_1000m_g_kg": 11.0,
            "surface_t_td_spread_c": 2.0,
            "estimated_lcl_height_m_agl": 250.0,
            "lapse_rate_0_1000m_c_per_km": 5.0,
            "lapse_rate_0_3000m_c_per_km": 4.5,
            "cap_strength_proxy": 0.0,
            "cap_height_m_agl": None,
            "moisture_depth_m": 3000.0,
            "midlevel_dry_layer_proxy": 0.5,
            "observed_wind_available": True,
            "profile_top_m_agl": 18000.0,
            "lowest_level_m_agl": 0.0,
        },
        package_ready=True,
    )

    assert {score.story for score in scores} == {
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
    }
    assert all(score.reasons for score in scores)
    assert {item.label for item in evidence} >= {
        "Low-level qv",
        "Mean qv 0-500 m",
        "Mean qv 0-1 km",
        "Surface T-Td spread",
        "Estimated LCL",
        "Low-level lapse rate",
        "Lapse rate 0-3 km",
        "Cap strength proxy",
        "Cap height proxy",
        "Moisture depth",
        "Midlevel dry-layer proxy",
        "Midlevel lapse rate 700-500 hPa",
        "Bulk shear 0-1 km",
        "Bulk shear 0-3 km",
        "Bulk shear 0-6 km",
        "Dry microburst / inverted-V proxy",
        "Freezing level",
        "Observed wind availability",
        "Profile top",
        "Lowest usable level",
        "Profile completeness",
        "Package readiness",
    }


def test_saved_candidates_round_trip_runtime_local(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(settings)
    candidate = screen_cached_soundings(settings, latest_per_station=1).candidates[0]

    saved = save_candidate(
        settings,
        SaveCandidateRequest(candidate=candidate, tags=["candidate"], notes="try this"),
    )

    assert saved.saved_candidate_id == candidate.candidate_id
    assert saved.selected_sounding_payload == candidate.selected_sounding_payload
    saved_path = settings.cache_dir / "sounding-candidates" / "saved_candidates.json"
    assert saved_path.exists()
    assert json.loads(saved_path.read_text())[0]["tags"] == ["candidate"]
    assert list_saved_candidates(settings)[0].notes == "try this"

    updated = update_saved_candidate(
        settings,
        saved.saved_candidate_id,
        UpdateSavedCandidateRequest(
            tags=["Deep convection candidates", "Needs review", "Needs review"],
            notes="tagged for follow-up",
        ),
    )

    assert updated is not None
    assert updated.tags == ["Deep convection candidates", "Needs review"]
    assert list_saved_candidates(settings)[0].notes == "tagged for follow-up"


def test_sounding_candidate_api_screen_save_and_delete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(settings)
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(settings.runtime_home))
    client = TestClient(app)

    inputs = client.get("/api/sounding-candidates/screening-inputs")
    assert inputs.status_code == 200
    assert inputs.json()["inputs"][0]["station_id"] == "USM00072558"

    screened = client.post(
        "/api/sounding-candidates/screen",
        json={
            "station_id": "USM00072558",
            "latest_per_station": 1,
            "limit": 5,
            "target_story": "shallow_cumulus_candidate",
        },
    )
    assert screened.status_code == 200
    candidate = screened.json()["candidates"][0]
    assert candidate["selected_sounding_payload"]["station_id"] == "USM00072558"

    deep_screened = client.post(
        "/api/sounding-candidates/screen",
        json={
            "station_id": "USM00072558",
            "latest_per_station": 1,
            "limit": 5,
            "target_story": "deep_convection_trial",
        },
    )
    assert deep_screened.status_code == 200

    analyzed = client.post(
        "/api/sounding-candidates/analyze",
        json={
            "station_id": "USM00072558",
            "latest_per_station": 1,
            "limit": 5,
            "story_filter": "shallow_cumulus_candidate",
            "support": "weak",
            "readiness": "package_ready",
            "sort_by": "mean_qv_0_1000m_g_kg",
        },
    )
    assert analyzed.status_code == 200
    analyzed_payload = analyzed.json()
    assert analyzed_payload["filters"]["story_filter"] == "shallow_cumulus_candidate"
    assert analyzed_payload["sort_by"] == "mean_qv_0_1000m_g_kg"
    assert analyzed_payload["sort_options"]
    assert analyzed_payload["filter_trace"]["analyzed_soundings"] >= 1
    assert analyzed_payload["filter_trace"]["stage_counts"]["limited"] == len(
        analyzed_payload["candidates"]
    )
    assert analyzed_payload["candidates"][0]["active_story"] == "shallow_cumulus_candidate"

    saved = client.post(
        "/api/sounding-candidates/saved",
        json={"candidate": candidate, "tags": ["manual-review"]},
    )
    assert saved.status_code == 200
    saved_id = saved.json()["saved_candidate_id"]

    patched = client.patch(
        f"/api/sounding-candidates/saved/{saved_id}",
        json={"tags": ["Surface-forced candidates", "Needs review"], "notes": "try longer"},
    )
    assert patched.status_code == 200
    assert patched.json()["tags"] == ["Surface-forced candidates", "Needs review"]
    assert patched.json()["notes"] == "try longer"

    listed = client.get("/api/sounding-candidates/saved")
    assert listed.status_code == 200
    assert listed.json()["saved_candidates"][0]["saved_candidate_id"] == saved_id
    assert listed.json()["saved_candidates"][0]["tags"] == [
        "Surface-forced candidates",
        "Needs review",
    ]

    deleted = client.delete(f"/api/sounding-candidates/saved/{saved_id}")
    assert deleted.status_code == 200
    assert deleted.json() == {"saved_candidate_id": saved_id, "deleted": True}


def test_sounding_candidate_api_rejects_invalid_screen_limits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(settings)
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(settings.runtime_home))

    response = TestClient(app).post(
        "/api/sounding-candidates/screen",
        json={"latest_per_station": 0, "limit": 5},
    )

    assert response.status_code == 400
    assert "latest_per_station" in response.json()["detail"]


def test_candidate_screening_metadata_is_written_to_package_manifests(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(settings)
    candidate = screen_cached_soundings(settings, latest_per_station=1).candidates[0]
    candidate_screening = {
        "candidate_id": candidate.candidate_id,
        "primary_story": candidate.primary_story,
        "screening_version": candidate.screening_version,
        "rank_score": candidate.rank_score,
    }

    result = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=settings.runtime_home,
        run_id="dry-run-candidate-test",
        controls={},
        observed_sounding=candidate.selected_sounding_payload,
        candidate_screening=candidate_screening,
    )

    manifest = load_run_manifest(result.manifest_path)
    case_manifest = json.loads((result.package_dir / "case_manifest.json").read_text())
    report = read_dry_run_report(result.report_path)
    assert manifest.candidate_screening == candidate_screening
    assert case_manifest["candidate_screening"] == candidate_screening
    assert report["candidate_screening"] == candidate_screening
