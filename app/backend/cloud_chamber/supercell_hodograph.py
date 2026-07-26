"""Source-locked straight-line hodograph customization for Supercells Compare."""

from __future__ import annotations

import hashlib
from pathlib import Path

STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND = "straight_line_hodograph_v1"
STRAIGHT_LINE_HODOGRAPH_SCHEMA_VERSION = "supercell_straight_line_hodograph_v1"
STRAIGHT_LINE_HODOGRAPH_ARTIFACT_FILENAME = "straight_line_hodograph_customization.json"
STRAIGHT_LINE_HODOGRAPH_MARKER = "CLOUD_CHAMBER_STRAIGHT_LINE_HODOGRAPH_V1"
STRAIGHT_LINE_HODOGRAPH_TARGET = Path("src/base.F")
PINNED_BASE_F_SHA256 = "9c88a1021ddde22d02680786246c52bcffb040cbd72c3c4708f24fe24eec32ef"

# The stock iwnd=2 profile has a 0-6 km endpoint shear of (31, 7) m/s and
# a layer-mean wind of (13.5145538645, 6.1521128022) m/s. These endpoints
# preserve both quantities while removing the quarter-circle curvature.
SURFACE_U_M_S = -1.9854461355
SURFACE_V_M_S = 2.6521128022
SIX_KM_U_M_S = 29.0145538645
SIX_KM_V_M_S = 9.6521128022
SHEAR_TOP_M = 6000.0

_WIND_BRANCH_ANCHOR = """!-----------------------------------------------------------------------

      ENDIF    ! endif for iwnd options
"""


class StraightLineHodographError(RuntimeError):
    """Raised when the pinned CM1 hodograph customization cannot be reproduced."""


def render_straight_line_hodograph_source(source: str) -> str:
    if STRAIGHT_LINE_HODOGRAPH_MARKER in source:
        raise StraightLineHodographError(
            "CM1 base.F already contains the straight-line hodograph customization."
        )
    if source.count(_WIND_BRANCH_ANCHOR) != 1:
        raise StraightLineHodographError(
            "Unable to locate the pinned CM1 iwnd branch terminator in base.F."
        )
    branch = f"""!-----------------------------------------------------------------------
!  iwnd = 12
!  Cloud Chamber controlled straight-line hodograph.
!  Preserves iwnd=2 0-6 km shear and layer-mean wind.

      ELSEIF(iwnd.eq.12)THEN

        do k=1,nk
        do j=1,nj
        do i=1,ni+1
          zu=0.5*(zh(i-1,j,k)+zh(i,j,k))
          u0(i,j,k)={SURFACE_U_M_S:.10f}                                  &
     &      +min(max(zu,0.0),{SHEAR_TOP_M:.1f})/{SHEAR_TOP_M:.1f}*31.0
        enddo
        enddo
        enddo

        do k=1,nk
        do j=1,nj+1
        do i=1,ni
          zv=0.5*(zh(i,j-1,k)+zh(i,j,k))
          v0(i,j,k)={SURFACE_V_M_S:.10f}                                  &
     &      +min(max(zv,0.0),{SHEAR_TOP_M:.1f})/{SHEAR_TOP_M:.1f}*7.0
        enddo
        enddo
        enddo

!  {STRAIGHT_LINE_HODOGRAPH_MARKER}

!-----------------------------------------------------------------------

      ENDIF    ! endif for iwnd options
"""
    return source.replace(_WIND_BRANCH_ANCHOR, branch, 1)


def straight_line_hodograph_artifact(source: str) -> dict[str, object]:
    source_sha256 = _sha256_text(source)
    if source_sha256 != PINNED_BASE_F_SHA256:
        raise StraightLineHodographError(
            "Configured CM1 base.F does not match the accepted r21.1 source lock: "
            f"{source_sha256} != {PINNED_BASE_F_SHA256}."
        )
    patched = render_straight_line_hodograph_source(source)
    return {
        "schema_version": STRAIGHT_LINE_HODOGRAPH_SCHEMA_VERSION,
        "customization_kind": STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND,
        "target_relative_path": str(STRAIGHT_LINE_HODOGRAPH_TARGET),
        "marker": STRAIGHT_LINE_HODOGRAPH_MARKER,
        "original_source_sha256": source_sha256,
        "patched_source_sha256": _sha256_text(patched),
        "wind_profile": {
            "vertical_extent_m": [0.0, SHEAR_TOP_M],
            "surface_wind_m_s": [SURFACE_U_M_S, SURFACE_V_M_S],
            "six_km_wind_m_s": [SIX_KM_U_M_S, SIX_KM_V_M_S],
            "endpoint_shear_m_s": [31.0, 7.0],
            "layer_mean_wind_m_s": [13.5145538645, 6.1521128022],
            "above_six_km": "constant",
            "model_translation_m_s": [12.5, 3.0],
        },
        "scientific_scope": {
            "changed": ["hodograph_geometry"],
            "preserved": [
                "thermodynamic_profile",
                "deterministic_warm_bubble",
                "domain_and_grid",
                "time_step_and_duration",
                "output_contract",
                "microphysics",
                "boundaries",
                "damping",
                "numerical_options",
                "model_translation",
            ],
        },
        "source_policy": {
            "isolated_external_build": True,
            "original_cm1_tree_modified": False,
            "cm1_source_committed_to_repo": False,
        },
    }


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


__all__ = [
    "PINNED_BASE_F_SHA256",
    "SHEAR_TOP_M",
    "SIX_KM_U_M_S",
    "SIX_KM_V_M_S",
    "STRAIGHT_LINE_HODOGRAPH_ARTIFACT_FILENAME",
    "STRAIGHT_LINE_HODOGRAPH_CUSTOMIZATION_KIND",
    "STRAIGHT_LINE_HODOGRAPH_MARKER",
    "STRAIGHT_LINE_HODOGRAPH_SCHEMA_VERSION",
    "STRAIGHT_LINE_HODOGRAPH_TARGET",
    "SURFACE_U_M_S",
    "SURFACE_V_M_S",
    "StraightLineHodographError",
    "render_straight_line_hodograph_source",
    "straight_line_hodograph_artifact",
]
