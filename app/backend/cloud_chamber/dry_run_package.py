"""Dry-run CM1 package generation.

Writes reviewable package files without launching CM1 or requiring NetCDF output.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from cloud_chamber import __version__
from cloud_chamber.cm1_input_contract import (
    CM1InputContract,
    build_cm1_input_contract,
    render_input_sounding_notes,
    render_namelist_fragment,
)
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
    run_size_preset: str = "quick_look",
    user_name: str | None = None,
    allow_overwrite: bool = False,
    app_commit: str | None = None,
) -> DryRunPackageResult:
    scenario = validate_scenario_template(scenario_data)
    selected_controls = controls or {}
    _validate_selected_controls(scenario, selected_controls)

    package_dir = runtime_home.expanduser() / "runs" / run_id
    if package_dir.exists() and not allow_overwrite:
        raise DryRunPackageError(f"Run package already exists: {package_dir}")
    package_dir.mkdir(parents=True, exist_ok=allow_overwrite)

    contract = build_cm1_input_contract(
        scenario,
        selected_controls=selected_controls,
        run_size_preset=run_size_preset,
    )
    now = datetime.now(UTC)

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
        run_size_preset=run_size_preset,
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
        user=UserMetadata(name=user_name or scenario.display_name),
    )

    case_manifest = _case_manifest_payload(scenario, contract)
    report = _dry_run_report_payload(
        scenario=scenario,
        manifest=manifest,
        contract=contract,
        generated_files=paths,
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
) -> dict[str, object]:
    return {
        "scenario_id": scenario.id,
        "display_name": scenario.display_name,
        "physical_question": scenario.physical_question,
        "learning_goals": scenario.learning_goals,
        "expected_behavior": scenario.expected_behavior,
        "warnings": scenario.warnings,
        "limitations": scenario.limitations,
        "cm1_mapping_status": (
            "CM1-ready provisional baseline package; still pending local/manual smoke-run "
            "scientific validation"
        ),
        "contract": asdict(contract),
    }


def _dry_run_report_payload(
    *,
    scenario: ScenarioTemplate,
    manifest: RunManifest,
    contract: CM1InputContract,
    generated_files: dict[str, Path],
) -> dict[str, object]:
    return {
        "status": "dry_run_package_only",
        "not_a_completed_cm1_result": True,
        "cm1_was_launched": False,
        "scenario_id": scenario.id,
        "physical_question": scenario.physical_question,
        "controls": manifest.controls,
        "variant_metadata": {
            "moisture_profile": contract.moisture_profile,
            "low_level_humidity": manifest.controls.get("low_level_humidity"),
            "mapping": (
                "external input_sounding moisture profile; non-moisture namelist settings "
                "remain inherited from the validated baseline"
            ),
        },
        "run_size_preset": manifest.run_size_preset,
        "estimated_cost_or_size": "unknown until validated",
        "expected_diagnostics": manifest.expected_diagnostics,
        "visualization_defaults": contract.visualization_defaults,
        "generated_files": {name: str(path) for name, path in generated_files.items()},
        "provenance": {
            "product_state": manifest.provenance.product_state.value,
            "source_model": manifest.provenance.source_model,
            "preview_is_guidance_only": manifest.provenance.preview_is_guidance_only,
            "visualizer_is_interpretation": manifest.provenance.visualizer_is_interpretation,
        },
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
