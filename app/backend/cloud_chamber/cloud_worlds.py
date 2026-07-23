"""Bounded Cloud World payloads for the first Trade Cumulus MVP increment."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cloud_chamber.mountain_waves_world import (
    MountainWavesWorldSummary,
    mountain_waves_world_detail,
)
from cloud_chamber.result_ingest import (
    ResultMetadata,
    list_result_metadata,
    result_metadata_from_json,
)
from cloud_chamber.run_manifest import LifecycleState, RunManifestError, load_run_manifest
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.supercells_world import SupercellsWorldSummary, supercells_world_detail
from cloud_chamber.trade_cumulus_comparison_story import (
    CASE_ID,
    COMPARISON_GROUP_ID,
    COMPARISON_ID,
    EXPECTED_CM1_EXECUTABLE_SHA256,
    EXPECTED_CM1_SOURCE_MANIFEST_SHA256,
    PRODUCT_SLICE_ID,
    TradeCumulusComparisonStoryConflict,
    TradeCumulusComparisonStoryNotFound,
    trade_cumulus_moisture_comparison_story,
)

WORLD_ID: Literal["trade_cumulus"] = "trade_cumulus"
WORLD_DISPLAY_NAME: Literal["Trade Cumulus"] = "Trade Cumulus"
WORLD_STATUS: Literal["mvp_candidate"] = "mvp_candidate"
REFERENCE_SIMULATION_ID: Literal["trade_cumulus_canonical_bomex"] = "trade_cumulus_canonical_bomex"
REFERENCE_DISPLAY_NAME = "Canonical BOMEX Baseline"
PRESENTATION_BASELINE_RESULT_ID = "result-trade-cumulus-presentation-v1-baseline-20260722"
PRESENTATION_BASELINE_RUN_ID = "trade-cumulus-presentation-v1-baseline-20260722"
PRESENTATION_MORE_MOISTURE_RESULT_ID = "result-trade-cumulus-presentation-v1-more-moisture-20260722"
PRESENTATION_MORE_MOISTURE_RUN_ID = "trade-cumulus-presentation-v1-more-moisture-20260722"
PRESENTATION_FIXED_ASSUMPTIONS_SHA256 = (
    "861375a82d209c36cc63ccce2d20934553b0e7e8811579c718dfb275899172a7"
)
MORE_MOISTURE_SIMULATION_ID: Literal["trade_cumulus_more_moisture"] = "trade_cumulus_more_moisture"
MORE_MOISTURE_DISPLAY_NAME = "More Moisture"
FEATURED_COMPARISON_DISPLAY_NAME: Literal["More Moisture versus Baseline"] = (
    "More Moisture versus Baseline"
)
WORLD_SHORT_DESCRIPTION = (
    "A maritime shallow-cumulus field for watching clouds form, mix, decay, and respond "
    "to changes in initial conditions and forcing."
)

AvailabilityState = Literal["available", "partial", "unavailable", "conflict"]
TechnicalState = Literal["available", "missing", "conflict"]
TrustState = Literal["trusted", "caveated", "untrusted", "unassessed", "unavailable"]
SimulationRole = Literal["reference", "variation", "lab_history"]
LineageState = Literal["known", "valid", "unlineaged", "invalid"]
DifferenceCategory = Literal["atmospheric", "numerical", "output", "operational", "metadata"]


class ConfigurationDifference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    label: str
    category: DifferenceCategory
    left_value: Any
    right_value: Any
    units: str | None = None
    material: bool


class CompareSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comparison_id: str
    display_name: str
    target_simulation_id: str


class SimulationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: str | None
    display_name: str
    role: SimulationRole
    world_id: Literal["trade_cumulus"] = WORLD_ID
    product_slice_id: str
    case_id: str
    result_id: str
    run_id: str
    source_recipe_id: str | None = None
    parent_simulation_id: str | None = None
    reference_simulation_id: str | None = None
    technical_state: TechnicalState
    technical_state_message: str
    technical_trust_state: TrustState
    explore_available: bool
    compare_suggestions: list[CompareSuggestion] = Field(default_factory=list)
    configuration_difference_from_reference: list[ConfigurationDifference] | None = None
    lineage_state: LineageState
    created_at: str | None = None
    completed_at: str | None = None


class FeaturedComparisonRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comparison_id: Literal["trade_cumulus_moisture_v1"] = COMPARISON_ID
    display_name: Literal["More Moisture versus Baseline"] = FEATURED_COMPARISON_DISPLAY_NAME
    baseline_simulation_id: Literal["trade_cumulus_canonical_bomex"] = REFERENCE_SIMULATION_ID
    more_moisture_simulation_id: Literal["trade_cumulus_more_moisture"] = (
        MORE_MOISTURE_SIMULATION_ID
    )
    availability_state: TechnicalState
    availability_message: str
    open_available: bool


class LabSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active_run_count: int
    completed_uninspected_run_count: int
    lab_history_count: int
    summary: str


class WorldCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_explore: bool
    featured_comparison: bool
    lab: Literal[True] = True
    saved_views: Literal[False] = False
    ordinary_compare: Literal[False] = False


class CloudWorldSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: Literal["trade_cumulus"] = WORLD_ID
    display_name: Literal["Trade Cumulus"] = WORLD_DISPLAY_NAME
    status: Literal["mvp_candidate"] = WORLD_STATUS
    short_description: str = WORLD_SHORT_DESCRIPTION
    reference_simulation_id: Literal["trade_cumulus_canonical_bomex"] = REFERENCE_SIMULATION_ID
    reference_available: bool
    simulation_count: int
    saved_view_count: Literal[0] = 0
    saved_comparison_count: int
    featured_comparison_count: int
    active_run_count: int
    completed_uninspected_run_count: int
    availability_state: AvailabilityState
    availability_message: str


class TradeCumulusWorldDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: Literal["trade_cumulus"] = WORLD_ID
    display_name: Literal["Trade Cumulus"] = WORLD_DISPLAY_NAME
    status: Literal["mvp_candidate"] = WORLD_STATUS
    short_description: str = WORLD_SHORT_DESCRIPTION
    availability_state: AvailabilityState
    availability_message: str
    reference_simulation: SimulationRecord
    simulations: list[SimulationRecord]
    lab_history: list[SimulationRecord]
    featured_comparison: FeaturedComparisonRecord
    lab_summary: LabSummary
    capabilities: WorldCapabilities
    caveats: list[str] = Field(default_factory=list)

    def summary(self) -> CloudWorldSummary:
        available_simulations = sum(
            simulation.technical_state == "available" for simulation in self.simulations
        )
        comparison_available = self.featured_comparison.availability_state == "available"
        return CloudWorldSummary(
            reference_available=self.reference_simulation.technical_state == "available",
            simulation_count=available_simulations,
            saved_comparison_count=1 if comparison_available else 0,
            featured_comparison_count=1 if comparison_available else 0,
            active_run_count=self.lab_summary.active_run_count,
            completed_uninspected_run_count=self.lab_summary.completed_uninspected_run_count,
            availability_state=self.availability_state,
            availability_message=self.availability_message,
        )


@dataclass(frozen=True)
class _KnownSimulationSpec:
    simulation_id: str
    display_name: str
    result_id: str
    run_id: str
    role: Literal["reference", "variation"]
    control_state: Literal["baseline", "more_moisture"]
    control_value: float
    parent_simulation_id: str | None


@dataclass(frozen=True)
class _LoadedKnownSimulation:
    record: SimulationRecord
    metadata: ResultMetadata | None


@dataclass(frozen=True)
class _Inspectability:
    technical_state: TechnicalState
    technical_state_message: str
    explore_available: bool


@dataclass(frozen=True)
class _LineageCandidate:
    metadata: ResultMetadata
    simulation_id: str | None
    display_name: str | None
    source_recipe_id: str | None
    parent_simulation_id: str | None
    parent_result_id: str | None
    reference_simulation_id: str | None
    reference_result_id: str | None
    supplied_keys: bool
    shape_valid: bool


_REFERENCE_SPEC = _KnownSimulationSpec(
    simulation_id=REFERENCE_SIMULATION_ID,
    display_name=REFERENCE_DISPLAY_NAME,
    result_id=PRESENTATION_BASELINE_RESULT_ID,
    run_id=PRESENTATION_BASELINE_RUN_ID,
    role="reference",
    control_state="baseline",
    control_value=5.2e-5,
    parent_simulation_id=None,
)
_MORE_MOISTURE_SPEC = _KnownSimulationSpec(
    simulation_id=MORE_MOISTURE_SIMULATION_ID,
    display_name=MORE_MOISTURE_DISPLAY_NAME,
    result_id=PRESENTATION_MORE_MOISTURE_RESULT_ID,
    run_id=PRESENTATION_MORE_MOISTURE_RUN_ID,
    role="variation",
    control_state="more_moisture",
    control_value=7.8e-5,
    parent_simulation_id=REFERENCE_SIMULATION_ID,
)
_RESERVED_SIMULATION_IDS = {REFERENCE_SIMULATION_ID, MORE_MOISTURE_SIMULATION_ID}
_LINEAGE_KEYS = {
    "cloud_world_id",
    "simulation_id",
    "simulation_display_name",
    "source_recipe_id",
    "parent_simulation_id",
    "parent_result_id",
    "reference_simulation_id",
    "reference_result_id",
    "user_question",
}


def list_cloud_world_summaries(
    settings: CloudChamberSettings,
) -> list[CloudWorldSummary | MountainWavesWorldSummary | SupercellsWorldSummary]:
    """Return real Cloud Worlds without assigning one shared scientific framing."""
    return [
        trade_cumulus_world_detail(settings).summary(),
        mountain_waves_world_detail(settings).summary(),
        supercells_world_detail(settings).summary(),
    ]


def trade_cumulus_world_detail(settings: CloudChamberSettings) -> TradeCumulusWorldDetail:
    """Return strict World identity, Simulation, Comparison, and Lab state."""
    reference = _load_known_simulation(settings, _REFERENCE_SPEC)
    more_moisture = _load_known_simulation(settings, _MORE_MOISTURE_SPEC)

    if reference.metadata is not None and more_moisture.metadata is not None:
        differences = configuration_differences(reference.metadata, more_moisture.metadata)
        more_moisture = _LoadedKnownSimulation(
            record=more_moisture.record.model_copy(
                update={"configuration_difference_from_reference": differences}
            ),
            metadata=more_moisture.metadata,
        )

    featured = _featured_comparison(settings, reference, more_moisture)
    if featured.availability_state == "available":
        suggestion_for_reference = CompareSuggestion(
            comparison_id=COMPARISON_ID,
            display_name=FEATURED_COMPARISON_DISPLAY_NAME,
            target_simulation_id=MORE_MOISTURE_SIMULATION_ID,
        )
        suggestion_for_more = suggestion_for_reference.model_copy(
            update={"target_simulation_id": REFERENCE_SIMULATION_ID}
        )
        reference = _LoadedKnownSimulation(
            record=reference.record.model_copy(
                update={"compare_suggestions": [suggestion_for_reference]}
            ),
            metadata=reference.metadata,
        )
        more_moisture = _LoadedKnownSimulation(
            record=more_moisture.record.model_copy(
                update={"compare_suggestions": [suggestion_for_more]}
            ),
            metadata=more_moisture.metadata,
        )

    all_metadata = list_result_metadata(settings)
    other_metadata = [
        metadata
        for metadata in all_metadata
        if metadata.result_id
        not in {
            PRESENTATION_BASELINE_RESULT_ID,
            PRESENTATION_MORE_MOISTURE_RESULT_ID,
        }
        and _is_trade_cumulus_result(metadata)
    ]
    retained, lab_history = _ordinary_simulations(
        other_metadata,
        known_metadata={
            record.record.simulation_id: record.metadata
            for record in (reference, more_moisture)
            if record.record.simulation_id is not None and record.metadata is not None
        },
    )

    simulations = [reference.record, more_moisture.record, *retained]
    lab_summary = _lab_summary(settings, all_metadata, lab_history)
    availability_state, availability_message = _world_availability(
        reference.record, more_moisture.record, featured
    )
    caveats = [
        (
            "Trade Cumulus remains an MVP candidate rather than the permanent definition "
            "of Cloud Chamber."
        ),
        "Saved Views and ordinary linked Comparison are not implemented in this increment.",
    ]
    if lab_history:
        caveats.append(
            "Eligible results without valid stable lineage remain in Lab history and are not "
            "curated Simulations."
        )

    return TradeCumulusWorldDetail(
        availability_state=availability_state,
        availability_message=availability_message,
        reference_simulation=reference.record,
        simulations=simulations,
        lab_history=lab_history,
        featured_comparison=featured,
        lab_summary=lab_summary,
        capabilities=WorldCapabilities(
            reference_explore=reference.record.explore_available,
            featured_comparison=featured.open_available,
        ),
        caveats=caveats,
    )


def trade_cumulus_simulation_exists(
    settings: CloudChamberSettings,
    simulation_id: str,
) -> bool:
    """Resolve one stable Simulation identity without building the complete World."""
    known = {
        spec.simulation_id: _load_known_simulation(settings, spec)
        for spec in (_REFERENCE_SPEC, _MORE_MOISTURE_SPEC)
    }
    if simulation_id in known:
        return known[simulation_id].metadata is not None

    other_metadata = [
        metadata
        for metadata in list_result_metadata(settings)
        if metadata.result_id
        not in {
            PRESENTATION_BASELINE_RESULT_ID,
            PRESENTATION_MORE_MOISTURE_RESULT_ID,
        }
        and _is_trade_cumulus_result(metadata)
    ]
    retained, _ = _ordinary_simulations(
        other_metadata,
        known_metadata={
            record.record.simulation_id: record.metadata
            for record in known.values()
            if record.record.simulation_id is not None and record.metadata is not None
        },
    )
    return any(record.simulation_id == simulation_id for record in retained)


def configuration_differences(
    left: ResultMetadata, right: ResultMetadata
) -> list[ConfigurationDifference]:
    """Compare persisted controls/configuration without machine bookkeeping."""
    left_payload = _comparison_payload(left)
    right_payload = _comparison_payload(right)
    differences: list[ConfigurationDifference] = []
    _compare_values(left_payload, right_payload, (), differences)
    return sorted(differences, key=lambda item: (item.category, item.label, item.path))


def _load_known_simulation(
    settings: CloudChamberSettings, spec: _KnownSimulationSpec
) -> _LoadedKnownSimulation:
    path = settings.runtime_home.expanduser() / "runs" / spec.run_id / "result_metadata.json"
    if not path.is_file():
        return _LoadedKnownSimulation(record=_missing_known_record(spec), metadata=None)
    try:
        metadata = result_metadata_from_json(path.read_text())
    except (OSError, ValueError, ValidationError, json.JSONDecodeError):
        return _LoadedKnownSimulation(record=_conflicting_known_record(spec), metadata=None)
    if not _known_identity_matches(metadata, spec):
        return _LoadedKnownSimulation(record=_conflicting_known_record(spec), metadata=None)
    return _LoadedKnownSimulation(
        record=_known_record(spec, metadata, _inspectability(metadata)), metadata=metadata
    )


def _known_identity_matches(metadata: ResultMetadata, spec: _KnownSimulationSpec) -> bool:
    configuration = metadata.run_configuration
    provenance = configuration.get("cm1_provenance")
    if not isinstance(provenance, Mapping):
        return False
    expected = (
        (metadata.result_id, spec.result_id),
        (metadata.run_id, spec.run_id),
        (metadata.scenario_id, CASE_ID),
        (metadata.source_lifecycle_state, "completed"),
        (metadata.source_product_state, "completed_cm1_result"),
        (metadata.source_model, "CM1"),
        (configuration.get("case_id"), CASE_ID),
        (configuration.get("product_slice_id"), PRODUCT_SLICE_ID),
        (configuration.get("comparison_group_id"), COMPARISON_GROUP_ID),
        (configuration.get("control_id"), "surface_moisture_supply"),
        (configuration.get("control_state"), spec.control_state),
        (configuration.get("fixed_assumptions_sha256"), PRESENTATION_FIXED_ASSUMPTIONS_SHA256),
        (metadata.controls.get("control_id"), "surface_moisture_supply"),
        (metadata.controls.get("control_state"), spec.control_state),
        (provenance.get("source_manifest_sha256"), EXPECTED_CM1_SOURCE_MANIFEST_SHA256),
        (provenance.get("executable_sha256"), EXPECTED_CM1_EXECUTABLE_SHA256),
    )
    if any(actual != wanted for actual, wanted in expected):
        return False
    return (
        metadata.controls.get("surface_moisture_flux_g_g_m_s") == spec.control_value
        and configuration.get("surface_moisture_flux_g_g_m_s") == spec.control_value
    )


def _known_record(
    spec: _KnownSimulationSpec,
    metadata: ResultMetadata,
    inspectability: _Inspectability,
) -> SimulationRecord:
    source_recipe = metadata.run_configuration.get("recipe_candidate_id")
    return SimulationRecord(
        simulation_id=spec.simulation_id,
        display_name=spec.display_name,
        role=spec.role,
        product_slice_id=PRODUCT_SLICE_ID,
        case_id=CASE_ID,
        result_id=spec.result_id,
        run_id=spec.run_id,
        source_recipe_id=source_recipe if isinstance(source_recipe, str) else None,
        parent_simulation_id=spec.parent_simulation_id,
        reference_simulation_id=REFERENCE_SIMULATION_ID,
        technical_state=inspectability.technical_state,
        technical_state_message=inspectability.technical_state_message,
        technical_trust_state=(
            _trust_state(metadata)
            if inspectability.technical_state == "available"
            else "unavailable"
        ),
        explore_available=inspectability.explore_available,
        lineage_state="known",
        created_at=metadata.created_at.isoformat(),
        completed_at=metadata.updated_at.isoformat(),
    )


def _missing_known_record(spec: _KnownSimulationSpec) -> SimulationRecord:
    return SimulationRecord(
        simulation_id=spec.simulation_id,
        display_name=spec.display_name,
        role=spec.role,
        product_slice_id=PRODUCT_SLICE_ID,
        case_id=CASE_ID,
        result_id=spec.result_id,
        run_id=spec.run_id,
        parent_simulation_id=spec.parent_simulation_id,
        reference_simulation_id=REFERENCE_SIMULATION_ID,
        technical_state="missing",
        technical_state_message="The expected local Simulation output is not installed.",
        technical_trust_state="unavailable",
        explore_available=False,
        lineage_state="known",
    )


def _conflicting_known_record(spec: _KnownSimulationSpec) -> SimulationRecord:
    return _missing_known_record(spec).model_copy(
        update={
            "technical_state": "conflict",
            "technical_state_message": (
                "Persisted Simulation identity conflicts with the approved World identity."
            ),
        }
    )


def _featured_comparison(
    settings: CloudChamberSettings,
    reference: _LoadedKnownSimulation,
    more_moisture: _LoadedKnownSimulation,
) -> FeaturedComparisonRecord:
    states = {reference.record.technical_state, more_moisture.record.technical_state}
    if "conflict" in states:
        return FeaturedComparisonRecord(
            availability_state="conflict",
            availability_message="Comparison member identity conflicts with the approved pair.",
            open_available=False,
        )
    if "missing" in states:
        return FeaturedComparisonRecord(
            availability_state="missing",
            availability_message="The complete featured Comparison pair is not installed.",
            open_available=False,
        )
    try:
        trade_cumulus_moisture_comparison_story(settings)
    except TradeCumulusComparisonStoryNotFound:
        return FeaturedComparisonRecord(
            availability_state="missing",
            availability_message="Featured Comparison story is unavailable.",
            open_available=False,
        )
    except TradeCumulusComparisonStoryConflict:
        return FeaturedComparisonRecord(
            availability_state="conflict",
            availability_message="Featured Comparison story conflicts with the approved pair.",
            open_available=False,
        )
    return FeaturedComparisonRecord(
        availability_state="available",
        availability_message="Featured Comparison is available.",
        open_available=True,
    )


def _ordinary_simulations(
    metadata_records: list[ResultMetadata],
    *,
    known_metadata: dict[str, ResultMetadata],
) -> tuple[list[SimulationRecord], list[SimulationRecord]]:
    candidates = [_lineage_candidate(metadata) for metadata in metadata_records]
    counts = Counter(
        candidate.simulation_id for candidate in candidates if candidate.simulation_id is not None
    )
    candidate_ids = {
        candidate.simulation_id
        for candidate in candidates
        if candidate.shape_valid
        and candidate.simulation_id is not None
        and counts[candidate.simulation_id] == 1
        and candidate.simulation_id not in _RESERVED_SIMULATION_IDS
    }
    known_ids = set(known_metadata)
    resolvable_ids = known_ids | candidate_ids
    result_to_simulation = {
        metadata.result_id: simulation_id for simulation_id, metadata in known_metadata.items()
    }
    result_to_simulation.update(
        {
            candidate.metadata.result_id: candidate.simulation_id
            for candidate in candidates
            if candidate.simulation_id in candidate_ids
        }
    )
    candidates_by_id = {
        candidate.simulation_id: candidate
        for candidate in candidates
        if candidate.simulation_id in candidate_ids
    }
    structurally_valid_ids = {
        candidate.simulation_id
        for candidate in candidates
        if _lineage_resolves(
            candidate,
            counts=counts,
            resolvable_ids=resolvable_ids,
            result_to_simulation=result_to_simulation,
        )
        and candidate.simulation_id is not None
    }
    valid_candidate_ids = structurally_valid_ids - _cyclic_lineage_ids(
        candidates_by_id,
        structurally_valid_ids=structurally_valid_ids,
        result_to_simulation=result_to_simulation,
    )
    while True:
        invalid_dependents = {
            simulation_id
            for simulation_id in valid_candidate_ids
            if any(
                target_id in candidate_ids and target_id not in valid_candidate_ids
                for target_id in _resolved_lineage_target_ids(
                    candidates_by_id[simulation_id], result_to_simulation
                )
            )
        }
        if not invalid_dependents:
            break
        valid_candidate_ids -= invalid_dependents
    metadata_by_simulation = dict(known_metadata)
    metadata_by_simulation.update(
        {
            candidate.simulation_id: candidate.metadata
            for candidate in candidates
            if candidate.simulation_id in valid_candidate_ids
        }
    )

    retained: list[SimulationRecord] = []
    history: list[SimulationRecord] = []
    for candidate in candidates:
        valid = candidate.simulation_id in valid_candidate_ids
        inspectability = _inspectability(candidate.metadata)
        if not valid:
            history.append(
                _lab_history_record(
                    candidate,
                    invalid=candidate.supplied_keys,
                    inspectability=inspectability,
                )
            )
            continue
        parent_id = candidate.parent_simulation_id or (
            result_to_simulation.get(candidate.parent_result_id)
            if candidate.parent_result_id is not None
            else None
        )
        reference_id = candidate.reference_simulation_id or (
            result_to_simulation.get(candidate.reference_result_id)
            if candidate.reference_result_id is not None
            else None
        )
        comparison_parent_id = parent_id or reference_id
        differences = None
        if comparison_parent_id is not None:
            parent_metadata = metadata_by_simulation.get(comparison_parent_id)
            if parent_metadata is not None:
                differences = configuration_differences(parent_metadata, candidate.metadata)
        retained.append(
            SimulationRecord(
                simulation_id=candidate.simulation_id,
                display_name=candidate.display_name or "Retained Trade Cumulus Simulation",
                role="variation",
                product_slice_id=PRODUCT_SLICE_ID,
                case_id=CASE_ID,
                result_id=candidate.metadata.result_id,
                run_id=candidate.metadata.run_id,
                source_recipe_id=candidate.source_recipe_id,
                parent_simulation_id=parent_id,
                reference_simulation_id=reference_id,
                technical_state=inspectability.technical_state,
                technical_state_message=inspectability.technical_state_message,
                technical_trust_state=(
                    _trust_state(candidate.metadata)
                    if inspectability.technical_state == "available"
                    else "unavailable"
                ),
                explore_available=inspectability.explore_available,
                configuration_difference_from_reference=differences,
                lineage_state="valid",
                created_at=candidate.metadata.created_at.isoformat(),
                completed_at=candidate.metadata.updated_at.isoformat(),
            )
        )
    retained.sort(key=lambda record: (record.display_name, record.simulation_id or ""))
    history.sort(key=lambda record: (record.completed_at or "", record.result_id), reverse=True)
    return retained, history


def _lineage_candidate(metadata: ResultMetadata) -> _LineageCandidate:
    configuration = metadata.run_configuration
    supplied_keys = any(key in configuration for key in _LINEAGE_KEYS)
    cloud_world_id = _optional_string(configuration.get("cloud_world_id"))
    simulation_id = _optional_string(configuration.get("simulation_id"))
    display_name = _optional_string(configuration.get("simulation_display_name"))
    source_recipe_id = _optional_string(configuration.get("source_recipe_id"))
    parent_simulation_id = _optional_string(configuration.get("parent_simulation_id"))
    parent_result_id = _optional_string(configuration.get("parent_result_id"))
    reference_simulation_id = _optional_string(configuration.get("reference_simulation_id"))
    reference_result_id = _optional_string(configuration.get("reference_result_id"))
    shape_valid = (
        supplied_keys
        and cloud_world_id == WORLD_ID
        and simulation_id is not None
        and display_name is not None
    )
    return _LineageCandidate(
        metadata=metadata,
        simulation_id=simulation_id,
        display_name=display_name,
        source_recipe_id=source_recipe_id,
        parent_simulation_id=parent_simulation_id,
        parent_result_id=parent_result_id,
        reference_simulation_id=reference_simulation_id,
        reference_result_id=reference_result_id,
        supplied_keys=supplied_keys,
        shape_valid=shape_valid,
    )


def _lineage_resolves(
    candidate: _LineageCandidate,
    *,
    counts: Counter[str],
    resolvable_ids: set[str],
    result_to_simulation: Mapping[str, str],
) -> bool:
    simulation_id = candidate.simulation_id
    if (
        not candidate.shape_valid
        or simulation_id is None
        or simulation_id in _RESERVED_SIMULATION_IDS
        or counts[simulation_id] != 1
    ):
        return False
    if candidate.parent_simulation_id and candidate.parent_simulation_id not in resolvable_ids:
        return False
    if (
        candidate.reference_simulation_id
        and candidate.reference_simulation_id not in resolvable_ids
    ):
        return False
    if candidate.parent_result_id and candidate.parent_result_id not in result_to_simulation:
        return False
    if candidate.reference_result_id and candidate.reference_result_id not in result_to_simulation:
        return False
    if candidate.parent_simulation_id and candidate.parent_result_id:
        if result_to_simulation.get(candidate.parent_result_id) != candidate.parent_simulation_id:
            return False
    if candidate.reference_simulation_id and candidate.reference_result_id:
        if (
            result_to_simulation.get(candidate.reference_result_id)
            != candidate.reference_simulation_id
        ):
            return False
    return simulation_id not in _resolved_lineage_target_ids(candidate, result_to_simulation)


def _resolved_lineage_target_ids(
    candidate: _LineageCandidate, result_to_simulation: Mapping[str, str]
) -> set[str]:
    targets = {
        target
        for target in (candidate.parent_simulation_id, candidate.reference_simulation_id)
        if target is not None
    }
    for result_id in (candidate.parent_result_id, candidate.reference_result_id):
        if result_id is not None and (target := result_to_simulation.get(result_id)) is not None:
            targets.add(target)
    return targets


def _cyclic_lineage_ids(
    candidates_by_id: Mapping[str, _LineageCandidate],
    *,
    structurally_valid_ids: set[str],
    result_to_simulation: Mapping[str, str],
) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    path: list[str] = []
    cyclic: set[str] = set()

    def visit(simulation_id: str) -> None:
        if simulation_id in visited:
            return
        if simulation_id in visiting:
            cyclic.update(path[path.index(simulation_id) :])
            return
        visiting.add(simulation_id)
        path.append(simulation_id)
        candidate = candidates_by_id[simulation_id]
        for target_id in _resolved_lineage_target_ids(candidate, result_to_simulation):
            if target_id in structurally_valid_ids:
                visit(target_id)
        path.pop()
        visiting.remove(simulation_id)
        visited.add(simulation_id)

    for simulation_id in sorted(structurally_valid_ids):
        visit(simulation_id)
    return cyclic


def _lab_history_record(
    candidate: _LineageCandidate,
    *,
    invalid: bool,
    inspectability: _Inspectability,
) -> SimulationRecord:
    return SimulationRecord(
        simulation_id=None,
        display_name="Unretained Trade Cumulus result",
        role="lab_history",
        product_slice_id=PRODUCT_SLICE_ID,
        case_id=CASE_ID,
        result_id=candidate.metadata.result_id,
        run_id=candidate.metadata.run_id,
        technical_state=inspectability.technical_state,
        technical_state_message=(
            (
                "Stable lineage is invalid; this result remains in Lab history."
                if invalid
                else "Stable lineage is absent; this result remains in Lab history."
            )
            if inspectability.technical_state == "available"
            else inspectability.technical_state_message
        ),
        technical_trust_state=(
            _trust_state(candidate.metadata)
            if inspectability.technical_state == "available"
            else "unavailable"
        ),
        explore_available=inspectability.explore_available,
        lineage_state="invalid" if invalid else "unlineaged",
        created_at=candidate.metadata.created_at.isoformat(),
        completed_at=candidate.metadata.updated_at.isoformat(),
    )


def _lab_summary(
    settings: CloudChamberSettings,
    metadata_records: list[ResultMetadata],
    lab_history: list[SimulationRecord],
) -> LabSummary:
    ingested_run_ids = {metadata.run_id for metadata in metadata_records}
    active = 0
    completed_uninspected = 0
    runs_dir = settings.runtime_home.expanduser() / "runs"
    if runs_dir.is_dir():
        for manifest_path in sorted(runs_dir.glob("*/run_manifest.json")):
            try:
                manifest = load_run_manifest(manifest_path)
            except (OSError, ValueError, RunManifestError):
                continue
            if not _is_trade_cumulus_configuration(manifest.run_configuration):
                continue
            if manifest.lifecycle_state in {LifecycleState.QUEUED, LifecycleState.RUNNING}:
                active += 1
            elif (
                manifest.lifecycle_state == LifecycleState.COMPLETED
                and manifest.run_id not in ingested_run_ids
            ):
                completed_uninspected += 1
    if active:
        summary = f"{active} active run{'s' if active != 1 else ''}"
    elif completed_uninspected:
        summary = (
            f"{completed_uninspected} completed run"
            f"{'s' if completed_uninspected != 1 else ''} awaiting inspection"
        )
    else:
        summary = "Lab is idle"
    return LabSummary(
        active_run_count=active,
        completed_uninspected_run_count=completed_uninspected,
        lab_history_count=len(lab_history),
        summary=summary,
    )


def _world_availability(
    reference: SimulationRecord,
    more_moisture: SimulationRecord,
    featured: FeaturedComparisonRecord,
) -> tuple[AvailabilityState, str]:
    states = {
        reference.technical_state,
        more_moisture.technical_state,
        featured.availability_state,
    }
    if "conflict" in states:
        return (
            "conflict",
            "One or more installed Trade Cumulus assets conflict with approved identity.",
        )
    if reference.technical_state == "missing":
        return "partial", "Canonical BOMEX Baseline is not installed. Lab remains available."
    if "missing" in states:
        return (
            "partial",
            "Canonical BOMEX Baseline is available; optional World content is missing.",
        )
    return "available", "Reference, variation, and featured Comparison are available."


def _inspectability(metadata: ResultMetadata) -> _Inspectability:
    paths = metadata.model_output_paths or metadata.netcdf_paths
    if metadata.missing_required_output_fields:
        return _Inspectability(
            technical_state="conflict",
            technical_state_message="Persisted output is missing required scientific fields.",
            explore_available=False,
        )
    if not paths:
        return _Inspectability(
            technical_state="missing",
            technical_state_message="Simulation model output is not installed.",
            explore_available=False,
        )
    if metadata.model_output_file_count and metadata.model_output_file_count != len(paths):
        return _Inspectability(
            technical_state="conflict",
            technical_state_message="Persisted output inventory conflicts with available files.",
            explore_available=False,
        )
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if not path.exists():
            return _Inspectability(
                technical_state="missing",
                technical_state_message="Simulation model output is not installed.",
                explore_available=False,
            )
        if not path.is_file():
            return _Inspectability(
                technical_state="conflict",
                technical_state_message="Persisted output inventory is not readable model output.",
                explore_available=False,
            )
        try:
            with path.open("rb") as handle:
                first_byte = handle.read(1)
        except FileNotFoundError:
            return _Inspectability(
                technical_state="missing",
                technical_state_message="Simulation model output is not installed.",
                explore_available=False,
            )
        except OSError:
            return _Inspectability(
                technical_state="conflict",
                technical_state_message="Persisted model output cannot be read.",
                explore_available=False,
            )
        if not first_byte:
            return _Inspectability(
                technical_state="conflict",
                technical_state_message="Persisted model output is empty.",
                explore_available=False,
            )
    return _Inspectability(
        technical_state="available",
        technical_state_message="Simulation output is available for inspection.",
        explore_available=True,
    )


def _trust_state(metadata: ResultMetadata) -> TrustState:
    state = metadata.runtime_integrity.state
    if state == "trusted":
        return "trusted"
    if state == "caveated":
        return "caveated"
    if state == "failed":
        return "untrusted"
    return "unassessed"


def _is_trade_cumulus_result(metadata: ResultMetadata) -> bool:
    return metadata.scenario_id == CASE_ID and _is_trade_cumulus_configuration(
        metadata.run_configuration
    )


def _is_trade_cumulus_configuration(configuration: Mapping[str, object]) -> bool:
    return configuration.get("case_id") == CASE_ID


def _comparison_payload(metadata: ResultMetadata) -> dict[str, Any]:
    controls = {
        key: value
        for key, value in metadata.controls.items()
        if key not in {"control_id", "control_state"}
    }
    configuration = {
        key: value
        for key, value in metadata.run_configuration.items()
        if key not in controls and key not in {"control_id", "control_state", "changed_assumptions"}
    }
    return {"controls": controls, "run_configuration": configuration}


def _compare_values(
    left: Any,
    right: Any,
    path: tuple[str, ...],
    differences: list[ConfigurationDifference],
) -> None:
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        for key in sorted(set(left) | set(right)):
            key_text = str(key)
            child_path = (*path, key_text)
            left_value = left.get(key)
            right_value = right.get(key)
            if _ignore_difference(child_path, left_value, right_value):
                continue
            _compare_values(left_value, right_value, child_path, differences)
        return
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        for index in range(max(len(left), len(right))):
            left_value = left[index] if index < len(left) else "(missing)"
            right_value = right[index] if index < len(right) else "(missing)"
            _compare_values(left_value, right_value, (*path, f"[{index}]"), differences)
        return
    left_value = _normalize_value(left)
    right_value = _normalize_value(right)
    if left_value == right_value or _ignore_difference(path, left_value, right_value):
        return
    category, label, units = _classify_difference(path)
    differences.append(
        ConfigurationDifference(
            path=_difference_path(path),
            label=label,
            category=category,
            left_value=left_value,
            right_value=right_value,
            units=units,
            material=category in {"atmospheric", "numerical"},
        )
    )


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_value(item) for item in value]
    return value


_IGNORED_SEGMENTS = {
    "run_id",
    "result_id",
    "cloud_world_id",
    "simulation_id",
    "simulation_display_name",
    "source_recipe_id",
    "parent_simulation_id",
    "parent_result_id",
    "reference_simulation_id",
    "reference_result_id",
    "user_question",
    "generated_input_sha256",
    "generated_forcing_input_sha256",
    "science_settings_sha256",
    "fixed_assumptions_sha256",
}


def _ignore_difference(path: tuple[str, ...], left: Any, right: Any) -> bool:
    for segment in path:
        lowered = segment.lower()
        if (
            lowered in _IGNORED_SEGMENTS
            or "sha256" in lowered
            or lowered.endswith("_hash")
            or lowered.endswith("_path")
            or lowered.endswith("_directory")
            or lowered.endswith("_timestamp")
            or lowered.endswith("_at")
            or lowered.startswith("worker_")
            or lowered.startswith("runtime_")
        ):
            return True
    return _absolute_path(left) or _absolute_path(right)


def _absolute_path(value: Any) -> bool:
    return isinstance(value, str) and (value.startswith("/") or value.startswith("~"))


_DIFFERENCE_CLASSIFICATIONS: dict[str, tuple[DifferenceCategory, str, str | None]] = {
    "surface_moisture_flux_g_g_m_s": (
        "atmospheric",
        "Surface moisture supply",
        "g/g m/s",
    ),
    "surface_sensible_heat_flux_k_m_s": (
        "atmospheric",
        "Surface sensible heat supply",
        "K m/s",
    ),
    "surface_heat_flux_k_m_s": (
        "atmospheric",
        "Surface sensible heat supply",
        "K m/s",
    ),
    "surface_patch_heat_flux_perturbation_k_m_s": (
        "atmospheric",
        "Surface-patch heat-flux perturbation",
        "K m/s",
    ),
    "surface_patch_moisture_flux_perturbation_g_g_m_s": (
        "atmospheric",
        "Surface-patch moisture-flux perturbation",
        "g/g m/s",
    ),
    "surface_temperature_k": ("atmospheric", "Surface temperature", "K"),
    "dx_m": ("numerical", "Grid spacing x", "m"),
    "dy_m": ("numerical", "Grid spacing y", "m"),
    "dz_m": ("numerical", "Grid spacing z", "m"),
    "model_top_m": ("numerical", "Model top", "m"),
    "time_step_seconds": ("numerical", "Target timestep", "s"),
    "target_seconds": ("numerical", "Target timestep", "s"),
    "duration_seconds": ("numerical", "Simulation duration", "s"),
    "output_cadence": ("output", "Model-field cadence", None),
    "output_cadence_seconds": ("output", "Model-field cadence", "s"),
    "diagnostic_cadence_seconds": ("output", "Diagnostic cadence", "s"),
    "required_output_fields": ("output", "Requested fields", None),
    "requested_fields": ("output", "Requested fields", None),
}

_DIFFERENCE_CONTAINER_CATEGORIES: dict[str, DifferenceCategory] = {
    "atmospheric_profile": "atmospheric",
    "atmospheric_profiles": "atmospheric",
    "forcing": "atmospheric",
    "initial_profile": "atmospheric",
    "initial_profiles": "atmospheric",
    "large_scale_forcing": "atmospheric",
    "sounding": "atmospheric",
    "surface_fluxes": "atmospheric",
    "surface_forcing": "atmospheric",
    "surface_forcing_patch": "atmospheric",
    "boundary_conditions": "numerical",
    "domain": "numerical",
    "grid": "numerical",
    "microphysics": "numerical",
    "physics": "numerical",
    "time_step_strategy": "numerical",
    "timestep_strategy": "numerical",
    "turbulence": "numerical",
}


def _classify_difference(path: tuple[str, ...]) -> tuple[DifferenceCategory, str, str | None]:
    leaf = path[-1] if path else "configuration"
    classification = _DIFFERENCE_CLASSIFICATIONS.get(leaf)
    if classification is not None:
        return classification
    for segment in reversed(path):
        category = _DIFFERENCE_CONTAINER_CATEGORIES.get(segment)
        if category is not None:
            return category, _humanize(leaf), None
    return "metadata", _humanize(leaf), None


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def _difference_path(path: tuple[str, ...]) -> str:
    rendered = ""
    for segment in path:
        if segment.startswith("["):
            rendered += segment
        else:
            rendered += f".{segment}" if rendered else segment
    return rendered


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
