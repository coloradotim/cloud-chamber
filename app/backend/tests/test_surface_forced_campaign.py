from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.output_products import ScienceSummary
from cloud_chamber.result_diagnostics import (
    CloudDiagnostics,
    RainDiagnostics,
    ReflectivityDiagnostics,
    ResultDiagnostics,
    SurfaceRainDiagnostics,
    TimeDiagnostics,
    TimeValue,
    VerticalVelocityDiagnostics,
)
from cloud_chamber.result_ingest import RESULT_METADATA_FILENAME, FieldMetadata, ResultMetadata
from cloud_chamber.run_manifest import (
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.surface_forced_campaign import (
    CampaignError,
    build_campaign_plan,
    ingest_campaign,
    package_campaign,
    plan_campaign,
    queue_campaign,
    report_campaign,
    status_campaign,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=tmp_path / "cm1r21.1",
        cm1_run_dir=tmp_path / "cm1r21.1" / "run",
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def write_matrix(
    tmp_path: Path,
    *,
    queue_target: str = "local",
    include_followups: bool = False,
    include_comparison: bool = False,
) -> Path:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "valley.txt").write_text(IGRA_FIXTURE)
    matrix: dict[str, Any] = {
        "schema_version": "surface_forced_campaign_matrix_v1",
        "campaign": {
            "campaign_id": "surface_forced_test",
            "title": "Surface forced test",
            "objective": "Verify campaign runner plumbing.",
            "protocol": "docs/research/surface-forced-sounding-verification-protocol.md",
            "commit_report_path": str(tmp_path / "reports" / "surface_forced_test.md"),
        },
        "execution": {"queue_target": queue_target, "resume_existing": True},
        "selection_sets": [
            {
                "selection_id": "control_sounding",
                "role": "forcing_path_smoke_check",
                "source": {
                    "type": "uploaded_or_local_igra",
                    "local_text_path": "fixtures/valley.txt",
                    "selected_valid_time_utc": "2025-01-02T00:00:00Z",
                },
                "selection_notes": "Tiny test IGRA fixture.",
                "candidate_screening": {
                    "candidate_id": "fixture-candidate",
                    "primary_story": "humid_rainy_candidate",
                    "primary_story_label": "Humid / rainy candidate",
                    "story_family": "lower_atmosphere",
                    "rank_score": 72.0,
                    "evidence": [{"label": "low-level moisture", "value": "high"}],
                    "caveats": ["fixture_screening"],
                },
            }
        ],
        "run_defaults": {
            "duration": "short_6h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "wide_12km",
            "output_cadence": "standard_15min",
            "surface_heat_flux_k_m_s": 8.0e-3,
            "surface_moisture_flux_g_g_m_s": 5.2e-5,
            "queue_target": queue_target,
            "tags": ["campaign-test"],
            "notes": "Campaign default note.",
        },
        "forcing_sets": [
            {
                "forcing_id": "stronger_flux",
                "surface_heat_flux_k_m_s": 4.0e-2,
                "surface_moisture_flux_g_g_m_s": 1.0e-4,
            }
        ],
        "comparison_types": [
            {
                "comparison_type": "forcing_sensitivity_same_duration",
                "varied_fields": ["surface_heat_flux_k_m_s"],
                "required_equal_fields": ["duration"],
                "required_available_fields": ["hfx", "qfx", "qv", "qc", "w"],
                "required_diagnostic_support": ["surface_fluxes", "low_level_response"],
            }
        ],
        "runs": [
            {
                "matrix_id": "phase1_control_high_flux",
                "phase": "forcing_path_smoke_check",
                "selection_id": "control_sounding",
                "forcing_id": "stronger_flux",
                "comparison_role": "phase1_control",
            }
        ],
        "required_summary_fields": {"metadata": ["campaign_id"], "evidence": ["hfx_present"]},
    }
    if include_followups:
        matrix["runs"].extend(
            [
                {
                    "matrix_id": "phase2_followup",
                    "phase": "easy_sounding_response_check",
                    "selection_id": "control_sounding",
                    "forcing_id": "stronger_flux",
                },
                {
                    "matrix_id": "phase2_optional_120km",
                    "phase": "easy_sounding_response_check",
                    "optional": True,
                    "selection_id": "control_sounding",
                    "forcing_id": "stronger_flux",
                    "domain_size": "regional_120km",
                },
            ]
        )
    if include_comparison:
        matrix["runs"].append(
            {
                "matrix_id": "phase1_experiment_high_flux",
                "phase": "forcing_path_smoke_check",
                "selection_id": "control_sounding",
                "forcing_id": "stronger_flux",
                "surface_heat_flux_k_m_s": 5.0e-2,
                "comparison": {
                    "type": "forcing_sensitivity_same_duration",
                    "control_matrix_id": "phase1_control_high_flux",
                },
            }
        )
    matrix_path = tmp_path / "campaign.yaml"
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False))
    return matrix_path


def test_campaign_plan_validates_matrix_and_resolves_cm1_values(tmp_path: Path) -> None:
    matrix_path = write_matrix(tmp_path)
    plan = build_campaign_plan(yaml.safe_load(matrix_path.read_text()), matrix_path=matrix_path)

    assert plan.campaign_id == "surface_forced_test"
    assert plan.run_count == 1
    run = plan.runs[0]
    assert run.matrix_id == "phase1_control_high_flux"
    assert run.queue_target == "local"
    assert run.run_configuration["surface_heat_flux_k_m_s"] == 4.0e-2
    assert run.run_configuration["surface_moisture_flux_g_g_m_s"] == 1.0e-4
    assert run.surface_flux_cm1_values["cnst_shflx"] == 4.0e-2
    assert run.surface_flux_cm1_values["cnst_lhflx"] == 1.0e-4
    assert run.cm1_values["nx"] == 128
    assert run.cm1_values["domain_x_km"] == 12.8
    assert "campaign:surface_forced_test" in run.tags
    assert run.stable_resume_identity


def test_campaign_plans_checked_in_example_matrix() -> None:
    plan = plan_campaign(
        REPO_ROOT / "docs/research/templates/surface-forced-campaign-matrix.example.yaml"
    )

    assert plan.campaign_id == "surface_forced_smoke_001"
    assert plan.run_count == 10
    assert plan.execution["max_concurrent_runs"] == 1
    assert "forcing_sensitivity_same_duration" in plan.comparison_types
    assert any(run.optional for run in plan.runs)
    assert plan.required_summary_fields["evidence"]


def test_campaign_plan_blocks_machine_private_absolute_igra_paths(tmp_path: Path) -> None:
    matrix_path = write_matrix(tmp_path)
    matrix = yaml.safe_load(matrix_path.read_text())
    matrix["selection_sets"][0]["source"]["local_text_path"] = str(tmp_path / "valley.txt")

    try:
        build_campaign_plan(matrix, matrix_path=matrix_path)
    except CampaignError as exc:
        assert "absolute" in str(exc)
    else:
        raise AssertionError("absolute local path should be blocked by default")


def test_campaign_plan_rejects_unknown_required_summary_field(tmp_path: Path) -> None:
    matrix_path = write_matrix(tmp_path)
    matrix = yaml.safe_load(matrix_path.read_text())
    matrix["required_summary_fields"]["evidence"].append("not_a_real_summary_field")

    with pytest.raises(CampaignError, match="Unsupported required_summary_fields"):
        build_campaign_plan(matrix, matrix_path=matrix_path)


def test_campaign_package_creates_observed_surface_forced_package_and_resumes(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)

    first = package_campaign(matrix_path, settings=settings, resume=True)
    second = package_campaign(matrix_path, settings=settings, resume=True)

    assert first.runs[0].status == "packaged"
    assert second.runs[0].message == "Resumed existing package."
    assert len(list((settings.runtime_home / "runs").iterdir())) == 1
    manifest = load_run_manifest(Path(first.runs[0].manifest_path or ""))
    assert manifest.run_recipe == "observed_surface_forced_evolution"
    assert manifest.observed_sounding is not None
    assert manifest.observed_sounding["station_id"] == "USM00072558"
    assert manifest.candidate_screening is not None
    assert manifest.candidate_screening["primary_story"] == "humid_rainy_candidate"
    assert manifest.run_configuration["surface_heat_flux_k_m_s"] == 4.0e-2
    assert manifest.run_configuration["surface_moisture_flux_g_g_m_s"] == 1.0e-4
    assert "campaign:surface_forced_test" in manifest.user.tags
    assert "Campaign default note." in (manifest.user.notes or "")


def test_campaign_queue_uses_existing_local_queue_path(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    enqueued: list[Path] = []

    class FakeQueue:
        def enqueue(self, manifest_path: Path) -> SimpleNamespace:
            enqueued.append(manifest_path)
            entry = SimpleNamespace(
                manifest_path=str(manifest_path),
                state="queued",
                message="Queued by fake local queue.",
                error=None,
                result_id=None,
            )
            return SimpleNamespace(entries=[entry])

    def fake_queue_factory(_settings: CloudChamberSettings) -> Any:
        return FakeQueue()

    result = queue_campaign(
        matrix_path,
        settings=settings,
        local_queue_factory=fake_queue_factory,
    )

    assert result.runs[0].status == "queued"
    assert result.runs[0].run_status == "queued"
    assert result.runs[0].message == "Queued by fake local queue."
    assert enqueued == [Path(result.runs[0].manifest_path or "")]


def test_campaign_queue_rejects_unknown_matrix_id(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)

    with pytest.raises(CampaignError, match="Unknown matrix_id"):
        queue_campaign(
            matrix_path,
            settings=settings,
            selected_matrix_ids={"missing-row"},
        )


def test_campaign_queue_blocks_followups_and_excludes_optional_by_default(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path, include_followups=True)
    enqueued: list[str] = []

    class FakeQueue:
        def enqueue(self, manifest_path: Path) -> SimpleNamespace:
            enqueued.append(manifest_path.name)
            entry = SimpleNamespace(
                manifest_path=str(manifest_path),
                state="queued",
                message="Queued by fake local queue.",
                error=None,
                result_id=None,
            )
            return SimpleNamespace(entries=[entry])

    result = queue_campaign(
        matrix_path,
        settings=settings,
        local_queue_factory=lambda _settings: FakeQueue(),
    )
    runs = {run.matrix_id: run for run in result.runs}

    assert len(enqueued) == 1
    assert runs["phase1_control_high_flux"].status == "queued"
    assert runs["phase2_followup"].status == "blocked"
    assert runs["phase2_optional_120km"].status == "planned"

    override = queue_campaign(
        matrix_path,
        settings=settings,
        selected_matrix_ids={"phase2_followup"},
        override_phase_gate=True,
        override_reason="manual smoke evidence reviewed",
        local_queue_factory=lambda _settings: FakeQueue(),
    )
    followup = next(run for run in override.runs if run.matrix_id == "phase2_followup")
    assert followup.status == "queued"
    assert followup.gate_override is not None
    assert followup.gate_override["reason"] == "manual smoke evidence reviewed"


@pytest.mark.parametrize(
    ("lifecycle", "product_state", "expected_status"),
    [
        (
            LifecycleState.QUEUED,
            ProductState.QUEUED_RUNNING_CM1_PROCESS,
            "queued",
        ),
        (
            LifecycleState.RUNNING,
            ProductState.QUEUED_RUNNING_CM1_PROCESS,
            "running",
        ),
        (
            LifecycleState.COMPLETED,
            ProductState.COMPLETED_CM1_RESULT,
            "completed_not_ingested",
        ),
        (
            LifecycleState.INGESTED,
            ProductState.INGESTED_RESULT_METADATA,
            "ingested",
        ),
        (
            LifecycleState.FAILED,
            ProductState.FAILED_CANCELED_CM1_RUN,
            "run_failed",
        ),
        (
            LifecycleState.CANCELED,
            ProductState.FAILED_CANCELED_CM1_RUN,
            "run_canceled",
        ),
    ],
)
def test_campaign_queue_is_idempotent_for_existing_lifecycle_states(
    tmp_path: Path,
    lifecycle: LifecycleState,
    product_state: ProductState,
    expected_status: str,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    _set_manifest_lifecycle(manifest_path, lifecycle, product_state)
    if lifecycle == LifecycleState.RUNNING:
        manifest = load_run_manifest(manifest_path)
        write_run_manifest(
            manifest_path,
            manifest.model_copy(
                update={
                    "execution": manifest.execution.model_copy(update={"process_id": os.getpid()})
                }
            ),
        )

    class FailingQueue:
        def enqueue(self, _manifest_path: Path) -> SimpleNamespace:
            raise AssertionError("queue should not be called for existing lifecycle state")

    result = queue_campaign(
        matrix_path,
        settings=settings,
        local_queue_factory=lambda _settings: FailingQueue(),
    )

    assert result.runs[0].status == expected_status
    assert "Skipped queue" in (result.runs[0].message or "")


def test_campaign_status_reconciles_stale_running_manifest_before_queue_state(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.RUNNING,
                "provenance": ProvenanceMetadata(
                    product_state=ProductState.QUEUED_RUNNING_CM1_PROCESS
                ),
                "execution": manifest.execution.model_copy(update={"process_id": 987654321}),
            }
        ),
    )
    queue_path = settings.runtime_home / "run-queue.json"
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "entries": [
                    {
                        "run_id": packaged.runs[0].run_id,
                        "manifest_path": str(manifest_path),
                        "state": "running",
                        "queued_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "started_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "finished_at": None,
                        "result_id": None,
                        "message": "Stale queue entry still claims running.",
                        "error": None,
                        "cleanup_status": None,
                    }
                ],
            }
        )
        + "\n"
    )

    status = status_campaign(matrix_path, settings=settings)

    assert status.runs[0].status == "run_failed"
    manifest = load_run_manifest(manifest_path)
    assert manifest.lifecycle_state == LifecycleState.FAILED
    assert (
        "Tracked CM1 process 987654321 is no longer running"
        in (manifest.outputs.runtime_warnings[0])
    )


def test_campaign_status_reports_queued_entry_for_packaged_manifest(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    queue_path = settings.runtime_home / "run-queue.json"
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "entries": [
                    {
                        "run_id": packaged.runs[0].run_id,
                        "manifest_path": str(manifest_path),
                        "state": "queued",
                        "queued_at": now,
                        "updated_at": now,
                        "started_at": None,
                        "finished_at": None,
                        "result_id": None,
                        "message": "Queued behind another local run.",
                        "error": None,
                        "cleanup_status": None,
                    }
                ],
            }
        )
        + "\n"
    )

    status = status_campaign(matrix_path, settings=settings)

    assert status.runs[0].status == "queued"
    assert status.runs[0].run_status == "queued"
    assert status.runs[0].message == "Queued behind another local run."


def test_campaign_status_prefers_ingested_result_over_stale_queue_message(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    _write_fake_result_metadata(manifest_path)
    queue_path = settings.runtime_home / "run-queue.json"
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "entries": [
                    {
                        "run_id": packaged.runs[0].run_id,
                        "manifest_path": str(manifest_path),
                        "state": "running",
                        "queued_at": now,
                        "updated_at": now,
                        "started_at": now,
                        "finished_at": None,
                        "result_id": None,
                        "message": "CM1 is running; waiting for terminal status.",
                        "error": None,
                        "cleanup_status": None,
                    }
                ],
            }
        )
        + "\n"
    )

    status = status_campaign(matrix_path, settings=settings)

    assert status.runs[0].status == "ingested"
    assert status.runs[0].message == "Completed CM1 output ingested."


def test_campaign_lan_queue_status_collect_and_ingest_flow(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    from cloud_chamber import surface_forced_campaign

    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path, queue_target="lan")
    started: list[Path] = []

    def fake_start(_settings: CloudChamberSettings, manifest_path: Path) -> dict[str, object]:
        started.append(manifest_path)
        return {"state": "running", "message": "LAN worker started"}

    def fake_running(_settings: CloudChamberSettings, _manifest_path: Path) -> dict[str, object]:
        return {"state": "running", "message": "LAN worker still running"}

    def fake_complete(_settings: CloudChamberSettings, _manifest_path: Path) -> dict[str, object]:
        return {"state": "ready_for_local_ingest", "message": "LAN output is ready"}

    def fake_collect(_settings: CloudChamberSettings, manifest_path: Path) -> dict[str, object]:
        netcdf_path = manifest_path.parent / "cm1out_000001.nc"
        netcdf_path.write_text("fake netcdf placeholder")
        _set_manifest_lifecycle(
            manifest_path,
            LifecycleState.COMPLETED,
            ProductState.COMPLETED_CM1_RESULT,
            netcdf_path=netcdf_path,
        )
        return {"state": "ready_for_local_ingest", "message": "LAN output collected"}

    queued = queue_campaign(
        matrix_path,
        settings=settings,
        lan_start=fake_start,
        lan_status=fake_running,
    )
    assert queued.runs[0].status == "running"
    assert len(started) == 1

    def duplicate_start(_settings: CloudChamberSettings, _manifest_path: Path) -> dict[str, object]:
        raise AssertionError("LAN start should not run twice")

    repeated = queue_campaign(
        matrix_path,
        settings=settings,
        lan_start=duplicate_start,
        lan_status=fake_running,
    )
    assert repeated.runs[0].status == "running"
    assert len(started) == 1

    running = status_campaign(matrix_path, settings=settings, lan_status=fake_running)
    assert running.runs[0].status == "running"

    not_ready = ingest_campaign(matrix_path, settings=settings, lan_status=fake_running)
    assert not_ready.runs[0].status == "running"
    assert not_ready.runs[0].ingest_status == "not_started"

    complete = status_campaign(matrix_path, settings=settings, lan_status=fake_complete)
    assert complete.runs[0].status == "completed_not_ingested"

    monkeypatch.setattr(
        surface_forced_campaign,
        "ingest_completed_run",
        lambda _manifest_path: SimpleNamespace(result_id="result-lan-campaign"),
    )
    ingested = ingest_campaign(
        matrix_path,
        settings=settings,
        lan_status=fake_complete,
        lan_collect=fake_collect,
    )

    assert ingested.runs[0].status == "ingested"
    assert ingested.runs[0].result_id == "result-lan-campaign"


def test_campaign_lan_queue_enforces_max_concurrent_runs(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path, queue_target="lan", include_comparison=True)
    started: list[Path] = []

    def fake_start(_settings: CloudChamberSettings, manifest_path: Path) -> dict[str, object]:
        started.append(manifest_path)
        return {"state": "running", "message": "LAN worker started"}

    result = queue_campaign(
        matrix_path,
        settings=settings,
        lan_start=fake_start,
    )
    runs = {run.matrix_id: run for run in result.runs}

    assert len(started) == 1
    assert runs["phase1_control_high_flux"].status == "running"
    assert runs["phase1_experiment_high_flux"].status == "blocked"
    assert "max_concurrent_runs=1" in (runs["phase1_experiment_high_flux"].message or "")


def test_campaign_report_summarizes_ingested_result_without_fabricating_bl_response(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    _write_fake_result_metadata(manifest_path)

    report_path = tmp_path / "report.md"
    summary_path = tmp_path / "summary.json"
    artifacts = report_campaign(
        matrix_path,
        settings=settings,
        report_path=report_path,
        summary_json_path=summary_path,
    )

    summary = artifacts.summary
    assert Path(artifacts.markdown_path) == report_path
    assert Path(artifacts.summary_json_path) == summary_path
    assert summary["status_counts"] == {"ingested": 1}
    assert summary["phase_gate_state"] == "forcing_wiring_verified_but_response_not_verified"
    run = summary["runs"][0]
    assert run["hfx_present"] is True
    assert run["qfx_present"] is True
    assert run["surface_moisture_flux_output_field"] == "qfx"
    assert run["qfx_units"] == "kg/m^2/s"
    assert run["lhfx_present"] is True
    assert run["low_level_qv_response"] == (
        "unavailable:low_level_response_diagnostic_not_implemented"
    )
    assert run["low_level_qv_response_method"] == "low_level_response_diagnostic_not_implemented"
    assert "low_level_qv_response" in summary["unavailable_diagnostics"]
    assert "max w 2.5" in report_path.read_text()


def test_campaign_report_marks_non_finite_outcomes_as_untrusted(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    _write_fake_result_metadata(
        manifest_path,
        surface_rain_present=True,
        run_caveats=[
            "non_finite_values_detected_in_qc",
            "qc_field_entirely_non_finite",
            "non_finite_values_detected_in_w",
            "non_finite_values_detected_in_qr",
            "qr_field_entirely_non_finite",
            "non_finite_values_detected_in_surface_rain",
            "surface_rain_field_entirely_non_finite",
        ],
    )

    artifacts = report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=tmp_path / "summary.json",
    )

    run = artifacts.summary["runs"][0]
    assert run["diagnostic_trust"]["qc"] == "untrusted_entirely_non_finite"
    assert run["diagnostic_trust"]["w"] == "caveated_non_finite_values_detected"
    assert run["diagnostic_trust"]["qr"] == "untrusted_entirely_non_finite"
    assert run["diagnostic_trust"]["surface_rain"] == "untrusted_entirely_non_finite"
    assert run["surface_rain_present"] == (
        "unavailable:untrusted_surface_rain_field_entirely_non_finite"
    )
    assert "surface_rain_field_entirely_non_finite" in run["diagnostic_quality_warnings"]

    report = Path(artifacts.markdown_path).read_text()
    assert "surface rain unavailable (untrusted)" in report
    assert "max w 2.5 (caveated)" in report
    assert "Diagnostic trust: `qc untrusted" in report
    assert "Field-quality warnings: `" in report
    assert "surface rain `True`" not in report


def test_campaign_report_treats_stale_lhfx_requirement_as_qfx_alias(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(update={"required_output_fields": ["hfx", "lhfx", "qv", "qc", "w"]}),
    )
    _write_fake_result_metadata(
        manifest_path,
        missing_required_output_fields=["lhfx"],
        warnings=["Recipe required output fields missing from NetCDF metadata: lhfx"],
    )

    artifacts = report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=tmp_path / "summary.json",
    )

    run = artifacts.summary["runs"][0]
    assert run["required_output_fields"] == ["hfx", "qfx", "qv", "qc", "w"]
    assert run["missing_output_fields"] == []
    assert run["warnings"] == []
    assert "missing_output_field:qfx" not in artifacts.summary["unavailable_diagnostics"]
    assert "missing_output_field:lhfx" not in artifacts.summary["unavailable_diagnostics"]
    report = Path(artifacts.markdown_path).read_text()
    assert "lhfx" not in report
    assert "Required/missing fields: `hfx, qfx, qv, qc, w` / `none`" in report


def test_campaign_report_normalizes_stale_lhfx_comparison_evidence(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path, include_comparison=True)
    matrix = yaml.safe_load(matrix_path.read_text())
    matrix["comparison_types"][0]["required_available_fields"] = ["hfx", "lhfx"]
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False))

    artifacts = report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=tmp_path / "summary.json",
    )

    assert artifacts.summary["runs"][0]["diagnostic_trust"] == {
        "qc": "unavailable_until_result_ingested",
        "w": "unavailable_until_result_ingested",
        "qr": "unavailable_until_result_ingested",
        "surface_rain": "unavailable_until_result_ingested",
        "dbz": "unavailable_until_result_ingested",
    }
    unavailable_evidence = artifacts.summary["comparisons"][0]["unavailable_evidence"]
    assert "control:missing_required_field:qfx" in unavailable_evidence
    assert "control:missing_required_field:lhfx" not in unavailable_evidence
    assert (
        "missing_output_field:unavailable:until_result_ingested"
        not in artifacts.summary["unavailable_diagnostics"]
    )
    report = Path(artifacts.markdown_path).read_text()
    assert "missing_required_field:qfx" in report
    assert "missing_required_field:lhfx" not in report


def test_campaign_report_evaluates_comparison_contract(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path, include_comparison=True)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    for state_run in packaged.runs:
        _write_fake_result_metadata(Path(state_run.manifest_path or ""))

    artifacts = report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=tmp_path / "summary.json",
    )

    comparisons = artifacts.summary["comparisons"]
    assert len(comparisons) == 1
    comparison = comparisons[0]
    assert comparison["comparison_type"] == "forcing_sensitivity_same_duration"
    assert comparison["control_matrix_id"] == "phase1_control_high_flux"
    assert comparison["experiment_matrix_id"] == "phase1_experiment_high_flux"
    assert comparison["status"] == "inconclusive_missing_evidence"
    assert comparison["equality_gate_failures"] == []
    assert "control:diagnostic_unavailable:low_level_response" in comparison["unavailable_evidence"]
    assert {
        "field": "surface_heat_flux_k_m_s",
        "control": 0.04,
        "experiment": 0.05,
    } in comparison["supported_differences"]
    assert "## Matched Comparisons" in Path(artifacts.markdown_path).read_text()


def test_campaign_ingest_updates_state_with_existing_completed_output(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    from cloud_chamber import surface_forced_campaign

    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    manifest = load_run_manifest(manifest_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    netcdf_path.write_text("fake netcdf placeholder")
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.COMPLETED,
                "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
                "outputs": OutputMetadata(netcdf_paths=[str(netcdf_path)]),
            }
        ),
    )

    monkeypatch.setattr(
        surface_forced_campaign,
        "ingest_completed_run",
        lambda _manifest_path: SimpleNamespace(result_id="result-surface-forced-test"),
    )

    result = surface_forced_campaign.ingest_campaign(matrix_path, settings=settings)

    assert result.runs[0].status == "ingested"
    assert result.runs[0].ingest_status == "ingested"
    assert result.runs[0].result_id == "result-surface-forced-test"


def _set_manifest_lifecycle(
    manifest_path: Path,
    lifecycle: LifecycleState,
    product_state: ProductState,
    *,
    netcdf_path: Path | None = None,
) -> None:
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": lifecycle,
                "provenance": ProvenanceMetadata(product_state=product_state),
                "outputs": OutputMetadata(
                    netcdf_paths=[str(netcdf_path)] if netcdf_path is not None else []
                ),
            }
        ),
    )


def _write_fake_result_metadata(
    manifest_path: Path,
    *,
    missing_required_output_fields: list[str] | None = None,
    warnings: list[str] | None = None,
    run_caveats: list[str] | None = None,
    interesting_time_caveats: list[str] | None = None,
    surface_rain_present: bool = False,
) -> None:
    manifest = load_run_manifest(manifest_path)
    now = datetime.now(UTC)
    result = ResultMetadata(
        result_id=f"result-{manifest.run_id}",
        run_id=manifest.run_id,
        scenario_id=manifest.scenario.id,
        physical_question=manifest.physical_question,
        controls=manifest.controls,
        run_configuration=manifest.run_configuration,
        source_lifecycle_state="completed",
        source_product_state="completed_cm1_result",
        source_model="CM1",
        input_source=manifest.input_source or "observed_sounding",
        input_source_label="Observed sounding",
        observed_sounding=manifest.observed_sounding,
        run_recipe=manifest.run_recipe,
        run_recipe_display_name=manifest.run_recipe_display_name,
        recipe_id=manifest.recipe_id,
        recipe_display_name=manifest.recipe_display_name,
        assumption_set_id=manifest.assumption_set_id,
        assumption_mode=manifest.assumption_mode,
        recipe_assumptions=manifest.recipe_assumptions,
        required_output_fields=manifest.required_output_fields,
        missing_required_output_fields=missing_required_output_fields or [],
        candidate_screening=manifest.candidate_screening,
        variables=["qc", "w", "qr", "rain", "dbz", "hfx", "qfx", "qv", "th"],
        fields_detected=[
            FieldMetadata(
                name="hfx", dimensions=["time", "y", "x"], shape=[2, 2, 2], units="K m/s"
            ),
            FieldMetadata(
                name="qfx", dimensions=["time", "y", "x"], shape=[2, 2, 2], units="kg/m^2/s"
            ),
            FieldMetadata(
                name="qv", dimensions=["time", "z", "y", "x"], shape=[2, 2, 2, 2], units="kg/kg"
            ),
            FieldMetadata(
                name="th", dimensions=["time", "z", "y", "x"], shape=[2, 2, 2, 2], units="K"
            ),
        ],
        diagnostics=ResultDiagnostics(
            cloud=CloudDiagnostics(
                formed=True,
                first_cloud_time_seconds=900.0,
                cloud_top_m=1800.0,
                cloud_top_time_series=[
                    TimeValue(time_seconds=900.0, value=900.0),
                    TimeValue(time_seconds=1800.0, value=1800.0),
                ],
                max_qc_kg_kg=2.0e-5,
                time_of_max_qc_seconds=1800.0,
            ),
            vertical_velocity=VerticalVelocityDiagnostics(
                max_w_m_s=2.5,
                time_of_max_w_seconds=1800.0,
                max_w_height_time_series=[
                    TimeValue(time_seconds=1800.0, value=2400.0),
                ],
                units="m/s",
            ),
            rain=RainDiagnostics(
                present=True,
                first_rain_time_seconds=2700.0,
                max_qr_kg_kg=1.0e-6,
                available=True,
            ),
            surface_rain=SurfaceRainDiagnostics(
                present=surface_rain_present,
                max_surface_rain=1.25 if surface_rain_present else 0.0,
                units="mm",
                available=True,
                field_absent=False,
            ),
            reflectivity=ReflectivityDiagnostics(
                max_dbz=32.0,
                units="dBZ",
                available=True,
                field_absent=False,
            ),
            time=TimeDiagnostics(source="time", fallback_used=False, coordinate_name="time"),
        ),
        run_caveats=run_caveats or [],
        science_summary=ScienceSummary(
            cloud_formed=True,
            deep_cloud_formed=False,
            strong_updraft_formed=False,
            first_cloud_time_seconds=900.0,
            first_cloud_time_label="900 s",
            time_of_first_deep_convection_seconds=None,
            max_qc_kg_kg=2.0e-5,
            max_qc_time_seconds=1800.0,
            max_updraft_w_m_s=2.5,
            max_updraft_time_seconds=1800.0,
            highest_cloud_top_m=1800.0,
            rain_onset_time_seconds=2700.0,
            max_qr_kg_kg=1.0e-6,
            max_rain_or_surface_precip=0.0,
            max_dbz_or_reflectivity_proxy=32.0,
            latest_output_time_seconds=3600.0,
            default_explore_time_index=1,
            default_explore_time_seconds=1800.0,
            interesting_time_support_state="supported",
        ),
        warnings=warnings or [],
        interesting_time_caveats=interesting_time_caveats or [],
        created_at=now,
        updated_at=now,
    )
    (manifest_path.parent / RESULT_METADATA_FILENAME).write_text(result.to_json_text())


def test_campaign_summary_json_is_plain_json(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    package_campaign(matrix_path, settings=settings, resume=True)
    summary_path = tmp_path / "summary.json"

    report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=summary_path,
    )

    loaded = json.loads(summary_path.read_text())
    assert loaded["campaign_id"] == "surface_forced_test"
