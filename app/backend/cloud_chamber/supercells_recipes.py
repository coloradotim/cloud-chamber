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
REFERENCE_TRANSLATION_U_M_S = 12.5
REFERENCE_TRANSLATION_V_M_S = 3.0
# Presentation-grid diagnostics from the source-defined CM1 r21.1 isnd=5 state.
# These are the canonical direct-control values shown for the retained parents.
REFERENCE_CAPE_J_KG = 2_187.2982743400066
REFERENCE_CIN_J_KG = 47.68705306509532
REFERENCE_LCL_HEIGHT_M_AGL = 976.467737214442
REFERENCE_MIDLEVEL_RH_PERCENT = 74.67832813112985

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
CM1_GRAVITY_M_S2 = 9.81
CM1_DRY_AIR_GAS_CONSTANT = 287.04
CM1_DRY_AIR_CP = 1005.7
CM1_WATER_VAPOR_GAS_CONSTANT = 461.5
CM1_WATER_VAPOR_EPSILON = CM1_DRY_AIR_GAS_CONSTANT / CM1_WATER_VAPOR_GAS_CONSTANT
CM1_WATER_VAPOR_REPS = CM1_WATER_VAPOR_GAS_CONSTANT / CM1_DRY_AIR_GAS_CONSTANT
CM1_WK_TROPOPAUSE_M = 12_000.0
CM1_WK_THETA_TROPOPAUSE_K = 343.0
CM1_WK_TEMPERATURE_TROPOPAUSE_K = 213.0
CM1_WK_SURFACE_THETA_K = 300.0
CM1_WK_QV_CAP_KG_KG = 0.014

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


class SupercellsSoundingSurface(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pressure_pa: float
    theta_k: float
    qv_g_kg: float


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
    surface_based_cape_j_kg: float = Field(
        default=REFERENCE_CAPE_J_KG,
        ge=0.0,
        le=8_000.0,
    )
    buoyancy_distribution: BuoyancyDistribution = "reference"
    lcl_height_m_agl: float = Field(
        default=REFERENCE_LCL_HEIGHT_M_AGL,
        ge=100.0,
        le=4_000.0,
    )
    midlevel_rh_percent: float = Field(
        default=REFERENCE_MIDLEVEL_RH_PERCENT,
        ge=0.0,
        le=100.0,
    )
    cin_j_kg: float = Field(default=REFERENCE_CIN_J_KG, ge=0.0, le=500.0)
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
    sounding_surface: SupercellsSoundingSurface
    sounding: list[SupercellsProfileLevel]
    initialized_state: list[SupercellsProfileLevel]
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


def fixed_assumptions() -> dict[str, Any]:
    return {
        "horizontally_homogeneous_environment": True,
        "microphysics": "Morrison double-moment",
        "terrain": "flat",
        "surface_heat_moisture_forcing": False,
        "single_deterministic_thermal": True,
        "storm_object_lineage": False,
        "tornado_diagnosis": False,
    }


def generator_contract() -> dict[str, str]:
    return {
        "wind": "authored_true_circle_hodograph_direct_targets_v2",
        "thermodynamics": "cm1_r21_1_isnd5_reference_continuous_transforms_v2",
        "parcel_diagnostics": "surface_parcel_pseudoadiabatic_lfc_el_v1",
        "external_sounding": "cm1_r21_1_isnd7_scalar_grid_equivalence_v1",
        "translating_frame": "parent_translation_plus_mean_wind_delta_v1",
        "initiation": "source_locked_single_thermal_v1",
    }


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
    heights = _profile_heights(numerical.nz, numerical.dz_m)
    raw_wind = _wind_profile(effective, heights)
    sounding_surface, sounding, thermo = _thermodynamic_profile(
        effective,
        raw_wind,
        heights,
        model_level_count=numerical.nz,
    )
    initialized_state = emulate_cm1_isnd7_initialization(
        sounding_surface,
        sounding,
        heights[: numerical.nz],
    )
    achieved = _achieved_controls(
        effective,
        initialized_state,
        thermo,
    )
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

    mean_u = _layer_mean(
        [(level.height_m, level.u_m_s) for level in initialized_state],
        0.0,
        6_000.0,
    )
    mean_v = _layer_mean(
        [(level.height_m, level.v_m_s) for level in initialized_state],
        0.0,
        6_000.0,
    )
    translation_u, translation_v = _translation_for_controls(effective)
    diagnostics = SupercellsDiagnostics(
        achieved_cape_j_kg=thermo["cape_j_kg"],
        achieved_cin_j_kg=thermo["cin_j_kg"],
        achieved_lcl_height_m_agl=thermo["lcl_height_m_agl"],
        achieved_midlevel_rh_percent=thermo["midlevel_rh_percent"],
        freezing_level_m_agl=thermo["freezing_level_m_agl"],
        hydrostatic_residual_pa=thermo["hydrostatic_residual_pa"],
        shear_0_1_km_m_s=_vector_shear(initialized_state, 0.0, 1_000.0),
        shear_0_2_km_m_s=_vector_shear(initialized_state, 0.0, 2_000.0),
        shear_0_3_km_m_s=_vector_shear(initialized_state, 0.0, 3_000.0),
        shear_0_6_km_m_s=_vector_shear(initialized_state, 0.0, 6_000.0),
        shear_6_12_km_m_s=_vector_shear(initialized_state, 6_000.0, 12_000.0),
        mean_wind_0_6_km_u_m_s=mean_u,
        mean_wind_0_6_km_v_m_s=mean_v,
        mean_wind_0_6_km_speed_m_s=effective.mean_wind_0_6_km_speed_m_s,
        mean_wind_0_6_km_direction_deg=(effective.mean_wind_0_6_km_direction_deg % 360.0),
        storm_relative_helicity_0_1_km_m2_s2=_storm_relative_helicity(
            initialized_state,
            1_000.0,
        ),
        storm_relative_helicity_0_3_km_m2_s2=_storm_relative_helicity(
            initialized_state,
            3_000.0,
        ),
        model_translation_u_m_s=translation_u,
        model_translation_v_m_s=translation_v,
        minimum_boundary_clearance_km=boundary_clearance_m / 1_000.0,
        minimum_vertical_clearance_km=vertical_clearance_m / 1_000.0,
        labels=_diagnostic_labels(effective),
    )
    return ResolvedSupercellsRecipe(
        controls=effective.model_dump(mode="json"),
        achieved_controls=achieved,
        sounding_surface=sounding_surface,
        sounding=sounding,
        initialized_state=initialized_state,
        hodograph=[
            SupercellsHodographLevel(
                height_m=level.height_m,
                u_m_s=level.u_m_s,
                v_m_s=level.v_m_s,
            )
            for level in initialized_state
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
        differences=_resolved_differences(
            effective.model_dump(mode="json"),
            parent.model_dump(mode="json"),
            translation=(translation_u, translation_v),
            parent_translation=_translation_for_controls(parent),
        ),
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
    *,
    model_level_count: int,
) -> tuple[
    SupercellsSoundingSurface,
    list[SupercellsProfileLevel],
    _ThermodynamicDiagnostics,
]:
    surface, source = _source_defined_isnd5_profile(winds, heights)
    source, source_diagnostics = _diagnose_thermodynamics(
        surface,
        source,
        model_level_count=model_level_count,
    )
    if _uses_source_defined_thermodynamics(controls):
        return surface, source, source_diagnostics
    return _transformed_source_profile(
        controls,
        surface,
        source,
        source_diagnostics,
        model_level_count=model_level_count,
    )


def _uses_source_defined_thermodynamics(controls: SupercellsControls) -> bool:
    reference = default_controls()
    return all(
        getattr(controls, name) == getattr(reference, name)
        for name in (
            "surface_based_cape_j_kg",
            "buoyancy_distribution",
            "lcl_height_m_agl",
            "midlevel_rh_percent",
            "cin_j_kg",
        )
    )


def _source_defined_isnd5_profile(
    winds: list[tuple[float, float]],
    heights: list[float],
) -> tuple[SupercellsSoundingSurface, list[SupercellsProfileLevel]]:
    """Reproduce the stock CM1 r21.1 Weisman-Klemp `isnd=5` environment."""
    z = np.asarray(heights, dtype=float)
    below_tropopause = z < CM1_WK_TROPOPAUSE_M
    fractional_height = np.maximum(z / CM1_WK_TROPOPAUSE_M, 0.0) ** 1.25
    theta = np.where(
        below_tropopause,
        CM1_WK_SURFACE_THETA_K
        + (CM1_WK_THETA_TROPOPAUSE_K - CM1_WK_SURFACE_THETA_K) * fractional_height,
        CM1_WK_THETA_TROPOPAUSE_K
        * np.exp(
            CM1_GRAVITY_M_S2
            * (z - CM1_WK_TROPOPAUSE_M)
            / (CM1_WK_TEMPERATURE_TROPOPAUSE_K * CM1_DRY_AIR_CP)
        ),
    )
    authored_rh = np.where(
        below_tropopause,
        1.0 - 0.75 * fractional_height,
        0.25,
    )
    qv = np.zeros_like(z)
    exner = np.ones_like(z)
    pressure = np.full_like(z, SURFACE_PRESSURE_PA)
    surface_saturated_qv = _cm1_saturation_mixing_ratio(
        SURFACE_PRESSURE_PA,
        CM1_WK_SURFACE_THETA_K,
    )
    surface_virtual_theta = (
        CM1_WK_SURFACE_THETA_K
        * (1.0 + surface_saturated_qv * CM1_WATER_VAPOR_REPS)
        / (1.0 + surface_saturated_qv)
    )
    for _iteration in range(20):
        virtual_theta = theta * (1.0 + qv * CM1_WATER_VAPOR_REPS) / (1.0 + qv)
        exner[0] = 1.0 - CM1_GRAVITY_M_S2 * z[0] / (
            CM1_DRY_AIR_CP * 0.5 * (surface_virtual_theta + virtual_theta[0])
        )
        for index in range(1, len(z)):
            exner[index] = exner[index - 1] - CM1_GRAVITY_M_S2 * (z[index] - z[index - 1]) / (
                CM1_DRY_AIR_CP * 0.5 * (virtual_theta[index] + virtual_theta[index - 1])
            )
        pressure = SURFACE_PRESSURE_PA * exner ** (CM1_DRY_AIR_CP / CM1_DRY_AIR_GAS_CONSTANT)
        temperature = theta * exner
        qv = np.minimum(
            np.asarray(
                [
                    rh * _cm1_saturation_mixing_ratio(float(p), float(t))
                    for rh, p, t in zip(
                        authored_rh,
                        pressure,
                        temperature,
                        strict=True,
                    )
                ]
            ),
            CM1_WK_QV_CAP_KG_KG,
        )

    temperature = theta * exner
    actual_rh = np.asarray(
        [
            100.0 * mixing_ratio / max(_cm1_saturation_mixing_ratio(float(p), float(t)), 1.0e-12)
            for mixing_ratio, p, t in zip(qv, pressure, temperature, strict=True)
        ]
    )
    output = [
        SupercellsProfileLevel(
            height_m=float(height),
            pressure_pa=float(level_pressure),
            theta_k=float(level_theta),
            temperature_k=float(level_temperature),
            qv_g_kg=float(level_qv * 1_000.0),
            relative_humidity_percent=float(level_rh),
            parcel_temperature_k=float(level_temperature),
            parcel_buoyancy_m_s2=0.0,
            u_m_s=winds[index][0],
            v_m_s=winds[index][1],
        )
        for index, (
            height,
            level_pressure,
            level_theta,
            level_temperature,
            level_qv,
            level_rh,
        ) in enumerate(
            zip(
                z,
                pressure,
                theta,
                temperature,
                qv,
                actual_rh,
                strict=True,
            )
        )
    ]
    return (
        SupercellsSoundingSurface(
            pressure_pa=SURFACE_PRESSURE_PA,
            theta_k=CM1_WK_SURFACE_THETA_K,
            qv_g_kg=surface_saturated_qv * 1_000.0,
        ),
        output,
    )


def _transformed_source_profile(
    controls: SupercellsControls,
    source_surface: SupercellsSoundingSurface,
    source: list[SupercellsProfileLevel],
    source_diagnostics: _ThermodynamicDiagnostics,
    *,
    model_level_count: int,
) -> tuple[
    SupercellsSoundingSurface,
    list[SupercellsProfileLevel],
    _ThermodynamicDiagnostics,
]:
    latent = controls.model_dump(mode="json")
    result = _source_relative_transformed_profile(
        controls,
        source_surface,
        source,
        source_diagnostics,
        model_level_count=model_level_count,
    )
    target_keys = (
        "surface_based_cape_j_kg",
        "cin_j_kg",
        "lcl_height_m_agl",
        "midlevel_rh_percent",
    )
    for _iteration in range(12):
        diagnostics = result[2]
        achieved = {
            "surface_based_cape_j_kg": diagnostics["cape_j_kg"],
            "cin_j_kg": diagnostics["cin_j_kg"],
            "lcl_height_m_agl": diagnostics["lcl_height_m_agl"],
            "midlevel_rh_percent": diagnostics["midlevel_rh_percent"],
        }
        errors = {key: float(getattr(controls, key)) - float(achieved[key]) for key in target_keys}
        if all(
            abs(errors[key])
            <= _thermodynamic_target_tolerance(
                key,
                float(getattr(controls, key)),
            )
            for key in target_keys
        ):
            break
        for key in target_keys:
            target = float(getattr(controls, key))
            if key in {"surface_based_cape_j_kg", "cin_j_kg"} and target == 0.0:
                continue
            gain = 4.0 if key == "midlevel_rh_percent" else 1.0
            latent[key] = float(latent[key]) + gain * errors[key]
        result = _source_relative_transformed_profile(
            controls.model_copy(update=latent),
            source_surface,
            source,
            source_diagnostics,
            model_level_count=model_level_count,
        )
    return result


def _source_relative_transformed_profile(
    controls: SupercellsControls,
    source_surface: SupercellsSoundingSurface,
    source: list[SupercellsProfileLevel],
    source_diagnostics: _ThermodynamicDiagnostics,
    *,
    model_level_count: int,
    apply_reference_delta: bool = True,
) -> tuple[
    SupercellsSoundingSurface,
    list[SupercellsProfileLevel],
    _ThermodynamicDiagnostics,
]:
    reference = default_controls()
    z = np.asarray([level.height_m for level in source], dtype=float)
    physical_z = z[:model_level_count]
    source_buoyancy = np.asarray(
        [level.parcel_buoyancy_m_s2 for level in source],
        dtype=float,
    )
    target_cape = max(
        0.0,
        source_diagnostics["cape_j_kg"]
        + controls.surface_based_cape_j_kg
        - reference.surface_based_cape_j_kg,
    )
    target_cin = max(
        0.0,
        source_diagnostics["cin_j_kg"] + controls.cin_j_kg - reference.cin_j_kg,
    )
    target_lcl = max(
        0.0,
        source_diagnostics["lcl_height_m_agl"]
        + controls.lcl_height_m_agl
        - reference.lcl_height_m_agl,
    )
    target_midlevel_rh = (
        source_diagnostics["midlevel_rh_percent"]
        + controls.midlevel_rh_percent
        - reference.midlevel_rh_percent
    )
    lfc_index, equilibrium_index = _parcel_energy_indices(
        physical_z,
        source_buoyancy[:model_level_count],
        lcl_height_m=source_diagnostics["lcl_height_m_agl"],
    )
    target_buoyancy = source_buoyancy.copy()
    positive = np.maximum(
        source_buoyancy[lfc_index : equilibrium_index + 1],
        0.0,
    )
    negative = np.maximum(-source_buoyancy[: lfc_index + 1], 0.0)
    if controls.buoyancy_distribution == "reference":
        positive_shape = positive
    else:
        positive_shape = _cape_shape(
            z[lfc_index : equilibrium_index + 1],
            max(target_lcl + 750.0, 2_000.0),
            controls.buoyancy_distribution,
        )
    target_buoyancy[lfc_index : equilibrium_index + 1] = _normalized_area_profile(
        physical_z[lfc_index : equilibrium_index + 1],
        positive_shape,
        target_cape,
        negative=False,
    )
    target_buoyancy[: lfc_index + 1] = _normalized_area_profile(
        physical_z[: lfc_index + 1],
        negative,
        -target_cin,
        negative=True,
    )

    source_rh = np.asarray(
        [level.relative_humidity_percent for level in source],
        dtype=float,
    )
    midlevel_delta = target_midlevel_rh - source_diagnostics["midlevel_rh_percent"]
    lower_midlevel_node = max(float(value) for value in z if value < 3_000.0)
    upper_midlevel_node = min(float(value) for value in z if value > 7_000.0)
    midlevel_weight = np.where(
        z <= upper_midlevel_node,
        1.0,
        np.clip(
            (12_000.0 - z) / max(12_000.0 - upper_midlevel_node, 1.0),
            0.0,
            1.0,
        ),
    )
    target_rh = source_rh + midlevel_delta * midlevel_weight
    pressure = np.asarray([level.pressure_pa for level in source], dtype=float)
    theta = np.asarray([level.theta_k for level in source], dtype=float)
    qv = np.asarray([level.qv_g_kg / 1_000.0 for level in source], dtype=float)
    temperature = np.asarray([level.temperature_k for level in source], dtype=float)
    source_parcel_qv = _parcel_surface_qv(source)
    target_low_qv = source_parcel_qv
    surface_qv = source_surface.qv_g_kg / 1_000.0

    for _iteration in range(40):
        dewpoint_k = SURFACE_TEMPERATURE_K - target_lcl / 125.0
        target_low_qv = _cm1_saturation_mixing_ratio(SURFACE_PRESSURE_PA, dewpoint_k)
        lowlevel_weight = np.clip(
            (lower_midlevel_node - z) / max(lower_midlevel_node, 1.0),
            0.0,
            1.0,
        )
        desired_lowlevel_qv = np.maximum(
            1.0e-12,
            np.asarray([level.qv_g_kg / 1_000.0 for level in source])
            + (target_low_qv - source_parcel_qv) * lowlevel_weight,
        )
        lowlevel_rh = np.asarray(
            [
                100.0
                * desired_qv
                / max(
                    _cm1_saturation_mixing_ratio(
                        float(level_pressure),
                        float(level_temperature),
                    ),
                    1.0e-12,
                )
                for desired_qv, level_pressure, level_temperature in zip(
                    desired_lowlevel_qv,
                    pressure,
                    temperature,
                    strict=True,
                )
            ]
        )
        resolved_rh = np.clip(
            np.where(lowlevel_weight > 0.0, lowlevel_rh, target_rh),
            0.01,
            100.0,
        )
        surface_qv = max(
            1.0e-12,
            source_surface.qv_g_kg / 1_000.0 + target_low_qv - source_parcel_qv,
        )
        surface_virtual_theta = (
            source_surface.theta_k * (1.0 + surface_qv * CM1_WATER_VAPOR_REPS) / (1.0 + surface_qv)
        )
        virtual_theta = theta * (1.0 + qv * CM1_WATER_VAPOR_REPS) / (1.0 + qv)
        exner = np.empty_like(z)
        exner[0] = 1.0 - CM1_GRAVITY_M_S2 * z[0] / (
            CM1_DRY_AIR_CP * 0.5 * (surface_virtual_theta + virtual_theta[0])
        )
        for index in range(1, len(z)):
            exner[index] = exner[index - 1] - CM1_GRAVITY_M_S2 * (z[index] - z[index - 1]) / (
                CM1_DRY_AIR_CP * 0.5 * (virtual_theta[index] + virtual_theta[index - 1])
            )
        pressure = SURFACE_PRESSURE_PA * exner ** (CM1_DRY_AIR_CP / CM1_DRY_AIR_GAS_CONSTANT)
        provisional = [
            source[index].model_copy(
                update={
                    "pressure_pa": float(pressure[index]),
                    "theta_k": float(theta[index]),
                    "temperature_k": float(temperature[index]),
                    "qv_g_kg": float(qv[index] * 1_000.0),
                }
            )
            for index in range(len(source))
        ]
        parcel_temperature = _parcel_temperature_profile(
            provisional,
            initial_qv_kg_kg=target_low_qv,
            lcl_height_m=target_lcl,
        )
        for index in range(len(z)):
            parcel_qv = (
                target_low_qv
                if z[index] <= target_lcl
                else _cm1_saturation_mixing_ratio(
                    float(pressure[index]),
                    float(parcel_temperature[index]),
                )
            )
            parcel_virtual_temperature = (
                parcel_temperature[index]
                * (1.0 + parcel_qv * CM1_WATER_VAPOR_REPS)
                / (1.0 + parcel_qv)
            )
            target_virtual_temperature = parcel_virtual_temperature / (
                1.0 + target_buoyancy[index] / CM1_GRAVITY_M_S2
            )
            temperature[index] = _temperature_for_cm1_virtual_target(
                float(pressure[index]),
                float(target_virtual_temperature),
                float(resolved_rh[index]),
            )
            qv[index] = (
                resolved_rh[index]
                / 100.0
                * _cm1_saturation_mixing_ratio(
                    float(pressure[index]),
                    float(temperature[index]),
                )
            )
            theta[index] = temperature[index] / exner[index]

    surface = SupercellsSoundingSurface(
        pressure_pa=source_surface.pressure_pa,
        theta_k=source_surface.theta_k,
        qv_g_kg=surface_qv * 1_000.0,
    )
    transformed = [
        SupercellsProfileLevel(
            height_m=level.height_m,
            pressure_pa=float(pressure[index]),
            theta_k=float(theta[index]),
            temperature_k=float(temperature[index]),
            qv_g_kg=float(qv[index] * 1_000.0),
            relative_humidity_percent=float(
                100.0
                * qv[index]
                / max(
                    _cm1_saturation_mixing_ratio(
                        float(pressure[index]),
                        float(temperature[index]),
                    ),
                    1.0e-12,
                )
            ),
            parcel_temperature_k=float(temperature[index]),
            parcel_buoyancy_m_s2=0.0,
            u_m_s=level.u_m_s,
            v_m_s=level.v_m_s,
        )
        for index, level in enumerate(source)
    ]
    if apply_reference_delta:
        baseline_surface, baseline, _baseline_diagnostics = _source_relative_transformed_profile(
            default_controls(),
            source_surface,
            source,
            source_diagnostics,
            model_level_count=model_level_count,
            apply_reference_delta=False,
        )
        return _apply_source_relative_delta(
            source_surface,
            source,
            baseline_surface,
            baseline,
            surface,
            transformed,
            model_level_count=model_level_count,
        )
    return (
        surface,
        *_diagnose_thermodynamics(
            surface,
            transformed,
            model_level_count=model_level_count,
        ),
    )


def _apply_source_relative_delta(
    source_surface: SupercellsSoundingSurface,
    source: list[SupercellsProfileLevel],
    baseline_surface: SupercellsSoundingSurface,
    baseline: list[SupercellsProfileLevel],
    target_surface: SupercellsSoundingSurface,
    target: list[SupercellsProfileLevel],
    *,
    model_level_count: int,
) -> tuple[
    SupercellsSoundingSurface,
    list[SupercellsProfileLevel],
    _ThermodynamicDiagnostics,
]:
    surface = source_surface.model_copy(
        update={
            "qv_g_kg": max(
                1.0e-9,
                source_surface.qv_g_kg + target_surface.qv_g_kg - baseline_surface.qv_g_kg,
            )
        }
    )
    z = np.asarray([level.height_m for level in source], dtype=float)
    theta = np.asarray(
        [
            source_level.theta_k + target_level.theta_k - baseline_level.theta_k
            for source_level, target_level, baseline_level in zip(
                source,
                target,
                baseline,
                strict=True,
            )
        ]
    )
    qv = np.asarray(
        [
            max(
                1.0e-12,
                (source_level.qv_g_kg + target_level.qv_g_kg - baseline_level.qv_g_kg) / 1_000.0,
            )
            for source_level, target_level, baseline_level in zip(
                source,
                target,
                baseline,
                strict=True,
            )
        ]
    )
    virtual_theta = theta * (1.0 + qv * CM1_WATER_VAPOR_REPS) / (1.0 + qv)
    surface_qv = surface.qv_g_kg / 1_000.0
    surface_virtual_theta = (
        surface.theta_k * (1.0 + surface_qv * CM1_WATER_VAPOR_REPS) / (1.0 + surface_qv)
    )
    exner = np.empty_like(z)
    exner[0] = 1.0 - CM1_GRAVITY_M_S2 * z[0] / (
        CM1_DRY_AIR_CP * 0.5 * (surface_virtual_theta + virtual_theta[0])
    )
    for index in range(1, len(z)):
        exner[index] = exner[index - 1] - CM1_GRAVITY_M_S2 * (z[index] - z[index - 1]) / (
            CM1_DRY_AIR_CP * 0.5 * (virtual_theta[index] + virtual_theta[index - 1])
        )
    pressure = SURFACE_PRESSURE_PA * exner ** (CM1_DRY_AIR_CP / CM1_DRY_AIR_GAS_CONSTANT)
    temperature = theta * exner
    adjusted = [
        source_level.model_copy(
            update={
                "pressure_pa": float(pressure[index]),
                "theta_k": float(theta[index]),
                "temperature_k": float(temperature[index]),
                "qv_g_kg": float(qv[index] * 1_000.0),
                "relative_humidity_percent": float(
                    100.0
                    * qv[index]
                    / max(
                        _cm1_saturation_mixing_ratio(
                            float(pressure[index]),
                            float(temperature[index]),
                        ),
                        1.0e-12,
                    )
                ),
            }
        )
        for index, source_level in enumerate(source)
    ]
    return (
        surface,
        *_diagnose_thermodynamics(
            surface,
            adjusted,
            model_level_count=model_level_count,
        ),
    )


def _diagnose_thermodynamics(
    surface: SupercellsSoundingSurface,
    sounding: list[SupercellsProfileLevel],
    *,
    model_level_count: int,
) -> tuple[list[SupercellsProfileLevel], _ThermodynamicDiagnostics]:
    physical = sounding[:model_level_count]
    lcl_height = _lcl_from_profile(physical)
    parcel_temperature = _parcel_temperature_profile(
        sounding,
        initial_qv_kg_kg=_parcel_surface_qv(physical),
        lcl_height_m=lcl_height,
    )
    buoyancy: list[float] = []
    diagnosed: list[SupercellsProfileLevel] = []
    for index, level in enumerate(sounding):
        parcel_qv = (
            _parcel_surface_qv(physical)
            if level.height_m <= lcl_height
            else _cm1_saturation_mixing_ratio(
                level.pressure_pa,
                float(parcel_temperature[index]),
            )
        )
        parcel_virtual_temperature = (
            parcel_temperature[index] * (1.0 + parcel_qv * CM1_WATER_VAPOR_REPS) / (1.0 + parcel_qv)
        )
        environment_qv = level.qv_g_kg / 1_000.0
        environment_virtual_temperature = (
            level.temperature_k
            * (1.0 + environment_qv * CM1_WATER_VAPOR_REPS)
            / (1.0 + environment_qv)
        )
        level_buoyancy = (
            CM1_GRAVITY_M_S2
            * (parcel_virtual_temperature - environment_virtual_temperature)
            / environment_virtual_temperature
        )
        buoyancy.append(float(level_buoyancy))
        diagnosed.append(
            level.model_copy(
                update={
                    "parcel_temperature_k": float(parcel_temperature[index]),
                    "parcel_buoyancy_m_s2": float(level_buoyancy),
                }
            )
        )
    cape, cin = _integrated_parcel_energy(
        np.asarray([level.height_m for level in physical], dtype=float),
        np.asarray(buoyancy[:model_level_count], dtype=float),
        lcl_height_m=lcl_height,
    )
    freezing_level = _crossing_height(
        [(level.height_m, level.temperature_k - 273.15) for level in physical],
        0.0,
    )
    mean_u = _layer_mean([(level.height_m, level.u_m_s) for level in physical], 0, 6_000)
    mean_v = _layer_mean([(level.height_m, level.v_m_s) for level in physical], 0, 6_000)
    return diagnosed, {
        "cape_j_kg": cape,
        "cin_j_kg": cin,
        "lcl_height_m_agl": lcl_height,
        "midlevel_rh_percent": _layer_mean(
            [(level.height_m, level.relative_humidity_percent) for level in physical],
            3_000.0,
            7_000.0,
        ),
        "freezing_level_m_agl": freezing_level,
        "hydrostatic_residual_pa": _cm1_exner_readback_residual_pa(
            diagnosed,
            surface=surface,
        ),
        "translation_u_m_s": mean_u,
        "translation_v_m_s": mean_v,
    }


def _integrated_parcel_energy(
    height_m: NDArray[np.float64],
    buoyancy_m_s2: NDArray[np.float64],
    *,
    lcl_height_m: float,
) -> tuple[float, float]:
    lfc_index, equilibrium_index = _parcel_energy_indices(
        height_m,
        buoyancy_m_s2,
        lcl_height_m=lcl_height_m,
    )
    cin = float(
        -np.trapezoid(
            np.minimum(buoyancy_m_s2[: lfc_index + 1], 0.0),
            height_m[: lfc_index + 1],
        )
    )
    cape = float(
        np.trapezoid(
            np.maximum(buoyancy_m_s2[lfc_index : equilibrium_index + 1], 0.0),
            height_m[lfc_index : equilibrium_index + 1],
        )
    )
    return cape, cin


def _parcel_energy_indices(
    height_m: NDArray[np.float64],
    buoyancy_m_s2: NDArray[np.float64],
    *,
    lcl_height_m: float,
) -> tuple[int, int]:
    lfc_index = next(
        (
            index
            for index, (height, buoyancy) in enumerate(zip(height_m, buoyancy_m_s2, strict=True))
            if height >= lcl_height_m and buoyancy > 0.0
        ),
        len(height_m) - 1,
    )
    equilibrium_index = next(
        (index for index in range(lfc_index + 1, len(height_m)) if buoyancy_m_s2[index] <= 0.0),
        len(height_m) - 1,
    )
    return lfc_index, equilibrium_index


def _temperature_for_cm1_virtual_target(
    pressure_pa: float,
    target_virtual_temperature_k: float,
    rh_percent: float,
) -> float:
    def residual(temperature_k: float) -> float:
        qv = rh_percent / 100.0 * _cm1_saturation_mixing_ratio(pressure_pa, temperature_k)
        virtual_temperature = temperature_k * (1.0 + qv * CM1_WATER_VAPOR_REPS) / (1.0 + qv)
        return virtual_temperature - target_virtual_temperature_k

    lower = max(100.0, target_virtual_temperature_k - 90.0)
    upper = min(420.0, target_virtual_temperature_k + 40.0)
    if residual(lower) * residual(upper) > 0.0:
        raise ValueError("Requested thermodynamic transform does not admit a finite temperature.")
    return float(brentq(residual, lower, upper, xtol=1.0e-9))


def emulate_cm1_isnd7_initialization(
    surface: SupercellsSoundingSurface,
    sounding: list[SupercellsProfileLevel],
    model_heights_m: list[float],
) -> list[SupercellsProfileLevel]:
    """Emulate pinned CM1 r21.1 `base.F` isnd=7 initialization."""
    zsnd = np.asarray([0.0, *[level.height_m for level in sounding]], dtype=float)
    theta_snd = np.asarray([surface.theta_k, *[level.theta_k for level in sounding]])
    qv_snd = np.asarray(
        [surface.qv_g_kg / 1_000.0, *[level.qv_g_kg / 1_000.0 for level in sounding]]
    )
    u_rows = [level.u_m_s for level in sounding]
    v_rows = [level.v_m_s for level in sounding]
    surface_u = u_rows[0] - zsnd[1] * (u_rows[1] - u_rows[0]) / (zsnd[2] - zsnd[1])
    surface_v = v_rows[0] - zsnd[1] * (v_rows[1] - v_rows[0]) / (zsnd[2] - zsnd[1])
    u_snd = np.asarray([surface_u, *u_rows])
    v_snd = np.asarray([surface_v, *v_rows])
    virtual_theta_snd = theta_snd * (1.0 + qv_snd * CM1_WATER_VAPOR_REPS) / (1.0 + qv_snd)
    exner_snd = np.empty_like(zsnd)
    exner_snd[0] = (surface.pressure_pa / SURFACE_PRESSURE_PA) ** (
        CM1_DRY_AIR_GAS_CONSTANT / CM1_DRY_AIR_CP
    )
    for index in range(1, len(zsnd)):
        exner_snd[index] = exner_snd[index - 1] - CM1_GRAVITY_M_S2 * (
            zsnd[index] - zsnd[index - 1]
        ) / (CM1_DRY_AIR_CP * 0.5 * (virtual_theta_snd[index] + virtual_theta_snd[index - 1]))
    pressure_snd = SURFACE_PRESSURE_PA * exner_snd ** (CM1_DRY_AIR_CP / CM1_DRY_AIR_GAS_CONSTANT)
    temperature_snd = theta_snd * exner_snd
    rh_snd = np.asarray(
        [
            mixing_ratio
            / max(
                _cm1_saturation_mixing_ratio(float(pressure), float(temperature)),
                1.0e-12,
            )
            for mixing_ratio, pressure, temperature in zip(
                qv_snd,
                pressure_snd,
                temperature_snd,
                strict=True,
            )
        ]
    )
    heights = np.asarray(model_heights_m, dtype=float)
    theta = np.interp(heights, zsnd, theta_snd)
    provisional_pressure = np.interp(heights, zsnd, pressure_snd)
    temperature = np.interp(heights, zsnd, temperature_snd)
    rh = np.interp(heights, zsnd, rh_snd)
    u = np.interp(heights, zsnd, u_snd)
    v = np.interp(heights, zsnd, v_snd)
    qv = np.asarray(
        [
            level_rh * _cm1_saturation_mixing_ratio(float(pressure), float(level_temperature))
            for level_rh, pressure, level_temperature in zip(
                rh,
                provisional_pressure,
                temperature,
                strict=True,
            )
        ]
    )
    virtual_theta = theta * (1.0 + qv * CM1_WATER_VAPOR_REPS) / (1.0 + qv)
    surface_qv = surface.qv_g_kg / 1_000.0
    surface_virtual_theta = (
        surface.theta_k * (1.0 + surface_qv * CM1_WATER_VAPOR_REPS) / (1.0 + surface_qv)
    )
    exner = np.empty_like(heights)
    exner[0] = exner_snd[0] - CM1_GRAVITY_M_S2 * heights[0] / (
        CM1_DRY_AIR_CP * 0.5 * (surface_virtual_theta + virtual_theta[0])
    )
    for index in range(1, len(heights)):
        exner[index] = exner[index - 1] - CM1_GRAVITY_M_S2 * (
            heights[index] - heights[index - 1]
        ) / (CM1_DRY_AIR_CP * 0.5 * (virtual_theta[index] + virtual_theta[index - 1]))
    pressure = SURFACE_PRESSURE_PA * exner ** (CM1_DRY_AIR_CP / CM1_DRY_AIR_GAS_CONSTANT)
    final_rh = np.asarray(
        [
            100.0
            * mixing_ratio
            / max(
                _cm1_saturation_mixing_ratio(
                    float(level_pressure),
                    float(level_theta * level_exner),
                ),
                1.0e-12,
            )
            for mixing_ratio, level_pressure, level_theta, level_exner in zip(
                qv,
                pressure,
                theta,
                exner,
                strict=True,
            )
        ]
    )
    return [
        SupercellsProfileLevel(
            height_m=float(heights[index]),
            pressure_pa=float(pressure[index]),
            theta_k=float(theta[index]),
            temperature_k=float(temperature[index]),
            qv_g_kg=float(qv[index] * 1_000.0),
            relative_humidity_percent=float(final_rh[index]),
            parcel_temperature_k=float(temperature[index]),
            parcel_buoyancy_m_s2=0.0,
            u_m_s=float(u[index]),
            v_m_s=float(v[index]),
        )
        for index in range(len(heights))
    ]


def _cm1_saturation_mixing_ratio(
    pressure_pa: float,
    temperature_k: float,
) -> float:
    vapor_pressure = 611.2 * math.exp(17.67 * (temperature_k - 273.15) / (temperature_k - 29.65))
    vapor_pressure = min(vapor_pressure, pressure_pa * 0.5)
    return CM1_WATER_VAPOR_EPSILON * vapor_pressure / (pressure_pa - vapor_pressure)


def _cm1_exner_readback_residual_pa(
    sounding: list[SupercellsProfileLevel],
    *,
    surface: SupercellsSoundingSurface,
) -> float:
    surface_virtual_theta = (
        surface.theta_k
        * (1.0 + surface.qv_g_kg / 1_000.0 * CM1_WATER_VAPOR_REPS)
        / (1.0 + surface.qv_g_kg / 1_000.0)
    )
    residual = 0.0
    previous_exner = (surface.pressure_pa / SURFACE_PRESSURE_PA) ** (
        CM1_DRY_AIR_GAS_CONSTANT / CM1_DRY_AIR_CP
    )
    previous_virtual_theta = surface_virtual_theta
    previous_height = 0.0
    for level in sounding:
        virtual_theta = (
            level.theta_k
            * (1.0 + level.qv_g_kg / 1_000.0 * CM1_WATER_VAPOR_REPS)
            / (1.0 + level.qv_g_kg / 1_000.0)
        )
        expected_exner = previous_exner - CM1_GRAVITY_M_S2 * (level.height_m - previous_height) / (
            CM1_DRY_AIR_CP * 0.5 * (previous_virtual_theta + virtual_theta)
        )
        expected_pressure = SURFACE_PRESSURE_PA * expected_exner ** (
            CM1_DRY_AIR_CP / CM1_DRY_AIR_GAS_CONSTANT
        )
        residual = max(residual, abs(level.pressure_pa - expected_pressure))
        previous_exner = expected_exner
        previous_virtual_theta = virtual_theta
        previous_height = level.height_m
    return residual


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


def _achieved_controls(
    controls: SupercellsControls,
    sounding: list[SupercellsProfileLevel],
    thermo: _ThermodynamicDiagnostics,
) -> dict[str, Any]:
    del sounding
    return {
        "hodograph_family": controls.hodograph_family,
        "shear_0_6_km_m_s": controls.shear_0_6_km_m_s,
        "shear_0_2_km_m_s": controls.shear_0_2_km_m_s,
        "turning_depth_km_agl": controls.turning_depth_km_agl,
        "shear_6_12_km_m_s": controls.shear_6_12_km_m_s,
        "upper_shear_direction_relative_deg": controls.upper_shear_direction_relative_deg,
        "mean_wind_0_6_km_speed_m_s": controls.mean_wind_0_6_km_speed_m_s,
        "mean_wind_0_6_km_direction_deg": controls.mean_wind_0_6_km_direction_deg,
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
        tolerance = (
            _thermodynamic_target_tolerance(key, float(target))
            if key
            in {
                "surface_based_cape_j_kg",
                "lcl_height_m_agl",
                "midlevel_rh_percent",
                "cin_j_kg",
            }
            else _TARGET_TOLERANCES.get(key, 0.02)
        )
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


def _thermodynamic_target_tolerance(key: str, target: float) -> float:
    tolerance = _TARGET_TOLERANCES[key]
    if key in {"surface_based_cape_j_kg", "cin_j_kg"}:
        return max(tolerance, 0.01 * max(abs(target), 1.0))
    return tolerance


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


def _resolved_differences(
    after: dict[str, Any],
    before: dict[str, Any],
    *,
    translation: tuple[float, float],
    parent_translation: tuple[float, float],
) -> list[VariationDifference]:
    differences = _control_differences(after, before)
    for component, after_value, before_value in (
        ("u", translation[0], parent_translation[0]),
        ("v", translation[1], parent_translation[1]),
    ):
        if math.isclose(after_value, before_value, rel_tol=0.0, abs_tol=1.0e-6):
            continue
        differences.append(
            VariationDifference(
                category="wind",
                path=f"derived.model_translation_{component}_m_s",
                label=f"Model translation {component}",
                before=before_value,
                after=after_value,
                units="m/s",
            )
        )
    return differences


def _translation_for_controls(
    controls: SupercellsControls,
) -> tuple[float, float]:
    normalized = normalize_controls(controls)
    direction = math.radians(normalized.mean_wind_0_6_km_direction_deg % 360.0)
    mean_u = normalized.mean_wind_0_6_km_speed_m_s * math.cos(direction)
    mean_v = normalized.mean_wind_0_6_km_speed_m_s * math.sin(direction)
    return (
        REFERENCE_TRANSLATION_U_M_S + mean_u - REFERENCE_MEAN_U_M_S,
        REFERENCE_TRANSLATION_V_M_S + mean_v - REFERENCE_MEAN_V_M_S,
    )


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


def _parcel_temperature_profile(
    sounding: list[SupercellsProfileLevel],
    *,
    initial_qv_kg_kg: float,
    lcl_height_m: float,
) -> NDArray[np.float64]:
    del initial_qv_kg_kg
    output = np.empty(len(sounding), dtype=float)
    dry_lapse = CM1_GRAVITY_M_S2 / CM1_DRY_AIR_CP
    lcl_temperature = SURFACE_TEMPERATURE_K - dry_lapse * lcl_height_m
    parcel_temperature = SURFACE_TEMPERATURE_K
    previous_height = 0.0
    for index, level in enumerate(sounding):
        if level.height_m <= lcl_height_m:
            parcel_temperature = SURFACE_TEMPERATURE_K - dry_lapse * level.height_m
        else:
            start_height = max(previous_height, lcl_height_m)
            if previous_height < lcl_height_m:
                parcel_temperature = lcl_temperature
            distance = level.height_m - start_height
            substeps = max(1, math.ceil(distance / 25.0))
            step = distance / substeps
            for substep in range(substeps):
                height = start_height + (substep + 0.5) * step
                pressure = _interpolate_points(
                    [(item.height_m, item.pressure_pa) for item in sounding],
                    height,
                )
                saturation_qv = _cm1_saturation_mixing_ratio(
                    pressure,
                    parcel_temperature,
                )
                moist_lapse = (
                    CM1_GRAVITY_M_S2
                    * (
                        1.0
                        + LATENT_HEAT_VAPORIZATION
                        * saturation_qv
                        / (CM1_DRY_AIR_GAS_CONSTANT * parcel_temperature)
                    )
                    / (
                        CM1_DRY_AIR_CP
                        + LATENT_HEAT_VAPORIZATION**2
                        * saturation_qv
                        * CM1_WATER_VAPOR_EPSILON
                        / (CM1_DRY_AIR_GAS_CONSTANT * parcel_temperature**2)
                    )
                )
                parcel_temperature -= moist_lapse * step
        output[index] = parcel_temperature
        previous_height = level.height_m
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


def _lcl_from_profile(sounding: list[SupercellsProfileLevel]) -> float:
    dewpoint = _dewpoint_from_mixing_ratio(
        SURFACE_PRESSURE_PA,
        _parcel_surface_qv(sounding),
    )
    return 125.0 * (SURFACE_TEMPERATURE_K - dewpoint)


def _parcel_surface_qv(sounding: list[SupercellsProfileLevel]) -> float:
    if len(sounding) < 2:
        return sounding[0].qv_g_kg / 1_000.0
    first, second = sounding[:2]
    fraction = -first.height_m / (second.height_m - first.height_m)
    extrapolated = first.qv_g_kg + fraction * (second.qv_g_kg - first.qv_g_kg)
    return max(extrapolated / 1_000.0, 1.0e-12)


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


def _profile_heights(nz: int, dz_m: float) -> list[float]:
    return [(index + 0.5) * dz_m for index in range(nz + 1)]


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
    "surface_based_cape_j_kg": 10.0,
    "lcl_height_m_agl": 1.0,
    "midlevel_rh_percent": 0.05,
    "cin_j_kg": 2.0,
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
    "fixed_assumptions",
    "generator_contract",
    "normalize_controls",
    "resolve_supercells_recipe",
]
