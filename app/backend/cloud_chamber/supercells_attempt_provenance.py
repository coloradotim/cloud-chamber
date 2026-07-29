"""Strict provenance binding for retained Supercells variation attempts."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from cloud_chamber.generated_input_identity import (
    GeneratedInputIdentityError,
    verify_generated_input_identity,
)
from cloud_chamber.run_manifest import RunManifest
from cloud_chamber.supercell_benchmark import (
    CM1_EXECUTABLE_SHA256,
    CM1_SOURCE_MANIFEST_SHA256,
)
from cloud_chamber.supercells_source_customization import (
    PINNED_INIT3D_F_SHA256,
    SUPERCELLS_SOURCE_CUSTOMIZATION_KIND,
    SUPERCELLS_SOURCE_CUSTOMIZATION_TARGET,
    load_supercells_source_customization,
)
from cloud_chamber.variation_envelope import (
    VariationEnvelope,
    canonical_payload_sha256,
)


class SupercellsAttemptProvenanceError(ValueError):
    """Raised when a retained attempt is not bound to approved CM1 provenance."""


def validate_supercells_attempt_provenance(
    manifest: RunManifest,
) -> dict[str, Any]:
    """Verify package inputs, isolated build, and the executable actually launched."""
    try:
        verify_generated_input_identity(manifest)
    except (GeneratedInputIdentityError, OSError) as exc:
        raise SupercellsAttemptProvenanceError(
            "Generated inputs no longer match the retained package identity."
        ) from exc

    provenance = manifest.run_configuration.get("cm1_provenance")
    if not isinstance(provenance, Mapping):
        raise SupercellsAttemptProvenanceError("Pinned CM1 provenance is unavailable.")
    if provenance.get("source_manifest_sha256") != CM1_SOURCE_MANIFEST_SHA256:
        raise SupercellsAttemptProvenanceError(
            "CM1 source identity does not match the approved source manifest."
        )
    if provenance.get("executable_sha256") != CM1_EXECUTABLE_SHA256:
        raise SupercellsAttemptProvenanceError(
            "The package was not based on the approved canonical CM1 executable."
        )

    try:
        envelope = VariationEnvelope.model_validate(
            manifest.run_configuration.get("variation_envelope")
        )
    except ValueError as exc:
        raise SupercellsAttemptProvenanceError(
            "Retained attempt lacks its reviewed Supercells envelope."
        ) from exc
    if (
        manifest.run_configuration.get("cm1_source_customization_kind")
        != SUPERCELLS_SOURCE_CUSTOMIZATION_KIND
    ):
        raise SupercellsAttemptProvenanceError(
            "Retained attempt lacks the declared Supercells customization kind."
        )

    run_dir = Path(manifest.generated_inputs.run_directory).expanduser().resolve()
    customization_value = manifest.generated_inputs.cm1_source_customization
    if not customization_value:
        raise SupercellsAttemptProvenanceError(
            "Retained attempt lacks its packaged source customization."
        )
    customization_path = Path(customization_value).expanduser().resolve()
    _require_contained(customization_path, run_dir, "Packaged source customization")
    try:
        customization = load_supercells_source_customization(customization_path)
    except (OSError, ValueError) as exc:
        raise SupercellsAttemptProvenanceError(
            "Packaged Supercells source customization is invalid."
        ) from exc
    if customization.get("original_source_sha256") != PINNED_INIT3D_F_SHA256:
        raise SupercellsAttemptProvenanceError(
            "Packaged customization does not start from the approved init3d.F."
        )
    if customization.get("wind_profile_sha256") != canonical_payload_sha256(
        envelope.world_payload.get("hodograph")
    ):
        raise SupercellsAttemptProvenanceError(
            "Packaged wind profile does not match the reviewed envelope."
        )
    if customization.get("thermodynamic_profile_sha256") != canonical_payload_sha256(
        envelope.world_payload.get("sounding")
    ):
        raise SupercellsAttemptProvenanceError(
            "Packaged thermodynamic profile does not match the reviewed envelope."
        )
    if customization.get("initiation") != {
        key: float(value)
        for key, value in dict(envelope.world_payload.get("initiation") or {}).items()
        if key
        in {
            "amplitude_k",
            "horizontal_radius_m",
            "vertical_radius_m",
            "center_height_m_agl",
            "center_x_m",
            "center_y_m",
        }
    }:
        raise SupercellsAttemptProvenanceError(
            "Packaged thermal initiation does not match the reviewed envelope."
        )

    status = manifest.cm1_source_customization_status
    if not isinstance(status, Mapping):
        raise SupercellsAttemptProvenanceError(
            "Retained attempt lacks applied isolated-build status."
        )
    required_status = {
        "schema_version": "cm1_source_customization_status_v1",
        "customization_kind": SUPERCELLS_SOURCE_CUSTOMIZATION_KIND,
        "run_id": manifest.run_id,
        "original_target_sha256": customization["original_source_sha256"],
        "patched_target_sha256": customization["patched_source_sha256"],
        "patched_files": [str(SUPERCELLS_SOURCE_CUSTOMIZATION_TARGET)],
        "source_restored_after_build": "not_modified_isolated_build_tree",
        "build_command": ["make"],
        "wind_profile_sha256": customization["wind_profile_sha256"],
        "thermodynamic_profile_sha256": customization["thermodynamic_profile_sha256"],
        "no_silent_profile_or_thermal_fallback": True,
    }
    mismatches = {
        key: (status.get(key), expected)
        for key, expected in required_status.items()
        if status.get(key) != expected
    }
    if mismatches:
        raise SupercellsAttemptProvenanceError(
            f"Applied Supercells customization disagrees with the package: {mismatches}."
        )
    if status.get("initiation") != customization["initiation"]:
        raise SupercellsAttemptProvenanceError(
            "Applied thermal readback does not match the packaged initiation."
        )

    status_customization = _required_status_path(status, "customization_manifest")
    if status_customization != customization_path:
        raise SupercellsAttemptProvenanceError(
            "Applied build status references a different customization artifact."
        )
    build_root = _required_status_path(status, "build_root")
    runtime_builds = (
        Path(manifest.runtime_paths.runtime_home).expanduser().resolve() / "cm1_source_builds"
    )
    _require_contained(build_root, runtime_builds, "Isolated CM1 build")
    if not build_root.is_dir():
        raise SupercellsAttemptProvenanceError("Applied isolated CM1 build tree is unavailable.")
    built_target = build_root / SUPERCELLS_SOURCE_CUSTOMIZATION_TARGET
    if (
        not built_target.is_file()
        or _sha256_file(built_target) != customization["patched_source_sha256"]
    ):
        raise SupercellsAttemptProvenanceError(
            "Applied isolated CM1 build source no longer matches the reviewed customization."
        )

    executable_path = _required_status_path(status, "custom_executable")
    _require_contained(executable_path, run_dir, "Custom CM1 executable")
    if not executable_path.is_file():
        raise SupercellsAttemptProvenanceError("Applied custom CM1 executable is unavailable.")
    executable_sha256 = status.get("custom_executable_sha256")
    if not isinstance(executable_sha256, str) or _sha256_file(executable_path) != executable_sha256:
        raise SupercellsAttemptProvenanceError(
            "Applied custom executable hash does not match the retained executable."
        )
    if _execution_path(manifest) != executable_path:
        raise SupercellsAttemptProvenanceError(
            "Retained CM1 execution did not use the applied custom executable."
        )
    if manifest.execution.executable_sha256 != executable_sha256:
        raise SupercellsAttemptProvenanceError(
            "Launch-time executable hash does not match the applied custom executable."
        )

    return {
        "approved_source_manifest_sha256": CM1_SOURCE_MANIFEST_SHA256,
        "base_executable_sha256": CM1_EXECUTABLE_SHA256,
        "executable_kind": "isolated_supercells_customization",
        "executable_sha256": executable_sha256,
        "customization_kind": SUPERCELLS_SOURCE_CUSTOMIZATION_KIND,
        "original_target_sha256": customization["original_source_sha256"],
        "patched_target_sha256": customization["patched_source_sha256"],
        "source_build_isolated": True,
    }


def _required_status_path(status: Mapping[str, object], key: str) -> Path:
    value = status.get(key)
    if not isinstance(value, str) or not value:
        raise SupercellsAttemptProvenanceError(f"Applied source-customization status lacks {key}.")
    return Path(value).expanduser().resolve()


def _execution_path(manifest: RunManifest) -> Path:
    if not manifest.execution.command or not manifest.execution.command[0]:
        raise SupercellsAttemptProvenanceError("Retained CM1 execution command is unavailable.")
    return Path(manifest.execution.command[0]).expanduser().resolve()


def _require_contained(path: Path, root: Path, label: str) -> None:
    if not path.is_relative_to(root):
        raise SupercellsAttemptProvenanceError(f"{label} escapes its accepted attempt storage.")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "SupercellsAttemptProvenanceError",
    "validate_supercells_attempt_provenance",
]
