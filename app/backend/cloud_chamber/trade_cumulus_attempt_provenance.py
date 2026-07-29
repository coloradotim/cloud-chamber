"""Strict provenance binding for retained Trade Cumulus variation attempts."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from cloud_chamber.bomex_case import (
    CM1_EXECUTABLE_SHA256,
    CM1_SOURCE_MANIFEST_SHA256,
    CRITICAL_SOURCE_HASHES,
)
from cloud_chamber.run_manifest import RunManifest
from cloud_chamber.trade_cumulus_forcing import (
    TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND,
    TRADE_CUMULUS_FORCING_TARGET,
    load_forcing_customization,
)
from cloud_chamber.trade_cumulus_recipes import (
    TradeCumulusControls,
    default_controls,
    normalize_controls,
)
from cloud_chamber.variation_envelope import VariationEnvelope


class TradeCumulusAttemptProvenanceError(ValueError):
    """Raised when a retained attempt is not bound to approved CM1 provenance."""


def validate_trade_cumulus_attempt_provenance(
    manifest: RunManifest,
) -> dict[str, Any]:
    """Bind the reviewed package to approved source and the executable actually used."""
    provenance = manifest.run_configuration.get("cm1_provenance")
    if not isinstance(provenance, Mapping):
        raise TradeCumulusAttemptProvenanceError("Pinned CM1 provenance is unavailable.")
    if provenance.get("source_manifest_sha256") != CM1_SOURCE_MANIFEST_SHA256:
        raise TradeCumulusAttemptProvenanceError(
            "CM1 source identity does not match the approved source manifest."
        )
    if provenance.get("executable_sha256") != CM1_EXECUTABLE_SHA256:
        raise TradeCumulusAttemptProvenanceError(
            "CM1 executable identity does not match the approved canonical executable."
        )

    controls = _retained_controls(manifest)
    forcing_required = _forcing_changed(controls)
    declared_kind = manifest.run_configuration.get("cm1_source_customization_kind")
    customization_path_value = manifest.generated_inputs.cm1_source_customization
    status = manifest.cm1_source_customization_status

    if not forcing_required:
        if declared_kind is not None or customization_path_value is not None or status is not None:
            raise TradeCumulusAttemptProvenanceError(
                "Canonical forcing attempt carries contradictory source-customization evidence."
            )
        return {
            "approved_source_manifest_sha256": CM1_SOURCE_MANIFEST_SHA256,
            "executable_kind": "approved_canonical",
            "executable_sha256": CM1_EXECUTABLE_SHA256,
            "forcing_customization_required": False,
        }

    if declared_kind != TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND:
        raise TradeCumulusAttemptProvenanceError(
            "Forcing-modified attempt lacks the declared Trade Cumulus customization kind."
        )
    if not customization_path_value:
        raise TradeCumulusAttemptProvenanceError(
            "Forcing-modified attempt lacks its packaged source customization."
        )
    run_dir = Path(manifest.generated_inputs.run_directory).expanduser().resolve()
    customization_path = Path(customization_path_value).expanduser().resolve()
    _require_contained(customization_path, run_dir, "Packaged source customization")
    try:
        customization = load_forcing_customization(customization_path)
    except (OSError, ValueError) as exc:
        raise TradeCumulusAttemptProvenanceError(
            "Packaged Trade Cumulus forcing customization is invalid."
        ) from exc
    if (
        customization.get("original_source_sha256")
        != CRITICAL_SOURCE_HASHES[str(TRADE_CUMULUS_FORCING_TARGET)]
    ):
        raise TradeCumulusAttemptProvenanceError(
            "Packaged forcing customization does not start from the approved base.F."
        )
    expected_forcing = {
        "vertical_motion_m_s": controls.large_scale_vertical_motion_m_s,
        "temperature_tendency_k_day": controls.temperature_tendency_k_day,
        "total_water_tendency_g_kg_day": controls.total_water_tendency_g_kg_day,
    }
    _require_numeric_mapping(
        customization.get("forcing"),
        expected_forcing,
        "Packaged forcing targets",
    )

    if not isinstance(status, Mapping):
        raise TradeCumulusAttemptProvenanceError(
            "Forcing-modified attempt lacks applied-build status."
        )
    required_status = {
        "schema_version": "cm1_source_customization_status_v1",
        "customization_kind": TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND,
        "run_id": manifest.run_id,
        "original_target_sha256": customization["original_source_sha256"],
        "patched_target_sha256": customization["patched_source_sha256"],
        "source_restored_after_build": "not_modified_isolated_build_tree",
    }
    mismatches = {
        key: (status.get(key), expected)
        for key, expected in required_status.items()
        if status.get(key) != expected
    }
    if mismatches:
        raise TradeCumulusAttemptProvenanceError(
            f"Applied forcing customization disagrees with the package: {mismatches}."
        )
    if status.get("patched_files") != [str(TRADE_CUMULUS_FORCING_TARGET)]:
        raise TradeCumulusAttemptProvenanceError(
            "Applied forcing customization has an unexpected patched-file inventory."
        )
    if status.get("build_command") != ["make"]:
        raise TradeCumulusAttemptProvenanceError(
            "Applied forcing customization lacks the isolated CM1 build record."
        )
    if status.get("no_silent_forcing_fallback") is not True:
        raise TradeCumulusAttemptProvenanceError(
            "Applied forcing customization permits an unreviewed fallback."
        )
    _require_numeric_mapping(status.get("forcing"), expected_forcing, "Applied forcing readback")

    status_customization = _required_status_path(status, "customization_manifest")
    if status_customization != customization_path:
        raise TradeCumulusAttemptProvenanceError(
            "Applied build status references a different forcing customization."
        )
    build_root = _required_status_path(status, "build_root")
    runtime_builds = (
        Path(manifest.runtime_paths.runtime_home).expanduser().resolve() / "cm1_source_builds"
    )
    _require_contained(build_root, runtime_builds, "Isolated CM1 build")
    if not build_root.is_dir():
        raise TradeCumulusAttemptProvenanceError(
            "Applied forcing customization build tree is unavailable."
        )

    executable_path = _required_status_path(status, "custom_executable")
    _require_contained(executable_path, run_dir, "Custom CM1 executable")
    if not executable_path.is_file():
        raise TradeCumulusAttemptProvenanceError("Applied custom CM1 executable is unavailable.")
    executable_sha256 = status.get("custom_executable_sha256")
    if not isinstance(executable_sha256, str) or _sha256_file(executable_path) != executable_sha256:
        raise TradeCumulusAttemptProvenanceError(
            "Applied custom CM1 executable hash does not match the retained executable."
        )
    if (
        not manifest.execution.command
        or Path(manifest.execution.command[0]).expanduser().resolve() != executable_path
    ):
        raise TradeCumulusAttemptProvenanceError(
            "Retained CM1 execution did not use the applied custom executable."
        )

    return {
        "approved_source_manifest_sha256": CM1_SOURCE_MANIFEST_SHA256,
        "executable_kind": "isolated_forcing_customization",
        "executable_sha256": executable_sha256,
        "forcing_customization_required": True,
        "customization_kind": TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND,
        "original_target_sha256": customization["original_source_sha256"],
        "patched_target_sha256": customization["patched_source_sha256"],
        "forcing_readback": expected_forcing,
    }


def _retained_controls(manifest: RunManifest) -> TradeCumulusControls:
    try:
        envelope = VariationEnvelope.model_validate(
            manifest.run_configuration.get("variation_envelope")
        )
        return normalize_controls(
            TradeCumulusControls.model_validate(envelope.world_payload.get("controls"))
        )
    except ValueError as exc:
        raise TradeCumulusAttemptProvenanceError(
            "Retained attempt lacks valid absolute Trade Cumulus controls."
        ) from exc


def _forcing_changed(controls: TradeCumulusControls) -> bool:
    reference = default_controls()
    return any(
        not math.isclose(
            getattr(controls, field),
            getattr(reference, field),
            rel_tol=0.0,
            abs_tol=1.0e-12,
        )
        for field in (
            "large_scale_vertical_motion_m_s",
            "temperature_tendency_k_day",
            "total_water_tendency_g_kg_day",
        )
    )


def _require_numeric_mapping(
    value: object,
    expected: dict[str, float],
    label: str,
) -> None:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise TradeCumulusAttemptProvenanceError(f"{label} is missing or incomplete.")
    if any(
        not isinstance(value[key], int | float)
        or not math.isclose(
            float(value[key]),
            target,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        )
        for key, target in expected.items()
    ):
        raise TradeCumulusAttemptProvenanceError(
            f"{label} does not match the reviewed forcing targets."
        )


def _required_status_path(status: Mapping[str, object], key: str) -> Path:
    value = status.get(key)
    if not isinstance(value, str) or not value:
        raise TradeCumulusAttemptProvenanceError(
            f"Applied source-customization status lacks {key}."
        )
    return Path(value).expanduser().resolve()


def _require_contained(path: Path, root: Path, label: str) -> None:
    if not path.is_relative_to(root):
        raise TradeCumulusAttemptProvenanceError(f"{label} escapes its accepted attempt storage.")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
