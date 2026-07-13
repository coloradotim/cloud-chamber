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
    )

    manifest = load_run_manifest(result.manifest_path)
    report = json.loads(result.report_path.read_text())

    assert manifest.lifecycle_state.value == "packaged"
    assert manifest.run_configuration["duration"] == "short_6h"
    assert manifest.run_configuration["domain_size"] == "local_6km"
    assert manifest.pre_run_validation_report is not None
    assert manifest.pre_run_validation_report["hypothesis_recipe_alignment"]["status"] == "aligned"
    assert manifest.scenario.id == "baseline-shallow-cumulus"
    assert "first_cloud_time" in manifest.expected_diagnostics
    assert report["not_a_completed_cm1_result"] is True
    assert report["cm1_was_launched"] is False
    assert report["estimated_cost_or_size"] == (
        "Configuration cost depends on duration, horizontal cells, domain, cadence, "
        "and full output volume. Review the CM1-facing values before launch."
    )
    assert report["physical_question"] == manifest.physical_question
    assert report["visualization_defaults"]["primary_field"] == "qc"
    assert (
        report["run_configuration"]["configuration_id"]
        == (manifest.run_configuration["configuration_id"])
    )
    assert report["pre_run_validation_report"] == manifest.pre_run_validation_report
    assert report["pre_run_validation_report"]["run_shape_validation"]["estimated_frames"] == 25
    summary = report["run_configuration_summary"]
    assert summary["runtime_seconds"] == 21600
    assert summary["output_cadence_seconds"] == 900
    assert summary["expected_output_frames"] == 25


def test_dry_run_package_can_use_observed_igra_sounding(tmp_path: Path) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding

    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-observed-sounding",
        observed_sounding=observed,
        user_tags=["compare", "candidate", "compare"],
        user_notes="  Compare against humid/rainy candidates.  ",
    )

    manifest = load_run_manifest(result.manifest_path)
    report = json.loads(result.report_path.read_text())
    case_manifest = json.loads((result.package_dir / "case_manifest.json").read_text())
    sounding = (result.package_dir / "input_sounding").read_text()
    namelist = (result.package_dir / "namelist.input").read_text()

    assert manifest.observed_sounding is not None
    assert manifest.observed_sounding["station_id"] == "USM00072558"
    assert manifest.observed_sounding["model_bottom_elevation_m_msl"] == pytest.approx(351.5)
    assert manifest.run_configuration["domain_size"] == "wide_12km"
    assert manifest.run_configuration["cm1_values"]["nx"] == 128
    assert manifest.run_configuration["cm1_values"]["runtime_seconds"] == 21600
    assert manifest.run_recipe == "observed_surface_forced_evolution"
    assert manifest.recipe_id == "observed_surface_forced_evolution_v0"
    assert manifest.recipe_display_name == "Observed Surface-Forced Evolution v0"
    assert manifest.assumption_set_id == "observed_surface_forced_evolution_v0_assumptions"
    assert manifest.assumption_mode == "observed_surface_forced_evolution"
    assert manifest.required_output_fields == ["qv", "qc", "w", "qr", "rain", "dbz", "hfx", "qfx"]
    assert manifest.recipe_assumptions["trigger"]["mode"] == "none"
    assert manifest.recipe_assumptions["radiation"]["mode"] == "disabled"
    assert manifest.recipe_assumptions["large_scale_forcing"]["mode"] == "none"
    assert manifest.recipe_assumptions["surface_fluxes"]["mode"] == (
        "constant_uniform_surface_flux_proxy"
    )
    assert manifest.recipe_assumptions["surface_fluxes"]["cm1_values"]["cnst_shflx"] == 8.0e-3
    assert manifest.recipe_assumptions["surface_fluxes"]["cm1_values"]["cnst_lhflx"] == 5.2e-5
    assert "No artificial atmospheric trigger is applied." in manifest.recipe_caveats
    assert "No artificial atmospheric trigger is applied." in manifest.run_caveats
    assert manifest.pre_run_validation_report is not None
    assert manifest.pre_run_validation_report["input_validation"]["observed_wind_profile"] == (
        "present_required"
    )
    assert manifest.pre_run_validation_report["run_shape_validation"]["domain"] == "wide_12km"
    assert manifest.pre_run_validation_report["selected_run_recipe"]["run_recipe"] == (
        "observed_surface_forced_evolution"
    )
    assert manifest.pre_run_validation_report["selected_run_recipe"]["recipe_id"] == (
        "observed_surface_forced_evolution_v0"
    )
    assert manifest.pre_run_validation_report["selected_run_recipe"]["required_fields"] == [
        "qv",
        "qc",
        "w",
        "qr",
        "rain",
        "dbz",
        "hfx",
        "qfx",
    ]
    assert manifest.user.tags == ["compare", "candidate"]
    assert manifest.user.notes == "Compare against humid/rainy candidates."
    assert report["recipe_id"] == "observed_surface_forced_evolution_v0"
    assert report["assumption_mode"] == "observed_surface_forced_evolution"
    assert report["required_output_fields"] == ["qv", "qc", "w", "qr", "rain", "dbz", "hfx", "qfx"]
    assert report["variant_metadata"]["sounding_source"] == "observed_igra_station_text"
    assert report["variant_metadata"]["surface_flux_mode"] == (
        "constant_uniform_surface_flux_proxy"
    )
    assert report["run_configuration_summary"]["surface_flux_summary"] == (
        "Surface heat flux 0.008 K m/s; surface moisture flux 5.2e-05 g/g m/s; "
        "constant uniform proxy"
    )
    assert (
        report["pre_run_validation_report"]["forcing_validation"]["surface_fluxes"]["mode"]
        == "constant_uniform_surface_flux_proxy"
    )
    assert report["observed_sounding"]["station_name"] == "Valley, Nebraska"
    assert report["user"]["tags"] == ["compare", "candidate"]
    assert report["user"]["notes"] == "Compare against humid/rainy candidates."
    assert report["observed_sounding"]["usable_levels"] >= 5
    assert report["observed_sounding"]["wind_source"] == "observed_igra_wind_profile"
    assert report["observed_sounding"]["wind_units"] == "m/s"
    assert "input_sounding" in report["observed_sounding"]["wind_conversion"]
    assert case_manifest["recipe_id"] == "observed_surface_forced_evolution_v0"
    assert case_manifest["contract"]["recipe_id"] == "observed_surface_forced_evolution_v0"
    assert case_manifest["contract"]["observed_sounding"]["station_id"] == "USM00072558"
    assert "isnd      =  7," in namelist
    assert "iwnd      =  0," in namelist
    assert "cnst_shflx = 8.0e-3," in namelist
    assert "cnst_lhflx = 5.2e-5," in namelist
    assert "output_sfcflx    = 1," in namelist
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


def test_observed_dry_run_package_persists_surface_flux_proxy_choices(
    tmp_path: Path,
) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding

    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-observed-surface-flux",
        observed_sounding=observed,
        run_configuration={
            "duration": "short_6h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "wide_12km",
            "output_cadence": "standard_15min",
            "diagnostic_set": "essential",
            "surface_heat_flux_k_m_s": 4.0e-2,
            "surface_moisture_flux_g_g_m_s": 1.0e-4,
        },
    )

    manifest = load_run_manifest(result.manifest_path)
    report = json.loads(result.report_path.read_text())
    namelist = (result.package_dir / "namelist.input").read_text()

    assert manifest.run_configuration["surface_heat_flux_k_m_s"] == 4.0e-2
    assert manifest.run_configuration["surface_moisture_flux_g_g_m_s"] == 1.0e-4
    assert manifest.run_configuration["surface_flux_cm1_values"]["cnst_shflx"] == 4.0e-2
    assert manifest.run_configuration["surface_flux_cm1_values"]["cnst_lhflx"] == 1.0e-4
    assert (
        manifest.recipe_assumptions["surface_fluxes"]["product_selections"][
            "surface_heat_flux_k_m_s"
        ]
        == 4.0e-2
    )
    assert (
        manifest.recipe_assumptions["surface_fluxes"]["product_selections"][
            "surface_moisture_flux_g_g_m_s"
        ]
        == 1.0e-4
    )
    assert "surface_flux_proxy_not_real_land_surface_or_evaporation_model" in (manifest.run_caveats)
    for field in ("qc", "qr", "qv", "w", "rain", "dbz", "hfx", "qfx", "updraft_helicity"):
        assert field in report["expected_outputs"]
    assert report["run_configuration_summary"]["surface_flux_cm1_values"]["cnst_shflx"] == 4.0e-2
    assert report["run_configuration_summary"]["surface_flux_cm1_values"]["cnst_lhflx"] == 1.0e-4
    assert "cnst_shflx = 4.0e-2," in namelist
    assert "cnst_lhflx = 1.0e-4," in namelist
    assert "output_sfcflx    = 1," in namelist
    assert "output_sfcparams = 1," in namelist
    assert "output_sfcdiags  = 1," in namelist


def test_triggered_deep_potential_package_generation_is_removed(
    tmp_path: Path,
) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding

    with pytest.raises(DryRunPackageError, match="package generation has been removed"):
        generate_dry_run_package(
            scenario_data=load_baseline_template(),
            runtime_home=tmp_path,
            run_id="run-triggered-removed",
            run_recipe="triggered_deep_potential",
            observed_sounding=observed,
        )
    assert not (tmp_path / "runs" / "run-triggered-removed").exists()


def test_pre_run_validation_caveats_deep_hypothesis_under_uniform_forcing(
    tmp_path: Path,
) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding
    candidate_screening = {
        "candidate_id": "USM00072558-supercell",
        "primary_story": "supercell_environment",
        "active_story": "supercell_environment",
        "active_story_label": "Supercell-like environment",
        "rank_score": 93.0,
    }

    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-deep-hypothesis-uniform-forcing",
        run_recipe="observed_surface_forced_evolution",
        observed_sounding=observed,
        candidate_screening=candidate_screening,
    )

    manifest = load_run_manifest(result.manifest_path)
    report = manifest.pre_run_validation_report
    assert report is not None
    assert report["status"] == "caveated"
    assert report["selected_hypothesis"]["story_id"] == "supercell_environment"
    assert report["selected_run_recipe"]["run_recipe"] == "observed_surface_forced_evolution"
    assert report["selected_run_recipe"]["recipe_id"] == ("observed_surface_forced_evolution_v0")
    assert report["hypothesis_recipe_alignment"]["status"] == "partial"
    assert "updraft_helicity" in report["output_validation"]["required_fields"]
    assert (
        "deep_convection_outcome_depends_on_surface_forcing_duration_domain_and_resolution"
        in (report["caveats"])
    )
    assert (tmp_path / "runs" / "run-deep-hypothesis-uniform-forcing").exists()


def test_pre_run_validation_blocks_invalid_run_configuration(tmp_path: Path) -> None:
    with pytest.raises(DryRunPackageError, match="Unknown domain size") as excinfo:
        generate_dry_run_package(
            scenario_data=load_baseline_template(),
            runtime_home=tmp_path,
            run_id="run-invalid-domain",
            run_configuration={
                "duration": "short_6h",
                "horizontal_cell_count": "cells_128",
                "domain_size": "planetary_9000km",
                "output_cadence": "standard_15min",
                "diagnostic_set": "process",
            },
        )

    report = excinfo.value.pre_run_validation_report
    assert report is not None
    assert report["status"] == "blocked"
    assert report["run_shape_validation"]["domain"] == "planetary_9000km"
    assert "Unknown domain size" in report["blocking_errors"][0]
    assert not (tmp_path / "runs" / "run-invalid-domain").exists()


def test_observed_run_configuration_preserves_selected_regional_domain(
    tmp_path: Path,
) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding

    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-regional-domain",
        run_recipe="observed_surface_forced_evolution",
        observed_sounding=observed,
        run_configuration={
            "duration": "short_6h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "regional_60km",
            "output_cadence": "standard_15min",
            "diagnostic_set": "full",
        },
    )

    manifest = load_run_manifest(result.manifest_path)
    report = manifest.pre_run_validation_report
    assert manifest.run_configuration["domain_size"] == "regional_60km"
    assert manifest.run_configuration["cm1_values"]["domain_x_km"] == pytest.approx(60.0)
    assert manifest.run_configuration["cm1_values"]["dx_m"] == pytest.approx(468.75)
    assert report is not None
    assert report["run_shape_validation"]["domain"] == "regional_60km"
    assert report["run_shape_validation"]["domain_x_km"] == pytest.approx(60.0)


def test_removed_storm_domain_is_not_silently_coerced(tmp_path: Path) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding

    with pytest.raises(DryRunPackageError, match="Removed domain size") as excinfo:
        generate_dry_run_package(
            scenario_data=load_baseline_template(),
            runtime_home=tmp_path,
            run_id="run-removed-domain",
            run_recipe="observed_surface_forced_evolution",
            observed_sounding=observed,
            run_configuration={
                "duration": "short_6h",
                "horizontal_cell_count": "cells_128",
                "domain_size": "storm_120km",
                "output_cadence": "standard_15min",
                "diagnostic_set": "full",
            },
        )

    report = excinfo.value.pre_run_validation_report
    assert report is not None
    assert report["status"] == "blocked"
    assert report["run_shape_validation"]["domain"] == "storm_120km"
    assert "Removed domain size" in report["blocking_errors"][0]
    assert not (tmp_path / "runs" / "run-removed-domain").exists()


def test_pre_run_validation_requests_full_deep_comparison_outputs(
    tmp_path: Path,
) -> None:
    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding

    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-deep-core-output",
        run_recipe="observed_surface_forced_evolution",
        observed_sounding=observed,
        candidate_screening={
            "candidate_id": "USM00072558-supercell",
            "primary_story": "supercell_environment",
            "active_story": "supercell_environment",
        },
        run_configuration={
            "duration": "short_6h",
            "horizontal_cell_count": "cells_64",
            "domain_size": "local_6km",
            "output_cadence": "standard_15min",
            "diagnostic_set": "essential",
        },
    )

    manifest = load_run_manifest(result.manifest_path)
    report = manifest.pre_run_validation_report
    assert report is not None
    assert report["status"] == "caveated"
    assert "updraft_helicity" in report["output_validation"]["enabled_fields"]
    assert report["output_validation"]["missing_fields"] == []


def test_observed_runs_require_wind_before_input_sounding_render(tmp_path: Path) -> None:
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

    with pytest.raises(
        DryRunPackageError, match="complete finite observed u/v wind profile"
    ) as excinfo:
        generate_dry_run_package(
            scenario_data=load_baseline_template(),
            runtime_home=tmp_path,
            run_id="run-observed-no-wind",
            observed_sounding=no_wind,
        )
    report = excinfo.value.pre_run_validation_report
    assert report is not None
    assert report["status"] == "blocked"
    assert report["input_validation"]["observed_wind_profile"] == "blocked"
    assert "complete finite observed u/v wind profile" in report["blocking_errors"][0]
    assert not (tmp_path / "runs" / "run-observed-no-wind").exists()


def test_observed_runs_require_complete_rendered_wind_profile(
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

    with pytest.raises(
        DryRunPackageError, match="complete finite observed u/v wind profile"
    ) as excinfo:
        generate_dry_run_package(
            scenario_data=load_baseline_template(),
            runtime_home=tmp_path,
            run_id="run-observed-partial-wind",
            observed_sounding=missing_mid_profile_wind,
        )
    report = excinfo.value.pre_run_validation_report
    assert report is not None
    assert report["status"] == "blocked"
    assert report["input_validation"]["observed_wind_profile"] == "blocked"
    assert "complete finite observed u/v wind profile" in report["blocking_errors"][0]

    assert not (tmp_path / "runs" / "run-observed-partial-wind").exists()


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
    assert "nx           =      64," in namelist
    assert "ny           =      64," in namelist
    assert "nz           =      100," in namelist
    assert "dx     =   100.0," in namelist
    assert "dy     =   100.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "timax  = 21600.0," in namelist
    assert "tapfrq =  900.0," in namelist
    assert "stretch_z =  1," in namelist
    assert "ztop      = 18000.0," in namelist
    assert "str_bot   =  2000.0," in namelist
    assert "str_top   = 18000.0," in namelist
    assert "dz_bot    =    40.0," in namelist
    assert "dz_top    =   600.0," in namelist
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


def test_dry_run_package_smoke_mode_is_short_package_health_run(tmp_path: Path) -> None:
    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-006",
        run_configuration={
            "duration": "smoke_1h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "local_6km",
            "output_cadence": "standard_15min",
            "diagnostic_set": "essential",
        },
    )
    namelist = (result.package_dir / "namelist.input").read_text()
    report = json.loads(result.report_path.read_text())

    assert report["run_configuration"]["mode"] == "smoke"
    assert "timax  = 3600.0," in namelist
    assert "tapfrq =  900.0," in namelist
    assert "nx           =      128," in namelist
    assert "ny           =      128," in namelist
    assert "nz           =      100," in namelist
    assert "dx     =   50.0," in namelist
    assert "dy     =   50.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "stretch_z =  1," in namelist
    assert "ztop      = 18000.0," in namelist
    assert "str_bot   =  2000.0," in namelist
    assert "str_top   = 18000.0," in namelist
    assert "set_znt    =      0," in namelist
    assert "set_ust    =      1," in namelist
    assert "cnst_ust   =   0.28," in namelist
    assert "testcase  =  3," in namelist
    assert "isnd      = 17," in namelist
    assert "iwnd      =  9," in namelist
    assert "output_format    = 2," in namelist


def test_dry_run_package_explicit_high_detail_configuration_reports_cost(
    tmp_path: Path,
) -> None:
    result = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-deep-001",
        run_configuration={
            "duration": "standard_12h",
            "horizontal_cell_count": "cells_256",
            "domain_size": "wide_12km",
            "output_cadence": "detailed_5min",
            "diagnostic_set": "full",
        },
    )
    namelist = (result.package_dir / "namelist.input").read_text()
    report = json.loads(result.report_path.read_text())
    details = report["run_configuration_summary"]

    assert report["run_configuration"]["duration"] == "standard_12h"
    assert "duration, horizontal cells, domain, cadence" in report["estimated_cost_or_size"]
    assert details["nx"] == 256
    assert details["ny"] == 256
    assert details["nz"] == 100
    assert details["dx_m"] == 50
    assert details["dy_m"] == 50
    assert details["dz_m"] == 40
    assert details["stretch_z"] == 1
    assert details["str_bot_m"] == 2000.0
    assert details["str_top_m"] == 18000.0
    assert details["dz_bot_m"] == 40.0
    assert details["dz_top_m"] == 600.0
    assert details["runtime_seconds"] == 43200
    assert details["output_cadence_seconds"] == 300
    assert details["expected_output_frames"] == 145
    assert details["grid_cell_multiplier_vs_default"] == 16.0
    assert details["time_step_seconds"] == 3.0
    assert details["time_step_multiplier_vs_default"] == 1.0
    assert details["output_frame_multiplier_vs_default"] == 5.8
    assert details["estimated_compute_multiplier_vs_default"] == 32.0
    assert details["estimated_output_volume_multiplier_vs_default"] == 92.8
    assert "resolved from the selected run configuration" in details["time_step_note"]

    assert "nx           =      256," in namelist
    assert "ny           =      256," in namelist
    assert "dx     =   50.0," in namelist
    assert "dy     =   50.0," in namelist
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
    )
    baseline = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-baseline",
        controls={"low_level_humidity": "baseline"},
    )
    more_humid = generate_dry_run_package(
        scenario_data=load_baseline_template(),
        runtime_home=tmp_path,
        run_id="run-baseline-more-humid",
        controls={"low_level_humidity": "more_humid"},
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
    assert "timax  = 21600.0," in baseline_namelist
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
    )
    dry_failed = generate_dry_run_package(
        scenario_data=load_dry_failed_template(),
        runtime_home=tmp_path,
        run_id="run-dry-failed",
    )

    baseline_namelist = (baseline.package_dir / "namelist.input").read_text()
    dry_namelist = (dry_failed.package_dir / "namelist.input").read_text()
    baseline_sounding = (baseline.package_dir / "input_sounding").read_text().splitlines()
    dry_sounding = (dry_failed.package_dir / "input_sounding").read_text().splitlines()
    dry_report = json.loads(dry_failed.report_path.read_text())

    assert dry_report["scenario_id"] == "dry-failed-cumulus"
    assert dry_report["controls"]["low_level_humidity"] == "drier"
    assert "timax  = 21600.0," in dry_namelist
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
    )
    capped = generate_dry_run_package(
        scenario_data=load_capped_template(),
        runtime_home=tmp_path,
        run_id="run-capped",
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
    assert "timax  = 21600.0," in capped_namelist
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
