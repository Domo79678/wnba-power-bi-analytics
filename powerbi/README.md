# Power BI

This directory will hold Power BI project assets and documentation.

The final CSV tables consumed by Power BI belong in `data/output/`, not here.
When the model is designed, document table relationships, DAX measures, refresh
steps, and report-page decisions in this directory.

Power BI Project (`.pbip`) format is preferable when practical because its text
files work better with Git than a single binary `.pbix` file.
