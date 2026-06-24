# SQL Module

The SQL files define the repeatable analytical logic for the project. The build script runs these files against an in-memory SQLite database created from the cleaned transaction CSV.

## Query files

| File | Output | Purpose |
|---|---|---|
| `00_dataset_overview.sql` | `outputs/dataset_overview.csv` | Overall rows, customers, orders, revenue, and analysis date |
| `01_customer_kpis.sql` | `outputs/customer_metrics.csv` | Customer-level revenue, order frequency, AOV, first/last purchase dates, recency |
| `02_rfm_segmentation.sql` | `outputs/rfm_segments.csv` | RFM scores and customer segment labels |
| `02b_rfm_segment_summary.sql` | `outputs/rfm_segment_summary.csv` | Segment-level customer counts, revenue and average inactivity |
| `03_cohort_retention.sql` | `outputs/cohort_retention.csv` | Monthly cohort retention matrix input |
| `04_campaign_targets.sql` | `outputs/campaign_targets.csv` | Prioritised CRM retention target list |
| `05_monthly_kpis.sql` | `outputs/monthly_kpis.csv` | Monthly dashboard KPI trend |

## SQL dialect

The queries use SQLite syntax so the project can run locally without a database server. The same business logic can be translated to PostgreSQL by replacing date functions such as `strftime` and `julianday`.
