"""Clean raw JSON records into a consistent, table-shaped collection."""

import json
import re
from pathlib import Path
from typing import Any


ESPN_SCOREBOARD_SOURCE = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"
)


def _to_snake_case(name: str) -> str:
    """Convert a source field such as ``Player Name`` into ``player_name``."""

    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_")
    return cleaned.lower()


def _make_tabular(value: Any) -> Any:
    """Keep scalar values as-is and serialize nested values predictably."""

    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return value


def normalize_records(payload: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    """Return records with snake_case column names and table-friendly values.

    The starter accepts either a list of records or a dictionary containing a
    ``records`` list. Real source-specific rules will be added only after the
    actual JSON response is understood.
    """

    records: Any = payload.get("records", []) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("Expected a list or a dictionary containing a 'records' list.")

    normalized: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Every record must be a dictionary of field names and values.")
        normalized.append(
            {
                _to_snake_case(str(column)): _make_tabular(value)
                for column, value in record.items()
            }
        )
    return normalized


def transform_raw_json(source: Path, destination: Path) -> list[dict[str, Any]]:
    """Read raw JSON, normalize its records, and save processed JSON."""

    payload = json.loads(source.read_text(encoding="utf-8"))
    records = normalize_records(payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return records


def _as_dict(value: Any) -> dict[str, Any]:
    """Return a dictionary, or an empty one when an optional object is absent."""

    return value if isinstance(value, dict) else {}


def _first_dict(value: Any) -> dict[str, Any]:
    """Return the first dictionary in a list, or an empty dictionary."""

    if isinstance(value, list):
        return next((item for item in value if isinstance(item, dict)), {})
    return {}


def _find_competitor(competition: dict[str, Any], side: str) -> dict[str, Any]:
    """Find a home or away competitor without trusting the source array order."""

    competitors = competition.get("competitors", [])
    if not isinstance(competitors, list):
        return {}
    return next(
        (
            competitor
            for competitor in competitors
            if isinstance(competitor, dict) and competitor.get("homeAway") == side
        ),
        {},
    )


def _team_fields(competitor: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    """Return team id, display name, abbreviation, and score safely."""

    team = _as_dict(competitor.get("team"))
    return (
        team.get("id", competitor.get("id")),
        team.get("displayName"),
        team.get("abbreviation"),
        competitor.get("score"),
    )


def transform_scoreboard_games(
    payload: dict[str, Any],
    extracted_at_utc: str,
    source: str = ESPN_SCOREBOARD_SOURCE,
) -> list[dict[str, Any]]:
    """Flatten ESPN scoreboard events into one analysis row per game."""

    events = payload.get("events", [])
    if not isinstance(events, list):
        raise ValueError("Expected ESPN's 'events' field to be a list.")

    games: list[dict[str, Any]] = []
    for event_value in events:
        event = _as_dict(event_value)
        competition = _first_dict(event.get("competitions"))
        season = _as_dict(event.get("season"))
        status = _as_dict(competition.get("status") or event.get("status"))
        status_type = _as_dict(status.get("type"))
        venue = _as_dict(competition.get("venue"))
        address = _as_dict(venue.get("address"))

        home = _find_competitor(competition, "home")
        away = _find_competitor(competition, "away")
        home_id, home_name, home_abbreviation, home_score = _team_fields(home)
        away_id, away_name, away_abbreviation, away_score = _team_fields(away)
        completed = status_type.get("completed")

        # ESPN commonly represents a scheduled game's not-yet-known score as
        # the string "0". Blank both scores until the game is completed so
        # Power BI does not interpret placeholders as real results.
        if completed is not True:
            home_score = None
            away_score = None

        games.append(
            {
                "game_id": event.get("id") or competition.get("id"),
                "game_date_utc": event.get("date") or competition.get("date"),
                "season_year": season.get("year"),
                "season_type": season.get("slug", season.get("type")),
                "game_name": event.get("name"),
                "short_name": event.get("shortName"),
                "status": status_type.get("description"),
                "status_detail": status_type.get("detail")
                or status_type.get("shortDetail"),
                "completed": completed,
                "home_team_id": home_id,
                "home_team": home_name,
                "home_abbreviation": home_abbreviation,
                "home_score": home_score,
                "away_team_id": away_id,
                "away_team": away_name,
                "away_abbreviation": away_abbreviation,
                "away_score": away_score,
                "venue": venue.get("fullName"),
                "city": address.get("city"),
                "state": address.get("state"),
                "neutral_site": competition.get("neutralSite"),
                "attendance": competition.get("attendance"),
                "source": source,
                "extracted_at_utc": extracted_at_utc,
            }
        )

    return games
