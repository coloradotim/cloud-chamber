from __future__ import annotations

from datetime import UTC, datetime

from cloud_chamber.lifecycle import (
    LifecycleDifference,
    WorldLifecycleSource,
    _humanize,
    _variation_source,
    build_lifecycle_projection,
)
from cloud_chamber.local_run_queue import RunQueueEntry, RunQueueState
from cloud_chamber.mountain_waves_variations import VARIATION_CASE_ID
from cloud_chamber.mountain_waves_world import MOIST_SIMULATION_ID
from cloud_chamber.result_cards import ResultCard
from cloud_chamber.runtime_integrity import RuntimeIntegrity
from cloud_chamber.runtime_storage import RunStorageEntry, RuntimeStorageInventory

NOW = datetime(2026, 7, 27, 18, 0, tzinfo=UTC)


def test_humanize_preserves_common_scientific_identifiers() -> None:
    assert (
        _humanize("cm1_r21_1_straight_line_supercell_characterization_v1")
        == "CM1 r21.1 Straight-Line Supercell Characterization v1"
    )


def inventory(*runs: RunStorageEntry) -> RuntimeStorageInventory:
    return RuntimeStorageInventory(
        runtime_home="/runtime",
        runs_directory="/runtime/runs",
        total_size_bytes=sum(run.size_bytes for run in runs),
        warning_threshold_bytes=50 * 1024**3,
        above_warning_threshold=False,
        runs=list(runs),
        largest_runs=sorted(runs, key=lambda run: run.size_bytes, reverse=True),
    )


def run(
    run_id: str,
    state: str,
    *,
    category: str | None = None,
    output_count: int = 0,
    configuration: dict[str, object] | None = None,
    manifest: bool = True,
    validation: str = "valid",
) -> RunStorageEntry:
    return RunStorageEntry(
        run_id=run_id,
        scenario_id="test-case",
        lifecycle_state=state,
        validation_status=validation,
        product_state=(
            "completed_cm1_result" if state == "completed" else "packaged_dry_run_output"
        ),
        run_configuration=configuration or {},
        created_at="2026-07-27T16:00:00+00:00",
        updated_at="2026-07-27T17:00:00+00:00",
        output_artifact_count=output_count,
        output_summary={"netcdf_paths": output_count},
        size_bytes=1_024,
        path=f"/runtime/runs/{run_id}",
        category=category
        or (
            "completed_with_output"
            if state == "completed" and output_count
            else "dry_run_only"
            if state == "packaged"
            else state
        ),
        manifest_path=f"/runtime/runs/{run_id}/run_manifest.json" if manifest else None,
    )


def queue(*entries: RunQueueEntry) -> RunQueueState:
    return RunQueueState(
        entries=list(entries),
        active_run_id=next(
            (entry.run_id for entry in entries if entry.state == "running"),
            None,
        ),
        queued_count=sum(entry.state == "queued" for entry in entries),
        updated_at="2026-07-27T17:30:00+00:00",
    )


def queue_entry(run_id: str, state: str, *, error: str | None = None) -> RunQueueEntry:
    return RunQueueEntry(
        run_id=run_id,
        manifest_path=f"/runtime/runs/{run_id}/run_manifest.json",
        state=state,
        queued_at="2026-07-27T16:30:00+00:00",
        updated_at="2026-07-27T17:30:00+00:00",
        started_at="2026-07-27T17:00:00+00:00" if state == "running" else None,
        error=error,
    )


def world_source(
    *,
    state: str = "available",
    trust: str = "trusted",
    parent_eligible: str = "eligible",
    run_id: str = "attempt-initial",
) -> WorldLifecycleSource:
    return WorldLifecycleSource(
        owner_id="mountain_waves",
        simulation_id="mountain_waves_broader_boulder_ridge",
        display_name="Broader Boulder Ridge",
        role="variation",
        run_id=run_id,
        case_id="mountain-wave-case",
        recipe_id="boulder_moist_v1",
        recipe_version="1",
        parent_simulation_id="mountain_waves_boulder_moist_reference",
        reference_simulation_id="mountain_waves_boulder_moist_reference",
        question="How does a broader ridge change the wave cloud?",
        differences=[
            LifecycleDifference(
                category="terrain",
                label="Ridge half-width",
                before=10_000,
                after=15_000,
                units="m",
            )
        ],
        availability_state=state,  # type: ignore[arg-type]
        inspectability_state=(
            "passed" if state == "available" else "conflict" if state == "conflict" else "missing"
        ),
        parent_eligibility_state=parent_eligible,  # type: ignore[arg-type]
        trust_state=trust,  # type: ignore[arg-type]
        caveats=(
            ["Finite underflow is retained as a visible caveat."] if trust == "caveated" else []
        ),
        created_at="2026-07-27T16:00:00+00:00",
        completed_at="2026-07-27T17:00:00+00:00",
    )


def result_card(
    *,
    run_id: str,
    result_id: str,
    observed: bool,
    trust: str = "trusted",
) -> ResultCard:
    return ResultCard.model_construct(
        result_id=result_id,
        run_id=run_id,
        name="Observed Surface-Forced Evolution — Topeka",
        tags=["topeka", "sounding"],
        notes="Retained experiment note.",
        scenario_id="observed-surface-forced-evolution-v0",
        physical_question="Will this observed atmosphere form deep cloud?",
        observed_sounding={"station_id": "USM00072456"} if observed else None,
        run_recipe="observed_surface_forced_evolution" if observed else None,
        recipe_id="observed_surface_forced_evolution_v0" if observed else None,
        input_source="local_igra_period_of_record_cache" if observed else "generated_reference",
        caveats=[],
        runtime_integrity=RuntimeIntegrity(
            assessed=True,
            state=trust,  # type: ignore[arg-type]
            reason="fixture",
            summary="Fixture integrity.",
        ),
        created_at=NOW,
        updated_at=NOW,
    )


def test_projection_keeps_lifecycle_facts_distinct_and_groups_activity() -> None:
    projection = build_lifecycle_projection(
        storage=inventory(
            run("packaged", "packaged"),
            run("queued", "queued"),
            run("running", "running"),
            run("awaiting-ingest", "completed", output_count=2),
            run("failed", "failed", category="failed"),
            run("cancelled", "canceled", category="canceled"),
            run("missing-output", "completed", category="completed_no_output"),
        ),
        results=[],
        queue=queue(
            queue_entry("queued", "queued"),
            queue_entry("running", "running"),
            queue_entry("failed", "failed", error="CM1 exited 2"),
            queue_entry("cancelled", "canceled"),
        ),
        world_sources=[],
        now=NOW,
    )

    by_run = {record.attempts[0].run_id: record for record in projection.records if record.attempts}
    assert by_run["packaged"].activity_group == "ready_to_run"
    assert by_run["packaged"].facts.package == "present"
    assert by_run["packaged"].facts.process == "pending"
    assert by_run["queued"].activity_group == "queued"
    assert by_run["queued"].facts.queue == "pending"
    assert by_run["running"].activity_group == "running"
    assert by_run["awaiting-ingest"].activity_group == "awaiting_validation_or_ingest"
    assert by_run["awaiting-ingest"].facts.expected_output == "present"
    assert by_run["awaiting-ingest"].facts.ingest == "pending"
    assert by_run["failed"].activity_group == "needs_attention"
    assert by_run["failed"].lifecycle_detail == "CM1 exited 2"
    assert by_run["cancelled"].activity_group == "needs_attention"
    assert by_run["missing-output"].facts.expected_output == "missing"


def test_projection_does_not_present_an_unmeasured_run_size_as_zero() -> None:
    unmeasured = run("unmeasured", "completed", output_count=2).model_copy(update={"size_bytes": 0})

    projection = build_lifecycle_projection(
        storage=inventory(unmeasured),
        results=[],
        queue=queue(),
        world_sources=[],
        now=NOW,
    )

    assert projection.records[0].attempts[0].size_bytes is None
    assert projection.records[0].size_bytes is None


def test_projection_preserves_all_attempt_relationships_under_one_simulation() -> None:
    source = world_source()
    relationships = [
        "initial",
        "unchanged_retry",
        "checkpoint_restart",
        "alternate_observation_attempt",
        "extension",
        "later_backing_candidate",
    ]
    runs = [
        run(
            f"attempt-{relationship}",
            "completed",
            output_count=2,
            configuration={
                "cloud_world_id": "mountain_waves",
                "simulation_id": source.simulation_id,
                "attempt_relationship": relationship,
            },
        )
        for relationship in relationships
    ]
    source = source.model_copy(update={"run_id": runs[0].run_id})

    projection = build_lifecycle_projection(
        storage=inventory(*runs),
        results=[],
        queue=queue(),
        world_sources=[source],
        now=NOW,
    )

    assert len(projection.records) == 1
    record = projection.records[0]
    assert record.record_kind == "simulation"
    assert record.owner_id == "mountain_waves"
    assert record.simulation_id == source.simulation_id
    assert {attempt.relationship for attempt in record.attempts} == set(relationships)
    assert sum(attempt.accepted_backing for attempt in record.attempts) == 1
    assert record.parent_simulation_id == "mountain_waves_boulder_moist_reference"
    assert record.differences[0].after == 15_000


def test_available_caveated_and_parent_eligibility_remain_separate() -> None:
    source = world_source(trust="caveated", parent_eligible="ineligible")
    projection = build_lifecycle_projection(
        storage=inventory(run(source.run_id, "completed", output_count=2)),
        results=[],
        queue=queue(),
        world_sources=[source],
        now=NOW,
    )

    record = projection.records[0]
    assert record.lifecycle_label == "Available with caveats"
    assert record.facts.simulation_availability == "present"
    assert record.facts.world_inspectability == "passed"
    assert record.facts.parent_eligibility == "ineligible"
    assert record.trust_state == "caveated"
    assert [action.kind for action in record.actions] == ["explore", "compare_parent"]


def test_conflicting_and_missing_world_output_fail_closed() -> None:
    conflict = world_source(state="conflict", run_id="conflict")
    missing = world_source(state="missing", run_id="missing")
    projection = build_lifecycle_projection(
        storage=inventory(),
        results=[],
        queue=queue(),
        world_sources=[
            conflict,
            missing.model_copy(update={"simulation_id": "missing-simulation"}),
        ],
        now=NOW,
    )
    by_id = {record.simulation_id: record for record in projection.records}

    assert by_id[conflict.simulation_id].activity_group == "needs_attention"
    assert by_id[conflict.simulation_id].facts.simulation_availability == "conflict"
    assert by_id["missing-simulation"].facts.retained_assets == "missing"
    assert by_id["missing-simulation"].facts.simulation_availability == "missing"
    assert all(action.kind != "explore" for action in by_id["missing-simulation"].actions)


def test_only_observed_result_is_soundings_owned_and_other_claims_fail_closed() -> None:
    observed_run = run("observed", "completed", output_count=2)
    ambiguous_run = run(
        "ambiguous",
        "completed",
        output_count=2,
        configuration={
            "cloud_world_id": "trade_cumulus",
            "simulation_id": "unknown-simulation",
            "simulation_display_name": "Self-declared World simulation",
        },
    )
    technical_run = run("technical", "completed", output_count=2).model_copy(
        update={"input_source": "CM1_r21.1_analytic_isnd5_iwnd2_iinit1"}
    )
    technical_result = result_card(
        run_id="technical",
        result_id="result-technical",
        observed=False,
    ).model_copy(
        update={
            "name": "CM1 r21.1 Supercell characterization",
            "recipe_id": "supercell_characterization_v1",
            "run_recipe": "supercell_characterization",
            "input_source": "CM1_r21.1_analytic_isnd5_iwnd2_iinit1",
        }
    )
    projection = build_lifecycle_projection(
        storage=inventory(observed_run, ambiguous_run, technical_run),
        results=[
            result_card(run_id="observed", result_id="result-observed", observed=True),
            result_card(run_id="ambiguous", result_id="result-ambiguous", observed=False),
            technical_result,
        ],
        queue=queue(),
        world_sources=[],
        now=NOW,
    )
    by_run = {record.attempts[0].run_id: record for record in projection.records}

    assert by_run["observed"].owner_id == "fun_with_soundings"
    assert by_run["observed"].record_kind == "experiment"
    assert by_run["observed"].lifecycle_label == "Ready to inspect"
    assert by_run["observed"].tags == ["topeka", "sounding"]
    assert by_run["ambiguous"].owner_id == "legacy_unassigned"
    assert "did not verify ownership" in by_run["ambiguous"].caveats[0]
    assert by_run["technical"].owner_id == "legacy_unassigned"


def test_dynamic_world_ownership_requires_current_mountain_waves_contract() -> None:
    claimed = run(
        "claimed",
        "completed",
        output_count=2,
        configuration={
            "cloud_world_id": "mountain_waves",
            "simulation_id": "claimed-simulation",
            "simulation_display_name": "Claimed Simulation",
        },
    )
    current = run(
        "current-variation",
        "completed",
        output_count=2,
        configuration={
            "cloud_world_id": "mountain_waves",
            "simulation_id": "mountain-waves-broader-ridge",
            "simulation_display_name": "Broader Ridge",
            "parent_simulation_id": MOIST_SIMULATION_ID,
            "reference_simulation_id": MOIST_SIMULATION_ID,
            "mountain_waves_configuration": {"terrain": {"half_width_m": 15_000}},
            "configuration_difference": {
                "terrain": [
                    {
                        "label": "Ridge half-width",
                        "before": 10_000,
                        "after": 15_000,
                        "units": "m",
                    }
                ]
            },
            "generated_input_sha256": {"namelist.input": "abc123"},
        },
    ).model_copy(update={"scenario_id": VARIATION_CASE_ID})

    assert _variation_source(claimed, None) is None
    source = _variation_source(current, None)
    assert source is not None
    assert source.owner_id == "mountain_waves"
    assert source.simulation_id == "mountain-waves-broader-ridge"
    assert source.differences[0].label == "Ridge half-width"


def test_projection_is_stable_across_reload_for_same_retained_sources() -> None:
    source = world_source()
    storage = inventory(run(source.run_id, "completed", output_count=2))
    first = build_lifecycle_projection(
        storage=storage,
        results=[],
        queue=queue(),
        world_sources=[source],
        now=NOW,
    )
    second = build_lifecycle_projection(
        storage=storage,
        results=[],
        queue=queue(),
        world_sources=[source],
        now=NOW,
    )

    assert first == second
