"""Clean raw JSON records into a consistent, table-shaped collection."""

import json
import re
from pathlib import Path
from typing import Any


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
