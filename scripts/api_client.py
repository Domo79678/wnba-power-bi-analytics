"""Define the boundary between this project and a future WNBA data source.

No live request is made in the scaffold stage. The helper methods below already
handle URL and header construction, while ``fetch_json`` stops with an
educational error until a source has been researched and selected.
"""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin


class LiveApiNotConfiguredError(RuntimeError):
    """Explain that live API access is intentionally unavailable for now."""


@dataclass(frozen=True)
class WnbaApiClient:
    """Hold the settings needed to communicate with a future WNBA API."""

    base_url: str
    api_key: str = ""
    timeout_seconds: int = 30

    def build_url(self, endpoint: str) -> str:
        """Combine a base URL and endpoint without duplicate or missing slashes."""

        normalized_base = f"{self.base_url.rstrip('/')}/"
        return urljoin(normalized_base, endpoint.lstrip("/"))

    def build_headers(self) -> dict[str, str]:
        """Build HTTP headers without exposing a blank authentication value."""

        headers = {"Accept": "application/json"}
        if self.api_key:
            # The exact authentication header may change when a source is chosen.
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def fetch_json(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[Any]:
        """Eventually request JSON from the selected WNBA data source.

        Raising an explicit exception is safer than pretending a request
        succeeded. A later stage will implement this method with ``requests``
        after authentication, rate limits, and response structure are known.
        """

        del endpoint, params  # Mark these future inputs as intentionally unused.
        raise LiveApiNotConfiguredError(
            "Live API access is not configured. Run `python -m scripts.main "
            "--demo` to use the offline learning pipeline."
        )
