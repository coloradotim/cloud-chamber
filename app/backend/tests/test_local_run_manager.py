import json
from pathlib import Path
from typing import Any, TextIO

import pytest

from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.local_run_manager import (
    LocalRunManager,
    LocalRunManagerError,
    default_process_factory,
)
from cloud_chamber.run_manifest import (
    LifecycleState,
    ProductState,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"


class FakeProcess:
    def __init__(self) -> None:
        self.exit_code: int | None = None
        self.terminated = False
        self.pid = 12345

    def poll(self) -> int | None:
        return self.exit_code

    def wait(self, timeout: float | None = None) -> int:
        if self.exit_code is None:
            self.exit_code = -15
        return self.exit_code

    def terminate(self) -> None:
        self.terminated = True
        self.exit_code = -15


class FakeProcessFactory:
    def __init__(
        self,
        process: FakeProcess,
        *,
        stderr_text: str = "fake cm1 stderr\n",
    ) -> None:
        self.process = process
        self.stderr_text = stderr_text
        self.commands: list[list[str]] = []
        self.cwd: Path | None = None

    def __call__(
        self,
        command: list[str],
        *,
        cwd: Path,
        stdout: TextIO,
        stderr: TextIO,
    ) -> FakeProcess:
        self.commands.append(command)
        self.cwd = cwd
        stdout.write("fake cm1 stdout\n")
        stdout.flush()
        stderr.write(self.stderr_text)
        stderr.flush()
        return self.process


class FakePopen:
    pid = 34567

    def poll(self) -> int | None:
        return None

    def wait(self, timeout: float | None = None) -> int:
        return 0

    def terminate(self) -> None:
        return None


def load_baseline_template() -> object:
    return json.loads(BASELINE_TEMPLATE.read_text())


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    cm1_root = tmp_path / "cm1"
    cm1_run_dir = cm1_root / "run"
    cm1_run_dir.mkdir(parents=True)
    (cm1_run_dir / "cm1.exe").write_text("# fake executable\n")
    (cm1_run_dir / "LANDUSE.TBL").write_text("fallback local runtime file\n")
    reference_dir = cm1_run_dir / "config_files" / "les_ShallowCu"
    reference_dir.mkdir(parents=True)
    (reference_dir / "LANDUSE.TBL").write_text("fake reference runtime file\n")
    return CloudChamberSettings(
        runtime_home=tmp_path / "CloudChamber",
        cm1_root=cm1_root,
        cm1_run_dir=cm1_run_dir,
        cache_dir=tmp_path / "CloudChamber" / "cache",
        log_dir=tmp_path / "CloudChamber" / "logs",
    )


def dry_run_manifest_path(tmp_path: Path, run_id: str = "run-001") -> Path:
    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path / "CloudChamber",
        run_id=run_id,
    )
    return result.manifest_path


def test_default_process_factory_detaches_cm1_from_short_lived_callers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_popen(
        command: list[str],
        *,
        cwd: Path,
        stdout: TextIO,
        stderr: TextIO,
        text: bool,
        start_new_session: bool,
    ) -> FakePopen:
        calls.append(
            {
                "command": command,
                "cwd": cwd,
                "stdout": stdout,
                "stderr": stderr,
                "text": text,
                "start_new_session": start_new_session,
            }
        )
        return FakePopen()

    monkeypatch.setattr("cloud_chamber.local_run_manager.subprocess.Popen", fake_popen)
    stdout_path = tmp_path / "stdout.log"
    stderr_path = tmp_path / "stderr.log"

    with stdout_path.open("w") as stdout, stderr_path.open("w") as stderr:
        process = default_process_factory(
            ["cm1.exe"],
            cwd=tmp_path,
            stdout=stdout,
            stderr=stderr,
        )

    assert process.pid == 34567
    assert len(calls) == 1
    assert calls[0]["command"] == ["cm1.exe"]
    assert calls[0]["cwd"] == tmp_path
    assert calls[0]["text"] is True
    assert calls[0]["start_new_session"] is True


def test_launch_constructs_cm1_command_and_captures_logs(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    assert settings.cm1_run_dir is not None
    manifest_path = dry_run_manifest_path(tmp_path)
    fake_process = FakeProcess()
    factory = FakeProcessFactory(fake_process)
    manager = LocalRunManager(settings=settings, process_factory=factory)

    status = manager.launch(manifest_path)

    assert status.lifecycle_state == LifecycleState.RUNNING
    assert factory.commands == [[str(settings.cm1_run_dir / "cm1.exe")]]
    assert factory.cwd == tmp_path / "CloudChamber" / "runs" / "run-001"
    assert factory.cwd is not None
    assert status.stdout_log.read_text() == "fake cm1 stdout\n"
    assert status.stderr_log.read_text() == "fake cm1 stderr\n"
    assert (factory.cwd / "LANDUSE.TBL").read_text() == "fake reference runtime file\n"

    manifest = load_run_manifest(manifest_path)
    assert manifest.lifecycle_state == LifecycleState.RUNNING
    assert manifest.provenance.product_state == ProductState.QUEUED_RUNNING_CM1_PROCESS
    assert manifest.execution.command == [str(settings.cm1_run_dir / "cm1.exe")]
    assert manifest.execution.process_id == fake_process.pid


def test_exit_zero_without_output_needs_review_not_completed_result(tmp_path: Path) -> None:
    manifest_path = dry_run_manifest_path(tmp_path)
    fake_process = FakeProcess()
    manager = LocalRunManager(
        settings=fake_settings(tmp_path),
        process_factory=FakeProcessFactory(fake_process),
    )
    manager.launch(manifest_path)

    fake_process.exit_code = 0
    status = manager.status(manifest_path)

    assert status.lifecycle_state == LifecycleState.COMPLETED
    assert status.exit_code == 0
    manifest = load_run_manifest(manifest_path)
    assert manifest.lifecycle_state == LifecycleState.COMPLETED
    assert manifest.validation_status.value == "needs_review"
    assert manifest.provenance.product_state == ProductState.PROCESS_COMPLETED_NO_OUTPUT
    assert manifest.outputs.netcdf_paths == []
    assert manifest.outputs.raw_cm1_artifacts == []


def test_exit_zero_with_netcdf_output_marks_completed_result(tmp_path: Path) -> None:
    manifest_path = dry_run_manifest_path(tmp_path)
    run_dir = tmp_path / "CloudChamber" / "runs" / "run-001"
    fake_process = FakeProcess()
    manager = LocalRunManager(
        settings=fake_settings(tmp_path),
        process_factory=FakeProcessFactory(fake_process),
    )
    manager.launch(manifest_path)
    (run_dir / "cm1out_000001.nc").write_text("fake output")

    fake_process.exit_code = 0
    status = manager.status(manifest_path)

    assert status.lifecycle_state == LifecycleState.COMPLETED
    assert status.exit_code == 0
    manifest = load_run_manifest(manifest_path)
    assert manifest.validation_status.value == "valid"
    assert manifest.provenance.product_state == ProductState.COMPLETED_CM1_RESULT
    assert manifest.outputs.netcdf_paths == [str(run_dir / "cm1out_000001.nc")]
    assert manifest.outputs.raw_cm1_artifacts == []


def test_status_reconciles_stale_running_manifest_with_completed_output(tmp_path: Path) -> None:
    manifest_path = dry_run_manifest_path(tmp_path)
    run_dir = tmp_path / "CloudChamber" / "runs" / "run-001"
    settings = fake_settings(tmp_path)
    manager = LocalRunManager(
        settings=settings,
        process_factory=FakeProcessFactory(FakeProcess()),
    )
    status = manager.launch(manifest_path)
    with status.stdout_log.open("a") as stdout:
        stdout.write("Program terminated normally\n")
    (run_dir / "cm1out_000001.nc").write_text("fake output")

    restarted_manager = LocalRunManager(
        settings=settings,
        process_factory=FakeProcessFactory(FakeProcess()),
    )
    reconciled = restarted_manager.status(manifest_path)

    assert reconciled.lifecycle_state == LifecycleState.COMPLETED
    assert reconciled.exit_code == 0
    manifest = load_run_manifest(manifest_path)
    assert manifest.lifecycle_state == LifecycleState.COMPLETED
    assert manifest.provenance.product_state == ProductState.COMPLETED_CM1_RESULT
    assert manifest.outputs.netcdf_paths == [str(run_dir / "cm1out_000001.nc")]


def test_status_does_not_reconcile_stale_running_manifest_without_normal_stdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = dry_run_manifest_path(tmp_path)
    run_dir = tmp_path / "CloudChamber" / "runs" / "run-001"
    settings = fake_settings(tmp_path)
    manager = LocalRunManager(
        settings=settings,
        process_factory=FakeProcessFactory(FakeProcess()),
    )
    manager.launch(manifest_path)
    (run_dir / "cm1out_000001.nc").write_text("fake output")
    monkeypatch.setattr(
        "cloud_chamber.local_run_manager._process_id_is_alive",
        lambda _process_id: True,
    )

    restarted_manager = LocalRunManager(
        settings=settings,
        process_factory=FakeProcessFactory(FakeProcess()),
    )
    status = restarted_manager.status(manifest_path)

    assert status.lifecycle_state == LifecycleState.RUNNING
    manifest = load_run_manifest(manifest_path)
    assert manifest.lifecycle_state == LifecycleState.RUNNING
    assert manifest.provenance.product_state == ProductState.QUEUED_RUNNING_CM1_PROCESS


def test_status_fails_stale_running_manifest_when_tracked_process_disappears(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = dry_run_manifest_path(tmp_path)
    settings = fake_settings(tmp_path)
    manager = LocalRunManager(
        settings=settings,
        process_factory=FakeProcessFactory(FakeProcess()),
    )
    manager.launch(manifest_path)
    monkeypatch.setattr(
        "cloud_chamber.local_run_manager._process_id_is_alive",
        lambda _process_id: False,
    )

    restarted_manager = LocalRunManager(
        settings=settings,
        process_factory=FakeProcessFactory(FakeProcess()),
    )
    status = restarted_manager.status(manifest_path)

    assert status.lifecycle_state == LifecycleState.FAILED
    manifest = load_run_manifest(manifest_path)
    assert manifest.lifecycle_state == LifecycleState.FAILED
    assert manifest.validation_status.value == "failed"
    assert manifest.provenance.product_state == ProductState.FAILED_CANCELED_CM1_RUN
    assert manifest.outputs.runtime_warnings == [
        "Tracked CM1 process 12345 is no longer running and no normal completion marker "
        "was found; marking the run failed so the serial queue can continue."
    ]


def test_status_fails_untracked_stale_running_manifest_without_matching_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = dry_run_manifest_path(tmp_path)
    settings = fake_settings(tmp_path)
    manager = LocalRunManager(
        settings=settings,
        process_factory=FakeProcessFactory(FakeProcess()),
    )
    manager.launch(manifest_path)
    manifest = load_run_manifest(manifest_path)
    execution = manifest.execution.model_copy(update={"process_id": None})
    write_run_manifest(manifest_path, manifest.model_copy(update={"execution": execution}))
    monkeypatch.setattr(
        "cloud_chamber.local_run_manager._command_process_may_be_running",
        lambda _command: False,
    )

    restarted_manager = LocalRunManager(
        settings=settings,
        process_factory=FakeProcessFactory(FakeProcess()),
    )
    status = restarted_manager.status(manifest_path)

    assert status.lifecycle_state == LifecycleState.FAILED
    manifest = load_run_manifest(manifest_path)
    assert manifest.lifecycle_state == LifecycleState.FAILED
    assert manifest.outputs.runtime_warnings == [
        "Running CM1 manifest has no tracked process id, no matching cm1 process was "
        "found, and no normal completion marker was found; marking the run failed so "
        "the serial queue can continue."
    ]


def test_exit_zero_with_dat_ctl_outputs_marks_completed_result(tmp_path: Path) -> None:
    manifest_path = dry_run_manifest_path(tmp_path)
    run_dir = tmp_path / "CloudChamber" / "runs" / "run-001"
    fake_process = FakeProcess()
    manager = LocalRunManager(
        settings=fake_settings(tmp_path),
        process_factory=FakeProcessFactory(fake_process),
    )
    manager.launch(manifest_path)
    (run_dir / "cm1out_000001_s.dat").write_text("fake scalar output")
    (run_dir / "cm1out_s.ctl").write_text("fake descriptor")
    (run_dir / "cm1out_stats.dat").write_text("fake stats")
    (run_dir / "cm1out_metadata.ctl").write_text("fake metadata descriptor")

    fake_process.exit_code = 0
    status = manager.status(manifest_path)

    assert status.lifecycle_state == LifecycleState.COMPLETED
    manifest = load_run_manifest(manifest_path)
    assert manifest.validation_status.value == "valid"
    assert manifest.provenance.product_state == ProductState.COMPLETED_CM1_RESULT
    assert manifest.outputs.netcdf_paths == []
    assert manifest.outputs.raw_cm1_artifacts == [
        str(run_dir / "cm1out_000001_s.dat"),
        str(run_dir / "cm1out_metadata.ctl"),
        str(run_dir / "cm1out_s.ctl"),
        str(run_dir / "cm1out_stats.dat"),
    ]


def test_exit_zero_surfaces_stderr_floating_point_warnings(tmp_path: Path) -> None:
    manifest_path = dry_run_manifest_path(tmp_path)
    run_dir = tmp_path / "CloudChamber" / "runs" / "run-001"
    fake_process = FakeProcess()
    manager = LocalRunManager(
        settings=fake_settings(tmp_path),
        process_factory=FakeProcessFactory(
            fake_process,
            stderr_text=(
                "Note: IEEE_INVALID_FLAG IEEE_DIVIDE_BY_ZERO "
                "IEEE_OVERFLOW_FLAG IEEE_UNDERFLOW_FLAG\n"
            ),
        ),
    )
    manager.launch(manifest_path)
    (run_dir / "cm1out_000001_s.dat").write_text("fake scalar output")

    fake_process.exit_code = 0
    manager.status(manifest_path)

    manifest = load_run_manifest(manifest_path)
    assert manifest.outputs.runtime_warnings == [
        "CM1 stderr reported floating-point exception flags: "
        "IEEE_INVALID_FLAG, IEEE_DIVIDE_BY_ZERO, "
        "IEEE_OVERFLOW_FLAG, IEEE_UNDERFLOW_FLAG"
    ]


def test_failed_process_updates_manifest_state(tmp_path: Path) -> None:
    manifest_path = dry_run_manifest_path(tmp_path)
    fake_process = FakeProcess()
    manager = LocalRunManager(
        settings=fake_settings(tmp_path),
        process_factory=FakeProcessFactory(fake_process),
    )
    manager.launch(manifest_path)

    fake_process.exit_code = 2
    status = manager.status(manifest_path)

    assert status.lifecycle_state == LifecycleState.FAILED
    assert status.exit_code == 2
    manifest = load_run_manifest(manifest_path)
    assert manifest.validation_status.value == "failed"
    assert manifest.provenance.product_state == ProductState.FAILED_CANCELED_CM1_RUN


def test_cancel_updates_state_and_terminates_process(tmp_path: Path) -> None:
    manifest_path = dry_run_manifest_path(tmp_path)
    fake_process = FakeProcess()
    manager = LocalRunManager(
        settings=fake_settings(tmp_path),
        process_factory=FakeProcessFactory(fake_process),
    )
    manager.launch(manifest_path)

    status = manager.cancel()

    assert fake_process.terminated
    assert status.lifecycle_state == LifecycleState.CANCELED
    assert status.exit_code == -15
    manifest = load_run_manifest(manifest_path)
    assert manifest.lifecycle_state == LifecycleState.CANCELED
    assert manifest.provenance.product_state == ProductState.FAILED_CANCELED_CM1_RUN


def test_manager_allows_only_one_active_local_run(tmp_path: Path) -> None:
    fake_process = FakeProcess()
    manager = LocalRunManager(
        settings=fake_settings(tmp_path),
        process_factory=FakeProcessFactory(fake_process),
    )
    manager.launch(dry_run_manifest_path(tmp_path, "run-001"))

    with pytest.raises(LocalRunManagerError, match="already active"):
        manager.launch(dry_run_manifest_path(tmp_path, "run-002"))


def test_launch_refuses_missing_cm1_settings(tmp_path: Path) -> None:
    settings = CloudChamberSettings(
        runtime_home=tmp_path / "CloudChamber",
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "CloudChamber" / "cache",
        log_dir=tmp_path / "CloudChamber" / "logs",
    )
    manager = LocalRunManager(settings=settings)

    with pytest.raises(LocalRunManagerError, match="CM1 is not ready"):
        manager.launch(dry_run_manifest_path(tmp_path))


def test_launch_refuses_existing_output_like_files(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = dry_run_manifest_path(tmp_path)
    run_dir = tmp_path / "CloudChamber" / "runs" / "run-001"
    (run_dir / "cm1out_000001.nc").write_text("local output placeholder")
    manager = LocalRunManager(settings=settings)

    with pytest.raises(LocalRunManagerError, match="output-like files already exist"):
        manager.launch(manifest_path)


def test_launch_refuses_placeholder_only_inputs(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = dry_run_manifest_path(tmp_path)
    run_dir = tmp_path / "CloudChamber" / "runs" / "run-001"
    (run_dir / "namelist.input").write_text(
        "# Status: placeholder until local/manual CM1 validation\n&cloud_chamber_domain\n/\n"
    )
    manager = LocalRunManager(settings=settings)

    with pytest.raises(LocalRunManagerError, match="placeholder-only CM1 input"):
        manager.launch(manifest_path)


def test_launch_refuses_rayleigh_damping_over_half_domain(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = dry_run_manifest_path(tmp_path)
    run_dir = tmp_path / "CloudChamber" / "runs" / "run-001"
    namelist = (run_dir / "namelist.input").read_text()
    (run_dir / "namelist.input").write_text(
        namelist.replace("ztop      = 18000.0,", "ztop      =  6000.0,").replace(
            "zd      =  12000.0,", "zd      =  2500.0,"
        )
    )
    manager = LocalRunManager(settings=settings)

    with pytest.raises(LocalRunManagerError, match="Rayleigh damping starts too low"):
        manager.launch(manifest_path)


def test_launch_refuses_tall_domain_with_low_rayleigh_damping_start(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = dry_run_manifest_path(tmp_path)
    run_dir = tmp_path / "CloudChamber" / "runs" / "run-001"
    namelist = (run_dir / "namelist.input").read_text()
    (run_dir / "namelist.input").write_text(
        namelist.replace("zd      =  12000.0,", "zd      =  2500.0,")
    )
    manager = LocalRunManager(settings=settings)

    with pytest.raises(LocalRunManagerError, match="Rayleigh damping starts too low"):
        manager.launch(manifest_path)


def test_launch_reports_missing_runtime_file(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    assert settings.cm1_run_dir is not None
    (settings.cm1_run_dir / "LANDUSE.TBL").unlink()
    (settings.cm1_run_dir / "config_files" / "les_ShallowCu" / "LANDUSE.TBL").unlink()
    manifest_path = dry_run_manifest_path(tmp_path)
    manager = LocalRunManager(settings=settings)

    with pytest.raises(LocalRunManagerError, match="Required CM1 runtime file is missing"):
        manager.launch(manifest_path)
