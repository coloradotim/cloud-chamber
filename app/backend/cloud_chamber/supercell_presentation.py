"""Issue #421 source-locked Supercell presentation-run packaging and validation."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import xarray as xr
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber import __version__
from cloud_chamber.generated_input_identity import (
    GeneratedInputIdentityError,
    verify_generated_input_identity,
)
from cloud_chamber.local_run_manager import NORMAL_TERMINATION_MARKER
from cloud_chamber.mountain_wave_case import (
    active_cm1_processes,
    normalize_time_to_seconds,
    parse_namelist_assignments,
    replace_namelist_assignment,
    verified_clean_git_commit,
)
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
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.supercell_benchmark import (
    CASE_ID as SOURCE_CASE_ID,
)
from cloud_chamber.supercell_benchmark import (
    collect_cm1_provenance,
    sha256_file,
    verify_gate_a_source_lock,
)
from cloud_chamber.supercell_hodograph import (
    STRAIGHT_LINE_HODOGRAPH_ARTIFACT_FILENAME,
    STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND,
    STRAIGHT_LINE_HODOGRAPH_TARGET,
    straight_line_hodograph_artifact,
)

SOURCE_RUN_ID = "quarter-circle-supercell-official-20260722T142521Z"
SOURCE_EVIDENCE_FILENAME = "supercell_gate_b_evidence.json"
PRESENTATION_PROFILE_ID = "supercell_presentation_v1"
PRESENTATION_RUN_ID = "quarter-circle-supercell-presentation-v1-20260723"
PRESENTATION_CASE_ID = "cm1_r21_1_quarter_circle_supercell_presentation_v1"
CHARACTERIZATION_RUN_ID = "quarter-circle-supercell-presentation-characterization-20260723"
CHARACTERIZATION_CASE_ID = "cm1_r21_1_quarter_circle_supercell_characterization_v1"
STRAIGHT_LINE_PRESENTATION_RUN_ID = "straight-line-supercell-presentation-v1-20260726"
STRAIGHT_LINE_PRESENTATION_CASE_ID = "cm1_r21_1_straight_line_supercell_presentation_v1"
STRAIGHT_LINE_CHARACTERIZATION_RUN_ID = (
    "straight-line-supercell-presentation-characterization-20260726"
)
STRAIGHT_LINE_CHARACTERIZATION_CASE_ID = "cm1_r21_1_straight_line_supercell_characterization_v1"
QUARTER_CIRCLE_SIMULATION_ID = "supercells_quarter_circle_reference"
STRAIGHT_LINE_SIMULATION_ID = "supercells_straight_line_hodograph"
MINIMUM_POST_RUN_FREE_BYTES = 5 * 1024**3
MEASURED_REFERENCE_RETAINED_BYTES = 8_873_437_520
FINAL_RUN_STORAGE_RESERVATION_BYTES = 12 * 1024**3
FINAL_CAMPAIGN_RUN_IDS = (
    PRESENTATION_RUN_ID,
    STRAIGHT_LINE_PRESENTATION_RUN_ID,
)

REQUIRED_3D_FIELDS = (
    "th",
    "prs",
    "qv",
    "qc",
    "qr",
    "qi",
    "qs",
    "qg",
    "nci",
    "ncs",
    "ncr",
    "ncg",
    "dbz",
    "uinterp",
    "vinterp",
    "winterp",
    "xvort",
    "yvort",
    "zvort",
)
REQUIRED_2D_FIELDS = ("rain", "prate", "uh", "cref")
REQUIRED_OUTPUT_FIELDS = (*REQUIRED_3D_FIELDS, *REQUIRED_2D_FIELDS)
REQUIRED_COORDINATES = ("time", "xh", "yh", "zh")
FATAL_FLOATING_POINT_FLAGS = (
    "IEEE_INVALID_FLAG",
    "IEEE_DIVIDE_BY_ZERO",
    "IEEE_OVERFLOW_FLAG",
)

BASE_PRESENTATION_ASSIGNMENTS = {
    "nx": "240",
    "ny": "240",
    "nz": "60",
    "dx": "500.0",
    "dy": "500.0",
    "dz": "333.3333333333",
    "dtl": "3.0",
    "output_format": "2",
    "output_filetype": "2",
    "output_sws": "0",
    "output_svs": "0",
    "output_sps": "0",
    "output_srs": "0",
    "output_sgs": "0",
    "output_sus": "0",
    "output_shs": "0",
    "output_tke": "0",
    "output_km": "0",
    "output_kh": "0",
    "output_u": "0",
    "output_v": "0",
    "output_w": "0",
}
EXPECTED_OFFICIAL_ASSIGNMENTS = {
    "nx": "120",
    "ny": "120",
    "nz": "40",
    "dx": "1000.0",
    "dy": "1000.0",
    "dz": "500.0",
    "dtl": "6.000",
    "timax": "7200.0",
    "tapfrq": "900.0",
    "output_format": "1",
    "output_filetype": "1",
    "output_sws": "1",
    "output_svs": "1",
    "output_sps": "1",
    "output_srs": "1",
    "output_sgs": "1",
    "output_sus": "1",
    "output_shs": "1",
    "output_tke": "1",
    "output_km": "1",
    "output_kh": "1",
    "output_u": "1",
    "output_v": "1",
    "output_w": "1",
}
LOCKED_SCIENCE_ASSIGNMENTS = {
    "terrain_flag": ".false.",
    "isnd": "5",
    "iwnd": "2",
    "iinit": "1",
    "irandp": "0",
    "ibalance": "0",
    "imove": "1",
    "umove": "12.5",
    "vmove": "3.0",
    "stretch_x": "0",
    "stretch_y": "0",
    "stretch_z": "0",
    "zd": "15000.0",
    "output_interp": "0",
    "output_rain": "1",
    "output_th": "1",
    "output_prs": "1",
    "output_qv": "1",
    "output_q": "1",
    "output_dbz": "1",
    "output_uinterp": "1",
    "output_vinterp": "1",
    "output_winterp": "1",
    "output_vort": "1",
    "output_uh": "1",
}


class SupercellPresentationError(RuntimeError):
    """Raised when the bounded presentation-run contract must fail closed."""


@dataclass(frozen=True)
class SupercellPresentationSpec:
    kind: Literal["characterization", "final"]
    run_id: str
    case_id: str
    duration_seconds: int
    output_cadence_seconds: int
    hodograph: Literal["quarter_circle", "straight_line"] = "quarter_circle"

    @property
    def expected_times_seconds(self) -> tuple[int, ...]:
        return tuple(range(0, self.duration_seconds + 1, self.output_cadence_seconds))

    @property
    def changed_assignments(self) -> dict[str, str]:
        assignments = {
            **BASE_PRESENTATION_ASSIGNMENTS,
            "timax": _fortran_float(self.duration_seconds),
            "tapfrq": _fortran_float(self.output_cadence_seconds),
        }
        if self.hodograph == "straight_line":
            assignments["iwnd"] = "12"
        return assignments

    @property
    def expected_science_assignments(self) -> dict[str, str]:
        return {
            **LOCKED_SCIENCE_ASSIGNMENTS,
            "iwnd": "12" if self.hodograph == "straight_line" else "2",
        }

    @property
    def simulation_id(self) -> str:
        if self.hodograph == "straight_line":
            return STRAIGHT_LINE_SIMULATION_ID
        return QUARTER_CIRCLE_SIMULATION_ID

    @property
    def display_name(self) -> str:
        if self.hodograph == "straight_line":
            return "Straight-Line Hodograph Supercell"
        return "Quarter-Circle Supercell"

    @property
    def scalar_cells(self) -> int:
        return 240 * 240 * 60

    @property
    def integration_steps(self) -> int:
        return self.duration_seconds // 3


CHARACTERIZATION_SPEC = SupercellPresentationSpec(
    kind="characterization",
    run_id=CHARACTERIZATION_RUN_ID,
    case_id=CHARACTERIZATION_CASE_ID,
    duration_seconds=300,
    output_cadence_seconds=300,
)
PRESENTATION_SPEC = SupercellPresentationSpec(
    kind="final",
    run_id=PRESENTATION_RUN_ID,
    case_id=PRESENTATION_CASE_ID,
    duration_seconds=10_800,
    output_cadence_seconds=120,
)
STRAIGHT_LINE_CHARACTERIZATION_SPEC = SupercellPresentationSpec(
    kind="characterization",
    run_id=STRAIGHT_LINE_CHARACTERIZATION_RUN_ID,
    case_id=STRAIGHT_LINE_CHARACTERIZATION_CASE_ID,
    duration_seconds=300,
    output_cadence_seconds=300,
    hodograph="straight_line",
)
STRAIGHT_LINE_PRESENTATION_SPEC = SupercellPresentationSpec(
    kind="final",
    run_id=STRAIGHT_LINE_PRESENTATION_RUN_ID,
    case_id=STRAIGHT_LINE_PRESENTATION_CASE_ID,
    duration_seconds=10_800,
    output_cadence_seconds=120,
    hodograph="straight_line",
)


class NamelistDifference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    official_value: str
    generated_value: str
    reason: Literal[
        "output_transport",
        "presentation_grid",
        "presentation_timing",
        "bounded_output_inventory",
        "controlled_hodograph_geometry",
    ]


class PresentationStorageEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_history_count: int
    scalar_grid: list[int]
    scalar_3d_array_count: int
    scalar_2d_array_count: int
    precision_bytes: int = 4
    uncompressed_numeric_history_floor_bytes: int
    compression_credit_bytes: Literal[0] = 0
    minimum_post_run_free_bytes: int = MINIMUM_POST_RUN_FREE_BYTES
    gate_basis: Literal[
        "uncompressed_numeric_floor",
        "measured_retained_campaign_reservation",
    ] = "uncompressed_numeric_floor"
    measured_reference_retained_bytes: int | None = None
    per_final_run_reservation_bytes: int | None = None
    final_campaign_run_ids: list[str] = Field(default_factory=list)
    final_campaign_runs_remaining: int = 1
    required_free_bytes: int
    available_free_bytes: int
    passed: bool


class PresentationPreflight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checked_at: datetime
    run_id: str
    implementation_commit: str
    checks: dict[str, bool]
    storage: PresentationStorageEstimate
    passed: bool


class SupercellPresentationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_version: Literal["supercell_presentation_run_evidence_v1"] = (
        "supercell_presentation_run_evidence_v1"
    )
    kind: Literal["characterization", "final"]
    run_id: str
    case_id: str
    simulation_id: str
    hodograph: Literal["quarter_circle", "straight_line"]
    source_run_id: str = SOURCE_RUN_ID
    implementation_commit: str
    grid: dict[str, int | float]
    duration_seconds: int
    output_cadence_seconds: int
    history_count: int
    times_seconds: list[int]
    required_fields: list[str]
    history_inventory: list[dict[str, int | str]]
    field_minimums: dict[str, float]
    field_maximums: dict[str, float]
    non_finite_counts: dict[str, int]
    runtime_seconds: float
    peak_rss_bytes: int | None
    numbered_history_bytes: int
    retained_run_bytes: int
    available_free_bytes_after_validation: int
    source_customization: dict[str, Any] | None = None
    runtime_warnings: list[str] = Field(default_factory=list)
    normal_completion: bool


@dataclass(frozen=True)
class SupercellPresentationPackage:
    spec: SupercellPresentationSpec
    package_dir: Path
    manifest_path: Path
    case_manifest_path: Path
    storage_estimate_path: Path
    implementation_commit: str


def spec_for_kind(
    kind: str,
    hodograph: str = "quarter_circle",
) -> SupercellPresentationSpec:
    if hodograph == "straight_line":
        if kind == "characterization":
            return STRAIGHT_LINE_CHARACTERIZATION_SPEC
        if kind == "final":
            return STRAIGHT_LINE_PRESENTATION_SPEC
    if kind == "characterization":
        return CHARACTERIZATION_SPEC
    if kind == "final":
        return PRESENTATION_SPEC
    raise SupercellPresentationError(
        f"Unknown presentation-run selection: kind={kind}, hodograph={hodograph}."
    )


def render_presentation_namelist(
    official_text: str,
    spec: SupercellPresentationSpec,
) -> tuple[str, list[NamelistDifference]]:
    official = parse_namelist_assignments(official_text)
    expected_official = {
        **EXPECTED_OFFICIAL_ASSIGNMENTS,
        "timax": "7200.0",
        "tapfrq": "900.0",
    }
    for name, expected in {**expected_official, **LOCKED_SCIENCE_ASSIGNMENTS}.items():
        actual = official.get(name)
        if not _same_assignment(actual, expected):
            raise SupercellPresentationError(
                f"Official source assignment {name} changed: {actual!r} != {expected!r}."
            )

    rendered = official_text
    for name, value in spec.changed_assignments.items():
        rendered = replace_namelist_assignment(rendered, name, value)
    generated = parse_namelist_assignments(rendered)
    if generated.keys() != official.keys():
        raise SupercellPresentationError("Presentation namelist assignment inventory changed.")

    differences: list[NamelistDifference] = []
    for name, official_value in official.items():
        generated_value = generated[name]
        if _same_assignment(generated_value, official_value):
            continue
        expected_change = spec.changed_assignments.get(name)
        if expected_change is None or not _same_assignment(
            generated_value,
            expected_change,
        ):
            raise SupercellPresentationError(
                f"Unapproved presentation namelist difference: {name}."
            )
        differences.append(
            NamelistDifference(
                name=name,
                official_value=official_value,
                generated_value=generated_value,
                reason=_difference_reason(name),
            )
        )

    if {item.name for item in differences} != set(spec.changed_assignments):
        raise SupercellPresentationError("Presentation namelist differences are incomplete.")
    for name, expected in spec.expected_science_assignments.items():
        if not _same_assignment(generated.get(name), expected):
            raise SupercellPresentationError(f"Scientific assignment {name} did not remain fixed.")

    restored = rendered
    for difference in differences:
        restored = replace_namelist_assignment(
            restored,
            difference.name,
            difference.official_value,
        )
    if restored != official_text:
        raise SupercellPresentationError(
            "Presentation namelist differs outside the declared assignments."
        )
    return rendered.rstrip() + "\n", differences


def estimate_storage(
    spec: SupercellPresentationSpec,
    target_dir: Path,
) -> PresentationStorageEstimate:
    history_bytes = (
        len(REQUIRED_3D_FIELDS) * spec.scalar_cells + len(REQUIRED_2D_FIELDS) * 240 * 240
    ) * 4
    floor = history_bytes * len(spec.expected_times_seconds)
    available = shutil.disk_usage(target_dir).free
    gate_basis: Literal[
        "uncompressed_numeric_floor",
        "measured_retained_campaign_reservation",
    ] = "uncompressed_numeric_floor"
    measured_reference_retained_bytes = None
    per_final_run_reservation_bytes = None
    campaign_run_ids: list[str] = []
    campaign_runs_remaining = 1
    required = floor + MINIMUM_POST_RUN_FREE_BYTES
    if spec.kind == "final":
        gate_basis = "measured_retained_campaign_reservation"
        measured_reference_retained_bytes = MEASURED_REFERENCE_RETAINED_BYTES
        per_final_run_reservation_bytes = FINAL_RUN_STORAGE_RESERVATION_BYTES
        campaign_run_ids = list(FINAL_CAMPAIGN_RUN_IDS)
        completed = _completed_final_campaign_runs(target_dir.parent)
        campaign_runs_remaining = len(set(FINAL_CAMPAIGN_RUN_IDS) - completed)
        required = (
            campaign_runs_remaining * FINAL_RUN_STORAGE_RESERVATION_BYTES
            + MINIMUM_POST_RUN_FREE_BYTES
        )
    return PresentationStorageEstimate(
        expected_history_count=len(spec.expected_times_seconds),
        scalar_grid=[240, 240, 60],
        scalar_3d_array_count=len(REQUIRED_3D_FIELDS),
        scalar_2d_array_count=len(REQUIRED_2D_FIELDS),
        uncompressed_numeric_history_floor_bytes=floor,
        gate_basis=gate_basis,
        measured_reference_retained_bytes=measured_reference_retained_bytes,
        per_final_run_reservation_bytes=per_final_run_reservation_bytes,
        final_campaign_run_ids=campaign_run_ids,
        final_campaign_runs_remaining=campaign_runs_remaining,
        required_free_bytes=required,
        available_free_bytes=available,
        passed=available >= required,
    )


def generate_presentation_package(
    *,
    settings: CloudChamberSettings,
    spec: SupercellPresentationSpec,
) -> SupercellPresentationPackage:
    implementation_commit = verified_clean_git_commit()
    if active_cm1_processes():
        raise SupercellPresentationError("A CM1 or MPI process is already active.")
    source = _accepted_source_identity(settings)
    provenance = collect_cm1_provenance(settings)
    target_dir = settings.runtime_home.expanduser() / "runs" / spec.run_id
    if target_dir.exists():
        raise SupercellPresentationError(f"Presentation package already exists: {spec.run_id}")
    target_dir.mkdir(parents=True)
    paths = {
        "manifest": target_dir / "run_manifest.json",
        "case_manifest": target_dir / "case_manifest.json",
        "namelist": target_dir / "namelist.input",
        "runtime_checklist": target_dir / "runtime_file_checklist.json",
        "namelist_diff": target_dir / "presentation_namelist_diff.json",
        "storage": target_dir / "storage_estimate.json",
        "package_report": target_dir / "presentation_package_report.json",
    }
    if spec.hodograph == "straight_line":
        paths["hodograph_customization"] = target_dir / STRAIGHT_LINE_HODOGRAPH_ARTIFACT_FILENAME
    try:
        generated_text, differences = render_presentation_namelist(
            provenance.supercell_namelist_path.read_text(),
            spec,
        )
        paths["namelist"].write_text(generated_text)
        if spec.hodograph == "straight_line":
            source_path = provenance.source_root / STRAIGHT_LINE_HODOGRAPH_TARGET
            _write_json(
                paths["hodograph_customization"],
                straight_line_hodograph_artifact(source_path.read_text()),
            )
        wind_source = (
            "a source-locked Cloud Chamber straight-line profile that preserves the "
            "accepted iwnd=2 endpoint shear and layer-mean wind"
            if spec.hodograph == "straight_line"
            else "CM1 src/base.F iwnd=2 analytic quarter-circle wind profile"
        )
        _write_json(
            paths["runtime_checklist"],
            {
                "status": (
                    "source_locked_hodograph_customization_declared"
                    if spec.hodograph == "straight_line"
                    else "empty_external_scientific_runtime_file_inventory"
                ),
                "consumed_files": [],
                "required_files": [],
                "packaged_source_customization": (
                    STRAIGHT_LINE_HODOGRAPH_ARTIFACT_FILENAME
                    if spec.hodograph == "straight_line"
                    else None
                ),
                "source_candidates": {},
                "scientific_state_sources": [
                    "CM1 src/base.F isnd=5 analytic Weisman-Klemp sounding",
                    wind_source,
                    "CM1 src/init3d.F iinit=1 deterministic warm bubble",
                ],
            },
        )
        _write_json(
            paths["namelist_diff"],
            {
                "official_sha256": _sha256_text(provenance.supercell_namelist_path.read_text()),
                "generated_sha256": _sha256_text(generated_text),
                "differences": [item.model_dump() for item in differences],
                "expected_scientific_assignments": spec.expected_science_assignments,
                "controlled_atmospheric_difference": (
                    {
                        "name": "hodograph_geometry",
                        "official_iwnd": "2",
                        "generated_iwnd": "12",
                        "preserved_endpoint_shear_m_s": [31.0, 7.0],
                        "preserved_layer_mean_wind_m_s": [13.5145538645, 6.1521128022],
                    }
                    if spec.hodograph == "straight_line"
                    else None
                ),
            },
        )
        storage = estimate_storage(spec, target_dir)
        if not storage.passed:
            raise SupercellPresentationError(
                f"Storage preflight failed: {storage.available_free_bytes} < "
                f"{storage.required_free_bytes}."
            )
        _write_json(paths["storage"], storage.model_dump())
        generated_hashes = {
            path.name: sha256_file(path)
            for key, path in paths.items()
            if key
            not in {
                "manifest",
                "case_manifest",
                "package_report",
            }
        }
        case_manifest = {
            "profile_id": PRESENTATION_PROFILE_ID,
            "kind": spec.kind,
            "run_id": spec.run_id,
            "case_id": spec.case_id,
            "simulation_id": spec.simulation_id,
            "hodograph": spec.hodograph,
            "source_run": source,
            "gate_a_source_lock": verify_gate_a_source_lock(),
            "cm1_provenance": provenance.report_record(),
            "implementation_commit": implementation_commit,
            "configuration_differences": [item.model_dump() for item in differences],
            "generated_input_sha256": generated_hashes,
            "storage_estimate": storage.model_dump(),
            "execution_authorization": {
                "process_count": 1,
                "retry_allowed": False,
                "tuning_matrix_allowed": False,
                "duration_seconds": spec.duration_seconds,
            },
        }
        _write_json(paths["case_manifest"], case_manifest)
        now = datetime.now(UTC)
        manifest = RunManifest(
            run_id=spec.run_id,
            scenario=ScenarioReference(
                id=spec.case_id,
                schema_version="supercell_presentation_v1",
            ),
            controls={},
            run_configuration={
                "profile_id": PRESENTATION_PROFILE_ID,
                "kind": spec.kind,
                "case_id": spec.case_id,
                "simulation_id": spec.simulation_id,
                "parent_simulation_id": (
                    QUARTER_CIRCLE_SIMULATION_ID if spec.hodograph == "straight_line" else None
                ),
                "reference_simulation_id": QUARTER_CIRCLE_SIMULATION_ID,
                "hodograph": spec.hodograph,
                "source_run": source,
                "source_lock": provenance.report_record(),
                "gate_a_source_lock": verify_gate_a_source_lock(),
                "grid": {
                    "nx": 240,
                    "ny": 240,
                    "nz": 60,
                    "dx_m": 500.0,
                    "dy_m": 500.0,
                    "dz_m": 20_000.0 / 60.0,
                },
                "time_step_seconds": 3.0,
                "duration_seconds": spec.duration_seconds,
                "history_cadence_seconds": spec.output_cadence_seconds,
                "stats_cadence_seconds": 60,
                "expected_history_count": len(spec.expected_times_seconds),
                "expected_times_seconds": list(spec.expected_times_seconds),
                "changed_namelist_assignments": spec.changed_assignments,
                "generated_input_sha256": generated_hashes,
                "storage_estimate": storage.model_dump(),
                **(
                    {"cm1_source_customization_kind": (STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND)}
                    if spec.hodograph == "straight_line"
                    else {}
                ),
            },
            physical_question=(
                (
                    "How does hodograph curvature change storm organization, rotating-updraft "
                    "structure, precipitation, and low-level flow when the thermodynamic "
                    "environment and numerical experiment remain otherwise matched?"
                )
                if spec.hodograph == "straight_line"
                else (
                    "Does the accepted quarter-circle Supercell produce a materially more "
                    "detailed, smoother, and longer presentation Simulation?"
                )
            ),
            expected_diagnostics=[
                "three_accepted_supercell_lenses",
                "dense_saved_output_timeline",
                "bounded_product_explore_payloads",
                "later_storm_evolution",
            ],
            generated_inputs=GeneratedInputs(
                run_directory=str(target_dir),
                manifest_path=str(paths["manifest"]),
                namelist_input=str(paths["namelist"]),
                input_sounding=None,
                dry_run_report=str(paths["package_report"]),
                runtime_file_checklist=[str(paths["runtime_checklist"])],
                cm1_source_customization=(
                    str(paths["hodograph_customization"])
                    if spec.hodograph == "straight_line"
                    else None
                ),
            ),
            runtime_paths=RuntimePaths(runtime_home=str(settings.runtime_home.expanduser())),
            app=AppMetadata(app_version=__version__, commit=implementation_commit),
            lifecycle_state=LifecycleState.PACKAGED,
            validation_status=ValidationStatus.VALID,
            provenance=ProvenanceMetadata(product_state=ProductState.PACKAGED_DRY_RUN_OUTPUT),
            created_at=now,
            updated_at=now,
            user=UserMetadata(name=f"{spec.display_name} {spec.kind}"),
            required_output_fields=list(REQUIRED_OUTPUT_FIELDS),
            input_source=(
                "CM1_r21.1_analytic_isnd5_source_locked_straight_line_iwnd12_iinit1"
                if spec.hodograph == "straight_line"
                else "CM1_r21.1_analytic_isnd5_iwnd2_iinit1"
            ),
            trigger_type="source_defined_deterministic_warm_bubble",
            trigger_parameters={
                "center": "domain_center",
                "center_agl_m": 1400.0,
                "horizontal_radius_m": 10000.0,
                "vertical_radius_m": 1400.0,
                "maximum_theta_perturbation_k": 1.0,
            },
            expected_outputs=[
                f"{len(spec.expected_times_seconds)}_numbered_native_netcdf_histories",
                "one_statistics_netcdf",
            ],
            run_limitations=[
                (
                    "idealized_source_locked_straight_line_hodograph_supercell"
                    if spec.hodograph == "straight_line"
                    else "idealized_source_locked_quarter_circle_supercell"
                ),
                "presentation_grid_and_timing_adaptation_not_exact_gate_b_reproduction",
                "one_authorized_process_without_retry",
                "translating_model_frame",
                "15_to_20_km_rayleigh_layer",
            ],
            manual_validation_status=(
                f"issue_444_straight_line_{spec.kind}_pending"
                if spec.hodograph == "straight_line"
                else f"issue_421_{spec.kind}_pending"
            ),
        )
        write_run_manifest(paths["manifest"], manifest)
        _write_json(
            paths["package_report"],
            {
                "status": "packaged_not_executed",
                "profile_id": PRESENTATION_PROFILE_ID,
                "kind": spec.kind,
                "run_id": spec.run_id,
                "case_id": spec.case_id,
                "simulation_id": spec.simulation_id,
                "hodograph": spec.hodograph,
                "implementation_commit": implementation_commit,
                "source_run": source,
                "configuration_differences": [item.model_dump() for item in differences],
                "storage_estimate": storage.model_dump(),
                "process_started": False,
            },
        )
        package = SupercellPresentationPackage(
            spec=spec,
            package_dir=target_dir,
            manifest_path=paths["manifest"],
            case_manifest_path=paths["case_manifest"],
            storage_estimate_path=paths["storage"],
            implementation_commit=implementation_commit,
        )
        verify_presentation_package(
            settings=settings,
            package=package,
            require_clean_head=True,
        )
        return package
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise


def load_presentation_package(
    *,
    settings: CloudChamberSettings,
    spec: SupercellPresentationSpec,
) -> SupercellPresentationPackage:
    package_dir = settings.runtime_home.expanduser() / "runs" / spec.run_id
    paths = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "storage": package_dir / "storage_estimate.json",
    }
    missing = sorted(path.name for path in paths.values() if not path.is_file())
    if missing:
        raise SupercellPresentationError(f"Presentation package is incomplete: {missing}")
    case_manifest = json.loads(paths["case_manifest"].read_text())
    implementation_commit = case_manifest.get("implementation_commit")
    if not isinstance(implementation_commit, str):
        raise SupercellPresentationError("Presentation package has no implementation identity.")
    return SupercellPresentationPackage(
        spec=spec,
        package_dir=package_dir,
        manifest_path=paths["manifest"],
        case_manifest_path=paths["case_manifest"],
        storage_estimate_path=paths["storage"],
        implementation_commit=implementation_commit,
    )


def verify_presentation_package(
    *,
    settings: CloudChamberSettings,
    package: SupercellPresentationPackage,
    require_clean_head: bool,
) -> PresentationPreflight:
    manifest = load_run_manifest(package.manifest_path)
    case_manifest = json.loads(package.case_manifest_path.read_text())
    if manifest.run_id != package.spec.run_id or manifest.scenario.id != package.spec.case_id:
        raise SupercellPresentationError("Presentation package identity changed.")
    if manifest.lifecycle_state != LifecycleState.PACKAGED:
        raise SupercellPresentationError("Only a packaged, never-started run may launch.")
    if manifest.app.commit != package.implementation_commit:
        raise SupercellPresentationError("Manifest implementation identity changed.")
    if require_clean_head and verified_clean_git_commit() != package.implementation_commit:
        raise SupercellPresentationError("Package does not match the clean implementation head.")
    try:
        verified_inputs = verify_generated_input_identity(manifest)
    except GeneratedInputIdentityError as exc:
        raise SupercellPresentationError(str(exc)) from exc
    if verified_inputs != case_manifest.get("generated_input_sha256"):
        raise SupercellPresentationError("Generated input inventory changed.")
    current_source = _accepted_source_identity(settings)
    if current_source != case_manifest.get("source_run"):
        raise SupercellPresentationError("Accepted Gate B source identity changed.")
    provenance = collect_cm1_provenance(settings)
    if provenance.report_record() != case_manifest.get("cm1_provenance"):
        raise SupercellPresentationError("CM1 provenance changed after packaging.")
    generated_text, differences = render_presentation_namelist(
        provenance.supercell_namelist_path.read_text(),
        package.spec,
    )
    namelist_path = Path(manifest.generated_inputs.namelist_input or "")
    if namelist_path.read_text() != generated_text:
        raise SupercellPresentationError("Generated presentation namelist changed.")
    if [item.model_dump() for item in differences] != case_manifest.get(
        "configuration_differences"
    ):
        raise SupercellPresentationError("Presentation configuration audit changed.")
    if package.spec.hodograph == "straight_line":
        customization_path = Path(manifest.generated_inputs.cm1_source_customization or "")
        expected_customization = straight_line_hodograph_artifact(
            (provenance.source_root / STRAIGHT_LINE_HODOGRAPH_TARGET).read_text()
        )
        if json.loads(customization_path.read_text()) != expected_customization:
            raise SupercellPresentationError(
                "Straight-line hodograph source customization changed after packaging."
            )
    if active_cm1_processes():
        raise SupercellPresentationError("Another CM1 or MPI process is active.")
    prior = _prior_execution(settings, package.spec)
    if prior:
        raise SupercellPresentationError(
            f"A prior {package.spec.kind} process forbids another: {prior}."
        )
    existing = _numbered_histories(package.package_dir)
    if existing:
        raise SupercellPresentationError("Presentation target already contains model output.")
    stored = PresentationStorageEstimate.model_validate_json(
        package.storage_estimate_path.read_text()
    )
    storage = estimate_storage(package.spec, package.package_dir)
    mutable_storage_fields = {
        "final_campaign_runs_remaining",
        "required_free_bytes",
        "available_free_bytes",
        "passed",
    }
    if stored.model_dump(exclude=mutable_storage_fields) != storage.model_dump(
        exclude=mutable_storage_fields
    ):
        raise SupercellPresentationError("Presentation storage contract changed after packaging.")
    checks = {
        "clean_implementation_head": (
            not require_clean_head or verified_clean_git_commit() == package.implementation_commit
        ),
        "accepted_gate_b_source_identity": True,
        "pinned_cm1_source_and_executable": True,
        "generated_input_hashes": bool(verified_inputs),
        "exact_declared_namelist_differences": True,
        "unrelated_scientific_setup_unchanged": True,
        "controlled_hodograph_identity": (
            manifest.run_configuration.get("hodograph") == package.spec.hodograph
        ),
        "expected_timeline": (
            tuple(manifest.run_configuration.get("expected_times_seconds", []))
            == package.spec.expected_times_seconds
        ),
        "no_untracked_external_scientific_runtime_files": (
            manifest.generated_inputs.input_sounding is None
        ),
        "no_active_cm1_or_mpi_process": True,
        "no_prior_same_kind_process": True,
        "target_contains_no_output": True,
        "no_unproven_compression_assumption": storage.compression_credit_bytes == 0,
        "explicit_storage_gate_basis": (
            storage.gate_basis == "uncompressed_numeric_floor"
            or (
                storage.gate_basis == "measured_retained_campaign_reservation"
                and storage.measured_reference_retained_bytes == MEASURED_REFERENCE_RETAINED_BYTES
                and storage.per_final_run_reservation_bytes == FINAL_RUN_STORAGE_RESERVATION_BYTES
            )
        ),
        "adequate_free_space": storage.passed,
    }
    preflight = PresentationPreflight(
        checked_at=datetime.now(UTC),
        run_id=package.spec.run_id,
        implementation_commit=package.implementation_commit,
        checks=checks,
        storage=storage,
        passed=all(checks.values()),
    )
    _write_json(
        package.package_dir / "execution_preflight.json",
        preflight.model_dump(mode="json"),
    )
    return preflight


def validate_completed_presentation_run(
    *,
    settings: CloudChamberSettings,
    package: SupercellPresentationPackage,
    peak_rss_bytes: int | None = None,
) -> SupercellPresentationEvidence:
    manifest = load_run_manifest(package.manifest_path)
    if manifest.lifecycle_state != LifecycleState.COMPLETED or manifest.execution.exit_code != 0:
        raise SupercellPresentationError("Validation requires one normally completed process.")
    if manifest.app.commit != package.implementation_commit:
        raise SupercellPresentationError("Completed run lost its implementation identity.")
    try:
        verify_generated_input_identity(manifest)
    except GeneratedInputIdentityError as exc:
        raise SupercellPresentationError(str(exc)) from exc
    collect_cm1_provenance(settings)
    source_customization = _validate_completed_source_customization(
        manifest=manifest,
        spec=package.spec,
    )
    histories = _numbered_histories(package.package_dir)
    if len(histories) != len(package.spec.expected_times_seconds):
        raise SupercellPresentationError(
            f"Expected {len(package.spec.expected_times_seconds)} histories; "
            f"found {len(histories)}."
        )
    stats = sorted(package.package_dir.glob("*stats*.nc*"))
    if len(stats) != 1:
        raise SupercellPresentationError("Expected exactly one statistics NetCDF.")

    times: list[int] = []
    inventory: list[dict[str, int | str]] = []
    minimums = {name: math.inf for name in REQUIRED_OUTPUT_FIELDS}
    maximums = {name: -math.inf for name in REQUIRED_OUTPUT_FIELDS}
    non_finite = {name: 0 for name in REQUIRED_OUTPUT_FIELDS}
    reference_coordinates: dict[str, np.ndarray[Any, np.dtype[Any]]] | None = None
    for path in histories:
        with xr.open_dataset(path, decode_times=False) as dataset:
            time_seconds = _dataset_time_seconds(dataset)
            times.append(int(round(time_seconds)))
            missing = sorted(set(REQUIRED_OUTPUT_FIELDS) - set(dataset.data_vars))
            if missing:
                raise SupercellPresentationError(f"Required fields are missing: {missing}.")
            _validate_grid(dataset)
            coordinates = {
                name: np.asarray(dataset[name].values, dtype=np.float64)
                for name in ("xh", "yh", "zh")
            }
            if reference_coordinates is None:
                reference_coordinates = coordinates
            elif any(
                not np.array_equal(reference_coordinates[name], values)
                for name, values in coordinates.items()
            ):
                raise SupercellPresentationError("Native coordinates changed between histories.")
            _validate_units(dataset)
            for name in REQUIRED_OUTPUT_FIELDS:
                values = np.asarray(dataset[name].values)
                finite = np.isfinite(values)
                count = int(values.size - np.count_nonzero(finite))
                non_finite[name] += count
                if count:
                    continue
                minimums[name] = min(minimums[name], float(np.min(values)))
                maximums[name] = max(maximums[name], float(np.max(values)))
        inventory.append(
            {
                "filename": path.name,
                "time_seconds": int(round(time_seconds)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if times != list(package.spec.expected_times_seconds):
        raise SupercellPresentationError(
            f"Saved history times changed: {times} != {package.spec.expected_times_seconds}."
        )
    contaminated = {name: count for name, count in non_finite.items() if count}
    if contaminated:
        raise SupercellPresentationError(
            f"Required native fields contain non-finite values: {contaminated}."
        )
    stdout = Path(manifest.execution.stdout_log or "").read_text(errors="replace")
    stderr = Path(manifest.execution.stderr_log or "").read_text(errors="replace")
    if NORMAL_TERMINATION_MARKER not in stdout:
        raise SupercellPresentationError("CM1 normal completion marker is absent.")
    fatal = [flag for flag in FATAL_FLOATING_POINT_FLAGS if flag in stderr]
    if fatal:
        raise SupercellPresentationError(f"CM1 reported fatal floating-point flags: {fatal}.")
    warnings = (
        ["CM1 stderr reported IEEE_UNDERFLOW_FLAG"] if "IEEE_UNDERFLOW_FLAG" in stderr else []
    )
    if manifest.execution.started_at is None or manifest.execution.finished_at is None:
        raise SupercellPresentationError("Completed run has no runtime interval.")
    runtime_seconds = (
        manifest.execution.finished_at - manifest.execution.started_at
    ).total_seconds()
    evidence = SupercellPresentationEvidence(
        kind=package.spec.kind,
        run_id=package.spec.run_id,
        case_id=package.spec.case_id,
        simulation_id=package.spec.simulation_id,
        hodograph=package.spec.hodograph,
        implementation_commit=package.implementation_commit,
        grid={
            "nx": 240,
            "ny": 240,
            "nz": 60,
            "dx_m": 500.0,
            "dy_m": 500.0,
            "dz_m": 20_000.0 / 60.0,
        },
        duration_seconds=package.spec.duration_seconds,
        output_cadence_seconds=package.spec.output_cadence_seconds,
        history_count=len(histories),
        times_seconds=times,
        required_fields=list(REQUIRED_OUTPUT_FIELDS),
        history_inventory=inventory,
        field_minimums=minimums,
        field_maximums=maximums,
        non_finite_counts=non_finite,
        runtime_seconds=runtime_seconds,
        peak_rss_bytes=peak_rss_bytes,
        numbered_history_bytes=sum(path.stat().st_size for path in histories),
        retained_run_bytes=_directory_bytes(package.package_dir),
        available_free_bytes_after_validation=shutil.disk_usage(package.package_dir).free,
        source_customization=source_customization,
        runtime_warnings=warnings,
        normal_completion=True,
    )
    evidence_path = package.package_dir / "supercell_presentation_evidence.json"
    _write_json(evidence_path, evidence.model_dump(mode="json"))
    current = load_run_manifest(package.manifest_path)
    processed = list(dict.fromkeys([*current.outputs.processed_artifacts, str(evidence_path)]))
    write_run_manifest(
        package.manifest_path,
        current.model_copy(
            update={
                "outputs": current.outputs.model_copy(update={"processed_artifacts": processed}),
                "validation_status": ValidationStatus.VALID,
                "manual_validation_status": (
                    f"issue_444_straight_line_{package.spec.kind}_native_validated"
                    if package.spec.hodograph == "straight_line"
                    else f"issue_421_{package.spec.kind}_native_validated"
                ),
                "updated_at": datetime.now(UTC),
            }
        ),
    )
    return evidence


def _accepted_source_identity(settings: CloudChamberSettings) -> dict[str, str]:
    source_dir = settings.runtime_home.expanduser() / "runs" / SOURCE_RUN_ID
    manifest_path = source_dir / "run_manifest.json"
    evidence_path = source_dir / SOURCE_EVIDENCE_FILENAME
    if not manifest_path.is_file() or not evidence_path.is_file():
        raise SupercellPresentationError("Accepted Gate B source run is unavailable.")
    manifest = load_run_manifest(manifest_path)
    if (
        manifest.run_id != SOURCE_RUN_ID
        or manifest.scenario.id != SOURCE_CASE_ID
        or manifest.lifecycle_state != LifecycleState.COMPLETED
        or manifest.execution.exit_code != 0
    ):
        raise SupercellPresentationError("Accepted Gate B source manifest is invalid.")
    evidence = json.loads(evidence_path.read_text())
    if (
        evidence.get("run_id") != SOURCE_RUN_ID
        or evidence.get("case_id") != SOURCE_CASE_ID
        or evidence.get("final_disposition") != "advance_to_storm_examination_validation"
        or evidence.get("manual_structural_review", {}).get("judgment")
        != "supports_coherent_persistent_rotating_supercell"
    ):
        raise SupercellPresentationError("Accepted Gate B evidence is invalid.")
    return {
        "run_id": SOURCE_RUN_ID,
        "case_id": SOURCE_CASE_ID,
        "manifest_sha256": sha256_file(manifest_path),
        "evidence_sha256": sha256_file(evidence_path),
    }


def _prior_execution(
    settings: CloudChamberSettings,
    spec: SupercellPresentationSpec,
) -> list[str]:
    prior: list[str] = []
    for path in sorted((settings.runtime_home.expanduser() / "runs").glob("*/run_manifest.json")):
        try:
            manifest = load_run_manifest(path)
        except (OSError, ValueError):
            continue
        if manifest.run_id == spec.run_id or manifest.scenario.id != spec.case_id:
            continue
        if manifest.lifecycle_state not in {LifecycleState.CREATED, LifecycleState.PACKAGED}:
            prior.append(manifest.run_id)
    return prior


def _completed_final_campaign_runs(runs_dir: Path) -> set[str]:
    completed: set[str] = set()
    for run_id in FINAL_CAMPAIGN_RUN_IDS:
        run_dir = runs_dir / run_id
        manifest_path = run_dir / "run_manifest.json"
        evidence_path = run_dir / "supercell_presentation_evidence.json"
        if not manifest_path.is_file() or not evidence_path.is_file():
            continue
        try:
            manifest = load_run_manifest(manifest_path)
            evidence = json.loads(evidence_path.read_text())
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if (
            manifest.lifecycle_state == LifecycleState.COMPLETED
            and manifest.execution.exit_code == 0
            and manifest.validation_status == ValidationStatus.VALID
            and evidence.get("run_id") == run_id
            and evidence.get("normal_completion") is True
        ):
            completed.add(run_id)
    return completed


def _validate_completed_source_customization(
    *,
    manifest: RunManifest,
    spec: SupercellPresentationSpec,
) -> dict[str, Any] | None:
    status = manifest.cm1_source_customization_status
    if spec.hodograph == "quarter_circle":
        if status is not None:
            raise SupercellPresentationError(
                "Quarter-circle reference unexpectedly reports a source customization."
            )
        return None
    if not isinstance(status, dict):
        raise SupercellPresentationError(
            "Straight-line result has no applied source-customization evidence."
        )
    expected_artifact = json.loads(
        Path(manifest.generated_inputs.cm1_source_customization or "").read_text()
    )
    expected = {
        "schema_version": "cm1_source_customization_status_v1",
        "customization_kind": STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND,
        "original_target_sha256": expected_artifact.get("original_source_sha256"),
        "patched_target_sha256": expected_artifact.get("patched_source_sha256"),
        "patched_files": [str(STRAIGHT_LINE_HODOGRAPH_TARGET)],
        "no_silent_hodograph_fallback": True,
    }
    mismatched = {
        name: (status.get(name), value)
        for name, value in expected.items()
        if status.get(name) != value
    }
    if mismatched:
        raise SupercellPresentationError(
            f"Applied straight-line source customization changed: {mismatched}."
        )
    executable = Path(str(status.get("custom_executable", "")))
    expected_executable_sha256 = status.get("custom_executable_sha256")
    if (
        not executable.is_file()
        or not isinstance(expected_executable_sha256, str)
        or sha256_file(executable) != expected_executable_sha256
    ):
        raise SupercellPresentationError(
            "Applied straight-line custom executable identity is invalid."
        )
    return status


def _numbered_histories(run_dir: Path) -> list[Path]:
    return sorted(path for path in run_dir.glob("cm1out_*.nc*") if "stats" not in path.name.lower())


def _validate_grid(dataset: xr.Dataset) -> None:
    expected_sizes = {"xh": 240, "yh": 240, "zh": 60}
    actual = {name: int(dataset.sizes.get(name, -1)) for name in expected_sizes}
    if actual != expected_sizes:
        raise SupercellPresentationError(f"Native grid changed: {actual}.")
    expected_spacing = {"xh": 0.5, "yh": 0.5, "zh": 20.0 / 60.0}
    for name, spacing in expected_spacing.items():
        values = np.asarray(dataset[name].values, dtype=np.float64)
        if values.size < 2 or not np.allclose(np.diff(values), spacing, atol=2e-5, rtol=0):
            raise SupercellPresentationError(f"Native {name} spacing changed.")
    for name in REQUIRED_3D_FIELDS:
        if tuple(dim for dim in dataset[name].dims if dim != "time") != ("zh", "yh", "xh"):
            raise SupercellPresentationError(f"Required field {name} has invalid dimensions.")
    for name in REQUIRED_2D_FIELDS:
        if tuple(dim for dim in dataset[name].dims if dim != "time") != ("yh", "xh"):
            raise SupercellPresentationError(f"Required field {name} has invalid dimensions.")


def _validate_units(dataset: xr.Dataset) -> None:
    accepted = {
        "th": {"k"},
        "prs": {"pa"},
        "qv": {"kg/kg"},
        "qc": {"kg/kg"},
        "qr": {"kg/kg"},
        "qi": {"kg/kg"},
        "qs": {"kg/kg"},
        "qg": {"kg/kg"},
        "nci": {"#/kg"},
        "ncs": {"#/kg"},
        "ncr": {"#/kg"},
        "ncg": {"#/kg"},
        "dbz": {"dbz"},
        "uinterp": {"m/s"},
        "vinterp": {"m/s"},
        "winterp": {"m/s"},
        "xvort": {"1/s"},
        "yvort": {"1/s"},
        "zvort": {"1/s"},
        "rain": {"cm"},
        "prate": {"kg/m2/s"},
        "uh": {"m2/s2"},
        "cref": {"dbz"},
    }
    for name, expected in accepted.items():
        actual = str(dataset[name].attrs.get("units", "")).strip().lower().replace(" ", "")
        normalized = {value.replace(" ", "") for value in expected}
        if actual not in normalized:
            raise SupercellPresentationError(
                f"Required field {name} has unsupported units {actual!r}."
            )


def _dataset_time_seconds(dataset: xr.Dataset) -> float:
    if "time" not in dataset:
        raise SupercellPresentationError("Numbered history has no time coordinate.")
    values = normalize_time_to_seconds(
        dataset["time"].values,
        str(dataset["time"].attrs.get("units", "")),
    ).reshape(-1)
    if values.size != 1 or not np.isfinite(values[0]):
        raise SupercellPresentationError("Numbered history time is invalid.")
    return float(values[0])


def _difference_reason(
    name: str,
) -> Literal[
    "output_transport",
    "presentation_grid",
    "presentation_timing",
    "bounded_output_inventory",
    "controlled_hodograph_geometry",
]:
    if name == "iwnd":
        return "controlled_hodograph_geometry"
    if name in {"output_format", "output_filetype"}:
        return "output_transport"
    if name in {"nx", "ny", "nz", "dx", "dy", "dz"}:
        return "presentation_grid"
    if name in {"dtl", "timax", "tapfrq"}:
        return "presentation_timing"
    return "bounded_output_inventory"


def _same_assignment(actual: str | None, expected: str) -> bool:
    if actual is None:
        return False
    if actual.strip().lower() == expected.strip().lower():
        return True
    try:
        return math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=1e-9)
    except ValueError:
        return False


def _fortran_float(value: int | float) -> str:
    return f"{float(value):.1f}"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
