"""Source-locked deterministic thermal customization for Supercells variations."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SUPERCELLS_SOURCE_CUSTOMIZATION_KIND = "supercells_environment_and_thermal_v1"
SUPERCELLS_SOURCE_CUSTOMIZATION_SCHEMA_VERSION = "supercells_source_customization_v1"
SUPERCELLS_SOURCE_CUSTOMIZATION_FILENAME = "cm1_source_customization.json"
SUPERCELLS_SOURCE_CUSTOMIZATION_MARKER = "CLOUD_CHAMBER_SUPERCELLS_THERMAL_V1"
SUPERCELLS_SOURCE_CUSTOMIZATION_TARGET = Path("src/init3d.F")
PINNED_INIT3D_F_SHA256 = "9c45c0982ba194ea6ea74afd6a2516445cdd011fc90902091d089f4cb92dfd28"

_THERMAL_ANCHOR = """        ric     =  centerx  ! center of bubble in x-direction (m)
        rjc     =  centery  ! center of bubble in y-direction (m)
        zc      =   1400.0  ! height of center of bubble above ground (m)
        bhrad   =  10000.0  ! horizontal radius of bubble (m)
        bvrad   =   1400.0  ! vertical radius of bubble (m)
        bptpert =      1.0  ! max potential temp perturbation (K)
"""


class SupercellsSourceCustomizationError(RuntimeError):
    """Raised when the pinned Supercells source transform cannot be reproduced."""


def render_supercells_source(
    source: str,
    initiation: Mapping[str, float],
) -> str:
    if SUPERCELLS_SOURCE_CUSTOMIZATION_MARKER in source:
        raise SupercellsSourceCustomizationError(
            "CM1 init3d.F already contains the Supercells thermal customization."
        )
    if source.count(_THERMAL_ANCHOR) != 1:
        raise SupercellsSourceCustomizationError(
            "Unable to locate the pinned CM1 iinit=1 thermal block in init3d.F."
        )
    required = {
        "amplitude_k",
        "horizontal_radius_m",
        "vertical_radius_m",
        "center_height_m_agl",
        "center_x_m",
        "center_y_m",
    }
    if set(initiation) < required:
        missing = sorted(required - set(initiation))
        raise SupercellsSourceCustomizationError(
            f"Supercells thermal customization is missing values: {missing}."
        )
    replacement = f"""        ric     =  centerx + {initiation["center_x_m"]:.6f}
        rjc     =  centery + {initiation["center_y_m"]:.6f}
        zc      =  {initiation["center_height_m_agl"]:.6f}
        bhrad   =  {initiation["horizontal_radius_m"]:.6f}
        bvrad   =  {initiation["vertical_radius_m"]:.6f}
        bptpert =  {initiation["amplitude_k"]:.6f}
        ! {SUPERCELLS_SOURCE_CUSTOMIZATION_MARKER}
"""
    return source.replace(_THERMAL_ANCHOR, replacement, 1)


def supercells_source_customization_artifact(
    source: str,
    *,
    initiation: Mapping[str, float],
    wind_profile: list[dict[str, float]],
    thermodynamic_profile: list[dict[str, float]],
) -> dict[str, object]:
    source_sha256 = _sha256_text(source)
    if source_sha256 != PINNED_INIT3D_F_SHA256:
        raise SupercellsSourceCustomizationError(
            "Configured CM1 init3d.F does not match the accepted r21.1 source lock: "
            f"{source_sha256} != {PINNED_INIT3D_F_SHA256}."
        )
    normalized_initiation = {
        key: float(value)
        for key, value in initiation.items()
        if key
        in {
            "amplitude_k",
            "horizontal_radius_m",
            "vertical_radius_m",
            "center_height_m_agl",
            "center_x_m",
            "center_y_m",
        }
    }
    patched = render_supercells_source(source, normalized_initiation)
    return {
        "schema_version": SUPERCELLS_SOURCE_CUSTOMIZATION_SCHEMA_VERSION,
        "customization_kind": SUPERCELLS_SOURCE_CUSTOMIZATION_KIND,
        "target_relative_path": str(SUPERCELLS_SOURCE_CUSTOMIZATION_TARGET),
        "marker": SUPERCELLS_SOURCE_CUSTOMIZATION_MARKER,
        "original_source_sha256": source_sha256,
        "patched_source_sha256": _sha256_text(patched),
        "initiation": normalized_initiation,
        "wind_profile_sha256": _canonical_sha256(wind_profile),
        "thermodynamic_profile_sha256": _canonical_sha256(thermodynamic_profile),
        "input_contract": {
            "thermodynamics": "external_input_sounding",
            "wind": "external_input_sounding",
            "initiation": "source_locked_single_thermal",
            "no_silent_stock_profile_fallback": True,
            "no_silent_stock_thermal_fallback": True,
        },
        "source_policy": {
            "isolated_external_build": True,
            "original_cm1_tree_modified": False,
            "cm1_source_committed_to_repo": False,
        },
    }


def load_supercells_source_customization(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SupercellsSourceCustomizationError(
            f"Unable to read Supercells source customization: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise SupercellsSourceCustomizationError(
            "Supercells source customization must be a JSON object."
        )
    if (
        payload.get("schema_version") != SUPERCELLS_SOURCE_CUSTOMIZATION_SCHEMA_VERSION
        or payload.get("customization_kind") != SUPERCELLS_SOURCE_CUSTOMIZATION_KIND
        or payload.get("target_relative_path") != str(SUPERCELLS_SOURCE_CUSTOMIZATION_TARGET)
        or payload.get("marker") != SUPERCELLS_SOURCE_CUSTOMIZATION_MARKER
    ):
        raise SupercellsSourceCustomizationError(
            "Supercells source customization identity is invalid."
        )
    initiation = payload.get("initiation")
    if not isinstance(initiation, dict):
        raise SupercellsSourceCustomizationError(
            "Supercells source customization is missing its initiation payload."
        )
    return payload


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "PINNED_INIT3D_F_SHA256",
    "SUPERCELLS_SOURCE_CUSTOMIZATION_KIND",
    "SUPERCELLS_SOURCE_CUSTOMIZATION_FILENAME",
    "SUPERCELLS_SOURCE_CUSTOMIZATION_MARKER",
    "SUPERCELLS_SOURCE_CUSTOMIZATION_SCHEMA_VERSION",
    "SUPERCELLS_SOURCE_CUSTOMIZATION_TARGET",
    "SupercellsSourceCustomizationError",
    "load_supercells_source_customization",
    "render_supercells_source",
    "supercells_source_customization_artifact",
]
