"""Lightweight World-owned descriptors for transient ordinary Compare."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.cloud_worlds import (
    SimulationRecord,
    trade_cumulus_world_detail,
)
from cloud_chamber.explore_state import (
    ExploreWorldState,
    MountainWavesExploreState,
    MountainWavesOverlayState,
    SupercellsExploreState,
    SupercellsOverlayState,
    TradeCumulusExploreState,
)
from cloud_chamber.mountain_waves_world import (
    MountainWavesSimulationRecord,
    mountain_waves_world_detail,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.supercells_world import (
    SupercellSimulationRecord,
    supercells_world_detail,
)

WorldId = Literal["trade_cumulus", "mountain_waves", "supercells"]
WorldSlug = Literal["trade-cumulus", "mountain-waves", "supercells"]
CompareTopology = Literal["native_3d", "native_2d_xz"]

WORLD_SLUG_TO_ID: dict[str, WorldId] = {
    "trade-cumulus": "trade_cumulus",
    "mountain-waves": "mountain_waves",
    "supercells": "supercells",
}


class CompareDifference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    label: str
    category: Literal["atmospheric", "numerical", "output", "operational", "metadata"]
    left_value: Any = None
    right_value: Any = None
    left_known: bool = True
    right_known: bool = True
    units: str | None = None
    material: bool = True


class CompareGridDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topology: CompareTopology
    nx: int
    ny: int
    nz: int
    dx_m: float
    dy_m: float
    dz_m: float
    x_extent_km: tuple[float, float]
    y_extent_km: tuple[float, float] | None
    z_extent_km: tuple[float, float]


class CompareTimeDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    times_seconds: list[float]
    start_seconds: float
    end_seconds: float
    cadence_seconds: float
    saved_output_count: int
    interpolation_allowed: Literal[False] = False


class CompareSimulationDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    display_name: str
    world_id: WorldId
    role: str
    run_id: str
    result_id: str | None = None
    case_id: str
    parent_simulation_id: str | None = None
    reference_simulation_id: str | None = None
    lineage_state: str
    availability_state: str
    availability_message: str
    inspectable: bool
    grid: CompareGridDescriptor
    time: CompareTimeDescriptor
    available_field_ids: list[str]
    available_view_ids: list[str]
    fixed_scale_ids: list[str]
    plane_orientations: list[Literal["horizontal", "vertical_x", "vertical_y"]]
    camera_mapping: Literal["normalized_3d", "native_2d_xz"]
    initial_state: ExploreWorldState
    caveats: list[str] = Field(default_factory=list)


class CompareCompatibility(BaseModel):
    model_config = ConfigDict(extra="forbid")

    same_world: bool
    both_inspectable: bool
    relationship: str
    controlled_pair: bool
    controlled_pair_message: str
    shared_field_ids: list[str]
    shared_view_ids: list[str]
    shared_fixed_scale_ids: list[str]
    exact_time_link_available: bool
    nearest_time_link_available: bool
    time_tolerance_seconds: float
    physical_plane_link_available: bool
    camera_link_available: bool
    selection_link_available: bool
    blockers: list[str] = Field(default_factory=list)


class WorldCompareDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["world_compare_v1"] = "world_compare_v1"
    world_id: WorldId
    display_name: str
    simulations: list[CompareSimulationDescriptor]
    default_left_simulation_id: str | None
    default_right_simulation_id: str | None
    selected_left_simulation_id: str | None
    selected_right_simulation_id: str | None
    material_differences: list[CompareDifference]
    compatibility: CompareCompatibility | None
    no_second_simulation_message: str | None = None
    persistence: Literal["transient_only"] = "transient_only"


def world_compare_descriptor(
    settings: CloudChamberSettings,
    *,
    world_slug: str,
    left_simulation_id: str | None = None,
    right_simulation_id: str | None = None,
) -> WorldCompareDescriptor:
    """Return bounded Compare metadata without reading visualization volumes."""
    world_id = WORLD_SLUG_TO_ID.get(world_slug)
    if world_id is None:
        raise ValueError(f"Unknown Cloud World: {world_slug}")
    if world_id == "trade_cumulus":
        return _trade_descriptor(
            settings,
            left_simulation_id=left_simulation_id,
            right_simulation_id=right_simulation_id,
        )
    if world_id == "mountain_waves":
        return _mountain_descriptor(
            settings,
            left_simulation_id=left_simulation_id,
            right_simulation_id=right_simulation_id,
        )
    return _supercells_descriptor(
        settings,
        left_simulation_id=left_simulation_id,
        right_simulation_id=right_simulation_id,
    )


def _trade_descriptor(
    settings: CloudChamberSettings,
    *,
    left_simulation_id: str | None,
    right_simulation_id: str | None,
) -> WorldCompareDescriptor:
    world = trade_cumulus_world_detail(settings)
    simulations = [_trade_simulation(item) for item in world.simulations if item.simulation_id]
    default_left = world.reference_simulation.simulation_id
    if default_left is None:
        raise ValueError("Trade Cumulus Compare requires a stable reference Simulation.")
    default_right = world.featured_comparison.more_moisture_simulation_id
    left, right = _selected_pair(
        simulations,
        left_simulation_id or default_left,
        right_simulation_id or default_right,
    )
    differences = _trade_differences(left, right, world.simulations)
    compatibility = _compatibility(
        left,
        right,
        relationship=_relationship(left, right),
        controlled_pair=bool(
            {left.simulation_id, right.simulation_id} == {default_left, default_right}
        ),
        controlled_message=(
            "Only surface moisture supply changed; the retained pair is a controlled comparison."
            if {left.simulation_id, right.simulation_id} == {default_left, default_right}
            else "The selected Trade Cumulus relationship is not the approved controlled pair."
        ),
    )
    return WorldCompareDescriptor(
        world_id="trade_cumulus",
        display_name=world.display_name,
        simulations=simulations,
        default_left_simulation_id=default_left,
        default_right_simulation_id=default_right,
        selected_left_simulation_id=left.simulation_id,
        selected_right_simulation_id=right.simulation_id,
        material_differences=differences,
        compatibility=compatibility,
    )


def _mountain_descriptor(
    settings: CloudChamberSettings,
    *,
    left_simulation_id: str | None,
    right_simulation_id: str | None,
) -> WorldCompareDescriptor:
    world = mountain_waves_world_detail(settings)
    simulations = [_mountain_simulation(item) for item in world.simulations]
    default_left = "mountain_waves_dry_ridge"
    default_right = "mountain_waves_boulder_moist_reference"
    left, right = _selected_pair(
        simulations,
        left_simulation_id or default_left,
        right_simulation_id or default_right,
    )
    records = {item.simulation_id: item for item in world.simulations}
    left_record = records[left.simulation_id]
    right_record = records[right.simulation_id]
    direct_relationship = _mountain_envelope_relationship(left_record, right_record)
    differences = (
        _mountain_envelope_differences(left_record, right_record)
        if direct_relationship is not None
        else _mountain_absolute_differences(left_record, right_record)
    )
    pair_classification = direct_relationship or _mountain_pair_classification(
        left_record, right_record, differences
    )
    controlled = pair_classification == "controlled_physical_variation"
    compatibility = _compatibility(
        left,
        right,
        relationship=(_mountain_relationship_message(left, right, pair_classification)),
        controlled_pair=controlled,
        controlled_message=(
            "The shared variation envelope records one material physical change and "
            "matched numerical and observation layers."
            if controlled
            else (
                "The shared variation envelope classifies this pair as "
                f"{pair_classification.replace('_', ' ')}."
                if pair_classification != "different_recipes"
                else (
                    "The selected Simulations use different Mountain Waves Recipes. "
                    "Their absolute scientific and numerical layers remain comparable, "
                    "but they are not a controlled pair."
                )
            )
        ),
    )
    return WorldCompareDescriptor(
        world_id="mountain_waves",
        display_name=world.display_name,
        simulations=simulations,
        default_left_simulation_id=default_left,
        default_right_simulation_id=default_right,
        selected_left_simulation_id=left.simulation_id,
        selected_right_simulation_id=right.simulation_id,
        material_differences=differences,
        compatibility=compatibility,
    )


def _supercells_descriptor(
    settings: CloudChamberSettings,
    *,
    left_simulation_id: str | None,
    right_simulation_id: str | None,
) -> WorldCompareDescriptor:
    world = supercells_world_detail(settings)
    simulations = [_supercell_simulation(item) for item in world.simulations]
    available = [item for item in simulations if item.inspectable]
    if len(available) < 2:
        requested_left = left_simulation_id or world.reference_simulation.simulation_id
        requested = _simulation_by_id(simulations, requested_left)
        left = requested if requested.inspectable or not available else available[0]
        if right_simulation_id is not None:
            requested_right = _simulation_by_id(simulations, right_simulation_id)
            if requested_right.inspectable and requested_right.simulation_id != left.simulation_id:
                raise ValueError(
                    "Supercells Compare requires two retained, inspectable Simulations."
                )
        return WorldCompareDescriptor(
            world_id="supercells",
            display_name=world.display_name,
            simulations=simulations,
            default_left_simulation_id=left.simulation_id,
            default_right_simulation_id=None,
            selected_left_simulation_id=left.simulation_id,
            selected_right_simulation_id=None,
            material_differences=[],
            compatibility=None,
            no_second_simulation_message=(
                "Supercells currently has one retained Simulation. Compare requires two "
                "distinct Simulations in the same World; this reference is not cloned."
            ),
        )
    left, right = _selected_pair(
        available,
        left_simulation_id or "supercells_quarter_circle_reference",
        right_simulation_id or "supercells_straight_line_hodograph",
    )
    reverse = left.simulation_id == "supercells_straight_line_hodograph"
    differences = [
        CompareDifference(
            path="atmosphere.hodograph_geometry",
            label="Hodograph geometry",
            category="atmospheric",
            left_value="Straight line" if reverse else "Quarter circle",
            right_value="Quarter circle" if reverse else "Straight line",
        )
    ]
    compatibility = _compatibility(
        left,
        right,
        relationship=_relationship(left, right),
        controlled_pair=(
            {left.simulation_id, right.simulation_id}
            == {
                "supercells_quarter_circle_reference",
                "supercells_straight_line_hodograph",
            }
        ),
        controlled_message=(
            "Only hodograph curvature changed; thermodynamics, trigger, grid, timing, "
            "output inventory, model translation, and numerical options are matched. "
            "Coordinates and local evidence are compared without claiming storm-object lineage."
        ),
    )
    return WorldCompareDescriptor(
        world_id="supercells",
        display_name=world.display_name,
        simulations=simulations,
        default_left_simulation_id="supercells_quarter_circle_reference",
        default_right_simulation_id="supercells_straight_line_hodograph",
        selected_left_simulation_id=left.simulation_id,
        selected_right_simulation_id=right.simulation_id,
        material_differences=differences,
        compatibility=compatibility,
    )


def _trade_simulation(record: SimulationRecord) -> CompareSimulationDescriptor:
    if record.simulation_id is None:
        raise ValueError("Trade Cumulus Compare requires stable Simulation identity.")
    is_more_moisture = record.simulation_id == "trade_cumulus_more_moisture"
    time_seconds = 13_920.0 if is_more_moisture else 12_060.0
    plane_index = 72 if is_more_moisture else 83
    plane_coordinate = 1.6333333253860474 if is_more_moisture else 2.366666555404663
    return CompareSimulationDescriptor(
        simulation_id=record.simulation_id,
        display_name=record.display_name,
        world_id="trade_cumulus",
        role=record.role,
        run_id=record.run_id,
        result_id=record.result_id,
        case_id=record.case_id,
        parent_simulation_id=record.parent_simulation_id,
        reference_simulation_id=record.reference_simulation_id,
        lineage_state=record.lineage_state,
        availability_state=record.technical_state,
        availability_message=record.technical_state_message,
        inspectable=record.explore_available,
        grid=CompareGridDescriptor(
            topology="native_3d",
            nx=96,
            ny=96,
            nz=100,
            dx_m=66.6666667,
            dy_m=66.6666667,
            dz_m=30.0,
            x_extent_km=(-3.2, 3.2),
            y_extent_km=(-3.2, 3.2),
            z_extent_km=(0.0, 3.0),
        ),
        time=_regular_time_descriptor(14_400, 60),
        available_field_ids=["ql", "w"],
        available_view_ids=["field", "updraft_lens"],
        fixed_scale_ids=["trade_cumulus_updraft_velocity_v1"],
        plane_orientations=["horizontal", "vertical_x", "vertical_y"],
        camera_mapping="normalized_3d",
        initial_state=TradeCumulusExploreState(
            world_id="trade_cumulus",
            model_time_seconds=time_seconds,
            view_id="updraft_lens",
            scene_field_id="ql",
            slice_field_id="w",
            fixed_scale_id="trade_cumulus_updraft_velocity_v1",
            active_slice_plane="vertical_x",
            slice_coordinate_km=plane_coordinate,
            slice_native_index=plane_index,
            horizontal_slice_coordinate_km=0.0,
            threshold_native=1e-6,
            layer_opacity=0.68,
            point_size_px=11,
            lens_opacity=0.9,
            show_slice_plane=True,
            show_cloud_boundary=True,
            show_horizontal_wind=True,
            wind_mode="perturbation",
            camera_preset="overview",
            camera_transform=None,
            playback_speed=1,
        ),
        caveats=[],
    )


def _mountain_simulation(
    record: MountainWavesSimulationRecord,
) -> CompareSimulationDescriptor:
    configuration = record.configuration or {}
    domain = configuration.get("domain") if isinstance(configuration, Mapping) else {}
    domain = domain if isinstance(domain, Mapping) else {}
    duration = _number(configuration.get("duration_seconds"), 0)
    cadence = _number(configuration.get("output_cadence_seconds"), 1)
    nx = int(_number(domain.get("nx"), 1))
    ny = int(_number(domain.get("ny"), 1))
    nz = int(_number(domain.get("nz"), 1))
    dx = _number(domain.get("dx_m"), 1)
    dy = _number(domain.get("dy_m"), 1)
    dz = _number(domain.get("dz_m"), 1)
    active_top = _number(
        domain.get("active_model_top_m", domain.get("active_top_m")),
        nz * dz,
    )
    fields = ["w", "theta_perturbation"]
    views = ["field", "wave_structure"]
    scales = [
        "mountain_waves_vertical_velocity_v1",
        "mountain_waves_theta_perturbation_v1",
    ]
    if record.moist_fields_available:
        fields.extend(["cloud_liquid", "relative_humidity"])
        views.append("wave_cloud")
        scales.extend(
            [
                "mountain_waves_cloud_liquid_v1",
                "mountain_waves_relative_humidity_v1",
            ]
        )
    is_independent_dry_builtin = (
        record.role == "built_in" and record.simulation_id == "mountain_waves_dry_ridge"
    )
    return CompareSimulationDescriptor(
        simulation_id=record.simulation_id,
        display_name=record.display_name,
        world_id="mountain_waves",
        role=record.role,
        run_id=record.run_id,
        case_id=record.case_id,
        parent_simulation_id=record.parent_simulation_id,
        reference_simulation_id=(
            None if is_independent_dry_builtin else record.reference_simulation_id
        ),
        lineage_state=(
            "independent_built_in"
            if is_independent_dry_builtin
            else ("known" if record.role == "built_in" else "retained_variation")
        ),
        availability_state=record.state,
        availability_message=record.state_message,
        inspectable=record.inspectable,
        grid=CompareGridDescriptor(
            topology="native_2d_xz",
            nx=nx,
            ny=ny,
            nz=nz,
            dx_m=dx,
            dy_m=dy,
            dz_m=dz,
            x_extent_km=(-0.5 * nx * dx / 1_000, 0.5 * nx * dx / 1_000),
            y_extent_km=None,
            z_extent_km=(0.0, active_top / 1_000),
        ),
        time=_regular_time_descriptor(duration, cadence),
        available_field_ids=fields,
        available_view_ids=views,
        fixed_scale_ids=scales,
        plane_orientations=[],
        camera_mapping="native_2d_xz",
        initial_state=MountainWavesExploreState(
            world_id="mountain_waves",
            model_time_seconds=duration,
            view_id="wave_structure",
            field_id="w",
            fixed_scale_id="mountain_waves_vertical_velocity_v1",
            viewport_id="full" if record.simulation_id == "mountain_waves_dry_ridge" else "focus",
            geometry_id="expanded",
            overlays=MountainWavesOverlayState(
                cloud_points=False,
                cloud_boundary=False,
                saturation_contour=False,
                horizontal_wind=True,
                potential_temperature_contours=True,
            ),
            cloud_opacity=0.68,
            cloud_point_size_px=11,
            playback_speed=1,
        ),
        caveats=[*record.caveats, *record.warnings],
    )


def _supercell_simulation(
    record: SupercellSimulationRecord,
) -> CompareSimulationDescriptor:
    start = record.model_start_seconds or 0.0
    end = record.model_end_seconds or start
    cadence = record.history_cadence_seconds or 1.0
    times = [start + index * cadence for index in range(record.saved_output_count)]
    return CompareSimulationDescriptor(
        simulation_id=record.simulation_id,
        display_name=record.display_name,
        world_id="supercells",
        role=record.role,
        run_id=record.run_id,
        case_id=record.case_id,
        parent_simulation_id=record.parent_simulation_id,
        reference_simulation_id=record.reference_simulation_id,
        lineage_state=record.lineage_state,
        availability_state=record.technical_state,
        availability_message=record.technical_state_message,
        inspectable=record.explore_available,
        grid=CompareGridDescriptor(
            topology="native_3d",
            nx=240,
            ny=240,
            nz=60,
            dx_m=500,
            dy_m=500,
            dz_m=333.3333333,
            x_extent_km=(-60.0, 60.0),
            y_extent_km=(-60.0, 60.0),
            z_extent_km=(0.0, 20.0),
        ),
        time=CompareTimeDescriptor(
            times_seconds=times,
            start_seconds=start,
            end_seconds=end,
            cadence_seconds=cadence,
            saved_output_count=record.saved_output_count,
        ),
        available_field_ids=["winterp", "total_condensate"],
        available_view_ids=[
            "rotating_updraft",
            "cloud_precipitation",
            "low_level_interactions",
        ],
        fixed_scale_ids=[
            "supercell_midlevel_vertical_velocity_v1",
            "supercell_total_condensate_v2",
            "supercell_low_level_vertical_velocity_v1",
        ],
        plane_orientations=["horizontal", "vertical_x", "vertical_y"],
        camera_mapping="normalized_3d",
        initial_state=SupercellsExploreState(
            world_id="supercells",
            model_time_seconds=4_440,
            lens_id="rotating_updraft",
            viewport_id="storm",
            evidence_view="plan",
            plane_coordinate_km=3.1666669845581055,
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
                condensate=True,
                rain=False,
                wind=False,
                precipitating_condensate=False,
                vertical_motion=True,
            ),
            hydrometeor_category_codes=[1, 2, 3, 4, 5],
            camera_preset="look_along_y",
            camera_transform=None,
            scene_opacity=1,
            scene_point_size=1,
            selected_evidence_visible=False,
            playback_speed=1,
        ),
        caveats=[],
    )


def _regular_time_descriptor(
    duration_seconds: float,
    cadence_seconds: float,
) -> CompareTimeDescriptor:
    count = int(round(duration_seconds / cadence_seconds)) + 1
    times = [index * cadence_seconds for index in range(count)]
    return CompareTimeDescriptor(
        times_seconds=times,
        start_seconds=0,
        end_seconds=duration_seconds,
        cadence_seconds=cadence_seconds,
        saved_output_count=count,
    )


def _selected_pair(
    simulations: list[CompareSimulationDescriptor],
    left_simulation_id: str,
    right_simulation_id: str,
) -> tuple[CompareSimulationDescriptor, CompareSimulationDescriptor]:
    if left_simulation_id == right_simulation_id:
        raise ValueError("Compare requires two distinct Simulations.")
    return (
        _simulation_by_id(simulations, left_simulation_id),
        _simulation_by_id(simulations, right_simulation_id),
    )


def _simulation_by_id(
    simulations: list[CompareSimulationDescriptor],
    simulation_id: str,
) -> CompareSimulationDescriptor:
    simulation = next(
        (item for item in simulations if item.simulation_id == simulation_id),
        None,
    )
    if simulation is None:
        raise ValueError(f"Simulation is not available in this World: {simulation_id}")
    return simulation


def _compatibility(
    left: CompareSimulationDescriptor,
    right: CompareSimulationDescriptor,
    *,
    relationship: str,
    controlled_pair: bool,
    controlled_message: str,
) -> CompareCompatibility:
    fields = sorted(set(left.available_field_ids) & set(right.available_field_ids))
    views = sorted(set(left.available_view_ids) & set(right.available_view_ids))
    scales = sorted(set(left.fixed_scale_ids) & set(right.fixed_scale_ids))
    inspectable = left.inspectable and right.inspectable
    blockers = []
    if not inspectable:
        blockers.append("Both Simulations must have inspectable retained output.")
    if not views:
        blockers.append("The selected Simulations do not share a compatible Field or Lens.")
    exact_times = bool(set(left.time.times_seconds) & set(right.time.times_seconds))
    if not exact_times:
        blockers.append("The retained output histories have no exact modeled time in common.")
    native_3d = left.grid.topology == right.grid.topology == "native_3d"
    plane_link = native_3d and bool(set(left.plane_orientations) & set(right.plane_orientations))
    return CompareCompatibility(
        same_world=left.world_id == right.world_id,
        both_inspectable=inspectable,
        relationship=relationship,
        controlled_pair=controlled_pair,
        controlled_pair_message=controlled_message,
        shared_field_ids=fields,
        shared_view_ids=views,
        shared_fixed_scale_ids=scales,
        exact_time_link_available=exact_times,
        nearest_time_link_available=inspectable,
        time_tolerance_seconds=max(left.time.cadence_seconds, right.time.cadence_seconds) * 1.5,
        physical_plane_link_available=plane_link,
        camera_link_available=native_3d,
        selection_link_available=inspectable,
        blockers=blockers,
    )


def _relationship(
    left: CompareSimulationDescriptor,
    right: CompareSimulationDescriptor,
) -> str:
    if right.parent_simulation_id == left.simulation_id:
        return f"{right.display_name} is a child of {left.display_name}."
    if left.parent_simulation_id == right.simulation_id:
        return f"{left.display_name} is a child of {right.display_name}."
    if (
        left.reference_simulation_id
        and left.reference_simulation_id == right.reference_simulation_id
    ):
        return "Both Simulations share the same retained reference lineage."
    return "Both Simulations belong to the same Cloud World; no direct lineage is declared."


def _trade_differences(
    left: CompareSimulationDescriptor,
    right: CompareSimulationDescriptor,
    records: list[SimulationRecord],
) -> list[CompareDifference]:
    if right.simulation_id == "trade_cumulus_more_moisture":
        source = next(
            item for item in records if item.simulation_id == "trade_cumulus_more_moisture"
        )
        reverse = False
    elif left.simulation_id == "trade_cumulus_more_moisture":
        source = next(
            item for item in records if item.simulation_id == "trade_cumulus_more_moisture"
        )
        reverse = True
    else:
        return []
    differences = []
    for item in source.configuration_difference_from_reference or []:
        if not item.material:
            continue
        differences.append(
            CompareDifference(
                path=item.path,
                label=item.label,
                category=item.category,
                left_value=item.right_value if reverse else item.left_value,
                right_value=item.left_value if reverse else item.right_value,
                units=item.units,
                material=True,
            )
        )
    return differences


def _mapping_differences(
    left: Mapping[str, Any] | None,
    right: Mapping[str, Any] | None,
) -> list[CompareDifference]:
    flattened_left = _flatten_mapping(left or {})
    flattened_right = _flatten_mapping(right or {})
    differences: list[CompareDifference] = []
    for path in sorted(set(flattened_left) | set(flattened_right)):
        left_known = path in flattened_left
        right_known = path in flattened_right
        left_value = flattened_left.get(path)
        right_value = flattened_right.get(path)
        if left_known and right_known and left_value == right_value:
            continue
        differences.append(
            CompareDifference(
                path=path,
                label=_difference_label(path),
                category=_difference_category(path),
                left_value=left_value,
                right_value=right_value,
                left_known=left_known,
                right_known=right_known,
                units=_difference_units(path),
            )
        )
    return differences


def _mountain_comparison_configuration(
    record: MountainWavesSimulationRecord,
) -> dict[str, Any]:
    configuration = record.configuration or {}
    domain = configuration.get("domain")
    domain = domain if isinstance(domain, Mapping) else {}
    terrain = configuration.get("terrain")
    terrain = terrain if isinstance(terrain, Mapping) else {}
    active_top = domain.get("active_model_top_m", domain.get("active_top_m"))
    return {
        "atmosphere": {
            "moisture_state": "Moist" if record.moist else "Dry",
        },
        "duration_seconds": configuration.get("duration_seconds"),
        "output_cadence_seconds": configuration.get("output_cadence_seconds"),
        "domain": {
            "nx": domain.get("nx"),
            "ny": domain.get("ny"),
            "nz": domain.get("nz"),
            "dx_m": domain.get("dx_m"),
            "dy_m": domain.get("dy_m"),
            "dz_m": domain.get("dz_m"),
            "active_top_m": active_top,
        },
        "terrain": {
            key: terrain[key]
            for key in (
                "type",
                "terrain_flag",
                "itern",
                "height_m",
                "half_width_m",
                "center_m",
                "native_dx_m",
            )
            if key in terrain
        },
    }


def _mountain_envelope_relationship(
    left: MountainWavesSimulationRecord,
    right: MountainWavesSimulationRecord,
) -> str | None:
    if right.parent_simulation_id == left.simulation_id:
        return right.relationship_classification
    if left.parent_simulation_id == right.simulation_id:
        return left.relationship_classification
    return None


def _mountain_relationship_message(
    left: CompareSimulationDescriptor,
    right: CompareSimulationDescriptor,
    classification: str | None,
) -> str:
    if classification == "different_recipes":
        return (
            "Different Recipes: the selected Mountain Waves Simulations do not share "
            "one controlled Recipe envelope."
        )
    if classification is not None:
        if right.parent_simulation_id == left.simulation_id:
            return (
                f"{right.display_name} is a {classification.replace('_', ' ')} of "
                f"{left.display_name}."
            )
        if left.parent_simulation_id == right.simulation_id:
            return (
                f"{left.display_name} is a {classification.replace('_', ' ')} of "
                f"{right.display_name}."
            )
        return (
            "The selected same-Recipe Simulations form a "
            f"{classification.replace('_', ' ')} based on their normalized absolute layers."
        )
    return "No material normalized difference is recorded for this pair."


def _mountain_envelope_differences(
    left: MountainWavesSimulationRecord,
    right: MountainWavesSimulationRecord,
) -> list[CompareDifference]:
    child = right if right.parent_simulation_id == left.simulation_id else left
    reverse = child is left
    category_map = {
        "terrain": "atmospheric",
        "wind": "atmospheric",
        "moisture": "atmospheric",
        "stability/thermodynamics": "atmospheric",
        "forcing/initiation": "atmospheric",
        "numerical realization": "numerical",
        "observation plan": "output",
    }
    rows: list[CompareDifference] = []
    for group, differences in child.differences.items():
        for difference in differences:
            if difference.get("material") is False:
                continue
            before = difference.get("before")
            after = difference.get("after")
            rows.append(
                CompareDifference(
                    path=str(difference.get("path") or difference.get("label") or group),
                    label=str(difference.get("label") or group),
                    category=category_map.get(group, "metadata"),  # type: ignore[arg-type]
                    left_value=after if reverse else before,
                    right_value=before if reverse else after,
                    units=(
                        str(difference["units"]) if difference.get("units") is not None else None
                    ),
                    material=True,
                )
            )
    return rows


def _mountain_absolute_differences(
    left: MountainWavesSimulationRecord,
    right: MountainWavesSimulationRecord,
) -> list[CompareDifference]:
    layers = (
        ("scientific_design", "atmospheric", left.scientific_design, right.scientific_design),
        (
            "numerical_realization",
            "numerical",
            left.numerical_realization,
            right.numerical_realization,
        ),
        ("observation_plan", "output", left.observation_plan, right.observation_plan),
    )
    rows: list[CompareDifference] = []
    left_recipe_id = _mountain_recipe_id(left)
    right_recipe_id = _mountain_recipe_id(right)
    if left_recipe_id != right_recipe_id:
        rows.append(
            CompareDifference(
                path="recipe_id",
                label="Recipe",
                category="metadata",
                left_value=left_recipe_id,
                right_value=right_recipe_id,
            )
        )
    for prefix, category, left_payload, right_payload in layers:
        flattened_left = _flatten_mapping(left_payload or {})
        flattened_right = _flatten_mapping(right_payload or {})
        for path in sorted(set(flattened_left) | set(flattened_right)):
            left_known = path in flattened_left
            right_known = path in flattened_right
            left_value = flattened_left.get(path)
            right_value = flattened_right.get(path)
            if left_known and right_known and left_value == right_value:
                continue
            full_path = f"{prefix}.{path}"
            rows.append(
                CompareDifference(
                    path=full_path,
                    label=_mountain_difference_label(full_path),
                    category=category,  # type: ignore[arg-type]
                    left_value=left_value,
                    right_value=right_value,
                    left_known=left_known,
                    right_known=right_known,
                    units=_mountain_difference_units(full_path),
                )
            )
    return rows


def _mountain_pair_classification(
    left: MountainWavesSimulationRecord,
    right: MountainWavesSimulationRecord,
    differences: list[CompareDifference],
) -> str:
    if _mountain_recipe_id(left) != _mountain_recipe_id(right):
        return "different_recipes"
    physical = [item for item in differences if item.category == "atmospheric"]
    numerical = [item for item in differences if item.category == "numerical"]
    observation = [item for item in differences if item.category == "output"]
    if physical and (numerical or observation):
        return "mixed_variation"
    if numerical:
        return "numerical_sensitivity"
    if physical:
        return (
            "controlled_physical_variation"
            if len(physical) == 1
            else "multi_factor_physical_variation"
        )
    if observation:
        return "observation_only_attempt"
    return "replicate_realization"


def _mountain_recipe_id(record: MountainWavesSimulationRecord) -> str | None:
    if record.recipe_id:
        return record.recipe_id
    if record.simulation_id == "mountain_waves_dry_ridge":
        return "dry_ridge_mechanics"
    if record.simulation_id == "mountain_waves_boulder_moist_reference":
        return "boulder_moist_wave"
    return None


def _mountain_difference_label(path: str) -> str:
    labels = {
        "scientific_design.controls.ridge_height_m": "Ridge height",
        "scientific_design.controls.ridge_half_width_m": "Ridge half-width",
        "scientific_design.controls.low_level_wind_m_s": "0–4 km mean wind",
        "scientific_design.controls.shear_through_10km_m_s": "0–10 km shear",
        "scientific_design.controls.lower_layer_rh_percent": "0–4 km mean RH",
        "scientific_design.controls.midlevel_rh_percent": "4–10 km mean RH",
        "scientific_design.controls.dry_air_counterpart": "Boulder dry-air counterpart",
        "scientific_design.controls.lower_stability_factor": "Lower-layer stability",
        "scientific_design.controls.midlevel_stability_factor": "Midlevel stability",
        "scientific_design.controls.upper_stability_factor": "Upper-layer stability",
        "observation_plan.output_cadence_seconds": "Saved-output cadence",
        "observation_plan.duration_seconds": "Simulation duration",
        "observation_plan.expected_history_count": "Expected saved outputs",
    }
    return labels.get(path, path.replace(".", " / ").replace("_", " ").title())


def _mountain_difference_units(path: str) -> str | None:
    if path.endswith(("_wind_m_s", "shear_through_10km_m_s")):
        return "m/s"
    if path.endswith("_rh_percent"):
        return "%"
    if path.endswith("_m"):
        return "m"
    if path.endswith("_seconds"):
        return "s"
    return None


def _flatten_mapping(value: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, Mapping):
            flattened.update(_flatten_mapping(item, path))
        else:
            flattened[path] = item
    return flattened


def _difference_label(path: str) -> str:
    labels = {
        "duration_seconds": "Simulation duration",
        "output_cadence_seconds": "Saved-output cadence",
        "domain.nx": "Grid cells along x",
        "domain.ny": "Grid cells along y",
        "domain.nz": "Grid cells along z",
        "domain.dx_m": "Grid spacing along x",
        "domain.dy_m": "Grid spacing along y",
        "domain.dz_m": "Grid spacing along z",
        "domain.active_model_top_m": "Active model top",
        "domain.active_top_m": "Active model top",
        "atmosphere.moisture_state": "Atmosphere moisture state",
        "terrain.height_m": "Terrain height",
        "terrain.half_width_m": "Terrain half-width",
        "terrain.center_m": "Terrain center",
        "terrain.native_dx_m": "Terrain native grid spacing",
        "terrain.type": "Terrain function",
        "terrain.itern": "CM1 terrain option",
        "terrain.terrain_flag": "Terrain enabled",
    }
    return labels.get(path, path.replace(".", " / ").replace("_", " ").title())


def _difference_category(
    path: str,
) -> Literal["atmospheric", "numerical", "output", "operational", "metadata"]:
    if path.startswith("domain.") or path.startswith("terrain."):
        return "numerical"
    if "cadence" in path or "duration" in path:
        return "output"
    return "atmospheric"


def _difference_units(path: str) -> str | None:
    if path.endswith("_seconds"):
        return "s"
    if path.endswith("_m"):
        return "m"
    return None


def _number(value: Any, fallback: float) -> float:
    return float(value) if isinstance(value, (int, float)) else fallback
