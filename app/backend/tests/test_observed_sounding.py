from __future__ import annotations

from datetime import UTC, datetime

import pytest
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.observed_sounding import (
    ObservedSoundingError,
    parse_igra_station_text,
    render_observed_input_sounding,
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
    assert "metadata_only" in record.wind_handling


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
    assert float(lines[-1].split()[0]) > 18000
    assert "USM00072558" not in rendered
