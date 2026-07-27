"""Extract source records by saving them as raw JSON.

Extraction should preserve the source response. Cleaning belongs in
``transform.py`` so analysts can always compare transformed results with the
original evidence.
"""

import json
from pathlib import Path
from typing import Any


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
