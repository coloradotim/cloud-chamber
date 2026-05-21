from datetime import UTC, datetime

import pytest

from cloud_chamber.run_manifest import (
    LifecycleState,
    ProductState,
    RunManifestError,
    run_manifest_from_json,
    validate_run_manifest,
)


def valid_manifest_data() -> dict[str, object]:
    created_at = datetime(2026, 5, 21, 12, 0, tzinfo=UTC).isoformat()
    return {
        "manifest_version": "1",
        "run_id": "run-001",
        "scenario": {
            "id": "baseline-shallow-cumulus",
            "schema_version": "1",
            "template_path": "scenarios/lower-atmosphere/baseline-shallow-cumulus.json",
        },
        "controls": {"low_level_humidity": "baseline", "surface_heating": "baseline"},
        "run_size_preset": "quick_look",
        "physical_question": "How do moisture and heating shape shallow cumulus?",
        "expected_diagnostics": ["first_cloud_time", "cloud_base_top", "cloud_water_summary"],
        "generated_inputs": {
            "run_directory": "~/CloudChamber/runs/run-001",
            "manifest_path": "~/CloudChamber/runs/run-001/run_manifest.json",
            "namelist_input": "~/CloudChamber/runs/run-001/namelist.input",
            "input_sounding": "~/CloudChamber/runs/run-001/input_sounding",
            "dry_run_report": "~/CloudChamber/runs/run-001/dry_run_report.json",
            "runtime_file_checklist": ["LANDUSE.TBL"],
        },
        "runtime_paths": {
            "runtime_home": "~/CloudChamber",
            "cm1_root": "/Users/timpeterson/cm1r21.1",
            "cm1_run_dir": "/Users/timpeterson/cm1r21.1/run",
            "cache_dir": "~/CloudChamber/cache",
            "log_dir": "~/CloudChamber/logs",
        },
        "app": {"app_version": "0.1.0", "commit": "abc123", "created_by": "Cloud Chamber"},
        "lifecycle_state": "packaged",
        "validation_status": "valid",
        "provenance": {
            "source_model": "CM1",
            "product_state": "packaged_dry_run_output",
            "preview_is_guidance_only": True,
            "visualizer_is_interpretation": True,
        },
        "created_at": created_at,
        "updated_at": created_at,
        "execution": {"command": []},
        "outputs": {"netcdf_paths": [], "processed_artifacts": []},
        "user": {"name": "Baseline check", "tags": ["golden-path"], "saved": False},
    }


def test_valid_packaged_manifest_does_not_require_netcdf_output() -> None:
    manifest = validate_run_manifest(valid_manifest_data())

    assert manifest.lifecycle_state == LifecycleState.PACKAGED
    assert manifest.provenance.product_state == ProductState.PACKAGED_DRY_RUN_OUTPUT
    assert manifest.outputs.netcdf_paths == []


def test_manifest_serializes_and_deserializes() -> None:
    manifest = validate_run_manifest(valid_manifest_data())

    round_tripped = run_manifest_from_json(manifest.to_json_text())

    assert round_tripped == manifest


def test_invalid_lifecycle_state_fails() -> None:
    data = valid_manifest_data()
    data["lifecycle_state"] = "almost_running"

    with pytest.raises(RunManifestError, match="almost_running"):
        validate_run_manifest(data)


def test_packaged_manifest_cannot_include_netcdf_outputs() -> None:
    data = valid_manifest_data()
    outputs = data["outputs"]
    assert isinstance(outputs, dict)
    outputs["netcdf_paths"] = ["cm1out_000001.nc"]

    with pytest.raises(RunManifestError, match="must not include NetCDF"):
        validate_run_manifest(data)


def test_saved_manifest_requires_user_saved_flag() -> None:
    data = valid_manifest_data()
    data["lifecycle_state"] = "saved"
    provenance = data["provenance"]
    assert isinstance(provenance, dict)
    provenance["product_state"] = "saved_result_notebook_entry"

    with pytest.raises(RunManifestError, match="must set user.saved"):
        validate_run_manifest(data)


def test_completed_manifest_cannot_be_dry_run_package() -> None:
    data = valid_manifest_data()
    data["lifecycle_state"] = "completed"

    with pytest.raises(RunManifestError, match="cannot be dry-run packages"):
        validate_run_manifest(data)
