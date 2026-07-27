import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import cloud_chamber.saved_comparisons as saved_comparisons_module
from cloud_chamber.explore_state import TradeCumulusExploreState
from cloud_chamber.saved_comparisons import (
    CapturedComparisonDifference,
    CapturedPairSummary,
    CurrentSimulationDependency,
    SavedCompareLinkModes,
    SavedComparisonCreate,
    SavedComparisonError,
    SavedComparisonUpdate,
    SavedComparisonWorkspace,
    SupercellsComparePresentation,
    create_saved_comparison,
    delete_saved_comparison,
    get_saved_comparison,
    list_saved_comparisons,
    migrate_saved_comparison_library_payload,
    saved_comparison_dependents,
    update_saved_comparison,
)
from cloud_chamber.settings import load_settings


def trade_state(model_time_seconds: float = 12_060) -> TradeCumulusExploreState:
    return TradeCumulusExploreState(
        world_id="trade_cumulus",
        model_time_seconds=model_time_seconds,
        view_id="updraft_lens",
        scene_field_id="ql",
        slice_field_id="w",
        fixed_scale_id="trade_cumulus_updraft_velocity_v1",
        active_slice_plane="vertical_x",
        slice_coordinate_km=2.3666666,
        slice_native_index=5,
        threshold_native=1e-6,
        layer_opacity=0.68,
        point_size_px=11,
        lens_opacity=0.9,
        show_slice_plane=True,
        show_cloud_boundary=True,
        show_horizontal_wind=True,
        wind_mode="perturbation",
        camera_preset="overview",
        playback_speed=1,
    )


def workspace() -> SavedComparisonWorkspace:
    return SavedComparisonWorkspace(
        world_id="trade_cumulus",
        left_simulation_id="trade_cumulus_canonical_bomex",
        right_simulation_id="trade_cumulus_more_moisture",
        left_state=trade_state(),
        right_state=trade_state(12_180),
        links=SavedCompareLinkModes(
            time=True,
            view=True,
            plane=True,
            camera=True,
            selection=False,
        ),
        context_collapsed=False,
    )


def captured_pair() -> CapturedPairSummary:
    return CapturedPairSummary(
        left_display_name="Canonical BOMEX Baseline",
        right_display_name="More Moisture",
        relationship="Reference and controlled variation",
        controlled_pair=True,
        controlled_pair_message="Only surface moisture supply changed.",
        material_differences=[],
    )


def all_available() -> dict[str, CurrentSimulationDependency]:
    return {
        simulation_id: CurrentSimulationDependency(
            simulation_id=simulation_id,
            availability_state="available",
            availability_message="Simulation output is available for inspection.",
            role="reference" if "canonical" in simulation_id else "variation",
            ownership="built_in",
            protection_state="protected",
        )
        for simulation_id in (
            "trade_cumulus_canonical_bomex",
            "trade_cumulus_more_moisture",
        )
    }


def test_saved_comparison_crud_preserves_immutable_workspace(tmp_path: Path) -> None:
    settings = load_settings(home=tmp_path)
    created = create_saved_comparison(
        settings,
        world_id="trade_cumulus",
        request=SavedComparisonCreate(
            title="  Moisture response  ",
            scientific_question="  How does added moisture change cloud growth?  ",
            workspace=workspace(),
        ),
        captured_pair=captured_pair(),
        simulation_inventory=all_available(),
    )

    assert created.record.title == "Moisture response"
    assert created.record.scientific_question == "How does added moisture change cloud growth?"
    assert created.effective_restoration_status == "healthy"
    original_workspace = created.record.workspace.model_copy(deep=True)

    updated = update_saved_comparison(
        settings,
        world_id="trade_cumulus",
        saved_comparison_id=created.record.saved_comparison_id,
        request=SavedComparisonUpdate(
            title="Moisture pulse",
            restoration_status="partially_restorable",
            restoration_message="Mapped to the nearest retained output.",
        ),
        simulation_inventory=all_available(),
    )

    assert updated.record.title == "Moisture pulse"
    assert updated.record.workspace == original_workspace
    assert updated.effective_restoration_status == "partially_restorable"
    loaded = get_saved_comparison(
        settings,
        world_id="trade_cumulus",
        saved_comparison_id=created.record.saved_comparison_id,
        simulation_inventory=all_available(),
    )
    assert loaded == updated

    delete_saved_comparison(
        settings,
        world_id="trade_cumulus",
        saved_comparison_id=created.record.saved_comparison_id,
    )
    assert (
        list_saved_comparisons(
            settings,
            world_id="trade_cumulus",
            simulation_inventory=all_available(),
        ).saved_comparisons
        == []
    )
    assert list((tmp_path / "saved-comparisons").rglob("*.tmp")) == []


def test_missing_dependency_keeps_record_visible_and_marks_it_unavailable(
    tmp_path: Path,
) -> None:
    settings = load_settings(home=tmp_path)
    created = create_saved_comparison(
        settings,
        world_id="trade_cumulus",
        request=SavedComparisonCreate(title="Missing side", workspace=workspace()),
        captured_pair=captured_pair(),
        simulation_inventory=all_available(),
    )

    response = list_saved_comparisons(
        settings,
        world_id="trade_cumulus",
        simulation_inventory={
            "trade_cumulus_canonical_bomex": all_available()["trade_cumulus_canonical_bomex"],
            "trade_cumulus_more_moisture": CurrentSimulationDependency(
                simulation_id="trade_cumulus_more_moisture",
                availability_state="missing",
                availability_message="Simulation model output is not installed.",
                role="variation",
                ownership="built_in",
                protection_state="protected",
            ),
        },
    )

    assert len(response.saved_comparisons) == 1
    entry = response.saved_comparisons[0]
    assert entry.record.saved_comparison_id == created.record.saved_comparison_id
    assert entry.effective_restoration_status == "unavailable"
    assert entry.dependencies[1].available is False
    assert entry.dependencies[1].availability_state == "missing"
    assert entry.dependencies[1].ownership == "built_in"
    assert entry.dependencies[1].protection_state == "protected"
    assert "More Moisture" in (entry.effective_restoration_message or "")


def test_reverse_dependency_lookup_reports_each_side(tmp_path: Path) -> None:
    settings = load_settings(home=tmp_path)
    created = create_saved_comparison(
        settings,
        world_id="trade_cumulus",
        request=SavedComparisonCreate(title="Dependency lookup", workspace=workspace()),
        captured_pair=captured_pair(),
        simulation_inventory=all_available(),
    )

    right_dependents = saved_comparison_dependents(
        settings,
        world_id="trade_cumulus",
        simulation_id="trade_cumulus_more_moisture",
    )
    left_dependents = saved_comparison_dependents(
        settings,
        world_id="trade_cumulus",
        simulation_id="trade_cumulus_canonical_bomex",
    )

    assert len(right_dependents) == 1
    assert right_dependents[0].saved_comparison_id == created.record.saved_comparison_id
    assert right_dependents[0].side == "right"
    assert len(left_dependents) == 1
    assert left_dependents[0].saved_comparison_id == created.record.saved_comparison_id
    assert left_dependents[0].side == "left"


def test_saved_comparison_rejects_cross_world_and_duplicate_simulation_state() -> None:
    with pytest.raises(ValidationError, match="two distinct"):
        SavedComparisonWorkspace(
            world_id="trade_cumulus",
            left_simulation_id="same",
            right_simulation_id="same",
            left_state=trade_state(),
            right_state=trade_state(),
            links=SavedCompareLinkModes(
                time=False,
                view=False,
                plane=False,
                camera=False,
                selection=False,
            ),
            context_collapsed=True,
        )

    with pytest.raises(ValidationError, match="does not match the owning World"):
        SavedComparisonWorkspace.model_validate(
            {
                **workspace().model_dump(mode="json"),
                "world_id": "mountain_waves",
            }
        )


def test_saved_comparison_rejects_unknown_schema_without_rewriting(
    tmp_path: Path,
) -> None:
    settings = load_settings(home=tmp_path)
    path = tmp_path / "saved-comparisons" / "trade_cumulus.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 99, "world_id": "trade_cumulus"}))

    with pytest.raises(SavedComparisonError, match="unsupported schema"):
        list_saved_comparisons(
            settings,
            world_id="trade_cumulus",
            simulation_inventory=all_available(),
        )

    assert json.loads(path.read_text())["schema_version"] == 99


def test_non_supercells_workspace_rejects_supercells_presentation() -> None:
    payload = workspace().model_dump(mode="json")
    payload["supercells_presentation"] = SupercellsComparePresentation(
        left="scene",
        right="evidence",
    ).model_dump(mode="json")

    with pytest.raises(ValidationError, match="Only Supercells"):
        SavedComparisonWorkspace.model_validate(payload)


def test_saved_comparison_bounds_and_non_finite_state_are_rejected() -> None:
    with pytest.raises(ValidationError, match="at most 120"):
        SavedComparisonCreate(
            title="x" * 121,
            workspace=workspace(),
        )
    with pytest.raises(ValidationError, match="at most 2000"):
        SavedComparisonCreate(
            title="Bounded",
            scientific_question="x" * 2_001,
            workspace=workspace(),
        )
    with pytest.raises(ValidationError, match="finite"):
        SavedComparisonWorkspace.model_validate(
            {
                **workspace().model_dump(mode="json"),
                "left_state": {
                    **trade_state().model_dump(mode="json"),
                    "model_time_seconds": float("nan"),
                },
            }
        )
    with pytest.raises(ValidationError, match="finite"):
        CapturedComparisonDifference(
            path="atmosphere.value",
            label="Value",
            category="atmospheric",
            left_value=float("inf"),
            right_value=1,
        )
    with pytest.raises(ValidationError, match="too long"):
        CapturedComparisonDifference(
            path="atmosphere.value",
            label="Value",
            category="atmospheric",
            left_value="x" * 1_001,
            right_value=1,
        )


def test_record_count_and_file_size_are_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = load_settings(home=tmp_path)
    monkeypatch.setattr(
        saved_comparisons_module,
        "MAX_SAVED_COMPARISONS_PER_WORLD",
        1,
    )
    create_saved_comparison(
        settings,
        world_id="trade_cumulus",
        request=SavedComparisonCreate(title="First", workspace=workspace()),
        captured_pair=captured_pair(),
        simulation_inventory=all_available(),
    )
    with pytest.raises(SavedComparisonError, match="at most 1"):
        create_saved_comparison(
            settings,
            world_id="trade_cumulus",
            request=SavedComparisonCreate(title="Second", workspace=workspace()),
            captured_pair=captured_pair(),
            simulation_inventory=all_available(),
        )

    path = tmp_path / "saved-comparisons" / "mountain_waves.json"
    path.write_bytes(b"x" * 101)
    monkeypatch.setattr(
        saved_comparisons_module,
        "MAX_SAVED_COMPARISON_FILE_BYTES",
        100,
    )
    with pytest.raises(SavedComparisonError, match="size limit"):
        list_saved_comparisons(
            settings,
            world_id="mountain_waves",
            simulation_inventory=all_available(),
        )


def test_atomic_write_failure_preserves_existing_library(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = load_settings(home=tmp_path)
    created = create_saved_comparison(
        settings,
        world_id="trade_cumulus",
        request=SavedComparisonCreate(title="Original", workspace=workspace()),
        captured_pair=captured_pair(),
        simulation_inventory=all_available(),
    )
    path = tmp_path / "saved-comparisons" / "trade_cumulus.json"
    original = path.read_bytes()

    def fail_replace(_source: Path, _destination: Path) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(
        "cloud_chamber.saved_comparisons.os.replace",
        fail_replace,
    )
    with pytest.raises(SavedComparisonError, match="could not be saved"):
        update_saved_comparison(
            settings,
            world_id="trade_cumulus",
            saved_comparison_id=created.record.saved_comparison_id,
            request=SavedComparisonUpdate(title="Not persisted"),
            simulation_inventory=all_available(),
        )

    assert path.read_bytes() == original
    assert list(path.parent.glob("*.tmp")) == []


def test_schema_migration_entrypoint_rejects_unknown_versions() -> None:
    assert (
        migrate_saved_comparison_library_payload(
            {
                "schema_version": 1,
                "world_id": "trade_cumulus",
                "saved_comparisons": [],
            }
        )["schema_version"]
        == 1
    )
    with pytest.raises(SavedComparisonError, match="unsupported schema"):
        migrate_saved_comparison_library_payload(
            {
                "schema_version": 0,
                "world_id": "trade_cumulus",
                "saved_comparisons": [],
            }
        )
