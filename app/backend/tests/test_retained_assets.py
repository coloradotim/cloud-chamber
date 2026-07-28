from pathlib import Path
from typing import Literal

from cloud_chamber.lifecycle import (
    LifecycleAttempt,
    LifecycleDependency,
    LifecycleFacts,
    LifecycleProjection,
    LifecycleRecord,
    OwnerId,
)
from cloud_chamber.retained_assets import retained_asset_inventory
from cloud_chamber.settings import CloudChamberSettings


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=tmp_path,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "cache",
        log_dir=tmp_path / "logs",
    )


def facts(*, inspectable: bool = True) -> LifecycleFacts:
    return LifecycleFacts(
        scientific_work="passed",
        package="passed",
        attempt="passed",
        queue="not_applicable",
        process="passed",
        expected_output="passed",
        technical_integrity="passed",
        ingest="passed",
        world_inspectability="passed" if inspectable else "failed",
        simulation_availability="passed" if inspectable else "missing",
        parent_eligibility="eligible",
        retained_assets="present" if inspectable else "missing",
    )


def record(
    *,
    run_id: str,
    simulation_id: str,
    display_name: str,
    owner_id: OwnerId = "trade_cumulus",
    accepted: bool = True,
    retained_state: Literal["retained", "missing", "conflict", "unknown"] = "retained",
) -> LifecycleRecord:
    return LifecycleRecord(
        record_id=f"simulation:{owner_id}:{simulation_id}",
        record_kind="simulation",
        owner_id=owner_id,
        owner_label={
            "trade_cumulus": "Trade Cumulus",
            "mountain_waves": "Mountain Waves",
            "supercells": "Supercells",
            "fun_with_soundings": "Fun With Soundings",
            "legacy_unassigned": "Legacy / unassigned",
        }[owner_id],
        simulation_id=simulation_id,
        world_id=owner_id,
        reference_simulation_id=simulation_id,
        display_name=display_name,
        role="reference" if accepted else "variation",
        attempts=[
            LifecycleAttempt(
                attempt_id=run_id,
                run_id=run_id,
                relationship="initial",
                accepted_backing=accepted,
                manifest_path=str(Path("/runtime/runs") / run_id / "run_manifest.json"),
                lifecycle_state="completed",
                validation_status="valid",
                retained_state=retained_state,
                result_id=f"result-{run_id}",
            )
        ],
        facts=facts(inspectable=retained_state == "retained"),
        trust_state="trusted" if retained_state == "retained" else "unavailable",
        lifecycle_label="Available" if retained_state == "retained" else "Missing",
        lifecycle_detail="Fixture lifecycle state.",
        dependencies=[
            LifecycleDependency(
                kind="saved_view",
                dependency_id=f"view-{run_id}",
                title="Saved cloud view",
                relationship="Saved View",
            )
        ],
    )


def test_inventory_projects_protected_output_components_and_dependencies(
    tmp_path: Path,
) -> None:
    run_id = "trade-cumulus-presentation-v1-baseline-20260722"
    run_dir = tmp_path / "runs" / run_id
    (run_dir / "logs").mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text("{}")
    (run_dir / "namelist.input").write_text("&param0\n/")
    (run_dir / "cm1out_000001.nc").write_bytes(b"x" * 128)
    (run_dir / "logs" / "stdout.log").write_text("complete")
    projection = LifecycleProjection(
        generated_at="2026-07-28T00:00:00+00:00",
        records=[
            record(
                run_id=run_id,
                simulation_id="trade_cumulus_canonical_bomex",
                display_name="Canonical BOMEX Baseline",
            )
        ],
    )

    inventory = retained_asset_inventory(
        fake_settings(tmp_path),
        lifecycle=projection,
        refresh=True,
    )

    asset = next(item for item in inventory.assets if item.asset_id == f"run:{run_id}")
    assert asset.owner_id == "trade_cumulus"
    assert asset.asset_class == "simulation_output"
    assert asset.protection_state == "system_protected"
    assert asset.accepted_backing == "accepted"
    assert asset.required_for_explore is True
    assert asset.required_for_compare is False
    assert {item.component for item in asset.components} >= {
        "model output",
        "logs",
        "package inputs",
    }
    assert any(item.kind == "saved_view" for item in asset.dependencies)
    assert any(item.kind == "world_inventory" for item in asset.dependencies)
    assert inventory.system_protected_bytes == asset.size_bytes
    assert inventory.free_space_bytes > 0


def test_inventory_preserves_missing_asset_and_uses_persistent_cache(tmp_path: Path) -> None:
    projection = LifecycleProjection(
        generated_at="2026-07-28T00:00:00+00:00",
        records=[
            record(
                run_id="missing-boulder",
                simulation_id="mountain_waves_boulder_moist_reference",
                display_name="Boulder Windstorm",
                owner_id="mountain_waves",
                retained_state="missing",
            )
        ],
    )
    settings = fake_settings(tmp_path)

    first = retained_asset_inventory(settings, lifecycle=projection, refresh=True)
    second = retained_asset_inventory(settings, lifecycle=projection)

    asset = next(item for item in first.assets if item.run_id == "missing-boulder")
    assert asset.availability_state == "missing"
    assert asset.size_bytes is None
    assert asset.protection_state == "system_protected"
    assert first.uncounted_asset_count == 1
    assert first.performance.cache_hit is False
    assert second.performance.cache_hit is True
    assert second.performance.scanned_file_count == 0


def test_inventory_distinguishes_user_package_and_source_assets(tmp_path: Path) -> None:
    run_id = "mw-user-package"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text("{}")
    (run_dir / "namelist.input").write_text("&param0\n/")
    source_dir = tmp_path / "cache" / "igra"
    source_dir.mkdir(parents=True)
    (source_dir / "station.txt").write_text("observed atmosphere")
    user_record = record(
        run_id=run_id,
        simulation_id="mountain_waves_user_variation",
        display_name="User Mountain Wave",
        owner_id="mountain_waves",
        accepted=False,
    )
    user_record.attempts[0].lifecycle_state = "packaged"
    projection = LifecycleProjection(
        generated_at="2026-07-28T00:00:00+00:00",
        records=[user_record],
    )

    inventory = retained_asset_inventory(
        fake_settings(tmp_path),
        lifecycle=projection,
        refresh=True,
    )

    package = next(item for item in inventory.assets if item.run_id == run_id)
    source = next(item for item in inventory.assets if item.asset_id == "runtime:cache")
    assert package.asset_class == "package_logs"
    assert package.protection_state == "ordinary"
    assert package.repairability_state == "unknown"
    assert source.asset_class == "source_asset"
    assert source.owner_id == "fun_with_soundings"


def test_inventory_distinguishes_user_experiment_and_attempt_states(
    tmp_path: Path,
) -> None:
    user = record(
        run_id="user-simulation-accepted",
        simulation_id="trade_cumulus_user_variation",
        display_name="User Trade Cumulus Variation",
    )
    user.attempts[0].manifest_path = str(
        tmp_path / "runs" / "user-simulation-accepted" / "run_manifest.json"
    )
    user.dependencies.append(
        LifecycleDependency(
            kind="saved_comparison",
            dependency_id="comparison-user-reference",
            title="User variation versus reference",
            relationship="Left Simulation",
        )
    )
    user.attempts.append(
        LifecycleAttempt(
            attempt_id="user-simulation-alternate",
            run_id="user-simulation-alternate",
            relationship="later_backing_candidate",
            accepted_backing=False,
            lifecycle_state="completed",
            validation_status="valid",
            retained_state="retained",
        )
    )

    experiment = record(
        run_id="sounding-experiment",
        simulation_id="temporary-experiment-placeholder",
        display_name="Observed Sounding Experiment",
        owner_id="fun_with_soundings",
    )
    experiment.record_id = "experiment:fun_with_soundings:observed-sounding"
    experiment.record_kind = "experiment"
    experiment.experiment_id = "observed-sounding"
    experiment.simulation_id = None
    experiment.world_id = None
    experiment.reference_simulation_id = None

    failed = record(
        run_id="failed-attempt",
        simulation_id="trade_cumulus_failed_attempt",
        display_name="Failed Trade Cumulus Attempt",
        accepted=False,
    )
    failed.attempts[0].validation_status = "failed"

    cancelled = record(
        run_id="cancelled-attempt",
        simulation_id="trade_cumulus_cancelled_attempt",
        display_name="Cancelled Trade Cumulus Attempt",
        accepted=False,
    )
    cancelled.attempts[0].lifecycle_state = "canceled"

    conflicted = record(
        run_id="conflicted-attempt",
        simulation_id="trade_cumulus_conflicted_attempt",
        display_name="Conflicted Trade Cumulus Attempt",
        accepted=False,
        retained_state="conflict",
    )

    for run_id in (
        "user-simulation-accepted",
        "user-simulation-alternate",
        "sounding-experiment",
        "failed-attempt",
        "cancelled-attempt",
    ):
        run_dir = tmp_path / "runs" / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "evidence.json").write_text("{}")

    note_path = (
        tmp_path / "simulation-notes" / "trade_cumulus" / "trade_cumulus_user_variation.json"
    )
    note_path.parent.mkdir(parents=True)
    note_path.write_text('{"note":"Retained note"}')
    explore_state = (
        tmp_path / "explore-state" / "trade_cumulus" / "trade_cumulus_user_variation.json"
    )
    explore_state.parent.mkdir(parents=True)
    explore_state.write_text('{"last_active":{"time_index":4}}')

    inventory = retained_asset_inventory(
        fake_settings(tmp_path),
        lifecycle=LifecycleProjection(
            generated_at="2026-07-28T00:00:00+00:00",
            records=[user, experiment, failed, cancelled, conflicted],
        ),
        refresh=True,
    )
    by_run = {asset.run_id: asset for asset in inventory.assets if asset.run_id}

    accepted = by_run["user-simulation-accepted"]
    alternate = by_run["user-simulation-alternate"]
    assert accepted.asset_class == "simulation_output"
    assert accepted.protection_state == "ordinary"
    assert accepted.accepted_backing == "accepted"
    assert accepted.required_for_compare is True
    assert {dependency.kind for dependency in accepted.dependencies} >= {
        "accepted_backing",
        "last_active_explore",
        "note",
        "result",
        "saved_comparison",
        "saved_view",
    }
    assert alternate.asset_class == "attempt"
    assert alternate.protection_state == "temporary"
    assert alternate.accepted_backing == "alternate"
    assert by_run["sounding-experiment"].asset_class == "experiment_output"
    assert by_run["sounding-experiment"].owner_id == "fun_with_soundings"
    assert by_run["failed-attempt"].availability_state == "invalid"
    assert by_run["failed-attempt"].protection_state == "ordinary"
    assert by_run["cancelled-attempt"].asset_class == "attempt"
    assert by_run["cancelled-attempt"].protection_state == "temporary"
    assert by_run["conflicted-attempt"].availability_state == "conflicted"
