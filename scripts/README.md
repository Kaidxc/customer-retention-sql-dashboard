# Scripts Module

## Main script

`build_online_retail_outputs.py`

This script rebuilds the complete product sales, BI reporting and demand planning analysis from the local cleaned transaction CSV.

## What it does

1. Loads the cleaned transaction data.
2. Loads the data into an in-memory SQLite database.
3. Runs the SQL queries in `../sql`.
4. Writes dashboard-ready CSV files to `../outputs`.
5. Generates product, country and forecast validation SVG charts in `../documentation/figures`.
6. Generates `../outputs/executive_summary.md`.
7. Generates `../dashboard/product_sales_dashboard.html`.

## Run command

From the project root:

```bash
python scripts/build_online_retail_outputs.py
```

## Dependency

The script requires `pandas`. SQLite is provided by the Python standard library.
