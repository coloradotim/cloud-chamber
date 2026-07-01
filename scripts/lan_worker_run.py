#!/usr/bin/env python3
# ruff: noqa: E501
"""Run a generated Cloud Chamber CM1 package on a trusted LAN worker.

This script keeps the Mac runtime home as the system of record. It copies a
generated package to a trusted SSH worker, launches CM1 there, and copies the
completed run directory back into the original local package directory so the
existing local ingest path can handle it.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_PACKAGE_FILES = (
    "run_manifest.json",
    "case_manifest.json",
    "namelist.input",
    "input_sounding",
    "runtime_file_checklist.json",
    "dry_run_report.json",
)
NETCDF_OUTPUT_PATTERNS = ("*.nc", "*.nc4", "*.cdf", "*.netcdf")
RAW_CM1_OUTPUT_PATTERNS = ("cm1out_*.dat", "cm1out_*.ctl")
FLOATING_POINT_WARNING_FLAGS = (
    "IEEE_INVALID_FLAG",
    "IEEE_DIVIDE_BY_ZERO",
    "IEEE_OVERFLOW_FLAG",
    "IEEE_UNDERFLOW_FLAG",
    "IEEE_DENORMAL",
)
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKER_CONFIG_PATHS = (
    Path("~/CloudChamber/lan-worker.json"),
    REPO_ROOT / "local-data" / "lan-worker.json",
)


class LanWorkerError(RuntimeError):
    """Raised for unsafe or invalid LAN worker operations."""


@dataclass(frozen=True)
class WorkerConfig:
    host: str
    worker_root: str
    cm1_exe: str
    cm1_command: str | None = None
    cm1_env: dict[str, str] | None = None
    ssh_command: tuple[str, ...] = ("ssh",)
    rsync_command: tuple[str, ...] = ("rsync",)

    @property
    def runs_root(self) -> str:
        return f"{self.worker_root.rstrip('/')}/runs"


@dataclass(frozen=True)
class PackageInfo:
    package_dir: Path
    runtime_home: Path
    manifest_path: Path
    run_id: str


@dataclass(frozen=True)
class WorkerStatus:
    run_id: str
    state: str
    cm1_exe: str
    cm1_command: str | None = None
    cm1_env: dict[str, str] | None = None
    started_at: str | None = None
    finished_at: str | None = None
    exit_code: int | None = None
    netcdf_count: int = 0
    raw_artifact_count: int = 0
    message: str | None = None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "start":
            start_worker_run(args)
        elif args.command == "status":
            print_worker_status(args)
        elif args.command == "collect":
            collect_worker_run(args)
        elif args.command == "cleanup":
            cleanup_worker_run(args)
        else:
            parser.error("missing command")
    except LanWorkerError as exc:
        print(f"lan-worker-run: {exc}", file=sys.stderr)
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Cloud Chamber package on a trusted LAN CM1 worker."
    )
    parser.add_argument(
        "--runtime-home",
        default=os.environ.get("CLOUD_CHAMBER_RUNTIME_HOME", "~/CloudChamber"),
        help="Local Cloud Chamber runtime home. Defaults to CLOUD_CHAMBER_RUNTIME_HOME or ~/CloudChamber.",
    )
    parser.add_argument(
        "--worker-config",
        default=os.environ.get("CLOUD_CHAMBER_LAN_WORKER_CONFIG"),
        help=(
            "Local JSON worker config path. Defaults to CLOUD_CHAMBER_LAN_WORKER_CONFIG, "
            "~/CloudChamber/lan-worker.json, or local-data/lan-worker.json."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("start", "status", "collect"):
        command = subparsers.add_parser(name)
        command.add_argument(
            "--package-dir", required=True, help="Local generated run package dir."
        )

    collect = subparsers.choices["collect"]
    collect.add_argument(
        "--replace-incoming",
        action="store_true",
        help="Replace an existing <run-id>.incoming staging directory.",
    )
    collect.add_argument(
        "--keep-incoming",
        action="store_true",
        help="Keep the incoming staging directory after promotion.",
    )

    cleanup = subparsers.add_parser(
        "cleanup",
        help="Remove a copied-back worker run directory after local ingest succeeds.",
    )
    cleanup_identity = cleanup.add_mutually_exclusive_group(required=True)
    cleanup_identity.add_argument("--run-id", help="Run ID to remove from the worker.")
    cleanup_identity.add_argument(
        "--package-dir", help="Local package dir; run ID is read from it."
    )
    return parser


def load_worker_config(
    env: dict[str, str] | None = None,
    config_path: str | None = None,
) -> WorkerConfig:
    source = env or os.environ
    file_values, _loaded_config_path = load_worker_config_file(config_path)
    values = {
        "host": file_values.get("host"),
        "worker_root": file_values.get("worker_root"),
        "cm1_exe": file_values.get("cm1_exe"),
        "cm1_command": file_values.get("cm1_command"),
        "cm1_env": file_values.get("cm1_env"),
        "ssh": file_values.get("ssh"),
        "rsync": file_values.get("rsync"),
    }
    if source.get("CLOUD_CHAMBER_LAN_WORKER_HOST"):
        values["host"] = source["CLOUD_CHAMBER_LAN_WORKER_HOST"]
    if source.get("CLOUD_CHAMBER_LAN_WORKER_ROOT"):
        values["worker_root"] = source["CLOUD_CHAMBER_LAN_WORKER_ROOT"]
    if source.get("CLOUD_CHAMBER_LAN_WORKER_CM1_EXE"):
        values["cm1_exe"] = source["CLOUD_CHAMBER_LAN_WORKER_CM1_EXE"]
    if source.get("CLOUD_CHAMBER_LAN_WORKER_CM1_COMMAND"):
        values["cm1_command"] = source["CLOUD_CHAMBER_LAN_WORKER_CM1_COMMAND"]
    if source.get("CLOUD_CHAMBER_LAN_WORKER_SSH"):
        values["ssh"] = source["CLOUD_CHAMBER_LAN_WORKER_SSH"]
    if source.get("CLOUD_CHAMBER_LAN_WORKER_RSYNC"):
        values["rsync"] = source["CLOUD_CHAMBER_LAN_WORKER_RSYNC"]

    missing = [name for name in ("host", "worker_root", "cm1_exe") if not values.get(name)]
    if missing:
        searched = ", ".join(str(path.expanduser()) for path in DEFAULT_WORKER_CONFIG_PATHS)
        if config_path:
            searched = str(Path(config_path).expanduser())
        raise LanWorkerError(
            "Missing LAN worker configuration: "
            + ", ".join(missing)
            + ". Add them to an ignored local config file or set env overrides. "
            + f"Searched: {searched}"
        )
    return WorkerConfig(
        host=str(values["host"]),
        worker_root=str(values["worker_root"]),
        cm1_exe=str(values["cm1_exe"]),
        cm1_command=(
            str(values["cm1_command"]) if isinstance(values.get("cm1_command"), str) else None
        ),
        cm1_env=(dict(values["cm1_env"]) if isinstance(values.get("cm1_env"), dict) else {}),
        ssh_command=tuple(shlex.split(str(values.get("ssh") or "ssh"))),
        rsync_command=tuple(shlex.split(str(values.get("rsync") or "rsync"))),
    )


def load_worker_config_file(config_path: str | None) -> tuple[dict[str, Any], Path | None]:
    paths = (
        (Path(config_path).expanduser(),)
        if config_path
        else tuple(path.expanduser() for path in DEFAULT_WORKER_CONFIG_PATHS)
    )
    for path in paths:
        if not path.exists():
            continue
        data = _read_json(path)
        values: dict[str, Any] = {}
        aliases = {
            "host": ("host", "worker_host", "CLOUD_CHAMBER_LAN_WORKER_HOST"),
            "worker_root": (
                "worker_root",
                "root",
                "scratch_root",
                "CLOUD_CHAMBER_LAN_WORKER_ROOT",
            ),
            "cm1_exe": (
                "cm1_exe",
                "cm1_executable",
                "CLOUD_CHAMBER_LAN_WORKER_CM1_EXE",
            ),
            "cm1_command": (
                "cm1_command",
                "launch_command",
                "CLOUD_CHAMBER_LAN_WORKER_CM1_COMMAND",
            ),
            "ssh": ("ssh", "ssh_command", "CLOUD_CHAMBER_LAN_WORKER_SSH"),
            "rsync": ("rsync", "rsync_command", "CLOUD_CHAMBER_LAN_WORKER_RSYNC"),
        }
        for canonical, keys in aliases.items():
            for key in keys:
                value = data.get(key)
                if isinstance(value, str) and value:
                    values[canonical] = value
                    break
        cm1_env = data.get("cm1_env")
        if isinstance(cm1_env, dict):
            values["cm1_env"] = {
                str(key): str(value)
                for key, value in cm1_env.items()
                if isinstance(key, str) and key and isinstance(value, str)
            }
        return values, path
    return {}, None


def validate_package(package_dir_arg: str, runtime_home_arg: str) -> PackageInfo:
    runtime_home = Path(runtime_home_arg).expanduser().resolve()
    package_dir = Path(package_dir_arg).expanduser().resolve()
    runs_dir = runtime_home / "runs"
    if not _is_relative_to(package_dir, runs_dir):
        raise LanWorkerError(
            f"Refusing package outside runtime runs directory: {package_dir} "
            f"is not under {runs_dir}"
        )
    if not package_dir.is_dir():
        raise LanWorkerError(f"Package directory does not exist: {package_dir}")
    missing = [name for name in REQUIRED_PACKAGE_FILES if not (package_dir / name).exists()]
    if missing:
        raise LanWorkerError(f"Package is missing required generated files: {', '.join(missing)}")
    manifest_path = package_dir / "run_manifest.json"
    data = _read_json(manifest_path)
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise LanWorkerError(f"Manifest does not contain a valid run_id: {manifest_path}")
    expected_dir = runs_dir / run_id
    if package_dir != expected_dir:
        raise LanWorkerError(
            f"Package directory must match its run ID under runtime home: expected {expected_dir}"
        )
    return PackageInfo(
        package_dir=package_dir,
        runtime_home=runtime_home,
        manifest_path=manifest_path,
        run_id=run_id,
    )


def start_worker_run(args: argparse.Namespace) -> None:
    config = load_worker_config(config_path=args.worker_config)
    package = validate_package(args.package_dir, args.runtime_home)
    remote_dir = remote_run_dir(config, package.run_id)
    run_command((*config.ssh_command, config.host, f"mkdir -p {shlex.quote(remote_dir)}"))
    run_command(
        (
            *config.rsync_command,
            "-a",
            "--delete",
            f"{package.package_dir}/",
            f"{config.host}:{remote_dir}/",
        )
    )
    runner_text = render_worker_runner(
        package.run_id,
        config.cm1_exe,
        config.cm1_command or config.cm1_exe,
        config.cm1_env or {},
    )
    with tempfile.TemporaryDirectory(prefix="cloud-chamber-worker-runner-") as tempdir:
        local_runner = Path(tempdir) / ".cloud_chamber_worker_runner.sh"
        local_runner.write_text(runner_text)
        run_command(
            (
                *config.rsync_command,
                "-a",
                str(local_runner),
                f"{config.host}:{remote_dir}/.cloud_chamber_worker_runner.sh",
            )
        )
    remote_start = (
        f"cd {shlex.quote(remote_dir)} && "
        "chmod +x ./.cloud_chamber_worker_runner.sh && "
        "setsid -f bash ./.cloud_chamber_worker_runner.sh "
        "> worker_launcher.log 2>&1 < /dev/null && "
        "printf '%s\\n' worker_run_started"
    )
    run_command((*config.ssh_command, config.host, remote_start))
    mark_local_worker_status(
        package.package_dir,
        "running",
        "Package copied to the LAN worker and CM1 launch was requested.",
        {
            "run_id": package.run_id,
            "remote_dir": remote_dir,
            "cm1_exe": config.cm1_exe,
            "cm1_command": config.cm1_command or config.cm1_exe,
            "cm1_env": config.cm1_env or {},
            "netcdf_count": 0,
            "raw_artifact_count": 0,
        },
    )
    print(json.dumps({"run_id": package.run_id, "remote_dir": remote_dir, "state": "started"}))


def print_worker_status(args: argparse.Namespace) -> None:
    config = load_worker_config(config_path=args.worker_config)
    package = validate_package(args.package_dir, args.runtime_home)
    status = fetch_worker_status(config, package.run_id)
    status_path = package.package_dir / "worker_status.json"
    local_status = _read_json(status_path) if status_path.exists() else {}
    local_state = str(local_status.get("state") or "")
    if _preserve_local_worker_state(local_state, status.state):
        print(json.dumps(local_status, indent=2, sort_keys=True))
        return

    mark_local_worker_status(
        package.package_dir,
        status.state,
        status.message or "LAN worker status refreshed.",
        status.__dict__,
    )
    print(json.dumps(status.__dict__, indent=2, sort_keys=True))


def _preserve_local_worker_state(local_state: str, remote_state: str) -> bool:
    local_states_after_copy_back = {
        "copied_back_to_mac",
        "ready_for_local_ingest",
        "local_ingest_confirmed",
        "worker_cleanup_pending",
        "worker_cleanup_complete",
        "worker_cleanup_failed",
    }
    return local_state in local_states_after_copy_back and remote_state in {
        "completed",
        "completed_no_output",
        "failed",
    }


def collect_worker_run(args: argparse.Namespace) -> None:
    config = load_worker_config(config_path=args.worker_config)
    package = validate_package(args.package_dir, args.runtime_home)
    status = fetch_worker_status(config, package.run_id)
    remote_dir = remote_run_dir(config, package.run_id)
    incoming_dir = package.package_dir.with_name(package.package_dir.name + ".incoming")
    if incoming_dir.exists():
        if not args.replace_incoming:
            raise LanWorkerError(
                f"Incoming staging directory already exists: {incoming_dir}. "
                "Use --replace-incoming to replace it."
            )
        shutil.rmtree(incoming_dir)
    incoming_dir.mkdir(parents=True)
    run_command(
        (
            *config.rsync_command,
            "-a",
            f"{config.host}:{remote_dir}/",
            f"{incoming_dir}/",
        )
    )
    verify_returned_run(incoming_dir, package.run_id)
    copy_tree_contents(incoming_dir, package.package_dir)
    updated_status = read_worker_status(package.package_dir / "worker_status.json")
    update_local_manifest_after_return(package, updated_status)
    ready_for_ingest = (
        updated_status.exit_code == 0
        and updated_status.netcdf_count + updated_status.raw_artifact_count > 0
    )
    mark_local_worker_status(
        package.package_dir,
        "ready_for_local_ingest" if ready_for_ingest else "copied_back_to_mac",
        (
            "Worker output was copied back, verified, and promoted locally. "
            "Run local ingest, then use cleanup to remove the worker copy."
            if ready_for_ingest
            else "Worker run was copied back and promoted locally, but it is not a "
            "successful output-producing run ready for ingest."
        ),
    )
    if not args.keep_incoming:
        shutil.rmtree(incoming_dir)
    print(
        json.dumps(
            {
                "run_id": package.run_id,
                "state": status.state,
                "local_package_dir": str(package.package_dir),
                "ready_for_ingest": status.exit_code == 0
                and status.netcdf_count + status.raw_artifact_count > 0,
            },
            indent=2,
            sort_keys=True,
        )
    )


def cleanup_worker_run(args: argparse.Namespace) -> None:
    config = load_worker_config(config_path=args.worker_config)
    package_dir: Path | None = None
    if args.package_dir:
        package = validate_package(args.package_dir, args.runtime_home)
        run_id = package.run_id
        package_dir = package.package_dir
    else:
        run_id = args.run_id
        candidate = Path(args.runtime_home).expanduser().resolve() / "runs" / str(run_id)
        if candidate.exists():
            package_dir = candidate
    remote_dir = safe_remote_run_dir(config, str(run_id))
    command = build_cleanup_remote_command(remote_dir)
    try:
        result = run_command((*config.ssh_command, config.host, command), capture=True)
    except LanWorkerError as exc:
        if package_dir is not None:
            mark_local_worker_status(
                package_dir,
                "worker_cleanup_failed",
                f"LAN worker cleanup failed and can be retried: {exc}",
            )
        raise

    outcome = result.stdout.strip() or "worker_cleanup_complete"
    state = (
        "worker_cleanup_complete"
        if outcome in {"worker_cleanup_complete", "already_removed"}
        else outcome
    )
    message = (
        "LAN worker run directory was already removed."
        if outcome == "already_removed"
        else "LAN worker run directory was removed."
    )
    if package_dir is not None:
        mark_local_worker_status(package_dir, state, message)
    print(
        json.dumps(
            {
                "run_id": run_id,
                "remote_dir": remote_dir,
                "state": state,
                "message": message,
            },
            indent=2,
            sort_keys=True,
        )
    )


def remote_run_dir(config: WorkerConfig, run_id: str) -> str:
    return safe_remote_run_dir(config, run_id)


def safe_remote_run_dir(config: WorkerConfig, run_id: str) -> str:
    validate_run_id(run_id)
    worker_root = _normalize_posix_path(config.worker_root)
    runs_root = _normalize_posix_path(config.runs_root)
    cm1_dir = _normalize_posix_path(posixpath.dirname(config.cm1_exe))
    remote_dir = _normalize_posix_path(posixpath.join(runs_root, run_id))
    unsafe_exact = {"/", "~", ".", worker_root, runs_root, cm1_dir}
    if remote_dir in unsafe_exact:
        raise LanWorkerError(f"Refusing unsafe worker cleanup path: {remote_dir}")
    if not _is_posix_relative_to(remote_dir, runs_root):
        raise LanWorkerError(f"Refusing worker path outside configured runs root: {remote_dir}")
    if _is_posix_relative_to(remote_dir, cm1_dir):
        raise LanWorkerError(f"Refusing worker path inside CM1 install directory: {remote_dir}")
    return remote_dir


def validate_run_id(run_id: str) -> None:
    if not run_id:
        raise LanWorkerError("Run ID is required for worker cleanup.")
    if run_id in {".", ".."} or ".." in run_id:
        raise LanWorkerError(f"Refusing unsafe run ID with path traversal: {run_id}")
    if "/" in run_id or "\\" in run_id:
        raise LanWorkerError(f"Refusing unsafe run ID with path separators: {run_id}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", run_id):
        raise LanWorkerError(f"Refusing unsafe run ID: {run_id}")


def build_cleanup_remote_command(remote_dir: str) -> str:
    quoted = shlex.quote(remote_dir)
    return (
        f"if [ ! -e {quoted} ]; then "
        "printf '%s\\n' already_removed; "
        "else "
        f"rm -rf -- {quoted} && printf '%s\\n' worker_cleanup_complete; "
        "fi"
    )


def render_worker_runner(
    run_id: str,
    cm1_exe: str,
    cm1_command: str,
    cm1_env: dict[str, str],
) -> str:
    run_id_q = shlex.quote(run_id)
    cm1_exe_q = shlex.quote(cm1_exe)
    cm1_command_q = shlex.quote(cm1_command)
    cm1_env_q = shlex.quote(json.dumps(cm1_env, sort_keys=True))
    return f"""#!/usr/bin/env bash
set -u

RUN_ID={run_id_q}
CM1_EXE={cm1_exe_q}
CM1_COMMAND={cm1_command_q}
CM1_ENV_JSON={cm1_env_q}

write_status() {{
  local state="$1"
  local started_at="${{2:-}}"
  local finished_at="${{3:-}}"
  local exit_code="${{4:-}}"
  local netcdf_count="${{5:-0}}"
  local raw_count="${{6:-0}}"
  local message="${{7:-}}"
  python3 - "$RUN_ID" "$state" "$CM1_EXE" "$CM1_COMMAND" "$CM1_ENV_JSON" "$started_at" "$finished_at" "$exit_code" "$netcdf_count" "$raw_count" "$message" <<'PY'
import json
import sys
from pathlib import Path

run_id, state, cm1_exe, cm1_command, cm1_env_json, started_at, finished_at, exit_code, netcdf_count, raw_count, message = sys.argv[1:]

def maybe_none(value):
    return None if value == "" else value

payload = {{
    "schema_version": "1",
    "run_id": run_id,
    "state": state,
    "cm1_exe": cm1_exe,
    "cm1_command": cm1_command,
    "cm1_env": json.loads(cm1_env_json or "{{}}"),
    "started_at": maybe_none(started_at),
    "finished_at": maybe_none(finished_at),
    "exit_code": None if exit_code == "" else int(exit_code),
    "netcdf_count": int(netcdf_count),
    "raw_artifact_count": int(raw_count),
    "message": maybe_none(message),
}}
Path("worker_status.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\\n")
PY
}}

mkdir -p logs
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
write_status "running" "$started_at" "" "" 0 0 "CM1 is running on the LAN worker."

if [[ ! -x "$CM1_EXE" ]]; then
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  write_status "failed" "$started_at" "$finished_at" 127 0 0 "CM1 executable is missing or not executable on the worker."
  touch worker_failed.marker
  exit 127
fi

python3 - "$CM1_ENV_JSON" <<'PY' > .cloud_chamber_cm1_env.sh
import json
import shlex
import sys

env = json.loads(sys.argv[1] or "{{}}")
for key, value in sorted(env.items()):
    if not key.replace("_", "").isalnum() or key[0].isdigit():
        raise SystemExit(f"Unsafe environment variable name: {{key}}")
    print(f"export {{key}}={{shlex.quote(str(value))}}")
PY
env_status=$?
if [[ "$env_status" -ne 0 ]]; then
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  write_status "failed" "$started_at" "$finished_at" "$env_status" 0 0 "CM1 worker environment setup failed."
  touch worker_failed.marker
  exit "$env_status"
fi
source ./.cloud_chamber_cm1_env.sh

python3 - "$CM1_EXE" <<'PY'
import json
import shutil
import sys
from pathlib import Path

cm1_run_dir = Path(sys.argv[1]).resolve().parent
checklist_path = Path("runtime_file_checklist.json")
if checklist_path.exists():
    checklist = json.loads(checklist_path.read_text())
    required_files = checklist.get("required_files", [])
    source_candidates = checklist.get("source_candidates", {{}})
    for required_file in required_files:
        if not isinstance(required_file, str):
            continue
        destination = Path(required_file)
        if destination.exists():
            continue
        candidates = [required_file]
        configured = source_candidates.get(required_file)
        if isinstance(configured, list):
            candidates = [item for item in configured if isinstance(item, str)] or candidates
        if required_file not in candidates:
            candidates.append(required_file)
        for candidate in candidates:
            source = cm1_run_dir / candidate
            if source.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                break
        else:
            raise SystemExit(f"Missing worker runtime file: {{required_file}}")
PY
runtime_stage_status=$?
if [[ "$runtime_stage_status" -ne 0 ]]; then
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  write_status "failed" "$started_at" "$finished_at" "$runtime_stage_status" 0 0 "Required CM1 runtime file staging failed on the LAN worker."
  touch worker_failed.marker
  exit "$runtime_stage_status"
fi

bash -lc "$CM1_COMMAND" > logs/stdout.log 2> logs/stderr.log
exit_code=$?
finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
shopt -s nullglob
netcdf=( *.nc *.nc4 *.cdf *.netcdf )
raw=( cm1out_*.dat cm1out_*.ctl )
output_count=$(( ${{#netcdf[@]}} + ${{#raw[@]}} ))

if [[ "$exit_code" -eq 0 && "$output_count" -gt 0 ]]; then
  write_status "completed" "$started_at" "$finished_at" "$exit_code" "${{#netcdf[@]}}" "${{#raw[@]}}" "CM1 completed with output artifacts."
  touch worker_complete.marker
elif [[ "$exit_code" -eq 0 ]]; then
  write_status "completed_no_output" "$started_at" "$finished_at" "$exit_code" 0 0 "CM1 exited successfully but no output artifacts were detected."
  touch worker_complete.marker
else
  write_status "failed" "$started_at" "$finished_at" "$exit_code" "${{#netcdf[@]}}" "${{#raw[@]}}" "CM1 failed on the LAN worker."
  touch worker_failed.marker
fi

exit "$exit_code"
"""


def fetch_worker_status(config: WorkerConfig, run_id: str) -> WorkerStatus:
    remote_dir = remote_run_dir(config, run_id)
    remote_dir_q = shlex.quote(remote_dir)
    command = f"""python3 - {remote_dir_q} <<'PY'
import glob
import json
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
status_path = run_dir / "worker_status.json"
data = json.loads(status_path.read_text())
data["netcdf_count"] = len(
    set(
        str(path)
        for pattern in ("*.nc", "*.nc4", "*.cdf", "*.netcdf")
        for path in run_dir.glob(pattern)
    )
)
data["raw_artifact_count"] = len(
    set(
        str(path)
        for pattern in ("cm1out_*.dat", "cm1out_*.ctl")
        for path in run_dir.glob(pattern)
    )
)
print(json.dumps(data, sort_keys=True))
PY"""
    result = run_command(
        (*config.ssh_command, config.host, command),
        capture=True,
    )
    data = json.loads(result.stdout)
    return worker_status_from_mapping(data)


def read_worker_status(path: Path) -> WorkerStatus:
    return worker_status_from_mapping(_read_json(path))


def worker_status_from_mapping(data: dict[str, Any]) -> WorkerStatus:
    run_id = data.get("run_id")
    state = data.get("state")
    cm1_exe = data.get("cm1_exe")
    if not isinstance(run_id, str) or not isinstance(state, str) or not isinstance(cm1_exe, str):
        raise LanWorkerError("Worker status is missing run_id, state, or cm1_exe.")
    cm1_env = data.get("cm1_env")
    return WorkerStatus(
        run_id=run_id,
        state=state,
        cm1_exe=cm1_exe,
        cm1_command=_optional_str(data.get("cm1_command")),
        cm1_env=(
            {str(key): str(value) for key, value in cm1_env.items()}
            if isinstance(cm1_env, dict)
            else {}
        ),
        started_at=_optional_str(data.get("started_at")),
        finished_at=_optional_str(data.get("finished_at")),
        exit_code=_optional_int(data.get("exit_code")),
        netcdf_count=int(data.get("netcdf_count") or 0),
        raw_artifact_count=int(data.get("raw_artifact_count") or 0),
        message=_optional_str(data.get("message")),
    )


def verify_returned_run(returned_dir: Path, expected_run_id: str) -> None:
    missing = [name for name in REQUIRED_PACKAGE_FILES if not (returned_dir / name).exists()]
    if missing:
        raise LanWorkerError(
            f"Returned worker run is missing required package files: {', '.join(missing)}"
        )
    status_path = returned_dir / "worker_status.json"
    if not status_path.exists():
        raise LanWorkerError("Returned worker run is missing worker_status.json")
    status = read_worker_status(status_path)
    if status.run_id != expected_run_id:
        raise LanWorkerError(
            f"Returned worker run ID mismatch: expected {expected_run_id}, got {status.run_id}"
        )


def mark_local_worker_status(
    package_dir: Path,
    state: str,
    message: str,
    extra: dict[str, Any] | None = None,
) -> None:
    status_path = package_dir / "worker_status.json"
    data = _read_json(status_path) if status_path.exists() else {}
    previous_state = data.get("state")
    if previous_state and previous_state != state:
        data["previous_state"] = previous_state
    if extra:
        data.update(extra)
    data.update(
        {
            "state": state,
            "message": message,
            "local_status_updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
    )
    status_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def update_local_manifest_after_return(package: PackageInfo, status: WorkerStatus) -> None:
    data = _read_json(package.manifest_path)
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    netcdf_paths = [
        str(path) for path in sorted_output_paths(package.package_dir, NETCDF_OUTPUT_PATTERNS)
    ]
    raw_paths = [
        str(path) for path in sorted_output_paths(package.package_dir, RAW_CM1_OUTPUT_PATTERNS)
    ]
    stdout_log = package.package_dir / "logs" / "stdout.log"
    stderr_log = package.package_dir / "logs" / "stderr.log"
    output_count = len(netcdf_paths) + len(raw_paths)
    exit_code = status.exit_code
    if exit_code == 0 and output_count:
        lifecycle_state = "completed"
        product_state = "completed_cm1_result"
        validation_status = "valid"
    elif exit_code == 0:
        lifecycle_state = "completed"
        product_state = "process_completed_no_output"
        validation_status = "needs_review"
    else:
        lifecycle_state = "failed"
        product_state = "failed_canceled_cm1_run"
        validation_status = "failed"

    execution = dict(data.get("execution") or {})
    command = [status.cm1_exe]
    if status.cm1_command:
        command = ["bash", "-lc", status.cm1_command]
    execution.update(
        {
            "command": command,
            "started_at": _normalize_datetime(status.started_at),
            "finished_at": _normalize_datetime(status.finished_at) or now,
            "exit_code": exit_code,
            "stdout_log": str(stdout_log) if stdout_log.exists() else None,
            "stderr_log": str(stderr_log) if stderr_log.exists() else None,
        }
    )
    outputs = dict(data.get("outputs") or {})
    outputs.update(
        {
            "netcdf_paths": netcdf_paths,
            "raw_cm1_artifacts": raw_paths,
            "runtime_warnings": runtime_warnings_from_stderr(stderr_log),
        }
    )
    provenance = dict(data.get("provenance") or {})
    provenance["product_state"] = product_state
    data.update(
        {
            "lifecycle_state": lifecycle_state,
            "validation_status": validation_status,
            "execution": execution,
            "outputs": outputs,
            "provenance": provenance,
            "updated_at": now,
        }
    )
    package.manifest_path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")


def sorted_output_paths(run_dir: Path, patterns: tuple[str, ...]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        paths.update(run_dir.glob(pattern))
    return sorted(paths)


def runtime_warnings_from_stderr(stderr_log: Path) -> list[str]:
    if not stderr_log.exists():
        return []
    text = stderr_log.read_text(errors="replace")
    flags = [flag for flag in FLOATING_POINT_WARNING_FLAGS if flag in text]
    if not flags:
        return []
    return ["CM1 stderr reported floating-point exception flags: " + ", ".join(flags)]


def copy_tree_contents(source_dir: Path, destination_dir: Path) -> None:
    for source in source_dir.iterdir():
        destination = destination_dir / source.name
        if source.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def run_command(
    command: tuple[str, ...],
    *,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=capture,
        )
    except FileNotFoundError as exc:
        raise LanWorkerError(f"Command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.strip() if exc.stderr else str(exc)
        raise LanWorkerError(f"Command failed: {shlex.join(command)}\n{details}") from exc


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise LanWorkerError(f"Missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LanWorkerError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise LanWorkerError(f"Expected JSON object in {path}")
    return data


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _normalize_datetime(value: str | None) -> str | None:
    if not value:
        return None
    if value.endswith("Z"):
        return value
    return value.replace("+00:00", "Z")


def _normalize_posix_path(value: str) -> str:
    if not value or value in {"~", "."}:
        return value
    return posixpath.normpath(value)


def _is_posix_relative_to(path: str, parent: str) -> bool:
    parent_with_separator = parent.rstrip("/") + "/"
    return path.startswith(parent_with_separator)


if __name__ == "__main__":
    raise SystemExit(main())
