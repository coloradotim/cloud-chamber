"""Surface-forced observed-sounding campaign planning and reporting.

This module is intentionally orchestration-only. CM1 package generation,
queueing, LAN worker execution, and result ingest remain owned by the existing
backend paths; the campaign layer validates a matrix, keeps resumable state, and
summarizes what those paths produced.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.cm1_input_contract import RunRecipe
from cloud_chamber.dry_run_package import DryRunPackageError, generate_dry_run_package
from cloud_chamber.lan_worker import (
    LanWorkerApiError,
    collect_lan_worker_run,
    lan_worker_run_status,
    start_lan_worker_run,
)
from cloud_chamber.local_run_manager import LocalRunManager, reconcile_completed_run_manifest
from cloud_chamber.local_run_queue import LocalRunQueueError, LocalRunQueueManager
from cloud_chamber.observed_sounding import (
    ObservedSoundingError,
    ObservedSoundingRecord,
    observed_sounding_from_payload,
    parse_igra_station_text,
)
from cloud_chamber.result_diagnostics import (
    FieldFrameQualitySummary,
    FieldQuality,
    LowLevelResponseFieldDiagnostics,
    SurfaceFluxDiagnostics,
    SurfaceFluxFieldDiagnostics,
)
from cloud_chamber.result_ingest import (
    RESULT_METADATA_FILENAME,
    ResultIngestError,
    ResultMetadata,
    ingest_completed_run,
    result_metadata_from_json,
)
from cloud_chamber.run_configuration import resolve_run_configuration
from cloud_chamber.run_manifest import LifecycleState, ProductState, load_run_manifest
from cloud_chamber.scenario_catalog import load_scenario_template
from cloud_chamber.settings import CloudChamberSettings, load_settings
from cloud_chamber.sounding_candidates import (
    SavedSoundingCandidate,
    SoundingCandidate,
    list_saved_candidates,
    list_screening_inputs,
    screen_cached_soundings,
)

MATRIX_SCHEMA_VERSION = "surface_forced_campaign_matrix_v1"
CAMPAIGN_STATE_SCHEMA_VERSION = "surface_forced_campaign_state_v1"
CAMPAIGN_SUMMARY_SCHEMA_VERSION = "surface_forced_campaign_summary_v1"
OBSERVED_SURFACE_FORCED_RECIPE = RunRecipe.OBSERVED_SURFACE_FORCED_EVOLUTION.value
DEFAULT_SCENARIO_ID = "baseline-shallow-cumulus"
DEFAULT_REPORT_ROOT = Path("docs/research/surface-forced-campaigns")
DEFAULT_PHASE1_REQUIRED_COMPARISON_TYPES = (
    "heat_flux_sensitivity",
    "moisture_flux_sensitivity",
    "combined_flux_sensitivity",
)
RUN_CONFIGURATION_KEYS = {
    "duration",
    "horizontal_cell_count",
    "domain_size",
    "output_cadence",
    "diagnostic_set",
    "surface_heat_flux_k_m_s",
    "surface_moisture_flux_g_g_m_s",
}
KNOWN_STATUS_VALUES = {
    "planned",
    "packaged",
    "queued",
    "running",
    "completed_not_ingested",
    "ingested",
    "package_failed",
    "run_failed",
    "ingest_failed",
    "run_canceled",
    "skipped",
    "blocked",
}
TERMINAL_OR_ACTIVE_STATUSES = {
    "queued",
    "running",
    "completed_not_ingested",
    "ingested",
}
RERUN_REQUIRED_STATUSES = {
    "run_failed",
    "ingest_failed",
    "run_canceled",
    "package_failed",
    "blocked",
}
SUPPORTED_REQUIRED_SUMMARY_FIELDS = {
    "campaign_id",
    "schema_version",
    "matrix_id",
    "stable_resume_identity",
    "run_id",
    "result_id",
    "package_status",
    "run_status",
    "ingest_status",
    "queue_target",
    "station_id",
    "station_name",
    "valid_time_utc",
    "candidate_id",
    "selection_source_type",
    "selection_source_reference",
    "candidate_story",
    "candidate_score",
    "candidate_evidence",
    "candidate_caveats",
    "surface_heat_flux_k_m_s",
    "surface_heat_flux_units",
    "surface_moisture_flux_g_g_m_s",
    "surface_moisture_flux_units",
    "cm1_cnst_shflx",
    "cm1_cnst_shflx_units",
    "cm1_cnst_lhflx",
    "cm1_cnst_lhflx_units",
    "duration",
    "duration_seconds",
    "domain_size",
    "horizontal_cell_count",
    "nx",
    "ny",
    "nz",
    "dx_m",
    "dy_m",
    "dz_m",
    "stretch_z",
    "str_bot_m",
    "str_top_m",
    "dz_bot_m",
    "dz_top_m",
    "model_top_m",
    "output_cadence",
    "expected_output_volume",
    "cloud_chamber_commit",
    "cm1_version",
    "cm1_build",
    "required_output_fields",
    "missing_output_fields",
    "available_output_fields",
    "diagnostic_support",
    "diagnostic_trust",
    "diagnostic_quality_warnings",
    "trusted_key_result",
    "interesting_time_support_state",
    "source_manifest_lifecycle_state",
    "source_manifest_product_state",
    "warnings",
    "caveats",
    "hfx_present",
    "hfx_units",
    "hfx_min",
    "hfx_max",
    "hfx_mean",
    "hfx_finite_count",
    "hfx_non_finite_count",
    "hfx_total_count",
    "hfx_finite_fraction",
    "hfx_frame_quality",
    "qfx_present",
    "qfx_units",
    "qfx_min",
    "qfx_max",
    "qfx_mean",
    "qfx_finite_count",
    "qfx_non_finite_count",
    "qfx_total_count",
    "qfx_finite_fraction",
    "qfx_frame_quality",
    "terminal_output_contamination",
    "terminal_output_contamination_fields",
    "runtime_floating_point_warnings",
    "lhfx_present",
    "lhfx_units",
    "lhfx_min",
    "lhfx_max",
    "lhfx_mean",
    "low_level_qv_response",
    "low_level_qv_response_method",
    "low_level_qv_early_response_available",
    "low_level_qv_early_response_delta",
    "low_level_qv_early_response_delta_units",
    "low_level_qv_early_response_min_finite_fraction",
    "low_level_qv_early_response_quality_state",
    "low_level_qv_full_run_response_available",
    "low_level_qv_full_run_delta",
    "low_level_theta_or_temperature_response",
    "low_level_theta_or_temperature_response_method",
    "low_level_theta_or_temperature_early_response_available",
    "low_level_theta_or_temperature_early_response_delta",
    "low_level_theta_or_temperature_early_response_delta_units",
    "low_level_theta_or_temperature_early_response_min_finite_fraction",
    "low_level_theta_or_temperature_early_response_quality_state",
    "low_level_theta_or_temperature_full_run_response_available",
    "low_level_theta_or_temperature_full_run_delta",
    "first_cloud_time",
    "max_cloud_top_m",
    "max_cloud_top_time",
    "max_qc",
    "max_qc_time",
    "cloud_depth_or_classification",
    "max_w_m_s",
    "max_w_time",
    "max_w_height_m",
    "qr_present",
    "surface_rain_present",
    "surface_rain_max",
    "surface_rain_units",
    "dbz_present",
    "max_dbz",
    "first_deep_cloud_time",
    "deep_cloud_formed",
    "deep_cloud_flag",
    "evidence_fields",
    "forcing_path_not_verified",
    "surface_outputs_missing",
    "boundary_layer_response_verified",
    "forcing_wiring_verified_but_response_not_verified",
    "uniform_forcing_too_weak",
    "uniform_forcing_physics_limited",
    "run_duration_or_domain_limited",
    "candidate_selection_limited",
    "output_products_or_diagnostics_missing",
    "valid_no_initiation_under_tested_assumptions",
    "inconclusive_noncomparable_runs",
    "inconclusive_missing_evidence",
    "differential_forcing_followup_candidate",
    "radiation_or_place_time_followup_candidate",
}
MATRIX_CONTEXT_FIELDS = {
    "selection_id",
    "cloud_chamber_commit",
    "cm1_version",
    "required_output_fields",
    "surface_heat_flux_k_m_s",
    "surface_moisture_flux_g_g_m_s",
    "cm1_cnst_shflx",
    "cm1_cnst_lhflx",
    "runtime_seconds",
    "expected_output_frames",
    "expected_output_volume",
}

QueueTarget = Literal["local", "lan"]


class LocalQueueLike(Protocol):
    def enqueue(self, manifest_path: Path) -> Any: ...


class CampaignError(RuntimeError):
    """Raised when a campaign matrix or campaign operation is invalid."""


class CampaignRunPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = MATRIX_SCHEMA_VERSION
    campaign_id: str
    matrix_id: str
    phase: str | None = None
    optional: bool = False
    selection_id: str
    selection_role: str | None = None
    selection_source_type: str
    selection_source_reference: str
    selection_payload_hash: str
    forcing_id: str | None = None
    comparison_type: str | None = None
    comparison_control_matrix_id: str | None = None
    comparison_role: str | None = None
    queue_target: QueueTarget
    run_configuration: dict[str, Any]
    resolved_run_configuration: dict[str, Any]
    cm1_values: dict[str, Any]
    surface_flux_cm1_values: dict[str, Any]
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    stable_resume_identity: str
    run_id: str
    candidate_screening: dict[str, Any] | None = None


class CampaignPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = MATRIX_SCHEMA_VERSION
    campaign_id: str
    title: str | None = None
    objective: str | None = None
    protocol: str | None = None
    commit_report_path: str | None = None
    matrix_path: str | None = None
    execution: dict[str, Any] = Field(default_factory=dict)
    comparison_types: dict[str, dict[str, Any]] = Field(default_factory=dict)
    phase1_required_comparison_types: list[str] = Field(default_factory=list)
    required_summary_fields: dict[str, list[str]] = Field(default_factory=dict)
    run_count: int
    runs: list[CampaignRunPlan]
    caveats: list[str] = Field(default_factory=list)


class CampaignStateRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matrix_id: str
    stable_resume_identity: str
    run_id: str
    queue_target: QueueTarget
    status: str
    package_status: str = "planned"
    run_status: str = "planned"
    ingest_status: str = "not_started"
    manifest_path: str | None = None
    package_dir: str | None = None
    result_id: str | None = None
    error: str | None = None
    message: str | None = None
    lan_worker_payload: dict[str, Any] | None = None
    gate_override: dict[str, Any] | None = None
    updated_at: datetime


class CampaignState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = CAMPAIGN_STATE_SCHEMA_VERSION
    campaign_id: str
    matrix_path: str | None = None
    updated_at: datetime
    runs: list[CampaignStateRun] = Field(default_factory=list)


class CampaignReportArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown_path: str
    summary_json_path: str
    summary: dict[str, Any]


class CampaignOperationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    campaign_id: str
    state_path: str
    runs: list[CampaignStateRun]


def load_campaign_matrix(path: Path) -> dict[str, Any]:
    """Load a campaign matrix from YAML or JSON."""

    try:
        loaded = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise CampaignError(f"Invalid campaign matrix YAML/JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise CampaignError(f"Campaign matrix must be a YAML/JSON object: {path}")
    return dict(loaded)


def build_campaign_plan(
    matrix: Mapping[str, Any],
    *,
    matrix_path: Path | None = None,
    allow_absolute_local_paths: bool = False,
) -> CampaignPlan:
    """Validate a matrix and resolve each run to CM1-facing configuration values."""

    errors: list[str] = []
    caveats: list[str] = []
    if matrix.get("schema_version") != MATRIX_SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {MATRIX_SCHEMA_VERSION!r}; "
            f"got {matrix.get('schema_version')!r}"
        )

    campaign = _mapping(matrix.get("campaign"), "campaign", errors)
    campaign_id = _required_string(campaign, "campaign_id", "campaign", errors)
    execution = _mapping(matrix.get("execution", {}), "execution", errors)
    selection_sets = _indexed_mappings(
        matrix.get("selection_sets"),
        key="selection_id",
        label="selection_sets",
        errors=errors,
    )
    forcing_sets = _indexed_mappings(
        matrix.get("forcing_sets", []),
        key="forcing_id",
        label="forcing_sets",
        errors=errors,
    )
    comparison_types = _indexed_mappings(
        matrix.get("comparison_types", []),
        key="comparison_type",
        label="comparison_types",
        errors=errors,
    )
    phase1_required_comparison_types = _string_list(matrix.get("phase1_required_comparison_types"))
    for required_comparison_type in phase1_required_comparison_types:
        if required_comparison_type not in comparison_types:
            errors.append(
                "phase1_required_comparison_types references unknown comparison_type: "
                f"{required_comparison_type}"
            )
    run_defaults = _mapping(matrix.get("run_defaults", {}), "run_defaults", errors)
    runs = _list_of_mappings(matrix.get("runs"), "runs", errors)
    required_summary_fields = _required_summary_fields(
        matrix.get("required_summary_fields"), errors
    )
    _validate_execution(execution, errors)

    planned: list[CampaignRunPlan] = []
    matrix_ids: set[str] = set()
    default_queue_target = _queue_target(
        run_defaults.get("queue_target") or execution.get("queue_target") or "local",
        errors=errors,
        context="execution.queue_target",
    )
    matrix_base = matrix_path.parent if matrix_path is not None else Path.cwd()

    for index, run in enumerate(runs):
        context = f"runs[{index}]"
        matrix_id = _required_string(run, "matrix_id", context, errors)
        if matrix_id in matrix_ids:
            errors.append(f"Duplicate run matrix_id: {matrix_id}")
        matrix_ids.add(matrix_id)

        selection_id = _required_string(run, "selection_id", context, errors)
        selection = selection_sets.get(selection_id)
        if selection is None:
            errors.append(f"{context}.selection_id references unknown selection: {selection_id}")
            selection = {}

        forcing_id = _optional_string(run.get("forcing_id"))
        forcing = forcing_sets.get(forcing_id or "", {})
        if forcing_id is not None and not forcing:
            errors.append(f"{context}.forcing_id references unknown forcing set: {forcing_id}")

        comparison = _optional_mapping(run.get("comparison"))
        comparison_type = _optional_string(comparison.get("type")) if comparison else None
        if comparison_type is not None and comparison_type not in comparison_types:
            errors.append(f"{context}.comparison.type references unknown type: {comparison_type}")

        source = _validate_selection_source(
            selection,
            context=f"selection_sets[{selection_id}].source",
            matrix_base=matrix_base,
            allow_absolute_local_paths=allow_absolute_local_paths,
            errors=errors,
        )
        queue_target = _queue_target(
            run.get("queue_target") or run_defaults.get("queue_target") or default_queue_target,
            errors=errors,
            context=f"{context}.queue_target",
        )
        run_configuration = _resolved_run_configuration_payload(
            defaults=run_defaults,
            forcing=forcing,
            run=run,
        )
        try:
            resolved_configuration = resolve_run_configuration(
                run_configuration=run_configuration,
                run_recipe=OBSERVED_SURFACE_FORCED_RECIPE,
            )
        except ValueError as exc:
            errors.append(f"{context}.run_configuration invalid: {exc}")
            continue

        source_type = str(source.get("type", "unknown"))
        source_reference = _selection_source_reference(source)
        selection_payload_hash = _selection_payload_hash(source, matrix_base)
        candidate_screening = _candidate_screening_from_matrix(selection, source)
        stable_identity = _stable_resume_identity(
            campaign_id=campaign_id,
            matrix_id=matrix_id,
            selection_id=selection_id,
            selection_source_reference=source_reference,
            selection_payload_hash=selection_payload_hash,
            run_configuration=resolved_configuration.model_dump(mode="json"),
            forcing_id=forcing_id,
        )
        planned.append(
            CampaignRunPlan(
                campaign_id=campaign_id,
                matrix_id=matrix_id,
                phase=_optional_string(run.get("phase")),
                optional=bool(run.get("optional", False)),
                selection_id=selection_id,
                selection_role=_optional_string(selection.get("role")),
                selection_source_type=source_type,
                selection_source_reference=source_reference,
                selection_payload_hash=selection_payload_hash,
                forcing_id=forcing_id,
                comparison_type=comparison_type,
                comparison_control_matrix_id=(
                    _optional_string(comparison.get("control_matrix_id")) if comparison else None
                ),
                comparison_role=_optional_string(run.get("comparison_role")),
                queue_target=queue_target,
                run_configuration=run_configuration,
                resolved_run_configuration=resolved_configuration.model_dump(mode="json"),
                cm1_values=resolved_configuration.cm1_values.model_dump(mode="json"),
                surface_flux_cm1_values=(
                    resolved_configuration.surface_flux_cm1_values.model_dump(mode="json")
                ),
                tags=_resolved_tags(run_defaults, selection, run, campaign_id, matrix_id),
                notes=_resolved_notes(run_defaults, selection, run),
                stable_resume_identity=stable_identity,
                run_id=_run_id(campaign_id, matrix_id, stable_identity),
                candidate_screening=candidate_screening,
            )
        )

    _validate_comparison_control_refs(planned, errors)
    if errors:
        raise CampaignError("; ".join(errors))

    if any(run.queue_target == "lan" for run in planned):
        caveats.append("lan_queue_target_uses_existing_trusted_lan_worker_configuration")

    return CampaignPlan(
        campaign_id=campaign_id,
        title=_optional_string(campaign.get("title")),
        objective=_optional_string(campaign.get("objective")),
        protocol=_optional_string(campaign.get("protocol")),
        commit_report_path=_optional_string(campaign.get("commit_report_path")),
        matrix_path=str(matrix_path) if matrix_path is not None else None,
        execution=execution,
        comparison_types={key: dict(value) for key, value in comparison_types.items()},
        phase1_required_comparison_types=phase1_required_comparison_types,
        required_summary_fields=required_summary_fields,
        run_count=len(planned),
        runs=planned,
        caveats=caveats,
    )


def plan_campaign(
    matrix_path: Path,
    *,
    allow_absolute_local_paths: bool = False,
) -> CampaignPlan:
    matrix = load_campaign_matrix(matrix_path)
    return build_campaign_plan(
        matrix,
        matrix_path=matrix_path,
        allow_absolute_local_paths=allow_absolute_local_paths,
    )


def package_campaign(
    matrix_path: Path,
    *,
    settings: CloudChamberSettings | None = None,
    runtime_home: Path | None = None,
    selected_matrix_ids: set[str] | None = None,
    resume: bool = False,
    force_rerun: bool = False,
    allow_absolute_local_paths: bool = False,
) -> CampaignOperationResult:
    resolved_settings = settings or load_settings(home=runtime_home)
    plan = plan_campaign(matrix_path, allow_absolute_local_paths=allow_absolute_local_paths)
    state = _load_or_create_state(plan, resolved_settings.runtime_home)
    scenario = load_scenario_template(DEFAULT_SCENARIO_ID).model_dump(mode="json")

    for run in _selected_runs(plan.runs, selected_matrix_ids):
        existing = _state_run_for_matrix(state, run.matrix_id)
        if (
            resume
            and existing is not None
            and existing.stable_resume_identity == run.stable_resume_identity
            and existing.manifest_path
            and Path(existing.manifest_path).expanduser().exists()
            and not force_rerun
        ):
            _upsert_state_run(
                state,
                existing.model_copy(update={"message": "Resumed existing package."}),
            )
            continue

        try:
            package_dir = resolved_settings.runtime_home.expanduser() / "runs" / run.run_id
            if force_rerun and _run_dir_has_runtime_artifacts(package_dir):
                raise CampaignError(
                    "Refusing --force-rerun because the existing run directory contains "
                    "output, logs, or result artifacts. Delete it intentionally outside the "
                    "campaign runner before rerunning."
                )
            observed = _resolve_observed_sounding(
                run, settings=resolved_settings, matrix_path=matrix_path
            )
            candidate_screening = _candidate_screening_for_package(
                run,
                observed=observed,
                settings=resolved_settings,
                matrix_path=matrix_path,
            )
            result = generate_dry_run_package(
                scenario_data=scenario,
                runtime_home=resolved_settings.runtime_home,
                run_id=run.run_id,
                observed_sounding=observed,
                candidate_screening=candidate_screening,
                user_tags=run.tags,
                user_notes=run.notes,
                run_recipe=OBSERVED_SURFACE_FORCED_RECIPE,
                run_configuration=run.run_configuration,
                allow_overwrite=force_rerun,
                app_commit=_repo_commit(),
            )
        except (CampaignError, DryRunPackageError, ObservedSoundingError, OSError) as exc:
            _upsert_state_run(
                state,
                _new_state_run(
                    run,
                    status="package_failed",
                    package_status="package_failed",
                    run_status="not_started",
                    ingest_status="not_started",
                    error=str(exc),
                ),
            )
            continue

        _upsert_state_run(
            state,
            _new_state_run(
                run,
                status="packaged",
                package_status="packaged",
                run_status="not_started",
                ingest_status="not_started",
                manifest_path=str(result.manifest_path),
                package_dir=str(result.package_dir),
                message="Dry-run package created.",
            ),
        )

    _save_state(state, resolved_settings.runtime_home)
    return CampaignOperationResult(
        campaign_id=state.campaign_id,
        state_path=str(_state_path(resolved_settings.runtime_home, state.campaign_id)),
        runs=state.runs,
    )


def queue_campaign(
    matrix_path: Path,
    *,
    settings: CloudChamberSettings | None = None,
    runtime_home: Path | None = None,
    selected_matrix_ids: set[str] | None = None,
    resume: bool = True,
    include_optional: bool = False,
    override_phase_gate: bool = False,
    override_reason: str | None = None,
    allow_absolute_local_paths: bool = False,
    local_queue_factory: Callable[[CloudChamberSettings], LocalQueueLike] | None = None,
    lan_start: Callable[[CloudChamberSettings, Path], dict[str, object]] = start_lan_worker_run,
    lan_status: Callable[[CloudChamberSettings, Path], dict[str, object]] = lan_worker_run_status,
) -> CampaignOperationResult:
    resolved_settings = settings or load_settings(home=runtime_home)
    plan = plan_campaign(matrix_path, allow_absolute_local_paths=allow_absolute_local_paths)
    execution_runs = _selected_runs(
        plan.runs,
        selected_matrix_ids,
        include_optional=include_optional,
    )
    package_campaign(
        matrix_path,
        settings=resolved_settings,
        selected_matrix_ids={run.matrix_id for run in execution_runs},
        resume=resume,
        allow_absolute_local_paths=allow_absolute_local_paths,
    )
    status_campaign(
        matrix_path,
        settings=resolved_settings,
        allow_absolute_local_paths=allow_absolute_local_paths,
        lan_status=lan_status,
    )
    state = _load_or_create_state(plan, resolved_settings.runtime_home)
    queue_factory = local_queue_factory or _default_local_queue
    summaries = [_summary_for_plan_run(run, state) for run in plan.runs]
    surface_flux_response = _surface_flux_response_evaluation(plan, summaries)
    low_level_response = _low_level_response_evaluation(plan, summaries)
    gate_state = _phase_gate_state(summaries, surface_flux_response, low_level_response)
    override = _gate_override_payload(
        enabled=override_phase_gate,
        reason=override_reason,
        gate_state=gate_state,
    )
    max_lan = _max_concurrent_runs(plan)
    lan_active = _active_lan_count(state)

    for run in execution_runs:
        state_run = _state_run_for_matrix(state, run.matrix_id)
        if state_run is None or not state_run.manifest_path:
            continue
        if state_run.status in TERMINAL_OR_ACTIVE_STATUSES:
            _upsert_state_run(
                state,
                state_run.model_copy(
                    update={
                        "message": f"Skipped queue; campaign row is already {state_run.status}.",
                        "updated_at": _now(),
                    }
                ),
            )
            continue
        if state_run.status in RERUN_REQUIRED_STATUSES and not (
            state_run.status == "blocked" and override_phase_gate
        ):
            _upsert_state_run(
                state,
                state_run.model_copy(
                    update={
                        "message": (
                            f"Skipped queue; {state_run.status} rows require an explicit rerun."
                        ),
                        "updated_at": _now(),
                    }
                ),
            )
            continue
        if not _phase_gate_allows_queue(run, gate_state, override_phase_gate):
            _upsert_state_run(
                state,
                state_run.model_copy(
                    update={
                        "status": "blocked",
                        "run_status": "blocked",
                        "message": (
                            f"Phase gate blocked queueing: {gate_state}. "
                            "Queue Phase 1 first or provide an override reason."
                        ),
                        "gate_override": override,
                        "updated_at": _now(),
                    }
                ),
            )
            continue
        manifest_path = Path(state_run.manifest_path).expanduser()
        try:
            if run.queue_target == "local":
                queue_state = queue_factory(resolved_settings).enqueue(manifest_path)
                entry = next(
                    (
                        candidate
                        for candidate in queue_state.entries
                        if Path(candidate.manifest_path).expanduser() == manifest_path
                    ),
                    None,
                )
                status = _queue_entry_to_campaign_status(entry.state if entry else "queued")
                _upsert_state_run(
                    state,
                    state_run.model_copy(
                        update={
                            "status": status,
                            "run_status": status,
                            "message": entry.message if entry else "Queued for local CM1.",
                            "error": entry.error if entry else None,
                            "gate_override": override,
                            "updated_at": _now(),
                        }
                    ),
                )
            else:
                if lan_active >= max_lan:
                    _upsert_state_run(
                        state,
                        state_run.model_copy(
                            update={
                                "status": "blocked",
                                "run_status": "blocked",
                                "message": (f"LAN max_concurrent_runs={max_lan} already reached."),
                                "gate_override": override,
                                "updated_at": _now(),
                            }
                        ),
                    )
                    continue
                payload = lan_start(resolved_settings, manifest_path)
                status = _lan_payload_to_campaign_status(payload)
                if status in {"queued", "running"}:
                    lan_active += 1
                _upsert_state_run(
                    state,
                    state_run.model_copy(
                        update={
                            "status": status,
                            "run_status": status,
                            "lan_worker_payload": dict(payload),
                            "message": _payload_message(payload, "LAN worker run started."),
                            "error": None,
                            "gate_override": override,
                            "updated_at": _now(),
                        }
                    ),
                )
        except (LocalRunQueueError, LanWorkerApiError, CampaignError) as exc:
            _upsert_state_run(
                state,
                state_run.model_copy(
                    update={
                        "status": "run_failed",
                        "run_status": "run_failed",
                        "error": str(exc),
                        "updated_at": _now(),
                    }
                ),
            )

    _save_state(state, resolved_settings.runtime_home)
    return CampaignOperationResult(
        campaign_id=state.campaign_id,
        state_path=str(_state_path(resolved_settings.runtime_home, state.campaign_id)),
        runs=state.runs,
    )


def status_campaign(
    matrix_path: Path,
    *,
    settings: CloudChamberSettings | None = None,
    runtime_home: Path | None = None,
    allow_absolute_local_paths: bool = False,
    lan_status: Callable[[CloudChamberSettings, Path], dict[str, object]] = lan_worker_run_status,
) -> CampaignOperationResult:
    resolved_settings = settings or load_settings(home=runtime_home)
    plan = plan_campaign(matrix_path, allow_absolute_local_paths=allow_absolute_local_paths)
    state = _load_or_create_state(plan, resolved_settings.runtime_home)
    queue_entries = _read_queue_entries(resolved_settings.runtime_home)

    for run in plan.runs:
        state_run = _state_run_for_matrix(state, run.matrix_id)
        if state_run is None:
            _upsert_state_run(
                state,
                _new_state_run(
                    run,
                    status="planned",
                    package_status="planned",
                    run_status="planned",
                    ingest_status="not_started",
                ),
            )
            continue
        _upsert_state_run(
            state,
            _state_run_with_runtime_status(
                state_run,
                run,
                settings=resolved_settings,
                queue_entries=queue_entries,
                lan_status=lan_status,
            ),
        )

    _save_state(state, resolved_settings.runtime_home)
    return CampaignOperationResult(
        campaign_id=state.campaign_id,
        state_path=str(_state_path(resolved_settings.runtime_home, state.campaign_id)),
        runs=state.runs,
    )


def ingest_campaign(
    matrix_path: Path,
    *,
    settings: CloudChamberSettings | None = None,
    runtime_home: Path | None = None,
    selected_matrix_ids: set[str] | None = None,
    allow_absolute_local_paths: bool = False,
    lan_status: Callable[[CloudChamberSettings, Path], dict[str, object]] = lan_worker_run_status,
    lan_collect: Callable[[CloudChamberSettings, Path], dict[str, object]] = collect_lan_worker_run,
) -> CampaignOperationResult:
    resolved_settings = settings or load_settings(home=runtime_home)
    status_campaign(
        matrix_path,
        settings=resolved_settings,
        allow_absolute_local_paths=allow_absolute_local_paths,
        lan_status=lan_status,
    )
    plan = plan_campaign(matrix_path, allow_absolute_local_paths=allow_absolute_local_paths)
    state = _load_or_create_state(plan, resolved_settings.runtime_home)

    for run in _selected_runs(plan.runs, selected_matrix_ids):
        state_run = _state_run_for_matrix(state, run.matrix_id)
        if state_run is None or not state_run.manifest_path:
            continue
        manifest_path = Path(state_run.manifest_path).expanduser()
        try:
            if run.queue_target == "lan" and state_run.status in {"queued", "running"}:
                _upsert_state_run(
                    state,
                    state_run.model_copy(
                        update={
                            "message": "LAN worker output is not ready for collection.",
                            "updated_at": _now(),
                        }
                    ),
                )
                continue
            if run.queue_target == "lan" and state_run.status == "completed_not_ingested":
                payload = lan_collect(resolved_settings, manifest_path)
                state_run = state_run.model_copy(
                    update={
                        "lan_worker_payload": dict(payload),
                        "message": _payload_message(payload, "LAN worker output collected."),
                        "updated_at": _now(),
                    }
                )
                if _lan_payload_to_campaign_status(payload) not in {
                    "completed_not_ingested",
                    "ingested",
                }:
                    _upsert_state_run(state, state_run)
                    continue
                manifest = load_run_manifest(manifest_path)
                if (
                    manifest.lifecycle_state != LifecycleState.COMPLETED
                    or manifest.provenance.product_state != ProductState.COMPLETED_CM1_RESULT
                    or not manifest.outputs.netcdf_paths
                ):
                    _upsert_state_run(
                        state,
                        state_run.model_copy(
                            update={
                                "message": (
                                    "LAN worker reported completion, but collection has not "
                                    "updated the local manifest with completed CM1 output."
                                ),
                                "updated_at": _now(),
                            }
                        ),
                    )
                    continue
            existing_result = _load_result_for_manifest_path(manifest_path)
            if existing_result is not None:
                _upsert_state_run(
                    state,
                    state_run.model_copy(
                        update={
                            "status": "ingested",
                            "ingest_status": "ingested",
                            "result_id": existing_result.result_id,
                            "error": None,
                            "updated_at": _now(),
                        }
                    ),
                )
                continue
            result = ingest_completed_run(manifest_path)
        except (ResultIngestError, LanWorkerApiError, OSError) as exc:
            _upsert_state_run(
                state,
                state_run.model_copy(
                    update={
                        "status": "ingest_failed",
                        "ingest_status": "ingest_failed",
                        "error": str(exc),
                        "updated_at": _now(),
                    }
                ),
            )
            continue
        _upsert_state_run(
            state,
            state_run.model_copy(
                update={
                    "status": "ingested",
                    "ingest_status": "ingested",
                    "result_id": result.result_id,
                    "error": None,
                    "message": "Completed CM1 output ingested.",
                    "updated_at": _now(),
                }
            ),
        )

    _save_state(state, resolved_settings.runtime_home)
    return CampaignOperationResult(
        campaign_id=state.campaign_id,
        state_path=str(_state_path(resolved_settings.runtime_home, state.campaign_id)),
        runs=state.runs,
    )


def report_campaign(
    matrix_path: Path,
    *,
    settings: CloudChamberSettings | None = None,
    runtime_home: Path | None = None,
    report_path: Path | None = None,
    summary_json_path: Path | None = None,
    allow_absolute_local_paths: bool = False,
) -> CampaignReportArtifacts:
    resolved_settings = settings or load_settings(home=runtime_home)
    status_campaign(
        matrix_path,
        settings=resolved_settings,
        allow_absolute_local_paths=allow_absolute_local_paths,
    )
    plan = plan_campaign(matrix_path, allow_absolute_local_paths=allow_absolute_local_paths)
    state = _load_or_create_state(plan, resolved_settings.runtime_home)
    summaries = [_summary_for_plan_run(run, state) for run in plan.runs]
    comparisons = _evaluate_comparisons(plan, summaries)
    surface_flux_response = _surface_flux_response_evaluation(plan, summaries)
    low_level_response = _low_level_response_evaluation(plan, summaries)
    summary = {
        "schema_version": CAMPAIGN_SUMMARY_SCHEMA_VERSION,
        "campaign_id": plan.campaign_id,
        "title": plan.title,
        "objective": plan.objective,
        "protocol": plan.protocol,
        "matrix_path": str(matrix_path),
        "generated_at": _now().isoformat(),
        "run_count": len(summaries),
        "status_counts": _status_counts(summaries),
        "phase_gate_state": _phase_gate_state(
            summaries,
            surface_flux_response,
            low_level_response,
        ),
        "surface_flux_response": surface_flux_response,
        "low_level_response": low_level_response,
        "gate_overrides": _gate_overrides(summaries),
        "runs": summaries,
        "comparisons": comparisons,
        "unavailable_diagnostics": _unavailable_diagnostics(summaries),
        "preliminary_diagnosis_categories": _preliminary_diagnosis_categories(summaries),
        "recommended_follow_ups": _recommended_follow_ups(
            summaries,
            surface_flux_response,
            low_level_response,
        ),
    }

    markdown_path = report_path or _default_report_path(plan)
    if not markdown_path.is_absolute():
        markdown_path = Path.cwd() / markdown_path
    json_path = summary_json_path or (
        resolved_settings.runtime_home.expanduser()
        / "campaigns"
        / _safe_id(plan.campaign_id)
        / "campaign-summary.json"
    )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(_render_markdown_report(plan, summary))
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return CampaignReportArtifacts(
        markdown_path=str(markdown_path),
        summary_json_path=str(json_path),
        summary=summary,
    )


def _validate_selection_source(
    selection: Mapping[str, Any],
    *,
    context: str,
    matrix_base: Path,
    allow_absolute_local_paths: bool,
    errors: list[str],
) -> dict[str, Any]:
    source = _mapping(selection.get("source"), context, errors)
    source_type = source.get("type")
    if source_type not in {"saved_candidate", "cached_recommendation", "uploaded_or_local_igra"}:
        errors.append(
            f"{context}.type must be saved_candidate, cached_recommendation, "
            "or uploaded_or_local_igra"
        )
        return dict(source)
    if source_type == "saved_candidate" and not _optional_string(source.get("saved_candidate_id")):
        errors.append(f"{context}.saved_candidate_id is required")
    if source_type == "cached_recommendation" and not _optional_string(source.get("candidate_id")):
        errors.append(f"{context}.candidate_id is required")
    if source_type == "uploaded_or_local_igra":
        local_text_path = _optional_string(source.get("local_text_path"))
        runtime_file_ref = _optional_string(source.get("runtime_file_ref"))
        if bool(local_text_path) == bool(runtime_file_ref):
            errors.append(
                f"{context} must specify exactly one of local_text_path or runtime_file_ref"
            )
        if not _optional_string(source.get("selected_valid_time_utc")):
            errors.append(f"{context}.selected_valid_time_utc is required")
        if local_text_path:
            configured_path = Path(local_text_path).expanduser()
            if configured_path.is_absolute() and not allow_absolute_local_paths:
                errors.append(
                    f"{context}.local_text_path is absolute; pass --allow-absolute-local-paths "
                    "for local-only matrices and do not commit machine-private paths"
                )
    return dict(source)


def _resolved_run_configuration_payload(
    *,
    defaults: Mapping[str, Any],
    forcing: Mapping[str, Any],
    run: Mapping[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for source in (defaults, forcing, run):
        for key in RUN_CONFIGURATION_KEYS:
            if key in source:
                payload[key] = source[key]
    payload["diagnostic_set"] = "full"
    return payload


def _stable_resume_identity(
    *,
    campaign_id: str,
    matrix_id: str,
    selection_id: str,
    selection_source_reference: str,
    selection_payload_hash: str,
    run_configuration: Mapping[str, Any],
    forcing_id: str | None,
) -> str:
    payload = {
        "campaign_id": campaign_id,
        "matrix_id": matrix_id,
        "selection_id": selection_id,
        "selection_source_reference": selection_source_reference,
        "selection_payload_hash": selection_payload_hash,
        "forcing_id": forcing_id,
        "run_configuration": run_configuration,
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run_id(campaign_id: str, matrix_id: str, stable_identity: str) -> str:
    raw = f"{_safe_id(campaign_id)}-{matrix_id}-{stable_identity[:10]}"
    cleaned = _safe_id(raw)
    return cleaned[:112] or f"campaign-run-{stable_identity[:10]}"


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return cleaned or "campaign"


def _required_summary_fields(data: Any, errors: list[str]) -> dict[str, list[str]]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        errors.append("required_summary_fields must be an object")
        return {}
    output: dict[str, list[str]] = {}
    for group, values in data.items():
        if not isinstance(group, str):
            errors.append("required_summary_fields keys must be strings")
            continue
        if not isinstance(values, list):
            errors.append(f"required_summary_fields.{group} must be a list")
            continue
        fields: list[str] = []
        for value in values:
            if not isinstance(value, str):
                errors.append(f"required_summary_fields.{group} contains a non-string field")
                continue
            if value not in SUPPORTED_REQUIRED_SUMMARY_FIELDS:
                errors.append(f"Unsupported required_summary_fields.{group} field: {value}")
            fields.append(value)
        output[group] = fields
    return output


def _validate_execution(execution: Mapping[str, Any], errors: list[str]) -> None:
    max_concurrent = execution.get("max_concurrent_runs")
    if max_concurrent is not None and (not isinstance(max_concurrent, int) or max_concurrent < 1):
        errors.append("execution.max_concurrent_runs must be an integer >= 1")


def _selection_payload_hash(source: Mapping[str, Any], matrix_base: Path) -> str:
    source_type = source.get("type")
    payload = source.get("selected_sounding_payload") or source.get("observed_sounding_payload")
    if isinstance(payload, dict):
        return _hash_json(payload)
    if source_type == "uploaded_or_local_igra":
        local_text_path = _optional_string(source.get("local_text_path"))
        if local_text_path:
            path = _resolve_matrix_path(local_text_path, matrix_base)
            if path.exists():
                selected_time = _optional_string(source.get("selected_valid_time_utc"))
                return _hash_text(path.read_text() + f"\nselected_time={selected_time}")
        runtime_ref = _optional_string(source.get("runtime_file_ref"))
        if runtime_ref:
            return _hash_text(f"runtime_file_ref:{runtime_ref}")
    return _hash_text(_selection_source_reference(source))


def _hash_json(payload: Mapping[str, Any]) -> str:
    return _hash_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str))


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _selection_source_reference(source: Mapping[str, Any]) -> str:
    source_type = source.get("type")
    if source_type == "saved_candidate":
        return str(source.get("saved_candidate_id"))
    if source_type == "cached_recommendation":
        parts = [str(source.get("candidate_id"))]
        if source.get("station_id"):
            parts.append(str(source.get("station_id")))
        if source.get("valid_time_utc"):
            parts.append(str(source.get("valid_time_utc")))
        return "|".join(parts)
    if source_type == "uploaded_or_local_igra":
        return str(source.get("local_text_path") or source.get("runtime_file_ref"))
    return "unknown"


def _candidate_screening_from_matrix(
    selection: Mapping[str, Any],
    source: Mapping[str, Any],
) -> dict[str, Any] | None:
    payload = selection.get("candidate_screening")
    if isinstance(payload, dict):
        return dict(payload)
    criteria = selection.get("selection_criteria")
    if not isinstance(criteria, dict):
        return None
    preferred_story = _optional_string(criteria.get("preferred_story"))
    if preferred_story is None:
        return None
    return {
        "candidate_id": source.get("candidate_id"),
        "primary_story": preferred_story,
        "primary_story_label": preferred_story.replace("_", " ").title(),
        "story_family": "deep_convection"
        if preferred_story
        in {
            "severe_thunderstorm_environment",
            "supercell_environment",
            "high_cape_pulse_storm",
            "dry_microburst_inverted_v",
            "squall_line_cold_pool_candidate",
            "elevated_convection",
        }
        else "lower_atmosphere",
        "rank_score": criteria.get("score_0_to_100"),
        "evidence": criteria.get("desired_properties") or [],
        "caveats": ["campaign_matrix_selection_criteria_not_recomputed"],
    }


def _candidate_screening_for_package(
    run: CampaignRunPlan,
    *,
    observed: ObservedSoundingRecord,
    settings: CloudChamberSettings,
    matrix_path: Path,
) -> dict[str, Any] | None:
    if run.candidate_screening is not None:
        return run.candidate_screening
    candidate = _candidate_for_source(run, settings=settings, matrix_path=matrix_path)
    if candidate is not None:
        return candidate.model_dump(mode="json")
    return {
        "candidate_id": run.selection_source_reference,
        "station_id": observed.station_id,
        "station_name": observed.station_name,
        "valid_time_utc": observed.valid_time_utc.isoformat(),
        "primary_story": "needs_review",
        "primary_story_label": "Campaign-selected observed sounding",
        "story_family": "review",
        "rank_score": None,
        "evidence": [],
        "caveats": ["campaign_source_has_no_cached_screening_payload"],
    }


def _resolve_observed_sounding(
    run: CampaignRunPlan,
    *,
    settings: CloudChamberSettings,
    matrix_path: Path,
) -> ObservedSoundingRecord:
    source = _source_from_plan(run, matrix_path)
    source_type = source.get("type")
    if source_type == "saved_candidate":
        saved = _saved_candidate(settings, str(source.get("saved_candidate_id")))
        if saved.selected_sounding_payload is None:
            raise CampaignError(
                f"Saved candidate {saved.saved_candidate_id} has no selected sounding payload"
            )
        return observed_sounding_from_payload(saved.selected_sounding_payload)
    if source_type == "cached_recommendation":
        candidate = _candidate_for_source(run, settings=settings, matrix_path=matrix_path)
        if candidate is None or candidate.selected_sounding_payload is None:
            raise CampaignError(
                f"Cached recommendation {source.get('candidate_id')} could not be resolved "
                "to a package-ready observed sounding"
            )
        return observed_sounding_from_payload(candidate.selected_sounding_payload)
    if source_type == "uploaded_or_local_igra":
        text_path = _local_igra_text_path(source, matrix_path)
        selected_time = _parse_utc_datetime(str(source.get("selected_valid_time_utc")))
        return parse_igra_station_text(
            text_path.read_text(),
            uploaded_filename=text_path.name,
            selected_time_utc=selected_time,
        ).selected_sounding
    raise CampaignError(f"Unsupported selection source type: {source_type}")


def _candidate_for_source(
    run: CampaignRunPlan,
    *,
    settings: CloudChamberSettings,
    matrix_path: Path,
) -> SoundingCandidate | None:
    source = _source_from_plan(run, matrix_path)
    if source.get("type") == "saved_candidate":
        saved = _saved_candidate(settings, str(source.get("saved_candidate_id")))
        return saved.candidate
    if source.get("type") != "cached_recommendation":
        return None

    payload = source.get("selected_sounding_payload") or source.get("observed_sounding_payload")
    if isinstance(payload, dict):
        observed = observed_sounding_from_payload(payload)
        return SoundingCandidate(
            candidate_id=str(source.get("candidate_id")),
            station_id=observed.station_id,
            station_name=observed.station_name,
            station_latitude=observed.station_latitude,
            station_longitude=observed.station_longitude,
            station_elevation_m_msl=observed.station_elevation_m_msl,
            valid_time_utc=observed.valid_time_utc,
            source_time_text=observed.source_time_text,
            source_file_name=observed.uploaded_filename,
            source_file_hash="campaign-matrix-payload",
            primary_story="needs_review",
            primary_story_label="Campaign-supplied cached recommendation",
            story_family="review",
            story_scores=[],
            rank_score=0.0,
            confidence="low",
            package_ready=True,
            features={},
            evidence=[],
            caveats=["campaign_matrix_embedded_selected_sounding_payload"],
            selected_sounding_payload=observed.model_dump(mode="json"),
            created_at=_now(),
        )

    station_id = _optional_string(source.get("station_id"))
    valid_time = _optional_string(source.get("valid_time_utc"))
    if station_id and valid_time:
        selected_time = _parse_utc_datetime(valid_time)
        for screening_input in list_screening_inputs(settings):
            if screening_input.station_id != station_id:
                continue
            text_path = Path(screening_input.cached_text_path).expanduser()
            observed = parse_igra_station_text(
                text_path.read_text(),
                uploaded_filename=text_path.name,
                selected_time_utc=selected_time,
            ).selected_sounding
            screened = screen_cached_soundings(
                settings,
                station_id=station_id,
                latest_per_station=int(source.get("latest_per_station", 50)),
                limit=10_000,
            )
            matching = next(
                (
                    candidate
                    for candidate in screened.candidates
                    if candidate.valid_time_utc == selected_time
                ),
                None,
            )
            if matching is not None:
                return matching
            return SoundingCandidate(
                candidate_id=str(source.get("candidate_id")),
                station_id=observed.station_id,
                station_name=observed.station_name,
                station_latitude=observed.station_latitude,
                station_longitude=observed.station_longitude,
                station_elevation_m_msl=observed.station_elevation_m_msl,
                valid_time_utc=observed.valid_time_utc,
                source_time_text=observed.source_time_text,
                source_file_name=observed.uploaded_filename,
                source_file_hash="campaign-cache-resolution",
                primary_story="needs_review",
                primary_story_label="Campaign-selected cached sounding",
                story_family="review",
                story_scores=[],
                rank_score=0.0,
                confidence="low",
                package_ready=True,
                features={},
                evidence=[],
                caveats=["cached_recommendation_resolved_by_station_time_without_screening_match"],
                selected_sounding_payload=observed.model_dump(mode="json"),
                created_at=_now(),
            )

    screened = screen_cached_soundings(
        settings,
        latest_per_station=int(source.get("latest_per_station", 50)),
        limit=10_000,
    )
    candidate_id = str(source.get("candidate_id"))
    return next(
        (candidate for candidate in screened.candidates if candidate.candidate_id == candidate_id),
        None,
    )


def _source_from_plan(run: CampaignRunPlan, matrix_path: Path) -> dict[str, Any]:
    matrix = load_campaign_matrix(matrix_path)
    selection_sets = _indexed_mappings(
        matrix.get("selection_sets", []),
        key="selection_id",
        label="selection_sets",
        errors=[],
    )
    selection = selection_sets.get(run.selection_id)
    if selection is None or not isinstance(selection.get("source"), dict):
        raise CampaignError(f"Selection not found in matrix: {run.selection_id}")
    return dict(selection["source"])


def _saved_candidate(
    settings: CloudChamberSettings, saved_candidate_id: str
) -> SavedSoundingCandidate:
    for candidate in list_saved_candidates(settings):
        if candidate.saved_candidate_id == saved_candidate_id:
            return candidate
    raise CampaignError(f"Saved candidate not found: {saved_candidate_id}")


def _local_igra_text_path(source: Mapping[str, Any], matrix_path: Path) -> Path:
    configured = _optional_string(source.get("local_text_path")) or _optional_string(
        source.get("runtime_file_ref")
    )
    if configured is None:
        raise CampaignError("uploaded_or_local_igra source is missing a text path")
    return _resolve_matrix_path(configured, matrix_path.parent)


def _resolve_matrix_path(value: str, matrix_base: Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (matrix_base / path).resolve()


def _load_or_create_state(plan: CampaignPlan, runtime_home: Path) -> CampaignState:
    path = _state_path(runtime_home, plan.campaign_id)
    if path.exists():
        try:
            return CampaignState.model_validate_json(path.read_text())
        except ValueError as exc:
            raise CampaignError(f"Campaign state is unreadable: {path}: {exc}") from exc
    return CampaignState(
        schema_version=CAMPAIGN_STATE_SCHEMA_VERSION,
        campaign_id=plan.campaign_id,
        matrix_path=plan.matrix_path,
        updated_at=_now(),
        runs=[],
    )


def _save_state(state: CampaignState, runtime_home: Path) -> None:
    updated = state.model_copy(update={"updated_at": _now()})
    path = _state_path(runtime_home, updated.campaign_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated.model_dump_json(indent=2) + "\n")


def _state_path(runtime_home: Path, campaign_id: str) -> Path:
    return runtime_home.expanduser() / "campaigns" / _safe_id(campaign_id) / "campaign-state.json"


def _new_state_run(
    run: CampaignRunPlan,
    *,
    status: str,
    package_status: str,
    run_status: str,
    ingest_status: str,
    manifest_path: str | None = None,
    package_dir: str | None = None,
    result_id: str | None = None,
    error: str | None = None,
    message: str | None = None,
) -> CampaignStateRun:
    if status not in KNOWN_STATUS_VALUES:
        raise CampaignError(f"Unknown campaign status: {status}")
    return CampaignStateRun(
        matrix_id=run.matrix_id,
        stable_resume_identity=run.stable_resume_identity,
        run_id=run.run_id,
        queue_target=run.queue_target,
        status=status,
        package_status=package_status,
        run_status=run_status,
        ingest_status=ingest_status,
        manifest_path=manifest_path,
        package_dir=package_dir,
        result_id=result_id,
        error=error,
        message=message,
        updated_at=_now(),
    )


def _upsert_state_run(state: CampaignState, run: CampaignStateRun) -> None:
    state.runs = [existing for existing in state.runs if existing.matrix_id != run.matrix_id]
    state.runs.append(run)
    state.runs.sort(key=lambda item: item.matrix_id)


def _state_run_for_matrix(state: CampaignState, matrix_id: str) -> CampaignStateRun | None:
    return next((run for run in state.runs if run.matrix_id == matrix_id), None)


def _selected_runs(
    runs: Sequence[CampaignRunPlan],
    selected_matrix_ids: set[str] | None,
    *,
    include_optional: bool = True,
) -> list[CampaignRunPlan]:
    if selected_matrix_ids is None:
        return [run for run in runs if include_optional or not run.optional]
    available = {run.matrix_id for run in runs}
    unknown = sorted(selected_matrix_ids - available)
    if unknown:
        raise CampaignError("Unknown matrix_id values: " + ", ".join(unknown))
    return [run for run in runs if run.matrix_id in selected_matrix_ids]


def _phase_gate_allows_queue(
    run: CampaignRunPlan,
    gate_state: str,
    override_phase_gate: bool,
) -> bool:
    if _is_phase_one_run(run):
        return True
    if gate_state == "forcing_path_verified_for_campaign":
        return True
    return override_phase_gate


def _is_phase_one_run(run: CampaignRunPlan) -> bool:
    if run.phase is not None:
        return run.phase == "forcing_path_smoke_check"
    return run.selection_role == "forcing_path_smoke_check"


def _gate_override_payload(
    *,
    enabled: bool,
    reason: str | None,
    gate_state: str,
) -> dict[str, Any] | None:
    if not enabled:
        return None
    return {
        "enabled": True,
        "reason": reason or "operator_override_without_reason",
        "gate_state_at_override": gate_state,
        "recorded_at": _now().isoformat(),
    }


def _max_concurrent_runs(plan: CampaignPlan) -> int:
    value = plan.execution.get("max_concurrent_runs")
    if isinstance(value, int) and value >= 1:
        return value
    return 1


def _active_lan_count(state: CampaignState) -> int:
    return len(
        [
            run
            for run in state.runs
            if run.queue_target == "lan" and run.status in {"queued", "running"}
        ]
    )


def _default_local_queue(settings: CloudChamberSettings) -> LocalRunQueueManager:
    return LocalRunQueueManager(
        settings=settings,
        run_manager=LocalRunManager(settings=settings),
    )


def _state_run_with_runtime_status(
    state_run: CampaignStateRun,
    run: CampaignRunPlan,
    *,
    settings: CloudChamberSettings,
    queue_entries: Mapping[str, Mapping[str, Any]],
    lan_status: Callable[[CloudChamberSettings, Path], dict[str, object]],
) -> CampaignStateRun:
    if not state_run.manifest_path:
        return state_run
    manifest_path = Path(state_run.manifest_path).expanduser()
    if not manifest_path.exists():
        return state_run.model_copy(
            update={
                "status": "blocked",
                "run_status": "blocked",
                "error": f"Manifest path no longer exists: {manifest_path}",
                "updated_at": _now(),
            }
        )
    manifest = reconcile_completed_run_manifest(manifest_path, load_run_manifest(manifest_path))
    if state_run.status == "blocked":
        return state_run.model_copy(
            update={
                "package_status": "packaged"
                if manifest.lifecycle_state != LifecycleState.CREATED
                else state_run.package_status,
                "updated_at": _now(),
            }
        )
    if run.queue_target == "lan" and state_run.status in {
        "queued",
        "running",
        "completed_not_ingested",
    }:
        try:
            payload = lan_status(settings, manifest_path)
        except LanWorkerApiError as exc:
            return state_run.model_copy(
                update={
                    "message": "LAN worker status could not be refreshed.",
                    "error": str(exc),
                    "updated_at": _now(),
                }
            )
        status = _lan_payload_to_campaign_status(payload)
        return state_run.model_copy(
            update={
                "status": status,
                "run_status": status,
                "lan_worker_payload": dict(payload),
                "message": _payload_message(payload, f"LAN worker status: {status}."),
                "error": None
                if status != "run_failed"
                else _payload_message(payload, "LAN failed."),
                "updated_at": _now(),
            }
        )

    queue_entry = queue_entries.get(str(manifest_path))
    status = _manifest_to_campaign_status(manifest)
    message = state_run.message
    error = state_run.error
    result_id = state_run.result_id
    if queue_entry is not None and manifest.lifecycle_state in {
        LifecycleState.PACKAGED,
        LifecycleState.QUEUED,
        LifecycleState.RUNNING,
    }:
        status = _queue_entry_to_campaign_status(str(queue_entry.get("state")))
        message = _optional_string(queue_entry.get("message")) or message
        error = _optional_string(queue_entry.get("error")) or error
        result_id = _optional_string(queue_entry.get("result_id")) or result_id
    result = _load_result_for_manifest_path(manifest_path)
    if result is not None:
        status = "ingested"
        result_id = result.result_id
        message = "Completed CM1 output ingested."
        error = None
    return state_run.model_copy(
        update={
            "status": status,
            "package_status": "packaged",
            "run_status": status if status not in {"ingested"} else "completed_not_ingested",
            "ingest_status": "ingested" if status == "ingested" else state_run.ingest_status,
            "result_id": result_id,
            "message": message,
            "error": error,
            "updated_at": _now(),
        }
    )


def _manifest_to_campaign_status(manifest: Any) -> str:
    if manifest.lifecycle_state == LifecycleState.PACKAGED:
        return "packaged"
    if manifest.lifecycle_state == LifecycleState.QUEUED:
        return "queued"
    if manifest.lifecycle_state == LifecycleState.RUNNING:
        return "running"
    if manifest.lifecycle_state == LifecycleState.COMPLETED:
        if manifest.provenance.product_state == ProductState.COMPLETED_CM1_RESULT:
            return "completed_not_ingested"
        return "run_failed"
    if manifest.lifecycle_state == LifecycleState.FAILED:
        return "run_failed"
    if manifest.lifecycle_state == LifecycleState.CANCELED:
        return "run_canceled"
    if manifest.lifecycle_state == LifecycleState.INGESTED:
        return "ingested"
    return "blocked"


def _queue_entry_to_campaign_status(state: str) -> str:
    mapping = {
        "queued": "queued",
        "running": "running",
        "ingested": "ingested",
        "ingest_failed": "ingest_failed",
        "completed_no_output": "run_failed",
        "failed": "run_failed",
        "canceled": "run_canceled",
        "launch_failed": "run_failed",
    }
    return mapping.get(state, "blocked")


def _lan_payload_to_campaign_status(payload: Mapping[str, Any]) -> str:
    state = str(payload.get("state", "running"))
    if state in {"running", "started"}:
        return "running"
    if state in {"queued"}:
        return "queued"
    if state in {"ready_for_local_ingest", "completed", "complete"}:
        return "completed_not_ingested"
    if state in {"failed", "error"}:
        return "run_failed"
    return "running"


def _read_queue_entries(runtime_home: Path) -> dict[str, dict[str, Any]]:
    path = runtime_home.expanduser() / "run-queue.json"
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    entries = loaded.get("entries") if isinstance(loaded, dict) else None
    if not isinstance(entries, list):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        manifest_path = _optional_string(entry.get("manifest_path"))
        if manifest_path:
            indexed[manifest_path] = dict(entry)
    return indexed


def _load_result_for_manifest_path(manifest_path: Path) -> ResultMetadata | None:
    path = manifest_path.parent / RESULT_METADATA_FILENAME
    if not path.exists():
        return None
    try:
        return result_metadata_from_json(path.read_text())
    except (OSError, ValueError):
        return None


def _run_dir_has_runtime_artifacts(package_dir: Path) -> bool:
    if not package_dir.exists():
        return False
    patterns = (
        RESULT_METADATA_FILENAME,
        "cm1out_*.nc",
        "cm1out_*.nc4",
        "cm1out_*.cdf",
        "cm1out_*.netcdf",
        "cm1out_*.dat",
        "cm1out_*.ctl",
        "logs/*.log",
        "logs/*",
    )
    for pattern in patterns:
        if list(package_dir.glob(pattern)):
            return True
    return False


def _repo_commit() -> str | None:
    try:
        completed = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            check=True,
            cwd=Path(__file__).resolve().parents[3],
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    commit = completed.stdout.strip()
    return commit or None


def _summary_for_plan_run(run: CampaignRunPlan, state: CampaignState) -> dict[str, Any]:
    state_run = _state_run_for_matrix(state, run.matrix_id)
    manifest = None
    result = None
    if state_run is not None and state_run.manifest_path:
        manifest_path = Path(state_run.manifest_path).expanduser()
        if manifest_path.exists():
            manifest = load_run_manifest(manifest_path)
            result = _load_result_for_manifest_path(manifest_path)
    observed = manifest.observed_sounding if manifest is not None else None
    diagnostics = result.diagnostics if result is not None else None
    science = result.science_summary if result is not None else None
    variables = set(result.variables) if result is not None else set()
    required_fields = _normalize_campaign_output_fields(
        manifest.required_output_fields if manifest is not None else []
    )
    missing_fields = (
        _normalize_campaign_missing_output_fields(result.missing_required_output_fields, variables)
        if result is not None
        else ["unavailable:until_result_ingested"]
    )
    warnings = _normalize_campaign_messages(
        result.warnings if result is not None else [], variables
    )
    caveats = _normalize_campaign_messages(_summary_caveats(run, state_run, result), variables)
    field_quality = diagnostics.field_quality if diagnostics is not None else None
    field_quality_assessed = (
        diagnostics.field_quality_assessed if diagnostics is not None else False
    )
    diagnostic_trust = _diagnostic_trust(
        caveats,
        field_quality,
        field_quality_assessed=field_quality_assessed,
    )
    diagnostic_quality_warnings = _diagnostic_quality_warnings(caveats, field_quality)
    candidate = manifest.candidate_screening if manifest is not None else run.candidate_screening
    cloud = diagnostics.cloud if diagnostics is not None else None
    vertical_velocity = diagnostics.vertical_velocity if diagnostics is not None else None
    rain = diagnostics.rain if diagnostics is not None else None
    surface_rain = diagnostics.surface_rain if diagnostics is not None else None
    reflectivity = diagnostics.reflectivity if diagnostics is not None else None
    surface_fluxes = diagnostics.surface_fluxes if diagnostics is not None else None
    low_level_response = diagnostics.low_level_response if diagnostics is not None else None
    hfx_stats = _surface_flux_summary_values(
        surface_fluxes.hfx if surface_fluxes is not None else None,
        source_field="hfx",
        fallback_units=_field_units(result, "hfx"),
    )
    qfx_stats = _surface_flux_summary_values(
        surface_fluxes.qfx if surface_fluxes is not None else None,
        source_field="qfx",
        fallback_units=_field_units(result, "qfx"),
    )
    low_level_qv = _low_level_response_summary_values(
        low_level_response.qv if low_level_response is not None else None,
        fallback_source_field="qv",
        fallback_units=_field_units(result, "qv"),
    )
    low_level_thermal = _low_level_response_summary_values(
        low_level_response.theta_or_temperature if low_level_response is not None else None,
        fallback_source_field=_first_available_field(
            result,
            ["th", "theta", "temperature", "t"],
        ),
        fallback_units=_field_units(
            result,
            _first_available_field(result, ["th", "theta", "temperature", "t"]),
        ),
    )
    deep_cloud_formed = (
        science.deep_cloud_formed if science is not None else "unavailable:not_ingested"
    )
    first_cloud_time = _trusted_outcome(
        _first_defined(
            cloud.first_cloud_time_seconds if cloud is not None else None,
            science.first_cloud_time_seconds if science is not None else None,
        ),
        diagnostic_trust,
        "qc",
    )
    max_cloud_top_m = _trusted_outcome(
        _first_defined(
            cloud.cloud_top_m if cloud is not None else None,
            science.highest_cloud_top_m if science is not None else None,
        ),
        diagnostic_trust,
        "qc",
    )
    max_cloud_top_time = _trusted_outcome(
        _time_of_max_time_value(cloud.cloud_top_time_series if cloud is not None else []),
        diagnostic_trust,
        "qc",
    )
    max_qc = _trusted_outcome(
        _first_defined(
            cloud.max_qc_kg_kg if cloud is not None else None,
            science.max_qc_kg_kg if science is not None else None,
        ),
        diagnostic_trust,
        "qc",
    )
    max_qc_time = _trusted_outcome(
        _first_defined(
            cloud.time_of_max_qc_seconds if cloud is not None else None,
            science.max_qc_time_seconds if science is not None else None,
        ),
        diagnostic_trust,
        "qc",
    )
    max_w_m_s = _trusted_outcome(
        _first_defined(
            vertical_velocity.max_w_m_s if vertical_velocity is not None else None,
            science.max_updraft_w_m_s if science is not None else None,
        ),
        diagnostic_trust,
        "w",
    )
    max_w_time = _trusted_outcome(
        _first_defined(
            vertical_velocity.time_of_max_w_seconds if vertical_velocity is not None else None,
            science.max_updraft_time_seconds if science is not None else None,
        ),
        diagnostic_trust,
        "w",
    )
    max_w_height_m = _trusted_outcome(
        _time_value_at_time(
            vertical_velocity.max_w_height_time_series if vertical_velocity is not None else [],
            vertical_velocity.time_of_max_w_seconds if vertical_velocity is not None else None,
        ),
        diagnostic_trust,
        "w",
    )
    qr_present = _trusted_outcome(
        rain.present if rain is not None else None, diagnostic_trust, "qr"
    )
    surface_rain_present = _trusted_outcome(
        surface_rain.present if surface_rain is not None else None,
        diagnostic_trust,
        "surface_rain",
    )
    surface_rain_max = _trusted_outcome(
        surface_rain.max_surface_rain if surface_rain is not None else None,
        diagnostic_trust,
        "surface_rain",
    )
    dbz_present = _trusted_outcome(
        reflectivity.max_dbz is not None if reflectivity is not None else None,
        diagnostic_trust,
        "dbz",
    )
    max_dbz = _trusted_outcome(
        reflectivity.max_dbz if reflectivity is not None else None,
        diagnostic_trust,
        "dbz",
    )
    terminal_contamination = _terminal_output_contamination_summary(field_quality, warnings)
    summary = {
        "schema_version": CAMPAIGN_SUMMARY_SCHEMA_VERSION,
        "campaign_id": run.campaign_id,
        "matrix_id": run.matrix_id,
        "phase": run.phase,
        "stable_resume_identity": run.stable_resume_identity,
        "run_id": state_run.run_id if state_run else run.run_id,
        "result_id": (
            result.result_id if result is not None else state_run.result_id if state_run else None
        ),
        "status": state_run.status if state_run else "planned",
        "package_status": state_run.package_status if state_run else "planned",
        "run_status": state_run.run_status if state_run else "planned",
        "ingest_status": state_run.ingest_status if state_run else "not_started",
        "queue_target": run.queue_target,
        "source_manifest_lifecycle_state": (
            manifest.lifecycle_state.value if manifest is not None else None
        ),
        "source_manifest_product_state": (
            manifest.provenance.product_state.value if manifest is not None else None
        ),
        "station_id": _mapping_value(observed, "station_id"),
        "station_name": _mapping_value(observed, "station_name"),
        "valid_time_utc": _mapping_value(observed, "valid_time_utc"),
        "selection_id": run.selection_id,
        "selection_source_type": run.selection_source_type,
        "selection_source_reference": run.selection_source_reference,
        "candidate_id": _mapping_value(candidate, "candidate_id"),
        "candidate_story": _mapping_value(candidate, "primary_story"),
        "candidate_score": _mapping_value(candidate, "rank_score"),
        "candidate_evidence": _candidate_evidence(candidate),
        "candidate_caveats": _list_from_mapping(candidate, "caveats"),
        "surface_heat_flux_k_m_s": run.run_configuration["surface_heat_flux_k_m_s"],
        "surface_heat_flux_units": "K m/s",
        "surface_moisture_flux_g_g_m_s": run.run_configuration["surface_moisture_flux_g_g_m_s"],
        "surface_moisture_flux_units": "g/g m/s",
        "cm1_cnst_shflx": run.surface_flux_cm1_values.get("cnst_shflx"),
        "cm1_cnst_shflx_units": run.surface_flux_cm1_values.get("cnst_shflx_units"),
        "cm1_cnst_lhflx": run.surface_flux_cm1_values.get("cnst_lhflx"),
        "cm1_cnst_lhflx_units": run.surface_flux_cm1_values.get("cnst_lhflx_units"),
        "duration": run.run_configuration["duration"],
        "duration_seconds": run.resolved_run_configuration["duration_seconds"],
        "domain_size": run.run_configuration["domain_size"],
        "horizontal_cell_count": run.resolved_run_configuration["horizontal_cell_count"],
        "nx": run.cm1_values.get("nx"),
        "ny": run.cm1_values.get("ny"),
        "nz": run.cm1_values.get("nz"),
        "dx_m": run.cm1_values.get("dx_m"),
        "dy_m": run.cm1_values.get("dy_m"),
        "dz_m": run.cm1_values.get("dz_m"),
        "stretch_z": run.cm1_values.get("stretch_z"),
        "str_bot_m": run.cm1_values.get("str_bot_m"),
        "str_top_m": run.cm1_values.get("str_top_m"),
        "dz_bot_m": run.cm1_values.get("dz_bot_m"),
        "dz_top_m": run.cm1_values.get("dz_top_m"),
        "model_top_m": run.cm1_values.get("model_top_m"),
        "output_cadence": run.run_configuration["output_cadence"],
        "expected_output_frames": run.cm1_values.get("expected_output_frames"),
        "expected_output_volume": run.resolved_run_configuration.get("output_volume_summary"),
        "cloud_chamber_commit": manifest.app.commit if manifest is not None else None,
        "cm1_version": "unavailable:cm1_version_not_recorded",
        "cm1_build": "unavailable:cm1_build_not_recorded",
        "required_output_fields": required_fields,
        "missing_output_fields": missing_fields,
        "available_output_fields": sorted(variables),
        "evidence_fields": sorted(variables),
        "diagnostic_support": _diagnostic_support(result),
        "diagnostic_trust": diagnostic_trust,
        "diagnostic_quality_warnings": diagnostic_quality_warnings,
        "interesting_time_support_state": (
            science.interesting_time_support_state
            if science is not None
            else "unavailable:not_ingested"
        ),
        "hfx_present": "hfx" in variables,
        "hfx_units": hfx_stats["units"],
        "hfx_min": hfx_stats["min"],
        "hfx_max": hfx_stats["max"],
        "hfx_mean": hfx_stats["mean"],
        "hfx_finite_count": hfx_stats["finite_count"],
        "hfx_non_finite_count": hfx_stats["non_finite_count"],
        "hfx_total_count": hfx_stats["total_count"],
        "hfx_finite_fraction": hfx_stats["finite_fraction"],
        "hfx_frame_quality": hfx_stats["frame_quality"],
        "qfx_present": "qfx" in variables,
        "qfx_units": qfx_stats["units"],
        "qfx_min": qfx_stats["min"],
        "qfx_max": qfx_stats["max"],
        "qfx_mean": qfx_stats["mean"],
        "qfx_finite_count": qfx_stats["finite_count"],
        "qfx_non_finite_count": qfx_stats["non_finite_count"],
        "qfx_total_count": qfx_stats["total_count"],
        "qfx_finite_fraction": qfx_stats["finite_fraction"],
        "qfx_frame_quality": qfx_stats["frame_quality"],
        "terminal_output_contamination": terminal_contamination["present"],
        "terminal_output_contamination_fields": terminal_contamination["fields"],
        "runtime_floating_point_warnings": terminal_contamination["warnings"],
        "surface_moisture_flux_output_field": _surface_moisture_flux_field(variables),
        "lhfx_present": _surface_moisture_flux_field(variables) is not None,
        "lhfx_units": qfx_stats["units"],
        "lhfx_min": qfx_stats["min"],
        "lhfx_max": qfx_stats["max"],
        "lhfx_mean": qfx_stats["mean"],
        "low_level_qv_response": low_level_qv["early_delta"],
        "low_level_qv_early_response_available": low_level_qv["early_response_available"],
        "low_level_qv_full_run_response_available": low_level_qv["full_run_response_available"],
        "low_level_qv_early_response_delta": low_level_qv["early_delta"],
        "low_level_qv_early_response_delta_units": low_level_qv["units"],
        "low_level_qv_early_response_start_mean": low_level_qv["early_start_mean"],
        "low_level_qv_early_response_end_mean": low_level_qv["early_end_mean"],
        "low_level_qv_early_response_start_time_seconds": low_level_qv["early_start_time_seconds"],
        "low_level_qv_early_response_end_time_seconds": low_level_qv["early_end_time_seconds"],
        "low_level_qv_early_response_start_finite_fraction": low_level_qv[
            "early_start_finite_fraction"
        ],
        "low_level_qv_early_response_end_finite_fraction": low_level_qv[
            "early_end_finite_fraction"
        ],
        "low_level_qv_early_response_min_finite_fraction": low_level_qv[
            "early_min_finite_fraction"
        ],
        "low_level_qv_early_response_quality_state": low_level_qv["early_quality_state"],
        "low_level_qv_full_run_delta": low_level_qv["full_delta"],
        "low_level_qv_response_method": low_level_qv["method"],
        "low_level_qv_response_source_field": low_level_qv["source_field"],
        "low_level_qv_response_units": low_level_qv["units"],
        "low_level_qv_response_first_mean": low_level_qv["first_mean"],
        "low_level_qv_response_final_mean": low_level_qv["final_mean"],
        "low_level_qv_response_first_time_seconds": low_level_qv["first_time_seconds"],
        "low_level_qv_response_final_time_seconds": low_level_qv["final_time_seconds"],
        "low_level_qv_response_first_finite_count": low_level_qv["first_finite_count"],
        "low_level_qv_response_final_finite_count": low_level_qv["final_finite_count"],
        "low_level_theta_or_temperature_response": low_level_thermal["early_delta"],
        "low_level_theta_or_temperature_early_response_available": low_level_thermal[
            "early_response_available"
        ],
        "low_level_theta_or_temperature_full_run_response_available": low_level_thermal[
            "full_run_response_available"
        ],
        "low_level_theta_or_temperature_early_response_delta": low_level_thermal["early_delta"],
        "low_level_theta_or_temperature_early_response_delta_units": low_level_thermal["units"],
        "low_level_theta_or_temperature_early_response_start_mean": low_level_thermal[
            "early_start_mean"
        ],
        "low_level_theta_or_temperature_early_response_end_mean": low_level_thermal[
            "early_end_mean"
        ],
        "low_level_theta_or_temperature_early_response_start_time_seconds": low_level_thermal[
            "early_start_time_seconds"
        ],
        "low_level_theta_or_temperature_early_response_end_time_seconds": low_level_thermal[
            "early_end_time_seconds"
        ],
        "low_level_theta_or_temperature_early_response_start_finite_fraction": low_level_thermal[
            "early_start_finite_fraction"
        ],
        "low_level_theta_or_temperature_early_response_end_finite_fraction": low_level_thermal[
            "early_end_finite_fraction"
        ],
        "low_level_theta_or_temperature_early_response_min_finite_fraction": low_level_thermal[
            "early_min_finite_fraction"
        ],
        "low_level_theta_or_temperature_early_response_quality_state": low_level_thermal[
            "early_quality_state"
        ],
        "low_level_theta_or_temperature_full_run_delta": low_level_thermal["full_delta"],
        "low_level_theta_or_temperature_response_method": low_level_thermal["method"],
        "low_level_theta_or_temperature_response_source_field": low_level_thermal["source_field"],
        "low_level_theta_or_temperature_response_units": low_level_thermal["units"],
        "low_level_theta_or_temperature_response_first_mean": low_level_thermal["first_mean"],
        "low_level_theta_or_temperature_response_final_mean": low_level_thermal["final_mean"],
        "low_level_theta_or_temperature_response_first_time_seconds": low_level_thermal[
            "first_time_seconds"
        ],
        "low_level_theta_or_temperature_response_final_time_seconds": low_level_thermal[
            "final_time_seconds"
        ],
        "low_level_theta_or_temperature_response_first_finite_count": low_level_thermal[
            "first_finite_count"
        ],
        "low_level_theta_or_temperature_response_final_finite_count": low_level_thermal[
            "final_finite_count"
        ],
        "first_cloud_time": first_cloud_time,
        "max_cloud_top_m": max_cloud_top_m,
        "max_cloud_top_time": max_cloud_top_time,
        "max_qc": max_qc,
        "max_qc_time": max_qc_time,
        "cloud_depth_or_classification": _cloud_depth_or_classification(result, diagnostic_trust),
        "max_w_m_s": max_w_m_s,
        "max_w_time": max_w_time,
        "max_w_height_m": max_w_height_m,
        "qr_present": qr_present,
        "surface_rain_present": surface_rain_present,
        "surface_rain_max": surface_rain_max,
        "surface_rain_units": surface_rain.units if surface_rain is not None else None,
        "dbz_present": dbz_present,
        "max_dbz": max_dbz,
        "deep_cloud_formed": deep_cloud_formed,
        "deep_cloud_flag": deep_cloud_formed,
        "first_deep_cloud_time": (
            science.time_of_first_deep_convection_seconds
            if science is not None
            else "unavailable:not_ingested"
        ),
        "warnings": warnings,
        "caveats": caveats,
        "gate_override": state_run.gate_override if state_run is not None else None,
        "error": state_run.error if state_run else None,
    }
    return {
        **summary,
        "trusted_key_result": _key_result_label(summary),
    }


def _diagnostic_support(result: ResultMetadata | None) -> dict[str, str]:
    if result is None or result.diagnostics is None:
        return {
            "surface_fluxes": "unavailable:until_result_ingested",
            "low_level_response": "unavailable:until_result_ingested",
            "cloud": "unavailable:until_result_ingested",
            "vertical_velocity": "unavailable:until_result_ingested",
            "rain_water_aloft": "unavailable:until_result_ingested",
            "surface_rain": "unavailable:until_result_ingested",
            "reflectivity": "unavailable:until_result_ingested",
        }
    diagnostics = result.diagnostics
    variables = set(result.variables)
    return {
        "surface_fluxes": _surface_flux_support(diagnostics.surface_fluxes, variables),
        "low_level_response": _low_level_response_support(diagnostics.low_level_response),
        "cloud": "available" if diagnostics.cloud.available else "missing",
        "vertical_velocity": "available" if diagnostics.vertical_velocity.available else "missing",
        "rain_water_aloft": "available" if diagnostics.rain.available else "missing",
        "surface_rain": "available" if diagnostics.surface_rain.available else "missing",
        "reflectivity": "available" if diagnostics.reflectivity.available else "missing",
    }


def _surface_flux_support(
    diagnostics: SurfaceFluxDiagnostics,
    variables: set[str],
) -> str:
    field_presence = "hfx" in variables and _surface_moisture_flux_field(variables) is not None
    if diagnostics.hfx.available and diagnostics.qfx.available:
        return "available"
    if field_presence:
        return "unavailable:surface_flux_statistics_unavailable"
    return "missing"


def _low_level_response_support(response: Any) -> str:
    qv = response.qv
    thermal = response.theta_or_temperature
    if qv.early_response_available and thermal.early_response_available:
        return "available"
    if qv.field_absent or thermal.field_absent:
        return "missing"
    reasons = [
        _low_level_response_early_unavailable_reason(field)
        for field in (qv, thermal)
        if not field.early_response_available
    ]
    return "unavailable:" + ",".join(_dedupe([reason for reason in reasons if reason]))


def _field_units(result: ResultMetadata | None, field_name: str | None) -> str | None:
    if result is None or field_name is None:
        return None
    return next((field.units for field in result.fields_detected if field.name == field_name), None)


def _surface_flux_summary_values(
    diagnostics: SurfaceFluxFieldDiagnostics | None,
    *,
    source_field: str,
    fallback_units: str | None,
) -> dict[str, Any]:
    if diagnostics is None:
        unavailable = "unavailable:until_result_ingested"
        return {
            "units": fallback_units,
            "min": unavailable,
            "max": unavailable,
            "mean": unavailable,
            "finite_count": 0,
            "non_finite_count": 0,
            "total_count": 0,
            "finite_fraction": None,
            "frame_quality": None,
        }
    if diagnostics.available:
        return {
            "units": diagnostics.units or fallback_units,
            "min": diagnostics.min_value,
            "max": diagnostics.max_value,
            "mean": diagnostics.mean_value,
            "finite_count": diagnostics.finite_count,
            "non_finite_count": diagnostics.non_finite_count,
            "total_count": diagnostics.total_count,
            "finite_fraction": diagnostics.finite_fraction,
            "frame_quality": _frame_quality_summary_values(diagnostics.frame_quality),
        }
    if diagnostics.field_absent:
        reason = f"unavailable:{source_field}_field_absent"
    elif diagnostics.total_count > 0 and diagnostics.finite_count == 0:
        reason = f"unavailable:{source_field}_field_entirely_non_finite"
    else:
        reason = f"unavailable:{source_field}_statistics_unavailable"
    return {
        "units": diagnostics.units or fallback_units,
        "min": reason,
        "max": reason,
        "mean": reason,
        "finite_count": diagnostics.finite_count,
        "non_finite_count": diagnostics.non_finite_count,
        "total_count": diagnostics.total_count,
        "finite_fraction": diagnostics.finite_fraction,
        "frame_quality": _frame_quality_summary_values(diagnostics.frame_quality),
    }


def _frame_quality_summary_values(
    frame_quality: FieldFrameQualitySummary | None,
) -> dict[str, Any] | None:
    if frame_quality is None:
        return None
    return {
        "frame_times_seconds": frame_quality.frame_times_seconds,
        "affected_frame_indices": frame_quality.affected_frame_indices,
        "affected_frame_times_seconds": frame_quality.affected_frame_times_seconds,
        "initial_frame_affected": frame_quality.initial_frame_affected,
        "terminal_frame_affected": frame_quality.terminal_frame_affected,
        "affected_frame_count": frame_quality.affected_frame_count,
        "entirely_non_finite_frame_count": frame_quality.entirely_non_finite_frame_count,
        "partially_non_finite_frame_count": frame_quality.partially_non_finite_frame_count,
        "finite_frame_count": frame_quality.finite_frame_count,
        "total_frame_count": frame_quality.total_frame_count,
        "finite_point_fraction": frame_quality.finite_point_fraction,
        "chronology_available": frame_quality.chronology_available,
        "chronology_caveats": frame_quality.chronology_caveats,
        "first_finite_frame_time_seconds": frame_quality.first_finite_frame_time_seconds,
        "last_finite_frame_time_seconds": frame_quality.last_finite_frame_time_seconds,
        "affected_frames": [
            {
                "frame_index": frame.frame_index,
                "time_seconds": frame.time_seconds,
                "position": frame.position,
                "finite_count": frame.finite_count,
                "non_finite_count": frame.non_finite_count,
                "total_count": frame.total_count,
                "entirely_non_finite": frame.entirely_non_finite,
            }
            for frame in frame_quality.affected_frames
        ],
    }


def _low_level_response_summary_values(
    diagnostics: LowLevelResponseFieldDiagnostics | None,
    *,
    fallback_source_field: str | None,
    fallback_units: str | None,
) -> dict[str, Any]:
    unavailable = "unavailable:until_result_ingested"
    if diagnostics is None:
        return {
            "source_field": fallback_source_field,
            "units": fallback_units,
            "early_response_available": False,
            "full_run_response_available": False,
            "early_delta": unavailable,
            "early_start_mean": unavailable,
            "early_end_mean": unavailable,
            "early_start_time_seconds": unavailable,
            "early_end_time_seconds": unavailable,
            "early_start_finite_count": 0,
            "early_start_total_count": 0,
            "early_start_finite_fraction": None,
            "early_end_finite_count": 0,
            "early_end_total_count": 0,
            "early_end_finite_fraction": None,
            "early_min_finite_fraction": None,
            "early_quality_state": "unavailable",
            "full_delta": unavailable,
            "first_mean": unavailable,
            "final_mean": unavailable,
            "first_time_seconds": unavailable,
            "final_time_seconds": unavailable,
            "first_finite_count": 0,
            "final_finite_count": 0,
            "method": unavailable,
        }
    early_reason = _low_level_response_early_unavailable_reason(diagnostics)
    full_reason = _low_level_response_full_run_unavailable_reason(diagnostics)
    method = (
        diagnostics.vertical_coordinate_method
        if diagnostics.vertical_coordinate_method is not None
        else f"unavailable:{early_reason}"
    )
    early_unavailable = f"unavailable:{early_reason}"
    full_unavailable = f"unavailable:{full_reason}"
    early_start_fraction = _finite_fraction(
        diagnostics.early_response_start_finite_count,
        diagnostics.early_response_start_total_count,
    )
    early_end_fraction = _finite_fraction(
        diagnostics.early_response_end_finite_count,
        diagnostics.early_response_end_total_count,
    )
    early_min_fraction = _min_defined([early_start_fraction, early_end_fraction])
    early_quality_state = _low_level_early_quality_state(diagnostics, early_min_fraction)
    return {
        "source_field": diagnostics.source_field or fallback_source_field,
        "units": diagnostics.units or fallback_units,
        "early_response_available": diagnostics.early_response_available,
        "full_run_response_available": diagnostics.full_run_response_available,
        "early_delta": (
            diagnostics.early_response_delta
            if diagnostics.early_response_available
            else early_unavailable
        ),
        "early_start_mean": (
            diagnostics.early_response_start_mean_value
            if diagnostics.early_response_available
            else early_unavailable
        ),
        "early_end_mean": (
            diagnostics.early_response_end_mean_value
            if diagnostics.early_response_available
            else early_unavailable
        ),
        "early_start_time_seconds": (
            diagnostics.early_response_start_time_seconds
            if diagnostics.early_response_available
            else early_unavailable
        ),
        "early_end_time_seconds": (
            diagnostics.early_response_end_time_seconds
            if diagnostics.early_response_available
            else early_unavailable
        ),
        "early_start_finite_count": diagnostics.early_response_start_finite_count,
        "early_start_total_count": diagnostics.early_response_start_total_count,
        "early_start_finite_fraction": early_start_fraction,
        "early_end_finite_count": diagnostics.early_response_end_finite_count,
        "early_end_total_count": diagnostics.early_response_end_total_count,
        "early_end_finite_fraction": early_end_fraction,
        "early_min_finite_fraction": early_min_fraction,
        "early_quality_state": early_quality_state,
        "full_delta": (
            diagnostics.full_run_delta
            if diagnostics.full_run_response_available
            else full_unavailable
        ),
        "first_mean": (
            diagnostics.first_mean_value
            if diagnostics.first_mean_value is not None
            else full_unavailable
        ),
        "final_mean": (
            diagnostics.final_mean_value
            if diagnostics.final_mean_value is not None
            else full_unavailable
        ),
        "first_time_seconds": (
            diagnostics.first_time_seconds
            if diagnostics.first_time_seconds is not None
            else full_unavailable
        ),
        "final_time_seconds": (
            diagnostics.final_time_seconds
            if diagnostics.final_time_seconds is not None
            else full_unavailable
        ),
        "first_finite_count": diagnostics.first_finite_count,
        "final_finite_count": diagnostics.final_finite_count,
        "method": method,
    }


def _low_level_response_unavailable_reason(
    diagnostics: LowLevelResponseFieldDiagnostics,
) -> str:
    if diagnostics.available:
        return "available"
    if diagnostics.caveats:
        return diagnostics.caveats[0]
    if diagnostics.field_absent:
        source_field = diagnostics.source_field or "theta_or_temperature"
        return f"{source_field}_field_absent"
    return "low_level_response_unavailable"


def _low_level_response_early_unavailable_reason(
    diagnostics: LowLevelResponseFieldDiagnostics,
) -> str:
    if diagnostics.early_response_available:
        return "available"
    if diagnostics.field_absent:
        source_field = diagnostics.source_field or "theta_or_temperature"
        return f"{source_field}_field_absent"
    for caveat in diagnostics.caveats:
        if (
            "missing_early_output" in caveat
            or "early_endpoint_entirely_non_finite" in caveat
            or "start_endpoint_entirely_non_finite" in caveat
            or "requires_at_least_two_time_steps" in caveat
            or "missing_vertical" in caveat
            or "vertical_units_not_supported" in caveat
            or "unavailable" in caveat
        ):
            return caveat
    return "low_level_early_response_unavailable"


def _low_level_response_full_run_unavailable_reason(
    diagnostics: LowLevelResponseFieldDiagnostics,
) -> str:
    if diagnostics.full_run_response_available:
        return "available"
    if diagnostics.field_absent:
        source_field = diagnostics.source_field or "theta_or_temperature"
        return f"{source_field}_field_absent"
    for caveat in diagnostics.caveats:
        if (
            "final_endpoint_entirely_non_finite" in caveat
            or "start_endpoint_entirely_non_finite" in caveat
            or "requires_at_least_two_time_steps" in caveat
            or "missing_vertical" in caveat
            or "vertical_units_not_supported" in caveat
            or "unavailable" in caveat
        ):
            return caveat
    return "low_level_full_run_response_unavailable"


def _finite_fraction(finite_count: int, total_count: int) -> float | None:
    if total_count <= 0:
        return None
    return finite_count / total_count


def _min_defined(values: Sequence[float | None]) -> float | None:
    defined = [value for value in values if value is not None]
    return min(defined) if defined else None


def _low_level_early_quality_state(
    diagnostics: LowLevelResponseFieldDiagnostics,
    finite_fraction: float | None,
) -> str:
    if not diagnostics.early_response_available:
        return "unavailable"
    if (
        finite_fraction is not None
        and finite_fraction < LOW_LEVEL_RESPONSE_MIN_EARLY_FINITE_FRACTION
    ):
        return "caveated_below_minimum_finite_fraction"
    if (
        diagnostics.early_response_start_non_finite_count > 0
        or diagnostics.early_response_end_non_finite_count > 0
    ):
        return "caveated"
    return "trusted"


def _first_available_field(result: ResultMetadata | None, fields: Sequence[str]) -> str | None:
    if result is None:
        return None
    variables = set(result.variables)
    return next((field for field in fields if field in variables), None)


def _surface_moisture_flux_field(fields: Iterable[str]) -> str | None:
    available = set(fields)
    if "qfx" in available:
        return "qfx"
    if "lhfx" in available:
        return "lhfx"
    return None


def _normalize_campaign_output_fields(fields: Iterable[str]) -> list[str]:
    return _dedupe(_normalize_campaign_output_field_name(field) for field in fields)


def _normalize_campaign_output_field_name(field: str) -> str:
    return "qfx" if field == "lhfx" else field


def _normalize_campaign_missing_output_fields(
    fields: Iterable[str], available_fields: set[str]
) -> list[str]:
    normalized: list[str] = []
    for field in fields:
        if field.startswith("unavailable:"):
            normalized.append(field)
            continue
        report_field = _normalize_campaign_output_field_name(field)
        if _field_available(report_field, available_fields):
            continue
        normalized.append(report_field)
    return _dedupe(normalized)


def _normalize_campaign_messages(messages: Iterable[str], available_fields: set[str]) -> list[str]:
    normalized: list[str] = []
    for message in messages:
        if _stale_lhfx_missing_message(message, available_fields):
            continue
        normalized.append(message.replace("lhfx", "qfx"))
    return _dedupe(normalized)


FIELD_TRUST_CAVEATS = {
    "qc": {
        "missing": "missing_qc_field",
        "partial": "non_finite_values_detected_in_qc",
        "entire": "qc_field_entirely_non_finite",
    },
    "w": {
        "missing": "missing_w_field",
        "partial": "non_finite_values_detected_in_w",
        "entire": "w_field_entirely_non_finite",
    },
    "qr": {
        "missing": "qr_field_absent",
        "partial": "non_finite_values_detected_in_qr",
        "entire": "qr_field_entirely_non_finite",
    },
    "surface_rain": {
        "missing": "surface_rain_field_absent",
        "partial": "non_finite_values_detected_in_surface_rain",
        "entire": "surface_rain_field_entirely_non_finite",
    },
    "dbz": {
        "missing": "dbz_field_absent",
        "partial": "non_finite_values_detected_in_dbz",
        "entire": "dbz_field_entirely_non_finite",
    },
}


def _diagnostic_trust(
    caveats: Iterable[str],
    field_quality: Mapping[str, FieldQuality] | None = None,
    *,
    field_quality_assessed: bool = False,
) -> dict[str, str]:
    caveat_set = set(caveats)
    if "result_not_ingested" in caveat_set:
        return {field: "unavailable_until_result_ingested" for field in FIELD_TRUST_CAVEATS}
    if field_quality_assessed:
        quality_trust: dict[str, str] = {}
        for field, codes in FIELD_TRUST_CAVEATS.items():
            quality = (field_quality or {}).get(field)
            if quality is None:
                quality_trust[field] = "not_assessed"
            elif quality.quality_state == "untrusted":
                if (
                    quality.reason is not None
                    and "_terminal_output_frame_entirely_non_finite" in quality.reason
                ):
                    quality_trust[field] = "untrusted_terminal_non_finite_frame"
                elif (
                    quality.reason is not None
                    and "_intermediate_output_frame_entirely_non_finite" in quality.reason
                ):
                    quality_trust[field] = "untrusted_intermediate_non_finite_frame"
                else:
                    quality_trust[field] = "untrusted_entirely_non_finite"
            elif quality.quality_state == "unavailable":
                quality_trust[field] = "unavailable_field_missing"
            elif quality.quality_state == "caveated":
                quality_trust[field] = "caveated_non_finite_values_detected"
            else:
                quality_trust[field] = "trusted"
            if quality is not None and quality.reason == codes["entire"]:
                quality_trust[field] = "untrusted_entirely_non_finite"
        return quality_trust
    trust: dict[str, str] = {}
    for field, codes in FIELD_TRUST_CAVEATS.items():
        if codes["entire"] in caveat_set:
            trust[field] = "untrusted_entirely_non_finite"
        elif codes["missing"] in caveat_set:
            trust[field] = "unavailable_field_missing"
        elif codes["partial"] in caveat_set:
            trust[field] = "caveated_non_finite_values_detected"
        else:
            trust[field] = "not_assessed"
    return trust


def _diagnostic_quality_warnings(
    caveats: Iterable[str],
    field_quality: Mapping[str, FieldQuality] | None = None,
) -> list[str]:
    return _dedupe(
        [
            *(
                caveat
                for caveat in caveats
                if "non_finite" in caveat or caveat.endswith("_field_entirely_non_finite")
            ),
            *(
                caveat
                for quality in (field_quality or {}).values()
                for caveat in quality.caveats
                if "non_finite" in caveat or caveat.endswith("_field_entirely_non_finite")
            ),
        ]
    )


def _terminal_output_contamination_summary(
    field_quality: Mapping[str, FieldQuality] | None,
    warnings: Iterable[str],
) -> dict[str, Any]:
    fields: list[str] = []
    for field, quality in (field_quality or {}).items():
        if _frame_quality_has_terminal_entirely_non_finite(
            _frame_quality_summary_values(quality.frame_quality)
        ):
            fields.append(field)
    warning_list = [
        warning
        for warning in warnings
        if "IEEE_" in warning or "floating-point exception" in warning
    ]
    return {
        "present": bool(fields),
        "fields": sorted(fields),
        "warnings": _dedupe(warning_list),
    }


def _trusted_outcome(value: Any, diagnostic_trust: Mapping[str, str], field: str) -> Any:
    status = diagnostic_trust.get(field)
    if status is not None and status.startswith("untrusted"):
        if status == "untrusted_terminal_non_finite_frame":
            return f"unavailable:untrusted_{field}_terminal_output_frame_entirely_non_finite"
        return f"unavailable:untrusted_{field}_field_entirely_non_finite"
    return value


def _field_trust_label(status: str | None) -> str:
    if status is not None and status.startswith("untrusted"):
        return "untrusted"
    if status == "caveated_non_finite_values_detected":
        return "caveated"
    if status == "unavailable_field_missing":
        return "unavailable"
    if status == "unavailable_until_result_ingested":
        return "unavailable"
    if status == "not_assessed":
        return "not assessed"
    return "trusted"


def _trusted_metric_label(label: str, value: Any, trust_status: str | None) -> str:
    trust_label = _field_trust_label(trust_status)
    if trust_label == "untrusted":
        return f"{label} unavailable (untrusted)"
    if trust_label == "unavailable":
        return f"{label} unavailable"
    suffix = f" ({trust_label})" if trust_label in {"caveated", "not assessed"} else ""
    return f"{label} {_fmt(value)}{suffix}"


def _trusted_bool_label(label: str, value: Any, trust_status: str | None) -> str:
    trust_label = _field_trust_label(trust_status)
    if trust_label == "untrusted":
        return f"{label} unavailable (untrusted)"
    if trust_label == "unavailable":
        return f"{label} unavailable"
    suffix = f" ({trust_label})" if trust_label in {"caveated", "not assessed"} else ""
    return f"{label} {_bool_or_fmt(value)}{suffix}"


def _diagnostic_trust_summary(trust: Mapping[str, Any]) -> str:
    fields = ("qc", "w", "qr", "surface_rain", "dbz")
    return ", ".join(f"{field} {_field_trust_label(str(trust.get(field)))}" for field in fields)


def _frame_quality_report_label(frame_quality: Any) -> str:
    if not isinstance(frame_quality, Mapping):
        return "not assessed"
    indices = frame_quality.get("affected_frame_indices")
    times = frame_quality.get("affected_frame_times_seconds")
    if not isinstance(indices, list) or not indices:
        total = frame_quality.get("total_frame_count")
        finite = frame_quality.get("finite_frame_count")
        if isinstance(total, int) and isinstance(finite, int):
            return f"all {finite}/{total} frames finite"
        return "no affected frames"
    time_labels = (
        [_time_seconds_report_label(time_seconds) for time_seconds in times]
        if isinstance(times, list)
        else []
    )
    terminal = (
        "terminal affected" if frame_quality.get("terminal_frame_affected") else "terminal ok"
    )
    initial = "initial affected" if frame_quality.get("initial_frame_affected") else "initial ok"
    entirely = frame_quality.get("entirely_non_finite_frame_count")
    return (
        f"affected frames {indices}"
        + (f" at {', '.join(time_labels)}" if time_labels else "")
        + f"; {initial}; {terminal}; entirely non-finite frames {entirely}"
    )


def _time_seconds_report_label(value: Any) -> str:
    if isinstance(value, int):
        return f"{value} s"
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value)} s"
        return f"{value:.3f} s"
    return "time unavailable"


def _stale_lhfx_missing_message(message: str, available_fields: set[str]) -> bool:
    if not _field_available("qfx", available_fields):
        return False
    lower = message.lower()
    return "lhfx" in lower and "missing" in lower and "required output" in lower


def _first_defined(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _time_of_max_time_value(values: Sequence[Any]) -> float | None:
    best_time: float | None = None
    best_value: float | None = None
    for point in values:
        value = getattr(point, "value", None)
        time_seconds = getattr(point, "time_seconds", None)
        if not isinstance(value, int | float):
            continue
        if best_value is None or float(value) > best_value:
            best_value = float(value)
            best_time = float(time_seconds) if isinstance(time_seconds, int | float) else None
    return best_time


def _time_value_at_time(values: Sequence[Any], target_time: float | None) -> float | None:
    if target_time is None:
        return None
    for point in values:
        time_seconds = getattr(point, "time_seconds", None)
        value = getattr(point, "value", None)
        if (
            isinstance(time_seconds, int | float)
            and abs(float(time_seconds) - target_time) < 1e-6
            and isinstance(value, int | float)
        ):
            return float(value)
    return None


def _cloud_depth_or_classification(
    result: ResultMetadata | None,
    diagnostic_trust: Mapping[str, str],
) -> str:
    if str(diagnostic_trust.get("qc", "")).startswith("untrusted"):
        return "unavailable:untrusted_qc_field"
    if result is None or result.diagnostics is None:
        return "unavailable:not_ingested"
    cloud = result.diagnostics.cloud
    if not cloud.available:
        return "unavailable:missing_qc_field"
    if not cloud.formed:
        return "no_cloud_detected"
    top = cloud.cloud_top_m
    if top is None:
        return "cloud_detected_depth_unavailable"
    if top >= 8000.0:
        return f"deep_cloud_top_{top:.0f}_m"
    return f"shallow_or_midlevel_cloud_top_{top:.0f}_m"


def _summary_caveats(
    run: CampaignRunPlan,
    state_run: CampaignStateRun | None,
    result: ResultMetadata | None,
) -> list[str]:
    caveats = [
        "surface_forcing_is_constant_uniform_proxy",
    ]
    if run.optional:
        caveats.append("optional_campaign_run")
    if state_run is not None and state_run.error:
        caveats.append("campaign_run_has_error")
    if result is None:
        caveats.append("result_not_ingested")
    else:
        caveats.extend(result.run_caveats)
        caveats.extend(result.interesting_time_caveats)
        if result.diagnostics is not None:
            caveats.extend(result.diagnostics.caveats)
            if not (
                result.diagnostics.low_level_response.qv.available
                and result.diagnostics.low_level_response.theta_or_temperature.available
            ):
                caveats.append("low_level_response_unavailable")
    return _dedupe(caveats)


def _render_markdown_report(plan: CampaignPlan, summary: Mapping[str, Any]) -> str:
    lines = [
        f"# Surface-Forced Campaign Report: {plan.campaign_id}",
        "",
        f"Campaign ID: `{plan.campaign_id}`",
        f"Protocol: `{plan.protocol or 'not specified'}`",
        (f"Matrix file: `{Path(str(summary['matrix_path'])).name}` (runtime-local path omitted)"),
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Objective",
        "",
        plan.objective or "No objective supplied in the campaign matrix.",
        "",
        "## Matrix Summary",
        "",
        f"- Runs planned: {summary['run_count']}",
        f"- Status counts: `{json.dumps(summary['status_counts'], sort_keys=True)}`",
        f"- Phase gate state: `{summary['phase_gate_state']}`",
        (
            f"- Surface flux response: "
            f"`{summary.get('surface_flux_response', {}).get('state', 'unavailable')}`"
        ),
        "",
        "## Operator Overrides",
        "",
    ]
    if summary.get("gate_overrides"):
        for override in summary["gate_overrides"]:
            lines.append(
                f"- {override['matrix_id']}: `{override['reason']}` "
                f"(gate `{override['gate_state_at_override']}`)"
            )
    else:
        lines.append("No operator phase-gate overrides were recorded.")
    lines.extend(
        [
            "",
            "## Run Table",
            "",
            "| Matrix ID | Status | Station/time | Forcing | Grid/domain | Key result |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for run in summary["runs"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(run["matrix_id"]),
                    str(run["status"]),
                    _station_time_label(run),
                    _forcing_label(run),
                    _grid_label(run),
                    _key_result_label(run),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            (
                "Cloud-top values currently use the total hydrometeor envelope and may "
                "exceed the coherent liquid/ice cloud-object top. See #330."
            ),
        ]
    )
    lines.extend(
        [
            "",
            "## Per-Run Evidence",
            "",
        ]
    )
    for run in summary["runs"]:
        required_fields = ", ".join(run["required_output_fields"]) or "unavailable"
        missing_fields = ", ".join(run["missing_output_fields"]) or "none"
        trust = run.get("diagnostic_trust")
        diagnostic_trust = trust if isinstance(trust, dict) else {}
        quality_warnings = ", ".join(run["diagnostic_quality_warnings"]) or "none"
        terminal_fields = ", ".join(run.get("terminal_output_contamination_fields") or []) or "none"
        runtime_warnings = ", ".join(run.get("runtime_floating_point_warnings") or []) or "none"
        cloud_updraft = ", ".join(
            [
                _trusted_metric_label(
                    "first cloud", run["first_cloud_time"], diagnostic_trust.get("qc")
                ),
                _trusted_metric_label(
                    "max cloud top", run["max_cloud_top_m"], diagnostic_trust.get("qc")
                ),
                _trusted_metric_label("max qc", run["max_qc"], diagnostic_trust.get("qc")),
                _trusted_metric_label("max w", run["max_w_m_s"], diagnostic_trust.get("w")),
            ]
        )
        precipitation = ", ".join(
            [
                _trusted_bool_label("qr", run["qr_present"], diagnostic_trust.get("qr")),
                _trusted_bool_label(
                    "surface rain",
                    run["surface_rain_present"],
                    diagnostic_trust.get("surface_rain"),
                ),
                _trusted_metric_label("max dBZ", run["max_dbz"], diagnostic_trust.get("dbz")),
            ]
        )
        lines.extend(
            [
                f"### {run['matrix_id']}",
                "",
                f"- Run ID: `{run['run_id']}`",
                f"- Result ID: `{run['result_id'] or 'not ingested'}`",
                (
                    f"- Status: package `{run['package_status']}`, "
                    f"run `{run['run_status']}`, ingest `{run['ingest_status']}`"
                ),
                (
                    f"- Provenance: Cloud Chamber "
                    f"`{run['cloud_chamber_commit'] or 'unavailable'}`, "
                    f"CM1 `{run['cm1_version']}`"
                ),
                f"- Source: `{run['selection_source_type']}` `{run['selection_source_reference']}`",
                f"- Candidate story: `{run['candidate_story'] or 'unavailable'}`",
                f"- Required/missing fields: `{required_fields}` / `{missing_fields}`",
                (
                    f"- Surface flux fields: hfx `{run['hfx_present']}`, "
                    f"moisture flux `{run['lhfx_present']}` "
                    f"via `{run.get('surface_moisture_flux_output_field') or 'missing'}`"
                ),
                (
                    f"- Surface flux stats: hfx `{run['hfx_min']}`/"
                    f"`{run['hfx_max']}`/`{run['hfx_mean']}`, "
                    f"qfx `{run['qfx_min']}`/`{run['qfx_max']}`/"
                    f"`{run['qfx_mean']}`; counts hfx "
                    f"`{run['hfx_finite_count']}`/`{run['hfx_non_finite_count']}`/"
                    f"`{run['hfx_total_count']}`, qfx "
                    f"`{run['qfx_finite_count']}`/`{run['qfx_non_finite_count']}`/"
                    f"`{run['qfx_total_count']}`"
                ),
                (
                    f"- Surface flux frame quality: hfx "
                    f"`{_frame_quality_report_label(run.get('hfx_frame_quality'))}`, "
                    f"qfx `{_frame_quality_report_label(run.get('qfx_frame_quality'))}`"
                ),
                (f"- Terminal field contamination: `{terminal_fields}`"),
                f"- Runtime floating-point warnings: `{runtime_warnings}`",
                f"- Cloud/updraft: {cloud_updraft}",
                f"- Precipitation/reflectivity: {precipitation}",
                f"- Diagnostic trust: `{_diagnostic_trust_summary(diagnostic_trust)}`",
                f"- Field-quality warnings: `{quality_warnings}`",
                (
                    f"- Low-level qv early response: "
                    f"`{run['low_level_qv_early_response_delta']}` "
                    f"`{run['low_level_qv_response_units'] or ''}` via "
                    f"`{run['low_level_qv_response_method']}` "
                    f"({run['low_level_qv_early_response_start_mean']} -> "
                    f"{run['low_level_qv_early_response_end_mean']}); "
                    f"quality `{run['low_level_qv_early_response_quality_state']}`; "
                    f"full-run delta `{run['low_level_qv_full_run_delta']}`"
                ),
                (
                    f"- Low-level theta/temperature early response: "
                    f"`{run['low_level_theta_or_temperature_early_response_delta']}` "
                    f"`{run['low_level_theta_or_temperature_response_units'] or ''}` via "
                    f"`{run['low_level_theta_or_temperature_response_method']}` "
                    f"({run['low_level_theta_or_temperature_early_response_start_mean']} -> "
                    f"{run['low_level_theta_or_temperature_early_response_end_mean']}); "
                    f"quality "
                    f"`{run['low_level_theta_or_temperature_early_response_quality_state']}`; "
                    f"full-run delta "
                    f"`{run['low_level_theta_or_temperature_full_run_delta']}`"
                ),
                f"- Caveats: `{', '.join(run['caveats']) or 'none'}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Forcing Response",
            "",
            _forcing_response_summary(summary),
            "",
            "## Surface Flux Response",
            "",
        ]
    )
    surface_flux_response = summary.get("surface_flux_response", {})
    response_evaluations = surface_flux_response.get("evaluations", [])
    missing_required_comparison_types = surface_flux_response.get(
        "missing_required_comparison_types",
        [],
    )
    if missing_required_comparison_types:
        lines.append(
            "- Missing required Phase 1 comparison types: "
            f"`{', '.join(missing_required_comparison_types)}`"
        )
    if response_evaluations:
        for evaluation in response_evaluations:
            lines.append(
                f"- `{evaluation['experiment_matrix_id']}` vs "
                f"`{evaluation['control_matrix_id']}`: `{evaluation['status']}`"
            )
            for expectation in evaluation.get("expectations", []):
                role = "required" if expectation.get("required") else "informational"
                lines.append(
                    f"  - {expectation['field']}: {role}; expected "
                    f"`{expectation['expected']}`, observed `{expectation['observed']}`; "
                    f"`{expectation['status']}`"
                )
            if evaluation.get("unavailable_evidence"):
                lines.append(
                    f"  - Unavailable evidence: `{', '.join(evaluation['unavailable_evidence'])}`"
                )
    else:
        lines.append("No Phase 1 surface-flux response comparisons are available.")
    lines.extend(
        [
            "",
            "## Low-Level Response",
            "",
        ]
    )
    low_level_response = summary.get("low_level_response", {})
    low_level_evaluations = low_level_response.get("evaluations", [])
    missing_low_level_comparison_types = low_level_response.get(
        "missing_required_comparison_types",
        [],
    )
    if missing_low_level_comparison_types:
        lines.append(
            "- Missing required Phase 1 comparison types: "
            f"`{', '.join(missing_low_level_comparison_types)}`"
        )
    if low_level_evaluations:
        for evaluation in low_level_evaluations:
            lines.append(
                f"- `{evaluation['experiment_matrix_id']}` vs "
                f"`{evaluation['control_matrix_id']}`: `{evaluation['status']}`"
            )
            for expectation in evaluation.get("expectations", []):
                role = "required" if expectation.get("required") else "informational"
                lines.append(
                    f"  - {expectation['field']}: {role}; expected "
                    f"`{expectation['expected']}`, observed `{expectation['observed']}`; "
                    f"`{expectation['status']}`; quality "
                    f"`{expectation.get('quality_state', 'unknown')}`"
                )
    else:
        lines.append("No Phase 1 low-level response comparisons are available.")
    lines.extend(
        [
            "",
            "## Matched Comparisons",
            "",
        ]
    )
    if summary["comparisons"]:
        for comparison in summary["comparisons"]:
            lines.extend(
                [
                    (
                        f"### {comparison['experiment_matrix_id']} vs "
                        f"{comparison['control_matrix_id']}"
                    ),
                    "",
                    f"- Type: `{comparison['comparison_type']}`",
                    f"- Status: `{comparison['status']}`",
                    f"- Varied fields: `{', '.join(comparison['fields_that_varied']) or 'none'}`",
                    (
                        f"- Equality failures: "
                        f"`{json.dumps(comparison['equality_gate_failures'], sort_keys=True)}`"
                    ),
                    (
                        f"- Unavailable evidence: "
                        f"`{', '.join(comparison['unavailable_evidence']) or 'none'}`"
                    ),
                    f"- Interpretation: {comparison['interpretation']}",
                    "",
                ]
            )
    else:
        lines.append("No comparison instances are defined in this matrix.")
    lines.extend(
        [
            "## Deepening And Class Differences",
            "",
            _deepening_summary(summary),
            "",
            "## Unavailable Or Missing Diagnostics",
            "",
        ]
    )
    for item in summary["unavailable_diagnostics"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Preliminary Diagnosis Categories",
            "",
        ]
    )
    for item in summary["preliminary_diagnosis_categories"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Recommended Follow-Up Issues",
            "",
        ]
    )
    for item in summary["recommended_follow_ups"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def _status_counts(summaries: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for summary in summaries:
        status = str(summary.get("status") or "planned")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _gate_overrides(summaries: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    overrides: list[dict[str, Any]] = []
    for summary in summaries:
        payload = summary.get("gate_override")
        if not isinstance(payload, dict):
            continue
        overrides.append(
            {
                "matrix_id": summary.get("matrix_id"),
                "reason": payload.get("reason") or "operator_override_without_reason",
                "gate_state_at_override": payload.get("gate_state_at_override"),
                "recorded_at": payload.get("recorded_at"),
            }
        )
    return overrides


def _evaluate_comparisons(
    plan: CampaignPlan,
    summaries: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_matrix_id = {str(summary["matrix_id"]): summary for summary in summaries}
    results: list[dict[str, Any]] = []
    for run in plan.runs:
        if not run.comparison_type or not run.comparison_control_matrix_id:
            continue
        definition = plan.comparison_types.get(run.comparison_type, {})
        control = by_matrix_id.get(run.comparison_control_matrix_id)
        experiment = by_matrix_id.get(run.matrix_id)
        if control is None or experiment is None:
            results.append(
                {
                    "comparison_type": run.comparison_type,
                    "control_matrix_id": run.comparison_control_matrix_id,
                    "experiment_matrix_id": run.matrix_id,
                    "status": "inconclusive_missing_evidence",
                    "interpretation": "Control or experiment summary is unavailable.",
                    "equality_gate_failures": [],
                    "unavailable_evidence": ["missing_control_or_experiment_summary"],
                    "supported_differences": [],
                }
            )
            continue
        equality_failures = _comparison_equality_failures(control, experiment, definition)
        unavailable = _comparison_unavailable_evidence(control, experiment, definition)
        supported = _comparison_supported_differences(control, experiment, definition)
        if equality_failures:
            status = "inconclusive_noncomparable_runs"
            interpretation = (
                "Runs are not comparable because required-equal fields differ or are missing."
            )
        elif unavailable:
            status = "inconclusive_missing_evidence"
            interpretation = (
                "Runs are structurally comparable, but required output fields or diagnostics "
                "are unavailable."
            )
        else:
            status = "comparable"
            interpretation = (
                "Required comparison gates passed; inspect supported differences without "
                "treating them as predicted-vs-actual verdicts."
            )
        results.append(
            {
                "comparison_type": run.comparison_type,
                "control_matrix_id": run.comparison_control_matrix_id,
                "experiment_matrix_id": run.matrix_id,
                "status": status,
                "fields_that_varied": list(definition.get("varied_fields", [])),
                "equality_gate_failures": equality_failures,
                "unavailable_evidence": unavailable,
                "supported_differences": supported,
                "interpretation": interpretation,
            }
        )
    return results


def _comparison_equality_failures(
    control: Mapping[str, Any],
    experiment: Mapping[str, Any],
    definition: Mapping[str, Any],
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for field in _string_list(definition.get("required_equal_fields")):
        left = _comparison_field_value(control, field)
        right = _comparison_field_value(experiment, field)
        if left != right:
            failures.append(
                {
                    "field": field,
                    "control": left,
                    "experiment": right,
                }
            )
    return failures


def _comparison_unavailable_evidence(
    control: Mapping[str, Any],
    experiment: Mapping[str, Any],
    definition: Mapping[str, Any],
) -> list[str]:
    unavailable: list[str] = []
    for summary, role in ((control, "control"), (experiment, "experiment")):
        if summary.get("status") != "ingested":
            unavailable.append(f"{role}:result_not_ingested")
        fields = set(_string_list(summary.get("available_output_fields")))
        for field in _string_list(definition.get("required_available_fields")):
            if not _field_available(field, fields):
                report_field = _normalize_campaign_output_field_name(field)
                unavailable.append(f"{role}:missing_required_field:{report_field}")
        support = summary.get("diagnostic_support")
        diagnostic_support = support if isinstance(support, dict) else {}
        for diagnostic in _string_list(definition.get("required_diagnostic_support")):
            if diagnostic_support.get(diagnostic) != "available":
                unavailable.append(f"{role}:diagnostic_unavailable:{diagnostic}")
    return _dedupe(unavailable)


def _comparison_supported_differences(
    control: Mapping[str, Any],
    experiment: Mapping[str, Any],
    definition: Mapping[str, Any],
) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    for field in _string_list(definition.get("varied_fields")):
        left = _comparison_field_value(control, field)
        right = _comparison_field_value(experiment, field)
        if left != right:
            differences.append({"field": field, "control": left, "experiment": right})
    for field in (
        "max_cloud_top_m",
        "max_qc",
        "max_w_m_s",
        "qr_present",
        "surface_rain_present",
        "max_dbz",
        "low_level_qv_response",
        "low_level_qv_early_response_delta",
        "low_level_qv_full_run_delta",
        "low_level_theta_or_temperature_response",
        "low_level_theta_or_temperature_early_response_delta",
        "low_level_theta_or_temperature_full_run_delta",
    ):
        left = control.get(field)
        right = experiment.get(field)
        if (
            left is not None
            and not _is_unavailable(left)
            or right is not None
            and not _is_unavailable(right)
        ):
            differences.append({"field": field, "control": left, "experiment": right})
    return differences


def _comparison_field_value(summary: Mapping[str, Any], field: str) -> Any:
    if field in MATRIX_CONTEXT_FIELDS:
        if field == "runtime_seconds":
            return summary.get("duration_seconds")
        return summary.get(field)
    return summary.get(field)


SURFACE_FLUX_RESPONSE_VERIFIED = "surface_flux_response_verified"
SURFACE_FLUX_RESPONSE_NOT_VERIFIED = "surface_flux_response_not_verified"
SURFACE_FLUX_RESPONSE_MISSING = "surface_flux_response_inconclusive_missing_evidence"
SURFACE_FLUX_RESPONSE_NONCOMPARABLE = "surface_flux_response_inconclusive_noncomparable"
LOW_LEVEL_RESPONSE_VERIFIED = "low_level_response_verified"
LOW_LEVEL_RESPONSE_NOT_VERIFIED = "low_level_response_not_verified"
LOW_LEVEL_RESPONSE_MISSING = "low_level_response_inconclusive_missing_evidence"
LOW_LEVEL_RESPONSE_NONCOMPARABLE = "low_level_response_inconclusive_noncomparable"
LOW_LEVEL_RESPONSE_MIN_EARLY_FINITE_FRACTION = 0.95


def _surface_flux_response_evaluation(
    plan: CampaignPlan,
    summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    by_matrix_id = {str(summary["matrix_id"]): summary for summary in summaries}
    required_comparison_types = list(
        plan.phase1_required_comparison_types or DEFAULT_PHASE1_REQUIRED_COMPARISON_TYPES
    )
    evaluations: list[dict[str, Any]] = []
    for run in plan.runs:
        if not _is_phase_one_run(run):
            continue
        if not run.comparison_type or not run.comparison_control_matrix_id:
            continue
        definition = plan.comparison_types.get(run.comparison_type, {})
        control = by_matrix_id.get(run.comparison_control_matrix_id)
        experiment = by_matrix_id.get(run.matrix_id)
        evaluations.append(
            _surface_flux_response_for_pair(
                comparison_type=run.comparison_type,
                control_matrix_id=run.comparison_control_matrix_id,
                experiment_matrix_id=run.matrix_id,
                definition=definition,
                control=control,
                experiment=experiment,
            )
        )

    evaluated_comparison_types = {str(evaluation["comparison_type"]) for evaluation in evaluations}
    missing_required_comparison_types = [
        comparison_type
        for comparison_type in required_comparison_types
        if comparison_type not in evaluated_comparison_types
    ]
    unavailable_evidence = [
        f"missing_phase1_required_comparison_type:{comparison_type}"
        for comparison_type in missing_required_comparison_types
    ]
    unavailable_evidence.extend(
        evidence
        for evaluation in evaluations
        for evidence in evaluation.get("unavailable_evidence", [])
        if isinstance(evidence, str)
    )
    unavailable_evidence = _dedupe(unavailable_evidence)
    if missing_required_comparison_types:
        state = SURFACE_FLUX_RESPONSE_MISSING
    elif not evaluations:
        state = SURFACE_FLUX_RESPONSE_MISSING
    elif any(
        evaluation["status"] == SURFACE_FLUX_RESPONSE_NONCOMPARABLE for evaluation in evaluations
    ):
        state = SURFACE_FLUX_RESPONSE_NONCOMPARABLE
    elif any(evaluation["status"] == SURFACE_FLUX_RESPONSE_MISSING for evaluation in evaluations):
        state = SURFACE_FLUX_RESPONSE_MISSING
    elif any(
        evaluation["status"] == SURFACE_FLUX_RESPONSE_NOT_VERIFIED for evaluation in evaluations
    ):
        state = SURFACE_FLUX_RESPONSE_NOT_VERIFIED
    else:
        state = SURFACE_FLUX_RESPONSE_VERIFIED
    return {
        "state": state,
        "required_comparison_types": required_comparison_types,
        "missing_required_comparison_types": missing_required_comparison_types,
        "unavailable_evidence": unavailable_evidence,
        "evaluations": evaluations,
    }


def _low_level_response_evaluation(
    plan: CampaignPlan,
    summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    by_matrix_id = {str(summary["matrix_id"]): summary for summary in summaries}
    required_comparison_types = list(
        plan.phase1_required_comparison_types or DEFAULT_PHASE1_REQUIRED_COMPARISON_TYPES
    )
    evaluations: list[dict[str, Any]] = []
    for run in plan.runs:
        if not _is_phase_one_run(run):
            continue
        if not run.comparison_type or not run.comparison_control_matrix_id:
            continue
        definition = plan.comparison_types.get(run.comparison_type, {})
        control = by_matrix_id.get(run.comparison_control_matrix_id)
        experiment = by_matrix_id.get(run.matrix_id)
        evaluations.append(
            _low_level_response_for_pair(
                comparison_type=run.comparison_type,
                control_matrix_id=run.comparison_control_matrix_id,
                experiment_matrix_id=run.matrix_id,
                definition=definition,
                control=control,
                experiment=experiment,
            )
        )

    evaluated_comparison_types = {str(evaluation["comparison_type"]) for evaluation in evaluations}
    missing_required_comparison_types = [
        comparison_type
        for comparison_type in required_comparison_types
        if comparison_type not in evaluated_comparison_types
    ]
    unavailable_evidence = [
        f"missing_phase1_required_comparison_type:{comparison_type}"
        for comparison_type in missing_required_comparison_types
    ]
    if missing_required_comparison_types:
        state = LOW_LEVEL_RESPONSE_MISSING
    elif not evaluations:
        state = LOW_LEVEL_RESPONSE_MISSING
    elif any(
        evaluation["status"] == LOW_LEVEL_RESPONSE_NONCOMPARABLE for evaluation in evaluations
    ):
        state = LOW_LEVEL_RESPONSE_NONCOMPARABLE
    elif any(evaluation["status"] == LOW_LEVEL_RESPONSE_MISSING for evaluation in evaluations):
        state = LOW_LEVEL_RESPONSE_MISSING
    elif any(evaluation["status"] == LOW_LEVEL_RESPONSE_NOT_VERIFIED for evaluation in evaluations):
        state = LOW_LEVEL_RESPONSE_NOT_VERIFIED
    else:
        state = LOW_LEVEL_RESPONSE_VERIFIED
    return {
        "state": state,
        "required_comparison_types": required_comparison_types,
        "missing_required_comparison_types": missing_required_comparison_types,
        "unavailable_evidence": unavailable_evidence,
        "evaluations": evaluations,
    }


def _low_level_response_for_pair(
    *,
    comparison_type: str,
    control_matrix_id: str,
    experiment_matrix_id: str,
    definition: Mapping[str, Any],
    control: Mapping[str, Any] | None,
    experiment: Mapping[str, Any] | None,
) -> dict[str, Any]:
    base = {
        "comparison_type": comparison_type,
        "control_matrix_id": control_matrix_id,
        "experiment_matrix_id": experiment_matrix_id,
        "expectations": [],
        "equality_gate_failures": [],
        "unavailable_evidence": [],
    }
    if control is None or experiment is None:
        return {
            **base,
            "status": LOW_LEVEL_RESPONSE_MISSING,
            "unavailable_evidence": ["missing_control_or_experiment_summary"],
        }

    equality_failures = _comparison_equality_failures(control, experiment, definition)
    if equality_failures:
        return {
            **base,
            "status": LOW_LEVEL_RESPONSE_NONCOMPARABLE,
            "equality_gate_failures": equality_failures,
        }

    unavailable = _low_level_pair_unavailable_evidence(control, experiment)
    if unavailable:
        status = (
            LOW_LEVEL_RESPONSE_NONCOMPARABLE
            if any("noncomparable_units" in item for item in unavailable)
            else LOW_LEVEL_RESPONSE_MISSING
        )
        return {
            **base,
            "status": status,
            "unavailable_evidence": unavailable,
        }

    expectations = [
        _low_level_response_expectation(
            field="low_level_theta_or_temperature_early_response_delta",
            selected_control_field="surface_heat_flux_k_m_s",
            control=control,
            experiment=experiment,
        ),
        _low_level_response_expectation(
            field="low_level_qv_early_response_delta",
            selected_control_field="surface_moisture_flux_g_g_m_s",
            control=control,
            experiment=experiment,
        ),
    ]
    required_expectations = [expectation for expectation in expectations if expectation["required"]]
    status = (
        LOW_LEVEL_RESPONSE_VERIFIED
        if all(expectation["status"] == "verified" for expectation in required_expectations)
        else LOW_LEVEL_RESPONSE_NOT_VERIFIED
    )
    if not required_expectations:
        status = LOW_LEVEL_RESPONSE_NONCOMPARABLE
    return {
        **base,
        "status": status,
        "expectations": expectations,
    }


def _low_level_pair_unavailable_evidence(
    control: Mapping[str, Any],
    experiment: Mapping[str, Any],
) -> list[str]:
    unavailable: list[str] = []
    for summary, role in ((control, "control"), (experiment, "experiment")):
        if summary.get("status") != "ingested":
            unavailable.append(f"{role}:result_not_ingested")
        support = summary.get("diagnostic_support")
        diagnostic_support = support if isinstance(support, dict) else {}
        if diagnostic_support.get("low_level_response") != "available":
            unavailable.append(f"{role}:diagnostic_unavailable:low_level_response")
        for field in (
            "low_level_qv_early_response_delta",
            "low_level_theta_or_temperature_early_response_delta",
        ):
            value = summary.get(field)
            if not isinstance(value, int | float) or _is_unavailable(value):
                unavailable.append(f"{role}:{field}_unavailable:{value}")
            units = summary.get(f"{field}_units")
            if not isinstance(units, str) or not units:
                unavailable.append(f"{role}:{field}_units_unavailable")
            finite_fraction = _float_or_none(
                summary.get(field.replace("_delta", "_min_finite_fraction"))
            )
            if finite_fraction is None:
                unavailable.append(f"{role}:{field}_finite_fraction_unavailable")
            elif finite_fraction < LOW_LEVEL_RESPONSE_MIN_EARLY_FINITE_FRACTION:
                unavailable.append(
                    f"{role}:{field}_finite_fraction_below_threshold:"
                    f"{finite_fraction:.3f}<"
                    f"{LOW_LEVEL_RESPONSE_MIN_EARLY_FINITE_FRACTION:.3f}"
                )
    for field in (
        "low_level_qv_early_response_delta",
        "low_level_theta_or_temperature_early_response_delta",
    ):
        control_units = control.get(f"{field}_units")
        experiment_units = experiment.get(f"{field}_units")
        if control_units is None or experiment_units is None:
            continue
        if control_units != experiment_units:
            unavailable.append(f"{field}:noncomparable_units:{control_units}:vs:{experiment_units}")
    noncomparable = [item for item in unavailable if "noncomparable_units" in item]
    if noncomparable:
        return noncomparable
    return _dedupe(unavailable)


def _low_level_response_expectation(
    *,
    field: str,
    selected_control_field: str,
    control: Mapping[str, Any],
    experiment: Mapping[str, Any],
) -> dict[str, Any]:
    control_selected = _float_or_none(control.get(selected_control_field))
    experiment_selected = _float_or_none(experiment.get(selected_control_field))
    control_delta = _float_or_none(control.get(field))
    experiment_delta = _float_or_none(experiment.get(field))
    control_finite_fraction = _float_or_none(
        control.get(field.replace("_delta", "_min_finite_fraction"))
    )
    experiment_finite_fraction = _float_or_none(
        experiment.get(field.replace("_delta", "_min_finite_fraction"))
    )
    control_quality_state = control.get(field.replace("_delta", "_quality_state"))
    experiment_quality_state = experiment.get(field.replace("_delta", "_quality_state"))
    expected = _expected_direction(control_selected, experiment_selected)
    observed = _expected_direction(control_delta, experiment_delta)
    required = expected in {"increase", "decrease"}
    if required:
        status = "verified" if expected == observed else "not_verified"
    elif expected == "comparable":
        status = "informational"
    else:
        status = "not_evaluated"
    return {
        "field": field,
        "selected_control_field": selected_control_field,
        "expected": expected,
        "observed": observed,
        "required": required,
        "status": status,
        "control_selected": control_selected,
        "experiment_selected": experiment_selected,
        "control_delta": control_delta,
        "experiment_delta": experiment_delta,
        "units": control.get(f"{field}_units"),
        "control_finite_fraction": control_finite_fraction,
        "experiment_finite_fraction": experiment_finite_fraction,
        "control_quality_state": control_quality_state,
        "experiment_quality_state": experiment_quality_state,
        "quality_state": (
            "caveated"
            if "caveated" in {control_quality_state, experiment_quality_state}
            else "trusted"
        ),
    }


def _surface_flux_response_for_pair(
    *,
    comparison_type: str,
    control_matrix_id: str,
    experiment_matrix_id: str,
    definition: Mapping[str, Any],
    control: Mapping[str, Any] | None,
    experiment: Mapping[str, Any] | None,
) -> dict[str, Any]:
    base = {
        "comparison_type": comparison_type,
        "control_matrix_id": control_matrix_id,
        "experiment_matrix_id": experiment_matrix_id,
        "expectations": [],
        "equality_gate_failures": [],
        "unavailable_evidence": [],
    }
    if control is None or experiment is None:
        return {
            **base,
            "status": SURFACE_FLUX_RESPONSE_MISSING,
            "unavailable_evidence": ["missing_control_or_experiment_summary"],
        }

    equality_failures = _comparison_equality_failures(control, experiment, definition)
    if equality_failures:
        return {
            **base,
            "status": SURFACE_FLUX_RESPONSE_NONCOMPARABLE,
            "equality_gate_failures": equality_failures,
        }

    unavailable = _surface_flux_pair_unavailable_evidence(control, experiment)
    if unavailable:
        status = (
            SURFACE_FLUX_RESPONSE_NONCOMPARABLE
            if any("noncomparable_units" in item for item in unavailable)
            else SURFACE_FLUX_RESPONSE_MISSING
        )
        return {
            **base,
            "status": status,
            "unavailable_evidence": unavailable,
        }

    expectations = [
        _surface_flux_field_expectation(
            field="hfx",
            control=control,
            experiment=experiment,
            selected_control_field="surface_heat_flux_k_m_s",
        ),
        _surface_flux_field_expectation(
            field="qfx",
            control=control,
            experiment=experiment,
            selected_control_field="surface_moisture_flux_g_g_m_s",
        ),
    ]
    required_expectations = [expectation for expectation in expectations if expectation["required"]]
    status = (
        SURFACE_FLUX_RESPONSE_VERIFIED
        if all(expectation["status"] == "verified" for expectation in required_expectations)
        else SURFACE_FLUX_RESPONSE_NOT_VERIFIED
    )
    if not required_expectations:
        status = SURFACE_FLUX_RESPONSE_NONCOMPARABLE
    return {
        **base,
        "status": status,
        "expectations": expectations,
    }


def _surface_flux_pair_unavailable_evidence(
    control: Mapping[str, Any],
    experiment: Mapping[str, Any],
) -> list[str]:
    unavailable: list[str] = []
    for summary, role in ((control, "control"), (experiment, "experiment")):
        if summary.get("status") != "ingested":
            unavailable.append(f"{role}:result_not_ingested")
        for field in ("hfx", "qfx"):
            unavailable.extend(_surface_flux_stat_unavailable_reasons(summary, role, field))
    for field in ("hfx", "qfx"):
        control_units = control.get(f"{field}_units")
        experiment_units = experiment.get(f"{field}_units")
        if control_units is None or experiment_units is None:
            continue
        if control_units != experiment_units:
            unavailable.append(f"{field}:noncomparable_units:{control_units}:vs:{experiment_units}")
    noncomparable = [item for item in unavailable if "noncomparable_units" in item]
    if noncomparable:
        return noncomparable
    return _dedupe(unavailable)


def _surface_flux_stat_unavailable_reasons(
    summary: Mapping[str, Any],
    role: str,
    field: str,
) -> list[str]:
    value = summary.get(f"{field}_mean")
    finite_count = _int_or_none(summary.get(f"{field}_finite_count"))
    non_finite_count = _int_or_none(summary.get(f"{field}_non_finite_count"))
    total_count = _int_or_none(summary.get(f"{field}_total_count"))
    units = summary.get(f"{field}_units")
    frame_quality = _frame_quality_mapping(summary.get(f"{field}_frame_quality"))
    reasons: list[str] = []
    if not isinstance(value, int | float) or _is_unavailable(value):
        reasons.append(f"{role}:{field}_mean_unavailable")
    if finite_count is None or finite_count <= 0:
        reasons.append(f"{role}:{field}_finite_count_unavailable")
    if total_count is None or total_count <= 0:
        reasons.append(f"{role}:{field}_total_count_unavailable")
    if non_finite_count is None:
        reasons.append(f"{role}:{field}_non_finite_count_unavailable")
    elif non_finite_count > 0:
        if frame_quality is not None and not frame_quality.get("chronology_available", True):
            reasons.append(f"{role}:{field}_frame_chronology_unavailable")
        elif _frame_quality_has_terminal_entirely_non_finite(frame_quality):
            reasons.append(f"{role}:{field}_terminal_output_frame_entirely_non_finite")
        elif _frame_quality_has_intermediate_entirely_non_finite(frame_quality):
            reasons.append(f"{role}:{field}_intermediate_output_frame_entirely_non_finite")
        elif _frame_quality_is_initial_only_entirely_non_finite(frame_quality):
            reasons.append(f"{role}:{field}_initial_output_frame_entirely_non_finite")
        else:
            reasons.append(f"{role}:{field}_stats_not_trusted_non_finite")
    if not isinstance(units, str) or not units:
        reasons.append(f"{role}:{field}_units_unavailable")
    return reasons


def _frame_quality_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _frame_quality_has_terminal_entirely_non_finite(
    frame_quality: Mapping[str, Any] | None,
) -> bool:
    if frame_quality is None:
        return False
    return any(
        isinstance(frame, Mapping)
        and frame.get("position") in {"terminal", "single"}
        and frame.get("entirely_non_finite") is True
        for frame in _frame_quality_affected_frames(frame_quality)
    )


def _frame_quality_has_intermediate_entirely_non_finite(
    frame_quality: Mapping[str, Any] | None,
) -> bool:
    if frame_quality is None:
        return False
    return any(
        isinstance(frame, Mapping)
        and frame.get("position") == "intermediate"
        and frame.get("entirely_non_finite") is True
        for frame in _frame_quality_affected_frames(frame_quality)
    )


def _frame_quality_is_initial_only_entirely_non_finite(
    frame_quality: Mapping[str, Any] | None,
) -> bool:
    if frame_quality is None:
        return False
    affected_frames = [
        frame
        for frame in _frame_quality_affected_frames(frame_quality)
        if isinstance(frame, Mapping)
    ]
    return bool(affected_frames) and all(
        frame.get("position") == "initial" and frame.get("entirely_non_finite") is True
        for frame in affected_frames
    )


def _frame_quality_affected_frames(frame_quality: Mapping[str, Any]) -> Sequence[Any]:
    frames = frame_quality.get("affected_frames")
    return frames if isinstance(frames, list) else []


def _surface_flux_field_expectation(
    *,
    field: str,
    control: Mapping[str, Any],
    experiment: Mapping[str, Any],
    selected_control_field: str,
) -> dict[str, Any]:
    control_selected = _float_or_none(control.get(selected_control_field))
    experiment_selected = _float_or_none(experiment.get(selected_control_field))
    control_mean = _float_or_none(control.get(f"{field}_mean"))
    experiment_mean = _float_or_none(experiment.get(f"{field}_mean"))
    expected = _expected_direction(control_selected, experiment_selected)
    observed = _expected_direction(control_mean, experiment_mean)
    required = expected in {"increase", "decrease"}
    if required:
        status = "verified" if expected == observed else "not_verified"
    elif expected == "comparable":
        status = "informational"
    else:
        status = "not_evaluated"
    return {
        "field": field,
        "selected_control_field": selected_control_field,
        "expected": expected,
        "observed": observed,
        "required": required,
        "status": status,
        "control_selected": control_selected,
        "experiment_selected": experiment_selected,
        "control_mean": control_mean,
        "experiment_mean": experiment_mean,
        "units": control.get(f"{field}_units"),
    }


def _expected_direction(left: float | None, right: float | None) -> str:
    if left is None or right is None:
        return "unknown"
    tolerance = _comparison_numeric_tolerance(left, right)
    if right > left + tolerance:
        return "increase"
    if right < left - tolerance:
        return "decrease"
    return "comparable"


def _comparison_numeric_tolerance(left: float, right: float) -> float:
    return max(abs(left), abs(right), 1.0) * 1e-9


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _field_available(field: str, available_fields: set[str]) -> bool:
    if field in {"qfx", "lhfx"}:
        return bool({"qfx", "lhfx"} & available_fields)
    if field == "th_or_temperature":
        return bool({"th", "theta", "temperature", "t"} & available_fields)
    return field in available_fields


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _is_unavailable(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("unavailable")


def _phase_gate_state(
    summaries: Sequence[Mapping[str, Any]],
    surface_flux_response: Mapping[str, Any],
    low_level_response: Mapping[str, Any],
) -> str:
    phase1 = [
        summary for summary in summaries if summary.get("phase") == "forcing_path_smoke_check"
    ]
    if not phase1:
        return "inconclusive_missing_evidence"
    if not all(summary.get("status") == "ingested" for summary in phase1):
        return "inconclusive_missing_evidence"
    if not all(summary.get("hfx_present") and summary.get("qfx_present") for summary in phase1):
        return "forcing_wiring_not_verified"
    response_state = surface_flux_response.get("state")
    if response_state != SURFACE_FLUX_RESPONSE_VERIFIED:
        return str(response_state or SURFACE_FLUX_RESPONSE_MISSING)
    low_level_state = low_level_response.get("state")
    if low_level_state != LOW_LEVEL_RESPONSE_VERIFIED:
        return "forcing_wiring_verified_but_response_not_verified"
    return "forcing_path_verified_for_campaign"


def _unavailable_diagnostics(summaries: Sequence[Mapping[str, Any]]) -> list[str]:
    unavailable: set[str] = set()
    for summary in summaries:
        for field in summary.get("missing_output_fields", []):
            if isinstance(field, str) and field.startswith("unavailable:"):
                continue
            unavailable.add(f"missing_output_field:{field}")
        if _is_unavailable(summary.get("low_level_qv_response")):
            unavailable.add("low_level_qv_response")
        if _is_unavailable(summary.get("low_level_theta_or_temperature_response")):
            unavailable.add("low_level_theta_or_temperature_response")
    return sorted(unavailable)


def _preliminary_diagnosis_categories(summaries: Sequence[Mapping[str, Any]]) -> list[str]:
    categories: set[str] = set()
    if not summaries:
        return ["no_runs_available"]
    if any(summary.get("status") in {"package_failed", "blocked"} for summary in summaries):
        categories.add("implementation_or_validation_blocked_some_runs")
    if any(summary.get("status") == "ingested" for summary in summaries):
        categories.add("ingested_results_available_for_review")
    if any(summary.get("hfx_present") and summary.get("lhfx_present") for summary in summaries):
        categories.add("surface_flux_outputs_present_in_at_least_one_result")
    if any(
        summary.get("max_cloud_top_m") is not None
        and not _is_unavailable(summary.get("max_cloud_top_m"))
        for summary in summaries
    ):
        categories.add("cloud_depth_evidence_available")
    if not categories:
        categories.add("campaign_not_far_enough_for_science_diagnosis")
    return sorted(categories)


def _recommended_follow_ups(
    summaries: Sequence[Mapping[str, Any]],
    surface_flux_response: Mapping[str, Any],
    low_level_response: Mapping[str, Any],
) -> list[str]:
    followups = [
        (
            "Review campaign rows with unavailable required output fields before "
            "scientific conclusions."
        ),
    ]
    if surface_flux_response.get("state") != SURFACE_FLUX_RESPONSE_VERIFIED:
        followups.append(
            "Resolve Phase 1 surface-flux response comparisons before treating "
            "selected forcing changes as verified in CM1 output."
        )
    low_level_state = low_level_response.get("state")
    if low_level_state == LOW_LEVEL_RESPONSE_MISSING:
        followups.append(
            "Resolve missing or unavailable low-level qv/theta response evidence before "
            "continuing the campaign automatically."
        )
    elif low_level_state == LOW_LEVEL_RESPONSE_NOT_VERIFIED:
        followups.append(
            "Review Phase 1 low-level response comparisons; emitted surface fluxes changed, "
            "but boundary-layer qv/theta deltas did not move in the expected direction."
        )
    elif low_level_state == LOW_LEVEL_RESPONSE_NONCOMPARABLE:
        followups.append(
            "Fix non-comparable Phase 1 low-level response runs or units before "
            "treating boundary-layer response as verified."
        )
    if any(summary.get("diagnostic_quality_warnings") for summary in summaries):
        followups.append(
            "Review caveated or untrusted non-finite fields before using cloud, "
            "updraft, rain-water, surface-rain, or reflectivity outcomes as "
            "scientific evidence."
        )
    if any(summary.get("status") == "package_failed" for summary in summaries):
        followups.append("Fix package-generation blockers before queueing the full campaign.")
    if any(summary.get("status") == "run_failed" for summary in summaries):
        followups.append(
            "Inspect CM1 runtime logs for failed campaign runs outside the repository."
        )
    return _dedupe(followups)


def _forcing_response_summary(summary: Mapping[str, Any]) -> str:
    state = summary.get("phase_gate_state")
    if state == "forcing_path_verified_for_campaign":
        return (
            "Phase 1 has ingested comparable surface-forced runs, verified matched "
            "hfx/qfx output response to selected forcing changes, and has low-level "
            "response diagnostics available. Later phases may be queued without an "
            "operator override, subject to campaign cost/runtime judgment."
        )
    if state == "forcing_wiring_verified_but_response_not_verified":
        low_level_state = (summary.get("low_level_response") or {}).get("state")
        if low_level_state == LOW_LEVEL_RESPONSE_NOT_VERIFIED:
            return (
                "Phase 1 confirmed selected forcing metadata, CM1-facing forcing controls, "
                "hfx/qfx output-field presence, and matched emitted surface-flux response. "
                "However, matched low-level qv/theta response did not move in the expected "
                "direction, so automatic continuation remains blocked."
            )
        if low_level_state == LOW_LEVEL_RESPONSE_MISSING:
            return (
                "Phase 1 confirmed selected forcing metadata, CM1-facing forcing controls, "
                "hfx/qfx output-field presence, and matched emitted surface-flux response. "
                "It did not verify boundary-layer thermodynamic response because low-level "
                "qv/theta evidence is missing or unavailable."
            )
        if low_level_state == LOW_LEVEL_RESPONSE_NONCOMPARABLE:
            return (
                "Phase 1 confirmed selected forcing metadata, CM1-facing forcing controls, "
                "hfx/qfx output-field presence, and matched emitted surface-flux response. "
                "It did not verify boundary-layer thermodynamic response because the "
                "low-level response comparisons are not structurally comparable."
            )
        return (
            "Phase 1 confirmed selected forcing metadata, CM1-facing forcing controls, "
            "hfx/qfx output-field presence, and matched emitted surface-flux response. "
            "It did not verify boundary-layer thermodynamic response."
        )
    if state == SURFACE_FLUX_RESPONSE_NOT_VERIFIED:
        return (
            "Phase 1 produced hfx/qfx statistics, but matched emitted surface-flux "
            "means did not move in the expected direction for the selected forcing "
            "changes."
        )
    if state == SURFACE_FLUX_RESPONSE_MISSING:
        if _surface_flux_response_has_terminal_contamination(summary):
            return (
                "Phase 1 produced finite hfx/qfx means that can be directionally "
                "reviewed, but emitted surface-flux verification remains blocked "
                "because terminal output-frame contamination makes at least one "
                "matched run untrusted."
            )
        return (
            "Phase 1 cannot verify emitted surface-flux response because one or more "
            "matched hfx/qfx statistics are missing, untrusted, or not ingested."
        )
    if state == SURFACE_FLUX_RESPONSE_NONCOMPARABLE:
        return (
            "Phase 1 cannot verify emitted surface-flux response because one or more "
            "matched runs are structurally non-comparable or use non-comparable hfx/qfx "
            "units."
        )
    if state == "forcing_wiring_not_verified":
        return "Surface-flux output fields are missing from ingested results."
    return "No ingested result evidence is available yet."


def _surface_flux_response_has_terminal_contamination(summary: Mapping[str, Any]) -> bool:
    surface_flux_response = summary.get("surface_flux_response")
    if not isinstance(surface_flux_response, Mapping):
        return False
    evaluations = surface_flux_response.get("evaluations")
    if not isinstance(evaluations, list):
        return False
    return any(
        isinstance(evaluation, Mapping)
        and any(
            isinstance(item, str) and "terminal_output_frame_entirely_non_finite" in item
            for item in evaluation.get("unavailable_evidence", [])
        )
        for evaluation in evaluations
    )


def _deepening_summary(summary: Mapping[str, Any]) -> str:
    ingested = [run for run in summary["runs"] if run.get("status") == "ingested"]
    if not ingested:
        return "No ingested results are available to compare deepening or sounding-class response."
    return (
        "Deepening and class-difference evidence is listed per run above. This report does "
        "not convert those diagnostics into predicted-vs-actual verdicts."
    )


def _default_report_path(plan: CampaignPlan) -> Path:
    if plan.commit_report_path:
        return Path(plan.commit_report_path)
    return DEFAULT_REPORT_ROOT / f"{_safe_id(plan.campaign_id)}.md"


def _station_time_label(run: Mapping[str, Any]) -> str:
    station = run.get("station_name") or run.get("station_id") or "unavailable"
    valid_time = run.get("valid_time_utc") or "time unavailable"
    return f"{station} {valid_time}"


def _forcing_label(run: Mapping[str, Any]) -> str:
    return (
        f"H {run.get('surface_heat_flux_k_m_s')} K m/s; "
        f"M {run.get('surface_moisture_flux_g_g_m_s')} g/g m/s"
    )


def _grid_label(run: Mapping[str, Any]) -> str:
    return f"{run.get('domain_size')} {run.get('horizontal_cell_count')} dx {run.get('dx_m')} m"


def _key_result_label(run: Mapping[str, Any]) -> str:
    if run.get("status") != "ingested":
        return str(run.get("status"))
    trust = run.get("diagnostic_trust")
    diagnostic_trust = trust if isinstance(trust, dict) else {}
    return "; ".join(
        [
            _trusted_metric_label(
                "cloud top",
                run.get("max_cloud_top_m"),
                diagnostic_trust.get("qc"),
            ),
            _trusted_metric_label("max w", run.get("max_w_m_s"), diagnostic_trust.get("w")),
            _trusted_bool_label(
                "surface rain",
                run.get("surface_rain_present"),
                diagnostic_trust.get("surface_rain"),
            ),
        ]
    )


def _mapping(data: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        errors.append(f"{label} must be an object")
        return {}
    return dict(data)


def _optional_mapping(data: Any) -> dict[str, Any] | None:
    return dict(data) if isinstance(data, dict) else None


def _list_of_mappings(data: Any, label: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        errors.append(f"{label} must be a list")
        return []
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        rows.append(dict(item))
    return rows


def _indexed_mappings(
    data: Any,
    *,
    key: str,
    label: str,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    rows = _list_of_mappings(data, label, errors)
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        identifier = _optional_string(row.get(key))
        if identifier is None:
            errors.append(f"{label} item missing {key}")
            continue
        if identifier in indexed:
            errors.append(f"Duplicate {label}.{key}: {identifier}")
            continue
        indexed[identifier] = row
    return indexed


def _required_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
    errors: list[str],
) -> str:
    value = _optional_string(data.get(key))
    if value is None:
        errors.append(f"{context}.{key} is required")
        return ""
    return value


def _optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _queue_target(value: Any, *, errors: list[str], context: str) -> QueueTarget:
    if value == "local":
        return "local"
    if value == "lan":
        return "lan"
    errors.append(f"{context} must be local or lan")
    return "local"


def _resolved_tags(
    defaults: Mapping[str, Any],
    selection: Mapping[str, Any],
    run: Mapping[str, Any],
    campaign_id: str,
    matrix_id: str,
) -> list[str]:
    tags: list[str] = [f"campaign:{campaign_id}", f"matrix:{matrix_id}"]
    for source in (defaults, selection, run):
        value = source.get("tags")
        if isinstance(value, list):
            tags.extend(str(item).strip() for item in value if str(item).strip())
    return _dedupe(tags)


def _resolved_notes(
    defaults: Mapping[str, Any],
    selection: Mapping[str, Any],
    run: Mapping[str, Any],
) -> str | None:
    notes = [
        text
        for text in (
            _optional_string(defaults.get("notes")),
            _optional_string(selection.get("selection_notes")),
            _optional_string(run.get("notes")),
        )
        if text
    ]
    return "\n\n".join(notes) if notes else None


def _validate_comparison_control_refs(
    planned: Sequence[CampaignRunPlan], errors: list[str]
) -> None:
    matrix_ids = {run.matrix_id for run in planned}
    for run in planned:
        if run.comparison_control_matrix_id and run.comparison_control_matrix_id not in matrix_ids:
            errors.append(
                f"{run.matrix_id}.comparison.control_matrix_id references unknown run: "
                f"{run.comparison_control_matrix_id}"
            )


def _parse_utc_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CampaignError(f"Invalid UTC datetime: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _mapping_value(mapping: Mapping[str, Any] | None, key: str) -> Any:
    if mapping is None:
        return None
    value = mapping.get(key)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _list_from_mapping(mapping: Mapping[str, Any] | None, key: str) -> list[Any]:
    if mapping is None:
        return []
    value = mapping.get(key)
    return list(value) if isinstance(value, list) else []


def _candidate_evidence(candidate: Mapping[str, Any] | None) -> list[Any]:
    if candidate is None:
        return []
    evidence = candidate.get("evidence")
    if isinstance(evidence, list):
        return evidence
    reasons = candidate.get("interest_reasons")
    return list(reasons) if isinstance(reasons, list) else []


def _payload_message(payload: Mapping[str, object], fallback: str) -> str:
    message = payload.get("message")
    return str(message) if isinstance(message, str) and message else fallback


def _dedupe(values: Iterable[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _fmt(value: object) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _bool_or_fmt(value: object) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return _fmt(value)


def _now() -> datetime:
    return datetime.now(UTC)
