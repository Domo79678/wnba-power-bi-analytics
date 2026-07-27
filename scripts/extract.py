"""Extract source records by saving them as raw JSON.

Extraction should preserve the source response. Cleaning belongs in
``transform.py`` so analysts can always compare transformed results with the
original evidence.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.api_client import WnbaApiClient


@dataclass(frozen=True)
class ScoreboardExtraction:
    """Describe the artifacts produced by one live extraction."""

    raw_path: Path
    payload: dict[str, Any]
    extracted_at_utc: str


def save_raw_json(payload: dict[str, Any] | list[Any], destination: Path) -> Path:
    """Write a JSON-compatible payload to disk and return its path.

    Args:
        payload: Data received from a source or supplied by the offline demo.
        destination: Complete path of the raw JSON file to create.
    """

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return destination


def extract_scoreboard(
    client: WnbaApiClient,
    raw_data_dir: Path,
    extracted_at: datetime | None = None,
) -> ScoreboardExtraction:
    """Request ESPN and save its complete response body as timestamped JSON.

    ``extracted_at`` is injectable so tests can verify filenames without relying
    on the computer clock. Production runs default to the current UTC time.
    """

    response = client.fetch_scoreboard()
    timestamp = extracted_at or datetime.now(timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)
    filename_timestamp = timestamp.strftime("%Y%m%dT%H%M%SZ")
    extracted_at_utc = timestamp.isoformat().replace("+00:00", "Z")

    raw_path = raw_data_dir / f"espn_wnba_scoreboard_{filename_timestamp}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    # Save response.content rather than re-serializing response.json(). This
    # preserves the exact successful body received from ESPN.
    raw_path.write_bytes(response.content)

    try:
        payload = response.json()
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"ESPN returned a successful response that was not valid JSON: {raw_path}"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError("Expected the ESPN scoreboard response to be a JSON object.")

    return ScoreboardExtraction(raw_path, payload, extracted_at_utc)
