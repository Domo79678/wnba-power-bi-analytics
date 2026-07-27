"""Load cleaned records into a CSV table that Power BI can import."""

import csv
from pathlib import Path
from typing import Any


GAMES_COLUMNS = [
    "game_id",
    "game_date_utc",
    "season_year",
    "season_type",
    "game_name",
    "short_name",
    "status",
    "status_detail",
    "completed",
    "home_team_id",
    "home_team",
    "home_abbreviation",
    "home_score",
    "away_team_id",
    "away_team",
    "away_abbreviation",
    "away_score",
    "venue",
    "city",
    "state",
    "neutral_site",
    "attendance",
    "source",
    "extracted_at_utc",
]


def write_csv(
    records: list[dict[str, Any]],
    destination: Path,
    columns: list[str] | None = None,
) -> Path:
    """Write records to UTF-8 CSV and return the created file path.

    UTF-8 with a byte-order mark (``utf-8-sig``) helps spreadsheet and Microsoft
    tools recognize the encoding correctly. Column order follows first
    appearance across the records.
    """

    if not records and columns is None:
        raise ValueError("Cannot create a Power BI table from zero records.")

    fieldnames = columns or list(
        dict.fromkeys(key for record in records for key in record)
    )
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=fieldnames, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(records)

    return destination


def write_games_csv(records: list[dict[str, Any]], destination: Path) -> Path:
    """Write the stable games schema expected by Power BI."""

    return write_csv(records, destination, columns=GAMES_COLUMNS)
