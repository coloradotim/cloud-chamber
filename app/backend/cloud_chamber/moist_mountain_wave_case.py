"""Deterministic packaging and native-output evidence for issue #407's moist wave case."""

from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber import __version__
from cloud_chamber.mountain_wave_case import (
    accepted_model_output_paths,
    active_cm1_processes,
    collect_cm1_provenance,
    lower_boundary_tangency_metrics,
    normalize_length_to_m,
    normalize_time_to_seconds,
    parse_namelist_assignments,
    reconstruct_physical_heights,
    replace_namelist_assignment,
    sha256_file,
    sha256_text,
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

CASE_ID = "cm1_r21_1_toy2011_boulder_moist_wave_4000s_v1"
SCENARIO_ID = CASE_ID
EVIDENCE_VERSION = "moist_mountain_wave_gate_d_e_v2"
PRESERVED_RUN_ID = "moist-mountain-wave-toy-1972-20260721T215226Z"
SOURCE_LOCK_RELATIVE_PATH = Path("docs/research/mountain-waves/moist-reference-case-selection.md")
SOURCE_LOCK_SHA256 = "939c4b7c6b067c125402383e7ed966b6e09eed2f5e0c0762ca6331a6f381b20b"
IGRA_STATION_ID = "USM00072476"
IGRA_OBSERVATION_TIME = "1972-01-11T12:00:00Z"
IGRA_SOURCE_RECORD_SHA256 = "33953228bc6bcdf7d65c5cf800b5f8bed9a71aedda910edb4d32a28bef37e652"

NX = 220
NY = 1
NZ = 125
DX_M = 1_000.0
DY_M = 1_000.0
DZ_M = 200.0
ACTIVE_TOP_M = 25_000.0
TERRAIN_HEIGHT_M = 2_000.0
TERRAIN_HALF_WIDTH_M = 10_000.0
TERRAIN_CENTER_M = 500.0
EXPECTED_DURATION_SECONDS = 4_000
EXPECTED_OUTPUT_CADENCE_SECONDS = 200
EXPECTED_OUTPUT_TIMES_SECONDS = tuple(
    range(0, EXPECTED_DURATION_SECONDS + 1, EXPECTED_OUTPUT_CADENCE_SECONDS)
)
NUMERICAL_CLEAR_FLOOR_KG_KG = 1.0e-12
CLOUD_FLOOR_KG_KG = 1.0e-6
MATERIAL_PEAK_KG_KG = 2.0e-4
MIN_COHERENT_CELLS = 8
MIN_PERSISTENT_FRAMES = 3
INTERIOR_X_BOUNDS_M = (-40_000.0, 60_000.0)
UPSTREAM_X_BOUNDS_M = (-100_000.0, -60_000.0)
EVALUATION_TOP_M = 12_000.0
EDGE_WIDTH_M = 10_000.0
REQUIRED_OUTPUT_FIELDS = ("zs", "zhval", "th", "prs", "qv", "ql", "u", "v", "w")
REQUIRED_COORDINATES = ("time", "xh", "xf", "yh", "yf", "zh", "zf")
_OUTPUT_LIKE_PATTERNS = ("cm1out*", "*.nc", "*.nc4", "*.ctl")
PRESERVED_RUN_ARTIFACT_SHA256 = {
    "run_manifest.json": "026a3887f4120fa3e2e6663d8a486a28f83338ff5b3be09639cd245fd8ba1845",
    "case_manifest.json": "208d05ba72149a53f423ef13fa97cab4e298f374f20f30e6ea9c12fc6e016a78",
    "namelist.input": "d94f54d5e60627daf9020aa9eceaecd4f3b35fa1c81590186c72c7ccf99a10be",
    "input_sounding": "cb43243d04e328e9dd1a08ff52139f5a6096dcbe89f7b0d0e4aeb536f6a33b22",
    "perts.dat": "10d4fd60cac78acc2a19fe4a84b5d3c12c7e8a2ab58789faecebc40bf23e1028",
    "execution_preflight.json": "917f2f17c33f602760801c4447e014ef09e0f6031a2218b9dba4a49a2e0b9185",
    "logs/stdout.log": "42a120685c18d29d855cdea5039f54a3530157f2d36497cd41318f1af97fc0cb",
    "logs/stderr.log": "6e8658cbd2bf71044b960ff59b4371a98438c32a7d4cb54ab562294b8cc4f05d",
    "cm1out_stats.nc": "46cf824b20ab0c4b00806cd9ec2b0e52833e35d1913e2fa4d9205e12a523ff7a",
    "cm1out_000001.nc": "a62959ceaae1c108ea0d2eb3805809615faf233a0e35096eeeceac18329ae9a5",
    "cm1out_000002.nc": "79a4d4a95534b29dbd98286d1086dbf2a168af4484862b994e30e09af3b76c0a",
    "cm1out_000003.nc": "bbe5d4d40bcf59acb4c87d44a2aa73060d5dca9eb72572ccc58ec87a6b33ecf3",
    "cm1out_000004.nc": "b5bcad79828812d1f81b1d1972622d492e7967e97dc35a9c6b505301033e16c1",
    "cm1out_000005.nc": "5dd3efac88159d955e6e4e2880ca3faf06c7024c3ffc9de4c6f45ba43e5493df",
    "cm1out_000006.nc": "cf5aeb035f784fc8f252f08a92b6bb6a78740431b6060a20bdbc30a3d6540699",
    "cm1out_000007.nc": "48091a925b4e9a9219c6f1e07902ea1a09a8f427113b5f25589d0a2ef322019e",
    "cm1out_000008.nc": "183ceae29cd44cc767a8987db4f218c9479d283d8f7330547d65992e02094752",
    "cm1out_000009.nc": "294fe39221cfe6af1d48ea65093bc0698d903bc848535d349371f898cf66b6d6",
    "cm1out_000010.nc": "316fb4c2c0bb2c93ef588eeae50516b78c2bca6087bc85cf62da7596c9a526b6",
    "cm1out_000011.nc": "41a9a6c8fdd7a81e3ea1074fb2cb717a312a46602e814e58c57f5eb1b81fd2ce",
    "cm1out_000012.nc": "e7ce11ae105ea035d9dc0f408647507a3ed51a7165eb75fae2fc38e3549d1572",
    "cm1out_000013.nc": "93d0b34b075a194f5c621c7f8d5b0ca8de82f51170fad30456962fdacaf298e7",
    "cm1out_000014.nc": "9410bcb03d2ff9f251356f01f9d19391eaa6d254f1bf6497f27901e461ff75e8",
    "cm1out_000015.nc": "49956dcf04d32f2569e8d585e4d76af23e4765012c8111a63b1d426b93fe0d73",
    "cm1out_000016.nc": "724a5acf714b2fa1a55e497a9a3c5343dea4608863db7a1702af5187d7b7063d",
    "cm1out_000017.nc": "9bc9e235bacfc73424651bf547c68c56cf24d3422741f5d732660ff647db4290",
    "cm1out_000018.nc": "82d3a544ff5026ad74ec066c90adcddf17251ef161bccb0053684b57c3f20375",
    "cm1out_000019.nc": "9caac2cd58d33852934579dc2973c183113383f23665f2ed8b17795759e67613",
    "cm1out_000020.nc": "c6920f6d47eb6b0fb8a2cfd7ca8ac901a49e92802d40f9f1f161937eadb76023",
    "cm1out_000021.nc": "0f8f31f2bf91ca80d430b326025cc734f4295e1ad6c687d2bae7f02ae0fe2b43",
}


class MoistMountainWaveCaseError(RuntimeError):
    """Raised when source lock, package, preflight, or evaluation must stop."""


@dataclass(frozen=True)
class ObservedSoundingRow:
    pressure_pa: int
    geopotential_height_m: int
    temperature_tenths_c: int
    relative_humidity_tenths_percent: int
    wind_direction_deg: int
    wind_speed_tenths_m_s: int


# Pressure-level rows copied from the hash-pinned 1200 UTC Grand Junction IGRA record.
OBSERVED_SOUNDING_ROWS = (
    ObservedSoundingRow(85000, 1514, -6, 410, 121, 50),
    ObservedSoundingRow(80700, 1929, 2, 360, 176, 60),
    ObservedSoundingRow(70000, 3048, -88, 560, 258, 120),
    ObservedSoundingRow(62400, 3927, -155, 830, 284, 160),
    ObservedSoundingRow(59500, 4285, -180, 770, 291, 170),
    ObservedSoundingRow(57500, 4540, -184, 750, 293, 210),
    ObservedSoundingRow(54400, 4952, -209, 950, 292, 260),
    ObservedSoundingRow(52800, 5173, -204, 940, 292, 290),
    ObservedSoundingRow(50000, 5574, -229, 750, 298, 310),
    ObservedSoundingRow(47500, 5949, -239, 680, 302, 330),
    ObservedSoundingRow(43200, 6636, -283, 600, 306, 360),
    ObservedSoundingRow(40000, 7182, -335, 710, 306, 380),
    ObservedSoundingRow(35300, 8048, -399, 670, 306, 440),
    ObservedSoundingRow(30000, 9138, -491, -9999, 316, 410),
    ObservedSoundingRow(25000, 10309, -589, -9999, 334, 440),
    ObservedSoundingRow(21300, 11298, -658, -9999, 333, 430),
    ObservedSoundingRow(20000, 11680, -666, -9999, 321, 420),
    ObservedSoundingRow(18200, 12251, -662, -9999, 310, 410),
    ObservedSoundingRow(17600, 12457, -599, -9999, 309, 370),
    ObservedSoundingRow(16800, 12748, -592, -9999, 308, 310),
    ObservedSoundingRow(15000, 13457, -602, -9999, 299, 340),
    ObservedSoundingRow(13500, 14121, -562, -9999, 292, 180),
    ObservedSoundingRow(11600, 15071, -624, -9999, 274, 230),
    ObservedSoundingRow(10000, 15979, -662, -9999, 287, 300),
    ObservedSoundingRow(7600, 17669, -597, -9999, 281, 210),
    ObservedSoundingRow(7400, 17838, -530, -9999, 282, 210),
    ObservedSoundingRow(7000, 18196, -538, -9999, 281, 190),
    ObservedSoundingRow(6100, 19080, -538, -9999, 291, 140),
    ObservedSoundingRow(5400, 19857, -572, -9999, 285, 130),
    ObservedSoundingRow(5000, 20347, -548, -9999, 274, 130),
    ObservedSoundingRow(4800, 20608, -556, -9999, 271, 120),
    ObservedSoundingRow(4300, 21317, -507, -9999, 281, 70),
    ObservedSoundingRow(3800, 22116, -541, -9999, 3, 20),
    ObservedSoundingRow(3300, 23033, -485, -9999, 359, 50),
    ObservedSoundingRow(3000, 23659, -493, -9999, 344, 50),
    ObservedSoundingRow(2400, 25122, -493, -9999, 3, 60),
    ObservedSoundingRow(2000, 26309, -524, -9999, 344, 120),
    ObservedSoundingRow(1700, 27360, -524, -9999, 320, 100),
)

LOCKED_NAMELIST_VALUES = {
    "nx": "220",
    "ny": "1",
    "nz": "125",
    "dx": "1000.0",
    "dy": "1000.0",
    "dz": "200.0",
    "dtl": "2.000",
    "timax": "4000.0",
    "tapfrq": "200.0",
    "cm1setup": "1",
    "apmasscon": "0",
    "imoist": "1",
    "ipbl": "0",
    "sgsmodel": "2",
    "tconfig": "2",
    "horizturb": "0",
    "irdamp": "0",
    "hrdamp": "0",
    "psolver": "3",
    "ptype": "6",
    "icor": "0",
    "lspgrad": "0",
    "eqtset": "2",
    "efall": "0",
    "wbc": "1",
    "ebc": "1",
    "sbc": "1",
    "nbc": "1",
    "bbc": "1",
    "tbc": "1",
    "roflux": "0",
    "nudgeobc": "0",
    "isnd": "7",
    "iwnd": "0",
    "itern": "4",
    "iinit": "0",
    "irandp": "0",
    "iorigin": "2",
    "fcor": "0.00000",
    "v_t": "0.0",
    "stretch_x": "0",
    "stretch_y": "0",
    "stretch_z": "0",
    "ztop": "25000.0",
    "isfcflx": "0",
    "sfcmodel": "0",
    "output_format": "2",
    "output_filetype": "2",
    "output_interp": "0",
    "output_rain": "0",
    "output_dbz": "0",
    "output_zs": "1",
    "output_zh": "1",
    "output_th": "1",
    "output_prs": "1",
    "output_qv": "1",
    "output_q": "1",
    "output_u": "1",
    "output_uinterp": "1",
    "output_v": "1",
    "output_vinterp": "1",
    "output_w": "1",
    "output_winterp": "1",
}


class MoistStorageEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_history_times_seconds: list[int]
    expected_history_count: int
    estimated_total_bytes: int
    required_free_bytes: int
    available_free_bytes: int
    passed: bool


class MoistExecutionPreflight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checked_at: datetime
    implementation_commit: str
    checks: dict[str, bool]
    storage: MoistStorageEstimate
    passed: bool


class MoistMountainWaveEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_version: str = EVIDENCE_VERSION
    case_id: str = CASE_ID
    run_id: str
    implementation_commit: str
    generated_at: datetime
    offline_reevaluation: dict[str, Any] | None = None
    source_lock: dict[str, Any]
    provenance: dict[str, Any]
    lifecycle: dict[str, Any]
    output_inventory: dict[str, Any]
    geometry: dict[str, Any]
    initial_and_upstream: dict[str, Any]
    cloud_and_wave: dict[str, Any]
    boundaries_and_top: dict[str, Any]
    runtime_integrity: dict[str, Any]
    predeclared_checks: dict[str, bool]
    caveats: list[str] = Field(default_factory=list)

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2) + "\n"


@dataclass(frozen=True)
class MoistMountainWavePackageResult:
    run_id: str
    package_dir: Path
    manifest_path: Path
    case_manifest_path: Path
    namelist_audit_path: Path
    storage_estimate_path: Path
    implementation_commit: str
    generated_files: tuple[Path, ...]


def source_lock_path() -> Path:
    return Path(__file__).resolve().parents[3] / SOURCE_LOCK_RELATIVE_PATH


def verify_source_lock() -> dict[str, str]:
    path = source_lock_path()
    if not path.is_file():
        raise MoistMountainWaveCaseError(f"Source-lock artifact is missing: {path}")
    actual = sha256_file(path)
    if actual != SOURCE_LOCK_SHA256:
        raise MoistMountainWaveCaseError(
            f"Source-lock SHA-256 changed: expected {SOURCE_LOCK_SHA256}, found {actual}."
        )
    return {"relative_path": SOURCE_LOCK_RELATIVE_PATH.as_posix(), "sha256": actual}


def _temperature_k(row: ObservedSoundingRow) -> float:
    return row.temperature_tenths_c / 10.0 + 273.15


def _potential_temperature_k(row: ObservedSoundingRow) -> float:
    pressure_ratio = 100_000.0 / float(row.pressure_pa)
    return _temperature_k(row) * math.pow(pressure_ratio, 287.04 / 1004.0)


def _saturation_mixing_ratio_kg_kg(temperature_k: Any, pressure_pa: Any) -> np.ndarray[Any, Any]:
    temperature = np.asarray(temperature_k, dtype=np.float64)
    pressure = np.asarray(pressure_pa, dtype=np.float64)
    vapor_pressure = 611.2 * np.exp(17.67 * (temperature - 273.15) / (temperature - 29.65))
    vapor_pressure = np.minimum(vapor_pressure, 0.5 * pressure)
    return 0.622 * vapor_pressure / (pressure - vapor_pressure)


def _mixing_ratio_g_kg(row: ObservedSoundingRow) -> float:
    if row.relative_humidity_tenths_percent < 0:
        return 0.0
    relative_humidity = row.relative_humidity_tenths_percent / 1000.0
    return float(
        1000.0
        * relative_humidity
        * _saturation_mixing_ratio_kg_kg(_temperature_k(row), row.pressure_pa)
    )


def _cross_ridge_wind_m_s(row: ObservedSoundingRow) -> float:
    speed = row.wind_speed_tenths_m_s / 10.0
    return -speed * math.sin(math.radians(row.wind_direction_deg))


def sounding_records() -> list[dict[str, float | int]]:
    base_height = OBSERVED_SOUNDING_ROWS[0].geopotential_height_m
    records: list[dict[str, float | int]] = []
    for row in OBSERVED_SOUNDING_ROWS:
        records.append(
            {
                "pressure_pa": row.pressure_pa,
                "reported_geopotential_height_m": row.geopotential_height_m,
                "model_height_m": row.geopotential_height_m - base_height,
                "temperature_k": _temperature_k(row),
                "theta_k": _potential_temperature_k(row),
                "relative_humidity_percent": (
                    row.relative_humidity_tenths_percent / 10.0
                    if row.relative_humidity_tenths_percent >= 0
                    else -999.9
                ),
                "qv_g_kg": _mixing_ratio_g_kg(row),
                "u_m_s": _cross_ridge_wind_m_s(row),
                "v_m_s": 0.0,
            }
        )
    return records


def render_input_sounding() -> str:
    records = sounding_records()
    surface = records[0]
    lines = [
        f"{surface['pressure_pa'] / 100.0:.4f} {surface['theta_k']:.6f} {surface['qv_g_kg']:.9f}"
    ]
    for record in records[1:]:
        lines.append(
            f"{record['model_height_m']:.1f} {record['theta_k']:.6f} "
            f"{record['qv_g_kg']:.9f} {record['u_m_s']:.6f} {record['v_m_s']:.6f}"
        )
    return "\n".join(lines) + "\n"


def audit_input_sounding(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    records = sounding_records()
    if len(lines) != len(records):
        raise MoistMountainWaveCaseError("Generated sounding row count changed.")
    parsed = [[float(value) for value in line.split()] for line in lines]
    if len(parsed[0]) != 3 or any(len(row) != 5 for row in parsed[1:]):
        raise MoistMountainWaveCaseError("Generated sounding has an invalid CM1 row shape.")
    heights = np.asarray([row[0] for row in parsed[1:]], dtype=np.float64)
    values = np.asarray([value for row in parsed for value in row], dtype=np.float64)
    max_source_rh = max(
        row.relative_humidity_tenths_percent / 10.0
        for row in OBSERVED_SOUNDING_ROWS
        if row.relative_humidity_tenths_percent >= 0
    )
    checks = {
        "all_values_finite": bool(np.all(np.isfinite(values))),
        "strictly_increasing_height": bool(np.all(np.diff(heights) > 0.0)),
        "final_height_above_model_top": bool(heights[-1] > ACTIVE_TOP_M),
        "surface_pressure_is_850_hpa": math.isclose(parsed[0][0], 850.0),
        "maximum_source_rh_is_95_percent": math.isclose(max_source_rh, 95.0),
        "missing_rh_rows_map_to_zero_qv": all(
            math.isclose(_mixing_ratio_g_kg(row), 0.0)
            for row in OBSERVED_SOUNDING_ROWS
            if row.relative_humidity_tenths_percent < 0
        ),
    }
    if not all(checks.values()):
        raise MoistMountainWaveCaseError(f"Generated sounding audit failed: {checks}")
    return {
        "station_id": IGRA_STATION_ID,
        "observation_time": IGRA_OBSERVATION_TIME,
        "source_record_sha256": IGRA_SOURCE_RECORD_SHA256,
        "surface_row_count": 1,
        "profile_row_count": len(parsed) - 1,
        "final_model_height_m": float(heights[-1]),
        "maximum_source_relative_humidity_percent": max_source_rh,
        "checks": checks,
        "rows": records,
    }


def terrain_x_m() -> np.ndarray[Any, Any]:
    return (np.arange(NX, dtype=np.float64) - (NX - 1) / 2.0) * DX_M


def analytic_terrain_m(x_m: Any) -> np.ndarray[Any, Any]:
    x = np.asarray(x_m, dtype=np.float64)
    return TERRAIN_HEIGHT_M / (1.0 + ((x - TERRAIN_CENTER_M) / TERRAIN_HALF_WIDTH_M) ** 2)


def write_terrain_file(path: Path) -> dict[str, Any]:
    terrain = np.broadcast_to(analytic_terrain_m(terrain_x_m())[None, :], (NY, NX))
    encoded = np.asarray(terrain, dtype="<f4")
    path.write_bytes(encoded.tobytes(order="C"))
    decoded = np.fromfile(path, dtype="<f4").reshape((NY, NX), order="C")
    max_error = float(np.max(np.abs(decoded.astype(np.float64) - terrain)))
    crest_index = int(np.argmax(decoded[0]))
    checks = {
        "byte_count_matches_one_direct_access_record": path.stat().st_size == 4 * NX * NY,
        "shape_matches_ny_nx": decoded.shape == (NY, NX),
        "all_values_finite": bool(np.all(np.isfinite(decoded))),
        "crest_is_exact_grid_point": math.isclose(float(decoded[0, crest_index]), 2000.0),
        "crest_x_is_500_m": math.isclose(float(terrain_x_m()[crest_index]), 500.0),
        "float32_roundtrip_within_tolerance": max_error <= 5.0e-4,
    }
    if not all(checks.values()):
        raise MoistMountainWaveCaseError(f"Generated terrain audit failed: {checks}")
    return {
        "formula": "2000 / (1 + ((x - 500) / 10000)^2) m",
        "binary_layout": "one headerless little-endian IEEE-754 float32 direct-access record",
        "array_shape": [NY, NX],
        "storage_order": "x fastest",
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "crest_index": crest_index,
        "crest_x_m": float(terrain_x_m()[crest_index]),
        "crest_height_m": float(decoded[0, crest_index]),
        "maximum_roundtrip_error_m": max_error,
        "maximum_analytic_slope": 9.0
        * TERRAIN_HEIGHT_M
        / (8.0 * math.sqrt(3.0) * TERRAIN_HALF_WIDTH_M),
        "checks": checks,
    }


def render_moist_namelist(official_text: str) -> str:
    official = parse_namelist_assignments(official_text)
    missing = sorted(set(LOCKED_NAMELIST_VALUES) - set(official))
    if missing:
        raise MoistMountainWaveCaseError(f"Pinned namelist lacks locked assignments: {missing}")
    rendered = official_text
    for name, value in LOCKED_NAMELIST_VALUES.items():
        if official[name] != value:
            rendered = replace_namelist_assignment(rendered, name, value)
    audit_moist_namelist(official_text, rendered)
    return rendered


def audit_moist_namelist(official_text: str, generated_text: str) -> dict[str, Any]:
    official = parse_namelist_assignments(official_text)
    generated = parse_namelist_assignments(generated_text)
    if official.keys() != generated.keys():
        raise MoistMountainWaveCaseError("Generated namelist assignment set changed.")
    for name, value in LOCKED_NAMELIST_VALUES.items():
        if generated.get(name) != value:
            raise MoistMountainWaveCaseError(
                f"Locked namelist assignment {name} must be {value}; found {generated.get(name)}."
            )
    differences = []
    for name, original in official.items():
        current = generated[name]
        if original == current:
            continue
        if name not in LOCKED_NAMELIST_VALUES:
            raise MoistMountainWaveCaseError(
                f"Undocumented namelist difference {name}: {original} -> {current}."
            )
        differences.append(
            {
                "name": name,
                "official_dry_value": original,
                "moist_case_value": current,
                "classification": "source_locked_or_explicit_cm1_output_mapping",
            }
        )
    return {
        "official_sha256": sha256_text(official_text),
        "generated_sha256": sha256_text(generated_text),
        "assignment_count": len(generated),
        "changed_assignment_count": len(differences),
        "unchanged_assignment_count": len(generated) - len(differences),
        "locked_values": dict(LOCKED_NAMELIST_VALUES),
        "differences": differences,
        "all_unlisted_assignments_preserved": True,
    }


def expected_output_times(namelist_text: str) -> tuple[int, ...]:
    assignments = parse_namelist_assignments(namelist_text)
    duration = float(assignments["timax"])
    cadence = float(assignments["tapfrq"])
    if not duration.is_integer() or not cadence.is_integer() or duration % cadence:
        raise MoistMountainWaveCaseError("History duration and cadence must divide exactly.")
    return tuple(range(0, int(duration) + 1, int(cadence)))


def estimate_storage(namelist_text: str, target: Path) -> MoistStorageEstimate:
    assignments = parse_namelist_assignments(namelist_text)
    nx = int(float(assignments["nx"]))
    ny = int(float(assignments["ny"]))
    nz = int(float(assignments["nz"]))
    times = expected_output_times(namelist_text)
    scalar_cells = nx * ny * nz
    # Twenty-five full scalar equivalents bound native, interpolated, moisture, and SGS output.
    raw_history = 25 * scalar_cells * 4 * len(times)
    estimated_total = math.ceil(raw_history * 1.5) + 100 * 1024 * 1024
    target.mkdir(parents=True, exist_ok=True)
    available = shutil.disk_usage(target).free
    required = 2 * estimated_total
    return MoistStorageEstimate(
        expected_history_times_seconds=list(times),
        expected_history_count=len(times),
        estimated_total_bytes=estimated_total,
        required_free_bytes=required,
        available_free_bytes=available,
        passed=available >= required,
    )


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")


def _human_namelist_audit(audit: dict[str, Any]) -> str:
    lines = [
        "CM1 r21.1 moist mountain-wave namelist audit",
        f"Official SHA-256: {audit['official_sha256']}",
        f"Generated SHA-256: {audit['generated_sha256']}",
        f"Assignments audited: {audit['assignment_count']}",
        "All unlisted assignments preserved: true",
        "",
        "Locked differences:",
    ]
    lines.extend(
        f"CHANGED {item['name']}: {item['official_dry_value']} -> {item['moist_case_value']}"
        for item in audit["differences"]
    )
    return "\n".join(lines) + "\n"


def generate_moist_mountain_wave_package(
    *, settings: CloudChamberSettings, run_id: str
) -> MoistMountainWavePackageResult:
    """Create the one source-locked package without starting CM1."""
    implementation_commit = verified_clean_git_commit()
    source_lock = verify_source_lock()
    provenance = collect_cm1_provenance(settings)
    active = active_cm1_processes()
    if active:
        raise MoistMountainWaveCaseError(f"CM1/MPI is already active: {active}")
    prior = prior_moist_executions(settings.runtime_home.expanduser(), run_id)
    if prior:
        raise MoistMountainWaveCaseError(f"A prior execution forbids another process: {prior}")

    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    if package_dir.exists():
        raise MoistMountainWaveCaseError(f"Run package already exists: {run_id}")
    package_dir.mkdir(parents=True)
    paths = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "namelist": package_dir / "namelist.input",
        "input_sounding": package_dir / "input_sounding",
        "terrain": package_dir / "perts.dat",
        "runtime_checklist": package_dir / "runtime_file_checklist.json",
        "namelist_audit": package_dir / "source_namelist_diff.json",
        "namelist_audit_text": package_dir / "source_namelist_diff.txt",
        "storage_estimate": package_dir / "storage_estimate.json",
        "package_report": package_dir / "moist_run_report.json",
    }
    try:
        official_text = provenance.mountain_wave_namelist_path.read_text()
        namelist_text = render_moist_namelist(official_text)
        namelist_audit = audit_moist_namelist(official_text, namelist_text)
        paths["namelist"].write_text(namelist_text)
        sounding_text = render_input_sounding()
        paths["input_sounding"].write_text(sounding_text)
        sounding_audit = audit_input_sounding(sounding_text)
        terrain_audit = write_terrain_file(paths["terrain"])
        storage = estimate_storage(namelist_text, package_dir)
        if not storage.passed:
            raise MoistMountainWaveCaseError(
                "Available storage is less than twice the conservative estimate."
            )
        runtime_checklist = {
            "status": "exact_generated_runtime_files_present_in_package",
            "consumed_files": ["input_sounding", "perts.dat"],
            "required_files": [],
            "source_candidates": {},
            "explicitly_not_consumed": [
                "LANDUSE.TBL",
                "radiation_tables",
                "microphysics_lookup_tables",
                "input_grid_x",
                "input_grid_y",
                "input_grid_z",
            ],
        }
        _write_json(paths["runtime_checklist"], runtime_checklist)
        _write_json(paths["namelist_audit"], namelist_audit)
        paths["namelist_audit_text"].write_text(_human_namelist_audit(namelist_audit))
        _write_json(paths["storage_estimate"], storage.model_dump(mode="json"))

        generated_hashes = {
            path.name: sha256_file(path)
            for key, path in paths.items()
            if key not in {"manifest", "case_manifest", "package_report"}
        }
        case_manifest = {
            "case_id": CASE_ID,
            "scenario_id": SCENARIO_ID,
            "authority_state": "issue_407_source_locked_research_case_not_product",
            "run_id": run_id,
            "implementation_commit": implementation_commit,
            "source_lock": source_lock,
            "source_observation": {
                "station_id": IGRA_STATION_ID,
                "observation_time": IGRA_OBSERVATION_TIME,
                "record_sha256": IGRA_SOURCE_RECORD_SHA256,
            },
            "cm1_provenance": provenance.report_record(),
            "namelist_audit": namelist_audit,
            "sounding_audit": sounding_audit,
            "terrain_audit": terrain_audit,
            "runtime_file_checklist": runtime_checklist,
            "storage_estimate": storage.model_dump(mode="json"),
            "generated_input_sha256": generated_hashes,
            "execution_authorization": {
                "duration_seconds": EXPECTED_DURATION_SECONDS,
                "process_count": 1,
                "smoke_process_allowed": False,
                "retry_allowed": False,
                "tuning_process_allowed": False,
            },
            "run_recipe": None,
            "recipe_id": None,
            "cloud_world_id": None,
        }
        _write_json(paths["case_manifest"], case_manifest)

        now = datetime.now(UTC)
        manifest = RunManifest(
            run_id=run_id,
            scenario=ScenarioReference(id=SCENARIO_ID, schema_version=EVIDENCE_VERSION),
            controls={},
            run_configuration={
                "case_id": CASE_ID,
                "source_lock": source_lock,
                "duration_seconds": EXPECTED_DURATION_SECONDS,
                "output_cadence_seconds": EXPECTED_OUTPUT_CADENCE_SECONDS,
                "expected_model_output_count": len(EXPECTED_OUTPUT_TIMES_SECONDS),
                "domain": {
                    "nx": NX,
                    "ny": NY,
                    "nz": NZ,
                    "dx_m": DX_M,
                    "dy_m": DY_M,
                    "dz_m": DZ_M,
                    "active_top_m": ACTIVE_TOP_M,
                },
                "generated_input_sha256": generated_hashes,
                "cm1_provenance": provenance.report_record(),
                "run_recipe": None,
                "recipe_id": None,
                "cloud_world_id": None,
            },
            physical_question=(
                "Can an initially clear, source-backed moist mountain wave form coherent, "
                "terrain-locked, nonprecipitating gravity-wave cloud in CM1 r21.1?"
            ),
            expected_diagnostics=[
                "initial_and_upstream_clear_air",
                "interior_cloud_formation_and_coherence",
                "saturation_ascent_and_descent_evaporation",
                "terrain_and_wave_locking",
                "boundary_top_runtime_and_storage_integrity",
            ],
            generated_inputs=GeneratedInputs(
                run_directory=str(package_dir),
                manifest_path=str(paths["manifest"]),
                namelist_input=str(paths["namelist"]),
                input_sounding=str(paths["input_sounding"]),
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
            user=UserMetadata(name="Toy 1972 Boulder moist mountain-wave feasibility case"),
            run_recipe=None,
            recipe_id=None,
            required_output_fields=list(REQUIRED_OUTPUT_FIELDS),
            input_source="NOAA_IGRA_USM00072476_19720111T1200Z",
            expected_outputs=["native_numbered_cm1_netcdf", "cm1_stats_and_logs"],
            run_limitations=[
                "two_dimensional_research_case_only",
                "source_supported_25_km_top_sensitivity_configuration",
                "not_a_world_recipe_or_product_decision",
            ],
            manual_validation_status="issue_407_native_output_evidence_pending",
        )
        write_run_manifest(paths["manifest"], manifest)
        _write_json(
            paths["package_report"],
            {
                "status": "source_locked_package_complete_not_executed",
                "case_id": CASE_ID,
                "run_id": run_id,
                "implementation_commit": implementation_commit,
                "source_lock": source_lock,
                "generated_input_sha256": generated_hashes,
                "run_recipe": None,
                "recipe_id": None,
                "cloud_world_id": None,
            },
        )
    except Exception:
        shutil.rmtree(package_dir, ignore_errors=True)
        raise

    return MoistMountainWavePackageResult(
        run_id=run_id,
        package_dir=package_dir,
        manifest_path=paths["manifest"],
        case_manifest_path=paths["case_manifest"],
        namelist_audit_path=paths["namelist_audit"],
        storage_estimate_path=paths["storage_estimate"],
        implementation_commit=implementation_commit,
        generated_files=tuple(paths.values()),
    )


def load_moist_mountain_wave_package(
    *, settings: CloudChamberSettings, run_id: str
) -> MoistMountainWavePackageResult:
    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    names = {
        "manifest": "run_manifest.json",
        "case_manifest": "case_manifest.json",
        "namelist": "namelist.input",
        "input_sounding": "input_sounding",
        "terrain": "perts.dat",
        "runtime_checklist": "runtime_file_checklist.json",
        "namelist_audit": "source_namelist_diff.json",
        "namelist_audit_text": "source_namelist_diff.txt",
        "storage_estimate": "storage_estimate.json",
        "package_report": "moist_run_report.json",
    }
    paths = {key: package_dir / name for key, name in names.items()}
    missing = sorted(path.name for path in paths.values() if not path.is_file())
    if missing:
        raise MoistMountainWaveCaseError(f"Existing package is incomplete: {missing}")
    manifest = load_run_manifest(paths["manifest"])
    case_manifest = json.loads(paths["case_manifest"].read_text())
    implementation_commit = case_manifest.get("implementation_commit")
    if (
        manifest.run_id != run_id
        or manifest.scenario.id != SCENARIO_ID
        or manifest.lifecycle_state != LifecycleState.PACKAGED
        or not isinstance(implementation_commit, str)
        or manifest.app.commit != implementation_commit
    ):
        raise MoistMountainWaveCaseError("Existing package identity or lifecycle is invalid.")
    return MoistMountainWavePackageResult(
        run_id=run_id,
        package_dir=package_dir,
        manifest_path=paths["manifest"],
        case_manifest_path=paths["case_manifest"],
        namelist_audit_path=paths["namelist_audit"],
        storage_estimate_path=paths["storage_estimate"],
        implementation_commit=implementation_commit,
        generated_files=tuple(paths.values()),
    )


def prior_moist_executions(runtime_home: Path, current_run_id: str) -> list[str]:
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


def preflight_package_for_execution(
    *, settings: CloudChamberSettings, package: MoistMountainWavePackageResult
) -> MoistExecutionPreflight:
    implementation_commit = verified_clean_git_commit()
    if implementation_commit != package.implementation_commit:
        raise MoistMountainWaveCaseError("Package and clean implementation commits differ.")
    source_lock = verify_source_lock()
    provenance = collect_cm1_provenance(settings)
    manifest = load_run_manifest(package.manifest_path)
    case_manifest = json.loads(package.case_manifest_path.read_text())
    if manifest.app.commit != implementation_commit:
        raise MoistMountainWaveCaseError("Run manifest implementation commit changed.")
    if case_manifest.get("source_lock") != source_lock:
        raise MoistMountainWaveCaseError("Package source-lock identity changed.")

    namelist_path = package.package_dir / "namelist.input"
    sounding_path = package.package_dir / "input_sounding"
    terrain_path = package.package_dir / "perts.dat"
    official_text = provenance.mountain_wave_namelist_path.read_text()
    audit = audit_moist_namelist(official_text, namelist_path.read_text())
    stored_audit = json.loads(package.namelist_audit_path.read_text())
    if audit["generated_sha256"] != stored_audit.get("generated_sha256"):
        raise MoistMountainWaveCaseError("Generated namelist changed after packaging.")
    sounding_audit = audit_input_sounding(sounding_path.read_text())
    terrain_audit = _audit_existing_terrain(terrain_path)
    expected_hashes = case_manifest.get("generated_input_sha256", {})
    actual_hashes = {
        path.name: sha256_file(path)
        for path in package.generated_files
        if path.name in expected_hashes
    }
    if actual_hashes != expected_hashes:
        raise MoistMountainWaveCaseError("Generated input hash identity changed.")

    checklist = json.loads((package.package_dir / "runtime_file_checklist.json").read_text())
    consumed = checklist.get("consumed_files")
    if consumed != ["input_sounding", "perts.dat"] or checklist.get("required_files") != []:
        raise MoistMountainWaveCaseError("Consumed runtime-file checklist is not exact.")
    active = active_cm1_processes()
    if active:
        raise MoistMountainWaveCaseError(f"Another CM1/MPI process is active: {active}")
    prior = prior_moist_executions(settings.runtime_home.expanduser(), package.run_id)
    if prior:
        raise MoistMountainWaveCaseError(f"A prior execution forbids this process: {prior}")
    outputs = sorted(
        path.name
        for pattern in _OUTPUT_LIKE_PATTERNS
        for path in package.package_dir.glob(pattern)
        if path.name != "perts.dat"
    )
    if outputs:
        raise MoistMountainWaveCaseError(f"Package already contains output-like files: {outputs}")

    stored_storage = MoistStorageEstimate.model_validate(
        json.loads(package.storage_estimate_path.read_text())
    )
    available = shutil.disk_usage(package.package_dir).free
    storage = stored_storage.model_copy(
        update={
            "available_free_bytes": available,
            "passed": available >= stored_storage.required_free_bytes,
        }
    )
    checks = {
        "clean_worktree_and_commit_match": True,
        "source_lock_hash_matches": True,
        "pinned_cm1_provenance_matches": True,
        "netcdf_support_linked": bool(provenance.netcdf_link_evidence),
        "complete_namelist_audit_matches": True,
        "sounding_audit_matches": all(sounding_audit["checks"].values()),
        "terrain_hash_and_readback_match": all(terrain_audit["checks"].values()),
        "consumed_runtime_files_exact": True,
        "expected_histories_exact": expected_output_times(namelist_path.read_text())
        == EXPECTED_OUTPUT_TIMES_SECONDS,
        "storage_has_double_estimate": storage.passed,
        "no_active_cm1_or_mpi": True,
        "no_prior_execution": True,
        "target_has_no_output": True,
    }
    preflight = MoistExecutionPreflight(
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


def _audit_existing_terrain(path: Path) -> dict[str, Any]:
    if path.stat().st_size != 4 * NX * NY:
        raise MoistMountainWaveCaseError("Existing terrain byte count changed.")
    decoded = np.fromfile(path, dtype="<f4").reshape((NY, NX), order="C")
    expected = np.broadcast_to(analytic_terrain_m(terrain_x_m())[None, :], (NY, NX))
    max_error = float(np.max(np.abs(decoded.astype(np.float64) - expected)))
    crest_index = int(np.argmax(decoded[0]))
    checks = {
        "byte_count_matches_one_direct_access_record": path.stat().st_size == 4 * NX * NY,
        "shape_matches_ny_nx": decoded.shape == (NY, NX),
        "all_values_finite": bool(np.all(np.isfinite(decoded))),
        "crest_is_exact_grid_point": math.isclose(float(decoded[0, crest_index]), 2000.0),
        "crest_x_is_500_m": math.isclose(float(terrain_x_m()[crest_index]), 500.0),
        "float32_roundtrip_within_tolerance": max_error <= 5.0e-4,
    }
    return {"sha256": sha256_file(path), "maximum_roundtrip_error_m": max_error, "checks": checks}


def load_preserved_moist_mountain_wave_run(
    *, settings: CloudChamberSettings, run_id: str
) -> MoistMountainWavePackageResult:
    """Load only the exact completed run authorized for offline reevaluation."""
    if run_id != PRESERVED_RUN_ID:
        raise MoistMountainWaveCaseError(
            f"Offline reevaluation is pinned to {PRESERVED_RUN_ID}; found {run_id}."
        )
    package_dir = settings.runtime_home.expanduser() / "runs" / run_id
    required = {
        "manifest": package_dir / "run_manifest.json",
        "case_manifest": package_dir / "case_manifest.json",
        "namelist_audit": package_dir / "source_namelist_diff.json",
        "storage_estimate": package_dir / "storage_estimate.json",
    }
    missing = sorted(path.name for path in required.values() if not path.is_file())
    if missing:
        raise MoistMountainWaveCaseError(f"Preserved run is incomplete: {missing}")

    manifest = load_run_manifest(required["manifest"])
    case_manifest = json.loads(required["case_manifest"].read_text())
    implementation_commit = case_manifest.get("implementation_commit")
    if (
        manifest.run_id != PRESERVED_RUN_ID
        or manifest.scenario.id != SCENARIO_ID
        or manifest.lifecycle_state != LifecycleState.COMPLETED
        or manifest.execution.exit_code != 0
        or not isinstance(implementation_commit, str)
        or manifest.app.commit != implementation_commit
    ):
        raise MoistMountainWaveCaseError(
            "Preserved run identity, lifecycle, or implementation commit changed."
        )
    return MoistMountainWavePackageResult(
        run_id=run_id,
        package_dir=package_dir,
        manifest_path=required["manifest"],
        case_manifest_path=required["case_manifest"],
        namelist_audit_path=required["namelist_audit"],
        storage_estimate_path=required["storage_estimate"],
        implementation_commit=implementation_commit,
        generated_files=tuple(required.values()),
    )


def verify_preserved_run_artifacts(
    package: MoistMountainWavePackageResult,
) -> dict[str, Any]:
    """Fail closed unless every source, input, log, stat, and history hash is pinned."""
    if package.run_id != PRESERVED_RUN_ID:
        raise MoistMountainWaveCaseError("Preserved artifact verification received another run.")
    source_lock = verify_source_lock()
    actual: dict[str, str] = {}
    for relative_path, expected_sha256 in PRESERVED_RUN_ARTIFACT_SHA256.items():
        path = package.package_dir / relative_path
        if not path.is_file():
            raise MoistMountainWaveCaseError(f"Preserved run artifact is missing: {relative_path}.")
        actual_sha256 = sha256_file(path)
        if actual_sha256 != expected_sha256:
            raise MoistMountainWaveCaseError(
                f"Preserved run artifact changed: {relative_path}; expected "
                f"{expected_sha256}, found {actual_sha256}."
            )
        actual[relative_path] = actual_sha256

    manifest = load_run_manifest(package.manifest_path)
    expected_history_names = [f"cm1out_{index:06d}.nc" for index in range(1, 22)]
    manifest_history_paths = [Path(path).resolve() for path in manifest.outputs.netcdf_paths]
    expected_history_paths = [
        (package.package_dir / name).resolve() for name in expected_history_names
    ]
    if manifest_history_paths != expected_history_paths:
        raise MoistMountainWaveCaseError(
            "Preserved manifest no longer names the exact 21 pinned histories in order."
        )
    expected_stdout = (package.package_dir / "logs/stdout.log").resolve()
    expected_stderr = (package.package_dir / "logs/stderr.log").resolve()
    if Path(manifest.execution.stdout_log or "").resolve() != expected_stdout:
        raise MoistMountainWaveCaseError("Preserved stdout path identity changed.")
    if Path(manifest.execution.stderr_log or "").resolve() != expected_stderr:
        raise MoistMountainWaveCaseError("Preserved stderr path identity changed.")

    case_manifest = json.loads(package.case_manifest_path.read_text())
    if case_manifest.get("source_lock") != source_lock:
        raise MoistMountainWaveCaseError("Preserved case-manifest source lock changed.")
    if case_manifest.get("implementation_commit") != package.implementation_commit:
        raise MoistMountainWaveCaseError("Preserved implementation commit identity changed.")
    return {
        "run_id": package.run_id,
        "source_lock": source_lock,
        "artifact_sha256": actual,
        "artifact_count": len(actual),
    }


def reevaluate_preserved_moist_mountain_wave_run(
    *,
    settings: CloudChamberSettings,
    package: MoistMountainWavePackageResult,
    evaluator_commit: str,
) -> MoistMountainWaveEvidence:
    """Reevaluate the pinned output without constructing or invoking a run manager."""
    before = verify_preserved_run_artifacts(package)
    evidence = evaluate_moist_mountain_wave_run(settings=settings, package=package)
    after = verify_preserved_run_artifacts(package)
    if before != after:
        raise MoistMountainWaveCaseError(
            "Preserved run hashes changed during offline reevaluation."
        )
    return evidence.model_copy(
        update={
            "offline_reevaluation": {
                "mode": "fail_closed_preserved_native_output_only",
                "run_id": package.run_id,
                "original_implementation_commit": package.implementation_commit,
                "evaluator_commit": evaluator_commit,
                "run_manager_constructed_or_invoked": False,
                "artifact_hashes_verified_before": before,
                "artifact_hashes_verified_after": after,
                "artifacts_unchanged": True,
            }
        }
    )


def evaluate_moist_mountain_wave_run(
    *, settings: CloudChamberSettings, package: MoistMountainWavePackageResult
) -> MoistMountainWaveEvidence:
    """Evaluate the completed process directly from native numbered NetCDF."""
    manifest = load_run_manifest(package.manifest_path)
    if manifest.lifecycle_state != LifecycleState.COMPLETED or manifest.execution.exit_code != 0:
        raise MoistMountainWaveCaseError("Evaluation requires one zero-exit completed process.")
    if manifest.app.commit != package.implementation_commit:
        raise MoistMountainWaveCaseError("Completed process commit identity changed.")
    provenance = collect_cm1_provenance(settings)
    candidates = [Path(path) for path in manifest.outputs.netcdf_paths]
    if not candidates:
        candidates = list(package.package_dir.glob("cm1out_*.nc*"))
    model_paths = accepted_model_output_paths(candidates)
    if len(model_paths) != len(EXPECTED_OUTPUT_TIMES_SECONDS):
        raise MoistMountainWaveCaseError(
            f"Expected {len(EXPECTED_OUTPUT_TIMES_SECONDS)} native histories; "
            f"found {len(model_paths)}."
        )

    frames: list[dict[str, Any]] = []
    finite_by_field: dict[str, list[dict[str, Any]]] = {
        field: [] for field in REQUIRED_OUTPUT_FIELDS
    }
    actual_times: list[float] = []
    first_terrain: np.ndarray[Any, Any] | None = None
    first_coords: dict[str, np.ndarray[Any, Any]] | None = None
    first_ql_max = math.inf
    maximum_terrain_error = 0.0
    minimum_vertical_spacing = math.inf
    maximum_height_transform_error = 0.0
    top_values: list[float] = []
    active_top_by_time: list[dict[str, Any]] = []
    tangency_by_time: list[dict[str, Any]] = []
    upstream_flow_by_time: list[dict[str, Any]] = []
    initial_upstream_state: dict[str, Any] | None = None
    inventory: dict[str, Any] | None = None

    for path in model_paths:
        with xr.open_dataset(path, decode_times=False) as dataset:
            _require_fields(dataset)
            time_seconds = _dataset_time_seconds(dataset)
            actual_times.append(time_seconds)
            coords = _coordinates(dataset)
            terrain = _field(dataset, "zs", ("yh", "xh"))
            zh_physical = _field(dataset, "zhval", ("zh", "yh", "xh"))
            active_top = _active_top_evidence(dataset, coords, time_seconds=time_seconds)
            active_top_by_time.append(active_top)
            if first_coords is None:
                first_coords = coords
                first_terrain = terrain
                inventory = _inventory(dataset)
            else:
                for name, values in first_coords.items():
                    if not np.array_equal(values, coords[name]):
                        raise MoistMountainWaveCaseError(f"Coordinate {name} changed by time.")
            assert first_terrain is not None

            expected_terrain = np.broadcast_to(
                analytic_terrain_m(coords["xh"])[None, :], terrain.shape
            )
            maximum_terrain_error = max(
                maximum_terrain_error,
                float(np.max(np.abs(terrain - expected_terrain))),
                float(np.max(np.abs(terrain - first_terrain))),
            )
            minimum_vertical_spacing = min(
                minimum_vertical_spacing, float(np.min(np.diff(zh_physical, axis=0)))
            )
            expected_zh = reconstruct_physical_heights(
                terrain,
                coords["zh"],
                active_top_m=ACTIVE_TOP_M,
            )
            maximum_height_transform_error = max(
                maximum_height_transform_error,
                float(np.max(np.abs(zh_physical - expected_zh))),
            )
            top_values.append(float(active_top["final_nominal_zf_m"]))

            fields = {name: np.asarray(dataset[name].values) for name in REQUIRED_OUTPUT_FIELDS}
            for name, values in fields.items():
                finite = np.isfinite(values)
                finite_by_field[name].append(
                    {
                        "time_seconds": time_seconds,
                        "total_count": int(values.size),
                        "finite_count": int(np.count_nonzero(finite)),
                        "non_finite_count": int(values.size - np.count_nonzero(finite)),
                        "minimum": float(np.nanmin(values)),
                        "maximum": float(np.nanmax(values)),
                    }
                )

            ql = _field(dataset, "ql", ("zh", "yh", "xh"))[:, 0, :]
            qv = _field(dataset, "qv", ("zh", "yh", "xh"))[:, 0, :]
            theta = _field(dataset, "th", ("zh", "yh", "xh"))[:, 0, :]
            pressure = _field(dataset, "prs", ("zh", "yh", "xh"))[:, 0, :]
            u = _field(dataset, "u", ("zh", "yh", "xf"))
            v = _field(dataset, "v", ("zh", "yf", "xh"))
            w_full = _field(dataset, "w", ("zf", "yh", "xh"))[:, 0, :]
            u_scalar = 0.5 * (u[:, 0, :-1] + u[:, 0, 1:])
            v_scalar = 0.5 * (v[:, :-1, :] + v[:, 1:, :])[:, 0, :]
            w_scalar = 0.5 * (w_full[:-1] + w_full[1:])
            temperature = theta * (pressure / 100_000.0) ** (287.04 / 1004.0)
            qsat = _saturation_mixing_ratio_kg_kg(temperature, pressure)
            relative_humidity = np.divide(qv, qsat, out=np.zeros_like(qv), where=qsat > 0.0)
            height = zh_physical[:, 0, :]
            tangency = lower_boundary_tangency_metrics(
                x_m=coords["xh"],
                y_m=coords["yh"],
                zs_m=terrain,
                u_bottom=u[0, :, :],
                v_bottom=v[0, :, :],
                w_bottom=w_full[0, :][None, :],
            )
            tangency["time_seconds"] = time_seconds
            tangency_by_time.append(tangency)
            upstream_flow_by_time.append(
                _upstream_flow_evidence(
                    time_seconds=time_seconds,
                    x_m=coords["xh"],
                    height_m=height,
                    u=u_scalar,
                    v=v_scalar,
                    w=w_scalar,
                )
            )
            if initial_upstream_state is None:
                initial_upstream_state = _initial_upstream_state_evidence(
                    x_m=coords["xh"],
                    height_m=height,
                    theta=theta,
                    pressure=pressure,
                    qv=qv,
                    u=u_scalar,
                    v=v_scalar,
                    w=w_scalar,
                )
            frame = _cloud_frame_evidence(
                time_seconds=time_seconds,
                x_m=coords["xh"],
                height_m=height,
                ql=ql,
                relative_humidity=relative_humidity,
                w=w_scalar,
            )
            frames.append(frame)
            if math.isinf(first_ql_max):
                first_ql_max = float(np.max(ql))

    if actual_times != [float(value) for value in EXPECTED_OUTPUT_TIMES_SECONDS]:
        raise MoistMountainWaveCaseError(f"Native history times changed: {actual_times}")
    non_finite = sum(
        item["non_finite_count"] for records in finite_by_field.values() for item in records
    )
    if non_finite:
        raise MoistMountainWaveCaseError(f"Required fields contain {non_finite} non-finite values.")
    assert first_coords is not None
    assert first_terrain is not None
    assert inventory is not None
    assert initial_upstream_state is not None

    coherent_flags = [frame["largest_component_cells"] >= MIN_COHERENT_CELLS for frame in frames]
    persistent_windows = [
        [frames[index + offset]["time_seconds"] for offset in range(MIN_PERSISTENT_FRAMES)]
        for index in range(len(frames) - MIN_PERSISTENT_FRAMES + 1)
        if all(coherent_flags[index : index + MIN_PERSISTENT_FRAMES])
    ]
    first_cloud = next((frame for frame in frames if frame["cloud_cell_count"] > 0), None)
    peak_frame = max(frames, key=lambda frame: float(frame["maximum_ql_kg_kg"]))
    upstream_maximum = max(float(frame["upstream_maximum_ql_kg_kg"]) for frame in frames)
    edge_maximum = max(float(frame["edge_maximum_ql_kg_kg"]) for frame in frames)
    descent_evaporation_frames = [
        frame["time_seconds"]
        for frame in frames
        if frame["downstream_descent_evaporation"]["selected_cell_count"] > 0
        and frame["downstream_descent_evaporation"]["largest_component_cells"] > 0
    ]
    runtime_integrity = _runtime_integrity(package, manifest, model_paths)
    checks = {
        "normal_completion_and_exact_finite_histories": runtime_integrity[
            "normal_termination_marker_present"
        ]
        and non_finite == 0,
        "terrain_and_physical_height_integrity": maximum_terrain_error <= 1.0e-3
        and maximum_height_transform_error <= 0.02
        and minimum_vertical_spacing > 0.0
        and all(math.isclose(value, ACTIVE_TOP_M, abs_tol=0.01) for value in top_values),
        "initial_condensate_at_numerical_floor": first_ql_max <= NUMERICAL_CLEAR_FLOOR_KG_KG,
        "upstream_clear_at_interpretable_floor": upstream_maximum < CLOUD_FLOOR_KG_KG,
        "first_cloud_forms_interior_not_edge": first_cloud is not None
        and first_cloud["interior_cloud_cell_count"] > 0
        and first_cloud["edge_cloud_cell_count"] == 0
        and first_cloud["peak_location_is_interior"],
        "coherent_cloud_persists_three_histories": bool(persistent_windows),
        "material_peak_reached": float(peak_frame["maximum_ql_kg_kg"]) >= MATERIAL_PEAK_KG_KG,
        "cloud_colocated_with_ascent_and_saturation": first_cloud is not None
        and first_cloud["interior_cloud_in_ascent_and_saturation_cells"] > 0
        and first_cloud["peak_location_w_m_s"] > 0.0
        and first_cloud["peak_location_relative_humidity"] >= 0.99,
        "descent_and_evaporation_evidence_present": bool(descent_evaporation_frames),
        "edge_cloud_does_not_compromise_interpretation": edge_maximum < CLOUD_FLOOR_KG_KG,
        "active_top_sources_agree_all_histories": all(
            bool(item["all_active_top_sources_agree"]) for item in active_top_by_time
        ),
        "lower_boundary_tangency_metrics_retained": len(tangency_by_time)
        == len(EXPECTED_OUTPUT_TIMES_SECONDS),
        "initial_upstream_wind_and_stability_retained": bool(
            initial_upstream_state["profile_by_level"]
        ),
    }
    return MoistMountainWaveEvidence(
        run_id=package.run_id,
        implementation_commit=package.implementation_commit,
        generated_at=datetime.now(UTC),
        source_lock=verify_source_lock(),
        provenance=provenance.report_record(),
        lifecycle={
            "state": manifest.lifecycle_state.value,
            "exit_code": manifest.execution.exit_code,
            "started_at": manifest.execution.started_at,
            "finished_at": manifest.execution.finished_at,
            "exactly_one_process_authorized": True,
        },
        output_inventory={
            "model_output_files": [
                {"filename": path.name, "bytes": path.stat().st_size} for path in model_paths
            ],
            "actual_times_seconds": actual_times,
            "expected_times_seconds": list(EXPECTED_OUTPUT_TIMES_SECONDS),
            "total_model_netcdf_bytes": sum(path.stat().st_size for path in model_paths),
            "variable_inventory": inventory["variables"],
            "coordinate_inventory": inventory["coordinates"],
            "required_field_finite_counts_by_time": finite_by_field,
        },
        geometry={
            "terrain_formula": "2000 / (1 + ((x - 500) / 10000)^2) m",
            "terrain_maximum_abs_error_m": maximum_terrain_error,
            "terrain_maximum_m": float(np.max(first_terrain)),
            "terrain_crest_x_m": float(first_coords["xh"][int(np.argmax(first_terrain[0]))]),
            "physical_height_transform_maximum_abs_error_m": maximum_height_transform_error,
            "minimum_scalar_vertical_spacing_m": minimum_vertical_spacing,
            "active_top_values_m": top_values,
            "active_top_checks_by_time": active_top_by_time,
            "lower_boundary_tangency": {
                "physical_condition": "w = u * dzs/dx + v * dzs/dy",
                "per_time_metrics": tangency_by_time,
                "maximum_abs_residual_m_s": max(
                    max(
                        abs(float(item["residual_min_m_s"])),
                        abs(float(item["residual_max_m_s"])),
                    )
                    for item in tangency_by_time
                ),
            },
        },
        initial_and_upstream={
            "initial_maximum_ql_kg_kg": first_ql_max,
            "upstream_maximum_ql_kg_kg_all_times": upstream_maximum,
            "upstream_x_bounds_m": list(UPSTREAM_X_BOUNDS_M),
            "evaluation_top_m": EVALUATION_TOP_M,
            "initial_upstream_state": initial_upstream_state,
            "upstream_flow_by_time": upstream_flow_by_time,
        },
        cloud_and_wave={
            "cloud_floor_kg_kg": CLOUD_FLOOR_KG_KG,
            "material_peak_kg_kg": MATERIAL_PEAK_KG_KG,
            "minimum_coherent_cells": MIN_COHERENT_CELLS,
            "minimum_persistent_frames": MIN_PERSISTENT_FRAMES,
            "first_cloud_frame": first_cloud,
            "peak_cloud_frame": peak_frame,
            "persistent_windows_seconds": persistent_windows,
            "descent_evaporation_frames_seconds": descent_evaporation_frames,
            "downstream_descent_evaporation_by_time": [
                frame["downstream_descent_evaporation"] for frame in frames
            ],
            "frames": frames,
        },
        boundaries_and_top={
            "edge_width_m": EDGE_WIDTH_M,
            "edge_maximum_ql_kg_kg_all_times": edge_maximum,
            "top_abs_w_maximum_m_s_all_times": max(
                float(frame["top_abs_w_maximum_m_s"]) for frame in frames
            ),
            "top_ql_maximum_kg_kg_all_times": max(
                float(frame["top_ql_maximum_kg_kg"]) for frame in frames
            ),
        },
        runtime_integrity=runtime_integrity,
        predeclared_checks=checks,
        caveats=[
            "two_dimensional_case_not_a_three_dimensional_cloud_volume",
            "25_km_top_is_source_supported_but_has_no_absorbing_layer",
            "cm1_smagorinsky_closure_is_not_pointwise_identical_to_source_model",
            "runtime_visual_review_and_scientific_judgment_remain_manual",
        ],
    )


def _active_top_evidence(
    dataset: xr.Dataset,
    coords: dict[str, np.ndarray[Any, Any]],
    *,
    time_seconds: float,
) -> dict[str, Any]:
    if "ztop" not in dataset:
        raise MoistMountainWaveCaseError("Native output is missing runtime ztop.")
    runtime_values = normalize_length_to_m(
        dataset["ztop"].values,
        str(dataset["ztop"].attrs.get("units", "")),
    ).reshape(-1)
    if runtime_values.size != 1:
        raise MoistMountainWaveCaseError("Runtime ztop must be scalar-valued.")
    final_nominal_zf_m = float(coords["zf"][-1])
    runtime_ztop_m = float(runtime_values[0])
    configured_top_m = NZ * DZ_M
    agrees = all(
        math.isclose(value, final_nominal_zf_m, rel_tol=0.0, abs_tol=0.01)
        for value in (runtime_ztop_m, configured_top_m, ACTIVE_TOP_M)
    )
    if not agrees:
        raise MoistMountainWaveCaseError(
            "Active-top evidence disagrees among final nominal zf, runtime ztop, "
            "configured nz*dz, and the source lock."
        )
    return {
        "time_seconds": time_seconds,
        "final_nominal_zf_m": final_nominal_zf_m,
        "runtime_ztop_m": runtime_ztop_m,
        "configured_nz": NZ,
        "configured_dz_m": DZ_M,
        "configured_nz_times_dz_m": configured_top_m,
        "source_locked_active_top_m": ACTIVE_TOP_M,
        "all_active_top_sources_agree": agrees,
    }


def _upstream_flow_evidence(
    *,
    time_seconds: float,
    x_m: np.ndarray[Any, Any],
    height_m: np.ndarray[Any, Any],
    u: np.ndarray[Any, Any],
    v: np.ndarray[Any, Any],
    w: np.ndarray[Any, Any],
) -> dict[str, Any]:
    upstream_x = (x_m >= UPSTREAM_X_BOUNDS_M[0]) & (x_m <= UPSTREAM_X_BOUNDS_M[1])
    mask = upstream_x[None, :] & (height_m < EVALUATION_TOP_M)
    return {
        "time_seconds": time_seconds,
        "x_bounds_m": list(UPSTREAM_X_BOUNDS_M),
        "height_maximum_m": EVALUATION_TOP_M,
        "selected_cell_count": int(np.count_nonzero(mask)),
        "u_m_s": _numeric_summary(u[mask]),
        "v_m_s": _numeric_summary(v[mask]),
        "w_m_s": _numeric_summary(w[mask]),
    }


def _initial_upstream_state_evidence(
    *,
    x_m: np.ndarray[Any, Any],
    height_m: np.ndarray[Any, Any],
    theta: np.ndarray[Any, Any],
    pressure: np.ndarray[Any, Any],
    qv: np.ndarray[Any, Any],
    u: np.ndarray[Any, Any],
    v: np.ndarray[Any, Any],
    w: np.ndarray[Any, Any],
) -> dict[str, Any]:
    upstream_x = (x_m >= UPSTREAM_X_BOUNDS_M[0]) & (x_m <= UPSTREAM_X_BOUNDS_M[1])
    profile: list[dict[str, Any]] = []
    for level_index in range(height_m.shape[0]):
        selected_x = upstream_x & (height_m[level_index] < EVALUATION_TOP_M)
        if not np.any(selected_x):
            continue
        profile.append(
            {
                "level_index": level_index,
                "sample_count": int(np.count_nonzero(selected_x)),
                "mean_height_m": float(np.mean(height_m[level_index, selected_x])),
                "mean_theta_k": float(np.mean(theta[level_index, selected_x])),
                "mean_pressure_pa": float(np.mean(pressure[level_index, selected_x])),
                "mean_qv_kg_kg": float(np.mean(qv[level_index, selected_x])),
                "mean_u_m_s": float(np.mean(u[level_index, selected_x])),
                "mean_v_m_s": float(np.mean(v[level_index, selected_x])),
                "mean_w_m_s": float(np.mean(w[level_index, selected_x])),
            }
        )
    if len(profile) < 2:
        raise MoistMountainWaveCaseError(
            "Initial upstream profile does not contain enough levels for stability evidence."
        )
    heights = np.asarray([item["mean_height_m"] for item in profile], dtype=np.float64)
    theta_values = np.asarray([item["mean_theta_k"] for item in profile], dtype=np.float64)
    delta_height = np.diff(heights)
    if np.any(delta_height <= 0.0):
        raise MoistMountainWaveCaseError("Initial upstream physical heights are not monotonic.")
    theta_mid = 0.5 * (theta_values[:-1] + theta_values[1:])
    n_squared = 9.81 / theta_mid * np.diff(theta_values) / delta_height
    return {
        "method": (
            "native t=0 scalar-grid means in the locked -100 to -60 km upstream sector "
            "below 12 km; N^2=(g/theta_mid)*(delta theta/delta physical height)"
        ),
        "x_bounds_m": list(UPSTREAM_X_BOUNDS_M),
        "height_maximum_m": EVALUATION_TOP_M,
        "profile_by_level": profile,
        "wind_summary": {
            "u_m_s": _numeric_summary(u[:, upstream_x][height_m[:, upstream_x] < EVALUATION_TOP_M]),
            "v_m_s": _numeric_summary(v[:, upstream_x][height_m[:, upstream_x] < EVALUATION_TOP_M]),
            "w_m_s": _numeric_summary(w[:, upstream_x][height_m[:, upstream_x] < EVALUATION_TOP_M]),
        },
        "stability": {
            "sample_count": int(n_squared.size),
            "n_squared_s_2": _numeric_summary(n_squared),
            "negative_n_squared_count": int(np.count_nonzero(n_squared < 0.0)),
            "positive_n_squared_count": int(np.count_nonzero(n_squared > 0.0)),
        },
    }


def _cloud_frame_evidence(
    *,
    time_seconds: float,
    x_m: np.ndarray[Any, Any],
    height_m: np.ndarray[Any, Any],
    ql: np.ndarray[Any, Any],
    relative_humidity: np.ndarray[Any, Any],
    w: np.ndarray[Any, Any],
) -> dict[str, Any]:
    below = height_m < EVALUATION_TOP_M
    cloud = (ql >= CLOUD_FLOOR_KG_KG) & below
    components = _connected_components(cloud)
    largest = max(components, key=len, default=[])
    component_evidence = sorted(
        (
            _component_evidence(
                component,
                x_m=x_m,
                height_m=height_m,
                ql=ql,
                w=w,
                relative_humidity=relative_humidity,
            )
            for component in components
        ),
        key=lambda item: int(item["cell_count"]),
        reverse=True,
    )
    interior_x = (x_m >= INTERIOR_X_BOUNDS_M[0]) & (x_m <= INTERIOR_X_BOUNDS_M[1])
    upstream_x = (x_m >= UPSTREAM_X_BOUNDS_M[0]) & (x_m <= UPSTREAM_X_BOUNDS_M[1])
    edge_x = (x_m <= x_m.min() + EDGE_WIDTH_M) | (x_m >= x_m.max() - EDGE_WIDTH_M)
    interior = below & interior_x[None, :]
    upstream = below & upstream_x[None, :]
    edge = below & edge_x[None, :]
    near_cloud = _dilate_mask(cloud)
    descending_clear = near_cloud & below & (w < 0.0) & (relative_humidity < 1.0) & ~cloud
    east_adjacent = np.zeros_like(cloud)
    east_adjacent[:, 1:] = cloud[:, :-1]
    downstream_descending_clear = (
        east_adjacent & below & (w < 0.0) & (relative_humidity < 1.0) & (ql < CLOUD_FLOOR_KG_KG)
    )
    downstream_evidence = _downstream_descent_evidence(
        time_seconds=time_seconds,
        mask=downstream_descending_clear,
        x_m=x_m,
        height_m=height_m,
        w=w,
        relative_humidity=relative_humidity,
        ql=ql,
    )
    cloud_ascent_saturated = cloud & (w > 0.0) & (relative_humidity >= 0.99)
    peak_index = np.unravel_index(int(np.argmax(ql)), ql.shape)
    component_centroid_x: float | None = None
    component_centroid_z: float | None = None
    if largest:
        component_centroid_x = float(np.mean([x_m[index[1]] for index in largest]))
        component_centroid_z = float(np.mean([height_m[index] for index in largest]))
    top_mask = height_m >= ACTIVE_TOP_M - 2_000.0
    return {
        "time_seconds": time_seconds,
        "maximum_ql_kg_kg": float(np.max(ql)),
        "mean_positive_ql_kg_kg": float(np.mean(ql[ql > 0.0])) if np.any(ql > 0.0) else 0.0,
        "cloud_cell_count": int(np.count_nonzero(cloud)),
        "component_count": len(components),
        "largest_component_cells": len(largest),
        "largest_component_centroid_x_m": component_centroid_x,
        "largest_component_centroid_height_m": component_centroid_z,
        "cloud_components": component_evidence,
        "interior_cloud_cell_count": int(np.count_nonzero(cloud & interior)),
        "upstream_cloud_cell_count": int(np.count_nonzero(cloud & upstream)),
        "edge_cloud_cell_count": int(np.count_nonzero(cloud & edge)),
        "upstream_maximum_ql_kg_kg": _masked_maximum(ql, upstream),
        "edge_maximum_ql_kg_kg": _masked_maximum(ql, edge),
        "cloud_in_ascent_and_saturation_cells": int(np.count_nonzero(cloud_ascent_saturated)),
        "interior_cloud_in_ascent_and_saturation_cells": int(
            np.count_nonzero(cloud_ascent_saturated & interior)
        ),
        "descending_clear_near_cloud_cells": int(np.count_nonzero(descending_clear)),
        "downstream_descent_evaporation": downstream_evidence,
        "cloud_weighted_mean_w_m_s": _weighted_mean(w, ql, cloud),
        "cloud_weighted_mean_relative_humidity": _weighted_mean(relative_humidity, ql, cloud),
        "peak_location_x_m": float(x_m[peak_index[1]]),
        "peak_location_height_m": float(height_m[peak_index]),
        "peak_location_w_m_s": float(w[peak_index]),
        "peak_location_relative_humidity": float(relative_humidity[peak_index]),
        "peak_location_is_interior": bool(interior[peak_index]),
        "top_abs_w_maximum_m_s": _masked_maximum(np.abs(w), top_mask),
        "top_ql_maximum_kg_kg": _masked_maximum(ql, top_mask),
    }


def _component_evidence(
    component: list[tuple[int, int]],
    *,
    x_m: np.ndarray[Any, Any],
    height_m: np.ndarray[Any, Any],
    ql: np.ndarray[Any, Any],
    w: np.ndarray[Any, Any],
    relative_humidity: np.ndarray[Any, Any],
) -> dict[str, Any]:
    mask = np.zeros(ql.shape, dtype=bool)
    for index in component:
        mask[index] = True
    z_indices, x_indices = np.nonzero(mask)
    x_values = x_m[x_indices]
    height_values = height_m[z_indices, x_indices]
    return {
        "cell_count": len(component),
        "centroid_x_m": float(np.mean(x_values)),
        "centroid_height_m": float(np.mean(height_values)),
        "x_bounds_m": [float(np.min(x_values)), float(np.max(x_values))],
        "height_bounds_m": [float(np.min(height_values)), float(np.max(height_values))],
        "maximum_ql_kg_kg": float(np.max(ql[mask])),
        "ql_weighted_mean_w_m_s": _weighted_mean(w, ql, mask),
        "ql_weighted_mean_relative_humidity": _weighted_mean(relative_humidity, ql, mask),
    }


def _downstream_descent_evidence(
    *,
    time_seconds: float,
    mask: np.ndarray[Any, Any],
    x_m: np.ndarray[Any, Any],
    height_m: np.ndarray[Any, Any],
    w: np.ndarray[Any, Any],
    relative_humidity: np.ndarray[Any, Any],
    ql: np.ndarray[Any, Any],
) -> dict[str, Any]:
    components = _connected_components(mask)
    largest = max(components, key=len, default=[])
    selected_z, selected_x = np.nonzero(mask)
    selected_count = int(selected_z.size)
    bounds: dict[str, list[float] | None]
    if selected_count:
        selected_heights = height_m[selected_z, selected_x]
        bounds = {
            "x_bounds_m": [float(np.min(x_m[selected_x])), float(np.max(x_m[selected_x]))],
            "height_bounds_m": [
                float(np.min(selected_heights)),
                float(np.max(selected_heights)),
            ],
        }
    else:
        bounds = {"x_bounds_m": None, "height_bounds_m": None}

    largest_bounds: dict[str, list[float] | None]
    if largest:
        largest_z = np.asarray([index[0] for index in largest], dtype=np.int64)
        largest_x = np.asarray([index[1] for index in largest], dtype=np.int64)
        largest_heights = height_m[largest_z, largest_x]
        largest_bounds = {
            "x_bounds_m": [float(np.min(x_m[largest_x])), float(np.max(x_m[largest_x]))],
            "height_bounds_m": [
                float(np.min(largest_heights)),
                float(np.max(largest_heights)),
            ],
        }
    else:
        largest_bounds = {"x_bounds_m": None, "height_bounds_m": None}

    return {
        "time_seconds": time_seconds,
        "method": (
            "clear scalar cells one x-grid cell immediately east of a cloud cell, with "
            "w<0, RH<1, and ql below the locked interpretable cloud floor"
        ),
        "direction": "downstream_east_positive_x",
        "selected_cell_count": selected_count,
        "component_count": len(components),
        "largest_component_cells": len(largest),
        **bounds,
        "largest_component_bounds": largest_bounds,
        "w_m_s": _numeric_summary(w[mask]),
        "relative_humidity_fraction": _numeric_summary(relative_humidity[mask]),
        "ql_kg_kg": _numeric_summary(ql[mask]),
    }


def _numeric_summary(values: Any) -> dict[str, float | int | None]:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return {
            "sample_count": 0,
            "minimum": None,
            "median": None,
            "mean": None,
            "maximum": None,
        }
    return {
        "sample_count": int(finite.size),
        "minimum": float(np.min(finite)),
        "median": float(np.median(finite)),
        "mean": float(np.mean(finite)),
        "maximum": float(np.max(finite)),
    }


def _connected_components(mask: np.ndarray[Any, Any]) -> list[list[tuple[int, int]]]:
    visited = np.zeros(mask.shape, dtype=bool)
    components: list[list[tuple[int, int]]] = []
    for z_index, x_index in zip(*np.nonzero(mask), strict=True):
        start = (int(z_index), int(x_index))
        if visited[start]:
            continue
        stack = [start]
        visited[start] = True
        component: list[tuple[int, int]] = []
        while stack:
            current = stack.pop()
            component.append(current)
            z_now, x_now = current
            for candidate in (
                (z_now - 1, x_now),
                (z_now + 1, x_now),
                (z_now, x_now - 1),
                (z_now, x_now + 1),
            ):
                z_next, x_next = candidate
                if (
                    0 <= z_next < mask.shape[0]
                    and 0 <= x_next < mask.shape[1]
                    and mask[candidate]
                    and not visited[candidate]
                ):
                    visited[candidate] = True
                    stack.append(candidate)
        components.append(component)
    return components


def _dilate_mask(mask: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    dilated = mask.copy()
    dilated[1:, :] |= mask[:-1, :]
    dilated[:-1, :] |= mask[1:, :]
    dilated[:, 1:] |= mask[:, :-1]
    dilated[:, :-1] |= mask[:, 1:]
    return dilated


def _masked_maximum(values: np.ndarray[Any, Any], mask: np.ndarray[Any, Any]) -> float:
    selected = values[mask]
    return float(np.max(selected)) if selected.size else 0.0


def _weighted_mean(
    values: np.ndarray[Any, Any], weights: np.ndarray[Any, Any], mask: np.ndarray[Any, Any]
) -> float | None:
    selected_weights = weights[mask]
    if selected_weights.size == 0 or float(np.sum(selected_weights)) <= 0.0:
        return None
    return float(np.average(values[mask], weights=selected_weights))


def _require_fields(dataset: xr.Dataset) -> None:
    available = set(dataset.data_vars) | set(dataset.coords)
    missing = sorted(
        (set(REQUIRED_OUTPUT_FIELDS) | set(REQUIRED_COORDINATES) | {"ztop"}) - available
    )
    if missing:
        raise MoistMountainWaveCaseError(f"Native output is missing required data: {missing}")


def _field(dataset: xr.Dataset, name: str, dimensions: tuple[str, ...]) -> np.ndarray[Any, Any]:
    data = dataset[name]
    if "time" in data.dims:
        if data.sizes["time"] != 1:
            raise MoistMountainWaveCaseError(f"{name} must contain one time per native file.")
        data = data.isel(time=0)
    if set(data.dims) != set(dimensions):
        raise MoistMountainWaveCaseError(
            f"{name} dimensions must be {dimensions}; found {data.dims}."
        )
    return np.asarray(data.transpose(*dimensions).values, dtype=np.float64)


def _dataset_time_seconds(dataset: xr.Dataset) -> float:
    values = normalize_time_to_seconds(
        dataset["time"].values, str(dataset["time"].attrs.get("units", ""))
    ).reshape(-1)
    if values.size != 1:
        raise MoistMountainWaveCaseError("Each native history must contain exactly one time.")
    return float(values[0])


def _coordinates(dataset: xr.Dataset) -> dict[str, np.ndarray[Any, Any]]:
    result: dict[str, np.ndarray[Any, Any]] = {}
    for name in ("xh", "xf", "yh", "yf", "zh", "zf"):
        result[name] = normalize_length_to_m(
            dataset[name].values, str(dataset[name].attrs.get("units", ""))
        ).reshape(-1)
    return result


def _inventory(dataset: xr.Dataset) -> dict[str, Any]:
    variables = {
        name: {
            "dimensions": list(data.dims),
            "shape": list(data.shape),
            "units": str(data.attrs.get("units", "")),
            "dtype": str(data.dtype),
        }
        for name, data in dataset.data_vars.items()
    }
    coordinates = {
        name: {
            "dimensions": list(data.dims),
            "shape": list(data.shape),
            "units": str(data.attrs.get("units", "")),
            "dtype": str(data.dtype),
        }
        for name, data in dataset.coords.items()
    }
    return {"variables": variables, "coordinates": coordinates}


def _runtime_integrity(
    package: MoistMountainWavePackageResult,
    manifest: RunManifest,
    model_paths: list[Path],
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
    wall_clock_seconds: float | None = None
    if manifest.execution.started_at is not None and manifest.execution.finished_at is not None:
        wall_clock_seconds = (
            manifest.execution.finished_at - manifest.execution.started_at
        ).total_seconds()
    stats_paths = sorted(package.package_dir.glob("cm1out_stats*.nc*"))
    stats_inventory: dict[str, Any] = {"status": "not_found", "files": []}
    if stats_paths:
        stats_inventory = {"status": "inspected", "files": []}
        for path in stats_paths:
            with xr.open_dataset(path, decode_times=False) as dataset:
                stats_inventory["files"].append(
                    {
                        "filename": path.name,
                        "bytes": path.stat().st_size,
                        "variables": sorted(str(name) for name in dataset.data_vars),
                        "finite": all(
                            bool(np.all(np.isfinite(np.asarray(value.values))))
                            for value in dataset.data_vars.values()
                        ),
                    }
                )
    return {
        "exit_code": manifest.execution.exit_code,
        "normal_termination_marker_present": "Program terminated normally" in stdout,
        "stdout_bytes": stdout_path.stat().st_size if stdout_path.is_file() else 0,
        "stderr_bytes": stderr_path.stat().st_size if stderr_path.is_file() else 0,
        "floating_point_flags": flags,
        "stderr_excerpt": stderr[-4000:],
        "wall_clock_seconds": wall_clock_seconds,
        "stats_evidence": stats_inventory,
        "package_total_bytes": sum(
            path.stat().st_size for path in package.package_dir.rglob("*") if path.is_file()
        ),
        "model_output_bytes": sum(path.stat().st_size for path in model_paths),
    }


def write_moist_mountain_wave_evidence(path: Path, evidence: MoistMountainWaveEvidence) -> None:
    path.write_text(evidence.to_json_text())
