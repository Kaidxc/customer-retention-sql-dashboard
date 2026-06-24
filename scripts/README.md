# Scripts Module

## Main script

`build_customer_retention_outputs.py`

This script rebuilds the complete project output from the local cleaned transaction CSV.

## What it does

1. Loads the cleaned transaction data.
2. Loads the data into an in-memory SQLite database.
3. Runs the SQL queries in `../sql`.
4. Writes dashboard-ready CSV files to `../outputs`.
5. Generates `../outputs/executive_summary.md`.
6. Generates `../dashboard/customer_retention_dashboard.html`.

## Run command

From the project root:

```bash
python scripts/build_customer_retention_outputs.py
```

## Dependency

The script requires `pandas`. SQLite is provided by the Python standard library.

