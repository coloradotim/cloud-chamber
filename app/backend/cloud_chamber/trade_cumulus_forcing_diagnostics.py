"""Retained CM1 diagnostic contract for Trade Cumulus large-scale forcing."""

from __future__ import annotations

from typing import Any

import numpy as np

from cloud_chamber.run_cost import ExactNumericalDomain
from cloud_chamber.trade_cumulus_recipes import TradeCumulusControls

FORCING_DIAGNOSTIC_SCHEMA_VERSION = "trade_cumulus_forcing_diagnostics_v1"
FORCING_DIAGNOSTIC_CADENCE_SECONDS = 60
FORCING_DIAGNOSTIC_PATTERN = "cm1out_diag_*.nc"
FORCING_DIAGNOSTIC_FIELDS = {
    "wprof": {
        "dimensions": ["time", "zf", "yh", "xh"],
        "units": "m/s",
        "meaning": "retained large-scale vertical-motion profile",
    },
    "ptb_frc": {
        "dimensions": ["time", "zh", "yh", "xh"],
        "units": "K/s",
        "meaning": "retained large-scale potential-temperature tendency",
    },
    "qvb_frc": {
        "dimensions": ["time", "zh", "yh", "xh"],
        "units": "g/g/s",
        "meaning": "retained large-scale total-water tendency",
    },
}


def forcing_diagnostic_contract(
    *,
    duration_seconds: int,
    numerical: ExactNumericalDomain,
) -> dict[str, Any]:
    if duration_seconds % FORCING_DIAGNOSTIC_CADENCE_SECONDS:
        raise ValueError("Trade Cumulus duration must align with the forcing diagnostic cadence.")
    return {
        "schema_version": FORCING_DIAGNOSTIC_SCHEMA_VERSION,
        "file_pattern": FORCING_DIAGNOSTIC_PATTERN,
        "cadence_seconds": FORCING_DIAGNOSTIC_CADENCE_SECONDS,
        "expected_file_count": (duration_seconds // FORCING_DIAGNOSTIC_CADENCE_SECONDS + 1),
        "first_time_seconds": 0,
        "last_time_seconds": duration_seconds,
        "fields": FORCING_DIAGNOSTIC_FIELDS,
        "vertical_grid": {
            "zh_count": numerical.nz,
            "zf_count": numerical.nz + 1,
            "spacing_m": numerical.dz_m,
            "model_top_m": numerical.model_top_m,
        },
        "profile_definition": {
            "wprof": "linear_to_peak_at_1500_m_taper_to_zero_at_2100_m",
            "ptb_frc": "constant_to_1500_m_taper_to_zero_at_2100_m",
            "qvb_frc": "constant_to_300_m_taper_to_zero_at_500_m",
        },
    }


def expected_forcing_profiles(
    controls: TradeCumulusControls,
    *,
    zh_m: np.ndarray,
    zf_m: np.ndarray,
) -> dict[str, np.ndarray]:
    w_factor = np.where(
        zf_m <= 1_500.0,
        zf_m / 1_500.0,
        np.where(zf_m <= 2_100.0, (2_100.0 - zf_m) / 600.0, 0.0),
    )
    temperature_factor = np.where(
        zh_m <= 1_500.0,
        1.0,
        np.where(zh_m <= 2_100.0, (2_100.0 - zh_m) / 600.0, 0.0),
    )
    water_factor = np.where(
        zh_m <= 300.0,
        1.0,
        np.where(zh_m <= 500.0, (500.0 - zh_m) / 200.0, 0.0),
    )
    return {
        "wprof": controls.large_scale_vertical_motion_m_s * w_factor,
        "ptb_frc": controls.temperature_tendency_k_day / 86_400.0 * temperature_factor,
        "qvb_frc": (controls.total_water_tendency_g_kg_day / 86_400_000.0 * water_factor),
    }
