"""Backend wrapper for trusted LAN worker CM1 runs.

The script in ``scripts/lan_worker_run.py`` owns SSH/rsync execution and the
worker cleanup safety checks.  This module gives the FastAPI app a small,
bounded JSON surface without teaching the browser anything about SSH.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

from cloud_chamber.cm1_source_customization import manifest_requires_cm1_source_customization
from cloud_chamber.run_manifest import RunManifestError, load_run_manifest
from cloud_chamber.settings import CloudChamberSettings

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "lan_worker_run.py"
SCRIPT_WRAPPER_PATH = REPO_ROOT / "scripts" / "lan-worker-run.sh"


class LanWorkerApiError(RuntimeError):
    """Raised when a LAN worker operation cannot be completed safely."""


def lan_worker_config_status() -> dict[str, object]:
    """Return a sanitized worker configuration status for Build UI gating."""
    try:
        script = _load_script_module()
        config = script.load_worker_config()
    except Exception as exc:  # noqa: BLE001 - script reports setup problems as runtime errors.
        return {
            "configured": False,
            "available": False,
            "message": str(exc),
            "cm1_env_keys": [],
            "cm1_env_settings": [],
            "custom_launch_command": False,
        }
    cm1_env = config.cm1_env or {}
    return {
        "configured": True,
        "available": True,
        "message": "Trusted LAN worker is configured.",
        "cm1_env_keys": sorted(cm1_env.keys()),
        "cm1_env_settings": _safe_cm1_env_settings(cm1_env),
        "custom_launch_command": bool(config.cm1_command),
    }


def _safe_cm1_env_settings(cm1_env: dict[str, str]) -> list[str]:
    """Return non-secret CM1 runtime environment settings for the UI."""
    blocked_fragments = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS")
    settings: list[str] = []
    for key in sorted(cm1_env):
        if any(fragment in key.upper() for fragment in blocked_fragments):
            continue
        settings.append(f"{key}={cm1_env[key]}")
    return settings


def start_lan_worker_run(settings: CloudChamberSettings, manifest_path: Path) -> dict[str, object]:
    package_dir = _package_dir_from_manifest(manifest_path)
    payload = _run_lan_worker_script(settings, "start", package_dir)
    payload["state"] = "running"
    payload["message"] = "Package copied to the LAN worker and CM1 launch was requested."
    return payload


def lan_worker_run_status(settings: CloudChamberSettings, manifest_path: Path) -> dict[str, object]:
    package_dir = _package_dir_from_manifest(manifest_path)
    return _run_lan_worker_script(settings, "status", package_dir)


def collect_lan_worker_run(
    settings: CloudChamberSettings, manifest_path: Path
) -> dict[str, object]:
    package_dir = _package_dir_from_manifest(manifest_path)
    payload = _run_lan_worker_script(
        settings,
        "collect",
        package_dir,
        extra_args=("--replace-incoming",),
    )
    if payload.get("ready_for_ingest"):
        payload["state"] = "ready_for_local_ingest"
        payload["message"] = (
            "Completed LAN worker output was copied back, verified, and is ready for local ingest."
        )
    else:
        payload["state"] = payload.get("state") or "copied_back_to_mac"
        payload["message"] = (
            "LAN worker output was copied back, but it is not a successful output-producing run."
        )
    return payload


def cleanup_lan_worker_run(
    settings: CloudChamberSettings, manifest_path: Path
) -> dict[str, object]:
    package_dir = _package_dir_from_manifest(manifest_path)
    return _run_lan_worker_script(settings, "cleanup", package_dir)


def _run_lan_worker_script(
    settings: CloudChamberSettings,
    command: str,
    package_dir: Path,
    *,
    extra_args: tuple[str, ...] = (),
) -> dict[str, object]:
    args = (
        str(SCRIPT_WRAPPER_PATH),
        "--runtime-home",
        str(settings.runtime_home),
        command,
        "--package-dir",
        str(package_dir),
        *extra_args,
    )
    try:
        completed = subprocess.run(
            args,
            check=True,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise LanWorkerApiError(
            f"LAN worker helper script was not found: {SCRIPT_WRAPPER_PATH}"
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise LanWorkerApiError(detail or "LAN worker command failed.") from exc
    return _parse_json_payload(completed.stdout)


def _package_dir_from_manifest(manifest_path: Path) -> Path:
    expanded = manifest_path.expanduser()
    try:
        manifest = load_run_manifest(expanded)
    except RunManifestError as exc:
        raise LanWorkerApiError(str(exc)) from exc
    if manifest_requires_cm1_source_customization(manifest):
        raise LanWorkerApiError(
            "Differential surface forcing is local-only until LAN worker CM1 source "
            "customization and custom-executable provenance are implemented."
        )
    return expanded.parent


def _parse_json_payload(stdout: str) -> dict[str, object]:
    start = stdout.find("{")
    if start < 0:
        raise LanWorkerApiError("LAN worker command did not return a JSON payload.")
    try:
        payload = json.loads(stdout[start:])
    except json.JSONDecodeError as exc:
        raise LanWorkerApiError(f"LAN worker command returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise LanWorkerApiError("LAN worker command returned a non-object JSON payload.")
    return dict(payload)


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("cloud_chamber_lan_worker_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise LanWorkerApiError(f"Unable to load LAN worker helper: {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
