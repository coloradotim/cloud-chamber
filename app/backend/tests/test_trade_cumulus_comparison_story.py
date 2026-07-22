from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import cloud_chamber.trade_cumulus_comparison_story as comparison_story
from cloud_chamber.result_ingest import ResultIngestError, ResultMetadata
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.trade_cumulus_comparison_story import (
    BASELINE_RESULT_ID,
    BASELINE_RUN_ID,
    MORE_MOISTURE_RESULT_ID,
    MORE_MOISTURE_RUN_ID,
    TradeCumulusComparisonStoryConflict,
    TradeCumulusComparisonStoryNotFound,
    trade_cumulus_moisture_comparison_story,
)
from cloud_chamber.trade_cumulus_updraft_lens import (
    TRADE_CUMULUS_UPDRAFT_SCALE_BREAKPOINTS_M_S,
    TRADE_CUMULUS_UPDRAFT_SCALE_COLORS,
    TRADE_CUMULUS_UPDRAFT_SCALE_ID,
    TradeCumulusUpdraftLensError,
)


def _settings(tmp_path: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=tmp_path,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "cache",
        log_dir=tmp_path / "logs",
    )


def _gate(control_value: float) -> dict[str, Any]:
    return {
        "valid": True,
        "lifecycle_state": "completed",
        "product_state": "completed_cm1_result",
        "exit_code": 0,
        "normal_completion_reported": True,
        "runtime_integrity_state": "caveated",
        "runtime_integrity_reason": "runtime_integrity_caveated_evidence_present",
        "runtime_integrity_caveats": ["runtime_integrity_caveated_underflow_only"],
        "model_output_count": 241,
        "expected_model_output_count": 241,
        "diagnostic_output_count": 241,
        "expected_diagnostic_output_count": 241,
        "missing_required_fields": [],
        "required_field_non_finite_counts": {"ql": 0, "w": 0, "u": 0, "v": 0},
        "intended_surface_moisture_flux_g_g_m_s": control_value,
        "emitted_surface_moisture_flux_min_g_g_m_s": control_value,
        "emitted_surface_moisture_flux_max_g_g_m_s": control_value,
        "failures": [],
    }


def _run_evidence(
    *, result_id: str, run_id: str, control_state: str, control_value: float
) -> dict[str, Any]:
    cwp_values = [
        {"time_seconds": 3_600.0, "value": 0.007},
        {"time_seconds": 3_660.0, "value": 0.009},
    ]
    cover_values = [
        {"time_seconds": 3_600.0, "value": 10.0},
        {"time_seconds": 3_660.0, "value": 12.0},
    ]
    if control_state == "more_moisture":
        cwp_values = [
            {"time_seconds": 3_600.0, "value": 0.008},
            {"time_seconds": 3_660.0, "value": 0.008},
        ]
        cover_values = [
            {"time_seconds": 3_600.0, "value": 11.0},
            {"time_seconds": 3_660.0, "value": 11.0},
        ]
    return {
        "evidence_version": "trade_cumulus_moisture_run_evidence_v1",
        "product_slice_id": "trade_cumulus_v1",
        "comparison_group_id": "trade_cumulus_moisture_v1",
        "case_id": "bomex_trade_cumulus_baseline_v0",
        "recipe_candidate_id": "canonical_bomex_baseline",
        "control_id": "surface_moisture_supply",
        "control_state": control_state,
        "run_length": "full",
        "run_id": run_id,
        "result_id": result_id,
        "app_commit": "4647ef54a6c1b7a5d31e6e758c3c276fc5e5b2e0",
        "surface_moisture_flux_g_g_m_s": control_value,
        "duration_seconds": 14_400,
        "output_cadence_seconds": 60,
        "diagnostic_cadence_seconds": 60,
        "wall_clock_seconds": 1_300.0,
        "cm1_reported_runtime_seconds": 1_299.0,
        "output_bytes": 1_000,
        "gate": _gate(control_value),
        "scalar_metrics": {},
        "time_series": {
            "domain_mean_cwp": cwp_values,
            "total_cloud_cover_percent": cover_values,
        },
        "vertical_profiles": {},
        "final_domain_mean_profiles": {},
        "forcing_diagnostics": {},
        "forcing_and_transport_fields_available": [],
        "available_fields": ["cwp", "ql", "u", "v", "w"],
        "caveats": [],
    }


def _metric(
    units: str,
    method: str,
    window: str,
    baseline: float,
    more: float,
    absolute_delta: float,
    percent_delta: float,
) -> dict[str, Any]:
    return {
        "units": units,
        "method": method,
        "window": window,
        "baseline": baseline,
        "more_moisture": more,
        "absolute_delta": absolute_delta,
        "percent_delta": percent_delta,
        "percent_delta_unavailable_reason": None,
        "quality": "trusted",
        "caveats": [],
    }


def _evidence() -> dict[str, Any]:
    return {
        "evidence_version": "trade_cumulus_moisture_comparison_evidence_v2",
        "evidence_state": "matched_runs_valid",
        "implementation_commit": "4647ef54a6c1b7a5d31e6e758c3c276fc5e5b2e0",
        "baseline": _run_evidence(
            result_id=BASELINE_RESULT_ID,
            run_id=BASELINE_RUN_ID,
            control_state="baseline",
            control_value=5.2e-5,
        ),
        "more_moisture": _run_evidence(
            result_id=MORE_MOISTURE_RESULT_ID,
            run_id=MORE_MOISTURE_RUN_ID,
            control_state="more_moisture",
            control_value=7.8e-5,
        ),
        "scalar_metrics": {
            "mean_total_cloud_cover_final_three_hours": _metric(
                "%",
                "time mean of horizontal columns containing ql >= 1e-6 kg/kg",
                "time >= 3600 s",
                12.049246566144873,
                14.248040880141192,
                2.198794313996318,
                18.24839671033321,
            ),
            "domain_mean_cwp_final_three_hour_mean": _metric(
                "kg/m^2",
                "time mean of horizontal domain-mean cwp",
                "time >= 3600 s",
                0.006739830541318102,
                0.009686668911071296,
                0.0029468383697531936,
                43.72273682087092,
            ),
            "coherent_cloud_top_final_three_hour_mean": _metric(
                "m",
                "mean supported coherent cloud-object top",
                "time >= 3600 s",
                1750.690681499671,
                1859.9172027071536,
                109.22652120748262,
                6.2390530983987045,
            ),
            "first_isolated_cloud_liquid_time": _metric(
                "s",
                "first model frame with any finite ql >= 1e-6 kg/kg",
                "full run",
                1140.0,
                1140.0,
                0.0,
                0.0,
            ),
            "time_mean_cloud_fraction_profile_peak_height": _metric(
                "m",
                "height of first maximum in final-three-hour time-mean cloud-fraction profile",
                "time >= 3600 s",
                615.0000095367432,
                585.0000381469727,
                -29.999971389770508,
                -4.87804405277463,
            ),
            "cloudy_scalar_cells_with_positive_centered_w": _metric(
                "%",
                "pooled fraction of cloudy scalar cells with centered w > 0",
                "time >= 3600 s",
                89.51790219011582,
                89.54264215595985,
                0.024739965844034373,
                0.02763689188280158,
            ),
        },
        "exact_time_pairing": {
            "domain_mean_cwp": [
                {"time_seconds": 3_600.0, "value": 0.001},
                {"time_seconds": 3_660.0, "value": -0.001},
            ],
            "total_cloud_cover_percent": [
                {"time_seconds": 3_600.0, "value": 1.0},
                {"time_seconds": 3_660.0, "value": -1.0},
            ],
        },
        "matched_package_proof": {
            "comparison_group_id": "trade_cumulus_moisture_v1",
            "run_length": "full",
            "baseline_run_id": BASELINE_RUN_ID,
            "more_moisture_run_id": MORE_MOISTURE_RUN_ID,
            "differing_namelist_assignments": ["cnst_lhflx"],
            "fixed_assumptions_sha256": (
                "861375a82d209c36cc63ccce2d20934553b0e7e8811579c718dfb275899172a7"
            ),
            "baseline_science_settings_sha256": "baseline-science",
            "more_moisture_science_settings_sha256": "more-moisture-science",
            "shared_cm1_source_manifest_sha256": (
                "fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e"
            ),
            "shared_cm1_executable_sha256": (
                "5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1"
            ),
            "valid": True,
        },
        "stage4_consistency": {
            "preserved_result_id": "result-bomex-370-full-20260719",
            "new_baseline_result_id": BASELINE_RESULT_ID,
            "common_times_seconds": [3_600.0],
            "absolute_tolerance": 1e-10,
            "relative_tolerance": 1e-6,
            "field_differences": [],
            "first_failure": None,
            "passed": True,
        },
        "lens_preparation": {
            "baseline_result_id": BASELINE_RESULT_ID,
            "more_moisture_result_id": MORE_MOISTURE_RESULT_ID,
            "baseline_default_time_index": 201,
            "baseline_default_time_seconds": 12_060.0,
            "baseline_default_plane_index": 83,
            "baseline_default_plane_coordinate": 2.366666555404663,
            "baseline_default_plane_units": "km",
            "inherited_variant_time_index": 201,
            "inherited_variant_plane_index": 83,
            "wind_target_level_m": 600.0,
            "wind_level_index": 14,
            "wind_actual_level_m": 580.0,
            "wind_stride": 8,
            "cloud_threshold_kg_kg": 1e-6,
            "joint_w_range_min_m_s": -1.0,
            "joint_w_range_max_m_s": 1.0,
            "joint_perturbation_wind_reference_m_s": 0.9,
            "joint_total_wind_reference_m_s": 8.8,
            "coordinate_compatibility": "exact_scalar_grid_coordinates_match",
            "field_availability": {
                BASELINE_RESULT_ID: ["cwp", "ql", "u", "v", "w"],
                MORE_MOISTURE_RESULT_ID: ["cwp", "ql", "u", "v", "w"],
            },
        },
        "estimated_full_pair_bytes": 2_000,
        "actual_full_pair_bytes": 2_100,
        "runtime_local_evidence_path": "/machine/private/comparison_evidence.json",
        "caveats": [],
    }


def _metadata(
    result_id: str,
    run_id: str,
    control_state: str,
    control_value: float,
) -> ResultMetadata:
    now = datetime(2026, 7, 20, tzinfo=UTC)
    return ResultMetadata(
        result_id=result_id,
        run_id=run_id,
        scenario_id="bomex_trade_cumulus_baseline_v0",
        physical_question="How does stronger surface moisture supply change the field?",
        controls={
            "control_id": "surface_moisture_supply",
            "control_state": control_state,
            "surface_moisture_flux_g_g_m_s": control_value,
        },
        run_configuration={
            "case_id": "bomex_trade_cumulus_baseline_v0",
            "product_slice_id": "trade_cumulus_v1",
            "comparison_group_id": "trade_cumulus_moisture_v1",
            "control_id": "surface_moisture_supply",
            "control_state": control_state,
            "surface_moisture_flux_g_g_m_s": control_value,
            "fixed_assumptions_sha256": (
                "861375a82d209c36cc63ccce2d20934553b0e7e8811579c718dfb275899172a7"
            ),
            "cm1_provenance": {
                "source_manifest_sha256": (
                    "fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e"
                ),
                "executable_sha256": (
                    "5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1"
                ),
            },
        },
        source_lifecycle_state="completed",
        source_product_state="completed_cm1_result",
        source_model="CM1",
        created_at=now,
        updated_at=now,
    )


def _scale(**updates: Any) -> SimpleNamespace:
    values = {
        "w_scale_id": TRADE_CUMULUS_UPDRAFT_SCALE_ID,
        "w_scale_breakpoints_m_s": list(TRADE_CUMULUS_UPDRAFT_SCALE_BREAKPOINTS_M_S),
        "w_scale_colors": list(TRADE_CUMULUS_UPDRAFT_SCALE_COLORS),
        "cloud_threshold_kg_kg": 1e-6,
    }
    values.update(updates)
    return SimpleNamespace(**values)


def _frame(result_id: str, **updates: Any) -> SimpleNamespace:
    if result_id == BASELINE_RESULT_ID:
        values = {
            "result_id": result_id,
            "time_index": 201,
            "time_seconds": 12_060.0,
            "plane_index": 83,
            "plane_coordinate": 2.366666555404663,
        }
    else:
        values = {
            "result_id": result_id,
            "time_index": 232,
            "time_seconds": 13_920.0,
            "plane_index": 72,
            "plane_coordinate": 1.6333333253860474,
        }
    values.update(
        {
            "orientation": "vertical_x",
            "plane_dimension": "y",
            "plane_units": "km",
            "wind_mode": "perturbation",
            "w_finite_count": 4,
            "cloud_mask": [[True, False]],
            "wind_vectors": [object()],
        }
    )
    values.update(vars(_scale()))
    values.update(updates)
    return SimpleNamespace(**values)


def _install_valid_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    evidence: dict[str, Any] | None = None,
    frame_factory: Callable[[str], SimpleNamespace] = _frame,
) -> CloudChamberSettings:
    evidence_path = (
        tmp_path
        / "comparisons"
        / "trade-cumulus-presentation-v1-20260722"
        / "comparison_evidence.json"
    )
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(json.dumps(evidence or _evidence()))
    metadata = {
        BASELINE_RESULT_ID: _metadata(BASELINE_RESULT_ID, BASELINE_RUN_ID, "baseline", 5.2e-5),
        MORE_MOISTURE_RESULT_ID: _metadata(
            MORE_MOISTURE_RESULT_ID,
            MORE_MOISTURE_RUN_ID,
            "more_moisture",
            7.8e-5,
        ),
    }
    monkeypatch.setattr(
        comparison_story,
        "get_result_metadata",
        lambda _settings, result_id: metadata[result_id],
    )
    monkeypatch.setattr(
        comparison_story,
        "trade_cumulus_updraft_lens_defaults",
        lambda _settings, _result_id: _scale(),
    )
    monkeypatch.setattr(
        comparison_story,
        "trade_cumulus_updraft_lens_frame",
        lambda _settings, result_id, **_kwargs: frame_factory(result_id),
    )
    return _settings(tmp_path)


def test_story_returns_exact_authored_payload_and_curated_views(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _install_valid_dependencies(tmp_path, monkeypatch)

    payload = trade_cumulus_moisture_comparison_story(settings).model_dump(mode="json")

    assert payload["title"] == "Trade Cumulus: Baseline and More Moisture"
    assert payload["question"] == (
        "How does stronger surface moisture supply change the trade-cumulus field?"
    )
    assert payload["illustrative_view_note"].startswith("Illustrative views: selected")
    assert payload["baseline"]["display_name"] == "Canonical BOMEX Baseline"
    assert payload["baseline"]["control_display"] == "0.0520 g/kg m/s"
    assert payload["baseline"]["curated_view"] == {
        "time_index": 201,
        "time_seconds": 12_060.0,
        "orientation": "vertical_x",
        "plane_dimension": "y",
        "plane_index": 83,
        "plane_coordinate": 2.366666555404663,
        "plane_units": "km",
        "camera_preset": "overview",
        "cloud_field": "ql",
        "cloud_threshold_kg_kg": 1e-6,
        "lens_id": "updraft",
        "scale_id": "trade_cumulus_updraft_velocity_v1",
        "wind_mode": "perturbation",
        "show_wind": True,
        "show_cloud_boundary": True,
        "opacity": 0.68,
        "point_size": 11,
        "caption": (
            "This illustrative Baseline view shows several active cells across the slice, with "
            "rising cores bordered by sinking air."
        ),
    }
    assert payload["more_moisture"]["curated_view"]["time_index"] == 232
    assert payload["more_moisture"]["curated_view"]["plane_index"] == 72
    assert payload["more_moisture"]["curated_view"]["caption"].startswith(
        "This illustrative More Moisture view"
    )
    assert payload["changed_condition"] == {
        "label": "Surface moisture supply",
        "baseline_display": "0.0520 g/kg m/s",
        "more_moisture_display": "0.0780 g/kg m/s",
        "change_display": "+50%",
    }
    assert [item["metric_id"] for item in payload["material_responses"]] == [
        "mean_cloud_cover_final_three_hours",
        "mean_cloud_water_path_final_three_hours",
        "mean_coherent_cloud_top_final_three_hours",
    ]
    assert [item["change_display"] for item in payload["material_responses"]] == [
        "+2.199 percentage points",
        "+43.723%",
        "+109 m",
    ]
    assert len(payload["small_or_mixed_responses"]) == 4
    assert payload["small_or_mixed_responses"][3]["body"].endswith("saved frame.")
    assert payload["held_fixed_by_design"]["lead"] == "Only surface moisture supply changed."
    assert [group["title"] for group in payload["held_fixed_by_design"]["groups"]] == [
        "Initial atmosphere",
        "Forcing",
        "Model setup",
        "Execution and outputs",
    ]
    assert len(payload["explanation_paragraphs"]) == 4
    assert payload["provenance"]["comparison_source"] == "runtime_matched_pair_evidence"
    assert payload["caveats"] == [
        "one_deterministic_les_realization_per_control_state",
        "illustrative_views_are_not_direct_frame_matches",
        "individual_clouds_are_not_paired_one_to_one",
        "candidate_product_slice_not_supported_status",
    ]
    serialized = json.dumps(payload)
    assert "/machine/private" not in serialized
    assert "/Users/" not in serialized


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.update(evidence_state="baseline_invalid"),
        lambda payload: payload["baseline"].update(result_id="wrong-result"),
        lambda payload: payload["more_moisture"].update(surface_moisture_flux_g_g_m_s=7.9e-5),
        lambda payload: payload["baseline"]["gate"].update(valid=False),
        lambda payload: payload["matched_package_proof"].update(valid=False),
        lambda payload: payload["stage4_consistency"].update(passed=False),
        lambda payload: payload["scalar_metrics"]["domain_mean_cwp_final_three_hour_mean"].update(
            method="different method"
        ),
        lambda payload: payload["scalar_metrics"][
            "coherent_cloud_top_final_three_hour_mean"
        ].update(baseline=1700.0),
        lambda payload: payload["exact_time_pairing"]["domain_mean_cwp"].__setitem__(
            1, {"time_seconds": 10_920.0, "value": 0.5}
        ),
    ],
)
def test_story_rejects_conflicting_runtime_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    evidence = _evidence()
    mutate(evidence)
    settings = _install_valid_dependencies(tmp_path, monkeypatch, evidence=evidence)

    with pytest.raises(TradeCumulusComparisonStoryConflict):
        trade_cumulus_moisture_comparison_story(settings)


@pytest.mark.parametrize("target", ["top_level", "baseline", "more_moisture"])
def test_story_rejects_mismatched_implementation_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    evidence = _evidence()
    if target == "top_level":
        evidence["implementation_commit"] = "wrong"
    else:
        evidence[target]["app_commit"] = "wrong"
    settings = _install_valid_dependencies(tmp_path, monkeypatch, evidence=evidence)

    with pytest.raises(TradeCumulusComparisonStoryConflict, match="implementation commit"):
        trade_cumulus_moisture_comparison_story(settings)


def test_story_rejects_wrong_result_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _install_valid_dependencies(tmp_path, monkeypatch)
    original = comparison_story.get_result_metadata

    def wrong_hash(_settings: CloudChamberSettings, result_id: str) -> ResultMetadata:
        metadata = original(_settings, result_id)
        if result_id == BASELINE_RESULT_ID:
            metadata.run_configuration["fixed_assumptions_sha256"] = "wrong"
        return metadata

    monkeypatch.setattr(comparison_story, "get_result_metadata", wrong_hash)

    with pytest.raises(TradeCumulusComparisonStoryConflict, match="fixed assumptions hash"):
        trade_cumulus_moisture_comparison_story(settings)


@pytest.mark.parametrize(
    ("result_id", "hash_key"),
    [
        (BASELINE_RESULT_ID, "source_manifest_sha256"),
        (MORE_MOISTURE_RESULT_ID, "source_manifest_sha256"),
        (BASELINE_RESULT_ID, "executable_sha256"),
        (MORE_MOISTURE_RESULT_ID, "executable_sha256"),
    ],
)
def test_story_rejects_mismatched_persisted_cm1_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    result_id: str,
    hash_key: str,
) -> None:
    settings = _install_valid_dependencies(tmp_path, monkeypatch)
    original = comparison_story.get_result_metadata

    def wrong_provenance(_settings: CloudChamberSettings, requested_id: str) -> ResultMetadata:
        metadata = original(_settings, requested_id)
        if requested_id == result_id:
            metadata.run_configuration["cm1_provenance"][hash_key] = "wrong"
        return metadata

    monkeypatch.setattr(comparison_story, "get_result_metadata", wrong_provenance)

    with pytest.raises(TradeCumulusComparisonStoryConflict, match="CM1"):
        trade_cumulus_moisture_comparison_story(settings)


@pytest.mark.parametrize(
    "updates",
    [
        {"w_scale_id": "wrong-scale"},
        {"w_scale_breakpoints_m_s": [-1.0, 1.0]},
        {"time_seconds": 18_360.0},
        {"plane_index": 6},
        {"plane_coordinate": -2.64},
        {"w_finite_count": 0},
        {"cloud_mask": [[False, False]]},
        {"wind_vectors": []},
    ],
)
def test_story_rejects_conflicting_scale_or_curated_frame(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    updates: dict[str, Any],
) -> None:
    settings = _install_valid_dependencies(
        tmp_path,
        monkeypatch,
        frame_factory=lambda result_id: _frame(
            result_id,
            **(updates if result_id == BASELINE_RESULT_ID else {}),
        ),
    )

    with pytest.raises(TradeCumulusComparisonStoryConflict):
        trade_cumulus_moisture_comparison_story(settings)


def test_story_returns_not_found_for_missing_evidence(tmp_path: Path) -> None:
    with pytest.raises(TradeCumulusComparisonStoryNotFound, match="evidence is unavailable"):
        trade_cumulus_moisture_comparison_story(_settings(tmp_path))


def test_story_returns_not_found_for_missing_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _install_valid_dependencies(tmp_path, monkeypatch)

    def missing_result(_settings: CloudChamberSettings, _result_id: str) -> ResultMetadata:
        raise ResultIngestError("Result metadata not found at /machine/private/result.json")

    monkeypatch.setattr(comparison_story, "get_result_metadata", missing_result)

    with pytest.raises(TradeCumulusComparisonStoryNotFound) as caught:
        trade_cumulus_moisture_comparison_story(settings)
    assert "/machine/private" not in str(caught.value)


def test_story_returns_not_found_for_missing_model_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _install_valid_dependencies(tmp_path, monkeypatch)

    def missing_frame(*_args: object, **_kwargs: object) -> SimpleNamespace:
        raise TradeCumulusUpdraftLensError(
            "Model-output file is unavailable: /machine/private/cm1out.nc"
        )

    monkeypatch.setattr(comparison_story, "trade_cumulus_updraft_lens_frame", missing_frame)

    with pytest.raises(TradeCumulusComparisonStoryNotFound) as caught:
        trade_cumulus_moisture_comparison_story(settings)
    assert "/machine/private" not in str(caught.value)
