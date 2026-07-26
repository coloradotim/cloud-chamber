"""Stable product identity and retained-output state for the Supercells World."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
)
from cloud_chamber.storm_examination import (
    STRAIGHT_LINE_SIMULATION_ID as STORM_STRAIGHT_LINE_SIMULATION_ID,
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
SupercellSimulationId = Literal[
    "supercells_quarter_circle_reference",
    "supercells_straight_line_hodograph",
]


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


class SupercellsCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_explore: bool
    lab: Literal[False] = False
    compare: bool
    saved_views: Literal[False] = False


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
    saved_comparison_count: Literal[0] = 0
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
    ]
    reference = simulations[0]
    available_count = sum(item.technical_state == "available" for item in simulations)
    if available_count == len(simulations):
        availability_state: AvailabilityState = "available"
        availability_message = (
            "Quarter-Circle and Straight-Line Hodograph Supercells are available "
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
    )
