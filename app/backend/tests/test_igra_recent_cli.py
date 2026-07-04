from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.igra_catalog import (
    GREAT_PLAINS_MIDWEST_REGION,
    IGRACacheEntry,
    IGRACacheManifest,
    IGRARecentCatalog,
    IGRAStationMetadata,
    IGRAStationZipReference,
)
from cloud_chamber.igra_recent_cli import main
from cloud_chamber.settings import CloudChamberSettings


def catalog() -> IGRARecentCatalog:
    return IGRARecentCatalog(
        source_url="https://example.test/igra/",
        station_metadata_source="https://example.test/stations.txt",
        region=GREAT_PLAINS_MIDWEST_REGION,
        refreshed_at=datetime(2026, 7, 1, tzinfo=UTC),
        stations=[
            IGRAStationMetadata(
                station_id="USM00072558",
                station_name="VALLEY",
                latitude=41.32,
                longitude=-96.3669,
                elevation_m_msl=351.5,
                region_tags=["great_plains_midwest"],
            )
        ],
        zip_references=[
            IGRAStationZipReference(
                station_id="USM00072558",
                station_name="VALLEY",
                latitude=41.32,
                longitude=-96.3669,
                elevation_m_msl=351.5,
                filename="USM00072558-data-beg2025.txt.zip",
                begin_year=2025,
                source_url="https://example.test/USM00072558-data-beg2025.txt.zip",
                region_tags=["great_plains_midwest"],
                cached_status="not_cached",
            )
        ],
        cache_manifest_path="/tmp/cache/igra/recent/cache_manifest.json",
    )


def cache_manifest() -> IGRACacheManifest:
    return IGRACacheManifest(
        cache_root="/tmp/CloudChamber/cache/igra/recent",
        entries=[],
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )


def cache_entry(tmp_path: Path) -> IGRACacheEntry:
    return IGRACacheEntry(
        station_id="USM00072558",
        station_name="VALLEY",
        latitude=41.32,
        longitude=-96.3669,
        elevation_m_msl=351.5,
        filename="USM00072558-data-beg2025.txt.zip",
        source_url="https://example.test/USM00072558-data-beg2025.txt.zip",
        region_tags=["great_plains_midwest"],
        cached_status="cached_extracted",
        cached_zip_path=str(tmp_path / "USM00072558-data-beg2025.txt.zip"),
        cached_text_path=str(tmp_path / "USM00072558-data-beg2025.txt"),
        downloaded_at=datetime(2026, 7, 1, tzinfo=UTC),
        extracted_at=datetime(2026, 7, 1, tzinfo=UTC),
    )


def test_cleanup_deletes_runtime_recent_cache(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    settings = CloudChamberSettings(
        runtime_home=tmp_path / "CloudChamber",
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "CloudChamber" / "cache",
        log_dir=tmp_path / "CloudChamber" / "logs",
    )
    recent_cache = settings.cache_dir / "igra" / "recent"
    recent_cache.mkdir(parents=True)
    (recent_cache / "catalog.json").write_text("{}")
    monkeypatch.setattr("cloud_chamber.igra_recent_cli.load_settings", lambda: settings)

    assert main(["cleanup"]) == 0

    output = capsys.readouterr().out
    assert "Deleted IGRA recent cache" in output
    assert not recent_cache.exists()


def test_cleanup_is_idempotent_when_cache_is_absent(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    settings = CloudChamberSettings(
        runtime_home=tmp_path / "CloudChamber",
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "CloudChamber" / "cache",
        log_dir=tmp_path / "CloudChamber" / "logs",
    )
    monkeypatch.setattr("cloud_chamber.igra_recent_cli.load_settings", lambda: settings)

    assert main(["cleanup"]) == 0

    output = capsys.readouterr().out
    assert "already clean" in output


def test_cleanup_refuses_unexpected_cache_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    settings = CloudChamberSettings(
        runtime_home=tmp_path / "CloudChamber",
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "CloudChamber" / "cache",
        log_dir=tmp_path / "CloudChamber" / "logs",
    )
    monkeypatch.setattr("cloud_chamber.igra_recent_cli.load_settings", lambda: settings)
    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.igra_recent_catalog_path",
        lambda _settings: settings.cache_dir / "catalog.json",
    )

    assert main(["cleanup"]) == 2

    output = capsys.readouterr().out
    assert "Refusing to clean IGRA cache" in output


def test_status_points_to_refresh_when_catalog_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("cloud_chamber.igra_recent_cli.read_igra_recent_catalog", lambda _s: None)
    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.read_igra_cache_manifest",
        lambda _s: cache_manifest(),
    )

    assert main(["status"]) == 0

    output = capsys.readouterr().out
    assert "IGRA recent catalog: not refreshed yet" in output
    assert "Run: scripts/igra-recent.sh refresh" in output
    assert "Cached entries: 0" in output


def test_list_prints_station_period_files(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.read_igra_recent_catalog", lambda _s: catalog()
    )

    assert main(["list"]) == 0

    output = capsys.readouterr().out
    assert "Station ID" in output
    assert "USM00072558" in output
    assert "USM00072558-data-beg2025.txt.zip" in output


def test_cache_prints_local_paths(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    entry = cache_entry(tmp_path)
    calls: list[tuple[str, str | None]] = []

    def fake_cache(
        _settings: object,
        *,
        station_id: str,
        filename: str | None,
    ) -> IGRACacheEntry:
        calls.append((station_id, filename))
        return entry

    monkeypatch.setattr("cloud_chamber.igra_recent_cli.cache_station_zip_from_catalog", fake_cache)

    assert main(["cache", "USM00072558"]) == 0

    output = capsys.readouterr().out
    assert calls == [("USM00072558", None)]
    assert "Cached IGRA station-period file" in output
    assert str(tmp_path / "USM00072558-data-beg2025.txt") in output


def test_cache_all_downloads_multiple_uncached_references(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    second_reference = IGRAStationZipReference(
        station_id="USM00072558",
        station_name="VALLEY",
        latitude=41.32,
        longitude=-96.3669,
        elevation_m_msl=351.5,
        filename="USM00072558-data-beg2026.txt.zip",
        begin_year=2026,
        source_url="https://example.test/USM00072558-data-beg2026.txt.zip",
        region_tags=["great_plains_midwest"],
        cached_status="not_cached",
    )
    test_catalog = catalog().model_copy(
        update={"zip_references": [*catalog().zip_references, second_reference]}
    )
    entries = [
        cache_entry(tmp_path).model_copy(update={"filename": "USM00072558-data-beg2025.txt.zip"}),
        cache_entry(tmp_path).model_copy(update={"filename": "USM00072558-data-beg2026.txt.zip"}),
    ]
    calls: list[str] = []
    written_catalogs: list[IGRARecentCatalog] = []

    def fake_cache(_settings: object, reference: IGRAStationZipReference) -> IGRACacheEntry:
        calls.append(reference.filename)
        return entries[len(calls) - 1]

    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.read_igra_recent_catalog", lambda _s: test_catalog
    )
    monkeypatch.setattr("cloud_chamber.igra_recent_cli.cache_station_zip", fake_cache)
    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.write_igra_recent_catalog",
        lambda _s, item: written_catalogs.append(item),
    )

    assert main(["cache-all", "--limit", "2"]) == 0

    output = capsys.readouterr().out
    assert calls == ["USM00072558-data-beg2025.txt.zip", "USM00072558-data-beg2026.txt.zip"]
    assert "Caching 2 IGRA station-period file(s)" in output
    assert "scripts/igra-recent.sh soundings" in output
    assert len(written_catalogs) == 1
    assert all(
        reference.cached_status == "cached_extracted"
        for reference in written_catalogs[0].zip_references
    )


def test_soundings_lists_cached_sounding_times(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    text_path = tmp_path / "USM00072558-data-beg2025.txt"
    text_path.write_text(IGRA_FIXTURE)
    entry = cache_entry(tmp_path).model_copy(update={"cached_text_path": str(text_path)})
    manifest = cache_manifest().model_copy(update={"entries": [entry]})
    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.read_igra_cache_manifest",
        lambda _s: manifest,
    )

    assert main(["soundings", "--limit", "5"]) == 0

    output = capsys.readouterr().out
    assert "Station ID" in output
    assert "Valid time UTC" in output
    assert "USM00072558" in output
    assert "2025-01-01T00:00:00Z" in output


def test_soundings_defaults_to_latest_per_station(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    text_path = tmp_path / "USM00072558-data-beg2025.txt"
    text_path.write_text(IGRA_FIXTURE)
    entry = cache_entry(tmp_path).model_copy(update={"cached_text_path": str(text_path)})
    manifest = cache_manifest().model_copy(update={"entries": [entry]})
    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.read_igra_cache_manifest",
        lambda _s: manifest,
    )

    assert main(["soundings", "--latest-per-station", "1"]) == 0

    output = capsys.readouterr().out
    assert "2025-01-02T00:00:00Z" in output
    assert "2025-01-01T00:00:00Z" not in output
    assert "Use --all to list every time" in output


def test_soundings_all_lists_every_cached_time(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    text_path = tmp_path / "USM00072558-data-beg2025.txt"
    text_path.write_text(IGRA_FIXTURE)
    entry = cache_entry(tmp_path).model_copy(update={"cached_text_path": str(text_path)})
    manifest = cache_manifest().model_copy(update={"entries": [entry]})
    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.read_igra_cache_manifest",
        lambda _s: manifest,
    )

    assert main(["soundings", "--latest-per-station", "1", "--all"]) == 0

    output = capsys.readouterr().out
    assert "2025-01-02T00:00:00Z" in output
    assert "2025-01-01T00:00:00Z" in output
    assert "Use --all to list every time" not in output


def test_soundings_lists_multiple_cached_stations(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    valley_path = tmp_path / "USM00072558-data-beg2025.txt"
    norman_path = tmp_path / "USM00072357-data-beg2025.txt"
    valley_path.write_text(IGRA_FIXTURE)
    norman_path.write_text(IGRA_FIXTURE.replace("USM00072558", "USM00072357"))
    valley = cache_entry(tmp_path).model_copy(update={"cached_text_path": str(valley_path)})
    norman = cache_entry(tmp_path).model_copy(
        update={
            "station_id": "USM00072357",
            "station_name": "NORMAN/MAX WESTHEIMER A; OK.",
            "filename": "USM00072357-data-beg2025.txt.zip",
            "cached_zip_path": str(tmp_path / "USM00072357-data-beg2025.txt.zip"),
            "cached_text_path": str(norman_path),
        }
    )
    manifest = cache_manifest().model_copy(update={"entries": [valley, norman]})
    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.read_igra_cache_manifest",
        lambda _s: manifest,
    )

    assert main(["soundings", "--limit", "10"]) == 0

    output = capsys.readouterr().out
    assert "USM00072558" in output
    assert "USM00072357" in output
    assert "NORMAN/MAX WESTHEIMER A; OK." in output


def test_candidates_screens_cached_sounding_times(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    text_path = tmp_path / "USM00072558-data-beg2025.txt"
    text_path.write_text(IGRA_FIXTURE)
    entry = cache_entry(tmp_path).model_copy(update={"cached_text_path": str(text_path)})
    manifest = cache_manifest().model_copy(update={"entries": [entry]})
    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.read_igra_cache_manifest",
        lambda _s: manifest,
    )
    monkeypatch.setattr(
        "cloud_chamber.sounding_candidates.read_igra_cache_manifest",
        lambda _s: manifest,
    )

    assert (
        main(
            [
                "candidates",
                "--story",
                "shallow-cumulus",
                "--limit",
                "2",
                "--latest-per-station",
                "2",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Match" in output
    assert "Evidence" in output
    assert "shallow-cumulus" in output
    assert "USM00072558" in output
    assert "candidate_id:" in output
    assert "package_ready" in output


def test_candidates_all_prints_story_specific_sections(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    text_path = tmp_path / "USM00072558-data-beg2025.txt"
    text_path.write_text(IGRA_FIXTURE)
    entry = cache_entry(tmp_path).model_copy(update={"cached_text_path": str(text_path)})
    manifest = cache_manifest().model_copy(update={"entries": [entry]})
    monkeypatch.setattr(
        "cloud_chamber.sounding_candidates.read_igra_cache_manifest",
        lambda _s: manifest,
    )

    assert main(["candidates", "--limit", "1", "--latest-per-station", "1"]) == 0

    output = capsys.readouterr().out
    assert "Cloud-forming shallow cumulus candidate" in output
    assert "Dry failed cumulus candidate" in output
    assert "Capped / suppressed cumulus candidate" in output
    assert "Humid / rainy candidate" in output
    assert "Severe thunderstorm environment" in output
    assert "Supercell-like environment" in output
    assert "High-CAPE pulse-storm candidate" in output


def test_refresh_prints_next_commands(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "cloud_chamber.igra_recent_cli.refresh_recent_catalog", lambda _s: catalog()
    )

    assert main(["refresh"]) == 0

    output = capsys.readouterr().out
    assert "IGRA recent catalog" in output
    assert "scripts/igra-recent.sh list" in output
    assert "scripts/igra-recent.sh cache-all --limit 10" in output
    assert "scripts/igra-recent.sh soundings" in output
    assert "scripts/igra-recent.sh candidates" in output
