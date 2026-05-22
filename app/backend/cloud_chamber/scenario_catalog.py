"""Scenario catalog loading for committed scenario templates."""

from __future__ import annotations

import json
from pathlib import Path

from cloud_chamber.scenario_schema import ScenarioTemplate, validate_scenario_template

REPO_ROOT = Path(__file__).resolve().parents[3]
SCENARIO_DIR = REPO_ROOT / "scenarios" / "lower-atmosphere"


def load_scenario_templates(scenario_dir: Path = SCENARIO_DIR) -> list[ScenarioTemplate]:
    return [
        validate_scenario_template(json.loads(path.read_text()))
        for path in sorted(scenario_dir.glob("*.json"))
    ]


def load_scenario_template(scenario_id: str, scenario_dir: Path = SCENARIO_DIR) -> ScenarioTemplate:
    for scenario in load_scenario_templates(scenario_dir):
        if scenario.id == scenario_id:
            return scenario
    raise KeyError(f"Unknown scenario: {scenario_id}")


def scenario_summary(scenario: ScenarioTemplate) -> dict[str, object]:
    return {
        "id": scenario.id,
        "display_name": scenario.display_name,
        "description": scenario.description,
        "physical_question": scenario.physical_question,
        "intended_behavior": scenario.intended_behavior,
        "expected_behavior": scenario.expected_behavior,
        "learning_goals": scenario.learning_goals,
        "warnings": scenario.warnings,
        "limitations": scenario.limitations,
        "controls": [
            {
                "id": control.id,
                "label": control.label,
                "description": control.description,
                "type": control.type.value,
                "audience": control.audience.value,
                "default": control.default,
                "options": [
                    {
                        "value": option.value,
                        "label": option.label,
                        "description": option.description,
                    }
                    for option in control.options
                ],
            }
            for control in scenario.controls
            if control.audience.value == "product"
        ],
        "run_size_presets": [
            {
                "id": preset.id.value,
                "label": preset.label,
                "purpose": preset.purpose,
                "expected_runtime": preset.expected_runtime,
                "confidence": preset.confidence,
                "output_notes": preset.output_notes,
            }
            for preset in scenario.run_size_presets
        ],
    }
