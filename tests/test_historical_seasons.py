"""Offline tests for the multi-season ESPN WNBA pipeline."""

import csv
import json
from pathlib import Path

import requests

from config import Settings
from scripts.api_client import WnbaApiClient
from scripts.main import run_historical_seasons_pipeline
from scripts.transform import combine_scoreboard_games, transform_scoreboard_games


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "espn_scoreboard_sample.json"
SAMPLE_PAYLOAD = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload
        self.content = json.dumps(payload).encode()

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self.payload


def test_season_request_parameters_are_isolated_and_used(monkeypatch) -> None:
    captured = {}

    def fake_get(url, **kwargs):
        captured.update(url=url, **kwargs)
        return FakeResponse(SAMPLE_PAYLOAD)

    monkeypatch.setattr(requests, "get", fake_get)
    client = WnbaApiClient("https://example.test/scoreboard")

    assert client.build_season_params(2025) == {"dates": "2025", "limit": "1000"}
    client.fetch_season(2025)
    assert captured["url"] == "https://example.test/scoreboard"
    assert captured["params"] == {"dates": "2025", "limit": "1000"}


def test_client_fetches_multiple_seasons_in_order(monkeypatch) -> None:
    requested = []

    def fake_fetch(self, season):
        requested.append(season)
        return FakeResponse({"events": []})

    monkeypatch.setattr(WnbaApiClient, "fetch_season", fake_fetch)
    responses = WnbaApiClient("https://example.test").fetch_seasons([2025, 2026])

    assert requested == [2025, 2026]
    assert len(responses) == 2


def test_combining_deduplicates_and_sorts_chronologically() -> None:
    later = {"game_id": "2", "game_date_utc": "2026-06-01T00:00Z"}
    earlier = {"game_id": "1", "game_date_utc": "2025-05-01T00:00Z"}
    duplicate = {"game_id": "2", "game_date_utc": "2026-06-01T00:00Z"}

    combined, removed = combine_scoreboard_games([[later, earlier], [duplicate]])

    assert [game["game_id"] for game in combined] == ["1", "2"]
    assert removed == 1


def test_historical_pipeline_orchestrates_seasons_and_uses_output_name(
    monkeypatch, tmp_path
) -> None:
    requested = []

    def fake_fetch(self, season):
        requested.append(season)
        payload = json.loads(json.dumps(SAMPLE_PAYLOAD))
        if season == 2025:
            payload["events"] = [payload["events"][0]]
            payload["events"][0]["season"]["year"] = 2025
            payload["events"][0]["date"] = "2025-05-15T23:30Z"
        return FakeResponse(payload)

    monkeypatch.setattr(WnbaApiClient, "fetch_season", fake_fetch)
    result = run_historical_seasons_pipeline(
        Settings(project_root=tmp_path, scoreboard_url="https://example.test"),
        [2025, 2026],
    )

    assert requested == [2025, 2026]
    assert [path.name.split("_")[3] for path in result["raw_paths"]] == [
        "2025",
        "2026",
    ]
    assert Path(result["output"]).name == "games_historical.csv"
    assert result["total_events_before_deduplication"] == 3
    assert result["unique_game_count"] == 2
    assert result["duplicate_count_removed"] == 1

    with Path(result["output"]).open(
        encoding="utf-8-sig", newline=""
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert [row["game_date_utc"] for row in rows] == sorted(
        row["game_date_utc"] for row in rows
    )


def test_historical_transform_keeps_score_edge_cases() -> None:
    games = transform_scoreboard_games(SAMPLE_PAYLOAD, "2026-05-01T00:00:00Z")
    assert games[1]["home_score"] is None
    assert games[1]["away_score"] is None

    payload = json.loads(json.dumps(SAMPLE_PAYLOAD))
    payload["events"][0]["competitions"][0]["competitors"][1]["score"] = "0"
    completed = transform_scoreboard_games(payload, "2026-05-01T00:00:00Z")[0]
    assert completed["home_score"] == "0"
