import json
from pathlib import Path

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
    assert contract.run_configuration.duration_preset == "quick_6h"
    assert contract.run_configuration.domain_size_preset == "local_6km"
    assert contract.run_configuration.output_field_density_preset == "analysis"
    assert {file.role for file in contract.generated_files} == set(GeneratedFileRole)
    assert contract.cloud_scale_defaults.nx == 64
    assert contract.cloud_scale_defaults.ny == 64
    assert contract.cloud_scale_defaults.nz == 75
    assert contract.cloud_scale_defaults.horizontal_spacing_m == 100
    assert contract.cloud_scale_defaults.vertical_spacing_m == 40
    assert contract.cloud_scale_defaults.vertical_extent_km == 18.0
    assert contract.cloud_scale_defaults.runtime_seconds == 21600
    assert contract.cloud_scale_defaults.output_cadence_seconds == 900


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
    assert "nz           =      75," in namelist
    assert "dx     =   100.0," in namelist
    assert "dy     =   100.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "timax  = 21600.0," in namelist
    assert "tapfrq =  900.0," in namelist
    assert "rstfrq = 10800.0," in namelist
    assert "zd      =  2500.0," in namelist
    assert "ztop      = 18000.0," in namelist
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
            "duration_preset": "smoke_1h",
            "grid_detail_preset": "standard",
            "domain_size_preset": "local_6km",
            "output_cadence_preset": "standard_15min",
            "output_field_density_preset": "core",
        },
    )
    namelist = render_namelist_fragment(contract)

    assert contract.run_configuration.mode == "smoke"
    assert "short_smoke_mode_is_for_package_health_not_science_evolution" in (
        contract.run_configuration.caveats
    )
    assert "timax  = 3600.0," in namelist
    assert "tapfrq =  900.0," in namelist
    assert "nx           =      64," in namelist
    assert "ny           =      64," in namelist
    assert "nz           =      75," in namelist
    assert "dx     =   100.0," in namelist
    assert "dy     =   100.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "ztop      = 18000.0," in namelist
    assert "zd      =  2500.0," in namelist
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
            "duration_preset": "standard_12h",
            "grid_detail_preset": "fine",
            "domain_size_preset": "wide_12km",
            "output_cadence_preset": "detailed_5min",
            "output_field_density_preset": "rich",
        },
    )
    namelist = render_namelist_fragment(contract)

    assert contract.run_configuration.duration_seconds == 43200
    assert contract.run_configuration.cm1_values.expected_output_frames == 145
    assert "configuration_better_suited_to_larger_compute" in (contract.run_configuration.caveats)
    assert "nx           =      256," in namelist
    assert "ny           =      256," in namelist
    assert "nz           =      75," in namelist
    assert "dx     =   50.0," in namelist
    assert "dy     =   50.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "dtl    =   3.000," in namelist
    assert "timax  = 43200.0," in namelist
    assert "tapfrq =  300.0," in namelist
    assert "ztop      = 18000.0," in namelist
    assert "testcase  =  3," in namelist
    assert "isnd      = 17," in namelist
    assert "output_format    = 2," in namelist


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
