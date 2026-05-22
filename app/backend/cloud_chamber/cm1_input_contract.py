"""CM1-facing input generation contract.

This module defines deterministic metadata and CM1-facing text for package generation.
It does not launch CM1 and does not write generated files.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cloud_chamber.scenario_schema import ControlAudience, ScenarioTemplate


class GeneratedFileRole(StrEnum):
    RUN_MANIFEST = "run_manifest"
    CASE_MANIFEST = "case_manifest"
    NAMELIST = "namelist"
    INPUT_SOUNDING = "input_sounding"
    DRY_RUN_REPORT = "dry_run_report"
    RUNTIME_FILE_CHECKLIST = "runtime_file_checklist"


@dataclass(frozen=True)
class CloudScaleDefaults:
    horizontal_extent_km: int = 16
    y_extent_km: int = 16
    vertical_extent_km: int = 6
    horizontal_spacing_m: int = 200
    vertical_spacing_m: int = 125
    runtime_seconds: int = 7200
    output_cadence_seconds: int = 300


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
    scenario_id: str
    physical_question: str
    run_size_preset: str
    cloud_scale_defaults: CloudScaleDefaults
    generated_files: tuple[GeneratedFileSpec, ...]
    control_fragments: tuple[ControlMappingFragment, ...]
    expected_diagnostics: tuple[str, ...]
    visualization_defaults: dict[str, str | list[str]]
    limitations: tuple[str, ...]


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
        scientific_status="CM1-ready provisional baseline derived from local CM1 BOMEX example",
    ),
    GeneratedFileSpec(
        role=GeneratedFileRole.INPUT_SOUNDING,
        relative_path="input_sounding",
        description="CM1 sounding/profile input generated from validated scenario controls.",
        scientific_status="CM1-readable provisional profile; baseline namelist uses built-in BOMEX",
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
) -> CM1InputContract:
    selected = selected_controls or {}
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

    return CM1InputContract(
        scenario_id=scenario.id,
        physical_question=scenario.physical_question,
        run_size_preset=run_size_preset,
        cloud_scale_defaults=CloudScaleDefaults(),
        generated_files=GENERATED_FILE_SPECS,
        control_fragments=control_fragments,
        expected_diagnostics=_diagnostic_names(scenario),
        visualization_defaults={
            "primary_field": scenario.visualization_defaults.primary_field,
            "secondary_fields": scenario.visualization_defaults.secondary_fields,
            "camera": scenario.visualization_defaults.camera,
            "rendering_method": scenario.visualization_defaults.rendering_method,
            "provenance_label": scenario.visualization_defaults.provenance_label,
        },
        limitations=tuple(scenario.limitations),
    )


def render_namelist_fragment(contract: CM1InputContract) -> str:
    return render_cm1_namelist(contract)


def render_cm1_namelist(contract: CM1InputContract) -> str:
    """Render a runnable CM1 namelist for the baseline shallow-cumulus package.

    The first baseline uses CM1's built-in BOMEX shallow-cumulus analytic profile
    (`testcase = 3`, `isnd = 19`) from the local CM1 reference case. The grid/runtime
    are adjusted to Cloud Chamber's quick-look cloud-scale starting point.
    """

    defaults = contract.cloud_scale_defaults
    nx = int(defaults.horizontal_extent_km * 1000 / defaults.horizontal_spacing_m)
    ny = int(defaults.y_extent_km * 1000 / defaults.horizontal_spacing_m)
    nz = int(defaults.vertical_extent_km * 1000 / defaults.vertical_spacing_m)
    return f"""
 &param0
 nx           =      {nx},
 ny           =      {ny},
 nz           =      {nz},
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =   {float(defaults.horizontal_spacing_m):.1f},
 dy     =   {float(defaults.horizontal_spacing_m):.1f},
 dz     =   {float(defaults.vertical_spacing_m):.1f},
 dtl    =   3.000,
 timax  = {float(defaults.runtime_seconds):.1f},
 run_time =  -999.9,
 tapfrq =  {float(defaults.output_cadence_seconds):.1f},
 rstfrq = -3600.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  3,
 adapt_dt  =  1,
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
 ptype     =  5,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  2,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = 19,
 iwnd      =  9,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
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
 zd      =  2500.0,
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
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
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
 set_flx    =      1,
 cnst_shflx = 8.0e-3,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.00,
 set_ust    =      1,
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
 ztop      =  {float(defaults.vertical_extent_km * 1000):.1f},
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
 output_format    = 1,
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


def render_input_sounding_notes(contract: CM1InputContract) -> str:
    return render_cm1_input_sounding(contract)


def render_cm1_input_sounding(contract: CM1InputContract) -> str:
    """Render a CM1-readable external sounding profile.

    The current baseline namelist uses CM1's built-in BOMEX sounding (`isnd = 19`),
    so CM1 will not read this file for the first smoke run. We still generate a
    numeric CM1/WRF-format profile so package preflight can reject notes-only
    artifacts and future external-sounding experiments have a concrete starting point.
    """

    del contract
    lines = [
        "1015.0 298.7 17.0",
        "0.0 298.7 17.0 -8.75 0.0",
        "520.0 298.7 16.3 -8.75 0.0",
        "1480.0 302.4 10.7 -8.75 0.0",
        "2000.0 308.2 4.2 -8.75 0.0",
        "3000.0 311.8 3.0 -8.75 0.0",
        "6000.0 330.0 1.0 -8.75 0.0",
        "7000.0 340.0 0.5 -8.75 0.0",
    ]
    return "\n".join(lines) + "\n"


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
