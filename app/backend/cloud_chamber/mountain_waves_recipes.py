"""Approved Mountain Waves Recipe controls and deterministic generators."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cloud_chamber.run_cost import (
    MIB,
    NumericalRealization,
    ObservationPlan,
    RunCostProfile,
)
from cloud_chamber.variation_envelope import VariationDifference

DRY_RECIPE_ID: Literal["dry_ridge_mechanics"] = "dry_ridge_mechanics"
BOULDER_RECIPE_ID: Literal["boulder_moist_wave"] = "boulder_moist_wave"
RECIPE_CONTRACT_VERSION: Literal["1"] = "1"
RUN_COST_RECIPE_VERSION = "approved_variation_contract_v1"

RecipeId = Literal["dry_ridge_mechanics", "boulder_moist_wave"]


class RecipeSoundingLevel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    height_m: float
    pressure_pa: float
    theta_k: float
    qv_g_kg: float
    u_m_s: float
    v_m_s: float = 0.0


class DryRidgeControls(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ridge_height_m: float = Field(default=400.0, ge=100.0, le=2_500.0)
    ridge_half_width_m: float = Field(default=1_000.0, ge=500.0, le=20_000.0)
    cross_ridge_wind_m_s: float = Field(default=10.0, ge=5.0, le=30.0)
    dry_stability_n_s: float = Field(default=0.01, ge=0.005, le=0.020)
    wind_shear_through_10km_m_s: float = Field(default=0.0, ge=-20.0, le=20.0)
    layered_stability: bool = False
    lower_stability_n_s: float = Field(default=0.01, ge=0.005, le=0.020)
    upper_stability_n_s: float = Field(default=0.01, ge=0.005, le=0.020)
    stability_transition_height_m: float = Field(default=6_000.0, ge=2_000.0, le=12_000.0)
    stability_transition_width_m: float = Field(default=1_000.0, ge=500.0, le=3_000.0)


class BoulderMoistControls(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ridge_height_m: float = Field(default=2_000.0, ge=500.0, le=3_500.0)
    ridge_half_width_m: float = Field(default=10_000.0, ge=5_000.0, le=30_000.0)
    flow_strength_factor: float = Field(default=1.0, ge=0.5, le=1.5)
    wind_offset_m_s: float = Field(default=0.0, ge=-10.0, le=10.0)
    shear_strength_factor: float = Field(default=1.0, ge=0.5, le=1.5)
    lower_rh_deficit_factor: float = Field(default=1.0, ge=0.0, le=2.0)
    midlevel_rh_deficit_factor: float = Field(default=1.0, ge=0.0, le=2.0)
    dry_air_counterpart: bool = False
    lower_stability_factor: float = Field(default=1.0, ge=0.5, le=1.5)
    midlevel_stability_factor: float = Field(default=1.0, ge=0.5, le=1.5)
    upper_stability_factor: float = Field(default=1.0, ge=0.5, le=1.5)


class MountainWavesRecipeControls(BaseModel):
    """Typed union wrapper that keeps the Recipe identity explicit."""

    model_config = ConfigDict(extra="forbid")

    recipe_id: RecipeId
    dry_ridge: DryRidgeControls | None = None
    boulder_moist: BoulderMoistControls | None = None

    @model_validator(mode="after")
    def validate_recipe_payload(self) -> MountainWavesRecipeControls:
        if self.recipe_id == DRY_RECIPE_ID:
            if self.dry_ridge is None or self.boulder_moist is not None:
                raise ValueError("Dry Ridge Mechanics requires only dry_ridge controls.")
        elif self.boulder_moist is None or self.dry_ridge is not None:
            raise ValueError("Boulder Moist Wave requires only boulder_moist controls.")
        return self

    def payload(self) -> dict[str, Any]:
        controls = self.dry_ridge if self.recipe_id == DRY_RECIPE_ID else self.boulder_moist
        assert controls is not None
        return controls.model_dump(mode="json")


class RecipeRegimeDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    maximum_terrain_slope: float
    cells_per_half_width: float
    nondimensional_mountain_height: float
    nonhydrostatic_width_parameter: float
    critical_levels_m: list[float]
    terrain_resolution: str
    upstream_clearance_km: float
    downstream_clearance_km: float
    advective_time_seconds: float
    periodic_wrap_time_seconds: float
    model_top_m: float
    damping_base_m: float
    labels: list[str]


class ResolvedMountainWavesRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: RecipeId
    recipe_name: str
    controls: dict[str, Any]
    terrain: dict[str, float]
    sounding: list[RecipeSoundingLevel]
    numerical_realization: NumericalRealization
    observation_plan: ObservationPlan
    resolved_cost_profile: RunCostProfile
    differences: list[VariationDifference]
    warnings: list[str]
    blocking_errors: list[str]
    diagnostics: RecipeRegimeDiagnostics
    terrain_profile: list[dict[str, float]]
    wind_profile: list[dict[str, float]]
    moisture_profile: list[dict[str, float]]
    relative_humidity_profile: list[dict[str, float]]
    theta_profile: list[dict[str, float]]
    stability_profile: list[dict[str, float]]


def default_controls(recipe_id: RecipeId) -> MountainWavesRecipeControls:
    if recipe_id == DRY_RECIPE_ID:
        return MountainWavesRecipeControls(recipe_id=recipe_id, dry_ridge=DryRidgeControls())
    return MountainWavesRecipeControls(recipe_id=recipe_id, boulder_moist=BoulderMoistControls())


def recipe_name(recipe_id: RecipeId) -> str:
    return "Dry Ridge Mechanics" if recipe_id == DRY_RECIPE_ID else "Boulder Moist Wave"


def resolve_mountain_waves_recipe(
    *,
    controls: MountainWavesRecipeControls,
    reference_controls: MountainWavesRecipeControls,
    reference_sounding: list[RecipeSoundingLevel],
    catalog_profile: RunCostProfile,
) -> ResolvedMountainWavesRecipe:
    if controls.recipe_id != reference_controls.recipe_id:
        raise ValueError("Variation controls and Recipe reference must use the same Recipe.")
    if catalog_profile.recipe_id != controls.recipe_id:
        raise ValueError("Selected run profile does not belong to this Recipe.")
    if controls.recipe_id == DRY_RECIPE_ID:
        assert controls.dry_ridge is not None
        assert reference_controls.dry_ridge is not None
        return _resolve_dry(controls.dry_ridge, reference_controls.dry_ridge, catalog_profile)
    assert controls.boulder_moist is not None
    assert reference_controls.boulder_moist is not None
    return _resolve_boulder(
        controls.boulder_moist,
        reference_controls.boulder_moist,
        reference_sounding,
        catalog_profile,
    )


def _resolve_dry(
    controls: DryRidgeControls,
    reference: DryRidgeControls,
    profile: RunCostProfile,
) -> ResolvedMountainWavesRecipe:
    role = profile.role
    errors: list[str] = []
    warnings: list[str] = []
    if role == "Extended":
        errors.append(
            "Extended dry-wave runs remain uncharacterized and cannot be packaged until a "
            "bounded reservation is approved."
        )
    dx_m = 200.0 if role == "Quick" else 100.0
    dz_m = 200.0 if role == "Quick" else 100.0
    timestep_s = 2.0 if role == "Quick" else 1.0
    cadence_s = 180 if role == "Quick" else 30 if role == "Presentation" else 60
    cells_per_half_width = controls.ridge_half_width_m / dx_m
    required_cells = 5 if role == "Quick" else 10
    if cells_per_half_width < required_cells:
        errors.append(
            f"The selected profile resolves the ridge with {cells_per_half_width:.1f} cells "
            f"per half-width; {required_cells} are required."
        )

    maximum_slope = _maximum_slope(controls.ridge_height_m, controls.ridge_half_width_m)
    if maximum_slope > 0.50:
        errors.append(
            f"Analytic maximum terrain slope is {maximum_slope:.2f}; the supported maximum is 0.50."
        )
    elif maximum_slope > 0.35:
        warnings.append(
            f"Analytic maximum terrain slope is {maximum_slope:.2f}; terrain-following "
            "compression may be strong."
        )

    lower_n = (
        controls.lower_stability_n_s if controls.layered_stability else controls.dry_stability_n_s
    )
    upper_n = (
        controls.upper_stability_n_s if controls.layered_stability else controls.dry_stability_n_s
    )
    representative_n = max(lower_n, upper_n)
    nh_over_u = representative_n * controls.ridge_height_m / controls.cross_ridge_wind_m_s
    na_over_u = representative_n * controls.ridge_half_width_m / controls.cross_ridge_wind_m_s
    if not 0.1 <= nh_over_u <= 4.0:
        errors.append(f"Nh/U is {nh_over_u:.2f}; the supported interpretation range is 0.1–4.0.")
    if not 0.25 <= na_over_u <= 20.0:
        errors.append(f"Na/U is {na_over_u:.2f}; the supported range is 0.25–20.")

    advective_time = controls.ridge_half_width_m / controls.cross_ridge_wind_m_s
    duration_s = _ceil_to(max(2_160.0, 8.0 * advective_time), cadence_s)
    flow_distance = _maximum_abs_dry_wind(controls) * duration_s
    minimum_span = max(20_000.0, 12.0 * controls.ridge_half_width_m, 1.35 * flow_distance)
    nx = _odd_count(minimum_span, dx_m)
    span_m = (nx - 1) * dx_m
    vertical_wavelength = (
        2.0 * math.pi * controls.cross_ridge_wind_m_s / max(representative_n, 1.0e-6)
    )
    required_top = max(18_000.0, controls.ridge_height_m + 1.5 * vertical_wavelength)
    if required_top > 40_000.0:
        errors.append(
            "The selected wind and stability require a model top above the supported 40 km limit."
        )
    model_top_m = min(40_000.0, _ceil_to(required_top, dz_m))
    nz = max(1, int(round(model_top_m / dz_m)))
    damping_base_m = max(0.7 * model_top_m, model_top_m - 6_000.0)
    periodic_wrap_time = span_m / max(_maximum_abs_dry_wind(controls), 1.0)
    if periodic_wrap_time < 1.2 * duration_s:
        errors.append("Generated domain does not preserve the approved periodic-wrap margin.")

    heights = [index * dz_m for index in range(nz + 2)]
    sounding = _dry_sounding(controls, heights)
    critical_levels = _critical_levels(sounding)
    if critical_levels:
        warnings.append(
            "The authored shear introduces a critical level; wave absorption or breaking "
            "may become central to the result."
        )
    labels = _regime_labels(nh_over_u, na_over_u, critical_levels)
    observation = ObservationPlan(
        duration_seconds=int(duration_s),
        output_cadence_seconds=cadence_s,
        expected_history_count=int(duration_s) // cadence_s + 1,
        retained_field_inventory=profile.observation_plan.retained_field_inventory,
    )
    numerical = NumericalRealization(
        domain=f"{span_m / 1_000.0:.1f} km × {model_top_m / 1_000.0:.1f} km; native 2-D x-z",
        grid=f"{nx} × 1 × {nz}",
        spacing=f"{dx_m:g} × {dz_m:g} m",
        timestep_strategy=f"target {timestep_s:g} s",
        physics_source="Dry Ridge Mechanics analytic generator v1",
    )
    resolved_profile = _resolve_cost_profile(
        profile,
        numerical=numerical,
        observation=observation,
        nominal_cells=200 * 200,
        actual_cells=nx * nz,
        nominal_histories=73 if role == "Presentation" else 37 if role == "Standard" else 13,
    )
    differences = _control_differences(
        controls.model_dump(mode="json"),
        reference.model_dump(mode="json"),
        _DRY_DIFFERENCE_METADATA,
    )
    return ResolvedMountainWavesRecipe(
        recipe_id=DRY_RECIPE_ID,
        recipe_name=recipe_name(DRY_RECIPE_ID),
        controls=controls.model_dump(mode="json"),
        terrain={
            "height_m": controls.ridge_height_m,
            "half_width_m": controls.ridge_half_width_m,
            "center_m": 0.0,
        },
        sounding=sounding,
        numerical_realization=numerical,
        observation_plan=observation,
        resolved_cost_profile=resolved_profile,
        differences=differences,
        warnings=warnings,
        blocking_errors=errors,
        diagnostics=RecipeRegimeDiagnostics(
            maximum_terrain_slope=maximum_slope,
            cells_per_half_width=cells_per_half_width,
            nondimensional_mountain_height=nh_over_u,
            nonhydrostatic_width_parameter=na_over_u,
            critical_levels_m=critical_levels,
            terrain_resolution=f"{cells_per_half_width:.1f} cells per half-width",
            upstream_clearance_km=span_m / 2_000.0,
            downstream_clearance_km=span_m / 2_000.0,
            advective_time_seconds=advective_time,
            periodic_wrap_time_seconds=periodic_wrap_time,
            model_top_m=model_top_m,
            damping_base_m=damping_base_m,
            labels=labels,
        ),
        terrain_profile=_terrain_profile(
            controls.ridge_height_m, controls.ridge_half_width_m, extent_m=span_m / 2.0
        ),
        wind_profile=_profile_values(sounding, "u_m_s"),
        moisture_profile=_profile_values(sounding, "qv_g_kg"),
        relative_humidity_profile=_relative_humidity_values(sounding),
        theta_profile=_profile_values(sounding, "theta_k"),
        stability_profile=_stability_values(sounding),
    )


def _resolve_boulder(
    controls: BoulderMoistControls,
    reference: BoulderMoistControls,
    reference_sounding: list[RecipeSoundingLevel],
    profile: RunCostProfile,
) -> ResolvedMountainWavesRecipe:
    errors: list[str] = []
    warnings: list[str] = []
    if profile.role == "Extended":
        errors.append(
            "Extended Boulder runs remain uncharacterized and cannot be packaged until a "
            "bounded reservation is approved."
        )
    if not reference_sounding:
        errors.append("The source-backed Boulder reference sounding is unavailable.")
        reference_sounding = _fallback_boulder_sounding()
    dx_m = 1_000.0 if profile.role in {"Quick", "Standard", "Extended"} else 500.0
    dz_m = 200.0 if profile.role in {"Quick", "Standard", "Extended"} else 100.0
    timestep_s = 2.0 if profile.role in {"Quick", "Standard", "Extended"} else 1.0
    duration_s = 4_000 if profile.role == "Quick" else 7_200
    cadence_s = 200 if profile.role == "Quick" else 30 if profile.role == "Presentation" else 120

    sounding = _boulder_sounding(reference_sounding, controls)
    if any(not _finite_level(level) for level in sounding):
        errors.append("The transformed Boulder atmosphere contains nonfinite values.")
    if any(level.qv_g_kg < 0.0 for level in sounding):
        errors.append("The transformed Boulder atmosphere contains negative water vapor.")
    stability = _stability_values(sounding)
    if any(item["n2_s2"] <= 0.0 for item in stability):
        errors.append("The transformed Boulder atmosphere is statically unstable.")
    critical_levels = _critical_levels(sounding)
    maximum_wind = max(abs(level.u_m_s) for level in sounding)
    if maximum_wind > 60.0:
        errors.append("The transformed Boulder wind exceeds the supported 60 m/s envelope.")
    if critical_levels:
        warnings.append(
            "The transformed profile contains a critical level; the generated domain and "
            "result should be interpreted as a critical-level experiment."
        )

    representative_n = _representative_n(stability)
    representative_u = max(5.0, _lower_mean_wind(sounding))
    nh_over_u = representative_n * controls.ridge_height_m / representative_u
    na_over_u = representative_n * controls.ridge_half_width_m / representative_u
    maximum_slope = _maximum_slope(controls.ridge_height_m, controls.ridge_half_width_m)
    cells_per_half_width = controls.ridge_half_width_m / dx_m
    minimum_span = max(
        220_000.0,
        12.0 * controls.ridge_half_width_m,
        1.25 * maximum_wind * duration_s,
    )
    nx = _even_count(minimum_span, dx_m)
    span_m = nx * dx_m
    nz = 125 if dz_m == 200.0 else 250
    model_top_m = nz * dz_m
    damping_base_m = 14_000.0
    periodic_wrap_time = span_m / max(maximum_wind, 1.0)
    if periodic_wrap_time < 1.15 * duration_s:
        errors.append("Generated domain does not preserve the approved periodic-wrap margin.")
    if controls.ridge_height_m >= 3_000.0 and maximum_slope > 0.35:
        warnings.append(
            "This high, compact ridge enters a strongly nonlinear terrain-following regime."
        )
    labels = _regime_labels(nh_over_u, na_over_u, critical_levels)
    observation = ObservationPlan(
        duration_seconds=duration_s,
        output_cadence_seconds=cadence_s,
        expected_history_count=duration_s // cadence_s + 1,
        retained_field_inventory=profile.observation_plan.retained_field_inventory,
    )
    numerical = NumericalRealization(
        domain=f"{span_m / 1_000.0:.1f} km × {model_top_m / 1_000.0:.1f} km; native 2-D x-z",
        grid=f"{nx} × 1 × {nz}",
        spacing=f"{dx_m:g} × {dz_m:g} m",
        timestep_strategy=f"target {timestep_s:g} s",
        physics_source="Boulder Moist Wave source-backed generator v1",
    )
    nominal_nx = 440 if profile.role == "Presentation" else 220
    nominal_histories = (
        241 if profile.role == "Presentation" else 21 if profile.role == "Quick" else 61
    )
    resolved_profile = _resolve_cost_profile(
        profile,
        numerical=numerical,
        observation=observation,
        nominal_cells=nominal_nx * nz,
        actual_cells=nx * nz,
        nominal_histories=nominal_histories,
    )
    differences = _control_differences(
        controls.model_dump(mode="json"),
        reference.model_dump(mode="json"),
        _BOULDER_DIFFERENCE_METADATA,
    )
    return ResolvedMountainWavesRecipe(
        recipe_id=BOULDER_RECIPE_ID,
        recipe_name=recipe_name(BOULDER_RECIPE_ID),
        controls=controls.model_dump(mode="json"),
        terrain={
            "height_m": controls.ridge_height_m,
            "half_width_m": controls.ridge_half_width_m,
            "center_m": dx_m / 2.0,
        },
        sounding=sounding,
        numerical_realization=numerical,
        observation_plan=observation,
        resolved_cost_profile=resolved_profile,
        differences=differences,
        warnings=warnings,
        blocking_errors=errors,
        diagnostics=RecipeRegimeDiagnostics(
            maximum_terrain_slope=maximum_slope,
            cells_per_half_width=cells_per_half_width,
            nondimensional_mountain_height=nh_over_u,
            nonhydrostatic_width_parameter=na_over_u,
            critical_levels_m=critical_levels,
            terrain_resolution=f"{cells_per_half_width:.1f} cells per half-width",
            upstream_clearance_km=span_m / 2_000.0,
            downstream_clearance_km=span_m / 2_000.0,
            advective_time_seconds=controls.ridge_half_width_m / representative_u,
            periodic_wrap_time_seconds=periodic_wrap_time,
            model_top_m=model_top_m,
            damping_base_m=damping_base_m,
            labels=labels,
        ),
        terrain_profile=_terrain_profile(
            controls.ridge_height_m, controls.ridge_half_width_m, extent_m=span_m / 2.0
        ),
        wind_profile=_profile_values(sounding, "u_m_s"),
        moisture_profile=_profile_values(sounding, "qv_g_kg"),
        relative_humidity_profile=_relative_humidity_values(sounding),
        theta_profile=_profile_values(sounding, "theta_k"),
        stability_profile=stability,
    )


def _dry_sounding(controls: DryRidgeControls, heights: list[float]) -> list[RecipeSoundingLevel]:
    gravity = 9.81
    cp = 1004.0
    rd = 287.04
    theta_surface = 288.0
    theta_values = [theta_surface]
    exner_values = [1.0]
    for lower, upper in zip(heights, heights[1:], strict=False):
        midpoint = 0.5 * (lower + upper)
        dz = upper - lower
        n = _dry_n_at_height(controls, midpoint)
        theta_next = theta_values[-1] * math.exp(n * n * dz / gravity)
        mean_theta = 0.5 * (theta_values[-1] + theta_next)
        exner_next = exner_values[-1] - gravity * dz / (cp * mean_theta)
        theta_values.append(theta_next)
        exner_values.append(max(exner_next, 0.01))
    sounding: list[RecipeSoundingLevel] = []
    for height, theta, exner in zip(heights, theta_values, exner_values, strict=True):
        shear_fraction = min(max(height / 10_000.0, 0.0), 1.0)
        wind = controls.cross_ridge_wind_m_s + (
            controls.wind_shear_through_10km_m_s * shear_fraction
        )
        sounding.append(
            RecipeSoundingLevel(
                height_m=height,
                pressure_pa=100_000.0 * exner ** (cp / rd),
                theta_k=theta,
                qv_g_kg=0.0,
                u_m_s=wind,
            )
        )
    return sounding


def _dry_n_at_height(controls: DryRidgeControls, height_m: float) -> float:
    if not controls.layered_stability:
        return controls.dry_stability_n_s
    blend = 0.5 * (
        1.0
        + math.tanh(
            (height_m - controls.stability_transition_height_m)
            / controls.stability_transition_width_m
        )
    )
    return controls.lower_stability_n_s * (1.0 - blend) + controls.upper_stability_n_s * blend


def _boulder_sounding(
    reference: list[RecipeSoundingLevel], controls: BoulderMoistControls
) -> list[RecipeSoundingLevel]:
    reference_mean = sum(level.u_m_s for level in reference) / len(reference)
    theta = [reference[0].theta_k]
    for lower, upper in zip(reference, reference[1:], strict=False):
        midpoint = 0.5 * (lower.height_m + upper.height_m)
        factor = (
            controls.lower_stability_factor
            if midpoint < 4_000.0
            else controls.midlevel_stability_factor
            if midpoint < 10_000.0
            else controls.upper_stability_factor
        )
        theta.append(theta[-1] + (upper.theta_k - lower.theta_k) * factor)
    output: list[RecipeSoundingLevel] = []
    for index, source in enumerate(reference):
        wind = (
            controls.flow_strength_factor
            * (reference_mean + controls.shear_strength_factor * (source.u_m_s - reference_mean))
            + controls.wind_offset_m_s
        )
        final_theta = theta[index]
        if controls.dry_air_counterpart:
            qv = 0.0
        else:
            temperature = final_theta * (source.pressure_pa / 100_000.0) ** (287.04 / 1004.0)
            reference_temperature = source.theta_k * (source.pressure_pa / 100_000.0) ** (
                287.04 / 1004.0
            )
            reference_rh = _relative_humidity(
                source.pressure_pa, reference_temperature, source.qv_g_kg
            )
            deficit_factor = (
                controls.lower_rh_deficit_factor
                if source.height_m < 4_000.0
                else controls.midlevel_rh_deficit_factor
                if source.height_m < 10_000.0
                else 1.0
            )
            rh = min(100.0, max(0.0, 100.0 - (100.0 - reference_rh) * deficit_factor))
            qv = _qv_from_rh(source.pressure_pa, temperature, rh)
        output.append(
            RecipeSoundingLevel(
                height_m=source.height_m,
                pressure_pa=source.pressure_pa,
                theta_k=final_theta,
                qv_g_kg=qv,
                u_m_s=wind,
            )
        )
    return output


def _control_differences(
    after: dict[str, Any],
    before: dict[str, Any],
    metadata: dict[str, tuple[str, str, str | None]],
) -> list[VariationDifference]:
    differences: list[VariationDifference] = []
    for key, (category, label, units) in metadata.items():
        if before.get(key) == after.get(key):
            continue
        differences.append(
            VariationDifference(
                category=category,  # type: ignore[arg-type]
                path=f"controls.{key}",
                label=label,
                before=before.get(key),
                after=after.get(key),
                units=units,
            )
        )
    return differences


_DRY_DIFFERENCE_METADATA = {
    "ridge_height_m": ("terrain", "Ridge height", "m"),
    "ridge_half_width_m": ("terrain", "Ridge half-width", "m"),
    "cross_ridge_wind_m_s": ("wind", "Cross-ridge wind", "m/s"),
    "dry_stability_n_s": ("stability_thermodynamics", "Dry stability N", "s^-1"),
    "wind_shear_through_10km_m_s": (
        "wind",
        "Wind change through 10 km",
        "m/s",
    ),
    "layered_stability": (
        "stability_thermodynamics",
        "Layered stability",
        None,
    ),
    "lower_stability_n_s": (
        "stability_thermodynamics",
        "Lower-layer stability N",
        "s^-1",
    ),
    "upper_stability_n_s": (
        "stability_thermodynamics",
        "Upper-layer stability N",
        "s^-1",
    ),
    "stability_transition_height_m": (
        "stability_thermodynamics",
        "Stability transition",
        "m",
    ),
    "stability_transition_width_m": (
        "stability_thermodynamics",
        "Transition width",
        "m",
    ),
}
_BOULDER_DIFFERENCE_METADATA = {
    "ridge_height_m": ("terrain", "Ridge height", "m"),
    "ridge_half_width_m": ("terrain", "Ridge half-width", "m"),
    "flow_strength_factor": ("wind", "Cross-ridge flow strength", "x"),
    "wind_offset_m_s": ("wind", "Wind-profile offset", "m/s"),
    "shear_strength_factor": ("wind", "Shear strength", "x"),
    "lower_rh_deficit_factor": ("moisture", "Lower RH-deficit factor", "x"),
    "midlevel_rh_deficit_factor": ("moisture", "Midlevel RH-deficit factor", "x"),
    "dry_air_counterpart": ("moisture", "Boulder dry-air counterpart", None),
    "lower_stability_factor": (
        "stability_thermodynamics",
        "Lower-layer stability",
        "x",
    ),
    "midlevel_stability_factor": (
        "stability_thermodynamics",
        "Midlevel stability",
        "x",
    ),
    "upper_stability_factor": (
        "stability_thermodynamics",
        "Upper-layer stability",
        "x",
    ),
}


def _resolve_cost_profile(
    profile: RunCostProfile,
    *,
    numerical: NumericalRealization,
    observation: ObservationPlan,
    nominal_cells: int,
    actual_cells: int,
    nominal_histories: int,
) -> RunCostProfile:
    ratio = max(
        1.0,
        (actual_cells / max(nominal_cells, 1))
        * ((observation.expected_history_count or nominal_histories) / max(nominal_histories, 1)),
    )
    low = profile.expected_size_min_bytes
    high = profile.expected_size_max_bytes
    runtime_low = profile.expected_runtime_min_seconds
    runtime_high = profile.expected_runtime_max_seconds
    if low is not None:
        low = max(int(math.ceil(low * ratio)), MIB)
    if high is not None:
        high = max(int(math.ceil(high * ratio)), low or MIB)
    if runtime_low is not None:
        runtime_low = max(1, int(math.ceil(runtime_low * ratio)))
    if runtime_high is not None:
        runtime_high = max(runtime_low or 1, int(math.ceil(runtime_high * ratio)))
    reasons = list(profile.cost_change_reasons)
    if ratio > 1.001:
        reasons.append(
            f"Resolved domain and output inventory are {ratio:.2f}x the nominal retained-cell plan."
        )
    return profile.model_copy(
        update={
            "numerical_realization": numerical,
            "observation_plan": observation,
            "expected_size_min_bytes": low,
            "expected_size_max_bytes": high,
            "expected_runtime_min_seconds": runtime_low,
            "expected_runtime_max_seconds": runtime_high,
            "cost_change_reasons": reasons,
        }
    )


def _terrain_profile(
    height_m: float, half_width_m: float, *, extent_m: float
) -> list[dict[str, float]]:
    points: list[dict[str, float]] = []
    for index in range(121):
        x_m = -extent_m + 2.0 * extent_m * index / 120.0
        points.append(
            {
                "x_m": x_m,
                "height_m": height_m / (1.0 + (x_m / half_width_m) ** 2),
            }
        )
    return points


def _profile_values(
    sounding: list[RecipeSoundingLevel],
    field: Literal["u_m_s", "qv_g_kg", "theta_k"],
) -> list[dict[str, float]]:
    return [
        {"height_m": level.height_m, "value": float(getattr(level, field))} for level in sounding
    ]


def _relative_humidity_values(
    sounding: list[RecipeSoundingLevel],
) -> list[dict[str, float]]:
    return [
        {
            "height_m": level.height_m,
            "value": _relative_humidity(
                level.pressure_pa,
                level.theta_k * (level.pressure_pa / 100_000.0) ** (287.04 / 1004.0),
                level.qv_g_kg,
            ),
        }
        for level in sounding
    ]


def _stability_values(sounding: list[RecipeSoundingLevel]) -> list[dict[str, float]]:
    gravity = 9.81
    values: list[dict[str, float]] = []
    for lower, upper in zip(sounding, sounding[1:], strict=False):
        dz = upper.height_m - lower.height_m
        mean_theta = 0.5 * (lower.theta_k + upper.theta_k)
        n2 = gravity / mean_theta * (upper.theta_k - lower.theta_k) / dz
        values.append({"height_m": 0.5 * (lower.height_m + upper.height_m), "n2_s2": n2})
    return values


def _critical_levels(sounding: list[RecipeSoundingLevel]) -> list[float]:
    levels: list[float] = []
    for lower, upper in zip(sounding, sounding[1:], strict=False):
        if lower.u_m_s == 0.0:
            levels.append(lower.height_m)
        elif lower.u_m_s * upper.u_m_s < 0.0:
            fraction = abs(lower.u_m_s) / (abs(lower.u_m_s) + abs(upper.u_m_s))
            levels.append(lower.height_m + fraction * (upper.height_m - lower.height_m))
    return levels


def _representative_n(stability: list[dict[str, float]]) -> float:
    positive = [math.sqrt(item["n2_s2"]) for item in stability if item["n2_s2"] > 0.0]
    return sum(positive) / len(positive) if positive else 0.0


def _lower_mean_wind(sounding: list[RecipeSoundingLevel]) -> float:
    lower = [abs(level.u_m_s) for level in sounding if level.height_m <= 5_000.0]
    return sum(lower) / len(lower) if lower else 0.0


def _maximum_abs_dry_wind(controls: DryRidgeControls) -> float:
    return max(
        abs(controls.cross_ridge_wind_m_s),
        abs(controls.cross_ridge_wind_m_s + controls.wind_shear_through_10km_m_s),
    )


def _maximum_slope(height_m: float, half_width_m: float) -> float:
    return 9.0 * height_m / (8.0 * math.sqrt(3.0) * half_width_m)


def _regime_labels(nh_over_u: float, na_over_u: float, critical: list[float]) -> list[str]:
    labels = [
        (
            "linear / weakly nonlinear"
            if nh_over_u < 0.5
            else "breaking likely"
            if nh_over_u >= 1.0
            else "nonlinear amplification"
        )
    ]
    if nh_over_u >= 2.0:
        labels.append("blocking likely")
    if na_over_u >= 3.0:
        labels.append("trapped / ducted structure possible")
    if critical:
        labels.append("critical-level interaction")
    return labels


def _relative_humidity(pressure_pa: float, temperature_k: float, qv_g_kg: float) -> float:
    qv = qv_g_kg / 1_000.0
    vapor_pressure = pressure_pa * qv / (0.622 + qv)
    saturation = _saturation_vapor_pressure(temperature_k)
    return 100.0 * vapor_pressure / max(saturation, 1.0)


def _qv_from_rh(pressure_pa: float, temperature_k: float, rh_percent: float) -> float:
    vapor_pressure = min(
        0.99 * pressure_pa,
        max(0.0, rh_percent / 100.0 * _saturation_vapor_pressure(temperature_k)),
    )
    return 1_000.0 * 0.622 * vapor_pressure / max(pressure_pa - vapor_pressure, 1.0)


def _saturation_vapor_pressure(temperature_k: float) -> float:
    temperature_c = temperature_k - 273.15
    return 611.2 * math.exp(17.67 * temperature_c / (temperature_c + 243.5))


def _finite_level(level: RecipeSoundingLevel) -> bool:
    return all(
        math.isfinite(value)
        for value in (
            level.height_m,
            level.pressure_pa,
            level.theta_k,
            level.qv_g_kg,
            level.u_m_s,
        )
    )


def _ceil_to(value: float, increment: float) -> int:
    return int(math.ceil(value / increment) * increment)


def _odd_count(span_m: float, spacing_m: float) -> int:
    count = int(math.ceil(span_m / spacing_m)) + 1
    return count if count % 2 else count + 1


def _even_count(span_m: float, spacing_m: float) -> int:
    count = int(math.ceil(span_m / spacing_m))
    return count if count % 2 == 0 else count + 1


def _fallback_boulder_sounding() -> list[RecipeSoundingLevel]:
    return [
        RecipeSoundingLevel(
            height_m=0.0,
            pressure_pa=100_000.0,
            theta_k=288.0,
            qv_g_kg=8.0,
            u_m_s=10.0,
        ),
        RecipeSoundingLevel(
            height_m=10_000.0,
            pressure_pa=26_000.0,
            theta_k=330.0,
            qv_g_kg=0.5,
            u_m_s=20.0,
        ),
        RecipeSoundingLevel(
            height_m=25_000.0,
            pressure_pa=2_500.0,
            theta_k=470.0,
            qv_g_kg=0.0,
            u_m_s=30.0,
        ),
    ]
