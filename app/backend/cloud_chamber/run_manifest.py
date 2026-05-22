"""Run manifest schema and lifecycle state validation."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class RunManifestError(ValueError):
    """Raised when a run manifest fails validation or parsing."""


class LifecycleState(StrEnum):
    CREATED = "created"
    PACKAGED = "packaged"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    INGESTED = "ingested"
    SAVED = "saved"


class ValidationStatus(StrEnum):
    UNVALIDATED = "unvalidated"
    VALID = "valid"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class ProductState(StrEnum):
    PREVIEW_ESTIMATE = "preview_estimate"
    GENERATED_CM1_CONFIGURATION = "generated_cm1_configuration"
    PACKAGED_DRY_RUN_OUTPUT = "packaged_dry_run_output"
    QUEUED_RUNNING_CM1_PROCESS = "queued_running_cm1_process"
    COMPLETED_CM1_RESULT = "completed_cm1_result"
    PROCESS_COMPLETED_NO_OUTPUT = "process_completed_no_output"
    FAILED_CANCELED_CM1_RUN = "failed_canceled_cm1_run"
    INGESTED_RESULT_METADATA = "ingested_result_metadata"
    VISUALIZER_INTERPRETATION = "visualizer_interpretation"
    SAVED_RESULT_NOTEBOOK_ENTRY = "saved_result_notebook_entry"


class ScenarioReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    schema_version: str
    template_path: str | None = None


class GeneratedInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_directory: str
    manifest_path: str | None = None
    namelist_input: str | None = None
    input_sounding: str | None = None
    dry_run_report: str | None = None
    runtime_file_checklist: list[str] = Field(default_factory=list)


class RuntimePaths(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime_home: str
    cm1_root: str | None = None
    cm1_run_dir: str | None = None
    cache_dir: str | None = None
    log_dir: str | None = None


class AppMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_version: str
    commit: str | None = None
    created_by: str = "Cloud Chamber"


class ExecutionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    stdout_log: str | None = None
    stderr_log: str | None = None


class OutputMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    netcdf_paths: list[str] = Field(default_factory=list)
    processed_artifacts: list[str] = Field(default_factory=list)
    diagnostics_summary: str | None = None
    visualization_defaults: str | None = None


class ProvenanceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_model: str = "CM1"
    product_state: ProductState
    preview_is_guidance_only: bool = True
    visualizer_is_interpretation: bool = True


class UserMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    saved: bool = False


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_version: str = "1"
    run_id: str
    scenario: ScenarioReference
    controls: dict[str, str | float | bool]
    run_size_preset: str
    physical_question: str
    expected_diagnostics: list[str]
    generated_inputs: GeneratedInputs
    runtime_paths: RuntimePaths
    app: AppMetadata
    lifecycle_state: LifecycleState
    validation_status: ValidationStatus
    provenance: ProvenanceMetadata
    created_at: datetime
    updated_at: datetime
    execution: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
    outputs: OutputMetadata = Field(default_factory=OutputMetadata)
    user: UserMetadata

    @model_validator(mode="after")
    def validate_state_contract(self) -> RunManifest:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be earlier than created_at")
        if self.lifecycle_state == LifecycleState.PACKAGED:
            if self.provenance.product_state != ProductState.PACKAGED_DRY_RUN_OUTPUT:
                raise ValueError("packaged manifests must use packaged dry-run product state")
            if self.outputs.netcdf_paths:
                raise ValueError("packaged dry-run manifests must not include NetCDF outputs")
        if self.lifecycle_state in {
            LifecycleState.COMPLETED,
            LifecycleState.INGESTED,
            LifecycleState.SAVED,
        }:
            if self.provenance.product_state == ProductState.PACKAGED_DRY_RUN_OUTPUT:
                raise ValueError("completed/ingested/saved manifests cannot be dry-run packages")
        if self.lifecycle_state == LifecycleState.SAVED and not self.user.saved:
            raise ValueError("saved manifests must set user.saved")
        return self

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2) + "\n"


def validate_run_manifest(data: object) -> RunManifest:
    try:
        return RunManifest.model_validate(data)
    except ValidationError as exc:
        raise RunManifestError(str(exc)) from exc


def run_manifest_from_json(text: str) -> RunManifest:
    try:
        data: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RunManifestError(str(exc)) from exc
    return validate_run_manifest(data)


def load_run_manifest(path: Path) -> RunManifest:
    return run_manifest_from_json(path.read_text())


def write_run_manifest(path: Path, manifest: RunManifest) -> None:
    path.write_text(manifest.to_json_text())
