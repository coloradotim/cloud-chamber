from datetime import UTC, datetime
from pathlib import Path

import pytest

from cloud_chamber.run_cost import (
    LaunchBudgetError,
    create_launch_review_snapshot,
    estimate_profile,
    immediate_prelaunch_disk_gate,
    profile_by_id,
    run_cost_catalog,
    validate_manifest_launch_budget,
)
from cloud_chamber.run_manifest import RunManifest, validate_run_manifest
from cloud_chamber.settings import CloudChamberSettings


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=tmp_path,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "cache",
        log_dir=tmp_path / "logs",
    )


def bound_manifest(
    tmp_path: Path,
    *,
    profile_id: str,
    run_id: str = "reviewed-attempt",
) -> RunManifest:
    profile = profile_by_id(profile_id)
    created_at = datetime(2026, 7, 28, 12, 0, tzinfo=UTC).isoformat()
    launch_specification = {
        "world_id": profile.world_id,
        "recipe_id": profile.recipe_id,
        "recipe_version": profile.recipe_version,
        "profile_id": profile.profile_id,
        "numerical_realization": profile.numerical_realization.model_dump(mode="json"),
        "observation_plan": profile.observation_plan.model_dump(mode="json"),
    }
    return validate_run_manifest(
        {
            "manifest_version": "1",
            "run_id": run_id,
            "scenario": {"id": profile.world_id, "schema_version": "1"},
            "controls": {"fixture_control": "reviewed"},
            "run_configuration": {
                "configuration_id": f"{profile.profile_id}-fixture",
                "launch_specification": launch_specification,
            },
            "physical_question": "How does the reviewed atmosphere evolve?",
            "expected_diagnostics": ["reviewed_output"],
            "generated_inputs": {
                "run_directory": str(tmp_path / "runs" / run_id),
                "manifest_path": str(tmp_path / "runs" / run_id / "run_manifest.json"),
                "namelist_input": str(tmp_path / "runs" / run_id / "namelist.input"),
            },
            "runtime_paths": {
                "runtime_home": str(tmp_path),
                "cache_dir": str(tmp_path / "cache"),
                "log_dir": str(tmp_path / "logs"),
            },
            "app": {"app_version": "test"},
            "lifecycle_state": "packaged",
            "validation_status": "valid",
            "provenance": {
                "product_state": "packaged_dry_run_output",
            },
            "created_at": created_at,
            "updated_at": created_at,
            "user": {"name": "Reviewed fixture"},
            "recipe_id": profile.recipe_id,
            "required_output_fields": list(profile.observation_plan.retained_field_inventory),
        }
    )


def test_catalog_has_measured_scaled_and_uncharacterized_world_profiles(tmp_path: Path) -> None:
    catalog = run_cost_catalog(fake_settings(tmp_path))

    assert {item.profile.world_id for item in catalog.estimates} == {
        "trade_cumulus",
        "mountain_waves",
        "supercells",
    }
    assert {item.profile.estimate_basis for item in catalog.estimates} == {
        "measured",
        "scaled_from_measured",
        "uncharacterized",
    }
    assert all(
        item.profile.required_post_run_reserve_bytes == 2 * 1024**3 for item in catalog.estimates
    )
    inventories = {
        item.profile.profile_id: item.profile.observation_plan.retained_field_inventory
        for item in catalog.estimates
    }
    assert inventories["trade_cumulus_standard_v1"][:4] == ("ql", "qv", "th", "prs")
    assert inventories["mountain_waves_dry_standard_v1"] == (
        "zs",
        "zhval",
        "th",
        "prs",
        "uinterp",
        "winterp",
        "w",
    )
    assert "ql" in inventories["mountain_waves_boulder_standard_v1"]
    assert "cref" in inventories["supercells_standard_v1"]
    assert "World Explore" not in " ".join(
        field for inventory in inventories.values() for field in inventory
    )
    uncharacterized = next(
        item
        for item in catalog.estimates
        if item.profile.profile_id == "mountain_waves_boulder_extended_v1"
    )
    assert uncharacterized.disposition == "blocked"
    assert uncharacterized.projected_free_space_bytes is None


def test_estimate_uses_high_retained_size_plus_reserve(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = profile_by_id("supercells_quick_v1")
    high = profile.expected_size_max_bytes
    assert high is not None
    free = high + profile.required_post_run_reserve_bytes + 123
    monkeypatch.setattr(
        "cloud_chamber.run_cost.shutil.disk_usage",
        lambda _path: type("Usage", (), {"free": free})(),
    )

    estimate = estimate_profile(fake_settings(tmp_path), profile)

    assert estimate.disposition == "passes"
    assert estimate.required_free_space_bytes == high + profile.required_post_run_reserve_bytes
    assert estimate.projected_free_space_bytes == free - high


def test_snapshot_is_immutable_and_prelaunch_check_records_changed_free_space(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)
    profile = profile_by_id("mountain_waves_boulder_quick_v1")
    high = profile.expected_size_max_bytes
    assert high is not None
    free_values = iter(
        [
            high + profile.required_post_run_reserve_bytes + 1,
            high + profile.required_post_run_reserve_bytes - 1,
        ]
    )
    monkeypatch.setattr(
        "cloud_chamber.run_cost.shutil.disk_usage",
        lambda _path: type("Usage", (), {"free": next(free_values)})(),
    )

    review = create_launch_review_snapshot(
        settings,
        profile_id=profile.profile_id,
        warning_threshold_bytes=50 * 1024**3,
    )
    snapshot_path = tmp_path / "launch-reviews" / f"{review.snapshot.snapshot_id}.snapshot.json"
    original_snapshot = snapshot_path.read_text()
    checked = immediate_prelaunch_disk_gate(
        settings,
        snapshot_id=review.snapshot.snapshot_id,
    )

    assert review.snapshot.manifest_binding is None
    assert review.snapshot.estimate.disposition == "passes"
    assert checked.immediate_prelaunch_checks[-1].disposition == "blocked"
    assert checked.immediate_prelaunch_checks[-1].check_kind == "planning"
    assert snapshot_path.read_text() == original_snapshot
    audit_path = tmp_path / "launch-reviews" / f"{review.snapshot.snapshot_id}.preflight.jsonl"
    assert checked.immediate_prelaunch_checks[-1].check_id in audit_path.read_text()


def test_manifest_gate_fails_closed_for_blocked_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)
    manifest = bound_manifest(tmp_path, profile_id="trade_cumulus_standard_v1")
    monkeypatch.setattr(
        "cloud_chamber.run_cost.shutil.disk_usage",
        lambda _path: type("Usage", (), {"free": 1})(),
    )
    review = create_launch_review_snapshot(
        settings,
        profile_id="trade_cumulus_standard_v1",
        warning_threshold_bytes=50 * 1024**3,
        manifest=manifest,
    )

    with pytest.raises(LaunchBudgetError, match="Launch blocked"):
        validate_manifest_launch_budget(
            settings,
            manifest=manifest,
            snapshot_id=review.snapshot.snapshot_id,
        )


def test_manifest_gate_rejects_planning_only_snapshot(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest = bound_manifest(tmp_path, profile_id="trade_cumulus_quick_v1")
    review = create_launch_review_snapshot(
        settings,
        profile_id="trade_cumulus_quick_v1",
        warning_threshold_bytes=50 * 1024**3,
    )

    with pytest.raises(LaunchBudgetError, match="planning-only review"):
        validate_manifest_launch_budget(
            settings,
            manifest=manifest,
            snapshot_id=review.snapshot.snapshot_id,
        )


def test_manifest_gate_rejects_package_mismatch_and_successful_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)
    profile = profile_by_id("trade_cumulus_quick_v1")
    manifest = bound_manifest(tmp_path, profile_id=profile.profile_id)
    high = profile.expected_size_max_bytes
    assert high is not None
    monkeypatch.setattr(
        "cloud_chamber.run_cost.shutil.disk_usage",
        lambda _path: type(
            "Usage",
            (),
            {"free": high + profile.required_post_run_reserve_bytes + 1},
        )(),
    )
    review = create_launch_review_snapshot(
        settings,
        profile_id=profile.profile_id,
        warning_threshold_bytes=50 * 1024**3,
        manifest=manifest,
    )
    changed = manifest.model_copy(
        update={"controls": {**manifest.controls, "fixture_control": "changed"}}
    )

    with pytest.raises(LaunchBudgetError, match="no longer matches"):
        validate_manifest_launch_budget(
            settings,
            manifest=changed,
            snapshot_id=review.snapshot.snapshot_id,
        )

    check = validate_manifest_launch_budget(
        settings,
        manifest=manifest,
        snapshot_id=review.snapshot.snapshot_id,
    )
    assert check is not None
    assert check.check_kind == "launch"
    assert check.attempt_id == manifest.run_id
    assert check.specification_fingerprint

    with pytest.raises(LaunchBudgetError, match="already been consumed"):
        validate_manifest_launch_budget(
            settings,
            manifest=manifest,
            snapshot_id=review.snapshot.snapshot_id,
        )


def test_mountain_waves_snapshot_binds_the_resolved_recipe_realization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)
    catalog = profile_by_id("mountain_waves_boulder_standard_v1")
    resolved = catalog.model_copy(
        update={
            "numerical_realization": catalog.numerical_realization.model_copy(
                update={
                    "domain": "Generated 180 km domain",
                    "grid": "360 × 1 × 250",
                }
            ),
            "observation_plan": catalog.observation_plan.model_copy(
                update={
                    "duration_seconds": 6_000,
                    "expected_history_count": 101,
                }
            ),
            "expected_size_min_bytes": 400 * 1024**2,
            "expected_size_max_bytes": 600 * 1024**2,
        }
    )
    manifest = bound_manifest(tmp_path, profile_id=catalog.profile_id)
    launch_specification = {
        "world_id": resolved.world_id,
        "recipe_id": resolved.recipe_id,
        "recipe_version": resolved.recipe_version,
        "profile_id": resolved.profile_id,
        "numerical_realization": resolved.numerical_realization.model_dump(mode="json"),
        "observation_plan": resolved.observation_plan.model_dump(mode="json"),
    }
    manifest = manifest.model_copy(
        update={
            "run_configuration": {
                **manifest.run_configuration,
                "launch_specification": launch_specification,
            }
        }
    )
    high = resolved.expected_size_max_bytes
    assert high is not None
    monkeypatch.setattr(
        "cloud_chamber.run_cost.shutil.disk_usage",
        lambda _path: type(
            "Usage",
            (),
            {"free": high + resolved.required_post_run_reserve_bytes + 1},
        )(),
    )

    review = create_launch_review_snapshot(
        settings,
        profile_id=catalog.profile_id,
        warning_threshold_bytes=50 * 1024**3,
        manifest=manifest,
        resolved_profile=resolved,
    )
    check = validate_manifest_launch_budget(
        settings,
        manifest=manifest,
        snapshot_id=review.snapshot.snapshot_id,
    )

    assert review.snapshot.estimate.profile == resolved
    assert review.snapshot.manifest_binding is not None
    assert review.snapshot.manifest_binding.numerical_realization.grid == "360 × 1 × 250"
    assert check is not None
    assert check.disposition == "passes"


def test_manifest_gate_remains_opt_in_for_legacy_packages(tmp_path: Path) -> None:
    assert (
        validate_manifest_launch_budget(
            fake_settings(tmp_path),
            manifest=None,
            snapshot_id=None,
        )
        is None
    )
