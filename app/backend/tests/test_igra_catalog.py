from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from cloud_chamber.igra_catalog import (
    IGRACacheManifest,
    IGRACatalogError,
    IGRAStationZipReference,
    build_recent_catalog,
    cache_station_zip,
    cache_station_zip_from_catalog,
    igra_cache_manifest_path,
    parse_recent_directory_listing,
    parse_station_metadata,
    read_igra_cache_manifest,
    read_igra_recent_catalog,
    write_igra_recent_catalog,
)
from cloud_chamber.settings import CloudChamberSettings

DIRECTORY_HTML = """
<html>
  <body>
    <a href="USM00072558-data-beg2025.txt.zip">Valley</a>
    <a href="USM00072469-data-beg2025.txt.zip">Denver</a>
    <a href="USM00099999-data-beg2025.txt.zip">Missing station</a>
    <a href="README.txt">README</a>
    <a href="../">Parent</a>
  </body>
</html>
"""


def station_line(
    station_id: str,
    latitude: float,
    longitude: float,
    elevation: float,
    state: str,
    name: str,
) -> str:
    return (
        f"{station_id:<11} {latitude:8.4f} {longitude:9.4f} {elevation:6.1f} "
        f"{state:<2} {name:<30} {1948:4d} {2026:4d} {50000:6d}"
    )


STATION_LIST = "\n".join(
    [
        station_line("USM00072558", 41.32, -96.3669, 351.5, "NE", "VALLEY"),
        station_line("USM00072469", 39.8328, -104.6575, 1650.0, "CO", "DENVER INTL AIRPORT"),
        station_line("USM00072295", 33.4255, -112.0130, 337.0, "AZ", "PHOENIX"),
    ]
)


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def station_zip(filename: str = "USM00072558-data-beg2025.txt") -> bytes:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr(filename, "#USM00072558 2025 01 01 00\n")
    return payload.getvalue()


def test_recent_directory_parser_finds_station_period_zip_links() -> None:
    references = parse_recent_directory_listing(
        DIRECTORY_HTML,
        base_url="https://example.test/igra/",
    )

    assert [reference.filename for reference in references] == [
        "USM00072469-data-beg2025.txt.zip",
        "USM00072558-data-beg2025.txt.zip",
        "USM00099999-data-beg2025.txt.zip",
    ]
    assert references[1].station_id == "USM00072558"
    assert references[1].begin_year == 2025
    assert references[1].source_url == (
        "https://example.test/igra/USM00072558-data-beg2025.txt.zip"
    )


def test_station_metadata_join_and_great_plains_midwest_filter() -> None:
    catalog = build_recent_catalog(
        directory_html=DIRECTORY_HTML,
        station_metadata_text=STATION_LIST,
        source_url="https://example.test/igra/",
        refreshed_at=datetime(2026, 7, 1, tzinfo=UTC),
    )

    assert [station.station_id for station in catalog.stations] == ["USM00072469", "USM00072558"]
    assert [reference.station_id for reference in catalog.zip_references] == [
        "USM00072469",
        "USM00072558",
    ]
    valley = catalog.zip_references[1]
    assert valley.station_name == "VALLEY"
    assert valley.latitude == pytest.approx(41.32)
    assert valley.longitude == pytest.approx(-96.3669)
    assert valley.region_tags == ["great_plains_midwest"]
    assert valley.cached_status == "not_cached"
    assert "station_metadata_missing_for_recent_links:1" in catalog.caveats


def test_parse_station_metadata_handles_fixed_width_station_list() -> None:
    stations = parse_station_metadata(STATION_LIST)

    valley = stations["USM00072558"]
    assert valley.station_name == "VALLEY"
    assert valley.elevation_m_msl == pytest.approx(351.5)
    assert valley.first_year == 1948
    assert valley.last_year == 2026
    assert valley.record_count == 50000
    assert valley.region_tags == ["great_plains_midwest"]
    assert stations["USM00072295"].region_tags == []


def test_cache_manifest_marks_already_cached_references(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    reference = IGRAStationZipReference(
        station_id="USM00072558",
        filename="USM00072558-data-beg2025.txt.zip",
        begin_year=2025,
        source_url="https://example.test/USM00072558-data-beg2025.txt.zip",
        region_tags=["great_plains_midwest"],
    )
    entry = cache_station_zip(settings, reference, zip_bytes=station_zip())
    manifest = read_igra_cache_manifest(settings)

    catalog = build_recent_catalog(
        directory_html=DIRECTORY_HTML,
        station_metadata_text=STATION_LIST,
        cache_manifest=manifest,
        source_url="https://example.test/igra/",
    )

    cached = next(item for item in catalog.zip_references if item.filename == entry.filename)
    assert cached.cached_status == "cached_extracted"
    assert cached.cached_zip_path == entry.cached_zip_path
    assert cached.cached_text_path == entry.cached_text_path


def test_cache_station_zip_writes_under_runtime_cache_only(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    reference = IGRAStationZipReference(
        station_id="USM00072558",
        station_name="Valley",
        latitude=41.32,
        longitude=-96.3669,
        elevation_m_msl=351.5,
        filename="USM00072558-data-beg2025.txt.zip",
        begin_year=2025,
        source_url="https://example.test/USM00072558-data-beg2025.txt.zip",
        region_tags=["great_plains_midwest"],
    )

    entry = cache_station_zip(settings, reference, zip_bytes=station_zip())

    assert Path(entry.cached_zip_path).is_relative_to(settings.cache_dir)
    assert entry.cached_text_path is not None
    assert Path(entry.cached_text_path).is_relative_to(settings.cache_dir)
    assert Path(entry.cached_zip_path).exists()
    assert Path(entry.cached_text_path).exists()
    manifest = read_igra_cache_manifest(settings)
    assert manifest.entries == [entry]
    assert igra_cache_manifest_path(settings).exists()


def test_cache_station_zip_rejects_zip_slip_entries(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    reference = IGRAStationZipReference(
        station_id="USM00072558",
        filename="USM00072558-data-beg2025.txt.zip",
        begin_year=2025,
        source_url="https://example.test/USM00072558-data-beg2025.txt.zip",
    )
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("../USM00072558-data-beg2025.txt", "unsafe")

    with pytest.raises(IGRACatalogError, match="Unsafe path"):
        cache_station_zip(settings, reference, zip_bytes=payload.getvalue())

    assert not (tmp_path / "USM00072558-data-beg2025.txt").exists()


def test_cache_station_zip_rejects_absolute_entries(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    reference = IGRAStationZipReference(
        station_id="USM00072558",
        filename="USM00072558-data-beg2025.txt.zip",
        begin_year=2025,
        source_url="https://example.test/USM00072558-data-beg2025.txt.zip",
    )
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("/tmp/USM00072558-data-beg2025.txt", "unsafe")

    with pytest.raises(IGRACatalogError, match="Unsafe path"):
        cache_station_zip(settings, reference, zip_bytes=payload.getvalue())


def test_cache_station_zip_from_catalog_uses_cached_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = fake_settings(tmp_path)
    catalog = build_recent_catalog(
        directory_html=DIRECTORY_HTML,
        station_metadata_text=STATION_LIST,
        source_url="https://example.test/igra/",
    )
    write_igra_recent_catalog(settings, catalog)
    monkeypatch.setattr(
        "cloud_chamber.igra_catalog._fetch_url_bytes",
        lambda _url, *, max_bytes: station_zip(),
    )

    entry = cache_station_zip_from_catalog(settings, station_id="USM00072558")

    assert entry.station_id == "USM00072558"
    assert entry.cached_status == "cached_extracted"
    updated_catalog = read_igra_recent_catalog(settings)
    assert updated_catalog is not None
    cached_reference = next(
        reference
        for reference in updated_catalog.zip_references
        if reference.station_id == "USM00072558"
    )
    assert cached_reference.cached_status == "cached_extracted"
    assert cached_reference.cached_text_path == entry.cached_text_path


def test_cache_station_zip_rejects_unsafe_station_id_and_filename(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    bad_station = IGRAStationZipReference(
        station_id="BAD/ID",
        filename="BAD00000000-data-beg2025.txt.zip",
        begin_year=2025,
        source_url="https://example.test/BAD00000000-data-beg2025.txt.zip",
    )
    with pytest.raises(IGRACatalogError, match="station id"):
        cache_station_zip(settings, bad_station, zip_bytes=station_zip())

    bad_filename = IGRAStationZipReference(
        station_id="USM00072558",
        filename="../USM00072558-data-beg2025.txt.zip",
        begin_year=2025,
        source_url="https://example.test/USM00072558-data-beg2025.txt.zip",
    )
    with pytest.raises(IGRACatalogError, match="filename"):
        cache_station_zip(settings, bad_filename, zip_bytes=station_zip())


def test_cache_manifest_default_is_runtime_local(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)

    manifest = read_igra_cache_manifest(settings)

    assert isinstance(manifest, IGRACacheManifest)
    assert manifest.cache_root == str(settings.cache_dir / "igra" / "recent")
    assert manifest.entries == []
