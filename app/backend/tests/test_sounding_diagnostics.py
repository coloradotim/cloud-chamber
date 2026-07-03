from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.observed_sounding import (
    ObservedSoundingLevel,
    ObservedSoundingRecord,
    ObservedSoundingValidation,
    parse_igra_station_text,
)
from cloud_chamber.sounding_diagnostics import (
    SoundingDiagnosticFeature,
    compute_sounding_diagnostics,
)


def _record() -> ObservedSoundingRecord:
    return parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding


def _feature(record: ObservedSoundingRecord, key: str) -> SoundingDiagnosticFeature:
    diagnostics = compute_sounding_diagnostics(record)
    return diagnostics.feature_values[key]


def _qv_g_kg_from_dewpoint(pressure_pa: float, dewpoint_c: float) -> float:
    vapor_pressure_hpa = 6.112 * math.exp((17.67 * dewpoint_c) / (dewpoint_c + 243.5))
    pressure_hpa = pressure_pa / 100.0
    mixing_ratio = 0.622 * vapor_pressure_hpa / (pressure_hpa - vapor_pressure_hpa)
    return mixing_ratio * 1000.0


def _synthetic_record() -> ObservedSoundingRecord:
    pressure_pa = [100000.0, 90000.0, 80000.0, 70000.0, 60000.0, 50000.0]
    heights_m = [0.0, 1000.0, 2000.0, 3000.0, 4000.0, 6000.0]
    temperatures_c = [20.0, 14.0, 8.0, 5.0, 7.0, -10.0]
    qv_g_kg = [
        _qv_g_kg_from_dewpoint(100000.0, 16.0),
        10.0,
        8.0,
        6.0,
        4.0,
        2.0,
    ]
    winds = [(0.0, 0.0), (3.0, 4.0), (4.5, 6.0), (6.0, 8.0), (4.0, 9.0), (0.0, 12.0)]
    levels = [
        ObservedSoundingLevel(
            pressure_pa=pressure,
            source_height_m_msl=350.0 + height,
            model_z_m=height,
            temperature_c=temperature,
            potential_temperature_k=temperature + 273.15,
            qv_g_kg=qv,
            u_wind_m_s=u_wind,
            v_wind_m_s=v_wind,
        )
        for pressure, height, temperature, qv, (u_wind, v_wind) in zip(
            pressure_pa, heights_m, temperatures_c, qv_g_kg, winds, strict=True
        )
    ]
    return ObservedSoundingRecord(
        uploaded_filename="synthetic-known-profile.txt",
        station_id="TEST00000001",
        station_name="Synthetic Known Profile",
        station_latitude=40.0,
        station_longitude=-100.0,
        station_elevation_m_msl=350.0,
        valid_time_utc=datetime(2026, 7, 3, tzinfo=UTC),
        source_time_text="2026 07 03 00",
        source_units={
            "pressure": "Pa",
            "height": "m",
            "temperature": "C",
            "qv": "g/kg",
            "wind": "m/s",
        },
        converted_cm1_units={
            "height": "m AGL",
            "potential_temperature": "K",
            "qv": "g/kg",
            "wind": "m/s",
        },
        source_vertical_coordinate_type="synthetic_height_m_agl",
        model_bottom_elevation_m_msl=350.0,
        levels=levels,
        wind_handling="synthetic_observed_wind_profile",
        conversion_choices={"fixture": "known numeric regression profile"},
        validation=ObservedSoundingValidation(status="accepted"),
        provenance={"station_metadata_source": "synthetic_test_fixture"},
    )


def test_synthetic_profile_has_known_numeric_diagnostics() -> None:
    diagnostics = compute_sounding_diagnostics(_synthetic_record())
    features = diagnostics.feature_values

    assert features["estimated_lcl_height_m_agl"].value == pytest.approx(500.0)
    assert features["lapse_rate_0_1000m_c_per_km"].value == pytest.approx(6.0)
    assert features["lapse_rate_0_3000m_c_per_km"].value == pytest.approx(5.0)
    assert features["inversion_strength_c"].value == pytest.approx(2.0)
    assert features["inversion_base_m_agl"].value == pytest.approx(3000.0)
    assert features["inversion_top_m_agl"].value == pytest.approx(4000.0)
    assert features["bulk_shear_0_1km_m_s"].value == pytest.approx(5.0)
    assert features["bulk_shear_0_3km_m_s"].value == pytest.approx(10.0)
    assert features["bulk_shear_0_6km_m_s"].value == pytest.approx(12.0)
    assert features["freezing_level_m_agl"].value == pytest.approx(4823.5)


def test_sounding_diagnostics_payload_has_quality_provenance_and_required_features() -> None:
    diagnostics = compute_sounding_diagnostics(_record())

    assert diagnostics.diagnostic_version == "sounding-diagnostics-v1"
    assert diagnostics.station_id == "USM00072558"
    assert diagnostics.provenance["source_format"] == "igra_station_text"
    assert diagnostics.provenance["diagnostic_claim"].startswith("computed from observed sounding")
    assert diagnostics.data_quality.score_0_to_100 > 0
    assert diagnostics.data_quality.usable_levels_below_1km >= 2
    assert set(diagnostics.feature_values) >= {
        "data_completeness_score",
        "lowest_level_m_agl",
        "profile_top_m_agl",
        "usable_levels_below_1km",
        "has_temperature",
        "has_moisture",
        "has_pressure",
        "has_height",
        "has_observed_wind_profile",
        "estimated_lcl_height_m_agl",
        "mean_qv_0_1000m_g_kg",
        "lapse_rate_0_1000m_c_per_km",
        "cap_strength_proxy",
        "bulk_shear_0_6km_m_s",
        "surface_based_cape_j_kg",
        "srh_0_1km_m2_s2",
    }

    dumped = diagnostics.model_dump(mode="json")
    assert dumped["feature_values"]["data_completeness_score"]["support_state"] == "supported"


def test_sounding_diagnostics_compute_moisture_lcl_lapse_and_cap_proxies() -> None:
    diagnostics = compute_sounding_diagnostics(_record())
    features = diagnostics.feature_values

    assert features["surface_or_lowest_temperature_c"].support_state == "supported"
    assert features["surface_or_lowest_dewpoint_c"].support_state == "supported"
    assert features["surface_t_td_spread_c"].value is not None
    assert features["estimated_lcl_height_m_agl"].support_state == "supported"
    assert features["estimated_lcl_height_m_agl"].value is not None
    assert float(features["estimated_lcl_height_m_agl"].value) >= 0
    assert features["mean_qv_0_500m_g_kg"].support_state == "supported"
    assert features["mean_qv_0_1000m_g_kg"].support_state == "supported"
    assert features["mean_qv_0_3000m_g_kg"].support_state == "supported"
    assert features["lapse_rate_0_1000m_c_per_km"].support_state == "supported"
    assert features["lapse_rate_0_3000m_c_per_km"].support_state == "supported"
    assert features["cap_strength_proxy"].support_state == "supported"


def test_sounding_diagnostics_compute_bulk_shear_from_observed_wind_profile() -> None:
    diagnostics = compute_sounding_diagnostics(_record())
    features = diagnostics.feature_values

    assert features["wind_available"].value is True
    assert features["wind_profile_depth_m"].support_state == "supported"
    assert features["bulk_shear_0_1km_m_s"].support_state == "supported"
    assert features["bulk_shear_0_3km_m_s"].support_state == "supported"
    assert features["bulk_shear_0_6km_m_s"].support_state == "supported"
    assert features["mean_wind_0_6km_m_s"].support_state == "supported"


def test_missing_wind_profile_caveats_wind_diagnostics_without_guessing_srh() -> None:
    record = _record()
    missing_wind = record.model_copy(
        update={
            "levels": [
                level.model_copy(update={"u_wind_m_s": None, "v_wind_m_s": None})
                for level in record.levels
            ]
        }
    )
    diagnostics = compute_sounding_diagnostics(missing_wind)
    features = diagnostics.feature_values

    assert features["wind_available"].value is False
    assert features["has_observed_wind_profile"].value is False
    assert features["bulk_shear_0_1km_m_s"].support_state == "unavailable"
    assert features["bulk_shear_0_3km_m_s"].support_state == "unavailable"
    assert features["bulk_shear_0_6km_m_s"].support_state == "unavailable"
    assert features["srh_0_1km_m2_s2"].support_state == "unavailable"
    assert "observed_wind_profile_missing_or_incomplete" in diagnostics.caveats


def test_missing_moisture_caveats_moisture_diagnostics_without_calling_it_dry() -> None:
    record = _record()
    missing_moisture = record.model_copy(
        update={
            "levels": [level.model_copy(update={"qv_g_kg": math.nan}) for level in record.levels]
        }
    )
    diagnostics = compute_sounding_diagnostics(missing_moisture)
    features = diagnostics.feature_values

    assert features["has_moisture"].value is False
    assert features["surface_or_lowest_dewpoint_c"].support_state == "unavailable"
    assert features["estimated_lcl_height_m_agl"].support_state == "unavailable"
    assert features["mean_qv_0_1000m_g_kg"].support_state == "unavailable"
    assert features["midlevel_dry_layer_proxy"].support_state == "unavailable"
    assert features["dry_microburst_inverted_v_proxy"].support_state == "unavailable"


@pytest.mark.parametrize(
    "key",
    [
        "surface_based_cape_j_kg",
        "surface_based_cin_j_kg",
        "mixed_layer_cape_j_kg",
        "mixed_layer_cin_j_kg",
        "lfc_height_m_agl",
        "el_height_m_agl",
        "srh_0_1km_m2_s2",
        "srh_0_3km_m2_s2",
        "wet_bulb_zero_m_agl_or_unavailable",
        "warm_nose_depth_m_or_unavailable",
        "subfreezing_surface_layer_depth_m_or_unavailable",
    ],
)
def test_unimplemented_science_diagnostics_are_unavailable_not_fake_values(key: str) -> None:
    feature = _feature(_record(), key)

    assert feature.support_state == "unavailable"
    assert feature.value is None
    assert feature.caveats
