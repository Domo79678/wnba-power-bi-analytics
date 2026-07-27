"""Communicate with the ESPN WNBA scoreboard endpoint.

Only HTTP concerns belong here: URL, headers, timeout, and response errors.
Saving raw data and reshaping games remain separate ETL responsibilities.
"""

from dataclasses import dataclass

import requests


class WnbaApiError(RuntimeError):
    """Provide a clear project-level message when the ESPN request fails."""


@dataclass(frozen=True)
class WnbaApiClient:
    """Make a configured GET request to ESPN's WNBA scoreboard."""

    scoreboard_url: str
    timeout_seconds: int = 30

    def build_headers(self) -> dict[str, str]:
        """Tell ESPN that this pipeline expects a JSON response."""

        return {"Accept": "application/json"}

    def fetch_scoreboard(self) -> requests.Response:
        """GET the scoreboard and return its successful, unmodified response.

        Returning the response lets the extraction layer save the exact bytes
        ESPN sent. Tests replace ``requests.get`` with a local fake, so the test
        suite never needs an internet connection.
        """

        try:
            response = requests.get(
                self.scoreboard_url,
                headers=self.build_headers(),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise WnbaApiError(
                f"ESPN scoreboard request timed out after "
                f"{self.timeout_seconds} seconds: {self.scoreboard_url}"
            ) from exc
        except requests.RequestException as exc:
            raise WnbaApiError(
                f"ESPN scoreboard request failed for {self.scoreboard_url}: {exc}"
            ) from exc

        return response
