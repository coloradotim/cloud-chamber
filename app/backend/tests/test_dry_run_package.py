import json
from pathlib import Path

import pytest

from cloud_chamber.dry_run_package import DryRunPackageError, generate_dry_run_package
from cloud_chamber.run_manifest import load_run_manifest

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"


def load_baseline_template() -> object:
    return json.loads(BASELINE_TEMPLATE.read_text())


def test_generate_dry_run_package_writes_expected_files_to_temp_runtime_home(
    tmp_path: Path,
) -> None:
    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-001",
        controls={"low_level_humidity": "more_humid"},
        run_size_preset="quick_look",
    )

    assert result.package_dir == tmp_path / "runs" / "run-001"
    assert {path.name for path in result.generated_files} == {
        "run_manifest.json",
        "case_manifest.json",
        "namelist.input",
        "input_sounding",
        "dry_run_report.json",
        "runtime_file_checklist.json",
    }
    assert all(path.exists() for path in result.generated_files)
    assert str(REPO_ROOT) not in str(result.package_dir)


def test_dry_run_manifest_and_report_include_golden_path_metadata(tmp_path: Path) -> None:
    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-002",
        run_size_preset="standard",
    )

    manifest = load_run_manifest(result.manifest_path)
    report = json.loads(result.report_path.read_text())

    assert manifest.lifecycle_state.value == "packaged"
    assert manifest.run_size_preset == "standard"
    assert manifest.scenario.id == "baseline-shallow-cumulus"
    assert "first_cloud_time" in manifest.expected_diagnostics
    assert report["not_a_completed_cm1_result"] is True
    assert report["cm1_was_launched"] is False
    assert report["estimated_cost_or_size"] == "unknown until validated"
    assert report["physical_question"] == manifest.physical_question
    assert report["visualization_defaults"]["primary_field"] == "qc"


def test_dry_run_package_refuses_to_overwrite_existing_run_dir(tmp_path: Path) -> None:
    generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-003",
    )

    with pytest.raises(DryRunPackageError, match="already exists"):
        generate_dry_run_package(
            scenario_data=load_baseline_template(),
            runtime_home=tmp_path,
            run_id="run-003",
        )


def test_dry_run_package_validates_controls_before_writing(tmp_path: Path) -> None:
    with pytest.raises(DryRunPackageError, match="Unknown controls"):
        generate_dry_run_package(
            scenario_data=load_baseline_template(),
            runtime_home=tmp_path,
            run_id="run-004",
            controls={"missing_control": "value"},
        )

    assert not (tmp_path / "runs" / "run-004").exists()


def test_dry_run_package_writes_cm1_ready_inputs_not_outputs(tmp_path: Path) -> None:
    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-005",
    )
    namelist = (result.package_dir / "namelist.input").read_text()
    sounding = (result.package_dir / "input_sounding").read_text()

    assert "&param0" in namelist
    assert "testcase  =  3," in namelist
    assert "&cloud_chamber_domain" not in namelist
    assert "placeholder until local/manual CM1 validation" not in namelist
    assert len(sounding.splitlines()[0].split()) == 3
    assert "Cloud Chamber input_sounding notes" not in sounding
    assert not list(result.package_dir.glob("*.nc"))
