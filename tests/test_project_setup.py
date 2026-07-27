"""Starter tests that demonstrate how the offline pipeline is verified."""

import csv
import json

from config import Settings
from scripts.api_client import WnbaApiClient
from scripts.main import run_demo_pipeline
from scripts.transform import normalize_records


def test_api_client_builds_json_headers() -> None:
    """The client should clearly request JSON from ESPN."""

    client = WnbaApiClient(scoreboard_url="https://data.example.test/scoreboard")
    assert client.build_headers() == {"Accept": "application/json"}


def test_transform_normalizes_column_names() -> None:
    """Source labels should become predictable Python and Power BI fields."""

    result = normalize_records([{"Player Name": "Example", "Points": 10}])
    assert result == [{"player_name": "Example", "points": 10}]


def test_demo_pipeline_creates_expected_files(tmp_path) -> None:
    """The full offline flow should produce valid JSON and CSV outputs."""

    settings = Settings(project_root=tmp_path)
    created = run_demo_pipeline(settings)

    assert all(path.exists() for path in created.values())
    assert json.loads(created["raw"].read_text(encoding="utf-8"))["records"]

    with created["output"].open(encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 2
    assert rows[0]["player_name"] == "Sample Guard"
