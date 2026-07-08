"""Small command-line surface for the runtime-local IGRA recent cache."""

from __future__ import annotations

import argparse
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from cloud_chamber.igra_catalog import (
    IGRACacheEntry,
    IGRACacheManifest,
    IGRACatalogError,
    IGRARecentCatalog,
    IGRAStationZipReference,
    cache_station_zip,
    cache_station_zip_from_catalog,
    igra_cache_manifest_path,
    igra_recent_catalog_path,
    read_igra_cache_manifest,
    read_igra_recent_catalog,
    refresh_recent_catalog,
    write_igra_recent_catalog,
)
from cloud_chamber.observed_sounding import ObservedSoundingError, summarize_igra_station_text
from cloud_chamber.settings import CloudChamberSettings, load_settings
from cloud_chamber.sounding_candidates import (
    DEEP_CONVECTION_STORY_IDS,
    STORY_LABELS,
    SoundingCandidate,
    StoryId,
    TargetStoryId,
    screen_cached_soundings,
)

STORY_OPTION_TO_ID: dict[str, TargetStoryId] = {
    "deep-convection": "deep_convection_trial",
    "shallow-cumulus": "shallow_cumulus_candidate",
    "dry-failed": "dry_failed_candidate",
    "capped-suppressed": "capped_suppressed_candidate",
    "humid-rainy": "humid_rainy_candidate",
    "severe-thunderstorm": "severe_thunderstorm_environment",
    "supercell": "supercell_environment",
    "high-cape-pulse": "high_cape_pulse_storm",
    "dry-microburst": "dry_microburst_inverted_v",
    "squall-line": "squall_line_cold_pool_candidate",
    "elevated-convection": "elevated_convection",
    "needs-review": "needs_review",
    "poor-or-incomplete": "poor_or_incomplete_candidate",
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    settings = load_settings()
    try:
        return int(args.func(args, settings))
    except IGRACatalogError as exc:
        print(f"IGRA recent cache error: {exc}")
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scripts/igra-recent.sh",
        description="Manage Cloud Chamber's runtime-local NOAA/NCEI IGRA recent cache.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    refresh = subparsers.add_parser(
        "refresh",
        help="Fetch the recent IGRA catalog and station metadata, then cache catalog metadata.",
    )
    refresh.set_defaults(func=_cmd_refresh)

    cleanup = subparsers.add_parser(
        "cleanup",
        help="Delete the runtime-local recent IGRA cache so discovery can start clean.",
    )
    cleanup.set_defaults(func=_cmd_cleanup)

    status = subparsers.add_parser(
        "status",
        help="Show the current local IGRA recent catalog/cache status.",
    )
    status.set_defaults(func=_cmd_status)

    list_parser = subparsers.add_parser(
        "list",
        help="List Great Plains / Midwest station-period files from the cached catalog.",
    )
    list_parser.add_argument("--cached", action="store_true", help="Show only cached files.")
    list_parser.add_argument("--station", help="Show only one station id.")
    list_parser.add_argument("--limit", type=int, default=25, help="Maximum rows to print.")
    list_parser.set_defaults(func=_cmd_list)

    cache = subparsers.add_parser(
        "cache",
        help="Download/cache one selected station-period file from the cached catalog.",
    )
    cache.add_argument("station_id", help="IGRA station id, for example USM00072558.")
    cache.add_argument(
        "filename",
        nargs="?",
        help="Optional exact station-period ZIP filename. Usually not needed.",
    )
    cache.set_defaults(func=_cmd_cache)

    cache_all = subparsers.add_parser(
        "cache-all",
        help="Download/cache many uncached station-period files from the cached catalog.",
    )
    cache_all.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum uncached station-period files to download. Default: 10.",
    )
    cache_all.add_argument(
        "--station",
        help="Optionally restrict batch caching to one station id.",
    )
    cache_all.set_defaults(func=_cmd_cache_all)

    soundings = subparsers.add_parser(
        "soundings",
        help="List available sounding times from locally cached station text files.",
    )
    soundings.add_argument("--station", help="Show only one station id.")
    soundings.add_argument("--limit", type=int, default=50, help="Maximum rows to print.")
    soundings.add_argument(
        "--latest-per-station",
        type=int,
        default=5,
        help="Show only the latest N sounding times per station. Default: 5.",
    )
    soundings.add_argument(
        "--all",
        action="store_true",
        help="Show all cached sounding times instead of the latest N per station.",
    )
    soundings.set_defaults(func=_cmd_soundings)

    candidates = subparsers.add_parser(
        "candidates",
        help="Screen cached sounding times into story-specific pre-run LES candidates.",
    )
    candidates.add_argument("--station", help="Screen only one station id.")
    candidates.add_argument(
        "--story",
        choices=["all", *STORY_OPTION_TO_ID.keys()],
        default="all",
        help=(
            "Candidate story to search for. Use all to show separate short lists "
            "for each story. Default: all."
        ),
    )
    candidates.add_argument(
        "--limit",
        type=int,
        default=5,
        help=(
            "Maximum candidates to print for the selected story. With --story all, "
            "this applies per story. Default: 5."
        ),
    )
    candidates.add_argument(
        "--latest-per-station",
        type=int,
        default=5,
        help="Screen only the latest N sounding times per station. Default: 5.",
    )
    candidates.set_defaults(func=_cmd_candidates)

    return parser


def _cmd_refresh(_args: argparse.Namespace, settings: CloudChamberSettings) -> int:
    catalog = refresh_recent_catalog(settings)
    _print_catalog_summary(catalog, settings)
    print("")
    print("Next:")
    print("  scripts/igra-recent.sh list --limit 20")
    print("  scripts/igra-recent.sh cache-all --limit 10")
    print("  scripts/igra-recent.sh soundings")
    print("  scripts/igra-recent.sh candidates")
    return 0


def _cmd_cleanup(_args: argparse.Namespace, settings: CloudChamberSettings) -> int:
    cache_root = igra_recent_catalog_path(settings).parent.expanduser()
    expected_root = (settings.cache_dir.expanduser() / "igra" / "recent").resolve()
    resolved = cache_root.resolve()
    if resolved != expected_root:
        raise IGRACatalogError(
            "Refusing to clean IGRA cache because the resolved path did not match "
            f"the expected runtime cache path: {resolved}"
        )
    if resolved in {
        settings.runtime_home.expanduser().resolve(),
        settings.cache_dir.expanduser().resolve(),
        Path.home().resolve(),
        Path("/").resolve(),
    }:
        raise IGRACatalogError(f"Refusing to clean unsafe IGRA cache path: {resolved}")
    if not resolved.exists():
        print("IGRA recent cache is already clean")
        print(f"  Cache root: {resolved}")
        return 0
    if not resolved.is_dir():
        raise IGRACatalogError(f"Refusing to clean non-directory IGRA cache path: {resolved}")
    shutil.rmtree(resolved)
    print("Deleted IGRA recent cache")
    print(f"  Cache root: {resolved}")
    print("")
    print("Next:")
    print("  scripts/igra-recent.sh status")
    print("  scripts/igra-recent.sh refresh")
    return 0


def _cmd_status(_args: argparse.Namespace, settings: CloudChamberSettings) -> int:
    catalog = read_igra_recent_catalog(settings)
    manifest = read_igra_cache_manifest(settings)
    if catalog is None:
        print("IGRA recent catalog: not refreshed yet")
        print(f"Expected catalog path: {igra_recent_catalog_path(settings)}")
        print("")
        print("Run: scripts/igra-recent.sh refresh")
    else:
        _print_catalog_summary(catalog, settings)
    print("")
    _print_cache_summary(manifest, settings)
    return 0


def _cmd_list(args: argparse.Namespace, settings: CloudChamberSettings) -> int:
    catalog = read_igra_recent_catalog(settings)
    if catalog is None:
        raise IGRACatalogError("No local catalog yet. Run: scripts/igra-recent.sh refresh")
    references = catalog.zip_references
    if args.cached:
        references = [
            reference for reference in references if reference.cached_status != "not_cached"
        ]
    if args.station:
        references = [reference for reference in references if reference.station_id == args.station]
    if args.limit < 1:
        raise IGRACatalogError("--limit must be at least 1.")
    _print_references(references[: args.limit])
    if len(references) > args.limit:
        print(
            f"... {len(references) - args.limit} more. Use --limit {len(references)} to show all."
        )
    return 0


def _cmd_cache(args: argparse.Namespace, settings: CloudChamberSettings) -> int:
    entry = cache_station_zip_from_catalog(
        settings,
        station_id=args.station_id,
        filename=args.filename,
    )
    _print_cache_entry(entry)
    return 0


def _cmd_cache_all(args: argparse.Namespace, settings: CloudChamberSettings) -> int:
    catalog = read_igra_recent_catalog(settings)
    if catalog is None:
        raise IGRACatalogError("No local catalog yet. Run: scripts/igra-recent.sh refresh")
    if args.limit < 1:
        raise IGRACatalogError("--limit must be at least 1.")
    references = [
        reference
        for reference in catalog.zip_references
        if reference.cached_status == "not_cached"
        and (args.station is None or reference.station_id == args.station)
    ]
    selected = references[: args.limit]
    if not selected:
        print("No uncached IGRA station-period files matched.")
        return 0
    entries: list[IGRACacheEntry] = []
    updated_references = list(catalog.zip_references)
    print(f"Caching {len(selected)} IGRA station-period file(s)")
    for index, reference in enumerate(selected, start=1):
        name = reference.station_name or reference.station_id
        print(f"  [{index}/{len(selected)}] {reference.station_id} {name}")
        entry = cache_station_zip(settings, reference)
        entries.append(entry)
        updated_references = [
            _reference_with_cache_entry_for_cli(existing, entry)
            if existing.filename == entry.filename
            else existing
            for existing in updated_references
        ]
    write_igra_recent_catalog(
        settings,
        catalog.model_copy(
            update={
                "zip_references": updated_references,
                "cache_manifest_path": str(igra_cache_manifest_path(settings)),
            }
        ),
    )
    print("")
    print(f"Cached {len(entries)} station-period file(s).")
    print("Next:")
    print("  scripts/igra-recent.sh soundings")
    print("  scripts/igra-recent.sh candidates")
    return 0


def _cmd_soundings(args: argparse.Namespace, settings: CloudChamberSettings) -> int:
    manifest = read_igra_cache_manifest(settings)
    entries = [
        entry
        for entry in manifest.entries
        if entry.cached_text_path and (args.station is None or entry.station_id == args.station)
    ]
    if args.limit < 1:
        raise IGRACatalogError("--limit must be at least 1.")
    if args.latest_per_station < 1:
        raise IGRACatalogError("--latest-per-station must be at least 1.")
    if not entries:
        print("No cached IGRA station text files matched.")
        print("Run: scripts/igra-recent.sh cache-all --limit 10")
        return 0
    rows: list[tuple[str, str, str, int, str]] = []
    caveats: list[str] = []
    for entry in entries:
        assert entry.cached_text_path is not None
        path = Path(entry.cached_text_path)
        try:
            soundings = summarize_igra_station_text(path.read_text())
        except (OSError, ObservedSoundingError) as exc:
            caveats.append(f"{entry.station_id}:{path.name}:{exc}")
            continue
        for sounding in soundings:
            rows.append(
                (
                    sounding.station_id,
                    entry.station_name or "",
                    sounding.valid_time_utc.isoformat().replace("+00:00", "Z"),
                    sounding.num_levels,
                    path.name,
                )
            )
    rows.sort(key=lambda row: (row[2], row[0]), reverse=True)
    total_rows = len(rows)
    if not args.all:
        rows = _latest_rows_per_station(rows, latest_per_station=args.latest_per_station)
    _print_soundings(rows[: args.limit])
    if len(rows) > args.limit:
        print(f"... {len(rows) - args.limit} more. Use --limit {len(rows)} to show all.")
    if not args.all and total_rows > len(rows):
        print(
            f"Showing latest {args.latest_per_station} sounding(s) per station "
            f"({len(rows)} of {total_rows} cached sounding times). Use --all to list every time."
        )
    if caveats:
        print("")
        print("Caveats:")
        for caveat in caveats[:8]:
            print(f"  - {caveat}")
    return 0


def _cmd_candidates(args: argparse.Namespace, settings: CloudChamberSettings) -> int:
    if args.limit < 1:
        raise IGRACatalogError("--limit must be at least 1.")
    if args.latest_per_station < 1:
        raise IGRACatalogError("--latest-per-station must be at least 1.")
    story_option = cast(str, args.story)
    stories: list[TargetStoryId]
    if story_option == "all":
        stories = [
            "shallow_cumulus_candidate",
            "dry_failed_candidate",
            "capped_suppressed_candidate",
            "humid_rainy_candidate",
            "severe_thunderstorm_environment",
            "supercell_environment",
            "high_cape_pulse_storm",
            "dry_microburst_inverted_v",
            "squall_line_cold_pool_candidate",
            "elevated_convection",
        ]
    else:
        stories = [STORY_OPTION_TO_ID[story_option]]

    all_caveats: list[str] = []
    any_candidates = False
    for index, story in enumerate(stories):
        result = screen_cached_soundings(
            settings,
            station_id=args.station,
            latest_per_station=args.latest_per_station,
            limit=args.limit,
            target_story=story,
        )
        all_caveats.extend(result.caveats)
        if story_option == "all":
            print(STORY_LABELS[cast(StoryId, story)])
        _print_candidates(result.candidates, target_story=story)
        any_candidates = any_candidates or bool(result.candidates)
        if story_option == "all" and index < len(stories) - 1:
            print("")
    if all_caveats:
        print("")
        print("Caveats:")
        for caveat in all_caveats[:8]:
            print(f"  - {caveat}")
    if any_candidates:
        print("")
        print("Next:")
        print("  Pick the story you want to test; candidates are pre-run hypotheses.")
        print("  Review candidate_id, match score, evidence level, and package_ready.")
        print(
            "  Use the saved-candidate API or future UI to hand a candidate "
            "into package generation."
        )
    else:
        print("Run: scripts/igra-recent.sh cache-all --limit 10")
    return 0


def _latest_rows_per_station(
    rows: list[tuple[str, str, str, int, str]], *, latest_per_station: int
) -> list[tuple[str, str, str, int, str]]:
    kept: list[tuple[str, str, str, int, str]] = []
    counts_by_station: dict[str, int] = {}
    for row in rows:
        station_id = row[0]
        count = counts_by_station.get(station_id, 0)
        if count >= latest_per_station:
            continue
        kept.append(row)
        counts_by_station[station_id] = count + 1
    return kept


def _print_catalog_summary(catalog: IGRARecentCatalog, settings: CloudChamberSettings) -> None:
    cached = [
        reference for reference in catalog.zip_references if reference.cached_status != "not_cached"
    ]
    print("IGRA recent catalog")
    print(f"  Region: {catalog.region.label} ({catalog.region.tag})")
    print(
        "  Bounds: "
        f"lat {catalog.region.min_latitude:g} to {catalog.region.max_latitude:g}, "
        f"lon {catalog.region.min_longitude:g} to {catalog.region.max_longitude:g}"
    )
    print(f"  Refreshed: {catalog.refreshed_at.isoformat()}")
    print(f"  Region stations: {len(catalog.stations)}")
    print(f"  Region station-period files: {len(catalog.zip_references)}")
    print(f"  Cached station-period files: {len(cached)}")
    print(f"  Catalog path: {igra_recent_catalog_path(settings)}")
    if catalog.caveats:
        print("  Caveats:")
        for caveat in catalog.caveats[:8]:
            print(f"    - {caveat}")


def _print_cache_summary(manifest: IGRACacheManifest, settings: CloudChamberSettings) -> None:
    print("IGRA recent cache")
    print(f"  Cache root: {manifest.cache_root}")
    print(f"  Cache manifest: {igra_cache_manifest_path(settings)}")
    print(f"  Cached entries: {len(manifest.entries)}")
    if manifest.entries:
        print("  Recent cached files:")
        for entry in manifest.entries[-5:]:
            name = entry.station_name or entry.station_id
            cached_path = Path(entry.cached_text_path or entry.cached_zip_path).name
            print(f"    - {entry.station_id} {name}: {cached_path}")


def _print_references(references: list[IGRAStationZipReference]) -> None:
    if not references:
        print("No IGRA recent station-period files matched.")
        return
    print("Station ID   Status            Station                         File")
    print("-" * 92)
    for reference in references:
        name = (reference.station_name or "").strip()[:30]
        print(
            f"{reference.station_id:<11}  "
            f"{reference.cached_status:<16}  "
            f"{name:<30}  "
            f"{reference.filename}"
        )


def _print_soundings(rows: list[tuple[str, str, str, int, str]]) -> None:
    if not rows:
        print("No cached IGRA sounding times could be parsed.")
        return
    print("Station ID   Valid time UTC        Levels  Station                         File")
    print("-" * 102)
    for station_id, station_name, valid_time, levels, filename in rows:
        print(
            f"{station_id:<11}  "
            f"{valid_time:<20}  "
            f"{levels:<6}  "
            f"{station_name.strip()[:30]:<30}  "
            f"{filename}"
        )


def _print_candidates(
    candidates: list[SoundingCandidate], *, target_story: TargetStoryId | None = None
) -> None:
    if not candidates:
        print("No cached sounding candidates could be screened.")
        return
    print("Rank  Story                  Match  Evidence  Ready  Valid time UTC        Station")
    print("-" * 104)
    for index, candidate in enumerate(candidates, start=1):
        story = (
            (target_story or candidate.primary_story).replace("_candidate", "").replace("_", "-")
        )
        ready = "yes" if candidate.package_ready else "no"
        station = candidate.station_name or candidate.station_id
        match_score = _candidate_story_match(candidate, target_story)
        print(
            f"{index:<4}  "
            f"{story[:22]:<22} "
            f"{match_score:>5.1f}  "
            f"{candidate.confidence:<10}  "
            f"{ready:<5}  "
            f"{candidate.valid_time_utc.isoformat().replace('+00:00', 'Z'):<20}  "
            f"{candidate.station_id} {station[:24]}"
        )
        print(f"      candidate_id: {candidate.candidate_id}")
        top_evidence = [
            evidence
            for evidence in candidate.evidence
            if evidence.value is not None and evidence.value != ""
        ][:3]
        if top_evidence:
            summary = "; ".join(
                f"{item.label}: {item.value}{' ' + item.units if item.units else ''}"
                for item in top_evidence
            )
            print(f"      {summary}")
        if candidate.caveats:
            print(f"      caveat: {candidate.caveats[0]}")


def _candidate_story_match(
    candidate: SoundingCandidate, target_story: TargetStoryId | None
) -> float:
    if target_story is None:
        return candidate.rank_score
    if target_story == "deep_convection_trial":
        return (
            max(
                (
                    score.score_0_to_100
                    for score in candidate.story_scores
                    if score.story in DEEP_CONVECTION_STORY_IDS
                ),
                default=0.0,
            )
            if candidate.package_ready
            else 0.0
        )
    for score in candidate.story_scores:
        if score.story == target_story:
            return score.score_0_to_100 if candidate.package_ready else 0.0
    return 0.0


def _reference_with_cache_entry_for_cli(
    reference: IGRAStationZipReference,
    entry: IGRACacheEntry,
) -> IGRAStationZipReference:
    return reference.model_copy(
        update={
            "cached_status": entry.cached_status,
            "cached_zip_path": entry.cached_zip_path,
            "cached_text_path": entry.cached_text_path,
            "source_etag_or_last_modified": entry.source_etag_or_last_modified,
        }
    )


def _print_cache_entry(entry: IGRACacheEntry) -> None:
    print("Cached IGRA station-period file")
    print(f"  Station: {entry.station_id} {entry.station_name or ''}".rstrip())
    print(f"  Status: {entry.cached_status}")
    print(f"  ZIP: {entry.cached_zip_path}")
    if entry.cached_text_path:
        print(f"  Text: {entry.cached_text_path}")
    print(f"  Source: {entry.source_url}")
    print(f"  Downloaded: {entry.downloaded_at.isoformat()}")
    if entry.extracted_at:
        print(f"  Extracted: {entry.extracted_at.isoformat()}")
    if entry.caveats:
        print("  Caveats:")
        for caveat in entry.caveats:
            print(f"    - {caveat}")


if __name__ == "__main__":
    raise SystemExit(main())
