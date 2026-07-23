from pathlib import Path

import pytest

from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storm_examination import StormExaminationError
from cloud_chamber.supercells_world import supercells_world_detail


def _settings(runtime_home: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def test_world_exposes_stable_identity_and_data_driven_timeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.storm_examination_inventory",
        lambda _settings: tuple(
            (tmp_path / f"cm1out_{index + 1:06d}.nc", float(index * 120)) for index in range(91)
        ),
    )

    detail = supercells_world_detail(_settings(tmp_path))

    assert detail.world_id == "supercells"
    assert detail.display_name == "Supercells"
    assert len(detail.simulations) == 1
    simulation = detail.reference_simulation
    assert simulation.simulation_id == "supercells_quarter_circle_reference"
    assert simulation.display_name == "Quarter-Circle Supercell"
    assert simulation.run_id == "quarter-circle-supercell-presentation-v1-20260723"
    assert simulation.case_id == "cm1_r21_1_quarter_circle_supercell_presentation_v1"
    assert simulation.explore_available is True
    assert simulation.saved_output_count == 91
    assert simulation.model_end_seconds == 10_800
    assert simulation.history_cadence_seconds == 120
    assert simulation.default_explore_time_index == 37
    assert detail.capabilities.lab is False
    assert detail.capabilities.compare is False
    assert detail.summary().simulation_count == 1


def test_world_remains_usable_when_retained_output_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unavailable(_settings: CloudChamberSettings) -> None:
        raise StormExaminationError("The accepted Gate B retained output is unavailable.")

    monkeypatch.setattr("cloud_chamber.supercells_world.storm_examination_inventory", unavailable)

    detail = supercells_world_detail(_settings(tmp_path))

    assert detail.availability_state == "unavailable"
    assert detail.reference_simulation.technical_state == "missing"
    assert detail.reference_simulation.explore_available is False
    assert detail.simulations[0].simulation_id == "supercells_quarter_circle_reference"
    assert detail.summary().simulation_count == 0
