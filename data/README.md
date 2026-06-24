# Data Module

## Source

This project uses the UCI Online Retail II dataset.

Source URL: https://archive.ics.uci.edu/dataset/502/online+retail+ii

## Local input

The public project does not store the full raw workbook or the large cleaned transaction file. Locally, the build script reads:

```text
../SQL_Study_package/day1_customer_retention_learning_pack/outputs/clean_transactions.csv
```

Expected columns:

| Column | Meaning |
|---|---|
| `invoice_no` | Invoice identifier |
| `stock_code` | Product identifier |
| `description` | Product description |
| `quantity` | Units sold on the transaction line |
| `invoice_date` | Transaction timestamp |
| `unit_price` | Unit price in GBP |
| `customer_id` | Customer identifier |
| `country` | Customer country |
| `source_period` | Source worksheet period |
| `line_value` | `quantity * unit_price` |

## Cleaning rules already applied

- Removed cancellation invoices where `invoice_no` starts with `C`.
- Removed rows with missing `customer_id`.
- Removed rows with non-positive `quantity` or `unit_price`.
- Removed exact duplicate rows after standardising fields.
- Added `line_value`.

## Why the full data is not committed

The full cleaned transaction file is large and unnecessary for reviewing the portfolio project. The repository contains code, SQL, documentation, and summary outputs instead.

