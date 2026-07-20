"""Bounded matched-run evidence for the Trade Cumulus moisture Control."""

from __future__ import annotations

import importlib
import json
import math
import re
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.bomex_case import (
    CASE_ID,
    DIAGNOSTIC_CADENCE_SECONDS,
    MAPPING_VERSION,
    REQUIRED_OUTPUT_FIELDS,
    SCIENTIFIC_SOURCE_DOI,
    SCIENTIFIC_SOURCE_RECORD,
    BomexCaseError,
    BomexVariant,
    cloud_water_cycle_peak_count,
    generate_bomex_package,
    render_bomex_namelist,
    replace_bomex_namelist_assignment,
    sha256_file,
    sha256_text,
    verified_clean_git_commit,
)
from cloud_chamber.result_ingest import ResultMetadata
from cloud_chamber.run_manifest import load_run_manifest, write_run_manifest
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.trade_cumulus_updraft_lens import (
    CLOUD_THRESHOLD_KG_KG,
    W_MIN_RANGE_M_S,
    W_PERCENTILE,
    WIND_MIN_REFERENCE_M_S,
    WIND_PERCENTILE,
    WIND_STRIDE,
    WIND_TARGET_LEVEL_M,
    center_horizontal_wind_to_scalar_grid,
    center_vertical_velocity_to_scalar_grid,
    rounded_percentile_reference,
    trade_cumulus_updraft_lens_defaults,
)

PRODUCT_SLICE_ID = "trade_cumulus_v1"
COMPARISON_GROUP_ID = "trade_cumulus_moisture_v1"
RECIPE_CANDIDATE_ID = "canonical_bomex_baseline"
CONTROL_ID = "surface_moisture_supply"
OUTPUT_CADENCE_SECONDS = 120
MINIMUM_FREE_BYTES = 8 * 1024**3
STAGE4_RESULT_ID = "result-bomex-370-full-20260719"
STAGE4_ATOL = 1e-10
STAGE4_RTOL = 1e-6
FINAL_THREE_HOUR_START_SECONDS = 10_800.0
PERCENT_DELTA_MINIMUM_DENOMINATOR = 1e-12


class TradeCumulusMoistureComparisonError(RuntimeError):
    """Raised when the bounded matched comparison cannot proceed."""


class TradeCumulusMoistureState(StrEnum):
    BASELINE = "baseline"
    MORE_MOISTURE = "more_moisture"

    @property
    def surface_moisture_flux_g_g_m_s(self) -> float:
        if self is TradeCumulusMoistureState.BASELINE:
            return 5.2e-5
        return 7.8e-5

    @property
    def namelist_value(self) -> str:
        if self is TradeCumulusMoistureState.BASELINE:
            return "5.2e-5"
        return "7.8e-5"


class TradeCumulusRunLength(StrEnum):
    SMOKE = "smoke"
    FULL = "full"

    @property
    def duration_seconds(self) -> int:
        if self is TradeCumulusRunLength.SMOKE:
            return 600
        return 21_600

    @property
    def expected_model_output_count(self) -> int:
        return self.duration_seconds // OUTPUT_CADENCE_SECONDS + 1

    @property
    def expected_diagnostic_output_count(self) -> int:
        return self.duration_seconds // DIAGNOSTIC_CADENCE_SECONDS + 1

    @property
    def bomex_variant(self) -> BomexVariant:
        if self is TradeCumulusRunLength.SMOKE:
            return BomexVariant.SMOKE
        return BomexVariant.FULL


@dataclass(frozen=True)
class TradeCumulusMatchedPackage:
    run_id: str
    control_state: TradeCumulusMoistureState
    run_length: TradeCumulusRunLength
    package_dir: Path
    manifest_path: Path
    case_manifest_path: Path
    namelist_path: Path
    science_settings_sha256: str
    fixed_assumptions_sha256: str
    app_commit: str


class PackageComparisonProof(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comparison_group_id: str = COMPARISON_GROUP_ID
    run_length: str
    baseline_run_id: str
    more_moisture_run_id: str
    differing_namelist_assignments: list[str]
    fixed_assumptions_sha256: str
    baseline_science_settings_sha256: str
    more_moisture_science_settings_sha256: str
    shared_cm1_source_manifest_sha256: str | None = None
    shared_cm1_executable_sha256: str | None = None
    valid: bool


class TimedValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_seconds: float
    value: float | None


class VerticalProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    height_m: list[float]
    values: list[float | None]
    units: str
    method: str
    window: str
    quality: str = "trusted"
    caveats: list[str] = Field(default_factory=list)


class ScalarRunMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float | None
    units: str
    method: str
    window: str
    quality: str = "trusted"
    unavailable_reason: str | None = None
    caveats: list[str] = Field(default_factory=list)


class PairedScalarMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    units: str
    method: str
    window: str
    baseline: float | None
    more_moisture: float | None
    absolute_delta: float | None
    percent_delta: float | None
    percent_delta_unavailable_reason: str | None = None
    quality: str
    caveats: list[str] = Field(default_factory=list)


class RunGateEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    lifecycle_state: str
    product_state: str
    exit_code: int | None
    normal_completion_reported: bool | None
    runtime_integrity_state: str
    runtime_integrity_reason: str
    runtime_integrity_caveats: list[str]
    model_output_count: int
    expected_model_output_count: int
    diagnostic_output_count: int
    expected_diagnostic_output_count: int
    missing_required_fields: list[str]
    required_field_non_finite_counts: dict[str, int]
    intended_surface_moisture_flux_g_g_m_s: float
    emitted_surface_moisture_flux_min_g_g_m_s: float | None
    emitted_surface_moisture_flux_max_g_g_m_s: float | None
    failures: list[str] = Field(default_factory=list)


class TradeCumulusRunEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_version: str = "trade_cumulus_moisture_run_evidence_v1"
    product_slice_id: str = PRODUCT_SLICE_ID
    comparison_group_id: str = COMPARISON_GROUP_ID
    case_id: str = CASE_ID
    recipe_candidate_id: str = RECIPE_CANDIDATE_ID
    control_id: str = CONTROL_ID
    control_state: str
    run_length: str
    run_id: str
    result_id: str
    app_commit: str
    surface_moisture_flux_g_g_m_s: float
    duration_seconds: int
    output_cadence_seconds: int = OUTPUT_CADENCE_SECONDS
    diagnostic_cadence_seconds: int = DIAGNOSTIC_CADENCE_SECONDS
    wall_clock_seconds: float | None = None
    cm1_reported_runtime_seconds: float | None = None
    output_bytes: int
    gate: RunGateEvidence
    scalar_metrics: dict[str, ScalarRunMetric]
    time_series: dict[str, list[TimedValue]]
    vertical_profiles: dict[str, VerticalProfile]
    final_domain_mean_profiles: dict[str, VerticalProfile]
    forcing_diagnostics: dict[str, dict[str, float | None]]
    forcing_and_transport_fields_available: list[str]
    available_fields: list[str]
    caveats: list[str] = Field(default_factory=list)

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2) + "\n"


class Stage4FieldDifference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    maximum_absolute_difference: float
    maximum_relative_difference: float


class Stage4FirstFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_seconds: float
    field: str
    index: list[int]
    stage4_value: float
    new_baseline_value: float
    absolute_difference: float
    allowed_difference: float


class Stage4ConsistencyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preserved_result_id: str
    new_baseline_result_id: str
    common_times_seconds: list[float]
    absolute_tolerance: float = STAGE4_ATOL
    relative_tolerance: float = STAGE4_RTOL
    field_differences: list[Stage4FieldDifference]
    first_failure: Stage4FirstFailure | None = None
    passed: bool


class JointLensPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline_result_id: str
    more_moisture_result_id: str
    baseline_default_time_index: int
    baseline_default_time_seconds: float | None
    baseline_default_plane_index: int
    baseline_default_plane_coordinate: float | None
    baseline_default_plane_units: str | None
    inherited_variant_time_index: int
    inherited_variant_plane_index: int
    wind_target_level_m: float = WIND_TARGET_LEVEL_M
    wind_level_index: int
    wind_actual_level_m: float
    wind_stride: int = WIND_STRIDE
    cloud_threshold_kg_kg: float = CLOUD_THRESHOLD_KG_KG
    joint_w_range_min_m_s: float
    joint_w_range_max_m_s: float
    joint_perturbation_wind_reference_m_s: float
    joint_total_wind_reference_m_s: float
    coordinate_compatibility: str
    field_availability: dict[str, list[str]]


class TradeCumulusPairedEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_version: str = "trade_cumulus_moisture_comparison_evidence_v1"
    evidence_state: Literal[
        "matched_runs_valid",
        "baseline_invalid",
        "more_moisture_invalid",
        "comparison_inconclusive_missing_evidence",
    ]
    implementation_commit: str
    baseline: TradeCumulusRunEvidence
    more_moisture: TradeCumulusRunEvidence
    scalar_metrics: dict[str, PairedScalarMetric]
    exact_time_pairing: dict[str, list[TimedValue]]
    stage4_consistency: Stage4ConsistencyEvidence
    lens_preparation: JointLensPreparation
    estimated_full_pair_bytes: int
    actual_full_pair_bytes: int
    runtime_local_evidence_path: str | None = None
    caveats: list[str] = Field(default_factory=list)

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2) + "\n"


def render_trade_cumulus_matched_namelist(
    reference_text: str,
    control_state: TradeCumulusMoistureState,
    run_length: TradeCumulusRunLength,
) -> str:
    """Render one of the four approved matched-run namelists."""
    rendered = render_bomex_namelist(reference_text, run_length.bomex_variant)
    rendered = replace_bomex_namelist_assignment(rendered, "tapfrq", f"{OUTPUT_CADENCE_SECONDS}.0")
    rendered = replace_bomex_namelist_assignment(
        rendered, "diagfrq", f"{DIAGNOSTIC_CADENCE_SECONDS}.0"
    )
    rendered = replace_bomex_namelist_assignment(
        rendered, "cnst_lhflx", control_state.namelist_value
    )
    return rendered.rstrip() + "\n"


def normalized_trade_cumulus_science_namelist(namelist_text: str) -> str:
    """Normalize duration only for state-specific science equivalence."""
    return replace_bomex_namelist_assignment(namelist_text, "timax", "<duration>")


def normalized_trade_cumulus_fixed_assumptions_namelist(namelist_text: str) -> str:
    """Normalize only duration and the approved moisture Control."""
    normalized = normalized_trade_cumulus_science_namelist(namelist_text)
    return replace_bomex_namelist_assignment(normalized, "cnst_lhflx", "<surface_moisture_control>")


def generate_trade_cumulus_matched_package(
    *,
    settings: CloudChamberSettings,
    control_state: TradeCumulusMoistureState,
    run_length: TradeCumulusRunLength,
    run_id: str,
    comparison_group_id: str = COMPARISON_GROUP_ID,
    allow_overwrite: bool = False,
    app_commit: str | None = None,
) -> TradeCumulusMatchedPackage:
    """Generate one exact package in the approved matched comparison."""
    if comparison_group_id != COMPARISON_GROUP_ID:
        raise TradeCumulusMoistureComparisonError(
            f"Unsupported comparison_group_id: {comparison_group_id}"
        )
    try:
        verified_commit = verified_clean_git_commit()
    except BomexCaseError as exc:
        raise TradeCumulusMoistureComparisonError(str(exc)) from exc
    if app_commit is not None and app_commit != verified_commit:
        raise TradeCumulusMoistureComparisonError(
            "Requested app_commit does not match the verified clean Git HEAD."
        )
    try:
        base = generate_bomex_package(
            settings=settings,
            variant=run_length.bomex_variant,
            run_id=run_id,
            allow_overwrite=allow_overwrite,
        )
    except BomexCaseError as exc:
        raise TradeCumulusMoistureComparisonError(str(exc)) from exc

    try:
        manifest = load_run_manifest(base.manifest_path)
        paths = {
            "manifest": base.manifest_path,
            "case_manifest": base.case_manifest_path,
            "namelist": base.package_dir / "namelist.input",
            "input_sounding": base.package_dir / "input_sounding",
            "report": base.package_dir / "dry_run_report.json",
            "runtime_checklist": base.package_dir / "runtime_file_checklist.json",
        }
        provenance = manifest.run_configuration["cm1_provenance"]
        reference_path = Path(str(provenance["bundled_bomex_namelist_path"]))
        namelist_text = render_trade_cumulus_matched_namelist(
            reference_path.read_text(), control_state, run_length
        )
        paths["namelist"].write_text(namelist_text)
        generated_hashes = {
            "namelist.input": sha256_text(namelist_text),
            "input_sounding": sha256_file(paths["input_sounding"]),
            "runtime_file_checklist.json": sha256_file(paths["runtime_checklist"]),
        }
        science_hash = sha256_text(normalized_trade_cumulus_science_namelist(namelist_text))
        fixed_hash = sha256_text(normalized_trade_cumulus_fixed_assumptions_namelist(namelist_text))
        fixed_assumptions = _fixed_assumptions()
        changed_assumptions = {
            "control_id": CONTROL_ID,
            "control_state": control_state.value,
            "surface_moisture_flux_g_g_m_s": control_state.surface_moisture_flux_g_g_m_s,
        }
        case_manifest: dict[str, Any] = {
            "case_id": CASE_ID,
            "mapping_version": MAPPING_VERSION,
            "authority_state": "stage5b2_matched_evidence_not_product_graduation",
            "product_slice_id": PRODUCT_SLICE_ID,
            "comparison_group_id": COMPARISON_GROUP_ID,
            "recipe_candidate_id": RECIPE_CANDIDATE_ID,
            "control_id": CONTROL_ID,
            "control_state": control_state.value,
            "run_length": run_length.value,
            "duration_seconds": run_length.duration_seconds,
            "surface_moisture_flux_g_g_m_s": control_state.surface_moisture_flux_g_g_m_s,
            "changed_assumptions": changed_assumptions,
            "fixed_assumptions": fixed_assumptions,
            "scientific_sources": [SCIENTIFIC_SOURCE_DOI, SCIENTIFIC_SOURCE_RECORD],
            "cm1_translation": {
                "testcase": 3,
                "isnd": 19,
                "iwnd": 9,
                "ptype": 6,
                "v_t_m_s": 0.0,
                "cloud_liquid_output_field": "ql",
                "output_format": "netcdf",
                "output_cadence_seconds": OUTPUT_CADENCE_SECONDS,
                "diagnostic_cadence_seconds": DIAGNOSTIC_CADENCE_SECONDS,
            },
            "cm1_provenance": provenance,
            "cloud_chamber_commit": verified_commit,
            "generated_input_sha256": generated_hashes,
            "generated_forcing_input_sha256": {},
            "science_settings_sha256": science_hash,
            "fixed_assumptions_sha256": fixed_hash,
            "unsupported_components": [],
        }
        _write_json(paths["case_manifest"], case_manifest)
        generated_hashes["case_manifest.json"] = sha256_file(paths["case_manifest"])

        run_configuration = dict(manifest.run_configuration)
        run_configuration.update(
            {
                "product_slice_id": PRODUCT_SLICE_ID,
                "comparison_group_id": COMPARISON_GROUP_ID,
                "recipe_candidate_id": RECIPE_CANDIDATE_ID,
                "control_id": CONTROL_ID,
                "control_state": control_state.value,
                "surface_moisture_flux_g_g_m_s": (control_state.surface_moisture_flux_g_g_m_s),
                "changed_assumptions": changed_assumptions,
                "fixed_assumptions": fixed_assumptions,
                "fixed_assumptions_sha256": fixed_hash,
                "science_settings_sha256": science_hash,
                "generated_input_sha256": generated_hashes,
                "run_length": run_length.value,
                "variant": run_length.value,
                "duration_seconds": run_length.duration_seconds,
                "output_cadence_seconds": OUTPUT_CADENCE_SECONDS,
                "diagnostic_cadence_seconds": DIAGNOSTIC_CADENCE_SECONDS,
                "expected_model_output_count": run_length.expected_model_output_count,
                "expected_diagnostic_output_count": (run_length.expected_diagnostic_output_count),
            }
        )
        updated_manifest = manifest.model_copy(
            update={
                "controls": {
                    "control_id": CONTROL_ID,
                    "control_state": control_state.value,
                    "surface_moisture_flux_g_g_m_s": (control_state.surface_moisture_flux_g_g_m_s),
                },
                "run_configuration": run_configuration,
                "physical_question": (
                    "How does stronger surface moisture supply change the trade-cumulus field?"
                ),
                "app": manifest.app.model_copy(update={"commit": verified_commit}),
                "user": manifest.user.model_copy(
                    update={
                        "name": (
                            "Trade Cumulus moisture comparison "
                            f"{control_state.value} ({run_length.value})"
                        )
                    }
                ),
                "run_recipe": None,
                "run_limitations": [
                    "stage5b2_matched_evidence_not_product_graduation",
                    "one_deterministic_les_realization_per_control_state",
                    "individual_clouds_are_not_paired_one_to_one",
                ],
                "manual_validation_status": "stage5b2_evidence_pending",
            }
        )
        write_run_manifest(paths["manifest"], updated_manifest)
        report = {
            "status": "packaged_not_executed",
            "product_slice_id": PRODUCT_SLICE_ID,
            "comparison_group_id": COMPARISON_GROUP_ID,
            "case_id": CASE_ID,
            "recipe_candidate_id": RECIPE_CANDIDATE_ID,
            "control_id": CONTROL_ID,
            "control_state": control_state.value,
            "run_length": run_length.value,
            "run_id": run_id,
            "surface_moisture_flux_g_g_m_s": control_state.surface_moisture_flux_g_g_m_s,
            "duration_seconds": run_length.duration_seconds,
            "output_cadence_seconds": OUTPUT_CADENCE_SECONDS,
            "diagnostic_cadence_seconds": DIAGNOSTIC_CADENCE_SECONDS,
            "expected_model_output_count": run_length.expected_model_output_count,
            "expected_diagnostic_output_count": run_length.expected_diagnostic_output_count,
            "changed_assumptions": changed_assumptions,
            "fixed_assumptions": fixed_assumptions,
            "generated_input_sha256": generated_hashes,
            "science_settings_sha256": science_hash,
            "fixed_assumptions_sha256": fixed_hash,
            "cloud_chamber_commit": verified_commit,
            "cm1_release": provenance["release"],
            "cm1_executable_sha256": provenance["executable_sha256"],
            "source_manifest_sha256": provenance["source_manifest_sha256"],
            "required_output_fields": list(REQUIRED_OUTPUT_FIELDS),
            "run_recipe": None,
            "notes": "Generated package is configured evidence, not scientific success.",
        }
        _write_json(paths["report"], report)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        shutil.rmtree(base.package_dir, ignore_errors=True)
        raise TradeCumulusMoistureComparisonError(
            f"Unable to specialize the canonical BOMEX package: {exc}"
        ) from exc

    return TradeCumulusMatchedPackage(
        run_id=run_id,
        control_state=control_state,
        run_length=run_length,
        package_dir=base.package_dir,
        manifest_path=base.manifest_path,
        case_manifest_path=base.case_manifest_path,
        namelist_path=paths["namelist"],
        science_settings_sha256=science_hash,
        fixed_assumptions_sha256=fixed_hash,
        app_commit=verified_commit,
    )


def compare_matched_packages(
    baseline: TradeCumulusMatchedPackage,
    more_moisture: TradeCumulusMatchedPackage,
) -> PackageComparisonProof:
    """Fail closed unless one same-length pair differs only in the approved Control."""
    if baseline.control_state is not TradeCumulusMoistureState.BASELINE:
        raise TradeCumulusMoistureComparisonError("The baseline package has the wrong state.")
    if more_moisture.control_state is not TradeCumulusMoistureState.MORE_MOISTURE:
        raise TradeCumulusMoistureComparisonError("The More Moisture package has the wrong state.")
    if baseline.run_length is not more_moisture.run_length:
        raise TradeCumulusMoistureComparisonError("Matched packages must use one run length.")
    differences = namelist_difference_names(
        baseline.namelist_path.read_text(), more_moisture.namelist_path.read_text()
    )
    if differences != ["cnst_lhflx"]:
        raise TradeCumulusMoistureComparisonError(
            f"Matched package proof failed: unauthorized namelist differences {differences}."
        )
    baseline_manifest = load_run_manifest(baseline.manifest_path)
    variant_manifest = load_run_manifest(more_moisture.manifest_path)
    baseline_configuration = baseline_manifest.run_configuration
    variant_configuration = variant_manifest.run_configuration
    baseline_provenance = baseline_configuration.get("cm1_provenance")
    variant_provenance = variant_configuration.get("cm1_provenance")
    provenance_matches = baseline_provenance == variant_provenance
    fixed_records_match = baseline_configuration.get(
        "fixed_assumptions"
    ) == variant_configuration.get("fixed_assumptions")
    baseline_hashes = baseline_configuration.get("generated_input_sha256")
    variant_hashes = variant_configuration.get("generated_input_sha256")
    fixed_generated_inputs_match = (
        isinstance(baseline_hashes, dict)
        and isinstance(variant_hashes, dict)
        and all(
            baseline_hashes.get(name) == variant_hashes.get(name)
            for name in ("input_sounding", "runtime_file_checklist.json")
        )
    )
    valid = (
        differences == ["cnst_lhflx"]
        and baseline.fixed_assumptions_sha256 == more_moisture.fixed_assumptions_sha256
        and baseline.science_settings_sha256 != more_moisture.science_settings_sha256
        and baseline.app_commit == more_moisture.app_commit
        and provenance_matches
        and fixed_records_match
        and fixed_generated_inputs_match
    )
    shared_source_hash = (
        str(baseline_provenance.get("source_manifest_sha256"))
        if isinstance(baseline_provenance, dict) and provenance_matches
        else None
    )
    shared_executable_hash = (
        str(baseline_provenance.get("executable_sha256"))
        if isinstance(baseline_provenance, dict) and provenance_matches
        else None
    )
    proof = PackageComparisonProof(
        run_length=baseline.run_length.value,
        baseline_run_id=baseline.run_id,
        more_moisture_run_id=more_moisture.run_id,
        differing_namelist_assignments=differences,
        fixed_assumptions_sha256=baseline.fixed_assumptions_sha256,
        baseline_science_settings_sha256=baseline.science_settings_sha256,
        more_moisture_science_settings_sha256=more_moisture.science_settings_sha256,
        shared_cm1_source_manifest_sha256=shared_source_hash,
        shared_cm1_executable_sha256=shared_executable_hash,
        valid=valid,
    )
    if not valid:
        raise TradeCumulusMoistureComparisonError(
            "Matched package proof failed: " + proof.model_dump_json()
        )
    return proof


def verify_smoke_full_equivalence(
    smoke: TradeCumulusMatchedPackage,
    full: TradeCumulusMatchedPackage,
) -> None:
    """Fail unless one state differs between smoke and full only in duration."""
    if smoke.control_state is not full.control_state:
        raise TradeCumulusMoistureComparisonError("Smoke/full packages use different states.")
    if smoke.run_length is not TradeCumulusRunLength.SMOKE:
        raise TradeCumulusMoistureComparisonError("Expected a smoke package.")
    if full.run_length is not TradeCumulusRunLength.FULL:
        raise TradeCumulusMoistureComparisonError("Expected a full package.")
    differences = namelist_difference_names(
        smoke.namelist_path.read_text(), full.namelist_path.read_text()
    )
    if differences != ["timax"]:
        raise TradeCumulusMoistureComparisonError(
            f"Smoke/full namelists differ outside duration: {differences}"
        )
    if smoke.science_settings_sha256 != full.science_settings_sha256:
        raise TradeCumulusMoistureComparisonError(
            "Smoke/full state-specific science hashes do not match."
        )
    if smoke.fixed_assumptions_sha256 != full.fixed_assumptions_sha256:
        raise TradeCumulusMoistureComparisonError(
            "Smoke/full fixed-assumption hashes do not match."
        )


def namelist_difference_names(left: str, right: str) -> list[str]:
    """Return sorted assignments whose generated values differ."""
    left_values = _namelist_assignments(left)
    right_values = _namelist_assignments(right)
    if left_values.keys() != right_values.keys():
        missing_left = sorted(right_values.keys() - left_values.keys())
        missing_right = sorted(left_values.keys() - right_values.keys())
        raise TradeCumulusMoistureComparisonError(
            f"Namelist assignment sets differ; left missing {missing_left}, "
            f"right missing {missing_right}."
        )
    return sorted(name for name in left_values if left_values[name] != right_values[name])


def pair_scalar_metric(
    baseline: ScalarRunMetric,
    more_moisture: ScalarRunMetric,
) -> PairedScalarMetric:
    """Pair one identically defined scalar metric without inventing missing values."""
    if (baseline.units, baseline.method, baseline.window) != (
        more_moisture.units,
        more_moisture.method,
        more_moisture.window,
    ):
        raise TradeCumulusMoistureComparisonError(
            "Paired scalar metrics must share units, method, and window."
        )
    absolute_delta: float | None = None
    percent_delta: float | None = None
    unavailable_reason: str | None = None
    if baseline.value is None or more_moisture.value is None:
        unavailable_reason = (
            baseline.unavailable_reason
            or more_moisture.unavailable_reason
            or "metric_value_unavailable"
        )
    else:
        absolute_delta = more_moisture.value - baseline.value
        if abs(baseline.value) <= PERCENT_DELTA_MINIMUM_DENOMINATOR:
            unavailable_reason = "baseline_denominator_zero_or_near_zero"
        else:
            percent_delta = absolute_delta / baseline.value * 100.0
    qualities = {baseline.quality, more_moisture.quality}
    quality = "trusted" if qualities == {"trusted"} else "+".join(sorted(qualities))
    return PairedScalarMetric(
        units=baseline.units,
        method=baseline.method,
        window=baseline.window,
        baseline=baseline.value,
        more_moisture=more_moisture.value,
        absolute_delta=absolute_delta,
        percent_delta=percent_delta,
        percent_delta_unavailable_reason=unavailable_reason,
        quality=quality,
        caveats=sorted(set(baseline.caveats + more_moisture.caveats)),
    )


def thickness_weighted_layer_mean(
    profile: np.ndarray[Any, Any],
    height_centers_m: np.ndarray[Any, Any],
    *,
    bottom_m: float = 0.0,
    top_m: float = 1000.0,
) -> float | None:
    """Average a scalar-level profile using geometric overlap with one height layer."""
    values = np.asarray(profile, dtype=float).reshape(-1)
    centers = np.asarray(height_centers_m, dtype=float).reshape(-1)
    if values.size != centers.size or not values.size:
        raise TradeCumulusMoistureComparisonError(
            "Profile and height-center arrays must have the same nonzero length."
        )
    if not np.all(np.isfinite(centers)) or np.any(np.diff(centers) <= 0.0):
        raise TradeCumulusMoistureComparisonError(
            "Height centers must be finite and strictly increasing."
        )
    if top_m <= bottom_m:
        raise TradeCumulusMoistureComparisonError("Layer top must be above layer bottom.")
    interfaces = np.empty(centers.size + 1, dtype=float)
    if centers.size == 1:
        interfaces[:] = (bottom_m, top_m)
    else:
        interfaces[1:-1] = 0.5 * (centers[:-1] + centers[1:])
        interfaces[0] = max(0.0, centers[0] - 0.5 * (centers[1] - centers[0]))
        interfaces[-1] = centers[-1] + 0.5 * (centers[-1] - centers[-2])
    weights = np.maximum(
        0.0,
        np.minimum(interfaces[1:], top_m) - np.maximum(interfaces[:-1], bottom_m),
    )
    finite = np.isfinite(values) & (weights > 0.0)
    if not np.any(finite):
        return None
    return float(np.sum(values[finite] * weights[finite]) / np.sum(weights[finite]))


def pair_exact_time_series(
    baseline: list[TimedValue],
    more_moisture: list[TimedValue],
) -> list[TimedValue]:
    """Return variant-minus-baseline values only for identical ordered model times."""
    baseline_times = [point.time_seconds for point in baseline]
    variant_times = [point.time_seconds for point in more_moisture]
    if baseline_times != variant_times:
        raise TradeCumulusMoistureComparisonError(
            "Time-series pairing requires exact identical model times; interpolation is forbidden."
        )
    paired: list[TimedValue] = []
    for baseline_point, variant_point in zip(baseline, more_moisture, strict=True):
        value = None
        if baseline_point.value is not None and variant_point.value is not None:
            value = variant_point.value - baseline_point.value
        paired.append(TimedValue(time_seconds=baseline_point.time_seconds, value=value))
    return paired


def build_trade_cumulus_run_evidence(
    result: ResultMetadata,
    package: TradeCumulusMatchedPackage,
    *,
    wall_clock_seconds: float | None = None,
) -> TradeCumulusRunEvidence:
    """Calculate the approved metrics and fail-closed run gate for one matched run."""
    if result.run_id != package.run_id:
        raise TradeCumulusMoistureComparisonError(
            f"Result {result.result_id} does not belong to package {package.run_id}."
        )
    manifest = load_run_manifest(package.manifest_path)
    frames = _analyze_model_frames(result)
    forcing, forcing_fields, diagnostic_times = _analyze_diagnostic_frames(result)
    cm1_reported_runtime_seconds = _cm1_reported_runtime_seconds(manifest)
    gate = _build_run_gate(
        result=result,
        package=package,
        manifest=manifest,
        frame_analysis=frames,
        forcing=forcing,
        diagnostic_times=diagnostic_times,
    )
    final_indices = [
        index
        for index, time_seconds in enumerate(frames.times_seconds)
        if time_seconds >= FINAL_THREE_HOUR_START_SECONDS
    ]
    final_cwp = [frames.domain_mean_cwp[index] for index in final_indices]
    final_cover = [frames.total_cloud_cover_percent[index] for index in final_indices]
    final_cloud_profiles = [frames.cloud_fraction_profiles[index] for index in final_indices]
    final_cloud_w_profiles = [frames.cloud_conditioned_w_profiles[index] for index in final_indices]
    time_mean_cloud_profile = _mean_optional_profiles(final_cloud_profiles)
    cloud_w_profile = _mean_optional_profiles(final_cloud_w_profiles)
    peak_fraction, peak_height = _profile_peak(time_mean_cloud_profile, frames.height_m)
    cloud = result.diagnostics.cloud if result.diagnostics is not None else None
    coherent_top_series = (
        [
            TimedValue(time_seconds=float(point.time_seconds), value=point.value)
            for point in cloud.coherent_cloud_object_top_time_series
            if point.time_seconds is not None
        ]
        if cloud is not None
        else []
    )
    final_coherent_tops = [
        point.value
        for point in coherent_top_series
        if point.time_seconds >= FINAL_THREE_HOUR_START_SECONDS and point.value is not None
    ]
    positive_cloud_fraction = (
        frames.final_positive_cloudy_count / frames.final_cloudy_count * 100.0
        if frames.final_cloudy_count
        else None
    )
    scalar_metrics = {
        "first_isolated_cloud_liquid_time": _metric(
            frames.first_isolated_cloud_time_seconds,
            "s",
            "first model frame with any finite ql >= 1e-6 kg/kg",
            "full run",
        ),
        "first_coherent_cloud_time": _metric(
            cloud.first_cloud_time_seconds if cloud is not None else None,
            "s",
            "first ingested frame with at least 10 cloud-liquid grid cells",
            "full run",
            unavailable_reason="coherent_cloud_diagnostic_unavailable",
        ),
        "mean_total_cloud_cover_final_three_hours": _metric(
            _finite_mean_list(final_cover),
            "%",
            "time mean of horizontal columns containing ql >= 1e-6 kg/kg",
            "time >= 10800 s",
        ),
        "time_mean_cloud_fraction_profile_peak": _metric(
            peak_fraction,
            "%",
            "peak of final-three-hour time-mean horizontal cloud-fraction profile",
            "time >= 10800 s",
        ),
        "time_mean_cloud_fraction_profile_peak_height": _metric(
            peak_height,
            "m",
            "height of first maximum in final-three-hour time-mean cloud-fraction profile",
            "time >= 10800 s",
        ),
        "domain_mean_cwp_final_three_hour_mean": _metric(
            _finite_mean_list(final_cwp),
            "kg/m^2",
            "time mean of horizontal domain-mean cwp",
            "time >= 10800 s",
        ),
        "domain_mean_cwp_final_three_hour_minimum": _metric(
            _finite_min_list(final_cwp),
            "kg/m^2",
            "minimum horizontal domain-mean cwp",
            "time >= 10800 s",
        ),
        "domain_mean_cwp_final_three_hour_maximum": _metric(
            _finite_max_list(final_cwp),
            "kg/m^2",
            "maximum horizontal domain-mean cwp",
            "time >= 10800 s",
        ),
        "cloud_water_growth_decay_peak_count": _metric(
            float(cloud_water_cycle_peak_count(frames.domain_mean_cwp)),
            "count",
            "Stage 4 local-peak count above 10% of full-run maximum cwp",
            "full run",
        ),
        "coherent_cloud_base": _metric(
            cloud.coherent_cloud_object_base_m if cloud is not None else None,
            "m",
            "lowest supported coherent cloud-object level from ingest diagnostics",
            "full run",
            unavailable_reason="coherent_cloud_base_unavailable",
        ),
        "coherent_cloud_top_maximum": _metric(
            cloud.coherent_cloud_object_top_m if cloud is not None else None,
            "m",
            "highest supported coherent cloud-object level from ingest diagnostics",
            "full run",
            unavailable_reason="coherent_cloud_top_unavailable",
        ),
        "coherent_cloud_top_final_three_hour_mean": _metric(
            _finite_mean_list(final_coherent_tops),
            "m",
            "mean supported coherent cloud-object top",
            "time >= 10800 s",
            unavailable_reason="final_three_hour_coherent_cloud_top_unavailable",
        ),
        "coherent_cloud_top_final_three_hour_minimum": _metric(
            _finite_min_list(final_coherent_tops),
            "m",
            "minimum supported coherent cloud-object top",
            "time >= 10800 s",
            unavailable_reason="final_three_hour_coherent_cloud_top_unavailable",
        ),
        "coherent_cloud_top_final_three_hour_maximum": _metric(
            _finite_max_list(final_coherent_tops),
            "m",
            "maximum supported coherent cloud-object top",
            "time >= 10800 s",
            unavailable_reason="final_three_hour_coherent_cloud_top_unavailable",
        ),
        "maximum_cloud_liquid": _metric(
            frames.maximum_ql,
            "kg/kg",
            "maximum finite raw ql value",
            "full run",
        ),
        "raw_w_minimum": _metric(
            frames.raw_w_minimum,
            "m/s",
            "minimum finite raw staggered w value",
            "full run",
        ),
        "raw_w_maximum": _metric(
            frames.raw_w_maximum,
            "m/s",
            "maximum finite raw staggered w value",
            "full run",
        ),
        "cloudy_scalar_cells_with_positive_centered_w": _metric(
            positive_cloud_fraction,
            "%",
            "pooled fraction of cloudy scalar cells with centered w > 0",
            "time >= 10800 s",
            unavailable_reason="no_cloudy_scalar_cells_in_window",
        ),
        "qv_0_1000m_final_three_hour_mean": _metric(
            _finite_mean_list([frames.low_level_qv[index] for index in final_indices]),
            "kg/kg",
            "time mean of thickness-weighted horizontal/domain qv over 0-1000 m",
            "time >= 10800 s",
        ),
        "th_0_1000m_final_three_hour_mean": _metric(
            _finite_mean_list([frames.low_level_th[index] for index in final_indices]),
            "K",
            "time mean of thickness-weighted horizontal/domain th over 0-1000 m",
            "time >= 10800 s",
        ),
        "wall_clock_runtime": _metric(
            wall_clock_seconds,
            "s",
            "monotonic wall-clock duration around local CM1 launch and completion",
            "process execution",
            unavailable_reason="wall_clock_runtime_not_recorded",
        ),
        "cm1_reported_runtime": _metric(
            cm1_reported_runtime_seconds,
            "s",
            "CM1 terminal Total time value parsed from the process stdout log",
            "process execution",
            unavailable_reason="cm1_reported_runtime_not_recorded",
        ),
        "netcdf_output_storage": _metric(
            float(frames.output_bytes),
            "bytes",
            "sum of ingested NetCDF artifact sizes",
            "completed run",
        ),
    }
    time_series = {
        "domain_mean_cwp": _timed_values(frames.times_seconds, frames.domain_mean_cwp),
        "total_cloud_cover_percent": _timed_values(
            frames.times_seconds, frames.total_cloud_cover_percent
        ),
        "qv_0_1000m": _timed_values(frames.times_seconds, frames.low_level_qv),
        "th_0_1000m": _timed_values(frames.times_seconds, frames.low_level_th),
        "coherent_cloud_top": coherent_top_series,
    }
    vertical_profiles = {
        "cloud_fraction_final_three_hours": VerticalProfile(
            height_m=frames.height_m,
            values=time_mean_cloud_profile,
            units="%",
            method="time mean of horizontal ql >= 1e-6 kg/kg fraction by scalar level",
            window="time >= 10800 s",
        ),
        "cloud_conditioned_centered_w_final_three_hours": VerticalProfile(
            height_m=frames.height_m,
            values=cloud_w_profile,
            units="m/s",
            method="time mean of per-frame centered w mean over cloudy scalar cells by level",
            window="time >= 10800 s",
            quality="trusted"
            if any(value is not None for value in cloud_w_profile)
            else "unavailable",
            caveats=(
                [] if any(value is not None for value in cloud_w_profile) else ["no_cloudy_cells"]
            ),
        ),
    }
    final_profiles = {
        name: VerticalProfile(
            height_m=frames.height_m,
            values=values,
            units="kg/kg" if name == "qv" else "K" if name == "th" else "m/s",
            method="horizontal domain mean on the final scalar-grid frame",
            window=f"time = {frames.times_seconds[-1]:g} s",
        )
        for name, values in frames.final_domain_mean_profiles.items()
    }
    caveats = sorted(set(result.runtime_integrity.caveats))
    return TradeCumulusRunEvidence(
        control_state=package.control_state.value,
        run_length=package.run_length.value,
        run_id=result.run_id,
        result_id=result.result_id,
        app_commit=package.app_commit,
        surface_moisture_flux_g_g_m_s=(package.control_state.surface_moisture_flux_g_g_m_s),
        duration_seconds=package.run_length.duration_seconds,
        wall_clock_seconds=wall_clock_seconds,
        cm1_reported_runtime_seconds=cm1_reported_runtime_seconds,
        output_bytes=frames.output_bytes,
        gate=gate,
        scalar_metrics=scalar_metrics,
        time_series=time_series,
        vertical_profiles=vertical_profiles,
        final_domain_mean_profiles=final_profiles,
        forcing_diagnostics=forcing,
        forcing_and_transport_fields_available=forcing_fields,
        available_fields=sorted(result.variables),
        caveats=caveats,
    )


def write_trade_cumulus_run_evidence(path: Path, evidence: TradeCumulusRunEvidence) -> None:
    path.write_text(evidence.to_json_text())


def build_paired_evidence(
    baseline: TradeCumulusRunEvidence,
    more_moisture: TradeCumulusRunEvidence,
    *,
    implementation_commit: str,
    stage4_consistency: Stage4ConsistencyEvidence,
    lens_preparation: JointLensPreparation,
    estimated_full_pair_bytes: int,
) -> TradeCumulusPairedEvidence:
    """Pair identically defined metrics after both full-run gates pass."""
    if baseline.control_state != TradeCumulusMoistureState.BASELINE.value:
        raise TradeCumulusMoistureComparisonError("Baseline evidence has the wrong state.")
    if more_moisture.control_state != TradeCumulusMoistureState.MORE_MOISTURE.value:
        raise TradeCumulusMoistureComparisonError("Variant evidence has the wrong state.")
    if (
        baseline.app_commit != implementation_commit
        or more_moisture.app_commit != implementation_commit
    ):
        raise TradeCumulusMoistureComparisonError(
            "Run evidence does not share the exact implementation commit."
        )
    metric_names = baseline.scalar_metrics.keys() & more_moisture.scalar_metrics.keys()
    paired_metrics = {
        name: pair_scalar_metric(baseline.scalar_metrics[name], more_moisture.scalar_metrics[name])
        for name in sorted(metric_names)
    }
    series_names = baseline.time_series.keys() & more_moisture.time_series.keys()
    paired_series = {
        name: pair_exact_time_series(baseline.time_series[name], more_moisture.time_series[name])
        for name in sorted(series_names)
    }
    if not baseline.gate.valid:
        state: Literal[
            "matched_runs_valid",
            "baseline_invalid",
            "more_moisture_invalid",
            "comparison_inconclusive_missing_evidence",
        ] = "baseline_invalid"
    elif not more_moisture.gate.valid:
        state = "more_moisture_invalid"
    elif not stage4_consistency.passed:
        state = "comparison_inconclusive_missing_evidence"
    else:
        state = "matched_runs_valid"
    return TradeCumulusPairedEvidence(
        evidence_state=state,
        implementation_commit=implementation_commit,
        baseline=baseline,
        more_moisture=more_moisture,
        scalar_metrics=paired_metrics,
        exact_time_pairing=paired_series,
        stage4_consistency=stage4_consistency,
        lens_preparation=lens_preparation,
        estimated_full_pair_bytes=estimated_full_pair_bytes,
        actual_full_pair_bytes=baseline.output_bytes + more_moisture.output_bytes,
        caveats=[
            "one_deterministic_les_realization_per_control_state",
            "individual_clouds_are_not_paired_one_to_one",
            "comparison_evidence_does_not_establish_product_graduation",
        ],
    )


def write_paired_evidence(path: Path, evidence: TradeCumulusPairedEvidence) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(evidence.to_json_text())


@dataclass(frozen=True)
class _ModelFrameAnalysis:
    times_seconds: list[float]
    height_m: list[float]
    domain_mean_cwp: list[float]
    total_cloud_cover_percent: list[float]
    cloud_fraction_profiles: list[list[float | None]]
    cloud_conditioned_w_profiles: list[list[float | None]]
    low_level_qv: list[float]
    low_level_th: list[float]
    final_domain_mean_profiles: dict[str, list[float | None]]
    first_isolated_cloud_time_seconds: float | None
    maximum_ql: float | None
    raw_w_minimum: float | None
    raw_w_maximum: float | None
    final_cloudy_count: int
    final_positive_cloudy_count: int
    non_finite_counts: dict[str, int]
    output_bytes: int


def _analyze_model_frames(result: ResultMetadata) -> _ModelFrameAnalysis:
    xarray = importlib.import_module("xarray")
    times: list[float] = []
    heights: list[float] | None = None
    cwp_means: list[float] = []
    cloud_cover: list[float] = []
    cloud_profiles: list[list[float | None]] = []
    cloud_w_profiles: list[list[float | None]] = []
    low_qv: list[float] = []
    low_th: list[float] = []
    final_profiles: dict[str, list[float | None]] = {}
    first_isolated: float | None = None
    maximum_ql: float | None = None
    raw_w_minimum: float | None = None
    raw_w_maximum: float | None = None
    final_cloudy_count = 0
    final_positive_count = 0
    non_finite_counts = {field: 0 for field in REQUIRED_OUTPUT_FIELDS}
    paths = [Path(path) for path in result.model_output_paths]
    if not paths:
        raise TradeCumulusMoistureComparisonError("Result has no model-output paths.")
    for path in paths:
        dataset = xarray.open_dataset(path, decode_times=False)
        try:
            local_count = _time_count(dataset)
            for local_index in range(local_count):
                ql, scalar_dimensions = _scalar_field(dataset, "ql", local_index)
                qv, qv_dimensions = _scalar_field(dataset, "qv", local_index)
                th, th_dimensions = _scalar_field(dataset, "th", local_index)
                if qv_dimensions != scalar_dimensions or th_dimensions != scalar_dimensions:
                    raise TradeCumulusMoistureComparisonError(
                        "ql, qv, and th do not share one scalar-grid dimension order."
                    )
                w = center_vertical_velocity_to_scalar_grid(
                    dataset, local_index, scalar_dimensions, ql.shape
                )
                u, v = center_horizontal_wind_to_scalar_grid(
                    dataset, local_index, scalar_dimensions, ql.shape
                )
                frame_heights = _coordinate_as_m(dataset, scalar_dimensions[0], ql.shape[0])
                if heights is None:
                    heights = [float(value) for value in frame_heights]
                elif not np.array_equal(np.asarray(heights), frame_heights):
                    raise TradeCumulusMoistureComparisonError(
                        "Model frames do not share identical scalar-level heights."
                    )
                time_seconds = _time_seconds(dataset, local_index)
                if times and time_seconds <= times[-1]:
                    raise TradeCumulusMoistureComparisonError(
                        "Model output times must be finite and strictly increasing."
                    )
                times.append(time_seconds)
                cloud_mask = np.isfinite(ql) & (ql >= CLOUD_THRESHOLD_KG_KG)
                cloudy_count = int(np.count_nonzero(cloud_mask))
                if first_isolated is None and cloudy_count:
                    first_isolated = time_seconds
                level_fraction = np.mean(cloud_mask, axis=(1, 2)) * 100.0
                cloud_profiles.append([float(value) for value in level_fraction])
                cloud_cover.append(float(np.mean(np.any(cloud_mask, axis=0)) * 100.0))
                cloud_w_profiles.append(_cloud_conditioned_profile(w, cloud_mask))
                cwp = _horizontal_field(dataset, "cwp", local_index, scalar_dimensions[1:])
                finite_cwp = cwp[np.isfinite(cwp)]
                if not finite_cwp.size:
                    raise TradeCumulusMoistureComparisonError(
                        f"cwp has no finite values at {time_seconds:g} s."
                    )
                cwp_means.append(float(np.mean(finite_cwp)))
                qv_profile = _horizontal_mean_profile(qv)
                th_profile = _horizontal_mean_profile(th)
                qv_layer = thickness_weighted_layer_mean(qv_profile, frame_heights)
                th_layer = thickness_weighted_layer_mean(th_profile, frame_heights)
                if qv_layer is None or th_layer is None:
                    raise TradeCumulusMoistureComparisonError(
                        f"Low-level qv/th evidence is unavailable at {time_seconds:g} s."
                    )
                low_qv.append(qv_layer)
                low_th.append(th_layer)
                finite_ql = ql[np.isfinite(ql)]
                if finite_ql.size:
                    maximum_ql = _max_optional(maximum_ql, float(np.max(finite_ql)))
                raw_w, _ = _raw_field(dataset, "w", local_index)
                finite_raw_w = raw_w[np.isfinite(raw_w)]
                if finite_raw_w.size:
                    raw_w_minimum = _min_optional(raw_w_minimum, float(np.min(finite_raw_w)))
                    raw_w_maximum = _max_optional(raw_w_maximum, float(np.max(finite_raw_w)))
                for required_field in REQUIRED_OUTPUT_FIELDS:
                    source = _required_field_source(dataset, required_field)
                    if source is None:
                        continue
                    values, _ = _raw_field(dataset, source, local_index)
                    non_finite_counts[required_field] += int(
                        values.size - np.count_nonzero(np.isfinite(values))
                    )
                if time_seconds >= FINAL_THREE_HOUR_START_SECONDS:
                    final_cloudy_count += cloudy_count
                    final_positive_count += int(np.count_nonzero(cloud_mask & (w > 0.0)))
                final_profiles = {
                    "qv": _optional_float_list(qv_profile),
                    "th": _optional_float_list(th_profile),
                    "u": _optional_float_list(_horizontal_mean_profile(u)),
                    "v": _optional_float_list(_horizontal_mean_profile(v)),
                }
        finally:
            dataset.close()
    if heights is None:
        raise TradeCumulusMoistureComparisonError("No readable model frames were analyzed.")
    return _ModelFrameAnalysis(
        times_seconds=times,
        height_m=heights,
        domain_mean_cwp=cwp_means,
        total_cloud_cover_percent=cloud_cover,
        cloud_fraction_profiles=cloud_profiles,
        cloud_conditioned_w_profiles=cloud_w_profiles,
        low_level_qv=low_qv,
        low_level_th=low_th,
        final_domain_mean_profiles=final_profiles,
        first_isolated_cloud_time_seconds=first_isolated,
        maximum_ql=maximum_ql,
        raw_w_minimum=raw_w_minimum,
        raw_w_maximum=raw_w_maximum,
        final_cloudy_count=final_cloudy_count,
        final_positive_cloudy_count=final_positive_count,
        non_finite_counts=non_finite_counts,
        output_bytes=sum(path.stat().st_size for path in map(Path, result.netcdf_paths)),
    )


def _analyze_diagnostic_frames(
    result: ResultMetadata,
) -> tuple[dict[str, dict[str, float | None]], list[str], list[float]]:
    xarray = importlib.import_module("xarray")
    paths = _diagnostic_paths(result)
    fields = (
        "wprof",
        "ptb_frc",
        "qvb_frc",
        "ug",
        "vg",
        "thflux",
        "qvflux",
        "ust",
        "upwp",
        "vpwp",
        "wpwp",
        "ufr",
        "vfr",
        "ptfr",
        "qvfr",
        "ptb_vturbr",
        "qvb_vturbr",
    )
    extrema: dict[str, tuple[float, float]] = {}
    available: set[str] = set()
    times: list[float] = []
    for path in paths:
        dataset = xarray.open_dataset(path, decode_times=False)
        try:
            local_count = _time_count(dataset)
            for local_index in range(local_count):
                time_seconds = _time_seconds(dataset, local_index)
                if times and time_seconds <= times[-1]:
                    raise TradeCumulusMoistureComparisonError(
                        "Diagnostic output times must be finite and strictly increasing."
                    )
                times.append(time_seconds)
                for field in fields:
                    if field not in dataset.data_vars:
                        continue
                    available.add(field)
                    values, _ = _raw_field(dataset, field, local_index)
                    finite = values[np.isfinite(values)]
                    if not finite.size:
                        continue
                    frame_min = float(np.min(finite))
                    frame_max = float(np.max(finite))
                    prior = extrema.get(field)
                    extrema[field] = (
                        min(frame_min, prior[0]) if prior is not None else frame_min,
                        max(frame_max, prior[1]) if prior is not None else frame_max,
                    )
        finally:
            dataset.close()
    summary = {
        field: {
            "min": extrema[field][0] if field in extrema else None,
            "max": extrema[field][1] if field in extrema else None,
        }
        for field in sorted(available)
    }
    return summary, sorted(available), times


def _build_run_gate(
    *,
    result: ResultMetadata,
    package: TradeCumulusMatchedPackage,
    manifest: Any,
    frame_analysis: _ModelFrameAnalysis,
    forcing: dict[str, dict[str, float | None]],
    diagnostic_times: list[float],
) -> RunGateEvidence:
    expected_model = package.run_length.expected_model_output_count
    expected_diagnostic = package.run_length.expected_diagnostic_output_count
    failures: list[str] = []
    if result.source_lifecycle_state != "completed":
        failures.append(f"lifecycle_state:{result.source_lifecycle_state}")
    if result.source_product_state != "completed_cm1_result":
        failures.append(f"product_state:{result.source_product_state}")
    if manifest.execution.exit_code != 0:
        failures.append(f"exit_code:{manifest.execution.exit_code}")
    if result.runtime_integrity.normal_completion_reported is not True:
        failures.append("normal_completion_marker_missing")
    allowed_integrity = result.runtime_integrity.state == "trusted" or (
        result.runtime_integrity.state == "caveated"
        and result.runtime_integrity.caveats == ["runtime_integrity_caveated_underflow_only"]
        and not result.runtime_integrity.fatal_warning_flags
        and not result.runtime_integrity.terminal_non_finite_fields
        and not result.runtime_integrity.stats_sentinel_collapse_detected
    )
    if not allowed_integrity:
        failures.append(f"runtime_integrity:{result.runtime_integrity.state}")
    missing = _missing_required_fields(result.variables)
    if missing:
        failures.append("missing_required_fields:" + ",".join(missing))
    contaminated = {
        field: count for field, count in frame_analysis.non_finite_counts.items() if count
    }
    if contaminated:
        failures.append("required_field_non_finite_values")
    if result.model_output_file_count != expected_model:
        failures.append(f"model_output_count:{result.model_output_file_count}!={expected_model}")
    if len(frame_analysis.times_seconds) != expected_model:
        failures.append(f"model_frame_count:{len(frame_analysis.times_seconds)}!={expected_model}")
    expected_model_times = [
        float(index * OUTPUT_CADENCE_SECONDS) for index in range(expected_model)
    ]
    if frame_analysis.times_seconds != expected_model_times:
        failures.append("model_output_times_do_not_match_120_second_cadence")
    if len(diagnostic_times) != expected_diagnostic:
        failures.append(f"diagnostic_frame_count:{len(diagnostic_times)}!={expected_diagnostic}")
    expected_diagnostic_times = [
        float(index * DIAGNOSTIC_CADENCE_SECONDS) for index in range(expected_diagnostic)
    ]
    if diagnostic_times != expected_diagnostic_times:
        failures.append("diagnostic_output_times_do_not_match_60_second_cadence")
    required_diagnostic_fields = {
        "wprof",
        "ptb_frc",
        "qvb_frc",
        "ug",
        "vg",
        "thflux",
        "qvflux",
        "ust",
    }
    missing_diagnostic_fields = sorted(required_diagnostic_fields - forcing.keys())
    if missing_diagnostic_fields:
        failures.append("missing_required_diagnostic_fields:" + ",".join(missing_diagnostic_fields))
    intended = package.control_state.surface_moisture_flux_g_g_m_s
    emitted = forcing.get("qvflux", {})
    emitted_min = emitted.get("min")
    emitted_max = emitted.get("max")
    if emitted_min is None or emitted_max is None:
        failures.append("surface_moisture_forcing_diagnostic_unavailable")
    elif not (
        math.isclose(emitted_min, intended, rel_tol=1e-6, abs_tol=1e-10)
        and math.isclose(emitted_max, intended, rel_tol=1e-6, abs_tol=1e-10)
    ):
        failures.append(f"surface_moisture_forcing_mismatch:{emitted_min}:{emitted_max}:{intended}")
    namelist_value = _namelist_assignments(package.namelist_path.read_text()).get("cnst_lhflx")
    if namelist_value != package.control_state.namelist_value:
        failures.append(f"namelist_surface_moisture_forcing_mismatch:{namelist_value}")
    return RunGateEvidence(
        valid=not failures,
        lifecycle_state=result.source_lifecycle_state,
        product_state=result.source_product_state,
        exit_code=manifest.execution.exit_code,
        normal_completion_reported=result.runtime_integrity.normal_completion_reported,
        runtime_integrity_state=result.runtime_integrity.state,
        runtime_integrity_reason=result.runtime_integrity.reason,
        runtime_integrity_caveats=result.runtime_integrity.caveats,
        model_output_count=result.model_output_file_count,
        expected_model_output_count=expected_model,
        diagnostic_output_count=len(diagnostic_times),
        expected_diagnostic_output_count=expected_diagnostic,
        missing_required_fields=missing,
        required_field_non_finite_counts=frame_analysis.non_finite_counts,
        intended_surface_moisture_flux_g_g_m_s=intended,
        emitted_surface_moisture_flux_min_g_g_m_s=emitted_min,
        emitted_surface_moisture_flux_max_g_g_m_s=emitted_max,
        failures=failures,
    )


def compare_stage4_baseline(
    preserved: ResultMetadata,
    new_baseline: ResultMetadata,
) -> Stage4ConsistencyEvidence:
    """Compare exact common 600-second fields with explicit grid alignment."""
    xarray = importlib.import_module("xarray")
    preserved_frames = _result_frame_locations(preserved)
    baseline_frames = _result_frame_locations(new_baseline)
    expected_times = [float(value) for value in range(0, 21_601, 600)]
    common_times = [
        time_seconds
        for time_seconds in expected_times
        if time_seconds in preserved_frames and time_seconds in baseline_frames
    ]
    if common_times != expected_times:
        missing = sorted(set(expected_times) - set(common_times))
        raise TradeCumulusMoistureComparisonError(
            f"Stage 4 consistency check lacks required common times: {missing}"
        )
    fields = ("ql", "qv", "th", "w", "cwp")
    maxima = {field: [0.0, 0.0] for field in fields}
    first_failure: Stage4FirstFailure | None = None
    for time_seconds in common_times:
        preserved_location = preserved_frames[time_seconds]
        baseline_location = baseline_frames[time_seconds]
        preserved_dataset = xarray.open_dataset(preserved_location[0], decode_times=False)
        baseline_dataset = xarray.open_dataset(baseline_location[0], decode_times=False)
        try:
            preserved_values = _comparison_fields(preserved_dataset, preserved_location[1])
            baseline_values = _comparison_fields(baseline_dataset, baseline_location[1])
            for field in fields:
                reference, reference_coordinates = preserved_values[field]
                candidate, candidate_coordinates = baseline_values[field]
                if reference.shape != candidate.shape:
                    raise TradeCumulusMoistureComparisonError(
                        f"Stage 4 {field} shape mismatch at {time_seconds:g} s."
                    )
                if len(reference_coordinates) != len(candidate_coordinates) or any(
                    not np.array_equal(left, right)
                    for left, right in zip(
                        reference_coordinates, candidate_coordinates, strict=True
                    )
                ):
                    raise TradeCumulusMoistureComparisonError(
                        f"Stage 4 {field} coordinate mismatch at {time_seconds:g} s."
                    )
                if not np.all(np.isfinite(reference)) or not np.all(np.isfinite(candidate)):
                    raise TradeCumulusMoistureComparisonError(
                        f"Stage 4 {field} contains non-finite comparison values."
                    )
                absolute = np.abs(candidate - reference)
                nonzero_reference = np.abs(reference) > 0.0
                relative = np.zeros_like(absolute)
                np.divide(
                    absolute,
                    np.abs(reference),
                    out=relative,
                    where=nonzero_reference,
                )
                maximum_absolute = float(np.max(absolute)) if absolute.size else 0.0
                maximum_relative = float(np.max(relative)) if relative.size else 0.0
                maxima[field][0] = max(maxima[field][0], maximum_absolute)
                maxima[field][1] = max(maxima[field][1], maximum_relative)
                allowed = STAGE4_ATOL + STAGE4_RTOL * np.abs(reference)
                failed = absolute > allowed
                if first_failure is None and np.any(failed):
                    failure_index = tuple(int(value) for value in np.argwhere(failed)[0])
                    first_failure = Stage4FirstFailure(
                        time_seconds=time_seconds,
                        field=field,
                        index=list(failure_index),
                        stage4_value=float(reference[failure_index]),
                        new_baseline_value=float(candidate[failure_index]),
                        absolute_difference=float(absolute[failure_index]),
                        allowed_difference=float(allowed[failure_index]),
                    )
        finally:
            preserved_dataset.close()
            baseline_dataset.close()
    return Stage4ConsistencyEvidence(
        preserved_result_id=preserved.result_id,
        new_baseline_result_id=new_baseline.result_id,
        common_times_seconds=common_times,
        field_differences=[
            Stage4FieldDifference(
                field=field,
                maximum_absolute_difference=maxima[field][0],
                maximum_relative_difference=maxima[field][1],
            )
            for field in fields
        ],
        first_failure=first_failure,
        passed=first_failure is None,
    )


def build_joint_lens_preparation(
    settings: CloudChamberSettings,
    baseline: ResultMetadata,
    more_moisture: ResultMetadata,
) -> JointLensPreparation:
    """Calculate pair-wide Lens references with the merged Lens algorithms."""
    xarray = importlib.import_module("xarray")
    defaults = trade_cumulus_updraft_lens_defaults(settings, baseline.result_id)
    absolute_w: list[np.ndarray[Any, Any]] = []
    perturbation_speeds: list[np.ndarray[Any, Any]] = []
    total_speeds: list[np.ndarray[Any, Any]] = []
    reference_coordinates: tuple[np.ndarray[Any, Any], ...] | None = None
    wind_actual_level_m: float | None = None
    field_availability: dict[str, list[str]] = {}
    for result in (baseline, more_moisture):
        field_availability[result.result_id] = sorted(
            set(result.variables) & {"ql", "w", "u", "v", "cwp"}
        )
        for path, local_index in _ordered_result_frames(result):
            dataset = xarray.open_dataset(path, decode_times=False)
            try:
                ql, dimensions = _scalar_field(dataset, "ql", local_index)
                coordinates = tuple(
                    _coordinate_as_m(dataset, dimension, size)
                    for dimension, size in zip(dimensions, ql.shape, strict=True)
                )
                if reference_coordinates is None:
                    reference_coordinates = coordinates
                elif any(
                    not np.array_equal(left, right)
                    for left, right in zip(reference_coordinates, coordinates, strict=True)
                ):
                    raise TradeCumulusMoistureComparisonError(
                        "Matched Lens preparation requires exact coordinate compatibility."
                    )
                w = center_vertical_velocity_to_scalar_grid(
                    dataset, local_index, dimensions, ql.shape
                )
                finite_absolute_w = np.abs(w[np.isfinite(w)])
                if finite_absolute_w.size:
                    absolute_w.append(finite_absolute_w.astype(np.float32, copy=False))
                z_values_m = coordinates[0]
                wind_level_index = defaults.wind_level_index
                if not 0 <= wind_level_index < z_values_m.size:
                    raise TradeCumulusMoistureComparisonError(
                        "Baseline Lens wind-level index is invalid for the matched grid."
                    )
                actual_level = float(z_values_m[wind_level_index])
                if wind_actual_level_m is None:
                    wind_actual_level_m = actual_level
                elif wind_actual_level_m != actual_level:
                    raise TradeCumulusMoistureComparisonError(
                        "Matched Lens wind level differs between result frames."
                    )
                u, v = center_horizontal_wind_to_scalar_grid(
                    dataset, local_index, dimensions, ql.shape
                )
                level_u = u[wind_level_index]
                level_v = v[wind_level_index]
                mean_u = _finite_mean_array(level_u)
                mean_v = _finite_mean_array(level_v)
                total = np.hypot(level_u, level_v)
                perturbation = np.hypot(level_u - mean_u, level_v - mean_v)
                finite_total = total[np.isfinite(total)]
                finite_perturbation = perturbation[np.isfinite(perturbation)]
                if finite_total.size:
                    total_speeds.append(finite_total.astype(np.float32, copy=False))
                if finite_perturbation.size:
                    perturbation_speeds.append(finite_perturbation.astype(np.float32, copy=False))
            finally:
                dataset.close()
    if reference_coordinates is None or wind_actual_level_m is None:
        raise TradeCumulusMoistureComparisonError(
            "No readable fields are available for joint Lens preparation."
        )
    if more_moisture.time_steps is None or defaults.default_time_index >= more_moisture.time_steps:
        raise TradeCumulusMoistureComparisonError(
            "Baseline Lens default time index is unavailable in More Moisture result."
        )
    if defaults.default_plane_index >= reference_coordinates[1].size:
        raise TradeCumulusMoistureComparisonError(
            "Baseline Lens default y-plane is unavailable in More Moisture result."
        )
    joint_w = rounded_percentile_reference(absolute_w, W_PERCENTILE, W_MIN_RANGE_M_S)
    return JointLensPreparation(
        baseline_result_id=baseline.result_id,
        more_moisture_result_id=more_moisture.result_id,
        baseline_default_time_index=defaults.default_time_index,
        baseline_default_time_seconds=defaults.default_time_seconds,
        baseline_default_plane_index=defaults.default_plane_index,
        baseline_default_plane_coordinate=defaults.default_plane_coordinate,
        baseline_default_plane_units=defaults.default_plane_units,
        inherited_variant_time_index=defaults.default_time_index,
        inherited_variant_plane_index=defaults.default_plane_index,
        wind_level_index=defaults.wind_level_index,
        wind_actual_level_m=wind_actual_level_m,
        joint_w_range_min_m_s=-joint_w,
        joint_w_range_max_m_s=joint_w,
        joint_perturbation_wind_reference_m_s=rounded_percentile_reference(
            perturbation_speeds, WIND_PERCENTILE, WIND_MIN_REFERENCE_M_S
        ),
        joint_total_wind_reference_m_s=rounded_percentile_reference(
            total_speeds, WIND_PERCENTILE, WIND_MIN_REFERENCE_M_S
        ),
        coordinate_compatibility="exact_scalar_grid_coordinates_match",
        field_availability=field_availability,
    )


def _comparison_fields(
    dataset: Any,
    time_index: int,
) -> dict[str, tuple[np.ndarray[Any, Any], tuple[np.ndarray[Any, Any], ...]]]:
    ql, dimensions = _scalar_field(dataset, "ql", time_index)
    coordinates = tuple(
        _coordinate_as_m(dataset, dimension, size)
        for dimension, size in zip(dimensions, ql.shape, strict=True)
    )
    fields: dict[str, tuple[np.ndarray[Any, Any], tuple[np.ndarray[Any, Any], ...]]] = {
        "ql": (ql, coordinates)
    }
    for field in ("qv", "th"):
        values, field_dimensions = _scalar_field(dataset, field, time_index)
        if field_dimensions != dimensions:
            raise TradeCumulusMoistureComparisonError(
                f"Stage 4 field {field} does not use the ql scalar grid."
            )
        fields[field] = (values, coordinates)
    fields["w"] = (
        center_vertical_velocity_to_scalar_grid(dataset, time_index, dimensions, ql.shape),
        coordinates,
    )
    fields["cwp"] = (
        _horizontal_field(dataset, "cwp", time_index, dimensions[1:]),
        coordinates[1:],
    )
    return fields


def _result_frame_locations(result: ResultMetadata) -> dict[float, tuple[Path, int]]:
    xarray = importlib.import_module("xarray")
    locations: dict[float, tuple[Path, int]] = {}
    for path in map(Path, result.model_output_paths):
        dataset = xarray.open_dataset(path, decode_times=False)
        try:
            for local_index in range(_time_count(dataset)):
                time_seconds = _time_seconds(dataset, local_index)
                if time_seconds in locations:
                    raise TradeCumulusMoistureComparisonError(
                        f"Duplicate model-output time {time_seconds:g} s."
                    )
                locations[time_seconds] = (path, local_index)
        finally:
            dataset.close()
    return locations


def _ordered_result_frames(result: ResultMetadata) -> list[tuple[Path, int]]:
    return [location for _, location in sorted(_result_frame_locations(result).items())]


def _scalar_field(
    dataset: Any, field: str, time_index: int
) -> tuple[np.ndarray[Any, Any], tuple[str, str, str]]:
    if field not in dataset.data_vars:
        raise TradeCumulusMoistureComparisonError(f"Required scalar field {field} is absent.")
    data = _select_time(dataset[field], time_index)
    dimensions = (
        _dimension_for_axis(data.dims, "z"),
        _dimension_for_axis(data.dims, "y"),
        _dimension_for_axis(data.dims, "x"),
    )
    values = np.asarray(data.transpose(*dimensions).values, dtype=float)
    if values.ndim != 3:
        raise TradeCumulusMoistureComparisonError(
            f"Scalar field {field} is not three-dimensional after time selection."
        )
    return values, dimensions


def _horizontal_field(
    dataset: Any,
    field: str,
    time_index: int,
    dimensions: tuple[str, str],
) -> np.ndarray[Any, Any]:
    if field not in dataset.data_vars:
        raise TradeCumulusMoistureComparisonError(f"Required horizontal field {field} is absent.")
    data = _select_time(dataset[field], time_index)
    if not all(dimension in data.dims for dimension in dimensions):
        raise TradeCumulusMoistureComparisonError(
            f"Horizontal field {field} does not use the scalar horizontal grid."
        )
    values = np.asarray(data.transpose(*dimensions).values, dtype=float)
    if values.ndim != 2:
        raise TradeCumulusMoistureComparisonError(
            f"Horizontal field {field} is not two-dimensional after time selection."
        )
    return values


def _raw_field(
    dataset: Any, field: str, time_index: int
) -> tuple[np.ndarray[Any, Any], tuple[str, ...]]:
    if field not in dataset.data_vars:
        raise TradeCumulusMoistureComparisonError(f"Required field {field} is absent.")
    data = _select_time(dataset[field], time_index)
    return np.asarray(data.values, dtype=float), tuple(str(value) for value in data.dims)


def _select_time(data: Any, time_index: int) -> Any:
    for candidate in ("time", "mtime", "t"):
        if candidate in data.dims:
            size = int(data.sizes[candidate])
            if not 0 <= time_index < size:
                raise TradeCumulusMoistureComparisonError(
                    f"time_index {time_index} is outside {candidate} size {size}."
                )
            return data.isel({candidate: time_index})
    if time_index != 0:
        raise TradeCumulusMoistureComparisonError(
            "A field without a time dimension supports only local time index zero."
        )
    return data


def _dimension_for_axis(dimensions: Any, axis: Literal["x", "y", "z"]) -> str:
    candidates = {
        "x": ("xh", "x"),
        "y": ("yh", "y"),
        "z": ("zh", "z", "height", "height_m"),
    }[axis]
    names = tuple(str(value) for value in dimensions)
    for candidate in candidates:
        if candidate in names:
            return candidate
    raise TradeCumulusMoistureComparisonError(f"Field lacks a supported {axis} dimension: {names}.")


def _coordinate_as_m(dataset: Any, name: str, expected_size: int) -> np.ndarray[Any, Any]:
    if name not in dataset.coords:
        raise TradeCumulusMoistureComparisonError(f"Coordinate {name} is absent.")
    coordinate = dataset.coords[name]
    values = np.asarray(coordinate.values, dtype=float).reshape(-1)
    if values.size != expected_size:
        raise TradeCumulusMoistureComparisonError(
            f"Coordinate {name} does not match its field dimension."
        )
    units = str(coordinate.attrs.get("units", "")).strip().lower()
    if units in {"km", "kilometer", "kilometers"}:
        values = values * 1000.0
    return values


def _time_count(dataset: Any) -> int:
    for candidate in ("time", "mtime", "t"):
        if candidate in dataset.sizes:
            return int(dataset.sizes[candidate])
    return 1


def _time_seconds(dataset: Any, time_index: int) -> float:
    for candidate in ("time", "mtime", "t"):
        if candidate in dataset.coords or candidate in dataset.variables:
            values = np.asarray(dataset[candidate].values, dtype=float).reshape(-1)
            if not 0 <= time_index < values.size:
                continue
            value = float(values[time_index])
            if not math.isfinite(value):
                break
            return value
    raise TradeCumulusMoistureComparisonError("A finite model time coordinate is required.")


def _required_field_source(dataset: Any, field: str) -> str | None:
    candidates = {
        "ql": ("ql", "qc"),
        "kmh": ("kmh", "km"),
        "khh": ("khh", "kh"),
    }.get(field, (field,))
    return next((candidate for candidate in candidates if candidate in dataset.data_vars), None)


def _missing_required_fields(variables: list[str]) -> list[str]:
    available = set(variables)
    aliases = {"ql": {"ql", "qc"}, "kmh": {"kmh", "km"}, "khh": {"khh", "kh"}}
    return [
        field for field in REQUIRED_OUTPUT_FIELDS if not (aliases.get(field, {field}) & available)
    ]


def _diagnostic_paths(result: ResultMetadata) -> list[Path]:
    return sorted(
        (Path(path) for path in result.netcdf_paths if Path(path).name.startswith("cm1out_diag_")),
        key=lambda path: path.name,
    )


def _cm1_reported_runtime_seconds(manifest: Any) -> float | None:
    configured = manifest.execution.stdout_log
    if not configured:
        return None
    path = Path(str(configured)).expanduser()
    if not path.is_file():
        return None
    matches = re.findall(
        r"^\s*Total time:\s*([0-9]+(?:\.[0-9]*)?)\s*$", path.read_text(), re.MULTILINE
    )
    if not matches:
        return None
    value = float(matches[-1])
    return value if math.isfinite(value) else None


def _horizontal_mean_profile(values: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    finite = np.isfinite(values)
    counts = np.sum(finite, axis=(1, 2))
    sums = np.sum(np.where(finite, values, 0.0), axis=(1, 2))
    profile = np.full(values.shape[0], np.nan, dtype=float)
    np.divide(sums, counts, out=profile, where=counts > 0)
    return profile


def _cloud_conditioned_profile(
    w: np.ndarray[Any, Any], cloud_mask: np.ndarray[Any, Any]
) -> list[float | None]:
    selected = cloud_mask & np.isfinite(w)
    counts = np.sum(selected, axis=(1, 2))
    sums = np.sum(np.where(selected, w, 0.0), axis=(1, 2))
    profile = np.full(w.shape[0], np.nan, dtype=float)
    np.divide(sums, counts, out=profile, where=counts > 0)
    return _optional_float_list(profile)


def _mean_optional_profiles(profiles: list[list[float | None]]) -> list[float | None]:
    if not profiles:
        return []
    widths = {len(profile) for profile in profiles}
    if len(widths) != 1:
        raise TradeCumulusMoistureComparisonError("Vertical profiles use inconsistent grids.")
    matrix = np.asarray(
        [[np.nan if value is None else value for value in profile] for profile in profiles],
        dtype=float,
    )
    finite = np.isfinite(matrix)
    counts = np.sum(finite, axis=0)
    sums = np.sum(np.where(finite, matrix, 0.0), axis=0)
    means = np.full(matrix.shape[1], np.nan, dtype=float)
    np.divide(sums, counts, out=means, where=counts > 0)
    return _optional_float_list(means)


def _profile_peak(
    profile: list[float | None], heights_m: list[float]
) -> tuple[float | None, float | None]:
    finite = [
        (value, heights_m[index])
        for index, value in enumerate(profile)
        if value is not None and index < len(heights_m)
    ]
    if not finite:
        return None, None
    maximum = max(value for value, _ in finite)
    height = min(height for value, height in finite if value == maximum)
    return maximum, height


def _metric(
    value: float | None,
    units: str,
    method: str,
    window: str,
    *,
    unavailable_reason: str | None = None,
) -> ScalarRunMetric:
    if value is None:
        return ScalarRunMetric(
            value=None,
            units=units,
            method=method,
            window=window,
            quality="unavailable",
            unavailable_reason=unavailable_reason or "metric_value_unavailable",
        )
    return ScalarRunMetric(value=value, units=units, method=method, window=window)


def _timed_values(times: list[float], values: list[float]) -> list[TimedValue]:
    if len(times) != len(values):
        raise TradeCumulusMoistureComparisonError(
            "Time and value sequences must have identical lengths."
        )
    return [
        TimedValue(time_seconds=time_seconds, value=value)
        for time_seconds, value in zip(times, values, strict=True)
    ]


def _optional_float_list(values: np.ndarray[Any, Any]) -> list[float | None]:
    return [float(value) if math.isfinite(float(value)) else None for value in values]


def _finite_mean_array(values: np.ndarray[Any, Any]) -> float:
    finite = values[np.isfinite(values)]
    if not finite.size:
        raise TradeCumulusMoistureComparisonError("A finite horizontal wind mean is required.")
    return float(np.mean(finite))


def _finite_mean_list(values: list[float]) -> float | None:
    finite = [value for value in values if math.isfinite(value)]
    return float(np.mean(finite)) if finite else None


def _finite_min_list(values: list[float]) -> float | None:
    finite = [value for value in values if math.isfinite(value)]
    return min(finite) if finite else None


def _finite_max_list(values: list[float]) -> float | None:
    finite = [value for value in values if math.isfinite(value)]
    return max(finite) if finite else None


def _min_optional(current: float | None, candidate: float) -> float:
    return min(current, candidate) if current is not None else candidate


def _max_optional(current: float | None, candidate: float) -> float:
    return max(current, candidate) if current is not None else candidate


def _fixed_assumptions() -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "canonical_profiles": "cm1_r21_1_analytic_isnd19_iwnd9_testcase3",
        "deterministic_perturbation": {"irandp": 1},
        "surface_sensible_heat_flux_k_m_s": 8.0e-3,
        "friction_velocity_m_s": 0.28,
        "large_scale_forcing": "canonical_bomex",
        "physics": {"ptype": 6, "terminal_velocity_m_s": 0.0},
        "grid": {"nx": 64, "ny": 64, "nz": 75},
        "spacing_m": {"dx": 100.0, "dy": 100.0, "dz": 40.0},
        "domain_m": {"x": 6400.0, "y": 6400.0, "z": 3000.0},
        "time_step": {"target_seconds": 3.0, "adaptive": True},
        "output_cadence_seconds": OUTPUT_CADENCE_SECONDS,
        "diagnostic_cadence_seconds": DIAGNOSTIC_CADENCE_SECONDS,
        "required_output_fields": list(REQUIRED_OUTPUT_FIELDS),
    }


def _namelist_assignments(text: str) -> dict[str, str]:
    pattern = re.compile(
        r"^\s*(?P<name>[A-Za-z][A-Za-z0-9_]*)\s*=\s*(?P<value>[^,!\n]+)", re.MULTILINE
    )
    values: dict[str, str] = {}
    for match in pattern.finditer(text):
        name = match.group("name")
        if name in values:
            raise TradeCumulusMoistureComparisonError(
                f"Generated namelist contains duplicate assignment {name!r}."
            )
        values[name] = match.group("value").strip()
    return values


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
