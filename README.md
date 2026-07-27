# WNBA Power BI Analytics

A beginner-friendly data engineering and analytics project built to practice
Python, APIs, ETL pipelines, data modeling, Power BI, Microsoft PL-300 skills,
and Git.

The project is intentionally being built in small stages. The current stage
creates the project foundation and an offline ETL demonstration. It does **not**
connect to a live WNBA data source yet.

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

1. `scripts/api_client.py` will communicate with the future WNBA data source.
2. `scripts/extract.py` saves a source response as unchanged raw JSON.
3. `scripts/transform.py` cleans and reshapes raw records.
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

## Run tests

```powershell
python -m pytest
```

Tests protect expected behavior as the project grows.

## Current scope

- [x] Professional folder structure
- [x] Offline ETL demonstration
- [x] Configuration and test foundations
- [ ] Select and document a WNBA data source
- [ ] Connect `api_client.py` to that source
- [ ] Design Power BI fact and dimension tables
- [ ] Build the Power BI semantic model and report

See [docs/project_plan.md](docs/project_plan.md) for the staged roadmap.
