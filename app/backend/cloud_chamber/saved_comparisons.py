"""World-owned durable Saved Comparisons built from live Compare workspaces."""

from __future__ import annotations

import json
import math
import os
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Literal, cast
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from cloud_chamber.explore_state import ExploreWorldState
from cloud_chamber.settings import CloudChamberSettings

SAVED_COMPARISON_SCHEMA_VERSION: Literal[1] = 1
MAX_SAVED_COMPARISONS_PER_WORLD = 100
MAX_SAVED_COMPARISON_FILE_BYTES = 8_000_000
MAX_TITLE_CHARACTERS = 120
MAX_QUESTION_CHARACTERS = 2_000
MAX_RESTORATION_MESSAGE_CHARACTERS = 1_000
MAX_MATERIAL_DIFFERENCES = 100
MAX_DIFFERENCE_VALUE_DEPTH = 4
MAX_DIFFERENCE_COLLECTION_ITEMS = 100
MAX_DIFFERENCE_STRING_CHARACTERS = 1_000
_IDENTITY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
_RECORD_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")
_WORLD_IDS = ("trade_cumulus", "mountain_waves", "supercells")
_LOCK = RLock()

WorldId = Literal["trade_cumulus", "mountain_waves", "supercells"]
RestorationStatus = Literal["healthy", "partially_restorable", "unavailable"]
CompareSide = Literal["left", "right"]


class SavedComparisonError(ValueError):
    """Raised when a Saved Comparison cannot be read or persisted safely."""


class SavedCompareLinkModes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time: bool
    view: bool
    plane: bool
    camera: bool
    selection: bool


class SupercellsComparePresentation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left: Literal["scene", "evidence"]
    right: Literal["scene", "evidence"]


class SavedComparisonWorkspace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = SAVED_COMPARISON_SCHEMA_VERSION
    world_id: WorldId
    left_simulation_id: str
    right_simulation_id: str
    left_state: ExploreWorldState
    right_state: ExploreWorldState
    links: SavedCompareLinkModes
    context_collapsed: bool
    supercells_presentation: SupercellsComparePresentation | None = None

    @model_validator(mode="after")
    def validate_workspace_identity(self) -> SavedComparisonWorkspace:
        _validate_identity("Left Simulation", self.left_simulation_id)
        _validate_identity("Right Simulation", self.right_simulation_id)
        if self.left_simulation_id == self.right_simulation_id:
            raise ValueError("Saved Comparisons require two distinct Simulations.")
        if self.left_state.world_id != self.world_id or self.right_state.world_id != self.world_id:
            raise ValueError("Saved Compare state does not match the owning World.")
        if self.world_id == "supercells" and self.supercells_presentation is None:
            raise ValueError("Supercells Saved Comparisons require per-side presentation state.")
        if self.world_id != "supercells" and self.supercells_presentation is not None:
            raise ValueError("Only Supercells uses per-side presentation state.")
        return self


class CapturedComparisonDifference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1, max_length=256)
    label: str = Field(min_length=1, max_length=256)
    category: Literal["atmospheric", "numerical", "output", "operational", "metadata"]
    left_value: Any = None
    right_value: Any = None
    left_known: bool = True
    right_known: bool = True
    units: str | None = Field(default=None, max_length=80)
    material: bool = True

    @field_validator("left_value", "right_value")
    @classmethod
    def validate_portable_value(cls, value: Any) -> Any:
        _validate_portable_difference_value(value)
        return value


class CapturedPairSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left_display_name: str = Field(min_length=1, max_length=200)
    right_display_name: str = Field(min_length=1, max_length=200)
    relationship: str = Field(min_length=1, max_length=500)
    controlled_pair: bool
    controlled_pair_message: str = Field(min_length=1, max_length=1_000)
    material_differences: list[CapturedComparisonDifference] = Field(
        default_factory=list,
        max_length=MAX_MATERIAL_DIFFERENCES,
    )


class SavedComparisonRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    saved_comparison_id: str
    title: str = Field(min_length=1, max_length=MAX_TITLE_CHARACTERS)
    scientific_question: str | None = Field(default=None, max_length=MAX_QUESTION_CHARACTERS)
    created_at: datetime
    updated_at: datetime
    restoration_status: RestorationStatus = "healthy"
    restoration_message: str | None = Field(
        default=None,
        max_length=MAX_RESTORATION_MESSAGE_CHARACTERS,
    )
    captured_pair: CapturedPairSummary
    workspace: SavedComparisonWorkspace


class SavedComparisonLibrary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = SAVED_COMPARISON_SCHEMA_VERSION
    world_id: WorldId
    saved_comparisons: list[SavedComparisonRecord] = Field(
        default_factory=list,
        max_length=MAX_SAVED_COMPARISONS_PER_WORLD,
    )


class SavedComparisonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=MAX_TITLE_CHARACTERS)
    scientific_question: str | None = Field(default=None, max_length=MAX_QUESTION_CHARACTERS)
    workspace: SavedComparisonWorkspace


class SavedComparisonUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=MAX_TITLE_CHARACTERS)
    scientific_question: str | None = Field(default=None, max_length=MAX_QUESTION_CHARACTERS)
    restoration_status: RestorationStatus | None = None
    restoration_message: str | None = Field(
        default=None,
        max_length=MAX_RESTORATION_MESSAGE_CHARACTERS,
    )


class SavedComparisonDependency(BaseModel):
    model_config = ConfigDict(extra="forbid")

    side: CompareSide
    simulation_id: str
    display_name: str
    available: bool


class SavedComparisonEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record: SavedComparisonRecord
    dependencies: list[SavedComparisonDependency]
    effective_restoration_status: RestorationStatus
    effective_restoration_message: str | None = None


class SavedComparisonLibraryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: WorldId
    saved_comparisons: list[SavedComparisonEntry]


class SavedComparisonDependent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: WorldId
    saved_comparison_id: str
    title: str
    side: CompareSide


SimulationExists = Callable[[str, str], bool]


def load_saved_comparison_library(
    settings: CloudChamberSettings,
    *,
    world_id: str,
) -> SavedComparisonLibrary:
    canonical_world_id = _validate_world_id(world_id)
    with _LOCK:
        path = _library_path(settings, canonical_world_id)
        if not path.exists():
            return SavedComparisonLibrary(world_id=canonical_world_id)
        try:
            if path.stat().st_size > MAX_SAVED_COMPARISON_FILE_BYTES:
                raise SavedComparisonError(
                    "The Saved Comparison library exceeds the supported local size limit."
                )
            payload = migrate_saved_comparison_library_payload(json.loads(path.read_text()))
            library = SavedComparisonLibrary.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise SavedComparisonError("The Saved Comparison library is unreadable.") from exc
        if library.world_id != canonical_world_id:
            raise SavedComparisonError("The Saved Comparison library identity is invalid.")
        _validate_library(library)
        return library


def migrate_saved_comparison_library_payload(payload: object) -> dict[str, Any]:
    """Return the supported schema payload or fail until a real migration exists."""
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise SavedComparisonError("The Saved Comparison library uses an unsupported schema.")
    return cast(dict[str, Any], payload)


def saved_comparison_count(
    settings: CloudChamberSettings,
    *,
    world_id: str,
) -> int:
    return len(load_saved_comparison_library(settings, world_id=world_id).saved_comparisons)


def list_saved_comparisons(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_exists: SimulationExists,
) -> SavedComparisonLibraryResponse:
    library = load_saved_comparison_library(settings, world_id=world_id)
    return SavedComparisonLibraryResponse(
        world_id=library.world_id,
        saved_comparisons=[
            _entry(record, simulation_exists=simulation_exists)
            for record in sorted(
                library.saved_comparisons,
                key=lambda item: item.updated_at,
                reverse=True,
            )
        ],
    )


def get_saved_comparison(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    saved_comparison_id: str,
    simulation_exists: SimulationExists,
) -> SavedComparisonEntry:
    _validate_record_id(saved_comparison_id)
    library = load_saved_comparison_library(settings, world_id=world_id)
    record = next(
        (
            item
            for item in library.saved_comparisons
            if item.saved_comparison_id == saved_comparison_id
        ),
        None,
    )
    if record is None:
        raise SavedComparisonError("Saved Comparison not found.")
    return _entry(record, simulation_exists=simulation_exists)


def create_saved_comparison(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    request: SavedComparisonCreate,
    captured_pair: CapturedPairSummary,
    simulation_exists: SimulationExists,
) -> SavedComparisonEntry:
    canonical_world_id = _validate_world_id(world_id)
    if request.workspace.world_id != canonical_world_id:
        raise SavedComparisonError("The Saved Comparison does not match the owning World.")
    for simulation_id in (
        request.workspace.left_simulation_id,
        request.workspace.right_simulation_id,
    ):
        if not simulation_exists(canonical_world_id, simulation_id):
            raise SavedComparisonError(
                "Both Simulations must be available when a comparison is saved."
            )
    with _LOCK:
        library = load_saved_comparison_library(settings, world_id=canonical_world_id)
        if len(library.saved_comparisons) >= MAX_SAVED_COMPARISONS_PER_WORLD:
            raise SavedComparisonError(
                f"A World can retain at most {MAX_SAVED_COMPARISONS_PER_WORLD} Saved Comparisons."
            )
        now = datetime.now(UTC)
        title = request.title.strip()
        if not title:
            raise SavedComparisonError("Saved Comparison title is required.")
        question = request.scientific_question.strip() if request.scientific_question else None
        record = SavedComparisonRecord(
            saved_comparison_id=uuid4().hex,
            title=title,
            scientific_question=question or None,
            created_at=now,
            updated_at=now,
            captured_pair=captured_pair,
            workspace=request.workspace,
        )
        library.saved_comparisons.append(record)
        _write_library(settings, library)
        return _entry(record, simulation_exists=simulation_exists)


def update_saved_comparison(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    saved_comparison_id: str,
    request: SavedComparisonUpdate,
    simulation_exists: SimulationExists,
) -> SavedComparisonEntry:
    _validate_record_id(saved_comparison_id)
    with _LOCK:
        library = load_saved_comparison_library(settings, world_id=world_id)
        record = next(
            (
                item
                for item in library.saved_comparisons
                if item.saved_comparison_id == saved_comparison_id
            ),
            None,
        )
        if record is None:
            raise SavedComparisonError("Saved Comparison not found.")
        updates = request.model_dump(exclude_unset=True)
        if "title" in updates:
            updates["title"] = updates["title"].strip()
            if not updates["title"]:
                raise SavedComparisonError("Saved Comparison title is required.")
        if "scientific_question" in updates and updates["scientific_question"] is not None:
            updates["scientific_question"] = updates["scientific_question"].strip() or None
        if "restoration_message" in updates and updates["restoration_message"] is not None:
            updates["restoration_message"] = updates["restoration_message"].strip() or None
        updates["updated_at"] = datetime.now(UTC)
        updated = record.model_copy(update=updates)
        library.saved_comparisons = [
            updated if item.saved_comparison_id == saved_comparison_id else item
            for item in library.saved_comparisons
        ]
        _write_library(settings, library)
        return _entry(updated, simulation_exists=simulation_exists)


def delete_saved_comparison(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    saved_comparison_id: str,
) -> None:
    _validate_record_id(saved_comparison_id)
    with _LOCK:
        library = load_saved_comparison_library(settings, world_id=world_id)
        retained = [
            item
            for item in library.saved_comparisons
            if item.saved_comparison_id != saved_comparison_id
        ]
        if len(retained) == len(library.saved_comparisons):
            raise SavedComparisonError("Saved Comparison not found.")
        library.saved_comparisons = retained
        _write_library(settings, library)


def saved_comparison_dependents(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
) -> list[SavedComparisonDependent]:
    canonical_world_id = _validate_world_id(world_id)
    _validate_identity("Simulation", simulation_id)
    library = load_saved_comparison_library(settings, world_id=canonical_world_id)
    dependents: list[SavedComparisonDependent] = []
    for record in library.saved_comparisons:
        for side in ("left", "right"):
            dependency_id = getattr(record.workspace, f"{side}_simulation_id")
            if dependency_id == simulation_id:
                dependents.append(
                    SavedComparisonDependent(
                        world_id=canonical_world_id,
                        saved_comparison_id=record.saved_comparison_id,
                        title=record.title,
                        side=side,
                    )
                )
    return dependents


def captured_pair_summary_from_descriptor(descriptor: Any) -> CapturedPairSummary:
    simulations = {item.simulation_id: item for item in descriptor.simulations}
    left = simulations.get(descriptor.selected_left_simulation_id)
    right = simulations.get(descriptor.selected_right_simulation_id)
    compatibility = descriptor.compatibility
    if left is None or right is None or compatibility is None:
        raise SavedComparisonError("The selected Compare pair is incomplete.")
    return CapturedPairSummary(
        left_display_name=left.display_name,
        right_display_name=right.display_name,
        relationship=compatibility.relationship,
        controlled_pair=compatibility.controlled_pair,
        controlled_pair_message=compatibility.controlled_pair_message,
        material_differences=[
            CapturedComparisonDifference.model_validate(item.model_dump(mode="json"))
            for item in descriptor.material_differences
        ],
    )


def _entry(
    record: SavedComparisonRecord,
    *,
    simulation_exists: SimulationExists,
) -> SavedComparisonEntry:
    dependencies = [
        SavedComparisonDependency(
            side="left",
            simulation_id=record.workspace.left_simulation_id,
            display_name=record.captured_pair.left_display_name,
            available=simulation_exists(
                record.workspace.world_id,
                record.workspace.left_simulation_id,
            ),
        ),
        SavedComparisonDependency(
            side="right",
            simulation_id=record.workspace.right_simulation_id,
            display_name=record.captured_pair.right_display_name,
            available=simulation_exists(
                record.workspace.world_id,
                record.workspace.right_simulation_id,
            ),
        ),
    ]
    missing = [item.display_name for item in dependencies if not item.available]
    message: str | None
    if missing:
        status: RestorationStatus = "unavailable"
        message = f"Missing retained Simulation: {', '.join(missing)}."
    else:
        status = record.restoration_status
        message = record.restoration_message
    return SavedComparisonEntry(
        record=record,
        dependencies=dependencies,
        effective_restoration_status=status,
        effective_restoration_message=message,
    )


def _validate_library(library: SavedComparisonLibrary) -> None:
    seen: set[str] = set()
    for record in library.saved_comparisons:
        _validate_record_id(record.saved_comparison_id)
        if record.saved_comparison_id in seen:
            raise SavedComparisonError("Saved Comparison identities must be unique.")
        seen.add(record.saved_comparison_id)
        if record.workspace.world_id != library.world_id:
            raise SavedComparisonError("A Saved Comparison has mismatched World identity.")


def _write_library(
    settings: CloudChamberSettings,
    library: SavedComparisonLibrary,
) -> None:
    path = _library_path(settings, library.world_id)
    serialized = library.model_dump_json(indent=2) + "\n"
    if len(serialized.encode("utf-8")) > MAX_SAVED_COMPARISON_FILE_BYTES:
        raise SavedComparisonError(
            "The Saved Comparison library exceeds the supported local size limit."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary_path.open("x") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except OSError as exc:
        temporary_path.unlink(missing_ok=True)
        raise SavedComparisonError("The Saved Comparison could not be saved.") from exc


def _library_path(settings: CloudChamberSettings, world_id: WorldId) -> Path:
    return settings.runtime_home.expanduser() / "saved-comparisons" / f"{world_id}.json"


def _validate_world_id(value: str) -> WorldId:
    if value not in _WORLD_IDS:
        raise SavedComparisonError("Cloud World identity is invalid.")
    return cast(WorldId, value)


def _validate_identity(label: str, value: str) -> None:
    if not _IDENTITY_PATTERN.fullmatch(value):
        raise SavedComparisonError(f"{label} identity is invalid.")


def _validate_record_id(value: str) -> None:
    if not _RECORD_ID_PATTERN.fullmatch(value):
        raise SavedComparisonError("Saved Comparison identity is invalid.")


def _validate_portable_difference_value(value: Any, *, depth: int = 0) -> None:
    if depth > MAX_DIFFERENCE_VALUE_DEPTH:
        raise ValueError("Captured difference values are nested too deeply.")
    if value is None or isinstance(value, bool | int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Captured difference values must be finite.")
        return
    if isinstance(value, str):
        if len(value) > MAX_DIFFERENCE_STRING_CHARACTERS:
            raise ValueError("Captured difference strings are too long.")
        return
    if isinstance(value, list):
        if len(value) > MAX_DIFFERENCE_COLLECTION_ITEMS:
            raise ValueError("Captured difference lists contain too many values.")
        for item in value:
            _validate_portable_difference_value(item, depth=depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > MAX_DIFFERENCE_COLLECTION_ITEMS:
            raise ValueError("Captured difference objects contain too many values.")
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 256:
                raise ValueError("Captured difference object keys are invalid.")
            _validate_portable_difference_value(item, depth=depth + 1)
        return
    raise ValueError("Captured difference values must be portable JSON values.")
