import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.app import app
from cloud_chamber.dry_run_package import generate_dry_run_package, read_dry_run_report
from cloud_chamber.igra_catalog import IGRACacheEntry, IGRACacheManifest, igra_cache_manifest_path
from cloud_chamber.run_manifest import load_run_manifest
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.sounding_candidates import (
    SaveCandidateRequest,
    _score_features,
    list_saved_candidates,
    list_screening_inputs,
    save_candidate,
    screen_cached_soundings,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"


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
    manifest = IGRACacheManifest(
        cache_root=str(settings.cache_dir / "igra" / "recent"),
        entries=[entry],
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    path = igra_cache_manifest_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2) + "\n")
    return text_path


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

    assert result.screening_version == "sounding-screening-v1"
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
        "needs_review",
        "poor_or_incomplete_candidate",
    }
    assert set(candidate.features) >= {
        "mean_qv_0_1000m_g_kg",
        "estimated_lcl_height_m_agl",
        "lapse_rate_0_1000m_c_per_km",
        "cap_strength_proxy",
        "profile_top_m_agl",
    }
    assert candidate.evidence
    assert candidate.story_scores[0].score_0_to_100 >= candidate.story_scores[-1].score_0_to_100


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
        "elevated_convection",
        "dry_microburst_inverted_v",
        "high_cape_pulse_storm",
        "squall_line_cold_pool_candidate",
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
        "Midlevel lapse rate",
        "Moisture depth",
        "Midlevel dry-layer proxy",
        "Bulk shear 0-6 km",
        "Bulk shear 0-3 km",
        "Dry microburst proxy",
        "Freezing level",
        "Observed wind availability",
        "Profile top",
        "Lowest usable level",
        "Profile completeness",
        "Package readiness",
    }


def _deep_convection_feature_set(
    **overrides: float | int | str | bool | None,
) -> dict[str, float | int | str | bool | None]:
    features: dict[str, float | int | str | bool | None] = {
        "data_completeness_score": 95.0,
        "low_level_qv_g_kg": 12.0,
        "mean_qv_0_500m_g_kg": 12.0,
        "mean_qv_0_1000m_g_kg": 12.0,
        "mean_qv_0_3000m_g_kg": 8.0,
        "surface_t_td_spread_c": 5.0,
        "estimated_lcl_height_m_agl": 625.0,
        "lapse_rate_0_1000m_c_per_km": 7.5,
        "lapse_rate_0_3000m_c_per_km": 7.5,
        "midlevel_lapse_rate_700_500_hpa_c_per_km": 7.0,
        "cap_strength_proxy": 2.0,
        "cap_height_m_agl": 1200.0,
        "inversion_strength_c": 2.0,
        "moisture_depth_m": 3500.0,
        "midlevel_dry_layer_proxy": 3.0,
        "qv_drop_0_3000m_g_kg": 4.0,
        "dry_microburst_inverted_v_proxy": 30.0,
        "bulk_shear_0_1km_m_s": 8.0,
        "bulk_shear_0_3km_m_s": 15.0,
        "bulk_shear_0_6km_m_s": 25.0,
        "freezing_level_m_agl": 3500.0,
        "observed_wind_available": True,
        "profile_top_m_agl": 18000.0,
        "lowest_level_m_agl": 0.0,
    }
    features.update(overrides)
    return features


@pytest.mark.parametrize(
    ("story", "overrides", "future_required", "readiness"),
    [
        ("severe_thunderstorm_environment", {}, False, "runnable_caveated"),
        (
            "supercell_environment",
            {
                "bulk_shear_0_1km_m_s": 16.0,
                "bulk_shear_0_3km_m_s": 26.0,
                "bulk_shear_0_6km_m_s": 35.0,
            },
            True,
            "future_package_needed",
        ),
        (
            "elevated_convection",
            {
                "inversion_strength_c": 7.0,
                "cap_strength_proxy": 6.0,
                "cap_height_m_agl": 1500.0,
                "bulk_shear_0_3km_m_s": 20.0,
            },
            True,
            "future_package_needed",
        ),
        (
            "dry_microburst_inverted_v",
            {
                "mean_qv_0_1000m_g_kg": 5.0,
                "surface_t_td_spread_c": 25.0,
                "estimated_lcl_height_m_agl": 2500.0,
                "midlevel_dry_layer_proxy": 9.0,
                "qv_drop_0_3000m_g_kg": 8.0,
                "dry_microburst_inverted_v_proxy": 90.0,
            },
            False,
            "runnable_caveated",
        ),
        (
            "high_cape_pulse_storm",
            {"bulk_shear_0_6km_m_s": 8.0, "cap_strength_proxy": 0.2},
            False,
            "runnable_caveated",
        ),
        (
            "squall_line_cold_pool_candidate",
            {
                "bulk_shear_0_3km_m_s": 24.0,
                "bulk_shear_0_6km_m_s": 30.0,
                "midlevel_dry_layer_proxy": 6.0,
                "freezing_level_m_agl": 4200.0,
            },
            True,
            "future_package_needed",
        ),
    ],
)
def test_deep_convection_story_scores_have_readiness_metadata(
    story: str,
    overrides: dict[str, float | int | str | bool | None],
    future_required: bool,
    readiness: str,
) -> None:
    scores, evidence = _score_features(
        _deep_convection_feature_set(**overrides),
        package_ready=True,
    )

    score = next(candidate for candidate in scores if candidate.story == story)
    assert score.story_family == "deep_convection"
    assert score.score_0_to_100 >= 65.0
    assert score.support == "supported"
    assert score.readiness_state == readiness
    assert score.future_package_required is future_required
    assert score.specialized_package_recommended is True
    assert score.required_diagnostics_used
    assert score.assumptions
    assert "cm1_output_remains_source_of_truth" in score.caveats
    assert evidence


def test_deep_convection_missing_shear_is_caveated_not_confident() -> None:
    scores, _evidence = _score_features(
        _deep_convection_feature_set(
            bulk_shear_0_1km_m_s=None,
            bulk_shear_0_3km_m_s=None,
            bulk_shear_0_6km_m_s=None,
            observed_wind_available=False,
        ),
        package_ready=True,
    )

    severe = next(score for score in scores if score.story == "severe_thunderstorm_environment")
    supercell = next(score for score in scores if score.story == "supercell_environment")
    assert severe.support == "weak"
    assert "bulk_shear_0_6km_m_s" in severe.unavailable_diagnostics
    assert supercell.support == "unavailable"
    assert "bulk_shear_0_1km_m_s" in supercell.unavailable_diagnostics
    assert "storm_relative_helicity_unavailable" in supercell.caveats


def test_saved_candidates_preserve_deep_convection_readiness_metadata(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_cached_igra_station(settings)
    candidate = screen_cached_soundings(
        settings,
        latest_per_station=1,
        target_story="severe_thunderstorm_environment",
    ).candidates[0]
    severe_score = next(
        score
        for score in candidate.story_scores
        if score.story == "severe_thunderstorm_environment"
    )

    saved = save_candidate(settings, SaveCandidateRequest(candidate=candidate))

    assert saved.story_scores == candidate.story_scores
    assert severe_score.story_family == "deep_convection"
    assert any(
        score.story == "severe_thunderstorm_environment" and score.specialized_package_recommended
        for score in list_saved_candidates(settings)[0].story_scores
    )


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

    saved = client.post(
        "/api/sounding-candidates/saved",
        json={"candidate": candidate, "tags": ["manual-review"]},
    )
    assert saved.status_code == 200
    saved_id = saved.json()["saved_candidate_id"]

    listed = client.get("/api/sounding-candidates/saved")
    assert listed.status_code == 200
    assert listed.json()["saved_candidates"][0]["saved_candidate_id"] == saved_id

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
        run_size_preset="quick_look",
        observed_sounding=candidate.selected_sounding_payload,
        candidate_screening=candidate_screening,
    )

    manifest = load_run_manifest(result.manifest_path)
    case_manifest = json.loads((result.package_dir / "case_manifest.json").read_text())
    report = read_dry_run_report(result.report_path)
    assert manifest.candidate_screening == candidate_screening
    assert case_manifest["candidate_screening"] == candidate_screening
    assert report["candidate_screening"] == candidate_screening
