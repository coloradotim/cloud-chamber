"""FastAPI application skeleton for local Cloud Chamber services."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from cloud_chamber.cli import ENGINE_NOTE
from cloud_chamber.dry_run_package import generate_dry_run_package, read_dry_run_report
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
