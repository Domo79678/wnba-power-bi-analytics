"""Central settings used by the ETL pipeline.

Paths are calculated from this file instead of from the terminal's current
directory. That means the project behaves consistently when run from an editor,
a test, or a future scheduler.
"""

from dataclasses import dataclass
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    # The offline demo can run before dependencies are installed.
    load_dotenv = None


# settings.py lives in config/, so its parent directory is the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load local values after `pip install -r requirements.txt`. The real `.env`
# file remains private because Git ignores it.
if load_dotenv is not None:
    load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Store project paths and future API configuration in one object."""

    project_root: Path = PROJECT_ROOT
    api_base_url: str = os.getenv("WNBA_API_BASE_URL", "https://example.invalid")
    api_key: str = os.getenv("WNBA_API_KEY", "")
    api_timeout_seconds: int = int(os.getenv("WNBA_API_TIMEOUT_SECONDS", "30"))

    @property
    def raw_data_dir(self) -> Path:
        """Return the folder used for untouched source responses."""
        return self.project_root / "data" / "raw"

    @property
    def processed_data_dir(self) -> Path:
        """Return the folder used for cleaned intermediate data."""
        return self.project_root / "data" / "processed"

    @property
    def output_data_dir(self) -> Path:
        """Return the folder used for final Power BI-ready CSV tables."""
        return self.project_root / "data" / "output"


def get_settings() -> Settings:
    """Create and return the current project settings.

    A function makes it straightforward to replace settings during a test.
    Environment values are intentionally optional during the offline stage.
    """

    return Settings()
