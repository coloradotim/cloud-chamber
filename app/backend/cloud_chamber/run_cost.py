"""Typed World run-cost estimates and immutable launch-budget records."""

from __future__ import annotations

import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storage_policy import MINIMUM_FREE_SPACE_BYTES

GIB = 1024**3
MIB = 1024**2
RUN_COST_SCHEMA_VERSION: Literal["1"] = "1"

EstimateBasis = Literal["measured", "scaled_from_measured", "uncharacterized"]
LaunchBudgetDisposition = Literal["passes", "blocked"]

TRADE_CUMULUS_RETAINED_FIELDS = "ql, qv, th, prs, u, v, w, tke, kmh, khh, cwp, hfx, qfx, and rain"
MOUNTAIN_WAVES_DRY_RETAINED_FIELDS = "zs, zhval, th, prs, u, v, and w"
MOUNTAIN_WAVES_MOIST_RETAINED_FIELDS = "zs, zhval, th, prs, qv, ql, uinterp, winterp, and w"
SUPERCELLS_RETAINED_FIELDS = (
    "th, prs, qv, qc, qr, qi, qs, qg, nci, ncs, ncr, ncg, dbz, uinterp, "
    "vinterp, winterp, xvort, yvort, zvort, rain, prate, uh, and cref"
)


class NumericalRealization(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str
    grid: str
    spacing: str
    timestep_strategy: str
    physics_source: str


class ObservationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_seconds: int | None
    output_cadence_seconds: int | None
    diagnostic_cadence_seconds: int | None = None
    expected_history_count: int | None
    retained_field_inventory: str


class RunCostProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = RUN_COST_SCHEMA_VERSION
    world_id: str
    world_name: str
    recipe_id: str
    recipe_version: str
    profile_id: str
    profile_name: str
    role: str
    numerical_realization: NumericalRealization
    observation_plan: ObservationPlan
    expected_runtime_min_seconds: int | None
    expected_runtime_max_seconds: int | None
    expected_size_min_bytes: int | None
    expected_size_max_bytes: int | None
    estimate_basis: EstimateBasis
    confidence: str
    cost_change_reasons: list[str] = Field(default_factory=list)
    scientific_limitations: list[str] = Field(default_factory=list)
    required_post_run_reserve_bytes: int = MINIMUM_FREE_SPACE_BYTES


class RunCostEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: RunCostProfile
    current_free_space_bytes: int
    projected_free_space_bytes: int | None
    required_free_space_bytes: int | None
    disposition: LaunchBudgetDisposition
    disposition_reason: str


class LaunchReviewSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"] = RUN_COST_SCHEMA_VERSION
    snapshot_id: str
    created_at: str
    estimate: RunCostEstimate
    review_free_space_bytes: int
    warning_threshold_bytes: int
    minimum_free_space_bytes: int


class ImmediatePrelaunchCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"] = RUN_COST_SCHEMA_VERSION
    check_id: str
    snapshot_id: str
    checked_at: str
    current_free_space_bytes: int
    expected_size_high_bytes: int | None
    required_post_run_reserve_bytes: int
    projected_free_space_bytes: int | None
    disposition: LaunchBudgetDisposition
    reason: str


class LaunchReviewRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot: LaunchReviewSnapshot
    immediate_prelaunch_checks: list[ImmediatePrelaunchCheck] = Field(default_factory=list)


class RunCostCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = RUN_COST_SCHEMA_VERSION
    estimates: list[RunCostEstimate]


class LaunchReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: str


class ImmediatePrelaunchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str


class LaunchBudgetError(ValueError):
    """Raised when a launch estimate or immutable review record is invalid."""


def run_cost_catalog(settings: CloudChamberSettings) -> RunCostCatalog:
    return RunCostCatalog(estimates=[estimate_profile(settings, profile) for profile in profiles()])


def estimate_profile(settings: CloudChamberSettings, profile: RunCostProfile) -> RunCostEstimate:
    free = shutil.disk_usage(settings.runtime_home.expanduser()).free
    high = profile.expected_size_max_bytes
    if profile.estimate_basis == "uncharacterized" or high is None:
        return RunCostEstimate(
            profile=profile,
            current_free_space_bytes=free,
            projected_free_space_bytes=None,
            required_free_space_bytes=None,
            disposition="blocked",
            disposition_reason=(
                "This profile is uncharacterized. Its owning variation issue must approve "
                "a conservative reservation before launch."
            ),
        )
    required = high + profile.required_post_run_reserve_bytes
    projected = free - high
    passed = free >= required
    return RunCostEstimate(
        profile=profile,
        current_free_space_bytes=free,
        projected_free_space_bytes=projected,
        required_free_space_bytes=required,
        disposition="passes" if passed else "blocked",
        disposition_reason=(
            "The high retained-size estimate fits while preserving the required safety margin."
            if passed
            else "The high retained-size estimate would violate the required safety margin."
        ),
    )


def create_launch_review_snapshot(
    settings: CloudChamberSettings,
    *,
    profile_id: str,
    warning_threshold_bytes: int,
) -> LaunchReviewRecord:
    profile = profile_by_id(profile_id)
    estimate = estimate_profile(settings, profile)
    now = datetime.now(UTC)
    snapshot = LaunchReviewSnapshot(
        snapshot_id=uuid4().hex,
        created_at=now.isoformat(),
        estimate=estimate,
        review_free_space_bytes=estimate.current_free_space_bytes,
        warning_threshold_bytes=warning_threshold_bytes,
        minimum_free_space_bytes=MINIMUM_FREE_SPACE_BYTES,
    )
    record = LaunchReviewRecord(snapshot=snapshot)
    _write_new_record(_snapshot_path(settings, snapshot.snapshot_id), record)
    return record


def load_launch_review_record(
    settings: CloudChamberSettings,
    snapshot_id: str,
) -> LaunchReviewRecord:
    path = _snapshot_path(settings, snapshot_id)
    if not path.is_file():
        raise LaunchBudgetError("Launch-review snapshot was not found.")
    try:
        return LaunchReviewRecord.model_validate_json(path.read_text())
    except (OSError, ValueError) as exc:
        raise LaunchBudgetError("Launch-review snapshot is invalid or unreadable.") from exc


def immediate_prelaunch_disk_gate(
    settings: CloudChamberSettings,
    *,
    snapshot_id: str,
) -> LaunchReviewRecord:
    record = load_launch_review_record(settings, snapshot_id)
    estimate = record.snapshot.estimate
    profile = estimate.profile
    current_free = shutil.disk_usage(settings.runtime_home.expanduser()).free
    high = profile.expected_size_max_bytes
    if profile.estimate_basis == "uncharacterized" or high is None:
        projected = None
        disposition: LaunchBudgetDisposition = "blocked"
        reason = (
            "Launch blocked: the selected profile remains uncharacterized and has no "
            "approved conservative reservation."
        )
    else:
        projected = current_free - high
        required = high + profile.required_post_run_reserve_bytes
        disposition = "passes" if current_free >= required else "blocked"
        reason = (
            "Launch budget passes at immediate prelaunch."
            if disposition == "passes"
            else "Launch blocked: current free space no longer preserves the required margin."
        )
    check = ImmediatePrelaunchCheck(
        check_id=uuid4().hex,
        snapshot_id=record.snapshot.snapshot_id,
        checked_at=datetime.now(UTC).isoformat(),
        current_free_space_bytes=current_free,
        expected_size_high_bytes=high,
        required_post_run_reserve_bytes=profile.required_post_run_reserve_bytes,
        projected_free_space_bytes=projected,
        disposition=disposition,
        reason=reason,
    )
    updated = record.model_copy(
        update={"immediate_prelaunch_checks": [*record.immediate_prelaunch_checks, check]}
    )
    _append_check(settings, check)
    return updated


def validate_manifest_launch_budget(
    settings: CloudChamberSettings,
    *,
    snapshot_id: str | None,
) -> ImmediatePrelaunchCheck | None:
    """Enforce the shared gate when a package opts into the approved contract."""
    if not snapshot_id:
        return None
    record = immediate_prelaunch_disk_gate(settings, snapshot_id=snapshot_id)
    check = record.immediate_prelaunch_checks[-1]
    if check.disposition != "passes":
        raise LaunchBudgetError(check.reason)
    return check


def profile_by_id(profile_id: str) -> RunCostProfile:
    for profile in profiles():
        if profile.profile_id == profile_id:
            return profile
    raise LaunchBudgetError("Run-cost profile is not recognized.")


def profiles() -> list[RunCostProfile]:
    return [
        _profile(
            world_id="trade_cumulus",
            world_name="Trade Cumulus",
            recipe_id="canonical_bomex_trade_cumulus",
            profile_id="trade_cumulus_quick_v1",
            profile_name="Quick — Three-hour field response",
            role="Quick",
            grid="64 × 64 × 75",
            spacing="100 × 100 × 40 m",
            timestep="target 3 s",
            duration=10_800,
            cadence=180,
            histories=61,
            runtime=(10 * 60, 20 * 60),
            size=(int(0.8 * GIB), int(1.1 * GIB)),
            basis="scaled_from_measured",
            confidence="Scaled from measured six-hour lower-resolution runs.",
            limitation="Early response; not a full steady-period assessment.",
        ),
        _profile(
            world_id="trade_cumulus",
            world_name="Trade Cumulus",
            recipe_id="canonical_bomex_trade_cumulus",
            profile_id="trade_cumulus_standard_v1",
            profile_name="Standard — Four-hour experiment",
            role="Standard",
            grid="64 × 64 × 75",
            spacing="100 × 100 × 40 m",
            timestep="target 3 s",
            duration=14_400,
            cadence=120,
            histories=121,
            runtime=(15 * 60, 30 * 60),
            size=(int(1.6 * GIB), int(2.2 * GIB)),
            basis="scaled_from_measured",
            confidence="Scaled from measured lower-resolution runs.",
        ),
        _profile(
            world_id="trade_cumulus",
            world_name="Trade Cumulus",
            recipe_id="canonical_bomex_trade_cumulus",
            profile_id="trade_cumulus_full_cycle_v1",
            profile_name="Full-cycle — Six-hour experiment",
            role="Full-cycle",
            grid="64 × 64 × 75",
            spacing="100 × 100 × 40 m",
            timestep="target 3 s",
            duration=21_600,
            cadence=120,
            histories=181,
            runtime=(22 * 60, 23 * 60),
            size=(int(2.5 * GIB), int(3.2 * GIB)),
            basis="measured",
            confidence="Measured near the Baseline and More Moisture reference runs.",
        ),
        _profile(
            world_id="trade_cumulus",
            world_name="Trade Cumulus",
            recipe_id="canonical_bomex_trade_cumulus",
            profile_id="trade_cumulus_presentation_v1",
            profile_name="Presentation — Detailed four-hour field",
            role="Presentation",
            grid="96 × 96 × 100",
            spacing="about 66.7 × 66.7 × 30 m",
            timestep="target 2 s",
            duration=14_400,
            cadence=60,
            histories=241,
            runtime=(68 * 60, 124 * 60),
            size=(int(9.08 * GIB), int(9.34 * GIB)),
            basis="measured",
            confidence="Measured retained presentation runs.",
        ),
        _profile(
            world_id="trade_cumulus",
            world_name="Trade Cumulus",
            recipe_id="canonical_bomex_trade_cumulus",
            profile_id="trade_cumulus_extended_v1",
            profile_name="Extended — Wide-domain organization",
            role="Extended",
            grid="128 × 128 × 75",
            spacing="100 × 100 × 40 m",
            timestep="target 3 s",
            duration=14_400,
            cadence=120,
            histories=121,
            runtime=(60 * 60, 120 * 60),
            size=(int(6.5 * GIB), 9 * GIB),
            basis="uncharacterized",
            confidence="Requires bounded characterization before launch.",
            limitation="Not an ordinary default.",
        ),
        _profile(
            world_id="mountain_waves",
            world_name="Mountain Waves",
            recipe_id="dry_ridge_wave_mechanics",
            profile_id="mountain_waves_dry_quick_v1",
            profile_name="Dry Ridge Quick — Mechanics check",
            role="Quick",
            grid="Generated from terrain and boundary constraints",
            spacing="target dx,dz no greater than 200 m",
            timestep="target no greater than 2 s",
            duration=None,
            cadence=180,
            histories=None,
            runtime=(8, 15),
            size=(7 * MIB, 12 * MIB),
            basis="measured",
            confidence="Measured source case, rounded with headroom.",
            limitation="Sparse playback.",
        ),
        _profile(
            world_id="mountain_waves",
            world_name="Mountain Waves",
            recipe_id="dry_ridge_wave_mechanics",
            profile_id="mountain_waves_dry_standard_v1",
            profile_name="Dry Ridge Standard — Wave evolution",
            role="Standard",
            grid="Generated from terrain and boundary constraints",
            spacing="target dx,dz no greater than 100 m",
            timestep="target no greater than 1 s",
            duration=None,
            cadence=60,
            histories=None,
            runtime=(80, 110),
            size=(45 * MIB, 65 * MIB),
            basis="scaled_from_measured",
            confidence="Reference-case estimate from measured source evidence.",
        ),
        _profile(
            world_id="mountain_waves",
            world_name="Mountain Waves",
            recipe_id="dry_ridge_wave_mechanics",
            profile_id="mountain_waves_dry_presentation_v1",
            profile_name="Dry Ridge Presentation — Smooth wave evolution",
            role="Presentation",
            grid="Generated Standard numerical realization",
            spacing="target dx,dz no greater than 100 m",
            timestep="target no greater than 1 s",
            duration=None,
            cadence=30,
            histories=None,
            runtime=(80, 95),
            size=(85 * MIB, 105 * MIB),
            basis="measured",
            confidence="Measured source presentation case.",
        ),
        _profile(
            world_id="mountain_waves",
            world_name="Mountain Waves",
            recipe_id="dry_ridge_wave_mechanics",
            profile_id="mountain_waves_dry_extended_v1",
            profile_name="Dry Ridge Extended — Long wave evolution",
            role="Extended",
            grid="Standard or Presentation resolution",
            spacing="Control-dependent",
            timestep="Profile-dependent",
            duration=None,
            cadence=None,
            histories=None,
            runtime=(None, None),
            size=(None, None),
            basis="uncharacterized",
            confidence="Requires an estimate from the selected configuration.",
            limitation="Not an ordinary default.",
        ),
        _profile(
            world_id="mountain_waves",
            world_name="Mountain Waves",
            recipe_id="boulder_moist_wave",
            profile_id="mountain_waves_boulder_quick_v1",
            profile_name="Boulder Quick — Wave/cloud response",
            role="Quick",
            grid="220 × 1 × 125",
            spacing="1,000 × 200 m",
            timestep="target 2 s",
            duration=4_000,
            cadence=200,
            histories=21,
            runtime=(55, 80),
            size=(40 * MIB, 55 * MIB),
            basis="measured",
            confidence="Measured reference case.",
        ),
        _profile(
            world_id="mountain_waves",
            world_name="Mountain Waves",
            recipe_id="boulder_moist_wave",
            profile_id="mountain_waves_boulder_standard_v1",
            profile_name="Boulder Standard — Full Boulder experiment",
            role="Standard",
            grid="220 × 1 × 125 nominal; domain may expand",
            spacing="1,000 × 200 m",
            timestep="target 2 s",
            duration=7_200,
            cadence=120,
            histories=61,
            runtime=(2 * 60, 4 * 60),
            size=(120 * MIB, 200 * MIB),
            basis="scaled_from_measured",
            confidence="Provisional near-reference estimate.",
        ),
        _profile(
            world_id="mountain_waves",
            world_name="Mountain Waves",
            recipe_id="boulder_moist_wave",
            profile_id="mountain_waves_boulder_presentation_v1",
            profile_name="Boulder Presentation — Detailed evolution",
            role="Presentation",
            grid="440 × 1 × 250",
            spacing="500 × 100 m",
            timestep="target 1 s",
            duration=7_200,
            cadence=30,
            histories=241,
            runtime=(24 * 60, 28 * 60),
            size=(int(1.15 * GIB), int(1.35 * GIB)),
            basis="measured",
            confidence="Measured retained presentation run.",
        ),
        _profile(
            world_id="mountain_waves",
            world_name="Mountain Waves",
            recipe_id="boulder_moist_wave",
            profile_id="mountain_waves_boulder_extended_v1",
            profile_name="Boulder Extended — Long adjustment",
            role="Extended",
            grid="Standard or Presentation resolution",
            spacing="Control-dependent",
            timestep="Profile-dependent",
            duration=None,
            cadence=None,
            histories=None,
            runtime=(None, None),
            size=(None, None),
            basis="uncharacterized",
            confidence="Requires an estimate from the selected configuration.",
        ),
        _profile(
            world_id="supercells",
            world_name="Supercells",
            recipe_id="idealized_supercell",
            profile_id="supercells_quick_v1",
            profile_name="Quick — Two-hour storm response",
            role="Quick",
            grid="120 × 120 × 40",
            spacing="1,000 × 1,000 × 500 m",
            timestep="target 6 s",
            duration=7_200,
            cadence=300,
            histories=25,
            runtime=(10 * 60, 15 * 60),
            size=(int(0.4 * GIB), int(0.7 * GIB)),
            basis="scaled_from_measured",
            confidence="Runtime measured for nine histories; denser output scaled.",
            limitation="Broad resolved structure; low-level detail is explicitly coarse.",
        ),
        _profile(
            world_id="supercells",
            world_name="Supercells",
            recipe_id="idealized_supercell",
            profile_id="supercells_standard_v1",
            profile_name="Standard — Three-hour supercell experiment",
            role="Standard",
            grid="160 × 160 × 50",
            spacing="750 × 750 × 400 m",
            timestep="target 4.5 s",
            duration=10_800,
            cadence=180,
            histories=61,
            runtime=(45 * 60, 75 * 60),
            size=(2 * GIB, 3 * GIB),
            basis="scaled_from_measured",
            confidence="Scaled from measured Quick and Presentation evidence.",
        ),
        _profile(
            world_id="supercells",
            world_name="Supercells",
            recipe_id="idealized_supercell",
            profile_id="supercells_presentation_v1",
            profile_name="Presentation — Detailed three-hour storm",
            role="Presentation",
            grid="240 × 240 × 60",
            spacing="500 × 500 × 333 m",
            timestep="target 3 s",
            duration=10_800,
            cadence=120,
            histories=91,
            runtime=(int(3.4 * 3600), int(3.75 * 3600)),
            size=(int(8.6 * GIB), int(8.9 * GIB)),
            basis="measured",
            confidence="Measured controlled presentation pair.",
        ),
        _profile(
            world_id="supercells",
            world_name="Supercells",
            recipe_id="idealized_supercell",
            profile_id="supercells_extended_v1",
            profile_name="Extended — Four-hour longevity",
            role="Extended",
            grid="Standard numerical realization by default",
            spacing="750 × 750 × 400 m",
            timestep="target 4.5 s",
            duration=14_400,
            cadence=180,
            histories=81,
            runtime=(60 * 60, 100 * 60),
            size=(3 * GIB, 4 * GIB),
            basis="uncharacterized",
            confidence="Requires bounded characterization before launch.",
            limitation="Boundary and domain review required.",
        ),
    ]


def _profile(
    *,
    world_id: str,
    world_name: str,
    recipe_id: str,
    profile_id: str,
    profile_name: str,
    role: str,
    grid: str,
    spacing: str,
    timestep: str,
    duration: int | None,
    cadence: int | None,
    histories: int | None,
    runtime: tuple[int | None, int | None],
    size: tuple[int | None, int | None],
    basis: EstimateBasis,
    confidence: str,
    limitation: str | None = None,
) -> RunCostProfile:
    return RunCostProfile(
        world_id=world_id,
        world_name=world_name,
        recipe_id=recipe_id,
        recipe_version="approved_variation_contract_v1",
        profile_id=profile_id,
        profile_name=profile_name,
        role=role,
        numerical_realization=NumericalRealization(
            domain="World and Recipe controlled",
            grid=grid,
            spacing=spacing,
            timestep_strategy=timestep,
            physics_source="Approved World Recipe",
        ),
        observation_plan=ObservationPlan(
            duration_seconds=duration,
            output_cadence_seconds=cadence,
            expected_history_count=histories,
            retained_field_inventory=_retained_field_inventory(world_id, recipe_id),
        ),
        expected_runtime_min_seconds=runtime[0],
        expected_runtime_max_seconds=runtime[1],
        expected_size_min_bytes=size[0],
        expected_size_max_bytes=size[1],
        estimate_basis=basis,
        confidence=confidence,
        cost_change_reasons=[
            "Control-dependent domain growth, adaptive timestep behavior, and output "
            "compression may change actual cost."
        ],
        scientific_limitations=[limitation] if limitation else [],
    )


def _retained_field_inventory(world_id: str, recipe_id: str) -> str:
    if world_id == "trade_cumulus":
        return TRADE_CUMULUS_RETAINED_FIELDS
    if world_id == "mountain_waves":
        if recipe_id == "dry_ridge_wave_mechanics":
            return MOUNTAIN_WAVES_DRY_RETAINED_FIELDS
        return MOUNTAIN_WAVES_MOIST_RETAINED_FIELDS
    if world_id == "supercells":
        return SUPERCELLS_RETAINED_FIELDS
    raise LaunchBudgetError("Run-cost profile has no approved retained-field inventory.")


def _snapshot_path(settings: CloudChamberSettings, snapshot_id: str) -> Path:
    if not snapshot_id or not snapshot_id.isalnum():
        raise LaunchBudgetError("Launch-review snapshot identity is invalid.")
    return settings.runtime_home.expanduser() / "launch-reviews" / f"{snapshot_id}.snapshot.json"


def _write_new_record(path: Path, record: LaunchReviewRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x") as handle:
            handle.write(record.model_dump_json(indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise LaunchBudgetError("Launch-review snapshot identity already exists.") from exc
    except OSError as exc:
        raise LaunchBudgetError("Launch-review snapshot could not be recorded.") from exc


def _append_check(settings: CloudChamberSettings, check: ImmediatePrelaunchCheck) -> None:
    path = (
        settings.runtime_home.expanduser()
        / "launch-reviews"
        / f"{check.snapshot_id}.preflight.jsonl"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a") as handle:
            handle.write(check.model_dump_json() + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise LaunchBudgetError("Immediate prelaunch disposition could not be recorded.") from exc
