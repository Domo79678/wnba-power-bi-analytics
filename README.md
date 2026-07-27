# WNBA Power BI Analytics

A beginner-friendly data engineering and analytics project built to practice
Python, APIs, ETL pipelines, data modeling, Power BI, Microsoft PL-300 skills,
and Git.

The project is intentionally being built in small stages. It now includes an
offline demonstration and one live-data vertical slice that turns ESPN WNBA
scoreboard JSON into a Power BI-ready games table.

## Learning goals

This project will help answer practical questions such as:

- How does Python request and store data from an API?
- Why should raw source data be preserved?
- How is nested JSON transformed into analysis-ready tables?
- How should tables be modeled for Power BI?
- How can tests and Git make an analytics project more reliable?

## Project structure

```text
config/          Shared application settings
data/raw/        Original JSON returned by a source
data/processed/  Cleaned intermediate data
data/archive/    Older data snapshots
data/output/     Final CSV tables imported into Power BI
docs/            Project plans and technical documentation
logs/            Pipeline run and error logs
notebooks/       Exploratory analysis notebooks
powerbi/         Power BI project files and notes
scripts/         Python ETL pipeline code
tests/           Automated checks
```

## ETL responsibility model

ETL means **Extract, Transform, Load**.

1. `scripts/api_client.py` communicates with the ESPN WNBA scoreboard.
2. `scripts/extract.py` saves the complete response body as untouched raw JSON.
3. `scripts/transform.py` cleans and reshapes one event into one game row.
4. `scripts/load.py` writes final CSV tables to `data/output/`.
5. `scripts/main.py` coordinates those steps.

Separating these responsibilities makes each part easier to understand, test,
replace, and troubleshoot.

## Setup

Python 3.11 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The `.env` file is for local configuration and secrets. It is ignored by Git.
Never commit real API keys.

## Run the offline demonstration

From the project root:

```powershell
python -m scripts.main --demo
```

The command uses sample records stored in memory—no internet connection is
made. It demonstrates the future flow by creating:

- a raw JSON file in `data/raw/`;
- a cleaned JSON file in `data/processed/`;
- a Power BI-ready CSV file in `data/output/`.

Generated data files are ignored by Git because they can be recreated.

## Run the live WNBA schedule pipeline

With the virtual environment active, run this command from the project root:

```powershell
python -m scripts.main --live-schedule
```

The pipeline makes one GET request to ESPN, applies the timeout configured by
`WNBA_API_TIMEOUT_SECONDS`, and creates:

- `data/raw/espn_wnba_scoreboard_<UTC timestamp>.json` — the complete response
  body exactly as received;
- `data/output/games.csv` — one flattened row for every event returned.

The raw filename includes UTC time so repeated extractions do not overwrite
their source evidence. `games.csv` has a stable name because Power BI needs a
consistent import path. Each run replaces that output table.

Scores and optional game details may be blank when ESPN has not published them.
The pipeline handles an empty event list by producing a header-only CSV.

### Data-source limitation

The [ESPN WNBA scoreboard endpoint](https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard)
is convenient for learning but is not documented as an official WNBA developer
API. Its fields or availability can change without notice. Without an explicit
date range, its default response is a scoreboard window rather than a guaranteed
complete season schedule.

Use the [official WNBA schedule](https://www.wnba.com/schedule) as the validation
source for game coverage, dates, and matchups before using the output for
reporting. Preserving each raw response makes later reconciliation possible.

## Run tests

```powershell
python -m pytest
```

Tests use a saved ESPN-shaped fixture and mocked HTTP responses. They never
require a live internet connection. They verify HTTP errors, raw preservation,
one-row-per-game grain, home/away assignment, missing optional values, and the
Power BI CSV schema.

## Current scope

- [x] Professional folder structure
- [x] Offline ETL demonstration
- [x] Configuration and test foundations
- [x] ESPN scoreboard live-data vertical slice
- [x] Power BI-ready `games.csv`
- [ ] Add historical date-range extraction
- [ ] Design Power BI fact and dimension tables
- [ ] Build the Power BI semantic model and report

Standings, players, rosters, and box scores are intentionally outside the
current milestone.

See [docs/project_plan.md](docs/project_plan.md) for the staged roadmap.
