"""Local CM1 launch and status monitoring.

The manager launches an external CM1 executable from a generated run package.
Tests inject fake processes; CI never requires a real CM1 runtime.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, TextIO

from cloud_chamber.cm1_source_customization import (
    CM1SourceCustomizationError,
    CommandRunner,
    prepare_cm1_source_customization,
)
from cloud_chamber.pre_run_validation import report_blocks_execution
from cloud_chamber.run_manifest import (
    ExecutionMetadata,
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    RunManifest,
    RuntimePaths,
    ValidationStatus,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings, discover_cm1


class LocalRunManagerError(RuntimeError):
    """Raised when a local CM1 launch or status update cannot proceed."""


class ProcessHandle(Protocol):
    pid: int

    def poll(self) -> int | None: ...

    def wait(self, timeout: float | None = None) -> int: ...

    def terminate(self) -> None: ...


class ProcessFactory(Protocol):
    def __call__(
        self,
        command: list[str],
        *,
        cwd: Path,
        stdout: TextIO,
        stderr: TextIO,
    ) -> ProcessHandle: ...


@dataclass(frozen=True)
class RunStatus:
    run_id: str
    lifecycle_state: LifecycleState
    manifest_path: Path
    command: tuple[str, ...]
    stdout_log: Path
    stderr_log: Path
    exit_code: int | None


@dataclass
class _ActiveRun:
    manifest_path: Path
    process: ProcessHandle
    stdout_handle: TextIO
    stderr_handle: TextIO


NETCDF_OUTPUT_PATTERNS = ("*.nc", "*.nc4", "*.cdf", "*.netcdf")
RAW_CM1_OUTPUT_PATTERNS = ("cm1out_*.dat", "cm1out_*.ctl")
FLOATING_POINT_WARNING_FLAGS = (
    "IEEE_INVALID_FLAG",
    "IEEE_DIVIDE_BY_ZERO",
    "IEEE_OVERFLOW_FLAG",
    "IEEE_UNDERFLOW_FLAG",
)
NORMAL_TERMINATION_MARKER = "Program terminated normally"


def default_process_factory(
    command: list[str],
    *,
    cwd: Path,
    stdout: TextIO,
    stderr: TextIO,
) -> ProcessHandle:
    return subprocess.Popen(
        command,
        cwd=cwd,
        stdout=stdout,
        stderr=stderr,
        text=True,
        start_new_session=True,
    )


class LocalRunManager:
    """Launch and monitor one local CM1 process at a time."""

    def __init__(
        self,
        *,
        settings: CloudChamberSettings,
        process_factory: ProcessFactory = default_process_factory,
        source_build_runner: CommandRunner = subprocess.run,
    ) -> None:
        self._settings = settings
        self._process_factory = process_factory
        self._source_build_runner = source_build_runner
        self._active: _ActiveRun | None = None

    def launch(self, manifest_path: Path) -> RunStatus:
        self._refresh_active()
        if self._active is not None:
            active_manifest = load_run_manifest(self._active.manifest_path)
            raise LocalRunManagerError(
                f"Another local CM1 run is already active: {active_manifest.run_id}"
            )

        discovery = discover_cm1(self._settings)
        if not discovery.ready:
            missing = "; ".join(discovery.missing)
            raise LocalRunManagerError(f"{discovery.message} Missing: {missing}")

        manifest = load_run_manifest(manifest_path)
        if manifest.lifecycle_state != LifecycleState.PACKAGED:
            raise LocalRunManagerError(
                f"Run {manifest.run_id} must be packaged before launch; "
                f"found {manifest.lifecycle_state.value}."
            )
        if report_blocks_execution(manifest.pre_run_validation_report):
            raise LocalRunManagerError("Pre-run validation blocked CM1 launch for this package.")

        run_dir = Path(manifest.generated_inputs.run_directory).expanduser()
        if not run_dir.exists():
            raise LocalRunManagerError(f"Run package directory does not exist: {run_dir}")
        try:
            source_customization = prepare_cm1_source_customization(
                settings=self._settings,
                manifest=manifest,
                command_runner=self._source_build_runner,
            )
        except CM1SourceCustomizationError as exc:
            raise LocalRunManagerError(str(exc)) from exc
        _preflight_cm1_inputs(manifest)
        if _existing_output_paths(run_dir):
            raise LocalRunManagerError(
                f"Refusing to launch because output-like files already exist in {run_dir}"
            )
        if self._settings.cm1_run_dir is None:
            raise LocalRunManagerError("CM1 run directory is not configured.")
        _stage_required_runtime_files(manifest, self._settings.cm1_run_dir, run_dir)

        executable = (
            source_customization.executable_path
            if source_customization is not None
            else self._settings.cm1_run_dir / "cm1.exe"
        )
        command = [str(executable)]
        log_dir = run_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_log = log_dir / "stdout.log"
        stderr_log = log_dir / "stderr.log"

        queued = self._with_state(
            manifest,
            state=LifecycleState.QUEUED,
            product_state=ProductState.QUEUED_RUNNING_CM1_PROCESS,
            command=command,
            stdout_log=stdout_log,
            stderr_log=stderr_log,
        )
        write_run_manifest(manifest_path, queued)

        stdout_handle = stdout_log.open("w")
        stderr_handle = stderr_log.open("w")
        try:
            process = self._process_factory(
                command,
                cwd=run_dir,
                stdout=stdout_handle,
                stderr=stderr_handle,
            )
        except Exception as exc:
            stdout_handle.close()
            stderr_handle.close()
            failed = self._with_state(
                queued,
                state=LifecycleState.FAILED,
                product_state=ProductState.FAILED_CANCELED_CM1_RUN,
                exit_code=None,
            )
            write_run_manifest(manifest_path, failed)
            raise LocalRunManagerError(f"Failed to launch CM1 process: {exc}") from exc

        running = self._with_state(
            queued,
            state=LifecycleState.RUNNING,
            product_state=ProductState.QUEUED_RUNNING_CM1_PROCESS,
            process_id=getattr(process, "pid", None),
        )
        write_run_manifest(manifest_path, running)
        self._active = _ActiveRun(manifest_path, process, stdout_handle, stderr_handle)
        return _status_from_manifest(running, manifest_path)

    def status(self, manifest_path: Path) -> RunStatus:
        self._refresh_active()
        manifest = load_run_manifest(manifest_path)
        if self._active is None or self._active.manifest_path != manifest_path:
            manifest = reconcile_completed_run_manifest(manifest_path, manifest)
        return _status_from_manifest(manifest, manifest_path)

    def cancel(self) -> RunStatus:
        if self._active is None:
            raise LocalRunManagerError("No local CM1 run is active.")

        active = self._active
        manifest = load_run_manifest(active.manifest_path)
        active.process.terminate()
        exit_code = active.process.wait(timeout=5)
        self._close_active()

        canceled = self._with_state(
            manifest,
            state=LifecycleState.CANCELED,
            product_state=ProductState.FAILED_CANCELED_CM1_RUN,
            exit_code=exit_code,
        )
        write_run_manifest(active.manifest_path, canceled)
        return _status_from_manifest(canceled, active.manifest_path)

    def _refresh_active(self) -> None:
        if self._active is None:
            return

        exit_code = self._active.process.poll()
        if exit_code is None:
            return

        active = self._active
        self._close_active()
        manifest = load_run_manifest(active.manifest_path)
        run_dir = Path(manifest.generated_inputs.run_directory).expanduser()
        output_metadata = _detect_output_metadata(run_dir, manifest.execution.stderr_log)
        output_exists = bool(output_metadata.netcdf_paths or output_metadata.raw_cm1_artifacts)
        completed_state = LifecycleState.COMPLETED if exit_code == 0 else LifecycleState.FAILED
        if exit_code == 0 and output_exists:
            product_state = ProductState.COMPLETED_CM1_RESULT
            validation_status = manifest.validation_status
        elif exit_code == 0:
            product_state = ProductState.PROCESS_COMPLETED_NO_OUTPUT
            validation_status = ValidationStatus.NEEDS_REVIEW
        else:
            product_state = ProductState.FAILED_CANCELED_CM1_RUN
            validation_status = ValidationStatus.FAILED
        updated = self._with_state(
            manifest,
            state=completed_state,
            product_state=product_state,
            exit_code=exit_code,
            validation_status=validation_status,
            outputs=output_metadata,
        )
        write_run_manifest(active.manifest_path, updated)

    def _close_active(self) -> None:
        if self._active is None:
            return
        self._active.stdout_handle.close()
        self._active.stderr_handle.close()
        self._active = None

    def _with_state(
        self,
        manifest: RunManifest,
        *,
        state: LifecycleState,
        product_state: ProductState,
        command: list[str] | None = None,
        stdout_log: Path | None = None,
        stderr_log: Path | None = None,
        process_id: int | None = None,
        exit_code: int | None = None,
        validation_status: ValidationStatus | None = None,
        outputs: OutputMetadata | None = None,
    ) -> RunManifest:
        now = datetime.now(UTC)
        existing_execution = manifest.execution
        started_at = existing_execution.started_at
        if state in {LifecycleState.QUEUED, LifecycleState.RUNNING} and started_at is None:
            started_at = now
        finished_at = existing_execution.finished_at
        if state in {LifecycleState.COMPLETED, LifecycleState.FAILED, LifecycleState.CANCELED}:
            finished_at = now

        runtime_paths = manifest.runtime_paths.model_copy(
            update={
                "runtime_home": str(self._settings.runtime_home),
                "cm1_root": str(self._settings.cm1_root) if self._settings.cm1_root else None,
                "cm1_run_dir": (
                    str(self._settings.cm1_run_dir) if self._settings.cm1_run_dir else None
                ),
                "cache_dir": str(self._settings.cache_dir),
                "log_dir": str(self._settings.log_dir),
            }
        )
        execution = existing_execution.model_copy(
            update={
                "command": command or existing_execution.command,
                "process_id": (
                    process_id if process_id is not None else existing_execution.process_id
                ),
                "started_at": started_at,
                "finished_at": finished_at,
                "exit_code": exit_code,
                "stdout_log": str(stdout_log) if stdout_log else existing_execution.stdout_log,
                "stderr_log": str(stderr_log) if stderr_log else existing_execution.stderr_log,
            }
        )
        next_validation_status = validation_status or (
            ValidationStatus.FAILED
            if state in {LifecycleState.FAILED, LifecycleState.CANCELED}
            else manifest.validation_status
        )
        return manifest.model_copy(
            update={
                "lifecycle_state": state,
                "validation_status": next_validation_status,
                "runtime_paths": RuntimePaths.model_validate(runtime_paths.model_dump()),
                "execution": ExecutionMetadata.model_validate(execution.model_dump()),
                "outputs": outputs or manifest.outputs,
                "provenance": ProvenanceMetadata(product_state=product_state),
                "updated_at": now,
            }
        )


def _status_from_manifest(manifest: RunManifest, manifest_path: Path) -> RunStatus:
    stdout_log = Path(manifest.execution.stdout_log or "")
    stderr_log = Path(manifest.execution.stderr_log or "")
    return RunStatus(
        run_id=manifest.run_id,
        lifecycle_state=manifest.lifecycle_state,
        manifest_path=manifest_path,
        command=tuple(manifest.execution.command),
        stdout_log=stdout_log,
        stderr_log=stderr_log,
        exit_code=manifest.execution.exit_code,
    )


def reconcile_completed_run_manifest(
    manifest_path: Path,
    manifest: RunManifest | None = None,
) -> RunManifest:
    """Promote or fail stale running manifests after backend restarts.

    This covers app/backend restarts where the in-memory process watcher is
    gone. Normal stdout termination remains the only path to completed output.
    If no process can be found and no normal completion evidence exists, fail
    loudly so the serial queue does not remain blocked forever.
    """
    manifest = manifest or load_run_manifest(manifest_path)
    if manifest.lifecycle_state not in {LifecycleState.QUEUED, LifecycleState.RUNNING}:
        return manifest
    if manifest.lifecycle_state == LifecycleState.QUEUED:
        return manifest
    stdout_log = _log_path(manifest.execution.stdout_log)
    run_dir = Path(manifest.generated_inputs.run_directory).expanduser()
    output_metadata = _detect_output_metadata(run_dir, manifest.execution.stderr_log)
    if _stdout_indicates_normal_completion(stdout_log):
        if output_metadata.netcdf_paths or output_metadata.raw_cm1_artifacts:
            return _write_reconciled_manifest(
                manifest_path,
                manifest,
                state=LifecycleState.COMPLETED,
                product_state=ProductState.COMPLETED_CM1_RESULT,
                validation_status=manifest.validation_status,
                exit_code=0,
                outputs=output_metadata,
            )
        return _write_reconciled_manifest(
            manifest_path,
            manifest,
            state=LifecycleState.COMPLETED,
            product_state=ProductState.PROCESS_COMPLETED_NO_OUTPUT,
            validation_status=ValidationStatus.NEEDS_REVIEW,
            exit_code=0,
            outputs=output_metadata,
        )

    stale_warning = _stale_running_process_warning(manifest)
    if stale_warning is None:
        return manifest
    output_metadata = output_metadata.model_copy(
        update={"runtime_warnings": [*output_metadata.runtime_warnings, stale_warning]}
    )
    return _write_reconciled_manifest(
        manifest_path,
        manifest,
        state=LifecycleState.FAILED,
        product_state=ProductState.FAILED_CANCELED_CM1_RUN,
        validation_status=ValidationStatus.FAILED,
        exit_code=manifest.execution.exit_code,
        outputs=output_metadata,
    )


def _write_reconciled_manifest(
    manifest_path: Path,
    manifest: RunManifest,
    *,
    state: LifecycleState,
    product_state: ProductState,
    validation_status: ValidationStatus,
    exit_code: int | None,
    outputs: OutputMetadata,
) -> RunManifest:
    now = datetime.now(UTC)
    execution = manifest.execution.model_copy(
        update={
            "finished_at": manifest.execution.finished_at or now,
            "exit_code": exit_code,
        }
    )
    updated = manifest.model_copy(
        update={
            "lifecycle_state": state,
            "validation_status": validation_status,
            "execution": ExecutionMetadata.model_validate(execution.model_dump()),
            "outputs": outputs,
            "provenance": ProvenanceMetadata(product_state=product_state),
            "updated_at": now,
        }
    )
    write_run_manifest(manifest_path, updated)
    return updated


def _stale_running_process_warning(manifest: RunManifest) -> str | None:
    process_id = manifest.execution.process_id
    if process_id is not None:
        if _process_id_is_alive(process_id):
            return None
        return (
            f"Tracked CM1 process {process_id} is no longer running and no normal "
            "completion marker was found; marking the run failed so the serial "
            "queue can continue."
        )
    if _command_process_may_be_running(manifest.execution.command):
        return None
    return (
        "Running CM1 manifest has no tracked process id, no matching cm1 process "
        "was found, and no normal completion marker was found; marking the run "
        "failed so the serial queue can continue."
    )


def _process_id_is_alive(process_id: int) -> bool:
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _command_process_may_be_running(command: list[str]) -> bool:
    if not command:
        return False
    executable = command[0]
    try:
        completed = subprocess.run(
            ["ps", "-axo", "command="],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return any(executable in line for line in completed.stdout.splitlines())


def _log_path(configured_path: str | None) -> Path | None:
    if not configured_path:
        return None
    return Path(configured_path).expanduser()


def _stdout_indicates_normal_completion(stdout_log: Path | None) -> bool:
    if stdout_log is None or not stdout_log.exists():
        return False
    text = stdout_log.read_text(errors="replace")
    return NORMAL_TERMINATION_MARKER in text


def _existing_output_paths(run_dir: Path) -> tuple[Path, ...]:
    return _output_artifact_paths(run_dir)


def _output_artifact_paths(run_dir: Path) -> tuple[Path, ...]:
    return _matching_paths(run_dir, NETCDF_OUTPUT_PATTERNS + RAW_CM1_OUTPUT_PATTERNS)


def _detect_output_metadata(run_dir: Path, stderr_log: str | None) -> OutputMetadata:
    netcdf_paths = _matching_paths(run_dir, NETCDF_OUTPUT_PATTERNS)
    raw_cm1_artifacts = _matching_paths(run_dir, RAW_CM1_OUTPUT_PATTERNS)
    return OutputMetadata(
        netcdf_paths=[str(path) for path in netcdf_paths],
        raw_cm1_artifacts=[str(path) for path in raw_cm1_artifacts],
        runtime_warnings=_runtime_warnings_from_stderr(stderr_log),
    )


def _runtime_warnings_from_stderr(stderr_log: str | None) -> list[str]:
    if not stderr_log:
        return []
    path = Path(stderr_log).expanduser()
    if not path.exists():
        return []
    text = path.read_text(errors="replace")
    flags = [flag for flag in FLOATING_POINT_WARNING_FLAGS if flag in text]
    if not flags:
        return []
    return ["CM1 stderr reported floating-point exception flags: " + ", ".join(flags)]


def _matching_paths(run_dir: Path, patterns: tuple[str, ...]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(run_dir.glob(pattern))
    return tuple(sorted(set(paths)))


def _preflight_cm1_inputs(manifest: RunManifest) -> None:
    checks = {
        "namelist.input": manifest.generated_inputs.namelist_input,
        "input_sounding": manifest.generated_inputs.input_sounding,
    }
    for label, configured_path in checks.items():
        if configured_path is None:
            raise LocalRunManagerError(f"Missing generated CM1 input path: {label}")
        path = Path(configured_path).expanduser()
        if not path.exists():
            raise LocalRunManagerError(f"Generated CM1 input does not exist: {path}")
        text = path.read_text()
        if _is_placeholder_input(text):
            raise LocalRunManagerError(
                f"Refusing to launch placeholder-only CM1 input: {path.name}"
            )
        if path.name == "namelist.input":
            _validate_rayleigh_damping(text)


def _is_placeholder_input(text: str) -> bool:
    lowered = text.lower()
    return (
        "placeholder until local/manual cm1 validation" in lowered
        or "cloud chamber input_sounding notes" in lowered
        or "&cloud_chamber_domain" in lowered
    )


def _validate_rayleigh_damping(namelist_text: str) -> None:
    zd = _namelist_float(namelist_text, "zd")
    maxz = _domain_top_m(namelist_text)
    if zd is None or maxz is None:
        return
    if zd <= maxz / 2:
        raise LocalRunManagerError(
            "Rayleigh damping starts too low for the configured domain: "
            f"zd={zd:g}, maxz={maxz:g}. Damping must not cover more than half the domain."
        )


def _domain_top_m(namelist_text: str) -> float | None:
    ztop = _namelist_float(namelist_text, "ztop")
    if ztop is not None:
        return ztop
    nz = _namelist_float(namelist_text, "nz")
    dz = _namelist_float(namelist_text, "dz")
    if nz is None or dz is None:
        return None
    return nz * dz


def _namelist_float(namelist_text: str, name: str) -> float | None:
    prefix = f"{name.lower()}"
    for line in namelist_text.splitlines():
        stripped = line.split("!", 1)[0].strip()
        if not stripped.lower().startswith(prefix):
            continue
        if "=" not in stripped:
            continue
        value = stripped.split("=", 1)[1].split(",", 1)[0].strip()
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _stage_required_runtime_files(
    manifest: RunManifest,
    cm1_run_dir: Path,
    run_dir: Path,
) -> None:
    for required_file, source_candidates in _required_runtime_files(manifest).items():
        source = _first_existing_runtime_file(cm1_run_dir, source_candidates)
        if source is None:
            formatted_candidates = ", ".join(
                str(cm1_run_dir / candidate) for candidate in source_candidates
            )
            if not formatted_candidates:
                formatted_candidates = str(cm1_run_dir / required_file)
            raise LocalRunManagerError(
                "Required CM1 runtime file is missing from configured run dir "
                f"or reference case candidates: {formatted_candidates}"
            )
        destination = run_dir / required_file
        if not destination.exists():
            shutil.copy2(source, destination)


def _required_runtime_files(manifest: RunManifest) -> dict[str, tuple[str, ...]]:
    required: dict[str, tuple[str, ...]] = {}
    for checklist_path in manifest.generated_inputs.runtime_file_checklist:
        path = Path(checklist_path).expanduser()
        if not path.exists():
            continue
        loaded = json.loads(path.read_text())
        if not isinstance(loaded, dict):
            continue
        files = loaded.get("required_files", [])
        source_candidates = loaded.get("source_candidates", {})
        if isinstance(files, list):
            for item in files:
                if not isinstance(item, str) or item in required:
                    continue
                candidates = [item]
                if isinstance(source_candidates, dict):
                    configured = source_candidates.get(item)
                    if isinstance(configured, list):
                        candidates = [
                            candidate for candidate in configured if isinstance(candidate, str)
                        ] or candidates
                if item not in candidates:
                    candidates.append(item)
                required[item] = tuple(dict.fromkeys(candidates))
    return required


def _first_existing_runtime_file(cm1_run_dir: Path, candidates: tuple[str, ...]) -> Path | None:
    for candidate in candidates:
        path = cm1_run_dir / candidate
        if path.exists():
            return path
    return None
