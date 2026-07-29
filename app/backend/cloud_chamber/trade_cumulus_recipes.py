"""Approved Trade Cumulus Recipe controls and deterministic profile generator."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.run_cost import ObservationPlan, RunCostProfile
from cloud_chamber.variation_envelope import VariationDifference

RECIPE_ID: Literal["canonical_bomex_trade_cumulus"] = "canonical_bomex_trade_cumulus"
RECIPE_NAME = "Canonical BOMEX Trade Cumulus"
RECIPE_CONTRACT_VERSION: Literal["1"] = "1"
RUN_COST_RECIPE_VERSION = "approved_variation_contract_v1"

SURFACE_PRESSURE_PA = 101_500.0
SURFACE_THETA_K = 298.7
REFERENCE_LAYER_MEAN_U_M_S = -7.50
REFERENCE_LAYER_MEAN_V_M_S = 0.0
REFERENCE_SUB_INVERSION_QT_G_KG = 16.65
REFERENCE_FREE_TROPOSPHERIC_RH_PERCENT = 41.0
TARGET_TOLERANCE = 0.02


class TradeCumulusControls(BaseModel):
    """Direct physical values approved by the #448 PM correction."""

    model_config = ConfigDict(extra="forbid")

    surface_sensible_heat_flux_k_m_s: float = Field(default=0.008, ge=-0.020, le=0.050)
    surface_moisture_flux_g_kg_m_s: float = Field(default=0.052, ge=-0.10, le=0.25)
    sub_inversion_total_water_g_kg: float = Field(
        default=REFERENCE_SUB_INVERSION_QT_G_KG, ge=0.0, le=25.0
    )
    inversion_base_m_agl: float = Field(default=520.0, ge=300.0, le=4_000.0)
    inversion_thickness_m: float = Field(default=960.0, ge=50.0, le=2_000.0)
    inversion_strength_k: float = Field(default=3.7, ge=-5.0, le=20.0)
    free_tropospheric_rh_percent: float = Field(
        default=REFERENCE_FREE_TROPOSPHERIC_RH_PERCENT, ge=0.0, le=100.0
    )
    cloud_layer_shear_m_s: float = Field(default=4.14, ge=0.0, le=50.0)
    cloud_layer_shear_direction_deg: float = Field(default=0.0, ge=0.0, le=360.0)
    cloud_layer_mean_u_m_s: float = Field(default=REFERENCE_LAYER_MEAN_U_M_S, ge=-50.0, le=50.0)
    cloud_layer_mean_v_m_s: float = Field(default=REFERENCE_LAYER_MEAN_V_M_S, ge=-50.0, le=50.0)
    large_scale_vertical_motion_m_s: float = Field(default=-0.0065, ge=-0.050, le=0.050)
    temperature_tendency_k_day: float = Field(default=-2.0, ge=-20.0, le=10.0)
    total_water_tendency_g_kg_day: float = Field(default=-1.0368, ge=-20.0, le=10.0)


class TradeCumulusProfileLevel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    height_m: float
    pressure_pa: float
    theta_l_k: float
    total_water_g_kg: float
    relative_humidity_percent: float
    u_m_s: float
    v_m_s: float


class TradeCumulusForcingLevel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    height_m: float
    vertical_motion_m_s: float
    temperature_tendency_k_day: float
    total_water_tendency_g_kg_day: float


class TradeCumulusDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inversion_top_m_agl: float
    model_top_m: float
    sub_inversion_total_water_g_kg: float
    free_tropospheric_rh_percent: float
    cloud_layer_shear_m_s: float
    cloud_layer_shear_direction_deg: float
    cloud_layer_mean_u_m_s: float
    cloud_layer_mean_v_m_s: float
    initial_saturated_level_count: int
    minimum_theta_gradient_k_km: float
    surface_heat_to_moisture_ratio_k_per_g_kg: float | None
    labels: list[str]


class ResolvedTradeCumulusRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: Literal["canonical_bomex_trade_cumulus"] = RECIPE_ID
    recipe_name: str = RECIPE_NAME
    controls: dict[str, float]
    achieved_controls: dict[str, float]
    sounding: list[TradeCumulusProfileLevel]
    forcing_profile: list[TradeCumulusForcingLevel]
    observation_plan: ObservationPlan
    resolved_cost_profile: RunCostProfile
    differences: list[VariationDifference]
    warnings: list[str]
    blocking_errors: list[str]
    diagnostics: TradeCumulusDiagnostics


def default_controls() -> TradeCumulusControls:
    return TradeCumulusControls()


def normalize_controls(
    controls: TradeCumulusControls,
    *,
    reference: TradeCumulusControls | None = None,
) -> TradeCumulusControls:
    """Remove inactive direction state when the shear magnitude is zero."""
    baseline = reference or default_controls()
    payload = controls.model_dump(mode="json")
    if controls.cloud_layer_shear_m_s == 0.0:
        payload["cloud_layer_shear_direction_deg"] = baseline.cloud_layer_shear_direction_deg
    elif controls.cloud_layer_shear_direction_deg == 360.0:
        payload["cloud_layer_shear_direction_deg"] = 0.0
    return TradeCumulusControls.model_validate(payload)


def resolve_trade_cumulus_recipe(
    *,
    controls: TradeCumulusControls,
    parent_controls: TradeCumulusControls,
    catalog_profile: RunCostProfile,
) -> ResolvedTradeCumulusRecipe:
    if catalog_profile.world_id != "trade_cumulus" or catalog_profile.recipe_id != RECIPE_ID:
        raise ValueError("Selected run profile does not belong to Trade Cumulus.")
    effective = normalize_controls(controls)
    parent = normalize_controls(parent_controls)
    model_top_m = _model_top(catalog_profile)
    inversion_top = effective.inversion_base_m_agl + effective.inversion_thickness_m
    errors: list[str] = []
    warnings = _scientific_warnings(effective)
    if inversion_top >= model_top_m - 100.0:
        errors.append(
            f"The requested inversion top is {inversion_top:,.0f} m AGL, but the selected "
            f"run profile ends at {model_top_m:,.0f} m. Choose a lower inversion or a "
            "numerical profile with a taller domain."
        )
    if catalog_profile.estimate_basis == "uncharacterized":
        errors.append(
            "The selected run profile remains uncharacterized and cannot be packaged "
            "without a bounded characterization decision."
        )

    sounding = _generate_sounding(effective, model_top_m)
    forcing = _generate_forcing(effective, model_top_m)
    achieved = _achieved_controls(effective, sounding, forcing)
    errors.extend(_target_errors(effective, achieved))
    minimum_gradient = _minimum_theta_gradient(sounding)
    saturated_count = sum(
        level.relative_humidity_percent >= 100.0 - TARGET_TOLERANCE for level in sounding
    )
    labels: list[str] = []
    if minimum_gradient < 0.0:
        labels.append("Static instability possible")
    if saturated_count:
        labels.append("Initial saturation present")
    if effective.cloud_layer_shear_m_s >= 30.0:
        labels.append("Strong cloud-layer shear")
    if effective.large_scale_vertical_motion_m_s > 0.0:
        labels.append("Large-scale ascent")
    elif effective.large_scale_vertical_motion_m_s < 0.0:
        labels.append("Large-scale subsidence")
    else:
        labels.append("No large-scale vertical motion")

    return ResolvedTradeCumulusRecipe(
        controls=effective.model_dump(mode="json"),
        achieved_controls=achieved,
        sounding=sounding,
        forcing_profile=forcing,
        observation_plan=catalog_profile.observation_plan,
        resolved_cost_profile=catalog_profile,
        differences=_control_differences(achieved, _achieved_parent(parent, model_top_m)),
        warnings=warnings,
        blocking_errors=errors,
        diagnostics=TradeCumulusDiagnostics(
            inversion_top_m_agl=inversion_top,
            model_top_m=model_top_m,
            sub_inversion_total_water_g_kg=achieved["sub_inversion_total_water_g_kg"],
            free_tropospheric_rh_percent=achieved["free_tropospheric_rh_percent"],
            cloud_layer_shear_m_s=achieved["cloud_layer_shear_m_s"],
            cloud_layer_shear_direction_deg=achieved["cloud_layer_shear_direction_deg"],
            cloud_layer_mean_u_m_s=achieved["cloud_layer_mean_u_m_s"],
            cloud_layer_mean_v_m_s=achieved["cloud_layer_mean_v_m_s"],
            initial_saturated_level_count=saturated_count,
            minimum_theta_gradient_k_km=minimum_gradient,
            surface_heat_to_moisture_ratio_k_per_g_kg=(
                effective.surface_sensible_heat_flux_k_m_s
                / effective.surface_moisture_flux_g_kg_m_s
                if not math.isclose(
                    effective.surface_moisture_flux_g_kg_m_s,
                    0.0,
                    abs_tol=1.0e-12,
                )
                else None
            ),
            labels=labels,
        ),
    )


def _generate_sounding(
    controls: TradeCumulusControls,
    model_top_m: float,
) -> list[TradeCumulusProfileLevel]:
    heights = _profile_heights(model_top_m, controls.inversion_base_m_agl)
    inversion_top = controls.inversion_base_m_agl + controls.inversion_thickness_m
    heights = sorted({*heights, inversion_top})
    shear_radians = math.radians(controls.cloud_layer_shear_direction_deg)
    delta_u = controls.cloud_layer_shear_m_s * math.cos(shear_radians)
    delta_v = controls.cloud_layer_shear_m_s * math.sin(shear_radians)
    u0 = controls.cloud_layer_mean_u_m_s - delta_u / 2.0
    v0 = controls.cloud_layer_mean_v_m_s - delta_v / 2.0
    pressure = SURFACE_PRESSURE_PA
    previous_height = 0.0
    output: list[TradeCumulusProfileLevel] = []
    raw_sub_water: list[tuple[float, float]] = []
    for height in heights:
        if height <= controls.inversion_base_m_agl:
            fraction = height / max(controls.inversion_base_m_agl, 1.0)
            raw_sub_water.append((height, 1.0 - 0.0412 * fraction))
    raw_mean = _layer_mean(raw_sub_water, 0.0, controls.inversion_base_m_agl)
    sub_scale = controls.sub_inversion_total_water_g_kg / max(raw_mean, 1.0e-12)

    for height in heights:
        theta = _theta_at(height, controls)
        if output:
            previous_theta = output[-1].theta_l_k
            mean_theta = 0.5 * (previous_theta + theta)
            mean_temperature = mean_theta * (pressure / 100_000.0) ** (287.05 / 1004.0)
            pressure *= math.exp(
                -9.80665 * (height - previous_height) / max(287.05 * mean_temperature, 1.0)
            )
        temperature = theta * (pressure / 100_000.0) ** (287.05 / 1004.0)
        saturation = _saturation_mixing_ratio_g_kg(pressure, temperature)
        if height <= controls.inversion_base_m_agl:
            fraction = height / max(controls.inversion_base_m_agl, 1.0)
            total_water = sub_scale * (1.0 - 0.0412 * fraction)
        elif height < inversion_top:
            base_value = sub_scale * (1.0 - 0.0412)
            target_value = controls.free_tropospheric_rh_percent / 100.0 * saturation
            fraction = (height - controls.inversion_base_m_agl) / max(
                controls.inversion_thickness_m, 1.0
            )
            total_water = base_value + (target_value - base_value) * fraction
        else:
            total_water = controls.free_tropospheric_rh_percent / 100.0 * saturation
        rh = 0.0 if saturation <= 0.0 else 100.0 * total_water / saturation
        shear_fraction = min(max(height / 3_000.0, 0.0), 1.0)
        output.append(
            TradeCumulusProfileLevel(
                height_m=height,
                pressure_pa=pressure,
                theta_l_k=theta,
                total_water_g_kg=max(0.0, total_water),
                relative_humidity_percent=max(0.0, rh),
                u_m_s=u0 + delta_u * shear_fraction,
                v_m_s=v0 + delta_v * shear_fraction,
            )
        )
        previous_height = height
    return output


def _generate_forcing(
    controls: TradeCumulusControls,
    model_top_m: float,
) -> list[TradeCumulusForcingLevel]:
    output: list[TradeCumulusForcingLevel] = []
    for height in _profile_heights(model_top_m, controls.inversion_base_m_agl):
        if height <= 1_500.0:
            w_factor = height / 1_500.0
            temperature_factor = 1.0
        elif height <= 2_100.0:
            w_factor = 1.0 - (height - 1_500.0) / 600.0
            temperature_factor = w_factor
        else:
            w_factor = 0.0
            temperature_factor = 0.0
        if height <= 300.0:
            moisture_factor = 1.0
        elif height <= 500.0:
            moisture_factor = 1.0 - (height - 300.0) / 200.0
        else:
            moisture_factor = 0.0
        output.append(
            TradeCumulusForcingLevel(
                height_m=height,
                vertical_motion_m_s=controls.large_scale_vertical_motion_m_s * w_factor,
                temperature_tendency_k_day=(
                    controls.temperature_tendency_k_day * temperature_factor
                ),
                total_water_tendency_g_kg_day=(
                    controls.total_water_tendency_g_kg_day * moisture_factor
                ),
            )
        )
    return output


def _achieved_parent(
    controls: TradeCumulusControls,
    model_top_m: float,
) -> dict[str, float]:
    sounding = _generate_sounding(controls, model_top_m)
    forcing = _generate_forcing(controls, model_top_m)
    return _achieved_controls(controls, sounding, forcing)


def _achieved_controls(
    controls: TradeCumulusControls,
    sounding: list[TradeCumulusProfileLevel],
    forcing: list[TradeCumulusForcingLevel],
) -> dict[str, float]:
    inversion_top = controls.inversion_base_m_agl + controls.inversion_thickness_m
    sub_water = [(level.height_m, level.total_water_g_kg) for level in sounding]
    free_rh = [(level.height_m, level.relative_humidity_percent) for level in sounding]
    lower = _interpolated_level(sounding, 0.0)
    upper = _interpolated_level(sounding, 3_000.0)
    delta_u = upper.u_m_s - lower.u_m_s
    delta_v = upper.v_m_s - lower.v_m_s
    shear = math.hypot(delta_u, delta_v)
    direction = 0.0 if shear < 1.0e-9 else math.degrees(math.atan2(delta_v, delta_u)) % 360.0
    winds_u = [(level.height_m, level.u_m_s) for level in sounding]
    winds_v = [(level.height_m, level.v_m_s) for level in sounding]
    return {
        "surface_sensible_heat_flux_k_m_s": controls.surface_sensible_heat_flux_k_m_s,
        "surface_moisture_flux_g_kg_m_s": controls.surface_moisture_flux_g_kg_m_s,
        "sub_inversion_total_water_g_kg": _layer_mean(
            sub_water, 0.0, controls.inversion_base_m_agl
        ),
        "inversion_base_m_agl": controls.inversion_base_m_agl,
        "inversion_thickness_m": controls.inversion_thickness_m,
        "inversion_strength_k": (
            _interpolated_level(sounding, inversion_top).theta_l_k
            - _interpolated_level(sounding, controls.inversion_base_m_agl).theta_l_k
        ),
        "free_tropospheric_rh_percent": _layer_mean(
            free_rh, inversion_top, min(3_000.0, sounding[-1].height_m)
        ),
        "cloud_layer_shear_m_s": shear,
        "cloud_layer_shear_direction_deg": direction,
        "cloud_layer_mean_u_m_s": _layer_mean(winds_u, 0.0, 3_000.0),
        "cloud_layer_mean_v_m_s": _layer_mean(winds_v, 0.0, 3_000.0),
        "large_scale_vertical_motion_m_s": _signed_extreme(
            [level.vertical_motion_m_s for level in forcing]
        ),
        "temperature_tendency_k_day": _signed_extreme(
            [level.temperature_tendency_k_day for level in forcing]
        ),
        "total_water_tendency_g_kg_day": _signed_extreme(
            [level.total_water_tendency_g_kg_day for level in forcing]
        ),
    }


def _target_errors(
    requested: TradeCumulusControls,
    achieved: dict[str, float],
) -> list[str]:
    errors: list[str] = []
    for key, target in requested.model_dump(mode="json").items():
        actual = achieved[key]
        if not math.isfinite(actual):
            errors.append(
                f"{_label(key)} target {target:g} is not attainable because the selected "
                "profile contains no valid sampling layer."
            )
            continue
        tolerance = (
            0.05 if key.endswith("_percent") else 0.1 if key.endswith("_deg") else TARGET_TOLERANCE
        )
        difference = (
            abs(((actual - target + 180.0) % 360.0) - 180.0)
            if key.endswith("_deg")
            else abs(actual - target)
        )
        if difference > tolerance:
            errors.append(
                f"{_label(key)} target {target:g} is not attainable; generated value is "
                f"{actual:g} (tolerance {tolerance:g})."
            )
    return errors


def _control_differences(
    after: dict[str, float],
    before: dict[str, float],
) -> list[VariationDifference]:
    differences: list[VariationDifference] = []
    for key, metadata in _DIFFERENCE_METADATA.items():
        if math.isclose(after[key], before[key], rel_tol=0.0, abs_tol=1.0e-6):
            continue
        category, label, units = metadata
        differences.append(
            VariationDifference(
                category=category,
                path=f"controls.{key}",
                label=label,
                before=before[key],
                after=after[key],
                units=units,
            )
        )
    return differences


def _scientific_warnings(controls: TradeCumulusControls) -> list[str]:
    warnings: list[str] = []
    if controls.surface_sensible_heat_flux_k_m_s < 0.0:
        warnings.append("Surface sensible heat flux is downward.")
    if controls.surface_moisture_flux_g_kg_m_s < 0.0:
        warnings.append("Surface moisture flux is downward.")
    if controls.inversion_strength_k < 0.0:
        warnings.append(
            "The requested liquid-water-potential-temperature jump reverses the inversion; "
            "static instability may dominate the result."
        )
    if controls.free_tropospheric_rh_percent >= 95.0:
        warnings.append("The authored free troposphere is near saturation.")
    if controls.cloud_layer_shear_m_s >= 30.0:
        warnings.append("Cloud-layer shear is much stronger than the canonical BOMEX reference.")
    if controls.large_scale_vertical_motion_m_s > 0.0:
        warnings.append("The canonical large-scale subsidence profile is reversed to ascent.")
    if controls.temperature_tendency_k_day > 0.0:
        warnings.append("The canonical radiative cooling profile is reversed to warming.")
    if controls.total_water_tendency_g_kg_day > 0.0:
        warnings.append("The canonical drying tendency is reversed to moistening.")
    return warnings


def _theta_at(height_m: float, controls: TradeCumulusControls) -> float:
    base = controls.inversion_base_m_agl
    top = base + controls.inversion_thickness_m
    if height_m <= base:
        return SURFACE_THETA_K
    if height_m <= top:
        return SURFACE_THETA_K + controls.inversion_strength_k * (height_m - base) / (top - base)
    return SURFACE_THETA_K + controls.inversion_strength_k + 0.0062 * (height_m - top)


def _profile_heights(model_top_m: float, inversion_base_m: float) -> list[float]:
    values = {float(index) for index in range(0, int(model_top_m) + 101, 100)}
    values.update(
        {
            inversion_base_m,
            min(model_top_m + 100.0, inversion_base_m + 50.0),
            300.0,
            500.0,
            1_500.0,
            2_100.0,
            3_000.0,
            model_top_m + 100.0,
        }
    )
    return sorted(value for value in values if 0.0 <= value <= model_top_m + 100.0)


def _model_top(profile: RunCostProfile) -> float:
    if profile.numerical_realization.exact_domain is not None:
        return profile.numerical_realization.exact_domain.model_top_m
    grid = profile.numerical_realization.grid.replace(" ", "").split("×")
    spacing = profile.numerical_realization.spacing.replace("about", "").strip().split("×")
    try:
        nz = float(grid[-1])
        dz = float(spacing[-1].strip().split()[0])
    except (IndexError, ValueError) as exc:
        raise ValueError("Trade Cumulus run profile has an invalid vertical realization.") from exc
    return nz * dz


def _saturation_mixing_ratio_g_kg(pressure_pa: float, temperature_k: float) -> float:
    temperature_c = temperature_k - 273.15
    vapor_pressure = 611.2 * math.exp(17.67 * temperature_c / (temperature_c + 243.5))
    vapor_pressure = min(vapor_pressure, 0.99 * pressure_pa)
    return 1_000.0 * 0.622 * vapor_pressure / max(pressure_pa - vapor_pressure, 1.0)


def _interpolated_level(
    levels: list[TradeCumulusProfileLevel],
    height_m: float,
) -> TradeCumulusProfileLevel:
    if height_m <= levels[0].height_m:
        return levels[0]
    for lower, upper in zip(levels, levels[1:], strict=False):
        if lower.height_m <= height_m <= upper.height_m:
            if math.isclose(lower.height_m, upper.height_m):
                return lower
            fraction = (height_m - lower.height_m) / (upper.height_m - lower.height_m)
            values = {
                key: getattr(lower, key) + fraction * (getattr(upper, key) - getattr(lower, key))
                for key in (
                    "pressure_pa",
                    "theta_l_k",
                    "total_water_g_kg",
                    "relative_humidity_percent",
                    "u_m_s",
                    "v_m_s",
                )
            }
            return TradeCumulusProfileLevel(height_m=height_m, **values)
    return levels[-1]


def _layer_mean(points: list[tuple[float, float]], lower: float, upper: float) -> float:
    if upper <= lower:
        return math.nan
    ordered = sorted(points)
    clipped = [(lower, _interpolate_points(ordered, lower))]
    clipped.extend((height, value) for height, value in ordered if lower < height < upper)
    clipped.append((upper, _interpolate_points(ordered, upper)))
    integral = sum(
        0.5 * (left[1] + right[1]) * (right[0] - left[0])
        for left, right in zip(clipped, clipped[1:], strict=False)
    )
    return integral / (upper - lower)


def _interpolate_points(points: list[tuple[float, float]], height: float) -> float:
    if height <= points[0][0]:
        return points[0][1]
    for lower, upper in zip(points, points[1:], strict=False):
        if lower[0] <= height <= upper[0]:
            fraction = (height - lower[0]) / max(upper[0] - lower[0], 1.0e-12)
            return lower[1] + fraction * (upper[1] - lower[1])
    return points[-1][1]


def _signed_extreme(values: list[float]) -> float:
    return max(values, key=abs)


def _minimum_theta_gradient(levels: list[TradeCumulusProfileLevel]) -> float:
    gradients = [
        (upper.theta_l_k - lower.theta_l_k)
        / max(upper.height_m - lower.height_m, 1.0e-12)
        * 1_000.0
        for lower, upper in zip(levels, levels[1:], strict=False)
    ]
    return min(gradients)


def _label(key: str) -> str:
    return _DIFFERENCE_METADATA[key][1]


_DIFFERENCE_METADATA: dict[str, tuple[Any, str, str]] = {
    "surface_sensible_heat_flux_k_m_s": (
        "forcing_initiation",
        "Surface sensible heat flux",
        "K m s^-1",
    ),
    "surface_moisture_flux_g_kg_m_s": (
        "forcing_initiation",
        "Surface moisture flux",
        "g kg^-1 m s^-1",
    ),
    "sub_inversion_total_water_g_kg": (
        "moisture",
        "Sub-inversion total water",
        "g kg^-1",
    ),
    "inversion_base_m_agl": ("stability_thermodynamics", "Inversion base", "m AGL"),
    "inversion_thickness_m": ("stability_thermodynamics", "Inversion thickness", "m"),
    "inversion_strength_k": ("stability_thermodynamics", "Inversion strength", "K"),
    "free_tropospheric_rh_percent": (
        "moisture",
        "Free-tropospheric humidity",
        "%",
    ),
    "cloud_layer_shear_m_s": ("wind", "0-3 km vector shear", "m s^-1"),
    "cloud_layer_shear_direction_deg": ("wind", "Shear direction", "deg"),
    "cloud_layer_mean_u_m_s": ("wind", "0-3 km mean u wind", "m s^-1"),
    "cloud_layer_mean_v_m_s": ("wind", "0-3 km mean v wind", "m s^-1"),
    "large_scale_vertical_motion_m_s": (
        "forcing_initiation",
        "Large-scale vertical motion",
        "m s^-1",
    ),
    "temperature_tendency_k_day": (
        "forcing_initiation",
        "Temperature tendency",
        "K day^-1",
    ),
    "total_water_tendency_g_kg_day": (
        "forcing_initiation",
        "Total-water tendency",
        "g kg^-1 day^-1",
    ),
}
