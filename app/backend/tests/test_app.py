import json
from pathlib import Path

import pytest
import xarray as xr
from fastapi.testclient import TestClient
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.app import app
from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.local_run_manager import LocalRunManagerError, RunStatus
from cloud_chamber.run_manifest import (
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    load_run_manifest,
    write_run_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"


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


def test_parse_observed_sounding_api_returns_igra_review_payload() -> None:
    response = TestClient(app).post(
        "/api/observed-soundings/parse",
        json={
            "uploaded_filename": "USM00072558-data-beg2025.txt",
            "text": IGRA_FIXTURE,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_provider"] == "NOAA/NCEI IGRA"
    assert len(payload["available_soundings"]) == 2
    selected = payload["selected_sounding"]
    assert selected["station_id"] == "USM00072558"
    assert selected["station_name"] == "Valley, Nebraska"
    assert selected["model_bottom_elevation_m_msl"] == pytest.approx(351.5)
    assert selected["source_vertical_coordinate_type"] == "geopotential_height_msl"
    assert selected["levels"][0]["model_z_m"] == pytest.approx(0.5)
    assert selected["levels"][-1]["model_z_m"] > 18000
    assert "metadata_only" in selected["wind_handling"]


def test_parse_observed_sounding_api_blocks_malformed_upload() -> None:
    response = TestClient(app).post(
        "/api/observed-soundings/parse",
        json={"uploaded_filename": "not-igra.txt", "text": "not a sounding"},
    )

    assert response.status_code == 400
    assert "No IGRA sounding headers" in response.json()["detail"]


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


def test_lan_worker_config_endpoint_returns_sanitized_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cloud_chamber.app.lan_worker_config_status",
        lambda: {
            "configured": True,
            "available": True,
            "message": "Trusted LAN worker is configured.",
            "cm1_env_keys": ["OMP_NUM_THREADS"],
            "cm1_env_settings": ["OMP_NUM_THREADS=16"],
            "custom_launch_command": False,
        },
    )

    response = TestClient(app).get("/api/lan-worker/config")

    assert response.status_code == 200
    assert response.json() == {
        "configured": True,
        "available": True,
        "message": "Trusted LAN worker is configured.",
        "cm1_env_keys": ["OMP_NUM_THREADS"],
        "cm1_env_settings": ["OMP_NUM_THREADS=16"],
        "custom_launch_command": False,
    }


def test_lan_worker_run_endpoints_surface_worker_states(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, Path]] = []

    def fake_start(_settings: object, manifest_path: Path) -> dict[str, object]:
        calls.append(("start", manifest_path))
        return {
            "run_id": "dry-run-worker",
            "state": "running",
            "message": "Package copied to the LAN worker and CM1 launch was requested.",
        }

    def fake_status(_settings: object, manifest_path: Path) -> dict[str, object]:
        calls.append(("status", manifest_path))
        return {
            "run_id": "dry-run-worker",
            "state": "completed",
            "exit_code": 0,
            "netcdf_count": 13,
            "raw_artifact_count": 0,
            "message": "CM1 completed with output artifacts.",
        }

    def fake_collect(_settings: object, manifest_path: Path) -> dict[str, object]:
        calls.append(("collect", manifest_path))
        return {
            "run_id": "dry-run-worker",
            "state": "ready_for_local_ingest",
            "ready_for_ingest": True,
            "local_package_dir": "/tmp/CloudChamber/runs/dry-run-worker",
            "message": "Completed LAN worker output was copied back.",
        }

    def fake_cleanup(_settings: object, manifest_path: Path) -> dict[str, object]:
        calls.append(("cleanup", manifest_path))
        return {
            "run_id": "dry-run-worker",
            "state": "worker_cleanup_complete",
            "message": "LAN worker run directory was removed.",
        }

    monkeypatch.setattr("cloud_chamber.app.start_lan_worker_run", fake_start)
    monkeypatch.setattr("cloud_chamber.app.lan_worker_run_status", fake_status)
    monkeypatch.setattr("cloud_chamber.app.collect_lan_worker_run", fake_collect)
    monkeypatch.setattr("cloud_chamber.app.cleanup_lan_worker_run", fake_cleanup)
    client = TestClient(app)

    start = client.post(
        "/api/lan-worker/start",
        json={"manifest_path": "/tmp/CloudChamber/runs/dry-run-worker/run_manifest.json"},
    )
    status = client.get(
        "/api/lan-worker/status",
        params={"manifest_path": "/tmp/CloudChamber/runs/dry-run-worker/run_manifest.json"},
    )
    collect = client.post(
        "/api/lan-worker/collect",
        json={"manifest_path": "/tmp/CloudChamber/runs/dry-run-worker/run_manifest.json"},
    )
    cleanup = client.post(
        "/api/lan-worker/cleanup",
        json={"manifest_path": "/tmp/CloudChamber/runs/dry-run-worker/run_manifest.json"},
    )

    assert start.status_code == 200
    assert start.json()["state"] == "running"
    assert status.status_code == 200
    assert status.json()["state"] == "completed"
    assert status.json()["netcdf_count"] == 13
    assert collect.status_code == 200
    assert collect.json()["state"] == "ready_for_local_ingest"
    assert cleanup.status_code == 200
    assert cleanup.json()["state"] == "worker_cleanup_complete"
    assert [call[0] for call in calls] == ["start", "status", "collect", "cleanup"]


def test_lan_worker_endpoint_reports_clear_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from cloud_chamber.lan_worker import LanWorkerApiError

    def fake_start(_settings: object, _manifest_path: Path) -> dict[str, object]:
        raise LanWorkerApiError("LAN worker SSH failed")

    monkeypatch.setattr("cloud_chamber.app.start_lan_worker_run", fake_start)

    response = TestClient(app).post(
        "/api/lan-worker/start",
        json={"manifest_path": "/tmp/CloudChamber/runs/dry-run-worker/run_manifest.json"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "LAN worker SSH failed"


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


def test_results_ingest_and_lookup_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(tmp_path / "CloudChamber"))
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path / "CloudChamber",
        run_id="run-api-ingest",
    )
    netcdf_path = package.package_dir / "cm1out_000001.nc"
    xr.Dataset(
        data_vars={
            "qc": (
                ("time", "z", "y", "x"),
                [[[[0.0]]]],
                {"units": "kg/kg"},
            ),
            "w": (
                ("time", "z", "y", "x"),
                [[[[1.0]]]],
                {"units": "m/s"},
            ),
        },
        coords={"time": [0.0], "z": [125.0], "y": [0.0], "x": [0.0]},
    ).to_netcdf(netcdf_path, engine="scipy")
    manifest = load_run_manifest(package.manifest_path)
    write_run_manifest(
        package.manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.COMPLETED,
                "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
                "outputs": OutputMetadata(netcdf_paths=[str(netcdf_path)]),
            }
        ),
    )

    ingest_response = TestClient(app).post(
        "/api/results/ingest",
        json={"manifest_path": str(package.manifest_path)},
    )
    list_response = TestClient(app).get("/api/results")
    get_response = TestClient(app).get("/api/results/result-run-api-ingest")

    assert ingest_response.status_code == 200
    assert ingest_response.json()["result_id"] == "result-run-api-ingest"
    assert ingest_response.json()["variables"] == ["qc", "w"]
    assert list_response.status_code == 200
    assert [result["result_id"] for result in list_response.json()["results"]] == [
        "result-run-api-ingest"
    ]
    assert list_response.json()["results"][0]["output_file_summary"]["model_output_count"] == 1
    assert get_response.status_code == 200
    assert get_response.json()["run_id"] == "run-api-ingest"
    assert get_response.json()["saved"] is False


def test_result_card_update_and_save_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(tmp_path / "CloudChamber"))
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path / "CloudChamber",
        run_id="run-api-card",
    )
    netcdf_path = package.package_dir / "cm1out_000001.nc"
    xr.Dataset(
        data_vars={
            "qc": (
                ("time", "z", "y", "x"),
                [[[[2e-6 for _x in range(4)] for _y in range(3)] for _z in range(2)]],
                {"units": "kg/kg"},
            ),
            "w": (
                ("time", "z", "y", "x"),
                [[[[1.0, 2.0, 3.0, 4.0] for _y in range(3)] for _z in range(2)]],
                {"units": "m/s"},
            ),
        },
        coords={
            "time": [1800.0],
            "z": [0.54, 1.94],
            "y": [0.0, 100.0, 200.0],
            "x": [0.0, 100.0, 200.0, 300.0],
        },
    ).to_netcdf(netcdf_path, engine="scipy")
    manifest = load_run_manifest(package.manifest_path)
    write_run_manifest(
        package.manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.COMPLETED,
                "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
                "outputs": OutputMetadata(netcdf_paths=[str(netcdf_path)]),
            }
        ),
    )
    client = TestClient(app)
    ingest_response = client.post(
        "/api/results/ingest",
        json={"manifest_path": str(package.manifest_path)},
    )
    result_id = ingest_response.json()["result_id"]

    patch_response = client.patch(
        f"/api/results/{result_id}",
        json={
            "name": "API notebook card",
            "tags": ["saved", "baseline"],
            "notes": "Opened after ingest.",
        },
    )
    save_response = client.post(f"/api/results/{result_id}/save")

    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "API notebook card"
    assert patch_response.json()["tags"] == ["saved", "baseline"]
    assert patch_response.json()["notes"] == "Opened after ingest."
    assert patch_response.json()["first_cloud_time_seconds"] == 1800.0
    assert patch_response.json()["max_qc_kg_kg"] == 2e-6
    assert patch_response.json()["max_w_m_s"] == 4.0
    assert patch_response.json()["min_w_m_s"] == 1.0
    assert save_response.status_code == 200
    assert save_response.json()["saved"] is True
    assert save_response.json()["protected"] is True
