"""NOAA/NCEI IGRA recent station-period catalog and cache helpers."""

from __future__ import annotations

import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.settings import CloudChamberSettings

IGRA_RECENT_CATALOG_VERSION = 1
IGRA_CACHE_MANIFEST_VERSION = 1
IGRA_RECENT_DATA_URL = (
    "https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/access/data-y2d/"
)
IGRA_STATION_LIST_URL = "https://www.ncei.noaa.gov/pub/data/igra/igra2-station-list.txt"

CATALOG_FILENAME = "catalog.json"
CACHE_MANIFEST_FILENAME = "cache_manifest.json"

STATION_ID_PATTERN = re.compile(r"^[A-Z0-9]{11}$")
RECENT_ZIP_FILENAME_PATTERN = re.compile(r"^([A-Z0-9]{11})-data-beg(\d{4})\.txt\.zip$")
MAX_DIRECTORY_LISTING_BYTES = 5_000_000
MAX_STATION_METADATA_BYTES = 20_000_000
MAX_STATION_ZIP_BYTES = 250_000_000

RegionTag = Literal["great_plains_midwest"]
CachedStatus = Literal["not_cached", "cached_zip", "cached_extracted"]


class IGRACatalogError(RuntimeError):
    """Raised when IGRA catalog/cache data cannot be parsed or managed safely."""


class IGRARegionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag: RegionTag
    label: str
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float
    caveats: list[str] = Field(default_factory=list)

    def contains(self, station: IGRAStationMetadata) -> bool:
        if station.latitude is None or station.longitude is None:
            return False
        return (
            self.min_latitude <= station.latitude <= self.max_latitude
            and self.min_longitude <= station.longitude <= self.max_longitude
        )


class IGRAStationMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str
    station_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    elevation_m_msl: float | None = None
    state: str | None = None
    first_year: int | None = None
    last_year: int | None = None
    record_count: int | None = None
    region_tags: list[RegionTag] = Field(default_factory=list)
    source: str = IGRA_STATION_LIST_URL
    caveats: list[str] = Field(default_factory=list)


class IGRAStationZipReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str
    station_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    elevation_m_msl: float | None = None
    filename: str
    begin_year: int
    source_url: str
    last_modified: str | None = None
    compressed_size_bytes: int | None = None
    region_tags: list[RegionTag] = Field(default_factory=list)
    cached_status: CachedStatus = "not_cached"
    cached_zip_path: str | None = None
    cached_text_path: str | None = None
    source_etag_or_last_modified: str | None = None
    caveats: list[str] = Field(default_factory=list)


class IGRACacheEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str
    station_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    elevation_m_msl: float | None = None
    filename: str
    source_url: str
    region_tags: list[RegionTag] = Field(default_factory=list)
    cached_status: CachedStatus
    cached_zip_path: str
    cached_text_path: str | None = None
    downloaded_at: datetime
    extracted_at: datetime | None = None
    source_etag_or_last_modified: str | None = None
    caveats: list[str] = Field(default_factory=list)


class IGRACacheManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_version: int = IGRA_CACHE_MANIFEST_VERSION
    cache_root: str
    entries: list[IGRACacheEntry] = Field(default_factory=list)
    updated_at: datetime
    caveats: list[str] = Field(default_factory=list)


class IGRARecentCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalog_version: int = IGRA_RECENT_CATALOG_VERSION
    source_url: str
    station_metadata_source: str
    region: IGRARegionDefinition
    refreshed_at: datetime
    stations: list[IGRAStationMetadata]
    zip_references: list[IGRAStationZipReference]
    cache_manifest_path: str
    caveats: list[str] = Field(default_factory=list)


GREAT_PLAINS_MIDWEST_REGION = IGRARegionDefinition(
    tag="great_plains_midwest",
    label="Great Plains / Midwest",
    min_latitude=30.0,
    max_latitude=50.0,
    min_longitude=-106.0,
    max_longitude=-80.0,
    caveats=[
        "Broad v1 lat/lon bounding box; not a GIS boundary.",
        "Bounds are intentionally conservative for recent IGRA sounding discovery.",
    ],
)


class _HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href" and value:
                self.hrefs.append(value)


def igra_recent_cache_root(settings: CloudChamberSettings) -> Path:
    """Return the runtime-local IGRA recent cache root."""
    return settings.cache_dir.expanduser() / "igra" / "recent"


def igra_recent_catalog_path(settings: CloudChamberSettings) -> Path:
    return igra_recent_cache_root(settings) / CATALOG_FILENAME


def igra_cache_manifest_path(settings: CloudChamberSettings) -> Path:
    return igra_recent_cache_root(settings) / CACHE_MANIFEST_FILENAME


def parse_recent_directory_listing(
    html: str,
    *,
    base_url: str = IGRA_RECENT_DATA_URL,
) -> list[IGRAStationZipReference]:
    """Parse the IGRA recent directory listing for station-period ZIP links."""
    parser = _HrefParser()
    parser.feed(html)
    references: list[IGRAStationZipReference] = []
    seen: set[str] = set()
    for href in parser.hrefs:
        filename = Path(urllib.parse.urlparse(href).path).name
        match = RECENT_ZIP_FILENAME_PATTERN.match(filename)
        if match is None or filename in seen:
            continue
        seen.add(filename)
        station_id = match.group(1)
        references.append(
            IGRAStationZipReference(
                station_id=station_id,
                filename=filename,
                begin_year=int(match.group(2)),
                source_url=urllib.parse.urljoin(base_url, href),
            )
        )
    return sorted(references, key=lambda reference: (reference.station_id, reference.filename))


def parse_station_metadata(
    text: str, *, source: str = IGRA_STATION_LIST_URL
) -> dict[str, IGRAStationMetadata]:
    """Parse IGRA station-list fixed-width metadata."""
    stations: dict[str, IGRAStationMetadata] = {}
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        if not line or line.startswith("ID") or line.startswith("-"):
            continue
        station_id = line[0:11].strip() if len(line) >= 11 else ""
        if not STATION_ID_PATTERN.match(station_id):
            continue
        station = IGRAStationMetadata(
            station_id=station_id,
            latitude=_parse_optional_float(line[12:20] if len(line) >= 20 else ""),
            longitude=_parse_optional_float(line[21:30] if len(line) >= 30 else ""),
            elevation_m_msl=_parse_optional_float(line[31:37] if len(line) >= 37 else ""),
            state=_parse_optional_text(line[38:40] if len(line) >= 40 else ""),
            station_name=_parse_optional_text(line[41:71] if len(line) >= 71 else ""),
            first_year=_parse_optional_int(line[72:76] if len(line) >= 76 else ""),
            last_year=_parse_optional_int(line[77:81] if len(line) >= 81 else ""),
            record_count=_parse_optional_int(line[82:88] if len(line) >= 88 else ""),
            source=source,
        )
        stations[station_id] = station.model_copy(
            update={"region_tags": _region_tags_for_station(station)}
        )
    return stations


def build_recent_catalog(
    *,
    directory_html: str,
    station_metadata_text: str,
    cache_manifest: IGRACacheManifest | None = None,
    source_url: str = IGRA_RECENT_DATA_URL,
    station_metadata_source: str = IGRA_STATION_LIST_URL,
    region: IGRARegionDefinition = GREAT_PLAINS_MIDWEST_REGION,
    refreshed_at: datetime | None = None,
) -> IGRARecentCatalog:
    """Build a Great Plains / Midwest recent IGRA catalog from source text."""
    station_by_id = parse_station_metadata(station_metadata_text, source=station_metadata_source)
    cache_by_filename = {
        entry.filename: entry for entry in (cache_manifest.entries if cache_manifest else [])
    }
    caveats: list[str] = []
    stations_in_region = [
        station for station in station_by_id.values() if region.tag in station.region_tags
    ]
    references: list[IGRAStationZipReference] = []
    for reference in parse_recent_directory_listing(directory_html, base_url=source_url):
        station = station_by_id.get(reference.station_id)
        if station is None:
            caveats.append(f"station_metadata_missing:{reference.station_id}")
            continue
        if region.tag not in station.region_tags:
            continue
        cache_entry = cache_by_filename.get(reference.filename)
        references.append(
            reference.model_copy(
                update={
                    "station_name": station.station_name,
                    "latitude": station.latitude,
                    "longitude": station.longitude,
                    "elevation_m_msl": station.elevation_m_msl,
                    "region_tags": station.region_tags,
                    "cached_status": cache_entry.cached_status if cache_entry else "not_cached",
                    "cached_zip_path": cache_entry.cached_zip_path if cache_entry else None,
                    "cached_text_path": cache_entry.cached_text_path if cache_entry else None,
                    "source_etag_or_last_modified": (
                        cache_entry.source_etag_or_last_modified if cache_entry else None
                    ),
                }
            )
        )
    return IGRARecentCatalog(
        source_url=source_url,
        station_metadata_source=station_metadata_source,
        region=region,
        refreshed_at=refreshed_at or datetime.now(UTC),
        stations=sorted(stations_in_region, key=lambda station: station.station_id),
        zip_references=references,
        cache_manifest_path=str(Path("cache") / "igra" / "recent" / CACHE_MANIFEST_FILENAME),
        caveats=sorted(set(caveats)),
    )


def read_igra_recent_catalog(settings: CloudChamberSettings) -> IGRARecentCatalog | None:
    path = igra_recent_catalog_path(settings)
    if not path.exists():
        return None
    return IGRARecentCatalog.model_validate(json.loads(path.read_text()))


def write_igra_recent_catalog(settings: CloudChamberSettings, catalog: IGRARecentCatalog) -> None:
    path = igra_recent_catalog_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(catalog.model_dump_json(indent=2) + "\n")


def read_igra_cache_manifest(settings: CloudChamberSettings) -> IGRACacheManifest:
    path = igra_cache_manifest_path(settings)
    if not path.exists():
        return IGRACacheManifest(
            cache_root=str(igra_recent_cache_root(settings)),
            updated_at=datetime.now(UTC),
        )
    return IGRACacheManifest.model_validate(json.loads(path.read_text()))


def write_igra_cache_manifest(settings: CloudChamberSettings, manifest: IGRACacheManifest) -> None:
    path = igra_cache_manifest_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2) + "\n")


def refresh_recent_catalog(settings: CloudChamberSettings) -> IGRARecentCatalog:
    """Fetch and persist the bounded recent IGRA catalog."""
    directory_html = _fetch_url_text(IGRA_RECENT_DATA_URL, max_bytes=MAX_DIRECTORY_LISTING_BYTES)
    station_metadata_text = _fetch_url_text(
        IGRA_STATION_LIST_URL,
        max_bytes=MAX_STATION_METADATA_BYTES,
    )
    catalog = build_recent_catalog(
        directory_html=directory_html,
        station_metadata_text=station_metadata_text,
        cache_manifest=read_igra_cache_manifest(settings),
    )
    catalog = catalog.model_copy(
        update={"cache_manifest_path": str(igra_cache_manifest_path(settings))}
    )
    write_igra_recent_catalog(settings, catalog)
    return catalog


def cache_station_zip(
    settings: CloudChamberSettings,
    reference: IGRAStationZipReference,
    *,
    zip_bytes: bytes | None = None,
) -> IGRACacheEntry:
    """Cache and safely extract a selected IGRA station-period ZIP."""
    _validate_station_id(reference.station_id)
    _validate_recent_zip_filename(reference.filename, expected_station_id=reference.station_id)
    payload = zip_bytes
    if payload is None:
        payload = _fetch_url_bytes(reference.source_url, max_bytes=MAX_STATION_ZIP_BYTES)
    station_dir = _station_cache_dir(settings, reference.station_id)
    station_dir.mkdir(parents=True, exist_ok=True)
    zip_path = station_dir / reference.filename
    zip_path.write_bytes(payload)
    extracted_text_path, caveats = _safe_extract_station_zip(
        zip_bytes=payload,
        target_dir=station_dir,
        expected_station_id=reference.station_id,
    )
    now = datetime.now(UTC)
    entry = IGRACacheEntry(
        station_id=reference.station_id,
        station_name=reference.station_name,
        latitude=reference.latitude,
        longitude=reference.longitude,
        elevation_m_msl=reference.elevation_m_msl,
        filename=reference.filename,
        source_url=reference.source_url,
        region_tags=reference.region_tags,
        cached_status="cached_extracted" if extracted_text_path else "cached_zip",
        cached_zip_path=str(zip_path),
        cached_text_path=str(extracted_text_path) if extracted_text_path else None,
        downloaded_at=now,
        extracted_at=now if extracted_text_path else None,
        source_etag_or_last_modified=reference.source_etag_or_last_modified,
        caveats=caveats,
    )
    manifest = read_igra_cache_manifest(settings)
    updated_entries = [
        existing for existing in manifest.entries if existing.filename != entry.filename
    ]
    updated_entries.append(entry)
    write_igra_cache_manifest(
        settings,
        manifest.model_copy(
            update={
                "cache_root": str(igra_recent_cache_root(settings)),
                "entries": sorted(
                    updated_entries, key=lambda item: (item.station_id, item.filename)
                ),
                "updated_at": now,
            }
        ),
    )
    return entry


def cache_station_zip_from_catalog(
    settings: CloudChamberSettings,
    *,
    station_id: str,
    filename: str | None = None,
) -> IGRACacheEntry:
    catalog = read_igra_recent_catalog(settings)
    if catalog is None:
        raise IGRACatalogError("Refresh IGRA recent catalog before caching station files.")
    matches = [
        reference
        for reference in catalog.zip_references
        if reference.station_id == station_id
        and (filename is None or reference.filename == filename)
    ]
    if not matches:
        raise IGRACatalogError("Requested IGRA station-period file is not in the recent catalog.")
    return cache_station_zip(settings, matches[0])


def _region_tags_for_station(station: IGRAStationMetadata) -> list[RegionTag]:
    return ["great_plains_midwest"] if GREAT_PLAINS_MIDWEST_REGION.contains(station) else []


def _safe_extract_station_zip(
    *,
    zip_bytes: bytes,
    target_dir: Path,
    expected_station_id: str,
) -> tuple[Path | None, list[str]]:
    caveats: list[str] = []
    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise IGRACatalogError("IGRA station ZIP is not a readable ZIP archive.") from exc
    safe_text_members: list[zipfile.ZipInfo] = []
    target_root = target_dir.resolve()
    with archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise IGRACatalogError(f"Unsafe path in IGRA ZIP entry: {member.filename}")
            output_path = (target_dir / member_path.name).resolve()
            if not output_path.is_relative_to(target_root):
                raise IGRACatalogError(
                    f"Unsafe extraction target for IGRA ZIP entry: {member.filename}"
                )
            if output_path.suffix != ".txt":
                caveats.append(f"unexpected_zip_member_ignored:{member.filename}")
                continue
            if not member_path.name.startswith(expected_station_id):
                caveats.append(f"unexpected_station_text_filename:{member_path.name}")
            safe_text_members.append(member)
        if not safe_text_members:
            raise IGRACatalogError("IGRA station ZIP did not contain a station text file.")
        if len(safe_text_members) > 1:
            caveats.append(f"multiple_station_text_files:{len(safe_text_members)}")
        selected = sorted(safe_text_members, key=lambda item: item.filename)[0]
        output_path = (target_dir / Path(selected.filename).name).resolve()
        output_path.write_bytes(archive.read(selected))
        return output_path, caveats


def _station_cache_dir(settings: CloudChamberSettings, station_id: str) -> Path:
    _validate_station_id(station_id)
    return igra_recent_cache_root(settings) / "stations" / station_id


def _validate_station_id(station_id: str) -> None:
    if not STATION_ID_PATTERN.match(station_id):
        raise IGRACatalogError(f"Unsafe or unsupported IGRA station id: {station_id!r}")


def _validate_recent_zip_filename(filename: str, *, expected_station_id: str) -> None:
    basename = Path(filename).name
    if basename != filename:
        raise IGRACatalogError("IGRA ZIP filename must not include a directory path.")
    match = RECENT_ZIP_FILENAME_PATTERN.match(filename)
    if match is None:
        raise IGRACatalogError(f"Unsupported IGRA recent ZIP filename: {filename!r}")
    if match.group(1) != expected_station_id:
        raise IGRACatalogError("IGRA ZIP filename station id does not match requested station.")


def _fetch_url_text(url: str, *, max_bytes: int) -> str:
    return _fetch_url_bytes(url, max_bytes=max_bytes).decode("utf-8", errors="replace")


def _fetch_url_bytes(url: str, *, max_bytes: int) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            payload = cast(bytes, response.read(max_bytes + 1))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise IGRACatalogError(f"Unable to fetch IGRA source URL: {url}") from exc
    if len(payload) > max_bytes:
        raise IGRACatalogError(f"IGRA source URL exceeded maximum size: {url}")
    return payload


def _parse_optional_text(text: str) -> str | None:
    stripped = text.strip()
    return stripped or None


def _parse_optional_float(text: str) -> float | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        value = float(stripped)
    except ValueError:
        return None
    if value in {-98_888.0, -99_999.0, -999.9, -998.8}:
        return None
    return value


def _parse_optional_int(text: str) -> int | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        value = int(stripped)
    except ValueError:
        return None
    if value in {-8888, -9999}:
        return None
    return value
