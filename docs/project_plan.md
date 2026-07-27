# Project Plan

## Purpose

Build a professional WNBA analytics pipeline while learning the full path from
source data to a Power BI report. Each stage should be understood and tested
before the next stage is added.

## Guiding principles

- Preserve raw data so the source can always be audited.
- Keep API, extraction, transformation, and loading responsibilities separate.
- Store secrets in environment variables, never in source control.
- Prefer repeatable scripts over manual data editing.
- Validate data before using it to make conclusions.
- Design tables for analysis before designing report visuals.
- Commit small, understandable changes with Git.

## Planned stages

### Stage 1: Project foundation — current

- Create the directory structure and documentation.
- Define configuration in one place.
- Build a small offline ETL demonstration.
- Add starter tests and Git exclusions.

**Learning outcome:** understand how the parts of a Python analytics repository
fit together.

### Stage 2: Data source discovery

- Compare available WNBA data sources.
- Review documentation, access rules, authentication, and rate limits.
- Record the chosen source and the fields it provides.
- Update `.env.example` with the real configuration variable names.

**Learning outcome:** understand how to evaluate an API before writing code.

### Stage 3: Extraction

- Implement HTTP requests in `api_client.py`.
- Add timeouts, clear errors, and responsible retry behavior.
- Save responses unchanged through `extract.py`.
- Test the client with mocked responses rather than repeated live calls.

**Learning outcome:** understand HTTP requests and reliable ingestion.

### Stage 4: Transformation and data quality

- Inspect raw JSON structure and data types.
- Handle missing values and duplicates deliberately.
- Create consistent identifiers, dates, and column names.
- Add tests for transformation rules and quality checks.

**Learning outcome:** turn source data into trustworthy analytical data.

### Stage 5: Dimensional modeling and loading

- Define the business grain of every table.
- Design fact and dimension tables.
- Write Power BI-ready CSV files to `data/output/`.
- Document relationships and metric definitions.

**Learning outcome:** understand star schemas and analytical table design.

### Stage 6: Power BI and PL-300 practice

- Import output tables into Power BI.
- Configure relationships and a date table.
- Create explicit DAX measures.
- Build accessible report pages with useful interactions.
- Validate report totals against Python outputs.

**Learning outcome:** practice the prepare, model, visualize, and manage domains
covered by PL-300.

### Stage 7: Automation and maintenance

- Add structured logging.
- Archive previous outputs safely.
- Add command-line options and scheduled execution.
- Expand tests and project documentation.

**Learning outcome:** operate the project as a repeatable data product.

## Data flow

```text
WNBA data source
        |
        v
api_client.py -> extract.py -> data/raw
                                  |
                                  v
                          transform.py
                                  |
                                  v
                          data/processed
                                  |
                                  v
                              load.py
                                  |
                                  v
                           data/output
                                  |
                                  v
                              Power BI
```

The current offline demo begins at `extract.py` with in-memory sample data. The
live-source arrow will be implemented only after a data source is selected.
