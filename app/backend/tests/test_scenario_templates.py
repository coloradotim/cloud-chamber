import json
from pathlib import Path

import pytest

from cloud_chamber.scenario_schema import ScenarioValidationError, validate_scenario_template

REPO_ROOT = Path(__file__).resolve().parents[3]
SCENARIO_DIR = REPO_ROOT / "scenarios" / "lower-atmosphere"
EXPECTED_SCENARIOS = {
    "baseline-shallow-cumulus",
    "dry-failed-cumulus",
    "capped-suppressed-cumulus",
    "humid-vigorous-cumulus",
    "low-stratus",
    "warm-rain",
}


def scenario_paths() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*.json"))


def load_json(path: Path) -> object:
    return json.loads(path.read_text())


def test_all_initial_lower_atmosphere_templates_exist() -> None:
    assert {path.stem for path in scenario_paths()} == EXPECTED_SCENARIOS


@pytest.mark.parametrize("path", scenario_paths(), ids=lambda path: path.stem)
def test_committed_lower_atmosphere_templates_validate(path: Path) -> None:
    template = validate_scenario_template(load_json(path))

    assert template.category == "lower-atmosphere"
    assert template.physical_question
    assert template.learning_goals
    assert template.warnings
    assert template.limitations


def test_baseline_is_golden_path_hero_case() -> None:
    template = validate_scenario_template(load_json(SCENARIO_DIR / "baseline-shallow-cumulus.json"))

    assert template.id == "baseline-shallow-cumulus"
    assert "First Golden Path hero case" in template.description
    assert template.variation_policy is not None
    assert template.variation_policy.baseline_scenario_id == "baseline-shallow-cumulus"


def test_warm_rain_is_early_but_non_blocking() -> None:
    template = validate_scenario_template(load_json(SCENARIO_DIR / "warm-rain.json"))

    assert "does not block the baseline Golden Path" in template.expected_behavior
    assert template.expected_diagnostics.rain_onset == "record rain onset if present"


def test_malformed_committed_template_fails_validation() -> None:
    data = load_json(SCENARIO_DIR / "baseline-shallow-cumulus.json")
    assert isinstance(data, dict)
    data["controls"] = []

    with pytest.raises(ScenarioValidationError, match="product-facing control"):
        validate_scenario_template(data)
