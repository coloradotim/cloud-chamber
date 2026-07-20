import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import xarray as xr
from fastapi.testclient import TestClient
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.app import app
from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.igra_catalog import (
    IGRACacheEntry,
    IGRACatalogError,
    IGRARecentCatalog,
    IGRARegionDefinition,
    IGRAStationZipReference,
)
from cloud_chamber.local_run_manager import LocalRunManagerError, RunStatus
from cloud_chamber.local_run_queue import RunQueueEntry, RunQueueState
from cloud_chamber.observed_sounding import parse_igra_station_text
from cloud_chamber.run_manifest import (
    ExecutionMetadata,
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


class FakeRunQueue:
    def __init__(self) -> None:
        self.enqueued_manifest_path: Path | None = None

    def enqueue(self, manifest_path: Path) -> RunQueueState:
        self.enqueued_manifest_path = manifest_path
        return fake_queue_state("run-queued", "running")

    def refresh(self) -> RunQueueState:
        return fake_queue_state("run-queued", "running")


def fake_queue_state(run_id: str, state: str) -> RunQueueState:
    return RunQueueState(
        entries=[
            RunQueueEntry(
                run_id=run_id,
                manifest_path="/tmp/run_manifest.json",
                state=state,
                queued_at="2026-05-22T15:15:36Z",
                started_at="2026-05-22T15:15:37Z",
                updated_at="2026-05-22T15:15:37Z",
                message="Running local CM1 process.",
            )
        ],
        active_run_id=run_id if state == "running" else None,
        queued_count=0,
        updated_at="2026-05-22T15:15:37Z",
    )


def test_health_endpoint_identifies_scaffold_without_cm1() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["product"] == "Cloud Chamber"
    assert "CM1 is the high-fidelity simulation engine" in response.json()["engine_note"]


def test_trade_cumulus_updraft_lens_defaults_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def model_dump(self, *, mode: str) -> dict[str, object]:
            assert mode == "json"
            return {
                "result_id": "result-bomex",
                "eligible": True,
                "default_time_index": 61,
                "default_plane_index": 5,
            }

    monkeypatch.setattr(
        "cloud_chamber.app.trade_cumulus_updraft_lens_defaults",
        lambda _settings, result_id: FakeResponse(),
    )

    response = TestClient(app).get(
        "/api/results/result-bomex/visualization/trade-cumulus-updraft-lens/defaults"
    )

    assert response.status_code == 200
    assert response.json() == {
        "result_id": "result-bomex",
        "eligible": True,
        "default_time_index": 61,
        "default_plane_index": 5,
    }


def test_trade_cumulus_updraft_lens_frame_endpoint_validates_and_forwards_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: dict[str, object] = {}

    class FakeResponse:
        def model_dump(self, *, mode: str) -> dict[str, object]:
            assert mode == "json"
            return {"result_id": "result-bomex", "wind_mode": "total"}

    def fake_frame(
        _settings: object,
        result_id: str,
        *,
        time_index: int,
        orientation: str,
        plane_index: int,
        wind_mode: str,
    ) -> FakeResponse:
        received.update(
            result_id=result_id,
            time_index=time_index,
            orientation=orientation,
            plane_index=plane_index,
            wind_mode=wind_mode,
        )
        return FakeResponse()

    monkeypatch.setattr("cloud_chamber.app.trade_cumulus_updraft_lens_frame", fake_frame)
    client = TestClient(app)

    response = client.get(
        "/api/results/result-bomex/visualization/trade-cumulus-updraft-lens/frame"
        "?time_index=4&plane_index=3&orientation=vertical_y&wind_mode=total"
    )
    invalid = client.get(
        "/api/results/result-bomex/visualization/trade-cumulus-updraft-lens/frame"
        "?time_index=4&plane_index=3&wind_mode=unsupported"
    )

    assert response.status_code == 200
    assert response.json()["wind_mode"] == "total"
    assert received == {
        "result_id": "result-bomex",
        "time_index": 4,
        "orientation": "vertical_y",
        "plane_index": 3,
        "wind_mode": "total",
    }
    assert invalid.status_code == 400

    invalid_orientation = client.get(
        "/api/results/result-bomex/visualization/trade-cumulus-updraft-lens/frame"
        "?time_index=4&plane_index=3&orientation=diagonal"
    )
    assert invalid_orientation.status_code == 400


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
            "run_configuration": {
                "duration": "short_6h",
                "horizontal_cell_count": "cells_128",
                "domain_size": "local_6km",
                "output_cadence": "standard_15min",
                "diagnostic_set": "process",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["package_dir"].startswith(str(tmp_path))
    assert payload["report"]["scenario_id"] == "baseline-shallow-cumulus"
    assert payload["report"]["controls"]["low_level_humidity"] == "more_humid"
    assert payload["report"]["not_a_completed_cm1_result"] is True
    assert payload["report"]["cm1_was_launched"] is False
    assert (
        payload["report"]["pre_run_validation_report"]["run_shape_validation"]["estimated_frames"]
        == 25
    )
    assert not list(tmp_path.glob("**/*.nc"))


def test_create_dry_run_package_api_returns_blocked_pre_run_validation_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(tmp_path))

    response = TestClient(app).post(
        "/api/dry-run-package",
        json={
            "scenario_id": "baseline-shallow-cumulus",
            "run_configuration": {
                "duration": "short_6h",
                "horizontal_cell_count": "cells_128",
                "domain_size": "not_a_real_domain",
                "output_cadence": "standard_15min",
                "diagnostic_set": "process",
            },
        },
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["message"] == "Unknown domain size: not_a_real_domain"
    report = detail["pre_run_validation_report"]
    assert report["status"] == "blocked"
    assert report["run_shape_validation"]["domain"] == "not_a_real_domain"
    assert not list(tmp_path.glob("runs/*"))


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
    assert "observed_sounding_winds" in selected["wind_handling"]


def test_parse_observed_sounding_api_blocks_malformed_upload() -> None:
    response = TestClient(app).post(
        "/api/observed-soundings/parse",
        json={"uploaded_filename": "not-igra.txt", "text": "not a sounding"},
    )

    assert response.status_code == 400
    assert "No IGRA sounding headers" in response.json()["detail"]


def test_igra_recent_catalog_endpoint_returns_cached_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = IGRARecentCatalog(
        source_url="https://example.test/igra/",
        station_metadata_source="https://example.test/stations.txt",
        region=IGRARegionDefinition(
            tag="great_plains_midwest",
            label="Great Plains / Midwest",
            min_latitude=35,
            max_latitude=50,
            min_longitude=-106,
            max_longitude=-82,
        ),
        refreshed_at=datetime(2026, 7, 1, tzinfo=UTC),
        stations=[],
        zip_references=[
            IGRAStationZipReference(
                station_id="USM00072558",
                filename="USM00072558-data-beg2025.txt.zip",
                begin_year=2025,
                source_url="https://example.test/USM00072558-data-beg2025.txt.zip",
                region_tags=["great_plains_midwest"],
            )
        ],
        cache_manifest_path="/tmp/cache/igra/recent/cache_manifest.json",
    )
    monkeypatch.setattr("cloud_chamber.app.read_igra_recent_catalog", lambda _settings: catalog)

    response = TestClient(app).get("/api/igra/recent/catalog")

    assert response.status_code == 200
    payload = response.json()
    assert payload["catalog"]["zip_references"][0]["station_id"] == "USM00072558"
    assert payload["catalog"]["zip_references"][0]["cached_status"] == "not_cached"


def test_igra_recent_cache_endpoint_reports_clear_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def blocked_cache(_settings: object, *, station_id: str, filename: str | None) -> object:
        raise IGRACatalogError(f"Requested file is not cached: {station_id} {filename}")

    monkeypatch.setattr("cloud_chamber.app.cache_station_zip_from_catalog", blocked_cache)

    response = TestClient(app).post(
        "/api/igra/recent/cache",
        json={"station_id": "USM00072558", "filename": "USM00072558-data-beg2025.txt.zip"},
    )

    assert response.status_code == 400
    assert "Requested file is not cached" in response.json()["detail"]


def test_igra_recent_batch_cache_endpoint_caches_bounded_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    catalog = IGRARecentCatalog(
        source_url="https://example.test/igra/",
        station_metadata_source="https://example.test/stations.txt",
        region=IGRARegionDefinition(
            tag="great_plains_midwest",
            label="Great Plains / Midwest",
            min_latitude=35,
            max_latitude=50,
            min_longitude=-106,
            max_longitude=-82,
        ),
        refreshed_at=datetime(2026, 7, 1, tzinfo=UTC),
        stations=[],
        zip_references=[
            IGRAStationZipReference(
                station_id="USM00072558",
                filename="USM00072558-data-beg2025.txt.zip",
                begin_year=2025,
                source_url="https://example.test/USM00072558-data-beg2025.txt.zip",
                region_tags=["great_plains_midwest"],
            ),
            IGRAStationZipReference(
                station_id="USM00072426",
                filename="USM00072426-data-beg2025.txt.zip",
                begin_year=2025,
                source_url="https://example.test/USM00072426-data-beg2025.txt.zip",
                region_tags=["great_plains_midwest"],
            ),
        ],
        cache_manifest_path=str(tmp_path / "cache_manifest.json"),
    )
    calls: list[tuple[str, str | None]] = []

    def fake_cache(
        _settings: object,
        *,
        station_id: str,
        filename: str | None,
    ) -> IGRACacheEntry:
        calls.append((station_id, filename))
        return IGRACacheEntry(
            station_id=station_id,
            filename=filename or f"{station_id}-data-beg2025.txt.zip",
            source_url=f"https://example.test/{filename}",
            region_tags=["great_plains_midwest"],
            cached_status="cached_extracted",
            cached_zip_path=str(tmp_path / (filename or f"{station_id}.zip")),
            cached_text_path=str(tmp_path / station_id / f"{station_id}-data.txt"),
            downloaded_at=datetime(2026, 7, 1, tzinfo=UTC),
            extracted_at=datetime(2026, 7, 1, tzinfo=UTC),
        )

    monkeypatch.setattr("cloud_chamber.app.read_igra_recent_catalog", lambda _settings: catalog)
    monkeypatch.setattr("cloud_chamber.app.cache_station_zip_from_catalog", fake_cache)

    response = TestClient(app).post("/api/igra/recent/cache-batch", json={"limit": 1})

    assert response.status_code == 200
    assert calls == [("USM00072558", "USM00072558-data-beg2025.txt.zip")]
    payload = response.json()
    assert payload["selected_count"] == 1
    assert payload["cached_entries"][0]["station_id"] == "USM00072558"
    assert payload["remaining_uncached_count"] == 1


def test_igra_recent_batch_cache_endpoint_rejects_invalid_limit() -> None:
    response = TestClient(app).post("/api/igra/recent/cache-batch", json={"limit": 0})

    assert response.status_code == 400
    assert "limit" in response.json()["detail"]


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


def test_run_status_api_reports_stdout_model_time_progress(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path / "CloudChamber",
        run_id="run-progress",
    )
    stdout_log = package.package_dir / "logs" / "stdout.log"
    stderr_log = package.package_dir / "logs" / "stderr.log"
    stdout_log.parent.mkdir()
    stdout_log.write_text("          592             48.700000 min \n")
    stderr_log.write_text("")
    manifest = load_run_manifest(package.manifest_path)
    started_at = datetime(2026, 5, 22, 15, 15, 36, tzinfo=UTC)
    write_run_manifest(
        package.manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.RUNNING,
                "provenance": ProvenanceMetadata(
                    product_state=ProductState.QUEUED_RUNNING_CM1_PROCESS
                ),
                "execution": ExecutionMetadata(
                    command=["/tmp/cm1/run/cm1.exe"],
                    started_at=started_at,
                    stdout_log=str(stdout_log),
                    stderr_log=str(stderr_log),
                ),
            }
        ),
    )
    fake_manager = FakeRunManager(
        RunStatus(
            run_id="run-progress",
            lifecycle_state=LifecycleState.RUNNING,
            manifest_path=package.manifest_path,
            command=("/tmp/cm1/run/cm1.exe",),
            stdout_log=stdout_log,
            stderr_log=stderr_log,
            exit_code=None,
        )
    )
    monkeypatch.setattr("cloud_chamber.app._local_run_manager", fake_manager)

    response = TestClient(app).get(
        "/api/runs/status",
        params={"manifest_path": str(package.manifest_path)},
    )

    assert response.status_code == 200
    progress = response.json()["progress"]
    assert progress["model_time_seconds"] == pytest.approx(2922.0)
    assert progress["total_model_time_seconds"] == pytest.approx(21600.0)
    assert progress["percent_complete"] == pytest.approx(13.5)
    assert progress["estimated_remaining_wall_seconds"] is not None
    assert progress["model_time_source"] == "stdout model-minute progress"
    assert progress["total_model_time_source"] == "namelist.input timax"


def test_run_status_api_includes_observed_sounding_and_notes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path / "CloudChamber",
        run_id="run-observed-notes",
        observed_sounding=observed,
        user_tags=["compare", "saved"],
        user_notes="Compare this sounding against the humid case.",
    )
    manifest = load_run_manifest(package.manifest_path)
    stdout_log = package.package_dir / "logs" / "stdout.log"
    stderr_log = package.package_dir / "logs" / "stderr.log"
    stdout_log.parent.mkdir()
    stdout_log.write_text("")
    stderr_log.write_text("")
    write_run_manifest(
        package.manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.RUNNING,
                "provenance": ProvenanceMetadata(
                    product_state=ProductState.QUEUED_RUNNING_CM1_PROCESS
                ),
                "execution": ExecutionMetadata(
                    command=["/tmp/cm1/run/cm1.exe"],
                    started_at=datetime(2026, 5, 22, 15, 15, 36, tzinfo=UTC),
                    stdout_log=str(stdout_log),
                    stderr_log=str(stderr_log),
                ),
            }
        ),
    )
    monkeypatch.setattr(
        "cloud_chamber.app._local_run_manager",
        FakeRunManager(
            RunStatus(
                run_id="run-observed-notes",
                lifecycle_state=LifecycleState.RUNNING,
                manifest_path=package.manifest_path,
                command=("/tmp/cm1/run/cm1.exe",),
                stdout_log=stdout_log,
                stderr_log=stderr_log,
                exit_code=None,
            )
        ),
    )

    response = TestClient(app).get(
        "/api/runs/status",
        params={"manifest_path": str(package.manifest_path)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["observed_sounding"]["station_id"] == "USM00072558"
    assert payload["observed_sounding"]["station_name"] == "Valley, Nebraska"
    assert payload["observed_sounding"]["valid_time_utc"] == "2025-01-02T00:00:00Z"
    assert payload["user"]["tags"] == ["compare", "saved"]
    assert payload["user"]["notes"] == "Compare this sounding against the humid case."


def test_run_status_api_reports_completed_elapsed_and_full_model_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path / "CloudChamber",
        run_id="run-completed-progress",
    )
    manifest = load_run_manifest(package.manifest_path)
    started_at = datetime(2026, 5, 22, 15, 15, 36, tzinfo=UTC)
    finished_at = datetime(2026, 5, 22, 15, 45, 36, tzinfo=UTC)
    stdout_log = package.package_dir / "logs" / "stdout.log"
    stderr_log = package.package_dir / "logs" / "stderr.log"
    stdout_log.parent.mkdir()
    stdout_log.write_text("Program terminated normally\n")
    stderr_log.write_text("")
    write_run_manifest(
        package.manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.COMPLETED,
                "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
                "execution": ExecutionMetadata(
                    command=["/tmp/cm1/run/cm1.exe"],
                    started_at=started_at,
                    finished_at=finished_at,
                    exit_code=0,
                    stdout_log=str(stdout_log),
                    stderr_log=str(stderr_log),
                ),
                "outputs": OutputMetadata(netcdf_paths=[str(package.package_dir / "cm1out.nc")]),
            }
        ),
    )
    fake_manager = FakeRunManager(
        RunStatus(
            run_id="run-completed-progress",
            lifecycle_state=LifecycleState.COMPLETED,
            manifest_path=package.manifest_path,
            command=("/tmp/cm1/run/cm1.exe",),
            stdout_log=stdout_log,
            stderr_log=stderr_log,
            exit_code=0,
        )
    )
    monkeypatch.setattr("cloud_chamber.app._local_run_manager", fake_manager)

    response = TestClient(app).get(
        "/api/runs/status",
        params={"manifest_path": str(package.manifest_path)},
    )

    assert response.status_code == 200
    progress = response.json()["progress"]
    assert progress["elapsed_wall_seconds"] == pytest.approx(1800.0)
    assert progress["model_time_seconds"] == pytest.approx(21600.0)
    assert progress["total_model_time_seconds"] == pytest.approx(21600.0)
    assert progress["percent_complete"] == pytest.approx(100.0)
    assert progress["estimated_remaining_wall_seconds"] is None
    assert progress["model_time_source"] == "completed_run_state"


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


def test_run_queue_endpoints_surface_serial_queue_state(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_queue = FakeRunQueue()
    monkeypatch.setattr("cloud_chamber.app._local_run_queue", fake_queue)
    client = TestClient(app)

    queued = client.post("/api/runs/queue", json={"manifest_path": "/tmp/run_manifest.json"})
    refreshed = client.get("/api/runs/queue")

    assert queued.status_code == 200
    assert queued.json()["active_run_id"] == "run-queued"
    assert queued.json()["entries"][0]["state"] == "running"
    assert refreshed.status_code == 200
    assert refreshed.json()["entries"][0]["message"] == "Running local CM1 process."
    assert fake_queue.enqueued_manifest_path == Path("/tmp/run_manifest.json")


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


def test_lan_worker_start_blocks_differential_surface_forcing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding
    result = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path,
        run_id="run-differential-lan-blocked",
        observed_sounding=observed,
        run_configuration={
            "duration": "short_6h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "wide_12km",
            "output_cadence": "standard_15min",
            "surface_forcing_mode": "differential_surface_forcing_patch_v0",
            "surface_heat_flux_k_m_s": 8.0e-3,
            "surface_moisture_flux_g_g_m_s": 5.2e-5,
            "surface_patch_heat_flux_perturbation_k_m_s": 4.0e-2,
            "surface_patch_moisture_flux_perturbation_g_g_m_s": 5.0e-5,
            "surface_patch_radius_m": 1500.0,
            "surface_patch_taper_width_m": 500.0,
            "surface_patch_ramp_seconds": 1800.0,
        },
    )
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(tmp_path))

    response = TestClient(app).post(
        "/api/lan-worker/start",
        json={"manifest_path": str(result.manifest_path)},
    )

    assert response.status_code == 400
    assert "Differential surface forcing is local-only" in response.json()["detail"]


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


def test_result_delete_preview_and_confirm_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(tmp_path / "CloudChamber"))
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path / "CloudChamber",
        run_id="run-api-delete-result",
    )
    run_dir = package.package_dir
    netcdf_path = run_dir / "cm1out_000001.nc"
    (run_dir / "logs").mkdir()
    (run_dir / "logs" / "stdout.log").write_text("Program terminated normally\n")
    xr.Dataset(
        data_vars={
            "qc": (
                ("time", "z", "y", "x"),
                [[[[2e-6]]]],
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
    client = TestClient(app)
    ingest_response = client.post(
        "/api/results/ingest",
        json={"manifest_path": str(package.manifest_path)},
    )
    result_id = ingest_response.json()["result_id"]

    preview = client.post(f"/api/results/{result_id}/delete-preview")
    blocked = client.post(f"/api/results/{result_id}/delete", json={"confirm": False})
    deleted = client.post(f"/api/results/{result_id}/delete", json={"confirm": True})
    list_after_delete = client.get("/api/results")
    get_after_delete = client.get(f"/api/results/{result_id}")

    assert preview.status_code == 200
    assert preview.json()["result_id"] == result_id
    assert preview.json()["run_id"] == "run-api-delete-result"
    assert preview.json()["deleted"] is False
    assert "Results" in preview.json()["affected_surfaces"]
    assert {
        category["label"] for category in preview.json()["categories"] if category["present"]
    } >= {
        "Result metadata and notebook edits",
        "Run manifests, package inputs, and reports",
        "CM1 output and stats",
        "Logs and runtime sidecars",
        "Derived diagnostics and Explore data",
    }
    assert blocked.status_code == 400
    assert blocked.json()["detail"] == "Real delete requires confirm=true."
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert not run_dir.exists()
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["results"] == []
    assert get_after_delete.status_code == 404


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
