from __future__ import annotations

from datetime import UTC, datetime

import pytest
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.observed_sounding import (
    ObservedSoundingError,
    ObservedSoundingLevel,
    StationMetadata,
    _validate_levels,
    parse_igra_station_text,
    render_observed_input_sounding,
    summarize_igra_station_text,
)


def test_parse_igra_station_text_defaults_to_latest_sounding() -> None:
    parsed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    )

    assert len(parsed.available_soundings) == 2
    record = parsed.selected_sounding
    assert record.station_id == "USM00072558"
    assert record.station_name == "Valley, Nebraska"
    assert record.valid_time_utc == datetime(2025, 1, 2, tzinfo=UTC)
    assert record.station_latitude == pytest.approx(41.32)
    assert record.station_longitude == pytest.approx(-96.3669)
    assert record.station_elevation_m_msl == pytest.approx(351.5)
    assert record.model_bottom_elevation_m_msl == pytest.approx(351.5)
    assert record.source_vertical_coordinate_type == "geopotential_height_msl"
    assert record.levels[0].source_height_m_msl == pytest.approx(352.0)
    assert record.levels[0].model_z_m == pytest.approx(0.5)
    assert record.levels[-1].model_z_m > 18000
    assert record.validation.status == "needs_review"
    assert "station elevation joined" in " ".join(record.validation.caveats)
    assert "observed_sounding_winds" in record.wind_handling
    assert record.provenance["wind_source"] == "observed_igra_wind_profile"
    assert record.levels[0].u_wind_m_s is not None
    assert record.levels[0].v_wind_m_s is not None


def test_summarize_igra_station_text_lists_times_without_package_validation() -> None:
    summaries = summarize_igra_station_text(IGRA_FIXTURE)

    assert len(summaries) == 2
    assert summaries[0].station_id == "USM00072558"
    assert summaries[0].valid_time_utc == datetime(2025, 1, 1, tzinfo=UTC)
    assert summaries[0].num_levels > 0


def test_parse_igra_station_text_accepts_supplied_station_metadata() -> None:
    alternate_station_text = IGRA_FIXTURE.replace("USM00072558", "USM00072357")
    parsed = parse_igra_station_text(
        alternate_station_text,
        uploaded_filename="USM00072357-data-beg2025.txt",
        station_metadata=StationMetadata(
            station_id="USM00072357",
            station_name="Norman, Oklahoma",
            latitude=35.2456,
            longitude=-97.4721,
            elevation_m_msl=357.0,
            source="IGRA recent cache station metadata",
        ),
    )

    record = parsed.selected_sounding
    assert record.station_id == "USM00072357"
    assert record.station_name == "Norman, Oklahoma"
    assert record.station_elevation_m_msl == pytest.approx(357.0)
    assert record.model_bottom_elevation_m_msl == pytest.approx(357.0)
    assert "station elevation joined from IGRA recent cache" in " ".join(record.validation.caveats)


def test_parse_igra_station_text_selects_requested_sounding_time() -> None:
    parsed = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
        selected_time_utc=datetime(2025, 1, 1, tzinfo=UTC),
    )

    assert parsed.selected_sounding.valid_time_utc == datetime(2025, 1, 1, tzinfo=UTC)


def test_parse_igra_station_text_rejects_unsupported_non_igra_file() -> None:
    with pytest.raises(ObservedSoundingError, match="No IGRA sounding headers"):
        parse_igra_station_text("not a sounding", uploaded_filename="notes.txt")


def test_parse_igra_station_text_blocks_too_shallow_profile() -> None:
    shallow = "\n".join(IGRA_FIXTURE.splitlines()[:6])

    with pytest.raises(ObservedSoundingError, match="too_few|profile_top"):
        parse_igra_station_text(shallow, uploaded_filename="USM00072558-data-beg2025.txt")


def test_validate_levels_allows_plausible_upper_level_theta_above_500k() -> None:
    levels = [
        ObservedSoundingLevel(
            pressure_pa=100000.0,
            source_height_m_msl=0.0,
            model_z_m=0.0,
            temperature_c=20.0,
            potential_temperature_k=293.0,
            qv_g_kg=10.0,
            u_wind_m_s=1.0,
            v_wind_m_s=2.0,
        ),
        ObservedSoundingLevel(
            pressure_pa=85000.0,
            source_height_m_msl=1500.0,
            model_z_m=1500.0,
            temperature_c=10.0,
            potential_temperature_k=296.0,
            qv_g_kg=8.0,
            u_wind_m_s=1.0,
            v_wind_m_s=2.0,
        ),
        ObservedSoundingLevel(
            pressure_pa=50000.0,
            source_height_m_msl=5500.0,
            model_z_m=5500.0,
            temperature_c=-15.0,
            potential_temperature_k=320.0,
            qv_g_kg=2.0,
            u_wind_m_s=1.0,
            v_wind_m_s=2.0,
        ),
        ObservedSoundingLevel(
            pressure_pa=20000.0,
            source_height_m_msl=12000.0,
            model_z_m=12000.0,
            temperature_c=-55.0,
            potential_temperature_k=430.0,
            qv_g_kg=0.1,
            u_wind_m_s=1.0,
            v_wind_m_s=2.0,
        ),
        ObservedSoundingLevel(
            pressure_pa=5000.0,
            source_height_m_msl=19000.0,
            model_z_m=19000.0,
            temperature_c=-60.0,
            potential_temperature_k=520.0,
            qv_g_kg=0.01,
            u_wind_m_s=1.0,
            v_wind_m_s=2.0,
        ),
    ]
    errors: list[str] = []

    _validate_levels(levels, errors, [])

    assert "implausible_potential_temperature_value" not in errors


def test_parse_igra_station_text_blocks_missing_wind_profile() -> None:
    missing_wind = "\n".join(_blank_wind_fields(line) for line in IGRA_FIXTURE.splitlines())

    with pytest.raises(ObservedSoundingError, match="observed_wind_profile_missing"):
        parse_igra_station_text(
            missing_wind,
            uploaded_filename="USM00072558-data-beg2025.txt",
        )


def test_render_observed_input_sounding_is_numeric_cm1_facing() -> None:
    record = parse_igra_station_text(
        IGRA_FIXTURE,
        uploaded_filename="USM00072558-data-beg2025.txt",
    ).selected_sounding

    rendered = render_observed_input_sounding(record)
    lines = rendered.splitlines()

    assert len(lines[0].split()) == 3
    assert len(lines[1].split()) == 5
    assert float(lines[0].split()[0]) == pytest.approx(record.levels[0].pressure_pa / 100.0)
    assert float(lines[1].split()[0]) == pytest.approx(0.0)
    assert float(lines[1].split()[3]) == pytest.approx(record.levels[0].u_wind_m_s, abs=0.01)
    assert float(lines[1].split()[4]) == pytest.approx(record.levels[0].v_wind_m_s, abs=0.01)
    assert float(lines[1].split()[3]) != pytest.approx(0.0)
    assert float(lines[1].split()[4]) != pytest.approx(0.0)
    assert float(lines[-1].split()[0]) > 18000
    assert "USM00072558" not in rendered


def _blank_wind_fields(line: str) -> str:
    if line.startswith("#") or len(line) < 51:
        return line
    return f"{line[:40]}-9999{line[45:46]}-9999{line[51:]}"
