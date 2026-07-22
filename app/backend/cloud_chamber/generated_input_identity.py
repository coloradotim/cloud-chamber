"""Generated-input identity checks shared by packaging, launch, and promotion."""

from __future__ import annotations

import hashlib
from pathlib import Path

from cloud_chamber.run_manifest import RunManifest


class GeneratedInputIdentityError(RuntimeError):
    """Raised when retained generated inputs no longer match their manifest identity."""


def verify_generated_input_identity(manifest: RunManifest) -> dict[str, str]:
    """Rehash every generated input declared by a package, failing closed on drift."""
    recorded = manifest.run_configuration.get("generated_input_sha256")
    if recorded is None:
        return {}
    if not isinstance(recorded, dict) or not recorded:
        raise GeneratedInputIdentityError("Generated-input hashes are empty or malformed.")

    run_dir = Path(manifest.generated_inputs.run_directory).expanduser().resolve()
    verified: dict[str, str] = {}
    for raw_name, raw_expected in sorted(recorded.items(), key=lambda item: str(item[0])):
        name = str(raw_name)
        expected = str(raw_expected)
        if Path(name).name != name or not expected:
            raise GeneratedInputIdentityError(
                f"Generated-input identity entry is invalid: {name!r}."
            )
        path = (run_dir / name).resolve()
        if not path.is_relative_to(run_dir) or not path.is_file():
            raise GeneratedInputIdentityError(
                f"Generated input is missing or escapes its run directory: {name}."
            )
        actual = _sha256_file(path)
        if actual != expected:
            raise GeneratedInputIdentityError(f"Generated input changed after packaging: {name}.")
        verified[name] = actual
    return verified


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
