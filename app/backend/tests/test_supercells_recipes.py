from __future__ import annotations

import math

import pytest

from cloud_chamber.run_cost import profile_by_id
from cloud_chamber.supercells_recipes import (
    HYDROSTATIC_RESIDUAL_TOLERANCE_PA,
    ResolvedSupercellsRecipe,
    SupercellsControls,
    _hydrostatic_readback_residual_pa,
    default_controls,
    normalize_controls,
    resolve_supercells_recipe,
)


def _resolve(
    controls: SupercellsControls,
    *,
    profile_id: str = "supercells_standard_v1",
    parent: SupercellsControls | None = None,
) -> ResolvedSupercellsRecipe:
    return resolve_supercells_recipe(
        controls=controls,
        parent_controls=parent or default_controls(),
        catalog_profile=profile_by_id(profile_id),
    )


def test_default_recipe_closes_every_requested_direct_target() -> None:
    controls = default_controls()
    resolved = _resolve(controls)

    assert resolved.blocking_errors == []
    assert resolved.differences == []
    assert resolved.achieved_controls["hodograph_family"] == "quarter_circle"
    assert resolved.achieved_controls["shear_0_6_km_m_s"] == pytest.approx(
        controls.shear_0_6_km_m_s,
        abs=0.02,
    )
    assert resolved.achieved_controls["shear_0_2_km_m_s"] == pytest.approx(
        controls.shear_0_2_km_m_s,
        abs=0.02,
    )
    assert resolved.achieved_controls["mean_wind_0_6_km_speed_m_s"] == pytest.approx(
        controls.mean_wind_0_6_km_speed_m_s,
        abs=0.02,
    )
    assert resolved.diagnostics.achieved_cape_j_kg == pytest.approx(2_200.0, abs=0.5)
    assert resolved.diagnostics.achieved_cin_j_kg == pytest.approx(25.0, abs=0.5)
    assert resolved.diagnostics.achieved_lcl_height_m_agl == pytest.approx(
        1_000.0,
        abs=1.0,
    )
    assert resolved.diagnostics.achieved_midlevel_rh_percent == pytest.approx(
        45.0,
        abs=0.05,
    )
    assert resolved.diagnostics.hydrostatic_residual_pa < 1.0e-6
    assert resolved.diagnostics.freezing_level_m_agl is not None


def test_default_thermodynamics_reproduce_stock_cm1_isnd5_readback() -> None:
    resolved = _resolve(
        default_controls().model_copy(update={"thermal_perturbation_amplitude_k": 2.0})
    )
    by_height = {level.height_m: level for level in resolved.sounding}
    expected = {
        0.0: (100_000.0, 300.0, 300.0, 14.0),
        1_000.0: (
            89_181.1929147654,
            301.9252711278505,
            292.2178927614537,
            14.0,
        ),
        6_000.0: (
            47_963.419131632654,
            318.0792729279549,
            257.9068802001032,
            1.6739880712349995,
        ),
        12_000.0: (
            20_205.91074385263,
            343.0,
            217.3044072302913,
            0.024474914259117155,
        ),
        20_000.0: (
            5_771.953670365771,
            494.7699393265583,
            219.21413815501373,
            0.10800094252237333,
        ),
    }

    for height, values in expected.items():
        level = by_height[height]
        assert (
            level.pressure_pa,
            level.theta_k,
            level.temperature_k,
            level.qv_g_kg,
        ) == pytest.approx(values, rel=0.0, abs=1.0e-9)
    assert resolved.diagnostics.hydrostatic_residual_pa == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("family", "expected_label"),
    [
        ("straight", "Straight"),
        ("quarter_circle", "Quarter Circle"),
        ("half_circle", "Half Circle"),
    ],
)
def test_all_authored_hodograph_families_are_finite_and_distinct(
    family: str,
    expected_label: str,
) -> None:
    controls = default_controls().model_copy(update={"hodograph_family": family})
    resolved = _resolve(controls)

    assert all(
        math.isfinite(component)
        for level in resolved.hodograph
        for component in (level.height_m, level.u_m_s, level.v_m_s)
    )
    assert resolved.diagnostics.labels[0] == expected_label
    assert resolved.achieved_controls["shear_0_6_km_m_s"] == pytest.approx(
        controls.shear_0_6_km_m_s,
        abs=0.02,
    )
    if family == "half_circle":
        assert any("characterization" in error for error in resolved.blocking_errors)
    else:
        assert not resolved.blocking_errors


def test_default_quarter_circle_reproduces_canonical_deep_layer_vector() -> None:
    resolved = _resolve(default_controls())
    by_height = {round(level.height_m): level for level in resolved.hodograph}
    surface = by_height[0]
    two = by_height[2_000]
    six = by_height[6_000]

    assert (two.u_m_s - surface.u_m_s, two.v_m_s - surface.v_m_s) == pytest.approx(
        (7.0, 7.0),
        abs=0.02,
    )
    assert (six.u_m_s - surface.u_m_s, six.v_m_s - surface.v_m_s) == pytest.approx(
        (31.0, 7.0),
        abs=0.02,
    )


def test_turning_depth_changes_the_authored_arc_beyond_two_km() -> None:
    shallow = _resolve(default_controls().model_copy(update={"turning_depth_km_agl": 2.0}))
    deep = _resolve(default_controls().model_copy(update={"turning_depth_km_agl": 6.0}))
    shallow_three = next(level for level in shallow.hodograph if level.height_m == 3_000)
    deep_three = next(level for level in deep.hodograph if level.height_m == 3_000)

    assert (deep_three.u_m_s, deep_three.v_m_s) != pytest.approx(
        (shallow_three.u_m_s, shallow_three.v_m_s),
        abs=0.1,
    )
    assert deep.achieved_controls["shear_0_6_km_m_s"] == pytest.approx(
        default_controls().shear_0_6_km_m_s,
        abs=0.02,
    )
    extended_turn = _resolve(default_controls().model_copy(update={"turning_depth_km_agl": 8.0}))
    deep_seven = next(level for level in deep.hodograph if level.height_m == 7_000)
    extended_seven = next(level for level in extended_turn.hodograph if level.height_m == 7_000)
    assert (extended_seven.u_m_s, extended_seven.v_m_s) != pytest.approx(
        (deep_seven.u_m_s, deep_seven.v_m_s),
        abs=0.1,
    )


def test_broad_wind_targets_preserve_mean_and_vector_shear() -> None:
    controls = default_controls().model_copy(
        update={
            "hodograph_family": "half_circle",
            "shear_0_6_km_m_s": 80.0,
            "shear_0_2_km_m_s": 50.0,
            "turning_depth_km_agl": 8.0,
            "shear_6_12_km_m_s": 50.0,
            "upper_shear_direction_relative_deg": -180.0,
            "mean_wind_0_6_km_speed_m_s": 50.0,
            "mean_wind_0_6_km_direction_deg": 359.0,
        }
    )
    resolved = _resolve(controls)

    assert not [error for error in resolved.blocking_errors if "attainable" in error]
    for key in (
        "shear_0_6_km_m_s",
        "shear_0_2_km_m_s",
        "shear_6_12_km_m_s",
        "mean_wind_0_6_km_speed_m_s",
    ):
        assert resolved.achieved_controls[key] == pytest.approx(
            getattr(controls, key),
            abs=0.02,
        )
    assert resolved.achieved_controls["upper_shear_direction_relative_deg"] == pytest.approx(
        -180.0, abs=0.1
    )
    assert resolved.achieved_controls["mean_wind_0_6_km_direction_deg"] == pytest.approx(
        359.0, abs=0.1
    )


def test_zero_mean_wind_removes_inactive_direction_identity() -> None:
    baseline = default_controls()
    controls = baseline.model_copy(
        update={
            "mean_wind_0_6_km_speed_m_s": 0.0,
            "mean_wind_0_6_km_direction_deg": 275.0,
        }
    )

    normalized = normalize_controls(controls, reference=baseline)
    resolved = _resolve(normalized)

    assert normalized.mean_wind_0_6_km_direction_deg == (baseline.mean_wind_0_6_km_direction_deg)
    assert resolved.achieved_controls["mean_wind_0_6_km_speed_m_s"] == pytest.approx(
        0.0,
        abs=0.02,
    )


@pytest.mark.parametrize(
    "updates",
    [
        {
            "surface_based_cape_j_kg": 0.0,
            "lcl_height_m_agl": 4_000.0,
            "midlevel_rh_percent": 0.0,
            "cin_j_kg": 500.0,
        },
        {
            "surface_based_cape_j_kg": 8_000.0,
            "lcl_height_m_agl": 100.0,
            "midlevel_rh_percent": 100.0,
            "cin_j_kg": 0.0,
        },
    ],
)
def test_broad_thermodynamic_edges_close_without_silent_clipping(
    updates: dict[str, float],
) -> None:
    controls = default_controls().model_copy(update=updates)
    resolved = _resolve(controls)

    assert not [error for error in resolved.blocking_errors if "attainable" in error]
    assert resolved.achieved_controls["surface_based_cape_j_kg"] == pytest.approx(
        updates["surface_based_cape_j_kg"],
        abs=0.5,
    )
    assert resolved.achieved_controls["lcl_height_m_agl"] == pytest.approx(
        updates["lcl_height_m_agl"],
        abs=1.0,
    )
    assert resolved.achieved_controls["midlevel_rh_percent"] == pytest.approx(
        updates["midlevel_rh_percent"],
        abs=0.05,
    )
    assert resolved.achieved_controls["cin_j_kg"] == pytest.approx(
        updates["cin_j_kg"],
        abs=0.5,
    )
    assert all(
        math.isfinite(value)
        for level in resolved.sounding
        for value in (
            level.pressure_pa,
            level.theta_k,
            level.temperature_k,
            level.qv_g_kg,
            level.parcel_buoyancy_m_s2,
        )
    )


def test_weak_or_failed_initiation_is_warned_not_blocked() -> None:
    controls = default_controls().model_copy(
        update={
            "surface_based_cape_j_kg": 0.0,
            "cin_j_kg": 500.0,
            "thermal_perturbation_amplitude_k": -3.0,
        }
    )
    resolved = _resolve(controls)

    assert resolved.blocking_errors == []
    assert any("valid likely outcome" in warning for warning in resolved.warnings)
    assert any("cold perturbation" in warning.lower() for warning in resolved.warnings)


def test_thermal_geometry_requires_horizontal_and_vertical_clearance() -> None:
    controls = default_controls().model_copy(
        update={
            "thermal_horizontal_radius_km": 40.0,
            "thermal_center_x_km": 60.0,
            "thermal_vertical_radius_km": 10.0,
            "thermal_center_height_km_agl": 8.0,
        }
    )
    resolved = _resolve(controls)

    assert any("horizontal domain" in error for error in resolved.blocking_errors)
    assert any("damping base" in error for error in resolved.blocking_errors)
    assert resolved.diagnostics.minimum_boundary_clearance_km < 0.0
    assert resolved.diagnostics.minimum_vertical_clearance_km < 0.0


def test_exact_profile_contracts_resolve_and_extended_remains_characterization_blocked() -> None:
    controls = default_controls()

    for profile_id in (
        "supercells_quick_v1",
        "supercells_standard_v1",
        "supercells_presentation_v1",
    ):
        resolved = _resolve(controls, profile_id=profile_id)
        assert resolved.resolved_cost_profile.numerical_realization.exact_domain is not None
        assert not resolved.blocking_errors

    extended = _resolve(controls, profile_id="supercells_extended_v1")
    assert any("uncharacterized" in error for error in extended.blocking_errors)


def test_differences_are_direct_absolute_values_against_selected_parent() -> None:
    parent = default_controls().model_copy(update={"surface_based_cape_j_kg": 3_000.0})
    child = parent.model_copy(
        update={
            "shear_0_2_km_m_s": 20.0,
            "thermal_perturbation_amplitude_k": 2.5,
        }
    )
    resolved = _resolve(child, parent=parent)

    assert {difference.path for difference in resolved.differences} == {
        "controls.shear_0_2_km_m_s",
        "controls.thermal_perturbation_amplitude_k",
    }
    assert next(
        difference
        for difference in resolved.differences
        if difference.path.endswith("shear_0_2_km_m_s")
    ).before == pytest.approx(parent.shear_0_2_km_m_s)


def test_hydrostatic_readback_is_independent_of_profile_generation() -> None:
    resolved = _resolve(default_controls())
    perturbed = list(resolved.sounding)
    perturbed[10] = perturbed[10].model_copy(
        update={"pressure_pa": perturbed[10].pressure_pa + 1.0}
    )

    assert _hydrostatic_readback_residual_pa(perturbed) > HYDROSTATIC_RESIDUAL_TOLERANCE_PA
