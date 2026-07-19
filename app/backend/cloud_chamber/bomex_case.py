"""Deterministic packaging and evidence extraction for the canonical BOMEX case."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber import __version__
from cloud_chamber.result_diagnostics import QC_CLOUD_THRESHOLD_KG_KG
from cloud_chamber.result_ingest import ResultMetadata
from cloud_chamber.run_manifest import (
    AppMetadata,
    GeneratedInputs,
    LifecycleState,
    ProductState,
    ProvenanceMetadata,
    RunManifest,
    RuntimePaths,
    ScenarioReference,
    UserMetadata,
    ValidationStatus,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings, discover_cm1

CASE_ID = "bomex_trade_cumulus_baseline_v0"
MAPPING_VERSION = "bomex_cm1_mapping_v1"
SMOKE_DURATION_SECONDS = 600
FULL_DURATION_SECONDS = 21_600
OUTPUT_CADENCE_SECONDS = 300
DIAGNOSTIC_CADENCE_SECONDS = 60
CM1_RELEASE = "21.1"
CM1_TAG_COMMIT = "0f734f64efa89a684963a66d2ac32db67617912b"
CM1_SOURCE_MANIFEST_SHA256 = "fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e"
CM1_README_NAMELIST_SHA256 = "7b95be56db51f5c9396c59dca252cf96b918a312cc70107451f91149a34ab3b5"
CM1_EXECUTABLE_SHA256 = "5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1"
CM1_BOMEX_NAMELIST_SHA256 = "4aa2f7cfad8c918801e0768c2618a37740e3966bc8f47205e5fafda3e506f965"
CM1_BOMEX_README_SHA256 = "368c6ca53445f920f0e89d6e4273111f0378785e393e1efa63a7758f2dc5ae56"
SCIENTIFIC_SOURCE_DOI = "https://doi.org/10.1175/1520-0469(2003)60%3C1201:ALESIS%3E2.0.CO;2"
SCIENTIFIC_SOURCE_RECORD = "https://pure.mpg.de/view/item_995314"
CM1_SOURCE_TAG = "https://github.com/NCAR/CM1/tree/21.1"

CRITICAL_SOURCE_HASHES = {
    "src/adv_routines.F": "265723c8b19e300592ddbad3839ee689aa4933ac2f0ae236c61f4d5d40ef7f00",
    "src/base.F": "9c88a1021ddde22d02680786246c52bcffb040cbd72c3c4708f24fe24eec32ef",
    "src/domaindiag.F": "a926b4938c6b576e2ec634c14dbf177f8bdcc557ddefa3b8155326e5f8ef7dff",
    "src/init3d.F": "9c45c0982ba194ea6ea74afd6a2516445cdd011fc90902091d089f4cb92dfd28",
    "src/kessler.F": "f232f840e425d8c9abd28841e0a46a06e0dbf641460224fa61b6a82e5a650472",
    "src/mp_driver.F": "f70684282df49338dbb6336c7f3ca538c66e8cc99933fe5fb52325303c394134",
    "src/param.F": "cac64a6cb4363c6b88367b5cb9391f1bcf2130c63ffedef6e5973c03b190c349",
    "src/sfcphys.F": "7cb54de579b8bb038285430890e075ab19ed2e6d93158bd50d656209d64696a7",
    "src/solve1.F": "515346f18268aea39e7a919536ee6187386e5db6d184e6e4c597509c701e2076",
    "src/testcase_simple_phys.F": (
        "ce0a74ba558634cf712669aae3cbee2eafeb4e23a116e0fe3d819886938ffc72"
    ),
}

REQUIRED_OUTPUT_FIELDS = (
    "ql",
    "qv",
    "th",
    "prs",
    "u",
    "v",
    "w",
    "tke",
    "kmh",
    "khh",
    "cwp",
    "hfx",
    "qfx",
    "rain",
)

REQUIRED_OUTPUT_SWITCHES = {
    "output_format": "2",
    "output_filetype": "2",
    "output_rain": "1",
    "output_sfcflx": "1",
    "output_sfcparams": "1",
    "output_sfcdiags": "1",
    "output_th": "1",
    "output_prs": "1",
    "output_rho": "1",
    "output_tke": "1",
    "output_km": "1",
    "output_kh": "1",
    "output_qv": "1",
    "output_q": "1",
    "output_u": "1",
    "output_v": "1",
    "output_w": "1",
    "output_pwat": "1",
    "output_lwp": "1",
}

_COMMON_NAMELIST_OVERRIDES = {
    "tapfrq": f"{OUTPUT_CADENCE_SECONDS}.0",
    "rstfrq": "86400.0",
    "statfrq": f"{DIAGNOSTIC_CADENCE_SECONDS}.0",
    "testcase": "3",
    "adapt_dt": "1",
    "ptype": "6",
    "iautoc": "0",
    "efall": "0",
    "isnd": "19",
    "iwnd": "9",
    "iinit": "0",
    "irandp": "1",
    "v_t": "0.0",
    "ztop": "3000.0",
    "output_format": "2",
    "output_filetype": "2",
    "output_interp": "0",
    "output_dbz": "0",
    "output_uinterp": "0",
    "output_vinterp": "0",
    "output_winterp": "0",
    "output_rho": "1",
    "output_pwat": "1",
    "output_lwp": "1",
    "output_thbudget": "0",
    "output_qvbudget": "0",
    "output_ubudget": "0",
    "output_vbudget": "0",
    "output_wbudget": "0",
    "dodomaindiag": ".true.",
    "diagfrq": f"{DIAGNOSTIC_CADENCE_SECONDS}.0",
}

_PROFILE_HEIGHTS_M = (0.0, 300.0, 500.0, 520.0, 700.0, 1480.0, 1500.0, 2000.0, 2100.0, 3000.0)
_THETA_L_KNOTS = ((0.0, 298.7), (520.0, 298.7), (1480.0, 302.4), (2000.0, 308.2), (3000.0, 311.85))
_QT_G_KG_KNOTS = ((0.0, 17.0), (520.0, 16.3), (1480.0, 10.7), (2000.0, 4.2), (3000.0, 3.0))
_U_M_S_KNOTS = ((0.0, -8.75), (700.0, -8.75), (3000.0, -4.61))


class BomexCaseError(RuntimeError):
    """Raised when BOMEX package or evidence generation cannot proceed."""


class BomexVariant(StrEnum):
    SMOKE = "smoke"
    FULL = "full"

    @property
    def duration_seconds(self) -> int:
        if self is BomexVariant.SMOKE:
            return SMOKE_DURATION_SECONDS
        return FULL_DURATION_SECONDS


class CM1Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    release: str
    official_tag_commit: str
    official_source_tag: str
    source_tree_path: str
    run_directory_path: str
    executable_path: str
    executable_sha256: str
    readme_namelist_path: str
    readme_namelist_sha256: str
    source_manifest_method: str
    source_manifest_sha256: str
    critical_source_sha256: dict[str, str]
    bundled_bomex_namelist_path: str
    bundled_bomex_namelist_sha256: str
    bundled_bomex_readme_path: str
    bundled_bomex_readme_sha256: str


@dataclass(frozen=True)
class BomexPackageResult:
    run_id: str
    variant: BomexVariant
    package_dir: Path
    manifest_path: Path
    case_manifest_path: Path
    generated_files: tuple[Path, ...]


class BomexRunEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_version: str = "bomex_run_evidence_v1"
    case_id: str = CASE_ID
    run_id: str
    result_id: str
    variant: str
    duration_seconds: int
    output_cadence_seconds: int
    wall_clock_seconds: float | None = None
    model_output_count: int
    expected_model_output_count: int
    netcdf_output_bytes: int
    runtime_integrity_state: str
    runtime_integrity_reason: str
    available_model_fields: list[str]
    missing_required_fields: list[str]
    field_non_finite_counts: dict[str, int]
    first_output_time_seconds: float | None = None
    last_output_time_seconds: float | None = None
    cloud_formed: bool | None = None
    first_cloud_time_seconds: float | None = None
    cloud_base_m: float | None = None
    cloud_top_m: float | None = None
    max_cloud_liquid_kg_kg: float | None = None
    max_updraft_m_s: float | None = None
    min_downdraft_m_s: float | None = None
    max_surface_rain: float | None = None
    mean_total_cloud_cover_final_three_hours_percent: float | None = None
    peak_cloud_fraction_final_three_hours_percent: float | None = None
    mean_lwp_final_three_hours_kg_m2: float | None = None
    max_lwp_kg_m2: float | None = None
    lwp_cycle_peak_count: int
    liquid_water_path_source_field: str = "cwp"
    cm1_lwp_field_status: str = "unusable_without_rain_allocation"
    forcing_diagnostic_fields: dict[str, dict[str, float | None]]
    resolved_turbulent_flux_fields: list[str]
    final_domain_mean_profiles: dict[str, list[float | None]] = Field(default_factory=dict)
    final_profile_height_m: list[float | None] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2) + "\n"


def collect_cm1_provenance(settings: CloudChamberSettings) -> CM1Provenance:
    """Verify the configured executable and scientific source against pinned CM1 r21.1."""
    discovery = discover_cm1(settings)
    if not discovery.ready or settings.cm1_root is None or settings.cm1_run_dir is None:
        detail = "; ".join(discovery.missing)
        raise BomexCaseError(f"Configured CM1 runtime is not ready: {detail}")

    root = settings.cm1_root.resolve()
    run_dir = settings.cm1_run_dir.resolve()
    executable = run_dir / "cm1.exe"
    readme_namelist = root / "README.namelist"
    bundled_dir = run_dir / "config_files" / "les_ShallowCu"
    bundled_namelist = bundled_dir / "namelist.input"
    bundled_readme = bundled_dir / "README"

    expected_files = {
        executable: CM1_EXECUTABLE_SHA256,
        readme_namelist: CM1_README_NAMELIST_SHA256,
        bundled_namelist: CM1_BOMEX_NAMELIST_SHA256,
        bundled_readme: CM1_BOMEX_README_SHA256,
        **{root / relative: expected for relative, expected in CRITICAL_SOURCE_HASHES.items()},
    }
    mismatches: list[str] = []
    for path, expected in expected_files.items():
        if not path.is_file():
            mismatches.append(f"missing:{path}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            mismatches.append(f"sha256_mismatch:{path.name}:{actual}")

    source_manifest_hash = source_manifest_sha256(root)
    if source_manifest_hash != CM1_SOURCE_MANIFEST_SHA256:
        mismatches.append(f"source_manifest_sha256_mismatch:{source_manifest_hash}")
    if mismatches:
        raise BomexCaseError(
            "Configured CM1 provenance does not match the pinned r21.1 evidence: "
            + "; ".join(mismatches)
        )

    return CM1Provenance(
        release=CM1_RELEASE,
        official_tag_commit=CM1_TAG_COMMIT,
        official_source_tag=CM1_SOURCE_TAG,
        source_tree_path=str(root),
        run_directory_path=str(run_dir),
        executable_path=str(executable),
        executable_sha256=CM1_EXECUTABLE_SHA256,
        readme_namelist_path=str(readme_namelist),
        readme_namelist_sha256=CM1_README_NAMELIST_SHA256,
        source_manifest_method=(
            "sha256 each sorted src/*.F line as '<sha256>  src/<name>\\n', then sha256 manifest"
        ),
        source_manifest_sha256=source_manifest_hash,
        critical_source_sha256=dict(CRITICAL_SOURCE_HASHES),
        bundled_bomex_namelist_path=str(bundled_namelist),
        bundled_bomex_namelist_sha256=CM1_BOMEX_NAMELIST_SHA256,
        bundled_bomex_readme_path=str(bundled_readme),
        bundled_bomex_readme_sha256=CM1_BOMEX_README_SHA256,
    )


def source_manifest_sha256(cm1_root: Path) -> str:
    source_paths = sorted((cm1_root / "src").glob("*.F"), key=lambda path: path.name)
    if not source_paths:
        raise BomexCaseError(f"No original CM1 src/*.F files found under {cm1_root}")
    lines = [
        f"{sha256_file(path)}  {path.relative_to(cm1_root).as_posix()}\n" for path in source_paths
    ]
    return sha256_text("".join(lines))


def render_bomex_namelist(reference_text: str, variant: BomexVariant) -> str:
    """Render the pinned CM1 BOMEX namelist with explicit Stage 4 translations."""
    rendered = reference_text
    overrides = {**_COMMON_NAMELIST_OVERRIDES, "timax": f"{variant.duration_seconds}.0"}
    for name, value in overrides.items():
        rendered = _replace_namelist_assignment(rendered, name, value)
    for name, value in REQUIRED_OUTPUT_SWITCHES.items():
        rendered = _replace_namelist_assignment(rendered, name, value)
    return rendered.rstrip() + "\n"


def normalized_science_namelist(namelist_text: str) -> str:
    """Normalize the sole smoke/full science difference for equivalence checks."""
    return _replace_namelist_assignment(namelist_text, "timax", "<duration_seconds>")


def render_profile_audit() -> str:
    """Render a deterministic WRF-format audit of the canonical initial profile."""
    lines = ["  1015.0000   298.7000   17.000000"]
    for height in _PROFILE_HEIGHTS_M:
        theta_l = _linear_profile_value(height, _THETA_L_KNOTS)
        qt = _linear_profile_value(height, _QT_G_KG_KNOTS)
        u = _linear_profile_value(height, _U_M_S_KNOTS)
        lines.append(f"  {height:9.4f}  {theta_l:9.4f}  {qt:10.6f}  {u:9.4f}  {0.0:9.4f}")
    return "\n".join(lines) + "\n"


def generate_bomex_package(
    *,
    settings: CloudChamberSettings,
    variant: BomexVariant,
    run_id: str,
    allow_overwrite: bool = False,
    app_commit: str | None = None,
) -> BomexPackageResult:
    """Generate a deterministic, provenance-rich BOMEX runtime package."""
    provenance = collect_cm1_provenance(settings)
    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    if package_dir.exists():
        if not allow_overwrite:
            raise BomexCaseError(f"Run package already exists: {package_dir}")
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)

    paths = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "namelist": package_dir / "namelist.input",
        "input_sounding": package_dir / "input_sounding",
        "report": package_dir / "dry_run_report.json",
        "runtime_checklist": package_dir / "runtime_file_checklist.json",
    }
    reference_namelist = Path(provenance.bundled_bomex_namelist_path).read_text()
    namelist_text = render_bomex_namelist(reference_namelist, variant)
    profile_text = render_profile_audit()
    runtime_checklist = {
        "status": "external_runtime_files_not_committed",
        "required_files": ["LANDUSE.TBL"],
        "source_candidates": {
            "LANDUSE.TBL": ["config_files/les_ShallowCu/LANDUSE.TBL", "LANDUSE.TBL"]
        },
        "notes": "Stage the CM1 r21.1 bundled shallow-cumulus runtime table.",
    }
    paths["namelist"].write_text(namelist_text)
    paths["input_sounding"].write_text(profile_text)
    _write_json(paths["runtime_checklist"], runtime_checklist)

    generated_hashes = {
        "namelist.input": sha256_text(namelist_text),
        "input_sounding": sha256_text(profile_text),
        "runtime_file_checklist.json": sha256_file(paths["runtime_checklist"]),
    }
    science_settings_hash = sha256_text(normalized_science_namelist(namelist_text))
    case_manifest = _case_manifest_payload(
        variant=variant,
        provenance=provenance,
        generated_hashes=generated_hashes,
        science_settings_hash=science_settings_hash,
    )
    _write_json(paths["case_manifest"], case_manifest)
    generated_hashes["case_manifest.json"] = sha256_file(paths["case_manifest"])

    now = datetime.now(UTC)
    resolved_commit = app_commit if app_commit is not None else _git_commit()
    run_configuration: dict[str, Any] = {
        "case_id": CASE_ID,
        "mapping_version": MAPPING_VERSION,
        "variant": variant.value,
        "duration_seconds": variant.duration_seconds,
        "output_cadence_seconds": OUTPUT_CADENCE_SECONDS,
        "diagnostic_cadence_seconds": DIAGNOSTIC_CADENCE_SECONDS,
        "expected_model_output_count": variant.duration_seconds // OUTPUT_CADENCE_SECONDS + 1,
        "domain": {
            "nx": 64,
            "ny": 64,
            "nz": 75,
            "dx_m": 100.0,
            "dy_m": 100.0,
            "dz_m": 40.0,
            "model_top_m": 3000.0,
        },
        "time_step": {"target_seconds": 3.0, "adaptive": True},
        "microphysics": {
            "ptype": 6,
            "terminal_velocity_m_s": 0.0,
            "precipitation_treatment": "reversible_moist_thermodynamics_no_fallout",
            "cloud_liquid_output_field": "ql",
        },
        "scientific_sources": [SCIENTIFIC_SOURCE_DOI, SCIENTIFIC_SOURCE_RECORD],
        "cm1_provenance": provenance.model_dump(mode="json"),
        "generated_input_sha256": dict(generated_hashes),
        "generated_forcing_input_sha256": {},
        "science_settings_sha256": science_settings_hash,
        "case_manifest_path": str(paths["case_manifest"]),
        "approximations": [
            "cm1_analytic_isnd19_iwnd9_testcase3_instead_of_external_case_files",
            "prescribed_radiative_tendency_not_interactive_radiation",
            "cm1_specific_upper_rayleigh_damping_above_2500m",
            "ql_mapped_to_cloud_chamber_canonical_cloud_liquid_diagnostics",
        ],
        "unsupported_components": [],
    }
    manifest = RunManifest(
        run_id=run_id,
        scenario=ScenarioReference(id=CASE_ID, schema_version=MAPPING_VERSION),
        controls={"variant": variant.value},
        run_configuration=run_configuration,
        physical_question=(
            "Can the canonical steady nonprecipitating BOMEX setup produce a recognizable, "
            "watchable, locally practical trade-cumulus field in configured CM1 r21.1?"
        ),
        expected_diagnostics=[
            "cloud_liquid_and_lwp",
            "cloud_fraction_by_height_and_time",
            "cloud_base_and_top_evolution",
            "vertical_velocity",
            "domain_mean_thermodynamic_profiles",
            "surface_and_resolved_turbulent_fluxes",
            "large_scale_forcing_profiles",
            "runtime_integrity_and_non_finite_scan",
        ],
        generated_inputs=GeneratedInputs(
            run_directory=str(package_dir),
            manifest_path=str(paths["manifest"]),
            namelist_input=str(paths["namelist"]),
            input_sounding=str(paths["input_sounding"]),
            dry_run_report=str(paths["report"]),
            runtime_file_checklist=[str(paths["runtime_checklist"])],
        ),
        runtime_paths=RuntimePaths(runtime_home=str(settings.runtime_home.expanduser())),
        app=AppMetadata(app_version=__version__, commit=resolved_commit),
        lifecycle_state=LifecycleState.PACKAGED,
        validation_status=ValidationStatus.VALID,
        provenance=ProvenanceMetadata(product_state=ProductState.PACKAGED_DRY_RUN_OUTPUT),
        created_at=now,
        updated_at=now,
        user=UserMetadata(name=f"Canonical BOMEX baseline ({variant.value})"),
        run_recipe=None,
        required_output_fields=list(REQUIRED_OUTPUT_FIELDS),
        input_source="canonical_bomex_analytic_case",
        expected_outputs=["cm1_model_netcdf", "cm1_domain_diagnostic_netcdf"],
        run_limitations=[
            "stage4_evidence_only_not_product_recipe",
            "single_cm1_les_translation_not_all_model_intercomparison",
        ],
        run_caveats=list(run_configuration["approximations"]),
        manual_validation_status="stage4_evidence_pending",
    )
    write_run_manifest(paths["manifest"], manifest)
    report = {
        "status": "packaged_not_executed",
        "case_id": CASE_ID,
        "mapping_version": MAPPING_VERSION,
        "variant": variant.value,
        "run_id": run_id,
        "generated_input_sha256": generated_hashes,
        "science_settings_sha256": science_settings_hash,
        "cm1_release": provenance.release,
        "cm1_executable_sha256": provenance.executable_sha256,
        "source_manifest_sha256": provenance.source_manifest_sha256,
        "required_output_fields": list(REQUIRED_OUTPUT_FIELDS),
        "run_recipe": None,
        "notes": "Generated package is configured run evidence, not scientific success.",
    }
    _write_json(paths["report"], report)
    return BomexPackageResult(
        run_id=run_id,
        variant=variant,
        package_dir=package_dir,
        manifest_path=paths["manifest"],
        case_manifest_path=paths["case_manifest"],
        generated_files=tuple(paths.values()),
    )


def build_bomex_run_evidence(
    result: ResultMetadata,
    *,
    wall_clock_seconds: float | None = None,
) -> BomexRunEvidence:
    """Build bounded BOMEX science/process evidence from an ingested result."""
    config = result.run_configuration
    variant = str(config.get("variant", "unknown"))
    duration_seconds = int(config.get("duration_seconds", 0))
    expected_count = int(config.get("expected_model_output_count", 0))
    required_missing = _missing_required_fields(result.variables)
    paths = [Path(path) for path in result.model_output_paths]
    frame_metrics, non_finite_counts, final_profiles, final_heights = _model_frame_evidence(paths)
    final_three_hour = [
        frame
        for frame in frame_metrics
        if frame["time_seconds"] is not None and frame["time_seconds"] >= 10_800.0
    ]
    lwp_values = [
        float(frame["mean_lwp"]) for frame in frame_metrics if frame["mean_lwp"] is not None
    ]
    diag_summary, flux_fields = _diagnostic_evidence(
        [Path(path) for path in result.netcdf_paths if "cm1out_diag_" in Path(path).name]
    )
    diagnostics = result.diagnostics
    cloud = diagnostics.cloud if diagnostics is not None else None
    vertical_velocity = diagnostics.vertical_velocity if diagnostics is not None else None
    surface_rain = diagnostics.surface_rain if diagnostics is not None else None
    caveats: list[str] = [
        "cm1_cwp_used_as_liquid_water_path_for_nonprecipitating_ptype6",
        "cm1_lwp_unusable_without_rain_allocation",
    ]
    caveats.extend(result.runtime_integrity.caveats)
    if not final_three_hour and variant == BomexVariant.FULL.value:
        caveats.append("final_three_hour_evidence_unavailable")
    if required_missing:
        caveats.append("required_output_fields_missing")
    if not diag_summary:
        caveats.append("forcing_diagnostic_fields_unavailable")

    return BomexRunEvidence(
        run_id=result.run_id,
        result_id=result.result_id,
        variant=variant,
        duration_seconds=duration_seconds,
        output_cadence_seconds=int(config.get("output_cadence_seconds", 0)),
        wall_clock_seconds=wall_clock_seconds,
        model_output_count=result.model_output_file_count,
        expected_model_output_count=expected_count,
        netcdf_output_bytes=sum(path.stat().st_size for path in map(Path, result.netcdf_paths)),
        runtime_integrity_state=result.runtime_integrity.state,
        runtime_integrity_reason=result.runtime_integrity.reason,
        available_model_fields=sorted(result.variables),
        missing_required_fields=required_missing,
        field_non_finite_counts=non_finite_counts,
        first_output_time_seconds=result.first_output_time_seconds,
        last_output_time_seconds=result.last_output_time_seconds,
        cloud_formed=cloud.formed if cloud is not None else None,
        first_cloud_time_seconds=cloud.first_cloud_time_seconds if cloud is not None else None,
        cloud_base_m=cloud.cloud_base_m if cloud is not None else None,
        cloud_top_m=cloud.cloud_top_m if cloud is not None else None,
        max_cloud_liquid_kg_kg=cloud.max_qc_kg_kg if cloud is not None else None,
        max_updraft_m_s=(vertical_velocity.max_w_m_s if vertical_velocity is not None else None),
        min_downdraft_m_s=(vertical_velocity.min_w_m_s if vertical_velocity is not None else None),
        max_surface_rain=(surface_rain.max_surface_rain if surface_rain is not None else None),
        mean_total_cloud_cover_final_three_hours_percent=_mean_metric(
            final_three_hour, "total_cloud_cover_percent"
        ),
        peak_cloud_fraction_final_three_hours_percent=_max_metric(
            final_three_hour, "peak_cloud_fraction_percent"
        ),
        mean_lwp_final_three_hours_kg_m2=_mean_metric(final_three_hour, "mean_lwp"),
        max_lwp_kg_m2=max(lwp_values) if lwp_values else None,
        lwp_cycle_peak_count=_local_peak_count(lwp_values),
        forcing_diagnostic_fields=diag_summary,
        resolved_turbulent_flux_fields=flux_fields,
        final_domain_mean_profiles=final_profiles,
        final_profile_height_m=final_heights,
        caveats=caveats,
    )


def write_bomex_run_evidence(path: Path, evidence: BomexRunEvidence) -> None:
    path.write_text(evidence.to_json_text())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _case_manifest_payload(
    *,
    variant: BomexVariant,
    provenance: CM1Provenance,
    generated_hashes: dict[str, str],
    science_settings_hash: str,
) -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "mapping_version": MAPPING_VERSION,
        "authority_state": "stage4_candidate_evidence_not_product_recipe",
        "variant": variant.value,
        "duration_seconds": variant.duration_seconds,
        "scientific_sources": [SCIENTIFIC_SOURCE_DOI, SCIENTIFIC_SOURCE_RECORD],
        "canonical_definition": {
            "domain_grid": {
                "nx": 64,
                "ny": 64,
                "nz": 75,
                "dx_m": 100.0,
                "dy_m": 100.0,
                "dz_m": 40.0,
            },
            "surface_fluxes": {
                "sensible_heat_flux_k_m_s": 8.0e-3,
                "moisture_flux_g_g_m_s": 5.2e-5,
                "friction_velocity_m_s": 0.28,
            },
            "coriolis_s_1": 0.376e-4,
            "nonprecipitating": True,
        },
        "cm1_translation": {
            "testcase": 3,
            "isnd": 19,
            "iwnd": 9,
            "ptype": 6,
            "v_t_m_s": 0.0,
            "cloud_liquid_output_field": "ql",
            "output_format": "netcdf",
            "output_cadence_seconds": OUTPUT_CADENCE_SECONDS,
            "diagnostic_cadence_seconds": DIAGNOSTIC_CADENCE_SECONDS,
        },
        "cm1_provenance": provenance.model_dump(mode="json"),
        "generated_input_sha256": generated_hashes,
        "generated_forcing_input_sha256": {},
        "science_settings_sha256": science_settings_hash,
        "approximations": [
            "analytic_cm1_bomex_source_capability",
            "prescribed_radiative_tendency",
            "cm1_upper_rayleigh_damping",
            "cloud_fraction_derived_from_ql_threshold",
        ],
        "unsupported_components": [],
    }


def _replace_namelist_assignment(text: str, name: str, value: str) -> str:
    pattern = re.compile(
        rf"^(?P<prefix>\s*{re.escape(name)}\s*=\s*)(?P<value>[^,!\n]+)(?P<suffix>\s*,.*)$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise BomexCaseError(
            f"Expected exactly one {name!r} assignment in pinned BOMEX namelist; "
            f"found {len(matches)}."
        )
    return pattern.sub(rf"\g<prefix>{value}\g<suffix>", text, count=1)


def _linear_profile_value(height_m: float, knots: tuple[tuple[float, float], ...]) -> float:
    for (lower_z, lower_value), (upper_z, upper_value) in zip(knots, knots[1:], strict=False):
        if height_m <= upper_z:
            fraction = (height_m - lower_z) / (upper_z - lower_z)
            return lower_value + fraction * (upper_value - lower_value)
    return knots[-1][1]


def _git_commit() -> str | None:
    repo_root = Path(__file__).resolve().parents[3]
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _missing_required_fields(variables: list[str]) -> list[str]:
    available = set(variables)
    aliases = {"kmh": {"kmh", "km"}, "khh": {"khh", "kh"}}
    return [
        field for field in REQUIRED_OUTPUT_FIELDS if not (aliases.get(field, {field}) & available)
    ]


def _model_frame_evidence(
    paths: list[Path],
) -> tuple[
    list[dict[str, float | None]],
    dict[str, int],
    dict[str, list[float | None]],
    list[float | None],
]:
    xarray = importlib.import_module("xarray")
    metrics: list[dict[str, float | None]] = []
    non_finite_counts: dict[str, int] = {}
    final_profiles: dict[str, list[float | None]] = {}
    final_heights: list[float | None] = []
    for file_index, path in enumerate(paths):
        dataset = xarray.open_dataset(path, decode_times=False)
        try:
            time_seconds = _dataset_time_seconds(dataset, file_index)
            liquid_name = "qc" if "qc" in dataset.data_vars else "ql"
            liquid = dataset[liquid_name]
            liquid_values = np.asarray(liquid.values, dtype=float)
            liquid_values = _first_time_slice(liquid_values, liquid.dims)
            vertical_axis, vertical_name = _vertical_axis(liquid)
            cloud_mask = np.isfinite(liquid_values) & (liquid_values >= QC_CLOUD_THRESHOLD_KG_KG)
            horizontal_axes = tuple(
                axis for axis in range(cloud_mask.ndim) if axis != vertical_axis
            )
            level_fraction = np.mean(cloud_mask, axis=horizontal_axes)
            column_cloud = np.any(cloud_mask, axis=vertical_axis)
            lwp = _optional_array(dataset, "cwp")
            w = _optional_array(dataset, "w")
            metrics.append(
                {
                    "time_seconds": time_seconds,
                    "total_cloud_cover_percent": float(np.mean(column_cloud) * 100.0),
                    "peak_cloud_fraction_percent": float(np.max(level_fraction) * 100.0),
                    "mean_lwp": _finite_mean(lwp),
                    "max_lwp": _finite_max(lwp),
                    "max_w": _finite_max(w),
                    "min_w": _finite_min(w),
                }
            )
            for field in REQUIRED_OUTPUT_FIELDS:
                source = field
                if field == "ql" and source not in dataset.data_vars and "qc" in dataset.data_vars:
                    source = "qc"
                if source in dataset.data_vars:
                    values = np.asarray(dataset[source].values, dtype=float)
                    non_finite_counts[field] = non_finite_counts.get(field, 0) + int(
                        values.size - np.count_nonzero(np.isfinite(values))
                    )
            if path == paths[-1]:
                final_profiles = _final_profiles(dataset)
                final_heights = _vertical_values(liquid, vertical_name)
        finally:
            dataset.close()
    return metrics, non_finite_counts, final_profiles, final_heights


def _diagnostic_evidence(
    paths: list[Path],
) -> tuple[dict[str, dict[str, float | None]], list[str]]:
    if not paths:
        return {}, []
    xarray = importlib.import_module("xarray")
    required = ("wprof", "ptb_frc", "qvb_frc", "ug", "vg", "thflux", "qvflux", "ust")
    flux_candidates = (
        "upwp",
        "vpwp",
        "wpwp",
        "ufr",
        "vfr",
        "ptfr",
        "qvfr",
        "ptb_vturbr",
        "qvb_vturbr",
    )
    summary: dict[str, dict[str, float | None]] = {}
    flux_fields: set[str] = set()
    for path in (paths[0], paths[-1]) if len(paths) > 1 else (paths[0],):
        dataset = xarray.open_dataset(path, decode_times=False)
        try:
            for field in required:
                if field in dataset.data_vars:
                    values = np.asarray(dataset[field].values, dtype=float)
                    summary[field] = {"min": _finite_min(values), "max": _finite_max(values)}
            flux_fields.update(field for field in flux_candidates if field in dataset.data_vars)
        finally:
            dataset.close()
    return summary, sorted(flux_fields)


def _dataset_time_seconds(dataset: Any, fallback_index: int) -> float:
    for name in ("time", "mtime", "t"):
        if name in dataset.coords or name in dataset.variables:
            values = np.asarray(dataset[name].values).reshape(-1)
            if values.size:
                return float(values[-1])
    return float(fallback_index * OUTPUT_CADENCE_SECONDS)


def _first_time_slice(
    values: np.ndarray[Any, Any], dimensions: tuple[str, ...]
) -> np.ndarray[Any, Any]:
    for candidate in ("time", "mtime", "t"):
        if candidate in dimensions:
            return np.asarray(np.take(values, 0, axis=dimensions.index(candidate)))
    return values


def _vertical_axis(data_array: Any) -> tuple[int, str]:
    dimensions = tuple(str(name) for name in data_array.dims)
    for candidate in ("zh", "z", "zf", "height", "height_m"):
        if candidate in dimensions:
            time_offset = 1 if dimensions and dimensions[0] in {"time", "mtime", "t"} else 0
            return dimensions.index(candidate) - time_offset, candidate
    raise BomexCaseError(f"Cloud-liquid field lacks a recognized vertical dimension: {dimensions}")


def _vertical_values(data_array: Any, vertical_name: str) -> list[float | None]:
    if vertical_name not in data_array.coords:
        return [float(index) for index in range(int(data_array.sizes[vertical_name]))]
    coordinate = data_array.coords[vertical_name]
    values = np.asarray(coordinate.values, dtype=float).reshape(-1)
    units = str(coordinate.attrs.get("units", "")).strip().lower()
    if units in {"km", "kilometer", "kilometers"}:
        values = values * 1000.0
    return [float(value) if np.isfinite(value) else None for value in values]


def _optional_array(dataset: Any, field: str) -> np.ndarray[Any, Any] | None:
    if field not in dataset.data_vars:
        return None
    return np.asarray(dataset[field].values, dtype=float)


def _final_profiles(dataset: Any) -> dict[str, list[float | None]]:
    profiles: dict[str, list[float | None]] = {}
    for field in ("qv", "th", "u", "v"):
        if field not in dataset.data_vars:
            continue
        data_array = dataset[field]
        values = np.asarray(data_array.values, dtype=float)
        dimensions = [str(name) for name in data_array.dims]
        if dimensions and dimensions[0] in {"time", "mtime", "t"}:
            values = values[-1]
            dimensions = dimensions[1:]
        vertical_name = next(
            (name for name in ("zh", "z", "zf", "height", "height_m") if name in dimensions),
            None,
        )
        if vertical_name is None:
            continue
        vertical_axis = dimensions.index(vertical_name)
        mean_axes = tuple(axis for axis in range(values.ndim) if axis != vertical_axis)
        profile = np.nanmean(values, axis=mean_axes) if mean_axes else values
        profiles[field] = [
            float(value) if np.isfinite(value) else None
            for value in np.asarray(profile).reshape(-1)
        ]
    return profiles


def _finite_mean(values: np.ndarray[Any, Any] | None) -> float | None:
    if values is None:
        return None
    finite = values[np.isfinite(values)]
    return float(np.mean(finite)) if finite.size else None


def _finite_max(values: np.ndarray[Any, Any] | None) -> float | None:
    if values is None:
        return None
    finite = values[np.isfinite(values)]
    return float(np.max(finite)) if finite.size else None


def _finite_min(values: np.ndarray[Any, Any] | None) -> float | None:
    if values is None:
        return None
    finite = values[np.isfinite(values)]
    return float(np.min(finite)) if finite.size else None


def _mean_metric(frames: list[dict[str, float | None]], key: str) -> float | None:
    values: list[float] = []
    for frame in frames:
        value = frame.get(key)
        if value is not None:
            values.append(value)
    return float(np.mean(values)) if values else None


def _max_metric(frames: list[dict[str, float | None]], key: str) -> float | None:
    values: list[float] = []
    for frame in frames:
        value = frame.get(key)
        if value is not None:
            values.append(value)
    return max(values) if values else None


def _local_peak_count(values: list[float]) -> int:
    if len(values) < 3:
        return 0
    maximum = max(values)
    if maximum <= 0.0:
        return 0
    floor = maximum * 0.1
    return sum(
        1
        for index in range(1, len(values) - 1)
        if values[index] >= floor
        and values[index] > values[index - 1]
        and values[index] >= values[index + 1]
    )
