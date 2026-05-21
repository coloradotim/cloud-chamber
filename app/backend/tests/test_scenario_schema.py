from typing import Any

import pytest

from cloud_chamber.scenario_schema import ScenarioValidationError, validate_scenario_template


def valid_template() -> dict[str, Any]:
    return {
        "schema_version": "1",
        "id": "baseline-shallow-cumulus",
        "display_name": "Baseline Shallow Cumulus",
        "category": "lower-atmosphere",
        "description": "A first hero case for shallow-cumulus exploration.",
        "physical_question": "How do moisture and heating shape shallow cumulus?",
        "learning_goals": ["Identify first cloud time", "Compare cloud base and top"],
        "intended_behavior": "Credible idealized shallow cumulus.",
        "expected_behavior": "Clouds may form after surface heating erodes inhibition.",
        "controls": [
            {
                "id": "low_level_humidity",
                "label": "Low-level humidity",
                "description": "Relative low-level moisture around the baseline.",
                "type": "choice",
                "audience": "product",
                "default": "baseline",
                "options": [
                    {"value": "drier", "label": "Drier"},
                    {"value": "baseline", "label": "Baseline"},
                    {"value": "more_humid", "label": "More humid"},
                ],
                "cm1_mapping_notes": "Maps toward sounding humidity profile adjustments.",
            },
            {
                "id": "raw_namelist_note",
                "label": "Developer namelist note",
                "description": "Advanced/developer-only mapping detail.",
                "type": "boolean",
                "audience": "advanced",
                "default": False,
                "cm1_mapping_notes": "Documents future raw namelist mapping, not primary UI.",
            },
        ],
        "run_size_presets": [
            {
                "id": "quick_look",
                "label": "Quick look",
                "purpose": "Sanity-check setup.",
                "expected_runtime": "roughly 10-20 minutes when feasible",
                "confidence": "lower confidence until locally validated",
                "output_notes": "coarser output cadence is acceptable if labeled",
            },
            {
                "id": "standard",
                "label": "Standard",
                "purpose": "Normal personal exploration.",
                "expected_runtime": "normal local run",
                "confidence": "balanced confidence and runtime",
                "output_notes": "useful saved diagnostics",
            },
            {
                "id": "deep_overnight",
                "label": "Deep / overnight",
                "purpose": "Richer result exploration.",
                "expected_runtime": "may take hours or overnight",
                "confidence": "higher confidence or detail",
                "output_notes": "larger output should be explicit before launch",
            },
        ],
        "expected_diagnostics": {
            "cloud_formed": True,
            "first_cloud_time": "expected after spin-up if clouds form",
            "cloud_base_top": "record cloud base/top if clouds form",
            "max_updraft": "record maximum vertical velocity",
            "cloud_water_summary": "summarize cloud-water evolution",
            "rain_onset": "not expected for the baseline, but record if present",
        },
        "cm1_template": {
            "namelist_template": "namelist.input.j2",
            "input_sounding_template": "input_sounding.j2",
            "runtime_files_needed": ["LANDUSE.TBL"],
            "mapping_notes": "CM1 remains the source of truth.",
        },
        "visualization_defaults": {
            "primary_field": "qc",
            "secondary_fields": ["w"],
            "camera": "orbit shallow-cumulus domain",
            "rendering_method": "cloud-water opacity approximation",
        },
        "variation_policy": {
            "baseline_scenario_id": "baseline-shallow-cumulus",
            "one_control_at_a_time": True,
            "suggested_controls": ["low_level_humidity"],
            "non_goals": ["arbitrary large parameter sweeps"],
        },
        "warnings": ["Preview estimates are guidance only."],
        "limitations": ["Exact morphology is not pass/fail."],
        "advanced_settings_notes": "Raw namelist settings belong in developer views.",
    }


def test_valid_scenario_template_supports_golden_path_contract() -> None:
    template = validate_scenario_template(valid_template())

    assert template.id == "baseline-shallow-cumulus"
    assert template.physical_question
    assert len(template.learning_goals) == 2
    assert {preset.id.value for preset in template.run_size_presets} == {
        "quick_look",
        "standard",
        "deep_overnight",
    }
    assert template.expected_diagnostics.cloud_water_summary is not None
    assert template.variation_policy is not None
    assert template.variation_policy.one_control_at_a_time


def test_invalid_template_requires_product_facing_control() -> None:
    data = valid_template()
    controls = data["controls"]
    assert isinstance(controls, list)
    controls[0]["audience"] = "advanced"

    with pytest.raises(ScenarioValidationError, match="product-facing control"):
        validate_scenario_template(data)


def test_invalid_template_requires_all_runtime_profiles() -> None:
    data = valid_template()
    presets = data["run_size_presets"]
    assert isinstance(presets, list)
    data["run_size_presets"] = presets[:2]

    with pytest.raises(ScenarioValidationError, match="quick/standard/deep"):
        validate_scenario_template(data)


def test_invalid_choice_control_reports_useful_default_error() -> None:
    data = valid_template()
    controls = data["controls"]
    assert isinstance(controls, list)
    controls[0]["default"] = "bogus"

    with pytest.raises(ScenarioValidationError, match="default must match an option"):
        validate_scenario_template(data)


def test_invalid_variation_policy_rejects_unknown_controls() -> None:
    data = valid_template()
    variation_policy = data["variation_policy"]
    assert isinstance(variation_policy, dict)
    variation_policy["suggested_controls"] = ["missing_control"]

    with pytest.raises(ScenarioValidationError, match="unknown controls"):
        validate_scenario_template(data)
