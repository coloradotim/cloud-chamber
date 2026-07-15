import json
from pathlib import Path
from typing import Any, cast

from cloud_chamber.cm1_input_contract import (
    GeneratedFileRole,
    build_cm1_input_contract,
    render_input_sounding_notes,
    render_namelist_fragment,
)
from cloud_chamber.scenario_schema import (
    ControlAudience,
    ScenarioTemplate,
    validate_scenario_template,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"
DRY_FAILED_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/dry-failed-cumulus.json"
CAPPED_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/capped-suppressed-cumulus.json"


def baseline_scenario() -> ScenarioTemplate:
    return validate_scenario_template(json.loads(BASELINE_TEMPLATE.read_text()))


def dry_failed_scenario() -> ScenarioTemplate:
    return validate_scenario_template(json.loads(DRY_FAILED_TEMPLATE.read_text()))


def capped_scenario() -> ScenarioTemplate:
    return validate_scenario_template(json.loads(CAPPED_TEMPLATE.read_text()))


def test_cm1_contract_documents_expected_generated_files_and_default_run_configuration() -> None:
    contract = build_cm1_input_contract(baseline_scenario())

    assert contract.scenario_id == "baseline-shallow-cumulus"
    assert contract.run_configuration.duration == "short_6h"
    assert contract.run_configuration.domain_size == "local_6km"
    assert contract.run_configuration.diagnostic_set == "full"
    assert {file.role for file in contract.generated_files} == set(GeneratedFileRole)
    assert contract.cloud_scale_defaults.nx == 64
    assert contract.cloud_scale_defaults.ny == 64
    assert contract.cloud_scale_defaults.nz == 100
    assert contract.cloud_scale_defaults.horizontal_spacing_m == 100
    assert contract.cloud_scale_defaults.vertical_spacing_m == 40
    assert contract.cloud_scale_defaults.vertical_extent_km == 18.0
    assert contract.cloud_scale_defaults.stretch_z == 1
    assert contract.cloud_scale_defaults.stretch_bottom_m == 2000.0
    assert contract.cloud_scale_defaults.stretch_top_m == 18000.0
    assert contract.cloud_scale_defaults.dz_bottom_m == 40.0
    assert contract.cloud_scale_defaults.dz_top_m == 600.0
    assert contract.cloud_scale_defaults.runtime_seconds == 21600
    assert contract.cloud_scale_defaults.output_cadence_seconds == 900
    assert contract.recipe_id == "generated_reference_lower_atmosphere_v1"
    assert contract.assumption_set_id == "generated_reference_lower_atmosphere_v1"


def test_cm1_contract_keeps_product_controls_separate_from_mapping_notes() -> None:
    scenario = baseline_scenario()
    contract = build_cm1_input_contract(
        scenario,
        selected_controls={"low_level_humidity": "more_humid"},
    )

    low_level_humidity = next(
        fragment
        for fragment in contract.control_fragments
        if fragment.control_id == "low_level_humidity"
    )

    assert low_level_humidity.audience == ControlAudience.PRODUCT
    assert low_level_humidity.selected_value == "more_humid"
    assert "sounding moisture" in low_level_humidity.cm1_mapping_notes
    assert "provisional until local/manual smoke-run validation" in (
        low_level_humidity.scientific_status
    )
    assert contract.moisture_profile == "more_humid"


def test_rendered_namelist_default_quick_science_preserves_reference_domain() -> None:
    contract = build_cm1_input_contract(baseline_scenario())
    namelist = render_namelist_fragment(contract)

    assert "&param0" in namelist
    assert "nx           =      64," in namelist
    assert "ny           =      64," in namelist
    assert "nz           =      100," in namelist
    assert "dx     =   100.0," in namelist
    assert "dy     =   100.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "timax  = 21600.0," in namelist
    assert "tapfrq =  900.0," in namelist
    assert "rstfrq = 10800.0," in namelist
    assert "zd      =  12000.0," in namelist
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
    assert "output_format    = 2," in namelist
    assert "output_filetype  = 2," in namelist
    assert "testcase  =  3," in namelist
    assert "isnd      = 17," in namelist
    assert "iwnd      =  9," in namelist
    assert "&cloud_chamber_domain" not in namelist
    assert "placeholder until local/manual CM1 validation" not in namelist


def test_rendered_namelist_smoke_mode_is_short_package_health_run() -> None:
    contract = build_cm1_input_contract(
        baseline_scenario(),
        run_configuration={
            "duration": "smoke_1h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "local_6km",
            "output_cadence": "standard_15min",
            "diagnostic_set": "essential",
        },
    )
    namelist = render_namelist_fragment(contract)

    assert contract.run_configuration.mode == "smoke"
    assert "short_smoke_mode_is_for_package_health_not_science_evolution" in (
        contract.run_configuration.caveats
    )
    assert "timax  = 3600.0," in namelist
    assert "tapfrq =  900.0," in namelist
    assert "nx           =      128," in namelist
    assert "ny           =      128," in namelist
    assert "nz           =      100," in namelist
    assert "dx     =   50.0," in namelist
    assert "dy     =   50.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "ztop      = 18000.0," in namelist
    assert "stretch_z =  1," in namelist
    assert "str_bot   =  2000.0," in namelist
    assert "str_top   = 18000.0," in namelist
    assert "zd      =  12000.0," in namelist
    assert "set_znt    =      0," in namelist
    assert "cnst_znt   =   0.00," in namelist
    assert "set_ust    =      1," in namelist
    assert "cnst_ust   =   0.28," in namelist
    assert "testcase  =  3," in namelist
    assert "isnd      = 17," in namelist
    assert "iwnd      =  9," in namelist
    assert "output_format    = 2," in namelist


def test_rendered_namelist_explicit_configuration_changes_domain_detail_and_cadence() -> None:
    contract = build_cm1_input_contract(
        baseline_scenario(),
        run_configuration={
            "duration": "standard_12h",
            "horizontal_cell_count": "cells_256",
            "domain_size": "wide_12km",
            "output_cadence": "detailed_5min",
            "diagnostic_set": "full",
        },
    )
    namelist = render_namelist_fragment(contract)

    assert contract.run_configuration.duration_seconds == 43200
    assert contract.run_configuration.cm1_values.expected_output_frames == 145
    assert "configuration_better_suited_to_larger_compute" in (contract.run_configuration.caveats)
    assert "nx           =      256," in namelist
    assert "ny           =      256," in namelist
    assert "nz           =      100," in namelist
    assert "dx     =   50.0," in namelist
    assert "dy     =   50.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "dtl    =   3.000," in namelist
    assert "timax  = 43200.0," in namelist
    assert "tapfrq =  300.0," in namelist
    assert "ztop      = 18000.0," in namelist
    assert "stretch_z =  1," in namelist
    assert "str_bot   =  2000.0," in namelist
    assert "str_top   = 18000.0," in namelist
    assert "testcase  =  3," in namelist
    assert "isnd      = 17," in namelist
    assert "output_format    = 2," in namelist


def test_rendered_namelist_preserves_explicit_timestep_target() -> None:
    contract = build_cm1_input_contract(
        baseline_scenario(),
        run_configuration={
            "duration": "short_6h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "wide_12km",
            "output_cadence": "standard_15min",
            "diagnostic_set": "full",
            "time_step_seconds": 1.0,
        },
    )
    namelist = render_namelist_fragment(contract)

    assert contract.run_configuration.cm1_values.time_step_seconds == 1.0
    assert "dtl_1p000e00s" in contract.run_configuration.configuration_id
    assert "non_default_timestep_target_requires_like_for_like_campaign_evidence" in (
        contract.run_configuration.caveats
    )
    assert "dtl    =   1.000," in namelist


def test_rendered_input_sounding_is_external_baseline_profile() -> None:
    contract = build_cm1_input_contract(baseline_scenario())
    sounding = render_input_sounding_notes(contract)
    lines = sounding.splitlines()

    assert len(lines[0].split()) == 3
    assert all(len(line.split()) == 5 for line in lines[1:])
    assert lines[0].split()[0] == "1015.00"
    assert float(lines[0].split()[2]) > 17.0
    assert float(lines[-1].split()[0]) > 18000
    assert "-8.75" in lines[1]
    assert "-4.61" in lines[-1]
    assert "Cloud Chamber input_sounding notes" not in sounding
    assert "placeholder until local/manual CM1 validation" not in sounding


def test_observed_contract_declares_surface_forced_v0_recipe_assumptions() -> None:
    from igra_fixtures import IGRA_FIXTURE

    from cloud_chamber.observed_sounding import parse_igra_station_text

    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding

    contract = build_cm1_input_contract(
        baseline_scenario(),
        observed_sounding=observed,
    )

    assert contract.run_recipe.value == "observed_surface_forced_evolution"
    assert contract.recipe_id == "observed_surface_forced_evolution_v0"
    assert contract.recipe_display_name == "Observed Surface-Forced Evolution v0"
    assert contract.assumption_set_id == "observed_surface_forced_evolution_v0_assumptions"
    assert contract.assumption_mode == "observed_surface_forced_evolution"
    assert contract.required_output_fields == ("qv", "qc", "w", "qr", "rain", "dbz", "hfx", "qfx")
    trigger = cast(dict[str, Any], contract.recipe_assumptions["trigger"])
    radiation = cast(dict[str, Any], contract.recipe_assumptions["radiation"])
    forcing = cast(dict[str, Any], contract.recipe_assumptions["large_scale_forcing"])
    surface_fluxes = cast(dict[str, Any], contract.recipe_assumptions["surface_fluxes"])
    observed_sounding = cast(dict[str, Any], contract.recipe_assumptions["observed_sounding"])
    assert trigger["mode"] == "none"
    assert radiation["mode"] == "disabled"
    assert forcing["mode"] == "none"
    assert observed_sounding["wind_profile"] == "required_complete_rendered_u_v_profile"
    assert surface_fluxes["mode"] == "constant_uniform_surface_flux_proxy"
    assert surface_fluxes["product_selections"] == {
        "surface_heat_flux_k_m_s": 8.0e-3,
        "surface_moisture_flux_g_g_m_s": 5.2e-5,
        "summary": (
            "Surface heat flux 0.008 K m/s; surface moisture flux 5.2e-05 g/g m/s; "
            "constant uniform proxy"
        ),
    }
    assert surface_fluxes["cm1_values"]["cnst_shflx"] == 8.0e-3
    assert surface_fluxes["cm1_values"]["cnst_lhflx"] == 5.2e-5
    assert "No artificial atmospheric trigger is applied." in contract.recipe_caveats


def test_observed_surface_flux_proxy_choices_render_namelist_and_surface_outputs() -> None:
    from igra_fixtures import IGRA_FIXTURE

    from cloud_chamber.observed_sounding import parse_igra_station_text

    observed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding

    contract = build_cm1_input_contract(
        baseline_scenario(),
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
    namelist = render_namelist_fragment(contract)
    surface_fluxes = cast(dict[str, Any], contract.recipe_assumptions["surface_fluxes"])

    assert contract.run_configuration.surface_heat_flux_k_m_s == 4.0e-2
    assert contract.run_configuration.surface_moisture_flux_g_g_m_s == 1.0e-4
    assert contract.run_configuration.surface_flux_mode == "constant_uniform_surface_flux_proxy"
    assert contract.run_configuration.surface_flux_cm1_values.cnst_shflx == 4.0e-2
    assert contract.run_configuration.surface_flux_cm1_values.cnst_lhflx == 1.0e-4
    assert "surface_flux_proxy_values_need_local_smoke_validation" in (
        contract.run_configuration.surface_flux_caveats
    )
    assert surface_fluxes["product_selections"]["surface_heat_flux_k_m_s"] == 4.0e-2
    assert surface_fluxes["product_selections"]["surface_moisture_flux_g_g_m_s"] == 1.0e-4
    assert surface_fluxes["cm1_values"]["isfcflx"] == 1
    assert surface_fluxes["cm1_values"]["set_flx"] == 1
    assert surface_fluxes["cm1_values"]["cnst_shflx"] == 4.0e-2
    assert surface_fluxes["cm1_values"]["cnst_lhflx"] == 1.0e-4
    for field in ("qc", "qr", "qv", "w", "rain", "dbz", "hfx", "qfx", "updraft_helicity"):
        assert field in contract.expected_outputs
    assert "isfcflx    =      1," in namelist
    assert "sfcmodel   =      1," in namelist
    assert "set_flx    =      1," in namelist
    assert "cnst_shflx = 4.0e-2," in namelist
    assert "cnst_lhflx = 1.0e-4," in namelist
    assert "output_sfcflx    = 1," in namelist
    assert "output_sfcparams = 1," in namelist
    assert "output_sfcdiags  = 1," in namelist


def test_baseline_humidity_ladder_only_changes_low_level_moisture_profile() -> None:
    scenario = baseline_scenario()
    drier_contract = build_cm1_input_contract(
        scenario,
        selected_controls={"low_level_humidity": "drier"},
    )
    baseline_contract = build_cm1_input_contract(
        scenario,
        selected_controls={"low_level_humidity": "baseline"},
    )
    humid_contract = build_cm1_input_contract(
        scenario,
        selected_controls={"low_level_humidity": "more_humid"},
    )

    assert drier_contract.moisture_profile == "drier"
    assert baseline_contract.moisture_profile == "baseline"
    assert humid_contract.moisture_profile == "more_humid"
    assert render_namelist_fragment(drier_contract) == render_namelist_fragment(baseline_contract)
    assert render_namelist_fragment(humid_contract) == render_namelist_fragment(baseline_contract)

    drier_lines = render_input_sounding_notes(drier_contract).splitlines()
    baseline_lines = render_input_sounding_notes(baseline_contract).splitlines()
    humid_lines = render_input_sounding_notes(humid_contract).splitlines()

    assert len(drier_lines) == len(baseline_lines) == len(humid_lines)
    assert float(drier_lines[0].split()[2]) < float(baseline_lines[0].split()[2])
    assert float(humid_lines[0].split()[2]) > float(baseline_lines[0].split()[2])
    assert float(drier_lines[1].split()[2]) < float(baseline_lines[1].split()[2])
    assert float(humid_lines[1].split()[2]) > float(baseline_lines[1].split()[2])

    for drier_line, baseline_line, humid_line in zip(
        drier_lines[1:],
        baseline_lines[1:],
        humid_lines[1:],
        strict=True,
    ):
        drier_parts = drier_line.split()
        baseline_parts = baseline_line.split()
        humid_parts = humid_line.split()
        assert drier_parts[0:2] == baseline_parts[0:2]
        assert humid_parts[0:2] == baseline_parts[0:2]
        assert drier_parts[3:] == baseline_parts[3:]
        assert humid_parts[3:] == baseline_parts[3:]


def test_dry_failed_sounding_only_drives_low_level_moisture_drier() -> None:
    baseline = render_input_sounding_notes(build_cm1_input_contract(baseline_scenario()))
    dry_failed = render_input_sounding_notes(build_cm1_input_contract(dry_failed_scenario()))

    baseline_lines = baseline.splitlines()
    dry_lines = dry_failed.splitlines()

    assert len(baseline_lines) == len(dry_lines)
    assert dry_lines[0].split()[:2] == baseline_lines[0].split()[:2]
    assert float(dry_lines[0].split()[2]) < float(baseline_lines[0].split()[2])

    for baseline_line, dry_line in zip(baseline_lines[1:], dry_lines[1:], strict=True):
        baseline_parts = baseline_line.split()
        dry_parts = dry_line.split()
        assert dry_parts[0] == baseline_parts[0]
        assert dry_parts[1] == baseline_parts[1]
        assert dry_parts[3:] == baseline_parts[3:]

    assert float(dry_lines[1].split()[2]) < float(baseline_lines[1].split()[2])
    assert float(dry_lines[6].split()[2]) < float(baseline_lines[6].split()[2])
    assert dry_lines[-1].split()[2] == baseline_lines[-1].split()[2]


def test_capped_suppressed_sounding_changes_only_cap_stability() -> None:
    baseline = render_input_sounding_notes(build_cm1_input_contract(baseline_scenario()))
    capped = render_input_sounding_notes(build_cm1_input_contract(capped_scenario()))

    baseline_lines = baseline.splitlines()
    capped_lines = capped.splitlines()

    assert len(capped_lines) == len(baseline_lines)
    assert capped_lines[0] == baseline_lines[0]

    unchanged_low_level_indexes = [1, 2]
    for index in unchanged_low_level_indexes:
        assert capped_lines[index] == baseline_lines[index]

    for baseline_line, capped_line in zip(baseline_lines[1:], capped_lines[1:], strict=True):
        baseline_parts = baseline_line.split()
        capped_parts = capped_line.split()
        assert capped_parts[0] == baseline_parts[0]
        assert capped_parts[2:] == baseline_parts[2:]

    assert float(capped_lines[3].split()[1]) > float(baseline_lines[3].split()[1])
    assert float(capped_lines[4].split()[1]) > float(baseline_lines[4].split()[1])
    assert float(capped_lines[5].split()[1]) > float(baseline_lines[5].split()[1])
    assert capped_lines[6] == baseline_lines[6]


def test_capped_suppressed_keeps_baseline_namelist_family() -> None:
    baseline_contract = build_cm1_input_contract(baseline_scenario())
    capped_contract = build_cm1_input_contract(capped_scenario())

    assert capped_contract.moisture_profile == "baseline"
    assert capped_contract.stability_profile == "stronger_cap"
    assert render_namelist_fragment(capped_contract) == render_namelist_fragment(baseline_contract)


def test_cm1_contract_includes_expected_diagnostics_and_visualization_defaults() -> None:
    contract = build_cm1_input_contract(baseline_scenario())

    assert "first_cloud_time" in contract.expected_diagnostics
    assert "cloud_base_top" in contract.expected_diagnostics
    assert "max_updraft" in contract.expected_diagnostics
    assert "cloud_water_summary" in contract.expected_diagnostics
    assert contract.visualization_defaults["primary_field"] == "qc"
    assert (
        contract.visualization_defaults["rendering_method"] == "cloud-water opacity approximation"
    )
