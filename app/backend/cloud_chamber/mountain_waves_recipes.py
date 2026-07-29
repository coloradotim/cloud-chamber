"""Approved Mountain Waves Recipe controls and deterministic generators."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.optimize import least_squares  # type: ignore[import-untyped]

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
RH_LAYER_MEAN_TOLERANCE_PERCENT = 0.05

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
    low_level_wind_m_s: float = Field(default=14.1, ge=0.0, le=50.0)
    shear_through_10km_m_s: float = Field(default=23.8, ge=-30.0, le=50.0)
    lower_layer_rh_percent: float = Field(default=66.0, ge=0.0, le=100.0)
    midlevel_rh_percent: float = Field(default=34.5, ge=0.0, le=100.0)
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
    achieved_controls: dict[str, Any]
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


def normalize_recipe_controls(
    controls: MountainWavesRecipeControls,
    *,
    recipe_reference: MountainWavesRecipeControls | None = None,
) -> MountainWavesRecipeControls:
    """Remove inactive UI state from the effective scientific design."""
    reference = recipe_reference or default_controls(controls.recipe_id)
    if controls.recipe_id != reference.recipe_id:
        raise ValueError("Controls and Recipe reference must use the same Recipe.")
    if controls.recipe_id == DRY_RECIPE_ID:
        assert controls.dry_ridge is not None
        assert reference.dry_ridge is not None
        payload = controls.dry_ridge.model_dump(mode="json")
        if controls.dry_ridge.layered_stability:
            payload["dry_stability_n_s"] = reference.dry_ridge.dry_stability_n_s
        else:
            for field in (
                "lower_stability_n_s",
                "upper_stability_n_s",
                "stability_transition_height_m",
                "stability_transition_width_m",
            ):
                payload[field] = getattr(reference.dry_ridge, field)
        return MountainWavesRecipeControls(
            recipe_id=DRY_RECIPE_ID,
            dry_ridge=DryRidgeControls.model_validate(payload),
        )
    assert controls.boulder_moist is not None
    assert reference.boulder_moist is not None
    payload = controls.boulder_moist.model_dump(mode="json")
    if controls.boulder_moist.dry_air_counterpart:
        payload["lower_layer_rh_percent"] = reference.boulder_moist.lower_layer_rh_percent
        payload["midlevel_rh_percent"] = reference.boulder_moist.midlevel_rh_percent
    return MountainWavesRecipeControls(
        recipe_id=BOULDER_RECIPE_ID,
        boulder_moist=BoulderMoistControls.model_validate(payload),
    )


def resolve_mountain_waves_recipe(
    *,
    controls: MountainWavesRecipeControls,
    reference_controls: MountainWavesRecipeControls,
    difference_reference_controls: MountainWavesRecipeControls | None = None,
    reference_sounding: list[RecipeSoundingLevel],
    catalog_profile: RunCostProfile,
) -> ResolvedMountainWavesRecipe:
    if controls.recipe_id != reference_controls.recipe_id:
        raise ValueError("Variation controls and Recipe reference must use the same Recipe.")
    effective_controls = normalize_recipe_controls(controls, recipe_reference=reference_controls)
    difference_reference = normalize_recipe_controls(
        difference_reference_controls or reference_controls,
        recipe_reference=reference_controls,
    )
    if catalog_profile.recipe_id != controls.recipe_id:
        raise ValueError("Selected run profile does not belong to this Recipe.")
    if effective_controls.recipe_id == DRY_RECIPE_ID:
        assert effective_controls.dry_ridge is not None
        assert reference_controls.dry_ridge is not None
        assert difference_reference.dry_ridge is not None
        return _resolve_dry(
            effective_controls.dry_ridge,
            difference_reference.dry_ridge,
            catalog_profile,
        )
    assert effective_controls.boulder_moist is not None
    assert reference_controls.boulder_moist is not None
    assert difference_reference.boulder_moist is not None
    return _resolve_boulder(
        effective_controls.boulder_moist,
        reference_controls.boulder_moist,
        difference_reference.boulder_moist,
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
    evidence = _cost_evidence_realization(profile.profile_id)
    resolved_profile = _resolve_cost_profile(
        profile,
        numerical=numerical,
        observation=observation,
        evidence_numerical=evidence[0],
        evidence_observation=evidence[1],
        nominal_cells=evidence[2] or 200 * 200,
        actual_cells=nx * nz,
        nominal_histories=(
            evidence[3] or (73 if role == "Presentation" else 37 if role == "Standard" else 13)
        ),
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
        achieved_controls=controls.model_dump(mode="json"),
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
    recipe_reference: BoulderMoistControls,
    difference_reference: BoulderMoistControls,
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

    (
        sounding,
        achieved_lower_rh,
        achieved_midlevel_rh,
        lower_rh_target,
        midlevel_rh_target,
    ) = _boulder_sounding(
        reference_sounding,
        controls,
        recipe_reference,
    )
    (
        _reference_sounding,
        parent_lower_rh,
        parent_midlevel_rh,
        _parent_lower_target,
        _parent_midlevel_target,
    ) = _boulder_sounding(
        reference_sounding,
        difference_reference,
        recipe_reference,
    )
    del _reference_sounding, _parent_lower_target, _parent_midlevel_target
    if not controls.dry_air_counterpart and not _boulder_thermodynamics_unchanged(
        controls, recipe_reference
    ):
        target_checks = (
            ("0–4 km", lower_rh_target, achieved_lower_rh),
            ("4–10 km", midlevel_rh_target, achieved_midlevel_rh),
        )
        for label, target, achieved in target_checks:
            if not math.isclose(
                achieved,
                target,
                rel_tol=0.0,
                abs_tol=RH_LAYER_MEAN_TOLERANCE_PERCENT,
            ):
                errors.append(
                    f"The requested {label} mean RH of {target:.2f}% is not attainable "
                    f"inside the authored smooth-transition envelope; the resolved mean is "
                    f"{achieved:.2f}% (tolerance "
                    f"{RH_LAYER_MEAN_TOLERANCE_PERCENT:.2f} percentage points)."
                )
    if any(not _finite_level(level) for level in sounding):
        errors.append("The transformed Boulder atmosphere contains nonfinite values.")
    if any(level.qv_g_kg < 0.0 for level in sounding):
        errors.append("The transformed Boulder atmosphere contains negative water vapor.")
    if any(
        upper.pressure_pa >= lower.pressure_pa
        for lower, upper in zip(sounding, sounding[1:], strict=False)
    ):
        errors.append(
            "The transformed Boulder hydrostatic pressure profile is not strictly decreasing."
        )
    stability = _stability_values(sounding)
    if any(item["n2_s2"] <= 0.0 for item in stability):
        errors.append("The transformed Boulder atmosphere is statically unstable.")
    critical_levels = _critical_levels(sounding)
    maximum_wind = max(abs(level.u_m_s) for level in sounding)
    if maximum_wind > 125.0:
        errors.append("The transformed Boulder wind exceeds the supported 125 m/s envelope.")
    elif maximum_wind > 80.0:
        warnings.append(
            "The transformed profile contains winds above 80 m/s; generated domain and "
            "cost growth should be reviewed before launch."
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
    vertical_wavelength_m = 2.0 * math.pi * representative_u / max(representative_n, 1.0e-6)
    required_top_m = max(
        25_000.0,
        controls.ridge_height_m + 1.5 * vertical_wavelength_m,
    )
    model_top_m = float(_ceil_to(required_top_m, dz_m))
    if model_top_m > 50_000.0:
        errors.append(
            "The selected wind and stability require a model top above the supported "
            "50 km Boulder envelope."
        )
        model_top_m = 50_000.0
    source_top_m = reference_sounding[-1].height_m
    if model_top_m > source_top_m:
        errors.append(
            f"The generated {model_top_m / 1_000.0:.1f} km model top exceeds the "
            f"{source_top_m / 1_000.0:.1f} km source-backed sounding; this vertical "
            "extension is outside the currently supported Boulder envelope."
        )
    nz = int(round(model_top_m / dz_m))
    damping_depth_m = max(6_000.0, 0.5 * vertical_wavelength_m)
    damping_base_m = model_top_m - damping_depth_m
    minimum_clear_damping_base_m = controls.ridge_height_m + 0.75 * vertical_wavelength_m
    if damping_base_m < minimum_clear_damping_base_m:
        errors.append(
            "The generated model top cannot keep damping above the terrain-forced "
            "wave inspection region."
        )
    if critical_levels:
        lowest_critical_level = min(critical_levels)
        inherited_wind_structure = all(
            math.isclose(actual, reference, rel_tol=0.0, abs_tol=1.0e-12)
            for actual, reference in (
                (controls.low_level_wind_m_s, difference_reference.low_level_wind_m_s),
                (
                    controls.shear_through_10km_m_s,
                    difference_reference.shear_through_10km_m_s,
                ),
            )
        )
        if (
            lowest_critical_level < controls.ridge_height_m + 0.5 * vertical_wavelength_m
            and not inherited_wind_structure
        ):
            errors.append(
                "A critical level falls inside the active terrain-forced wave region; "
                "this interaction is outside the currently supported Boulder envelope."
            )
        elif inherited_wind_structure:
            warnings.append(
                "The retained Boulder source atmosphere contains a critical level; its "
                "inherited wind structure remains visible rather than being treated as "
                "a new control-induced reversal."
            )
        else:
            warnings.append(
                "The transformed profile contains a critical level above the active wave "
                "inspection region; interpret the result as a critical-level experiment."
            )
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
    nominal_nz = 250 if profile.role == "Presentation" else 125
    nominal_histories = (
        241 if profile.role == "Presentation" else 21 if profile.role == "Quick" else 61
    )
    evidence = _cost_evidence_realization(profile.profile_id)
    resolved_profile = _resolve_cost_profile(
        profile,
        numerical=numerical,
        observation=observation,
        evidence_numerical=evidence[0],
        evidence_observation=evidence[1],
        nominal_cells=evidence[2] or nominal_nx * nominal_nz,
        actual_cells=nx * nz,
        nominal_histories=evidence[3] or nominal_histories,
    )
    achieved_controls = controls.model_dump(mode="json")
    achieved_reference = difference_reference.model_dump(mode="json")
    if not controls.dry_air_counterpart:
        achieved_controls["lower_layer_rh_percent"] = round(achieved_lower_rh, 6)
        achieved_controls["midlevel_rh_percent"] = round(achieved_midlevel_rh, 6)
    if not difference_reference.dry_air_counterpart:
        achieved_reference["lower_layer_rh_percent"] = round(parent_lower_rh, 6)
        achieved_reference["midlevel_rh_percent"] = round(parent_midlevel_rh, 6)
    differences = _control_differences(
        achieved_controls,
        achieved_reference,
        _BOULDER_DIFFERENCE_METADATA,
    )
    return ResolvedMountainWavesRecipe(
        recipe_id=BOULDER_RECIPE_ID,
        recipe_name=recipe_name(BOULDER_RECIPE_ID),
        controls=controls.model_dump(mode="json"),
        achieved_controls=achieved_controls,
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
    reference: list[RecipeSoundingLevel],
    controls: BoulderMoistControls,
    reference_controls: BoulderMoistControls,
) -> tuple[list[RecipeSoundingLevel], float, float, float, float]:
    source_low_mean = _layer_mean([level.u_m_s for level in reference if level.height_m < 4_000.0])
    source_shear = _interpolated_wind(reference, 10_000.0) - _interpolated_wind(reference, 0.0)
    target_low_mean = (
        source_low_mean
        if controls.low_level_wind_m_s == reference_controls.low_level_wind_m_s
        else controls.low_level_wind_m_s
    )
    target_shear = (
        source_shear
        if controls.shear_through_10km_m_s == reference_controls.shear_through_10km_m_s
        else controls.shear_through_10km_m_s
    )
    lower_height_fractions = [
        _wind_height_fraction(level.height_m) for level in reference if level.height_m < 4_000.0
    ]
    shear_adjustment = target_shear - source_shear
    profile_translation = (
        target_low_mean - source_low_mean - shear_adjustment * _layer_mean(lower_height_fractions)
    )
    theta = [reference[0].theta_k]
    for lower, upper in zip(reference, reference[1:], strict=False):
        midpoint = 0.5 * (lower.height_m + upper.height_m)
        lower_weight, midlevel_weight, upper_weight = _authored_layer_weights(midpoint)
        factor = (
            lower_weight * controls.lower_stability_factor
            + midlevel_weight * controls.midlevel_stability_factor
            + upper_weight * controls.upper_stability_factor
        )
        theta.append(theta[-1] + (upper.theta_k - lower.theta_k) * factor)
    reference_rh = [
        min(
            100.0,
            max(
                0.0,
                _relative_humidity(
                    level.pressure_pa,
                    level.theta_k * (level.pressure_pa / 100_000.0) ** (287.04 / 1004.0),
                    level.qv_g_kg,
                ),
            ),
        )
        for level in reference
    ]
    lower_indexes = [index for index, level in enumerate(reference) if level.height_m < 4_000.0]
    midlevel_indexes = [
        index for index, level in enumerate(reference) if 4_000.0 <= level.height_m < 10_000.0
    ]
    lower_target = (
        _layer_mean([reference_rh[index] for index in lower_indexes])
        if controls.lower_layer_rh_percent == reference_controls.lower_layer_rh_percent
        else controls.lower_layer_rh_percent
    )
    midlevel_target = (
        _layer_mean([reference_rh[index] for index in midlevel_indexes])
        if controls.midlevel_rh_percent == reference_controls.midlevel_rh_percent
        else controls.midlevel_rh_percent
    )
    adjusted_rh = _rh_profile_for_layer_targets(
        reference_rh,
        [level.height_m for level in reference],
        lower_target=lower_target,
        midlevel_target=midlevel_target,
    )
    thermodynamics_unchanged = _boulder_thermodynamics_unchanged(
        controls,
        reference_controls,
    )
    if thermodynamics_unchanged:
        pressures = [level.pressure_pa for level in reference]
        qv_values = [level.qv_g_kg for level in reference]
    else:
        pressures, qv_values = _hydrostatic_moist_profile(
            heights_m=[level.height_m for level in reference],
            theta_k=theta,
            rh_percent=[0.0 for _ in adjusted_rh] if controls.dry_air_counterpart else adjusted_rh,
            surface_pressure_pa=reference[0].pressure_pa,
        )

    output: list[RecipeSoundingLevel] = []
    for index, source in enumerate(reference):
        wind = (
            source.u_m_s
            + profile_translation
            + shear_adjustment * _wind_height_fraction(source.height_m)
        )
        final_theta = theta[index]
        output.append(
            RecipeSoundingLevel(
                height_m=source.height_m,
                pressure_pa=pressures[index],
                theta_k=final_theta,
                qv_g_kg=qv_values[index],
                u_m_s=wind,
            )
        )
    final_rh = [
        _relative_humidity(
            level.pressure_pa,
            level.theta_k * (level.pressure_pa / 100_000.0) ** (287.04 / 1004.0),
            level.qv_g_kg,
        )
        for level in output
    ]
    achieved_lower_rh = _layer_mean([final_rh[index] for index in lower_indexes])
    achieved_midlevel_rh = _layer_mean([final_rh[index] for index in midlevel_indexes])
    return (
        output,
        achieved_lower_rh,
        achieved_midlevel_rh,
        lower_target,
        midlevel_target,
    )


def _boulder_thermodynamics_unchanged(
    controls: BoulderMoistControls,
    reference_controls: BoulderMoistControls,
) -> bool:
    return (
        all(
            math.isclose(value, reference_value, rel_tol=0.0, abs_tol=1.0e-12)
            for value, reference_value in (
                (controls.lower_stability_factor, reference_controls.lower_stability_factor),
                (controls.midlevel_stability_factor, reference_controls.midlevel_stability_factor),
                (controls.upper_stability_factor, reference_controls.upper_stability_factor),
                (controls.lower_layer_rh_percent, reference_controls.lower_layer_rh_percent),
                (controls.midlevel_rh_percent, reference_controls.midlevel_rh_percent),
            )
        )
        and not controls.dry_air_counterpart
    )


def _wind_height_fraction(height_m: float) -> float:
    return min(max(height_m / 10_000.0, 0.0), 1.0)


def _interpolated_wind(sounding: list[RecipeSoundingLevel], height_m: float) -> float:
    if height_m <= sounding[0].height_m:
        return sounding[0].u_m_s
    for lower, upper in zip(sounding, sounding[1:], strict=False):
        if lower.height_m <= height_m <= upper.height_m:
            fraction = (height_m - lower.height_m) / (upper.height_m - lower.height_m)
            return lower.u_m_s + fraction * (upper.u_m_s - lower.u_m_s)
    return sounding[-1].u_m_s


def _layer_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _authored_layer_weights(height_m: float) -> tuple[float, float, float]:
    lower_to_mid = _smoothstep((height_m - 3_500.0) / 1_000.0)
    mid_to_upper = _smoothstep((height_m - 9_500.0) / 1_000.0)
    lower = 1.0 - lower_to_mid
    upper = mid_to_upper
    midlevel = lower_to_mid * (1.0 - mid_to_upper)
    total = lower + midlevel + upper
    return lower / total, midlevel / total, upper / total


def _smoothstep(value: float) -> float:
    bounded = min(max(value, 0.0), 1.0)
    return bounded * bounded * (3.0 - 2.0 * bounded)


def _rh_profile_for_layer_targets(
    reference_values: list[float],
    heights_m: list[float],
    *,
    lower_target: float,
    midlevel_target: float,
) -> list[float]:
    if len(reference_values) != len(heights_m):
        raise ValueError("RH values and heights must have the same length.")
    lower_indexes = [index for index, height in enumerate(heights_m) if height < 4_000.0]
    midlevel_indexes = [
        index for index, height in enumerate(heights_m) if 4_000.0 <= height < 10_000.0
    ]
    weights = [_authored_layer_weights(height) for height in heights_m]

    def profile(lower_delta: float, midlevel_delta: float) -> list[float]:
        return [
            min(
                100.0,
                max(
                    0.0,
                    reference + lower_delta * layer_weights[0] + midlevel_delta * layer_weights[1],
                ),
            )
            for reference, layer_weights in zip(reference_values, weights, strict=True)
        ]

    if not lower_indexes or not midlevel_indexes:
        raise ValueError("RH target layers must each contain at least one sounding level.")

    def residual(deltas: list[float]) -> list[float]:
        values = profile(float(deltas[0]), float(deltas[1]))
        return [
            _layer_mean([values[index] for index in lower_indexes]) - lower_target,
            _layer_mean([values[index] for index in midlevel_indexes]) - midlevel_target,
        ]

    reference_lower_mean = _layer_mean([reference_values[index] for index in lower_indexes])
    reference_midlevel_mean = _layer_mean([reference_values[index] for index in midlevel_indexes])
    direct_start = (
        lower_target - reference_lower_mean,
        midlevel_target - reference_midlevel_mean,
    )
    starts = (
        (0.0, 0.0),
        direct_start,
        (direct_start[0] * 2.0, direct_start[1] * 2.0),
        (-100.0, -100.0),
        (-100.0, 100.0),
        (100.0, -100.0),
        (100.0, 100.0),
    )
    best_values = profile(*direct_start)
    best_error = sum(value * value for value in residual(list(direct_start)))
    for start in starts:
        result = least_squares(
            residual,
            x0=start,
            bounds=((-2_000.0, -2_000.0), (2_000.0, 2_000.0)),
            ftol=1.0e-12,
            xtol=1.0e-12,
            gtol=1.0e-12,
            max_nfev=1_000,
        )
        values = profile(float(result.x[0]), float(result.x[1]))
        errors = residual([float(result.x[0]), float(result.x[1])])
        error = sum(value * value for value in errors)
        if error < best_error:
            best_values = values
            best_error = error
    return best_values


def _hydrostatic_moist_profile(
    *,
    heights_m: list[float],
    theta_k: list[float],
    rh_percent: list[float],
    surface_pressure_pa: float,
) -> tuple[list[float], list[float]]:
    if not (len(heights_m) == len(theta_k) == len(rh_percent)):
        raise ValueError("Hydrostatic profile inputs must have the same length.")
    pressures = [surface_pressure_pa]
    surface_temperature = theta_k[0] * (surface_pressure_pa / 100_000.0) ** (287.04 / 1004.0)
    qv_values = [_qv_from_rh(surface_pressure_pa, surface_temperature, rh_percent[0])]
    for index in range(1, len(heights_m)):
        dz = heights_m[index] - heights_m[index - 1]
        if dz <= 0.0:
            raise ValueError("Hydrostatic profile heights must increase.")
        lower_pressure = pressures[-1]
        pressure = lower_pressure * math.exp(-9.81 * dz / (287.04 * 280.0))
        upper_qv = 0.0
        for _ in range(24):
            lower_temperature = theta_k[index - 1] * (lower_pressure / 100_000.0) ** (
                287.04 / 1004.0
            )
            upper_temperature = theta_k[index] * (pressure / 100_000.0) ** (287.04 / 1004.0)
            upper_qv = _qv_from_rh(pressure, upper_temperature, rh_percent[index])
            lower_virtual_temperature = lower_temperature * (1.0 + 0.61 * qv_values[-1] / 1_000.0)
            upper_virtual_temperature = upper_temperature * (1.0 + 0.61 * upper_qv / 1_000.0)
            mean_virtual_temperature = 0.5 * (lower_virtual_temperature + upper_virtual_temperature)
            updated = lower_pressure * math.exp(-9.81 * dz / (287.04 * mean_virtual_temperature))
            if math.isclose(updated, pressure, rel_tol=0.0, abs_tol=1.0e-6):
                pressure = updated
                break
            pressure = updated
        pressures.append(pressure)
        qv_values.append(upper_qv)
    return pressures, qv_values


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
    "low_level_wind_m_s": ("wind", "0–4 km mean wind", "m/s"),
    "shear_through_10km_m_s": ("wind", "0–10 km shear", "m/s"),
    "lower_layer_rh_percent": ("moisture", "0–4 km mean RH", "%"),
    "midlevel_rh_percent": ("moisture", "4–10 km mean RH", "%"),
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
    evidence_numerical: NumericalRealization | None,
    evidence_observation: ObservationPlan | None,
    nominal_cells: int,
    actual_cells: int,
    nominal_histories: int,
) -> RunCostProfile:
    raw_ratio = (actual_cells / max(nominal_cells, 1)) * (
        (observation.expected_history_count or nominal_histories) / max(nominal_histories, 1)
    )
    ratio = max(raw_ratio, 0.05)
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
    estimate_basis = profile.estimate_basis
    confidence = profile.confidence
    evidence_matches = (
        evidence_numerical is not None
        and evidence_observation is not None
        and numerical == evidence_numerical
        and observation == evidence_observation
    )
    if not math.isclose(ratio, 1.0, rel_tol=0.0, abs_tol=0.001):
        comparison_basis = (
            "measured retained-cell realization"
            if evidence_numerical is not None and evidence_observation is not None
            else "nominal retained-cell plan"
        )
        reasons.append(
            f"Resolved domain and output inventory are {ratio:.2f}x the {comparison_basis}."
        )
    if estimate_basis == "measured" and not evidence_matches:
        estimate_basis = "scaled_from_measured"
        confidence = (
            "Scaled from the measured reference realization because the generated numerical "
            "realization or observation plan differs."
        )
    return profile.model_copy(
        update={
            "numerical_realization": numerical,
            "observation_plan": observation,
            "expected_size_min_bytes": low,
            "expected_size_max_bytes": high,
            "expected_runtime_min_seconds": runtime_low,
            "expected_runtime_max_seconds": runtime_high,
            "estimate_basis": estimate_basis,
            "confidence": confidence,
            "cost_change_reasons": reasons,
        }
    )


def _cost_evidence_realization(
    profile_id: str,
) -> tuple[NumericalRealization | None, ObservationPlan | None, int, int]:
    evidence: dict[
        str,
        tuple[NumericalRealization, ObservationPlan, int, int],
    ] = {
        "mountain_waves_dry_quick_v1": (
            NumericalRealization(
                domain="20.0 km × 20.0 km; native 2-D x-z",
                grid="100 × 1 × 100",
                spacing="200 × 200 m",
                timestep_strategy="target 2 s",
                physics_source="CM1 r21.1 source-defined dry mountain-wave case",
            ),
            ObservationPlan(
                duration_seconds=2_160,
                output_cadence_seconds=216,
                expected_history_count=11,
                retained_field_inventory=(
                    "zs",
                    "zhval",
                    "th",
                    "prs",
                    "uinterp",
                    "winterp",
                    "w",
                ),
            ),
            100 * 100,
            11,
        ),
        "mountain_waves_dry_presentation_v1": (
            NumericalRealization(
                domain="20.0 km × 20.0 km; native 2-D x-z",
                grid="200 × 1 × 200",
                spacing="100 × 100 m",
                timestep_strategy="target 1 s",
                physics_source="CM1 r21.1 source-defined dry mountain-wave case",
            ),
            ObservationPlan(
                duration_seconds=2_160,
                output_cadence_seconds=30,
                expected_history_count=73,
                retained_field_inventory=(
                    "zs",
                    "zhval",
                    "th",
                    "prs",
                    "uinterp",
                    "winterp",
                    "w",
                ),
            ),
            200 * 200,
            73,
        ),
        "mountain_waves_boulder_quick_v1": (
            NumericalRealization(
                domain="220.0 km × 25.0 km; native 2-D x-z",
                grid="220 × 1 × 125",
                spacing="1000 × 200 m",
                timestep_strategy="target 2 s",
                physics_source="Boulder Moist Wave source-backed generator v1",
            ),
            ObservationPlan(
                duration_seconds=4_000,
                output_cadence_seconds=200,
                expected_history_count=21,
                retained_field_inventory=(
                    "zs",
                    "zhval",
                    "th",
                    "prs",
                    "qv",
                    "ql",
                    "uinterp",
                    "winterp",
                    "w",
                ),
            ),
            220 * 125,
            21,
        ),
        "mountain_waves_boulder_presentation_v1": (
            NumericalRealization(
                domain="220.0 km × 25.0 km; native 2-D x-z",
                grid="440 × 1 × 250",
                spacing="500 × 100 m",
                timestep_strategy="target 1 s",
                physics_source="Boulder Moist Wave source-backed generator v1",
            ),
            ObservationPlan(
                duration_seconds=7_200,
                output_cadence_seconds=30,
                expected_history_count=241,
                retained_field_inventory=(
                    "zs",
                    "zhval",
                    "th",
                    "prs",
                    "qv",
                    "ql",
                    "uinterp",
                    "winterp",
                    "w",
                ),
            ),
            440 * 250,
            241,
        ),
    }
    return evidence.get(profile_id, (None, None, 0, 0))


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
