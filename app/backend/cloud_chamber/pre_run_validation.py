"""Pre-run validation for candidate hypotheses, recipes, and run shape."""

from __future__ import annotations

from typing import Any

from cloud_chamber.cm1_input_contract import CM1InputContract, PackageFamily
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
    required_outputs = _required_outputs_for_story(story, contract.package_family)
    missing_outputs = [
        field for field in required_outputs if field not in set(contract.expected_outputs)
    ]
    alignment = _hypothesis_recipe_alignment(story, contract.package_family)
    blocking_errors = list(alignment["blocking_errors"])
    caveats = _dedupe(
        [
            *contract.run_configuration.caveats,
            *contract.package_caveats,
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
        "input_validation": _input_validation_payload(contract.observed_sounding, contract),
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
    package_family: str | None,
    run_configuration: dict[str, object] | None,
    observed_sounding: dict[str, object] | ObservedSoundingRecord | None,
    candidate_screening: dict[str, Any] | None,
    error_message: str,
) -> dict[str, Any]:
    resolved_family = _family_value(package_family, observed_sounding)
    run_shape = _run_shape_from_payload(run_configuration, resolved_family)
    story = _selected_story(candidate_screening)
    return {
        "status": "blocked",
        "selected_candidate": _selected_candidate_payload(candidate_screening, observed_sounding),
        "selected_hypothesis": _selected_hypothesis_payload(candidate_screening, story),
        "selected_run_recipe": {
            "recipe_id": resolved_family,
            "display_name": _package_display_name(resolved_family),
            "assumption_set_id": _assumption_set_id(resolved_family),
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
        "forcing_validation": _forcing_validation_for_family(resolved_family),
        "output_validation": {
            "required_fields": _required_outputs_for_story(story, _package_family(resolved_family)),
            "enabled_fields": [],
            "missing_fields": [],
        },
        "runtime_file_validation": {
            "required_files": list(scenario.cm1_template.runtime_files_needed),
            "staging_status": "not_reached",
            "caveats": ["package_generation_blocked_before_runtime_file_staging"],
        },
        "blocking_errors": [error_message],
        "caveats": [],
        "controls": controls,
    }


def report_blocks_execution(report: dict[str, Any] | None) -> bool:
    return bool(report and report.get("status") == "blocked")


def _hypothesis_recipe_alignment(
    story: str | None,
    package_family: PackageFamily,
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
            "reasons": ["Selected sounding story is not package-ready."],
            "missing_assumptions": ["package_ready_candidate_hypothesis"],
            "blocking_errors": [
                "Selected candidate story is not package-ready and cannot be packaged honestly."
            ],
            "caveats": [],
        }
    if story in DEEP_CONVECTION_STORIES:
        if package_family == PackageFamily.DEEP_CONVECTION_TRIAL:
            return {
                "status": "aligned",
                "reasons": [
                    "Deep-convection hypothesis is paired with the triggered deep-potential recipe."
                ],
                "missing_assumptions": [],
                "blocking_errors": [],
                "caveats": [],
            }
        return {
            "status": "blocked",
            "reasons": ["Deep-convection hypothesis is paired with an untriggered/shallow recipe."],
            "missing_assumptions": ["triggered_deep_potential_warm_bubble_v1"],
            "blocking_errors": [
                "Selected run recipe does not test this deep-convection hypothesis."
            ],
            "caveats": [],
        }
    if story in NORMAL_EVOLUTION_STORIES and package_family == PackageFamily.DEEP_CONVECTION_TRIAL:
        return {
            "status": "blocked",
            "reasons": [
                "Normal-evolution hypothesis is paired with an explicitly triggered recipe."
            ],
            "missing_assumptions": ["normal_evolution_without_explicit_trigger"],
            "blocking_errors": [
                "Selected triggered recipe would make comparison metadata misleading "
                "for this hypothesis."
            ],
            "caveats": [],
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


def _selected_run_recipe_payload(contract: CM1InputContract) -> dict[str, str]:
    return {
        "recipe_id": contract.package_family.value,
        "display_name": contract.package_display_name,
        "assumption_set_id": _assumption_set_id(contract.package_family.value),
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
    wind_required = contract.package_family == PackageFamily.DEEP_CONVECTION_TRIAL
    wind_status = (
        ("present_required" if wind_required else "present_optional")
        if observed_sounding.wind_handling
        else ("missing_required" if wind_required else "optional_missing")
    )
    return {
        "observed_temperature_profile": "present",
        "observed_moisture_profile": "present",
        "observed_wind_profile": wind_status,
        "model_bottom_elevation": (
            "present" if observed_sounding.model_bottom_elevation_m_msl is not None else "missing"
        ),
        "caveats": list(observed_sounding.validation.caveats),
    }


def _run_shape_validation_payload(contract: CM1InputContract) -> dict[str, Any]:
    values = contract.run_configuration.cm1_values
    return {
        "duration": contract.run_configuration.duration_preset,
        "duration_seconds": values.runtime_seconds,
        "domain": contract.run_configuration.domain_size_preset,
        "domain_x_km": values.domain_x_km,
        "domain_y_km": values.domain_y_km,
        "model_top": values.model_top_m,
        "grid_detail": contract.run_configuration.grid_detail_preset,
        "dx_m": values.dx_m,
        "dy_m": values.dy_m,
        "output_cadence": contract.run_configuration.output_cadence_preset,
        "output_cadence_seconds": values.output_cadence_seconds,
        "estimated_frames": values.expected_output_frames,
        "estimated_output_volume": contract.run_configuration.output_volume_summary,
    }


def _run_shape_from_payload(
    run_configuration: dict[str, object] | None,
    package_family: str,
) -> dict[str, Any]:
    try:
        resolved = resolve_run_configuration(
            run_configuration=run_configuration,
            package_family=package_family,
        )
    except ValueError:
        return {
            "duration": run_configuration.get("duration_preset")
            if isinstance(run_configuration, dict)
            else None,
            "domain": run_configuration.get("domain_size_preset")
            if isinstance(run_configuration, dict)
            else None,
            "grid_detail": run_configuration.get("grid_detail_preset")
            if isinstance(run_configuration, dict)
            else None,
            "output_cadence": run_configuration.get("output_cadence_preset")
            if isinstance(run_configuration, dict)
            else None,
            "estimated_frames": None,
            "estimated_output_volume": None,
        }
    values = resolved.cm1_values
    return {
        "duration": resolved.duration_preset,
        "duration_seconds": values.runtime_seconds,
        "domain": resolved.domain_size_preset,
        "domain_x_km": values.domain_x_km,
        "domain_y_km": values.domain_y_km,
        "model_top": values.model_top_m,
        "grid_detail": resolved.grid_detail_preset,
        "dx_m": values.dx_m,
        "dy_m": values.dy_m,
        "output_cadence": resolved.output_cadence_preset,
        "output_cadence_seconds": values.output_cadence_seconds,
        "estimated_frames": values.expected_output_frames,
        "estimated_output_volume": resolved.output_volume_summary,
    }


def _forcing_validation_payload(contract: CM1InputContract) -> dict[str, str]:
    return _forcing_validation_for_family(contract.package_family.value)


def _forcing_validation_for_family(package_family: str) -> dict[str, str]:
    trigger = (
        "warm_bubble_required_for_triggered_deep_potential"
        if package_family == PackageFamily.DEEP_CONVECTION_TRIAL.value
        else "none"
    )
    return {
        "trigger": trigger,
        "surface_fluxes": "current_recipe_default",
        "radiation": "disabled_or_future",
        "large_scale_forcing": "not_supported_v1",
    }


def _required_outputs_for_story(
    story: str | None,
    package_family: PackageFamily,
) -> list[str]:
    if story in DEEP_CONVECTION_STORIES or package_family == PackageFamily.DEEP_CONVECTION_TRIAL:
        return ["qc", "w", "qr", "rain", "dbz", "updraft_helicity"]
    if story == "humid_rainy_candidate":
        return ["qc", "qr", "rain", "dbz"]
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


def _family_value(
    package_family: str | None,
    observed_sounding: dict[str, object] | ObservedSoundingRecord | None,
) -> str:
    if package_family:
        return package_family
    if observed_sounding is not None:
        return PackageFamily.OBSERVED_SOUNDING_QUICKLOOK.value
    return PackageFamily.SHALLOW_CUMULUS.value


def _package_family(value: str) -> PackageFamily:
    try:
        return PackageFamily(value)
    except ValueError:
        return PackageFamily.SHALLOW_CUMULUS


def _package_display_name(package_family: str) -> str:
    if package_family == PackageFamily.DEEP_CONVECTION_TRIAL.value:
        return "Deep Convection Trial"
    if package_family == PackageFamily.OBSERVED_SOUNDING_QUICKLOOK.value:
        return "Observed Sounding Quick Look"
    return "Baseline Shallow Cumulus"


def _assumption_set_id(package_family: str) -> str:
    if package_family == PackageFamily.DEEP_CONVECTION_TRIAL.value:
        return "triggered_deep_potential_warm_bubble_v1"
    if package_family == PackageFamily.OBSERVED_SOUNDING_QUICKLOOK.value:
        return "normal_evolution_current_observed_sounding_v1"
    return "generated_reference_lower_atmosphere_v1"


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
