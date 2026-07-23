import json
from pathlib import Path

import pytest

from cloud_chamber.settings import load_settings
from cloud_chamber.simulation_notes import (
    MAX_NOTE_CHARACTERS,
    SimulationNoteError,
    load_simulation_note,
    save_simulation_note,
)


def test_simulation_note_persists_by_stable_world_and_simulation_identity(
    tmp_path: Path,
) -> None:
    settings = load_settings(home=tmp_path)

    created = save_simulation_note(
        settings,
        world_id="trade_cumulus",
        simulation_id="trade_cumulus_canonical_bomex",
        text="  Cloud deepens after the third hour.  ",
    )

    assert created is not None
    assert created.text == "Cloud deepens after the third hour."
    assert created.created_at == created.updated_at
    loaded = load_simulation_note(
        settings,
        world_id="trade_cumulus",
        simulation_id="trade_cumulus_canonical_bomex",
    )
    assert loaded == created
    assert (
        tmp_path / "simulation-notes" / "trade_cumulus" / "trade_cumulus_canonical_bomex.json"
    ).exists()


def test_simulation_note_update_preserves_created_at_and_clear_removes_record(
    tmp_path: Path,
) -> None:
    settings = load_settings(home=tmp_path)
    first = save_simulation_note(
        settings,
        world_id="mountain_waves",
        simulation_id="mountain_waves_boulder_moist_reference",
        text="First observation",
    )
    updated = save_simulation_note(
        settings,
        world_id="mountain_waves",
        simulation_id="mountain_waves_boulder_moist_reference",
        text="Updated observation",
    )

    assert first is not None
    assert updated is not None
    assert updated.created_at == first.created_at
    assert updated.updated_at >= first.updated_at

    cleared = save_simulation_note(
        settings,
        world_id="mountain_waves",
        simulation_id="mountain_waves_boulder_moist_reference",
        text="   ",
    )

    assert cleared is None
    assert (
        load_simulation_note(
            settings,
            world_id="mountain_waves",
            simulation_id="mountain_waves_boulder_moist_reference",
        )
        is None
    )


def test_simulation_note_rejects_invalid_identity_and_corrupt_saved_data(
    tmp_path: Path,
) -> None:
    settings = load_settings(home=tmp_path)
    with pytest.raises(SimulationNoteError, match="World identity is invalid"):
        save_simulation_note(
            settings,
            world_id="../supercells",
            simulation_id="supercells_quarter_circle_reference",
            text="unsafe",
        )

    path = tmp_path / "simulation-notes" / "supercells" / "supercells_quarter_circle_reference.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "text": "incomplete"}))

    with pytest.raises(SimulationNoteError, match="invalid or unreadable"):
        load_simulation_note(
            settings,
            world_id="supercells",
            simulation_id="supercells_quarter_circle_reference",
        )

    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "world_id": "supercells",
                "simulation_id": "supercells_quarter_circle_reference",
                "text": "future schema",
                "created_at": "2026-07-23T12:00:00Z",
                "updated_at": "2026-07-23T12:00:00Z",
            },
        ),
    )
    with pytest.raises(SimulationNoteError, match="invalid or unreadable"):
        load_simulation_note(
            settings,
            world_id="supercells",
            simulation_id="supercells_quarter_circle_reference",
        )


def test_simulation_note_text_is_bounded(tmp_path: Path) -> None:
    settings = load_settings(home=tmp_path)

    with pytest.raises(ValueError):
        save_simulation_note(
            settings,
            world_id="supercells",
            simulation_id="supercells_quarter_circle_reference",
            text="x" * (MAX_NOTE_CHARACTERS + 1),
        )
