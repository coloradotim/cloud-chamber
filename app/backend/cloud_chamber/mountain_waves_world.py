"""Mountain Waves Cloud World inventory and persistent Simulation state."""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.generated_input_identity import (
    GeneratedInputIdentityError,
    verify_generated_input_identity,
)
from cloud_chamber.local_run_manager import reconcile_completed_run_manifest
from cloud_chamber.mountain_wave_case import (
    CM1_EXECUTABLE_SHA256,
    CM1_MOUNTAIN_WAVE_NAMELIST_SHA256,
    CM1_README_NAMELIST_SHA256,
    CM1_README_TERRAIN_SHA256,
    CM1_RELEASE,
    CM1_SOURCE_MANIFEST_SHA256,
    CM1_SOURCE_TAG,
    CM1_TAG_COMMIT,
    CRITICAL_SOURCE_HASHES,
)
from cloud_chamber.mountain_wave_terrain_visualization import (
    MOUNTAIN_WAVES_EXPLORE_REQUIRED_COORDINATES,
    MOUNTAIN_WAVES_EXPLORE_REQUIRED_FIELDS,
    MountainWaveTerrainVisualizationError,
    validate_mountain_waves_native_outputs,
)
from cloud_chamber.mountain_waves_recipes import (
    BOULDER_RECIPE_ID,
    DRY_RECIPE_ID,
    MountainWavesRecipeControls,
    RecipeId,
    default_controls,
    normalize_recipe_controls,
)
from cloud_chamber.presentation_runs import (
    PresentationRunError,
    PresentationRunEvidence,
    load_presentation_package,
    spec_by_key,
)
from cloud_chamber.run_manifest import (
    LifecycleState,
    ProductState,
    RunManifest,
    RunManifestError,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.variation_envelope import VariationAttempt, VariationEnvelope

WORLD_ID: Literal["mountain_waves"] = "mountain_waves"
WORLD_DISPLAY_NAME: Literal["Mountain Waves"] = "Mountain Waves"
WORLD_DESCRIPTION = (
    "Experiment with how terrain, wind, stability, and moisture create mountain waves and "
    "mountain-wave clouds."
)
DRY_SIMULATION_ID = "mountain_waves_dry_ridge"
DRY_RUN_ID = "dry-mountain-wave-presentation-v1-20260722"
DRY_CASE_ID = "cm1_r21_1_dry_mountain_wave_presentation_v1"
MOIST_SIMULATION_ID = "mountain_waves_boulder_moist_reference"
MOIST_RUN_ID = "moist-mountain-wave-presentation-v1-20260722"
MOIST_CASE_ID = "cm1_r21_1_toy2011_boulder_moist_wave_7200s_presentation_v1"
BROADER_BOULDER_SIMULATION_ID = "mountain_waves_broader-boulder-ridge_f8f714fb"
BROADER_BOULDER_RUN_ID = "mw-broader-boulder-ridge-20260722T040319Z-f8f7"

AvailabilityState = Literal["available", "partial", "unavailable", "conflict"]
SimulationState = Literal[
    "available", "packaged", "queued", "running", "failed", "canceled", "unavailable", "conflict"
]
SimulationRole = Literal["built_in", "variation"]

_INSPECTABILITY_CACHE_LIMIT = 64
_INSPECTABILITY_CACHE: OrderedDict[
    tuple[str, str, tuple[tuple[str, int, int, int], ...]], tuple[bool, str]
] = OrderedDict()
_INSPECTABILITY_CACHE_LOCK = RLock()


class MountainWavesWorldSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: Literal["mountain_waves"] = WORLD_ID
    display_name: Literal["Mountain Waves"] = WORLD_DISPLAY_NAME
    short_description: str = WORLD_DESCRIPTION
    reference_simulation_id: Literal["mountain_waves_boulder_moist_reference"] = (
        "mountain_waves_boulder_moist_reference"
    )
    reference_available: bool
    simulation_count: int
    saved_view_count: Literal[0] = 0
    saved_comparison_count: int = 0
    featured_comparison_count: Literal[0] = 0
    active_run_count: int
    completed_uninspected_run_count: int
    availability_state: AvailabilityState
    availability_message: str


class MountainWavesSimulationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    display_name: str
    role: SimulationRole
    world_id: Literal["mountain_waves"] = WORLD_ID
    run_id: str
    case_id: str
    parent_simulation_id: str | None = None
    parent_run_id: str | None = None
    reference_simulation_id: str = MOIST_SIMULATION_ID
    user_question: str | None = None
    recipe_id: str | None = None
    recipe_contract_version: str | None = None
    relationship_classification: str | None = None
    legacy_contract: bool = False
    parent_eligibility_reason: str | None = None
    state: SimulationState
    state_message: str
    inspectable: bool
    can_create_variation: bool
    moist: bool
    moist_fields_available: bool
    purpose: str
    configuration: dict[str, Any] | None = None
    scientific_design: dict[str, Any] | None = None
    numerical_realization: dict[str, Any] | None = None
    observation_plan: dict[str, Any] | None = None
    differences: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    manifest_path: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class MountainWavesLabSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active_run_count: int
    packaged_run_count: int
    completed_simulation_count: int
    failed_run_count: int
    total_variation_count: int


class MountainWavesWorldDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: Literal["mountain_waves"] = WORLD_ID
    display_name: Literal["Mountain Waves"] = WORLD_DISPLAY_NAME
    short_description: str = WORLD_DESCRIPTION
    availability_state: AvailabilityState
    availability_message: str
    default_parent_simulation_id: str = MOIST_SIMULATION_ID
    simulations: list[MountainWavesSimulationRecord]
    activity: list[MountainWavesSimulationRecord]
    history: list[MountainWavesSimulationRecord]
    lab_summary: MountainWavesLabSummary
    caveats: list[str] = Field(
        default_factory=lambda: [
            (
                "The dry and moist built-ins use different scientific configurations "
                "and are not a controlled pair."
            ),
            (
                "Mountain Waves is an honest native two-dimensional x-z World; "
                "singleton y is not a three-dimensional volume."
            ),
        ]
    )

    def summary(self) -> MountainWavesWorldSummary:
        moist_reference = next(
            (item for item in self.simulations if item.simulation_id == MOIST_SIMULATION_ID),
            None,
        )
        return MountainWavesWorldSummary(
            reference_available=bool(moist_reference and moist_reference.inspectable),
            simulation_count=sum(item.inspectable for item in self.simulations),
            active_run_count=self.lab_summary.active_run_count,
            completed_uninspected_run_count=sum(item.state == "conflict" for item in self.history),
            availability_state=self.availability_state,
            availability_message=self.availability_message,
        )


@dataclass(frozen=True)
class _BuiltInSpec:
    simulation_id: str
    display_name: str
    run_id: str
    case_id: str
    moist: bool
    presentation_key: str
    purpose: str
    caveats: tuple[str, ...]


@dataclass(frozen=True)
class _VariationSelection:
    manifest: RunManifest
    manifest_path: Path
    attempts: tuple[VariationAttempt, ...]
    accepted_backing: bool
    conflict_reason: str | None = None


_BUILT_INS = (
    _BuiltInSpec(
        simulation_id=DRY_SIMULATION_ID,
        display_name="Dry Ridge — Wave Mechanics",
        run_id=DRY_RUN_ID,
        case_id=DRY_CASE_ID,
        moist=False,
        presentation_key="mountain_dry",
        purpose=(
            "See the terrain-forced gravity wave without cloud and inspect vertical "
            "motion and temperature displacement."
        ),
        caveats=(
            "This dry benchmark does not simulate moisture or cloud formation.",
            (
                "The retained source-defined analytic atmosphere remains inspectable, "
                "but sampled-sounding equivalence is not approved for new variations."
            ),
        ),
    ),
    _BuiltInSpec(
        simulation_id=MOIST_SIMULATION_ID,
        display_name="Boulder Windstorm — Moist Reference",
        run_id=MOIST_RUN_ID,
        case_id=MOIST_CASE_ID,
        moist=True,
        presentation_key="mountain_moist",
        purpose=(
            "Watch clear air form windward and lee-wave cloud, then use the "
            "source-backed atmosphere as an experimental parent."
        ),
        caveats=(
            (
                "The run is a two-dimensional presentation reference, not a "
                "three-dimensional mountain-flow simulation."
            ),
            "It is not a controlled moisture variation of Dry Ridge.",
        ),
    ),
)


def mountain_waves_world_detail(settings: CloudChamberSettings) -> MountainWavesWorldDetail:
    built_ins = [_built_in_record(settings, spec) for spec in _BUILT_INS]
    variations = _variation_records(settings)
    if not any(item.simulation_id == BROADER_BOULDER_SIMULATION_ID for item in variations):
        variations.append(_missing_broader_boulder_record())
    completed = [item for item in variations if item.inspectable]
    simulations = [*built_ins, *completed]
    active_states = {"queued", "running"}
    activity = [
        item for item in variations if item.state in active_states or item.state == "packaged"
    ]
    failed_count = sum(item.state in {"failed", "canceled"} for item in variations)
    available_built_ins = sum(item.inspectable for item in built_ins)
    if available_built_ins == 2:
        availability: AvailabilityState = "available"
        message = "Both built-in Simulations and the Mountain Waves Lab are available."
    elif available_built_ins:
        availability = "partial"
        message = "One built-in Simulation is unavailable; the Lab remains available."
    else:
        availability = "unavailable"
        message = (
            "Built-in output is unavailable locally; the Lab remains available for "
            "retained variations."
        )
    return MountainWavesWorldDetail(
        availability_state=availability,
        availability_message=message,
        simulations=simulations,
        activity=activity,
        history=variations,
        lab_summary=MountainWavesLabSummary(
            active_run_count=sum(item.state in active_states for item in variations),
            packaged_run_count=sum(item.state == "packaged" for item in variations),
            completed_simulation_count=len(completed),
            failed_run_count=failed_count,
            total_variation_count=len(variations),
        ),
    )


def _missing_broader_boulder_record() -> MountainWavesSimulationRecord:
    return MountainWavesSimulationRecord(
        simulation_id=BROADER_BOULDER_SIMULATION_ID,
        display_name="Broader Boulder Ridge",
        role="variation",
        run_id=BROADER_BOULDER_RUN_ID,
        case_id="mountain_waves_exploratory_variation_v1",
        parent_simulation_id=MOIST_SIMULATION_ID,
        parent_run_id="moist-mountain-wave-toy-1972-20260721T215226Z",
        reference_simulation_id=MOIST_SIMULATION_ID,
        user_question="How does a 10% broader ridge change the mountain-wave cloud pattern?",
        recipe_id="boulder_moist_wave",
        legacy_contract=True,
        parent_eligibility_reason=(
            "This Legacy-contract Simulation remains recorded, but its retained output was "
            "removed and it cannot parent a new variation."
        ),
        state="unavailable",
        state_message=(
            "The stable Simulation identity and lineage are preserved, but its local run "
            "artifacts are no longer present."
        ),
        inspectable=False,
        can_create_variation=False,
        moist=True,
        moist_fields_available=True,
        purpose=(
            "Preserve the real broader-ridge experiment identity, lineage, and historical "
            "question after local output cleanup."
        ),
        differences={
            "terrain": [
                {
                    "path": "controls.ridge_half_width_m",
                    "label": "Ridge half-width",
                    "before": 10_000.0,
                    "after": 11_000.0,
                    "units": "m",
                    "material": True,
                }
            ]
        },
        caveats=["Legacy-contract Simulation; retained CM1 histories are no longer present."],
        created_at="2026-07-22T04:03:19+00:00",
    )


def mountain_waves_simulation(
    settings: CloudChamberSettings, simulation_id: str
) -> MountainWavesSimulationRecord | None:
    built_in = next((spec for spec in _BUILT_INS if spec.simulation_id == simulation_id), None)
    if built_in is not None:
        return _built_in_record(settings, built_in)
    selection = _variation_selection(settings, simulation_id)
    if selection is None:
        return None
    return _variation_record(
        selection.manifest,
        selection.manifest_path,
        attempts=selection.attempts,
        accepted_backing=selection.accepted_backing,
        conflict_reason=selection.conflict_reason,
    )


def mountain_waves_run_manifest(
    settings: CloudChamberSettings, simulation_id: str
) -> tuple[MountainWavesSimulationRecord, RunManifest, Path]:
    built_in = next((spec for spec in _BUILT_INS if spec.simulation_id == simulation_id), None)
    if built_in is not None:
        manifest_path = (
            settings.runtime_home.expanduser() / "runs" / built_in.run_id / "run_manifest.json"
        )
    else:
        selection = _variation_selection(settings, simulation_id)
        if selection is None:
            raise ValueError(f"Mountain Waves Simulation not found: {simulation_id}")
        if selection.conflict_reason:
            raise ValueError(
                f"Mountain Waves Simulation backing is conflicted: {selection.conflict_reason}"
            )
        manifest, manifest_path = selection.manifest, selection.manifest_path
        record = _variation_record(
            manifest,
            manifest_path,
            attempts=selection.attempts,
            accepted_backing=selection.accepted_backing,
        )
        if record is None:
            raise ValueError(f"Mountain Waves Simulation not found: {simulation_id}")
        return record, manifest, manifest_path
    try:
        manifest = load_run_manifest(manifest_path)
    except (OSError, RunManifestError) as exc:
        raise ValueError(f"Mountain Waves manifest is unavailable: {simulation_id}") from exc
    record = _built_in_record(settings, built_in)
    return record, manifest, manifest_path


def _variation_selection(
    settings: CloudChamberSettings, simulation_id: str
) -> _VariationSelection | None:
    runs_dir = settings.runtime_home.expanduser() / "runs"
    if not runs_dir.exists():
        return None
    candidates: list[tuple[RunManifest, Path]] = []
    for manifest_path in sorted(runs_dir.glob("*/run_manifest.json")):
        try:
            manifest = load_run_manifest(manifest_path)
        except (OSError, RunManifestError):
            continue
        if manifest.run_configuration.get("cloud_world_id") != WORLD_ID:
            continue
        if manifest.run_configuration.get("simulation_id") != simulation_id:
            continue
        if manifest.lifecycle_state in {LifecycleState.QUEUED, LifecycleState.RUNNING}:
            manifest = reconcile_completed_run_manifest(manifest_path, manifest)
        candidates.append((manifest, manifest_path))
    if not candidates:
        return None
    return _select_variation_backing(candidates)


def _built_in_record(
    settings: CloudChamberSettings, spec: _BuiltInSpec
) -> MountainWavesSimulationRecord:
    manifest_path = settings.runtime_home.expanduser() / "runs" / spec.run_id / "run_manifest.json"
    base: dict[str, Any] = dict(
        simulation_id=spec.simulation_id,
        display_name=spec.display_name,
        role="built_in",
        run_id=spec.run_id,
        case_id=spec.case_id,
        moist=spec.moist,
        moist_fields_available=spec.moist,
        purpose=spec.purpose,
        caveats=list(spec.caveats),
        manifest_path=str(manifest_path),
    )
    try:
        manifest = load_run_manifest(manifest_path)
    except OSError:
        return MountainWavesSimulationRecord.model_validate(
            {
                **base,
                "state": "unavailable",
                "state_message": (
                    "Preserved runtime evidence is not present in the configured runtime home."
                ),
                "inspectable": False,
                "can_create_variation": False,
            }
        )
    except RunManifestError:
        return MountainWavesSimulationRecord.model_validate(
            {
                **base,
                "state": "conflict",
                "state_message": (
                    "The preserved run manifest is unreadable or conflicts with the "
                    "expected identity."
                ),
                "inspectable": False,
                "can_create_variation": False,
            }
        )
    if manifest.run_id != spec.run_id or manifest.scenario.id != spec.case_id:
        return MountainWavesSimulationRecord.model_validate(
            {
                **base,
                "state": "conflict",
                "state_message": (
                    "The preserved run identity does not match this built-in Simulation."
                ),
                "inspectable": False,
                "can_create_variation": False,
            }
        )
    inspectable, inspectability_message = _built_in_inspectability(settings, spec, manifest)
    configuration = _built_in_configuration(manifest, spec)
    recipe_id: RecipeId = BOULDER_RECIPE_ID if spec.moist else DRY_RECIPE_ID
    scientific_design, numerical_realization, observation_plan = _built_in_layers(
        manifest,
        configuration=configuration,
        recipe_id=recipe_id,
        moist=spec.moist,
    )
    return MountainWavesSimulationRecord.model_validate(
        {
            **base,
            "state": (
                "available" if inspectable else _state_from_lifecycle(manifest.lifecycle_state)
            ),
            "state_message": (
                (
                    "Exact preserved output is available for terrain-aware inspection."
                    if spec.moist
                    else "Exact preserved output is available for terrain-aware inspection."
                )
                if inspectable
                else inspectability_message
            ),
            "inspectable": inspectable,
            "can_create_variation": inspectable and spec.simulation_id != DRY_SIMULATION_ID,
            "recipe_id": recipe_id,
            "recipe_contract_version": "1",
            "parent_eligibility_reason": (
                (
                    "Dry Ridge remains inspectable but cannot parent a variation until "
                    "source-defined analytic inheritance or bounded equivalence is approved."
                )
                if spec.simulation_id == DRY_SIMULATION_ID
                else None
                if inspectable
                else "The built-in must be available before it can parent a variation."
            ),
            "configuration": configuration,
            "scientific_design": scientific_design,
            "numerical_realization": numerical_realization,
            "observation_plan": observation_plan,
            "warnings": list(manifest.outputs.runtime_warnings),
            "created_at": manifest.created_at.isoformat(),
            "started_at": _iso(manifest.execution.started_at),
            "completed_at": _iso(manifest.execution.finished_at),
        }
    )


def _variation_records(settings: CloudChamberSettings) -> list[MountainWavesSimulationRecord]:
    runs_dir = settings.runtime_home.expanduser() / "runs"
    if not runs_dir.exists():
        return []
    grouped: dict[str, list[tuple[RunManifest, Path]]] = {}
    for manifest_path in sorted(runs_dir.glob("*/run_manifest.json")):
        try:
            manifest = load_run_manifest(manifest_path)
        except (OSError, RunManifestError):
            continue
        if manifest.run_configuration.get("cloud_world_id") != WORLD_ID:
            continue
        if manifest.lifecycle_state in {LifecycleState.QUEUED, LifecycleState.RUNNING}:
            manifest = reconcile_completed_run_manifest(manifest_path, manifest)
        simulation_id = _string(manifest.run_configuration.get("simulation_id"))
        if simulation_id is None:
            continue
        grouped.setdefault(simulation_id, []).append((manifest, manifest_path))
    records: list[MountainWavesSimulationRecord] = []
    for candidates in grouped.values():
        selection = _select_variation_backing(candidates)
        record = _variation_record(
            selection.manifest,
            selection.manifest_path,
            attempts=selection.attempts,
            accepted_backing=selection.accepted_backing,
            conflict_reason=selection.conflict_reason,
        )
        if record is not None:
            records.append(record)
    records.sort(key=lambda item: item.created_at or "", reverse=True)
    return records


def _select_variation_backing(
    candidates: list[tuple[RunManifest, Path]],
) -> _VariationSelection:
    ordered = sorted(
        candidates,
        key=lambda item: (item[0].created_at.isoformat(), str(item[1])),
    )
    by_run = {manifest.run_id: (manifest, path) for manifest, path in ordered}
    attempts_by_run: dict[str, VariationAttempt] = {}
    accepted_claims: set[str] = set()
    identities: set[tuple[str, str]] = set()
    conflict_reasons: list[str] = []
    for index, (manifest, _manifest_path) in enumerate(ordered):
        payload = manifest.run_configuration.get("variation_envelope")
        envelope: VariationEnvelope | None = None
        if isinstance(payload, dict):
            try:
                envelope = VariationEnvelope.model_validate(payload)
            except ValueError:
                conflict_reasons.append(
                    f"Attempt {manifest.run_id} has an invalid shared variation envelope."
                )
        elif manifest.scenario.id == "mountain_waves_recipe_variation_v1":
            conflict_reasons.append(
                f"Attempt {manifest.run_id} is missing its shared variation envelope."
            )
        if envelope is not None:
            identities.add(
                (
                    envelope.scientific_design.sha256,
                    envelope.numerical_realization.sha256,
                )
            )
            configured_simulation_id = manifest.run_configuration.get("simulation_id")
            if configured_simulation_id != envelope.simulation_id:
                conflict_reasons.append(
                    f"Attempt {manifest.run_id} disagrees with its envelope Simulation ID."
                )
            for attempt in envelope.attempts:
                if attempt.accepted_backing:
                    accepted_claims.add(attempt.run_id)
            current = next(
                (attempt for attempt in envelope.attempts if attempt.run_id == manifest.run_id),
                None,
            )
            if current is None:
                current = VariationAttempt(
                    attempt_id=manifest.run_id,
                    run_id=manifest.run_id,
                    relationship="initial" if index == 0 else "unchanged_retry",
                    package_identity_sha256=envelope.package_identity_sha256 or manifest.run_id,
                )
        else:
            current = VariationAttempt(
                attempt_id=manifest.run_id,
                run_id=manifest.run_id,
                relationship="initial" if index == 0 else "unchanged_retry",
                package_identity_sha256=manifest.run_id,
            )
        attempts_by_run[manifest.run_id] = current
    if len(identities) > 1:
        conflict_reasons.append(
            "Attempts grouped under one Simulation ID have different full scientific or "
            "numerical identities."
        )
    missing_claims = sorted(accepted_claims - set(by_run))
    if missing_claims:
        conflict_reasons.append(
            "Accepted-backing claims reference missing attempts: " + ", ".join(missing_claims)
        )
    if len(accepted_claims) > 1:
        conflict_reasons.append(
            "Multiple attempts claim accepted backing: " + ", ".join(sorted(accepted_claims))
        )

    accepted_run_id = next(iter(accepted_claims), None) if len(accepted_claims) == 1 else None
    if accepted_run_id is None and not conflict_reasons:
        for manifest, path in ordered:
            inspectable, _message = _variation_inspectability(manifest, path)
            if inspectable:
                accepted_run_id = manifest.run_id
                break
    selected_manifest, selected_path = (
        by_run[accepted_run_id]
        if accepted_run_id is not None and accepted_run_id in by_run
        else ordered[-1]
    )
    attempts = tuple(
        attempt.model_copy(update={"accepted_backing": attempt.run_id == accepted_run_id})
        for attempt in attempts_by_run.values()
    )
    return _VariationSelection(
        manifest=selected_manifest,
        manifest_path=selected_path,
        attempts=attempts,
        accepted_backing=accepted_run_id is not None,
        conflict_reason=" ".join(conflict_reasons) or None,
    )


def _variation_record(
    manifest: RunManifest,
    manifest_path: Path,
    *,
    attempts: tuple[VariationAttempt, ...] = (),
    accepted_backing: bool = False,
    conflict_reason: str | None = None,
) -> MountainWavesSimulationRecord | None:
    configuration = manifest.run_configuration
    simulation_id = _string(configuration.get("simulation_id"))
    display_name = _string(configuration.get("simulation_display_name"))
    if not simulation_id or not display_name:
        return None
    exact_configuration = configuration.get("mountain_waves_configuration")
    moist = _configuration_is_moist(exact_configuration)
    inspectable, inspectability_message = _variation_inspectability(manifest, manifest_path)
    if conflict_reason:
        inspectable = False
        inspectability_message = conflict_reason
    envelope = _variation_envelope(configuration)
    legacy_contract = envelope is None
    if inspectable and envelope is not None:
        envelope = _promote_variation_envelope(
            manifest,
            manifest_path,
            envelope,
            attempts=attempts,
            accepted_backing=accepted_backing,
        )
    state = (
        "available"
        if inspectable
        else (
            "conflict"
            if conflict_reason
            else "conflict"
            if manifest.lifecycle_state
            in {LifecycleState.COMPLETED, LifecycleState.INGESTED, LifecycleState.SAVED}
            else _state_from_lifecycle(manifest.lifecycle_state)
        )
    )
    differences = (
        _grouped_envelope_differences(envelope)
        if envelope is not None
        else configuration.get("configuration_difference")
    )
    warning_values = configuration.get("warnings")
    scientific_design = (
        envelope.get("scientific_design", {}).get("payload")
        if isinstance(envelope, dict) and isinstance(envelope.get("scientific_design"), dict)
        else None
    )
    numerical_realization = (
        envelope.get("numerical_realization", {}).get("payload")
        if isinstance(envelope, dict) and isinstance(envelope.get("numerical_realization"), dict)
        else None
    )
    observation_plan = (
        envelope.get("observation_plan", {}).get("payload")
        if isinstance(envelope, dict) and isinstance(envelope.get("observation_plan"), dict)
        else None
    )
    return MountainWavesSimulationRecord(
        simulation_id=simulation_id,
        display_name=display_name,
        role="variation",
        run_id=manifest.run_id,
        case_id=manifest.scenario.id,
        parent_simulation_id=_string(configuration.get("parent_simulation_id")),
        parent_run_id=_string(configuration.get("parent_run_id")),
        user_question=_string(configuration.get("user_question")),
        recipe_id=(
            _string(envelope.get("recipe_id")) if envelope is not None else manifest.recipe_id
        ),
        recipe_contract_version=(
            _string(envelope.get("recipe_contract_version")) if envelope is not None else None
        ),
        relationship_classification=(
            _string(envelope.get("relationship_classification")) if envelope is not None else None
        ),
        legacy_contract=legacy_contract,
        parent_eligibility_reason=(
            _string(envelope.get("parent_eligibility_reason"))
            if envelope is not None
            else (
                "This Legacy-contract Simulation remains inspectable but cannot parent "
                "a new Recipe variation."
            )
        ),
        state=state,
        state_message=(
            f"Attempt backing is conflicted: {conflict_reason}"
            if conflict_reason
            else _variation_state_message(manifest, inspectable, inspectability_message)
        ),
        inspectable=inspectable,
        can_create_variation=(
            inspectable and envelope is not None and envelope.get("parent_eligible") is True
        ),
        moist=moist,
        moist_fields_available=True,
        purpose=(
            "Explore this retained Recipe variation and its exact relationship to the parent."
            if envelope is not None
            else (
                "Explore this retained Legacy-contract Simulation. Its earlier technical "
                "configuration remains available for evidence, not as a new parent."
            )
        ),
        configuration=exact_configuration if isinstance(exact_configuration, dict) else None,
        scientific_design=(scientific_design if isinstance(scientific_design, dict) else None),
        numerical_realization=(
            numerical_realization if isinstance(numerical_realization, dict) else None
        ),
        observation_plan=observation_plan if isinstance(observation_plan, dict) else None,
        differences=(
            {str(key): value for key, value in differences.items() if isinstance(value, list)}
            if isinstance(differences, dict)
            else {}
        ),
        warnings=(
            [str(value) for value in warning_values]
            if isinstance(warning_values, list)
            else list(manifest.outputs.runtime_warnings)
        ),
        caveats=list(manifest.run_caveats),
        manifest_path=str(manifest_path),
        created_at=manifest.created_at.isoformat(),
        started_at=_iso(manifest.execution.started_at),
        completed_at=_iso(manifest.execution.finished_at),
    )


def _built_in_configuration(manifest: RunManifest, spec: _BuiltInSpec) -> dict[str, Any]:
    configuration = manifest.run_configuration
    return {
        "duration_seconds": configuration.get("duration_seconds"),
        "output_cadence_seconds": configuration.get("output_cadence_seconds"),
        "domain": configuration.get("domain"),
        "terrain": configuration.get("terrain")
        or (
            {"height_m": 2000.0, "half_width_m": 10000.0, "center_m": 500.0} if spec.moist else None
        ),
    }


def _built_in_layers(
    manifest: RunManifest,
    *,
    configuration: dict[str, Any],
    recipe_id: RecipeId,
    moist: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    launch = manifest.run_configuration.get("launch_specification")
    launch = launch if isinstance(launch, dict) else {}
    numerical = launch.get("numerical_realization")
    observation = launch.get("observation_plan")
    domain = configuration.get("domain")
    domain = domain if isinstance(domain, dict) else {}
    if not isinstance(numerical, dict):
        numerical = {
            "domain": domain,
            "physics_source": manifest.run_configuration.get("physics_source")
            or manifest.scenario.id,
        }
    if not isinstance(observation, dict):
        observation = {
            "duration_seconds": configuration.get("duration_seconds"),
            "output_cadence_seconds": configuration.get("output_cadence_seconds"),
            "expected_history_count": len(manifest.outputs.netcdf_paths),
            "retained_field_inventory": manifest.required_output_fields,
        }
    reference_controls = default_controls(recipe_id)
    scientific = {
        "world_id": WORLD_ID,
        "recipe_id": recipe_id,
        "recipe_contract_version": "1",
        "controls": reference_controls.payload(),
        "fixed_assumptions": {
            "native_geometry": "two-dimensional x-z with singleton y",
            "moist": moist,
        },
    }
    return scientific, numerical, observation


def _built_in_inspectability(
    settings: CloudChamberSettings, spec: _BuiltInSpec, manifest: RunManifest
) -> tuple[bool, str]:
    key = ("built_in", spec.simulation_id, _manifest_artifact_fingerprint(manifest))
    cached = _inspectability_cache_get(key)
    if cached is not None:
        return cached
    result = _evaluate_built_in_inspectability(settings, spec, manifest)
    _inspectability_cache_put(key, result)
    return result


def _evaluate_built_in_inspectability(
    settings: CloudChamberSettings, spec: _BuiltInSpec, manifest: RunManifest
) -> tuple[bool, str]:
    if manifest.lifecycle_state != LifecycleState.COMPLETED or manifest.execution.exit_code != 0:
        return False, "Preserved output is not a completed zero-exit CM1 run."
    try:
        before = _verify_presentation_built_in(settings, spec, manifest)
        native_validation = _validate_manifest_native_outputs(
            manifest, moist_fields_available=spec.moist
        )
        after = _verify_presentation_built_in(settings, spec, manifest)
        if before != after:
            raise ValueError("Preserved artifacts changed during inspectability validation.")
        if native_validation != before["world_validation"]:
            raise ValueError("Presentation evidence disagrees with native World validation.")
    except (
        OSError,
        ValueError,
        GeneratedInputIdentityError,
        MountainWaveTerrainVisualizationError,
        PresentationRunError,
    ) as exc:
        return False, f"Preserved output failed strict identity or native-data validation: {exc}"
    return True, "Exact preserved output passed strict identity and native-data validation."


def _verify_presentation_built_in(
    settings: CloudChamberSettings, spec: _BuiltInSpec, manifest: RunManifest
) -> dict[str, Any]:
    presentation_spec = spec_by_key(spec.presentation_key)
    if (
        presentation_spec.run_id != spec.run_id
        or presentation_spec.case_id != spec.case_id
        or presentation_spec.moist_terrain != spec.moist
    ):
        raise ValueError("Mountain Waves presentation identity conflicts with the built-in spec.")
    package = load_presentation_package(settings=settings, spec=presentation_spec)
    generated_manifest_path = manifest.generated_inputs.manifest_path
    if generated_manifest_path is None:
        raise ValueError("Mountain Waves preserved run has no generated-input manifest path.")
    if package.manifest_path.resolve() != Path(generated_manifest_path).resolve():
        raise ValueError("Mountain Waves presentation manifest path conflicts with the package.")
    verified_inputs = verify_generated_input_identity(manifest)
    evidence_path = package.package_dir / "presentation_run_evidence.json"
    evidence_bytes = evidence_path.read_bytes()
    evidence = PresentationRunEvidence.model_validate_json(evidence_bytes)
    expected_grid = {
        "nx": presentation_spec.nx,
        "ny": presentation_spec.ny,
        "nz": presentation_spec.nz,
        "dx_m": presentation_spec.dx_m,
        "dy_m": presentation_spec.dy_m,
        "dz_m": presentation_spec.dz_m,
    }
    expected_world_validation = {
        "history_count": len(presentation_spec.expected_times_seconds),
        "times_seconds": list(presentation_spec.expected_times_seconds),
        "required_fields": sorted(
            MOUNTAIN_WAVES_EXPLORE_REQUIRED_FIELDS
            if spec.moist
            else MOUNTAIN_WAVES_EXPLORE_REQUIRED_FIELDS - {"qv", "ql"}
        ),
        "required_coordinates": sorted(MOUNTAIN_WAVES_EXPLORE_REQUIRED_COORDINATES),
        "run_id": spec.run_id,
        "implementation_commit": manifest.app.commit or "unknown",
    }
    checks = {
        "run_id": (evidence.run_id, spec.run_id),
        "world": (evidence.world, WORLD_ID),
        "case_id": (evidence.case_id, spec.case_id),
        "implementation_commit": (evidence.implementation_commit, manifest.app.commit),
        "grid": (evidence.grid, expected_grid),
        "duration_seconds": (evidence.duration_seconds, presentation_spec.duration_seconds),
        "output_cadence_seconds": (
            evidence.output_cadence_seconds,
            presentation_spec.output_cadence_seconds,
        ),
        "history_count": (evidence.history_count, len(presentation_spec.expected_times_seconds)),
        "times_seconds": (evidence.times_seconds, list(presentation_spec.expected_times_seconds)),
        "normal_completion": (evidence.normal_completion, True),
        "world_validation": (evidence.world_validation, expected_world_validation),
    }
    mismatches = {
        name: {"actual": actual, "expected": expected}
        for name, (actual, expected) in checks.items()
        if actual != expected
    }
    if mismatches:
        raise ValueError(f"Mountain Waves presentation evidence conflicts: {mismatches}")
    return {
        "generated_input_sha256": verified_inputs,
        "presentation_evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
        "world_validation": expected_world_validation,
    }


def _validate_manifest_native_outputs(
    manifest: RunManifest, *, moist_fields_available: bool
) -> dict[str, Any]:
    return validate_mountain_waves_native_outputs(
        output_paths=[Path(path).expanduser() for path in manifest.outputs.netcdf_paths],
        namelist_path=Path(manifest.generated_inputs.namelist_input or "").expanduser(),
        run_id=manifest.run_id,
        implementation_commit=manifest.app.commit or "unknown",
        moist_fields_available=moist_fields_available,
    )


def _variation_inspectability(manifest: RunManifest, manifest_path: Path) -> tuple[bool, str]:
    key = (
        "variation",
        str(manifest_path.expanduser().resolve()),
        _manifest_artifact_fingerprint(manifest),
    )
    cached = _inspectability_cache_get(key)
    if cached is not None:
        return cached
    result = _evaluate_variation_inspectability(manifest, manifest_path)
    _inspectability_cache_put(key, result)
    return result


def _evaluate_variation_inspectability(
    manifest: RunManifest, manifest_path: Path
) -> tuple[bool, str]:
    if manifest.lifecycle_state not in {
        LifecycleState.COMPLETED,
        LifecycleState.INGESTED,
        LifecycleState.SAVED,
    }:
        return False, f"Output is {manifest.lifecycle_state.value} and is not inspectable yet."
    if (
        manifest.execution.exit_code != 0
        or manifest.execution.started_at is None
        or manifest.execution.finished_at is None
        or manifest.provenance.product_state != ProductState.COMPLETED_CM1_RESULT
    ):
        return False, "Completed output lacks normal zero-exit process evidence."
    exact_configuration = manifest.run_configuration.get("mountain_waves_configuration")
    moist_fields_available = _configuration_is_moist(exact_configuration)
    required_fields = (
        MOUNTAIN_WAVES_EXPLORE_REQUIRED_FIELDS
        if moist_fields_available
        else MOUNTAIN_WAVES_EXPLORE_REQUIRED_FIELDS - {"qv", "ql"}
    )
    missing_contract_fields = sorted(required_fields - set(manifest.required_output_fields))
    if missing_contract_fields:
        return False, (
            "Completed output does not declare every Explore field: "
            + ", ".join(missing_contract_fields)
            + "."
        )
    run_dir = Path(manifest.generated_inputs.run_directory).expanduser().resolve()
    output_paths = [Path(path).expanduser().resolve() for path in manifest.outputs.netcdf_paths]
    escaped = [path.name for path in output_paths if not path.is_relative_to(run_dir)]
    if escaped:
        return False, f"Completed output inventory escapes its retained run: {escaped}."
    try:
        verify_generated_input_identity(manifest)
        validation = validate_mountain_waves_native_outputs(
            output_paths=output_paths,
            namelist_path=Path(manifest.generated_inputs.namelist_input or "").expanduser(),
            run_id=manifest.run_id,
            implementation_commit=manifest.app.commit or "unknown",
            moist_fields_available=moist_fields_available,
        )
    except (
        OSError,
        ValueError,
        GeneratedInputIdentityError,
        MountainWaveTerrainVisualizationError,
    ) as exc:
        return False, f"Completed output failed native-data validation: {exc}"
    return True, (
        f"CM1 completed normally with {validation['history_count']} exact native histories "
        "ready for inspection."
    )


def clear_mountain_waves_inspectability_cache() -> None:
    """Clear in-process promotion decisions; intended for bounded test isolation."""
    with _INSPECTABILITY_CACHE_LOCK:
        _INSPECTABILITY_CACHE.clear()


def _manifest_artifact_fingerprint(
    manifest: RunManifest,
) -> tuple[tuple[str, int, int, int], ...]:
    manifest_digest = hashlib.sha256(manifest.model_dump_json().encode("utf-8")).hexdigest()
    fingerprint: list[tuple[str, int, int, int]] = [
        ("__manifest__", 0, 0, int(manifest_digest[:16], 16))
    ]
    run_dir = Path(manifest.generated_inputs.run_directory).expanduser().resolve()
    paths = (
        sorted(path for path in run_dir.rglob("*") if path.is_file()) if run_dir.exists() else []
    )
    for path in paths:
        try:
            stat = path.stat()
        except OSError:
            fingerprint.append((str(path), -1, -1, -1))
            continue
        fingerprint.append((str(path), stat.st_size, stat.st_mtime_ns, stat.st_ino))
    return tuple(fingerprint)


def _inspectability_cache_get(
    key: tuple[str, str, tuple[tuple[str, int, int, int], ...]],
) -> tuple[bool, str] | None:
    with _INSPECTABILITY_CACHE_LOCK:
        value = _INSPECTABILITY_CACHE.get(key)
        if value is not None:
            _INSPECTABILITY_CACHE.move_to_end(key)
        return value


def _inspectability_cache_put(
    key: tuple[str, str, tuple[tuple[str, int, int, int], ...]],
    value: tuple[bool, str],
) -> None:
    with _INSPECTABILITY_CACHE_LOCK:
        _INSPECTABILITY_CACHE[key] = value
        _INSPECTABILITY_CACHE.move_to_end(key)
        while len(_INSPECTABILITY_CACHE) > _INSPECTABILITY_CACHE_LIMIT:
            _INSPECTABILITY_CACHE.popitem(last=False)


def _state_from_lifecycle(state: LifecycleState) -> SimulationState:
    if state == LifecycleState.PACKAGED:
        return "packaged"
    if state == LifecycleState.QUEUED:
        return "queued"
    if state == LifecycleState.RUNNING:
        return "running"
    if state == LifecycleState.CANCELED:
        return "canceled"
    if state == LifecycleState.FAILED:
        return "failed"
    return "unavailable"


def _variation_state_message(
    manifest: RunManifest, inspectable: bool, inspectability_message: str
) -> str:
    if inspectable:
        return inspectability_message
    if manifest.lifecycle_state in {
        LifecycleState.COMPLETED,
        LifecycleState.INGESTED,
        LifecycleState.SAVED,
    }:
        return inspectability_message
    return {
        LifecycleState.PACKAGED: "Configuration is packaged and ready to run.",
        LifecycleState.QUEUED: "Waiting for the local CM1 runner.",
        LifecycleState.RUNNING: "CM1 is running locally.",
        LifecycleState.FAILED: "The attempt failed and remains in Lab history.",
        LifecycleState.CANCELED: "The attempt was canceled and remains in Lab history.",
    }.get(manifest.lifecycle_state, "Output is not inspectable.")


def _configuration_is_moist(configuration: object) -> bool:
    if not isinstance(configuration, dict):
        return False
    sounding = configuration.get("sounding")
    if not isinstance(sounding, list):
        return False
    return any(
        isinstance(level, dict)
        and isinstance(level.get("qv_g_kg"), int | float)
        and float(level["qv_g_kg"]) > 0.0
        for level in sounding
    )


def _variation_envelope(configuration: dict[str, Any]) -> dict[str, Any] | None:
    payload = configuration.get("variation_envelope")
    if not isinstance(payload, dict):
        return None
    try:
        envelope = VariationEnvelope.model_validate(payload)
    except ValueError:
        return None
    if (
        envelope.world_id != WORLD_ID
        or envelope.recipe_id not in {"dry_ridge_mechanics", "boulder_moist_wave"}
        or envelope.recipe_contract_version != "1"
    ):
        return None
    return envelope.model_dump(mode="json")


def _grouped_envelope_differences(
    envelope: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {
        "terrain": [],
        "wind": [],
        "moisture": [],
        "stability/thermodynamics": [],
        "forcing/initiation": [],
        "numerical realization": [],
        "observation plan": [],
    }
    names = {
        "terrain": "terrain",
        "wind": "wind",
        "moisture": "moisture",
        "stability_thermodynamics": "stability/thermodynamics",
        "forcing_initiation": "forcing/initiation",
        "numerical_realization": "numerical realization",
        "observation_plan": "observation plan",
    }
    differences = envelope.get("differences")
    if not isinstance(differences, list):
        return groups
    for difference in differences:
        if not isinstance(difference, dict):
            continue
        group = names.get(str(difference.get("category")))
        if group is not None:
            groups[group].append(
                {
                    key: difference.get(key)
                    for key in ("path", "label", "before", "after", "units", "material")
                }
            )
    return groups


def _promote_variation_envelope(
    manifest: RunManifest,
    manifest_path: Path,
    envelope: dict[str, Any],
    *,
    attempts: tuple[VariationAttempt, ...],
    accepted_backing: bool,
) -> dict[str, Any]:
    caveated = bool(manifest.run_caveats or manifest.outputs.runtime_warnings)
    parent_eligible, parent_reason = _evaluate_variation_parent_eligibility(
        manifest,
        envelope,
        accepted_backing=accepted_backing,
    )
    promoted = {
        **envelope,
        "attempts": [attempt.model_dump(mode="json") for attempt in attempts],
        "availability_state": "available_with_caveats" if caveated else "available",
        "parent_eligible": parent_eligible,
        "parent_eligibility_reason": parent_reason,
    }
    decisions = promoted.get("validation_decisions")
    if isinstance(decisions, list):
        replacements = {
            "attempt_integrity": (
                "passed",
                (
                    "Generated-input identity, normal completion, and accepted-backing "
                    "selection are coherent."
                    if accepted_backing
                    else "Generated-input identity and normal completion are coherent; "
                    "this attempt remains alternate output."
                ),
            ),
            "output_completeness": (
                "passed",
                "Required native histories and fields passed strict validation.",
            ),
            "world_inspectability": (
                "passed",
                "Mountain Waves Explore can inspect the retained output.",
            ),
            "availability": (
                "caveated" if caveated else "passed",
                (
                    "Simulation is available with retained runtime caveats."
                    if caveated
                    else "Simulation is available."
                ),
            ),
            "parent_eligibility": (
                "passed" if parent_eligible else "failed",
                parent_reason,
            ),
        }
        retained = [
            decision
            for decision in decisions
            if isinstance(decision, dict) and decision.get("stage") not in replacements
        ]
        promoted["validation_decisions"] = [
            *retained,
            *[
                {"stage": stage, "disposition": disposition, "reason": reason}
                for stage, (disposition, reason) in replacements.items()
            ],
        ]
    if promoted != envelope:
        manifest.run_configuration["variation_envelope"] = promoted
        try:
            write_run_manifest(manifest_path, manifest)
        except OSError:
            return envelope
    return promoted


def _evaluate_variation_parent_eligibility(
    manifest: RunManifest,
    envelope: dict[str, Any],
    *,
    accepted_backing: bool,
) -> tuple[bool, str]:
    if not accepted_backing:
        return False, "Only the accepted backing attempt can support descendant creation."
    if (
        envelope.get("recipe_id") != BOULDER_RECIPE_ID
        or envelope.get("recipe_contract_version") != "1"
    ):
        return False, "The retained Simulation is outside the current Boulder Recipe contract."
    world_payload = envelope.get("world_payload")
    controls_payload = world_payload.get("controls") if isinstance(world_payload, dict) else None
    if not isinstance(controls_payload, dict):
        return False, "The retained Simulation lacks reconstructible absolute Recipe controls."
    try:
        controls = MountainWavesRecipeControls.model_validate(controls_payload)
        normalized = normalize_recipe_controls(
            controls,
            recipe_reference=default_controls(BOULDER_RECIPE_ID),
        )
    except ValueError:
        return False, "The retained Simulation's absolute Recipe controls are invalid."
    if controls != normalized:
        return False, "The retained Simulation contains unresolved inactive Recipe controls."
    try:
        verify_generated_input_identity(manifest)
    except (OSError, ValueError, GeneratedInputIdentityError):
        return False, "Generated source assets no longer match the retained package identity."
    provenance = manifest.run_configuration.get("cm1_provenance")
    expected_provenance = {
        "release": CM1_RELEASE,
        "official_tag_commit": CM1_TAG_COMMIT,
        "official_source_tag": CM1_SOURCE_TAG,
        "executable_sha256": CM1_EXECUTABLE_SHA256,
        "source_manifest_sha256": CM1_SOURCE_MANIFEST_SHA256,
        "readme_namelist_sha256": CM1_README_NAMELIST_SHA256,
        "readme_terrain_sha256": CM1_README_TERRAIN_SHA256,
        "mountain_wave_namelist_sha256": CM1_MOUNTAIN_WAVE_NAMELIST_SHA256,
        "critical_source_sha256": CRITICAL_SOURCE_HASHES,
    }
    if not isinstance(provenance, dict) or any(
        provenance.get(key) != value for key, value in expected_provenance.items()
    ):
        return False, "Retained CM1 source or executable provenance is outside the pinned contract."
    diagnostics = world_payload.get("diagnostics") if isinstance(world_payload, dict) else None
    observation = envelope.get("observation_plan")
    observation_payload = observation.get("payload") if isinstance(observation, dict) else None
    duration = (
        observation_payload.get("duration_seconds")
        if isinstance(observation_payload, dict)
        else None
    )
    if not isinstance(diagnostics, dict) or not isinstance(duration, int | float):
        return False, "The retained Simulation lacks reconstructible boundary diagnostics."
    wrap = diagnostics.get("periodic_wrap_time_seconds")
    damping = diagnostics.get("damping_base_m")
    model_top = diagnostics.get("model_top_m")
    terrain = world_payload.get("terrain") if isinstance(world_payload, dict) else None
    terrain_height = terrain.get("height_m") if isinstance(terrain, dict) else None
    if not all(
        isinstance(value, int | float) for value in (wrap, damping, model_top, terrain_height)
    ):
        return False, "The retained Simulation's domain or damping evidence is incomplete."
    assert isinstance(wrap, int | float)
    assert isinstance(damping, int | float)
    assert isinstance(model_top, int | float)
    assert isinstance(terrain_height, int | float)
    if float(wrap) < 1.15 * float(duration):
        return False, "Periodic-wrap protection is insufficient for descendant reuse."
    if float(damping) <= float(terrain_height) or float(damping) >= float(model_top):
        return False, "Model-top and damping separation is not valid for descendant reuse."
    blocking_caveat_terms = (
        "outside the currently supported",
        "wrap-contaminated",
        "uncharacterized",
        "unresolved terrain",
    )
    caveats = [*manifest.run_caveats, *manifest.outputs.runtime_warnings]
    if any(term in caveat.lower() for caveat in caveats for term in blocking_caveat_terms):
        return False, "Retained caveats place this Simulation outside descendant reuse."
    return (
        True,
        "Accepted backing output remains reconstructible inside the current Boulder "
        "Recipe, source-asset, domain, and World inspection contracts.",
    )


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
