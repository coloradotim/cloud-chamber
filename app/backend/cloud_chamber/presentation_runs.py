"""Issue #420 high-resolution packages and native-output validation."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import xarray as xr
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.bomex_case import (
    collect_cm1_provenance as collect_bomex_cm1_provenance,
)
from cloud_chamber.bomex_case import (
    replace_bomex_namelist_assignment,
)
from cloud_chamber.generated_input_identity import verify_generated_input_identity
from cloud_chamber.local_run_manager import NORMAL_TERMINATION_MARKER
from cloud_chamber.mountain_wave_case import (
    active_cm1_processes,
    verified_clean_git_commit,
)
from cloud_chamber.mountain_wave_case import (
    collect_cm1_provenance as collect_mountain_cm1_provenance,
)
from cloud_chamber.result_ingest import ingest_completed_run
from cloud_chamber.run_manifest import (
    GeneratedInputs,
    LifecycleState,
    ProductState,
    ProvenanceMetadata,
    RunManifest,
    ScenarioReference,
    ValidationStatus,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings

PRESENTATION_PROFILE_ID = "cloud_world_presentation_v1"
MINIMUM_POST_RUN_FREE_BYTES = 5 * 1024**3
NUMBERED_HISTORY_PATTERN = re.compile(r"^cm1out_(\d+)\.nc4?$")


class PresentationRunError(RuntimeError):
    """Raised when an issue #420 package, launch gate, or output is invalid."""


@dataclass(frozen=True)
class PresentationRunSpec:
    key: str
    world: Literal["trade_cumulus", "mountain_waves"]
    display_name: str
    source_run_id: str
    run_id: str
    case_id: str
    nx: int
    ny: int
    nz: int
    dx_m: float
    dy_m: float
    dz_m: float
    time_step_seconds: float
    duration_seconds: int
    output_cadence_seconds: int
    moist_terrain: bool = False

    @property
    def expected_times_seconds(self) -> tuple[int, ...]:
        return tuple(range(0, self.duration_seconds + 1, self.output_cadence_seconds))

    @property
    def changed_assignments(self) -> dict[str, str]:
        return {
            "nx": str(self.nx),
            "ny": str(self.ny),
            "nz": str(self.nz),
            "dx": _fortran_float(self.dx_m),
            "dy": _fortran_float(self.dy_m),
            "dz": _fortran_float(self.dz_m),
            "dtl": _fortran_float(self.time_step_seconds),
            "timax": _fortran_float(self.duration_seconds),
            "tapfrq": _fortran_float(self.output_cadence_seconds),
        }


PRESENTATION_RUN_SPECS = (
    PresentationRunSpec(
        key="trade_baseline",
        world="trade_cumulus",
        display_name="Canonical BOMEX Baseline",
        source_run_id="trade-cumulus-5b-full-baseline-20260720T162342Z",
        run_id="trade-cumulus-presentation-v1-baseline-20260722",
        case_id="bomex_trade_cumulus_baseline_v0",
        nx=96,
        ny=96,
        nz=100,
        dx_m=6400.0 / 96.0,
        dy_m=6400.0 / 96.0,
        dz_m=30.0,
        time_step_seconds=2.0,
        duration_seconds=14_400,
        output_cadence_seconds=60,
    ),
    PresentationRunSpec(
        key="trade_more_moisture",
        world="trade_cumulus",
        display_name="More Moisture",
        source_run_id="trade-cumulus-5b-full-more_moisture-20260720T162342Z",
        run_id="trade-cumulus-presentation-v1-more-moisture-20260722",
        case_id="bomex_trade_cumulus_baseline_v0",
        nx=96,
        ny=96,
        nz=100,
        dx_m=6400.0 / 96.0,
        dy_m=6400.0 / 96.0,
        dz_m=30.0,
        time_step_seconds=2.0,
        duration_seconds=14_400,
        output_cadence_seconds=60,
    ),
    PresentationRunSpec(
        key="mountain_dry",
        world="mountain_waves",
        display_name="Dry Ridge - Wave Mechanics",
        source_run_id="dry-mountain-wave-official-20260721T183530Z",
        run_id="dry-mountain-wave-presentation-v1-20260722",
        case_id="cm1_r21_1_dry_mountain_wave_presentation_v1",
        nx=200,
        ny=1,
        nz=200,
        dx_m=100.0,
        dy_m=100.0,
        dz_m=100.0,
        time_step_seconds=1.0,
        duration_seconds=2_160,
        output_cadence_seconds=30,
    ),
    PresentationRunSpec(
        key="mountain_moist",
        world="mountain_waves",
        display_name="Boulder Windstorm - Moist Reference",
        source_run_id="moist-mountain-wave-toy-1972-20260721T215226Z",
        run_id="moist-mountain-wave-presentation-v1-20260722",
        case_id="cm1_r21_1_toy2011_boulder_moist_wave_7200s_presentation_v1",
        nx=440,
        ny=1,
        nz=250,
        dx_m=500.0,
        dy_m=500.0,
        dz_m=100.0,
        time_step_seconds=1.0,
        duration_seconds=7_200,
        output_cadence_seconds=30,
        moist_terrain=True,
    ),
)


class PresentationStorageEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_run_bytes: int
    source_history_count: int
    source_scalar_cells: int
    target_history_count: int
    target_scalar_cells: int
    estimated_retained_bytes: int
    minimum_post_run_free_bytes: int = MINIMUM_POST_RUN_FREE_BYTES


class PresentationPackage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    key: str
    run_id: str
    package_dir: Path
    manifest_path: Path
    storage: PresentationStorageEstimate


class PresentationRunEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_version: str = "cloud_world_presentation_run_evidence_v1"
    profile_id: str = PRESENTATION_PROFILE_ID
    run_id: str
    source_run_id: str
    world: str
    case_id: str
    implementation_commit: str
    grid: dict[str, int | float]
    duration_seconds: int
    output_cadence_seconds: int
    history_count: int
    times_seconds: list[int]
    required_fields: list[str]
    available_fields: list[str]
    non_finite_counts: dict[str, int]
    frame_minimums: dict[str, float]
    frame_maximums: dict[str, float]
    numbered_history_bytes: int
    retained_run_bytes: int
    runtime_seconds: float | None
    runtime_warnings: list[str] = Field(default_factory=list)
    normal_completion: bool


def spec_by_key(key: str) -> PresentationRunSpec:
    try:
        return next(spec for spec in PRESENTATION_RUN_SPECS if spec.key == key)
    except StopIteration as exc:
        raise PresentationRunError(f"Unknown presentation run: {key}") from exc


def generate_presentation_package(
    *, settings: CloudChamberSettings, spec: PresentationRunSpec
) -> PresentationPackage:
    """Clone one accepted source contract into a higher-resolution package."""
    implementation_commit = verified_clean_git_commit()
    if active_cm1_processes():
        raise PresentationRunError("A CM1 or MPI process is already active.")
    runs_root = settings.runtime_home.expanduser() / "runs"
    source_dir = runs_root / spec.source_run_id
    target_dir = runs_root / spec.run_id
    if target_dir.exists():
        raise PresentationRunError(f"Presentation package already exists: {spec.run_id}")
    source_manifest_path = source_dir / "run_manifest.json"
    if not source_manifest_path.is_file():
        raise PresentationRunError(f"Accepted source run is unavailable: {spec.source_run_id}")
    source_manifest = load_run_manifest(source_manifest_path)
    if (
        source_manifest.lifecycle_state != LifecycleState.COMPLETED
        or source_manifest.execution.exit_code != 0
    ):
        raise PresentationRunError(f"Accepted source run is not completed: {spec.source_run_id}")

    target_dir.mkdir(parents=True)
    try:
        source_namelist = source_dir / "namelist.input"
        source_sounding = source_dir / "input_sounding"
        source_checklist = source_dir / "runtime_file_checklist.json"
        namelist_path = target_dir / "namelist.input"
        sounding_path = target_dir / "input_sounding"
        checklist_path = target_dir / "runtime_file_checklist.json"
        namelist_text = render_presentation_namelist(source_namelist.read_text(), spec)
        namelist_path.write_text(namelist_text)
        shutil.copy2(source_sounding, sounding_path)
        shutil.copy2(source_checklist, checklist_path)
        generated_paths = [namelist_path, sounding_path, checklist_path]
        if spec.moist_terrain:
            terrain_path = target_dir / "perts.dat"
            write_moist_presentation_terrain(terrain_path, spec)
            generated_paths.append(terrain_path)

        storage = estimate_presentation_storage(source_dir, source_manifest, spec)
        available = shutil.disk_usage(target_dir).free
        if available < storage.estimated_retained_bytes + storage.minimum_post_run_free_bytes:
            raise PresentationRunError(
                f"Insufficient storage for {spec.run_id}: need "
                f"{storage.estimated_retained_bytes + storage.minimum_post_run_free_bytes} bytes."
            )
        storage_path = target_dir / "storage_estimate.json"
        _write_json(storage_path, storage.model_dump())
        generated_paths.append(storage_path)

        source_input_hashes = {
            path.name: _sha256_file(path)
            for path in (source_namelist, source_sounding, source_checklist)
        }
        case_manifest_path = target_dir / "case_manifest.json"
        case_manifest = {
            "case_id": spec.case_id,
            "profile_id": PRESENTATION_PROFILE_ID,
            "run_id": spec.run_id,
            "world": spec.world,
            "source_run_id": spec.source_run_id,
            "source_case_id": source_manifest.scenario.id,
            "source_input_sha256": source_input_hashes,
            "implementation_commit": implementation_commit,
            "changed_namelist_assignments": spec.changed_assignments,
            "storage_estimate": storage.model_dump(),
            "execution_authorization": {
                "process_count": 1,
                "retry_allowed": False,
                "duration_seconds": spec.duration_seconds,
            },
        }
        _write_json(case_manifest_path, case_manifest)
        generated_paths.append(case_manifest_path)
        generated_hashes = {path.name: _sha256_file(path) for path in generated_paths}

        now = datetime.now(UTC)
        configuration = json.loads(json.dumps(source_manifest.run_configuration))
        configuration.update(
            {
                "case_id": spec.case_id,
                "presentation_profile_id": PRESENTATION_PROFILE_ID,
                "source_run_id": spec.source_run_id,
                "duration_seconds": spec.duration_seconds,
                "output_cadence_seconds": spec.output_cadence_seconds,
                "expected_model_output_count": len(spec.expected_times_seconds),
                "domain": {
                    **dict(configuration.get("domain", {})),
                    "nx": spec.nx,
                    "ny": spec.ny,
                    "nz": spec.nz,
                    "dx_m": spec.dx_m,
                    "dy_m": spec.dy_m,
                    "dz_m": spec.dz_m,
                },
                "time_step": {
                    **dict(configuration.get("time_step", {})),
                    "target_seconds": spec.time_step_seconds,
                },
                "generated_input_sha256": generated_hashes,
                "storage_estimate": storage.model_dump(),
                "changed_namelist_assignments": spec.changed_assignments,
            }
        )
        diagnostic_cadence = configuration.get("diagnostic_cadence_seconds")
        if isinstance(diagnostic_cadence, int | float) and diagnostic_cadence > 0:
            configuration["expected_diagnostic_output_count"] = (
                math.floor(spec.duration_seconds / diagnostic_cadence) + 1
            )
        if spec.moist_terrain:
            configuration["terrain"] = {
                "type": "witch_of_agnesi",
                "height_m": 2000.0,
                "half_width_m": 10_000.0,
                "center_m": spec.dx_m / 2.0,
                "native_dx_m": spec.dx_m,
            }
        fixed = configuration.get("fixed_assumptions")
        if isinstance(fixed, dict):
            fixed["grid"] = {"nx": spec.nx, "ny": spec.ny, "nz": spec.nz}
            fixed["spacing_m"] = {"dx": spec.dx_m, "dy": spec.dy_m, "dz": spec.dz_m}
            fixed["time_step"] = {
                **dict(fixed.get("time_step", {})),
                "target_seconds": spec.time_step_seconds,
            }
            fixed["output_cadence_seconds"] = spec.output_cadence_seconds
            configuration["fixed_assumptions_sha256"] = _sha256_json(fixed)

        required_fields = list(source_manifest.required_output_fields)
        if spec.key == "mountain_dry":
            required_fields = sorted(set(required_fields) | {"uinterp", "winterp"})
        if spec.key == "mountain_moist":
            required_fields = sorted(set(required_fields) | {"uinterp", "winterp"})
        manifest_path = target_dir / "run_manifest.json"
        generated_inputs = GeneratedInputs(
            run_directory=str(target_dir),
            manifest_path=str(manifest_path),
            namelist_input=str(namelist_path),
            input_sounding=str(sounding_path),
            dry_run_report=str(target_dir / "presentation_run_report.json"),
            runtime_file_checklist=[str(checklist_path)],
        )
        manifest = source_manifest.model_copy(
            update={
                "run_id": spec.run_id,
                "scenario": ScenarioReference(
                    id=spec.case_id,
                    schema_version="cloud_world_presentation_v1",
                ),
                "run_configuration": configuration,
                "generated_inputs": generated_inputs,
                "app": source_manifest.app.model_copy(update={"commit": implementation_commit}),
                "lifecycle_state": LifecycleState.PACKAGED,
                "validation_status": ValidationStatus.VALID,
                "provenance": ProvenanceMetadata(
                    product_state=ProductState.PACKAGED_DRY_RUN_OUTPUT
                ),
                "created_at": now,
                "updated_at": now,
                "execution": source_manifest.execution.model_copy(
                    update={
                        "command": [],
                        "process_id": None,
                        "started_at": None,
                        "finished_at": None,
                        "exit_code": None,
                        "stdout_log": None,
                        "stderr_log": None,
                    }
                ),
                "outputs": source_manifest.outputs.model_copy(
                    update={
                        "raw_cm1_artifacts": [],
                        "netcdf_paths": [],
                        "processed_artifacts": [],
                        "runtime_warnings": [],
                        "diagnostics_summary": None,
                        "visualization_defaults": None,
                    }
                ),
                "user": source_manifest.user.model_copy(
                    update={"name": f"{spec.display_name} presentation v1"}
                ),
                "required_output_fields": required_fields,
                "missing_required_output_fields": [],
                "run_limitations": [
                    *source_manifest.run_limitations,
                    "issue_420_presentation_quality_upgrade",
                    "one_final_process_no_automatic_retry",
                ],
                "manual_validation_status": "issue_420_presentation_run_pending",
            }
        )
        write_run_manifest(manifest_path, manifest)
        _write_json(
            target_dir / "presentation_run_report.json",
            {
                "status": "packaged_not_executed",
                "run_id": spec.run_id,
                "source_run_id": spec.source_run_id,
                "profile_id": PRESENTATION_PROFILE_ID,
                "storage_estimate": storage.model_dump(),
            },
        )
        verify_presentation_package(settings=settings, spec=spec, require_clean_head=True)
        return PresentationPackage(
            key=spec.key,
            run_id=spec.run_id,
            package_dir=target_dir,
            manifest_path=manifest_path,
            storage=storage,
        )
    except Exception:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        raise


def load_presentation_package(
    *, settings: CloudChamberSettings, spec: PresentationRunSpec
) -> PresentationPackage:
    package_dir = settings.runtime_home.expanduser() / "runs" / spec.run_id
    manifest_path = package_dir / "run_manifest.json"
    storage_path = package_dir / "storage_estimate.json"
    if not manifest_path.is_file() or not storage_path.is_file():
        raise PresentationRunError(f"Presentation package is incomplete: {spec.run_id}")
    return PresentationPackage(
        key=spec.key,
        run_id=spec.run_id,
        package_dir=package_dir,
        manifest_path=manifest_path,
        storage=PresentationStorageEstimate.model_validate(json.loads(storage_path.read_text())),
    )


def verify_presentation_package(
    *,
    settings: CloudChamberSettings,
    spec: PresentationRunSpec,
    require_clean_head: bool,
) -> dict[str, Any]:
    package = load_presentation_package(settings=settings, spec=spec)
    manifest = load_run_manifest(package.manifest_path)
    if manifest.lifecycle_state != LifecycleState.PACKAGED:
        raise PresentationRunError(f"Package {spec.run_id} is not launchable.")
    if require_clean_head and verified_clean_git_commit() != manifest.app.commit:
        raise PresentationRunError("Package implementation commit does not match clean HEAD.")
    active = active_cm1_processes()
    if active:
        raise PresentationRunError(f"Another CM1/MPI process is active: {active}")
    verified = verify_generated_input_identity(manifest)
    verified_provenance = _verify_cm1_provenance(settings=settings, spec=spec, manifest=manifest)
    namelist_path = Path(manifest.generated_inputs.namelist_input or "")
    assignments = _parse_assignments(namelist_path.read_text())
    mismatches = {
        name: (assignments.get(name), expected)
        for name, expected in spec.changed_assignments.items()
        if not _same_numeric_assignment(assignments.get(name), expected)
    }
    if mismatches:
        raise PresentationRunError(f"Presentation namelist changed: {mismatches}")
    if _numbered_histories(package.package_dir):
        raise PresentationRunError(f"Package already contains model output: {spec.run_id}")
    available = shutil.disk_usage(package.package_dir).free
    required = package.storage.estimated_retained_bytes + MINIMUM_POST_RUN_FREE_BYTES
    if available < required:
        raise PresentationRunError(
            f"Storage preflight failed for {spec.run_id}: {available} < {required}."
        )
    preflight: dict[str, Any] = {
        "checked_at": datetime.now(UTC).isoformat(),
        "run_id": spec.run_id,
        "implementation_commit": manifest.app.commit,
        "generated_input_sha256": verified,
        "cm1_provenance": verified_provenance,
        "available_free_bytes": available,
        "required_free_bytes": required,
        "active_processes": [],
        "passed": True,
    }
    _write_json(package.package_dir / "execution_preflight.json", preflight)
    return preflight


def validate_completed_presentation_run(
    *, settings: CloudChamberSettings, spec: PresentationRunSpec
) -> PresentationRunEvidence:
    package = load_presentation_package(settings=settings, spec=spec)
    manifest = load_run_manifest(package.manifest_path)
    if manifest.lifecycle_state != LifecycleState.COMPLETED or manifest.execution.exit_code != 0:
        raise PresentationRunError(f"Run did not complete normally: {spec.run_id}")
    paths = _numbered_histories(package.package_dir)
    if len(paths) != len(spec.expected_times_seconds):
        raise PresentationRunError(
            f"Run {spec.run_id} emitted {len(paths)} histories; "
            f"expected {len(spec.expected_times_seconds)}."
        )
    required = set(manifest.required_output_fields)
    aliases = {"kmh": {"kmh", "km"}, "khh": {"khh", "kh"}}
    times: list[int] = []
    available_fields: set[str] = set()
    non_finite = {field: 0 for field in sorted(required)}
    minimums: dict[str, float] = {}
    maximums: dict[str, float] = {}
    for path in paths:
        with xr.open_dataset(path, decode_times=False) as dataset:
            times.append(_dataset_time_seconds(dataset))
            if dataset.sizes.get("xh") != spec.nx or dataset.sizes.get("yh") != spec.ny:
                raise PresentationRunError(f"Horizontal grid mismatch in {path.name}.")
            if dataset.sizes.get("zh") != spec.nz:
                raise PresentationRunError(f"Vertical grid mismatch in {path.name}.")
            available_fields.update(str(name) for name in dataset.data_vars)
            for field in required:
                candidates = aliases.get(field, {field})
                source = next((name for name in candidates if name in dataset.data_vars), None)
                if source is None:
                    raise PresentationRunError(f"Required field {field} is absent in {path.name}.")
                values = np.asarray(dataset[source].values)
                finite = np.isfinite(values)
                non_finite[field] += int(values.size - np.count_nonzero(finite))
                if np.any(finite):
                    minimums[field] = min(
                        minimums.get(field, math.inf), float(np.min(values[finite]))
                    )
                    maximums[field] = max(
                        maximums.get(field, -math.inf), float(np.max(values[finite]))
                    )
    if times != list(spec.expected_times_seconds):
        raise PresentationRunError(f"History times do not match the contract for {spec.run_id}.")
    contaminated = {field: count for field, count in non_finite.items() if count}
    if contaminated:
        raise PresentationRunError(f"Required fields contain non-finite values: {contaminated}")
    stdout = Path(manifest.execution.stdout_log or "").read_text(errors="replace")
    stderr = Path(manifest.execution.stderr_log or "").read_text(errors="replace")
    if NORMAL_TERMINATION_MARKER not in stdout:
        raise PresentationRunError(f"Normal completion marker is absent for {spec.run_id}.")
    fatal_flags = [
        flag
        for flag in ("IEEE_INVALID_FLAG", "IEEE_DIVIDE_BY_ZERO", "IEEE_OVERFLOW_FLAG")
        if flag in stderr
    ]
    if fatal_flags:
        raise PresentationRunError(f"Fatal floating-point flags: {fatal_flags}")
    warnings = []
    if "IEEE_UNDERFLOW_FLAG" in stderr:
        warnings.append("CM1 stderr reported IEEE_UNDERFLOW_FLAG")
    runtime = None
    if manifest.execution.started_at and manifest.execution.finished_at:
        runtime = (manifest.execution.finished_at - manifest.execution.started_at).total_seconds()
    evidence = PresentationRunEvidence(
        run_id=spec.run_id,
        source_run_id=spec.source_run_id,
        world=spec.world,
        case_id=spec.case_id,
        implementation_commit=str(manifest.app.commit),
        grid={
            "nx": spec.nx,
            "ny": spec.ny,
            "nz": spec.nz,
            "dx_m": spec.dx_m,
            "dy_m": spec.dy_m,
            "dz_m": spec.dz_m,
        },
        duration_seconds=spec.duration_seconds,
        output_cadence_seconds=spec.output_cadence_seconds,
        history_count=len(paths),
        times_seconds=times,
        required_fields=sorted(required),
        available_fields=sorted(available_fields),
        non_finite_counts=non_finite,
        frame_minimums=minimums,
        frame_maximums=maximums,
        numbered_history_bytes=sum(path.stat().st_size for path in paths),
        retained_run_bytes=_directory_bytes(package.package_dir),
        runtime_seconds=runtime,
        runtime_warnings=warnings,
        normal_completion=True,
    )
    evidence_path = package.package_dir / "presentation_run_evidence.json"
    _write_json(evidence_path, evidence.model_dump())
    processed = [*manifest.outputs.processed_artifacts, str(evidence_path)]
    updated = manifest.model_copy(
        update={
            "validation_status": ValidationStatus.VALID,
            "outputs": manifest.outputs.model_copy(update={"processed_artifacts": processed}),
            "manual_validation_status": "issue_420_native_output_validated",
            "updated_at": datetime.now(UTC),
        }
    )
    write_run_manifest(package.manifest_path, updated)
    if spec.world == "trade_cumulus":
        ingest_completed_run(package.manifest_path)
    return evidence


def render_presentation_namelist(text: str, spec: PresentationRunSpec) -> str:
    rendered = text
    for name, value in spec.changed_assignments.items():
        rendered = replace_bomex_namelist_assignment(rendered, name, value)
    assignments = _parse_assignments(rendered)
    for name, expected in spec.changed_assignments.items():
        if not _same_numeric_assignment(assignments.get(name), expected):
            raise PresentationRunError(f"Could not apply {name}={expected} for {spec.run_id}.")
    return rendered.rstrip() + "\n"


def write_moist_presentation_terrain(path: Path, spec: PresentationRunSpec) -> None:
    if not spec.moist_terrain or spec.ny != 1:
        raise PresentationRunError("Moist terrain generation requires the moist singleton-y spec.")
    x = (np.arange(spec.nx, dtype=np.float64) - (spec.nx - 1) / 2.0) * spec.dx_m
    center_m = spec.dx_m / 2.0
    terrain = 2000.0 / (1.0 + ((x - center_m) / 10_000.0) ** 2)
    np.asarray(terrain[None, :], dtype="<f4").tofile(path)
    decoded = np.fromfile(path, dtype="<f4")
    if decoded.size != spec.nx or not np.all(np.isfinite(decoded)):
        raise PresentationRunError("Generated moist terrain is malformed.")
    if not math.isclose(float(np.max(decoded)), 2000.0, abs_tol=1e-4):
        raise PresentationRunError("Generated moist terrain does not preserve the 2 km crest.")


def estimate_presentation_storage(
    source_dir: Path, source_manifest: RunManifest, spec: PresentationRunSpec
) -> PresentationStorageEstimate:
    source_domain = source_manifest.run_configuration.get("domain", {})
    source_cells = int(source_domain["nx"]) * int(source_domain["ny"]) * int(source_domain["nz"])
    source_histories = int(source_manifest.run_configuration["expected_model_output_count"])
    source_bytes = _directory_bytes(source_dir)
    target_cells = spec.nx * spec.ny * spec.nz
    spatial_ratio = target_cells / source_cells
    history_ratio = len(spec.expected_times_seconds) / source_histories
    estimate = math.ceil(source_bytes * spatial_ratio * history_ratio * 1.15)
    return PresentationStorageEstimate(
        source_run_bytes=source_bytes,
        source_history_count=source_histories,
        source_scalar_cells=source_cells,
        target_history_count=len(spec.expected_times_seconds),
        target_scalar_cells=target_cells,
        estimated_retained_bytes=estimate,
    )


def aggregate_estimated_bytes(settings: CloudChamberSettings) -> int:
    runs_root = settings.runtime_home.expanduser() / "runs"
    total = 0
    for spec in PRESENTATION_RUN_SPECS:
        source_manifest = load_run_manifest(runs_root / spec.source_run_id / "run_manifest.json")
        total += estimate_presentation_storage(
            runs_root / spec.source_run_id, source_manifest, spec
        ).estimated_retained_bytes
    return total


def _verify_cm1_provenance(
    *,
    settings: CloudChamberSettings,
    spec: PresentationRunSpec,
    manifest: RunManifest,
) -> dict[str, str]:
    expected = manifest.run_configuration.get("cm1_provenance")
    if not isinstance(expected, dict):
        raise PresentationRunError("The package has no CM1 provenance contract.")
    if spec.world == "trade_cumulus":
        trade_live = collect_bomex_cm1_provenance(settings)
        actual = {
            "source_manifest_sha256": trade_live.source_manifest_sha256,
            "executable_sha256": trade_live.executable_sha256,
        }
    else:
        mountain_live = collect_mountain_cm1_provenance(settings)
        actual = {
            "source_manifest_sha256": mountain_live.source_manifest_sha256,
            "executable_sha256": mountain_live.executable_sha256,
        }
    mismatches = {
        name: {"expected": expected.get(name), "actual": value}
        for name, value in actual.items()
        if expected.get(name) != value
    }
    if mismatches:
        raise PresentationRunError(f"CM1 provenance changed since packaging: {mismatches}")
    return actual


def _numbered_histories(run_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in run_dir.iterdir()
        if path.is_file() and NUMBERED_HISTORY_PATTERN.fullmatch(path.name)
    )


def _dataset_time_seconds(dataset: xr.Dataset) -> int:
    raw = np.asarray(dataset["time"].values).reshape(-1)
    if raw.size != 1 or not np.isfinite(raw[0]):
        raise PresentationRunError("Each numbered history must contain one finite time.")
    value = float(raw[0])
    units = str(dataset["time"].attrs.get("units", "seconds")).lower()
    if "minute" in units:
        value *= 60.0
    elif "hour" in units:
        value *= 3600.0
    return int(round(value))


def _parse_assignments(text: str) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for line in text.splitlines():
        content = line.split("!", 1)[0]
        if "=" not in content:
            continue
        name, raw = content.split("=", 1)
        name = name.strip().lower()
        if not name or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            continue
        assignments[name] = raw.split(",", 1)[0].strip()
    return assignments


def _same_numeric_assignment(actual: str | None, expected: str) -> bool:
    if actual is None:
        return False
    try:
        return math.isclose(float(actual.replace("d", "e").replace("D", "e")), float(expected))
    except ValueError:
        return actual == expected


def _fortran_float(value: int | float) -> str:
    return f"{float(value):.10g}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
