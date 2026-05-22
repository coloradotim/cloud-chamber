"""FastAPI application skeleton for local Cloud Chamber services."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cloud_chamber.cli import ENGINE_NOTE
from cloud_chamber.dry_run_package import generate_dry_run_package, read_dry_run_report
from cloud_chamber.local_run_manager import LocalRunManager, LocalRunManagerError, RunStatus
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
from cloud_chamber.settings import load_settings

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


class LaunchRunRequest(BaseModel):
    manifest_path: str


class DeleteRunRequest(BaseModel):
    run_id: str
    dry_run: bool = True
    confirm: bool = False
    force_saved: bool = False


class IngestResultRequest(BaseModel):
    manifest_path: str


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
    )
    report = read_dry_run_report(result.report_path)
    return {
        "package_dir": str(result.package_dir),
        "manifest_path": str(result.manifest_path),
        "report_path": str(result.report_path),
        "generated_files": [str(path) for path in result.generated_files],
        "report": report,
    }


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


def _get_local_run_manager() -> LocalRunManager:
    global _local_run_manager
    if _local_run_manager is None:
        _local_run_manager = LocalRunManager(settings=load_settings())
    return _local_run_manager


def _run_status_payload(status: RunStatus) -> dict[str, object]:
    return {
        "run_id": status.run_id,
        "lifecycle_state": status.lifecycle_state.value,
        "manifest_path": str(status.manifest_path),
        "command": list(status.command),
        "stdout_log": str(status.stdout_log),
        "stderr_log": str(status.stderr_log),
        "exit_code": status.exit_code,
    }
