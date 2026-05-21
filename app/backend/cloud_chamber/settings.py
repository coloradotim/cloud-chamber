"""Local settings and CM1 path discovery for Cloud Chamber."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_RUNTIME_HOME = Path("~/CloudChamber")
SETTINGS_FILENAME = "settings.json"
CLOUD_CHAMBER_CM1_ROOT = "CLOUD_CHAMBER_CM1_ROOT"
CLOUD_CHAMBER_RUNTIME_HOME = "CLOUD_CHAMBER_RUNTIME_HOME"
DEFAULT_CM1_PROBE_PATHS = (
    Path("/Users/timpeterson/cm1r21.1"),
    Path("/Users/timpeterson/cm1r21.1/run"),
)


@dataclass(frozen=True)
class CloudChamberSettings:
    runtime_home: Path
    cm1_root: Path | None
    cm1_run_dir: Path | None
    cache_dir: Path
    log_dir: Path


@dataclass(frozen=True)
class CM1DiscoveryStatus:
    ready: bool
    cm1_root: Path | None
    cm1_run_dir: Path | None
    message: str
    missing: tuple[str, ...] = ()


def default_runtime_home(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    configured = env.get(CLOUD_CHAMBER_RUNTIME_HOME)
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_RUNTIME_HOME.expanduser()


def load_settings(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    probe_paths: tuple[Path, ...] = DEFAULT_CM1_PROBE_PATHS,
) -> CloudChamberSettings:
    env = os.environ if environ is None else environ
    runtime_home = (home or default_runtime_home(env)).expanduser()
    saved = _read_saved_settings(runtime_home / SETTINGS_FILENAME)

    cm1_root = _path_from_env_or_saved(env, saved, CLOUD_CHAMBER_CM1_ROOT, "cm1_root")
    cm1_run_dir = _path_from_saved(saved, "cm1_run_dir")

    if cm1_root is None:
        cm1_root = _first_existing_path(probe_paths)
    if cm1_run_dir is None and cm1_root is not None:
        cm1_run_dir = _infer_run_dir(cm1_root)

    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=cm1_root,
        cm1_run_dir=cm1_run_dir,
        cache_dir=_path_from_saved(saved, "cache_dir") or runtime_home / "cache",
        log_dir=_path_from_saved(saved, "log_dir") or runtime_home / "logs",
    )


def discover_cm1(settings: CloudChamberSettings) -> CM1DiscoveryStatus:
    missing: list[str] = []

    if settings.cm1_root is None:
        missing.append("CM1 root path")
    elif not settings.cm1_root.exists():
        missing.append(f"CM1 root path does not exist: {settings.cm1_root}")

    if settings.cm1_run_dir is None:
        missing.append("CM1 run directory")
    elif not settings.cm1_run_dir.exists():
        missing.append(f"CM1 run directory does not exist: {settings.cm1_run_dir}")

    cm1_executable = _cm1_executable(settings.cm1_run_dir)
    if settings.cm1_run_dir is not None and cm1_executable is None:
        missing.append(f"CM1 executable not found in run directory: {settings.cm1_run_dir}")

    if missing:
        return CM1DiscoveryStatus(
            ready=False,
            cm1_root=settings.cm1_root,
            cm1_run_dir=settings.cm1_run_dir,
            message=(
                "CM1 is not ready. Set CLOUD_CHAMBER_CM1_ROOT or update "
                f"{settings.runtime_home / SETTINGS_FILENAME} with local CM1 paths."
            ),
            missing=tuple(missing),
        )

    return CM1DiscoveryStatus(
        ready=True,
        cm1_root=settings.cm1_root,
        cm1_run_dir=settings.cm1_run_dir,
        message="CM1 runtime is ready for local use.",
    )


def _read_saved_settings(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {}
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return loaded


def _path_from_env_or_saved(
    environ: Mapping[str, str],
    saved: Mapping[str, Any],
    env_name: str,
    saved_name: str,
) -> Path | None:
    configured = environ.get(env_name)
    if configured:
        return Path(configured).expanduser()
    return _path_from_saved(saved, saved_name)


def _path_from_saved(saved: Mapping[str, Any], name: str) -> Path | None:
    configured = saved.get(name)
    if configured is None:
        return None
    if not isinstance(configured, str):
        raise ValueError(f"settings field {name!r} must be a string path")
    return Path(configured).expanduser()


def _first_existing_path(paths: tuple[Path, ...]) -> Path | None:
    for path in paths:
        expanded = path.expanduser()
        if expanded.exists():
            return expanded
    return None


def _infer_run_dir(cm1_root: Path) -> Path:
    if cm1_root.name == "run":
        return cm1_root
    return cm1_root / "run"


def _cm1_executable(cm1_run_dir: Path | None) -> Path | None:
    if cm1_run_dir is None:
        return None
    candidate = cm1_run_dir / "cm1.exe"
    if candidate.exists():
        return candidate
    return None
