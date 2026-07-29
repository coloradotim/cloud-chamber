from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from cloud_chamber.trade_cumulus_forcing import (
    TRADE_CUMULUS_FORCING_MARKER,
    TradeCumulusForcingError,
    forcing_customization_artifact,
    render_trade_cumulus_forcing_source,
    verify_forcing_artifact,
)


def _source() -> str:
    return """\
    IF( testcase .eq. 3 )THEN
      ! shallow Cu case  (Siebesma et al, 2003, JAS)
      wmin  =  -0.0065
      radsfc = -2.0/( 3600.0 * 24.0 )
      qvsfc  = -1.2e-8
      qvfrc(k) = -1.2e-8
    ENDIF
    IF( testcase .eq. 4 )THEN
    ENDIF
"""


def test_forcing_artifact_is_source_locked_and_uses_absolute_values(tmp_path: Path) -> None:
    artifact = forcing_customization_artifact(
        _source(),
        vertical_motion_m_s=0.015,
        temperature_tendency_k_day=4.0,
        total_water_tendency_g_kg_day=6.0,
    )
    path = tmp_path / "trade_cumulus_forcing_customization.json"
    import json

    path.write_text(json.dumps(artifact))
    verified = verify_forcing_artifact(path, _source())
    rendered = render_trade_cumulus_forcing_source(_source(), verified["forcing"])

    assert TRADE_CUMULUS_FORCING_MARKER in rendered
    assert "wmin  =  1.500000000000d-02" in rendered
    assert "radsfc = 4.629629629630d-05" in rendered
    assert "qvsfc  = 6.944444444444d-08" in rendered
    assert "qvfrc(k) = qvsfc" in rendered
    assert artifact["original_source_sha256"] == hashlib.sha256(_source().encode()).hexdigest()


def test_forcing_artifact_rejects_changed_or_already_patched_source(tmp_path: Path) -> None:
    artifact = forcing_customization_artifact(
        _source(),
        vertical_motion_m_s=-0.01,
        temperature_tendency_k_day=-3.0,
        total_water_tendency_g_kg_day=-2.0,
    )
    path = tmp_path / "forcing.json"
    import json

    path.write_text(json.dumps(artifact))

    with pytest.raises(TradeCumulusForcingError, match="does not match"):
        verify_forcing_artifact(path, _source() + "! changed\n")
    with pytest.raises(TradeCumulusForcingError, match="already contains"):
        render_trade_cumulus_forcing_source(
            _source().replace(
                "! shallow Cu case  (Siebesma et al, 2003, JAS)",
                f"! {TRADE_CUMULUS_FORCING_MARKER}",
            ),
            artifact["forcing"],
        )
