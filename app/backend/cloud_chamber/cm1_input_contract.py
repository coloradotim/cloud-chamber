"""CM1-facing input generation contract.

This module defines deterministic metadata/fragments for future package generation.
It does not launch CM1 and does not write generated files.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cloud_chamber.scenario_schema import ControlAudience, ScenarioTemplate


class GeneratedFileRole(StrEnum):
    RUN_MANIFEST = "run_manifest"
    CASE_MANIFEST = "case_manifest"
    NAMELIST = "namelist"
    INPUT_SOUNDING = "input_sounding"
    DRY_RUN_REPORT = "dry_run_report"
    RUNTIME_FILE_CHECKLIST = "runtime_file_checklist"


@dataclass(frozen=True)
class CloudScaleDefaults:
    horizontal_extent_km: int = 16
    y_extent_km: int = 16
    vertical_extent_km: int = 6
    horizontal_spacing_m: int = 200
    vertical_spacing_m: int = 125
    runtime_seconds: int = 7200
    output_cadence_seconds: int = 300


@dataclass(frozen=True)
class GeneratedFileSpec:
    role: GeneratedFileRole
    relative_path: str
    description: str
    scientific_status: str


@dataclass(frozen=True)
class ControlMappingFragment:
    control_id: str
    control_label: str
    selected_value: str | float | bool
    audience: ControlAudience
    cm1_mapping_notes: str
    scientific_status: str


@dataclass(frozen=True)
class CM1InputContract:
    scenario_id: str
    physical_question: str
    run_size_preset: str
    cloud_scale_defaults: CloudScaleDefaults
    generated_files: tuple[GeneratedFileSpec, ...]
    control_fragments: tuple[ControlMappingFragment, ...]
    expected_diagnostics: tuple[str, ...]
    visualization_defaults: dict[str, str | list[str]]
    limitations: tuple[str, ...]


GENERATED_FILE_SPECS = (
    GeneratedFileSpec(
        role=GeneratedFileRole.RUN_MANIFEST,
        relative_path="run_manifest.json",
        description=(
            "Records scenario, controls, generated files, runtime paths, lifecycle state, "
            "and provenance."
        ),
        scientific_status="metadata contract",
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.CASE_MANIFEST,
        relative_path="case_manifest.json",
        description="Scenario-facing case metadata used to review the generated package.",
        scientific_status="metadata contract",
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.NAMELIST,
        relative_path="namelist.input",
        description="CM1 namelist input generated from validated scenario controls.",
        scientific_status="placeholder until local/manual CM1 validation",
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.INPUT_SOUNDING,
        relative_path="input_sounding",
        description="CM1 sounding/profile input generated from validated scenario controls.",
        scientific_status="placeholder until local/manual CM1 validation",
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.DRY_RUN_REPORT,
        relative_path="dry_run_report.json",
        description=(
            "Human/reviewable report describing what would be run and what remains unknown."
        ),
        scientific_status="review artifact",
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.RUNTIME_FILE_CHECKLIST,
        relative_path="runtime_file_checklist.json",
        description=(
            "Checklist of external CM1 runtime files required locally, such as LANDUSE.TBL."
        ),
        scientific_status="runtime preflight metadata",
    ),
)


def build_cm1_input_contract(
    scenario: ScenarioTemplate,
    selected_controls: dict[str, str | float | bool] | None = None,
    run_size_preset: str = "quick_look",
) -> CM1InputContract:
    selected = selected_controls or {}
    control_fragments = tuple(
        ControlMappingFragment(
            control_id=control.id,
            control_label=control.label,
            selected_value=selected.get(control.id, control.default),
            audience=control.audience,
            cm1_mapping_notes=control.cm1_mapping_notes,
            scientific_status=(
                "product-facing placeholder until local/manual CM1 validation"
                if control.audience == ControlAudience.PRODUCT
                else "advanced/developer metadata"
            ),
        )
        for control in scenario.controls
    )

    return CM1InputContract(
        scenario_id=scenario.id,
        physical_question=scenario.physical_question,
        run_size_preset=run_size_preset,
        cloud_scale_defaults=CloudScaleDefaults(),
        generated_files=GENERATED_FILE_SPECS,
        control_fragments=control_fragments,
        expected_diagnostics=_diagnostic_names(scenario),
        visualization_defaults={
            "primary_field": scenario.visualization_defaults.primary_field,
            "secondary_fields": scenario.visualization_defaults.secondary_fields,
            "camera": scenario.visualization_defaults.camera,
            "rendering_method": scenario.visualization_defaults.rendering_method,
            "provenance_label": scenario.visualization_defaults.provenance_label,
        },
        limitations=tuple(scenario.limitations),
    )


def render_namelist_fragment(contract: CM1InputContract) -> str:
    defaults = contract.cloud_scale_defaults
    lines = [
        "# Cloud Chamber CM1 namelist fragment",
        "# Status: placeholder until local/manual CM1 validation",
        f"# scenario_id = {contract.scenario_id}",
        "&cloud_chamber_domain",
        f"  x_extent_km = {defaults.horizontal_extent_km},",
        f"  y_extent_km = {defaults.y_extent_km},",
        f"  z_extent_km = {defaults.vertical_extent_km},",
        f"  dx_m = {defaults.horizontal_spacing_m},",
        f"  dz_m = {defaults.vertical_spacing_m},",
        f"  runtime_seconds = {defaults.runtime_seconds},",
        f"  output_cadence_seconds = {defaults.output_cadence_seconds},",
        "/",
    ]
    return "\n".join(lines) + "\n"


def render_input_sounding_notes(contract: CM1InputContract) -> str:
    lines = [
        "# Cloud Chamber input_sounding notes",
        "# Status: placeholder until local/manual CM1 validation",
        f"# scenario_id = {contract.scenario_id}",
        f"# physical_question = {contract.physical_question}",
        "# Product controls:",
    ]
    for fragment in contract.control_fragments:
        if fragment.audience == ControlAudience.PRODUCT:
            lines.append(
                f"# - {fragment.control_id} = {fragment.selected_value}: "
                f"{fragment.cm1_mapping_notes}"
            )
    return "\n".join(lines) + "\n"


def _diagnostic_names(scenario: ScenarioTemplate) -> tuple[str, ...]:
    diagnostics = scenario.expected_diagnostics
    names = []
    if diagnostics.cloud_formed:
        names.append("cloud_formed")
    for field_name in [
        "first_cloud_time",
        "cloud_base_top",
        "max_updraft",
        "cloud_water_summary",
        "rain_onset",
    ]:
        if getattr(diagnostics, field_name) is not None:
            names.append(field_name)
    return tuple(names)
