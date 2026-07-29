from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from cloud_chamber.run_cost import profile_by_id
from cloud_chamber.trade_cumulus_recipes import (
    RECIPE_ID,
    TARGET_TOLERANCE,
    ResolvedTradeCumulusRecipe,
    TradeCumulusControls,
    default_controls,
    normalize_controls,
    resolve_trade_cumulus_recipe,
)


def _resolve(
    controls: TradeCumulusControls,
    *,
    parent: TradeCumulusControls | None = None,
    profile_id: str = "trade_cumulus_standard_v1",
) -> ResolvedTradeCumulusRecipe:
    return resolve_trade_cumulus_recipe(
        controls=controls,
        parent_controls=parent or default_controls(),
        catalog_profile=profile_by_id(profile_id),
    )


def test_reference_recipe_resolves_exact_direct_targets() -> None:
    controls = default_controls()

    resolved = _resolve(controls)

    assert resolved.recipe_id == RECIPE_ID
    assert resolved.blocking_errors == []
    assert resolved.warnings == []
    for field, requested in controls.model_dump(mode="json").items():
        assert resolved.achieved_controls[field] == pytest.approx(
            requested,
            abs=0.1 if field.endswith("_deg") else TARGET_TOLERANCE,
        )
    assert resolved.differences == []
    assert resolved.diagnostics.inversion_top_m_agl == pytest.approx(1_480)
    assert resolved.observation_plan.expected_history_count == 121


@pytest.mark.parametrize(
    ("field", "minimum", "maximum"),
    [
        ("surface_sensible_heat_flux_k_m_s", -0.020, 0.050),
        ("surface_moisture_flux_g_kg_m_s", -0.10, 0.25),
        ("sub_inversion_total_water_g_kg", 0.0, 25.0),
        ("inversion_base_m_agl", 300.0, 2_800.0),
        ("inversion_thickness_m", 50.0, 2_000.0),
        ("inversion_strength_k", -5.0, 20.0),
        ("free_tropospheric_rh_percent", 0.0, 100.0),
        ("cloud_layer_shear_m_s", 0.0, 50.0),
        ("cloud_layer_shear_direction_deg", 0.0, 360.0),
        ("large_scale_vertical_motion_m_s", -0.050, 0.050),
        ("temperature_tendency_k_day", -20.0, 10.0),
        ("total_water_tendency_g_kg_day", -20.0, 10.0),
    ],
)
def test_direct_control_envelopes_accept_named_bounds(
    field: str,
    minimum: float,
    maximum: float,
) -> None:
    baseline = default_controls().model_dump(mode="json")

    TradeCumulusControls.model_validate({**baseline, field: minimum})
    TradeCumulusControls.model_validate({**baseline, field: maximum})
    with pytest.raises(ValidationError):
        TradeCumulusControls.model_validate({**baseline, field: math.nextafter(minimum, -math.inf)})
    with pytest.raises(ValidationError):
        TradeCumulusControls.model_validate({**baseline, field: math.nextafter(maximum, math.inf)})


def test_unusual_atmosphere_and_reversed_forcing_warn_without_science_block() -> None:
    controls = TradeCumulusControls(
        surface_sensible_heat_flux_k_m_s=-0.01,
        surface_moisture_flux_g_kg_m_s=-0.05,
        sub_inversion_total_water_g_kg=18.0,
        inversion_base_m_agl=500.0,
        inversion_thickness_m=700.0,
        inversion_strength_k=-2.0,
        free_tropospheric_rh_percent=98.0,
        cloud_layer_shear_m_s=35.0,
        cloud_layer_shear_direction_deg=225.0,
        large_scale_vertical_motion_m_s=0.02,
        temperature_tendency_k_day=4.0,
        total_water_tendency_g_kg_day=5.0,
    )

    resolved = _resolve(controls)

    assert resolved.blocking_errors == []
    assert len(resolved.warnings) == 8
    assert "Static instability possible" in resolved.diagnostics.labels
    assert "Initial saturation present" in resolved.diagnostics.labels
    assert "Large-scale ascent" in resolved.diagnostics.labels
    assert resolved.achieved_controls["cloud_layer_shear_m_s"] == pytest.approx(35.0)
    assert resolved.achieved_controls["cloud_layer_shear_direction_deg"] == pytest.approx(225.0)


def test_profile_top_blocks_an_unattainable_inversion_without_clipping() -> None:
    controls = default_controls().model_copy(
        update={
            "inversion_base_m_agl": 2_500.0,
            "inversion_thickness_m": 1_000.0,
        }
    )

    resolved = _resolve(controls)

    assert any("selected run profile ends at 3,000 m" in item for item in resolved.blocking_errors)
    assert resolved.controls["inversion_base_m_agl"] == 2_500.0
    assert resolved.controls["inversion_thickness_m"] == 1_000.0
    assert resolved.diagnostics.inversion_top_m_agl == 3_500.0
    assert any("contains no valid sampling layer" in item for item in resolved.blocking_errors)


def test_zero_shear_direction_is_canonicalized_without_hidden_state() -> None:
    controls = default_controls().model_copy(
        update={
            "cloud_layer_shear_m_s": 0.0,
            "cloud_layer_shear_direction_deg": 240.0,
        }
    )

    normalized = normalize_controls(controls)
    resolved = _resolve(controls)

    assert normalized.cloud_layer_shear_direction_deg == 0.0
    assert resolved.achieved_controls["cloud_layer_shear_m_s"] == pytest.approx(0.0)
    assert resolved.achieved_controls["cloud_layer_shear_direction_deg"] == pytest.approx(0.0)


def test_lineage_differences_compare_child_to_parent_not_reference() -> None:
    parent = default_controls().model_copy(update={"surface_moisture_flux_g_kg_m_s": 0.078})
    child = parent.model_copy(
        update={
            "surface_moisture_flux_g_kg_m_s": 0.090,
            "temperature_tendency_k_day": -3.0,
        }
    )

    resolved = _resolve(child, parent=parent)

    differences = {difference.path: difference for difference in resolved.differences}
    moisture = differences["controls.surface_moisture_flux_g_kg_m_s"]
    assert moisture.before == pytest.approx(0.078)
    assert moisture.after == pytest.approx(0.090)
    assert moisture.units == "g kg^-1 m s^-1"
    assert "controls.temperature_tendency_k_day" in differences
    assert "controls.surface_sensible_heat_flux_k_m_s" not in differences


def test_all_profiles_use_the_approved_recipe_and_field_inventory() -> None:
    expected = {
        "trade_cumulus_quick_v1": (10_800, 180, 61),
        "trade_cumulus_standard_v1": (14_400, 120, 121),
        "trade_cumulus_full_cycle_v1": (21_600, 120, 181),
        "trade_cumulus_presentation_v1": (14_400, 60, 241),
        "trade_cumulus_extended_v1": (14_400, 120, 121),
    }

    for profile_id, contract in expected.items():
        profile = profile_by_id(profile_id)
        resolved = _resolve(default_controls(), profile_id=profile_id)
        plan = resolved.observation_plan
        assert profile.recipe_id == RECIPE_ID
        assert (
            plan.duration_seconds,
            plan.output_cadence_seconds,
            plan.expected_history_count,
        ) == contract
        assert {"ql", "qv", "th", "prs", "u", "v", "w", "hfx", "qfx"}.issubset(
            plan.retained_field_inventory
        )

    assert any(
        "uncharacterized" in item
        for item in _resolve(
            default_controls(), profile_id="trade_cumulus_extended_v1"
        ).blocking_errors
    )
