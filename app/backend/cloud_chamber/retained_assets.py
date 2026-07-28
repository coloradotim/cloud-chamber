"""Read-only retained scientific asset and dependency inventory."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cloud_chamber.lifecycle import LifecycleAttempt, LifecycleProjection, LifecycleRecord
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storage_policy import (
    DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES,
    MINIMUM_FREE_SPACE_BYTES,
)

RETAINED_ASSET_SCHEMA_VERSION: Literal["1"] = "1"
_CACHE_RELATIVE_PATH = Path(".inventory-cache") / "retained-assets-v1.json"
_BUILT_IN_SIMULATIONS = {
    ("trade_cumulus", "trade_cumulus_canonical_bomex"),
    ("trade_cumulus", "trade_cumulus_more_moisture"),
    ("mountain_waves", "mountain_waves_dry_ridge"),
    ("mountain_waves", "mountain_waves_boulder_moist_reference"),
    ("supercells", "supercells_quarter_circle_reference"),
    ("supercells", "supercells_straight_line_hodograph"),
}
_OWNER_LABELS = {
    "trade_cumulus": "Trade Cumulus",
    "mountain_waves": "Mountain Waves",
    "supercells": "Supercells",
    "fun_with_soundings": "Fun With Soundings",
    "legacy_unassigned": "Legacy / unassigned",
}

OwnerId = Literal[
    "trade_cumulus",
    "mountain_waves",
    "supercells",
    "fun_with_soundings",
    "legacy_unassigned",
]
AssetClass = Literal[
    "simulation_output",
    "experiment_output",
    "attempt",
    "package_logs",
    "derived_cache",
    "source_asset",
    "durable_metadata",
]
AvailabilityState = Literal["retained", "missing", "invalid", "conflicted"]
ProtectionState = Literal["system_protected", "ordinary", "temporary", "unknown"]
RepairabilityState = Literal["repairable", "rerunnable", "not_repairable", "unknown"]
BackingState = Literal["accepted", "alternate", "not_applicable", "unknown"]


class AssetComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component: str
    size_bytes: int
    file_count: int
    uncounted_file_count: int = 0


class AssetDependency(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    dependency_id: str
    title: str
    relationship: str
    available: bool


class RetainedAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str
    stable_name: str
    owner_id: OwnerId
    owner_label: str
    asset_class: AssetClass
    lifecycle_role: str
    record_role: str | None = None
    world_id: str | None = None
    simulation_id: str | None = None
    experiment_id: str | None = None
    recipe_id: str | None = None
    recipe_version: str | None = None
    parent_simulation_id: str | None = None
    reference_simulation_id: str | None = None
    attempt_id: str | None = None
    attempt_lifecycle_state: str | None = None
    attempt_queue_state: str | None = None
    attempt_process_state: str | None = None
    attempt_validation_status: str | None = None
    run_id: str | None = None
    result_id: str | None = None
    case_id: str | None = None
    question: str | None = None
    tags: list[str] = Field(default_factory=list)
    technical_path: str | None = None
    size_bytes: int | None = None
    partially_uncounted: bool = False
    uncounted_path_count: int = 0
    components: list[AssetComponent] = Field(default_factory=list)
    created_at: str | None = None
    modified_at: str | None = None
    last_used_at: str | None = None
    built_in: bool = False
    accepted_backing: BackingState = "unknown"
    availability_state: AvailabilityState
    protection_state: ProtectionState
    repairability_state: RepairabilityState = "unknown"
    trust_state: str = "unassessed"
    caveats: list[str] = Field(default_factory=list)
    recreation_method: str | None = None
    dependencies: list[AssetDependency] = Field(default_factory=list)
    required_for_explore: bool = False
    required_for_compare: bool = False
    required_for_parent_reuse: bool = False
    required_for_repair: bool = False


class UsageGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    size_bytes: int
    asset_count: int


class InventoryPerformance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cache_hit: bool
    scan_duration_ms: float
    scanned_file_count: int
    fingerprinted_path_count: int
    fingerprint: str


class RetainedAssetInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = RETAINED_ASSET_SCHEMA_VERSION
    generated_at: str
    runtime_home: str
    total_usage_bytes: int
    free_space_bytes: int
    system_protected_bytes: int
    ordinary_retained_bytes: int
    temporary_bytes: int
    uncounted_asset_count: int
    warning_threshold_bytes: int
    minimum_free_space_bytes: int
    above_usage_warning: bool
    below_minimum_free_space: bool
    usage_by_owner: list[UsageGroup]
    usage_by_class: list[UsageGroup]
    state_counts: dict[str, int]
    lifecycle_counts: dict[str, int]
    trust_counts: dict[str, int]
    assets: list[RetainedAsset]
    performance: InventoryPerformance
    warnings: list[str] = Field(default_factory=list)


class _CachedInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = RETAINED_ASSET_SCHEMA_VERSION
    fingerprint: str
    generated_at: str
    total_usage_bytes: int
    system_protected_bytes: int
    ordinary_retained_bytes: int
    temporary_bytes: int
    uncounted_asset_count: int
    usage_by_owner: list[UsageGroup]
    usage_by_class: list[UsageGroup]
    state_counts: dict[str, int]
    lifecycle_counts: dict[str, int]
    trust_counts: dict[str, int]
    assets: list[RetainedAsset]
    scanned_file_count: int
    scan_duration_ms: float
    warnings: list[str] = Field(default_factory=list)


def retained_asset_inventory(
    settings: CloudChamberSettings,
    *,
    lifecycle: LifecycleProjection,
    refresh: bool = False,
) -> RetainedAssetInventory:
    """Return a cached product-level inventory without reading scientific arrays."""
    runtime_home = settings.runtime_home.expanduser()
    runtime_home.mkdir(parents=True, exist_ok=True)
    fingerprint, fingerprinted_path_count, fingerprint_warnings = _inventory_fingerprint(
        runtime_home
    )
    cache_path = runtime_home / _CACHE_RELATIVE_PATH
    active_attempts = _has_active_attempts(lifecycle)
    cached = None if refresh or active_attempts else _load_cache(cache_path, fingerprint)
    if cached is None:
        cached = _build_inventory(
            runtime_home,
            lifecycle,
            fingerprint,
            fingerprint_warnings=fingerprint_warnings,
        )
        _write_cache(cache_path, cached)
        cache_hit = False
    else:
        cache_hit = True

    free_space = shutil.disk_usage(runtime_home).free
    return RetainedAssetInventory(
        generated_at=cached.generated_at,
        runtime_home=str(runtime_home),
        total_usage_bytes=cached.total_usage_bytes,
        free_space_bytes=free_space,
        system_protected_bytes=cached.system_protected_bytes,
        ordinary_retained_bytes=cached.ordinary_retained_bytes,
        temporary_bytes=cached.temporary_bytes,
        uncounted_asset_count=cached.uncounted_asset_count,
        warning_threshold_bytes=DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES,
        minimum_free_space_bytes=MINIMUM_FREE_SPACE_BYTES,
        above_usage_warning=cached.total_usage_bytes >= DEFAULT_STORAGE_WARNING_THRESHOLD_BYTES,
        below_minimum_free_space=free_space < MINIMUM_FREE_SPACE_BYTES,
        usage_by_owner=cached.usage_by_owner,
        usage_by_class=cached.usage_by_class,
        state_counts=cached.state_counts,
        lifecycle_counts=cached.lifecycle_counts,
        trust_counts=cached.trust_counts,
        assets=cached.assets,
        performance=InventoryPerformance(
            cache_hit=cache_hit,
            scan_duration_ms=0.0 if cache_hit else cached.scan_duration_ms,
            scanned_file_count=0 if cache_hit else cached.scanned_file_count,
            fingerprinted_path_count=fingerprinted_path_count,
            fingerprint=fingerprint,
        ),
        warnings=[
            *cached.warnings,
            *(["Active attempts force a fresh retained-byte rollup."] if active_attempts else []),
            *lifecycle.warnings,
        ],
    )


def _build_inventory(
    runtime_home: Path,
    lifecycle: LifecycleProjection,
    fingerprint: str,
    *,
    fingerprint_warnings: list[str],
) -> _CachedInventory:
    started = time.perf_counter()
    assets: list[RetainedAsset] = []
    scanned_files = 0
    warnings = list(fingerprint_warnings)
    record_by_run: dict[str, tuple[LifecycleRecord, LifecycleAttempt]] = {}
    for record in lifecycle.records:
        for attempt in record.attempts:
            record_by_run[attempt.run_id] = (record, attempt)

    runs_root = runtime_home / "runs"
    present_run_ids: set[str] = set()
    if runs_root.is_dir():
        for run_dir in sorted(runs_root.iterdir()):
            if not run_dir.is_dir() or run_dir.is_symlink():
                continue
            present_run_ids.add(run_dir.name)
            record_and_attempt = record_by_run.get(run_dir.name)
            current_record: LifecycleRecord | None = (
                record_and_attempt[0] if record_and_attempt else None
            )
            current_attempt: LifecycleAttempt | None = (
                record_and_attempt[1] if record_and_attempt else None
            )
            components, file_count, uncounted_count, component_warnings = _component_inventory(
                run_dir
            )
            scanned_files += file_count
            warnings.extend(component_warnings)
            assets.append(
                _run_asset(
                    run_dir,
                    current_record,
                    current_attempt,
                    lifecycle,
                    components,
                    uncounted_count=uncounted_count,
                )
            )

    for run_id, (record, attempt) in record_by_run.items():
        if run_id in present_run_ids:
            continue
        assets.append(_missing_run_asset(runtime_home, record, attempt, lifecycle))

    recognized_roots = {
        "cache": ("source_asset", "Caches and source data"),
        "cm1_source_builds": ("source_asset", "Trusted local source packages"),
        "comparisons": ("derived_cache", "Derived comparison evidence"),
        "review-packets": ("package_logs", "Review packets"),
        "explore-state": ("durable_metadata", "Explore state and Saved Views"),
        "saved-comparisons": ("durable_metadata", "Saved Comparisons"),
        "simulation-notes": ("durable_metadata", "Simulation Notes"),
    }
    ignored_names = {"runs"}
    for path in sorted(runtime_home.iterdir()):
        if path.name in {*ignored_names, _CACHE_RELATIVE_PATH.parts[0]}:
            continue
        asset_class, label = recognized_roots.get(
            path.name, ("durable_metadata", "Runtime metadata")
        )
        size, file_count, uncounted_count, path_warnings = _path_size(path)
        scanned_files += file_count
        warnings.extend(path_warnings)
        owner_id: OwnerId = "legacy_unassigned"
        assets.append(
            RetainedAsset(
                asset_id=f"runtime:{path.name}",
                stable_name=label if path.name in recognized_roots else path.name,
                owner_id=owner_id,
                owner_label=_OWNER_LABELS[owner_id],
                asset_class=asset_class,  # type: ignore[arg-type]
                lifecycle_role="supporting_asset",
                technical_path=str(path),
                size_bytes=size,
                partially_uncounted=uncounted_count > 0,
                uncounted_path_count=uncounted_count,
                components=[
                    AssetComponent(
                        component="retained files",
                        size_bytes=size,
                        file_count=file_count,
                        uncounted_file_count=uncounted_count,
                    )
                ],
                created_at=_created_at(path),
                modified_at=_modified_at(path),
                built_in=False,
                accepted_backing="not_applicable",
                availability_state="retained",
                protection_state="ordinary",
                repairability_state="unknown",
                trust_state="unassessed",
            )
        )

    assets.sort(
        key=lambda asset: (
            -(asset.size_bytes or -1),
            asset.owner_label,
            asset.stable_name.casefold(),
        )
    )
    total = sum(asset.size_bytes or 0 for asset in assets)
    protected = sum(
        asset.size_bytes or 0 for asset in assets if asset.protection_state == "system_protected"
    )
    temporary = sum(
        asset.size_bytes or 0 for asset in assets if asset.protection_state == "temporary"
    )
    ordinary = total - protected - temporary
    return _CachedInventory(
        fingerprint=fingerprint,
        generated_at=datetime.now(UTC).isoformat(),
        total_usage_bytes=total,
        system_protected_bytes=protected,
        ordinary_retained_bytes=ordinary,
        temporary_bytes=temporary,
        uncounted_asset_count=sum(
            asset.size_bytes is None or asset.partially_uncounted for asset in assets
        ),
        usage_by_owner=_usage_groups(
            assets,
            key=lambda asset: asset.owner_id,
            label=lambda asset: asset.owner_label,
        ),
        usage_by_class=_usage_groups(
            assets,
            key=lambda asset: asset.asset_class,
            label=lambda asset: _class_label(asset.asset_class),
        ),
        state_counts=dict(Counter(_state_label(asset) for asset in assets)),
        lifecycle_counts=dict(
            Counter(asset.attempt_lifecycle_state or "not_applicable" for asset in assets)
        ),
        trust_counts=dict(Counter(asset.trust_state for asset in assets)),
        assets=assets,
        scanned_file_count=scanned_files,
        scan_duration_ms=round((time.perf_counter() - started) * 1000, 2),
        warnings=list(dict.fromkeys(warnings)),
    )


def _run_asset(
    run_dir: Path,
    record: LifecycleRecord | None,
    attempt: LifecycleAttempt | None,
    lifecycle: LifecycleProjection,
    components: list[AssetComponent],
    *,
    uncounted_count: int,
) -> RetainedAsset:
    built_in = bool(
        record
        and record.simulation_id
        and (record.owner_id, record.simulation_id) in _BUILT_IN_SIMULATIONS
    )
    accepted = bool(attempt and attempt.accepted_backing)
    availability = _attempt_availability(attempt)
    asset_class = _run_asset_class(record, attempt)
    protection: ProtectionState = (
        "system_protected"
        if built_in and accepted
        else "temporary"
        if asset_class == "attempt" and availability == "retained"
        else "ordinary"
    )
    dependencies = _asset_dependencies(record, attempt, lifecycle, built_in)
    size = sum(item.size_bytes for item in components)
    return RetainedAsset(
        asset_id=f"run:{run_dir.name}",
        stable_name=record.display_name if record else run_dir.name,
        owner_id=record.owner_id if record else "legacy_unassigned",
        owner_label=record.owner_label if record else _OWNER_LABELS["legacy_unassigned"],
        asset_class=asset_class,
        lifecycle_role=attempt.relationship if attempt else "technical_attempt",
        record_role=record.role if record else None,
        world_id=record.world_id if record else None,
        simulation_id=record.simulation_id if record else None,
        experiment_id=record.experiment_id if record else None,
        recipe_id=record.recipe_id if record else None,
        recipe_version=record.recipe_version if record else None,
        parent_simulation_id=record.parent_simulation_id if record else None,
        reference_simulation_id=record.reference_simulation_id if record else None,
        attempt_id=attempt.attempt_id if attempt else run_dir.name,
        attempt_lifecycle_state=attempt.lifecycle_state if attempt else None,
        attempt_queue_state=attempt.queue_state if attempt else None,
        attempt_process_state=_attempt_process_state(attempt),
        attempt_validation_status=attempt.validation_status if attempt else None,
        run_id=run_dir.name,
        result_id=attempt.result_id if attempt else None,
        case_id=record.case_id if record else None,
        question=record.question if record else None,
        tags=record.tags if record else [],
        technical_path=str(run_dir),
        size_bytes=size,
        partially_uncounted=uncounted_count > 0,
        uncounted_path_count=uncounted_count,
        components=components,
        created_at=(attempt.created_at if attempt else None) or _created_at(run_dir),
        modified_at=(attempt.updated_at if attempt else None) or _modified_at(run_dir),
        built_in=built_in,
        accepted_backing=(
            "accepted"
            if accepted
            else "alternate"
            if record and record.record_kind == "simulation"
            else "not_applicable"
        ),
        availability_state=availability,
        protection_state=protection,
        repairability_state="unknown",
        trust_state=record.trust_state if record else "unassessed",
        caveats=record.caveats if record else [],
        recreation_method=None,
        dependencies=dependencies,
        required_for_explore=bool(
            accepted and record and record.facts.world_inspectability == "passed"
        ),
        required_for_compare=any(item.kind == "saved_comparison" for item in dependencies),
        required_for_parent_reuse=any(item.kind == "child_simulation" for item in dependencies),
        required_for_repair=any(item.kind == "repair_source" for item in dependencies),
    )


def _missing_run_asset(
    runtime_home: Path,
    record: LifecycleRecord,
    attempt: LifecycleAttempt,
    lifecycle: LifecycleProjection,
) -> RetainedAsset:
    built_in = bool(
        record.simulation_id and (record.owner_id, record.simulation_id) in _BUILT_IN_SIMULATIONS
    )
    dependencies = _asset_dependencies(record, attempt, lifecycle, built_in)
    return RetainedAsset(
        asset_id=f"run:{attempt.run_id}",
        stable_name=record.display_name,
        owner_id=record.owner_id,
        owner_label=record.owner_label,
        asset_class=(
            "simulation_output" if record.record_kind == "simulation" else "experiment_output"
        ),
        lifecycle_role=attempt.relationship,
        record_role=record.role,
        world_id=record.world_id,
        simulation_id=record.simulation_id,
        experiment_id=record.experiment_id,
        recipe_id=record.recipe_id,
        recipe_version=record.recipe_version,
        parent_simulation_id=record.parent_simulation_id,
        reference_simulation_id=record.reference_simulation_id,
        attempt_id=attempt.attempt_id,
        attempt_lifecycle_state=attempt.lifecycle_state,
        attempt_queue_state=attempt.queue_state,
        attempt_process_state=_attempt_process_state(attempt),
        attempt_validation_status=attempt.validation_status,
        run_id=attempt.run_id,
        result_id=attempt.result_id,
        case_id=record.case_id,
        question=record.question,
        tags=record.tags,
        technical_path=str(runtime_home / "runs" / attempt.run_id),
        size_bytes=None,
        built_in=built_in,
        accepted_backing="accepted" if attempt.accepted_backing else "alternate",
        availability_state=("conflicted" if attempt.retained_state == "conflict" else "missing"),
        protection_state="system_protected" if built_in else "ordinary",
        repairability_state="unknown",
        trust_state="unavailable",
        caveats=[
            *record.caveats,
            "The durable record remains, but its retained output is unavailable locally.",
        ],
        dependencies=dependencies,
        required_for_explore=bool(attempt.accepted_backing),
        required_for_compare=any(item.kind == "saved_comparison" for item in dependencies),
        required_for_parent_reuse=any(item.kind == "child_simulation" for item in dependencies),
    )


def _asset_dependencies(
    record: LifecycleRecord | None,
    attempt: LifecycleAttempt | None,
    lifecycle: LifecycleProjection,
    built_in: bool,
) -> list[AssetDependency]:
    if record is None:
        return []
    dependencies = [
        AssetDependency(
            kind=item.kind,
            dependency_id=item.dependency_id,
            title=item.title,
            relationship=item.relationship,
            available=True,
        )
        for item in record.dependencies
    ]
    if record.world_id and record.simulation_id:
        state_path = (
            Path(record.attempts[0].manifest_path).parents[1]
            if record.attempts and record.attempts[0].manifest_path
            else None
        )
        runtime_home = state_path.parent if state_path and state_path.name == "runs" else None
        if runtime_home:
            note_path = (
                runtime_home / "simulation-notes" / record.world_id / f"{record.simulation_id}.json"
            )
            if note_path.is_file():
                dependencies.append(
                    AssetDependency(
                        kind="note",
                        dependency_id=f"{record.world_id}:{record.simulation_id}",
                        title="Simulation note",
                        relationship="Note",
                        available=True,
                    )
                )
            state_file = (
                runtime_home / "explore-state" / record.world_id / f"{record.simulation_id}.json"
            )
            state_payload = _read_json(state_file)
            if state_payload.get("last_active") is not None:
                dependencies.append(
                    AssetDependency(
                        kind="last_active_explore",
                        dependency_id=f"{record.world_id}:{record.simulation_id}",
                        title="Last active Explore state",
                        relationship="Explore resume",
                        available=True,
                    )
                )
    if attempt and attempt.result_id:
        dependencies.append(
            AssetDependency(
                kind="result",
                dependency_id=attempt.result_id,
                title="Retained Result record",
                relationship="Result",
                available=True,
            )
        )
    if attempt and attempt.accepted_backing:
        dependencies.append(
            AssetDependency(
                kind="accepted_backing",
                dependency_id=attempt.attempt_id,
                title="Accepted backing output",
                relationship="Simulation backing",
                available=True,
            )
        )
    if built_in and record.simulation_id:
        dependencies.append(
            AssetDependency(
                kind="world_inventory",
                dependency_id=record.simulation_id,
                title=f"{record.owner_label} built-in content",
                relationship="Current World requirement",
                available=True,
            )
        )
    if record.simulation_id:
        for candidate in lifecycle.records:
            if candidate.parent_simulation_id != record.simulation_id:
                continue
            dependencies.append(
                AssetDependency(
                    kind="child_simulation",
                    dependency_id=candidate.simulation_id or candidate.record_id,
                    title=candidate.display_name,
                    relationship="Parent Simulation",
                    available=candidate.facts.retained_assets not in {"missing", "failed"},
                )
            )
    unique: dict[tuple[str, str, str], AssetDependency] = {}
    for dependency in dependencies:
        unique[(dependency.kind, dependency.dependency_id, dependency.relationship)] = dependency
    return list(unique.values())


def _run_asset_class(
    record: LifecycleRecord | None,
    attempt: LifecycleAttempt | None,
) -> AssetClass:
    if attempt and attempt.lifecycle_state == "packaged":
        return "package_logs"
    if not record or not attempt or not attempt.accepted_backing:
        return "attempt"
    return "simulation_output" if record.record_kind == "simulation" else "experiment_output"


def _attempt_availability(attempt: LifecycleAttempt | None) -> AvailabilityState:
    if attempt is None:
        return "invalid"
    if attempt.retained_state == "conflict":
        return "conflicted"
    if attempt.retained_state == "missing":
        return "missing"
    if attempt.validation_status == "failed":
        return "invalid"
    return "retained"


def _attempt_process_state(attempt: LifecycleAttempt | None) -> str | None:
    if attempt is None or not attempt.lifecycle_state:
        return None
    if attempt.lifecycle_state in {"created", "packaged", "queued"}:
        return "not_started"
    if attempt.lifecycle_state == "running":
        return "running"
    if attempt.lifecycle_state in {"completed", "ingested", "saved"}:
        return "completed"
    if attempt.lifecycle_state == "failed":
        return "failed"
    if attempt.lifecycle_state == "canceled":
        return "canceled"
    return "unknown"


def _has_active_attempts(lifecycle: LifecycleProjection) -> bool:
    return any(
        attempt.lifecycle_state in {"queued", "running"}
        or attempt.queue_state in {"queued", "running"}
        for record in lifecycle.records
        for attempt in record.attempts
    )


def _component_inventory(
    run_dir: Path,
) -> tuple[list[AssetComponent], int, int, list[str]]:
    sizes: defaultdict[str, int] = defaultdict(int)
    counts: Counter[str] = Counter()
    uncounted: Counter[str] = Counter()
    warnings: list[str] = []

    def walk_error(error: OSError) -> None:
        warnings.append(f"Could not count retained path {error.filename or run_dir}: {error}.")

    for root, directories, files in os.walk(
        run_dir,
        followlinks=False,
        onerror=walk_error,
    ):
        directories[:] = [name for name in directories if not (Path(root) / name).is_symlink()]
        root_path = Path(root)
        for name in files:
            path = root_path / name
            component = _component_name(path.relative_to(run_dir))
            try:
                size = path.lstat().st_size
            except OSError as exc:
                uncounted[component] += 1
                warnings.append(f"Could not count retained file {path}: {exc}.")
                continue
            sizes[component] += size
            counts[component] += 1
    component_names = set(sizes) | set(uncounted)
    components = [
        AssetComponent(
            component=name,
            size_bytes=sizes[name],
            file_count=counts[name],
            uncounted_file_count=uncounted[name],
        )
        for name in sorted(component_names, key=lambda item: (-sizes[item], item))
    ]
    return (
        components,
        sum(counts.values()),
        sum(uncounted.values()),
        warnings,
    )


def _component_name(relative_path: Path) -> str:
    name = relative_path.name.lower()
    parts = {part.lower() for part in relative_path.parts}
    if (
        name.startswith("cm1out")
        or name.endswith((".nc", ".nc4", ".dat", ".ctl"))
        and name not in {"perts.dat"}
    ):
        return "model output"
    if "logs" in parts or name.endswith(".log") or name in {"stdout", "stderr"}:
        return "logs"
    if {"derived-products", "processed", "visualization"} & parts:
        return "derived data"
    if name in {
        "namelist.input",
        "input_sounding",
        "perts.dat",
        "case_manifest.json",
        "dry_run_report.json",
        "runtime_file_checklist.json",
        "storage_estimate.json",
        "execution_preflight.json",
    }:
        return "package inputs"
    return "metadata and supporting files"


def _path_size(path: Path) -> tuple[int, int, int, list[str]]:
    warnings: list[str] = []
    if path.is_symlink():
        try:
            return path.lstat().st_size, 1, 0, warnings
        except OSError as exc:
            return 0, 0, 1, [f"Could not count retained path {path}: {exc}."]
    if path.is_file():
        try:
            return path.stat().st_size, 1, 0, warnings
        except OSError as exc:
            return 0, 0, 1, [f"Could not count retained file {path}: {exc}."]
    total = 0
    count = 0
    uncounted = 0

    def walk_error(error: OSError) -> None:
        nonlocal uncounted
        uncounted += 1
        warnings.append(f"Could not count retained path {error.filename or path}: {error}.")

    for root, directories, files in os.walk(
        path,
        followlinks=False,
        onerror=walk_error,
    ):
        directories[:] = [name for name in directories if not (Path(root) / name).is_symlink()]
        for name in files:
            candidate = Path(root) / name
            try:
                total += candidate.lstat().st_size
                count += 1
            except OSError as exc:
                uncounted += 1
                warnings.append(f"Could not count retained file {candidate}: {exc}.")
    return total, count, uncounted, warnings


def _usage_groups(
    assets: list[RetainedAsset],
    *,
    key: Any,
    label: Any,
) -> list[UsageGroup]:
    sizes: defaultdict[str, int] = defaultdict(int)
    counts: Counter[str] = Counter()
    labels: dict[str, str] = {}
    for asset in assets:
        group_id = key(asset)
        sizes[group_id] += asset.size_bytes or 0
        counts[group_id] += 1
        labels[group_id] = label(asset)
    return [
        UsageGroup(
            id=group_id,
            label=labels[group_id],
            size_bytes=sizes[group_id],
            asset_count=counts[group_id],
        )
        for group_id in sorted(sizes, key=lambda item: (-sizes[item], labels[item]))
    ]


def _class_label(asset_class: AssetClass) -> str:
    return {
        "simulation_output": "Simulation output",
        "experiment_output": "Experiment output",
        "attempt": "Attempts",
        "package_logs": "Packages and logs",
        "derived_cache": "Derived caches",
        "source_asset": "Source assets",
        "durable_metadata": "Durable metadata",
    }[asset_class]


def _state_label(asset: RetainedAsset) -> str:
    if asset.availability_state != "retained":
        return asset.availability_state
    if asset.protection_state == "system_protected":
        return "protected"
    if asset.protection_state == "temporary":
        return "temporary"
    if asset.repairability_state in {"repairable", "rerunnable"}:
        return "potentially_repairable"
    return "ordinary"


def _inventory_fingerprint(runtime_home: Path) -> tuple[str, int, list[str]]:
    records: list[str] = []
    warnings: list[str] = []
    fingerprinted_path_count = 0
    for path in sorted(runtime_home.iterdir()) if runtime_home.is_dir() else []:
        if path.name == _CACHE_RELATIVE_PATH.parts[0]:
            continue
        record, warning = _stat_fingerprint(path, runtime_home)
        records.append(record)
        fingerprinted_path_count += 1
        if warning:
            warnings.append(warning)
        if not path.is_dir() or path.is_symlink():
            continue

        def walk_error(error: OSError, base_path: Path = path) -> None:
            warnings.append(
                f"Could not fingerprint retained path {error.filename or base_path}: {error}."
            )

        for root, directories, files in os.walk(
            path,
            followlinks=False,
            onerror=walk_error,
        ):
            directories[:] = sorted(
                name for name in directories if not (Path(root) / name).is_symlink()
            )
            for name in [*directories, *sorted(files)]:
                candidate = Path(root) / name
                record, warning = _stat_fingerprint(candidate, runtime_home)
                records.append(record)
                fingerprinted_path_count += 1
                if warning:
                    warnings.append(warning)
    return (
        hashlib.sha256("\n".join(records).encode()).hexdigest(),
        fingerprinted_path_count,
        warnings,
    )


def _stat_fingerprint(path: Path, runtime_home: Path) -> tuple[str, str | None]:
    try:
        stat = path.lstat()
        relative = path.relative_to(runtime_home)
        return f"{relative}:{stat.st_mode}:{stat.st_size}:{stat.st_mtime_ns}", None
    except (OSError, ValueError) as exc:
        return f"{path}:unreadable", f"Could not fingerprint retained path {path}: {exc}."


def _load_cache(path: Path, fingerprint: str) -> _CachedInventory | None:
    if not path.is_file():
        return None
    try:
        payload = _CachedInventory.model_validate_json(path.read_text())
    except (OSError, ValidationError, ValueError):
        return None
    return payload if payload.fingerprint == fingerprint else None


def _write_cache(path: Path, payload: _CachedInventory) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(payload.model_dump_json(indent=2) + "\n")
    os.replace(temporary, path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _created_at(path: Path) -> str | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    value = getattr(stat, "st_birthtime", stat.st_ctime)
    return datetime.fromtimestamp(value, UTC).isoformat()


def _modified_at(path: Path) -> str | None:
    try:
        value = path.stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(value, UTC).isoformat()
