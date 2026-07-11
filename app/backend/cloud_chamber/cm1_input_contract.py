"""CM1-facing input generation contract.

This module defines deterministic metadata and CM1-facing text for run generation.
It does not launch CM1 and does not write generated files.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from cloud_chamber.observed_sounding import (
    ObservedSoundingLevel,
    ObservedSoundingRecord,
    render_observed_input_sounding,
)
from cloud_chamber.run_configuration import (
    RunConfiguration,
    resolve_run_configuration,
)
from cloud_chamber.scenario_schema import ControlAudience, ScenarioTemplate


class GeneratedFileRole(StrEnum):
    RUN_MANIFEST = "run_manifest"
    CASE_MANIFEST = "case_manifest"
    NAMELIST = "namelist"
    INPUT_SOUNDING = "input_sounding"
    DRY_RUN_REPORT = "dry_run_report"
    RUNTIME_FILE_CHECKLIST = "runtime_file_checklist"


class RunRecipe(StrEnum):
    GENERATED_REFERENCE_LOWER_ATMOSPHERE = "generated_reference_lower_atmosphere"
    UNTRIGGERED_OBSERVED_EVOLUTION = "untriggered_observed_evolution"
    TRIGGERED_DEEP_POTENTIAL = "triggered_deep_potential"


@dataclass(frozen=True)
class CloudScaleDefaults:
    nx: int = 64
    ny: int = 64
    nz: int = 75
    horizontal_extent_km: float = 6.4
    y_extent_km: float = 6.4
    vertical_extent_km: float = 18.0
    horizontal_spacing_m: float = 100.0
    vertical_spacing_m: int = 40
    time_step_seconds: float = 3.0
    runtime_seconds: int = 21600
    output_cadence_seconds: int = 3600
    restart_cadence_seconds: int = 10800
    rayleigh_damping_start_m: int = 2500


@dataclass(frozen=True)
class GeneratedFileSpec:
    role: GeneratedFileRole
    relative_path: str
    description: str
    scientific_status: str


@dataclass(frozen=True)
class ControlMappingFragment:
    control_id: str
    control_label: str
    selected_value: str | float | bool
    audience: ControlAudience
    cm1_mapping_notes: str
    scientific_status: str


@dataclass(frozen=True)
class CM1InputContract:
    run_recipe: RunRecipe
    run_recipe_display_name: str
    recipe_id: str
    recipe_display_name: str
    assumption_set_id: str
    assumption_mode: str
    recipe_assumptions: dict[str, object]
    required_output_fields: tuple[str, ...]
    recipe_caveats: tuple[str, ...]
    input_source: str
    trigger_type: str | None
    trigger_parameters: dict[str, str | int | float | bool]
    scenario_id: str
    physical_question: str
    run_configuration: RunConfiguration
    moisture_profile: str
    stability_profile: str
    cloud_scale_defaults: CloudScaleDefaults
    generated_files: tuple[GeneratedFileSpec, ...]
    control_fragments: tuple[ControlMappingFragment, ...]
    expected_diagnostics: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    visualization_defaults: dict[str, str | list[str]]
    limitations: tuple[str, ...]
    run_caveats: tuple[str, ...]
    manual_validation_status: str
    observed_sounding: ObservedSoundingRecord | None = None


GENERATED_FILE_SPECS = (
    GeneratedFileSpec(
        role=GeneratedFileRole.RUN_MANIFEST,
        relative_path="run_manifest.json",
        description=(
            "Records scenario, controls, generated files, runtime paths, lifecycle state, "
            "and provenance."
        ),
        scientific_status="metadata contract",
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.CASE_MANIFEST,
        relative_path="case_manifest.json",
        description="Scenario-facing case metadata used to review the generated run inputs.",
        scientific_status="metadata contract",
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.NAMELIST,
        relative_path="namelist.input",
        description="CM1 namelist input generated from validated scenario controls.",
        scientific_status=(
            "CM1-ready external-sounding reproduction path derived from the local "
            "CM1 les_ShallowCu example"
        ),
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.INPUT_SOUNDING,
        relative_path="input_sounding",
        description="CM1 sounding/profile input generated from validated scenario controls.",
        scientific_status=(
            "CM1-readable external sounding profile used by the baseline reproduction path"
        ),
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.DRY_RUN_REPORT,
        relative_path="dry_run_report.json",
        description=(
            "Human/reviewable report describing what would be run and what remains unknown."
        ),
        scientific_status="review artifact",
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.RUNTIME_FILE_CHECKLIST,
        relative_path="runtime_file_checklist.json",
        description=(
            "Checklist of external CM1 runtime files required locally, such as LANDUSE.TBL."
        ),
        scientific_status="runtime preflight metadata",
    ),
)


def build_cm1_input_contract(
    scenario: ScenarioTemplate,
    selected_controls: dict[str, str | float | bool] | None = None,
    run_configuration: dict[str, object] | RunConfiguration | None = None,
    observed_sounding: ObservedSoundingRecord | None = None,
    run_recipe: str | RunRecipe | None = None,
) -> CM1InputContract:
    selected = selected_controls or {}
    resolved_run_recipe = _resolve_run_recipe(run_recipe, observed_sounding)
    resolved_run_configuration = resolve_run_configuration(
        run_configuration=run_configuration,
        run_recipe=resolved_run_recipe.value,
    )
    recipe_assumptions = _recipe_assumptions(
        resolved_run_recipe,
        resolved_run_configuration,
    )
    defaults = cloud_scale_defaults_for_configuration(resolved_run_configuration)
    if resolved_run_recipe == RunRecipe.TRIGGERED_DEEP_POTENTIAL:
        if observed_sounding is None:
            raise ValueError("Triggered deep-potential run requires a validated observed sounding.")
        if not _has_observed_wind_profile(
            observed_sounding,
            required_model_top_m=_required_sounding_top_m(defaults),
        ):
            raise ValueError(
                "Triggered deep-potential runs require a complete finite observed u/v wind "
                "profile for every input_sounding level."
            )
    control_fragments = tuple(
        ControlMappingFragment(
            control_id=control.id,
            control_label=control.label,
            selected_value=selected.get(control.id, control.default),
            audience=control.audience,
            cm1_mapping_notes=control.cm1_mapping_notes,
            scientific_status=(
                "product-facing CM1 mapping is provisional until local/manual smoke-run validation"
                if control.audience == ControlAudience.PRODUCT
                else "advanced/developer metadata"
            ),
        )
        for control in scenario.controls
    )

    moisture_profile = _moisture_profile_from_controls(scenario.id, control_fragments)
    stability_profile = _stability_profile_from_controls(scenario.id, control_fragments)

    return CM1InputContract(
        run_recipe=resolved_run_recipe,
        run_recipe_display_name=_run_recipe_display_name(resolved_run_recipe),
        recipe_id=recipe_id_for_run_recipe(resolved_run_recipe),
        recipe_display_name=recipe_display_name_for_run_recipe(resolved_run_recipe),
        assumption_set_id=assumption_set_id_for_run_recipe(resolved_run_recipe),
        assumption_mode=assumption_mode_for_run_recipe(resolved_run_recipe),
        recipe_assumptions=recipe_assumptions,
        required_output_fields=required_output_fields_for_run_recipe(resolved_run_recipe),
        recipe_caveats=recipe_caveats_for_run_recipe(resolved_run_recipe),
        input_source="observed_sounding"
        if observed_sounding is not None
        else "generated_reference",
        trigger_type=(
            "warm_bubble" if resolved_run_recipe == RunRecipe.TRIGGERED_DEEP_POTENTIAL else None
        ),
        trigger_parameters=_trigger_parameters(resolved_run_recipe),
        scenario_id=scenario.id,
        physical_question=scenario.physical_question,
        run_configuration=resolved_run_configuration,
        moisture_profile=moisture_profile,
        stability_profile=stability_profile,
        cloud_scale_defaults=defaults,
        generated_files=GENERATED_FILE_SPECS,
        control_fragments=control_fragments,
        expected_diagnostics=_diagnostic_names(scenario),
        expected_outputs=_expected_outputs(
            resolved_run_recipe,
            resolved_run_configuration.diagnostic_set,
        ),
        visualization_defaults={
            "primary_field": scenario.visualization_defaults.primary_field,
            "secondary_fields": scenario.visualization_defaults.secondary_fields,
            "camera": scenario.visualization_defaults.camera,
            "rendering_method": scenario.visualization_defaults.rendering_method,
            "provenance_label": scenario.visualization_defaults.provenance_label,
        },
        limitations=tuple(scenario.limitations),
        run_caveats=_run_caveats(resolved_run_recipe, resolved_run_configuration),
        manual_validation_status=_manual_validation_status(resolved_run_recipe),
        observed_sounding=observed_sounding,
    )


def cloud_scale_defaults_for_configuration(configuration: RunConfiguration) -> CloudScaleDefaults:
    values = configuration.cm1_values
    return CloudScaleDefaults(
        nx=values.nx,
        ny=values.ny,
        nz=values.nz,
        horizontal_extent_km=values.domain_x_km,
        y_extent_km=values.domain_y_km,
        vertical_extent_km=values.model_top_m / 1000.0,
        horizontal_spacing_m=values.dx_m,
        vertical_spacing_m=int(values.dz_m),
        time_step_seconds=values.time_step_seconds,
        runtime_seconds=values.runtime_seconds,
        output_cadence_seconds=values.output_cadence_seconds,
        restart_cadence_seconds=values.restart_cadence_seconds,
        rayleigh_damping_start_m=values.rayleigh_damping_start_m,
    )


def _resolve_run_recipe(
    run_recipe: str | RunRecipe | None,
    observed_sounding: ObservedSoundingRecord | None,
) -> RunRecipe:
    if isinstance(run_recipe, RunRecipe):
        return run_recipe
    if run_recipe:
        try:
            return RunRecipe(run_recipe)
        except ValueError as exc:
            raise ValueError(f"Unknown run recipe: {run_recipe}") from exc
    if observed_sounding is not None:
        return RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION
    return RunRecipe.GENERATED_REFERENCE_LOWER_ATMOSPHERE


def _run_recipe_display_name(run_recipe: RunRecipe) -> str:
    match run_recipe:
        case RunRecipe.TRIGGERED_DEEP_POTENTIAL:
            return "Triggered Deep-Potential Experiment"
        case RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION:
            return "Untriggered Observed Evolution"
        case RunRecipe.GENERATED_REFERENCE_LOWER_ATMOSPHERE:
            return "Generated Lower-Atmosphere Reference"


def recipe_id_for_run_recipe(run_recipe: str | RunRecipe) -> str:
    resolved = _coerce_run_recipe(run_recipe)
    match resolved:
        case RunRecipe.TRIGGERED_DEEP_POTENTIAL:
            return "triggered_deep_potential_v1"
        case RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION:
            return "untriggered_observed_sounding_evolution_v0"
        case RunRecipe.GENERATED_REFERENCE_LOWER_ATMOSPHERE:
            return "generated_reference_lower_atmosphere_v1"
        case None:
            return str(run_recipe)


def recipe_display_name_for_run_recipe(run_recipe: str | RunRecipe) -> str:
    resolved = _coerce_run_recipe(run_recipe)
    match resolved:
        case RunRecipe.TRIGGERED_DEEP_POTENTIAL:
            return "Triggered Deep-Potential Experiment"
        case RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION:
            return "Untriggered Observed-Sounding Evolution v0"
        case RunRecipe.GENERATED_REFERENCE_LOWER_ATMOSPHERE:
            return "Generated Lower-Atmosphere Reference"
        case None:
            return str(run_recipe)


def assumption_set_id_for_run_recipe(run_recipe: str | RunRecipe) -> str:
    resolved = _coerce_run_recipe(run_recipe)
    match resolved:
        case RunRecipe.TRIGGERED_DEEP_POTENTIAL:
            return "triggered_deep_potential_warm_bubble_v1"
        case RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION:
            return "untriggered_observed_sounding_evolution_v0_assumptions"
        case RunRecipe.GENERATED_REFERENCE_LOWER_ATMOSPHERE:
            return "generated_reference_lower_atmosphere_v1"
        case None:
            return "unknown_assumption_set"


def assumption_mode_for_run_recipe(run_recipe: str | RunRecipe) -> str:
    resolved = _coerce_run_recipe(run_recipe)
    match resolved:
        case RunRecipe.TRIGGERED_DEEP_POTENTIAL:
            return "triggered_deep_potential"
        case RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION:
            return "normal_evolution"
        case RunRecipe.GENERATED_REFERENCE_LOWER_ATMOSPHERE:
            return "generated_reference"
        case None:
            return "unknown"


def required_output_fields_for_run_recipe(run_recipe: str | RunRecipe) -> tuple[str, ...]:
    resolved = _coerce_run_recipe(run_recipe)
    match resolved:
        case RunRecipe.TRIGGERED_DEEP_POTENTIAL:
            return ("qc", "w", "qr", "rain", "dbz", "updraft_helicity")
        case RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION:
            return ("qv", "qc", "w", "qr", "rain", "dbz")
        case RunRecipe.GENERATED_REFERENCE_LOWER_ATMOSPHERE:
            return ("qc", "w")
        case None:
            return ()


def recipe_caveats_for_run_recipe(run_recipe: str | RunRecipe) -> tuple[str, ...]:
    resolved = _coerce_run_recipe(run_recipe)
    match resolved:
        case RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION:
            return (
                "No warm-bubble or artificial deep-convection trigger is applied.",
                (
                    "Surface fluxes use current recipe defaults; they are not validated "
                    "place/time surface-energy inputs."
                ),
                (
                    "Radiation, terrain, GIS surface initialization, and large-scale forcing "
                    "are not part of v0."
                ),
                (
                    "Humid/rainy hypotheses remain partial until rain-water-aloft, "
                    "surface-rain, and reflectivity outputs are present and inspected."
                ),
            )
        case RunRecipe.TRIGGERED_DEEP_POTENTIAL:
            return (
                "The recipe tests triggered potential, not normal atmospheric evolution.",
                "The warm-bubble trigger must be preserved in provenance and Results comparison.",
            )
        case RunRecipe.GENERATED_REFERENCE_LOWER_ATMOSPHERE:
            return ()
        case None:
            return ()


def _coerce_run_recipe(run_recipe: str | RunRecipe) -> RunRecipe | None:
    if isinstance(run_recipe, RunRecipe):
        return run_recipe
    try:
        return RunRecipe(run_recipe)
    except ValueError:
        return None


def _trigger_parameters(
    run_recipe: RunRecipe,
) -> dict[str, str | int | float | bool]:
    if run_recipe != RunRecipe.TRIGGERED_DEEP_POTENTIAL:
        return {}
    return {
        "cm1_iinit": 3,
        "cm1_trigger": (
            "CM1 built-in three warm bubbles with 2 K maximum potential-temperature "
            "perturbations in a line near 1.4 km AGL"
        ),
        "raw_controls_exposed": False,
    }


def _expected_outputs(
    run_recipe: RunRecipe,
    diagnostic_set: str,
) -> tuple[str, ...]:
    base = ("qc", "qr", "qv", "th", "prs", "u", "v", "w", "rain", "dbz")
    analysis = (*base, "psfc", "hfx", "lhfx", "lwp")
    rich = (*analysis, "tke", "km", "kh", "vorticity", "updraft_helicity")
    if diagnostic_set == "essential":
        return base
    if diagnostic_set == "process":
        return analysis
    if run_recipe == RunRecipe.TRIGGERED_DEEP_POTENTIAL:
        return rich
    return rich


def _run_caveats(
    run_recipe: RunRecipe,
    run_configuration: RunConfiguration,
) -> tuple[str, ...]:
    caveats = list(run_configuration.caveats)
    if run_recipe == RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION:
        caveats.extend(recipe_caveats_for_run_recipe(run_recipe))
        return tuple(caveats)
    if run_recipe != RunRecipe.TRIGGERED_DEEP_POTENTIAL:
        return tuple(caveats)
    caveats.extend(
        [
            "Triggered deep-potential runs use an idealized CM1 three-warm-bubble trigger.",
            (
                "Manual smoke evidence applies to the triggered deep-potential recipe; "
                "each observed sounding remains an experiment to evaluate after CM1 completes."
            ),
            (
                "Storm mode, rotation, rain, downdraft, and cold-pool behavior are outcomes "
                "to inspect after the run."
            ),
            "Terrain, mesoscale lift, radiation, and map/GIS forcing are not part of v1.",
        ]
    )
    if "configuration_better_suited_to_larger_compute" in run_configuration.caveats:
        caveats.append(
            "This configuration may be better suited to larger compute; cost/runtime/output "
            "volume should be reviewed before launch."
        )
    return tuple(caveats)


def _manual_validation_status(run_recipe: RunRecipe) -> str:
    if run_recipe == RunRecipe.TRIGGERED_DEEP_POTENTIAL:
        return "triggered_deep_potential_recipe_smoke_validated"
    if run_recipe == RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION:
        return "untriggered_observed_sounding_evolution_v0_metadata_only"
    return "current_run_recipe_path"


def _recipe_assumptions(
    run_recipe: RunRecipe,
    run_configuration: RunConfiguration,
) -> dict[str, object]:
    values = run_configuration.cm1_values
    configured_shape = {
        "duration": {
            "mode": "configured",
            "selection": run_configuration.duration,
            "seconds": values.runtime_seconds,
        },
        "domain": {
            "mode": "configured",
            "selection": run_configuration.domain_size,
            "x_km": values.domain_x_km,
            "y_km": values.domain_y_km,
            "model_top_m": values.model_top_m,
            "horizontal_cell_count": run_configuration.horizontal_cell_count,
            "dx_m": values.dx_m,
            "dy_m": values.dy_m,
        },
        "output_cadence": {
            "mode": "configured",
            "selection": run_configuration.output_cadence,
            "seconds": values.output_cadence_seconds,
        },
        "diagnostic_set": {
            "mode": "configured",
            "selection": run_configuration.diagnostic_set,
        },
    }
    if run_recipe == RunRecipe.UNTRIGGERED_OBSERVED_EVOLUTION:
        return {
            **configured_shape,
            "trigger": {
                "mode": "none",
                "description": "No warm-bubble or artificial deep-convection trigger.",
            },
            "observed_sounding": {
                "temperature_profile": "required",
                "moisture_profile": "required",
                "wind_profile": "used_when_available",
            },
            "surface_fluxes": {
                "mode": "current_recipe_default",
                "description": (
                    "Uniform constant sensible/latent flux proxy inherited from the "
                    "current observed-sounding LES path."
                ),
            },
            "radiation": {"mode": "disabled", "cm1_radopt": 0},
            "large_scale_forcing": {"mode": "none"},
        }
    if run_recipe == RunRecipe.TRIGGERED_DEEP_POTENTIAL:
        return {
            **configured_shape,
            "trigger": {
                "mode": "prescribed",
                "type": "warm_bubble",
                "description": "CM1 built-in three-warm-bubble line initiation.",
            },
            "observed_sounding": {
                "temperature_profile": "required",
                "moisture_profile": "required",
                "wind_profile": "required_complete_finite_uv",
            },
            "surface_fluxes": {"mode": "disabled"},
            "radiation": {"mode": "disabled", "cm1_radopt": 0},
            "large_scale_forcing": {"mode": "none"},
        }
    return {
        **configured_shape,
        "trigger": {"mode": "generated_reference"},
        "surface_fluxes": {"mode": "current_recipe_default"},
        "radiation": {"mode": "disabled", "cm1_radopt": 0},
        "large_scale_forcing": {"mode": "none"},
    }


def _output_switches(
    diagnostic_set: str,
    *,
    deep_convection: bool,
) -> dict[str, int]:
    switches = {
        "sfcflx": 0,
        "sfcparams": 0,
        "sfcdiags": 0,
        "psfc": 0,
        "tke": 0,
        "km": 0,
        "kh": 0,
        "vort": 0,
        "uh": 0,
        "lwp": 0,
    }
    if diagnostic_set in {"process", "full"}:
        switches.update(
            {
                "sfcflx": 1,
                "sfcparams": 1,
                "sfcdiags": 1,
                "psfc": 1,
                "lwp": 1,
            }
        )
    if diagnostic_set == "full" or deep_convection:
        switches.update(
            {
                "tke": 1,
                "km": 1,
                "kh": 1,
                "vort": 1,
                "uh": 1,
            }
        )
    return switches


def _has_observed_wind_profile(
    record: ObservedSoundingRecord,
    *,
    required_model_top_m: float,
) -> bool:
    levels = _rendered_observed_wind_levels(
        record,
        required_model_top_m=required_model_top_m,
    )
    return bool(levels) and all(
        _finite_number(level.u_wind_m_s) and _finite_number(level.v_wind_m_s) for level in levels
    )


def _rendered_observed_wind_levels(
    record: ObservedSoundingRecord,
    *,
    required_model_top_m: float,
) -> list[ObservedSoundingLevel]:
    levels = list(record.levels)
    if not levels:
        return []
    body = list(levels)
    if levels[0].model_z_m <= 0.01:
        body = [level for level in levels if level.model_z_m > 0.01]
        if not body:
            body = list(levels)
    if (
        body
        and math.isfinite(required_model_top_m)
        and required_model_top_m > 0
        and body[-1].model_z_m < required_model_top_m
    ):
        body = [*body, body[-1]]
    return body


def _finite_number(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def render_namelist_fragment(contract: CM1InputContract) -> str:
    return render_cm1_namelist(contract)


def render_cm1_namelist(contract: CM1InputContract) -> str:
    """Render a runnable CM1 namelist for the baseline shallow-cumulus run.

    The recovery baseline follows CM1's local ``les_ShallowCu`` reference case.
    Generated reference runs keep ``isnd = 17`` with the reference wind path.
    Observed-sounding runs use ``isnd = 7`` so CM1 reads the thermodynamic
    and wind profile from ``input_sounding``. The resolved run configuration
    controls runtime, horizontal cells, domain size, saved-output cadence, and
    diagnostic set before CM1 is launched. The intentional
    product-path change outside the sounding source is ``output_format = 2`` so
    Cloud Chamber can ingest NetCDF output when the local CM1 build supports it.
    """

    defaults = contract.cloud_scale_defaults
    sounding_source_id = 7 if contract.observed_sounding is not None else 17
    wind_profile_id = 0 if contract.observed_sounding is not None else 9
    deep_convection = contract.run_recipe == RunRecipe.TRIGGERED_DEEP_POTENTIAL
    testcase = 0 if deep_convection else 3
    adapt_dt = 0 if deep_convection else 1
    ptype = 5
    ihail = 1 if deep_convection else 0
    iautoc = 1 if deep_convection else 0
    icor = 0 if deep_convection else 1
    lspgrad = 0 if deep_convection else 2
    idiss = 1 if deep_convection else 0
    wbc = ebc = sbc = nbc = 2 if deep_convection else 1
    bbc = 1 if deep_convection else 3
    iinit = 3 if deep_convection else 0
    irandp = 0 if deep_convection else 1
    imove = 1 if deep_convection else 0
    output = _output_switches(
        contract.run_configuration.diagnostic_set,
        deep_convection=deep_convection,
    )
    isfcflx = 0 if deep_convection else 1
    sfcmodel = 0 if deep_convection else 1
    oceanmodel = 0 if deep_convection else 1
    set_flx = 0 if deep_convection else 1
    set_ust = 0 if deep_convection else 1
    l_h = 100.0 if deep_convection else 0.0
    lhref1 = 100.0 if deep_convection else 0.0
    lhref2 = 1000.0 if deep_convection else 0.0
    ndcnst = 250.0 if deep_convection else 100.0
    return f"""
 &param0
 nx           =      {defaults.nx},
 ny           =      {defaults.ny},
 nz           =      {defaults.nz},
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =   {_format_cm1_float(defaults.horizontal_spacing_m)},
 dy     =   {_format_cm1_float(defaults.horizontal_spacing_m)},
 dz     =   {float(defaults.vertical_spacing_m):.1f},
 dtl    =   {defaults.time_step_seconds:.3f},
 timax  = {float(defaults.runtime_seconds):.1f},
 run_time =  -999.9,
 tapfrq =  {float(defaults.output_cadence_seconds):.1f},
 rstfrq = {float(defaults.restart_cadence_seconds):.1f},
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  {testcase},
 adapt_dt  =  {adapt_dt},
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  2,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  {ptype},
 ihail     =  {ihail},
 iautoc    =  {iautoc},
 icor      =  {icor},
 lspgrad   =  {lspgrad},
 eqtset    =  2,
 idiss     =  {idiss},
 efall     =  0,
 rterm     =  0,
 wbc       =  {wbc},
 ebc       =  {ebc},
 sbc       =  {sbc},
 nbc       =  {nbc},
 bbc       =  {bbc},
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = {sounding_source_id:2d},
 iwnd      = {wind_profile_id:2d},
 itern     =  0,
 iinit     =  {iinit},
 irandp    =  {irandp},
 ibalance  =  0,
 iorigin   =  2,
 axisymm   =  0,
 imove     =  {imove},
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.376e-4,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  {float(defaults.rayleigh_damping_start_m):.1f},
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      7.0,
 l_h     =  {l_h:7.1f},
 lhref1  =  {lhref1:7.1f},
 lhref2  =  {lhref2:7.1f},
 l_inf   =     75.0,
 ndcnst  =  {ndcnst:7.1f},
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      {isfcflx},
 sfcmodel   =      {sfcmodel},
 oceanmodel =      {oceanmodel},
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      {set_flx},
 cnst_shflx = 8.0e-3,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.00,
 set_ust    =      {set_ust},
 cnst_ust   =   0.28,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      = {float(defaults.vertical_extent_km * 1000):.1f},
 str_bot   =     0.0,
 str_top   =  2000.0,
 dz_bot    =   125.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 2,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sfcflx    = {output["sfcflx"]},
 output_sfcparams = {output["sfcparams"]},
 output_sfcdiags  = {output["sfcdiags"]},
 output_psfc      = {output["psfc"]},
 output_th        = 1,
 output_prs       = 1,
 output_tke       = {output["tke"]},
 output_km        = {output["km"]},
 output_kh        = {output["kh"]},
 output_qv        = 1,
 output_q         = 1,
 output_dbz       = 1,
 output_u         = 1,
 output_uinterp   = 1,
 output_v         = 1,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = {output["vort"]},
 output_uh        = {output["uh"]},
 output_nm        = 1,
 output_def       = 1,
 output_lwp       = {output["lwp"]},
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 /

 &param10
 stat_w        = 1,
 stat_u        = 1,
 stat_v        = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_rh       = 1,
 stat_cloud    = 1,
 stat_cfl      = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_q        = 1,
 prcl_dbz      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 /

 &param20
 do_ib        =    .false.,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 /

 &nssl2mom_params
   alphah  = 0,
   alphahl = 0.5,
   ccn     = 0.6e9,
   cnor    = 8.e6,
   cnoh    = 4.e4,
 /
""".lstrip()


def _format_cm1_float(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    if "." not in text:
        return f"{text}.0"
    return text


def render_input_sounding_notes(contract: CM1InputContract) -> str:
    return render_cm1_input_sounding(contract)


def render_cm1_input_sounding(contract: CM1InputContract) -> str:
    """Render a CM1-readable external sounding profile.

    CM1 observed-sounding runs use ``isnd = 7`` so CM1 reads
    thermodynamics and wind from this file. Generated reference runs use
    the external-sounding profile derived from the BOMEX/Siebesma
    shallow-cumulus breakpoints used by CM1's ``isnd = 19`` reference case.
    """

    if contract.observed_sounding is not None:
        return render_observed_input_sounding(
            contract.observed_sounding,
            required_model_top_m=_required_sounding_top_m(contract.cloud_scale_defaults),
        )

    header, body = _baseline_shallow_cumulus_sounding_profile(
        moisture_profile=contract.moisture_profile,
        stability_profile=contract.stability_profile,
    )
    lines = [
        f"{header[0]:10.2f} {header[1]:12.4f} {header[2]:12.5f}",
    ]
    lines.extend(
        f"{z:10.1f} {theta:12.4f} {qv_gkg:12.5f} {u_ms:8.2f} {v_ms:7.2f}"
        for z, theta, qv_gkg, u_ms, v_ms in body
    )
    return "\n".join(lines) + "\n"


def _required_sounding_top_m(defaults: CloudScaleDefaults) -> float:
    return max(
        float(defaults.vertical_extent_km * 1000.0),
        float(defaults.nz * defaults.vertical_spacing_m),
    )


def _baseline_shallow_cumulus_sounding_profile(
    *,
    moisture_profile: str = "baseline",
    stability_profile: str = "baseline",
) -> tuple[
    tuple[float, float, float],
    tuple[tuple[float, float, float, float, float], ...],
]:
    """Return BOMEX-like external-sounding rows for the les_ShallowCu baseline.

    The first row is the CM1 input_sounding header:
    surface pressure (mb), surface theta (K), surface qv (g/kg).

    Subsequent rows are z (m), theta (K), qv (g/kg), u (m/s), v (m/s). CM1's
    external reader expects mixing ratio in g/kg. The isnd=19 shallow-cumulus
    reference stores moisture breakpoints as specific humidity, so these rows
    convert those breakpoints to mixing ratio before writing the file.
    """

    surface_specific_humidity = _adjust_specific_humidity(0.0170, 0.0, moisture_profile)
    header = (
        1015.0,
        298.7,
        _specific_humidity_to_mixing_ratio_gkg(surface_specific_humidity),
    )
    levels = (
        (
            0.0,
            _adjust_potential_temperature(298.7, 0.0, stability_profile),
            _specific_humidity_to_mixing_ratio_gkg(
                _adjust_specific_humidity(0.0170, 0.0, moisture_profile)
            ),
            _bomex_u_wind(0.0),
            0.0,
        ),
        (
            520.0,
            _adjust_potential_temperature(298.7, 520.0, stability_profile),
            _specific_humidity_to_mixing_ratio_gkg(
                _adjust_specific_humidity(0.0163, 520.0, moisture_profile)
            ),
            _bomex_u_wind(520.0),
            0.0,
        ),
        (
            700.0,
            _adjust_potential_temperature(
                _interpolate(700.0, 520.0, 1480.0, 298.7, 302.4),
                700.0,
                stability_profile,
            ),
            _specific_humidity_to_mixing_ratio_gkg(
                _adjust_specific_humidity(
                    _interpolate(700.0, 520.0, 1480.0, 0.0163, 0.0107),
                    700.0,
                    moisture_profile,
                )
            ),
            _bomex_u_wind(700.0),
            0.0,
        ),
        (
            1480.0,
            _adjust_potential_temperature(302.4, 1480.0, stability_profile),
            _specific_humidity_to_mixing_ratio_gkg(
                _adjust_specific_humidity(0.0107, 1480.0, moisture_profile)
            ),
            _bomex_u_wind(1480.0),
            0.0,
        ),
        (
            2000.0,
            _adjust_potential_temperature(308.2, 2000.0, stability_profile),
            _specific_humidity_to_mixing_ratio_gkg(
                _adjust_specific_humidity(0.0042, 2000.0, moisture_profile)
            ),
            _bomex_u_wind(2000.0),
            0.0,
        ),
        (
            3000.0,
            _adjust_potential_temperature(311.85, 3000.0, stability_profile),
            _specific_humidity_to_mixing_ratio_gkg(
                _adjust_specific_humidity(0.0030, 3000.0, moisture_profile)
            ),
            _bomex_u_wind(3000.0),
            0.0,
        ),
        (
            6000.0,
            _adjust_potential_temperature(330.0, 6000.0, stability_profile),
            _adjust_mixing_ratio_gkg(1.0, 6000.0, moisture_profile),
            _bomex_u_wind(6000.0),
            0.0,
        ),
        (
            7000.0,
            _adjust_potential_temperature(340.0, 7000.0, stability_profile),
            _adjust_mixing_ratio_gkg(0.5, 7000.0, moisture_profile),
            _bomex_u_wind(7000.0),
            0.0,
        ),
        (20000.0, 430.0, 0.01, _bomex_u_wind(20000.0), 0.0),
    )
    return header, levels


def _moisture_profile_from_controls(
    scenario_id: str,
    control_fragments: tuple[ControlMappingFragment, ...],
) -> str:
    selected = _selected_control_value(control_fragments, "low_level_humidity")
    if scenario_id == "dry-failed-cumulus":
        return "dry_failed" if selected == "drier" else "baseline"
    if scenario_id == "baseline-shallow-cumulus" and selected in {"drier", "more_humid"}:
        return str(selected)
    return "baseline"


def _stability_profile_from_controls(
    scenario_id: str,
    control_fragments: tuple[ControlMappingFragment, ...],
) -> str:
    selected = _selected_control_value(control_fragments, "cap_strength")
    if scenario_id == "capped-suppressed-cumulus" and selected == "stronger":
        return "stronger_cap"
    return "baseline"


def _selected_control_value(
    control_fragments: tuple[ControlMappingFragment, ...], control_id: str
) -> str | float | bool | None:
    for fragment in control_fragments:
        if fragment.control_id == control_id:
            return fragment.selected_value
    return None


def _adjust_specific_humidity(
    specific_humidity: float,
    height_m: float,
    moisture_profile: str,
) -> float:
    return specific_humidity * _moisture_scale(height_m, moisture_profile)


def _adjust_mixing_ratio_gkg(
    mixing_ratio_gkg: float,
    height_m: float,
    moisture_profile: str,
) -> float:
    return mixing_ratio_gkg * _moisture_scale(height_m, moisture_profile)


def _moisture_scale(height_m: float, moisture_profile: str) -> float:
    low_level_scales = {
        "drier": (0.82, 0.95),
        "baseline": (1.0, 1.0),
        "more_humid": (1.08, 1.02),
        "dry_failed": (0.45, 0.75),
    }
    low_scale, upper_scale = low_level_scales.get(moisture_profile, low_level_scales["baseline"])
    if height_m <= 3000.0:
        return low_scale
    if height_m >= 6000.0:
        return upper_scale
    return _interpolate(height_m, 3000.0, 6000.0, low_scale, upper_scale)


def _adjust_potential_temperature(
    potential_temperature_k: float,
    height_m: float,
    stability_profile: str,
) -> float:
    return potential_temperature_k + _cap_temperature_increment(height_m, stability_profile)


def _cap_temperature_increment(height_m: float, stability_profile: str) -> float:
    if stability_profile != "stronger_cap":
        return 0.0
    if height_m <= 520.0:
        return 0.0
    if height_m <= 1480.0:
        return _interpolate(height_m, 520.0, 1480.0, 0.0, 1.8)
    if height_m <= 2000.0:
        return _interpolate(height_m, 1480.0, 2000.0, 1.8, 2.4)
    if height_m <= 3000.0:
        return _interpolate(height_m, 2000.0, 3000.0, 2.4, 0.0)
    return 0.0


def _specific_humidity_to_mixing_ratio_gkg(specific_humidity: float) -> float:
    return 1000.0 * specific_humidity / (1.0 - specific_humidity)


def _interpolate(
    value: float,
    low_value: float,
    high_value: float,
    low_result: float,
    high_result: float,
) -> float:
    fraction = (value - low_value) / (high_value - low_value)
    return low_result + fraction * (high_result - low_result)


def _bomex_u_wind(height_m: float) -> float:
    if height_m <= 700.0:
        return -8.75
    if height_m >= 3000.0:
        return -4.61
    return _interpolate(height_m, 700.0, 3000.0, -8.75, -4.61)


def _diagnostic_names(scenario: ScenarioTemplate) -> tuple[str, ...]:
    diagnostics = scenario.expected_diagnostics
    names = []
    if diagnostics.cloud_formed:
        names.append("cloud_formed")
    for field_name in [
        "first_cloud_time",
        "cloud_base_top",
        "max_updraft",
        "cloud_water_summary",
        "rain_onset",
    ]:
        if getattr(diagnostics, field_name) is not None:
            names.append(field_name)
    return tuple(names)
