"""Coordinate the complete Extract, Transform, Load pipeline.

Run ``python -m scripts.main --demo`` from the project root. The demonstration
uses in-memory sample data and never connects to the internet.
"""

import argparse
from pathlib import Path

from config import Settings, get_settings
from scripts.extract import save_raw_json
from scripts.load import write_csv
from scripts.transform import transform_raw_json


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


def parse_args() -> argparse.Namespace:
    """Define and read command-line options."""

    parser = argparse.ArgumentParser(description="Run the WNBA analytics ETL pipeline.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the offline sample pipeline; no API request is made.",
    )
    return parser.parse_args()


def main() -> None:
    """Choose the requested pipeline mode and display its results."""

    args = parse_args()
    if not args.demo:
        print("Live API mode is not built yet. Use --demo for the offline pipeline.")
        return

    created_files = run_demo_pipeline(get_settings())
    print("Offline ETL demonstration completed:")
    for stage, path in created_files.items():
        print(f"  {stage}: {path}")


if __name__ == "__main__":
    main()
