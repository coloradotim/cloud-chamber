from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "lan_worker_run.py"


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("lan_worker_run", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_package(tmp_path: Path, run_id: str = "dry-run-test") -> Path:
    package_dir = tmp_path / "CloudChamber" / "runs" / run_id
    package_dir.mkdir(parents=True)
    manifest = {
        "run_id": run_id,
        "execution": {"command": [], "exit_code": None},
        "outputs": {
            "netcdf_paths": [],
            "raw_cm1_artifacts": [],
            "runtime_warnings": [],
        },
        "provenance": {"product_state": "packaged_dry_run_output"},
        "lifecycle_state": "packaged",
        "validation_status": "unvalidated",
    }
    (package_dir / "run_manifest.json").write_text(json.dumps(manifest))
    for name in (
        "case_manifest.json",
        "runtime_file_checklist.json",
        "dry_run_report.json",
    ):
        (package_dir / name).write_text("{}")
    (package_dir / "namelist.input").write_text("&param\n/")
    (package_dir / "input_sounding").write_text("0 0 0\n")
    return package_dir


def worker_config(module: ModuleType) -> object:
    return module.WorkerConfig(
        host="worker.example",
        worker_root="/srv/cloud-chamber-worker",
        cm1_exe="/opt/cm1/run/cm1.exe",
    )


def test_validate_package_rejects_package_outside_runtime_home(tmp_path: Path) -> None:
    module = load_script()
    package_dir = make_package(tmp_path)

    with pytest.raises(module.LanWorkerError, match="outside runtime runs directory"):
        module.validate_package(
            str(package_dir),
            str(tmp_path / "OtherCloudChamber"),
        )


def test_worker_config_loads_from_local_json_file(tmp_path: Path) -> None:
    module = load_script()
    config_path = tmp_path / "lan-worker.json"
    config_path.write_text(
        json.dumps(
            {
                "host": "worker.example",
                "worker_root": "/srv/cloud-chamber-worker",
                "cm1_exe": "/opt/cm1/run/cm1.exe",
                "cm1_env": {"OMP_NUM_THREADS": "16"},
            }
        )
    )

    config = module.load_worker_config(env={}, config_path=str(config_path))

    assert config.host == "worker.example"
    assert config.worker_root == "/srv/cloud-chamber-worker"
    assert config.cm1_exe == "/opt/cm1/run/cm1.exe"
    assert config.cm1_env == {"OMP_NUM_THREADS": "16"}
    assert config.ssh_command == ("ssh",)
    assert config.rsync_command == ("rsync",)


def test_worker_config_supports_custom_launch_command(tmp_path: Path) -> None:
    module = load_script()
    config_path = tmp_path / "lan-worker.json"
    config_path.write_text(
        json.dumps(
            {
                "host": "worker.example",
                "worker_root": "/srv/cloud-chamber-worker",
                "cm1_exe": "/opt/cm1/run/cm1.exe",
                "cm1_command": "mpirun -np 4 /opt/cm1/run/cm1.exe",
            }
        )
    )

    config = module.load_worker_config(env={}, config_path=str(config_path))

    assert config.cm1_exe == "/opt/cm1/run/cm1.exe"
    assert config.cm1_command == "mpirun -np 4 /opt/cm1/run/cm1.exe"


def test_worker_config_env_overrides_local_json_file(tmp_path: Path) -> None:
    module = load_script()
    config_path = tmp_path / "lan-worker.json"
    config_path.write_text(
        json.dumps(
            {
                "host": "file-worker.example",
                "worker_root": "/srv/file-worker",
                "cm1_exe": "/opt/file-cm1/run/cm1.exe",
            }
        )
    )

    config = module.load_worker_config(
        env={
            "CLOUD_CHAMBER_LAN_WORKER_HOST": "env-worker.example",
            "CLOUD_CHAMBER_LAN_WORKER_ROOT": "/srv/env-worker",
            "CLOUD_CHAMBER_LAN_WORKER_CM1_EXE": "/opt/env-cm1/run/cm1.exe",
        },
        config_path=str(config_path),
    )

    assert config.host == "env-worker.example"
    assert config.worker_root == "/srv/env-worker"
    assert config.cm1_exe == "/opt/env-cm1/run/cm1.exe"


@pytest.mark.parametrize("run_id", ["", "..", "dry-run/escape", "dry-run\\escape", ".hidden"])
def test_cleanup_rejects_unsafe_run_ids(run_id: str) -> None:
    module = load_script()

    with pytest.raises(module.LanWorkerError):
        module.safe_remote_run_dir(worker_config(module), run_id)


def test_cleanup_rejects_worker_runs_inside_cm1_install() -> None:
    module = load_script()
    config = module.WorkerConfig(
        host="worker.example",
        worker_root="/opt/cm1/run",
        cm1_exe="/opt/cm1/run/cm1.exe",
    )

    with pytest.raises(module.LanWorkerError, match="inside CM1 install directory"):
        module.safe_remote_run_dir(config, "dry-run-test")


def test_cleanup_remote_command_is_idempotent() -> None:
    module = load_script()

    command = module.build_cleanup_remote_command("/srv/cloud-chamber-worker/runs/dry-run-test")

    assert "[ ! -e" in command
    assert "already_removed" in command
    assert "rm -rf --" in command
    assert "worker_cleanup_complete" in command


def test_worker_runner_exports_and_records_cm1_environment() -> None:
    module = load_script()

    runner = module.render_worker_runner(
        "dry-run-test",
        "/opt/cm1/run/cm1.exe",
        "/opt/cm1/run/cm1.exe",
        {"OMP_NUM_THREADS": "16"},
    )

    assert "CM1_ENV_JSON=" in runner
    assert "export {key}=" in runner
    assert '"cm1_env": json.loads(cm1_env_json or "{}")' in runner
    assert 'bash -lc "$CM1_COMMAND"' in runner


def test_worker_status_parses_cm1_command_and_environment() -> None:
    module = load_script()

    status = module.worker_status_from_mapping(
        {
            "run_id": "dry-run-test",
            "state": "completed",
            "cm1_exe": "/opt/cm1/run/cm1.exe",
            "cm1_command": "mpirun -np 4 /opt/cm1/run/cm1.exe",
            "cm1_env": {"OMP_NUM_THREADS": "4"},
            "progress": {
                "model_time_seconds": 7200,
                "total_model_time_seconds": 10800,
                "percent_complete": 66.7,
            },
        }
    )

    assert status.cm1_command == "mpirun -np 4 /opt/cm1/run/cm1.exe"
    assert status.cm1_env == {"OMP_NUM_THREADS": "4"}
    assert status.progress == {
        "model_time_seconds": 7200,
        "total_model_time_seconds": 10800,
        "percent_complete": 66.7,
    }


def test_cleanup_already_removed_updates_local_worker_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_script()
    package_dir = make_package(tmp_path)
    (package_dir / "worker_status.json").write_text(
        json.dumps({"run_id": "dry-run-test", "state": "ready_for_local_ingest"})
    )

    def fake_run_command(
        command: tuple[str, ...], *, capture: bool = False
    ) -> subprocess.CompletedProcess[str]:
        assert command[-1].startswith("if [ ! -e")
        assert capture is True
        return subprocess.CompletedProcess(command, 0, stdout="already_removed\n", stderr="")

    monkeypatch.setattr(module, "run_command", fake_run_command)
    monkeypatch.setattr(module, "load_worker_config", lambda **kwargs: worker_config(module))

    module.cleanup_worker_run(
        argparse.Namespace(
            package_dir=str(package_dir),
            run_id=None,
            runtime_home=str(tmp_path / "CloudChamber"),
            worker_config=None,
        )
    )

    status = json.loads((package_dir / "worker_status.json").read_text())
    assert status["state"] == "worker_cleanup_complete"
    assert status["previous_state"] == "ready_for_local_ingest"
    assert "already removed" in status["message"]


def test_cleanup_failure_marks_worker_cleanup_failed_without_changing_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_script()
    package_dir = make_package(tmp_path)
    original_manifest = (package_dir / "run_manifest.json").read_text()
    (package_dir / "worker_status.json").write_text(
        json.dumps({"run_id": "dry-run-test", "state": "ready_for_local_ingest"})
    )

    def fake_run_command(command: tuple[str, ...], *, capture: bool = False) -> object:
        raise module.LanWorkerError("remote delete failed")

    monkeypatch.setattr(module, "run_command", fake_run_command)
    monkeypatch.setattr(module, "load_worker_config", lambda **kwargs: worker_config(module))

    with pytest.raises(module.LanWorkerError, match="remote delete failed"):
        module.cleanup_worker_run(
            argparse.Namespace(
                package_dir=str(package_dir),
                run_id=None,
                runtime_home=str(tmp_path / "CloudChamber"),
                worker_config=None,
            )
        )

    assert (package_dir / "run_manifest.json").read_text() == original_manifest
    status = json.loads((package_dir / "worker_status.json").read_text())
    assert status["state"] == "worker_cleanup_failed"
    assert status["previous_state"] == "ready_for_local_ingest"
    assert "can be retried" in status["message"]
