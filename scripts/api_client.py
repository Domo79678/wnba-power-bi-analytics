"""Communicate with the ESPN WNBA scoreboard endpoint.

Only HTTP concerns belong here: URL, headers, timeout, and response errors.
Saving raw data and reshaping games remain separate ETL responsibilities.
"""

from dataclasses import dataclass
from typing import Iterable

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

    def build_season_params(self, season: int) -> dict[str, str]:
        """Build ESPN's undocumented whole-season scoreboard query.

        Keeping this mapping separate makes it easy to revise if ESPN changes
        its date-query behavior.
        """

        if season < 1997:
            raise ValueError("WNBA seasons must be 1997 or later.")
        return {"dates": str(season), "limit": "1000"}

    def fetch_scoreboard(
        self, params: dict[str, str] | None = None
    ) -> requests.Response:
        """GET the scoreboard and return its successful, unmodified response.

        Returning the response lets the extraction layer save the exact bytes
        ESPN sent. Tests replace ``requests.get`` with a local fake, so the test
        suite never needs an internet connection.
        """

        try:
            request_kwargs = {
                "headers": self.build_headers(),
                "timeout": self.timeout_seconds,
            }
            if params is not None:
                request_kwargs["params"] = params
            response = requests.get(self.scoreboard_url, **request_kwargs)
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

    def fetch_season(self, season: int) -> requests.Response:
        """Fetch one requested season using ESPN's date-query support."""

        return self.fetch_scoreboard(params=self.build_season_params(season))

    def fetch_seasons(self, seasons: Iterable[int]) -> list[requests.Response]:
        """Fetch requested seasons in order."""

        return [self.fetch_season(season) for season in seasons]
