# Customer Retention SQL & Dashboard Project

Portfolio project using the UCI Online Retail II transaction dataset to support a retention-campaign targeting decision.

## Business question

A UK online retailer has a limited campaign budget. Which customers should be prioritised for a retention campaign?

## What this project demonstrates

- Data cleaning logic for transaction data with cancellations, missing customer IDs, non-positive quantities or prices, and duplicate records.
- SQL customer KPIs including revenue, order frequency, average order value, repeat purchase behaviour, first purchase date, last purchase date, and days since last purchase.
- RFM segmentation to identify high-value inactive customers.
- Cohort retention analysis to measure repeat purchasing patterns over time.
- Dashboard-ready CSV outputs and a self-contained HTML dashboard.
- A short business interpretation that turns analysis into CRM targeting recommendations.

## Folder structure

```text
data/             Data source notes and local input guidance
scripts/          Reproducible Python build script
sql/              SQL queries used to generate portfolio outputs
outputs/          Generated dashboard-ready CSVs and executive summary
dashboard/        Dashboard specification and generated HTML dashboard
documentation/    Business brief, data dictionary, analysis notes, CV bullets
```

## Reproduce the project

The full raw dataset is not committed. The script expects the cleaned transaction file already created in the earlier learning pack:

```text
../SQL_Study_package/day1_customer_retention_learning_pack/outputs/clean_transactions.csv
```

Run:

```bash
python scripts/build_customer_retention_outputs.py
```

The script will regenerate all CSV outputs, the executive summary, and the HTML dashboard.

## Main outputs

- `outputs/customer_metrics.csv`
- `outputs/rfm_segments.csv`
- `outputs/rfm_segment_summary.csv`
- `outputs/cohort_retention.csv`
- `outputs/monthly_kpis.csv`
- `outputs/campaign_targets.csv`
- `outputs/executive_summary.md`
- `dashboard/customer_retention_dashboard.html`

## How this maps to analyst work

This project mirrors a common product and CRM analytics workflow: prepare reliable customer-level data, define repeatable metrics in SQL, segment customers using transparent rules, measure retention patterns, and explain which customers should be contacted first.

