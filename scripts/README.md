# Scripts Module

## Main script

`build_customer_retention_outputs.py`

This script rebuilds the complete product sales and demand analysis from the local cleaned transaction CSV. The filename is retained for continuity with the original repository.

## What it does

1. Loads the cleaned transaction data.
2. Loads the data into an in-memory SQLite database.
3. Runs the SQL queries in `../sql`.
4. Writes dashboard-ready product CSV files to `../outputs`.
5. Generates product-focused SVG charts in `../documentation/figures`.
6. Generates `../outputs/executive_summary.md`.
7. Generates `../dashboard/product_sales_dashboard.html`.

## Run command

From the project root:

```bash
python scripts/build_customer_retention_outputs.py
```

## Dependency

The script requires `pandas`. SQLite is provided by the Python standard library.
