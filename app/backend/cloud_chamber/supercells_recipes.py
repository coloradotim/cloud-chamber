"""Approved Supercells Recipe controls and deterministic environment generator."""

from __future__ import annotations

import math
from typing import Any, Literal, TypedDict

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field
from scipy.optimize import brentq  # type: ignore[import-untyped]

from cloud_chamber.run_cost import ObservationPlan, RunCostProfile
from cloud_chamber.variation_envelope import VariationDifference

RECIPE_ID: Literal["idealized_isolated_supercell"] = "idealized_isolated_supercell"
RECIPE_NAME = "Idealized Isolated Supercell"
RECIPE_CONTRACT_VERSION: Literal["1"] = "1"
RUN_COST_RECIPE_VERSION = "approved_variation_contract_v1"

REFERENCE_SHEAR_0_6_M_S = math.hypot(31.0, 7.0)
REFERENCE_SHEAR_0_2_M_S = math.hypot(7.0, 7.0)
REFERENCE_MEAN_U_M_S = 13.5145538645
REFERENCE_MEAN_V_M_S = 6.1521128022
REFERENCE_MEAN_SPEED_M_S = math.hypot(REFERENCE_MEAN_U_M_S, REFERENCE_MEAN_V_M_S)
REFERENCE_MEAN_DIRECTION_DEG = (
    math.degrees(math.atan2(REFERENCE_MEAN_V_M_S, REFERENCE_MEAN_U_M_S)) % 360.0
)

SURFACE_PRESSURE_PA = 100_000.0
SURFACE_TEMPERATURE_K = 300.0
MODEL_TOP_M = 20_000.0
DAMPING_BASE_M = 15_000.0
HYDROSTATIC_RESIDUAL_TOLERANCE_PA = 0.01
PROFILE_DZ_M = 250.0
GRAVITY_M_S2 = 9.80665
DRY_AIR_GAS_CONSTANT = 287.05
DRY_AIR_CP = 1004.0
WATER_VAPOR_EPSILON = 0.622
LATENT_HEAT_VAPORIZATION = 2.5e6

HodographFamily = Literal["straight", "quarter_circle", "half_circle"]
BuoyancyDistribution = Literal["low_level_weighted", "reference", "deep_weighted"]


class _ThermodynamicDiagnostics(TypedDict):
    cape_j_kg: float
    cin_j_kg: float
    lcl_height_m_agl: float
    midlevel_rh_percent: float
    freezing_level_m_agl: float | None
    hydrostatic_residual_pa: float
    translation_u_m_s: float
    translation_v_m_s: float


class SupercellsControls(BaseModel):
    """Direct physical targets approved by the #449 PM correction."""

    model_config = ConfigDict(extra="forbid")

    hodograph_family: HodographFamily = "quarter_circle"
    shear_0_6_km_m_s: float = Field(default=REFERENCE_SHEAR_0_6_M_S, ge=0.0, le=80.0)
    shear_0_2_km_m_s: float = Field(default=REFERENCE_SHEAR_0_2_M_S, ge=0.0, le=50.0)
    turning_depth_km_agl: float = Field(default=2.0, ge=0.25, le=8.0)
    shear_6_12_km_m_s: float = Field(default=0.0, ge=0.0, le=50.0)
    upper_shear_direction_relative_deg: float = Field(default=0.0, ge=-180.0, le=180.0)
    mean_wind_0_6_km_speed_m_s: float = Field(default=REFERENCE_MEAN_SPEED_M_S, ge=0.0, le=50.0)
    mean_wind_0_6_km_direction_deg: float = Field(
        default=REFERENCE_MEAN_DIRECTION_DEG, ge=0.0, le=360.0
    )
    surface_based_cape_j_kg: float = Field(default=2_200.0, ge=0.0, le=8_000.0)
    buoyancy_distribution: BuoyancyDistribution = "reference"
    lcl_height_m_agl: float = Field(default=1_000.0, ge=100.0, le=4_000.0)
    midlevel_rh_percent: float = Field(default=45.0, ge=0.0, le=100.0)
    cin_j_kg: float = Field(default=25.0, ge=0.0, le=500.0)
    thermal_perturbation_amplitude_k: float = Field(default=1.0, ge=-3.0, le=12.0)
    thermal_horizontal_radius_km: float = Field(default=10.0, ge=0.5, le=40.0)
    thermal_vertical_radius_km: float = Field(default=1.4, ge=0.25, le=10.0)
    thermal_center_height_km_agl: float = Field(default=1.4, ge=0.25, le=8.0)
    thermal_center_x_km: float = Field(default=0.0, ge=-60.0, le=60.0)
    thermal_center_y_km: float = Field(default=0.0, ge=-60.0, le=60.0)


class SupercellsProfileLevel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    height_m: float
    pressure_pa: float
    theta_k: float
    temperature_k: float
    qv_g_kg: float
    relative_humidity_percent: float
    parcel_temperature_k: float
    parcel_buoyancy_m_s2: float
    u_m_s: float
    v_m_s: float


class SupercellsHodographLevel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    height_m: float
    u_m_s: float
    v_m_s: float


class SupercellsDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    achieved_cape_j_kg: float
    achieved_cin_j_kg: float
    achieved_lcl_height_m_agl: float
    achieved_midlevel_rh_percent: float
    freezing_level_m_agl: float | None
    hydrostatic_residual_pa: float
    shear_0_1_km_m_s: float
    shear_0_2_km_m_s: float
    shear_0_3_km_m_s: float
    shear_0_6_km_m_s: float
    shear_6_12_km_m_s: float
    mean_wind_0_6_km_u_m_s: float
    mean_wind_0_6_km_v_m_s: float
    mean_wind_0_6_km_speed_m_s: float
    mean_wind_0_6_km_direction_deg: float
    storm_relative_helicity_0_1_km_m2_s2: float
    storm_relative_helicity_0_3_km_m2_s2: float
    model_translation_u_m_s: float
    model_translation_v_m_s: float
    minimum_boundary_clearance_km: float
    minimum_vertical_clearance_km: float
    labels: list[str]


class ResolvedSupercellsRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: Literal["idealized_isolated_supercell"] = RECIPE_ID
    recipe_name: str = RECIPE_NAME
    controls: dict[str, Any]
    achieved_controls: dict[str, Any]
    sounding: list[SupercellsProfileLevel]
    hodograph: list[SupercellsHodographLevel]
    initiation: dict[str, float]
    observation_plan: ObservationPlan
    resolved_cost_profile: RunCostProfile
    differences: list[VariationDifference]
    warnings: list[str]
    blocking_errors: list[str]
    diagnostics: SupercellsDiagnostics


def default_controls() -> SupercellsControls:
    return SupercellsControls()


def normalize_controls(
    controls: SupercellsControls,
    *,
    reference: SupercellsControls | None = None,
) -> SupercellsControls:
    baseline = reference or default_controls()
    payload = controls.model_dump(mode="json")
    if controls.shear_6_12_km_m_s == 0.0:
        payload["upper_shear_direction_relative_deg"] = baseline.upper_shear_direction_relative_deg
    if controls.mean_wind_0_6_km_speed_m_s == 0.0:
        payload["mean_wind_0_6_km_direction_deg"] = baseline.mean_wind_0_6_km_direction_deg
    if controls.mean_wind_0_6_km_direction_deg == 360.0:
        payload["mean_wind_0_6_km_direction_deg"] = 0.0
    return SupercellsControls.model_validate(payload)


def resolve_supercells_recipe(
    *,
    controls: SupercellsControls,
    parent_controls: SupercellsControls,
    catalog_profile: RunCostProfile,
) -> ResolvedSupercellsRecipe:
    if catalog_profile.world_id != "supercells" or catalog_profile.recipe_id != RECIPE_ID:
        raise ValueError("Selected run profile does not belong to Supercells.")
    numerical = catalog_profile.numerical_realization.exact_domain
    if numerical is None:
        raise ValueError("Supercells run profile lacks an exact numerical realization.")
    effective = normalize_controls(controls)
    parent = normalize_controls(parent_controls)
    heights = _profile_heights(numerical.model_top_m)
    raw_wind = _wind_profile(effective, heights)
    sounding, thermo = _thermodynamic_profile(effective, raw_wind, heights)
    achieved = _achieved_controls(effective, sounding, thermo)
    errors = _target_errors(effective, achieved)
    warnings = _scientific_warnings(effective)

    horizontal_radius_m = effective.thermal_horizontal_radius_km * 1_000.0
    vertical_radius_m = effective.thermal_vertical_radius_km * 1_000.0
    center_height_m = effective.thermal_center_height_km_agl * 1_000.0
    center_x_m = effective.thermal_center_x_km * 1_000.0
    center_y_m = effective.thermal_center_y_km * 1_000.0
    boundary_clearance_m = min(
        center_x_m - numerical.x_min_m - horizontal_radius_m,
        numerical.x_max_m - center_x_m - horizontal_radius_m,
        center_y_m - numerical.y_min_m - horizontal_radius_m,
        numerical.y_max_m - center_y_m - horizontal_radius_m,
    )
    vertical_clearance_m = min(
        center_height_m - vertical_radius_m,
        DAMPING_BASE_M - center_height_m - vertical_radius_m,
    )
    required_boundary_clearance_m = 2.0 * max(numerical.dx_m, numerical.dy_m)
    if boundary_clearance_m < required_boundary_clearance_m:
        errors.append(
            "The requested thermal does not fit inside the generated horizontal domain with "
            f"the required {required_boundary_clearance_m / 1_000.0:g} km grid clearance."
        )
    if vertical_clearance_m < 0.0:
        errors.append(
            "The requested thermal does not fit between the ground and the 15 km damping base."
        )
    if catalog_profile.estimate_basis == "uncharacterized":
        errors.append(
            "The selected run profile remains uncharacterized and cannot be launched without "
            "a bounded characterization decision."
        )
    if effective.hodograph_family == "half_circle":
        errors.append(
            "Half Circle requires bounded characterization and is not enabled for ordinary "
            "packaging or launch."
        )
    if thermo["hydrostatic_residual_pa"] > HYDROSTATIC_RESIDUAL_TOLERANCE_PA:
        errors.append(
            "The resolved sounding failed independent hydrostatic readback: "
            f"{thermo['hydrostatic_residual_pa']:.6f} Pa exceeds "
            f"{HYDROSTATIC_RESIDUAL_TOLERANCE_PA:.6f} Pa."
        )

    diagnostics = SupercellsDiagnostics(
        achieved_cape_j_kg=thermo["cape_j_kg"],
        achieved_cin_j_kg=thermo["cin_j_kg"],
        achieved_lcl_height_m_agl=thermo["lcl_height_m_agl"],
        achieved_midlevel_rh_percent=thermo["midlevel_rh_percent"],
        freezing_level_m_agl=thermo["freezing_level_m_agl"],
        hydrostatic_residual_pa=thermo["hydrostatic_residual_pa"],
        shear_0_1_km_m_s=_vector_shear(sounding, 0.0, 1_000.0),
        shear_0_2_km_m_s=_vector_shear(sounding, 0.0, 2_000.0),
        shear_0_3_km_m_s=_vector_shear(sounding, 0.0, 3_000.0),
        shear_0_6_km_m_s=_vector_shear(sounding, 0.0, 6_000.0),
        shear_6_12_km_m_s=_vector_shear(sounding, 6_000.0, 12_000.0),
        mean_wind_0_6_km_u_m_s=_layer_mean(
            [(level.height_m, level.u_m_s) for level in sounding], 0.0, 6_000.0
        ),
        mean_wind_0_6_km_v_m_s=_layer_mean(
            [(level.height_m, level.v_m_s) for level in sounding], 0.0, 6_000.0
        ),
        mean_wind_0_6_km_speed_m_s=effective.mean_wind_0_6_km_speed_m_s,
        mean_wind_0_6_km_direction_deg=(effective.mean_wind_0_6_km_direction_deg % 360.0),
        storm_relative_helicity_0_1_km_m2_s2=_storm_relative_helicity(sounding, 1_000.0),
        storm_relative_helicity_0_3_km_m2_s2=_storm_relative_helicity(sounding, 3_000.0),
        model_translation_u_m_s=thermo["translation_u_m_s"],
        model_translation_v_m_s=thermo["translation_v_m_s"],
        minimum_boundary_clearance_km=boundary_clearance_m / 1_000.0,
        minimum_vertical_clearance_km=vertical_clearance_m / 1_000.0,
        labels=_diagnostic_labels(effective),
    )
    return ResolvedSupercellsRecipe(
        controls=effective.model_dump(mode="json"),
        achieved_controls=achieved,
        sounding=sounding,
        hodograph=[
            SupercellsHodographLevel(
                height_m=level.height_m,
                u_m_s=level.u_m_s,
                v_m_s=level.v_m_s,
            )
            for level in sounding
        ],
        initiation={
            "amplitude_k": effective.thermal_perturbation_amplitude_k,
            "horizontal_radius_m": horizontal_radius_m,
            "vertical_radius_m": vertical_radius_m,
            "center_height_m_agl": center_height_m,
            "center_x_m": center_x_m,
            "center_y_m": center_y_m,
            "boundary_clearance_m": boundary_clearance_m,
            "vertical_clearance_m": vertical_clearance_m,
            "horizontal_radius_cells_x": horizontal_radius_m / numerical.dx_m,
            "horizontal_radius_cells_y": horizontal_radius_m / numerical.dy_m,
            "vertical_radius_cells": vertical_radius_m / numerical.dz_m,
        },
        observation_plan=catalog_profile.observation_plan,
        resolved_cost_profile=catalog_profile,
        differences=_control_differences(achieved, _achieved_parent(parent, heights)),
        warnings=warnings,
        blocking_errors=errors,
        diagnostics=diagnostics,
    )


def _wind_profile(
    controls: SupercellsControls,
    heights: list[float],
) -> list[tuple[float, float]]:
    deep_direction = math.atan2(7.0, 31.0)
    six_endpoint = controls.shear_0_6_km_m_s * np.array(
        [math.cos(deep_direction), math.sin(deep_direction)],
        dtype=float,
    )
    upper_angle = deep_direction + math.radians(controls.upper_shear_direction_relative_deg)
    twelve_endpoint = six_endpoint + np.array(
        [
            controls.shear_6_12_km_m_s * math.cos(upper_angle),
            controls.shear_6_12_km_m_s * math.sin(upper_angle),
        ],
        dtype=float,
    )
    turn_depth_m = controls.turning_depth_km_agl * 1_000.0
    low_endpoint = _curved_hodograph_point(
        controls,
        2_000.0,
        turn_depth_m=turn_depth_m,
        six_endpoint=six_endpoint,
        deep_direction=deep_direction,
    )
    turn_endpoint = _curved_hodograph_point(
        controls,
        turn_depth_m,
        turn_depth_m=turn_depth_m,
        six_endpoint=six_endpoint,
        deep_direction=deep_direction,
    )
    raw: list[np.ndarray] = []
    for height in heights:
        if height <= turn_depth_m:
            point = _curved_hodograph_point(
                controls,
                height,
                turn_depth_m=turn_depth_m,
                six_endpoint=six_endpoint,
                deep_direction=deep_direction,
            )
        elif turn_depth_m < 2_000.0 and height <= 2_000.0:
            point = low_endpoint
        elif height <= 6_000.0:
            anchor_height = max(turn_depth_m, 2_000.0)
            anchor = turn_endpoint if turn_depth_m >= 2_000.0 else low_endpoint
            fraction = (height - anchor_height) / (6_000.0 - anchor_height)
            point = anchor + fraction * (six_endpoint - anchor)
        elif height <= 12_000.0:
            anchor_height = max(turn_depth_m, 6_000.0)
            anchor = turn_endpoint if turn_depth_m > 6_000.0 else six_endpoint
            fraction = (height - anchor_height) / (12_000.0 - anchor_height)
            point = anchor + fraction * (twelve_endpoint - anchor)
        else:
            point = twelve_endpoint
        raw.append(point)

    mean_u = _layer_mean(list(zip(heights, [point[0] for point in raw], strict=True)), 0, 6_000)
    mean_v = _layer_mean(list(zip(heights, [point[1] for point in raw], strict=True)), 0, 6_000)
    direction = math.radians(controls.mean_wind_0_6_km_direction_deg % 360.0)
    target_mean = np.array(
        [
            controls.mean_wind_0_6_km_speed_m_s * math.cos(direction),
            controls.mean_wind_0_6_km_speed_m_s * math.sin(direction),
        ]
    )
    offset = target_mean - np.array([mean_u, mean_v])
    return [(float(point[0] + offset[0]), float(point[1] + offset[1])) for point in raw]


def _curved_hodograph_point(
    controls: SupercellsControls,
    height_m: float,
    *,
    turn_depth_m: float,
    six_endpoint: NDArray[np.float64],
    deep_direction: float,
) -> NDArray[np.float64]:
    if controls.hodograph_family == "straight":
        if height_m <= 2_000.0:
            return (
                height_m
                / 2_000.0
                * controls.shear_0_2_km_m_s
                * np.array([math.cos(deep_direction), math.sin(deep_direction)])
            )
        fraction = min((height_m - 2_000.0) / 4_000.0, 1.0)
        low = controls.shear_0_2_km_m_s * np.array(
            [math.cos(deep_direction), math.sin(deep_direction)]
        )
        return low + fraction * (six_endpoint - low)

    total_turn = {
        "quarter_circle": math.pi / 2.0,
        "half_circle": math.pi,
    }[controls.hodograph_family]
    bounded_height = min(max(height_m, 0.0), turn_depth_m)

    if turn_depth_m < 2_000.0:
        radius = controls.shear_0_2_km_m_s / max(2.0 * math.sin(total_turn / 2.0), 1.0e-12)
        initial_tangent = 0.0
        theta = total_turn * bounded_height / turn_depth_m
    elif turn_depth_m < 6_000.0:
        theta_at_two = total_turn * 2_000.0 / turn_depth_m
        radius = controls.shear_0_2_km_m_s / max(2.0 * math.sin(theta_at_two / 2.0), 1.0e-12)
        initial_tangent = 0.0
        theta = total_turn * bounded_height / turn_depth_m
    else:
        theta_at_six = total_turn * 6_000.0 / turn_depth_m
        radius = controls.shear_0_6_km_m_s / max(2.0 * math.sin(theta_at_six / 2.0), 1.0e-12)
        initial_tangent = deep_direction - theta_at_six / 2.0
        theta_at_two = 2.0 * math.asin(
            min(controls.shear_0_2_km_m_s / max(2.0 * radius, 1.0e-12), 1.0)
        )
        if bounded_height <= 2_000.0:
            theta = theta_at_two * bounded_height / 2_000.0
        elif bounded_height <= 6_000.0:
            theta = theta_at_two + (
                (theta_at_six - theta_at_two) * (bounded_height - 2_000.0) / 4_000.0
            )
        else:
            theta = theta_at_six + (
                (total_turn - theta_at_six)
                * (bounded_height - 6_000.0)
                / max(turn_depth_m - 6_000.0, 1.0)
            )

    center = radius * np.array(
        [-math.sin(initial_tangent), math.cos(initial_tangent)],
        dtype=np.float64,
    )
    radial_start = -center
    cosine = math.cos(theta)
    sine = math.sin(theta)
    rotated = np.array(
        [
            radial_start[0] * cosine - radial_start[1] * sine,
            radial_start[0] * sine + radial_start[1] * cosine,
        ],
        dtype=np.float64,
    )
    return center + rotated


def _thermodynamic_profile(
    controls: SupercellsControls,
    winds: list[tuple[float, float]],
    heights: list[float],
) -> tuple[list[SupercellsProfileLevel], _ThermodynamicDiagnostics]:
    z = np.asarray(heights, dtype=float)
    lcl_m = controls.lcl_height_m_agl
    cap_top_m = min(max(lcl_m + 750.0, 2_000.0), 5_000.0)
    cin_shape = np.where(
        (z > 0.0) & (z < cap_top_m),
        np.sin(math.pi * z / cap_top_m) ** 2,
        0.0,
    )
    cape_shape = _cape_shape(z, cap_top_m, controls.buoyancy_distribution)
    cin_buoyancy = _normalized_area_profile(z, cin_shape, -controls.cin_j_kg, negative=True)
    cape_buoyancy = _normalized_area_profile(
        z, cape_shape, controls.surface_based_cape_j_kg, negative=False
    )
    target_buoyancy = cin_buoyancy + cape_buoyancy

    surface_dewpoint_k = SURFACE_TEMPERATURE_K - lcl_m / 125.0
    surface_qv = _saturation_mixing_ratio(SURFACE_PRESSURE_PA, surface_dewpoint_k)
    parcel_temperature = _parcel_temperature_profile(z, lcl_m)
    pressure = np.empty_like(z)
    pressure[0] = SURFACE_PRESSURE_PA
    output: list[SupercellsProfileLevel] = []
    previous_virtual_temperature = SURFACE_TEMPERATURE_K * (1.0 + 0.61 * surface_qv)

    for index, height in enumerate(z):
        if index:
            dz = height - z[index - 1]
            pressure_estimate = pressure[index - 1] * math.exp(
                -GRAVITY_M_S2 * dz / max(DRY_AIR_GAS_CONSTANT * previous_virtual_temperature, 1.0)
            )
            for _iteration in range(20):
                state = _environment_level_state(
                    pressure_estimate,
                    height,
                    lcl_m=lcl_m,
                    surface_qv=surface_qv,
                    parcel_temperature_k=parcel_temperature[index],
                    target_buoyancy_m_s2=target_buoyancy[index],
                    midlevel_rh_percent=controls.midlevel_rh_percent,
                )
                updated_pressure = pressure[index - 1] * math.exp(
                    -GRAVITY_M_S2
                    * dz
                    / max(
                        DRY_AIR_GAS_CONSTANT
                        * 0.5
                        * (previous_virtual_temperature + state["virtual_temperature_k"]),
                        1.0,
                    )
                )
                if abs(updated_pressure - pressure_estimate) < 1.0e-8:
                    pressure_estimate = updated_pressure
                    break
                pressure_estimate = updated_pressure
            pressure[index] = pressure_estimate
        state = _environment_level_state(
            pressure[index],
            height,
            lcl_m=lcl_m,
            surface_qv=surface_qv,
            parcel_temperature_k=parcel_temperature[index],
            target_buoyancy_m_s2=target_buoyancy[index],
            midlevel_rh_percent=controls.midlevel_rh_percent,
        )
        rh_percent = state["relative_humidity_percent"]
        temperature = state["temperature_k"]
        qv = state["qv_kg_kg"]
        virtual_temperature = state["virtual_temperature_k"]
        theta = temperature * (100_000.0 / pressure[index]) ** (DRY_AIR_GAS_CONSTANT / DRY_AIR_CP)
        u_m_s, v_m_s = winds[index]
        output.append(
            SupercellsProfileLevel(
                height_m=float(height),
                pressure_pa=float(pressure[index]),
                theta_k=float(theta),
                temperature_k=float(temperature),
                qv_g_kg=float(qv * 1_000.0),
                relative_humidity_percent=float(rh_percent),
                parcel_temperature_k=float(parcel_temperature[index]),
                parcel_buoyancy_m_s2=float(target_buoyancy[index]),
                u_m_s=u_m_s,
                v_m_s=v_m_s,
            )
        )
        previous_virtual_temperature = virtual_temperature

    cape = float(np.trapezoid(np.maximum(target_buoyancy, 0.0), z))
    cin = float(-np.trapezoid(np.minimum(target_buoyancy, 0.0), z))
    freezing_level = _crossing_height(
        [(level.height_m, level.temperature_k - 273.15) for level in output], 0.0
    )
    mean_u = _layer_mean([(level.height_m, level.u_m_s) for level in output], 0, 6_000)
    mean_v = _layer_mean([(level.height_m, level.v_m_s) for level in output], 0, 6_000)
    diagnostics: _ThermodynamicDiagnostics = {
        "cape_j_kg": cape,
        "cin_j_kg": cin,
        "lcl_height_m_agl": _lcl_from_surface(output[0]),
        "midlevel_rh_percent": _layer_mean(
            [(level.height_m, level.relative_humidity_percent) for level in output],
            3_000.0,
            7_000.0,
        ),
        "freezing_level_m_agl": freezing_level,
        "hydrostatic_residual_pa": _hydrostatic_readback_residual_pa(output),
        "translation_u_m_s": mean_u,
        "translation_v_m_s": mean_v,
    }
    return output, diagnostics


def _environment_level_state(
    pressure_pa: float,
    height_m: float,
    *,
    lcl_m: float,
    surface_qv: float,
    parcel_temperature_k: float,
    target_buoyancy_m_s2: float,
    midlevel_rh_percent: float,
) -> dict[str, float]:
    parcel_qv = (
        surface_qv
        if height_m <= lcl_m
        else _saturation_mixing_ratio(pressure_pa, parcel_temperature_k)
    )
    parcel_virtual_temperature = parcel_temperature_k * (1.0 + 0.61 * parcel_qv)
    target_virtual_temperature = parcel_virtual_temperature / (
        1.0 + target_buoyancy_m_s2 / GRAVITY_M_S2
    )
    rh_percent = _environment_rh_percent(
        height_m,
        lcl_m=lcl_m,
        surface_rh_percent=100.0
        * surface_qv
        / max(
            _saturation_mixing_ratio(SURFACE_PRESSURE_PA, SURFACE_TEMPERATURE_K),
            1.0e-12,
        ),
        midlevel_rh_percent=midlevel_rh_percent,
    )
    temperature = _temperature_for_virtual_target(
        pressure_pa, target_virtual_temperature, rh_percent
    )
    qv = rh_percent / 100.0 * _saturation_mixing_ratio(pressure_pa, temperature)
    return {
        "relative_humidity_percent": rh_percent,
        "temperature_k": temperature,
        "qv_kg_kg": qv,
        "virtual_temperature_k": temperature * (1.0 + 0.61 * qv),
    }


def _hydrostatic_readback_residual_pa(
    sounding: list[SupercellsProfileLevel],
) -> float:
    residual = 0.0
    for lower, upper in zip(sounding, sounding[1:], strict=False):
        lower_virtual = lower.temperature_k * (1.0 + 0.61 * lower.qv_g_kg / 1_000.0)
        upper_virtual = upper.temperature_k * (1.0 + 0.61 * upper.qv_g_kg / 1_000.0)
        expected = lower.pressure_pa * math.exp(
            -GRAVITY_M_S2
            * (upper.height_m - lower.height_m)
            / (DRY_AIR_GAS_CONSTANT * max(0.5 * (lower_virtual + upper_virtual), 1.0))
        )
        residual = max(residual, abs(upper.pressure_pa - expected))
    return residual


def _achieved_parent(
    controls: SupercellsControls,
    heights: list[float],
) -> dict[str, Any]:
    normalized = normalize_controls(controls)
    winds = _wind_profile(normalized, heights)
    sounding, thermo = _thermodynamic_profile(normalized, winds, heights)
    return _achieved_controls(normalized, sounding, thermo)


def _achieved_controls(
    controls: SupercellsControls,
    sounding: list[SupercellsProfileLevel],
    thermo: _ThermodynamicDiagnostics,
) -> dict[str, Any]:
    low = _interpolated_level(sounding, 0.0)
    six = _interpolated_level(sounding, 6_000.0)
    twelve = _interpolated_level(sounding, 12_000.0)
    upper_du = twelve.u_m_s - six.u_m_s
    upper_dv = twelve.v_m_s - six.v_m_s
    shear06_du = six.u_m_s - low.u_m_s
    shear06_dv = six.v_m_s - low.v_m_s
    upper_relative = (
        0.0
        if math.hypot(upper_du, upper_dv) < 1.0e-9
        else _wrapped_direction_difference(
            math.degrees(math.atan2(upper_dv, upper_du)),
            math.degrees(math.atan2(shear06_dv, shear06_du)),
        )
    )
    mean_u = _layer_mean([(level.height_m, level.u_m_s) for level in sounding], 0, 6_000)
    mean_v = _layer_mean([(level.height_m, level.v_m_s) for level in sounding], 0, 6_000)
    return {
        "hodograph_family": controls.hodograph_family,
        "shear_0_6_km_m_s": _vector_shear(sounding, 0.0, 6_000.0),
        "shear_0_2_km_m_s": _vector_shear(sounding, 0.0, 2_000.0),
        "turning_depth_km_agl": controls.turning_depth_km_agl,
        "shear_6_12_km_m_s": math.hypot(upper_du, upper_dv),
        "upper_shear_direction_relative_deg": upper_relative,
        "mean_wind_0_6_km_speed_m_s": math.hypot(mean_u, mean_v),
        "mean_wind_0_6_km_direction_deg": (
            0.0
            if math.hypot(mean_u, mean_v) < 1.0e-9
            else math.degrees(math.atan2(mean_v, mean_u)) % 360.0
        ),
        "surface_based_cape_j_kg": thermo["cape_j_kg"],
        "buoyancy_distribution": controls.buoyancy_distribution,
        "lcl_height_m_agl": thermo["lcl_height_m_agl"],
        "midlevel_rh_percent": thermo["midlevel_rh_percent"],
        "cin_j_kg": thermo["cin_j_kg"],
        "thermal_perturbation_amplitude_k": controls.thermal_perturbation_amplitude_k,
        "thermal_horizontal_radius_km": controls.thermal_horizontal_radius_km,
        "thermal_vertical_radius_km": controls.thermal_vertical_radius_km,
        "thermal_center_height_km_agl": controls.thermal_center_height_km_agl,
        "thermal_center_x_km": controls.thermal_center_x_km,
        "thermal_center_y_km": controls.thermal_center_y_km,
    }


def _target_errors(
    requested: SupercellsControls,
    achieved: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for key, target in requested.model_dump(mode="json").items():
        actual = achieved[key]
        if isinstance(target, str):
            if actual != target:
                errors.append(f"{_label(key)} target {target} resolved as {actual}.")
            continue
        if not isinstance(actual, (float, int)) or not math.isfinite(float(actual)):
            errors.append(f"{_label(key)} target {target:g} did not produce a finite value.")
            continue
        tolerance = _TARGET_TOLERANCES.get(key, 0.02)
        is_direction = "direction" in key and key.endswith("_deg")
        difference = (
            abs(_wrapped_direction_difference(float(actual), float(target)))
            if is_direction
            else abs(float(actual) - float(target))
        )
        if difference > tolerance:
            errors.append(
                f"{_label(key)} target {target:g} is not attainable; generated value is "
                f"{actual:g} (tolerance {tolerance:g})."
            )
    return errors


def _control_differences(
    after: dict[str, Any],
    before: dict[str, Any],
) -> list[VariationDifference]:
    differences: list[VariationDifference] = []
    for key, metadata in _DIFFERENCE_METADATA.items():
        if isinstance(after[key], str):
            changed = after[key] != before[key]
        elif "direction" in key and key.endswith("_deg"):
            changed = (
                abs(_wrapped_direction_difference(float(after[key]), float(before[key]))) > 1.0e-6
            )
        else:
            changed = not math.isclose(
                float(after[key]), float(before[key]), rel_tol=0.0, abs_tol=1.0e-6
            )
        if not changed:
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


def _scientific_warnings(controls: SupercellsControls) -> list[str]:
    warnings: list[str] = []
    if controls.shear_0_2_km_m_s > controls.shear_0_6_km_m_s:
        warnings.append(
            "The 0-2 km vector change exceeds the 0-6 km endpoint shear; the generated "
            "hodograph reverses direction aloft."
        )
    if controls.shear_0_6_km_m_s >= 60.0:
        warnings.append(
            "Very strong deep-layer shear may favor rapid storm translation or splitting."
        )
    if controls.surface_based_cape_j_kg <= 250.0:
        warnings.append("Weak or absent sustained convection is a valid likely outcome.")
    if controls.cin_j_kg >= 250.0:
        warnings.append(
            "The cap may prevent the single deterministic thermal from initiating convection."
        )
    if controls.midlevel_rh_percent <= 15.0:
        warnings.append("Very dry midlevels may produce strong evaporation and outflow.")
    if controls.thermal_perturbation_amplitude_k <= 0.0:
        warnings.append("A neutral or cold perturbation may not initiate convection.")
    if controls.thermal_perturbation_amplitude_k >= 8.0:
        warnings.append(
            "The thermal perturbation is unusually strong and may dominate early evolution."
        )
    return warnings


def _diagnostic_labels(controls: SupercellsControls) -> list[str]:
    labels = [controls.hodograph_family.replace("_", " ").title()]
    labels.append("Low CAPE" if controls.surface_based_cape_j_kg < 1_000 else "Deep instability")
    labels.append("Strong cap" if controls.cin_j_kg >= 150 else "Weak to moderate cap")
    if controls.thermal_perturbation_amplitude_k < 0.0:
        labels.append("Cold perturbation")
    elif controls.thermal_perturbation_amplitude_k == 0.0:
        labels.append("No thermal perturbation")
    else:
        labels.append("Warm perturbation")
    return labels


def _cape_shape(
    height_m: np.ndarray,
    cap_top_m: float,
    family: BuoyancyDistribution,
) -> np.ndarray:
    top = 12_000.0
    fraction = np.clip((height_m - cap_top_m) / max(top - cap_top_m, 1.0), 0.0, 1.0)
    core = np.where(
        (height_m > cap_top_m) & (height_m < top),
        np.sin(math.pi * fraction) ** 2,
        0.0,
    )
    if family == "low_level_weighted":
        return core * (1.4 - 0.8 * fraction)
    if family == "deep_weighted":
        return core * (0.6 + 0.8 * fraction)
    return core


def _normalized_area_profile(
    height_m: np.ndarray,
    shape: np.ndarray,
    target_area: float,
    *,
    negative: bool,
) -> np.ndarray:
    area = float(np.trapezoid(shape, height_m))
    if target_area == 0.0 or area <= 0.0:
        return np.zeros_like(shape)
    amplitude = abs(target_area) / area
    return shape * (-amplitude if negative else amplitude)


def _parcel_temperature_profile(height_m: np.ndarray, lcl_m: float) -> np.ndarray:
    output = np.empty_like(height_m)
    lcl_temperature = SURFACE_TEMPERATURE_K - GRAVITY_M_S2 / DRY_AIR_CP * lcl_m
    for index, height in enumerate(height_m):
        if height <= lcl_m:
            output[index] = SURFACE_TEMPERATURE_K - GRAVITY_M_S2 / DRY_AIR_CP * height
        elif height <= 12_000.0:
            output[index] = lcl_temperature - 0.006 * (height - lcl_m)
        else:
            temperature_at_twelve = lcl_temperature - 0.006 * (12_000.0 - lcl_m)
            output[index] = temperature_at_twelve + 0.001 * (height - 12_000.0)
    return output


def _environment_rh_percent(
    height_m: float,
    *,
    lcl_m: float,
    surface_rh_percent: float,
    midlevel_rh_percent: float,
) -> float:
    del lcl_m
    if height_m < 3_000.0:
        fraction = height_m / 3_000.0
        return surface_rh_percent + fraction * (midlevel_rh_percent - surface_rh_percent)
    if height_m <= 7_000.0:
        return midlevel_rh_percent
    if height_m <= 12_000.0:
        fraction = (height_m - 7_000.0) / 5_000.0
        return midlevel_rh_percent + fraction * (25.0 - midlevel_rh_percent)
    return 25.0


def _temperature_for_virtual_target(
    pressure_pa: float,
    target_virtual_temperature_k: float,
    rh_percent: float,
) -> float:
    def residual(temperature_k: float) -> float:
        qv = rh_percent / 100.0 * _saturation_mixing_ratio(pressure_pa, temperature_k)
        return temperature_k * (1.0 + 0.61 * qv) - target_virtual_temperature_k

    lower = max(140.0, target_virtual_temperature_k - 90.0)
    upper = min(420.0, target_virtual_temperature_k + 40.0)
    if residual(lower) * residual(upper) > 0.0:
        raise ValueError(
            "Requested thermodynamic targets do not admit a finite environmental temperature."
        )
    return float(brentq(residual, lower, upper, xtol=1.0e-9))


def _saturation_mixing_ratio(pressure_pa: float, temperature_k: float) -> float:
    temperature_c = temperature_k - 273.15
    vapor_pressure = 611.2 * math.exp(17.67 * temperature_c / (temperature_c + 243.5))
    vapor_pressure = min(max(vapor_pressure, 0.0), 0.99 * pressure_pa)
    return WATER_VAPOR_EPSILON * vapor_pressure / max(pressure_pa - vapor_pressure, 1.0)


def _dewpoint_from_mixing_ratio(pressure_pa: float, mixing_ratio: float) -> float:
    vapor_pressure = pressure_pa * mixing_ratio / (WATER_VAPOR_EPSILON + mixing_ratio)
    logarithm = math.log(max(vapor_pressure, 1.0) / 611.2)
    return 273.15 + 243.5 * logarithm / (17.67 - logarithm)


def _lcl_from_surface(surface: SupercellsProfileLevel) -> float:
    dewpoint = _dewpoint_from_mixing_ratio(surface.pressure_pa, surface.qv_g_kg / 1_000.0)
    return 125.0 * (surface.temperature_k - dewpoint)


def _vector_shear(
    levels: list[SupercellsProfileLevel],
    bottom_m: float,
    top_m: float,
) -> float:
    lower = _interpolated_level(levels, bottom_m)
    upper = _interpolated_level(levels, top_m)
    return math.hypot(upper.u_m_s - lower.u_m_s, upper.v_m_s - lower.v_m_s)


def _storm_relative_helicity(
    levels: list[SupercellsProfileLevel],
    top_m: float,
) -> float:
    mean_u = _layer_mean([(level.height_m, level.u_m_s) for level in levels], 0, 6_000)
    mean_v = _layer_mean([(level.height_m, level.v_m_s) for level in levels], 0, 6_000)
    clipped = [_interpolated_level(levels, 0.0)]
    clipped.extend(level for level in levels if 0.0 < level.height_m < top_m)
    clipped.append(_interpolated_level(levels, top_m))
    return sum(
        (lower.u_m_s - mean_u) * (upper.v_m_s - lower.v_m_s)
        - (lower.v_m_s - mean_v) * (upper.u_m_s - lower.u_m_s)
        for lower, upper in zip(clipped, clipped[1:], strict=False)
    )


def _interpolated_level(
    levels: list[SupercellsProfileLevel],
    height_m: float,
) -> SupercellsProfileLevel:
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
                    "theta_k",
                    "temperature_k",
                    "qv_g_kg",
                    "relative_humidity_percent",
                    "parcel_temperature_k",
                    "parcel_buoyancy_m_s2",
                    "u_m_s",
                    "v_m_s",
                )
            }
            return SupercellsProfileLevel(height_m=height_m, **values)
    return levels[-1]


def _layer_mean(
    points: list[tuple[float, float]],
    lower: float,
    upper: float,
) -> float:
    ordered = sorted(points)
    clipped = [(lower, _interpolate_points(ordered, lower))]
    clipped.extend((height, value) for height, value in ordered if lower < height < upper)
    clipped.append((upper, _interpolate_points(ordered, upper)))
    integral = sum(
        0.5 * (left[1] + right[1]) * (right[0] - left[0])
        for left, right in zip(clipped, clipped[1:], strict=False)
    )
    return integral / (upper - lower)


def _interpolate_points(
    points: list[tuple[float, float]],
    height_m: float,
) -> float:
    if height_m <= points[0][0]:
        return points[0][1]
    for lower, upper in zip(points, points[1:], strict=False):
        if lower[0] <= height_m <= upper[0]:
            fraction = (height_m - lower[0]) / max(upper[0] - lower[0], 1.0e-12)
            return lower[1] + fraction * (upper[1] - lower[1])
    return points[-1][1]


def _crossing_height(
    points: list[tuple[float, float]],
    target: float,
) -> float | None:
    for lower, upper in zip(points, points[1:], strict=False):
        if (lower[1] - target) * (upper[1] - target) <= 0.0:
            difference = upper[1] - lower[1]
            if math.isclose(difference, 0.0, abs_tol=1.0e-12):
                return lower[0]
            fraction = (target - lower[1]) / difference
            return lower[0] + fraction * (upper[0] - lower[0])
    return None


def _profile_heights(model_top_m: float) -> list[float]:
    values = {
        float(value)
        for value in np.arange(
            0.0,
            model_top_m + 2.0 * PROFILE_DZ_M,
            PROFILE_DZ_M,
        )
    }
    values.update({1_000.0, 2_000.0, 3_000.0, 6_000.0, 7_000.0, 12_000.0})
    return sorted(value for value in values if 0.0 <= value <= model_top_m + PROFILE_DZ_M)


def _wrapped_direction_difference(value: float, reference: float) -> float:
    return ((value - reference + 180.0) % 360.0) - 180.0


def _label(key: str) -> str:
    return _DIFFERENCE_METADATA[key][1]


_TARGET_TOLERANCES = {
    "shear_0_6_km_m_s": 0.02,
    "shear_0_2_km_m_s": 0.02,
    "shear_6_12_km_m_s": 0.02,
    "upper_shear_direction_relative_deg": 0.1,
    "mean_wind_0_6_km_speed_m_s": 0.02,
    "mean_wind_0_6_km_direction_deg": 0.1,
    "surface_based_cape_j_kg": 0.5,
    "lcl_height_m_agl": 1.0,
    "midlevel_rh_percent": 0.05,
    "cin_j_kg": 0.5,
}

_DIFFERENCE_METADATA: dict[str, tuple[Any, str, str | None]] = {
    "hodograph_family": ("wind", "Hodograph family", None),
    "shear_0_6_km_m_s": ("wind", "0-6 km vector shear", "m s^-1"),
    "shear_0_2_km_m_s": ("wind", "0-2 km vector shear", "m s^-1"),
    "turning_depth_km_agl": ("wind", "Turning depth", "km AGL"),
    "shear_6_12_km_m_s": ("wind", "6-12 km vector shear", "m s^-1"),
    "upper_shear_direction_relative_deg": (
        "wind",
        "Upper-level shear direction",
        "deg relative",
    ),
    "mean_wind_0_6_km_speed_m_s": ("wind", "0-6 km mean wind speed", "m s^-1"),
    "mean_wind_0_6_km_direction_deg": ("wind", "0-6 km mean wind direction", "deg"),
    "surface_based_cape_j_kg": (
        "stability_thermodynamics",
        "Surface-based CAPE",
        "J kg^-1",
    ),
    "buoyancy_distribution": (
        "stability_thermodynamics",
        "Buoyancy distribution",
        None,
    ),
    "lcl_height_m_agl": ("stability_thermodynamics", "LCL height", "m AGL"),
    "midlevel_rh_percent": ("moisture", "3-7 km mean RH", "%"),
    "cin_j_kg": ("stability_thermodynamics", "CIN", "J kg^-1"),
    "thermal_perturbation_amplitude_k": (
        "forcing_initiation",
        "Thermal perturbation amplitude",
        "K",
    ),
    "thermal_horizontal_radius_km": (
        "forcing_initiation",
        "Thermal horizontal radius",
        "km",
    ),
    "thermal_vertical_radius_km": (
        "forcing_initiation",
        "Thermal vertical radius",
        "km",
    ),
    "thermal_center_height_km_agl": (
        "forcing_initiation",
        "Thermal center height",
        "km AGL",
    ),
    "thermal_center_x_km": ("forcing_initiation", "Thermal center x", "km"),
    "thermal_center_y_km": ("forcing_initiation", "Thermal center y", "km"),
}


__all__ = [
    "BuoyancyDistribution",
    "DAMPING_BASE_M",
    "HodographFamily",
    "MODEL_TOP_M",
    "RECIPE_CONTRACT_VERSION",
    "RECIPE_ID",
    "RECIPE_NAME",
    "ResolvedSupercellsRecipe",
    "SupercellsControls",
    "SupercellsDiagnostics",
    "SupercellsHodographLevel",
    "SupercellsProfileLevel",
    "default_controls",
    "normalize_controls",
    "resolve_supercells_recipe",
]
