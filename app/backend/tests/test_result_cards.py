import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import xarray as xr

from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.result_cards import (
    RESULT_CARD_FILENAME,
    ResultCard,
    ResultCardUpdate,
    get_result_card,
    list_result_cards,
    save_result_card,
    update_result_card,
)
from cloud_chamber.result_ingest import ingest_completed_run
from cloud_chamber.run_manifest import (
    ExecutionMetadata,
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=tmp_path / "cm1r21.1",
        cm1_run_dir=tmp_path / "cm1r21.1" / "run",
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def create_completed_result(
    tmp_path: Path,
    *,
    run_id: str = "run-card",
    include_diagnostics_fields: bool = True,
    observed_sounding: dict[str, object] | None = None,
    package_updates: dict[str, object] | None = None,
) -> tuple[CloudChamberSettings, str, Path]:
    settings = fake_settings(tmp_path)
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=settings.runtime_home,
        run_id=run_id,
    )
    netcdf_path = package.package_dir / "cm1out_000001.nc"
    write_result_netcdf(netcdf_path, include_diagnostics_fields=include_diagnostics_fields)
    manifest = load_run_manifest(package.manifest_path)
    finished_at = datetime(2026, 5, 22, 15, 32, 21, tzinfo=UTC)
    update_payload = {
        "lifecycle_state": LifecycleState.COMPLETED,
        "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        "execution": ExecutionMetadata(finished_at=finished_at, exit_code=0),
        "outputs": OutputMetadata(
            netcdf_paths=[str(netcdf_path)],
            runtime_warnings=["CM1 stderr reported floating-point exception flags: TEST"],
        ),
        "observed_sounding": observed_sounding,
    }
    update_payload.update(package_updates or {})
    write_run_manifest(
        package.manifest_path,
        manifest.model_copy(update=update_payload),
    )
    result = ingest_completed_run(package.manifest_path)
    return settings, result.result_id, package.package_dir


def write_result_netcdf(path: Path, *, include_diagnostics_fields: bool) -> None:
    data_vars: dict[str, Any] = {}
    if include_diagnostics_fields:
        data_vars["qc"] = (
            ("time", "z", "y", "x"),
            [[[[2e-6 for _x in range(4)] for _y in range(3)] for _z in range(2)]],
            {"units": "kg/kg"},
        )
        data_vars["w"] = (
            ("time", "z", "y", "x"),
            [[[[1.0, 2.0, 3.0, 4.0] for _y in range(3)] for _z in range(2)]],
            {"units": "m/s"},
        )
        data_vars["qr"] = (
            ("time", "z", "y", "x"),
            [[[[2e-7 for _x in range(4)] for _y in range(3)] for _z in range(2)]],
            {"units": "kg/kg"},
        )
        data_vars["rain"] = (
            ("time", "y", "x"),
            [[[3.5 for _x in range(4)] for _y in range(3)]],
            {"units": "mm"},
        )
    else:
        data_vars["temperature"] = (
            ("time", "z", "y", "x"),
            [[[[300.0 for _x in range(4)] for _y in range(3)] for _z in range(2)]],
            {"units": "K"},
        )
    xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": [1800.0],
            "z": [0.54, 1.94],
            "y": [0.0, 100.0, 200.0],
            "x": [0.0, 100.0, 200.0, 300.0],
        },
    ).to_netcdf(path, engine="scipy")


def test_result_card_created_from_ingested_metadata(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_completed_result(tmp_path)

    card = get_result_card(settings, result_id)

    assert card.result_id == result_id
    assert card.run_id == "run-card"
    assert card.name == "baseline-shallow-cumulus"
    assert card.scenario_id == "baseline-shallow-cumulus"
    assert card.run_configuration["duration"] == "short_6h"
    assert card.run_configuration["domain_size"] == "local_6km"
    assert card.pre_run_validation_report is not None
    assert card.pre_run_validation_report["selected_run_recipe"]["recipe_id"] == (
        "generated_reference_lower_atmosphere_v1"
    )
    assert card.physical_question
    assert card.diagnostics_summary == (
        "cloud formed; rain water aloft detected; surface rain reached ground; "
        "reflectivity unavailable"
    )
    assert card.thermal_fate_label == "Fair-weather cumulus"
    assert card.thermal_fate_confidence == "candidate"
    assert card.main_limiting_factor == "unknown"
    assert card.first_cloud_time_seconds == 1800.0
    assert card.max_qc_kg_kg == 2e-6
    assert card.time_of_max_qc_seconds == 1800.0
    assert card.max_w_m_s == 4.0
    assert card.time_of_max_w_seconds == 1800.0
    assert card.min_w_m_s == 1.0
    assert card.time_of_min_w_seconds == 1800.0
    assert card.rain_present is True
    assert card.first_rain_time_seconds == 1800.0
    assert card.surface_rain_present is True
    assert card.max_surface_rain == 3.5
    assert card.surface_rain_units == "mm"
    assert card.reflectivity_available is False
    assert card.max_dbz is None
    assert card.field_quality["qc"].quality_state == "trusted"
    assert card.field_quality["qr"].quality_state == "trusted"
    assert card.field_quality["dbz"].quality_state == "unavailable"
    assert card.science_summary is not None
    assert card.science_summary.first_cloud_time_seconds == 1800.0
    assert card.science_summary.max_qc_kg_kg == 2e-6
    assert card.science_summary.max_updraft_w_m_s == 4.0
    assert card.science_summary.rain_onset_time_seconds == 1800.0
    assert card.science_summary.default_explore_time_index == 0
    assert card.interesting_times
    assert {record.key for record in card.interesting_times} >= {
        "first_cloud",
        "max_qc",
        "max_updraft_w",
        "rain_onset",
        "latest_output",
        "field_default_time",
    }
    assert card.default_time_by_field["qc"].time_index == 0
    assert card.input_source == "generated_reference"
    assert card.input_source_label == "Generated reference"
    assert card.observed_sounding is None
    assert card.output_file_summary.netcdf_count == 1
    assert card.output_file_summary.model_output_count == 1
    assert card.output_file_summary.time_steps == 1


def test_result_card_preserves_observed_surface_forced_recipe_metadata(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_completed_result(
        tmp_path,
        run_id="run-observed-recipe-card",
        observed_sounding={
            "station_id": "USM00072558",
            "station_name": "Valley, Nebraska",
            "valid_time_utc": "2026-06-30T00:00:00Z",
        },
        package_updates={
            "run_recipe": "observed_surface_forced_evolution",
            "run_recipe_display_name": "Observed Surface-Forced Evolution",
            "recipe_id": "observed_surface_forced_evolution_v0",
            "recipe_display_name": "Observed Surface-Forced Evolution v0",
            "assumption_set_id": "observed_surface_forced_evolution_v0_assumptions",
            "assumption_mode": "observed_surface_forced_evolution",
            "recipe_assumptions": {
                "trigger": {"mode": "none"},
                "radiation": {"mode": "disabled"},
                "large_scale_forcing": {"mode": "none"},
            },
            "required_output_fields": ["qv", "qc", "w", "qr", "rain", "dbz"],
            "recipe_caveats": ["No artificial atmospheric trigger is applied."],
            "input_source": "observed_sounding",
        },
    )

    card = get_result_card(settings, result_id)

    assert card.name == "Observed Surface-Forced Evolution v0 — Valley, Nebraska"
    assert card.scenario_name == "Observed Surface-Forced Evolution v0"
    assert card.recipe_id == "observed_surface_forced_evolution_v0"
    assert card.recipe_display_name == "Observed Surface-Forced Evolution v0"
    assert card.assumption_set_id == "observed_surface_forced_evolution_v0_assumptions"
    assert card.assumption_mode == "observed_surface_forced_evolution"
    assert card.recipe_assumptions["trigger"]["mode"] == "none"
    assert card.required_output_fields == ["qv", "qc", "w", "qr", "rain", "dbz"]
    assert card.missing_required_output_fields == ["qv", "dbz"]
    assert "recipe_id:observed_surface_forced_evolution_v0" in card.provenance_labels
    assert card.saved is False
    assert card.protected is False
    assert "source_model:CM1" in card.provenance_labels
    assert "CM1 stderr reported floating-point exception flags: TEST" in card.caveats
    assert "cloud_base_top_vertical_units_missing_assumed_meters" in card.caveats
    assert card.completed_at == datetime(2026, 5, 22, 15, 32, 21, tzinfo=UTC)


def test_result_card_exposes_observed_sounding_source(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_completed_result(
        tmp_path,
        observed_sounding={
            "source_type": "observed_sounding",
            "source_format": "igra_station_text",
            "station_id": "USM00072558",
            "station_name": "Valley, Nebraska",
            "station_elevation_m_msl": 351.5,
            "valid_time_utc": "2026-06-30T00:00:00Z",
        },
        package_updates={
            "run_recipe": "observed_surface_forced_evolution",
            "run_recipe_display_name": "Observed Surface-Forced Evolution",
            "recipe_id": "observed_surface_forced_evolution_v0",
            "recipe_display_name": "Observed Surface-Forced Evolution v0",
            "assumption_set_id": "observed_surface_forced_evolution_v0_assumptions",
            "assumption_mode": "observed_surface_forced_evolution",
            "recipe_assumptions": {"trigger": {"mode": "none"}},
            "required_output_fields": ["qv", "qc", "w", "qr", "rain", "dbz"],
            "input_source": "observed_sounding",
        },
    )

    card = get_result_card(settings, result_id)

    assert card.name == "Observed Surface-Forced Evolution v0 — Valley, Nebraska"
    assert card.scenario_id == "baseline-shallow-cumulus"
    assert card.scenario_name == "Observed Surface-Forced Evolution v0"
    assert card.input_source == "observed_sounding"
    assert card.input_source_label == "Observed sounding: USM00072558 · Valley, Nebraska"
    assert card.observed_sounding is not None
    assert card.observed_sounding["station_id"] == "USM00072558"


def test_result_card_preserves_deep_candidate_surface_forced_identity(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_completed_result(
        tmp_path,
        run_id="run-deep-card",
        observed_sounding={
            "source_type": "observed_sounding",
            "source_format": "igra_station_text",
            "station_id": "USM00072357",
            "station_name": "Norman, Oklahoma",
            "station_elevation_m_msl": 357.0,
            "valid_time_utc": "2026-06-30T00:00:00Z",
        },
        package_updates={
            "candidate_screening": {
                "candidate_id": "USM00072357-2025052000-supercell",
                "primary_story": "supercell_environment",
                "rank_score": 93.0,
            },
            "run_recipe": "observed_surface_forced_evolution",
            "run_recipe_display_name": "Observed Surface-Forced Evolution",
            "recipe_id": "observed_surface_forced_evolution_v0",
            "recipe_display_name": "Observed Surface-Forced Evolution v0",
            "assumption_set_id": "observed_surface_forced_evolution_v0_assumptions",
            "assumption_mode": "observed_surface_forced_evolution",
            "recipe_assumptions": {
                "trigger": {"mode": "none"},
                "surface_fluxes": {
                    "mode": "constant_uniform",
                    "sensible_heat_flux_k_m_s": 8.0e-3,
                    "moisture_flux_g_g_m_s": 5.2e-5,
                },
                "radiation": {"mode": "disabled"},
            },
            "required_output_fields": ["qc", "w", "qr", "rain", "dbz"],
            "input_source": "observed_sounding",
            "trigger_type": None,
            "trigger_parameters": {},
            "expected_outputs": ["qc", "qr", "w", "rain", "dbz"],
            "run_caveats": [
                "No artificial atmospheric trigger is applied.",
                "Surface heat/moisture fluxes are constant uniform lower-boundary proxy settings.",
            ],
            "manual_validation_status": "observed_surface_forced_evolution_v0_metadata_only",
        },
    )

    card = get_result_card(settings, result_id)

    assert card.name == "Observed Surface-Forced Evolution v0 — Norman, Oklahoma"
    assert card.scenario_name == "Observed Surface-Forced Evolution v0"
    assert card.run_recipe == "observed_surface_forced_evolution"
    assert card.run_recipe_display_name == "Observed Surface-Forced Evolution"
    assert card.recipe_id == "observed_surface_forced_evolution_v0"
    assert card.assumption_set_id == "observed_surface_forced_evolution_v0_assumptions"
    assert card.trigger_type is None
    assert card.trigger_parameters is not None
    assert card.trigger_parameters == {}
    assert "dbz" in card.expected_outputs
    assert card.run_caveats == [
        "No artificial atmospheric trigger is applied.",
        "Surface heat/moisture fluxes are constant uniform lower-boundary proxy settings.",
    ]
    assert card.manual_validation_status == "observed_surface_forced_evolution_v0_metadata_only"
    assert "run_recipe:observed_surface_forced_evolution" in card.provenance_labels
    assert card.candidate_screening is not None
    assert card.candidate_screening["primary_story"] == "supercell_environment"
    assert card.candidate_hypothesis_comparison is not None
    assert card.candidate_hypothesis_comparison.screened_as == "Supercell-like environment"
    assert card.candidate_hypothesis_comparison.ran_as == "Observed Surface-Forced Evolution v0"
    assert card.candidate_hypothesis_comparison.match_status == "partially_supported"


def test_list_get_and_result_card_serialization_round_trip(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_completed_result(tmp_path)

    listed = list_result_cards(settings)
    found = get_result_card(settings, result_id)
    round_tripped = ResultCard.model_validate_json(found.model_dump_json())

    assert [card.result_id for card in listed] == [result_id]
    assert found == listed[0]
    assert round_tripped == found


def test_update_name_tags_notes_and_saved_flags(tmp_path: Path) -> None:
    settings, result_id, run_dir = create_completed_result(tmp_path)

    updated = update_result_card(
        settings,
        result_id,
        ResultCardUpdate(
            name="Quick-look baseline",
            tags=["golden-path", "quick-look"],
            notes="Useful first notebook entry.",
            saved=True,
        ),
    )

    assert updated.name == "Quick-look baseline"
    assert updated.tags == ["golden-path", "quick-look"]
    assert updated.notes == "Useful first notebook entry."
    assert updated.saved is True
    assert updated.protected is True
    assert updated.status == "saved_result_notebook_entry"
    assert (run_dir / RESULT_CARD_FILENAME).exists()


def test_save_result_card_marks_saved_and_protected(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_completed_result(tmp_path)

    saved = save_result_card(settings, result_id)

    assert saved.saved is True
    assert saved.protected is True
    assert saved.status == "saved_result_notebook_entry"


def test_result_card_handles_missing_diagnostics_gracefully(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_completed_result(
        tmp_path,
        run_id="run-missing-diagnostics",
        include_diagnostics_fields=False,
    )

    card = get_result_card(settings, result_id)

    assert card.diagnostics_summary == (
        "cloud unavailable; rain water aloft unavailable; surface rain unavailable; "
        "reflectivity unavailable"
    )
    assert card.first_cloud_time_seconds is None
    assert card.max_qc_kg_kg is None
    assert card.time_of_max_qc_seconds is None
    assert card.max_w_m_s is None
    assert card.time_of_max_w_seconds is None
    assert card.min_w_m_s is None
    assert card.time_of_min_w_seconds is None
    assert card.rain_present is None
    assert card.first_rain_time_seconds is None
    assert card.field_quality["qc"].quality_state == "unavailable"
    assert card.field_quality["w"].quality_state == "unavailable"
    assert card.field_quality["qr"].quality_state == "unavailable"
    assert card.field_quality["surface_rain"].quality_state == "unavailable"
    assert card.field_quality["dbz"].quality_state == "unavailable"
    assert card.science_summary is not None
    assert card.science_summary.interesting_time_support_state == "fallback"
    assert card.default_time_by_field["qc"].support_state == "fallback"
    assert any(
        record.key == "first_cloud" and record.support_state == "unsupported_missing_fields"
        for record in card.interesting_times
    )
    assert "missing_qc_field" in card.caveats
    assert "missing_w_field" in card.caveats
