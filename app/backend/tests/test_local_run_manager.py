import json
from pathlib import Path
from typing import TextIO

import pytest

from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.local_run_manager import LocalRunManager, LocalRunManagerError
from cloud_chamber.run_manifest import LifecycleState, ProductState, load_run_manifest
from cloud_chamber.settings import CloudChamberSettings

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"


class FakeProcess:
    def __init__(self) -> None:
        self.exit_code: int | None = None
        self.terminated = False

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
    def __init__(self, process: FakeProcess) -> None:
        self.process = process
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
        stderr.write("fake cm1 stderr\n")
        stderr.flush()
        return self.process


def load_baseline_template() -> object:
    return json.loads(BASELINE_TEMPLATE.read_text())


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    cm1_root = tmp_path / "cm1"
    cm1_run_dir = cm1_root / "run"
    cm1_run_dir.mkdir(parents=True)
    (cm1_run_dir / "cm1.exe").write_text("# fake executable\n")
    (cm1_run_dir / "LANDUSE.TBL").write_text("fake local runtime file\n")
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
    assert (factory.cwd / "LANDUSE.TBL").read_text() == "fake local runtime file\n"

    manifest = load_run_manifest(manifest_path)
    assert manifest.lifecycle_state == LifecycleState.RUNNING
    assert manifest.provenance.product_state == ProductState.QUEUED_RUNNING_CM1_PROCESS
    assert manifest.execution.command == [str(settings.cm1_run_dir / "cm1.exe")]


def test_completed_process_updates_manifest_state(tmp_path: Path) -> None:
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
    assert manifest.provenance.product_state == ProductState.COMPLETED_CM1_RESULT


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


def test_launch_reports_missing_runtime_file(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    assert settings.cm1_run_dir is not None
    (settings.cm1_run_dir / "LANDUSE.TBL").unlink()
    manifest_path = dry_run_manifest_path(tmp_path)
    manager = LocalRunManager(settings=settings)

    with pytest.raises(LocalRunManagerError, match="Required CM1 runtime file is missing"):
        manager.launch(manifest_path)
