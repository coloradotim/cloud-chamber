import json
from pathlib import Path

import pytest

from cloud_chamber.dry_run_package import DryRunPackageError, generate_dry_run_package
from cloud_chamber.run_manifest import load_run_manifest

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"
DRY_FAILED_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/dry-failed-cumulus.json"
CAPPED_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/capped-suppressed-cumulus.json"


def load_baseline_template() -> object:
    return json.loads(BASELINE_TEMPLATE.read_text())


def load_dry_failed_template() -> object:
    return json.loads(DRY_FAILED_TEMPLATE.read_text())


def load_capped_template() -> object:
    return json.loads(CAPPED_TEMPLATE.read_text())


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
        run_size_preset="standard",
    )
    namelist = (result.package_dir / "namelist.input").read_text()
    sounding = (result.package_dir / "input_sounding").read_text()

    assert "&param0" in namelist
    assert "testcase  =  3," in namelist
    assert "nx           =      64," in namelist
    assert "ny           =      64," in namelist
    assert "nz           =      75," in namelist
    assert "dx     =   100.0," in namelist
    assert "dy     =   100.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "timax  = 21600.0," in namelist
    assert "tapfrq =  3600.0," in namelist
    assert "ztop      = 18000.0," in namelist
    assert "set_znt    =      0," in namelist
    assert "cnst_znt   =   0.00," in namelist
    assert "set_ust    =      1," in namelist
    assert "cnst_ust   =   0.28," in namelist
    assert "isnd      = 17," in namelist
    assert "iwnd      =  9," in namelist
    assert "&cloud_chamber_domain" not in namelist
    assert "placeholder until local/manual CM1 validation" not in namelist
    assert len(sounding.splitlines()[0].split()) == 3
    assert float(sounding.splitlines()[-1].split()[0]) > 18000
    assert "Cloud Chamber input_sounding notes" not in sounding
    assert not list(result.package_dir.glob("*.nc"))

    checklist = json.loads((result.package_dir / "runtime_file_checklist.json").read_text())
    assert checklist["source_candidates"]["LANDUSE.TBL"][0] == (
        "config_files/les_ShallowCu/LANDUSE.TBL"
    )


def test_dry_run_package_quick_look_changes_only_runtime_timing(tmp_path: Path) -> None:
    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-006",
        run_size_preset="quick_look",
    )
    namelist = (result.package_dir / "namelist.input").read_text()
    report = json.loads(result.report_path.read_text())

    assert report["run_size_preset"] == "quick_look"
    assert "timax  = 10800.0," in namelist
    assert "tapfrq =  900.0," in namelist
    assert "nx           =      64," in namelist
    assert "ny           =      64," in namelist
    assert "nz           =      75," in namelist
    assert "dx     =   100.0," in namelist
    assert "dy     =   100.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "ztop      = 18000.0," in namelist
    assert "set_znt    =      0," in namelist
    assert "set_ust    =      1," in namelist
    assert "cnst_ust   =   0.28," in namelist
    assert "testcase  =  3," in namelist
    assert "isnd      = 17," in namelist
    assert "iwnd      =  9," in namelist
    assert "output_format    = 2," in namelist


def test_baseline_humidity_ladder_packages_change_only_sounding_moisture(
    tmp_path: Path,
) -> None:
    drier = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-baseline-drier",
        controls={"low_level_humidity": "drier"},
        run_size_preset="quick_look",
    )
    baseline = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-baseline",
        controls={"low_level_humidity": "baseline"},
        run_size_preset="quick_look",
    )
    more_humid = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-baseline-more-humid",
        controls={"low_level_humidity": "more_humid"},
        run_size_preset="quick_look",
    )

    baseline_namelist = (baseline.package_dir / "namelist.input").read_text()
    drier_namelist = (drier.package_dir / "namelist.input").read_text()
    humid_namelist = (more_humid.package_dir / "namelist.input").read_text()
    drier_sounding = (drier.package_dir / "input_sounding").read_text().splitlines()
    baseline_sounding = (baseline.package_dir / "input_sounding").read_text().splitlines()
    humid_sounding = (more_humid.package_dir / "input_sounding").read_text().splitlines()
    drier_report = json.loads(drier.report_path.read_text())
    humid_report = json.loads(more_humid.report_path.read_text())
    drier_manifest = load_run_manifest(drier.manifest_path)

    assert drier_namelist == baseline_namelist == humid_namelist
    assert "timax  = 10800.0," in baseline_namelist
    assert "tapfrq =  900.0," in baseline_namelist
    assert "testcase  =  3," in baseline_namelist
    assert "isnd      = 17," in baseline_namelist
    assert "iwnd      =  9," in baseline_namelist
    assert "set_znt    =      0," in baseline_namelist
    assert "set_ust    =      1," in baseline_namelist
    assert "cnst_ust   =   0.28," in baseline_namelist
    assert "output_format    = 2," in baseline_namelist

    assert drier_manifest.controls["low_level_humidity"] == "drier"
    assert drier_report["variant_metadata"]["moisture_profile"] == "drier"
    assert humid_report["variant_metadata"]["moisture_profile"] == "more_humid"
    assert drier_report["controls"]["low_level_humidity"] == "drier"
    assert humid_report["controls"]["low_level_humidity"] == "more_humid"

    assert float(drier_sounding[0].split()[2]) < float(baseline_sounding[0].split()[2])
    assert float(humid_sounding[0].split()[2]) > float(baseline_sounding[0].split()[2])
    assert float(drier_sounding[1].split()[2]) < float(baseline_sounding[1].split()[2])
    assert float(humid_sounding[1].split()[2]) > float(baseline_sounding[1].split()[2])
    assert drier_sounding[1].split()[0:2] == baseline_sounding[1].split()[0:2]
    assert humid_sounding[1].split()[0:2] == baseline_sounding[1].split()[0:2]
    assert drier_sounding[1].split()[3:] == baseline_sounding[1].split()[3:]
    assert humid_sounding[1].split()[3:] == baseline_sounding[1].split()[3:]
    assert not list(drier.package_dir.glob("*.nc"))
    assert not list(more_humid.package_dir.glob("*.nc"))


def test_dry_failed_package_preserves_baseline_namelist_and_drives_sounding_drier(
    tmp_path: Path,
) -> None:
    baseline = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-baseline",
        run_size_preset="quick_look",
    )
    dry_failed = generate_dry_run_package(
        scenario_data=load_dry_failed_template(),
        runtime_home=tmp_path,
        run_id="run-dry-failed",
        run_size_preset="quick_look",
    )

    baseline_namelist = (baseline.package_dir / "namelist.input").read_text()
    dry_namelist = (dry_failed.package_dir / "namelist.input").read_text()
    baseline_sounding = (baseline.package_dir / "input_sounding").read_text().splitlines()
    dry_sounding = (dry_failed.package_dir / "input_sounding").read_text().splitlines()
    dry_report = json.loads(dry_failed.report_path.read_text())

    assert dry_report["scenario_id"] == "dry-failed-cumulus"
    assert dry_report["controls"]["low_level_humidity"] == "drier"
    assert "timax  = 10800.0," in dry_namelist
    assert "tapfrq =  900.0," in dry_namelist
    assert "isnd      = 17," in dry_namelist
    assert "iwnd      =  9," in dry_namelist
    assert "output_format    = 2," in dry_namelist
    assert dry_namelist == baseline_namelist
    assert len(dry_sounding) == len(baseline_sounding)
    assert float(dry_sounding[0].split()[2]) < float(baseline_sounding[0].split()[2])
    assert float(dry_sounding[1].split()[2]) < float(baseline_sounding[1].split()[2])
    assert dry_sounding[1].split()[0:2] == baseline_sounding[1].split()[0:2]
    assert dry_sounding[1].split()[3:] == baseline_sounding[1].split()[3:]
    assert dry_sounding[-1] == baseline_sounding[-1]


def test_capped_suppressed_package_preserves_baseline_namelist_and_strengthens_cap(
    tmp_path: Path,
) -> None:
    baseline = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-baseline",
        run_size_preset="quick_look",
    )
    capped = generate_dry_run_package(
        scenario_data=load_capped_template(),
        runtime_home=tmp_path,
        run_id="run-capped",
        run_size_preset="quick_look",
    )

    baseline_namelist = (baseline.package_dir / "namelist.input").read_text()
    capped_namelist = (capped.package_dir / "namelist.input").read_text()
    baseline_sounding = (baseline.package_dir / "input_sounding").read_text().splitlines()
    capped_sounding = (capped.package_dir / "input_sounding").read_text().splitlines()
    capped_report = json.loads(capped.report_path.read_text())
    capped_manifest = load_run_manifest(capped.manifest_path)

    assert capped_report["scenario_id"] == "capped-suppressed-cumulus"
    assert capped_report["controls"]["cap_strength"] == "stronger"
    assert capped_report["controls"]["cap_height"] == "baseline"
    assert capped_report["variant_metadata"]["moisture_profile"] == "baseline"
    assert capped_report["variant_metadata"]["stability_profile"] == "stronger_cap"
    assert capped_manifest.controls["cap_strength"] == "stronger"
    assert capped_namelist == baseline_namelist
    assert "timax  = 10800.0," in capped_namelist
    assert "tapfrq =  900.0," in capped_namelist
    assert "isnd      = 17," in capped_namelist
    assert "output_format    = 2," in capped_namelist

    assert len(capped_sounding) == len(baseline_sounding)
    assert capped_sounding[0] == baseline_sounding[0]
    assert capped_sounding[1] == baseline_sounding[1]
    assert capped_sounding[2] == baseline_sounding[2]
    for baseline_line, capped_line in zip(
        baseline_sounding[1:],
        capped_sounding[1:],
        strict=True,
    ):
        baseline_parts = baseline_line.split()
        capped_parts = capped_line.split()
        assert capped_parts[0] == baseline_parts[0]
        assert capped_parts[2:] == baseline_parts[2:]

    assert float(capped_sounding[3].split()[1]) > float(baseline_sounding[3].split()[1])
    assert float(capped_sounding[4].split()[1]) > float(baseline_sounding[4].split()[1])
    assert float(capped_sounding[5].split()[1]) > float(baseline_sounding[5].split()[1])
    assert capped_sounding[6] == baseline_sounding[6]
    assert not list(capped.package_dir.glob("*.nc"))
