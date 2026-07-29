from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

import pytest

from cloud_chamber.cloud_worlds import (
    ConfigurationDifference,
    SimulationRecord,
)
from cloud_chamber.mountain_wave_terrain_visualization import (
    _ordered_sample_indices,
    _sample_native_grid,
)
from cloud_chamber.mountain_waves_world import MountainWavesSimulationRecord
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.supercells_world import SupercellSimulationRecord
from cloud_chamber.world_compare import world_compare_descriptor


def _settings(tmp_path: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=tmp_path,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "cache",
        log_dir=tmp_path / "logs",
    )


def _trade_record(
    *,
    simulation_id: str,
    display_name: str,
    role: Literal["reference", "variation", "lab_history"],
    run_id: str,
    parent_simulation_id: str | None = None,
    difference: ConfigurationDifference | None = None,
) -> SimulationRecord:
    return SimulationRecord(
        simulation_id=simulation_id,
        display_name=display_name,
        role=role,
        product_slice_id="trade_cumulus_v1",
        case_id="bomex_trade_cumulus_baseline_v0",
        result_id=f"result-{run_id}",
        run_id=run_id,
        parent_simulation_id=parent_simulation_id,
        reference_simulation_id="trade_cumulus_canonical_bomex",
        technical_state="available",
        technical_state_message="Available",
        technical_trust_state="caveated",
        explore_available=True,
        configuration_difference_from_reference=[difference] if difference else None,
        lineage_state="known",
    )


def _mountain_record(
    *,
    simulation_id: str,
    display_name: str,
    run_id: str,
    moist: bool,
    configuration: dict[str, object],
) -> MountainWavesSimulationRecord:
    domain = configuration.get("domain")
    terrain = configuration.get("terrain")
    scientific_controls = {
        "moisture_state": "moist" if moist else "dry",
        **(terrain if isinstance(terrain, dict) else {}),
    }
    return MountainWavesSimulationRecord(
        simulation_id=simulation_id,
        display_name=display_name,
        role="built_in",
        run_id=run_id,
        case_id=f"{simulation_id}_case",
        state="available",
        state_message="Available",
        inspectable=True,
        can_create_variation=moist,
        recipe_id="boulder_moist_wave" if moist else "dry_ridge_mechanics",
        moist=moist,
        moist_fields_available=moist,
        purpose="Test retained output.",
        configuration=configuration,
        scientific_design={"controls": scientific_controls},
        numerical_realization={
            "domain": domain if isinstance(domain, dict) else {},
        },
        observation_plan={
            key: configuration[key]
            for key in ("duration_seconds", "output_cadence_seconds")
            if key in configuration
        },
    )


def test_trade_compare_uses_the_approved_pair_and_exact_material_difference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    difference = ConfigurationDifference(
        path="surface_moisture_flux_g_g_m_s",
        label="Surface moisture supply",
        category="atmospheric",
        left_value=0.052,
        right_value=0.078,
        units="g/kg m/s",
        material=True,
    )
    baseline = _trade_record(
        simulation_id="trade_cumulus_canonical_bomex",
        display_name="Canonical BOMEX Baseline",
        role="reference",
        run_id="baseline",
    )
    moisture = _trade_record(
        simulation_id="trade_cumulus_more_moisture",
        display_name="More Moisture",
        role="variation",
        run_id="moisture",
        parent_simulation_id=baseline.simulation_id,
        difference=difference,
    )
    monkeypatch.setattr(
        "cloud_chamber.world_compare.trade_cumulus_world_detail",
        lambda _settings: SimpleNamespace(
            display_name="Trade Cumulus",
            simulations=[baseline, moisture],
            reference_simulation=baseline,
            featured_comparison=SimpleNamespace(more_moisture_simulation_id=moisture.simulation_id),
        ),
    )

    descriptor = world_compare_descriptor(_settings(tmp_path), world_slug="trade-cumulus")

    assert descriptor.persistence == "transient_only"
    assert descriptor.selected_left_simulation_id == baseline.simulation_id
    assert descriptor.selected_right_simulation_id == moisture.simulation_id
    assert descriptor.compatibility is not None
    assert descriptor.compatibility.controlled_pair is True
    assert (
        descriptor.compatibility.relationship
        == "More Moisture is a child of Canonical BOMEX Baseline."
    )
    assert descriptor.compatibility.shared_view_ids == ["field", "updraft_lens"]
    assert descriptor.compatibility.physical_plane_link_available is True
    assert len(descriptor.material_differences) == 1
    material_difference = descriptor.material_differences[0]
    assert material_difference.path == difference.path
    assert material_difference.left_value == 0.052
    assert material_difference.right_value == 0.078
    assert material_difference.units == "g/kg m/s"
    assert all(
        simulation.initial_state.world_id == "trade_cumulus"
        for simulation in descriptor.simulations
    )


def test_mountain_compare_is_structural_and_keeps_unknown_distinct_from_equal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dry = _mountain_record(
        simulation_id="mountain_waves_dry_ridge",
        display_name="Dry Ridge",
        run_id="dry",
        moist=False,
        configuration={
            "duration_seconds": 2_160,
            "output_cadence_seconds": 120,
            "domain": {
                "nx": 800,
                "ny": 1,
                "nz": 100,
                "dx_m": 100,
                "dy_m": 100,
                "dz_m": 200,
                "active_model_top_m": 20_000,
            },
            "terrain": {"height_m": 1_500},
        },
    )
    moist = _mountain_record(
        simulation_id="mountain_waves_boulder_moist_reference",
        display_name="Boulder Windstorm",
        run_id="moist",
        moist=True,
        configuration={
            "duration_seconds": 7_200,
            "output_cadence_seconds": 200,
            "domain": {
                "nx": 800,
                "ny": 1,
                "nz": 126,
                "dx_m": 100,
                "dy_m": 100,
                "dz_m": 200,
                "active_model_top_m": 25_200,
            },
            "terrain": {"half_width_m": 10_000},
        },
    )
    monkeypatch.setattr(
        "cloud_chamber.world_compare.mountain_waves_world_detail",
        lambda _settings: SimpleNamespace(
            display_name="Mountain Waves",
            simulations=[dry, moist],
        ),
    )

    descriptor = world_compare_descriptor(_settings(tmp_path), world_slug="mountain-waves")

    assert descriptor.compatibility is not None
    assert descriptor.compatibility.controlled_pair is False
    assert descriptor.compatibility.relationship.startswith("Different Recipes:")
    assert descriptor.compatibility.camera_link_available is False
    assert descriptor.compatibility.physical_plane_link_available is False
    assert descriptor.compatibility.shared_view_ids == ["field", "wave_structure"]
    assert "different Mountain Waves Recipes" in (descriptor.compatibility.controlled_pair_message)
    moisture_row = next(
        item
        for item in descriptor.material_differences
        if item.path == "scientific_design.controls.moisture_state"
    )
    assert (moisture_row.left_value, moisture_row.right_value) == ("dry", "moist")
    missing_height = next(
        item
        for item in descriptor.material_differences
        if item.path == "scientific_design.controls.height_m"
    )
    assert missing_height.left_known is True
    assert missing_height.right_known is False
    assert missing_height.right_value is None
    assert all(simulation.grid.topology == "native_2d_xz" for simulation in descriptor.simulations)
    dry_descriptor = next(
        simulation
        for simulation in descriptor.simulations
        if simulation.simulation_id == "mountain_waves_dry_ridge"
    )
    assert dry_descriptor.reference_simulation_id is None
    assert dry_descriptor.lineage_state == "independent_built_in"


def test_mountain_compare_consumes_shared_envelope_relationship_and_differences(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = _mountain_record(
        simulation_id="mountain_waves_boulder_moist_reference",
        display_name="Boulder Windstorm",
        run_id="moist",
        moist=True,
        configuration={},
    )
    child = MountainWavesSimulationRecord(
        simulation_id="mountain_waves_broader_boulder",
        display_name="Broader Boulder Ridge",
        role="variation",
        run_id="broader",
        case_id="mountain_waves_recipe_variation_v1",
        parent_simulation_id=parent.simulation_id,
        reference_simulation_id=parent.simulation_id,
        recipe_id="boulder_moist_wave",
        recipe_contract_version="1",
        relationship_classification="controlled_physical_variation",
        state="available",
        state_message="Available",
        inspectable=True,
        can_create_variation=True,
        moist=True,
        moist_fields_available=True,
        purpose="Test retained variation.",
        differences={
            "terrain": [
                {
                    "path": "terrain.ridge_half_width_m",
                    "label": "Ridge half-width",
                    "before": 10_000,
                    "after": 11_000,
                    "units": "m",
                    "material": True,
                }
            ]
        },
    )
    monkeypatch.setattr(
        "cloud_chamber.world_compare.mountain_waves_world_detail",
        lambda _settings: SimpleNamespace(
            display_name="Mountain Waves",
            simulations=[parent, child],
        ),
    )

    descriptor = world_compare_descriptor(
        _settings(tmp_path),
        world_slug="mountain-waves",
        left_simulation_id=parent.simulation_id,
        right_simulation_id=child.simulation_id,
    )

    assert descriptor.compatibility is not None
    assert descriptor.compatibility.controlled_pair is True
    assert "controlled physical variation" in descriptor.compatibility.relationship
    assert len(descriptor.material_differences) == 1
    row = descriptor.material_differences[0]
    assert row.path == "terrain.ridge_half_width_m"
    assert (row.left_value, row.right_value, row.units) == (10_000, 11_000, "m")


def test_mountain_compare_uses_absolute_layers_for_sibling_variations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    common: dict[str, Any] = {
        "role": "variation",
        "case_id": "mountain_waves_recipe_variation_v1",
        "parent_simulation_id": "mountain_waves_boulder_moist_reference",
        "reference_simulation_id": "mountain_waves_boulder_moist_reference",
        "recipe_id": "boulder_moist_wave",
        "recipe_contract_version": "1",
        "state": "available",
        "state_message": "Available",
        "inspectable": True,
        "can_create_variation": True,
        "moist": True,
        "moist_fields_available": True,
        "purpose": "Sibling comparison fixture.",
        "numerical_realization": {"grid": "220 × 1 × 125"},
        "observation_plan": {
            "duration_seconds": 7_200,
            "output_cadence_seconds": 120,
        },
        "configuration": {
            "duration_seconds": 7_200,
            "output_cadence_seconds": 120,
            "domain": {
                "nx": 220,
                "ny": 1,
                "nz": 125,
                "dx_m": 1_000,
                "dy_m": 1_000,
                "dz_m": 200,
                "active_model_top_m": 25_000,
            },
        },
    }
    narrower = MountainWavesSimulationRecord(
        simulation_id="mountain_waves_narrower",
        display_name="Narrower",
        run_id="narrower",
        scientific_design={"controls": {"ridge_half_width_m": 8_000.0}},
        **common,
    )
    broader = MountainWavesSimulationRecord(
        simulation_id="mountain_waves_broader",
        display_name="Broader",
        run_id="broader",
        scientific_design={"controls": {"ridge_half_width_m": 14_000.0}},
        **common,
    )
    monkeypatch.setattr(
        "cloud_chamber.world_compare.mountain_waves_world_detail",
        lambda _settings: SimpleNamespace(
            display_name="Mountain Waves",
            simulations=[narrower, broader],
        ),
    )

    descriptor = world_compare_descriptor(
        _settings(tmp_path),
        world_slug="mountain-waves",
        left_simulation_id=narrower.simulation_id,
        right_simulation_id=broader.simulation_id,
    )

    assert descriptor.compatibility is not None
    assert descriptor.compatibility.controlled_pair is True
    assert "normalized absolute layers" in descriptor.compatibility.relationship
    assert len(descriptor.material_differences) == 1
    difference = descriptor.material_differences[0]
    assert difference.path == "scientific_design.controls.ridge_half_width_m"
    assert (difference.left_value, difference.right_value, difference.units) == (
        8_000.0,
        14_000.0,
        "m",
    )


def test_supercells_compare_does_not_clone_the_only_simulation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reference = SupercellSimulationRecord(
        simulation_id="supercells_quarter_circle_reference",
        display_name="Quarter-Circle Supercell",
        role="reference",
        run_id="quarter-circle",
        case_id="quarter-circle-case",
        technical_state="available",
        technical_state_message="Available",
        explore_available=True,
        saved_output_count=91,
        model_start_seconds=0,
        model_end_seconds=10_800,
        history_cadence_seconds=120,
    )
    monkeypatch.setattr(
        "cloud_chamber.world_compare.supercells_world_detail",
        lambda _settings: SimpleNamespace(
            display_name="Supercells",
            simulations=[reference],
            reference_simulation=reference,
        ),
    )

    descriptor = world_compare_descriptor(_settings(tmp_path), world_slug="supercells")

    assert descriptor.selected_left_simulation_id == reference.simulation_id
    assert descriptor.selected_right_simulation_id is None
    assert descriptor.compatibility is None
    assert descriptor.no_second_simulation_message is not None
    assert "not cloned" in descriptor.no_second_simulation_message
    assert len(descriptor.simulations) == 1
    assert descriptor.simulations[0].grid.nx == 240
    assert descriptor.simulations[0].grid.z_extent_km == (0.0, 20.0)


def test_supercells_compare_uses_real_controlled_hodograph_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reference = SupercellSimulationRecord(
        simulation_id="supercells_quarter_circle_reference",
        display_name="Quarter-Circle Supercell",
        role="reference",
        run_id="quarter-circle",
        case_id="quarter-circle-case",
        technical_state="available",
        technical_state_message="Available",
        explore_available=True,
        saved_output_count=91,
        model_start_seconds=0,
        model_end_seconds=10_800,
        history_cadence_seconds=120,
    )
    straight = SupercellSimulationRecord(
        simulation_id="supercells_straight_line_hodograph",
        display_name="Straight-Line Hodograph Supercell",
        role="variation",
        run_id="straight-line",
        case_id="straight-line-case",
        parent_simulation_id=reference.simulation_id,
        technical_state="available",
        technical_state_message="Available",
        explore_available=True,
        saved_output_count=91,
        model_start_seconds=0,
        model_end_seconds=10_800,
        history_cadence_seconds=120,
    )
    monkeypatch.setattr(
        "cloud_chamber.world_compare.supercells_world_detail",
        lambda _settings: SimpleNamespace(
            display_name="Supercells",
            simulations=[reference, straight],
            reference_simulation=reference,
        ),
    )

    descriptor = world_compare_descriptor(_settings(tmp_path), world_slug="supercells")

    assert descriptor.selected_left_simulation_id == reference.simulation_id
    assert descriptor.selected_right_simulation_id == straight.simulation_id
    assert descriptor.compatibility is not None
    assert descriptor.compatibility.controlled_pair is True
    assert descriptor.compatibility.camera_link_available is True
    assert descriptor.compatibility.physical_plane_link_available is True
    assert descriptor.compatibility.selection_link_available is True
    assert descriptor.compatibility.shared_view_ids == [
        "cloud_precipitation",
        "low_level_interactions",
        "rotating_updraft",
    ]
    assert len(descriptor.material_differences) == 1
    difference = descriptor.material_differences[0]
    assert difference.path == "atmosphere.hodograph_geometry"
    assert (difference.left_value, difference.right_value) == (
        "Quarter circle",
        "Straight line",
    )
    assert "without claiming storm-object lineage" in (
        descriptor.compatibility.controlled_pair_message
    )


def test_native_subset_is_bounded_ordered_and_never_interpolated() -> None:
    grid = [[float(row * 100 + column) for column in range(300)] for row in range(180)]
    rows = _ordered_sample_indices(180, 80)
    columns = _ordered_sample_indices(300, 120)
    sampled = _sample_native_grid(grid, rows, columns)

    assert len(rows) == 80
    assert len(columns) == 120
    assert rows == sorted(set(rows))
    assert columns == sorted(set(columns))
    assert sampled[17][31] == grid[rows[17]][columns[31]]
    assert all(
        value in grid[row] for row, values in zip(rows, sampled, strict=True) for value in values
    )


def test_compare_rejects_unknown_world_and_same_simulation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match="Unknown Cloud World"):
        world_compare_descriptor(_settings(tmp_path), world_slug="not-a-world")

    baseline = _trade_record(
        simulation_id="trade_cumulus_canonical_bomex",
        display_name="Canonical BOMEX Baseline",
        role="reference",
        run_id="baseline",
    )
    moisture = _trade_record(
        simulation_id="trade_cumulus_more_moisture",
        display_name="More Moisture",
        role="variation",
        run_id="moisture",
        parent_simulation_id=baseline.simulation_id,
    )
    monkeypatch.setattr(
        "cloud_chamber.world_compare.trade_cumulus_world_detail",
        lambda _settings: SimpleNamespace(
            display_name="Trade Cumulus",
            simulations=[baseline, moisture],
            reference_simulation=baseline,
            featured_comparison=SimpleNamespace(more_moisture_simulation_id=moisture.simulation_id),
        ),
    )

    with pytest.raises(ValueError, match="two distinct Simulations"):
        world_compare_descriptor(
            _settings(tmp_path),
            world_slug="trade-cumulus",
            left_simulation_id=baseline.simulation_id,
            right_simulation_id=baseline.simulation_id,
        )
