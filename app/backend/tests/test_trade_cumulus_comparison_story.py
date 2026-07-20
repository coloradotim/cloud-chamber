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
        "model_output_count": 181,
        "expected_model_output_count": 181,
        "diagnostic_output_count": 361,
        "expected_diagnostic_output_count": 361,
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
        {"time_seconds": 10_800.0, "value": 0.007},
        {"time_seconds": 10_920.0, "value": 0.009},
    ]
    cover_values = [
        {"time_seconds": 10_800.0, "value": 10.0},
        {"time_seconds": 10_920.0, "value": 12.0},
    ]
    if control_state == "more_moisture":
        cwp_values = [
            {"time_seconds": 10_800.0, "value": 0.008},
            {"time_seconds": 10_920.0, "value": 0.008},
        ]
        cover_values = [
            {"time_seconds": 10_800.0, "value": 11.0},
            {"time_seconds": 10_920.0, "value": 11.0},
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
        "app_commit": "49da1defc9914d3cc903ed9589c1312ddd843726",
        "surface_moisture_flux_g_g_m_s": control_value,
        "duration_seconds": 21_600,
        "output_cadence_seconds": 120,
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
        "evidence_version": "trade_cumulus_moisture_comparison_evidence_v1",
        "evidence_state": "matched_runs_valid",
        "implementation_commit": "49da1defc9914d3cc903ed9589c1312ddd843726",
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
                "time >= 10800 s",
                10.596239697802197,
                12.710873111263735,
                2.1146334134615383,
                19.956451286206196,
            ),
            "domain_mean_cwp_final_three_hour_mean": _metric(
                "kg/m^2",
                "time mean of horizontal domain-mean cwp",
                "time >= 10800 s",
                0.006351999299305916,
                0.009071426778155891,
                0.0027194274788499753,
                42.81215017053178,
            ),
            "coherent_cloud_top_final_three_hour_mean": _metric(
                "m",
                "mean supported coherent cloud-object top",
                "time >= 10800 s",
                1668.3517340775375,
                1805.0550379595913,
                136.7033038820539,
                8.193913854600911,
            ),
            "first_isolated_cloud_liquid_time": _metric(
                "s",
                "first model frame with any finite ql >= 1e-6 kg/kg",
                "full run",
                1080.0,
                1080.0,
                0.0,
                0.0,
            ),
            "time_mean_cloud_fraction_profile_peak_height": _metric(
                "m",
                "height of first maximum in final-three-hour time-mean cloud-fraction profile",
                "time >= 10800 s",
                620.0000047683716,
                620.0000047683716,
                0.0,
                0.0,
            ),
            "cloudy_scalar_cells_with_positive_centered_w": _metric(
                "%",
                "pooled fraction of cloudy scalar cells with centered w > 0",
                "time >= 10800 s",
                90.3791231845806,
                90.45123498042852,
                0.07211179584791694,
                0.0797881117972826,
            ),
        },
        "exact_time_pairing": {
            "domain_mean_cwp": [
                {"time_seconds": 10_800.0, "value": 0.001},
                {"time_seconds": 10_920.0, "value": -0.001},
            ],
            "total_cloud_cover_percent": [
                {"time_seconds": 10_800.0, "value": 1.0},
                {"time_seconds": 10_920.0, "value": -1.0},
            ],
        },
        "stage4_consistency": {
            "preserved_result_id": "result-bomex-370-full-20260719",
            "new_baseline_result_id": BASELINE_RESULT_ID,
            "common_times_seconds": [10_800.0],
            "absolute_tolerance": 1e-10,
            "relative_tolerance": 1e-6,
            "field_differences": [],
            "first_failure": None,
            "passed": True,
        },
        "lens_preparation": {
            "baseline_result_id": BASELINE_RESULT_ID,
            "more_moisture_result_id": MORE_MOISTURE_RESULT_ID,
            "baseline_default_time_index": 152,
            "baseline_default_time_seconds": 18_240.0,
            "baseline_default_plane_index": 5,
            "baseline_default_plane_coordinate": -2.6500000953674316,
            "baseline_default_plane_units": "km",
            "inherited_variant_time_index": 152,
            "inherited_variant_plane_index": 5,
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
                "71d746b110fb1310ebb6dafbef4cfa4bd44c379fc6964ed1787deaf45e422535"
            ),
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
            "time_index": 152,
            "time_seconds": 18_240.0,
            "plane_index": 5,
            "plane_coordinate": -2.6500000953674316,
        }
    else:
        values = {
            "result_id": result_id,
            "time_index": 169,
            "time_seconds": 20_280.0,
            "plane_index": 51,
            "plane_coordinate": 1.9500000476837158,
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
        / "trade-cumulus-moisture-20260720T162342Z"
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
    assert payload["baseline"]["control_display"] == "5.2 × 10⁻⁵ g/g m/s"
    assert payload["baseline"]["curated_view"] == {
        "time_index": 152,
        "time_seconds": 18_240.0,
        "orientation": "vertical_x",
        "plane_dimension": "y",
        "plane_index": 5,
        "plane_coordinate": -2.6500000953674316,
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
            "This illustrative Baseline view shows one concentrated active cloud reaching about "
            "2 km, with a strong rising core bordered by sinking air."
        ),
    }
    assert payload["more_moisture"]["curated_view"]["time_index"] == 169
    assert payload["more_moisture"]["curated_view"]["plane_index"] == 51
    assert payload["more_moisture"]["curated_view"]["caption"].startswith(
        "This illustrative More Moisture view"
    )
    assert payload["changed_condition"] == {
        "label": "Surface moisture supply",
        "baseline_display": "5.2 × 10⁻⁵ g/g m/s",
        "more_moisture_display": "7.8 × 10⁻⁵ g/g m/s",
        "change_display": "+50%",
    }
    assert [item["metric_id"] for item in payload["material_responses"]] == [
        "mean_cloud_cover_final_three_hours",
        "mean_cloud_water_path_final_three_hours",
        "mean_coherent_cloud_top_final_three_hours",
    ]
    assert [item["change_display"] for item in payload["material_responses"]] == [
        "+2.115 percentage points",
        "+42.812%",
        "+137 m",
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
