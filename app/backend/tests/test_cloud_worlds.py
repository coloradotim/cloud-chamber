from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from cloud_chamber.cloud_worlds import (
    MORE_MOISTURE_SIMULATION_ID,
    REFERENCE_SIMULATION_ID,
    configuration_differences,
    list_cloud_world_summaries,
    trade_cumulus_world_detail,
)
from cloud_chamber.result_ingest import ResultMetadata
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.trade_cumulus_comparison_story import (
    BASELINE_RESULT_ID,
    BASELINE_RUN_ID,
    MORE_MOISTURE_RESULT_ID,
    MORE_MOISTURE_RUN_ID,
    TradeCumulusComparisonStoryConflict,
    TradeCumulusComparisonStoryNotFound,
)


def _settings(tmp_path: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=tmp_path,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "cache",
        log_dir=tmp_path / "logs",
    )


def _metadata(
    result_id: str,
    run_id: str,
    *,
    control_state: str | None = None,
    moisture: float = 5.2e-5,
    configuration_updates: dict[str, Any] | None = None,
    controls_updates: dict[str, str | float | bool] | None = None,
) -> ResultMetadata:
    now = datetime(2026, 7, 20, tzinfo=UTC)
    controls: dict[str, str | float | bool] = {
        "surface_moisture_flux_g_g_m_s": moisture,
    }
    if control_state is not None:
        controls.update(
            {
                "control_id": "surface_moisture_supply",
                "control_state": control_state,
            }
        )
    controls.update(controls_updates or {})
    configuration: dict[str, Any] = {
        "case_id": "bomex_trade_cumulus_baseline_v0",
        "product_slice_id": "trade_cumulus_v1",
        "comparison_group_id": "trade_cumulus_moisture_v1",
        "surface_moisture_flux_g_g_m_s": moisture,
        "domain": {"nx": 64, "ny": 64, "nz": 75, "dx_m": 100.0, "dy_m": 100.0},
        "duration_seconds": 21_600,
        "output_cadence_seconds": 120,
        "fixed_assumptions_sha256": (
            "71d746b110fb1310ebb6dafbef4cfa4bd44c379fc6964ed1787deaf45e422535"
        ),
        "cm1_provenance": {
            "source_manifest_sha256": (
                "fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e"
            ),
            "executable_sha256": (
                "5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1"
            ),
            "source_tree_path": "/machine/private/cm1",
        },
        "case_manifest_path": f"/machine/private/{run_id}/case_manifest.json",
    }
    if control_state is not None:
        configuration.update(
            {
                "control_id": "surface_moisture_supply",
                "control_state": control_state,
                "recipe_candidate_id": "canonical_bomex_baseline",
            }
        )
    configuration.update(configuration_updates or {})
    return ResultMetadata(
        result_id=result_id,
        run_id=run_id,
        scenario_id="bomex_trade_cumulus_baseline_v0",
        physical_question="How does this Trade Cumulus Simulation respond?",
        controls=controls,
        run_configuration=configuration,
        source_lifecycle_state="completed",
        source_product_state="completed_cm1_result",
        source_model="CM1",
        created_at=now,
        updated_at=now,
    )


def _write_metadata(settings: CloudChamberSettings, metadata: ResultMetadata) -> Path:
    run_dir = settings.runtime_home / "runs" / metadata.run_id
    path = run_dir / "result_metadata.json"
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / "cm1out_000001.nc"
    output_path.write_bytes(b"CDF fixture")
    metadata.model_output_paths = [str(output_path)]
    metadata.netcdf_paths = [str(output_path)]
    metadata.model_output_file_count = 1
    path.write_text(metadata.to_json_text())
    return output_path


def _install_pair(
    settings: CloudChamberSettings, monkeypatch: pytest.MonkeyPatch
) -> tuple[ResultMetadata, ResultMetadata]:
    baseline = _metadata(
        BASELINE_RESULT_ID,
        BASELINE_RUN_ID,
        control_state="baseline",
        moisture=5.2e-5,
    )
    more_moisture = _metadata(
        MORE_MOISTURE_RESULT_ID,
        MORE_MOISTURE_RUN_ID,
        control_state="more_moisture",
        moisture=7.8e-5,
    )
    _write_metadata(settings, baseline)
    _write_metadata(settings, more_moisture)
    monkeypatch.setattr(
        "cloud_chamber.cloud_worlds.trade_cumulus_moisture_comparison_story",
        lambda _settings: SimpleNamespace(),
    )
    return baseline, more_moisture


def test_world_summary_and_detail_map_exact_known_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _install_pair(settings, monkeypatch)

    detail = trade_cumulus_world_detail(settings)
    summaries = list_cloud_world_summaries(settings)

    assert len(summaries) == 2
    summaries_by_id = {summary.world_id: summary for summary in summaries}
    trade_cumulus = summaries_by_id["trade_cumulus"]
    assert trade_cumulus.reference_available is True
    assert trade_cumulus.simulation_count == 2
    assert trade_cumulus.saved_view_count == 0
    assert trade_cumulus.saved_comparison_count == 1
    assert summaries_by_id["mountain_waves"].availability_state == "unavailable"
    assert detail.reference_simulation.simulation_id == REFERENCE_SIMULATION_ID
    assert detail.reference_simulation.display_name == "Canonical BOMEX Baseline"
    assert detail.simulations[1].simulation_id == MORE_MOISTURE_SIMULATION_ID
    assert detail.simulations[1].parent_simulation_id == REFERENCE_SIMULATION_ID
    assert detail.featured_comparison.open_available is True


def test_missing_baseline_is_bounded_and_keeps_lab_available(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    detail = trade_cumulus_world_detail(settings)

    assert detail.availability_state == "partial"
    assert detail.reference_simulation.technical_state == "missing"
    assert detail.reference_simulation.explore_available is False
    assert detail.capabilities.lab is True


def test_missing_more_moisture_does_not_disable_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    baseline, _ = _install_pair(settings, monkeypatch)
    more_path = settings.runtime_home / "runs" / MORE_MOISTURE_RUN_ID
    for path in more_path.iterdir():
        path.unlink()
    more_path.rmdir()

    detail = trade_cumulus_world_detail(settings)

    assert detail.availability_state == "partial"
    assert detail.reference_simulation.explore_available is True
    assert detail.simulations[1].technical_state == "missing"
    assert baseline.result_id == detail.reference_simulation.result_id


def test_missing_comparison_keeps_both_simulations_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _install_pair(settings, monkeypatch)

    def missing_story(_settings: CloudChamberSettings) -> None:
        raise TradeCumulusComparisonStoryNotFound("missing")

    monkeypatch.setattr(
        "cloud_chamber.cloud_worlds.trade_cumulus_moisture_comparison_story",
        missing_story,
    )

    detail = trade_cumulus_world_detail(settings)

    assert all(record.explore_available for record in detail.simulations[:2])
    assert detail.featured_comparison.availability_state == "missing"
    assert detail.capabilities.featured_comparison is False


def test_stale_known_metadata_without_model_output_disables_explore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _install_pair(settings, monkeypatch)
    output_path = settings.runtime_home / "runs" / BASELINE_RUN_ID / "cm1out_000001.nc"
    output_path.unlink()

    detail = trade_cumulus_world_detail(settings)
    summary = list_cloud_world_summaries(settings)[0]

    assert detail.reference_simulation.technical_state == "missing"
    assert detail.reference_simulation.explore_available is False
    assert detail.featured_comparison.availability_state == "missing"
    assert summary.reference_available is False


def test_world_comparison_fails_closed_when_story_validation_conflicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _install_pair(settings, monkeypatch)

    def conflicting_story(_settings: CloudChamberSettings) -> None:
        raise TradeCumulusComparisonStoryConflict("curated view mismatch")

    monkeypatch.setattr(
        "cloud_chamber.cloud_worlds.trade_cumulus_moisture_comparison_story",
        conflicting_story,
    )

    detail = trade_cumulus_world_detail(settings)

    assert all(record.explore_available for record in detail.simulations[:2])
    assert detail.featured_comparison.availability_state == "conflict"
    assert detail.featured_comparison.open_available is False


def test_contradictory_known_identity_returns_controlled_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _install_pair(settings, monkeypatch)
    path = settings.runtime_home / "runs" / BASELINE_RUN_ID / "result_metadata.json"
    payload = path.read_text().replace(
        '"scenario_id": "bomex_trade_cumulus_baseline_v0"',
        '"scenario_id": "contradictory_case"',
    )
    path.write_text(payload)

    detail = trade_cumulus_world_detail(settings)

    assert detail.availability_state == "conflict"
    assert detail.reference_simulation.technical_state == "conflict"
    assert "/" not in detail.reference_simulation.technical_state_message


def test_optional_valid_lineage_creates_retained_simulation_with_all_material_differences(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _install_pair(settings, monkeypatch)
    ordinary = _metadata(
        "result-ordinary-related",
        "ordinary-related",
        moisture=6.0e-5,
        controls_updates={},
        configuration_updates={
            "cloud_world_id": "trade_cumulus",
            "simulation_id": "trade_cumulus_two_change_fixture",
            "simulation_display_name": "Two-change investigation",
            "source_recipe_id": "canonical_bomex_baseline",
            "parent_simulation_id": REFERENCE_SIMULATION_ID,
            "reference_simulation_id": REFERENCE_SIMULATION_ID,
            "domain": {"nx": 64, "ny": 64, "nz": 75, "dx_m": 200.0, "dy_m": 100.0},
        },
    )
    _write_metadata(settings, ordinary)

    detail = trade_cumulus_world_detail(settings)
    retained = next(
        record
        for record in detail.simulations
        if record.simulation_id == "trade_cumulus_two_change_fixture"
    )
    differences = retained.configuration_difference_from_reference or []

    assert retained.lineage_state == "valid"
    assert retained.parent_simulation_id == REFERENCE_SIMULATION_ID
    assert [difference.label for difference in differences if difference.material] == [
        "Surface moisture supply",
        "Grid spacing x",
    ]
    assert not any("control" in difference.label.lower() for difference in differences)


def test_unlineaged_and_colliding_results_remain_lab_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _install_pair(settings, monkeypatch)
    _write_metadata(settings, _metadata("result-unlineaged", "unlineaged"))
    _write_metadata(
        settings,
        _metadata(
            "result-collision",
            "collision",
            configuration_updates={
                "cloud_world_id": "trade_cumulus",
                "simulation_id": REFERENCE_SIMULATION_ID,
                "simulation_display_name": "Collision",
                "parent_simulation_id": REFERENCE_SIMULATION_ID,
            },
        ),
    )

    detail = trade_cumulus_world_detail(settings)
    by_result = {record.result_id: record for record in detail.lab_history}

    assert by_result["result-unlineaged"].lineage_state == "unlineaged"
    assert by_result["result-collision"].lineage_state == "invalid"
    assert all(record.result_id != "result-collision" for record in detail.simulations)


def test_stale_ordinary_outputs_disable_retained_and_lab_history_explore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _install_pair(settings, monkeypatch)
    retained = _metadata(
        "result-retained-stale",
        "retained-stale",
        configuration_updates={
            "cloud_world_id": "trade_cumulus",
            "simulation_id": "trade_cumulus_retained_stale",
            "simulation_display_name": "Retained stale output",
            "parent_simulation_id": REFERENCE_SIMULATION_ID,
        },
    )
    history = _metadata("result-history-stale", "history-stale")
    _write_metadata(settings, retained).unlink()
    _write_metadata(settings, history).unlink()

    detail = trade_cumulus_world_detail(settings)
    retained_record = next(
        record
        for record in detail.simulations
        if record.simulation_id == "trade_cumulus_retained_stale"
    )
    history_record = next(
        record for record in detail.lab_history if record.result_id == "result-history-stale"
    )

    assert retained_record.technical_state == "missing"
    assert retained_record.explore_available is False
    assert history_record.technical_state == "missing"
    assert history_record.explore_available is False


def test_impossible_and_cyclic_lineage_remains_invalid_lab_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _install_pair(settings, monkeypatch)
    records = [
        _metadata(
            "result-self",
            "self",
            configuration_updates={
                "cloud_world_id": "trade_cumulus",
                "simulation_id": "trade_cumulus_self",
                "simulation_display_name": "Self relationship",
                "parent_simulation_id": "trade_cumulus_self",
                "reference_simulation_id": "trade_cumulus_self",
            },
        ),
        _metadata(
            "result-cycle-a",
            "cycle-a",
            configuration_updates={
                "cloud_world_id": "trade_cumulus",
                "simulation_id": "trade_cumulus_cycle_a",
                "simulation_display_name": "Cycle A",
                "parent_simulation_id": "trade_cumulus_cycle_b",
            },
        ),
        _metadata(
            "result-cycle-b",
            "cycle-b",
            configuration_updates={
                "cloud_world_id": "trade_cumulus",
                "simulation_id": "trade_cumulus_cycle_b",
                "simulation_display_name": "Cycle B",
                "reference_simulation_id": "trade_cumulus_cycle_a",
            },
        ),
        _metadata("result-unmapped-parent", "unmapped-parent"),
        _metadata(
            "result-lost-relationship",
            "lost-relationship",
            configuration_updates={
                "cloud_world_id": "trade_cumulus",
                "simulation_id": "trade_cumulus_lost_relationship",
                "simulation_display_name": "Lost relationship",
                "parent_result_id": "result-unmapped-parent",
            },
        ),
    ]
    for record in records:
        _write_metadata(settings, record)

    detail = trade_cumulus_world_detail(settings)
    history_by_result = {record.result_id: record for record in detail.lab_history}

    for result_id in (
        "result-self",
        "result-cycle-a",
        "result-cycle-b",
        "result-lost-relationship",
    ):
        assert history_by_result[result_id].lineage_state == "invalid"
        assert all(record.result_id != result_id for record in detail.simulations)


def test_known_pair_reports_only_surface_moisture_as_material_atmospheric_difference() -> None:
    baseline = _metadata(
        BASELINE_RESULT_ID,
        BASELINE_RUN_ID,
        control_state="baseline",
        moisture=5.2e-5,
    )
    more_moisture = _metadata(
        MORE_MOISTURE_RESULT_ID,
        MORE_MOISTURE_RUN_ID,
        control_state="more_moisture",
        moisture=7.8e-5,
    )

    differences = configuration_differences(baseline, more_moisture)
    material = [difference for difference in differences if difference.material]

    assert [(item.label, item.category) for item in material] == [
        ("Surface moisture supply", "atmospheric")
    ]


def test_configuration_differences_exclude_private_paths_and_sort_deterministically() -> None:
    baseline = _metadata("left", "left")
    variation = _metadata(
        "right",
        "right",
        configuration_updates={
            "duration_seconds": 25_200,
            "output_cadence_seconds": 300,
            "case_manifest_path": "/different/private/path.json",
            "cm1_provenance": {
                "source_manifest_sha256": "different",
                "executable_sha256": "different",
                "source_tree_path": "/different/private/cm1",
            },
        },
    )

    first = configuration_differences(baseline, variation)
    second = configuration_differences(baseline, variation)

    assert first == second
    assert [item.category for item in first] == ["numerical", "output"]
    assert not any("path" in item.path or "sha256" in item.path for item in first)


def test_configuration_differences_recurse_profiles_and_classify_current_forcing_keys() -> None:
    baseline = _metadata(
        "left",
        "left",
        configuration_updates={
            "initial_profiles": [
                {"height_m": 0.0, "temperature_k": 299.0},
                {"height_m": 500.0, "temperature_k": 296.0},
            ],
            "surface_heat_flux_k_m_s": 8.0e-3,
            "surface_forcing_patch": {
                "surface_patch_heat_flux_perturbation_k_m_s": 4.0e-2,
                "surface_patch_moisture_flux_perturbation_g_g_m_s": 5.0e-5,
            },
        },
    )
    variation = _metadata(
        "right",
        "right",
        configuration_updates={
            "initial_profiles": [
                {"height_m": 0.0, "temperature_k": 299.0},
                {"height_m": 500.0, "temperature_k": 297.0},
            ],
            "surface_heat_flux_k_m_s": 1.2e-2,
            "surface_forcing_patch": {
                "surface_patch_heat_flux_perturbation_k_m_s": 4.5e-2,
                "surface_patch_moisture_flux_perturbation_g_g_m_s": 6.0e-5,
            },
        },
    )

    differences = configuration_differences(baseline, variation)
    material = [difference for difference in differences if difference.material]

    assert all(difference.category == "atmospheric" for difference in material)
    assert {difference.label for difference in material} == {
        "Surface sensible heat supply",
        "Surface-patch heat-flux perturbation",
        "Surface-patch moisture-flux perturbation",
        "Temperature k",
    }
    assert any(
        difference.path == "run_configuration.initial_profiles[1].temperature_k"
        for difference in material
    )
