"""FastAPI application skeleton for local Cloud Chamber services."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cloud_chamber.cli import ENGINE_NOTE
from cloud_chamber.dry_run_package import generate_dry_run_package, read_dry_run_report
from cloud_chamber.igra_catalog import (
    IGRACatalogError,
    cache_station_zip_from_catalog,
    read_igra_cache_manifest,
    read_igra_recent_catalog,
    refresh_recent_catalog,
)
from cloud_chamber.lan_worker import (
    LanWorkerApiError,
    cleanup_lan_worker_run,
    collect_lan_worker_run,
    lan_worker_config_status,
    lan_worker_run_status,
    start_lan_worker_run,
)
from cloud_chamber.local_run_manager import LocalRunManager, LocalRunManagerError, RunStatus
from cloud_chamber.observed_sounding import ObservedSoundingError, parse_igra_station_text
from cloud_chamber.result_cards import (
    ResultCardUpdate,
    get_result_card,
    list_result_cards,
    save_result_card,
    update_result_card,
)
from cloud_chamber.result_ingest import (
    ResultIngestError,
    ingest_completed_run,
)
from cloud_chamber.run_manifest import RunManifestError, load_run_manifest
from cloud_chamber.runtime_storage import (
    RuntimeStorageError,
    delete_runtime_run,
    runtime_storage_inventory,
)
from cloud_chamber.scenario_catalog import (
    load_scenario_template,
    load_scenario_templates,
    scenario_summary,
)
from cloud_chamber.selected_region_diagnostics import (
    RegionType,
    SelectedRegionError,
    SelectedRegionRequest,
    selected_region_diagnostics,
)
from cloud_chamber.settings import load_settings
from cloud_chamber.visualization_data import (
    VisualizationDataError,
    VisualizationOrientation,
    field_catalog,
    field_slice,
    point_cloud,
    view_defaults,
)

app = FastAPI(
    title="Cloud Chamber Backend",
    summary="Local backend API for Cloud Chamber CM1 experiment workflows.",
    version="0.1.0",
)

_local_run_manager: LocalRunManager | None = None


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight readiness response that does not require CM1."""
    return {
        "status": "ok",
        "product": "Cloud Chamber",
        "engine_note": ENGINE_NOTE,
    }


class DryRunRequest(BaseModel):
    scenario_id: str = "baseline-shallow-cumulus"
    controls: dict[str, str | float | bool] = Field(default_factory=dict)
    run_size_preset: str = "quick_look"
    observed_sounding: dict[str, object] | None = None


class ObservedSoundingParseRequest(BaseModel):
    uploaded_filename: str
    text: str
    selected_time_utc: str | None = None


class LaunchRunRequest(BaseModel):
    manifest_path: str


class DeleteRunRequest(BaseModel):
    run_id: str
    dry_run: bool = True
    confirm: bool = False
    force_saved: bool = False


class IngestResultRequest(BaseModel):
    manifest_path: str


class LanWorkerRunRequest(BaseModel):
    manifest_path: str


class IGRACacheRequest(BaseModel):
    station_id: str
    filename: str | None = None


@app.get("/api/scenarios")
def list_scenarios() -> dict[str, object]:
    scenarios = [scenario_summary(scenario) for scenario in load_scenario_templates()]
    return {
        "golden_path_scenario_id": "baseline-shallow-cumulus",
        "scenarios": scenarios,
    }


@app.post("/api/dry-run-package")
def create_dry_run_package(request: DryRunRequest) -> dict[str, Any]:
    scenario = load_scenario_template(request.scenario_id)
    settings = load_settings()
    result = generate_dry_run_package(
        scenario_data=scenario.model_dump(mode="json"),
        runtime_home=settings.runtime_home,
        run_id=f"dry-run-{uuid4().hex[:12]}",
        controls=request.controls,
        run_size_preset=request.run_size_preset,
        observed_sounding=request.observed_sounding,
    )
    report = read_dry_run_report(result.report_path)
    return {
        "package_dir": str(result.package_dir),
        "manifest_path": str(result.manifest_path),
        "report_path": str(result.report_path),
        "generated_files": [str(path) for path in result.generated_files],
        "report": report,
    }


@app.post("/api/observed-soundings/parse")
def parse_observed_sounding(request: ObservedSoundingParseRequest) -> dict[str, object]:
    try:
        selected_time = (
            datetime.fromisoformat(request.selected_time_utc.replace("Z", "+00:00"))
            if request.selected_time_utc
            else None
        )
        result = parse_igra_station_text(
            request.text,
            uploaded_filename=request.uploaded_filename,
            selected_time_utc=selected_time,
        )
    except ObservedSoundingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/igra/recent/catalog")
def get_igra_recent_catalog() -> dict[str, object]:
    catalog = read_igra_recent_catalog(load_settings())
    return {"catalog": catalog.model_dump(mode="json") if catalog else None}


@app.post("/api/igra/recent/refresh-catalog")
def refresh_igra_recent_catalog() -> dict[str, object]:
    try:
        catalog = refresh_recent_catalog(load_settings())
    except IGRACatalogError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return catalog.model_dump(mode="json")


@app.get("/api/igra/recent/cache")
def get_igra_recent_cache() -> dict[str, object]:
    manifest = read_igra_cache_manifest(load_settings())
    return manifest.model_dump(mode="json")


@app.post("/api/igra/recent/cache")
def cache_igra_recent_file(request: IGRACacheRequest) -> dict[str, object]:
    try:
        entry = cache_station_zip_from_catalog(
            load_settings(),
            station_id=request.station_id,
            filename=request.filename,
        )
    except IGRACatalogError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return entry.model_dump(mode="json")


@app.post("/api/runs/launch")
def launch_run(request: LaunchRunRequest) -> dict[str, object]:
    try:
        status = _get_local_run_manager().launch(Path(request.manifest_path).expanduser())
    except LocalRunManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _run_status_payload(status)


@app.get("/api/runs/status")
def run_status(manifest_path: str) -> dict[str, object]:
    try:
        status = _get_local_run_manager().status(Path(manifest_path).expanduser())
    except LocalRunManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _run_status_payload(status)


@app.post("/api/runs/cancel")
def cancel_run() -> dict[str, object]:
    try:
        status = _get_local_run_manager().cancel()
    except LocalRunManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _run_status_payload(status)


@app.get("/api/lan-worker/config")
def get_lan_worker_config() -> dict[str, object]:
    return lan_worker_config_status()


@app.post("/api/lan-worker/start")
def start_lan_worker(request: LanWorkerRunRequest) -> dict[str, object]:
    try:
        return start_lan_worker_run(load_settings(), Path(request.manifest_path).expanduser())
    except LanWorkerApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/lan-worker/status")
def get_lan_worker_status(manifest_path: str) -> dict[str, object]:
    try:
        return lan_worker_run_status(load_settings(), Path(manifest_path).expanduser())
    except LanWorkerApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/lan-worker/collect")
def collect_lan_worker(request: LanWorkerRunRequest) -> dict[str, object]:
    try:
        return collect_lan_worker_run(load_settings(), Path(request.manifest_path).expanduser())
    except LanWorkerApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/lan-worker/cleanup")
def cleanup_lan_worker(request: LanWorkerRunRequest) -> dict[str, object]:
    try:
        return cleanup_lan_worker_run(load_settings(), Path(request.manifest_path).expanduser())
    except LanWorkerApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/storage/inventory")
def storage_inventory() -> dict[str, object]:
    inventory = runtime_storage_inventory(load_settings())
    return inventory.model_dump(mode="json")


@app.post("/api/storage/delete-run")
def delete_run(request: DeleteRunRequest) -> dict[str, object]:
    try:
        result = delete_runtime_run(
            load_settings(),
            run_id=request.run_id,
            dry_run=request.dry_run,
            confirm=request.confirm,
            force_saved=request.force_saved,
        )
    except RuntimeStorageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.post("/api/results/ingest")
def ingest_result(request: IngestResultRequest) -> dict[str, object]:
    try:
        result = ingest_completed_run(Path(request.manifest_path).expanduser())
    except ResultIngestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results")
def list_results() -> dict[str, object]:
    return {
        "results": [card.model_dump(mode="json") for card in list_result_cards(load_settings())]
    }


@app.get("/api/results/{result_id}")
def get_result(result_id: str) -> dict[str, object]:
    try:
        result = get_result_card(load_settings(), result_id)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.patch("/api/results/{result_id}")
def patch_result(result_id: str, request: ResultCardUpdate) -> dict[str, object]:
    try:
        result = update_result_card(load_settings(), result_id, request)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.post("/api/results/{result_id}/save")
def save_result(result_id: str) -> dict[str, object]:
    try:
        result = save_result_card(load_settings(), result_id)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/visualization/fields")
def get_visualization_fields(result_id: str) -> dict[str, object]:
    try:
        result = field_catalog(load_settings(), result_id)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/visualization/defaults")
def get_visualization_defaults(result_id: str, time_index: int | None = None) -> dict[str, object]:
    try:
        result = view_defaults(load_settings(), result_id, time_index=time_index)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/visualization/slice")
def get_visualization_slice(
    result_id: str,
    field: str,
    time_index: int = 0,
    orientation: str = "horizontal",
    level_index: int = 0,
    encoding: str = "json",
) -> dict[str, object]:
    if orientation not in {"horizontal", "vertical_x", "vertical_y"}:
        raise HTTPException(status_code=400, detail=f"Unsupported orientation: {orientation}")
    if encoding != "json":
        raise HTTPException(status_code=400, detail="Only encoding=json is supported.")
    checked_orientation = cast(VisualizationOrientation, orientation)
    try:
        result = field_slice(
            load_settings(),
            result_id,
            field=field,
            time_index=time_index,
            orientation=checked_orientation,
            level_index=level_index,
            encoding="json",
        )
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/visualization/point-cloud")
def get_visualization_point_cloud(
    result_id: str,
    field: str = "qc",
    time_index: int = 0,
    threshold: float = 1e-6,
    max_points: int = 50_000,
    encoding: str = "json",
) -> dict[str, object]:
    if encoding != "json":
        raise HTTPException(status_code=400, detail="Only encoding=json is supported.")
    try:
        result = point_cloud(
            load_settings(),
            result_id,
            field=field,
            time_index=time_index,
            threshold=threshold,
            max_points=max_points,
            encoding="json",
        )
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/diagnostics/selected-region")
def get_selected_region_diagnostics(
    result_id: str,
    region_type: str,
    x_index: int | None = None,
    y_index: int | None = None,
    z_index: int | None = None,
    x_start: int | None = None,
    x_end: int | None = None,
    y_start: int | None = None,
    y_end: int | None = None,
    z_start: int | None = None,
    z_end: int | None = None,
    neighborhood: int = 0,
) -> dict[str, object]:
    if region_type not in {"point", "column", "box"}:
        raise HTTPException(status_code=400, detail=f"Unsupported region_type: {region_type}")
    checked_region_type = cast(RegionType, region_type)
    try:
        request = SelectedRegionRequest(
            region_type=checked_region_type,
            x_index=x_index,
            y_index=y_index,
            z_index=z_index,
            x_start=x_start,
            x_end=x_end,
            y_start=y_start,
            y_end=y_end,
            z_start=z_start,
            z_end=z_end,
            neighborhood=neighborhood,
        )
        result = selected_region_diagnostics(load_settings(), result_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SelectedRegionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


def _get_local_run_manager() -> LocalRunManager:
    global _local_run_manager
    if _local_run_manager is None:
        _local_run_manager = LocalRunManager(settings=load_settings())
    return _local_run_manager


def _run_status_payload(status: RunStatus) -> dict[str, object]:
    try:
        manifest = load_run_manifest(status.manifest_path)
    except (OSError, RunManifestError):
        return {
            "run_id": status.run_id,
            "lifecycle_state": status.lifecycle_state.value,
            "product_state": None,
            "validation_status": None,
            "manifest_path": str(status.manifest_path),
            "command": list(status.command),
            "stdout_log": str(status.stdout_log),
            "stderr_log": str(status.stderr_log),
            "stdout_tail": _tail_text(status.stdout_log),
            "stderr_tail": _tail_text(status.stderr_log),
            "exit_code": status.exit_code,
            "started_at": None,
            "finished_at": None,
            "output_summary": {
                "raw_cm1_artifacts": 0,
                "netcdf_paths": 0,
                "processed_artifacts": 0,
            },
            "runtime_warnings": [],
        }
    return {
        "run_id": status.run_id,
        "lifecycle_state": status.lifecycle_state.value,
        "product_state": manifest.provenance.product_state.value,
        "validation_status": manifest.validation_status.value,
        "manifest_path": str(status.manifest_path),
        "command": list(status.command),
        "stdout_log": str(status.stdout_log),
        "stderr_log": str(status.stderr_log),
        "stdout_tail": _tail_text(status.stdout_log),
        "stderr_tail": _tail_text(status.stderr_log),
        "exit_code": status.exit_code,
        "started_at": manifest.execution.started_at.isoformat()
        if manifest.execution.started_at
        else None,
        "finished_at": manifest.execution.finished_at.isoformat()
        if manifest.execution.finished_at
        else None,
        "output_summary": {
            "raw_cm1_artifacts": len(manifest.outputs.raw_cm1_artifacts),
            "netcdf_paths": len(manifest.outputs.netcdf_paths),
            "processed_artifacts": len(manifest.outputs.processed_artifacts),
        },
        "runtime_warnings": manifest.outputs.runtime_warnings,
    }


def _tail_text(path: Path, *, max_lines: int = 12) -> str | None:
    if not str(path):
        return None
    try:
        if not path.exists():
            return None
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return None
    return "\n".join(lines[-max_lines:]) if lines else ""
