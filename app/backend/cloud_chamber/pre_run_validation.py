"""Pre-run validation for candidate hypotheses, recipes, and run shape."""

from __future__ import annotations

from typing import Any

from cloud_chamber.cm1_input_contract import (
    CM1InputContract,
    RunRecipe,
    assumption_mode_for_run_recipe,
    assumption_set_id_for_run_recipe,
    has_complete_rendered_observed_wind_profile,
    recipe_caveats_for_run_recipe,
    recipe_display_name_for_run_recipe,
    recipe_id_for_run_recipe,
    required_output_fields_for_run_recipe,
)
from cloud_chamber.observed_sounding import ObservedSoundingRecord
from cloud_chamber.run_configuration import resolve_run_configuration
from cloud_chamber.scenario_schema import ScenarioTemplate

DEEP_CONVECTION_STORIES = {
    "severe_thunderstorm_environment",
    "supercell_environment",
    "high_cape_pulse_storm",
    "dry_microburst_inverted_v",
    "squall_line_cold_pool_candidate",
    "elevated_convection",
}

NORMAL_EVOLUTION_STORIES = {
    "shallow_cumulus_candidate",
    "dry_failed_candidate",
    "capped_suppressed_candidate",
    "humid_rainy_candidate",
}

REVIEW_OR_BLOCKED_STORIES = {"needs_review", "poor_or_incomplete_candidate"}


def build_pre_run_validation_report(
    *,
    scenario: ScenarioTemplate,
    contract: CM1InputContract,
    candidate_screening: dict[str, Any] | None,
) -> dict[str, Any]:
    story = _selected_story(candidate_screening)
    required_outputs = _required_outputs_for_story(story, contract.run_recipe)
    missing_outputs = [
        field for field in required_outputs if field not in set(contract.expected_outputs)
    ]
    alignment = _hypothesis_recipe_alignment(story, contract.run_recipe)
    input_validation = _input_validation_payload(contract.observed_sounding, contract)
    blocking_errors = list(alignment["blocking_errors"])
    if input_validation["observed_wind_profile"] == "missing_required":
        blocking_errors.append(
            "Observed-sounding runs require a complete finite observed u/v wind profile "
            "for every input_sounding level."
        )
    caveats = _dedupe(
        [
            *contract.run_configuration.caveats,
            *contract.run_caveats,
            *alignment["caveats"],
            *[f"missing_required_output_field:{field}" for field in missing_outputs],
        ]
    )
    if alignment["status"] == "partial" and missing_outputs:
        caveats.append("output_fields_support_partial_comparison_only")

    status = "blocked" if blocking_errors else ("caveated" if caveats else "valid")
    return {
        "status": status,
        "selected_candidate": _selected_candidate_payload(
            candidate_screening,
            contract.observed_sounding,
        ),
        "selected_hypothesis": _selected_hypothesis_payload(candidate_screening, story),
        "selected_run_recipe": _selected_run_recipe_payload(contract),
        "hypothesis_recipe_alignment": {
            "status": alignment["status"],
            "reasons": alignment["reasons"],
            "missing_assumptions": alignment["missing_assumptions"],
            "missing_outputs": missing_outputs,
        },
        "input_validation": input_validation,
        "run_shape_validation": _run_shape_validation_payload(contract),
        "forcing_validation": _forcing_validation_payload(contract),
        "output_validation": {
            "required_fields": required_outputs,
            "enabled_fields": list(contract.expected_outputs),
            "missing_fields": missing_outputs,
        },
        "runtime_file_validation": {
            "required_files": list(scenario.cm1_template.runtime_files_needed),
            "staging_status": "checked_at_launch",
            "caveats": ["external_runtime_files_are_not_committed"],
        },
        "blocking_errors": blocking_errors,
        "caveats": caveats,
    }


def blocked_pre_run_validation_report(
    *,
    scenario: ScenarioTemplate,
    controls: dict[str, str | float | bool],
    run_recipe: str | None,
    run_configuration: dict[str, object] | None,
    observed_sounding: dict[str, object] | ObservedSoundingRecord | None,
    candidate_screening: dict[str, Any] | None,
    error_message: str,
) -> dict[str, Any]:
    resolved_recipe = _run_recipe_value(run_recipe, observed_sounding)
    run_shape = _run_shape_from_payload(run_configuration, resolved_recipe)
    story = _selected_story(candidate_screening)
    return {
        "status": "blocked",
        "selected_candidate": _selected_candidate_payload(candidate_screening, observed_sounding),
        "selected_hypothesis": _selected_hypothesis_payload(candidate_screening, story),
        "selected_run_recipe": {
            "run_recipe": resolved_recipe,
            "recipe_id": recipe_id_for_run_recipe(resolved_recipe),
            "display_name": _run_recipe_display_name(resolved_recipe),
            "recipe_display_name": recipe_display_name_for_run_recipe(resolved_recipe),
            "assumption_set_id": assumption_set_id_for_run_recipe(resolved_recipe),
            "assumption_mode": assumption_mode_for_run_recipe(resolved_recipe),
            "required_fields": list(required_output_fields_for_run_recipe(resolved_recipe)),
            "caveats": list(recipe_caveats_for_run_recipe(resolved_recipe)),
        },
        "hypothesis_recipe_alignment": {
            "status": "blocked",
            "reasons": [error_message],
            "missing_assumptions": [],
            "missing_outputs": [],
        },
        "input_validation": {
            "observed_temperature_profile": "unknown",
            "observed_moisture_profile": "unknown",
            "observed_wind_profile": "blocked" if "wind" in error_message.lower() else "unknown",
            "model_bottom_elevation": "unknown",
            "caveats": [],
        },
        "run_shape_validation": run_shape,
        "forcing_validation": _forcing_validation_for_recipe(resolved_recipe),
        "output_validation": {
            "required_fields": _required_outputs_for_story(story, _run_recipe(resolved_recipe)),
            "enabled_fields": [],
            "missing_fields": [],
        },
        "runtime_file_validation": {
            "required_files": list(scenario.cm1_template.runtime_files_needed),
            "staging_status": "not_reached",
            "caveats": ["run_generation_blocked_before_runtime_file_staging"],
        },
        "blocking_errors": [error_message],
        "caveats": [],
        "controls": controls,
    }


def report_blocks_execution(report: dict[str, Any] | None) -> bool:
    return bool(report and report.get("status") == "blocked")


def _hypothesis_recipe_alignment(
    story: str | None,
    run_recipe: RunRecipe,
) -> dict[str, list[str] | str]:
    if story is None:
        return {
            "status": "aligned",
            "reasons": ["No selected candidate hypothesis; validating the run configuration only."],
            "missing_assumptions": [],
            "blocking_errors": [],
            "caveats": [],
        }
    if story in REVIEW_OR_BLOCKED_STORIES:
        return {
            "status": "blocked",
            "reasons": ["Selected sounding story is not ready to run."],
            "missing_assumptions": ["run_ready_candidate_hypothesis"],
            "blocking_errors": [
                "Selected candidate story is not ready to run and cannot be generated honestly."
            ],
            "caveats": [],
        }
    if story in DEEP_CONVECTION_STORIES:
        if run_recipe in {
            RunRecipe.DEEP_TOWER_BENCHMARK,
            RunRecipe.EXPLICIT_LOCALIZED_THERMAL,
        }:
            reason = (
                "Deep-convection ingredients can be tested with the explicit "
                "Deep-Tower Benchmark trigger."
                if run_recipe == RunRecipe.DEEP_TOWER_BENCHMARK
                else "Deep-convection ingredients can be tested with the "
                "Explicit localized thermal trigger."
            )
            return {
                "status": "aligned",
                "reasons": [reason],
                "missing_assumptions": [],
                "blocking_errors": [],
                "caveats": [
                    "explicit_thermal_initiation_supplied_not_a_real_observed_trigger",
                ],
            }
        differential = run_recipe == RunRecipe.DIFFERENTIAL_SURFACE_FORCED_EVOLUTION
        return {
            "status": "partial",
            "reasons": [
                "Deep-convection ingredients can be tested only as the selected run evolves "
                "under the configured lower-boundary forcing."
            ],
            "missing_assumptions": [],
            "blocking_errors": [],
            "caveats": [
                "deep_convection_outcome_depends_on_surface_forcing_duration_domain_and_resolution",
                *([] if differential else ["differential_surface_forcing_is_a_separate_recipe"]),
            ],
        }
    if story == "humid_rainy_candidate":
        return {
            "status": "partial",
            "reasons": [
                "Humid/rainy hypothesis can be inspected, but comparison depends on "
                "rain-water, surface-rain, and reflectivity outputs."
            ],
            "missing_assumptions": [],
            "blocking_errors": [],
            "caveats": ["humid_rainy_prediction_requires_precipitation_output_review"],
        }
    return {
        "status": "aligned",
        "reasons": ["Selected hypothesis and run recipe are compatible."],
        "missing_assumptions": [],
        "blocking_errors": [],
        "caveats": [],
    }


def _selected_candidate_payload(
    candidate_screening: dict[str, Any] | None,
    observed_sounding: dict[str, object] | ObservedSoundingRecord | None,
) -> dict[str, Any]:
    observed = (
        observed_sounding.model_dump(mode="json")
        if isinstance(observed_sounding, ObservedSoundingRecord)
        else observed_sounding
        if isinstance(observed_sounding, dict)
        else {}
    )
    return {
        "candidate_id": _string_or_none(candidate_screening, "candidate_id"),
        "station_id": observed.get("station_id") if isinstance(observed, dict) else None,
        "valid_time_utc": observed.get("valid_time_utc") if isinstance(observed, dict) else None,
    }


def _selected_hypothesis_payload(
    candidate_screening: dict[str, Any] | None,
    story: str | None,
) -> dict[str, Any]:
    score = _active_story_score(candidate_screening, story)
    return {
        "hypothesis_id": story,
        "story_id": story,
        "story_label": _string_or_none(candidate_screening, "active_story_label"),
        "ingredient_score": score
        if score is not None
        else _number_or_none(candidate_screening, "rank_score"),
        "predicted_output_signature": _predicted_output_signature(story),
    }


def _selected_run_recipe_payload(contract: CM1InputContract) -> dict[str, Any]:
    return {
        "run_recipe": contract.run_recipe.value,
        "recipe_id": contract.recipe_id,
        "display_name": contract.run_recipe_display_name,
        "recipe_display_name": contract.recipe_display_name,
        "assumption_set_id": contract.assumption_set_id,
        "assumption_mode": contract.assumption_mode,
        "required_fields": list(contract.required_output_fields),
        "assumptions": contract.recipe_assumptions,
        "caveats": list(contract.recipe_caveats),
    }


def _input_validation_payload(
    observed_sounding: ObservedSoundingRecord | None,
    contract: CM1InputContract,
) -> dict[str, Any]:
    if observed_sounding is None:
        return {
            "observed_temperature_profile": "generated_reference",
            "observed_moisture_profile": "generated_reference",
            "observed_wind_profile": "generated_reference",
            "model_bottom_elevation": "generated_reference",
            "caveats": [],
        }
    wind_required = contract.run_recipe in {
        RunRecipe.OBSERVED_SURFACE_FORCED_EVOLUTION,
        RunRecipe.DIFFERENTIAL_SURFACE_FORCED_EVOLUTION,
        RunRecipe.DEEP_TOWER_BENCHMARK,
    }
    complete_wind_profile = has_complete_rendered_observed_wind_profile(
        observed_sounding,
        defaults=contract.cloud_scale_defaults,
    )
    if wind_required:
        wind_status = "present_required" if complete_wind_profile else "missing_required"
    else:
        wind_status = "present_optional" if complete_wind_profile else "optional_missing"
    caveats = list(observed_sounding.validation.caveats)
    if wind_status == "missing_required":
        caveats.append("complete_observed_wind_profile_required_for_input_sounding")
    return {
        "observed_temperature_profile": "present",
        "observed_moisture_profile": "present",
        "observed_wind_profile": wind_status,
        "model_bottom_elevation": (
            "present" if observed_sounding.model_bottom_elevation_m_msl is not None else "missing"
        ),
        "caveats": _dedupe(caveats),
    }


def _run_shape_validation_payload(contract: CM1InputContract) -> dict[str, Any]:
    values = contract.run_configuration.cm1_values
    return {
        "duration": contract.run_configuration.duration,
        "duration_seconds": values.runtime_seconds,
        "domain": contract.run_configuration.domain_size,
        "domain_x_km": values.domain_x_km,
        "domain_y_km": values.domain_y_km,
        "model_top": values.model_top_m,
        "nz": values.nz,
        "dz_m": values.dz_m,
        "stretch_z": values.stretch_z,
        "str_bot_m": values.str_bot_m,
        "str_top_m": values.str_top_m,
        "dz_bot_m": values.dz_bot_m,
        "dz_top_m": values.dz_top_m,
        "horizontal_cell_count": contract.run_configuration.horizontal_cell_count,
        "dx_m": values.dx_m,
        "dy_m": values.dy_m,
        "output_cadence": contract.run_configuration.output_cadence,
        "output_cadence_seconds": values.output_cadence_seconds,
        "diagnostic_set": contract.run_configuration.diagnostic_set,
        "estimated_frames": values.expected_output_frames,
        "estimated_output_volume": contract.run_configuration.output_volume_summary,
    }


def _run_shape_from_payload(
    run_configuration: dict[str, object] | None,
    run_recipe: str,
) -> dict[str, Any]:
    try:
        resolved = resolve_run_configuration(
            run_configuration=run_configuration,
            run_recipe=run_recipe,
        )
    except ValueError:
        return {
            "duration": run_configuration.get("duration")
            if isinstance(run_configuration, dict)
            else None,
            "domain": run_configuration.get("domain_size")
            if isinstance(run_configuration, dict)
            else None,
            "horizontal_cell_count": run_configuration.get("horizontal_cell_count")
            if isinstance(run_configuration, dict)
            else None,
            "output_cadence": run_configuration.get("output_cadence")
            if isinstance(run_configuration, dict)
            else None,
            "diagnostic_set": run_configuration.get("diagnostic_set")
            if isinstance(run_configuration, dict)
            else None,
            "estimated_frames": None,
            "estimated_output_volume": None,
        }
    values = resolved.cm1_values
    return {
        "duration": resolved.duration,
        "duration_seconds": values.runtime_seconds,
        "domain": resolved.domain_size,
        "domain_x_km": values.domain_x_km,
        "domain_y_km": values.domain_y_km,
        "model_top": values.model_top_m,
        "nz": values.nz,
        "dz_m": values.dz_m,
        "stretch_z": values.stretch_z,
        "str_bot_m": values.str_bot_m,
        "str_top_m": values.str_top_m,
        "dz_bot_m": values.dz_bot_m,
        "dz_top_m": values.dz_top_m,
        "horizontal_cell_count": resolved.horizontal_cell_count,
        "dx_m": values.dx_m,
        "dy_m": values.dy_m,
        "output_cadence": resolved.output_cadence,
        "output_cadence_seconds": values.output_cadence_seconds,
        "diagnostic_set": resolved.diagnostic_set,
        "estimated_frames": values.expected_output_frames,
        "estimated_output_volume": resolved.output_volume_summary,
    }


def _forcing_validation_payload(contract: CM1InputContract) -> dict[str, Any]:
    payload: dict[str, Any] = dict(_forcing_validation_for_recipe(contract.run_recipe.value))
    surface_fluxes = contract.recipe_assumptions.get("surface_fluxes")
    if isinstance(surface_fluxes, dict):
        payload["surface_fluxes"] = surface_fluxes
    return payload


def _forcing_validation_for_recipe(run_recipe: str) -> dict[str, Any]:
    if run_recipe == RunRecipe.DEEP_TOWER_BENCHMARK.value:
        return {
            "trigger": "cm1_iinit_3_three_warm_bubbles",
            "surface_fluxes": {
                "mode": "disabled",
                "status": "disabled_for_explicit_deep_tower_benchmark_v0",
            },
            "radiation": "disabled",
            "large_scale_forcing": "none",
        }
    if run_recipe == RunRecipe.EXPLICIT_LOCALIZED_THERMAL.value:
        return {
            "trigger": "cm1_iinit_1_single_warm_bubble",
            "surface_fluxes": {
                "mode": "disabled",
                "status": "disabled_for_explicit_localized_thermal_v0",
            },
            "radiation": "disabled",
            "large_scale_forcing": "none",
        }
    if run_recipe == RunRecipe.DIFFERENTIAL_SURFACE_FORCED_EVOLUTION.value:
        return {
            "trigger": "none",
            "surface_fluxes": {
                "mode": "differential_surface_forcing_patch_v0",
                "status": "selected_values_unavailable_before_configuration_resolves",
            },
            "radiation": "disabled",
            "large_scale_forcing": "none",
            "source_customization": "checked_and_applied_at_launch",
        }
    if run_recipe == RunRecipe.OBSERVED_SURFACE_FORCED_EVOLUTION.value:
        return {
            "trigger": "none",
            "surface_fluxes": {
                "mode": "constant_uniform_surface_flux_proxy",
                "status": "selected_values_unavailable_before_configuration_resolves",
            },
            "radiation": "disabled",
            "large_scale_forcing": "none",
        }
    return {
        "trigger": "none",
        "surface_fluxes": {"mode": "current_recipe_default"},
        "radiation": "disabled",
        "large_scale_forcing": "not_supported_v1",
    }


def _required_outputs_for_story(
    story: str | None,
    run_recipe: RunRecipe,
) -> list[str]:
    if story in DEEP_CONVECTION_STORIES:
        if run_recipe in {
            RunRecipe.DEEP_TOWER_BENCHMARK,
            RunRecipe.EXPLICIT_LOCALIZED_THERMAL,
        }:
            return ["qv", "qc", "w", "qr", "rain", "dbz", "u", "v", "th", "updraft_helicity"]
        return ["qv", "qc", "w", "qr", "rain", "dbz", "hfx", "qfx", "updraft_helicity"]
    if story == "humid_rainy_candidate":
        return ["qv", "qc", "w", "qr", "rain", "dbz", "hfx", "qfx"]
    if run_recipe in {
        RunRecipe.OBSERVED_SURFACE_FORCED_EVOLUTION,
        RunRecipe.DIFFERENTIAL_SURFACE_FORCED_EVOLUTION,
    }:
        return ["qv", "qc", "w", "hfx", "qfx"]
    return ["qc", "w"]


def _predicted_output_signature(story: str | None) -> list[str]:
    if story in DEEP_CONVECTION_STORIES:
        return ["deep_cloud", "strong_updraft", "rain_water_aloft", "reflectivity"]
    if story == "humid_rainy_candidate":
        return ["cloud_water", "rain_water_aloft_or_surface_rain"]
    if story == "dry_failed_candidate":
        return ["updraft_without_meaningful_cloud_water"]
    if story == "capped_suppressed_candidate":
        return ["suppressed_or_shallow_cloud", "limited_cloud_top"]
    if story == "shallow_cumulus_candidate":
        return ["shallow_cloud_water", "modest_vertical_velocity"]
    return []


def _selected_story(candidate_screening: dict[str, Any] | None) -> str | None:
    if not candidate_screening:
        return None
    active = candidate_screening.get("active_story")
    if isinstance(active, str) and active:
        return active
    primary = candidate_screening.get("primary_story")
    return primary if isinstance(primary, str) and primary else None


def _active_story_score(
    candidate_screening: dict[str, Any] | None, story: str | None
) -> float | None:
    if not candidate_screening or story is None:
        return None
    scores = candidate_screening.get("story_scores")
    if not isinstance(scores, list):
        return None
    for score in scores:
        if not isinstance(score, dict) or score.get("story") != story:
            continue
        value = score.get("score_0_to_100")
        return float(value) if isinstance(value, int | float) else None
    return None


def _string_or_none(payload: dict[str, Any] | None, key: str) -> str | None:
    value = payload.get(key) if payload else None
    return value if isinstance(value, str) else None


def _number_or_none(payload: dict[str, Any] | None, key: str) -> float | None:
    value = payload.get(key) if payload else None
    return float(value) if isinstance(value, int | float) else None


def _run_recipe_value(
    run_recipe: str | None,
    observed_sounding: dict[str, object] | ObservedSoundingRecord | None,
) -> str:
    if run_recipe:
        return run_recipe
    if observed_sounding is not None:
        return RunRecipe.OBSERVED_SURFACE_FORCED_EVOLUTION.value
    return RunRecipe.GENERATED_REFERENCE_LOWER_ATMOSPHERE.value


def _run_recipe(value: str) -> RunRecipe:
    try:
        return RunRecipe(value)
    except ValueError:
        return RunRecipe.GENERATED_REFERENCE_LOWER_ATMOSPHERE


def _run_recipe_display_name(run_recipe: str) -> str:
    if run_recipe == "triggered_deep_potential":
        return "Deep-Tower Benchmark"
    if run_recipe == RunRecipe.DEEP_TOWER_BENCHMARK.value:
        return "Deep-Tower Benchmark"
    if run_recipe == RunRecipe.EXPLICIT_LOCALIZED_THERMAL.value:
        return "Explicit localized thermal"
    if run_recipe == RunRecipe.OBSERVED_SURFACE_FORCED_EVOLUTION.value:
        return "Observed Surface-Forced Evolution"
    return "Generated Lower-Atmosphere Reference"


def _assumption_set_id(run_recipe: str) -> str:
    return assumption_set_id_for_run_recipe(run_recipe)


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
