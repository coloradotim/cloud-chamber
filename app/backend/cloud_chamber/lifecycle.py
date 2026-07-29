"""Owner-aware Activity and History projection over retained runtime records."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.cloud_worlds import (
    MORE_MOISTURE_DISPLAY_NAME,
    MORE_MOISTURE_SIMULATION_ID,
    PRESENTATION_BASELINE_RESULT_ID,
    PRESENTATION_BASELINE_RUN_ID,
    PRESENTATION_MORE_MOISTURE_RESULT_ID,
    PRESENTATION_MORE_MOISTURE_RUN_ID,
    REFERENCE_DISPLAY_NAME,
    REFERENCE_SIMULATION_ID,
)
from cloud_chamber.local_run_queue import RunQueueEntry, RunQueueState
from cloud_chamber.mountain_waves_variations import (
    LEGACY_VARIATION_CASE_ID,
    VARIATION_CASE_ID,
)
from cloud_chamber.mountain_waves_world import (
    DRY_CASE_ID,
    DRY_RUN_ID,
    DRY_SIMULATION_ID,
    MOIST_CASE_ID,
    MOIST_RUN_ID,
    MOIST_SIMULATION_ID,
)
from cloud_chamber.result_cards import ResultCard, list_result_cards
from cloud_chamber.runtime_storage import (
    RunStorageEntry,
    RuntimeStorageInventory,
    runtime_lifecycle_inventory,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storm_examination import (
    PRESENTATION_CASE_ID as SUPERCELLS_REFERENCE_CASE_ID,
)
from cloud_chamber.storm_examination import (
    PRESENTATION_RUN_ID as SUPERCELLS_REFERENCE_RUN_ID,
)
from cloud_chamber.storm_examination import (
    STRAIGHT_LINE_PRESENTATION_CASE_ID,
    STRAIGHT_LINE_PRESENTATION_RUN_ID,
)
from cloud_chamber.supercells_world import (
    REFERENCE_SIMULATION_ID as SUPERCELLS_REFERENCE_SIMULATION_ID,
)
from cloud_chamber.supercells_world import (
    STRAIGHT_LINE_SIMULATION_ID as SUPERCELLS_STRAIGHT_LINE_SIMULATION_ID,
)

OwnerId = Literal[
    "trade_cumulus",
    "mountain_waves",
    "supercells",
    "fun_with_soundings",
    "legacy_unassigned",
]
WorldOwnerId = Literal["trade_cumulus", "mountain_waves", "supercells"]
RecordKind = Literal["simulation", "experiment"]
AttemptRelationship = Literal[
    "initial",
    "unchanged_retry",
    "checkpoint_restart",
    "alternate_observation_attempt",
    "extension",
    "later_backing_candidate",
]
ActivityGroup = Literal[
    "needs_attention",
    "ready_to_run",
    "queued",
    "running",
    "awaiting_validation_or_ingest",
    "ready_to_inspect",
    "available_with_caveats",
    "recently_completed",
]
TrustState = Literal["trusted", "caveated", "failed", "unassessed", "unavailable"]
FactState = Literal[
    "not_applicable",
    "unknown",
    "absent",
    "present",
    "pending",
    "passed",
    "caveated",
    "failed",
    "conflict",
    "missing",
    "eligible",
    "ineligible",
]
ActionKind = Literal[
    "run",
    "cancel",
    "ingest",
    "explore",
    "compare_parent",
    "compare_reference",
    "review",
    "open_run_controls",
]
DependencyKind = Literal["saved_view", "saved_comparison"]

OWNER_LABELS: dict[OwnerId, str] = {
    "trade_cumulus": "Trade Cumulus",
    "mountain_waves": "Mountain Waves",
    "supercells": "Supercells",
    "fun_with_soundings": "Fun With Soundings",
    "legacy_unassigned": "Legacy / unassigned",
}
_WORLD_OWNER_IDS: set[OwnerId] = {"trade_cumulus", "mountain_waves", "supercells"}
_ATTEMPT_RELATIONSHIPS: set[str] = {
    "initial",
    "unchanged_retry",
    "checkpoint_restart",
    "alternate_observation_attempt",
    "extension",
    "later_backing_candidate",
}
_ACTIVE_QUEUE_STATES = {"queued", "running"}
_ATTENTION_STATES = {
    "failed",
    "canceled",
    "launch_failed",
    "ingest_failed",
    "completed_no_output",
}


class LifecycleDifference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    label: str
    before: Any = None
    after: Any = None
    units: str | None = None
    material: bool = True


class LifecycleFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scientific_work: FactState
    package: FactState
    attempt: FactState
    queue: FactState
    process: FactState
    expected_output: FactState
    technical_integrity: FactState
    ingest: FactState
    world_inspectability: FactState
    simulation_availability: FactState
    parent_eligibility: FactState
    retained_assets: FactState


class LifecycleAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt_id: str
    run_id: str
    relationship: AttemptRelationship
    accepted_backing: bool = False
    manifest_path: str | None = None
    lifecycle_state: str | None = None
    queue_state: str | None = None
    product_state: str | None = None
    validation_status: str | None = None
    result_id: str | None = None
    output_artifact_count: int = 0
    size_bytes: int | None = None
    retained_state: Literal["retained", "missing", "conflict", "unknown"] = "unknown"
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    updated_at: str | None = None
    message: str | None = None
    failure_reason: str | None = None


class LifecycleAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ActionKind
    label: str
    run_id: str | None = None
    manifest_path: str | None = None
    result_id: str | None = None
    world_id: str | None = None
    simulation_id: str | None = None
    target_simulation_id: str | None = None


class LifecycleDependency(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: DependencyKind
    dependency_id: str
    title: str
    relationship: str


class WorldLifecycleSource(BaseModel):
    """Normalized current World inventory fact used by the projection."""

    model_config = ConfigDict(extra="forbid")

    owner_id: WorldOwnerId
    simulation_id: str
    display_name: str
    role: str
    run_id: str
    result_id: str | None = None
    case_id: str | None = None
    recipe_id: str | None = None
    recipe_version: str | None = None
    parent_simulation_id: str | None = None
    reference_simulation_id: str | None = None
    question: str | None = None
    differences: list[LifecycleDifference] = Field(default_factory=list)
    accepted_backing: bool = True
    availability_state: Literal["available", "missing", "unavailable", "conflict"]
    inspectability_state: Literal["passed", "failed", "missing", "conflict"]
    parent_eligibility_state: Literal["eligible", "ineligible", "unknown"]
    trust_state: TrustState = "unassessed"
    caveats: list[str] = Field(default_factory=list)
    created_at: str | None = None
    completed_at: str | None = None


class LifecycleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str
    record_kind: RecordKind
    owner_id: OwnerId
    owner_label: str
    simulation_id: str | None = None
    experiment_id: str | None = None
    world_id: str | None = None
    recipe_id: str | None = None
    recipe_version: str | None = None
    parent_simulation_id: str | None = None
    reference_simulation_id: str | None = None
    display_name: str
    question: str | None = None
    role: str | None = None
    case_id: str | None = None
    differences: list[LifecycleDifference] = Field(default_factory=list)
    attempts: list[LifecycleAttempt] = Field(default_factory=list)
    facts: LifecycleFacts
    trust_state: TrustState
    caveats: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    lifecycle_label: str
    lifecycle_detail: str
    activity_group: ActivityGroup | None = None
    in_activity: bool = False
    created_at: str | None = None
    updated_at: str | None = None
    size_bytes: int | None = None
    dependencies: list[LifecycleDependency] = Field(default_factory=list)
    actions: list[LifecycleAction] = Field(default_factory=list)


class LifecycleProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    generated_at: str
    records: list[LifecycleRecord]
    warnings: list[str] = Field(default_factory=list)


def lifecycle_projection(
    settings: CloudChamberSettings,
    *,
    queue: RunQueueState,
    now: datetime | None = None,
) -> LifecycleProjection:
    """Build the canonical read-only lifecycle projection from current sources."""
    storage = runtime_lifecycle_inventory(settings)
    results = list_result_cards(settings)
    sources, warnings = _lightweight_world_sources(storage, results)
    return build_lifecycle_projection(
        storage=storage,
        results=results,
        queue=queue,
        world_sources=sources,
        dependencies=_dependency_index(settings),
        warnings=warnings,
        now=now,
    )


def build_lifecycle_projection(
    *,
    storage: RuntimeStorageInventory,
    results: list[ResultCard],
    queue: RunQueueState,
    world_sources: list[WorldLifecycleSource],
    dependencies: dict[tuple[str, str], list[LifecycleDependency]] | None = None,
    warnings: list[str] | None = None,
    now: datetime | None = None,
) -> LifecycleProjection:
    """Project normalized fixtures or live adapters into canonical records."""
    generated_at = now or datetime.now(UTC)
    dependency_index = dependencies or {}
    source_by_run = {source.run_id: source for source in world_sources}
    source_by_result = {
        source.result_id: source for source in world_sources if source.result_id is not None
    }
    source_by_identity = {
        (source.owner_id, source.simulation_id): source for source in world_sources
    }
    result_by_run = {result.run_id: result for result in results}
    queue_by_run = {entry.run_id: entry for entry in queue.entries}
    grouped_runs: dict[str, list[RunStorageEntry]] = defaultdict(list)
    group_source: dict[str, WorldLifecycleSource] = {}
    group_result: dict[str, ResultCard] = {}

    for run in storage.runs:
        result = result_by_run.get(run.run_id)
        source = source_by_run.get(run.run_id)
        if source is None and result is not None:
            source = source_by_result.get(result.result_id)
        if source is None:
            source = _declared_world_source(run, source_by_identity)
        key = _record_key(run.run_id, result, source)
        grouped_runs[key].append(run)
        if source is not None:
            group_source[key] = source
        if result is not None:
            group_result[key] = result

    for result in results:
        source = source_by_result.get(result.result_id)
        key = _record_key(result.run_id, result, source)
        group_result[key] = result
        if source is not None:
            group_source[key] = source
        grouped_runs.setdefault(key, [])

    for source in world_sources:
        key = _record_key(source.run_id, None, source)
        group_source[key] = source
        grouped_runs.setdefault(key, [])

    for entry in queue.entries:
        if any(entry.run_id == run.run_id for runs in grouped_runs.values() for run in runs):
            continue
        source = source_by_run.get(entry.run_id)
        key = _record_key(entry.run_id, None, source)
        if source is not None:
            group_source[key] = source
        grouped_runs.setdefault(key, [])

    records = [
        _project_record(
            key=key,
            runs=runs,
            result=group_result.get(key),
            source=group_source.get(key),
            queue_by_run=queue_by_run,
            dependencies=dependency_index,
            now=generated_at,
        )
        for key, runs in grouped_runs.items()
    ]
    records.sort(key=lambda record: (record.updated_at or "", record.display_name), reverse=True)
    return LifecycleProjection(
        generated_at=generated_at.isoformat(),
        records=records,
        warnings=warnings or [],
    )


def _project_record(
    *,
    key: str,
    runs: list[RunStorageEntry],
    result: ResultCard | None,
    source: WorldLifecycleSource | None,
    queue_by_run: dict[str, RunQueueEntry],
    dependencies: dict[tuple[str, str], list[LifecycleDependency]],
    now: datetime,
) -> LifecycleRecord:
    owner_id = source.owner_id if source is not None else _experiment_owner(result, runs)
    world_id = source.owner_id if source is not None else None
    attempts = [
        _attempt_from_run(
            run,
            queue_by_run.get(run.run_id),
            result if result is not None and result.run_id == run.run_id else None,
            source,
        )
        for run in runs
    ]
    for entry in queue_by_run.values():
        if any(attempt.run_id == entry.run_id for attempt in attempts):
            continue
        belongs_to_record = (
            (source is not None and entry.run_id == source.run_id)
            or (result is not None and entry.run_id == result.run_id)
            or (source is None and result is None and key == f"experiment:{entry.run_id}")
        )
        if not belongs_to_record:
            continue
        attempts.append(_attempt_from_queue(entry, source))
    if not attempts and source is not None:
        attempts.append(_missing_source_attempt(source))
    attempts.sort(key=lambda attempt: (attempt.created_at or "", attempt.run_id))

    tags = result.tags if result is not None else _manifest_tags(runs)
    caveats = _caveats(result, source, runs)
    trust = _trust_state(result, source)
    facts = _facts(attempts, result, source, trust)
    lifecycle_label, lifecycle_detail, activity_group = _lifecycle_summary(
        attempts, result, source, facts, trust
    )
    created_at = _earliest(
        [attempt.created_at for attempt in attempts]
        + ([source.created_at] if source is not None else [])
        + ([result.created_at.isoformat()] if result is not None else [])
    )
    updated_at = _latest(
        [attempt.updated_at for attempt in attempts]
        + ([source.completed_at] if source is not None else [])
        + ([result.updated_at.isoformat()] if result is not None else [])
    )
    recent = _is_recent(updated_at, now=now)
    in_activity = activity_group is not None and (
        activity_group
        in {
            "needs_attention",
            "ready_to_run",
            "queued",
            "running",
            "awaiting_validation_or_ingest",
        }
        or recent
    )
    if not in_activity:
        activity_group = None
    simulation_id = source.simulation_id if source is not None else None
    record_dependencies = (
        dependencies.get((source.owner_id, source.simulation_id), []) if source is not None else []
    )
    actions = _actions(attempts, result, source, facts)
    display_name = (
        source.display_name
        if source is not None
        else result.name
        if result is not None
        else _run_display_name(runs, key)
    )
    question = (
        source.question
        if source is not None and source.question
        else result.physical_question
        if result is not None
        else _run_question(runs)
    )
    return LifecycleRecord(
        record_id=key,
        record_kind="simulation" if source is not None else "experiment",
        owner_id=owner_id,
        owner_label=OWNER_LABELS[owner_id],
        simulation_id=simulation_id,
        experiment_id=(
            None if source is not None else (result.result_id if result else _run_id(runs))
        ),
        world_id=world_id,
        recipe_id=(
            source.recipe_id
            if source is not None
            else result.recipe_id
            if result is not None
            else _run_recipe_id(runs)
        ),
        recipe_version=source.recipe_version if source is not None else None,
        parent_simulation_id=source.parent_simulation_id if source is not None else None,
        reference_simulation_id=source.reference_simulation_id if source is not None else None,
        display_name=display_name,
        question=question,
        role=source.role if source is not None else "experiment",
        case_id=(
            source.case_id
            if source is not None
            else result.scenario_id
            if result is not None
            else _run_case_id(runs)
        ),
        differences=source.differences if source is not None else [],
        attempts=attempts,
        facts=facts,
        trust_state=trust,
        caveats=caveats,
        tags=tags,
        notes=result.notes if result is not None else _manifest_notes(runs),
        lifecycle_label=lifecycle_label,
        lifecycle_detail=lifecycle_detail,
        activity_group=activity_group,
        in_activity=in_activity,
        created_at=created_at,
        updated_at=updated_at,
        size_bytes=(sum(run.size_bytes for run in runs) or None) if runs else None,
        dependencies=record_dependencies,
        actions=actions,
    )


def _attempt_from_run(
    run: RunStorageEntry,
    queue: RunQueueEntry | None,
    result: ResultCard | None,
    source: WorldLifecycleSource | None,
) -> LifecycleAttempt:
    configuration = run.run_configuration or {}
    relationship = _attempt_relationship(configuration, run.run_id, source)
    queue_state = queue.state if queue is not None else _queue_state_from_lifecycle(run)
    failure_reason = (
        queue.error
        if queue is not None and queue.error
        else run.manifest_error
        if run.manifest_error
        else run.worker_message
        if run.category in {"failed", "canceled", "malformed_manifest", "missing_manifest"}
        else None
    )
    return LifecycleAttempt(
        attempt_id=_string(configuration.get("attempt_id")) or run.run_id,
        run_id=run.run_id,
        relationship=relationship,
        accepted_backing=bool(source and source.run_id == run.run_id and source.accepted_backing),
        manifest_path=run.manifest_path,
        lifecycle_state=run.lifecycle_state,
        queue_state=queue_state,
        product_state=run.product_state,
        validation_status=run.validation_status,
        result_id=result.result_id if result is not None else queue.result_id if queue else None,
        output_artifact_count=run.output_artifact_count,
        size_bytes=run.size_bytes or None,
        retained_state=(
            "conflict"
            if run.category == "malformed_manifest"
            else "missing"
            if run.category == "missing_manifest"
            else "retained"
        ),
        created_at=run.created_at or (queue.queued_at if queue else None),
        started_at=queue.started_at if queue else run.worker_started_at,
        finished_at=queue.finished_at if queue else run.worker_finished_at,
        updated_at=(queue.updated_at if queue else None)
        or run.worker_status_updated_at
        or run.updated_at,
        message=queue.message if queue is not None else run.worker_message,
        failure_reason=failure_reason,
    )


def _attempt_from_queue(
    entry: RunQueueEntry,
    source: WorldLifecycleSource | None,
) -> LifecycleAttempt:
    return LifecycleAttempt(
        attempt_id=entry.run_id,
        run_id=entry.run_id,
        relationship="initial",
        accepted_backing=bool(source and source.run_id == entry.run_id),
        manifest_path=entry.manifest_path,
        lifecycle_state=entry.state,
        queue_state=entry.state,
        result_id=entry.result_id,
        retained_state="retained" if Path(entry.manifest_path).exists() else "missing",
        created_at=entry.queued_at,
        started_at=entry.started_at,
        finished_at=entry.finished_at,
        updated_at=entry.updated_at,
        message=entry.message,
        failure_reason=entry.error,
    )


def _missing_source_attempt(source: WorldLifecycleSource) -> LifecycleAttempt:
    return LifecycleAttempt(
        attempt_id=source.run_id,
        run_id=source.run_id,
        relationship="initial",
        accepted_backing=source.accepted_backing,
        lifecycle_state="missing",
        retained_state="missing",
        created_at=source.created_at,
        finished_at=source.completed_at,
        updated_at=source.completed_at or source.created_at,
        failure_reason="The accepted backing run is not present in retained runtime storage.",
    )


def _facts(
    attempts: list[LifecycleAttempt],
    result: ResultCard | None,
    source: WorldLifecycleSource | None,
    trust: TrustState,
) -> LifecycleFacts:
    queue_states = {attempt.queue_state for attempt in attempts if attempt.queue_state}
    lifecycle_states = {attempt.lifecycle_state for attempt in attempts if attempt.lifecycle_state}
    output_count = sum(attempt.output_artifact_count for attempt in attempts)
    retained_states = {attempt.retained_state for attempt in attempts}
    process_state: FactState = "unknown"
    if "running" in queue_states or "running" in lifecycle_states:
        process_state = "pending"
    elif (
        "completed" in lifecycle_states
        or result is not None
        or (source is not None and source.availability_state == "available")
    ):
        process_state = "passed"
    elif lifecycle_states & {"failed", "canceled", "launch_failed"}:
        process_state = "failed"
    elif lifecycle_states & {"packaged", "queued"}:
        process_state = "pending"
    expected_output: FactState = "present" if output_count > 0 or result is not None else "unknown"
    if (
        any(state in {"completed_no_output", "missing"} for state in lifecycle_states)
        or "missing" in retained_states
        or ("completed" in lifecycle_states and output_count == 0 and result is None)
    ):
        expected_output = "missing"
    inspectability: FactState = "not_applicable"
    availability: FactState = "not_applicable"
    parent_eligibility: FactState = "not_applicable"
    if source is not None:
        inspectability = source.inspectability_state
        availability = (
            "present"
            if source.availability_state == "available"
            else "conflict"
            if source.availability_state == "conflict"
            else "missing"
        )
        parent_eligibility = (
            "eligible"
            if source.parent_eligibility_state == "eligible"
            else "ineligible"
            if source.parent_eligibility_state == "ineligible"
            else "unknown"
        )
    return LifecycleFacts(
        scientific_work="present",
        package="present" if any(attempt.manifest_path for attempt in attempts) else "missing",
        attempt="present" if attempts else "absent",
        queue=(
            "pending"
            if queue_states & _ACTIVE_QUEUE_STATES
            else "failed"
            if queue_states & _ATTENTION_STATES
            else "not_applicable"
        ),
        process=process_state,
        expected_output=expected_output,
        technical_integrity=(
            "passed"
            if trust == "trusted"
            else "caveated"
            if trust == "caveated"
            else "failed"
            if trust == "failed"
            else "unknown"
        ),
        ingest="present" if result is not None else "pending" if output_count else "not_applicable",
        world_inspectability=inspectability,
        simulation_availability=availability,
        parent_eligibility=parent_eligibility,
        retained_assets=(
            "conflict"
            if "conflict" in retained_states
            else "missing"
            if "missing" in retained_states and "retained" not in retained_states
            else "present"
            if "retained" in retained_states
            else "unknown"
        ),
    )


def _lifecycle_summary(
    attempts: list[LifecycleAttempt],
    result: ResultCard | None,
    source: WorldLifecycleSource | None,
    facts: LifecycleFacts,
    trust: TrustState,
) -> tuple[str, str, ActivityGroup | None]:
    queue_states = {attempt.queue_state for attempt in attempts if attempt.queue_state}
    lifecycle_states = {attempt.lifecycle_state for attempt in attempts if attempt.lifecycle_state}
    if source is not None and source.availability_state == "conflict":
        return (
            "Identity conflict",
            "The claimed Simulation identity conflicts with current World inventory.",
            "needs_attention",
        )
    if queue_states & {"running"} or lifecycle_states & {"running"}:
        return "Running", "CM1 execution is in progress.", "running"
    if queue_states & {"queued"} or lifecycle_states & {"queued"}:
        return "Queued", "The package is waiting for local CM1 execution.", "queued"
    if lifecycle_states & {"packaged"}:
        return (
            "Ready to run",
            "The deterministic package is retained and can be run.",
            "ready_to_run",
        )
    if lifecycle_states & _ATTENTION_STATES:
        state = next(iter(lifecycle_states & _ATTENTION_STATES))
        return (
            _humanize(state),
            _attempt_failure_detail(attempts),
            "needs_attention",
        )
    if facts.retained_assets == "missing" or facts.expected_output == "missing":
        return (
            "Output missing",
            "The scientific record remains, but retained backing output is unavailable.",
            "needs_attention",
        )
    if (
        facts.process == "passed"
        and result is None
        and (source is None or source.availability_state != "available")
    ):
        return (
            "Awaiting validation or ingest",
            "CM1 completed, but no inspectable Result or available Simulation is recorded.",
            "awaiting_validation_or_ingest",
        )
    if source is not None and source.availability_state == "available":
        if trust == "caveated" or source.caveats:
            return (
                "Available with caveats",
                "The Simulation is inspectable; visible caveats remain attached.",
                "available_with_caveats",
            )
        return (
            "Available",
            "The Simulation is inspectable in its Cloud World.",
            "recently_completed",
        )
    if result is not None:
        return (
            "Ready to inspect",
            "The ingested Experiment is available in Explore.",
            "ready_to_inspect",
        )
    return "Retained", "The record remains available in History.", None


def _actions(
    attempts: list[LifecycleAttempt],
    result: ResultCard | None,
    source: WorldLifecycleSource | None,
    facts: LifecycleFacts,
) -> list[LifecycleAction]:
    actions: list[LifecycleAction] = []
    current = attempts[-1] if attempts else None
    if current is not None and current.lifecycle_state == "packaged" and current.manifest_path:
        actions.append(
            LifecycleAction(
                kind="run",
                label="Run",
                run_id=current.run_id,
                manifest_path=current.manifest_path,
            )
        )
    if current is not None and (
        current.lifecycle_state == "running" or current.queue_state == "running"
    ):
        actions.append(LifecycleAction(kind="cancel", label="Cancel", run_id=current.run_id))
    if (
        current is not None
        and facts.process == "passed"
        and facts.expected_output == "present"
        and result is None
        and current.manifest_path
        and (source is None or source.availability_state != "available")
    ):
        actions.append(
            LifecycleAction(
                kind="ingest",
                label="Validate and ingest",
                run_id=current.run_id,
                manifest_path=current.manifest_path,
            )
        )
    if source is not None and source.availability_state == "available":
        actions.append(
            LifecycleAction(
                kind="explore",
                label="Explore",
                world_id=source.owner_id,
                simulation_id=source.simulation_id,
                result_id=source.result_id,
            )
        )
        if source.parent_simulation_id:
            actions.append(
                LifecycleAction(
                    kind="compare_parent",
                    label="Compare to parent",
                    world_id=source.owner_id,
                    simulation_id=source.simulation_id,
                    target_simulation_id=source.parent_simulation_id,
                )
            )
        if (
            source.reference_simulation_id
            and source.reference_simulation_id != source.simulation_id
            and source.reference_simulation_id != source.parent_simulation_id
        ):
            actions.append(
                LifecycleAction(
                    kind="compare_reference",
                    label="Compare to reference",
                    world_id=source.owner_id,
                    simulation_id=source.simulation_id,
                    target_simulation_id=source.reference_simulation_id,
                )
            )
    elif result is not None:
        actions.append(
            LifecycleAction(
                kind="explore",
                label="Explore",
                result_id=result.result_id,
            )
        )
    if any(attempt.failure_reason for attempt in attempts) or facts.retained_assets in {
        "missing",
        "conflict",
    }:
        actions.append(
            LifecycleAction(
                kind="review",
                label="Review issue",
                run_id=current.run_id if current else None,
            )
        )
    if source is None:
        actions.append(
            LifecycleAction(
                kind="open_run_controls",
                label="Open run controls",
                run_id=current.run_id if current else result.run_id if result else None,
            )
        )
    return actions


def _lightweight_world_sources(
    storage: RuntimeStorageInventory,
    results: list[ResultCard],
) -> tuple[list[WorldLifecycleSource], list[str]]:
    runs = {run.run_id: run for run in storage.runs}
    result_by_run = {result.run_id: result for result in results}
    sources = [
        _known_source(
            owner_id="trade_cumulus",
            simulation_id=REFERENCE_SIMULATION_ID,
            display_name=REFERENCE_DISPLAY_NAME,
            role="reference",
            run_id=PRESENTATION_BASELINE_RUN_ID,
            result_id=PRESENTATION_BASELINE_RESULT_ID,
            case_id=None,
            parent_simulation_id=None,
            reference_simulation_id=REFERENCE_SIMULATION_ID,
            parent_eligibility_state="unknown",
            run=runs.get(PRESENTATION_BASELINE_RUN_ID),
            result=result_by_run.get(PRESENTATION_BASELINE_RUN_ID),
            question="How does the canonical BOMEX trade-cumulus field evolve?",
        ),
        _known_source(
            owner_id="trade_cumulus",
            simulation_id=MORE_MOISTURE_SIMULATION_ID,
            display_name=MORE_MOISTURE_DISPLAY_NAME,
            role="variation",
            run_id=PRESENTATION_MORE_MOISTURE_RUN_ID,
            result_id=PRESENTATION_MORE_MOISTURE_RESULT_ID,
            case_id=None,
            parent_simulation_id=REFERENCE_SIMULATION_ID,
            reference_simulation_id=REFERENCE_SIMULATION_ID,
            parent_eligibility_state="unknown",
            run=runs.get(PRESENTATION_MORE_MOISTURE_RUN_ID),
            result=result_by_run.get(PRESENTATION_MORE_MOISTURE_RUN_ID),
            differences=_trade_moisture_difference(
                runs.get(PRESENTATION_BASELINE_RUN_ID),
                runs.get(PRESENTATION_MORE_MOISTURE_RUN_ID),
            ),
        ),
        _known_source(
            owner_id="mountain_waves",
            simulation_id=DRY_SIMULATION_ID,
            display_name="Dry Ridge — Wave Mechanics",
            role="built_in",
            run_id=DRY_RUN_ID,
            result_id=None,
            case_id=DRY_CASE_ID,
            parent_simulation_id=None,
            reference_simulation_id=MOIST_SIMULATION_ID,
            parent_eligibility_state="ineligible",
            run=runs.get(DRY_RUN_ID),
            result=None,
            question="How does terrain force a dry gravity wave?",
            authored_caveats=["This dry benchmark does not simulate moisture or cloud formation."],
        ),
        _known_source(
            owner_id="mountain_waves",
            simulation_id=MOIST_SIMULATION_ID,
            display_name="Boulder Windstorm — Moist Reference",
            role="built_in",
            run_id=MOIST_RUN_ID,
            result_id=None,
            case_id=MOIST_CASE_ID,
            parent_simulation_id=None,
            reference_simulation_id=MOIST_SIMULATION_ID,
            parent_eligibility_state="eligible",
            run=runs.get(MOIST_RUN_ID),
            result=None,
            question="Where does terrain-forced flow create and erode wave cloud?",
            authored_caveats=["This is a native two-dimensional x-z Simulation."],
        ),
        _known_source(
            owner_id="supercells",
            simulation_id=SUPERCELLS_REFERENCE_SIMULATION_ID,
            display_name="Quarter-Circle Supercell",
            role="reference",
            run_id=SUPERCELLS_REFERENCE_RUN_ID,
            result_id=None,
            case_id=SUPERCELLS_REFERENCE_CASE_ID,
            parent_simulation_id=None,
            reference_simulation_id=SUPERCELLS_REFERENCE_SIMULATION_ID,
            parent_eligibility_state="unknown",
            run=runs.get(SUPERCELLS_REFERENCE_RUN_ID),
            result=None,
            question="How do rotating ascent, hydrometeors, and low-level flow evolve?",
        ),
        _known_source(
            owner_id="supercells",
            simulation_id=SUPERCELLS_STRAIGHT_LINE_SIMULATION_ID,
            display_name="Straight-Line Hodograph Supercell",
            role="variation",
            run_id=STRAIGHT_LINE_PRESENTATION_RUN_ID,
            result_id=None,
            case_id=STRAIGHT_LINE_PRESENTATION_CASE_ID,
            parent_simulation_id=SUPERCELLS_REFERENCE_SIMULATION_ID,
            reference_simulation_id=SUPERCELLS_REFERENCE_SIMULATION_ID,
            parent_eligibility_state="unknown",
            run=runs.get(STRAIGHT_LINE_PRESENTATION_RUN_ID),
            result=None,
            question="How does hodograph curvature change storm organization?",
            differences=[
                LifecycleDifference(
                    category="atmospheric",
                    label="Hodograph geometry",
                    before="Quarter-circle",
                    after="Straight-line",
                )
            ],
        ),
    ]
    known_run_ids = {source.run_id for source in sources}
    variation_sources: dict[str, list[WorldLifecycleSource]] = defaultdict(list)
    for run in storage.runs:
        if run.run_id in known_run_ids:
            continue
        source = _variation_source(run, result_by_run.get(run.run_id))
        if source is not None:
            variation_sources[source.simulation_id].append(source)
    for candidates in variation_sources.values():
        accepted = [source for source in candidates if source.accepted_backing]
        if len(accepted) > 1:
            selected = sorted(
                accepted, key=lambda source: (source.created_at or "", source.run_id)
            )[0]
            selected.availability_state = "conflict"
            selected.inspectability_state = "conflict"
            selected.parent_eligibility_state = "ineligible"
            selected.trust_state = "failed"
            selected.caveats.append("Multiple attempts claim accepted backing.")
        elif accepted:
            selected = accepted[0]
        else:
            available = [
                source for source in candidates if source.availability_state == "available"
            ]
            selected = (
                sorted(
                    available,
                    key=lambda source: (source.created_at or "", source.run_id),
                )[0]
                if available
                else sorted(
                    candidates,
                    key=lambda source: (source.created_at or "", source.run_id),
                )[-1]
            )
            selected.accepted_backing = bool(available)
        sources.append(selected)
    warnings: list[str] = []
    return sources, warnings


def _known_source(
    *,
    owner_id: WorldOwnerId,
    simulation_id: str,
    display_name: str,
    role: str,
    run_id: str,
    result_id: str | None,
    case_id: str | None,
    parent_simulation_id: str | None,
    reference_simulation_id: str | None,
    parent_eligibility_state: Literal["eligible", "ineligible", "unknown"],
    run: RunStorageEntry | None,
    result: ResultCard | None,
    question: str | None = None,
    differences: list[LifecycleDifference] | None = None,
    authored_caveats: list[str] | None = None,
) -> WorldLifecycleSource:
    availability, inspectability = _source_availability(run, expected_case_id=case_id)
    caveats = [
        *(authored_caveats or []),
        *(run.run_caveats if run is not None else []),
        *(result.caveats if result is not None else []),
    ]
    return WorldLifecycleSource(
        owner_id=owner_id,
        simulation_id=simulation_id,
        display_name=display_name,
        role=role,
        run_id=run_id,
        result_id=result_id if result is not None else None,
        case_id=case_id or (run.scenario_id if run is not None else None),
        recipe_id=(
            run.recipe_id if run is not None else result.recipe_id if result is not None else None
        ),
        parent_simulation_id=parent_simulation_id,
        reference_simulation_id=reference_simulation_id,
        question=question or (run.physical_question if run is not None else None),
        differences=differences or [],
        availability_state=availability,
        inspectability_state=inspectability,
        parent_eligibility_state=(
            parent_eligibility_state if availability == "available" else "unknown"
        ),
        trust_state=_source_trust(run, result, caveats),
        caveats=list(dict.fromkeys(caveats)),
        created_at=run.created_at if run is not None else None,
        completed_at=run.updated_at if run is not None else None,
    )


def _variation_source(
    run: RunStorageEntry,
    result: ResultCard | None,
) -> WorldLifecycleSource | None:
    configuration = run.run_configuration or {}
    owner = _string(configuration.get("cloud_world_id"))
    simulation_id = _string(configuration.get("simulation_id"))
    display_name = _string(configuration.get("simulation_display_name"))
    if not _is_current_world_variation(
        run,
        owner=owner,
        simulation_id=simulation_id,
        display_name=display_name,
    ):
        return None
    assert simulation_id is not None
    assert display_name is not None
    parent_id = _string(configuration.get("parent_simulation_id"))
    reference_id = _string(configuration.get("reference_simulation_id"))
    envelope = configuration.get("variation_envelope")
    envelope_record = envelope if isinstance(envelope, dict) else {}
    attempts = envelope_record.get("attempts")
    accepted_backing = bool(
        isinstance(attempts, list)
        and any(
            isinstance(attempt, dict)
            and attempt.get("run_id") == run.run_id
            and attempt.get("accepted_backing") is True
            for attempt in attempts
        )
    )
    availability, inspectability = _source_availability(run, expected_case_id=None)
    caveats = [*run.run_caveats, *(result.caveats if result is not None else [])]
    differences = _configuration_differences(configuration.get("configuration_difference"))
    return WorldLifecycleSource(
        owner_id=cast(WorldOwnerId, owner),
        simulation_id=simulation_id,
        display_name=display_name,
        role="variation",
        run_id=run.run_id,
        result_id=result.result_id if result is not None else None,
        case_id=run.scenario_id,
        recipe_id=run.recipe_id or _string(envelope_record.get("recipe_id")),
        recipe_version=_string(envelope_record.get("recipe_contract_version")),
        parent_simulation_id=parent_id,
        reference_simulation_id=reference_id,
        question=_string(configuration.get("user_question")) or run.physical_question,
        differences=differences,
        accepted_backing=accepted_backing,
        availability_state=availability,
        inspectability_state=inspectability,
        parent_eligibility_state=(
            "eligible"
            if envelope_record.get("parent_eligible") is True
            else "ineligible"
            if availability == "available"
            else "unknown"
        ),
        trust_state=_source_trust(run, result, caveats),
        caveats=list(dict.fromkeys(caveats)),
        created_at=run.created_at,
        completed_at=run.updated_at,
    )


def _is_current_world_variation(
    run: RunStorageEntry,
    *,
    owner: str | None,
    simulation_id: str | None,
    display_name: str | None,
) -> bool:
    configuration = run.run_configuration or {}
    if owner == "mountain_waves":
        world_payload_valid = isinstance(configuration.get("mountain_waves_configuration"), dict)
        case_valid = run.scenario_id in {VARIATION_CASE_ID, LEGACY_VARIATION_CASE_ID}
        reference_valid = _string(configuration.get("reference_simulation_id")) in {
            DRY_SIMULATION_ID,
            MOIST_SIMULATION_ID,
        }
    elif owner == "trade_cumulus":
        world_payload_valid = isinstance(configuration.get("trade_cumulus_configuration"), dict)
        case_valid = run.scenario_id == "trade_cumulus_recipe_variation_v1"
        reference_valid = (
            _string(configuration.get("reference_simulation_id")) == REFERENCE_SIMULATION_ID
        )
    else:
        return False
    return (
        case_valid
        and bool(simulation_id)
        and bool(display_name)
        and bool(_string(configuration.get("parent_simulation_id")))
        and reference_valid
        and world_payload_valid
        and isinstance(configuration.get("configuration_difference"), dict)
        and bool(configuration.get("generated_input_sha256"))
        and isinstance(configuration.get("generated_input_sha256"), dict)
    )


def _source_availability(
    run: RunStorageEntry | None,
    *,
    expected_case_id: str | None,
) -> tuple[
    Literal["available", "missing", "unavailable", "conflict"],
    Literal["passed", "failed", "missing", "conflict"],
]:
    if run is None or run.category == "missing_manifest":
        return "missing", "missing"
    if run.category == "malformed_manifest":
        return "conflict", "conflict"
    if expected_case_id is not None and run.scenario_id != expected_case_id:
        return "conflict", "conflict"
    if run.validation_status == "failed":
        return "conflict", "conflict"
    if (
        run.lifecycle_state == "completed"
        and run.output_artifact_count > 0
        and run.validation_status in {"valid", "needs_review"}
        and bool(run.manual_validation_status)
    ):
        return "available", "passed"
    if run.lifecycle_state in {"failed", "canceled"}:
        return "unavailable", "failed"
    return "unavailable", "failed"


def _source_trust(
    run: RunStorageEntry | None,
    result: ResultCard | None,
    caveats: list[str],
) -> TrustState:
    if result is not None:
        state = result.runtime_integrity.state
        if state == "trusted":
            return "caveated" if caveats else "trusted"
        if state == "caveated":
            return "caveated"
        if state == "failed":
            return "failed"
    if run is None:
        return "unavailable"
    if run.validation_status == "failed":
        return "failed"
    if run.validation_status in {"valid", "needs_review"} and run.manual_validation_status:
        return "caveated" if caveats or run.validation_status == "needs_review" else "trusted"
    return "unassessed"


def _trade_moisture_difference(
    baseline: RunStorageEntry | None,
    variation: RunStorageEntry | None,
) -> list[LifecycleDifference]:
    before = (
        (baseline.run_configuration or {}).get("surface_moisture_flux_g_g_m_s")
        if baseline is not None
        else None
    )
    after = (
        (variation.run_configuration or {}).get("surface_moisture_flux_g_g_m_s")
        if variation is not None
        else None
    )
    if not isinstance(before, int | float) or not isinstance(after, int | float):
        return []
    return [
        LifecycleDifference(
            category="atmospheric",
            label="Surface moisture supply",
            before=float(before) * 1_000,
            after=float(after) * 1_000,
            units="g/kg m/s",
        )
    ]


def _configuration_differences(value: object) -> list[LifecycleDifference]:
    if not isinstance(value, dict):
        return []
    differences: list[LifecycleDifference] = []
    for category, items in value.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            differences.append(
                LifecycleDifference(
                    category=str(category),
                    label=str(item.get("label") or category),
                    before=item.get("before"),
                    after=item.get("after"),
                    units=_string(item.get("units")),
                )
            )
    return differences


def _declared_world_source(
    run: RunStorageEntry,
    sources: dict[tuple[WorldOwnerId, str], WorldLifecycleSource],
) -> WorldLifecycleSource | None:
    configuration = run.run_configuration or {}
    owner = _string(configuration.get("cloud_world_id"))
    simulation_id = _string(configuration.get("simulation_id"))
    if owner not in _WORLD_OWNER_IDS or not simulation_id:
        return None
    source = sources.get((owner, simulation_id))  # type: ignore[arg-type]
    if source is None:
        return None
    return source


def _dependency_index(
    settings: CloudChamberSettings,
) -> dict[tuple[str, str], list[LifecycleDependency]]:
    index: dict[tuple[str, str], list[LifecycleDependency]] = defaultdict(list)
    state_root = settings.runtime_home.expanduser() / "explore-state"
    if state_root.is_dir():
        for path in sorted(state_root.glob("*/*.json")):
            payload = _read_json(path)
            world_id = _string(payload.get("world_id"))
            simulation_id = _string(payload.get("simulation_id"))
            if not world_id or not simulation_id:
                continue
            saved_views = payload.get("saved_views")
            if not isinstance(saved_views, list):
                continue
            for item in saved_views:
                if not isinstance(item, dict):
                    continue
                saved_view_id = _string(item.get("saved_view_id"))
                title = _string(item.get("title"))
                if saved_view_id and title:
                    index[(world_id, simulation_id)].append(
                        LifecycleDependency(
                            kind="saved_view",
                            dependency_id=saved_view_id,
                            title=title,
                            relationship="Saved View",
                        )
                    )
    comparison_root = settings.runtime_home.expanduser() / "saved-comparisons"
    if comparison_root.is_dir():
        for path in sorted(comparison_root.glob("*.json")):
            payload = _read_json(path)
            world_id = _string(payload.get("world_id"))
            records = payload.get("saved_comparisons")
            if not world_id or not isinstance(records, list):
                continue
            for item in records:
                if not isinstance(item, dict):
                    continue
                comparison_id = _string(item.get("saved_comparison_id"))
                title = _string(item.get("title"))
                workspace = item.get("workspace")
                if not comparison_id or not title or not isinstance(workspace, dict):
                    continue
                for side in ("left", "right"):
                    simulation_id = _string(workspace.get(f"{side}_simulation_id"))
                    if simulation_id:
                        index[(world_id, simulation_id)].append(
                            LifecycleDependency(
                                kind="saved_comparison",
                                dependency_id=comparison_id,
                                title=title,
                                relationship=f"Saved Comparison ({side})",
                            )
                        )
    return dict(index)


def _record_key(
    run_id: str,
    result: ResultCard | None,
    source: WorldLifecycleSource | None,
) -> str:
    if source is not None:
        return f"simulation:{source.owner_id}:{source.simulation_id}"
    stable_id = result.run_id if result is not None else run_id
    return f"experiment:{stable_id}"


def _experiment_owner(
    result: ResultCard | None,
    runs: list[RunStorageEntry],
) -> OwnerId:
    if result is not None and (
        result.observed_sounding is not None
        or result.input_source
        in {
            "observed_sounding",
            "uploaded_igra_text",
            "local_igra_period_of_record_cache",
        }
    ):
        return "fun_with_soundings"
    if any(
        run.has_observed_sounding
        or run.input_source
        in {
            "observed_sounding",
            "uploaded_igra_text",
            "local_igra_period_of_record_cache",
        }
        for run in runs
    ):
        return "fun_with_soundings"
    return "legacy_unassigned"


def _attempt_relationship(
    configuration: dict[str, object],
    run_id: str,
    source: WorldLifecycleSource | None,
) -> AttemptRelationship:
    declared = _string(configuration.get("attempt_relationship"))
    if declared in _ATTEMPT_RELATIONSHIPS:
        return declared  # type: ignore[return-value]
    if source is not None and run_id != source.run_id:
        return "later_backing_candidate"
    return "initial"


def _queue_state_from_lifecycle(run: RunStorageEntry) -> str | None:
    if run.lifecycle_state in {"queued", "running"}:
        return run.lifecycle_state
    return None


def _trust_state(
    result: ResultCard | None,
    source: WorldLifecycleSource | None,
) -> TrustState:
    if source is not None and source.trust_state != "unassessed":
        return source.trust_state
    if result is None:
        return "unassessed"
    state = result.runtime_integrity.state
    if state == "trusted":
        return "trusted"
    if state == "caveated":
        return "caveated"
    if state == "failed":
        return "failed"
    return "unassessed"


def _caveats(
    result: ResultCard | None,
    source: WorldLifecycleSource | None,
    runs: list[RunStorageEntry],
) -> list[str]:
    values: list[str] = []
    if source is not None:
        values.extend(source.caveats)
    if result is not None:
        values.extend(result.caveats)
        values.extend(result.runtime_integrity.caveats)
    if source is None and any(
        _string((run.run_configuration or {}).get("cloud_world_id")) for run in runs
    ):
        values.append(
            "A World identity was claimed, but current stable World/Simulation evidence "
            "did not verify ownership."
        )
    return list(dict.fromkeys(value for value in values if value))


def _attempt_failure_detail(attempts: list[LifecycleAttempt]) -> str:
    for attempt in reversed(attempts):
        if attempt.failure_reason:
            return attempt.failure_reason
    return "The latest technical attempt needs review."


def _run_display_name(runs: list[RunStorageEntry], key: str) -> str:
    for run in runs:
        if run.scenario_name:
            return run.scenario_name
        configuration = run.run_configuration or {}
        configured = _string(configuration.get("simulation_display_name")) or _string(
            configuration.get("experiment_display_name")
        )
        if configured:
            return configured
        if run.scenario_id:
            return _humanize(run.scenario_id)
    return _humanize(key.split(":", 1)[-1])


def _run_question(runs: list[RunStorageEntry]) -> str | None:
    for run in runs:
        configuration = run.run_configuration or {}
        question = _string(configuration.get("user_question")) or _string(
            configuration.get("physical_question")
        )
        if question:
            return question
    return None


def _run_id(runs: list[RunStorageEntry]) -> str | None:
    return runs[0].run_id if runs else None


def _run_case_id(runs: list[RunStorageEntry]) -> str | None:
    return runs[0].scenario_id if runs else None


def _run_recipe_id(runs: list[RunStorageEntry]) -> str | None:
    for run in runs:
        value = _string((run.run_configuration or {}).get("recipe_id"))
        if value:
            return value
    return None


def _manifest_tags(runs: list[RunStorageEntry]) -> list[str]:
    for run in runs:
        if run.user_tags:
            return run.user_tags
    return []


def _manifest_notes(runs: list[RunStorageEntry]) -> str | None:
    for run in runs:
        if run.user_notes:
            return run.user_notes
    return None


def _earliest(values: list[str | None]) -> str | None:
    populated = [value for value in values if value]
    return min(populated) if populated else None


def _latest(values: list[str | None]) -> str | None:
    populated = [value for value in values if value]
    return max(populated) if populated else None


def _is_recent(value: str | None, *, now: datetime) -> bool:
    if value is None:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed >= now - timedelta(days=14)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _string(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _humanize(value: str) -> str:
    return (
        value.replace("_", " ")
        .replace("-", " ")
        .strip()
        .title()
        .replace("Cm1", "CM1")
        .replace("Bomex", "BOMEX")
        .replace("Quarter Circle", "Quarter-Circle")
        .replace("Straight Line", "Straight-Line")
        .replace("R21 1", "r21.1")
        .replace(" V0", " v0")
        .replace(" V1", " v1")
    )
