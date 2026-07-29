"""Stable product identity and retained-output state for the Supercells World."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.generated_input_identity import (
    GeneratedInputIdentityError,
    verify_generated_input_identity,
)
from cloud_chamber.mountain_wave_case import parse_namelist_assignments, sha256_file
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
    storm_examination_interactions,
    storm_examination_inventory,
    storm_examination_variation_interactions,
    storm_examination_variation_inventory,
)
from cloud_chamber.storm_examination import (
    STRAIGHT_LINE_SIMULATION_ID as STORM_STRAIGHT_LINE_SIMULATION_ID,
)
from cloud_chamber.supercell_benchmark import (
    CM1_EXECUTABLE_SHA256,
    CM1_SOURCE_MANIFEST_SHA256,
    CRITICAL_SOURCE_SHA256,
    collect_cm1_provenance,
)
from cloud_chamber.supercell_hodograph import (
    PINNED_BASE_F_SHA256,
    STRAIGHT_LINE_HODOGRAPH_ARTIFACT_FILENAME,
    STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND,
    STRAIGHT_LINE_HODOGRAPH_TARGET,
    straight_line_hodograph_artifact,
)
from cloud_chamber.supercell_presentation import (
    BASE_PRESENTATION_ASSIGNMENTS,
    LOCKED_SCIENCE_ASSIGNMENTS,
    PRESENTATION_PROFILE_ID,
)
from cloud_chamber.supercells_recipes import (
    RECIPE_CONTRACT_VERSION,
    RECIPE_ID,
    SupercellsControls,
    default_controls,
    fixed_assumptions,
    generator_contract,
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
    grouped_differences,
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
    scientific_design: dict[str, Any] = Field(default_factory=dict)
    numerical_realization: dict[str, Any] = Field(default_factory=dict)
    observation_plan: dict[str, Any] = Field(default_factory=dict)
    world_payload: dict[str, Any] = Field(default_factory=dict)
    differences: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    run_profile_contract: dict[str, Any] = Field(default_factory=dict)


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
            "The original retained Quarter-Circle and Straight-Line pair differs only in "
            "hodograph curvature; other variation pairs use their exact retained envelopes.",
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
        if (
            envelope.relationship_classification == "observation_only_attempt"
            and envelope.simulation_id in {REFERENCE_SIMULATION_ID, STRAIGHT_LINE_SIMULATION_ID}
        ):
            # Built-in Simulations remain backed by their accepted presentation run.
            # Alternate observation attempts stay visible in lifecycle history without
            # creating a duplicate World record.
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
    if len({_intended_simulation_sha256(candidate.envelope) for candidate in ordered}) > 1:
        conflict_reason = (
            "Attempts grouped under this Simulation disagree on their complete intended-"
            "Simulation contract."
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
            scientific_design=envelope.scientific_design.payload,
            numerical_realization=envelope.numerical_realization.payload,
            observation_plan=envelope.observation_plan.payload,
            world_payload=envelope.world_payload,
            differences=grouped_differences(envelope.differences),
            run_profile_contract=envelope.run_profile_contract,
        )

    attempts = _variation_attempts(ordered, accepted_run_id=candidate.manifest.run_id)
    promoted = _promote_variation_envelope(
        settings,
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
        scientific_design=promoted.scientific_design.payload,
        numerical_realization=promoted.numerical_realization.payload,
        observation_plan=promoted.observation_plan.payload,
        world_payload=promoted.world_payload,
        differences=grouped_differences(promoted.differences),
        run_profile_contract=promoted.run_profile_contract,
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
    settings: CloudChamberSettings,
    candidate: _VariationCandidate,
    *,
    attempts: list[VariationAttempt],
    accepted_backing: bool,
) -> VariationEnvelope:
    manifest = candidate.manifest
    envelope = candidate.envelope
    parent_eligible, parent_reason = _variation_parent_eligibility(
        settings,
        candidate,
        accepted_backing=accepted_backing,
    )
    interactions = storm_examination_variation_interactions(
        settings,
        candidate.manifest_path,
    )
    caveated = bool(
        manifest.run_caveats
        or manifest.outputs.runtime_warnings
        or interactions.classification != "clear"
    )
    interaction_summary = (
        "No retained storm signal reached the lateral guard or upper damping layer."
        if interactions.classification == "clear"
        else (
            "Retained boundary/damping interaction is classified "
            f"{interactions.classification.replace('_', ' ')} against the declared "
            f"0-{interactions.useful_window_end_seconds:g} s useful window."
        )
    )
    replacements = {
        "attempt_integrity": (
            "passed",
            "Generated inputs, normal completion, and accepted backing are coherent.",
        ),
        "output_completeness": (
            "passed",
            "Expected histories, exact selected grid and extents, native fields, "
            "dimensions, units, cadence, and finite data passed. " + interaction_summary,
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
    settings: CloudChamberSettings,
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
    try:
        storm_examination_variation_inventory(settings, candidate.manifest_path)
        interactions = storm_examination_variation_interactions(
            settings,
            candidate.manifest_path,
        )
    except StormExaminationError as exc:
        return False, str(exc)
    if interactions.blocking_classification == "inside_useful_window":
        return (
            False,
            _interaction_parent_reason(interactions),
        )
    if interactions.classification == "inside_useful_window":
        return (
            True,
            "Accepted output remains reconstructible inside Supercells Recipe contract "
            "version 1; retained boundary/damping overlap remains a nonblocking caveat.",
        )
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
    scientific, numerical, observation, world_payload, differences, profile = (
        _builtin_simulation_contract(simulation_id)
    )
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
            "Current retained output is available. Create Variation revalidates generated "
            "inputs, source execution, and useful-window evidence before packaging."
        ),
        scientific_design=scientific,
        numerical_realization=numerical,
        observation_plan=observation,
        world_payload=world_payload,
        differences=differences,
        run_profile_contract=profile,
    )


def validate_supercells_parent_eligibility(
    settings: CloudChamberSettings,
    *,
    simulation_id: str,
    manifest: RunManifest,
    manifest_path: Path,
) -> tuple[bool, str]:
    """Deeply revalidate only the selected parent when Create Variation opens."""
    if simulation_id in {REFERENCE_SIMULATION_ID, STRAIGHT_LINE_SIMULATION_ID}:
        return _builtin_parent_eligibility(settings, simulation_id, manifest.run_id)
    try:
        envelope = VariationEnvelope.model_validate(
            manifest.run_configuration.get("variation_envelope")
        )
    except ValueError:
        return False, "The selected parent lacks a valid retained variation envelope."
    if envelope.simulation_id != simulation_id:
        return False, "The selected parent identity disagrees with its retained envelope."
    return _variation_parent_eligibility(
        settings,
        _VariationCandidate(
            manifest=manifest,
            manifest_path=manifest_path,
            envelope=envelope,
        ),
        accepted_backing=True,
    )


def _builtin_parent_eligibility(
    settings: CloudChamberSettings,
    simulation_id: str,
    run_id: str,
) -> tuple[bool, str]:
    manifest_path = settings.runtime_home.expanduser() / "runs" / run_id / "run_manifest.json"
    try:
        manifest = load_run_manifest(manifest_path)
        verified_generated_inputs = verify_generated_input_identity(manifest)
    except (OSError, RunManifestError, GeneratedInputIdentityError) as exc:
        return False, f"Retained parent generated-input identity is invalid: {exc}"
    if manifest.lifecycle_state != LifecycleState.COMPLETED:
        return False, "The retained parent is not complete."
    try:
        _validate_builtin_source_identity(
            settings,
            simulation_id=simulation_id,
            manifest=manifest,
            manifest_path=manifest_path,
            verified_generated_inputs=verified_generated_inputs,
        )
    except (OSError, ValueError) as exc:
        return False, f"Retained parent source/case identity is invalid: {exc}"
    try:
        interactions = storm_examination_interactions(settings, simulation_id)
    except StormExaminationError as exc:
        return False, str(exc)
    if interactions.blocking_classification == "inside_useful_window":
        return (
            False,
            _interaction_parent_reason(interactions),
        )
    if interactions.classification == "inside_useful_window":
        return (
            True,
            "Accepted retained presentation evidence remains reconstructible; observed "
            "boundary/damping overlap is retained as a nonblocking caveat.",
        )
    return (
        True,
        "Accepted retained presentation evidence, generated inputs, source execution, and "
        "useful-window contract remain reconstructible.",
    )


def _validate_builtin_source_identity(
    settings: CloudChamberSettings,
    *,
    simulation_id: str,
    manifest: RunManifest,
    manifest_path: Path,
    verified_generated_inputs: dict[str, str],
) -> None:
    run_dir = manifest_path.parent.resolve()
    case_manifest = json.loads((run_dir / "case_manifest.json").read_text())
    provenance = collect_cm1_provenance(settings)
    provenance_record = provenance.report_record()
    expected_case = {
        "run_id": manifest.run_id,
        "case_id": manifest.scenario.id,
        "simulation_id": simulation_id,
        "profile_id": PRESENTATION_PROFILE_ID,
        "hodograph": (
            "quarter_circle" if simulation_id == REFERENCE_SIMULATION_ID else "straight_line"
        ),
        "cm1_provenance": provenance_record,
        "generated_input_sha256": verified_generated_inputs,
    }
    mismatches = {
        key: (case_manifest.get(key), expected)
        for key, expected in expected_case.items()
        if case_manifest.get(key) != expected
    }
    if mismatches:
        raise ValueError(f"retained case manifest disagrees with the pinned contract: {mismatches}")
    if provenance_record.get("source_manifest_sha256") != CM1_SOURCE_MANIFEST_SHA256:
        raise ValueError("configured CM1 source manifest is not the approved source lock")
    if provenance_record.get("critical_source_sha256") != CRITICAL_SOURCE_SHA256:
        raise ValueError("configured CM1 critical-source hashes are not approved")
    if manifest.run_configuration.get("source_lock") != provenance_record:
        raise ValueError("retained run source lock disagrees with current pinned CM1 provenance")
    for key in ("source_run", "gate_a_source_lock"):
        if manifest.run_configuration.get(key) != case_manifest.get(key):
            raise ValueError(f"retained {key} identity differs between manifest and case")

    namelist_path = run_dir / "namelist.input"
    if not namelist_path.is_file():
        raise ValueError("retained parent namelist is unavailable")
    assignments = parse_namelist_assignments(namelist_path.read_text())
    expected_assignments = {
        **BASE_PRESENTATION_ASSIGNMENTS,
        **LOCKED_SCIENCE_ASSIGNMENTS,
        "timax": "10800.0",
        "tapfrq": "120.0",
    }
    if simulation_id == STRAIGHT_LINE_SIMULATION_ID:
        expected_assignments["iwnd"] = "12"
    namelist_mismatches = {
        name: (assignments.get(name), expected)
        for name, expected in expected_assignments.items()
        if not _namelist_values_equal(assignments.get(name), expected)
    }
    if namelist_mismatches:
        raise ValueError(
            "retained namelist differs from the approved presentation contract: "
            f"{namelist_mismatches}"
        )

    if simulation_id == REFERENCE_SIMULATION_ID:
        executable = _relocated_asset(
            manifest.execution.command[0] if manifest.execution.command else None,
            fallback_root=provenance.run_directory,
        )
        if executable != provenance.executable_path.resolve():
            raise ValueError("Quarter-Circle execution did not use the pinned CM1 executable")
        if sha256_file(executable) != CM1_EXECUTABLE_SHA256:
            raise ValueError("Quarter-Circle executable hash changed")
        if (
            manifest.execution.executable_sha256 is not None
            and manifest.execution.executable_sha256 != CM1_EXECUTABLE_SHA256
        ):
            raise ValueError("Quarter-Circle launch-time executable hash changed")
        if manifest.generated_inputs.cm1_source_customization:
            raise ValueError("Quarter-Circle parent unexpectedly declares source customization")
        return

    source_path = provenance.source_root / STRAIGHT_LINE_HODOGRAPH_TARGET
    if sha256_file(source_path) != PINNED_BASE_F_SHA256:
        raise ValueError("Straight-Line customization base source changed")
    expected_customization = straight_line_hodograph_artifact(source_path.read_text())
    customization_path = _relocated_asset(
        manifest.generated_inputs.cm1_source_customization,
        fallback_root=run_dir,
        fallback_name=STRAIGHT_LINE_HODOGRAPH_ARTIFACT_FILENAME,
    )
    if json.loads(customization_path.read_text()) != expected_customization:
        raise ValueError("Straight-Line packaged customization no longer reproduces")

    status = manifest.cm1_source_customization_status
    if not isinstance(status, dict):
        raise ValueError("Straight-Line applied source-customization status is unavailable")
    required_status = {
        "schema_version": "cm1_source_customization_status_v1",
        "customization_kind": STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND,
        "run_id": manifest.run_id,
        "original_target_sha256": expected_customization["original_source_sha256"],
        "patched_target_sha256": expected_customization["patched_source_sha256"],
        "patched_files": [str(STRAIGHT_LINE_HODOGRAPH_TARGET)],
        "source_restored_after_build": "not_modified_isolated_build_tree",
        "build_command": ["make"],
        "hodograph_profile": expected_customization["wind_profile"],
        "no_silent_hodograph_fallback": True,
    }
    status_mismatches = {
        key: (status.get(key), expected)
        for key, expected in required_status.items()
        if status.get(key) != expected
    }
    if status_mismatches:
        raise ValueError(
            "Straight-Line applied customization disagrees with the pinned artifact: "
            f"{status_mismatches}"
        )
    applied_path = run_dir / "cm1_source_customization_applied.json"
    if json.loads(applied_path.read_text()) != status:
        raise ValueError("Straight-Line launch-time customization status changed")

    build_root = _relocated_asset(
        status.get("build_root"),
        fallback_root=(settings.runtime_home.expanduser().resolve() / "cm1_source_builds"),
        require_directory=True,
    )
    built_source = build_root / STRAIGHT_LINE_HODOGRAPH_TARGET
    if sha256_file(built_source) != expected_customization["patched_source_sha256"]:
        raise ValueError("Straight-Line isolated build source no longer matches the patch")
    executable = _relocated_asset(
        status.get("custom_executable"),
        fallback_root=run_dir,
    )
    executable_sha256 = status.get("custom_executable_sha256")
    if not isinstance(executable_sha256, str) or sha256_file(executable) != executable_sha256:
        raise ValueError("Straight-Line retained executable hash changed")
    launched_executable = _relocated_asset(
        manifest.execution.command[0] if manifest.execution.command else None,
        fallback_root=run_dir,
    )
    if launched_executable != executable:
        raise ValueError("Straight-Line execution command used a different executable")
    if (
        manifest.execution.executable_sha256 is not None
        and manifest.execution.executable_sha256 != executable_sha256
    ):
        raise ValueError("Straight-Line launch-time executable hash changed")


def _relocated_asset(
    value: object,
    *,
    fallback_root: Path,
    fallback_name: str | None = None,
    require_directory: bool = False,
) -> Path:
    if isinstance(value, str) and value:
        original = Path(value).expanduser()
        if original.exists():
            return original.resolve()
        name = original.name
    elif fallback_name is not None:
        name = fallback_name
    else:
        raise ValueError("retained provenance path is unavailable")
    candidate = fallback_root / (fallback_name or name)
    if require_directory:
        if not candidate.is_dir():
            raise ValueError(f"relocated provenance directory is unavailable: {candidate.name}")
    elif not candidate.is_file():
        raise ValueError(f"relocated provenance asset is unavailable: {candidate.name}")
    return candidate.resolve()


def _namelist_values_equal(actual: str | None, expected: str) -> bool:
    if actual == expected:
        return True
    try:
        return float(actual or "") == float(expected)
    except ValueError:
        return False


def _interaction_parent_reason(interactions: Any) -> str:
    labels = []
    if interactions.blocking_lateral_boundary_first_time_seconds is not None:
        labels.append(
            "dominant storm signal at the lateral boundary at "
            f"{interactions.blocking_lateral_boundary_first_time_seconds:g} s"
        )
    if interactions.blocking_damping_layer_first_time_seconds is not None:
        labels.append(
            "dominant storm signal in the upper damping layer at "
            f"{interactions.blocking_damping_layer_first_time_seconds:g} s"
        )
    return (
        "Retained storm evidence reaches "
        + " and ".join(labels)
        + f" inside the declared 0-{interactions.useful_window_end_seconds:g} s "
        "useful window."
    )


def _intended_simulation_sha256(envelope: VariationEnvelope) -> str:
    return canonical_payload_sha256(
        {
            "schema_version": envelope.schema_version,
            "world_id": envelope.world_id,
            "recipe_id": envelope.recipe_id,
            "recipe_contract_version": envelope.recipe_contract_version,
            "simulation_id": envelope.simulation_id,
            "reference_simulation_id": envelope.reference_simulation_id,
            "scientific_design": envelope.scientific_design.payload,
            "numerical_realization": envelope.numerical_realization.payload,
        }
    )


def _builtin_simulation_contract(
    simulation_id: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, list[dict[str, Any]]],
    dict[str, Any],
]:
    from cloud_chamber.run_cost import profile_by_id

    profile = profile_by_id("supercells_presentation_v1")
    controls = default_controls()
    if simulation_id == STRAIGHT_LINE_SIMULATION_ID:
        controls = controls.model_copy(update={"hodograph_family": "straight"})
    controls_payload = controls.model_dump(mode="json")
    scientific = {
        "world_id": WORLD_ID,
        "recipe_id": RECIPE_ID,
        "recipe_contract_version": RECIPE_CONTRACT_VERSION,
        "reference_simulation_id": REFERENCE_SIMULATION_ID,
        "controls": controls_payload,
        "achieved_controls": controls_payload,
        "generators": generator_contract(),
        "fixed_assumptions": fixed_assumptions(),
    }
    numerical = profile.numerical_realization.model_dump(mode="json")
    observation = profile.observation_plan.model_dump(mode="json")
    differences: dict[str, list[dict[str, Any]]] = {}
    if simulation_id == STRAIGHT_LINE_SIMULATION_ID:
        differences = {
            "wind": [
                {
                    "category": "wind",
                    "path": "controls.hodograph_family",
                    "label": "Hodograph family",
                    "before": "quarter_circle",
                    "after": "straight",
                    "units": None,
                    "material": True,
                }
            ]
        }
    return (
        scientific,
        numerical,
        observation,
        {
            "controls": controls_payload,
            "reference_controls": default_controls().model_dump(mode="json"),
            "parent_controls": controls_payload,
            "requested_controls": controls_payload,
            "achieved_controls": controls_payload,
            "useful_window_end_seconds": 10_800,
        },
        differences,
        profile.model_dump(mode="json"),
    )
