# Data Module

## Source

This project uses the UCI Online Retail II dataset.

Source URL: https://archive.ics.uci.edu/dataset/502/online+retail+ii

## Local input

The public project does not store the full raw workbook or the large cleaned transaction file. Locally, the build script reads:

```text
../SQL_Study_package/day1_customer_retention_learning_pack/outputs/clean_transactions.csv
```

## Data structure

The raw dataset is an order-line table. One invoice can appear across many rows when a customer buys multiple products in the same order.

| Layer | What it represents | Example fields |
|---|---|---|
| Transaction line | One product line inside an invoice | invoice, stock code, quantity, unit price, line value |
| Order | One completed customer purchase | invoice, customer ID, order date, order value |
| Product | One stock item aggregated across sales | units sold, revenue, orders, customers, active months |
| Planning item | A product selected for action | top seller, slow-moving candidate, forecast item |

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

The cleaned analytical file removes rows that could not support sales analysis.

- Removed cancellation invoices where `invoice_no` starts with `C`.
- Removed rows with missing `customer_id`.
- Removed rows with non-positive `quantity` or `unit_price`.
- Removed exact duplicate rows after standardising fields.
- Added `line_value`.

## Why the full data is not committed

The full cleaned transaction file is large and unnecessary for reviewing the portfolio project. The repository contains code, SQL, documentation, and summary outputs instead.
