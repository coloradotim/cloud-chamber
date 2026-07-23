"""Stable product identity and retained-output state for the Supercells World."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storm_examination import (
    PRESERVED_CASE_ID,
    PRESERVED_RUN_ID,
    StormExaminationError,
    storm_examination_inventory,
)

WORLD_ID: Literal["supercells"] = "supercells"
WORLD_DISPLAY_NAME: Literal["Supercells"] = "Supercells"
REFERENCE_SIMULATION_ID: Literal["supercells_quarter_circle_reference"] = (
    "supercells_quarter_circle_reference"
)
REFERENCE_DISPLAY_NAME: Literal["Quarter-Circle Supercell"] = "Quarter-Circle Supercell"
WORLD_SHORT_DESCRIPTION = (
    "A deep rotating thunderstorm for seeing organized ascent, rotation, hydrometeors, "
    "precipitation, and low-level flow evolve together."
)

AvailabilityState = Literal["available", "partial", "unavailable"]
TechnicalState = Literal["available", "missing", "invalid"]


class SupercellSimulationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: Literal["supercells_quarter_circle_reference"] = REFERENCE_SIMULATION_ID
    display_name: Literal["Quarter-Circle Supercell"] = REFERENCE_DISPLAY_NAME
    role: Literal["reference"] = "reference"
    world_id: Literal["supercells"] = WORLD_ID
    run_id: str = PRESERVED_RUN_ID
    case_id: str = PRESERVED_CASE_ID
    technical_state: TechnicalState
    technical_state_message: str
    explore_available: bool
    saved_output_count: int
    model_start_seconds: float | None
    model_end_seconds: float | None
    history_cadence_seconds: float | None
    lineage_state: Literal["known"] = "known"


class SupercellsCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_explore: bool
    lab: Literal[False] = False
    compare: Literal[False] = False
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
        available = self.reference_simulation.technical_state == "available"
        return SupercellsWorldSummary(
            reference_available=available,
            simulation_count=1 if available else 0,
            availability_state=self.availability_state,
            availability_message=self.availability_message,
        )


def supercells_world_detail(settings: CloudChamberSettings) -> SupercellsWorldDetail:
    """Resolve the one approved built-in without exposing its machine-private path."""
    try:
        inventory = storm_examination_inventory(settings)
    except StormExaminationError as exc:
        message = str(exc)
        state: TechnicalState = "missing" if "unavailable" in message.lower() else "invalid"
        simulation = SupercellSimulationRecord(
            technical_state=state,
            technical_state_message=message,
            explore_available=False,
            saved_output_count=0,
            model_start_seconds=None,
            model_end_seconds=None,
            history_cadence_seconds=None,
        )
        return SupercellsWorldDetail(
            availability_state="unavailable",
            availability_message=(
                "The Quarter-Circle Supercell output is not available for Explore."
            ),
            reference_simulation=simulation,
            simulations=[simulation],
            capabilities=SupercellsCapabilities(reference_explore=False),
            caveats=[message],
        )

    times = [item[1] for item in inventory]
    cadence = times[1] - times[0] if len(times) > 1 else None
    simulation = SupercellSimulationRecord(
        technical_state="available",
        technical_state_message="Retained native CM1 output is ready for inspection.",
        explore_available=True,
        saved_output_count=len(times),
        model_start_seconds=times[0],
        model_end_seconds=times[-1],
        history_cadence_seconds=cadence,
    )
    return SupercellsWorldDetail(
        availability_state="available",
        availability_message="Quarter-Circle Supercell is available for Explore.",
        reference_simulation=simulation,
        simulations=[simulation],
        capabilities=SupercellsCapabilities(reference_explore=True),
        caveats=[
            "This is an idealized stock CM1 quarter-circle benchmark, not an observed storm.",
            "Horizontal coordinates and winds use the translating model frame.",
        ],
    )
