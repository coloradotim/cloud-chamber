from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from cloud_chamber import supercells_source_customization
from cloud_chamber.supercells_source_customization import (
    SUPERCELLS_SOURCE_CUSTOMIZATION_MARKER,
    SupercellsSourceCustomizationError,
    load_supercells_source_customization,
    render_supercells_source,
    supercells_source_customization_artifact,
)


def _source() -> str:
    return """      IF(iinit.eq.1)THEN

        ric     =  centerx  ! center of bubble in x-direction (m)
        rjc     =  centery  ! center of bubble in y-direction (m)
        zc      =   1400.0  ! height of center of bubble above ground (m)
        bhrad   =  10000.0  ! horizontal radius of bubble (m)
        bvrad   =   1400.0  ! vertical radius of bubble (m)
        bptpert =      1.0  ! max potential temp perturbation (K)

        maintain_rh = .false.
"""


def _initiation() -> dict[str, float]:
    return {
        "amplitude_k": -2.5,
        "horizontal_radius_m": 17_500.0,
        "vertical_radius_m": 2_750.0,
        "center_height_m_agl": 4_000.0,
        "center_x_m": -12_000.0,
        "center_y_m": 8_500.0,
    }


def test_render_replaces_the_single_thermal_with_exact_physical_values() -> None:
    rendered = render_supercells_source(_source(), _initiation())

    assert rendered.count(SUPERCELLS_SOURCE_CUSTOMIZATION_MARKER) == 1
    assert "centerx + -12000.000000" in rendered
    assert "centery + 8500.000000" in rendered
    assert "zc      =  4000.000000" in rendered
    assert "bhrad   =  17500.000000" in rendered
    assert "bvrad   =  2750.000000" in rendered
    assert "bptpert =  -2.500000" in rendered
    assert "maintain_rh = .false." in rendered


def test_artifact_binds_source_profile_and_initiation_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = _source()
    monkeypatch.setattr(
        supercells_source_customization,
        "PINNED_INIT3D_F_SHA256",
        hashlib.sha256(source.encode()).hexdigest(),
    )
    artifact = supercells_source_customization_artifact(
        source,
        initiation=_initiation(),
        wind_profile=[{"height_m": 0.0, "u_m_s": 1.0, "v_m_s": 2.0}],
        thermodynamic_profile=[
            {
                "height_m": 0.0,
                "pressure_pa": 100_000.0,
                "theta_k": 300.0,
            }
        ],
    )
    artifact_path = tmp_path / "cm1_source_customization.json"
    artifact_path.write_text(json.dumps(artifact))

    loaded = load_supercells_source_customization(artifact_path)

    assert loaded["initiation"] == _initiation()
    assert loaded["original_source_sha256"] == hashlib.sha256(source.encode()).hexdigest()
    assert (
        loaded["patched_source_sha256"]
        == hashlib.sha256(render_supercells_source(source, _initiation()).encode()).hexdigest()
    )
    assert loaded["input_contract"]["no_silent_stock_profile_fallback"] is True


def test_render_fails_closed_when_source_anchor_or_values_change() -> None:
    with pytest.raises(SupercellsSourceCustomizationError, match="thermal block"):
        render_supercells_source("changed source", _initiation())
    with pytest.raises(SupercellsSourceCustomizationError, match="missing values"):
        render_supercells_source(_source(), {"amplitude_k": 1.0})
