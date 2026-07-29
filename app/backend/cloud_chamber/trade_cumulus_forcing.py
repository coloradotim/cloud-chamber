"""Source-locked CM1 forcing customization for Trade Cumulus variations."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND = "trade_cumulus_forcing_v1"
TRADE_CUMULUS_FORCING_SCHEMA_VERSION = "trade_cumulus_forcing_customization_v1"
TRADE_CUMULUS_FORCING_ARTIFACT_FILENAME = "trade_cumulus_forcing_customization.json"
TRADE_CUMULUS_FORCING_TARGET = Path("src/base.F")
TRADE_CUMULUS_FORCING_MARKER = "CLOUD_CHAMBER_TRADE_CUMULUS_FORCING_V1"


class TradeCumulusForcingError(ValueError):
    """Raised when the pinned BOMEX forcing block cannot be customized exactly."""


def forcing_customization_artifact(
    original_source: str,
    *,
    vertical_motion_m_s: float,
    temperature_tendency_k_day: float,
    total_water_tendency_g_kg_day: float,
) -> dict[str, Any]:
    forcing = {
        "vertical_motion_m_s": vertical_motion_m_s,
        "temperature_tendency_k_day": temperature_tendency_k_day,
        "total_water_tendency_g_kg_day": total_water_tendency_g_kg_day,
    }
    rendered = render_trade_cumulus_forcing_source(original_source, forcing)
    return {
        "schema_version": TRADE_CUMULUS_FORCING_SCHEMA_VERSION,
        "customization_kind": TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND,
        "target": str(TRADE_CUMULUS_FORCING_TARGET),
        "original_source_sha256": _sha256_text(original_source),
        "patched_source_sha256": _sha256_text(rendered),
        "forcing": forcing,
        "profile_shape": {
            "vertical_motion": "zero_to_peak_at_1500m_tapering_to_zero_at_2100m",
            "temperature_tendency": "peak_through_1500m_tapering_to_zero_at_2100m",
            "total_water_tendency": "peak_through_300m_tapering_to_zero_at_500m",
        },
    }


def load_forcing_customization(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise TradeCumulusForcingError(
            "Trade Cumulus forcing customization could not be read."
        ) from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != TRADE_CUMULUS_FORCING_SCHEMA_VERSION
        or payload.get("customization_kind") != TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND
        or payload.get("target") != str(TRADE_CUMULUS_FORCING_TARGET)
        or not isinstance(payload.get("forcing"), dict)
    ):
        raise TradeCumulusForcingError("Trade Cumulus forcing customization is invalid.")
    forcing = payload["forcing"]
    required = {
        "vertical_motion_m_s",
        "temperature_tendency_k_day",
        "total_water_tendency_g_kg_day",
    }
    if set(forcing) != required or any(
        not isinstance(forcing[key], int | float) for key in required
    ):
        raise TradeCumulusForcingError("Trade Cumulus forcing values are invalid.")
    return payload


def render_trade_cumulus_forcing_source(
    source: str,
    forcing: dict[str, Any],
) -> str:
    if TRADE_CUMULUS_FORCING_MARKER in source:
        raise TradeCumulusForcingError("CM1 source already contains the Trade Cumulus patch.")
    start = source.find("    IF( testcase .eq. 3 )THEN")
    end = source.find("    IF( testcase .eq. 4 )THEN", start)
    if start < 0 or end < 0:
        raise TradeCumulusForcingError("Unable to locate the pinned BOMEX forcing block.")
    block = source[start:end]
    replacements = (
        (
            r"(?m)^(\s*)wmin\s*=\s*-0\.0065\s*$",
            rf"\1wmin  =  {_fortran(float(forcing['vertical_motion_m_s']))}",
        ),
        (
            r"(?m)^(\s*)radsfc\s*=\s*-2\.0\s*/\(\s*3600\.0\s*\*\s*24\.0\s*\)\s*$",
            rf"\1radsfc = {_fortran(float(forcing['temperature_tendency_k_day']) / 86_400.0)}",
        ),
        (
            r"(?m)^(\s*)qvsfc\s*=\s*-1\.2e-8\s*$",
            (
                rf"\1qvsfc  = "
                f"{_fortran(float(forcing['total_water_tendency_g_kg_day']) / 86_400_000.0)}"
            ),
        ),
        (
            r"(?m)^(\s*)qvfrc\(k\)\s*=\s*-1\.2e-8\s*$",
            r"\1qvfrc(k) = qvsfc",
        ),
    )
    rendered = block
    for pattern, replacement in replacements:
        rendered, count = re.subn(pattern, replacement, rendered, count=1)
        if count != 1:
            raise TradeCumulusForcingError(
                "Pinned BOMEX forcing source no longer matches the approved patch."
            )
    marker = f"      ! {TRADE_CUMULUS_FORCING_MARKER}\n"
    rendered = rendered.replace(
        "      ! shallow Cu case  (Siebesma et al, 2003, JAS)\n",
        "      ! shallow Cu case  (Siebesma et al, 2003, JAS)\n" + marker,
        1,
    )
    return source[:start] + rendered + source[end:]


def verify_forcing_artifact(path: Path, source: str) -> dict[str, Any]:
    payload = load_forcing_customization(path)
    if payload["original_source_sha256"] != _sha256_text(source):
        raise TradeCumulusForcingError(
            "Configured CM1 source does not match the packaged Trade Cumulus source lock."
        )
    rendered = render_trade_cumulus_forcing_source(source, payload["forcing"])
    if payload["patched_source_sha256"] != _sha256_text(rendered):
        raise TradeCumulusForcingError(
            "Trade Cumulus forcing customization identity does not match its rendered source."
        )
    return payload


def _fortran(value: float) -> str:
    if value == 0.0:
        return "0.0"
    return f"{value:.12e}".replace("e", "d")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
