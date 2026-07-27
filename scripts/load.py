"""Load cleaned records into a CSV table that Power BI can import."""

import csv
from pathlib import Path
from typing import Any


def write_csv(records: list[dict[str, Any]], destination: Path) -> Path:
    """Write records to UTF-8 CSV and return the created file path.

    UTF-8 with a byte-order mark (``utf-8-sig``) helps spreadsheet and Microsoft
    tools recognize the encoding correctly. Column order follows first
    appearance across the records.
    """

    if not records:
        raise ValueError("Cannot create a Power BI table from zero records.")

    columns = list(dict.fromkeys(key for record in records for key in record))
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    return destination
