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
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.cm1_input_contract import RunRecipe
from cloud_chamber.dry_run_package import DryRunPackageError, generate_dry_run_package
from cloud_chamber.lan_worker import (
    LanWorkerApiError,
    collect_lan_worker_run,
    start_lan_worker_run,
)
from cloud_chamber.local_run_manager import LocalRunManager
from cloud_chamber.local_run_queue import LocalRunQueueError, LocalRunQueueManager
from cloud_chamber.observed_sounding import (
    ObservedSoundingError,
    ObservedSoundingRecord,
    observed_sounding_from_payload,
    parse_igra_station_text,
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

QueueTarget = Literal["local", "lan"]


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
    run_defaults = _mapping(matrix.get("run_defaults", {}), "run_defaults", errors)
    runs = _list_of_mappings(matrix.get("runs"), "runs", errors)

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
        candidate_screening = _candidate_screening_from_matrix(selection, source)
        stable_identity = _stable_resume_identity(
            campaign_id=campaign_id,
            matrix_id=matrix_id,
            selection_id=selection_id,
            selection_source_reference=source_reference,
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
    allow_absolute_local_paths: bool = False,
    local_queue_factory: Callable[[CloudChamberSettings], LocalRunQueueManager] | None = None,
    lan_start: Callable[[CloudChamberSettings, Path], dict[str, object]] = start_lan_worker_run,
) -> CampaignOperationResult:
    resolved_settings = settings or load_settings(home=runtime_home)
    plan = plan_campaign(matrix_path, allow_absolute_local_paths=allow_absolute_local_paths)
    package_campaign(
        matrix_path,
        settings=resolved_settings,
        selected_matrix_ids=selected_matrix_ids,
        resume=resume,
        allow_absolute_local_paths=allow_absolute_local_paths,
    )
    state = _load_or_create_state(plan, resolved_settings.runtime_home)
    queue_factory = local_queue_factory or _default_local_queue

    for run in _selected_runs(plan.runs, selected_matrix_ids):
        state_run = _state_run_for_matrix(state, run.matrix_id)
        if state_run is None or not state_run.manifest_path:
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
                            "updated_at": _now(),
                        }
                    ),
                )
            else:
                payload = lan_start(resolved_settings, manifest_path)
                status = _lan_payload_to_campaign_status(payload)
                _upsert_state_run(
                    state,
                    state_run.model_copy(
                        update={
                            "status": status,
                            "run_status": status,
                            "lan_worker_payload": dict(payload),
                            "message": _payload_message(payload, "LAN worker run started."),
                            "error": None,
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
            _state_run_with_runtime_status(state_run, queue_entries=queue_entries),
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
    lan_collect: Callable[[CloudChamberSettings, Path], dict[str, object]] = collect_lan_worker_run,
) -> CampaignOperationResult:
    resolved_settings = settings or load_settings(home=runtime_home)
    status_campaign(
        matrix_path,
        settings=resolved_settings,
        allow_absolute_local_paths=allow_absolute_local_paths,
    )
    plan = plan_campaign(matrix_path, allow_absolute_local_paths=allow_absolute_local_paths)
    state = _load_or_create_state(plan, resolved_settings.runtime_home)

    for run in _selected_runs(plan.runs, selected_matrix_ids):
        state_run = _state_run_for_matrix(state, run.matrix_id)
        if state_run is None or not state_run.manifest_path:
            continue
        manifest_path = Path(state_run.manifest_path).expanduser()
        try:
            if run.queue_target == "lan" and state_run.status in {"running", "queued"}:
                payload = lan_collect(resolved_settings, manifest_path)
                state_run = state_run.model_copy(
                    update={
                        "lan_worker_payload": dict(payload),
                        "message": _payload_message(payload, "LAN worker output collected."),
                        "updated_at": _now(),
                    }
                )
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
        "phase_gate_state": _phase_gate_state(summaries),
        "runs": summaries,
        "unavailable_diagnostics": _unavailable_diagnostics(summaries),
        "preliminary_diagnosis_categories": _preliminary_diagnosis_categories(summaries),
        "recommended_follow_ups": _recommended_follow_ups(summaries),
    }

    markdown_path = report_path or _default_report_path(plan)
    if not markdown_path.is_absolute():
        markdown_path = Path.cwd() / markdown_path
    json_path = summary_json_path or (
        resolved_settings.runtime_home.expanduser()
        / "campaigns"
        / plan.campaign_id
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
    run_configuration: Mapping[str, Any],
    forcing_id: str | None,
) -> str:
    payload = {
        "campaign_id": campaign_id,
        "matrix_id": matrix_id,
        "selection_id": selection_id,
        "selection_source_reference": selection_source_reference,
        "forcing_id": forcing_id,
        "run_configuration": run_configuration,
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run_id(campaign_id: str, matrix_id: str, stable_identity: str) -> str:
    raw = f"{campaign_id}-{matrix_id}-{stable_identity[:10]}"
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw).strip("-")
    return cleaned[:112] or f"campaign-run-{stable_identity[:10]}"


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
    return runtime_home.expanduser() / "campaigns" / campaign_id / "campaign-state.json"


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
) -> list[CampaignRunPlan]:
    if selected_matrix_ids is None:
        return list(runs)
    return [run for run in runs if run.matrix_id in selected_matrix_ids]


def _default_local_queue(settings: CloudChamberSettings) -> LocalRunQueueManager:
    return LocalRunQueueManager(
        settings=settings,
        run_manager=LocalRunManager(settings=settings),
    )


def _state_run_with_runtime_status(
    state_run: CampaignStateRun,
    *,
    queue_entries: Mapping[str, Mapping[str, Any]],
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
    manifest = load_run_manifest(manifest_path)
    queue_entry = queue_entries.get(str(manifest_path))
    status = _manifest_to_campaign_status(manifest)
    message = state_run.message
    error = state_run.error
    result_id = state_run.result_id
    if queue_entry is not None:
        status = _queue_entry_to_campaign_status(str(queue_entry.get("state")))
        message = _optional_string(queue_entry.get("message")) or message
        error = _optional_string(queue_entry.get("error")) or error
        result_id = _optional_string(queue_entry.get("result_id")) or result_id
    result = _load_result_for_manifest_path(manifest_path)
    if result is not None:
        status = "ingested"
        result_id = result.result_id
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
    variables = set(result.variables) if result is not None else set()
    missing_fields = (
        result.missing_required_output_fields
        if result is not None
        else ["unavailable_until_result_ingested"]
    )
    candidate = manifest.candidate_screening if manifest is not None else run.candidate_screening
    return {
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
        "model_top_m": run.cm1_values.get("model_top_m"),
        "output_cadence": run.run_configuration["output_cadence"],
        "expected_output_frames": run.cm1_values.get("expected_output_frames"),
        "expected_output_volume": run.resolved_run_configuration.get("output_volume_summary"),
        "required_output_fields": manifest.required_output_fields if manifest is not None else [],
        "missing_output_fields": missing_fields,
        "diagnostic_support": _diagnostic_support(result),
        "hfx_present": "hfx" in variables,
        "hfx_units": _field_units(result, "hfx"),
        "lhfx_present": "lhfx" in variables,
        "lhfx_units": _field_units(result, "lhfx"),
        "low_level_qv_response": "unavailable",
        "low_level_qv_response_method": "low_level_response_diagnostic_not_implemented",
        "low_level_theta_or_temperature_response": "unavailable",
        "low_level_theta_or_temperature_response_method": (
            "low_level_response_diagnostic_not_implemented"
        ),
        "first_cloud_time": (
            diagnostics.cloud.first_cloud_time_seconds if diagnostics is not None else None
        ),
        "max_cloud_top_m": diagnostics.cloud.cloud_top_m if diagnostics is not None else None,
        "max_qc": diagnostics.cloud.max_qc_kg_kg if diagnostics is not None else None,
        "max_qc_time": (
            diagnostics.cloud.time_of_max_qc_seconds if diagnostics is not None else None
        ),
        "max_w_m_s": (diagnostics.vertical_velocity.max_w_m_s if diagnostics is not None else None),
        "max_w_time": (
            diagnostics.vertical_velocity.time_of_max_w_seconds if diagnostics is not None else None
        ),
        "qr_present": diagnostics.rain.present if diagnostics is not None else None,
        "surface_rain_present": (
            diagnostics.surface_rain.present if diagnostics is not None else None
        ),
        "surface_rain_max": (
            diagnostics.surface_rain.max_surface_rain if diagnostics is not None else None
        ),
        "surface_rain_units": (diagnostics.surface_rain.units if diagnostics is not None else None),
        "dbz_present": (
            diagnostics.reflectivity.max_dbz is not None if diagnostics is not None else None
        ),
        "max_dbz": diagnostics.reflectivity.max_dbz if diagnostics is not None else None,
        "first_deep_cloud_time": "unavailable",
        "warnings": result.warnings if result is not None else [],
        "caveats": _summary_caveats(run, state_run, result),
        "error": state_run.error if state_run else None,
    }


def _diagnostic_support(result: ResultMetadata | None) -> dict[str, str]:
    if result is None or result.diagnostics is None:
        return {
            "surface_fluxes": "unavailable_until_result_ingested",
            "low_level_response": "unavailable",
            "cloud": "unavailable",
            "vertical_velocity": "unavailable",
            "rain_water_aloft": "unavailable",
            "surface_rain": "unavailable",
            "reflectivity": "unavailable",
        }
    diagnostics = result.diagnostics
    return {
        "surface_fluxes": "available" if {"hfx", "lhfx"} <= set(result.variables) else "missing",
        "low_level_response": "unavailable",
        "cloud": "available" if diagnostics.cloud.available else "missing",
        "vertical_velocity": "available" if diagnostics.vertical_velocity.available else "missing",
        "rain_water_aloft": "available" if diagnostics.rain.available else "missing",
        "surface_rain": "available" if diagnostics.surface_rain.available else "missing",
        "reflectivity": "available" if diagnostics.reflectivity.available else "missing",
    }


def _field_units(result: ResultMetadata | None, field_name: str) -> str | None:
    if result is None:
        return None
    return next((field.units for field in result.fields_detected if field.name == field_name), None)


def _summary_caveats(
    run: CampaignRunPlan,
    state_run: CampaignStateRun | None,
    result: ResultMetadata | None,
) -> list[str]:
    caveats = [
        "surface_forcing_is_constant_uniform_proxy",
        "low_level_response_diagnostic_not_implemented",
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
    return _dedupe(caveats)


def _render_markdown_report(plan: CampaignPlan, summary: Mapping[str, Any]) -> str:
    lines = [
        f"# Surface-Forced Campaign Report: {plan.campaign_id}",
        "",
        f"Campaign ID: `{plan.campaign_id}`",
        f"Protocol: `{plan.protocol or 'not specified'}`",
        f"Matrix: `{summary['matrix_path']}`",
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
        "",
        "## Run Table",
        "",
        "| Matrix ID | Status | Station/time | Forcing | Grid/domain | Key result |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
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
            "## Per-Run Evidence",
            "",
        ]
    )
    for run in summary["runs"]:
        required_fields = ", ".join(run["required_output_fields"]) or "unavailable"
        missing_fields = ", ".join(run["missing_output_fields"]) or "none"
        cloud_updraft = (
            f"first cloud `{_fmt(run['first_cloud_time'])}`, "
            f"max cloud top `{_fmt(run['max_cloud_top_m'])}`, "
            f"max qc `{_fmt(run['max_qc'])}`, "
            f"max w `{_fmt(run['max_w_m_s'])}`"
        )
        precipitation = (
            f"qr `{run['qr_present']}`, "
            f"surface rain `{run['surface_rain_present']}`, "
            f"max dBZ `{_fmt(run['max_dbz'])}`"
        )
        lines.extend(
            [
                f"### {run['matrix_id']}",
                "",
                f"- Run ID: `{run['run_id']}`",
                f"- Result ID: `{run['result_id'] or 'not ingested'}`",
                f"- Source: `{run['selection_source_type']}` `{run['selection_source_reference']}`",
                f"- Candidate story: `{run['candidate_story'] or 'unavailable'}`",
                f"- Required/missing fields: `{required_fields}` / `{missing_fields}`",
                f"- Surface flux fields: hfx `{run['hfx_present']}`, lhfx `{run['lhfx_present']}`",
                f"- Cloud/updraft: {cloud_updraft}",
                f"- Precipitation/reflectivity: {precipitation}",
                f"- Low-level response: `{run['low_level_qv_response_method']}`",
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


def _phase_gate_state(summaries: Sequence[Mapping[str, Any]]) -> str:
    ingested = [summary for summary in summaries if summary.get("status") == "ingested"]
    if not ingested:
        return "inconclusive_missing_evidence"
    if not all(summary.get("hfx_present") and summary.get("lhfx_present") for summary in ingested):
        return "forcing_wiring_not_verified"
    return "forcing_wiring_verified_but_response_not_verified"


def _unavailable_diagnostics(summaries: Sequence[Mapping[str, Any]]) -> list[str]:
    unavailable: set[str] = set()
    for summary in summaries:
        for field in summary.get("missing_output_fields", []):
            unavailable.add(f"missing_output_field:{field}")
        if summary.get("low_level_qv_response") == "unavailable":
            unavailable.add("low_level_qv_response")
        if summary.get("low_level_theta_or_temperature_response") == "unavailable":
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
    if any(summary.get("max_cloud_top_m") not in {None, "unavailable"} for summary in summaries):
        categories.add("cloud_depth_evidence_available")
    if not categories:
        categories.add("campaign_not_far_enough_for_science_diagnosis")
    return sorted(categories)


def _recommended_follow_ups(summaries: Sequence[Mapping[str, Any]]) -> list[str]:
    followups = [
        "Implement standardized low-level qv/theta/temperature response diagnostics.",
        (
            "Review campaign rows with unavailable required output fields before "
            "scientific conclusions."
        ),
    ]
    if any(summary.get("status") == "package_failed" for summary in summaries):
        followups.append("Fix package-generation blockers before queueing the full campaign.")
    if any(summary.get("status") == "run_failed" for summary in summaries):
        followups.append(
            "Inspect CM1 runtime logs for failed campaign runs outside the repository."
        )
    return _dedupe(followups)


def _forcing_response_summary(summary: Mapping[str, Any]) -> str:
    state = summary.get("phase_gate_state")
    if state == "forcing_wiring_verified_but_response_not_verified":
        return (
            "Surface-flux output fields are present in at least one ingested result, but "
            "standardized low-level response diagnostics are not implemented yet."
        )
    if state == "forcing_wiring_not_verified":
        return "Surface-flux output fields are missing from ingested results."
    return "No ingested result evidence is available yet."


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
    return DEFAULT_REPORT_ROOT / f"{plan.campaign_id}.md"


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
    return (
        f"cloud top {_fmt(run.get('max_cloud_top_m'))}; "
        f"max w {_fmt(run.get('max_w_m_s'))}; "
        f"surface rain {run.get('surface_rain_present')}"
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


def _now() -> datetime:
    return datetime.now(UTC)
