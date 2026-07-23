"""Durable notes keyed to stable Cloud World and Simulation identities."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cloud_chamber.settings import CloudChamberSettings

NOTE_SCHEMA_VERSION: Literal[1] = 1
MAX_NOTE_CHARACTERS = 20_000
_IDENTITY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")


class SimulationNoteError(ValueError):
    """Raised when a Simulation note cannot be read or persisted safely."""


class SimulationNoteRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = NOTE_SCHEMA_VERSION
    world_id: str
    simulation_id: str
    text: str = Field(max_length=MAX_NOTE_CHARACTERS)
    created_at: datetime
    updated_at: datetime


class SimulationNoteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: SimulationNoteRecord | None


class SimulationNoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(max_length=MAX_NOTE_CHARACTERS)


def load_simulation_note(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
) -> SimulationNoteRecord | None:
    """Load one note without coupling it to a replaceable run artifact."""
    path = _note_path(settings, world_id=world_id, simulation_id=simulation_id)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
        record = SimulationNoteRecord.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise SimulationNoteError("The saved Simulation note is invalid or unreadable.") from exc
    if record.world_id != world_id or record.simulation_id != simulation_id:
        raise SimulationNoteError("The saved Simulation note identity does not match its path.")
    return record


def save_simulation_note(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
    text: str,
) -> SimulationNoteRecord | None:
    """Atomically save one note, or clear it when the submitted text is empty."""
    path = _note_path(settings, world_id=world_id, simulation_id=simulation_id)
    normalized_text = text.strip()
    if not normalized_text:
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise SimulationNoteError("The Simulation note could not be cleared.") from exc
        return None

    existing = load_simulation_note(
        settings,
        world_id=world_id,
        simulation_id=simulation_id,
    )
    now = datetime.now(UTC)
    record = SimulationNoteRecord(
        world_id=world_id,
        simulation_id=simulation_id,
        text=normalized_text,
        created_at=existing.created_at if existing else now,
        updated_at=now,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary_path.open("x") as handle:
            handle.write(record.model_dump_json(indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except OSError as exc:
        temporary_path.unlink(missing_ok=True)
        raise SimulationNoteError("The Simulation note could not be saved.") from exc
    return record


def _note_path(
    settings: CloudChamberSettings,
    *,
    world_id: str,
    simulation_id: str,
) -> Path:
    _validate_identity("World", world_id)
    _validate_identity("Simulation", simulation_id)
    return (
        settings.runtime_home.expanduser() / "simulation-notes" / world_id / f"{simulation_id}.json"
    )


def _validate_identity(label: str, value: str) -> None:
    if not _IDENTITY_PATTERN.fullmatch(value):
        raise SimulationNoteError(f"{label} identity is invalid.")
