from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cloud_chamber.app import app
from cloud_chamber.local_run_manager import LocalRunManagerError, RunStatus
from cloud_chamber.run_manifest import LifecycleState


class FakeRunManager:
    def __init__(self, status: RunStatus | None = None, error: Exception | None = None) -> None:
        self.fake_status = status or RunStatus(
            run_id="run-001",
            lifecycle_state=LifecycleState.RUNNING,
            manifest_path=Path("/tmp/run_manifest.json"),
            command=("/tmp/cm1/run/cm1.exe",),
            stdout_log=Path("/tmp/stdout.log"),
            stderr_log=Path("/tmp/stderr.log"),
            exit_code=None,
        )
        self.error = error
        self.launched_manifest_path: Path | None = None

    def launch(self, manifest_path: Path) -> RunStatus:
        if self.error:
            raise self.error
        self.launched_manifest_path = manifest_path
        return self.fake_status

    def status(self, manifest_path: Path) -> RunStatus:
        if self.error:
            raise self.error
        self.launched_manifest_path = manifest_path
        return self.fake_status

    def cancel(self) -> RunStatus:
        if self.error:
            raise self.error
        return self.fake_status


def test_health_endpoint_identifies_scaffold_without_cm1() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["product"] == "Cloud Chamber"
    assert "CM1 is the high-fidelity simulation engine" in response.json()["engine_note"]


def test_list_scenarios_includes_baseline_golden_path() -> None:
    response = TestClient(app).get("/api/scenarios")

    assert response.status_code == 200
    payload = response.json()
    assert payload["golden_path_scenario_id"] == "baseline-shallow-cumulus"
    baseline = next(
        scenario
        for scenario in payload["scenarios"]
        if scenario["id"] == "baseline-shallow-cumulus"
    )
    assert baseline["display_name"] == "Baseline Shallow Cumulus"
    assert "physical_question" in baseline
    assert [control["id"] for control in baseline["controls"]] == [
        "low_level_humidity",
        "surface_heating",
        "cap_strength",
    ]


def test_create_dry_run_package_api_uses_runtime_home_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(tmp_path))
    response = TestClient(app).post(
        "/api/dry-run-package",
        json={
            "scenario_id": "baseline-shallow-cumulus",
            "controls": {"low_level_humidity": "more_humid"},
            "run_size_preset": "quick_look",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["package_dir"].startswith(str(tmp_path))
    assert payload["report"]["scenario_id"] == "baseline-shallow-cumulus"
    assert payload["report"]["controls"]["low_level_humidity"] == "more_humid"
    assert payload["report"]["not_a_completed_cm1_result"] is True
    assert payload["report"]["cm1_was_launched"] is False
    assert not list(tmp_path.glob("**/*.nc"))


def test_launch_run_api_returns_status(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_manager = FakeRunManager()
    monkeypatch.setattr("cloud_chamber.app._local_run_manager", fake_manager)

    response = TestClient(app).post(
        "/api/runs/launch",
        json={"manifest_path": "/tmp/run_manifest.json"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-001"
    assert payload["lifecycle_state"] == "running"
    assert payload["command"] == ["/tmp/cm1/run/cm1.exe"]
    assert fake_manager.launched_manifest_path == Path("/tmp/run_manifest.json")


def test_launch_run_api_reports_clear_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cloud_chamber.app._local_run_manager",
        FakeRunManager(error=LocalRunManagerError("CM1 is not ready")),
    )

    response = TestClient(app).post(
        "/api/runs/launch",
        json={"manifest_path": "/tmp/run_manifest.json"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "CM1 is not ready"


def test_storage_inventory_api_uses_runtime_home_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(tmp_path))
    run_dir = tmp_path / "runs" / "manual-run"
    run_dir.mkdir(parents=True)
    (run_dir / "cm1out_s.ctl").write_text("fake descriptor")

    response = TestClient(app).get("/api/storage/inventory")

    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime_home"] == str(tmp_path)
    assert payload["warning_threshold_bytes"] == 50 * 1024**3
    assert payload["above_warning_threshold"] is False
    assert payload["runs"][0]["run_id"] == "manual-run"
    assert payload["runs"][0]["category"] == "missing_manifest"


def test_storage_delete_run_api_requires_explicit_confirm(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(tmp_path))
    run_dir = tmp_path / "runs" / "manual-run"
    run_dir.mkdir(parents=True)
    (run_dir / "cm1out_s.ctl").write_text("fake descriptor")

    preview = TestClient(app).post(
        "/api/storage/delete-run",
        json={"run_id": "manual-run", "dry_run": True, "confirm": False},
    )
    blocked = TestClient(app).post(
        "/api/storage/delete-run",
        json={"run_id": "manual-run", "dry_run": False, "confirm": False},
    )
    assert preview.status_code == 200
    assert preview.json()["deleted"] is False
    assert run_dir.exists()
    assert blocked.status_code == 400
    assert blocked.json()["detail"] == "Real delete requires confirm=true."
    assert run_dir.exists()

    deleted = TestClient(app).post(
        "/api/storage/delete-run",
        json={"run_id": "manual-run", "dry_run": False, "confirm": True},
    )

    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert not run_dir.exists()
