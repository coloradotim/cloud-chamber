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


def baseline_scenario() -> ScenarioTemplate:
    return validate_scenario_template(json.loads(BASELINE_TEMPLATE.read_text()))


def test_cm1_contract_documents_expected_generated_files_and_defaults() -> None:
    contract = build_cm1_input_contract(baseline_scenario(), run_size_preset="standard")

    assert contract.scenario_id == "baseline-shallow-cumulus"
    assert contract.run_size_preset == "standard"
    assert {file.role for file in contract.generated_files} == set(GeneratedFileRole)
    assert contract.cloud_scale_defaults.nx == 64
    assert contract.cloud_scale_defaults.ny == 64
    assert contract.cloud_scale_defaults.nz == 75
    assert contract.cloud_scale_defaults.horizontal_spacing_m == 100
    assert contract.cloud_scale_defaults.vertical_spacing_m == 40
    assert contract.cloud_scale_defaults.vertical_extent_km == 18.0
    assert contract.cloud_scale_defaults.runtime_seconds == 21600
    assert contract.cloud_scale_defaults.output_cadence_seconds == 3600


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


def test_rendered_namelist_standard_preset_preserves_reference_timing() -> None:
    contract = build_cm1_input_contract(baseline_scenario(), run_size_preset="standard")
    namelist = render_namelist_fragment(contract)

    assert "&param0" in namelist
    assert "nx           =      64," in namelist
    assert "ny           =      64," in namelist
    assert "nz           =      75," in namelist
    assert "dx     =   100.0," in namelist
    assert "dy     =   100.0," in namelist
    assert "dz     =   40.0," in namelist
    assert "timax  = 21600.0," in namelist
    assert "tapfrq =  3600.0," in namelist
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
    assert "isnd      = 19," in namelist
    assert "&cloud_chamber_domain" not in namelist
    assert "placeholder until local/manual CM1 validation" not in namelist


def test_rendered_namelist_quick_look_only_changes_runtime_and_cadence() -> None:
    contract = build_cm1_input_contract(baseline_scenario(), run_size_preset="quick_look")
    namelist = render_namelist_fragment(contract)

    assert contract.run_size_preset == "quick_look"
    assert "timax  = 10800.0," in namelist
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
    assert "isnd      = 19," in namelist
    assert "output_format    = 2," in namelist


def test_rendered_input_sounding_is_cm1_readable_not_notes() -> None:
    contract = build_cm1_input_contract(baseline_scenario())
    sounding = render_input_sounding_notes(contract)
    lines = sounding.splitlines()

    assert len(lines[0].split()) == 3
    assert all(len(line.split()) == 5 for line in lines[1:])
    assert float(lines[-1].split()[0]) > 6000
    assert "Cloud Chamber input_sounding notes" not in sounding
    assert "placeholder until local/manual CM1 validation" not in sounding


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
