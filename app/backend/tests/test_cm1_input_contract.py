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
    contract = build_cm1_input_contract(baseline_scenario(), run_size_preset="quick_look")

    assert contract.scenario_id == "baseline-shallow-cumulus"
    assert {file.role for file in contract.generated_files} == set(GeneratedFileRole)
    assert contract.cloud_scale_defaults.horizontal_extent_km == 16
    assert contract.cloud_scale_defaults.y_extent_km == 16
    assert contract.cloud_scale_defaults.vertical_extent_km == 6
    assert contract.cloud_scale_defaults.horizontal_spacing_m == 200
    assert contract.cloud_scale_defaults.vertical_spacing_m == 125
    assert contract.cloud_scale_defaults.runtime_seconds == 7200
    assert contract.cloud_scale_defaults.output_cadence_seconds == 300


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
    assert "placeholder until local/manual CM1 validation" in low_level_humidity.scientific_status


def test_rendered_namelist_fragment_is_deterministic_snapshot() -> None:
    contract = build_cm1_input_contract(baseline_scenario())

    assert render_namelist_fragment(contract) == (
        "# Cloud Chamber CM1 namelist fragment\n"
        "# Status: placeholder until local/manual CM1 validation\n"
        "# scenario_id = baseline-shallow-cumulus\n"
        "&cloud_chamber_domain\n"
        "  x_extent_km = 16,\n"
        "  y_extent_km = 16,\n"
        "  z_extent_km = 6,\n"
        "  dx_m = 200,\n"
        "  dz_m = 125,\n"
        "  runtime_seconds = 7200,\n"
        "  output_cadence_seconds = 300,\n"
        "/\n"
    )


def test_rendered_sounding_notes_include_only_product_controls() -> None:
    contract = build_cm1_input_contract(baseline_scenario())
    notes = render_input_sounding_notes(contract)

    assert "# physical_question = How do low-level moisture" in notes
    assert "# - low_level_humidity = baseline" in notes
    assert "# - surface_heating = baseline" in notes
    assert "# - cap_strength = baseline" in notes
    assert "advanced/developer" not in notes


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
