"""Offline tests for the ESPN WNBA schedule vertical slice."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
import requests

from config import Settings
from scripts.api_client import WnbaApiClient, WnbaApiError
from scripts.extract import extract_scoreboard
from scripts.load import GAMES_COLUMNS, write_games_csv
from scripts.main import run_live_schedule_pipeline
from scripts.transform import transform_scoreboard_games


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "espn_scoreboard_sample.json"
SAMPLE_BYTES = FIXTURE_PATH.read_bytes()
SAMPLE_PAYLOAD = json.loads(SAMPLE_BYTES)


class FakeResponse:
    """Small requests.Response substitute used to keep every test offline."""

    def __init__(self, content: bytes = SAMPLE_BYTES, error: Exception | None = None):
        self.content = content
        self._error = error

    def raise_for_status(self) -> None:
        """Raise the configured HTTP error, if the test supplied one."""

        if self._error:
            raise self._error

    def json(self) -> dict:
        """Parse the same bytes that extraction writes to the raw layer."""

        return json.loads(self.content)


def test_api_client_uses_get_and_configured_timeout(monkeypatch) -> None:
    """The HTTP boundary should make one GET with the configured timeout."""

    captured: dict = {}

    def fake_get(url, headers, timeout):
        captured.update(url=url, headers=headers, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    client = WnbaApiClient("https://example.test/scoreboard", timeout_seconds=17)

    assert client.fetch_scoreboard().content == SAMPLE_BYTES
    assert captured == {
        "url": "https://example.test/scoreboard",
        "headers": {"Accept": "application/json"},
        "timeout": 17,
    }


def test_api_client_raises_clear_error_for_unsuccessful_response(monkeypatch) -> None:
    """HTTP failures should become a readable project-specific exception."""

    def fake_get(url, headers, timeout):
        del url, headers, timeout
        return FakeResponse(error=requests.HTTPError("503 Service Unavailable"))

    monkeypatch.setattr(requests, "get", fake_get)
    client = WnbaApiClient("https://example.test/scoreboard")

    with pytest.raises(WnbaApiError, match="ESPN scoreboard request failed"):
        client.fetch_scoreboard()


def test_extract_preserves_raw_bytes_and_uses_utc_filename(tmp_path) -> None:
    """Raw storage should preserve the body and identify when it was extracted."""

    client = WnbaApiClient("https://example.test/scoreboard")
    client_fetch = lambda: FakeResponse()
    object.__setattr__(client, "fetch_scoreboard", client_fetch)
    extracted_at = datetime(2026, 5, 1, 12, 34, 56, tzinfo=timezone.utc)

    result = extract_scoreboard(client, tmp_path, extracted_at=extracted_at)

    assert result.raw_path.name == "espn_wnba_scoreboard_20260501T123456Z.json"
    assert result.raw_path.read_bytes() == SAMPLE_BYTES
    assert result.payload == SAMPLE_PAYLOAD
    assert result.extracted_at_utc == "2026-05-01T12:34:56Z"


def test_transform_creates_one_row_per_game_and_assigns_teams() -> None:
    """Event count and home/away labels should control the table grain."""

    games = transform_scoreboard_games(SAMPLE_PAYLOAD, "2026-05-01T12:34:56Z")

    assert len(games) == len(SAMPLE_PAYLOAD["events"]) == 2
    assert games[0]["home_team"] == "Chicago Sky"
    assert games[0]["home_abbreviation"] == "CHI"
    assert games[0]["away_team"] == "Minnesota Lynx"
    assert games[0]["away_abbreviation"] == "MIN"


def test_scheduled_games_receive_blank_scores() -> None:
    """ESPN's placeholder zeroes should not look like real scheduled scores."""

    game = transform_scoreboard_games(
        SAMPLE_PAYLOAD, "2026-05-01T12:34:56Z"
    )[1]

    assert game["completed"] is False
    assert game["home_score"] is None
    assert game["away_score"] is None


def test_completed_games_retain_actual_scores() -> None:
    """Completed scores, including a genuine zero, should remain unchanged."""

    game = transform_scoreboard_games(
        SAMPLE_PAYLOAD, "2026-05-01T12:34:56Z"
    )[0]

    assert game["completed"] is True
    assert game["home_score"] == "77"
    assert game["away_score"] == "82"

    payload_with_zero = json.loads(json.dumps(SAMPLE_PAYLOAD))
    payload_with_zero["events"][0]["competitions"][0]["competitors"][1][
        "score"
    ] = "0"
    zero_score_game = transform_scoreboard_games(
        payload_with_zero, "2026-05-01T12:34:56Z"
    )[0]
    assert zero_score_game["home_score"] == "0"


def test_transform_handles_missing_optional_fields() -> None:
    """Other absent game details should become blank values without crashing."""

    game = transform_scoreboard_games(
        SAMPLE_PAYLOAD, "2026-05-01T12:34:56Z"
    )[1]

    assert game["home_team"] == "Example Home"
    assert game["away_team"] is None
    assert game["venue"] is None
    assert game["attendance"] is None
    assert game["status"] == "Scheduled"


def test_games_csv_contains_expected_columns(tmp_path) -> None:
    """Power BI should receive the complete schema in a stable order."""

    games = transform_scoreboard_games(SAMPLE_PAYLOAD, "2026-05-01T12:34:56Z")
    output_path = write_games_csv(games, tmp_path / "games.csv")

    with output_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert reader.fieldnames == GAMES_COLUMNS
    assert len(rows) == 2


def test_live_pipeline_uses_mocked_response(monkeypatch, tmp_path) -> None:
    """The complete vertical slice should be testable without the internet."""

    monkeypatch.setattr(
        WnbaApiClient,
        "fetch_scoreboard",
        lambda self: FakeResponse(),
    )
    settings = Settings(
        project_root=tmp_path,
        scoreboard_url="https://example.test/scoreboard",
    )

    result = run_live_schedule_pipeline(settings)

    assert result["game_count"] == 2
    assert Path(result["raw"]).read_bytes() == SAMPLE_BYTES
    assert Path(result["output"]).name == "games.csv"
