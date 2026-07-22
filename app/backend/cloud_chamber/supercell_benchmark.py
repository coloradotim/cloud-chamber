"""Source-locked packaging and native evidence for issue #416's supercell gate."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
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
from cloud_chamber.mountain_wave_case import (
    active_cm1_processes,
    normalize_length_to_m,
    normalize_time_to_seconds,
    parse_namelist_assignments,
    replace_namelist_assignment,
    source_manifest_sha256,
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
from cloud_chamber.settings import CloudChamberSettings, discover_cm1

CASE_ID = "cm1_r21_1_quarter_circle_supercell_official_v0"
SCENARIO_ID = CASE_ID
EVIDENCE_VERSION = "supercell_gate_b_v1"
EVIDENCE_FILENAME = "supercell_gate_b_evidence.json"
CM1_RELEASE = "21.1"
CM1_OFFICIAL_COMMIT = "0f734f64efa89a684963a66d2ac32db67617912b"
CM1_SOURCE_MANIFEST_SHA256 = "fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e"
CM1_EXECUTABLE_SHA256 = "5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1"
CM1_README_NAMELIST_SHA256 = "7b95be56db51f5c9396c59dca252cf96b918a312cc70107451f91149a34ab3b5"
CM1_SUPERCELL_NAMELIST_SHA256 = "3854f731efe6a6a9d56d6aa3db198434ccaba85bc5584b5e8ce1c5edfd3b56a4"
CM1_SUPERCELL_README_SHA256 = "3292aef3f7cdc49701015609626f55a3fd64162c88929d0992f9635dfb230200"
SOURCE_LOCK_RELATIVE_PATH = Path(
    "docs/research/storms/canonical-deep-convection-benchmark-mapping.md"
)
SOURCE_LOCK_SHA256 = "a9a4b3829ed9d6c03238702613f20ce8ee0721fe7f999b158311df7253427965"
CRITICAL_SOURCE_SHA256 = {
    "src/base.F": "9c88a1021ddde22d02680786246c52bcffb040cbd72c3c4708f24fe24eec32ef",
    "src/init3d.F": "9c45c0982ba194ea6ea74afd6a2516445cdd011fc90902091d089f4cb92dfd28",
    "src/param.F": "cac64a6cb4363c6b88367b5cb9391f1bcf2130c63ffedef6e5973c03b190c349",
    "src/writeout_nc.F": ("5023244d7ce4f9a0dde7df9c780cf5c70b675097e8467c4fbfc8125e254f4710"),
    "src/writeout.F": "bef128e897d09dbc9ae86ec13bb156794e605a7c2da1596058de53c71d640dbd",
}

NX = 120
NY = 120
NZ = 40
DX_M = 1_000.0
DY_M = 1_000.0
DZ_M = 500.0
ACTIVE_TOP_M = 20_000.0
RAYLEIGH_ONSET_M = 15_000.0
COORDINATE_SPACING_ABS_TOLERANCE_M = 0.01
MINIMUM_BOUNDARY_DISTANCE_M = 5_000.0
EXPECTED_DURATION_SECONDS = 7_200
EXPECTED_HISTORY_CADENCE_SECONDS = 900
EXPECTED_STATS_CADENCE_SECONDS = 60
EXPECTED_OUTPUT_TIMES_SECONDS = tuple(
    range(0, EXPECTED_DURATION_SECONDS + 1, EXPECTED_HISTORY_CADENCE_SECONDS)
)
RAW_HISTORY_BYTES = 572_140_800
RETAINED_STORAGE_MIN_BYTES = 650_000_000
RETAINED_STORAGE_MAX_BYTES = 900_000_000
MINIMUM_FREE_BYTES = 2 * 1024 * 1024 * 1024
OUTPUT_OVERRIDES = {
    "output_format": ("1", "2"),
    "output_filetype": ("1", "2"),
}
LOCKED_NAMELIST_VALUES = {
    "nx": "120",
    "ny": "120",
    "nz": "40",
    "dx": "1000.0",
    "dy": "1000.0",
    "dz": "500.0",
    "dtl": "6.000",
    "timax": "7200.0",
    "tapfrq": "900.0",
    "statfrq": "60.0",
    "rstfrq": "-3600.0",
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
    "ztop": "18000.0",
    "zd": "15000.0",
    "output_interp": "0",
    "output_qv": "1",
    "output_q": "1",
    "output_dbz": "1",
    "output_vort": "1",
    "output_uh": "1",
}
REQUIRED_COORDINATES = ("time", "xh", "xf", "yh", "yf", "zh", "zf")
SCALAR_3D_FIELDS = (
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
ZF_3D_FIELDS = ("tke", "kmh", "kmv", "khh", "khv", "w")
NATIVE_WIND_FIELDS = ("u", "v")
SURFACE_FIELDS = (
    "uh",
    "rain",
    "sws",
    "svs",
    "sps",
    "srs",
    "sgs",
    "sus",
    "shs",
    "rain2",
    "sws2",
    "svs2",
    "sps2",
    "srs2",
    "sgs2",
    "sus2",
    "shs2",
)
REQUIRED_OUTPUT_FIELDS = (*SCALAR_3D_FIELDS, *ZF_3D_FIELDS, *NATIVE_WIND_FIELDS, *SURFACE_FIELDS)
HYDROMETEOR_FIELDS = ("qc", "qr", "qi", "qs", "qg")
NUMBER_CONCENTRATION_FIELDS = ("nci", "ncs", "ncr", "ncg")
SWATH_FIELDS = SURFACE_FIELDS[2:]
_OUTPUT_LIKE_PATTERNS = ("cm1out*", "*.nc", "*.nc4", "*.cdf", "*.ctl", "*.dat")
_MIXING_RATIO_UNITS = {"kg/kg", "kgkg-1", "kgkg^-1", "kgkg**-1"}
_NUMBER_UNITS = {"#/kg", "kg-1", "#kg-1", "1/kg"}
_WIND_UNITS = {"m/s", "ms-1", "ms^-1", "ms**-1"}


class SupercellBenchmarkError(RuntimeError):
    """Raised when package, preflight, execution, or evaluation must stop."""


class CM1Provenance(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    release: str
    official_commit: str
    source_root: Path
    run_directory: Path
    executable_path: Path
    supercell_namelist_path: Path
    source_manifest_sha256: str
    executable_sha256: str
    readme_namelist_sha256: str
    supercell_namelist_sha256: str
    supercell_readme_sha256: str
    critical_source_sha256: dict[str, str]
    netcdf_link_evidence: list[str]

    def report_record(self) -> dict[str, Any]:
        return {
            "release": self.release,
            "official_commit": self.official_commit,
            "source_root": "configured_cm1_root",
            "run_directory": "configured_cm1_run_directory",
            "executable": "configured_cm1_run_directory/cm1.exe",
            "source_manifest_sha256": self.source_manifest_sha256,
            "executable_sha256": self.executable_sha256,
            "readme_namelist_sha256": self.readme_namelist_sha256,
            "supercell_namelist_sha256": self.supercell_namelist_sha256,
            "supercell_readme_sha256": self.supercell_readme_sha256,
            "critical_source_sha256": dict(self.critical_source_sha256),
            "netcdf_link_evidence": list(self.netcdf_link_evidence),
        }


class NamelistDifference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    official_value: str
    generated_value: str
    classification: str = "approved_output_transport_change"


class NamelistAudit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    official_sha256: str
    generated_sha256: str
    assignment_count: int
    unchanged_assignment_count: int
    byte_equivalent_after_restoring_approved_values: bool
    differences: list[NamelistDifference]
    locked_assignments: dict[str, str]
    assignments: list[dict[str, str]]


class StorageEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str
    expected_history_times_seconds: list[int]
    expected_history_count: int
    scalar_grid: list[int]
    precision_bytes: int
    scalar_grid_3d_array_count: int
    w_grid_3d_array_count: int
    native_wind_array_count: int
    scalar_2d_array_count: int
    uncompressed_history_floor_bytes: int
    retained_storage_planning_min_bytes: int
    retained_storage_planning_max_bytes: int
    compression_credit_bytes: int
    required_free_bytes: int
    available_free_bytes: int
    passed: bool


class ExecutionPreflight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checked_at: datetime
    implementation_commit: str
    checks: dict[str, bool]
    storage: StorageEstimate
    passed: bool


class ManualStructuralInterpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    initiation: str
    splitting_or_cell_multiplicity: str
    persistence: str
    rotation_updraft_relationship: str
    precipitation_organization: str
    boundary_separation: str
    upper_level_damping_interaction: str


class ManualStructuralReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_version: str = "supercell_gate_b_manual_spatial_review_v1"
    reviewer: str
    reviewed_at: datetime
    packet_manifest_filename: str
    packet_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    packet_files: list[str]
    checkpoint_times_seconds: list[int]
    judgment: Literal[
        "supports_coherent_persistent_rotating_supercell",
        "does_not_support_structural_advancement",
    ]
    interpretation: ManualStructuralInterpretation
    directly_visible: list[str]
    inferred: list[str]


class SupercellRunEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_version: str = EVIDENCE_VERSION
    case_id: str = CASE_ID
    run_id: str
    implementation_commit: str
    evaluation_commit: str
    generated_at: datetime
    lifecycle: dict[str, Any]
    provenance: dict[str, Any]
    namelist_audit: NamelistAudit
    storage_preflight: StorageEstimate
    output_inventory: dict[str, Any]
    grid_and_coordinates: dict[str, Any]
    initial_state: dict[str, Any]
    trigger: dict[str, Any]
    evolution: dict[str, Any]
    rotation_and_organization: dict[str, Any]
    boundaries_translation_and_damping: dict[str, Any]
    runtime_integrity: dict[str, Any]
    integrity_checks: dict[str, bool]
    manual_structural_review: ManualStructuralReview | None = None
    final_disposition: str
    caveats: list[str] = Field(default_factory=list)

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2) + "\n"


@dataclass(frozen=True)
class SupercellPackageResult:
    run_id: str
    package_dir: Path
    manifest_path: Path
    case_manifest_path: Path
    namelist_audit_path: Path
    storage_estimate_path: Path
    implementation_commit: str
    generated_files: tuple[Path, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def verify_gate_a_source_lock() -> dict[str, str]:
    path = _repo_root() / SOURCE_LOCK_RELATIVE_PATH
    if not path.is_file() or sha256_file(path) != SOURCE_LOCK_SHA256:
        raise SupercellBenchmarkError("The controlling Gate A artifact changed or is missing.")
    return {
        "logical_path": SOURCE_LOCK_RELATIVE_PATH.as_posix(),
        "sha256": SOURCE_LOCK_SHA256,
    }


def _netcdf_link_evidence(executable: Path) -> list[str]:
    for command in (("otool", "-L", str(executable)), ("ldd", str(executable))):
        try:
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
        except OSError:
            continue
        evidence = [
            line.strip().split(" ", 1)[0]
            for line in (completed.stdout + completed.stderr).splitlines()
            if "netcdf" in line.lower()
        ]
        if evidence:
            return [Path(item).name for item in evidence]
    return []


def collect_cm1_provenance(settings: CloudChamberSettings) -> CM1Provenance:
    discovery = discover_cm1(settings)
    if not discovery.ready or settings.cm1_root is None or settings.cm1_run_dir is None:
        raise SupercellBenchmarkError(
            "Configured CM1 runtime is not ready: " + "; ".join(discovery.missing)
        )
    root = settings.cm1_root.resolve()
    run_directory = settings.cm1_run_dir.resolve()
    executable = run_directory / "cm1.exe"
    namelist = root / "run/config_files/supercell/namelist.input"
    expected = {
        executable: CM1_EXECUTABLE_SHA256,
        root / "README.namelist": CM1_README_NAMELIST_SHA256,
        namelist: CM1_SUPERCELL_NAMELIST_SHA256,
        root / "run/config_files/supercell/README": CM1_SUPERCELL_README_SHA256,
        **{root / name: digest for name, digest in CRITICAL_SOURCE_SHA256.items()},
    }
    mismatches: list[str] = []
    for path, digest in expected.items():
        logical = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
        if not path.is_file():
            mismatches.append(f"missing:{logical}")
        elif sha256_file(path) != digest:
            mismatches.append(f"sha256_mismatch:{logical}:{sha256_file(path)}")
    source_hash = source_manifest_sha256(root)
    if source_hash != CM1_SOURCE_MANIFEST_SHA256:
        mismatches.append(f"source_manifest_sha256_mismatch:{source_hash}")
    if mismatches:
        raise SupercellBenchmarkError(
            "Configured CM1 provenance differs from Gate A: " + "; ".join(mismatches)
        )
    link_evidence = _netcdf_link_evidence(executable)
    if not link_evidence:
        raise SupercellBenchmarkError("The pinned executable has no visible NetCDF linkage.")
    return CM1Provenance(
        release=CM1_RELEASE,
        official_commit=CM1_OFFICIAL_COMMIT,
        source_root=root,
        run_directory=run_directory,
        executable_path=executable,
        supercell_namelist_path=namelist,
        source_manifest_sha256=source_hash,
        executable_sha256=CM1_EXECUTABLE_SHA256,
        readme_namelist_sha256=CM1_README_NAMELIST_SHA256,
        supercell_namelist_sha256=CM1_SUPERCELL_NAMELIST_SHA256,
        supercell_readme_sha256=CM1_SUPERCELL_README_SHA256,
        critical_source_sha256=dict(CRITICAL_SOURCE_SHA256),
        netcdf_link_evidence=link_evidence,
    )


def render_supercell_namelist(official_text: str) -> str:
    rendered = official_text
    for name, (official, generated) in OUTPUT_OVERRIDES.items():
        actual = parse_namelist_assignments(rendered).get(name)
        if actual != official:
            raise SupercellBenchmarkError(
                f"Official namelist {name} must be {official}; found {actual!r}."
            )
        rendered = replace_namelist_assignment(rendered, name, generated)
    audit_supercell_namelist(official_text, rendered)
    return rendered


def audit_supercell_namelist(official_text: str, generated_text: str) -> NamelistAudit:
    official = parse_namelist_assignments(official_text)
    generated = parse_namelist_assignments(generated_text)
    if official.keys() != generated.keys():
        raise SupercellBenchmarkError("Generated namelist assignment set is not exact.")
    differences: list[NamelistDifference] = []
    assignments: list[dict[str, str]] = []
    for name, official_value in official.items():
        generated_value = generated[name]
        status = "unchanged"
        if generated_value != official_value:
            if OUTPUT_OVERRIDES.get(name) != (official_value, generated_value):
                raise SupercellBenchmarkError(
                    f"Unapproved namelist difference {name}: {official_value} -> {generated_value}."
                )
            status = "approved_output_transport_change"
            differences.append(
                NamelistDifference(
                    name=name,
                    official_value=official_value,
                    generated_value=generated_value,
                )
            )
        assignments.append(
            {
                "name": name,
                "official_value": official_value,
                "generated_value": generated_value,
                "status": status,
            }
        )
    if {item.name for item in differences} != set(OUTPUT_OVERRIDES):
        raise SupercellBenchmarkError("Exactly two approved output changes are required.")
    for name, expected in LOCKED_NAMELIST_VALUES.items():
        if official.get(name) != expected or generated.get(name) != expected:
            raise SupercellBenchmarkError(f"Locked assignment {name} must remain {expected}.")
    restored = generated_text
    for name, (official_value, _generated_value) in OUTPUT_OVERRIDES.items():
        restored = replace_namelist_assignment(restored, name, official_value)
    if restored != official_text:
        raise SupercellBenchmarkError(
            "Generated namelist differs outside the two approved assignment values."
        )
    return NamelistAudit(
        official_sha256=sha256_text(official_text),
        generated_sha256=sha256_text(generated_text),
        assignment_count=len(assignments),
        unchanged_assignment_count=sum(item["status"] == "unchanged" for item in assignments),
        byte_equivalent_after_restoring_approved_values=True,
        differences=differences,
        locked_assignments=dict(LOCKED_NAMELIST_VALUES),
        assignments=assignments,
    )


def render_human_namelist_audit(audit: NamelistAudit) -> str:
    lines = [
        "CM1 r21.1 official quarter-circle supercell namelist audit",
        f"Official SHA-256: {audit.official_sha256}",
        f"Generated SHA-256: {audit.generated_sha256}",
        f"Assignments audited: {audit.assignment_count}",
        "Byte-equivalent after restoring approved values: true",
        "",
        "Approved output-transport differences:",
    ]
    lines.extend(
        f"CHANGED {item.name}: {item.official_value} -> {item.generated_value}"
        for item in audit.differences
    )
    lines.extend(("", "Complete assignment audit:"))
    for item in audit.assignments:
        if item["status"] == "unchanged":
            lines.append(f"UNCHANGED {item['name']} = {item['official_value']}")
        else:
            lines.append(
                f"CHANGED {item['name']}: {item['official_value']} -> {item['generated_value']}"
            )
    return "\n".join(lines) + "\n"


def expected_output_times(namelist_text: str) -> tuple[int, ...]:
    assignments = parse_namelist_assignments(namelist_text)
    duration = int(float(assignments["timax"]))
    cadence = int(float(assignments["tapfrq"]))
    if duration <= 0 or cadence <= 0 or duration % cadence:
        raise SupercellBenchmarkError("History duration and cadence must divide exactly.")
    return tuple(range(0, duration + 1, cadence))


def estimate_storage(namelist_text: str, target: Path) -> StorageEstimate:
    assignments = parse_namelist_assignments(namelist_text)
    grid = [int(float(assignments[name])) for name in ("nx", "ny", "nz")]
    if grid != [NX, NY, NZ]:
        raise SupercellBenchmarkError(f"Storage derivation received the wrong grid: {grid}.")
    times = expected_output_times(namelist_text)
    if times != EXPECTED_OUTPUT_TIMES_SECONDS:
        raise SupercellBenchmarkError("Storage derivation received unexpected history times.")
    # Gate A derives this floor from 19 scalar 3-D, 5 w-grid 3-D, 3 native wind,
    # and 17 scalar 2-D float32 arrays per history. No compression is credited.
    per_frame = (
        19 * NX * NY * NZ
        + 5 * NX * NY * (NZ + 1)
        + (NX + 1) * NY * NZ
        + NX * (NY + 1) * NZ
        + NX * NY * (NZ + 1)
        + 17 * NX * NY
    ) * 4
    floor = per_frame * len(times)
    if floor != RAW_HISTORY_BYTES:
        raise SupercellBenchmarkError(
            f"Field-derived history floor drifted: {floor} != {RAW_HISTORY_BYTES}."
        )
    target.mkdir(parents=True, exist_ok=True)
    available = shutil.disk_usage(target).free
    return StorageEstimate(
        method=(
            "uncompressed float32 numeric floor from the complete stock output inventory; "
            "retained planning band adds NetCDF metadata, statistics, logs, and reports"
        ),
        expected_history_times_seconds=list(times),
        expected_history_count=len(times),
        scalar_grid=[NX, NY, NZ],
        precision_bytes=4,
        scalar_grid_3d_array_count=19,
        w_grid_3d_array_count=5,
        native_wind_array_count=3,
        scalar_2d_array_count=17,
        uncompressed_history_floor_bytes=floor,
        retained_storage_planning_min_bytes=RETAINED_STORAGE_MIN_BYTES,
        retained_storage_planning_max_bytes=RETAINED_STORAGE_MAX_BYTES,
        compression_credit_bytes=0,
        required_free_bytes=MINIMUM_FREE_BYTES,
        available_free_bytes=available,
        passed=available >= MINIMUM_FREE_BYTES,
    )


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")


def prior_supercell_executions(runtime_home: Path, current_run_id: str) -> list[str]:
    prior: list[str] = []
    for manifest_path in sorted((runtime_home / "runs").glob("*/run_manifest.json")):
        try:
            manifest = load_run_manifest(manifest_path)
        except (OSError, ValueError):
            continue
        if manifest.run_id == current_run_id or manifest.scenario.id != SCENARIO_ID:
            continue
        if manifest.lifecycle_state not in {LifecycleState.CREATED, LifecycleState.PACKAGED}:
            prior.append(manifest.run_id)
    return prior


def generate_supercell_package(
    *, settings: CloudChamberSettings, run_id: str
) -> SupercellPackageResult:
    implementation_commit = verified_clean_git_commit()
    source_lock = verify_gate_a_source_lock()
    provenance = collect_cm1_provenance(settings)
    active = active_cm1_processes()
    if active:
        raise SupercellBenchmarkError(f"CM1/MPI is already active: {active}")
    prior = prior_supercell_executions(settings.runtime_home.expanduser(), run_id)
    if prior:
        raise SupercellBenchmarkError(f"A prior Gate B execution forbids another: {prior}")

    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    if package_dir.exists():
        raise SupercellBenchmarkError(f"Run package already exists: {run_id}")
    package_dir.mkdir(parents=True)
    paths = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "namelist": package_dir / "namelist.input",
        "runtime_checklist": package_dir / "runtime_file_checklist.json",
        "namelist_audit": package_dir / "official_namelist_diff.json",
        "namelist_audit_text": package_dir / "official_namelist_diff.txt",
        "storage_estimate": package_dir / "storage_estimate.json",
        "package_report": package_dir / "package_report.json",
    }
    try:
        official_text = provenance.supercell_namelist_path.read_text()
        generated_text = render_supercell_namelist(official_text)
        audit = audit_supercell_namelist(official_text, generated_text)
        storage = estimate_storage(generated_text, package_dir)
        if not storage.passed:
            raise SupercellBenchmarkError("At least 2.0 GiB free space is required.")
        checklist = {
            "status": "empty_external_scientific_runtime_file_inventory",
            "consumed_files": [],
            "required_files": [],
            "source_candidates": {},
            "scientific_state_sources": [
                "CM1 src/base.F isnd=5 analytic Weisman-Klemp sounding",
                "CM1 src/base.F iwnd=2 analytic quarter-circle wind profile",
                "CM1 src/init3d.F iinit=1 deterministic warm bubble",
            ],
            "explicitly_not_created_or_staged": ["input_sounding", "LANDUSE.TBL", "perts.dat"],
        }
        paths["namelist"].write_text(generated_text)
        _write_json(paths["runtime_checklist"], checklist)
        _write_json(paths["namelist_audit"], audit.model_dump(mode="json"))
        paths["namelist_audit_text"].write_text(render_human_namelist_audit(audit))
        _write_json(paths["storage_estimate"], storage.model_dump(mode="json"))
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
            "case_id": CASE_ID,
            "scenario_id": SCENARIO_ID,
            "run_id": run_id,
            "authority_state": "issue_416_gate_b_research_not_product",
            "implementation_commit": implementation_commit,
            "gate_a_source_lock": source_lock,
            "cm1_provenance": provenance.report_record(),
            "namelist_audit": audit.model_dump(mode="json"),
            "runtime_file_checklist": checklist,
            "storage_estimate": storage.model_dump(mode="json"),
            "generated_input_sha256": generated_hashes,
            "execution_authorization": {
                "duration_seconds": EXPECTED_DURATION_SECONDS,
                "process_count": 1,
                "smoke_process_allowed": False,
                "retry_allowed": False,
                "rerun_allowed": False,
                "tuning_allowed": False,
                "mpi_allowed": False,
            },
            "run_recipe": None,
            "recipe_id": None,
        }
        _write_json(paths["case_manifest"], case_manifest)
        now = datetime.now(UTC)
        manifest = RunManifest(
            run_id=run_id,
            scenario=ScenarioReference(id=SCENARIO_ID, schema_version=EVIDENCE_VERSION),
            controls={},
            run_configuration={
                "case_id": CASE_ID,
                "gate_a_source_lock": source_lock,
                "source_lock": provenance.report_record(),
                "duration_seconds": EXPECTED_DURATION_SECONDS,
                "history_cadence_seconds": EXPECTED_HISTORY_CADENCE_SECONDS,
                "stats_cadence_seconds": EXPECTED_STATS_CADENCE_SECONDS,
                "expected_history_count": len(EXPECTED_OUTPUT_TIMES_SECONDS),
                "generated_input_sha256": generated_hashes,
                "external_scientific_runtime_files": [],
                "run_recipe": None,
                "recipe_id": None,
            },
            physical_question=(
                "Does the exact stock CM1 r21.1 quarter-circle benchmark produce a "
                "trustworthy deep precipitating rotating supercell through 120 minutes?"
            ),
            expected_diagnostics=[
                "complete_native_field_inventory",
                "analytic_initial_state_and_trigger",
                "deep_multispecies_precipitating_convection",
                "joint_rotation_and_organization",
                "boundary_translation_and_damping_integrity",
            ],
            generated_inputs=GeneratedInputs(
                run_directory=str(package_dir),
                manifest_path=str(paths["manifest"]),
                namelist_input=str(paths["namelist"]),
                input_sounding=None,
                dry_run_report=str(paths["package_report"]),
                runtime_file_checklist=[str(paths["runtime_checklist"])],
            ),
            runtime_paths=RuntimePaths(runtime_home=str(settings.runtime_home.expanduser())),
            app=AppMetadata(app_version=__version__, commit=implementation_commit),
            lifecycle_state=LifecycleState.PACKAGED,
            validation_status=ValidationStatus.VALID,
            provenance=ProvenanceMetadata(product_state=ProductState.PACKAGED_DRY_RUN_OUTPUT),
            created_at=now,
            updated_at=now,
            user=UserMetadata(name="Official CM1 r21.1 quarter-circle supercell benchmark"),
            run_recipe=None,
            recipe_id=None,
            required_output_fields=list(REQUIRED_OUTPUT_FIELDS),
            input_source="CM1_r21.1_analytic_isnd5_iwnd2_iinit1",
            trigger_type="source_defined_deterministic_warm_bubble",
            trigger_parameters={
                "center": "domain_center",
                "center_agl_m": 1400.0,
                "horizontal_radius_m": 10000.0,
                "vertical_radius_m": 1400.0,
                "maximum_theta_perturbation_k": 1.0,
                "random_perturbation": False,
                "pressure_balancing": False,
                "maintain_rh": False,
            },
            expected_outputs=["nine_numbered_native_netcdf_histories", "one_stats_netcdf"],
            run_limitations=[
                "stock_cm1_r21_1_benchmark_not_observed_storm",
                "warm_bubble_is_an_initiation_device",
                "open_lateral_boundaries_and_15_to_20_km_rayleigh_layer",
                "research_evidence_not_product_approval",
            ],
            manual_validation_status="issue_416_native_evidence_pending",
        )
        write_run_manifest(paths["manifest"], manifest)
        _write_json(
            paths["package_report"],
            {
                "status": "source_locked_package_complete_not_executed",
                "case_id": CASE_ID,
                "run_id": run_id,
                "implementation_commit": implementation_commit,
                "approved_namelist_differences": [
                    item.model_dump(mode="json") for item in audit.differences
                ],
                "external_scientific_runtime_files": [],
                "generated_input_sha256": generated_hashes,
                "execute_requires_explicit_flag": "--execute",
            },
        )
    except Exception:
        shutil.rmtree(package_dir, ignore_errors=True)
        raise
    return SupercellPackageResult(
        run_id=run_id,
        package_dir=package_dir,
        manifest_path=paths["manifest"],
        case_manifest_path=paths["case_manifest"],
        namelist_audit_path=paths["namelist_audit"],
        storage_estimate_path=paths["storage_estimate"],
        implementation_commit=implementation_commit,
        generated_files=tuple(paths.values()),
    )


def load_supercell_package(
    *, settings: CloudChamberSettings, run_id: str
) -> SupercellPackageResult:
    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    names = {
        "manifest": "run_manifest.json",
        "case_manifest": "case_manifest.json",
        "namelist_audit": "official_namelist_diff.json",
        "storage_estimate": "storage_estimate.json",
    }
    paths = {name: package_dir / filename for name, filename in names.items()}
    missing = sorted(path.name for path in paths.values() if not path.is_file())
    if missing:
        raise SupercellBenchmarkError(f"Supercell package is incomplete: {missing}")
    manifest = load_run_manifest(paths["manifest"])
    case_manifest = json.loads(paths["case_manifest"].read_text())
    implementation_commit = case_manifest.get("implementation_commit")
    if (
        manifest.run_id != run_id
        or manifest.scenario.id != SCENARIO_ID
        or not isinstance(implementation_commit, str)
        or manifest.app.commit != implementation_commit
    ):
        raise SupercellBenchmarkError("Existing package identity is invalid.")
    return SupercellPackageResult(
        run_id=run_id,
        package_dir=package_dir,
        manifest_path=paths["manifest"],
        case_manifest_path=paths["case_manifest"],
        namelist_audit_path=paths["namelist_audit"],
        storage_estimate_path=paths["storage_estimate"],
        implementation_commit=implementation_commit,
        generated_files=tuple(path for path in package_dir.iterdir() if path.is_file()),
    )


def load_manual_structural_review(path: Path) -> ManualStructuralReview:
    review_path = path.expanduser().resolve()
    try:
        review = ManualStructuralReview.model_validate_json(review_path.read_text())
    except (OSError, ValueError) as exc:
        raise SupercellBenchmarkError(f"Manual structural review is invalid: {exc}") from exc
    if Path(review.packet_manifest_filename).name != review.packet_manifest_filename:
        raise SupercellBenchmarkError("Packet manifest must be a basename beside the review file.")
    if any(Path(name).name != name for name in review.packet_files):
        raise SupercellBenchmarkError("Packet files must be basenames beside the review file.")
    expected_times = [2700, 4500, 5400, 7200]
    if review.checkpoint_times_seconds != expected_times:
        raise SupercellBenchmarkError(f"Manual review checkpoints must be {expected_times}.")
    manifest_path = review_path.parent / review.packet_manifest_filename
    if not manifest_path.is_file() or sha256_file(manifest_path) != review.packet_manifest_sha256:
        raise SupercellBenchmarkError("Manual review packet manifest identity does not match.")
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SupercellBenchmarkError(f"Review packet manifest is invalid: {exc}") from exc
    manifest_files = [item.get("filename") for item in manifest.get("files", [])]
    if manifest_files != review.packet_files:
        raise SupercellBenchmarkError("Manual review packet file inventory does not match.")
    if manifest.get("checkpoint_times_seconds") != expected_times:
        raise SupercellBenchmarkError("Review packet checkpoint inventory does not match.")
    return review


def _existing_output_like_paths(package_dir: Path) -> list[str]:
    found = {
        path.name
        for pattern in _OUTPUT_LIKE_PATTERNS
        for path in package_dir.glob(pattern)
        if path.name != "official_namelist_diff.txt"
    }
    return sorted(found)


def preflight_supercell_package(
    *, settings: CloudChamberSettings, package: SupercellPackageResult
) -> ExecutionPreflight:
    implementation_commit = verified_clean_git_commit()
    if implementation_commit != package.implementation_commit:
        raise SupercellBenchmarkError("Package and clean implementation commits differ.")
    source_lock = verify_gate_a_source_lock()
    provenance = collect_cm1_provenance(settings)
    manifest = load_run_manifest(package.manifest_path)
    case_manifest = json.loads(package.case_manifest_path.read_text())
    if manifest.lifecycle_state != LifecycleState.PACKAGED:
        raise SupercellBenchmarkError("Only a packaged, never-started run may pass preflight.")
    if manifest.app.commit != implementation_commit:
        raise SupercellBenchmarkError("Run manifest implementation commit changed.")
    if case_manifest.get("gate_a_source_lock") != source_lock:
        raise SupercellBenchmarkError("Gate A source-lock identity changed.")
    official_text = provenance.supercell_namelist_path.read_text()
    namelist_path = Path(manifest.generated_inputs.namelist_input or "")
    audit = audit_supercell_namelist(official_text, namelist_path.read_text())
    stored_audit = NamelistAudit.model_validate(json.loads(package.namelist_audit_path.read_text()))
    if audit != stored_audit:
        raise SupercellBenchmarkError("Generated namelist audit changed after packaging.")
    try:
        verified_hashes = verify_generated_input_identity(manifest)
    except GeneratedInputIdentityError as exc:
        raise SupercellBenchmarkError(str(exc)) from exc
    if verified_hashes != case_manifest.get("generated_input_sha256"):
        raise SupercellBenchmarkError("Generated-input hash inventory changed.")
    checklist = json.loads((package.package_dir / "runtime_file_checklist.json").read_text())
    if (
        checklist.get("consumed_files") != []
        or checklist.get("required_files") != []
        or (package.package_dir / "input_sounding").exists()
    ):
        raise SupercellBenchmarkError("External scientific runtime-file inventory is not empty.")
    active = active_cm1_processes()
    if active:
        raise SupercellBenchmarkError(f"Another CM1/MPI process is active: {active}")
    prior = prior_supercell_executions(settings.runtime_home.expanduser(), package.run_id)
    if prior:
        raise SupercellBenchmarkError(f"A prior Gate B execution forbids this process: {prior}")
    output_paths = _existing_output_like_paths(package.package_dir)
    if output_paths:
        raise SupercellBenchmarkError(f"Package already contains output-like files: {output_paths}")
    stored_storage = StorageEstimate.model_validate(
        json.loads(package.storage_estimate_path.read_text())
    )
    available = shutil.disk_usage(package.package_dir).free
    storage = stored_storage.model_copy(
        update={"available_free_bytes": available, "passed": available >= MINIMUM_FREE_BYTES}
    )
    checks = {
        "clean_worktree_and_commit_match": True,
        "gate_a_artifact_hash_matches": True,
        "all_pinned_cm1_hashes_match": True,
        "netcdf_support_linked": bool(provenance.netcdf_link_evidence),
        "complete_namelist_audit_has_exact_two_changes": len(audit.differences) == 2,
        "output_interp_remains_native": audit.locked_assignments["output_interp"] == "0",
        "generated_input_hashes_match": bool(verified_hashes),
        "external_scientific_runtime_file_inventory_empty": True,
        "expected_history_times_exact": expected_output_times(namelist_path.read_text())
        == EXPECTED_OUTPUT_TIMES_SECONDS,
        "field_derived_storage_floor_exact": (
            storage.uncompressed_history_floor_bytes == RAW_HISTORY_BYTES
        ),
        "no_compression_credit": storage.compression_credit_bytes == 0,
        "at_least_two_gib_free": storage.passed,
        "no_active_cm1_or_mpi": True,
        "no_prior_execution": True,
        "target_has_no_output": True,
    }
    preflight = ExecutionPreflight(
        checked_at=datetime.now(UTC),
        implementation_commit=implementation_commit,
        checks=checks,
        storage=storage,
        passed=all(checks.values()),
    )
    _write_json(
        package.package_dir / "execution_preflight.json",
        preflight.model_dump(mode="json"),
    )
    return preflight


def _accepted_model_paths(paths: list[Path]) -> list[Path]:
    return sorted(
        path
        for path in paths
        if path.is_file()
        and path.name.startswith("cm1out_")
        and "stats" not in path.name.lower()
        and path.suffix.lower() in {".nc", ".nc4", ".cdf"}
    )


def _dataset_time_seconds(dataset: xr.Dataset) -> float:
    if "time" not in dataset:
        raise SupercellBenchmarkError("Numbered history has no time coordinate.")
    values = normalize_time_to_seconds(
        dataset["time"].values,
        str(dataset["time"].attrs.get("units", "")),
    ).reshape(-1)
    if values.size != 1 or not np.isfinite(values[0]):
        raise SupercellBenchmarkError("Each numbered history must contain one finite time.")
    return float(values[0])


def _normalized_coordinates(
    dataset: xr.Dataset,
) -> dict[str, np.ndarray[Any, np.dtype[np.float64]]]:
    coordinates: dict[str, np.ndarray[Any, np.dtype[np.float64]]] = {}
    for name in ("xh", "xf", "yh", "yf", "zh", "zf"):
        if name not in dataset:
            raise SupercellBenchmarkError(f"Required coordinate {name} is missing.")
        coordinates[name] = normalize_length_to_m(
            dataset[name].values,
            str(dataset[name].attrs.get("units", "")),
        ).astype(np.float64)
    return coordinates


def _same_coordinates(
    expected: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
    actual: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
) -> bool:
    return all(
        expected[name].shape == actual[name].shape and np.array_equal(expected[name], actual[name])
        for name in expected
    )


def _coordinate_spacing_matches(
    coordinate_m: np.ndarray[Any, np.dtype[np.float64]],
    expected_spacing_m: float,
) -> bool:
    deltas = np.diff(coordinate_m)
    return bool(
        deltas.size > 0
        and np.all(np.isfinite(deltas))
        and np.allclose(
            deltas,
            expected_spacing_m,
            rtol=0.0,
            atol=COORDINATE_SPACING_ABS_TOLERANCE_M,
        )
    )


def _field(
    dataset: xr.Dataset,
    name: str,
    dimensions: tuple[str, ...],
) -> np.ndarray[Any, np.dtype[np.float64]]:
    if name not in dataset:
        raise SupercellBenchmarkError(f"Required native field {name} is missing.")
    item = dataset[name]
    if "time" in item.dims:
        if item.sizes["time"] != 1:
            raise SupercellBenchmarkError(f"{name} has more than one time in a numbered file.")
        item = item.isel(time=0)
    for dim in list(item.dims):
        if dim not in dimensions and item.sizes[dim] == 1:
            item = item.isel({dim: 0})
    if set(item.dims) != set(dimensions):
        raise SupercellBenchmarkError(
            f"{name} dimensions are {tuple(item.dims)}; expected {dimensions}."
        )
    return np.asarray(item.transpose(*dimensions).values, dtype=np.float64)


def _normalized_unit(value: str) -> str:
    return value.strip().lower().replace(" ", "")


def _require_units(dataset: xr.Dataset, name: str, accepted: set[str]) -> None:
    actual = _normalized_unit(str(dataset[name].attrs.get("units", "")))
    normalized = {_normalized_unit(value) for value in accepted}
    if actual not in normalized:
        raise SupercellBenchmarkError(
            f"Required field {name} has unsupported units {actual!r}; accepted={sorted(accepted)}."
        )


def _validate_required_units(dataset: xr.Dataset) -> None:
    for name in HYDROMETEOR_FIELDS + ("qv",):
        _require_units(dataset, name, _MIXING_RATIO_UNITS)
    for name in NUMBER_CONCENTRATION_FIELDS:
        _require_units(dataset, name, _NUMBER_UNITS)
    for name in ("u", "v", "w", "uinterp", "vinterp", "winterp"):
        _require_units(dataset, name, _WIND_UNITS)
    _require_units(dataset, "th", {"k"})
    _require_units(dataset, "prs", {"pa"})


def _fill_count(item: xr.DataArray, values: np.ndarray[Any, np.dtype[Any]]) -> int:
    candidates = [item.attrs.get("_FillValue"), item.attrs.get("missing_value")]
    count = 0
    for candidate in candidates:
        if candidate is None:
            continue
        try:
            count = max(count, int(np.count_nonzero(values == candidate)))
        except (TypeError, ValueError):
            continue
    return count


def _variable_evidence(item: xr.DataArray) -> dict[str, Any]:
    values = np.asarray(item.values)
    numeric = np.issubdtype(values.dtype, np.number)
    finite_count: int | None = None
    non_finite_count: int | None = None
    minimum: float | None = None
    maximum: float | None = None
    fill_count: int | None = None
    if numeric:
        finite = np.isfinite(values)
        finite_count = int(np.count_nonzero(finite))
        non_finite_count = int(values.size - finite_count)
        fill_count = _fill_count(item, values)
        if finite_count:
            minimum = float(np.nanmin(values))
            maximum = float(np.nanmax(values))
    return {
        "dimensions": list(item.dims),
        "shape": list(item.shape),
        "units": str(item.attrs.get("units", "")),
        "dtype": str(values.dtype),
        "staggering": _staggering(tuple(str(dim) for dim in item.dims)),
        "fill_count": fill_count,
        "finite_count": finite_count,
        "non_finite_count": non_finite_count,
        "minimum": minimum,
        "maximum": maximum,
    }


def _staggering(dimensions: tuple[str, ...]) -> str:
    spatial = set(dimensions)
    if "xf" in spatial:
        return "native_x_staggered"
    if "yf" in spatial:
        return "native_y_staggered"
    if "zf" in spatial:
        return "native_z_staggered"
    if {"xh", "yh", "zh"}.issubset(spatial):
        return "scalar_interpolated_or_scalar_native"
    if {"xh", "yh"}.issubset(spatial):
        return "scalar_surface"
    return "coordinate_or_metadata"


def _require_fields(dataset: xr.Dataset) -> None:
    missing_fields = sorted(set(REQUIRED_OUTPUT_FIELDS) - set(dataset.data_vars))
    missing_coordinates = sorted(set(REQUIRED_COORDINATES) - set(dataset.variables))
    if missing_fields or missing_coordinates:
        raise SupercellBenchmarkError(
            f"Native output inventory incomplete; fields={missing_fields}, "
            f"coordinates={missing_coordinates}."
        )


def _validate_dimensions(dataset: xr.Dataset) -> None:
    for name in SCALAR_3D_FIELDS:
        _field(dataset, name, ("zh", "yh", "xh"))
    for name in ZF_3D_FIELDS:
        _field(dataset, name, ("zf", "yh", "xh"))
    _field(dataset, "u", ("zh", "yh", "xf"))
    _field(dataset, "v", ("zh", "yf", "xh"))
    for name in SURFACE_FIELDS:
        _field(dataset, name, ("yh", "xh"))


def _location_3d(
    values: np.ndarray[Any, np.dtype[np.float64]],
    x_m: np.ndarray[Any, np.dtype[np.float64]],
    y_m: np.ndarray[Any, np.dtype[np.float64]],
    z_m: np.ndarray[Any, np.dtype[np.float64]],
    *,
    maximum: bool,
) -> dict[str, float]:
    index = np.unravel_index(np.argmax(values) if maximum else np.argmin(values), values.shape)
    k, j, i = (int(value) for value in index)
    return {"x_m": float(x_m[i]), "y_m": float(y_m[j]), "z_m": float(z_m[k])}


def _location_2d(
    values: np.ndarray[Any, np.dtype[np.float64]],
    x_m: np.ndarray[Any, np.dtype[np.float64]],
    y_m: np.ndarray[Any, np.dtype[np.float64]],
    *,
    maximum: bool,
) -> dict[str, float]:
    index = np.unravel_index(np.argmax(values) if maximum else np.argmin(values), values.shape)
    j, i = (int(value) for value in index)
    return {"x_m": float(x_m[i]), "y_m": float(y_m[j])}


def _hydrometeor_evidence(
    dataset: xr.Dataset,
    zh_m: np.ndarray[Any, np.dtype[np.float64]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in HYDROMETEOR_FIELDS:
        values = _field(dataset, name, ("zh", "yh", "xh"))
        positive = values > 0.0
        levels = np.where(np.any(positive, axis=(1, 2)))[0]
        result[name] = {
            "maximum_kg_kg": float(np.max(values)),
            "positive_cell_count": int(np.count_nonzero(positive)),
            "top_m": float(zh_m[int(levels[-1])]) if levels.size else None,
        }
    return result


def _number_concentration_evidence(dataset: xr.Dataset) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in NUMBER_CONCENTRATION_FIELDS:
        values = _field(dataset, name, ("zh", "yh", "xh"))
        result[name] = {
            "minimum_per_kg": float(np.min(values)),
            "maximum_per_kg": float(np.max(values)),
            "positive_cell_count": int(np.count_nonzero(values > 0.0)),
        }
    return result


def _frame_evidence(
    dataset: xr.Dataset,
    *,
    filename: str,
    time_seconds: float,
    coordinates: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
) -> dict[str, Any]:
    w = _field(dataset, "w", ("zf", "yh", "xh"))
    winterp = _field(dataset, "winterp", ("zh", "yh", "xh"))
    zvort = _field(dataset, "zvort", ("zh", "yh", "xh"))
    dbz = _field(dataset, "dbz", ("zh", "yh", "xh"))
    rain = _field(dataset, "rain", ("yh", "xh"))
    uh = _field(dataset, "uh", ("yh", "xh"))
    primary_index = tuple(
        int(value) for value in np.unravel_index(np.argmax(winterp), winterp.shape)
    )
    k, j, i = primary_index
    updraft_mask = winterp >= max(5.0, 0.25 * float(np.max(winterp)))
    rotating_updraft = updraft_mask & (zvort > 0.005)
    damping = coordinates["zh"] >= RAYLEIGH_ONSET_M
    below_damping = coordinates["zh"] < RAYLEIGH_ONSET_M
    condensate = np.zeros_like(winterp)
    for name in HYDROMETEOR_FIELDS:
        condensate += _field(dataset, name, ("zh", "yh", "xh"))
    frame: dict[str, Any] = {
        "filename": filename,
        "time_seconds": time_seconds,
        "w_min_m_s": float(np.min(w)),
        "w_max_m_s": float(np.max(w)),
        "w_min_location": _location_3d(
            w,
            coordinates["xh"],
            coordinates["yh"],
            coordinates["zf"],
            maximum=False,
        ),
        "w_max_location": _location_3d(
            w,
            coordinates["xh"],
            coordinates["yh"],
            coordinates["zf"],
            maximum=True,
        ),
        "primary_scalar_updraft_location": {
            "x_m": float(coordinates["xh"][i]),
            "y_m": float(coordinates["yh"][j]),
            "z_m": float(coordinates["zh"][k]),
        },
        "primary_scalar_updraft_m_s": float(winterp[primary_index]),
        "zvort_at_primary_updraft_s_1": float(zvort[primary_index]),
        "rotating_updraft_cell_count": int(np.count_nonzero(rotating_updraft)),
        "zvort_min_s_1": float(np.min(zvort)),
        "zvort_max_s_1": float(np.max(zvort)),
        "uh_min_m2_s2": float(np.min(uh)),
        "uh_max_m2_s2": float(np.max(uh)),
        "uh_max_location": _location_2d(
            uh,
            coordinates["xh"],
            coordinates["yh"],
            maximum=True,
        ),
        "dbz_min": float(np.min(dbz)),
        "dbz_max": float(np.max(dbz)),
        "dbz_30_cell_count": int(np.count_nonzero(dbz >= 30.0)),
        "rain_max": float(np.max(rain)),
        "rain_positive_cell_count": int(np.count_nonzero(rain > 0.0)),
        "rain_domain_sum": float(np.sum(rain)),
        "hydrometeors": _hydrometeor_evidence(dataset, coordinates["zh"]),
        "number_concentrations": _number_concentration_evidence(dataset),
        "swaths": {},
        "cloud_top_m": None,
        "condensate_cell_count": int(np.count_nonzero(condensate > 0.0)),
        "damping_layer": {
            "winterp_max_below_15km_m_s": float(np.max(winterp[below_damping, :, :])),
            "winterp_max_15_to_20km_m_s": float(np.max(winterp[damping, :, :])),
            "condensate_max_below_15km_kg_kg": float(np.max(condensate[below_damping, :, :])),
            "condensate_max_15_to_20km_kg_kg": float(np.max(condensate[damping, :, :])),
        },
    }
    cloud_levels = np.where(np.any(condensate > 0.0, axis=(1, 2)))[0]
    if cloud_levels.size:
        frame["cloud_top_m"] = float(coordinates["zh"][int(cloud_levels[-1])])
    for name in SWATH_FIELDS:
        values = _field(dataset, name, ("yh", "xh"))
        t0_sentinel_like = time_seconds == 0.0 and bool(
            np.all(values == -1000.0) or np.all(values == 200000.0)
        )
        frame["swaths"][name] = {
            "minimum": float(np.min(values)),
            "maximum": float(np.max(values)),
            "nonzero_cell_count": int(np.count_nonzero(values)),
            "physical_evolution_summary_eligible": time_seconds > 0.0,
            "interpretation": (
                "source_consistent_initialization_sentinel_not_physical_evidence"
                if t0_sentinel_like
                else (
                    "initialization_value_not_physical_evolution"
                    if time_seconds == 0.0
                    else "physical_accumulated_or_swath_evidence"
                )
            ),
        }
    return frame


def _initial_state_evidence(
    dataset: xr.Dataset,
    coordinates: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    th = _field(dataset, "th", ("zh", "yh", "xh"))
    prs = _field(dataset, "prs", ("zh", "yh", "xh"))
    qv = _field(dataset, "qv", ("zh", "yh", "xh"))
    u = _field(dataset, "uinterp", ("zh", "yh", "xh"))
    v = _field(dataset, "vinterp", ("zh", "yh", "xh"))
    profile = []
    for k, height in enumerate(coordinates["zh"]):
        profile.append(
            {
                "z_m": float(height),
                "theta_domain_median_k": float(np.median(th[k])),
                "pressure_domain_median_pa": float(np.median(prs[k])),
                "qv_domain_median_kg_kg": float(np.median(qv[k])),
                "u_model_relative_m_s": float(np.median(u[k])),
                "v_model_relative_m_s": float(np.median(v[k])),
                "u_ground_relative_m_s": float(np.median(u[k]) + 12.5),
                "v_ground_relative_m_s": float(np.median(v[k]) + 3.0),
            }
        )
    low_index = int(np.argmin(np.abs(coordinates["zh"] - 250.0)))
    six_index = int(np.argmin(np.abs(coordinates["zh"] - 6_000.0)))
    u0 = float(np.median(u[low_index]) + 12.5)
    v0 = float(np.median(v[low_index]) + 3.0)
    u6 = float(np.median(u[six_index]) + 12.5)
    v6 = float(np.median(v[six_index]) + 3.0)
    shear = math.hypot(u6 - u0, v6 - v0)
    theta_base = np.min(th, axis=(1, 2), keepdims=True)
    perturbation = th - theta_base
    index = tuple(
        int(value) for value in np.unravel_index(np.argmax(perturbation), perturbation.shape)
    )
    k, j, i = index
    trigger = {
        "source_identity": {
            "iinit": 1,
            "center": "domain center",
            "vertical_center_agl_m": 1400.0,
            "horizontal_radius_m": 10000.0,
            "vertical_radius_m": 1400.0,
            "maximum_theta_perturbation_k": 1.0,
            "random_perturbation": False,
            "pressure_balancing": False,
            "maintain_rh": False,
        },
        "emitted_initial_theta_perturbation_max_k": float(np.max(perturbation)),
        "emitted_max_location": {
            "x_m": float(coordinates["xh"][i]),
            "y_m": float(coordinates["yh"][j]),
            "z_m": float(coordinates["zh"][k]),
        },
        "positive_perturbation_cell_count": int(np.count_nonzero(perturbation > 0.0)),
        "interpretation": "deterministic benchmark initiation device, not an observed boundary",
    }
    initial = {
        "analytic_source": "CM1 r21.1 src/base.F isnd=5 and iwnd=2",
        "thermodynamic_profile_by_level": profile,
        "source_profile_constants": {
            "surface_theta_k": 300.0,
            "surface_pressure_pa": 100000.0,
            "pbl_qv_cap_kg_kg": 0.014,
            "tropopause_height_m": 12000.0,
            "tropopause_theta_k": 343.0,
            "tropopause_temperature_k": 213.0,
        },
        "wind_profile": {
            "quarter_circle_through_m": 2000.0,
            "constant_above_m": 6000.0,
            "source_u_at_6km_and_above_m_s": 31.0,
            "source_v_at_2km_and_above_m_s": 7.0,
            "moving_domain_subtraction_m_s": [12.5, 3.0],
            "native_wind_frame": "model_relative_after_moving_domain_subtraction",
            "ground_relative_conversion": "u_ground=u_native+12.5; v_ground=v_native+3.0",
            "emitted_surface_to_6km_vector_difference_m_s": [u6 - u0, v6 - v0],
            "emitted_surface_to_6km_shear_magnitude_m_s": shear,
            "gate_a_expected_shear_magnitude_m_s": 31.78,
        },
        "cape_cin": (
            "not recomputed as a promoted benchmark value; the paper's approximate CAPE is "
            "lineage context, while emitted theta, pressure, and qv are retained directly"
        ),
    }
    return initial, trigger


def _stats_evidence(path: Path) -> dict[str, Any]:
    with xr.open_dataset(path, decode_times=False) as dataset:
        variables = {str(name): _variable_evidence(dataset[name]) for name in dataset.variables}
        time: dict[str, Any] | None = None
        if "time" in dataset:
            values = normalize_time_to_seconds(
                dataset["time"].values,
                str(dataset["time"].attrs.get("units", "")),
            ).reshape(-1)
            time = {
                "count": int(values.size),
                "first_seconds": float(values[0]),
                "last_seconds": float(values[-1]),
                "cadence_seconds": (
                    sorted({float(value) for value in np.diff(values)}) if values.size > 1 else []
                ),
                "all_finite": bool(np.all(np.isfinite(values))),
            }
        return {
            "filename": path.name,
            "bytes": path.stat().st_size,
            "time": time,
            "variables": variables,
            "global_attributes": {str(k): str(v) for k, v in dataset.attrs.items()},
        }


def _runtime_integrity(
    package: SupercellPackageResult,
    manifest: RunManifest,
    model_paths: list[Path],
    stats_path: Path,
) -> dict[str, Any]:
    stdout_path = Path(manifest.execution.stdout_log or "")
    stderr_path = Path(manifest.execution.stderr_log or "")
    stdout = stdout_path.read_text(errors="replace") if stdout_path.is_file() else ""
    stderr = stderr_path.read_text(errors="replace") if stderr_path.is_file() else ""
    flags = [
        flag
        for flag in (
            "IEEE_INVALID_FLAG",
            "IEEE_DIVIDE_BY_ZERO",
            "IEEE_OVERFLOW_FLAG",
            "IEEE_UNDERFLOW_FLAG",
        )
        if flag in stderr
    ]
    wall: float | None = None
    if manifest.execution.started_at is not None and manifest.execution.finished_at is not None:
        wall = (manifest.execution.finished_at - manifest.execution.started_at).total_seconds()
    files = [
        path
        for path in package.package_dir.iterdir()
        if path.is_file() and path.name != EVIDENCE_FILENAME
    ]
    files.extend(path for path in (stdout_path, stderr_path) if path.is_file())
    return {
        "execution_mode": "single_local_non_mpi_process",
        "command": ["configured_cm1_run_directory/cm1.exe"],
        "recorded_command": [Path(value).name for value in manifest.execution.command],
        "process_id": manifest.execution.process_id,
        "started_at": manifest.execution.started_at,
        "finished_at": manifest.execution.finished_at,
        "wall_clock_seconds": wall,
        "planning_wall_time_seconds": [900, 1800],
        "exit_code": manifest.execution.exit_code,
        "normal_termination_marker_present": "Program terminated normally" in stdout,
        "stdout_bytes": len(stdout.encode()),
        "stderr_bytes": len(stderr.encode()),
        "floating_point_flags": flags,
        "runtime_warnings": list(manifest.outputs.runtime_warnings),
        "artifact_bytes": {
            "history": sum(path.stat().st_size for path in model_paths),
            "statistics": stats_path.stat().st_size,
            "logs": sum(path.stat().st_size for path in files if "logs" in path.parts),
            "reports_and_manifests": sum(
                path.stat().st_size
                for path in files
                if path not in model_paths and path != stats_path and "logs" not in path.parts
            ),
            "total": sum(path.stat().st_size for path in files),
        },
        "peak_memory_evidence": "not_available_from_current_local_run_manager",
    }


def _nearest_frames(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for target in (2700, 4500, 5400, 7200):
        frame = min(frames, key=lambda item: abs(float(item["time_seconds"]) - target))
        if frame not in selected:
            selected.append(frame)
    return selected


def evaluate_supercell_run(
    *,
    settings: CloudChamberSettings,
    package: SupercellPackageResult,
    manual_structural_review: ManualStructuralReview | None = None,
) -> SupercellRunEvidence:
    evaluation_commit = verified_clean_git_commit()
    manifest = load_run_manifest(package.manifest_path)
    if manifest.lifecycle_state != LifecycleState.COMPLETED or manifest.execution.exit_code != 0:
        raise SupercellBenchmarkError(
            "Native evaluation requires the one normally completed CM1 process."
        )
    if manifest.app.commit != package.implementation_commit:
        raise SupercellBenchmarkError("Completed run lost its implementation identity.")
    try:
        verify_generated_input_identity(manifest)
    except GeneratedInputIdentityError as exc:
        raise SupercellBenchmarkError(str(exc)) from exc
    provenance = collect_cm1_provenance(settings)
    official_text = provenance.supercell_namelist_path.read_text()
    generated_text = Path(manifest.generated_inputs.namelist_input or "").read_text()
    namelist_audit = audit_supercell_namelist(official_text, generated_text)
    storage = StorageEstimate.model_validate(json.loads(package.storage_estimate_path.read_text()))
    output_candidates = [Path(path) for path in manifest.outputs.netcdf_paths]
    if not output_candidates:
        output_candidates = list(package.package_dir.glob("cm1out_*.nc*"))
    model_paths = _accepted_model_paths(output_candidates)
    stats_paths = sorted(
        path
        for path in output_candidates + list(package.package_dir.glob("*stats*.nc*"))
        if path.is_file() and "stats" in path.name.lower()
    )
    stats_paths = list(dict.fromkeys(stats_paths))
    if len(model_paths) != len(EXPECTED_OUTPUT_TIMES_SECONDS):
        raise SupercellBenchmarkError(
            f"Expected nine numbered histories; found {[path.name for path in model_paths]}."
        )
    if len(stats_paths) != 1:
        raise SupercellBenchmarkError(
            f"Expected one statistics NetCDF; found {[path.name for path in stats_paths]}."
        )

    actual_times: list[float] = []
    frames: list[dict[str, Any]] = []
    inventories: list[dict[str, Any]] = []
    first_coordinates: dict[str, np.ndarray[Any, np.dtype[np.float64]]] | None = None
    first_dataset_initial: dict[str, Any] | None = None
    trigger: dict[str, Any] | None = None
    all_required_finite = True
    all_coordinates_invariant = True
    global_attributes: list[dict[str, Any]] = []
    for path in model_paths:
        with xr.open_dataset(path, decode_times=False) as dataset:
            _require_fields(dataset)
            _validate_dimensions(dataset)
            _validate_required_units(dataset)
            time_seconds = _dataset_time_seconds(dataset)
            actual_times.append(time_seconds)
            coordinates = _normalized_coordinates(dataset)
            if first_coordinates is None:
                first_coordinates = coordinates
                first_dataset_initial, trigger = _initial_state_evidence(dataset, coordinates)
            else:
                all_coordinates_invariant = all_coordinates_invariant and _same_coordinates(
                    first_coordinates, coordinates
                )
            field_inventory = {
                name: _variable_evidence(dataset[name]) for name in REQUIRED_OUTPUT_FIELDS
            }
            for evidence in field_inventory.values():
                all_required_finite = all_required_finite and evidence["non_finite_count"] == 0
            inventories.append(
                {
                    "filename": path.name,
                    "time_seconds": time_seconds,
                    "bytes": path.stat().st_size,
                    "required_fields": field_inventory,
                    "all_variables": {
                        str(name): _variable_evidence(dataset[name]) for name in dataset.variables
                    },
                }
            )
            global_attributes.append(
                {
                    "filename": path.name,
                    "attributes": {str(k): str(v) for k, v in dataset.attrs.items()},
                }
            )
            frames.append(
                _frame_evidence(
                    dataset,
                    filename=path.name,
                    time_seconds=time_seconds,
                    coordinates=coordinates,
                )
            )
    assert first_coordinates is not None
    assert first_dataset_initial is not None
    assert trigger is not None
    rounded_times = [int(round(value)) for value in actual_times]
    if rounded_times != list(EXPECTED_OUTPUT_TIMES_SECONDS):
        raise SupercellBenchmarkError(
            "History times differ; "
            f"expected={EXPECTED_OUTPUT_TIMES_SECONDS}, actual={actual_times}."
        )
    if not all_required_finite:
        raise SupercellBenchmarkError("One or more required native fields contain non-finite data.")
    if not all_coordinates_invariant:
        raise SupercellBenchmarkError("Coordinates or geometry change between histories.")
    coordinates = first_coordinates
    expected_sizes = {
        "xh": NX,
        "xf": NX + 1,
        "yh": NY,
        "yf": NY + 1,
        "zh": NZ,
        "zf": NZ + 1,
    }
    actual_sizes = {name: int(values.size) for name, values in coordinates.items()}
    if actual_sizes != expected_sizes:
        raise SupercellBenchmarkError(
            f"Emitted scalar/staggered coordinate sizes differ: {actual_sizes}."
        )
    spacing = {
        name: sorted({round(float(value), 9) for value in np.diff(coordinates[name])})
        for name in ("xh", "xf", "yh", "yf", "zh", "zf")
    }
    expected_spacing = {
        "xh": DX_M,
        "xf": DX_M,
        "yh": DY_M,
        "yf": DY_M,
        "zh": DZ_M,
        "zf": DZ_M,
    }
    if not all(
        _coordinate_spacing_matches(coordinates[name], expected)
        for name, expected in expected_spacing.items()
    ):
        raise SupercellBenchmarkError(f"Emitted coordinate spacing is not exact: {spacing}.")
    if not math.isclose(float(coordinates["zf"][-1]), ACTIVE_TOP_M):
        raise SupercellBenchmarkError("Unstretched emitted active top is not 20 km.")
    stats = _stats_evidence(stats_paths[0])
    stats_time = stats.get("time")
    if not isinstance(stats_time, dict) or stats_time.get("last_seconds") != 7200.0:
        raise SupercellBenchmarkError("Statistics stream does not reach 7,200 s.")
    cadence_values = stats_time.get("cadence_seconds", [])
    if cadence_values != [60.0]:
        raise SupercellBenchmarkError(f"Statistics cadence is not 60 s: {cadence_values}.")
    runtime = _runtime_integrity(package, manifest, model_paths, stats_paths[0])
    if not runtime["normal_termination_marker_present"]:
        raise SupercellBenchmarkError("CM1 normal-termination marker is absent.")
    disallowed_flags = set(runtime["floating_point_flags"]) - {"IEEE_UNDERFLOW_FLAG"}
    if disallowed_flags:
        raise SupercellBenchmarkError(
            f"CM1 reported disallowed floating-point flags: {sorted(disallowed_flags)}."
        )

    mature = [frame for frame in frames if float(frame["time_seconds"]) >= 2700.0]
    mature_concurrent_evidence = [
        frame
        for frame in mature
        if float(frame["w_max_m_s"]) >= 10.0
        and float(frame["dbz_max"]) >= 30.0
        and int(frame["rain_positive_cell_count"]) > 0
        and float(frame["uh_max_m2_s2"]) > 0.0
        and int(frame["rotating_updraft_cell_count"]) > 0
    ]
    species_with_material_evolution = [
        name
        for name in HYDROMETEOR_FIELDS
        if max(float(frame["hydrometeors"][name]["maximum_kg_kg"]) for frame in frames) > 1.0e-8
    ]
    concurrent_mature_evidence_present = len(mature_concurrent_evidence) >= 3
    deep_multispecies = len(species_with_material_evolution) == len(HYDROMETEOR_FIELDS)
    active_updraft_frames = [
        frame for frame in frames if float(frame["primary_scalar_updraft_m_s"]) > 0.0
    ]
    if not active_updraft_frames:
        raise SupercellBenchmarkError(
            "No positive primary updraft exists for boundary-distance evaluation."
        )
    primary_boundary_distances = []
    for frame in active_updraft_frames:
        location = frame["primary_scalar_updraft_location"]
        primary_boundary_distances.append(
            {
                "time_seconds": frame["time_seconds"],
                "x_m": location["x_m"],
                "y_m": location["y_m"],
                "west_m": float(location["x_m"] - coordinates["xh"][0]),
                "east_m": float(coordinates["xh"][-1] - location["x_m"]),
                "south_m": float(location["y_m"] - coordinates["yh"][0]),
                "north_m": float(coordinates["yh"][-1] - location["y_m"]),
            }
        )
    minimum_boundary_distance = min(
        min(item[name] for name in ("west_m", "east_m", "south_m", "north_m"))
        for item in primary_boundary_distances
    )
    integrity_checks = {
        "lifecycle_completed_exit_zero": True,
        "normal_termination_at_7200s": True,
        "nine_expected_histories_exact": True,
        "one_complete_60s_statistics_stream": True,
        "all_required_fields_present": True,
        "all_required_fields_finite": all_required_finite,
        "coordinates_invariant": all_coordinates_invariant,
        "scalar_grid_120_120_40": True,
        "uniform_spacing_1km_1km_0_5km": True,
        "active_top_20km": True,
        "flat_terrain_source_configuration": (
            parse_namelist_assignments(generated_text)["terrain_flag"] == ".false."
        ),
        "exact_two_setting_namelist_diff": len(namelist_audit.differences) == 2,
        "empty_external_scientific_file_inventory": (
            manifest.run_configuration.get("external_scientific_runtime_files") == []
        ),
        "only_underflow_warning_if_any": not disallowed_flags,
    }
    interpretable_boundaries = minimum_boundary_distance >= MINIMUM_BOUNDARY_DISTANCE_M
    automated_gate_passes = (
        all(integrity_checks.values())
        and concurrent_mature_evidence_present
        and deep_multispecies
        and interpretable_boundaries
    )
    manual_review_supports_advancement = bool(
        manual_structural_review is not None
        and manual_structural_review.judgment == "supports_coherent_persistent_rotating_supercell"
    )
    if automated_gate_passes and manual_review_supports_advancement:
        disposition = "advance_to_storm_examination_validation"
    elif automated_gate_passes and manual_structural_review is None:
        disposition = "bounded_benchmark_correction_required"
    else:
        disposition = "defer_or_reject_storms_candidate"
    return SupercellRunEvidence(
        run_id=package.run_id,
        implementation_commit=package.implementation_commit,
        evaluation_commit=evaluation_commit,
        generated_at=datetime.now(UTC),
        lifecycle={
            "state": manifest.lifecycle_state.value,
            "exit_code": manifest.execution.exit_code,
            "product_state": manifest.provenance.product_state.value,
            "manual_validation_status": manifest.manual_validation_status,
        },
        provenance={
            "gate_a": verify_gate_a_source_lock(),
            "cm1": provenance.report_record(),
        },
        namelist_audit=namelist_audit,
        storage_preflight=storage,
        output_inventory={
            "history_files": [
                {"filename": path.name, "bytes": path.stat().st_size} for path in model_paths
            ],
            "history_count": len(model_paths),
            "history_times_seconds": actual_times,
            "required_field_inventory_by_time": inventories,
            "global_attributes_by_time": global_attributes,
            "statistics": stats,
        },
        grid_and_coordinates={
            "scalar_grid": [NX, NY, NZ],
            "coordinate_sizes": actual_sizes,
            "coordinate_units_normalized_to": "m",
            "coordinate_ranges_m": {
                name: [float(np.min(values)), float(np.max(values))]
                for name, values in coordinates.items()
            },
            "spacing_m": spacing,
            "active_top_m": float(coordinates["zf"][-1]),
            "inactive_namelist_ztop_m": 18_000.0,
            "terrain": "flat; terrain_flag=.false. and no terrain field requested",
            "coordinates_invariant": all_coordinates_invariant,
            "wind_staggering": {
                "u": "native xf",
                "v": "native yf",
                "w": "native zf",
                "uinterp_vinterp_winterp": "scalar xh/yh/zh",
            },
        },
        initial_state=first_dataset_initial,
        trigger=trigger,
        evolution={
            "frames": frames,
            "hydrometeor_species_with_material_evolution": species_with_material_evolution,
            "deep_multispecies_convection": deep_multispecies,
            "checkpoint_frames": _nearest_frames(frames),
        },
        rotation_and_organization={
            "method": (
                "concurrent saved-frame screen using independent domain-wide w, reflectivity, "
                "rain, and UH evidence plus grid-cell w-positive-zvort collocation; it does not "
                "establish storm-object continuity or UH/reflectivity/rain collocation"
            ),
            "mature_concurrent_evidence_frame_times_seconds": [
                frame["time_seconds"] for frame in mature_concurrent_evidence
            ],
            "concurrent_mature_convection_and_rotating_updraft_evidence": (
                concurrent_mature_evidence_present
            ),
            "automated_structural_claim_limit": (
                "No same-object continuity, UH collocation, or precipitation/reflection "
                "organization claim is made by this Boolean screen."
            ),
            "qualitative_gate_requires_pm_scientific_review": True,
        },
        boundaries_translation_and_damping={
            "primary_updraft_boundary_distances_by_time": primary_boundary_distances,
            "minimum_primary_boundary_distance_m": minimum_boundary_distance,
            "minimum_5km_interpretability_screen": interpretable_boundaries,
            "moving_domain_subtraction_m_s": [12.5, 3.0],
            "native_winds": "model-relative",
            "translated_swaths": list(SWATH_FIELDS),
            "rayleigh_layer_m": [RAYLEIGH_ONSET_M, ACTIVE_TOP_M],
            "damping_evidence_by_time": [
                {
                    "time_seconds": frame["time_seconds"],
                    **frame["damping_layer"],
                }
                for frame in frames
            ],
        },
        runtime_integrity=runtime,
        integrity_checks=integrity_checks,
        manual_structural_review=manual_structural_review,
        final_disposition=disposition,
        caveats=[
            "The stock benchmark is not an observed storm or a validated product recipe.",
            "The warm bubble is a deterministic initiation device.",
            "Histories are 15 minutes apart; 40- and 80-minute paper figures are not "
            "exact matches.",
            "A 5 km boundary-distance screen is descriptive, not a source-supplied tolerance.",
            "qg/ncg are one hail-treated large-ice category under ihail=1.",
        ],
    )


def write_supercell_evidence(path: Path, evidence: SupercellRunEvidence) -> None:
    path.write_text(evidence.to_json_text())


def _format_number(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def render_supercell_run_report(evidence: SupercellRunEvidence) -> str:
    runtime = evidence.runtime_integrity
    inventory = evidence.output_inventory
    frames = evidence.evolution["frames"]
    wind_profile = evidence.initial_state["wind_profile"]
    boundary_evidence = evidence.boundaries_translation_and_damping
    manual_review = evidence.manual_structural_review
    concurrent_times = evidence.rotation_and_organization[
        "mature_concurrent_evidence_frame_times_seconds"
    ]
    concurrent_evidence = evidence.rotation_and_organization[
        "concurrent_mature_convection_and_rotating_updraft_evidence"
    ]
    lines = [
        "# Canonical Deep-Convection Run Report",
        "",
        "## 1. Status, decision question, and non-product boundary",
        "",
        f"**Status:** one exact Gate B process completed and was evaluated. **Disposition:** "
        f"`{evidence.final_disposition}`.",
        "",
        "Decision question: does the stock CM1 r21.1 quarter-circle benchmark produce a "
        "trustworthy deep precipitating rotating supercell suitable for later examination? "
        "This is research evidence, not a World, Recipe, UX, or product approval.",
        "",
        "## 2. Controlling Gate A artifact and accepted identity",
        "",
        f"- Case and scenario ID: `{CASE_ID}`",
        f"- Run ID: `{evidence.run_id}`",
        f"- Gate A artifact SHA-256: `{SOURCE_LOCK_SHA256}`",
        "- Accepted identity: official CM1 r21.1 quarter-circle-hodograph supercell case",
        "",
        "## 3. Implementation and report commits",
        "",
        f"The package and process used implementation commit `{evidence.implementation_commit}`. "
        f"The completed output was evaluated at `{evidence.evaluation_commit}`. This report is "
        "committed later and does not alter the executed package or retained output.",
        "",
        "## 4. CM1 provenance and controlling hashes",
        "",
        f"- Release: `{CM1_RELEASE}`",
        f"- Official commit: `{CM1_OFFICIAL_COMMIT}`",
        f"- Source manifest: `{CM1_SOURCE_MANIFEST_SHA256}`",
        f"- Executable: `{CM1_EXECUTABLE_SHA256}`",
        f"- README.namelist: `{CM1_README_NAMELIST_SHA256}`",
        f"- Official supercell namelist: `{CM1_SUPERCELL_NAMELIST_SHA256}`",
        f"- Official supercell README: `{CM1_SUPERCELL_README_SHA256}`",
    ]
    lines.extend(f"- `{name}`: `{digest}`" for name, digest in CRITICAL_SOURCE_SHA256.items())
    lines.extend(
        [
            "",
            "## 5. Complete official-versus-generated namelist diff",
            "",
            f"All {evidence.namelist_audit.assignment_count} assignments were audited. Restoring "
            "the two approved transport values makes the generated file byte-identical to the "
            "official file.",
            "",
            "| Assignment | Official | Generated | Classification |",
            "|---|---:|---:|---|",
        ]
    )
    for item in evidence.namelist_audit.assignments:
        lines.append(
            f"| `{item['name']}` | `{item['official_value']}` | "
            f"`{item['generated_value']}` | {item['status']} |"
        )
    lines.extend(
        [
            "",
            "## 6. External scientific runtime-file inventory",
            "",
            "Empty. No `input_sounding`, terrain file, land-use table, or other scientific "
            "runtime file was created or staged. Sounding, hodograph, and bubble came from the "
            "hash-pinned CM1 analytic source paths.",
            "",
            "## 7. Package, storage, and free-space preflight",
            "",
            f"The field-derived uncompressed history floor was "
            f"{evidence.storage_preflight.uncompressed_history_floor_bytes:,} bytes for nine "
            "histories. No compression was credited. The retained planning band was "
            f"{RETAINED_STORAGE_MIN_BYTES:,}-{RETAINED_STORAGE_MAX_BYTES:,} bytes; "
            f"{evidence.storage_preflight.available_free_bytes:,} bytes were free against a "
            f"{MINIMUM_FREE_BYTES:,}-byte requirement.",
            "",
            "## 8. Run identity, command, process, and lifecycle",
            "",
            f"- Command: `{runtime['command'][0]}`",
            f"- Execution mode: {runtime['execution_mode']}",
            f"- Process ID: {runtime['process_id']}",
            f"- Start: {runtime['started_at']}",
            f"- Finish: {runtime['finished_at']}",
            f"- Wall time: {_format_number(runtime['wall_clock_seconds'])} s",
            f"- Exit code: {runtime['exit_code']}",
            f"- Normal termination marker: {runtime['normal_termination_marker_present']}",
            "",
            "## 9. File and time inventory",
            "",
            "| File | Time (s) | Bytes |",
            "|---|---:|---:|",
        ]
    )
    history_times = inventory["history_times_seconds"]
    for item, time_seconds in zip(inventory["history_files"], history_times, strict=True):
        lines.append(f"| `{item['filename']}` | {time_seconds:g} | {item['bytes']:,} |")
    stats = inventory["statistics"]
    lines.append(
        f"| `{stats['filename']}` | 0-{stats['time']['last_seconds']:g} at "
        f"{stats['time']['cadence_seconds'][0]:g}-s cadence | {stats['bytes']:,} |"
    )
    lines.extend(
        [
            "",
            "## 10. Native variable inventory and integrity",
            "",
            "Every required field was read from every numbered history. Rows below retain "
            "native dimensions, units, precision, staggering, fill counts, finite counts, and "
            "global ranges.",
            "",
            "| Time | Field | Dimensions | Units | Dtype | Staggering | Fill | "
            "Non-finite | Min | Max |",
            "|---:|---|---|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for frame_inventory in inventory["required_field_inventory_by_time"]:
        for name, item in frame_inventory["required_fields"].items():
            lines.append(
                f"| {frame_inventory['time_seconds']:g} | `{name}` | "
                f"`{' x '.join(str(value) for value in item['shape'])}` | "
                f"{item['units'] or 'none'} | {item['dtype']} | {item['staggering']} | "
                f"{_format_number(item['fill_count'])} | "
                f"{_format_number(item['non_finite_count'])} | "
                f"{_format_number(item['minimum'])} | {_format_number(item['maximum'])} |"
            )
    lines.extend(
        [
            "",
            "### Statistics stream inventory",
            "",
            "| Variable | Dimensions | Units | Dtype | Fill | Non-finite | Min | Max |",
            "|---|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for name, item in stats["variables"].items():
        lines.append(
            f"| `{name}` | `{' x '.join(str(value) for value in item['shape'])}` | "
            f"{item['units'] or 'none'} | {item['dtype']} | "
            f"{_format_number(item['fill_count'])} | "
            f"{_format_number(item['non_finite_count'])} | "
            f"{_format_number(item['minimum'])} | {_format_number(item['maximum'])} |"
        )
    lines.extend(
        [
            "",
            "All statistics times were finite and covered 0-7,200 s at the stock 60-s cadence.",
            "",
            "## 11. Grid, active top, coordinates, and moving domain",
            "",
            f"The scalar grid was {NX} x {NY} x {NZ}; scalar spacing was {DX_M:g} x "
            f"{DY_M:g} x {DZ_M:g} m. Native x/y/z staggered dimensions were preserved. The "
            f"unstretched emitted z-face top was {ACTIVE_TOP_M:g} m. The inactive namelist "
            "`ztop=18000` did not control the active grid. Coordinates were invariant across all "
            "histories. Terrain was flat and no terrain field was requested.",
            "",
            "Native `u`, `v`, and `w` are on `xf`, `yf`, and `zf`; `uinterp`, `vinterp`, and "
            "`winterp` are scalar-grid products. Native winds are model-relative. Ground-relative "
            "winds add `(12.5, 3.0) m/s`.",
            "",
            "## 12. Analytic thermodynamic, hodograph, frame, and trigger verification",
            "",
            "The hash-pinned `isnd=5` source defines the Weisman-Klemp analytic thermodynamic "
            "profile; `iwnd=2` defines the quarter-circle wind through 2 km, an increase to the "
            "6-km wind, and constant wind aloft. The emitted surface-to-6-km vector difference "
            f"was {wind_profile['emitted_surface_to_6km_vector_difference_m_s']} "
            "m/s, with magnitude "
            f"{wind_profile['emitted_surface_to_6km_shear_magnitude_m_s']:.3f} "
            "m/s versus the Gate A 31.78 m/s reference.",
            "",
            "The deterministic `iinit=1` bubble was source-verified at domain center, 1,400 m "
            "AGL, with 10,000 m horizontal and 1,400 m vertical radii, 1 K maximum perturbation, "
            "no random perturbation, no pressure balancing, and `maintain_rh=false`. The initial "
            f"history's sampled maximum theta perturbation was "
            f"{evidence.trigger['emitted_initial_theta_perturbation_max_k']:.4f} K at "
            f"{evidence.trigger['emitted_max_location']}.",
            "",
            "No CAPE/CIN value was promoted from the paper; emitted theta, pressure, and moisture "
            "profiles are the native benchmark evidence.",
            "",
            "### Initial native profile",
            "",
            "| z (m) | theta (K) | pressure (Pa) | qv (kg/kg) | u model | v model | "
            "u ground | v ground |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for level in evidence.initial_state["thermodynamic_profile_by_level"]:
        lines.append(
            f"| {level['z_m']:.0f} | {level['theta_domain_median_k']:.5g} | "
            f"{level['pressure_domain_median_pa']:.7g} | "
            f"{level['qv_domain_median_kg_kg']:.5g} | "
            f"{level['u_model_relative_m_s']:.5g} | "
            f"{level['v_model_relative_m_s']:.5g} | "
            f"{level['u_ground_relative_m_s']:.5g} | "
            f"{level['v_ground_relative_m_s']:.5g} |"
        )
    lines.extend(
        [
            "",
            "## 13. Deep cloud, hydrometeors, precipitation, reflectivity, and motion",
            "",
            "| Time (min) | w min | w max | Cloud top (km) | dBZ max | Rain max | "
            "qc | qr | qi | qs | qg |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for frame in frames:
        hydro = frame["hydrometeors"]
        cloud_top = (
            float(frame["cloud_top_m"]) / 1000.0 if frame["cloud_top_m"] is not None else None
        )
        lines.append(
            f"| {float(frame['time_seconds']) / 60.0:g} | {frame['w_min_m_s']:.3g} | "
            f"{frame['w_max_m_s']:.3g} | {_format_number(cloud_top)} | "
            f"{frame['dbz_max']:.3g} | {frame['rain_max']:.3g} | "
            + " | ".join(f"{hydro[name]['maximum_kg_kg']:.3g}" for name in HYDROMETEOR_FIELDS)
            + " |"
        )
    lines.extend(
        [
            "",
            f"Materially evolving hydrometeor categories: "
            f"{', '.join(evidence.evolution['hydrometeor_species_with_material_evolution'])}. "
            "`qg`/`ncg` are treated as one hail-configured large-ice category, not double-counted.",
            "",
            "### Number-concentration maxima by time (#/kg)",
            "",
            "| Time (min) | nci | ncs | ncr | ncg |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for frame in frames:
        numbers = frame["number_concentrations"]
        lines.append(
            f"| {float(frame['time_seconds']) / 60.0:g} | "
            + " | ".join(
                f"{numbers[name]['maximum_per_kg']:.5g}" for name in NUMBER_CONCENTRATION_FIELDS
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 14. Concurrent convection, rotating-updraft evidence, and swaths",
            "",
            "| Time (min) | Primary w | zvort at primary w | zvort max | UH max | "
            "Rotating-updraft cells |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for frame in frames:
        lines.append(
            f"| {float(frame['time_seconds']) / 60.0:g} | "
            f"{frame['primary_scalar_updraft_m_s']:.3g} | "
            f"{frame['zvort_at_primary_updraft_s_1']:.3g} | "
            f"{frame['zvort_max_s_1']:.3g} | {frame['uh_max_m2_s2']:.3g} | "
            f"{frame['rotating_updraft_cell_count']} |"
        )
    lines.extend(
        [
            "",
            "Automated concurrent-evidence screen: "
            f"{concurrent_times} "
            "s. Concurrent mature convection and rotating-updraft evidence: "
            f"{concurrent_evidence}. "
            "The screen combines independent domain-wide w, reflectivity, rain, and UH checks "
            "with grid-cell w-positive-zvort collocation. It does not establish same-object "
            "continuity, UH collocation, or precipitation/reflectivity organization.",
            "",
            "### Native and translated surface-product maxima",
            "",
            "The raw t=0 fields remain in the native integrity inventory. They are excluded "
            "below because accumulated/swath products are not physical evolution evidence at "
            "initialization; uniform -1000 and 200000 values are source-consistent sentinel-like "
            "initial states for the affected extrema products.",
            "",
            "| Time (min) | Product | Maximum | Nonzero cells |",
            "|---:|---|---:|---:|",
        ]
    )
    for frame in frames:
        for name, item in frame["swaths"].items():
            if not item["physical_evolution_summary_eligible"]:
                continue
            lines.append(
                f"| {float(frame['time_seconds']) / 60.0:g} | `{name}` | "
                f"{item['maximum']:.5g} | {item['nonzero_cell_count']} |"
            )
    lines.extend(
        [
            "",
            "## 15. Structural checkpoints and manual spatial examination",
            "",
        ]
    )
    for frame in evidence.evolution["checkpoint_frames"]:
        lines.append(
            f"- **{float(frame['time_seconds']) / 60.0:g} min:** primary scalar w "
            f"{frame['primary_scalar_updraft_m_s']:.3g} m/s at "
            f"{frame['primary_scalar_updraft_location']}; max UH "
            f"{frame['uh_max_m2_s2']:.3g} m2/s2; max dBZ {frame['dbz_max']:.3g}; "
            f"rain-positive cells {frame['rain_positive_cell_count']}."
        )
    if manual_review is None:
        lines.extend(
            [
                "",
                "No hashed manual spatial review was supplied. The automated screen cannot "
                "produce an advancing structural disposition by itself.",
            ]
        )
    else:
        interpretation = manual_review.interpretation
        lines.extend(
            [
                "",
                "### Manual spatial examination",
                "",
                f"- Reviewer: `{manual_review.reviewer}`",
                f"- Reviewed at: `{manual_review.reviewed_at.isoformat()}`",
                f"- Packet manifest: `{manual_review.packet_manifest_filename}` "
                f"(`{manual_review.packet_manifest_sha256}`)",
                f"- Packet files: {', '.join(f'`{name}`' for name in manual_review.packet_files)}",
                f"- Judgment: `{manual_review.judgment}`",
                f"- Initiation: {interpretation.initiation}",
                f"- Splitting/cell multiplicity: {interpretation.splitting_or_cell_multiplicity}",
                f"- Persistence: {interpretation.persistence}",
                f"- Rotation/updraft relationship: {interpretation.rotation_updraft_relationship}",
                f"- Precipitation organization: {interpretation.precipitation_organization}",
                f"- Boundary separation: {interpretation.boundary_separation}",
                f"- Upper-level/damping interaction: "
                f"{interpretation.upper_level_damping_interaction}",
                "",
                "Directly visible:",
                "",
                *[f"- {item}" for item in manual_review.directly_visible],
                "",
                "Inferred or intentionally unresolved:",
                "",
                *[f"- {item}" for item in manual_review.inferred],
            ]
        )
    lines.extend(
        [
            "",
            "The 15-minute history cadence supports 45, 75/90, and 120-minute inspection. It "
            "does not support claims of exact 40- or 80-minute figure reproduction.",
            "",
            "## 16. Lateral boundaries, translation, and upper damping",
            "",
            f"The minimum saved-frame distance from the primary updraft to any open lateral "
            f"boundary was "
            f"{boundary_evidence['minimum_primary_boundary_distance_m']:.0f} "
            "m. The 5-km screen is descriptive because the source provides no pointwise "
            "tolerance. Native fields are in the translating model frame; the `*2` products are "
            "the emitted translated swath/rain/wind products.",
            "",
            "Vertical motion and condensate maxima were recorded separately below 15 km and "
            "inside the 15-20 km Rayleigh layer for every history. No absence of top reflection "
            "is inferred from the namelist alone.",
            "",
            "| Time (min) | w max below 15 km | w max 15-20 km | condensate max below | "
            "condensate max 15-20 km |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for item in boundary_evidence["damping_evidence_by_time"]:
        lines.append(
            f"| {float(item['time_seconds']) / 60.0:g} | "
            f"{item['winterp_max_below_15km_m_s']:.5g} | "
            f"{item['winterp_max_15_to_20km_m_s']:.5g} | "
            f"{item['condensate_max_below_15km_kg_kg']:.5g} | "
            f"{item['condensate_max_15_to_20km_kg_kg']:.5g} |"
        )
    lines.extend(
        [
            "",
            "## 17. Runtime integrity, storage, warnings, and cost",
            "",
            f"The process ran for {_format_number(runtime['wall_clock_seconds'])} s and retained "
            f"{runtime['artifact_bytes']['total']:,} bytes. History output used "
            f"{runtime['artifact_bytes']['history']:,} bytes; statistics used "
            f"{runtime['artifact_bytes']['statistics']:,}; logs used "
            f"{runtime['artifact_bytes']['logs']:,}. Floating-point flags: "
            f"{runtime['floating_point_flags'] or 'none'}. Normal termination and finite required "
            "fields were both verified. Peak memory was not captured by the current launcher.",
            "",
            "## 18. Qualitative lineage and stock-versus-paper differences",
            "",
            "The official README links this case to Weisman and Rotunno (2000), and the analytic "
            "sounding lineage is Weisman and Klemp (1982). This run reproduces the stock CM1 "
            "r21.1 configuration, not the paper's exact numerical implementation or saved figure "
            "times. Grid, microphysics, output cadence, and other stock-r21.1 details therefore "
            "remain distinct from a pixel-level paper reproduction.",
            "",
            "## 19. Cloud Chamber implications and limits",
            "",
            "This gate establishes mechanics and practical cost for one source-locked storm "
            "benchmark. It does not select a permanent World, Recipe, UI, trigger, sounding, or "
            "general storm framework. Examination and product meaning remain later decisions.",
            "",
            "## 20. Unresolved questions",
            "",
            "- PM/scientific review must inspect the attached hashed spatial packet before "
            "accepting the recorded manual structural judgment.",
            "- The launcher does not currently record peak memory.",
            "- The source supplies no pointwise boundary- or damping-contamination tolerance.",
            "- A later gate would need to define examination, not rerun or tune this benchmark.",
            "",
            "## 21. Final disposition",
            "",
            f"`{evidence.final_disposition}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_supercell_run_report(path: Path, evidence: SupercellRunEvidence) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_supercell_run_report(evidence))
