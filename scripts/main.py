"""Coordinate the complete Extract, Transform, Load pipeline.

Run ``python -m scripts.main --demo`` from the project root. The demonstration
uses in-memory sample data and never connects to the internet.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

from config import Settings, get_settings
from scripts.api_client import WnbaApiClient
from scripts.extract import extract_scoreboard, save_raw_json
from scripts.load import write_csv, write_games_csv
from scripts.transform import (
    combine_scoreboard_games,
    transform_raw_json,
    transform_scoreboard_games,
)


# This intentionally small dataset makes each pipeline result easy to inspect.
DEMO_PAYLOAD = {
    "records": [
        {"Player ID": 1, "Player Name": "Sample Guard", "Points": 18},
        {"Player ID": 2, "Player Name": "Sample Forward", "Points": 14},
    ]
}


def run_demo_pipeline(settings: Settings) -> dict[str, Path]:
    """Run the offline pipeline and return the three files it creates."""

    raw_path = settings.raw_data_dir / "demo_players.json"
    processed_path = settings.processed_data_dir / "demo_players_clean.json"
    output_path = settings.output_data_dir / "demo_players.csv"

    save_raw_json(DEMO_PAYLOAD, raw_path)
    records = transform_raw_json(raw_path, processed_path)
    write_csv(records, output_path)

    return {
        "raw": raw_path,
        "processed": processed_path,
        "output": output_path,
    }


def run_live_schedule_pipeline(settings: Settings) -> dict[str, Path | int | str]:
    """Run ESPN scoreboard extraction, transformation, and CSV loading."""

    client = WnbaApiClient(
        scoreboard_url=settings.scoreboard_url,
        timeout_seconds=settings.api_timeout_seconds,
    )
    extraction = extract_scoreboard(client, settings.raw_data_dir)
    games = transform_scoreboard_games(
        extraction.payload,
        extracted_at_utc=extraction.extracted_at_utc,
        source=settings.scoreboard_url,
    )
    output_path = write_games_csv(
        games,
        settings.output_data_dir / "games.csv",
    )
    return {
        "raw": extraction.raw_path,
        "output": output_path,
        "game_count": len(games),
        "extracted_at_utc": extraction.extracted_at_utc,
    }


def run_historical_seasons_pipeline(
    settings: Settings,
    seasons: list[int],
) -> dict[str, object]:
    """Extract requested seasons and create one deduplicated historical table."""

    if not seasons:
        raise ValueError("At least one historical season is required.")

    client = WnbaApiClient(
        scoreboard_url=settings.scoreboard_url,
        timeout_seconds=settings.api_timeout_seconds,
    )
    raw_paths: list[Path] = []
    season_games: list[list[dict[str, object]]] = []
    extraction_time = datetime.now(timezone.utc)
    extraction_timestamp = extraction_time.isoformat().replace("+00:00", "Z")

    for season in seasons:
        extraction = extract_scoreboard(
            client,
            settings.raw_data_dir,
            extracted_at=extraction_time,
            season=season,
        )
        raw_paths.append(extraction.raw_path)
        season_games.append(
            transform_scoreboard_games(
                extraction.payload,
                extracted_at_utc=extraction.extracted_at_utc,
                source=settings.scoreboard_url,
            )
        )

    total_events = sum(len(games) for games in season_games)
    games, duplicate_count = combine_scoreboard_games(season_games)
    output_path = write_games_csv(
        games,
        settings.output_data_dir / "games_historical.csv",
    )
    return {
        "requested_seasons": seasons,
        "raw_paths": raw_paths,
        "output": output_path,
        "total_events_before_deduplication": total_events,
        "unique_game_count": len(games),
        "duplicate_count_removed": duplicate_count,
        "extracted_at_utc": extraction_timestamp,
    }


def parse_args() -> argparse.Namespace:
    """Define and read command-line options."""

    parser = argparse.ArgumentParser(description="Run the WNBA analytics ETL pipeline.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--demo",
        action="store_true",
        help="Run the offline sample pipeline; no API request is made.",
    )
    modes.add_argument(
        "--live-schedule",
        action="store_true",
        help="Fetch ESPN's live WNBA scoreboard and create games.csv.",
    )
    modes.add_argument(
        "--historical-seasons",
        nargs="+",
        type=int,
        metavar="YEAR",
        help="Fetch one or more WNBA seasons and create games_historical.csv.",
    )
    return parser.parse_args()


def main() -> None:
    """Choose the requested pipeline mode and display its results."""

    args = parse_args()
    if not args.demo and not args.live_schedule and not args.historical_seasons:
        print(
            "Choose --demo, --live-schedule, or --historical-seasons. "
            "Use --help for details."
        )
        return

    settings = get_settings()
    if args.demo:
        created_files = run_demo_pipeline(settings)
        print("Offline ETL demonstration completed:")
        for stage, path in created_files.items():
            print(f"  {stage}: {path}")
        return

    if args.historical_seasons:
        result = run_historical_seasons_pipeline(settings, args.historical_seasons)
        print("Historical ESPN WNBA season pipeline completed:")
        print(f"  requested seasons: {result['requested_seasons']}")
        print("  raw files:")
        for path in result["raw_paths"]:
            print(f"    {path}")
        print(f"  output: {result['output']}")
        print(
            "  total events before deduplication: "
            f"{result['total_events_before_deduplication']}"
        )
        print(f"  final unique games: {result['unique_game_count']}")
        print(f"  duplicates removed: {result['duplicate_count_removed']}")
        print(f"  extracted_at_utc: {result['extracted_at_utc']}")
        return

    result = run_live_schedule_pipeline(settings)
    print("Live ESPN WNBA schedule pipeline completed:")
    print(f"  raw: {result['raw']}")
    print(f"  output: {result['output']}")
    print(f"  games: {result['game_count']}")
    print(f"  extracted_at_utc: {result['extracted_at_utc']}")


if __name__ == "__main__":
    main()
