"""CM1-facing input generation contract.

This module defines deterministic metadata and CM1-facing text for package generation.
It does not launch CM1 and does not write generated files.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cloud_chamber.observed_sounding import ObservedSoundingRecord, render_observed_input_sounding
from cloud_chamber.scenario_schema import ControlAudience, ScenarioTemplate


class GeneratedFileRole(StrEnum):
    RUN_MANIFEST = "run_manifest"
    CASE_MANIFEST = "case_manifest"
    NAMELIST = "namelist"
    INPUT_SOUNDING = "input_sounding"
    DRY_RUN_REPORT = "dry_run_report"
    RUNTIME_FILE_CHECKLIST = "runtime_file_checklist"


class PackageFamily(StrEnum):
    SHALLOW_CUMULUS = "shallow_cumulus"
    OBSERVED_SOUNDING_QUICKLOOK = "observed_sounding_quicklook"
    DEEP_CONVECTION_TRIAL = "deep_convection_trial"


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
class RuntimePreset:
    runtime_seconds: int
    output_cadence_seconds: int
    nx: int = 64
    ny: int = 64
    horizontal_spacing_m: float = 100.0
    time_step_seconds: float = 3.0


RUNTIME_PRESETS: dict[str, RuntimePreset] = {
    "quick_look": RuntimePreset(runtime_seconds=10800, output_cadence_seconds=900),
    "standard": RuntimePreset(runtime_seconds=21600, output_cadence_seconds=3600),
    "deep_overnight": RuntimePreset(
        runtime_seconds=21600,
        output_cadence_seconds=300,
        nx=192,
        ny=192,
        horizontal_spacing_m=100.0 * 64.0 / 192.0,
    ),
}


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
    package_family: PackageFamily
    package_display_name: str
    input_source: str
    trigger_type: str | None
    trigger_parameters: dict[str, str | int | float | bool]
    scenario_id: str
    physical_question: str
    run_size_preset: str
    moisture_profile: str
    stability_profile: str
    cloud_scale_defaults: CloudScaleDefaults
    generated_files: tuple[GeneratedFileSpec, ...]
    control_fragments: tuple[ControlMappingFragment, ...]
    expected_diagnostics: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    visualization_defaults: dict[str, str | list[str]]
    limitations: tuple[str, ...]
    package_caveats: tuple[str, ...]
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
        description="Scenario-facing case metadata used to review the generated package.",
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
    run_size_preset: str = "quick_look",
    observed_sounding: ObservedSoundingRecord | None = None,
    package_family: str | PackageFamily | None = None,
) -> CM1InputContract:
    selected = selected_controls or {}
    resolved_package_family = _resolve_package_family(package_family, observed_sounding)
    if resolved_package_family == PackageFamily.DEEP_CONVECTION_TRIAL:
        if observed_sounding is None:
            raise ValueError("Deep Convection Trial requires a validated observed sounding.")
        if not _has_observed_wind_profile(observed_sounding):
            raise ValueError("Deep Convection Trial requires observed wind components.")
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
        package_family=resolved_package_family,
        package_display_name=_package_display_name(resolved_package_family),
        input_source="observed_sounding"
        if observed_sounding is not None
        else "generated_reference",
        trigger_type=(
            "warm_thermal_line"
            if resolved_package_family == PackageFamily.DEEP_CONVECTION_TRIAL
            else None
        ),
        trigger_parameters=_trigger_parameters(resolved_package_family),
        scenario_id=scenario.id,
        physical_question=scenario.physical_question,
        run_size_preset=run_size_preset,
        moisture_profile=moisture_profile,
        stability_profile=stability_profile,
        cloud_scale_defaults=cloud_scale_defaults_for_preset(
            run_size_preset,
            package_family=resolved_package_family,
        ),
        generated_files=GENERATED_FILE_SPECS,
        control_fragments=control_fragments,
        expected_diagnostics=_diagnostic_names(scenario),
        expected_outputs=_expected_outputs(resolved_package_family),
        visualization_defaults={
            "primary_field": scenario.visualization_defaults.primary_field,
            "secondary_fields": scenario.visualization_defaults.secondary_fields,
            "camera": scenario.visualization_defaults.camera,
            "rendering_method": scenario.visualization_defaults.rendering_method,
            "provenance_label": scenario.visualization_defaults.provenance_label,
        },
        limitations=tuple(scenario.limitations),
        package_caveats=_package_caveats(resolved_package_family, run_size_preset),
        manual_validation_status=_manual_validation_status(resolved_package_family),
        observed_sounding=observed_sounding,
    )


def cloud_scale_defaults_for_preset(
    run_size_preset: str,
    *,
    package_family: str | PackageFamily | None = None,
) -> CloudScaleDefaults:
    resolved = _resolve_package_family(package_family, None)
    if resolved == PackageFamily.DEEP_CONVECTION_TRIAL:
        return _deep_convection_defaults_for_preset(run_size_preset)
    preset = RUNTIME_PRESETS.get(run_size_preset, RUNTIME_PRESETS["standard"])
    return CloudScaleDefaults(
        nx=preset.nx,
        ny=preset.ny,
        horizontal_spacing_m=preset.horizontal_spacing_m,
        time_step_seconds=preset.time_step_seconds,
        runtime_seconds=preset.runtime_seconds,
        output_cadence_seconds=preset.output_cadence_seconds,
    )


def _deep_convection_defaults_for_preset(run_size_preset: str) -> CloudScaleDefaults:
    if run_size_preset == "deep_overnight":
        return CloudScaleDefaults(
            nx=240,
            ny=240,
            horizontal_extent_km=48.0,
            y_extent_km=48.0,
            horizontal_spacing_m=200.0,
            runtime_seconds=21600,
            output_cadence_seconds=300,
            restart_cadence_seconds=10800,
            rayleigh_damping_start_m=15000,
        )
    if run_size_preset == "standard":
        return CloudScaleDefaults(
            nx=160,
            ny=160,
            horizontal_extent_km=40.0,
            y_extent_km=40.0,
            horizontal_spacing_m=250.0,
            runtime_seconds=21600,
            output_cadence_seconds=600,
            restart_cadence_seconds=10800,
            rayleigh_damping_start_m=15000,
        )
    return CloudScaleDefaults(
        nx=96,
        ny=96,
        horizontal_extent_km=24.0,
        y_extent_km=24.0,
        horizontal_spacing_m=250.0,
        runtime_seconds=10800,
        output_cadence_seconds=600,
        restart_cadence_seconds=5400,
        rayleigh_damping_start_m=15000,
    )


def _resolve_package_family(
    package_family: str | PackageFamily | None,
    observed_sounding: ObservedSoundingRecord | None,
) -> PackageFamily:
    if isinstance(package_family, PackageFamily):
        return package_family
    if package_family:
        try:
            return PackageFamily(package_family)
        except ValueError as exc:
            raise ValueError(f"Unknown package family: {package_family}") from exc
    if observed_sounding is not None:
        return PackageFamily.OBSERVED_SOUNDING_QUICKLOOK
    return PackageFamily.SHALLOW_CUMULUS


def _package_display_name(package_family: PackageFamily) -> str:
    match package_family:
        case PackageFamily.DEEP_CONVECTION_TRIAL:
            return "Deep Convection Trial"
        case PackageFamily.OBSERVED_SOUNDING_QUICKLOOK:
            return "Observed Sounding Quick Look"
        case PackageFamily.SHALLOW_CUMULUS:
            return "Shallow Cumulus Package"


def _trigger_parameters(
    package_family: PackageFamily,
) -> dict[str, str | int | float | bool]:
    if package_family != PackageFamily.DEEP_CONVECTION_TRIAL:
        return {}
    return {
        "cm1_iinit": 8,
        "cm1_trigger": (
            "CM1 built-in line thermal with small random perturbations; 2 K maximum "
            "potential-temperature perturbation centered near 1.5 km AGL"
        ),
        "raw_controls_exposed": False,
    }


def _expected_outputs(package_family: PackageFamily) -> tuple[str, ...]:
    base = ("qc", "qr", "qv", "th", "prs", "u", "v", "w", "rain", "dbz")
    if package_family == PackageFamily.DEEP_CONVECTION_TRIAL:
        return (*base, "tke", "km", "kh", "vorticity", "updraft_helicity")
    return base


def _package_caveats(package_family: PackageFamily, run_size_preset: str) -> tuple[str, ...]:
    if package_family != PackageFamily.DEEP_CONVECTION_TRIAL:
        return ()
    caveats = [
        "Deep Convection Trial uses an idealized CM1 warm line-thermal trigger.",
        (
            "Storm mode, rotation, rain, downdraft, and cold-pool behavior are outcomes "
            "to inspect after the run."
        ),
        "Terrain, mesoscale lift, radiation, and map/GIS forcing are not part of v1.",
    ]
    if run_size_preset in {"standard", "deep_overnight"}:
        caveats.append(
            "This preset is intended for the LAN worker unless local performance is acceptable."
        )
    return tuple(caveats)


def _manual_validation_status(package_family: PackageFamily) -> str:
    if package_family == PackageFamily.DEEP_CONVECTION_TRIAL:
        return "needs_manual_cm1_smoke_run"
    return "existing_package_path"


def _has_observed_wind_profile(record: ObservedSoundingRecord) -> bool:
    return any(
        level.u_wind_m_s is not None and level.v_wind_m_s is not None for level in record.levels
    )


def render_namelist_fragment(contract: CM1InputContract) -> str:
    return render_cm1_namelist(contract)


def render_cm1_namelist(contract: CM1InputContract) -> str:
    """Render a runnable CM1 namelist for the baseline shallow-cumulus package.

    The recovery baseline follows CM1's local ``les_ShallowCu`` reference case.
    Generated reference packages keep ``isnd = 17`` with the reference wind path.
    Observed-sounding packages use ``isnd = 7`` so CM1 reads the thermodynamic
    and wind profile from ``input_sounding``. Run-size presets adjust runtime,
    saved-output cadence, and, for Deep Overnight, horizontal grid spacing while
    preserving the physical domain and Standard solver timestep. The intentional
    product-path change outside the sounding source is ``output_format = 2`` so
    Cloud Chamber can ingest NetCDF output when the local CM1 build supports it.
    """

    defaults = contract.cloud_scale_defaults
    sounding_source_id = 7 if contract.observed_sounding is not None else 17
    wind_profile_id = 0 if contract.observed_sounding is not None else 9
    deep_convection = contract.package_family == PackageFamily.DEEP_CONVECTION_TRIAL
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
    iinit = 8 if deep_convection else 0
    irandp = 0 if deep_convection else 1
    isfcflx = 0 if deep_convection else 1
    sfcmodel = 0 if deep_convection else 1
    oceanmodel = 0 if deep_convection else 1
    set_flx = 0 if deep_convection else 1
    set_ust = 0 if deep_convection else 1
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
 imove     =  0,
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
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
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
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_th        = 1,
 output_prs       = 1,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_q         = 1,
 output_dbz       = 1,
 output_u         = 1,
 output_uinterp   = 1,
 output_v         = 1,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 1,
 output_uh        = 1,
 output_nm        = 1,
 output_def       = 1,
 output_lwp       = 1,
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

    CM1 documents ``isnd = 17`` as the external ``input_sounding`` route that
    reads thermodynamics from this file while preserving the namelist wind
    profile. The profile is derived from the BOMEX/Siebesma shallow-cumulus
    breakpoints used by CM1's ``isnd = 19`` reference case and extends above the
    18 km model top as required by CM1's input_sounding reader.
    """

    if contract.observed_sounding is not None:
        return render_observed_input_sounding(contract.observed_sounding)

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
