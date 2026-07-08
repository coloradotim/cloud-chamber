import json
from pathlib import Path

import pytest
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.dry_run_package import DryRunPackageError, generate_dry_run_package
from cloud_chamber.observed_sounding import ObservedSoundingLevel, parse_igra_station_text
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


def _level_at_rendered_z(
    levels: list[ObservedSoundingLevel], rendered_z: float
) -> ObservedSoundingLevel:
    return next(level for level in levels if level.model_z_m == pytest.approx(rendered_z))


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
    assert report["estimated_cost_or_size"] == (
        "Normal local run-size preset; estimates remain approximate until local validation."
    )
    assert report["physical_question"] == manifest.physical_question
    assert report["visualization_defaults"]["primary_field"] == "qc"
    assert report["run_size_details"]["runtime_seconds"] == 21600
    assert report["run_size_details"]["output_cadence_seconds"] == 3600
    assert report["run_size_details"]["expected_output_frames"] == 7


def test_dry_run_package_can_use_observed_igra_sounding(tmp_path: Path) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding

    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-observed-sounding",
        run_size_preset="quick_look",
        observed_sounding=observed,
    )

    manifest = load_run_manifest(result.manifest_path)
    report = json.loads(result.report_path.read_text())
    case_manifest = json.loads((result.package_dir / "case_manifest.json").read_text())
    sounding = (result.package_dir / "input_sounding").read_text()
    namelist = (result.package_dir / "namelist.input").read_text()

    assert manifest.observed_sounding is not None
    assert manifest.observed_sounding["station_id"] == "USM00072558"
    assert manifest.observed_sounding["model_bottom_elevation_m_msl"] == pytest.approx(351.5)
    assert report["variant_metadata"]["sounding_source"] == "observed_igra_station_text"
    assert report["observed_sounding"]["station_name"] == "Valley, Nebraska"
    assert report["observed_sounding"]["usable_levels"] >= 5
    assert report["observed_sounding"]["wind_source"] == "observed_igra_wind_profile"
    assert report["observed_sounding"]["wind_units"] == "m/s"
    assert "input_sounding" in report["observed_sounding"]["wind_conversion"]
    assert case_manifest["contract"]["observed_sounding"]["station_id"] == "USM00072558"
    assert "isnd      =  7," in namelist
    assert "iwnd      =  0," in namelist
    assert "USM00072558" not in sounding
    assert float(sounding.splitlines()[1].split()[0]) == pytest.approx(observed.levels[0].model_z_m)
    first_body_z = float(sounding.splitlines()[1].split()[0])
    first_body_level = _level_at_rendered_z(observed.levels, first_body_z)
    assert float(sounding.splitlines()[1].split()[3]) == pytest.approx(
        first_body_level.u_wind_m_s,
        abs=0.01,
    )
    assert float(sounding.splitlines()[1].split()[4]) == pytest.approx(
        first_body_level.v_wind_m_s,
        abs=0.01,
    )
    assert float(sounding.splitlines()[-1].split()[0]) > 18000


def test_deep_convection_trial_package_uses_observed_sounding_and_warm_bubble(
    tmp_path: Path,
) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding
    candidate_screening = {
        "candidate_id": "USM00072558-deep-test",
        "primary_story": "supercell_environment",
        "rank_score": 91.0,
    }

    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-deep-convection-trial",
        run_size_preset="quick_look",
        package_family="deep_convection_trial",
        observed_sounding=observed,
        candidate_screening=candidate_screening,
    )

    manifest = load_run_manifest(result.manifest_path)
    report = json.loads(result.report_path.read_text())
    case_manifest = json.loads((result.package_dir / "case_manifest.json").read_text())
    namelist = (result.package_dir / "namelist.input").read_text()
    sounding = (result.package_dir / "input_sounding").read_text()

    assert manifest.package_family == "deep_convection_trial"
    assert manifest.package_display_name == "Deep Convection Trial"
    assert manifest.input_source == "observed_sounding"
    assert manifest.trigger_type == "warm_bubble"
    assert manifest.trigger_parameters == {
        "cm1_iinit": 3,
        "cm1_trigger": (
            "CM1 built-in three warm bubbles with 2 K maximum potential-temperature "
            "perturbations in a line near 1.4 km AGL"
        ),
        "raw_controls_exposed": False,
    }
    assert "dbz" in manifest.expected_outputs
    assert "updraft_helicity" in manifest.expected_outputs
    assert manifest.manual_validation_status == "deep_convection_trial_package_smoke_validated"
    assert any(
        "Manual smoke evidence applies to the Deep Convection Trial package family" in caveat
        and "each observed sounding remains an experiment" in caveat
        for caveat in manifest.package_caveats
    )
    assert manifest.candidate_screening == candidate_screening
    assert report["package_family"] == "deep_convection_trial"
    assert report["package_display_name"] == "Deep Convection Trial"
    assert report["trigger_type"] == "warm_bubble"
    assert report["candidate_screening"] == candidate_screening
    assert "testcase=0" in report["variant_metadata"]["mapping"]
    assert "iinit=3 three-warm-bubble" in report["variant_metadata"]["mapping"]
    assert "reflectivity output" in report["variant_metadata"]["mapping"]
    assert report["manual_validation_status"] == "deep_convection_trial_package_smoke_validated"
    assert "manual CM1 smoke evidence" in report["cm1_mapping_status"]
    assert "each observed sounding remains an experiment" in report["cm1_mapping_status"]
    assert case_manifest["package_family"] == "deep_convection_trial"
    assert case_manifest["contract"]["package_family"] == "deep_convection_trial"
    assert (
        case_manifest["contract"]["manual_validation_status"]
        == "deep_convection_trial_package_smoke_validated"
    )

    assert "testcase  =  0," in namelist
    assert "isnd      =  7," in namelist
    assert "iwnd      =  0," in namelist
    assert "iinit     =  3," in namelist
    assert "irandp    =  0," in namelist
    assert "imove     =  1," in namelist
    assert "ptype     =  5," in namelist
    assert "ihail     =  1," in namelist
    assert "iautoc    =  1," in namelist
    assert "output_rain      = 1," in namelist
    assert "output_dbz       = 1," in namelist
    assert "output_vort      = 1," in namelist
    assert "output_uh        = 1," in namelist
    assert "nx           =      120," in namelist
    assert "ny           =      120," in namelist
    assert "nz           =      40," in namelist
    assert "dx     =   1000.0," in namelist
    assert "dy     =   1000.0," in namelist
    assert "dz     =   500.0," in namelist
    assert "dtl    =   6.000," in namelist
    assert "timax  = 7200.0," in namelist
    assert "tapfrq =  600.0," in namelist
    assert "zd      =  15000.0," in namelist
    assert float(sounding.splitlines()[-1].split()[0]) >= 20000.0
    first_body_z = float(sounding.splitlines()[1].split()[0])
    first_body_level = _level_at_rendered_z(observed.levels, first_body_z)
    assert float(sounding.splitlines()[1].split()[3]) == pytest.approx(
        first_body_level.u_wind_m_s,
        abs=0.01,
    )
    assert float(sounding.splitlines()[1].split()[4]) == pytest.approx(
        first_body_level.v_wind_m_s,
        abs=0.01,
    )


def test_deep_convection_trial_requires_observed_sounding(tmp_path: Path) -> None:
    with pytest.raises(DryRunPackageError, match="requires a validated observed sounding"):
        generate_dry_run_package(
            scenario_data=load_baseline_template(),
            runtime_home=tmp_path,
            run_id="run-deep-no-sounding",
            package_family="deep_convection_trial",
        )


def test_deep_convection_trial_requires_observed_wind_components(tmp_path: Path) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding
    no_wind = observed.model_copy(
        update={
            "levels": [
                level.model_copy(update={"u_wind_m_s": None, "v_wind_m_s": None})
                for level in observed.levels
            ]
        }
    )

    with pytest.raises(DryRunPackageError, match="complete finite observed u/v wind profile"):
        generate_dry_run_package(
            scenario_data=load_baseline_template(),
            runtime_home=tmp_path,
            run_id="run-deep-no-wind",
            package_family="deep_convection_trial",
            observed_sounding=no_wind,
        )


def test_deep_convection_trial_requires_complete_rendered_wind_profile(
    tmp_path: Path,
) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding
    missing_mid_profile_wind = observed.model_copy(
        update={
            "levels": [
                level.model_copy(update={"u_wind_m_s": None})
                if index == len(observed.levels) // 2
                else level
                for index, level in enumerate(observed.levels)
            ]
        }
    )

    with pytest.raises(DryRunPackageError, match="complete finite observed u/v wind profile"):
        generate_dry_run_package(
            scenario_data=load_baseline_template(),
            runtime_home=tmp_path,
            run_id="run-deep-partial-wind",
            package_family="deep_convection_trial",
            observed_sounding=missing_mid_profile_wind,
        )

    assert not (tmp_path / "runs" / "run-deep-partial-wind").exists()


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


def test_dry_run_package_deep_overnight_reports_resolution_and_cost(tmp_path: Path) -> None:
    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-deep-001",
        run_size_preset="deep_overnight",
    )
    namelist = (result.package_dir / "namelist.input").read_text()
    report = json.loads(result.report_path.read_text())
    details = report["run_size_details"]

    assert report["run_size_preset"] == "deep_overnight"
    assert "Deep Overnight is an expensive local run" in report["estimated_cost_or_size"]
    assert details["nx"] == 192
    assert details["ny"] == 192
    assert details["nz"] == 75
    assert details["dx_m"] == pytest.approx(33.3333333333)
    assert details["dy_m"] == pytest.approx(33.3333333333)
    assert details["dz_m"] == 40
    assert details["runtime_seconds"] == 21600
    assert details["output_cadence_seconds"] == 300
    assert details["expected_output_frames"] == 73
    assert details["grid_cell_multiplier_vs_standard"] == 9.0
    assert details["time_step_seconds"] == 3.0
    assert details["time_step_multiplier_vs_standard"] == 1.0
    assert details["output_frame_multiplier_vs_standard"] == 10.43
    assert details["estimated_compute_multiplier_vs_standard"] == 9.0
    assert details["estimated_output_volume_multiplier_vs_standard"] == 93.86
    assert details["target_wall_clock_multiplier_vs_standard"] == "10-12x"
    assert "keeps the Standard CM1 solver timestep" in details["time_step_note"]

    assert "nx           =      192," in namelist
    assert "ny           =      192," in namelist
    assert "dx     =   33.333," in namelist
    assert "dy     =   33.333," in namelist
    assert "dtl    =   3.000," in namelist
    assert "tapfrq =  300.0," in namelist


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
