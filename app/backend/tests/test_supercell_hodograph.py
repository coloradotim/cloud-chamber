from __future__ import annotations

import hashlib

import pytest

from cloud_chamber import supercell_hodograph
from cloud_chamber.supercell_hodograph import (
    STRAIGHT_LINE_HODOGRAPH_MARKER,
    StraightLineHodographError,
    render_straight_line_hodograph_source,
    straight_line_hodograph_artifact,
)


def _source() -> str:
    return """      subroutine base
!-----------------------------------------------------------------------

      ENDIF    ! endif for iwnd options
      end subroutine base
"""


def test_render_adds_only_one_source_locked_straight_line_branch() -> None:
    source = _source()

    rendered = render_straight_line_hodograph_source(source)

    assert rendered.count(STRAIGHT_LINE_HODOGRAPH_MARKER) == 1
    assert "ELSEIF(iwnd.eq.12)THEN" in rendered
    assert "+min(max(zu,0.0),6000.0)/6000.0*31.0" in rendered
    assert "+min(max(zv,0.0),6000.0)/6000.0*7.0" in rendered
    assert rendered.endswith("      end subroutine base\n")


def test_artifact_records_original_and_patched_source_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source()
    monkeypatch.setattr(
        supercell_hodograph,
        "PINNED_BASE_F_SHA256",
        hashlib.sha256(source.encode()).hexdigest(),
    )

    artifact = straight_line_hodograph_artifact(source)

    assert artifact["original_source_sha256"] == hashlib.sha256(source.encode()).hexdigest()
    assert (
        artifact["patched_source_sha256"]
        == hashlib.sha256(render_straight_line_hodograph_source(source).encode()).hexdigest()
    )
    scientific_scope = artifact["scientific_scope"]
    wind_profile = artifact["wind_profile"]
    assert isinstance(scientific_scope, dict)
    assert isinstance(wind_profile, dict)
    assert scientific_scope["changed"] == ["hodograph_geometry"]
    assert wind_profile["endpoint_shear_m_s"] == [31.0, 7.0]


def test_render_fails_closed_when_source_anchor_changes() -> None:
    with pytest.raises(StraightLineHodographError, match="branch terminator"):
        render_straight_line_hodograph_source("changed source")
