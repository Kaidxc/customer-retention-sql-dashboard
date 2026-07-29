# SQL Module

The SQL files define repeatable analytical logic. The build script runs these files against an in-memory SQLite database created from the cleaned transaction CSV.

## Main product query files

| File | Output | Purpose |
|---|---|---|
| `00_dataset_overview.sql` | `outputs/dataset_overview.csv` | Overall rows, customers, orders, revenue and analysis date |
| `01_customer_kpis.sql` | `outputs/customer_metrics.csv` | Customer purchase-behaviour metrics used for reach context |
| `02_order_purchase_summary.sql` | `outputs/order_purchase_summary.csv` | Order-level purchase size and value metrics |
| `05_monthly_kpis.sql` | `outputs/monthly_kpis.csv` | Monthly revenue, orders, customers, AOV and repeat-purchase context |
| `06_repeat_customer_summary.sql` | `outputs/repeat_customer_summary.csv` | Repeat-customer extract demonstrating `WHERE` and `HAVING` in context |
| `07_data_quality_checks.sql` | `outputs/data_quality_checks.csv` | Quality checks across accuracy, validity, timeliness, completeness, consistency and uniqueness |
| `08_product_performance.sql` | `outputs/product_performance.csv` | Product-level quantity, revenue, orders, customer reach, active months and ranks |
| `09_product_revenue_concentration.sql` | `outputs/product_revenue_concentration.csv` | Top-N merchandise revenue concentration |
| `10_product_quarterly_sales.sql` | `outputs/product_quarterly_sales.csv` | Product-by-quarter sales inputs for forecasting |

## SQL dialect

The queries use SQLite syntax so the project can run locally without a database server. The same business logic can be translated to PostgreSQL by replacing date functions such as `strftime` and `julianday`.
