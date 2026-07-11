"""Dry-run CM1 package generation.

Writes reviewable package files without launching CM1 or requiring NetCDF output.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cloud_chamber import __version__
from cloud_chamber.cm1_input_contract import (
    CM1InputContract,
    build_cm1_input_contract,
    cloud_scale_defaults_for_configuration,
    render_input_sounding_notes,
    render_namelist_fragment,
)
from cloud_chamber.observed_sounding import ObservedSoundingRecord, observed_sounding_from_payload
from cloud_chamber.pre_run_validation import (
    blocked_pre_run_validation_report,
    build_pre_run_validation_report,
)
from cloud_chamber.run_configuration import resolve_run_configuration
from cloud_chamber.run_manifest import (
    AppMetadata,
    GeneratedInputs,
    LifecycleState,
    ProductState,
    ProvenanceMetadata,
    RunManifest,
    RuntimePaths,
    ScenarioReference,
    UserMetadata,
    ValidationStatus,
)
from cloud_chamber.scenario_schema import ScenarioTemplate, validate_scenario_template


class DryRunPackageError(RuntimeError):
    """Raised when a dry-run package cannot be generated."""

    def __init__(
        self,
        message: str,
        *,
        pre_run_validation_report: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.pre_run_validation_report = pre_run_validation_report


@dataclass(frozen=True)
class DryRunPackageResult:
    run_id: str
    package_dir: Path
    manifest_path: Path
    report_path: Path
    generated_files: tuple[Path, ...]


def generate_dry_run_package(
    *,
    scenario_data: object,
    runtime_home: Path,
    run_id: str,
    controls: dict[str, str | float | bool] | None = None,
    user_name: str | None = None,
    allow_overwrite: bool = False,
    app_commit: str | None = None,
    observed_sounding: dict[str, object] | ObservedSoundingRecord | None = None,
    candidate_screening: dict[str, object] | None = None,
    user_tags: list[str] | None = None,
    user_notes: str | None = None,
    package_family: str | None = None,
    run_configuration: dict[str, object] | None = None,
) -> DryRunPackageResult:
    scenario = validate_scenario_template(scenario_data)
    selected_controls = controls or {}
    _validate_selected_controls(scenario, selected_controls)

    package_dir = runtime_home.expanduser() / "runs" / run_id
    if package_dir.exists() and not allow_overwrite:
        raise DryRunPackageError(f"Run package already exists: {package_dir}")

    observed_record = _observed_sounding_record(observed_sounding)

    try:
        contract = build_cm1_input_contract(
            scenario,
            selected_controls=selected_controls,
            run_configuration=run_configuration,
            observed_sounding=observed_record,
            package_family=package_family,
        )
    except ValueError as exc:
        error_message = _user_facing_validation_error(str(exc))
        report = blocked_pre_run_validation_report(
            scenario=scenario,
            controls=selected_controls,
            package_family=package_family,
            run_configuration=run_configuration,
            observed_sounding=observed_sounding,
            candidate_screening=candidate_screening,
            error_message=error_message,
        )
        raise DryRunPackageError(error_message, pre_run_validation_report=report) from exc
    now = datetime.now(UTC)

    pre_run_validation_report = build_pre_run_validation_report(
        scenario=scenario,
        contract=contract,
        candidate_screening=candidate_screening,
    )
    if pre_run_validation_report["status"] == "blocked":
        message = "; ".join(
            str(error) for error in pre_run_validation_report.get("blocking_errors", [])
        )
        raise DryRunPackageError(
            f"Pre-run validation blocked package creation: {message}",
            pre_run_validation_report=pre_run_validation_report,
        )

    package_dir.mkdir(parents=True, exist_ok=allow_overwrite)

    paths = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "namelist": package_dir / "namelist.input",
        "input_sounding": package_dir / "input_sounding",
        "report": package_dir / "dry_run_report.json",
        "runtime_checklist": package_dir / "runtime_file_checklist.json",
    }

    manifest = RunManifest(
        run_id=run_id,
        scenario=ScenarioReference(
            id=scenario.id,
            schema_version=scenario.schema_version,
            template_path=scenario.cm1_template.namelist_template,
        ),
        controls=_effective_controls(scenario, selected_controls),
        run_configuration=contract.run_configuration.model_dump(mode="json"),
        physical_question=scenario.physical_question,
        expected_diagnostics=list(contract.expected_diagnostics),
        generated_inputs=GeneratedInputs(
            run_directory=str(package_dir),
            manifest_path=str(paths["manifest"]),
            namelist_input=str(paths["namelist"]),
            input_sounding=str(paths["input_sounding"]),
            dry_run_report=str(paths["report"]),
            runtime_file_checklist=[str(paths["runtime_checklist"])],
        ),
        runtime_paths=RuntimePaths(runtime_home=str(runtime_home.expanduser())),
        app=AppMetadata(app_version=__version__, commit=app_commit),
        lifecycle_state=LifecycleState.PACKAGED,
        validation_status=ValidationStatus.VALID,
        provenance=ProvenanceMetadata(product_state=ProductState.PACKAGED_DRY_RUN_OUTPUT),
        created_at=now,
        updated_at=now,
        user=UserMetadata(
            name=user_name or scenario.display_name,
            tags=_normalize_user_tags(user_tags),
            notes=_normalize_user_notes(user_notes),
        ),
        observed_sounding=(
            observed_record.model_dump(mode="json") if observed_record is not None else None
        ),
        candidate_screening=candidate_screening,
        pre_run_validation_report=pre_run_validation_report,
        package_family=contract.package_family.value,
        package_display_name=contract.package_display_name,
        input_source=contract.input_source,
        trigger_type=contract.trigger_type,
        trigger_parameters=contract.trigger_parameters,
        expected_outputs=list(contract.expected_outputs),
        package_limitations=list(contract.limitations),
        package_caveats=list(contract.package_caveats),
        manual_validation_status=contract.manual_validation_status,
    )

    case_manifest = _case_manifest_payload(
        scenario,
        contract,
        candidate_screening=candidate_screening,
        pre_run_validation_report=pre_run_validation_report,
    )
    report = _dry_run_report_payload(
        scenario=scenario,
        manifest=manifest,
        contract=contract,
        generated_files=paths,
        pre_run_validation_report=pre_run_validation_report,
    )
    runtime_checklist = {
        "status": "external_runtime_files_not_committed",
        "required_files": scenario.cm1_template.runtime_files_needed,
        "source_candidates": {
            "LANDUSE.TBL": [
                "config_files/les_ShallowCu/LANDUSE.TBL",
                "LANDUSE.TBL",
            ]
        },
        "notes": (
            "CM1 remains external to the repo. Required runtime files are staged from "
            "the configured local CM1 run directory, preferring the les_ShallowCu "
            "reference case where available, never committed to the repo."
        ),
    }

    _write_json(paths["manifest"], json.loads(manifest.to_json_text()))
    _write_json(paths["case_manifest"], case_manifest)
    paths["namelist"].write_text(render_namelist_fragment(contract))
    paths["input_sounding"].write_text(render_input_sounding_notes(contract))
    _write_json(paths["report"], report)
    _write_json(paths["runtime_checklist"], runtime_checklist)

    return DryRunPackageResult(
        run_id=run_id,
        package_dir=package_dir,
        manifest_path=paths["manifest"],
        report_path=paths["report"],
        generated_files=tuple(paths.values()),
    )


def _validate_selected_controls(
    scenario: ScenarioTemplate,
    selected_controls: dict[str, str | float | bool],
) -> None:
    known_controls = {control.id for control in scenario.controls}
    unknown_controls = sorted(set(selected_controls) - known_controls)
    if unknown_controls:
        raise DryRunPackageError("Unknown controls: " + ", ".join(unknown_controls))


def _observed_sounding_record(
    observed_sounding: dict[str, object] | ObservedSoundingRecord | None,
) -> ObservedSoundingRecord | None:
    if observed_sounding is None:
        return None
    if isinstance(observed_sounding, ObservedSoundingRecord):
        return observed_sounding
    try:
        return observed_sounding_from_payload(observed_sounding)
    except Exception as exc:
        raise DryRunPackageError(f"Invalid observed sounding: {exc}") from exc


def _user_facing_validation_error(message: str) -> str:
    replacements = {
        "duration_preset": "duration preset",
        "grid_detail_preset": "grid detail preset",
        "domain_size_preset": "domain size preset",
        "output_cadence_preset": "output cadence preset",
        "output_field_density_preset": "output field density preset",
    }
    for internal, label in replacements.items():
        message = message.replace(internal, label)
    return message


def _effective_controls(
    scenario: ScenarioTemplate,
    selected_controls: dict[str, str | float | bool],
) -> dict[str, str | float | bool]:
    return {
        control.id: selected_controls.get(control.id, control.default)
        for control in scenario.controls
    }


def read_dry_run_report(path: Path) -> dict[str, object]:
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise DryRunPackageError(f"Dry-run report must be a JSON object: {path}")
    return loaded


def _case_manifest_payload(
    scenario: ScenarioTemplate,
    contract: CM1InputContract,
    *,
    candidate_screening: dict[str, object] | None = None,
    pre_run_validation_report: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "scenario_id": scenario.id,
        "display_name": scenario.display_name,
        "package_family": contract.package_family.value,
        "package_display_name": contract.package_display_name,
        "input_source": contract.input_source,
        "trigger_type": contract.trigger_type,
        "trigger_parameters": contract.trigger_parameters,
        "physical_question": scenario.physical_question,
        "learning_goals": scenario.learning_goals,
        "expected_behavior": scenario.expected_behavior,
        "warnings": scenario.warnings,
        "limitations": scenario.limitations,
        "package_caveats": contract.package_caveats,
        "manual_validation_status": contract.manual_validation_status,
        "run_configuration": contract.run_configuration.model_dump(mode="json"),
        "pre_run_validation_report": pre_run_validation_report,
        "cm1_mapping_status": _cm1_mapping_status(contract),
        "contract": _contract_payload(contract),
        "candidate_screening": candidate_screening,
    }


def _dry_run_report_payload(
    *,
    scenario: ScenarioTemplate,
    manifest: RunManifest,
    contract: CM1InputContract,
    generated_files: dict[str, Path],
    pre_run_validation_report: dict[str, object],
) -> dict[str, object]:
    run_configuration_summary = _run_configuration_summary(contract)
    return {
        "status": "dry_run_package_only",
        "not_a_completed_cm1_result": True,
        "cm1_was_launched": False,
        "scenario_id": scenario.id,
        "package_family": contract.package_family.value,
        "package_display_name": contract.package_display_name,
        "input_source": contract.input_source,
        "trigger_type": contract.trigger_type,
        "trigger_parameters": contract.trigger_parameters,
        "physical_question": scenario.physical_question,
        "controls": manifest.controls,
        "variant_metadata": {
            "moisture_profile": contract.moisture_profile,
            "stability_profile": contract.stability_profile,
            "sounding_source": (
                "observed_igra_station_text"
                if contract.observed_sounding is not None
                else "generated_reference"
            ),
            "low_level_humidity": manifest.controls.get("low_level_humidity"),
            "cap_strength": manifest.controls.get("cap_strength"),
            "cap_height": manifest.controls.get("cap_height"),
            "mapping": _package_mapping_summary(contract),
        },
        "observed_sounding": (
            _observed_sounding_summary(contract.observed_sounding)
            if contract.observed_sounding is not None
            else None
        ),
        "candidate_screening": manifest.candidate_screening,
        "user": manifest.user.model_dump(mode="json"),
        "run_configuration": contract.run_configuration.model_dump(mode="json"),
        "run_configuration_summary": run_configuration_summary,
        "pre_run_validation_report": pre_run_validation_report,
        "estimated_cost_or_size": run_configuration_summary["cost_warning"],
        "expected_diagnostics": manifest.expected_diagnostics,
        "expected_outputs": list(contract.expected_outputs),
        "package_caveats": list(contract.package_caveats),
        "manual_validation_status": contract.manual_validation_status,
        "cm1_mapping_status": _cm1_mapping_status(contract),
        "visualization_defaults": contract.visualization_defaults,
        "generated_files": {name: str(path) for name, path in generated_files.items()},
        "provenance": {
            "product_state": manifest.provenance.product_state.value,
            "source_model": manifest.provenance.source_model,
            "preview_is_guidance_only": manifest.provenance.preview_is_guidance_only,
            "visualizer_is_interpretation": manifest.provenance.visualizer_is_interpretation,
        },
    }


def _contract_payload(contract: CM1InputContract) -> dict[str, object]:
    payload = asdict(contract)
    payload["run_configuration"] = contract.run_configuration.model_dump(mode="json")
    if contract.observed_sounding is not None:
        payload["observed_sounding"] = contract.observed_sounding.model_dump(mode="json")
    return payload


def _observed_sounding_summary(record: ObservedSoundingRecord) -> dict[str, object]:
    return {
        "source_provider": record.source_provider,
        "source_format": record.source_format,
        "uploaded_filename": record.uploaded_filename,
        "station_id": record.station_id,
        "station_name": record.station_name,
        "station_latitude": record.station_latitude,
        "station_longitude": record.station_longitude,
        "station_elevation_m_msl": record.station_elevation_m_msl,
        "valid_time_utc": record.valid_time_utc.isoformat(),
        "source_vertical_coordinate_type": record.source_vertical_coordinate_type,
        "model_bottom_elevation_m_msl": record.model_bottom_elevation_m_msl,
        "usable_levels": len(record.levels),
        "lowest_model_z_m": record.levels[0].model_z_m if record.levels else None,
        "highest_model_z_m": record.levels[-1].model_z_m if record.levels else None,
        "wind_handling": record.wind_handling,
        "wind_source": record.provenance.get("wind_source"),
        "wind_units": record.converted_cm1_units.get("wind_components"),
        "wind_conversion": record.conversion_choices.get("wind"),
        "validation_status": record.validation.status,
        "validation_errors": record.validation.errors,
        "caveats": record.validation.caveats,
        "provenance": record.provenance,
    }


def _normalize_user_tags(tags: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags or []:
        cleaned = tag.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cleaned)
    return normalized


def _normalize_user_notes(notes: str | None) -> str | None:
    if notes is None:
        return None
    cleaned = notes.strip()
    return cleaned or None


def _run_configuration_summary(contract: CM1InputContract) -> dict[str, object]:
    defaults = contract.cloud_scale_defaults
    reference_configuration = resolve_run_configuration(
        package_family=contract.package_family.value,
    )
    standard = cloud_scale_defaults_for_configuration(reference_configuration)
    grid_cells = defaults.nx * defaults.ny * defaults.nz
    standard_grid_cells = standard.nx * standard.ny * standard.nz
    output_frames = _expected_output_frames(
        defaults.runtime_seconds, defaults.output_cadence_seconds
    )
    standard_output_frames = _expected_output_frames(
        standard.runtime_seconds, standard.output_cadence_seconds
    )
    grid_multiplier = grid_cells / standard_grid_cells
    timestep_multiplier = standard.time_step_seconds / defaults.time_step_seconds
    output_frame_multiplier = output_frames / standard_output_frames
    runtime_multiplier = defaults.runtime_seconds / standard.runtime_seconds
    estimated_compute_multiplier = grid_multiplier * timestep_multiplier * runtime_multiplier
    estimated_output_volume_multiplier = grid_multiplier * output_frame_multiplier
    is_smoke = contract.run_configuration.mode == "smoke"
    is_deep_convection = contract.package_family.value == "deep_convection_trial"
    cost_warning = (
        _deep_convection_cost_warning(contract.run_configuration)
        if is_deep_convection
        else (
            (
                "Short smoke mode checks package health and CM1 startup behavior; "
                "it is not long enough to evaluate normal atmospheric evolution."
            )
            if is_smoke
            else (
                "Configuration cost depends on duration, grid/detail, domain, cadence, "
                "and output-field density. Review the CM1-facing values before launch."
            )
        )
    )
    return {
        "configuration_id": contract.run_configuration.configuration_id,
        "mode": contract.run_configuration.mode,
        "label": contract.run_configuration.label,
        "duration_preset": contract.run_configuration.duration_preset,
        "grid_detail_preset": contract.run_configuration.grid_detail_preset,
        "domain_size_preset": contract.run_configuration.domain_size_preset,
        "output_cadence_preset": contract.run_configuration.output_cadence_preset,
        "output_field_density_preset": contract.run_configuration.output_field_density_preset,
        "runtime_seconds": defaults.runtime_seconds,
        "output_cadence_seconds": defaults.output_cadence_seconds,
        "expected_output_frames": output_frames,
        "nx": defaults.nx,
        "ny": defaults.ny,
        "nz": defaults.nz,
        "dx_m": defaults.horizontal_spacing_m,
        "dy_m": defaults.horizontal_spacing_m,
        "dz_m": defaults.vertical_spacing_m,
        "model_top_m": defaults.vertical_extent_km * 1000.0,
        "time_step_seconds": defaults.time_step_seconds,
        "time_step_note": (
            "Deep Convection Trial uses a larger solver timestep for the storm-scale "
            "triggered-potential setup."
            if is_deep_convection
            else "CM1 solver timestep is resolved from the selected run configuration."
        ),
        "grid_cell_count": grid_cells,
        "grid_cell_multiplier_vs_default": round(grid_multiplier, 2),
        "time_step_multiplier_vs_default": round(timestep_multiplier, 2),
        "output_frame_multiplier_vs_default": round(output_frame_multiplier, 2),
        "estimated_compute_multiplier_vs_default": round(estimated_compute_multiplier, 2),
        "estimated_output_volume_multiplier_vs_default": round(
            estimated_output_volume_multiplier, 2
        ),
        "cost_warning": cost_warning,
        "validation_note": (
            "Deep Convection Trial uses a wider idealized domain and observed winds. "
            "Manual CM1 smoke evidence applies to the package family; each observed "
            "sounding remains an experiment until CM1 output is inspected."
            if is_deep_convection
            else (
                "Short smoke mode is separated from science runs; use Quick science or longer "
                "configurations for meteorological evolution."
                if is_smoke
                else (
                    "Run configuration preserves explicit duration, grid/detail, domain, "
                    "cadence, and output-density choices."
                )
            )
        ),
    }


def _package_mapping_summary(contract: CM1InputContract) -> str:
    if contract.package_family.value == "deep_convection_trial":
        return (
            "observed IGRA external input_sounding profile with observed u/v winds; "
            "Deep Convection Trial uses CM1 isnd=7, testcase=0, iinit=3 three-warm-bubble "
            "line initiation, a storm-scale idealized domain, NetCDF output, rain output, "
            "reflectivity output, vorticity output, and updraft-helicity output"
        )
    if contract.observed_sounding is not None:
        return (
            "observed IGRA external input_sounding profile; non-wind namelist settings "
            "remain inherited from the validated baseline; observed wind direction/speed is "
            "converted to u/v and applied through CM1 isnd=7 input_sounding handling"
        )
    return (
        "external input_sounding profile; namelist settings remain inherited from "
        "the validated baseline; capped/suppressed variants change only stability "
        "near the cap when cap_strength is stronger"
    )


def _cm1_mapping_status(contract: CM1InputContract) -> str:
    if contract.package_family.value == "deep_convection_trial":
        return (
            "CM1-ready Deep Convection Trial package with manual CM1 smoke evidence "
            "for deep-convection initiation; each observed sounding remains an experiment"
        )
    if contract.observed_sounding is not None:
        return (
            "CM1-ready observed-sounding quick-look package; still pending "
            "case-specific local/manual scientific interpretation"
        )
    return (
        "CM1-ready provisional baseline package; still pending local/manual smoke-run "
        "scientific validation"
    )


def _deep_convection_cost_warning(run_configuration: object) -> str:
    mode = getattr(run_configuration, "mode", "")
    domain = getattr(run_configuration, "domain_size_preset", "storm_120km")
    cadence = getattr(run_configuration, "output_cadence_preset", "standard_15min")
    if mode == "smoke":
        return (
            "Deep Convection Trial smoke mode checks package health with the triggered "
            "storm-scale setup; it is not a science-duration result."
        )
    return (
        "Deep Convection Trial uses a triggered storm-scale domain. Review expected "
        f"cost/runtime/output volume for {domain} and {cadence}; larger configurations "
        "may be better suited to larger compute."
    )


def _expected_output_frames(runtime_seconds: int, output_cadence_seconds: int) -> int:
    if output_cadence_seconds <= 0:
        return 0
    return runtime_seconds // output_cadence_seconds + 1


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
