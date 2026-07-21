"""Bounded packaging and native-output evidence for CM1's dry mountain-wave case."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber import __version__
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

CASE_ID = "cm1_r21_1_dry_mountain_wave_official_v0"
SCENARIO_ID = CASE_ID
EVIDENCE_VERSION = "dry_mountain_wave_gate_b_v1"
CM1_RELEASE = "21.1"
CM1_TAG_COMMIT = "0f734f64efa89a684963a66d2ac32db67617912b"
CM1_SOURCE_TAG = f"https://github.com/NCAR/CM1/tree/{CM1_TAG_COMMIT}"
CM1_EXECUTABLE_SHA256 = "5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1"
CM1_SOURCE_MANIFEST_SHA256 = "fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e"
CM1_README_NAMELIST_SHA256 = "7b95be56db51f5c9396c59dca252cf96b918a312cc70107451f91149a34ab3b5"
CM1_README_TERRAIN_SHA256 = "ed00d9c3867b087fc0d2ef0b6b6141869a3d0025d010b73ec9411d105166e82d"
CM1_MOUNTAIN_WAVE_NAMELIST_SHA256 = (
    "9578207be201d0f250f6398414e1afb539e6f1b842c2448a10910b5ffd5c15b5"
)

CRITICAL_SOURCE_HASHES = {
    "src/init_terrain.F": "813e579983c0f55347d5eb54828709eedb5911a08587b216ea668c9d03cbca7c",
    "src/base.F": "9c88a1021ddde22d02680786246c52bcffb040cbd72c3c4708f24fe24eec32ef",
    "src/input.F": "e8b3bb25e0b624d79da7d361a2027431b55f98434abfe19b4385d7c7e1692663",
    "src/param.F": "cac64a6cb4363c6b88367b5cb9391f1bcf2130c63ffedef6e5973c03b190c349",
    "src/bc.F": "5b7353a08b13eb9f69e4b89e250aec0e7918df3c93bd48c8539ab850787716e3",
    "src/writeout.F": "bef128e897d09dbc9ae86ec13bb156794e605a7c2da1596058de53c71d640dbd",
    "src/writeout_nc.F": "5023244d7ce4f9a0dde7df9c780cf5c70b675097e8467c4fbfc8125e254f4710",
}

OUTPUT_OVERRIDES = {
    "output_format": ("1", "2"),
    "output_filetype": ("1", "2"),
    "output_interp": ("1", "0"),
}
INACTIVE_AUDIT_VALUES = {
    "ibalance": "0",
    "axisymm": "0",
    "imove": "0",
    "alphobc": "60.0",
    "nudgeobc": "0",
    "roflux": "0",
    "xhd": "100000.0",
    "hrdamp": "0",
    "ztop": "18000.0",
}
REQUIRED_OUTPUT_FIELDS = ("zs", "zhval", "th", "prs", "u", "v", "w")
REQUIRED_COORDINATES = ("time", "xh", "xf", "yh", "yf", "zh", "zf")
MODEL_OUTPUT_PATTERN = re.compile(r"^cm1out_(?P<number>\d+)\.nc4?$")
EXPECTED_DURATION_SECONDS = 2_160
EXPECTED_OUTPUT_CADENCE_SECONDS = 216
EXPECTED_OUTPUT_TIMES_SECONDS = tuple(
    range(0, EXPECTED_DURATION_SECONDS + 1, EXPECTED_OUTPUT_CADENCE_SECONDS)
)
ACTIVE_TOP_M = 20_000.0
INACTIVE_NAMELIST_ZTOP_M = 18_000.0
RAYLEIGH_ONSET_M = 14_000.0
TERRAIN_HEIGHT_M = 400.0
TERRAIN_HALF_WIDTH_M = 1_000.0
TERRAIN_CENTER_M = 100.0
PRESERVED_GATE_B_RUN_ID = "dry-mountain-wave-official-20260721T183530Z"
PRESERVED_GATE_B_IMPLEMENTATION_COMMIT = "9ff73ff244c393bee2a2e93a851ad1ba2dc16287"
PRESERVED_GATE_B_EVALUATION_INPUT_SHA256 = {
    "run_manifest.json": "a72c2a9ba795b76cc779013817937bf34735835a74ad29c29efaf6df3ee1c13b",
    "case_manifest.json": "5a9d7ccc1dc9299c725eec4a3bd2c8e53163d918fe5d6ed7247527cd262c6356",
    "namelist.input": "bf202fb8e50abb903d50cb1cbeb86fb114efc88ff8049ab41ebf5bdd550b43be",
    "input_sounding": "75cf557b6258ab90943ee4368d3106a79ff63189e1d15aa0a6dcd2a051a033b3",
    "runtime_file_checklist.json": (
        "0a96a368c90454d8555f80ccb8f746da656276247a80f4dcb505e978f3586d63"
    ),
    "official_namelist_diff.json": (
        "7fda4d5ee51747e6b14f620ba087eb1b91f8a416cc8f635c5e2d9befefbeae92"
    ),
    "official_namelist_diff.txt": (
        "f9beafaddd3f156303a0375416db9f1620c912c754a29b760c0bbf2aa3254bfe"
    ),
    "storage_estimate.json": "2d9593624eefd69607b5204967c50d1bebed536fdd63b22e0baa3a4a938a9784",
    "execution_preflight.json": (
        "efc0dad92ba42e2cdaa4fb08905d08ca921a482b94356cd8ca9d50ff8d6a7286"
    ),
    "logs/stdout.log": "1018a9415063bbe9d5fcf87f1587f8086f614ddff9c1a1c44e74293cbb4e2fd0",
    "logs/stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "cm1out_stats.nc": "f26c12eee2cd9a23b2049374cd691394fae4b4793b56501bd97a633052148f58",
    "cm1out_000001.nc": "e894f6310f92827d8d0b8f15e11a36df7516d3f1113213a8bfca719c483faffe",
    "cm1out_000002.nc": "65d0e0eeb98c2e23309625a8931765e76d862c8e64d3d5bcfaf6abb86c16f73f",
    "cm1out_000003.nc": "457cc4b4da864a6cb41c2fe3199e4a2620025ee0994a4765b892661fc17ba3d2",
    "cm1out_000004.nc": "00a16c0c2d2390d8820d89502a506f967f5cd1ad3107084ab5436a24a517df9a",
    "cm1out_000005.nc": "0a3afb2fa258ad981e24fa4a4012d227fc4c7db34826d044e188856608d8398d",
    "cm1out_000006.nc": "dce854fd5cb90869edf5aa81f7ed50b56dd9ded8e704b9e815fd081860e01a3f",
    "cm1out_000007.nc": "e1dd0fb3f90f52a19e0ccda13194123b69511da6f76a529a5a48b30a63bff7df",
    "cm1out_000008.nc": "872bd649656084f82eca4409afbb2f4c509a424dcabbbd9a6c52266fd12a969e",
    "cm1out_000009.nc": "7a8553bfe14d751108db47a5696272c46842f1ec31db0f49ec17c05d2f563462",
    "cm1out_000010.nc": "a580260ddc8bcc1ab1c768bab510b6017513b686ed40b0a544220df3e83bddda",
    "cm1out_000011.nc": "b51ee4ca777bd825a5c4f52c92c6e39dd913071affb3c2694d36845cd687ded2",
}
SOURCE_MANIFEST_METHOD = (
    "sha256 each sorted src/*.F line as '<sha256>  src/<name>\\n', then sha256 manifest"
)
NON_CONSUMED_SOUNDING_LABEL = "present_for_launch_contract_not_consumed_by_isnd_9"
_OUTPUT_LIKE_PATTERNS = ("cm1out*", "*.nc", "*.nc4", "*.dat", "*.ctl")


class MountainWaveCaseError(RuntimeError):
    """Raised when Gate B packaging, preflight, or evaluation must stop."""


class CM1Provenance(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    release: str
    official_tag_commit: str
    official_source_tag: str
    source_tree_path: Path
    run_directory_path: Path
    executable_path: Path
    executable_sha256: str
    source_manifest_method: str
    source_manifest_sha256: str
    readme_namelist_sha256: str
    readme_terrain_sha256: str
    mountain_wave_namelist_path: Path
    mountain_wave_namelist_sha256: str
    critical_source_sha256: dict[str, str]
    netcdf_link_evidence: list[str]

    def report_record(self) -> dict[str, Any]:
        """Return provenance without machine-private filesystem paths."""
        return {
            "release": self.release,
            "official_tag_commit": self.official_tag_commit,
            "official_source_tag": self.official_source_tag,
            "source_tree_logical_location": "configured_cm1_root",
            "run_directory_logical_location": "configured_cm1_run_directory",
            "executable_logical_location": "configured_cm1_run_directory/cm1.exe",
            "executable_sha256": self.executable_sha256,
            "source_manifest_method": self.source_manifest_method,
            "source_manifest_sha256": self.source_manifest_sha256,
            "readme_namelist_sha256": self.readme_namelist_sha256,
            "readme_terrain_sha256": self.readme_terrain_sha256,
            "mountain_wave_namelist_logical_location": (
                "configured_cm1_root/run/config_files/nh_mountain_waves/namelist.input"
            ),
            "mountain_wave_namelist_sha256": self.mountain_wave_namelist_sha256,
            "critical_source_sha256": dict(self.critical_source_sha256),
            "netcdf_link_evidence": list(self.netcdf_link_evidence),
        }


class NamelistDifference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    official_value: str
    generated_value: str
    classification: str = "approved_output_only_change"


class NamelistAudit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    official_sha256: str
    generated_sha256: str
    assignment_count: int
    unchanged_assignment_count: int
    byte_equivalent_after_restoring_approved_values: bool
    differences: list[NamelistDifference]
    unchanged_inactive_values: dict[str, str]
    assignments: list[dict[str, str]]


class StorageEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_history_times_seconds: list[int]
    expected_history_count: int
    precision_bytes: int
    component_cells_per_frame: dict[str, int]
    raw_history_bytes: int
    netcdf_overhead_bytes: int
    estimated_netcdf_bytes: int
    estimated_stats_and_logs_bytes: int
    estimated_package_bytes: int
    estimated_total_bytes: int
    required_free_bytes: int
    available_free_bytes: int
    passed: bool


class ExecutionPreflight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checked_at: datetime
    implementation_commit: str
    checks: dict[str, bool]
    storage: StorageEstimate
    no_active_processes: bool
    no_prior_gate_b_execution: bool
    target_package_has_no_output: bool
    passed: bool


class ActiveTopEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transform_top_source: str = "final_nominal_zf"
    final_nominal_zf_m: float
    runtime_ztop_m: float
    configured_nz: int
    configured_dz_m: float
    nz_times_dz_m: float
    all_active_top_sources_agree: bool
    inactive_namelist_ztop_m: float = INACTIVE_NAMELIST_ZTOP_M


class MountainWaveRunEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_version: str = EVIDENCE_VERSION
    case_id: str = CASE_ID
    run_id: str
    implementation_commit: str
    generated_at: datetime
    reevaluation_identity: dict[str, Any]
    lifecycle: dict[str, Any]
    provenance: dict[str, Any]
    namelist_audit: NamelistAudit
    storage_preflight: StorageEstimate
    output_inventory: dict[str, Any]
    terrain_and_coordinates: dict[str, Any]
    base_state_and_flow: dict[str, Any]
    lower_boundary: dict[str, Any]
    wave_structure: dict[str, Any]
    boundary_and_damping: dict[str, Any]
    runtime_integrity: dict[str, Any]
    caveats: list[str] = Field(default_factory=list)

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2) + "\n"


@dataclass(frozen=True)
class MountainWavePackageResult:
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


def source_manifest_sha256(cm1_root: Path) -> str:
    source_paths = sorted((cm1_root / "src").glob("*.F"), key=lambda path: path.name)
    if not source_paths:
        raise MountainWaveCaseError("Configured CM1 root has no src/*.F files.")
    lines = [
        f"{sha256_file(path)}  {path.relative_to(cm1_root).as_posix()}\n" for path in source_paths
    ]
    return sha256_text("".join(lines))


def collect_cm1_provenance(settings: CloudChamberSettings) -> CM1Provenance:
    """Fail closed unless the configured runtime matches the pinned r21.1 evidence."""
    discovery = discover_cm1(settings)
    if not discovery.ready or settings.cm1_root is None or settings.cm1_run_dir is None:
        detail = "; ".join(discovery.missing)
        raise MountainWaveCaseError(f"Configured CM1 runtime is not ready: {detail}")

    root = settings.cm1_root.resolve()
    run_dir = settings.cm1_run_dir.resolve()
    executable = run_dir / "cm1.exe"
    official_namelist = root / "run/config_files/nh_mountain_waves/namelist.input"
    expected_files = {
        executable: CM1_EXECUTABLE_SHA256,
        root / "README.namelist": CM1_README_NAMELIST_SHA256,
        root / "README.terrain": CM1_README_TERRAIN_SHA256,
        official_namelist: CM1_MOUNTAIN_WAVE_NAMELIST_SHA256,
        **{root / relative: expected for relative, expected in CRITICAL_SOURCE_HASHES.items()},
    }
    mismatches: list[str] = []
    for path, expected in expected_files.items():
        logical = path.relative_to(root).as_posix() if path.is_relative_to(root) else "run/cm1.exe"
        if not path.is_file():
            mismatches.append(f"missing:{logical}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            mismatches.append(f"sha256_mismatch:{logical}:{actual}")

    source_hash = source_manifest_sha256(root)
    if source_hash != CM1_SOURCE_MANIFEST_SHA256:
        mismatches.append(f"source_manifest_sha256_mismatch:{source_hash}")
    if mismatches:
        raise MountainWaveCaseError(
            "Configured CM1 provenance does not match pinned r21.1 evidence: "
            + "; ".join(mismatches)
        )

    link_evidence = _netcdf_link_evidence(executable)
    if not link_evidence:
        raise MountainWaveCaseError(
            "Configured CM1 executable does not expose NetCDF link evidence."
        )

    return CM1Provenance(
        release=CM1_RELEASE,
        official_tag_commit=CM1_TAG_COMMIT,
        official_source_tag=CM1_SOURCE_TAG,
        source_tree_path=root,
        run_directory_path=run_dir,
        executable_path=executable,
        executable_sha256=CM1_EXECUTABLE_SHA256,
        source_manifest_method=SOURCE_MANIFEST_METHOD,
        source_manifest_sha256=source_hash,
        readme_namelist_sha256=CM1_README_NAMELIST_SHA256,
        readme_terrain_sha256=CM1_README_TERRAIN_SHA256,
        mountain_wave_namelist_path=official_namelist,
        mountain_wave_namelist_sha256=CM1_MOUNTAIN_WAVE_NAMELIST_SHA256,
        critical_source_sha256=dict(CRITICAL_SOURCE_HASHES),
        netcdf_link_evidence=link_evidence,
    )


def _netcdf_link_evidence(executable: Path) -> list[str]:
    commands = (("otool", "-L", str(executable)), ("ldd", str(executable)))
    for command in commands:
        try:
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
        except OSError:
            continue
        evidence = []
        for line in (completed.stdout + completed.stderr).splitlines():
            if "netcdf" not in line.lower():
                continue
            token = line.strip().split(" ", 1)[0]
            evidence.append(Path(token).name)
        if evidence:
            return evidence
    return []


def render_mountain_wave_namelist(official_text: str) -> str:
    """Change only the three output settings authorized by Gate B."""
    rendered = official_text
    for name, (official_value, generated_value) in OUTPUT_OVERRIDES.items():
        current = parse_namelist_assignments(rendered).get(name)
        if current != official_value:
            raise MountainWaveCaseError(
                f"Official namelist {name} must be {official_value}; found {current!r}."
            )
        rendered = replace_namelist_assignment(rendered, name, generated_value)
    audit_namelist(official_text, rendered)
    return rendered


def replace_namelist_assignment(text: str, name: str, value: str) -> str:
    pattern = re.compile(
        rf"^(?P<prefix>\s*{re.escape(name)}\s*=\s*)(?P<value>[^,!\n]+)(?P<suffix>\s*,.*)$",
        re.MULTILINE | re.IGNORECASE,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise MountainWaveCaseError(
            f"Expected exactly one {name!r} assignment; found {len(matches)}."
        )
    return pattern.sub(
        lambda match: f"{match.group('prefix')}{value}{match.group('suffix')}",
        text,
        count=1,
    )


def parse_namelist_assignments(text: str) -> dict[str, str]:
    pattern = re.compile(
        r"^\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
        r"(?P<value>[^,!\n]+)\s*,",
        re.MULTILINE,
    )
    assignments: dict[str, str] = {}
    for match in pattern.finditer(text):
        name = match.group("name").lower()
        if name in assignments:
            raise MountainWaveCaseError(f"Duplicate namelist assignment: {name}")
        assignments[name] = match.group("value").strip()
    if not assignments:
        raise MountainWaveCaseError("No Fortran namelist assignments were found.")
    return assignments


def audit_namelist(official_text: str, generated_text: str) -> NamelistAudit:
    official = parse_namelist_assignments(official_text)
    generated = parse_namelist_assignments(generated_text)
    if official.keys() != generated.keys():
        missing = sorted(official.keys() - generated.keys())
        extra = sorted(generated.keys() - official.keys())
        raise MountainWaveCaseError(
            f"Generated namelist assignment set differs; missing={missing}, extra={extra}."
        )

    differences: list[NamelistDifference] = []
    assignments: list[dict[str, str]] = []
    for name, official_value in official.items():
        generated_value = generated[name]
        status = "unchanged"
        if official_value != generated_value:
            approved = OUTPUT_OVERRIDES.get(name)
            if approved != (official_value, generated_value):
                raise MountainWaveCaseError(
                    f"Unapproved namelist difference {name}: {official_value} -> {generated_value}."
                )
            status = "approved_output_only_change"
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

    if {difference.name for difference in differences} != set(OUTPUT_OVERRIDES):
        raise MountainWaveCaseError(
            "Generated namelist must contain exactly the three approved output differences."
        )

    inactive: dict[str, str] = {}
    for name, expected in INACTIVE_AUDIT_VALUES.items():
        if official.get(name) != expected or generated.get(name) != expected:
            raise MountainWaveCaseError(
                f"Inactive carry-forward value {name} must remain {expected}."
            )
        inactive[name] = expected

    restored = generated_text
    for name, (official_value, _generated_value) in OUTPUT_OVERRIDES.items():
        restored = replace_namelist_assignment(restored, name, official_value)
    byte_equivalent = restored == official_text
    if not byte_equivalent:
        raise MountainWaveCaseError(
            "Generated namelist differs outside the three approved assignment values."
        )

    return NamelistAudit(
        official_sha256=sha256_text(official_text),
        generated_sha256=sha256_text(generated_text),
        assignment_count=len(assignments),
        unchanged_assignment_count=sum(item["status"] == "unchanged" for item in assignments),
        byte_equivalent_after_restoring_approved_values=byte_equivalent,
        differences=differences,
        unchanged_inactive_values=inactive,
        assignments=assignments,
    )


def render_human_namelist_audit(audit: NamelistAudit) -> str:
    lines = [
        "CM1 r21.1 official dry mountain-wave namelist audit",
        f"Official SHA-256: {audit.official_sha256}",
        f"Generated SHA-256: {audit.generated_sha256}",
        f"Assignments audited: {audit.assignment_count}",
        (
            "Byte-equivalent after restoring approved values: "
            f"{str(audit.byte_equivalent_after_restoring_approved_values).lower()}"
        ),
        "",
        "Approved material differences:",
    ]
    for difference in audit.differences:
        lines.append(
            f"CHANGED {difference.name}: {difference.official_value} -> "
            f"{difference.generated_value} ({difference.classification})"
        )
    lines.extend(("", "Mandatory inactive-value audit:"))
    for name, value in audit.unchanged_inactive_values.items():
        lines.append(f"UNCHANGED {name} = {value}")
    lines.extend(("", "Complete assignment audit:"))
    for assignment in audit.assignments:
        if assignment["status"] == "unchanged":
            lines.append(f"UNCHANGED {assignment['name']} = {assignment['official_value']}")
        else:
            lines.append(
                f"CHANGED {assignment['name']}: {assignment['official_value']} -> "
                f"{assignment['generated_value']}"
            )
    return "\n".join(lines) + "\n"


def expected_output_times(namelist_text: str) -> tuple[int, ...]:
    assignments = parse_namelist_assignments(namelist_text)
    duration = _integer_seconds(assignments, "timax")
    cadence = _integer_seconds(assignments, "tapfrq")
    if duration <= 0 or cadence <= 0 or duration % cadence:
        raise MountainWaveCaseError(
            f"History timing must divide exactly; timax={duration}, tapfrq={cadence}."
        )
    return tuple(range(0, duration + 1, cadence))


def estimate_storage(namelist_text: str, target: Path) -> StorageEstimate:
    assignments = parse_namelist_assignments(namelist_text)
    nx = _integer_value(assignments, "nx")
    ny = _integer_value(assignments, "ny")
    nz = _integer_value(assignments, "nz")
    times = expected_output_times(namelist_text)
    scalar = nx * ny * nz
    components = {
        "required_scalar_3d": 3 * scalar,  # zhval, th, prs
        "required_u_3d": (nx + 1) * ny * nz,
        "required_v_3d": nx * (ny + 1) * nz,
        "required_w_3d": nx * ny * (nz + 1),
        "required_terrain_2d": nx * ny,
        # The complete official namelist retains dry-inapplicable output switches.
        # This upper bound allows ten scalar-grid fields for any that CM1 emits.
        "retained_optional_3d_upper_bound": 10 * scalar,
        "retained_optional_2d_upper_bound": 8 * nx * ny,
        "coordinates_and_scalars": (nx + 1) + (ny + 1) + (nz + 1) + nx + ny + nz + 64,
    }
    precision_bytes = 4
    raw_history_bytes = sum(components.values()) * precision_bytes * len(times)
    netcdf_overhead = math.ceil(raw_history_bytes * 0.35) + len(times) * 1024 * 1024
    estimated_netcdf = raw_history_bytes + netcdf_overhead
    stats_and_logs = 20 * 1024 * 1024
    package_bytes = 2 * 1024 * 1024
    total = estimated_netcdf + stats_and_logs + package_bytes
    target.mkdir(parents=True, exist_ok=True)
    available = shutil.disk_usage(target).free
    required = 2 * total
    return StorageEstimate(
        expected_history_times_seconds=list(times),
        expected_history_count=len(times),
        precision_bytes=precision_bytes,
        component_cells_per_frame=components,
        raw_history_bytes=raw_history_bytes,
        netcdf_overhead_bytes=netcdf_overhead,
        estimated_netcdf_bytes=estimated_netcdf,
        estimated_stats_and_logs_bytes=stats_and_logs,
        estimated_package_bytes=package_bytes,
        estimated_total_bytes=total,
        required_free_bytes=required,
        available_free_bytes=available,
        passed=available >= required,
    )


def _integer_seconds(assignments: dict[str, str], name: str) -> int:
    value = float(assignments[name])
    if not value.is_integer():
        raise MountainWaveCaseError(f"{name} must be an integral number of seconds.")
    return int(value)


def _integer_value(assignments: dict[str, str], name: str) -> int:
    value = float(assignments[name])
    if not value.is_integer():
        raise MountainWaveCaseError(f"{name} must be integral.")
    return int(value)


def verified_clean_git_commit() -> str:
    commit = _git_output("rev-parse", "HEAD")
    dirty = _git_output("status", "--porcelain=v1", "--untracked-files=all")
    if dirty:
        raise MountainWaveCaseError(
            "Mountain-wave evidence generation requires a clean Git worktree."
        )
    if not commit:
        raise MountainWaveCaseError("Unable to identify the implementation commit.")
    return commit


def _git_output(*args: str) -> str:
    repo_root = Path(__file__).resolve().parents[3]
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise MountainWaveCaseError(
            f"Unable to verify Git provenance with: git {' '.join(args)}"
        ) from exc
    return completed.stdout.strip()


def active_cm1_processes() -> list[str]:
    found: list[str] = []
    for process_name in ("cm1.exe", "mpirun", "mpiexec"):
        try:
            completed = subprocess.run(
                ["pgrep", "-x", process_name],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise MountainWaveCaseError("Unable to inspect active CM1 processes.") from exc
        for process_id in completed.stdout.splitlines():
            if process_id.strip():
                found.append(f"{process_name}:{process_id.strip()}")
    return found


def generate_mountain_wave_package(
    *,
    settings: CloudChamberSettings,
    run_id: str,
) -> MountainWavePackageResult:
    """Create one exact, non-executing Gate B package after fail-closed checks."""
    implementation_commit = verified_clean_git_commit()
    provenance = collect_cm1_provenance(settings)
    if active_cm1_processes():
        raise MountainWaveCaseError("A CM1 or MPI process is already active.")

    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    if package_dir.exists():
        raise MountainWaveCaseError(f"Run package already exists: {run_id}")
    package_dir.mkdir(parents=True)

    official_text = provenance.mountain_wave_namelist_path.read_text()
    generated_text = render_mountain_wave_namelist(official_text)
    audit = audit_namelist(official_text, generated_text)
    storage = estimate_storage(generated_text, package_dir)
    if not storage.passed:
        shutil.rmtree(package_dir)
        raise MountainWaveCaseError(
            "Storage preflight failed: available space is less than twice the estimate."
        )

    paths = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "namelist": package_dir / "namelist.input",
        "input_sounding": package_dir / "input_sounding",
        "report": package_dir / "dry_run_report.json",
        "runtime_checklist": package_dir / "runtime_file_checklist.json",
        "namelist_audit": package_dir / "official_namelist_diff.json",
        "namelist_audit_text": package_dir / "official_namelist_diff.txt",
        "storage_estimate": package_dir / "storage_estimate.json",
    }
    input_sounding = "1000.0000 288.0000 0.000000\n0.0000 288.0000 0.000000 10.0000 0.0000\n"
    runtime_checklist = {
        "status": "no_scientifically_consumed_external_runtime_files",
        "required_files": [],
        "source_candidates": {},
        "explicitly_not_staged": [
            "LANDUSE.TBL",
            "perts.dat",
            "input_grid_x",
            "input_grid_y",
            "input_grid_z",
            "external_sounding",
        ],
        "input_sounding_status": NON_CONSUMED_SOUNDING_LABEL,
    }
    paths["namelist"].write_text(generated_text)
    paths["input_sounding"].write_text(input_sounding)
    _write_json(paths["runtime_checklist"], runtime_checklist)
    _write_json(paths["namelist_audit"], audit.model_dump(mode="json"))
    paths["namelist_audit_text"].write_text(render_human_namelist_audit(audit))
    _write_json(paths["storage_estimate"], storage.model_dump(mode="json"))

    generated_hashes = {
        path.name: sha256_file(path)
        for key, path in paths.items()
        if key not in {"manifest", "case_manifest", "report"}
    }
    case_manifest = {
        "case_id": CASE_ID,
        "scenario_id": SCENARIO_ID,
        "authority_state": "gate_b_source_bundled_dry_benchmark_not_product_recipe",
        "source_bundled_dry_benchmark": True,
        "run_id": run_id,
        "implementation_commit": implementation_commit,
        "run_recipe": None,
        "recipe_id": None,
        "cloud_world_id": None,
        "input_sounding_status": NON_CONSUMED_SOUNDING_LABEL,
        "cm1_provenance": provenance.report_record(),
        "namelist_audit": audit.model_dump(mode="json"),
        "storage_estimate": storage.model_dump(mode="json"),
        "generated_input_sha256": generated_hashes,
        "execution_authorization": {
            "duration_seconds": EXPECTED_DURATION_SECONDS,
            "process_count": 1,
            "smoke_process_allowed": False,
            "rerun_allowed": False,
        },
        "non_implications": [
            "not_a_cloud_world",
            "not_a_recipe",
            "not_a_moist_case",
            "not_terrain_browser_support",
        ],
    }
    _write_json(paths["case_manifest"], case_manifest)
    generated_hashes[paths["case_manifest"].name] = sha256_file(paths["case_manifest"])

    now = datetime.now(UTC)
    run_configuration: dict[str, Any] = {
        "case_id": CASE_ID,
        "scenario_id": SCENARIO_ID,
        "source_bundled_dry_benchmark": True,
        "duration_seconds": EXPECTED_DURATION_SECONDS,
        "output_cadence_seconds": EXPECTED_OUTPUT_CADENCE_SECONDS,
        "expected_model_output_count": len(EXPECTED_OUTPUT_TIMES_SECONDS),
        "domain": {
            "nx": 100,
            "ny": 1,
            "nz": 100,
            "dx_m": 200.0,
            "dy_m": 200.0,
            "dz_m": 200.0,
            "active_model_top_m": ACTIVE_TOP_M,
            "inactive_namelist_ztop_m": INACTIVE_NAMELIST_ZTOP_M,
        },
        "terrain": {
            "terrain_flag": True,
            "itern": 1,
            "height_m": TERRAIN_HEIGHT_M,
            "half_width_m": TERRAIN_HALF_WIDTH_M,
            "center_m": TERRAIN_CENTER_M,
        },
        "output_overrides": {
            name: {"official": old, "generated": new}
            for name, (old, new) in OUTPUT_OVERRIDES.items()
        },
        "cm1_provenance": provenance.report_record(),
        "generated_input_sha256": generated_hashes,
        "namelist_audit_sha256": sha256_file(paths["namelist_audit"]),
        "storage_estimate": storage.model_dump(mode="json"),
        "input_sounding_status": NON_CONSUMED_SOUNDING_LABEL,
    }
    manifest = RunManifest(
        run_id=run_id,
        scenario=ScenarioReference(id=SCENARIO_ID, schema_version=EVIDENCE_VERSION),
        controls={},
        run_configuration=run_configuration,
        physical_question=(
            "Can configured CM1 r21.1 faithfully execute its official dry mountain-wave "
            "case and produce internally consistent native terrain-following output?"
        ),
        expected_diagnostics=[
            "native_output_inventory_and_finite_counts",
            "terrain_and_physical_height_integrity",
            "lower_boundary_terrain_tangency",
            "dry_wave_structure_and_thermodynamic_displacement",
            "boundary_and_rayleigh_layer_assessment",
            "runtime_integrity_and_practical_cost",
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
        app=AppMetadata(app_version=__version__, commit=implementation_commit),
        lifecycle_state=LifecycleState.PACKAGED,
        validation_status=ValidationStatus.VALID,
        provenance=ProvenanceMetadata(product_state=ProductState.PACKAGED_DRY_RUN_OUTPUT),
        created_at=now,
        updated_at=now,
        user=UserMetadata(name="Official CM1 r21.1 dry mountain-wave benchmark"),
        run_recipe=None,
        recipe_id=None,
        required_output_fields=list(REQUIRED_OUTPUT_FIELDS),
        input_source="cm1_r21_1_built_in_isnd_9_iwnd_6_itern_1",
        expected_outputs=["native_numbered_cm1_model_netcdf", "cm1_stats_and_logs"],
        run_limitations=[
            "gate_b_dry_2d_benchmark_only",
            "no_moisture_or_cloud_product_conclusion",
            "current_flat_grid_browser_payloads_not_acceptance_evidence",
        ],
        manual_validation_status="gate_b_evidence_pending",
    )
    write_run_manifest(paths["manifest"], manifest)
    package_report = {
        "status": "package_and_storage_preflight_passed_not_executed",
        "case_id": CASE_ID,
        "run_id": run_id,
        "implementation_commit": implementation_commit,
        "cm1_provenance": provenance.report_record(),
        "namelist_audit": audit.model_dump(mode="json"),
        "storage_estimate": storage.model_dump(mode="json"),
        "input_sounding_status": NON_CONSUMED_SOUNDING_LABEL,
        "run_recipe": None,
        "recipe_id": None,
        "cloud_world_id": None,
    }
    _write_json(paths["report"], package_report)

    return MountainWavePackageResult(
        run_id=run_id,
        package_dir=package_dir,
        manifest_path=paths["manifest"],
        case_manifest_path=paths["case_manifest"],
        namelist_audit_path=paths["namelist_audit"],
        storage_estimate_path=paths["storage_estimate"],
        implementation_commit=implementation_commit,
        generated_files=tuple(paths.values()),
    )


def load_mountain_wave_package(
    *, settings: CloudChamberSettings, run_id: str
) -> MountainWavePackageResult:
    """Load the exact previously generated package for explicit execution."""
    return _load_mountain_wave_package(
        settings=settings,
        run_id=run_id,
        required_lifecycle=LifecycleState.PACKAGED,
    )


def load_completed_mountain_wave_package_for_evaluation(
    *,
    settings: CloudChamberSettings,
    run_id: str,
    expected_implementation_commit: str,
) -> MountainWavePackageResult:
    """Load a completed package without exposing any execution operation."""
    package = _load_mountain_wave_package(
        settings=settings,
        run_id=run_id,
        required_lifecycle=LifecycleState.COMPLETED,
    )
    manifest = load_run_manifest(package.manifest_path)
    if manifest.execution.exit_code != 0:
        raise MountainWaveCaseError("Offline evaluation requires a zero-exit completed run.")
    if package.implementation_commit != expected_implementation_commit:
        raise MountainWaveCaseError(
            "Completed package implementation commit does not match reevaluation authority."
        )
    return package


def _load_mountain_wave_package(
    *,
    settings: CloudChamberSettings,
    run_id: str,
    required_lifecycle: LifecycleState,
) -> MountainWavePackageResult:
    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    paths = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "namelist": package_dir / "namelist.input",
        "input_sounding": package_dir / "input_sounding",
        "report": package_dir / "dry_run_report.json",
        "runtime_checklist": package_dir / "runtime_file_checklist.json",
        "namelist_audit": package_dir / "official_namelist_diff.json",
        "namelist_audit_text": package_dir / "official_namelist_diff.txt",
        "storage_estimate": package_dir / "storage_estimate.json",
    }
    missing = sorted(path.name for path in paths.values() if not path.is_file())
    if missing:
        raise MountainWaveCaseError(
            f"Existing Gate B package is incomplete for {run_id}: {missing}"
        )
    manifest = load_run_manifest(paths["manifest"])
    if manifest.run_id != run_id or manifest.scenario.id != SCENARIO_ID:
        raise MountainWaveCaseError("Existing package identity does not match Gate B.")
    if manifest.lifecycle_state != required_lifecycle:
        raise MountainWaveCaseError(
            f"Existing package {run_id} is {manifest.lifecycle_state.value}; "
            f"expected {required_lifecycle.value}."
        )
    case_manifest = json.loads(paths["case_manifest"].read_text())
    implementation_commit = case_manifest.get("implementation_commit")
    if not isinstance(implementation_commit, str) or not implementation_commit:
        raise MountainWaveCaseError("Existing package lacks its implementation commit.")
    if manifest.app.commit != implementation_commit:
        raise MountainWaveCaseError("Existing package commit records disagree.")
    return MountainWavePackageResult(
        run_id=run_id,
        package_dir=package_dir,
        manifest_path=paths["manifest"],
        case_manifest_path=paths["case_manifest"],
        namelist_audit_path=paths["namelist_audit"],
        storage_estimate_path=paths["storage_estimate"],
        implementation_commit=implementation_commit,
        generated_files=tuple(paths.values()),
    )


def verify_evaluation_input_identity(
    package: MountainWavePackageResult,
    *,
    expected_run_id: str,
    expected_implementation_commit: str,
    expected_file_sha256: dict[str, str],
) -> dict[str, Any]:
    """Fail closed unless every preserved evaluation input matches its pinned hash."""
    if package.run_id != expected_run_id:
        raise MountainWaveCaseError("Preserved run ID does not match reevaluation authority.")
    if package.implementation_commit != expected_implementation_commit:
        raise MountainWaveCaseError(
            "Preserved implementation commit does not match reevaluation authority."
        )
    manifest = load_run_manifest(package.manifest_path)
    if manifest.lifecycle_state != LifecycleState.COMPLETED or manifest.execution.exit_code != 0:
        raise MountainWaveCaseError(
            "Preserved reevaluation input is not a completed zero-exit run."
        )
    if manifest.app.commit != expected_implementation_commit:
        raise MountainWaveCaseError("Run manifest implementation commit changed.")
    active = active_cm1_processes()
    if active:
        raise MountainWaveCaseError(
            f"Offline evaluation requires no active CM1/MPI process: {active}"
        )

    package_root = package.package_dir.resolve()
    actual_file_sha256: dict[str, str] = {}
    mismatches: list[str] = []
    for logical_path, expected_hash in expected_file_sha256.items():
        path = (package_root / logical_path).resolve()
        if not path.is_relative_to(package_root):
            raise MountainWaveCaseError(f"Evaluation input escapes package: {logical_path}")
        if not path.is_file():
            mismatches.append(f"missing:{logical_path}")
            continue
        actual_hash = sha256_file(path)
        actual_file_sha256[logical_path] = actual_hash
        if actual_hash != expected_hash:
            mismatches.append(f"sha256_mismatch:{logical_path}:{actual_hash}")
    if mismatches:
        raise MountainWaveCaseError(
            "Preserved Gate B evaluation identity mismatch: " + "; ".join(mismatches)
        )

    recorded_namelist_hash = manifest.run_configuration.get("generated_input_sha256", {}).get(
        "namelist.input"
    )
    if recorded_namelist_hash != actual_file_sha256.get("namelist.input"):
        raise MountainWaveCaseError("Manifest and preserved namelist hashes disagree.")
    return {
        "run_id": package.run_id,
        "implementation_commit": package.implementation_commit,
        "verification_mode": "pinned_sha256_before_and_after_offline_evaluation",
        "file_sha256": actual_file_sha256,
        "all_inputs_match_pinned_original": True,
    }


def preflight_package_for_execution(
    *,
    settings: CloudChamberSettings,
    package: MountainWavePackageResult,
) -> ExecutionPreflight:
    """Repeat every launch gate immediately before the one authorized process."""
    implementation_commit = verified_clean_git_commit()
    if implementation_commit != package.implementation_commit:
        raise MountainWaveCaseError(
            "Package implementation commit does not match current clean HEAD."
        )
    provenance = collect_cm1_provenance(settings)
    manifest = load_run_manifest(package.manifest_path)
    if manifest.app.commit != implementation_commit:
        raise MountainWaveCaseError("Run manifest does not record the implementation commit.")

    official_text = provenance.mountain_wave_namelist_path.read_text()
    generated_text = Path(manifest.generated_inputs.namelist_input or "").read_text()
    audit = audit_namelist(official_text, generated_text)
    if (
        audit.generated_sha256
        != json.loads(package.namelist_audit_path.read_text())["generated_sha256"]
    ):
        raise MountainWaveCaseError("Generated namelist changed after package creation.")

    storage = StorageEstimate.model_validate(json.loads(package.storage_estimate_path.read_text()))
    available = shutil.disk_usage(package.package_dir).free
    storage = storage.model_copy(
        update={
            "available_free_bytes": available,
            "passed": available >= storage.required_free_bytes,
        }
    )
    if not storage.passed:
        raise MountainWaveCaseError("Execution storage preflight no longer passes.")

    active = active_cm1_processes()
    if active:
        raise MountainWaveCaseError(f"Another CM1/MPI process is active: {active}")
    prior = prior_gate_b_executions(settings.runtime_home.expanduser(), package.run_id)
    if prior:
        raise MountainWaveCaseError(
            f"A Gate B CM1 execution already exists; rerun is forbidden: {prior}"
        )

    output_paths = _existing_output_like_paths(package.package_dir)
    if output_paths:
        raise MountainWaveCaseError(
            f"Target package contains output-like files before launch: {output_paths}"
        )
    checklist_path = package.package_dir / "runtime_file_checklist.json"
    checklist = json.loads(checklist_path.read_text())
    if checklist.get("required_files") != []:
        raise MountainWaveCaseError("Official itern=1 package must not stage runtime files.")
    if checklist.get("input_sounding_status") != NON_CONSUMED_SOUNDING_LABEL:
        raise MountainWaveCaseError("Non-consumed input_sounding is not labeled honestly.")

    checks = {
        "clean_worktree_and_commit_match": True,
        "configured_provenance_matches": True,
        "critical_source_hashes_match": True,
        "netcdf_support_linked": bool(provenance.netcdf_link_evidence),
        "complete_namelist_preserved": audit.byte_equivalent_after_restoring_approved_values,
        "exact_three_output_differences": len(audit.differences) == 3,
        "inactive_values_unchanged": len(audit.unchanged_inactive_values)
        == len(INACTIVE_AUDIT_VALUES),
        "runtime_checklist_empty": True,
        "input_sounding_non_consumed_label": True,
        "storage_has_double_estimate": storage.passed,
    }
    preflight = ExecutionPreflight(
        checked_at=datetime.now(UTC),
        implementation_commit=implementation_commit,
        checks=checks,
        storage=storage,
        no_active_processes=True,
        no_prior_gate_b_execution=True,
        target_package_has_no_output=True,
        passed=all(checks.values()),
    )
    _write_json(
        package.package_dir / "execution_preflight.json",
        preflight.model_dump(mode="json"),
    )
    return preflight


def prior_gate_b_executions(runtime_home: Path, current_run_id: str) -> list[str]:
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


def _existing_output_like_paths(package_dir: Path) -> list[str]:
    found: set[str] = set()
    for pattern in _OUTPUT_LIKE_PATTERNS:
        for path in package_dir.glob(pattern):
            if path.name in {"dry_run_report.json"}:
                continue
            found.add(path.name)
    return sorted(found)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")


def accepted_model_output_paths(paths: list[Path]) -> list[Path]:
    """Return only native numbered CM1 model files in numeric filename order."""
    accepted: list[tuple[int, Path]] = []
    for path in paths:
        match = MODEL_OUTPUT_PATTERN.fullmatch(path.name)
        if match is not None:
            accepted.append((int(match.group("number")), path))
    return [path for _number, path in sorted(accepted)]


def normalize_length_to_m(values: Any, units: str | None) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Normalize a CM1 length coordinate or field to meters from its actual units."""
    normalized = np.asarray(values, dtype=np.float64)
    unit = (units or "").strip().lower().replace(" ", "")
    if unit in {"m", "meter", "meters", "metre", "metres"}:
        return normalized
    if unit in {"km", "kilometer", "kilometers", "kilometre", "kilometres"}:
        return normalized * 1_000.0
    if unit in {"cm", "centimeter", "centimeters", "centimetre", "centimetres"}:
        return normalized * 0.01
    raise MountainWaveCaseError(f"Unsupported or missing length units: {units!r}")


def normalize_time_to_seconds(
    values: Any, units: str | None
) -> np.ndarray[Any, np.dtype[np.float64]]:
    normalized = np.asarray(values, dtype=np.float64)
    unit = (units or "").strip().lower().replace(" ", "")
    if unit in {"s", "sec", "secs", "second", "seconds"}:
        return normalized
    if unit in {"min", "mins", "minute", "minutes"}:
        return normalized * 60.0
    if unit in {"h", "hr", "hrs", "hour", "hours"}:
        return normalized * 3_600.0
    raise MountainWaveCaseError(f"Unsupported or missing time units: {units!r}")


def analytic_itern1_terrain(x_m: Any) -> np.ndarray[Any, np.dtype[np.float64]]:
    x_values = np.asarray(x_m, dtype=np.float64)
    return TERRAIN_HEIGHT_M / (1.0 + ((x_values - TERRAIN_CENTER_M) / TERRAIN_HALF_WIDTH_M) ** 2)


def reconstruct_physical_heights(
    zs_m: Any,
    nominal_levels_m: Any,
    *,
    active_top_m: float,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    terrain = np.asarray(zs_m, dtype=np.float64)
    nominal = np.asarray(nominal_levels_m, dtype=np.float64)
    if terrain.ndim != 2 or nominal.ndim != 1:
        raise MountainWaveCaseError("Terrain must be 2-D and nominal levels must be 1-D.")
    if active_top_m <= float(np.max(terrain)):
        raise MountainWaveCaseError("Active top must be above every terrain point.")
    return (
        terrain[None, :, :]
        + nominal[:, None, None] * (active_top_m - terrain[None, :, :]) / active_top_m
    )


def resolve_active_top_evidence(
    nominal_zf: Any,
    nominal_zf_units: str | None,
    runtime_ztop: Any,
    runtime_ztop_units: str | None,
    *,
    configured_nz: int,
    configured_dz_m: float,
) -> ActiveTopEvidence:
    full_levels_m = normalize_length_to_m(nominal_zf, nominal_zf_units)
    if full_levels_m.ndim != 1 or full_levels_m.size < 2:
        raise MountainWaveCaseError("Nominal zf must contain the full vertical coordinate.")
    final_nominal_zf_m = float(full_levels_m[-1])
    scalar_top_values = normalize_length_to_m(runtime_ztop, runtime_ztop_units).reshape(-1)
    if scalar_top_values.size != 1:
        raise MountainWaveCaseError("Runtime NetCDF ztop must be scalar-valued.")
    runtime_ztop_m = float(scalar_top_values[0])
    nz_times_dz_m = configured_nz * configured_dz_m
    evidence = ActiveTopEvidence(
        final_nominal_zf_m=final_nominal_zf_m,
        runtime_ztop_m=runtime_ztop_m,
        configured_nz=configured_nz,
        configured_dz_m=configured_dz_m,
        nz_times_dz_m=nz_times_dz_m,
        all_active_top_sources_agree=all(
            math.isclose(value, final_nominal_zf_m, rel_tol=0.0, abs_tol=0.01)
            for value in (runtime_ztop_m, nz_times_dz_m, ACTIVE_TOP_M)
        ),
    )
    if not evidence.all_active_top_sources_agree:
        raise MountainWaveCaseError(
            "Active-top evidence disagrees among final nominal zf, runtime ztop, and nz*dz."
        )
    return evidence


def lower_boundary_tangency_metrics(
    *,
    x_m: Any,
    y_m: Any,
    zs_m: Any,
    u_bottom: Any,
    v_bottom: Any,
    w_bottom: Any,
) -> dict[str, Any]:
    """Collocate staggered flow and compare physical bottom w with terrain tangency."""
    x = np.asarray(x_m, dtype=np.float64)
    y = np.asarray(y_m, dtype=np.float64)
    terrain = np.asarray(zs_m, dtype=np.float64)
    u = np.asarray(u_bottom, dtype=np.float64)
    v = np.asarray(v_bottom, dtype=np.float64)
    w = np.asarray(w_bottom, dtype=np.float64)
    if terrain.shape != (y.size, x.size) or w.shape != terrain.shape:
        raise MountainWaveCaseError("Terrain and bottom-w shapes do not match scalar coordinates.")
    u_scalar = _collocate_staggered_axis(u, axis=-1, expected_size=x.size)
    v_scalar = _collocate_staggered_axis(v, axis=-2, expected_size=y.size)
    if u_scalar.shape != terrain.shape or v_scalar.shape != terrain.shape:
        raise MountainWaveCaseError("Collocated u/v shapes do not match bottom w.")

    dzdx = np.gradient(terrain, x, axis=-1, edge_order=2 if x.size >= 3 else 1)
    if y.size > 1:
        dzdy = np.gradient(terrain, y, axis=-2, edge_order=2 if y.size >= 3 else 1)
    else:
        dzdy = np.zeros_like(terrain)
    predicted = u_scalar * dzdx + v_scalar * dzdy
    residual = w - predicted
    abs_residual = np.abs(residual)
    correlation: float | None = None
    if float(np.std(predicted)) > 0.0 and float(np.std(w)) > 0.0:
        correlation = float(np.corrcoef(predicted.reshape(-1), w.reshape(-1))[0, 1])
    return {
        "method": (
            "arithmetic face-to-scalar averaging for u/v; numpy coordinate gradient for "
            "dzs/dx and dzs/dy; residual=w-(u*dzs/dx+v*dzs/dy)"
        ),
        "sample_count": int(residual.size),
        "predicted_min_m_s": float(np.min(predicted)),
        "predicted_max_m_s": float(np.max(predicted)),
        "observed_min_m_s": float(np.min(w)),
        "observed_max_m_s": float(np.max(w)),
        "residual_min_m_s": float(np.min(residual)),
        "residual_max_m_s": float(np.max(residual)),
        "residual_mean_m_s": float(np.mean(residual)),
        "residual_mean_abs_m_s": float(np.mean(abs_residual)),
        "residual_rms_m_s": float(np.sqrt(np.mean(residual**2))),
        "residual_p95_abs_m_s": float(np.quantile(abs_residual, 0.95)),
        "predicted_observed_correlation": correlation,
    }


def _collocate_staggered_axis(
    values: np.ndarray[Any, np.dtype[np.float64]],
    *,
    axis: int,
    expected_size: int,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    actual_size = values.shape[axis]
    if actual_size == expected_size:
        return values
    if actual_size != expected_size + 1:
        raise MountainWaveCaseError(
            f"Cannot collocate axis of size {actual_size} to scalar size {expected_size}."
        )
    lower = [slice(None)] * values.ndim
    upper = [slice(None)] * values.ndim
    lower[axis] = slice(0, -1)
    upper[axis] = slice(1, None)
    return 0.5 * (values[tuple(lower)] + values[tuple(upper)])


def central_boundary_metrics(
    values: Any,
    x_m: Any,
    physical_z_m: Any,
    *,
    rayleigh_onset_m: float = RAYLEIGH_ONSET_M,
) -> dict[str, Any]:
    field = np.asarray(values, dtype=np.float64)
    x = np.asarray(x_m, dtype=np.float64)
    heights = np.asarray(physical_z_m, dtype=np.float64)
    if field.shape != heights.shape or field.shape[-1] != x.size:
        raise MountainWaveCaseError("Field, physical-height, and x-coordinate shapes differ.")
    west_limit = float(np.quantile(x, 0.2))
    east_limit = float(np.quantile(x, 0.8))
    central_x = (x >= west_limit) & (x <= east_limit)
    west_x = x < west_limit
    east_x = x > east_limit
    below = heights < rayleigh_onset_m
    rayleigh = heights >= rayleigh_onset_m
    central_mask = below & central_x[None, None, :]
    west_mask = below & west_x[None, None, :]
    east_mask = below & east_x[None, None, :]
    outer_mask = west_mask | east_mask
    return {
        "x_partition_method": (
            "west 20 percent, central 60 percent, and east 20 percent evaluated separately"
        ),
        "west_central_limit_m": west_limit,
        "east_central_limit_m": east_limit,
        "central_below_rayleigh_rms": _masked_rms(field, central_mask),
        "west_below_rayleigh_rms": _masked_rms(field, west_mask),
        "east_below_rayleigh_rms": _masked_rms(field, east_mask),
        "outer_combined_below_rayleigh_rms": _masked_rms(field, outer_mask),
        "all_below_rayleigh_rms": _masked_rms(field, below),
        "rayleigh_layer_rms": _masked_rms(field, rayleigh),
        "top_two_km_rms": _masked_rms(field, heights >= ACTIVE_TOP_M - 2_000.0),
    }


def _masked_rms(
    values: np.ndarray[Any, np.dtype[np.float64]],
    mask: np.ndarray[Any, np.dtype[np.bool_]],
) -> float | None:
    selected = values[mask]
    if selected.size == 0:
        return None
    return float(np.sqrt(np.mean(selected**2)))


def evaluate_mountain_wave_run(
    *,
    settings: CloudChamberSettings,
    package: MountainWavePackageResult,
    reevaluation_identity: dict[str, Any] | None = None,
) -> MountainWaveRunEvidence:
    """Evaluate the one completed run directly from native terrain-following NetCDF."""
    manifest = load_run_manifest(package.manifest_path)
    if manifest.lifecycle_state != LifecycleState.COMPLETED or manifest.execution.exit_code != 0:
        raise MountainWaveCaseError(
            "Native output evaluation requires one normally completed CM1 process."
        )
    if manifest.app.commit != package.implementation_commit:
        raise MountainWaveCaseError("Completed run does not retain the implementation commit.")
    provenance = collect_cm1_provenance(settings)
    official_text = provenance.mountain_wave_namelist_path.read_text()
    generated_text = Path(manifest.generated_inputs.namelist_input or "").read_text()
    namelist_audit = audit_namelist(official_text, generated_text)
    generated_assignments = parse_namelist_assignments(generated_text)
    if _integer_value(generated_assignments, "stretch_z") != 0:
        raise MountainWaveCaseError("Gate B active-top evaluation requires stretch_z=0.")
    configured_nz = _integer_value(generated_assignments, "nz")
    configured_dz_m = float(generated_assignments["dz"])
    storage = StorageEstimate.model_validate(json.loads(package.storage_estimate_path.read_text()))

    output_candidates = [Path(path) for path in manifest.outputs.netcdf_paths]
    if not output_candidates:
        output_candidates = list(package.package_dir.glob("cm1out_*.nc*"))
    model_paths = accepted_model_output_paths(output_candidates)
    if not model_paths:
        raise MountainWaveCaseError("No native numbered CM1 model NetCDF files were found.")

    frames: list[dict[str, Any]] = []
    field_finite: dict[str, list[dict[str, Any]]] = {name: [] for name in REQUIRED_OUTPUT_FIELDS}
    first_inventory: dict[str, Any] | None = None
    first_coords: dict[str, np.ndarray[Any, np.dtype[np.float64]]] | None = None
    first_terrain: np.ndarray[Any, np.dtype[np.float64]] | None = None
    first_th: np.ndarray[Any, np.dtype[np.float64]] | None = None
    first_zh_physical: np.ndarray[Any, np.dtype[np.float64]] | None = None
    full_heights: np.ndarray[Any, np.dtype[np.float64]] | None = None
    active_top_evidence: ActiveTopEvidence | None = None
    terrain_frame_errors: list[dict[str, Any]] = []
    zh_frame_errors: list[dict[str, Any]] = []
    tangency_by_time: list[dict[str, Any]] = []
    wave_by_time: list[dict[str, Any]] = []
    boundary_by_time: list[dict[str, Any]] = []
    flow_by_time: list[dict[str, Any]] = []
    moisture_by_time: list[dict[str, Any]] = []
    active_top_by_time: list[dict[str, Any]] = []
    actual_times: list[float] = []

    for path in model_paths:
        with xr.open_dataset(path, decode_times=False) as dataset:
            time_seconds = _dataset_time_seconds(dataset)
            actual_times.append(time_seconds)
            if first_inventory is None:
                first_inventory = _dataset_inventory(dataset)
            _require_native_fields_and_coordinates(dataset)
            coords = _normalized_coordinates(dataset)
            terrain = _field_array(dataset, "zs", ("yh", "xh"))
            zh_physical = _field_array(dataset, "zhval", ("zh", "yh", "xh"))
            frame_active_top = resolve_active_top_evidence(
                dataset["zf"].values,
                str(dataset["zf"].attrs.get("units", "")),
                dataset["ztop"].values,
                str(dataset["ztop"].attrs.get("units", "")),
                configured_nz=configured_nz,
                configured_dz_m=configured_dz_m,
            )
            active_top_by_time.append(
                {
                    "time_seconds": time_seconds,
                    **frame_active_top.model_dump(mode="json"),
                }
            )

            if first_coords is None:
                first_coords = coords
                first_terrain = terrain
                first_th = _field_array(dataset, "th", ("zh", "yh", "xh"))
                active_top_evidence = frame_active_top
                full_heights = reconstruct_physical_heights(
                    terrain,
                    coords["zf"],
                    active_top_m=active_top_evidence.final_nominal_zf_m,
                )
                first_zh_physical = zh_physical
            else:
                _require_same_coordinates(first_coords, coords)
            assert first_coords is not None
            assert first_terrain is not None
            assert first_th is not None
            assert full_heights is not None
            assert active_top_evidence is not None

            terrain_expected = np.broadcast_to(
                analytic_itern1_terrain(coords["xh"])[None, :], terrain.shape
            )
            terrain_error = terrain - terrain_expected
            terrain_frame_errors.append(
                {
                    "time_seconds": time_seconds,
                    "analytic_max_abs_error_m": float(np.max(np.abs(terrain_error))),
                    "time_invariance_max_abs_error_m": float(
                        np.max(np.abs(terrain - first_terrain))
                    ),
                }
            )
            expected_zh = reconstruct_physical_heights(
                terrain,
                coords["zh"],
                active_top_m=active_top_evidence.final_nominal_zf_m,
            )
            zh_frame_errors.append(
                {
                    "time_seconds": time_seconds,
                    "transform_max_abs_error_m": float(np.max(np.abs(zh_physical - expected_zh))),
                    "minimum_column_spacing_m": float(np.min(np.diff(zh_physical, axis=0))),
                }
            )

            for name in REQUIRED_OUTPUT_FIELDS:
                values = np.asarray(dataset[name].values)
                finite = np.isfinite(values)
                field_finite[name].append(
                    {
                        "time_seconds": time_seconds,
                        "total_count": int(values.size),
                        "finite_count": int(np.count_nonzero(finite)),
                        "non_finite_count": int(values.size - np.count_nonzero(finite)),
                        "minimum": float(np.nanmin(values)),
                        "maximum": float(np.nanmax(values)),
                    }
                )

            u = _field_array(dataset, "u", ("zh", "yh", "xf"))
            v = _field_array(dataset, "v", ("zh", "yf", "xh"))
            w = _field_array(dataset, "w", ("zf", "yh", "xh"))
            th = _field_array(dataset, "th", ("zh", "yh", "xh"))
            prs = _field_array(dataset, "prs", ("zh", "yh", "xh"))
            _require_units(dataset, "u", {"m/s", "ms-1", "m/s-1", "m/s^1", "m s-1"})
            _require_units(dataset, "v", {"m/s", "ms-1", "m/s-1", "m/s^1", "m s-1"})
            _require_units(dataset, "w", {"m/s", "ms-1", "m/s-1", "m/s^1", "m s-1"})
            _require_units(dataset, "th", {"k"})
            _require_units(dataset, "prs", {"pa"})

            u_scalar = _collocate_staggered_axis(u, axis=-1, expected_size=coords["xh"].size)
            v_scalar = _collocate_staggered_axis(v, axis=-2, expected_size=coords["yh"].size)
            tangency = lower_boundary_tangency_metrics(
                x_m=coords["xh"],
                y_m=coords["yh"],
                zs_m=terrain,
                u_bottom=u[0, :, :],
                v_bottom=v[0, :, :],
                w_bottom=w[0, :, :],
            )
            tangency["time_seconds"] = time_seconds
            tangency_by_time.append(tangency)

            th_perturbation = th - first_th
            flow_by_time.append(
                _flow_frame_evidence(
                    time_seconds=time_seconds,
                    x_m=coords["xh"],
                    zh_physical_m=zh_physical,
                    th=th,
                    prs=prs,
                    u_scalar=u_scalar,
                    v_scalar=v_scalar,
                )
            )
            moisture_by_time.append(_moisture_evidence(dataset, time_seconds))
            wave_by_time.append(
                _wave_frame_evidence(
                    time_seconds=time_seconds,
                    x_m=coords["xh"],
                    y_m=coords["yh"],
                    w=w,
                    full_heights_m=full_heights,
                    th_perturbation=th_perturbation,
                    scalar_heights_m=zh_physical,
                )
            )
            boundary_metrics = {
                "time_seconds": time_seconds,
                "w": central_boundary_metrics(w, coords["xh"], full_heights),
                "th_perturbation": central_boundary_metrics(
                    th_perturbation, coords["xh"], zh_physical
                ),
            }
            boundary_by_time.append(boundary_metrics)
            frames.append(
                {
                    "filename": path.name,
                    "time_seconds": time_seconds,
                    "bytes": path.stat().st_size,
                }
            )

    assert first_inventory is not None
    assert first_coords is not None
    assert first_terrain is not None
    assert first_th is not None
    assert first_zh_physical is not None
    assert full_heights is not None
    assert active_top_evidence is not None

    _require_complete_times(actual_times)
    non_finite_total = sum(
        item["non_finite_count"] for records in field_finite.values() for item in records
    )
    if non_finite_total:
        raise MountainWaveCaseError(
            f"Required native fields contain {non_finite_total} non-finite values."
        )

    x = first_coords["xh"]
    terrain_profile = first_terrain[0, :]
    terrain_max_index = int(np.argmax(terrain_profile))
    terrain_precision_tolerance = max(
        1.0e-4,
        float(np.finfo(np.float32).eps * max(1.0, np.max(np.abs(first_terrain))) * 32.0),
    )
    terrain_max_error = max(
        float(item["analytic_max_abs_error_m"]) for item in terrain_frame_errors
    )
    terrain_static_error = max(
        float(item["time_invariance_max_abs_error_m"]) for item in terrain_frame_errors
    )
    zh_max_error = max(float(item["transform_max_abs_error_m"]) for item in zh_frame_errors)
    if terrain_max_error > terrain_precision_tolerance:
        raise MountainWaveCaseError(
            "Emitted terrain does not match the exact itern=1 analytic terrain."
        )
    if terrain_static_error > terrain_precision_tolerance:
        raise MountainWaveCaseError("Emitted terrain is not time invariant.")
    if zh_max_error > max(0.01, terrain_precision_tolerance * 8.0):
        raise MountainWaveCaseError("zhval does not match the physical-height transform.")

    output_inventory = {
        "model_output_files": frames,
        "actual_model_output_count": len(frames),
        "expected_model_output_count": len(EXPECTED_OUTPUT_TIMES_SECONDS),
        "actual_times_seconds": actual_times,
        "expected_times_seconds": list(EXPECTED_OUTPUT_TIMES_SECONDS),
        "total_model_netcdf_bytes": sum(path.stat().st_size for path in model_paths),
        "variable_inventory": first_inventory["variables"],
        "coordinate_inventory": first_inventory["coordinates"],
        "global_attributes": first_inventory["global_attributes"],
        "required_field_finite_counts_by_time": field_finite,
        "additional_emitted_fields": sorted(
            set(first_inventory["variables"]) - set(REQUIRED_OUTPUT_FIELDS)
        ),
    }
    terrain_and_coordinates = {
        "analytic_terrain_equation": "400 / (1 + ((x - 100 m) / 1000 m)^2)",
        "terrain_max_m": float(np.max(first_terrain)),
        "terrain_max_x_m": float(x[terrain_max_index]),
        "terrain_domain_min_m": float(np.min(first_terrain)),
        "analytic_max_abs_error_m": terrain_max_error,
        "time_invariance_max_abs_error_m": terrain_static_error,
        "precision_derived_tolerance_m": terrain_precision_tolerance,
        "terrain_half_height_nearest_points": _terrain_half_height_points(x, terrain_profile),
        "nominal_zh_units_in_output": first_inventory["coordinates"]["zh"]["units"],
        "nominal_zf_units_in_output": first_inventory["coordinates"]["zf"]["units"],
        "zhval_units_in_output": first_inventory["variables"]["zhval"]["units"],
        "active_top_evidence": active_top_evidence.model_dump(mode="json"),
        "active_top_checks_by_time": active_top_by_time,
        "zhval_transform_max_abs_error_m": zh_max_error,
        "minimum_scalar_column_spacing_m": float(np.min(np.diff(first_zh_physical, axis=0))),
        "full_level_bottom_equals_terrain_max_abs_error_m": float(
            np.max(np.abs(full_heights[0] - first_terrain))
        ),
        "full_level_top_constant_range_m": float(
            np.max(full_heights[-1]) - np.min(full_heights[-1])
        ),
        "full_level_top_m": float(np.mean(full_heights[-1])),
        "per_frame_checks": zh_frame_errors,
    }
    base_state_and_flow = {
        "configured_dry_state": True,
        "configured_imoist": 0,
        "moisture_field_evidence_by_time": moisture_by_time,
        "flow_and_base_state_by_time": flow_by_time,
        "initial_stability": _initial_stability_evidence(
            first_th, first_zh_physical, x_m=first_coords["xh"]
        ),
        "singleton_y_scalar_size": int(first_coords["yh"].size),
        "coriolis_pressure_gradient_behavior": _background_flow_change(flow_by_time),
    }
    lower_boundary = {
        "physical_condition": "w = u * dzs/dx + v * dzs/dy",
        "per_time_metrics": tangency_by_time,
        "maximum_abs_residual_m_s": max(
            max(abs(float(item["residual_min_m_s"])), abs(float(item["residual_max_m_s"])))
            for item in tangency_by_time
        ),
    }
    representative = _representative_time_records(wave_by_time)
    wave_structure = {
        "representative_times": representative,
        "all_times": wave_by_time,
        "descriptive_coherence_method": (
            "contiguous sign-region counts use 10 percent of each frame's maximum absolute w "
            "as a descriptive mask, not a benchmark pass tolerance"
        ),
    }
    boundary_and_damping = {
        "rayleigh_onset_m": RAYLEIGH_ONSET_M,
        "metrics_by_time": boundary_by_time,
        "interpretation_method": (
            "compare RMS w and theta perturbations in separate west 20 percent, central 60 "
            "percent, and east 20 percent zones; compare below 14 km with Rayleigh and top "
            "layers; east-zone growth is retained separately from upstream west reflection"
        ),
    }
    runtime_integrity = _runtime_integrity_evidence(package, manifest, model_paths)
    caveats = list(manifest.outputs.runtime_warnings)
    caveats.extend(
        [
            "official_source_bundle_has_no_pointwise_reference_field_or_numeric_tolerance",
            "two_dimensional_dry_case_does_not_validate_moist_or_three_dimensional_behavior",
            "current_flat_grid_browser_payloads_are_not_used_as_acceptance_evidence",
        ]
    )
    return MountainWaveRunEvidence(
        run_id=package.run_id,
        implementation_commit=package.implementation_commit,
        generated_at=datetime.now(UTC),
        reevaluation_identity=reevaluation_identity
        or {
            "run_id": package.run_id,
            "implementation_commit": package.implementation_commit,
            "verification_mode": "initial_same-process_post-run_evaluation",
            "file_sha256": {path.name: sha256_file(path) for path in model_paths},
            "all_inputs_match_pinned_original": False,
        },
        lifecycle={
            "state": manifest.lifecycle_state.value,
            "exit_code": manifest.execution.exit_code,
            "started_at": manifest.execution.started_at,
            "finished_at": manifest.execution.finished_at,
            "exactly_one_process_authorized": True,
        },
        provenance=provenance.report_record(),
        namelist_audit=namelist_audit,
        storage_preflight=storage,
        output_inventory=output_inventory,
        terrain_and_coordinates=terrain_and_coordinates,
        base_state_and_flow=base_state_and_flow,
        lower_boundary=lower_boundary,
        wave_structure=wave_structure,
        boundary_and_damping=boundary_and_damping,
        runtime_integrity=runtime_integrity,
        caveats=caveats,
    )


def reevaluate_preserved_mountain_wave_run(
    *,
    settings: CloudChamberSettings,
    package: MountainWavePackageResult,
) -> MountainWaveRunEvidence:
    """Evaluate the PM-authorized preserved run without any package or launch operation."""
    evaluator_commit = verified_clean_git_commit()
    before = verify_evaluation_input_identity(
        package,
        expected_run_id=PRESERVED_GATE_B_RUN_ID,
        expected_implementation_commit=PRESERVED_GATE_B_IMPLEMENTATION_COMMIT,
        expected_file_sha256=PRESERVED_GATE_B_EVALUATION_INPUT_SHA256,
    )
    evidence = evaluate_mountain_wave_run(
        settings=settings,
        package=package,
        reevaluation_identity=before,
    )
    after = verify_evaluation_input_identity(
        package,
        expected_run_id=PRESERVED_GATE_B_RUN_ID,
        expected_implementation_commit=PRESERVED_GATE_B_IMPLEMENTATION_COMMIT,
        expected_file_sha256=PRESERVED_GATE_B_EVALUATION_INPUT_SHA256,
    )
    if before["file_sha256"] != after["file_sha256"]:
        raise MountainWaveCaseError("Preserved evaluation inputs changed during analysis.")
    identity = dict(after)
    identity["evaluator_commit"] = evaluator_commit
    identity["verified_before_and_after_evaluation"] = True
    return evidence.model_copy(update={"reevaluation_identity": identity})


def write_mountain_wave_run_evidence(path: Path, evidence: MountainWaveRunEvidence) -> None:
    path.write_text(evidence.to_json_text())


def _dataset_time_seconds(dataset: xr.Dataset) -> float:
    if "time" not in dataset:
        raise MountainWaveCaseError("Native output is missing the time coordinate.")
    values = normalize_time_to_seconds(
        dataset["time"].values,
        str(dataset["time"].attrs.get("units", "")),
    ).reshape(-1)
    if values.size != 1:
        raise MountainWaveCaseError("Each numbered native file must contain exactly one time.")
    return float(values[0])


def _require_complete_times(actual_times: list[float]) -> None:
    rounded = [int(round(value)) for value in actual_times]
    if len(set(rounded)) != len(rounded):
        raise MountainWaveCaseError(f"Duplicate model output times: {rounded}")
    if rounded != list(EXPECTED_OUTPUT_TIMES_SECONDS):
        missing = sorted(set(EXPECTED_OUTPUT_TIMES_SECONDS) - set(rounded))
        extra = sorted(set(rounded) - set(EXPECTED_OUTPUT_TIMES_SECONDS))
        raise MountainWaveCaseError(
            f"Model output times differ from expected cadence; missing={missing}, extra={extra}."
        )


def _dataset_inventory(dataset: xr.Dataset) -> dict[str, Any]:
    variables = {
        name: {
            "dimensions": list(item.dims),
            "shape": list(item.shape),
            "dtype": str(item.dtype),
            "units": str(item.attrs.get("units", "")),
            "long_name": str(item.attrs.get("long_name", "")),
            "staggering": _staggering_from_dims(item.dims),
        }
        for name, item in dataset.data_vars.items()
    }
    coordinates = {
        name: {
            "dimensions": list(item.dims),
            "shape": list(item.shape),
            "dtype": str(item.dtype),
            "units": str(item.attrs.get("units", "")),
            "long_name": str(item.attrs.get("long_name", "")),
        }
        for name, item in dataset.coords.items()
    }
    if "ztop" in dataset and "ztop" not in variables:
        item = dataset["ztop"]
        variables["ztop"] = {
            "dimensions": list(item.dims),
            "shape": list(item.shape),
            "dtype": str(item.dtype),
            "units": str(item.attrs.get("units", "")),
            "long_name": str(item.attrs.get("long_name", "")),
            "staggering": "scalar_metadata",
        }
    return {
        "variables": variables,
        "coordinates": coordinates,
        "global_attributes": {name: _json_scalar(value) for name, value in dataset.attrs.items()},
    }


def _staggering_from_dims(dims: tuple[Any, ...]) -> str:
    if "xf" in dims:
        return "u_staggered_x"
    if "yf" in dims:
        return "v_staggered_y"
    if "zf" in dims:
        return "w_staggered_z"
    if "zh" in dims:
        return "scalar_vertical_grid"
    if "xh" in dims and "yh" in dims:
        return "scalar_horizontal_grid"
    return "metadata_or_unknown"


def _json_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _require_native_fields_and_coordinates(dataset: xr.Dataset) -> None:
    missing_fields = [name for name in REQUIRED_OUTPUT_FIELDS if name not in dataset]
    missing_coordinates = [name for name in REQUIRED_COORDINATES if name not in dataset]
    if "ztop" not in dataset:
        missing_coordinates.append("ztop")
    if missing_fields or missing_coordinates:
        raise MountainWaveCaseError(
            f"Native output inventory incomplete; fields={missing_fields}, "
            f"coordinates={missing_coordinates}."
        )


def _normalized_coordinates(
    dataset: xr.Dataset,
) -> dict[str, np.ndarray[Any, np.dtype[np.float64]]]:
    return {
        name: normalize_length_to_m(dataset[name].values, str(dataset[name].attrs.get("units", "")))
        for name in ("xh", "xf", "yh", "yf", "zh", "zf")
    }


def _require_same_coordinates(
    expected: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
    actual: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
) -> None:
    for name, values in expected.items():
        if values.shape != actual[name].shape or not np.array_equal(values, actual[name]):
            raise MountainWaveCaseError(f"Coordinate {name} changes between output files.")


def _field_array(
    dataset: xr.Dataset,
    name: str,
    dimensions: tuple[str, ...],
) -> np.ndarray[Any, np.dtype[np.float64]]:
    item = dataset[name]
    if "time" in item.dims:
        if item.sizes["time"] != 1:
            raise MountainWaveCaseError(f"{name} has more than one time in a numbered file.")
        item = item.isel(time=0)
    unexpected = [dim for dim in item.dims if dim not in dimensions and item.sizes[dim] != 1]
    if unexpected:
        raise MountainWaveCaseError(f"{name} has unexpected dimensions: {unexpected}")
    for dim in list(item.dims):
        if dim not in dimensions:
            item = item.isel({dim: 0})
    if set(item.dims) != set(dimensions):
        raise MountainWaveCaseError(f"{name} dimensions are {item.dims}; expected {dimensions}.")
    return np.asarray(item.transpose(*dimensions).values, dtype=np.float64)


def _require_units(dataset: xr.Dataset, name: str, accepted: set[str]) -> None:
    actual = str(dataset[name].attrs.get("units", "")).strip().lower()
    normalized = actual.replace(" ", "")
    accepted_normalized = {unit.replace(" ", "") for unit in accepted}
    if normalized not in accepted_normalized:
        raise MountainWaveCaseError(
            f"Required field {name} has unsupported units {actual!r}; accepted={accepted}."
        )


def _flow_frame_evidence(
    *,
    time_seconds: float,
    x_m: np.ndarray[Any, np.dtype[np.float64]],
    zh_physical_m: np.ndarray[Any, np.dtype[np.float64]],
    th: np.ndarray[Any, np.dtype[np.float64]],
    prs: np.ndarray[Any, np.dtype[np.float64]],
    u_scalar: np.ndarray[Any, np.dtype[np.float64]],
    v_scalar: np.ndarray[Any, np.dtype[np.float64]],
) -> dict[str, Any]:
    upstream = x_m <= float(np.quantile(x_m, 0.2))
    pressure_difference = np.diff(prs, axis=0)
    return {
        "time_seconds": time_seconds,
        "upstream_x_max_m": float(np.max(x_m[upstream])),
        "upstream_u_mean_m_s": float(np.mean(u_scalar[:, :, upstream])),
        "upstream_u_min_m_s": float(np.min(u_scalar[:, :, upstream])),
        "upstream_u_max_m_s": float(np.max(u_scalar[:, :, upstream])),
        "domain_u_mean_m_s": float(np.mean(u_scalar)),
        "domain_v_mean_m_s": float(np.mean(v_scalar)),
        "domain_v_max_abs_m_s": float(np.max(np.abs(v_scalar))),
        "theta_min_k": float(np.min(th)),
        "theta_max_k": float(np.max(th)),
        "pressure_min_pa": float(np.min(prs)),
        "pressure_max_pa": float(np.max(prs)),
        "pressure_increasing_vertical_difference_count": int(
            np.count_nonzero(pressure_difference > 0.0)
        ),
        "pressure_vertical_difference_count": int(pressure_difference.size),
        "minimum_scalar_height_m": float(np.min(zh_physical_m)),
        "maximum_scalar_height_m": float(np.max(zh_physical_m)),
    }


def _initial_stability_evidence(
    theta: np.ndarray[Any, np.dtype[np.float64]],
    physical_height_m: np.ndarray[Any, np.dtype[np.float64]],
    *,
    x_m: np.ndarray[Any, np.dtype[np.float64]],
) -> dict[str, Any]:
    upstream = x_m <= float(np.quantile(x_m, 0.2))
    delta_theta = np.diff(theta[:, :, upstream], axis=0)
    delta_height = np.diff(physical_height_m[:, :, upstream], axis=0)
    theta_mid = 0.5 * (theta[:-1, :, upstream] + theta[1:, :, upstream])
    n_squared = 9.81 / theta_mid * delta_theta / delta_height
    finite = n_squared[np.isfinite(n_squared)]
    return {
        "method": "N^2=(g/theta_mid)*(delta theta/delta physical height) in west 20 percent",
        "sample_count": int(finite.size),
        "n_squared_min_s_2": float(np.min(finite)),
        "n_squared_median_s_2": float(np.median(finite)),
        "n_squared_max_s_2": float(np.max(finite)),
        "configured_n_squared_s_2": 1.0e-4,
    }


def _background_flow_change(flow_by_time: list[dict[str, Any]]) -> dict[str, Any]:
    first = flow_by_time[0]
    last = flow_by_time[-1]
    return {
        "method": "compare initial and final domain/upstream means; no pointwise tolerance imposed",
        "initial_domain_u_mean_m_s": first["domain_u_mean_m_s"],
        "final_domain_u_mean_m_s": last["domain_u_mean_m_s"],
        "domain_u_mean_change_m_s": (
            float(last["domain_u_mean_m_s"]) - float(first["domain_u_mean_m_s"])
        ),
        "initial_domain_v_mean_m_s": first["domain_v_mean_m_s"],
        "final_domain_v_mean_m_s": last["domain_v_mean_m_s"],
        "domain_v_mean_change_m_s": (
            float(last["domain_v_mean_m_s"]) - float(first["domain_v_mean_m_s"])
        ),
    }


def _moisture_evidence(dataset: xr.Dataset, time_seconds: float) -> dict[str, Any]:
    moisture_names = sorted(
        str(name)
        for name in dataset.data_vars
        if str(name).lower() in {"qv", "qc", "ql", "qr", "qi", "qs", "qg", "qh", "dbz", "cref"}
    )
    fields: dict[str, Any] = {}
    for name in moisture_names:
        values = np.asarray(dataset[name].values, dtype=np.float64)
        fields[name] = {
            "units": str(dataset[name].attrs.get("units", "")),
            "minimum": float(np.nanmin(values)),
            "maximum": float(np.nanmax(values)),
            "maximum_abs": float(np.nanmax(np.abs(values))),
        }
    return {"time_seconds": time_seconds, "emitted_moisture_like_fields": fields}


def _wave_frame_evidence(
    *,
    time_seconds: float,
    x_m: np.ndarray[Any, np.dtype[np.float64]],
    y_m: np.ndarray[Any, np.dtype[np.float64]],
    w: np.ndarray[Any, np.dtype[np.float64]],
    full_heights_m: np.ndarray[Any, np.dtype[np.float64]],
    th_perturbation: np.ndarray[Any, np.dtype[np.float64]],
    scalar_heights_m: np.ndarray[Any, np.dtype[np.float64]],
) -> dict[str, Any]:
    w_max_index = tuple(int(value) for value in np.unravel_index(np.argmax(w), w.shape))
    w_min_index = tuple(int(value) for value in np.unravel_index(np.argmin(w), w.shape))
    th_max_index = tuple(
        int(value) for value in np.unravel_index(np.argmax(th_perturbation), th_perturbation.shape)
    )
    th_min_index = tuple(
        int(value) for value in np.unravel_index(np.argmin(th_perturbation), th_perturbation.shape)
    )
    central_x = (x_m >= float(np.quantile(x_m, 0.2))) & (x_m <= float(np.quantile(x_m, 0.8)))
    central_w = w[:, :, central_x]
    central_heights = full_heights_m[:, :, central_x]
    below = central_heights < RAYLEIGH_ONSET_M
    selected = central_w[below]
    threshold = 0.1 * float(np.max(np.abs(selected))) if selected.size else 0.0
    y_index = 0 if y_m.size == 1 else int(y_m.size // 2)
    cross_section = w[:, y_index, :]
    sign_regions = _sign_region_count(cross_section, threshold)
    return {
        "time_seconds": time_seconds,
        "w_min_m_s": float(np.min(w)),
        "w_max_m_s": float(np.max(w)),
        "w_min_location": _location_record(w_min_index, x_m, y_m, full_heights_m),
        "w_max_location": _location_record(w_max_index, x_m, y_m, full_heights_m),
        "theta_perturbation_min_k": float(np.min(th_perturbation)),
        "theta_perturbation_max_k": float(np.max(th_perturbation)),
        "theta_perturbation_min_location": _location_record(
            th_min_index, x_m, y_m, scalar_heights_m
        ),
        "theta_perturbation_max_location": _location_record(
            th_max_index, x_m, y_m, scalar_heights_m
        ),
        "central_below_rayleigh_positive_w_fraction": (
            float(np.mean(selected > 0.0)) if selected.size else None
        ),
        "central_below_rayleigh_negative_w_fraction": (
            float(np.mean(selected < 0.0)) if selected.size else None
        ),
        "descriptive_sign_mask_m_s": threshold,
        "cross_section_contiguous_sign_region_count": sign_regions,
    }


def _location_record(
    index: tuple[int, ...],
    x_m: np.ndarray[Any, np.dtype[np.float64]],
    y_m: np.ndarray[Any, np.dtype[np.float64]],
    physical_heights_m: np.ndarray[Any, np.dtype[np.float64]],
) -> dict[str, float]:
    k, j, i = index
    return {
        "x_m": float(x_m[i]),
        "y_m": float(y_m[j]),
        "z_m": float(physical_heights_m[k, j, i]),
    }


def _sign_region_count(
    cross_section: np.ndarray[Any, np.dtype[np.float64]], threshold: float
) -> int:
    if threshold <= 0.0:
        return 0
    signs = np.where(cross_section >= threshold, 1, np.where(cross_section <= -threshold, -1, 0))
    count = 0
    for row in signs:
        previous = 0
        for value in row:
            current = int(value)
            if current != 0 and current != previous:
                count += 1
            if current != 0:
                previous = current
    return count


def _representative_time_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets = (0, 432, 1_080, 2_160)
    selected: list[dict[str, Any]] = []
    for target in targets:
        record = min(records, key=lambda item: abs(float(item["time_seconds"]) - target))
        if record not in selected:
            selected.append(record)
    return selected


def _terrain_half_height_points(
    x_m: np.ndarray[Any, np.dtype[np.float64]],
    terrain_m: np.ndarray[Any, np.dtype[np.float64]],
) -> dict[str, Any]:
    left = x_m <= TERRAIN_CENTER_M
    right = x_m >= TERRAIN_CENTER_M
    target = TERRAIN_HEIGHT_M / 2.0
    left_index = int(np.argmin(np.where(left, np.abs(terrain_m - target), np.inf)))
    right_index = int(np.argmin(np.where(right, np.abs(terrain_m - target), np.inf)))
    return {
        "target_height_m": target,
        "left_x_m": float(x_m[left_index]),
        "left_height_m": float(terrain_m[left_index]),
        "right_x_m": float(x_m[right_index]),
        "right_height_m": float(terrain_m[right_index]),
        "source_half_width_m": TERRAIN_HALF_WIDTH_M,
    }


def _runtime_integrity_evidence(
    package: MountainWavePackageResult,
    manifest: RunManifest,
    model_paths: list[Path],
) -> dict[str, Any]:
    stdout_path = Path(manifest.execution.stdout_log or "")
    stderr_path = Path(manifest.execution.stderr_log or "")
    stdout_text = stdout_path.read_text(errors="replace") if stdout_path.is_file() else ""
    stderr_text = stderr_path.read_text(errors="replace") if stderr_path.is_file() else ""
    flags = [
        name
        for name in (
            "IEEE_INVALID_FLAG",
            "IEEE_DIVIDE_BY_ZERO",
            "IEEE_OVERFLOW_FLAG",
            "IEEE_UNDERFLOW_FLAG",
        )
        if name in stderr_text
    ]
    wall_clock_seconds: float | None = None
    if manifest.execution.started_at is not None and manifest.execution.finished_at is not None:
        wall_clock_seconds = (
            manifest.execution.finished_at - manifest.execution.started_at
        ).total_seconds()
    all_paths = [path for path in package.package_dir.rglob("*") if path.is_file()]
    stats_files = sorted(
        path for path in all_paths if "stats" in path.name.lower() and path not in model_paths
    )
    return {
        "execution_mode": "existing_local_run_manager_single_process",
        "command": ["configured_cm1_run_directory/cm1.exe"],
        "implementation_commit": package.implementation_commit,
        "started_at": manifest.execution.started_at,
        "finished_at": manifest.execution.finished_at,
        "wall_clock_seconds": wall_clock_seconds,
        "exit_code": manifest.execution.exit_code,
        "normal_termination_marker_present": "Program terminated normally" in stdout_text,
        "stderr_bytes": len(stderr_text.encode()),
        "stdout_bytes": len(stdout_text.encode()),
        "floating_point_flags": flags,
        "runtime_warnings": list(manifest.outputs.runtime_warnings),
        "stats_artifacts": [path.name for path in stats_files],
        "stats_evidence": _stats_evidence(stats_files),
        "model_netcdf_bytes": sum(path.stat().st_size for path in model_paths),
        "logs_bytes": sum(path.stat().st_size for path in all_paths if "logs" in path.parts),
        "package_total_bytes": sum(path.stat().st_size for path in all_paths),
        "peak_memory_evidence": "not_available_from_current_local_run_manager",
    }


def _stats_evidence(paths: list[Path]) -> dict[str, Any]:
    netcdf_paths = [path for path in paths if path.suffix.lower() in {".nc", ".nc4"}]
    if not netcdf_paths:
        return {
            "status": "no_stats_netcdf_available",
            "selected_fields": {},
        }
    path = netcdf_paths[0]
    with xr.open_dataset(path, decode_times=False) as dataset:
        selected_names = sorted(
            str(name)
            for name in dataset.data_vars
            if any(
                token in str(name).lower()
                for token in ("cfl", "mass", "energ", "tmass", "tmois", "qmass")
            )
        )
        selected: dict[str, Any] = {}
        for name in selected_names:
            values = np.asarray(dataset[name].values, dtype=np.float64)
            selected[name] = {
                "dimensions": list(dataset[name].dims),
                "shape": list(dataset[name].shape),
                "units": str(dataset[name].attrs.get("units", "")),
                "finite_count": int(np.count_nonzero(np.isfinite(values))),
                "non_finite_count": int(values.size - np.count_nonzero(np.isfinite(values))),
                "minimum": float(np.nanmin(values)),
                "maximum": float(np.nanmax(values)),
            }
        time_evidence: dict[str, Any] | None = None
        if "time" in dataset:
            seconds = normalize_time_to_seconds(
                dataset["time"].values,
                str(dataset["time"].attrs.get("units", "")),
            ).reshape(-1)
            time_evidence = {
                "count": int(seconds.size),
                "first_seconds": float(seconds[0]),
                "last_seconds": float(seconds[-1]),
            }
        return {
            "status": "stats_netcdf_inspected",
            "filename": path.name,
            "time": time_evidence,
            "selected_fields": selected,
            "all_variable_names": sorted(str(name) for name in dataset.data_vars),
        }
