"""Durable Explore resume state and Saved Views keyed to stable Simulation identity."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Annotated, Literal, cast
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cloud_chamber.settings import CloudChamberSettings

EXPLORE_STATE_SCHEMA_VERSION: Literal[1] = 1
WORLD_STATE_VERSION: Literal[1] = 1
MAX_SAVED_VIEW_TITLE_CHARACTERS = 120
MAX_SAVED_VIEW_DESCRIPTION_CHARACTERS = 1_000
MAX_SAVED_VIEWS_PER_SIMULATION = 100
MAX_EXPLORE_STATE_FILE_BYTES = 2_000_000
MAX_STATE_IDENTIFIER_CHARACTERS = 128
MAX_VISIBLE_LAYER_IDS = 32
MAX_FIXED_SCALE_IDS = 16
MAX_HYDROMETEOR_CATEGORY_CODES = 16
_IDENTITY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
_SAVED_VIEW_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")
_LOCK = RLock()

FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
UnitIntervalFloat = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
PositiveDisplayFloat = Annotated[float, Field(gt=0, le=100, allow_inf_nan=False)]
PlaybackSpeedFloat = Annotated[float, Field(gt=0, le=16, allow_inf_nan=False)]
StateIdentifier = Annotated[
    str,
    Field(min_length=1, max_length=MAX_STATE_IDENTIFIER_CHARACTERS),
]
NativeIndex = Annotated[int, Field(ge=0, le=10_000_000)]
HydrometeorCategoryCode = Annotated[int, Field(ge=0, le=255)]


class ExploreStateError(ValueError):
    """Raised when durable Explore state cannot be read or persisted safely."""


class ExplorePoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_km: FiniteFloat
    y_km: FiniteFloat | None = None
    z_km: FiniteFloat


class CameraTransform(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: tuple[FiniteFloat, FiniteFloat, FiniteFloat]
    target: tuple[FiniteFloat, FiniteFloat, FiniteFloat]
    up: tuple[FiniteFloat, FiniteFloat, FiniteFloat]


class ExploreWorldStateBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state_version: Literal[1] = WORLD_STATE_VERSION
    model_time_seconds: FiniteFloat
    context_collapsed: bool = False
    secondary_section: Literal["science", "notes", "details"] = "science"
    selected_point: ExplorePoint | None = None


class TradeCumulusExploreState(ExploreWorldStateBase):
    world_id: Literal["trade_cumulus"]
    view_id: Literal["field", "updraft_lens"]
    scene_field_id: StateIdentifier
    slice_field_id: StateIdentifier
    fixed_scale_id: StateIdentifier | None = None
    active_slice_plane: Literal["horizontal", "vertical_x", "vertical_y"]
    slice_coordinate_km: FiniteFloat
    slice_native_index: NativeIndex
    horizontal_slice_coordinate_km: FiniteFloat | None = None
    threshold_native: FiniteFloat
    layer_opacity: UnitIntervalFloat
    point_size_px: PositiveDisplayFloat
    lens_opacity: UnitIntervalFloat
    show_slice_plane: bool
    show_cloud_boundary: bool
    show_horizontal_wind: bool
    wind_mode: Literal["perturbation", "total"]
    camera_preset: Literal[
        "overview",
        "top_down_xy",
        "look_along_x",
        "look_along_y",
        "low_level",
    ]
    camera_transform: CameraTransform | None = None
    playback_speed: PlaybackSpeedFloat
    display_controls_open: bool = False


class MountainWavesOverlayState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cloud_points: bool
    cloud_boundary: bool
    saturation_contour: bool
    horizontal_wind: bool
    potential_temperature_contours: bool


class MountainWavesExploreState(ExploreWorldStateBase):
    world_id: Literal["mountain_waves"]
    view_id: Literal["field", "wave_structure", "wave_cloud"]
    field_id: Literal[
        "w",
        "theta_perturbation",
        "cloud_liquid",
        "relative_humidity",
    ]
    fixed_scale_id: StateIdentifier
    viewport_id: Literal["focus", "full"]
    geometry_id: Literal["expanded", "physical"]
    overlays: MountainWavesOverlayState
    cloud_opacity: UnitIntervalFloat
    cloud_point_size_px: PositiveDisplayFloat
    playback_speed: PlaybackSpeedFloat


class SupercellsOverlayState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rotation: bool
    updraft_helicity: bool
    reflectivity: bool
    condensate: bool
    rain: bool
    wind: bool
    precipitating_condensate: bool
    vertical_motion: bool


class SupercellsExploreState(ExploreWorldStateBase):
    world_id: Literal["supercells"]
    lens_id: Literal[
        "rotating_updraft",
        "cloud_precipitation",
        "low_level_interactions",
    ]
    viewport_id: Literal["storm", "full"]
    evidence_view: Literal["plan", "xz", "yz"]
    plane_coordinate_km: FiniteFloat
    visible_layer_ids: list[StateIdentifier] = Field(max_length=MAX_VISIBLE_LAYER_IDS)
    fixed_scale_ids: list[StateIdentifier] = Field(max_length=MAX_FIXED_SCALE_IDS)
    overlays: SupercellsOverlayState
    hydrometeor_category_codes: list[HydrometeorCategoryCode] = Field(
        max_length=MAX_HYDROMETEOR_CATEGORY_CODES
    )
    camera_preset: Literal[
        "overview",
        "top_down_xy",
        "look_along_x",
        "look_along_y",
        "low_level",
    ]
    camera_transform: CameraTransform | None = None
    scene_opacity: UnitIntervalFloat
    scene_point_size: PositiveDisplayFloat
    selected_evidence_visible: bool
    playback_speed: PlaybackSpeedFloat
    display_controls_open: bool = False


ExploreWorldState = Annotated[
    TradeCumulusExploreState | MountainWavesExploreState | SupercellsExploreState,
    Field(discriminator="world_id"),
]


class ExploreStateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = EXPLORE_STATE_SCHEMA_VERSION
    world_id: StateIdentifier
    simulation_id: StateIdentifier
    captured_at: datetime
    state: ExploreWorldState


class SavedViewRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    saved_view_id: str
    title: str = Field(min_length=1, max_length=MAX_SAVED_VIEW_TITLE_CHARACTERS)
    description: str | None = Field(
        default=None,
        max_length=MAX_SAVED_VIEW_DESCRIPTION_CHARACTERS,
    )
    created_at: datetime
    updated_at: datetime
    restoration_status: Literal["healthy", "partially_restorable", "unavailable"] = "healthy"
    restoration_message: str | None = Field(default=None, max_length=1_000)
    snapshot: ExploreStateSnapshot


class ExploreStateLibrary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = EXPLORE_STATE_SCHEMA_VERSION
    world_id: StateIdentifier
    simulation_id: StateIdentifier
    last_active: ExploreStateSnapshot | None = None
    saved_views: list[SavedViewRecord] = Field(
        default_factory=list,
        max_length=MAX_SAVED_VIEWS_PER_SIMULATION,
    )


class ExploreStateLibraryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    library: ExploreStateLibrary
    backing_simulation_available: bool


class ExploreResumeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: ExploreWorldState


class SavedViewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=MAX_SAVED_VIEW_TITLE_CHARACTERS)
    description: str | None = Field(
        default=None,
        max_length=MAX_SAVED_VIEW_DESCRIPTION_CHARACTERS,
    )
    state: ExploreWorldState


class SavedViewUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_SAVED_VIEW_TITLE_CHARACTERS,
    )
    description: str | None = Field(
        default=None,
        max_length=MAX_SAVED_VIEW_DESCRIPTION_CHARACTERS,
    )
    restoration_status: Literal["healthy", "partially_restorable", "unavailable"] | None = None
    restoration_message: str | None = Field(default=None, max_length=1_000)


def load_explore_state_library(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
) -> ExploreStateLibrary:
    """Load one Simulation-owned Explore library."""
    with _LOCK:
        path = _library_path(settings, world_id=world_id, simulation_id=simulation_id)
        if not path.exists():
            return ExploreStateLibrary(world_id=world_id, simulation_id=simulation_id)
        try:
            if path.stat().st_size > MAX_EXPLORE_STATE_FILE_BYTES:
                raise ExploreStateError(
                    "The saved Explore-state file exceeds the supported local size limit."
                )
            raw_payload = json.loads(path.read_text())
            migration_required = (
                isinstance(raw_payload, dict) and raw_payload.get("schema_version") == 0
            )
            library = ExploreStateLibrary.model_validate(_migrate_library_payload(raw_payload))
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise ExploreStateError(
                "The saved Explore state uses an unsupported schema or is unreadable."
            ) from exc
        if library.world_id != world_id or library.simulation_id != simulation_id:
            raise ExploreStateError("The saved Explore-state identity does not match its path.")
        _validate_library_state_identity(library)
        if migration_required:
            _write_library(settings, library)
        return library


def explore_state_library_exists(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
) -> bool:
    return _library_path(settings, world_id=world_id, simulation_id=simulation_id).exists()


def save_last_active_explore_state(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
    state: ExploreWorldState,
) -> ExploreStateLibrary:
    with _LOCK:
        library = load_explore_state_library(
            settings,
            world_id=world_id,
            simulation_id=simulation_id,
        )
        _validate_state_identity(world_id, state)
        library.last_active = _snapshot(
            world_id=world_id,
            simulation_id=simulation_id,
            state=state,
        )
        _write_library(settings, library)
        return library


def create_saved_view(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
    request: SavedViewCreate,
) -> ExploreStateLibrary:
    with _LOCK:
        library = load_explore_state_library(
            settings,
            world_id=world_id,
            simulation_id=simulation_id,
        )
        _validate_state_identity(world_id, request.state)
        if len(library.saved_views) >= MAX_SAVED_VIEWS_PER_SIMULATION:
            raise ExploreStateError(
                f"A Simulation can retain at most {MAX_SAVED_VIEWS_PER_SIMULATION} Saved Views."
            )
        now = datetime.now(UTC)
        title = request.title.strip()
        if not title:
            raise ExploreStateError("Saved View title is required.")
        description = request.description.strip() if request.description else None
        library.saved_views.append(
            SavedViewRecord(
                saved_view_id=uuid4().hex,
                title=title,
                description=description or None,
                created_at=now,
                updated_at=now,
                snapshot=_snapshot(
                    world_id=world_id,
                    simulation_id=simulation_id,
                    state=request.state,
                    captured_at=now,
                ),
            )
        )
        _write_library(settings, library)
        return library


def update_saved_view(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
    saved_view_id: str,
    request: SavedViewUpdate,
) -> ExploreStateLibrary:
    _validate_saved_view_id(saved_view_id)
    with _LOCK:
        library = load_explore_state_library(
            settings,
            world_id=world_id,
            simulation_id=simulation_id,
        )
        record = next(
            (item for item in library.saved_views if item.saved_view_id == saved_view_id),
            None,
        )
        if record is None:
            raise ExploreStateError("Saved View not found.")
        updates = request.model_dump(exclude_unset=True)
        if "title" in updates:
            updates["title"] = updates["title"].strip()
            if not updates["title"]:
                raise ExploreStateError("Saved View title is required.")
        if "description" in updates and updates["description"] is not None:
            updates["description"] = updates["description"].strip() or None
        updates["updated_at"] = datetime.now(UTC)
        updated = record.model_copy(update=updates)
        library.saved_views = [
            updated if item.saved_view_id == saved_view_id else item for item in library.saved_views
        ]
        _write_library(settings, library)
        return library


def delete_saved_view(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
    saved_view_id: str,
) -> ExploreStateLibrary:
    _validate_saved_view_id(saved_view_id)
    with _LOCK:
        library = load_explore_state_library(
            settings,
            world_id=world_id,
            simulation_id=simulation_id,
        )
        retained = [item for item in library.saved_views if item.saved_view_id != saved_view_id]
        if len(retained) == len(library.saved_views):
            raise ExploreStateError("Saved View not found.")
        library.saved_views = retained
        _write_library(settings, library)
        return library


def _snapshot(
    *,
    world_id: str,
    simulation_id: str,
    state: ExploreWorldState,
    captured_at: datetime | None = None,
) -> ExploreStateSnapshot:
    return ExploreStateSnapshot(
        world_id=world_id,
        simulation_id=simulation_id,
        captured_at=captured_at or datetime.now(UTC),
        state=state,
    )


def _write_library(settings: CloudChamberSettings, library: ExploreStateLibrary) -> None:
    path = _library_path(
        settings,
        world_id=library.world_id,
        simulation_id=library.simulation_id,
    )
    serialized = library.model_dump_json(indent=2) + "\n"
    if len(serialized.encode("utf-8")) > MAX_EXPLORE_STATE_FILE_BYTES:
        raise ExploreStateError("The Explore state exceeds the supported local size limit.")
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
        raise ExploreStateError("The Explore state could not be saved.") from exc


def _migrate_library_payload(payload: object) -> object:
    """Migrate the one compatible development-era shape stored before v1."""
    if not isinstance(payload, dict) or payload.get("schema_version") != 0:
        return payload
    migrated = cast(dict[str, object], payload)
    migrated["schema_version"] = EXPLORE_STATE_SCHEMA_VERSION
    snapshots = []
    last_active = migrated.get("last_active")
    if last_active is not None:
        snapshots.append(last_active)
    saved_views = migrated.get("saved_views")
    if isinstance(saved_views, list):
        for record in saved_views:
            if isinstance(record, dict):
                snapshots.append(record.get("snapshot"))
    for snapshot in snapshots:
        if not isinstance(snapshot, dict) or snapshot.get("schema_version") != 0:
            raise ExploreStateError("The saved Explore state uses an unsupported legacy schema.")
        snapshot["schema_version"] = EXPLORE_STATE_SCHEMA_VERSION
        state = snapshot.get("state")
        if not isinstance(state, dict) or state.get("state_version") != 0:
            raise ExploreStateError("The saved Explore state uses an unsupported legacy schema.")
        state["state_version"] = WORLD_STATE_VERSION
        state.setdefault("context_collapsed", False)
        state.setdefault("secondary_section", "science")
        state.setdefault("selected_point", None)
        world_id = state.get("world_id")
        if world_id == "trade_cumulus":
            if "slice_native_index" not in state and "slice_index" in state:
                state["slice_native_index"] = state.pop("slice_index")
            state.setdefault("horizontal_slice_coordinate_km", None)
            state.setdefault("camera_transform", None)
            state.setdefault("display_controls_open", False)
        elif world_id == "supercells":
            state.setdefault("camera_transform", None)
            state.setdefault("display_controls_open", False)
        elif world_id != "mountain_waves":
            raise ExploreStateError("The saved Explore state uses an unsupported legacy World.")
    return migrated


def _library_path(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
) -> Path:
    _validate_identity("World", world_id)
    _validate_identity("Simulation", simulation_id)
    return settings.runtime_home.expanduser() / "explore-state" / world_id / f"{simulation_id}.json"


def _validate_library_state_identity(library: ExploreStateLibrary) -> None:
    if library.last_active:
        _validate_snapshot_identity(library, library.last_active)
    for record in library.saved_views:
        _validate_saved_view_id(record.saved_view_id)
        _validate_snapshot_identity(library, record.snapshot)


def _validate_snapshot_identity(
    library: ExploreStateLibrary,
    snapshot: ExploreStateSnapshot,
) -> None:
    if snapshot.world_id != library.world_id or snapshot.simulation_id != library.simulation_id:
        raise ExploreStateError("A saved Explore snapshot has mismatched identity.")
    _validate_state_identity(library.world_id, snapshot.state)


def _validate_state_identity(world_id: str, state: ExploreWorldState) -> None:
    if state.world_id != world_id:
        raise ExploreStateError("The Explore payload does not match the owning World.")


def _validate_identity(label: str, value: str) -> None:
    if not _IDENTITY_PATTERN.fullmatch(value):
        raise ExploreStateError(f"{label} identity is invalid.")


def _validate_saved_view_id(value: str) -> None:
    if not _SAVED_VIEW_ID_PATTERN.fullmatch(value):
        raise ExploreStateError("Saved View identity is invalid.")
