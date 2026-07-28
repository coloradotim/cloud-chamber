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
from cloud_chamber.settings import CloudChamberSettings


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=tmp_path,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "cache",
        log_dir=tmp_path / "logs",
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
    assert inventories["trade_cumulus_standard_v1"].startswith("ql, qv, th, prs")
    assert inventories["mountain_waves_dry_standard_v1"] == ("zs, zhval, th, prs, u, v, and w")
    assert "ql" in inventories["mountain_waves_boulder_standard_v1"]
    assert "cref" in inventories["supercells_standard_v1"]
    assert "World Explore" not in " ".join(inventories.values())
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

    assert review.snapshot.estimate.disposition == "passes"
    assert checked.immediate_prelaunch_checks[-1].disposition == "blocked"
    assert snapshot_path.read_text() == original_snapshot
    audit_path = tmp_path / "launch-reviews" / f"{review.snapshot.snapshot_id}.preflight.jsonl"
    assert checked.immediate_prelaunch_checks[-1].check_id in audit_path.read_text()


def test_manifest_gate_fails_closed_for_blocked_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)
    monkeypatch.setattr(
        "cloud_chamber.run_cost.shutil.disk_usage",
        lambda _path: type("Usage", (), {"free": 1})(),
    )
    review = create_launch_review_snapshot(
        settings,
        profile_id="trade_cumulus_standard_v1",
        warning_threshold_bytes=50 * 1024**3,
    )

    with pytest.raises(LaunchBudgetError, match="Launch blocked"):
        validate_manifest_launch_budget(
            settings,
            snapshot_id=review.snapshot.snapshot_id,
        )


def test_manifest_gate_remains_opt_in_for_legacy_packages(tmp_path: Path) -> None:
    assert validate_manifest_launch_budget(fake_settings(tmp_path), snapshot_id=None) is None
