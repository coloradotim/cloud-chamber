"""Stable product identity and retained-output state for the Supercells World."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.generated_input_identity import (
    GeneratedInputIdentityError,
    verify_generated_input_identity,
)
from cloud_chamber.run_manifest import (
    LifecycleState,
    RunManifest,
    RunManifestError,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storm_examination import (
    DEFAULT_PRESENTATION_TIME_INDEX,
    PRESENTATION_CASE_ID,
    PRESENTATION_RUN_ID,
    QUARTER_CIRCLE_SIMULATION_ID,
    STRAIGHT_LINE_PRESENTATION_CASE_ID,
    STRAIGHT_LINE_PRESENTATION_RUN_ID,
    StormExaminationError,
    storm_examination_inventory,
    storm_examination_variation_inventory,
)
from cloud_chamber.storm_examination import (
    STRAIGHT_LINE_SIMULATION_ID as STORM_STRAIGHT_LINE_SIMULATION_ID,
)
from cloud_chamber.supercells_recipes import (
    RECIPE_CONTRACT_VERSION,
    RECIPE_ID,
    SupercellsControls,
    normalize_controls,
)
from cloud_chamber.supercells_source_customization import (
    PINNED_INIT3D_F_SHA256,
    SUPERCELLS_SOURCE_CUSTOMIZATION_FILENAME,
    SupercellsSourceCustomizationError,
    load_supercells_source_customization,
)
from cloud_chamber.variation_envelope import (
    VariationAttempt,
    VariationEnvelope,
    VariationValidationDecision,
    canonical_payload_sha256,
)

WORLD_ID: Literal["supercells"] = "supercells"
WORLD_DISPLAY_NAME: Literal["Supercells"] = "Supercells"
REFERENCE_SIMULATION_ID: Literal["supercells_quarter_circle_reference"] = (
    QUARTER_CIRCLE_SIMULATION_ID
)
STRAIGHT_LINE_SIMULATION_ID: Literal["supercells_straight_line_hodograph"] = (
    STORM_STRAIGHT_LINE_SIMULATION_ID
)
REFERENCE_DISPLAY_NAME: Literal["Quarter-Circle Supercell"] = "Quarter-Circle Supercell"
WORLD_SHORT_DESCRIPTION = (
    "A deep rotating thunderstorm for seeing organized ascent, rotation, hydrometeors, "
    "precipitation, and low-level flow evolve together."
)

AvailabilityState = Literal["available", "partial", "unavailable"]
TechnicalState = Literal["available", "missing", "invalid"]
SupercellSimulationId = str
VARIATION_CASE_ID = "supercells_recipe_variation_v1"


@dataclass(frozen=True)
class _VariationCandidate:
    manifest: RunManifest
    manifest_path: Path
    envelope: VariationEnvelope


class SupercellSimulationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: SupercellSimulationId
    display_name: str
    role: Literal["reference", "variation"]
    world_id: Literal["supercells"] = WORLD_ID
    run_id: str
    case_id: str
    parent_simulation_id: str | None = None
    reference_simulation_id: str = REFERENCE_SIMULATION_ID
    technical_state: TechnicalState
    technical_state_message: str
    explore_available: bool
    saved_output_count: int
    model_start_seconds: float | None
    model_end_seconds: float | None
    history_cadence_seconds: float | None
    default_explore_time_index: int = DEFAULT_PRESENTATION_TIME_INDEX
    lineage_state: Literal["known"] = "known"
    recipe_contract_version: str = "1"
    relationship_classification: str | None = None
    run_profile_id: str = "supercells_presentation_v1"
    can_create_variation: bool = False
    parent_eligibility_reason: str


class SupercellsCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_explore: bool
    lab: Literal[False] = False
    compare: bool
    saved_views: Literal[False] = False
    saved_comparisons: Literal[True] = True
    create_variation: bool


class SupercellsWorldSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: Literal["supercells"] = WORLD_ID
    display_name: Literal["Supercells"] = WORLD_DISPLAY_NAME
    short_description: str = WORLD_SHORT_DESCRIPTION
    reference_simulation_id: Literal["supercells_quarter_circle_reference"] = (
        REFERENCE_SIMULATION_ID
    )
    reference_available: bool
    simulation_count: int
    saved_view_count: Literal[0] = 0
    saved_comparison_count: int = 0
    featured_comparison_count: Literal[0] = 0
    active_run_count: Literal[0] = 0
    completed_uninspected_run_count: Literal[0] = 0
    availability_state: AvailabilityState
    availability_message: str


class SupercellsWorldDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: Literal["supercells"] = WORLD_ID
    display_name: Literal["Supercells"] = WORLD_DISPLAY_NAME
    short_description: str = WORLD_SHORT_DESCRIPTION
    availability_state: AvailabilityState
    availability_message: str
    reference_simulation: SupercellSimulationRecord
    simulations: list[SupercellSimulationRecord]
    capabilities: SupercellsCapabilities
    caveats: list[str] = Field(default_factory=list)

    def summary(self) -> SupercellsWorldSummary:
        available = [item for item in self.simulations if item.technical_state == "available"]
        return SupercellsWorldSummary(
            reference_available=self.reference_simulation.technical_state == "available",
            simulation_count=len(available),
            availability_state=self.availability_state,
            availability_message=self.availability_message,
        )


def supercells_world_detail(settings: CloudChamberSettings) -> SupercellsWorldDetail:
    """Resolve retained Supercell Simulations without exposing machine-private paths."""
    simulations = [
        _simulation_record(
            settings,
            simulation_id=REFERENCE_SIMULATION_ID,
            display_name=REFERENCE_DISPLAY_NAME,
            role="reference",
            run_id=PRESENTATION_RUN_ID,
            case_id=PRESENTATION_CASE_ID,
            parent_simulation_id=None,
        ),
        _simulation_record(
            settings,
            simulation_id=STRAIGHT_LINE_SIMULATION_ID,
            display_name="Straight-Line Hodograph Supercell",
            role="variation",
            run_id=STRAIGHT_LINE_PRESENTATION_RUN_ID,
            case_id=STRAIGHT_LINE_PRESENTATION_CASE_ID,
            parent_simulation_id=REFERENCE_SIMULATION_ID,
        ),
        *_variation_simulation_records(settings),
    ]
    reference = simulations[0]
    available_count = sum(item.technical_state == "available" for item in simulations)
    if available_count == len(simulations):
        availability_state: AvailabilityState = "available"
        availability_message = (
            f"{available_count} retained Supercell Simulations are available "
            "for Explore and Compare."
        )
    elif available_count:
        availability_state = "partial"
        availability_message = (
            "Only one retained Supercell Simulation is currently available for Explore."
        )
    else:
        availability_state = "unavailable"
        availability_message = "Retained Supercell output is not available for Explore."
    return SupercellsWorldDetail(
        availability_state=availability_state,
        availability_message=availability_message,
        reference_simulation=reference,
        simulations=simulations,
        capabilities=SupercellsCapabilities(
            reference_explore=reference.explore_available,
            compare=available_count >= 2,
            create_variation=any(item.can_create_variation for item in simulations),
        ),
        caveats=[
            "These are idealized matched simulations, not observed storms.",
            "The controlled atmospheric difference is hodograph curvature; thermodynamics, "
            "trigger, grid, timing, output inventory, and numerical experiment are matched.",
            "Horizontal coordinates and winds use the same translating model frame.",
            "Coordinates and local evidence are comparable; storm objects and split lineage "
            "are not inferred between Simulations.",
        ],
    )


def _variation_simulation_records(
    settings: CloudChamberSettings,
) -> list[SupercellSimulationRecord]:
    by_simulation: dict[str, list[_VariationCandidate]] = defaultdict(list)
    run_root = settings.runtime_home.expanduser() / "runs"
    for manifest_path in sorted(run_root.glob("*/run_manifest.json")):
        try:
            manifest = load_run_manifest(manifest_path)
            envelope = VariationEnvelope.model_validate(
                manifest.run_configuration.get("variation_envelope")
            )
        except (OSError, RunManifestError, ValueError):
            continue
        if (
            manifest.lifecycle_state != LifecycleState.COMPLETED
            or manifest.scenario.id != VARIATION_CASE_ID
            or envelope.world_id != WORLD_ID
            or envelope.recipe_id != RECIPE_ID
        ):
            continue
        by_simulation[envelope.simulation_id].append(
            _VariationCandidate(
                manifest=manifest,
                manifest_path=manifest_path,
                envelope=envelope,
            )
        )

    records = [
        _variation_simulation_record(settings, simulation_id, candidates)
        for simulation_id, candidates in by_simulation.items()
    ]
    return sorted(records, key=lambda item: (item.display_name, item.simulation_id))


def _variation_simulation_record(
    settings: CloudChamberSettings,
    simulation_id: str,
    candidates: list[_VariationCandidate],
) -> SupercellSimulationRecord:
    ordered = sorted(
        candidates,
        key=lambda item: (item.manifest.created_at, item.manifest.run_id),
    )
    accepted_claims = {
        attempt.run_id
        for candidate in ordered
        for attempt in candidate.envelope.attempts
        if attempt.accepted_backing
    }
    candidates_by_run = {candidate.manifest.run_id: candidate for candidate in ordered}
    conflict_reason: str | None = None
    if len(accepted_claims) > 1:
        conflict_reason = "Multiple completed attempts claim accepted backing."
    elif accepted_claims and not accepted_claims.issubset(candidates_by_run):
        conflict_reason = "Accepted backing refers to a missing retained attempt."
    if (
        len(
            {
                (
                    candidate.envelope.scientific_design.sha256,
                    candidate.envelope.numerical_realization.sha256,
                )
                for candidate in ordered
            }
        )
        > 1
    ):
        conflict_reason = (
            "Attempts grouped under this Simulation disagree on scientific or numerical identity."
        )

    selected: _VariationCandidate | None = None
    inventory: tuple[tuple[Path, float], ...] | None = None
    validation_errors: list[str] = []
    if conflict_reason is None and len(accepted_claims) == 1:
        selected = candidates_by_run[next(iter(accepted_claims))]
        try:
            inventory = storm_examination_variation_inventory(
                settings,
                selected.manifest_path,
            )
        except StormExaminationError as exc:
            validation_errors.append(str(exc))
    elif conflict_reason is None:
        for candidate in ordered:
            try:
                inventory = storm_examination_variation_inventory(
                    settings,
                    candidate.manifest_path,
                )
            except StormExaminationError as exc:
                validation_errors.append(str(exc))
                continue
            selected = candidate
            break

    candidate = selected or ordered[-1]
    envelope = candidate.envelope
    if conflict_reason is not None or inventory is None:
        reason = conflict_reason or (
            validation_errors[-1]
            if validation_errors
            else "Completed output did not pass Supercells World validation."
        )
        return SupercellSimulationRecord(
            simulation_id=simulation_id,
            display_name=envelope.display_name,
            role="variation",
            run_id=candidate.manifest.run_id,
            case_id=candidate.manifest.scenario.id,
            parent_simulation_id=envelope.parent_simulation_id,
            technical_state="invalid",
            technical_state_message=reason,
            explore_available=False,
            saved_output_count=0,
            model_start_seconds=None,
            model_end_seconds=None,
            history_cadence_seconds=None,
            recipe_contract_version=envelope.recipe_contract_version,
            relationship_classification=envelope.relationship_classification,
            run_profile_id=envelope.run_profile_id,
            can_create_variation=False,
            parent_eligibility_reason=reason,
        )

    attempts = _variation_attempts(ordered, accepted_run_id=candidate.manifest.run_id)
    promoted = _promote_variation_envelope(
        candidate,
        attempts=attempts,
        accepted_backing=True,
    )
    times = [item[1] for item in inventory]
    cadence = times[1] - times[0] if len(times) > 1 else None
    caveated = promoted.availability_state == "available_with_caveats"
    return SupercellSimulationRecord(
        simulation_id=simulation_id,
        display_name=promoted.display_name,
        role="variation",
        run_id=candidate.manifest.run_id,
        case_id=candidate.manifest.scenario.id,
        parent_simulation_id=promoted.parent_simulation_id,
        technical_state="available",
        technical_state_message=(
            "Complete native output passed the Supercells Recipe and all-three-Lens contract"
            + (" with retained caveats." if caveated else ".")
        ),
        explore_available=True,
        saved_output_count=len(times),
        model_start_seconds=times[0],
        model_end_seconds=times[-1],
        history_cadence_seconds=cadence,
        default_explore_time_index=min(DEFAULT_PRESENTATION_TIME_INDEX, len(times) - 1),
        recipe_contract_version=promoted.recipe_contract_version,
        relationship_classification=promoted.relationship_classification,
        run_profile_id=promoted.run_profile_id,
        can_create_variation=promoted.parent_eligible,
        parent_eligibility_reason=promoted.parent_eligibility_reason,
    )


def _variation_attempts(
    candidates: list[_VariationCandidate],
    *,
    accepted_run_id: str,
) -> list[VariationAttempt]:
    attempts: dict[str, VariationAttempt] = {}
    for candidate in candidates:
        for attempt in candidate.envelope.attempts:
            attempts[attempt.run_id] = attempt
        attempts.setdefault(
            candidate.manifest.run_id,
            VariationAttempt(
                attempt_id=candidate.manifest.run_id,
                run_id=candidate.manifest.run_id,
                relationship="initial" if not attempts else "unchanged_retry",
                package_identity_sha256=(
                    candidate.envelope.package_identity_sha256
                    or candidate.envelope.scientific_design.sha256
                ),
            ),
        )
    return [
        attempt.model_copy(update={"accepted_backing": run_id == accepted_run_id})
        for run_id, attempt in sorted(attempts.items())
    ]


def _promote_variation_envelope(
    candidate: _VariationCandidate,
    *,
    attempts: list[VariationAttempt],
    accepted_backing: bool,
) -> VariationEnvelope:
    manifest = candidate.manifest
    envelope = candidate.envelope
    parent_eligible, parent_reason = _variation_parent_eligibility(
        candidate,
        accepted_backing=accepted_backing,
    )
    caveated = bool(manifest.run_caveats or manifest.outputs.runtime_warnings)
    replacements = {
        "attempt_integrity": (
            "passed",
            "Generated inputs, normal completion, and accepted backing are coherent.",
        ),
        "output_completeness": (
            "passed",
            "Expected histories, native fields, dimensions, units, cadence, and "
            "finite data passed.",
        ),
        "world_inspectability": (
            "passed",
            "Explore can render all three Supercells Lenses and native sections.",
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
        decision for decision in envelope.validation_decisions if decision.stage not in replacements
    ]
    updated = envelope.model_copy(
        update={
            "attempts": attempts,
            "availability_state": "available_with_caveats" if caveated else "available",
            "parent_eligible": parent_eligible,
            "parent_eligibility_reason": parent_reason,
            "validation_decisions": [
                *retained,
                *[
                    VariationValidationDecision.model_validate(
                        {
                            "stage": stage,
                            "disposition": disposition,
                            "reason": reason,
                        }
                    )
                    for stage, (disposition, reason) in replacements.items()
                ],
            ],
        }
    )
    if updated != envelope:
        manifest.run_configuration["variation_envelope"] = updated.model_dump(mode="json")
        try:
            write_run_manifest(candidate.manifest_path, manifest)
        except OSError:
            return envelope
    return updated


def _variation_parent_eligibility(
    candidate: _VariationCandidate,
    *,
    accepted_backing: bool,
) -> tuple[bool, str]:
    manifest = candidate.manifest
    envelope = candidate.envelope
    if not accepted_backing:
        return False, "Only the accepted backing attempt can parent a new variation."
    if manifest.run_configuration.get("characterization_authorization") is not None:
        return (
            False,
            "Characterization output requires explicit PM acceptance before descendant creation.",
        )
    if (
        envelope.recipe_id != RECIPE_ID
        or envelope.recipe_contract_version != RECIPE_CONTRACT_VERSION
    ):
        return False, "The retained Simulation is outside the current Supercells Recipe."
    controls_payload = envelope.world_payload.get("controls")
    try:
        controls = SupercellsControls.model_validate(controls_payload)
        normalized = normalize_controls(controls)
    except ValueError:
        return False, "The retained Simulation lacks valid absolute Recipe controls."
    if controls != normalized:
        return False, "The retained Simulation contains unresolved inactive controls."
    try:
        verify_generated_input_identity(manifest)
    except (GeneratedInputIdentityError, OSError):
        return False, "Generated inputs no longer match the retained package identity."
    customization_path = candidate.manifest_path.parent / SUPERCELLS_SOURCE_CUSTOMIZATION_FILENAME
    try:
        customization = load_supercells_source_customization(customization_path)
    except SupercellsSourceCustomizationError:
        return False, "The retained source customization identity is unavailable."
    if customization.get("original_source_sha256") != PINNED_INIT3D_F_SHA256:
        return False, "The retained source customization does not match pinned CM1 source."
    if customization.get("wind_profile_sha256") != canonical_payload_sha256(
        envelope.world_payload.get("hodograph")
    ) or customization.get("thermodynamic_profile_sha256") != canonical_payload_sha256(
        envelope.world_payload.get("sounding")
    ):
        return False, "The retained generated profiles do not match source customization."
    return (
        True,
        "Accepted output remains reconstructible inside Supercells Recipe contract version 1.",
    )


def _simulation_record(
    settings: CloudChamberSettings,
    *,
    simulation_id: SupercellSimulationId,
    display_name: str,
    role: Literal["reference", "variation"],
    run_id: str,
    case_id: str,
    parent_simulation_id: str | None,
) -> SupercellSimulationRecord:
    try:
        inventory = storm_examination_inventory(settings, simulation_id)
    except StormExaminationError as exc:
        message = str(exc)
        state: TechnicalState = "missing" if "unavailable" in message.lower() else "invalid"
        return SupercellSimulationRecord(
            simulation_id=simulation_id,
            display_name=display_name,
            role=role,
            run_id=run_id,
            case_id=case_id,
            parent_simulation_id=parent_simulation_id,
            technical_state=state,
            technical_state_message=message,
            explore_available=False,
            saved_output_count=0,
            model_start_seconds=None,
            model_end_seconds=None,
            history_cadence_seconds=None,
            can_create_variation=False,
            parent_eligibility_reason=message,
        )

    times = [item[1] for item in inventory]
    cadence = times[1] - times[0] if len(times) > 1 else None
    return SupercellSimulationRecord(
        simulation_id=simulation_id,
        display_name=display_name,
        role=role,
        run_id=run_id,
        case_id=case_id,
        parent_simulation_id=parent_simulation_id,
        technical_state="available",
        technical_state_message="Retained native CM1 output is ready for inspection.",
        explore_available=True,
        saved_output_count=len(times),
        model_start_seconds=times[0],
        model_end_seconds=times[-1],
        history_cadence_seconds=cadence,
        can_create_variation=True,
        parent_eligibility_reason=(
            "Accepted retained presentation evidence has a reconstructible "
            "Supercells Recipe contract."
        ),
    )
