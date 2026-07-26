import json
from pathlib import Path

import pytest

from cloud_chamber.explore_state import (
    ExploreStateError,
    MountainWavesExploreState,
    MountainWavesOverlayState,
    SavedViewCreate,
    SavedViewUpdate,
    SupercellsExploreState,
    SupercellsOverlayState,
    TradeCumulusExploreState,
    create_saved_view,
    delete_saved_view,
    load_explore_state_library,
    save_last_active_explore_state,
    update_saved_view,
)
from cloud_chamber.settings import load_settings


def trade_state() -> TradeCumulusExploreState:
    return TradeCumulusExploreState(
        world_id="trade_cumulus",
        model_time_seconds=12_060,
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


def mountain_state() -> MountainWavesExploreState:
    return MountainWavesExploreState(
        world_id="mountain_waves",
        model_time_seconds=7_200,
        view_id="wave_cloud",
        field_id="w",
        fixed_scale_id="mountain_waves_vertical_velocity_v1",
        viewport_id="focus",
        geometry_id="expanded",
        overlays=MountainWavesOverlayState(
            cloud_points=True,
            cloud_boundary=True,
            saturation_contour=True,
            horizontal_wind=True,
            potential_temperature_contours=False,
        ),
        cloud_opacity=0.68,
        cloud_point_size_px=11,
        playback_speed=1,
    )


def supercells_state() -> SupercellsExploreState:
    return SupercellsExploreState(
        world_id="supercells",
        model_time_seconds=4_440,
        lens_id="rotating_updraft",
        viewport_id="storm",
        evidence_view="plan",
        plane_coordinate_km=3.166667,
        visible_layer_ids=[
            "storm_cloud_body",
            "rising_core",
            "cyclonic_rotation",
            "updraft_helicity",
        ],
        fixed_scale_ids=["supercell_midlevel_vertical_velocity_v1"],
        overlays=SupercellsOverlayState(
            rotation=True,
            updraft_helicity=True,
            reflectivity=False,
            condensate=False,
            rain=False,
            wind=False,
            precipitating_condensate=False,
            vertical_motion=True,
        ),
        hydrometeor_category_codes=[1, 2, 3, 4, 5],
        camera_preset="look_along_y",
        scene_opacity=0.74,
        scene_point_size=1,
        selected_evidence_visible=True,
        playback_speed=1,
    )


@pytest.mark.parametrize(
    ("world_id", "simulation_id", "state"),
    [
        ("trade_cumulus", "trade_cumulus_canonical_bomex", trade_state()),
        (
            "mountain_waves",
            "mountain_waves_boulder_moist_reference",
            mountain_state(),
        ),
        ("supercells", "supercells_quarter_circle_reference", supercells_state()),
    ],
)
def test_last_active_state_persists_explicit_world_payloads(
    tmp_path: Path,
    world_id: str,
    simulation_id: str,
    state: object,
) -> None:
    settings = load_settings(home=tmp_path)

    saved = save_last_active_explore_state(
        settings,
        world_id=world_id,
        simulation_id=simulation_id,
        state=state,  # type: ignore[arg-type]
    )
    loaded = load_explore_state_library(
        settings,
        world_id=world_id,
        simulation_id=simulation_id,
    )

    assert saved.last_active is not None
    assert loaded == saved
    assert loaded.last_active is not None
    assert loaded.last_active.state.world_id == world_id
    assert (tmp_path / "explore-state" / world_id / f"{simulation_id}.json").exists()


def test_saved_view_create_rename_status_and_delete_are_atomic(tmp_path: Path) -> None:
    settings = load_settings(home=tmp_path)
    created = create_saved_view(
        settings,
        world_id="trade_cumulus",
        simulation_id="trade_cumulus_canonical_bomex",
        request=SavedViewCreate(
            title="  Western turret  ",
            description="  Before the pulse weakens.  ",
            state=trade_state(),
        ),
    )

    assert len(created.saved_views) == 1
    saved_view_id = created.saved_views[0].saved_view_id
    assert created.saved_views[0].title == "Western turret"
    assert created.saved_views[0].description == "Before the pulse weakens."

    updated = update_saved_view(
        settings,
        world_id="trade_cumulus",
        simulation_id="trade_cumulus_canonical_bomex",
        saved_view_id=saved_view_id,
        request=SavedViewUpdate(
            title="Turret weakening",
            restoration_status="partially_restorable",
            restoration_message="Mapped to the nearest retained plane.",
        ),
    )
    assert updated.saved_views[0].title == "Turret weakening"
    assert updated.saved_views[0].restoration_status == "partially_restorable"

    deleted = delete_saved_view(
        settings,
        world_id="trade_cumulus",
        simulation_id="trade_cumulus_canonical_bomex",
        saved_view_id=saved_view_id,
    )
    assert deleted.saved_views == []
    assert list((tmp_path / "explore-state").rglob("*.tmp")) == []


def test_saved_view_rejects_whitespace_only_title(tmp_path: Path) -> None:
    settings = load_settings(home=tmp_path)

    with pytest.raises(ExploreStateError, match="title is required"):
        create_saved_view(
            settings,
            world_id="trade_cumulus",
            simulation_id="trade_cumulus_canonical_bomex",
            request=SavedViewCreate(title="   ", state=trade_state()),
        )


def test_saved_view_record_survives_without_backing_output(tmp_path: Path) -> None:
    settings = load_settings(home=tmp_path)
    created = create_saved_view(
        settings,
        world_id="supercells",
        simulation_id="supercells_quarter_circle_reference",
        request=SavedViewCreate(title="Mature rotation", state=supercells_state()),
    )

    loaded = load_explore_state_library(
        settings,
        world_id="supercells",
        simulation_id="supercells_quarter_circle_reference",
    )

    assert loaded.saved_views == created.saved_views
    assert loaded.saved_views[0].snapshot.simulation_id == ("supercells_quarter_circle_reference")


def test_known_legacy_state_migrates_to_version_one(tmp_path: Path) -> None:
    settings = load_settings(home=tmp_path)
    saved = save_last_active_explore_state(
        settings,
        world_id="trade_cumulus",
        simulation_id="trade_cumulus_canonical_bomex",
        state=trade_state(),
    )
    path = tmp_path / "explore-state" / "trade_cumulus" / "trade_cumulus_canonical_bomex.json"
    payload = json.loads(path.read_text())
    payload["schema_version"] = 0
    payload["last_active"]["schema_version"] = 0
    payload["last_active"]["state"]["state_version"] = 0
    payload["last_active"]["state"]["slice_index"] = payload["last_active"]["state"].pop(
        "slice_native_index"
    )
    payload["last_active"]["state"].pop("display_controls_open")
    path.write_text(json.dumps(payload))

    migrated = load_explore_state_library(
        settings,
        world_id="trade_cumulus",
        simulation_id="trade_cumulus_canonical_bomex",
    )

    assert saved.last_active is not None
    assert migrated.schema_version == 1
    assert migrated.last_active is not None
    assert migrated.last_active.state.state_version == 1
    assert isinstance(migrated.last_active.state, TradeCumulusExploreState)
    assert migrated.last_active.state.slice_native_index == 5
    assert migrated.last_active.state.display_controls_open is False
    rewritten = json.loads(path.read_text())
    assert rewritten["schema_version"] == 1
    assert rewritten["last_active"]["schema_version"] == 1
    assert rewritten["last_active"]["state"]["state_version"] == 1
    assert "slice_index" not in rewritten["last_active"]["state"]


def test_explore_state_rejects_mismatched_identity_and_future_schema(
    tmp_path: Path,
) -> None:
    settings = load_settings(home=tmp_path)
    with pytest.raises(ExploreStateError, match="does not match the owning World"):
        save_last_active_explore_state(
            settings,
            world_id="trade_cumulus",
            simulation_id="trade_cumulus_canonical_bomex",
            state=mountain_state(),
        )

    path = tmp_path / "explore-state" / "trade_cumulus" / "trade_cumulus_canonical_bomex.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "world_id": "trade_cumulus",
                "simulation_id": "trade_cumulus_canonical_bomex",
                "last_active": None,
                "saved_views": [],
            }
        )
    )

    with pytest.raises(ExploreStateError, match="unsupported schema"):
        load_explore_state_library(
            settings,
            world_id="trade_cumulus",
            simulation_id="trade_cumulus_canonical_bomex",
        )


def test_explore_state_rejects_unsafe_identity(tmp_path: Path) -> None:
    settings = load_settings(home=tmp_path)

    with pytest.raises(ExploreStateError, match="Simulation identity is invalid"):
        load_explore_state_library(
            settings,
            world_id="supercells",
            simulation_id="../outside",
        )
