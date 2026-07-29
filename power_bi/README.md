# Power BI Design Pack

This folder describes how the generated outputs can be turned into a Power BI report for business users. The goal is not to copy every static chart from the README. The goal is to build an interactive report where a stakeholder can move from overview to product action.

## Recommended User Flow

1. Start with the executive overview to understand total revenue, orders, products, countries and revenue concentration.
2. Use the product performance page to compare revenue, units sold, order reach and customer reach.
3. Use the purchase behaviour page to understand order value, basket size and repeat purchase context.
4. Use the catalogue health page to identify slow-moving or inactive products for review.
5. Use the geographic page to understand country/region concentration.
6. Use the forecast and validation page to review next-quarter baseline demand and backtest error.
7. Use the data quality appendix to check whether the underlying data can be trusted.

## Data Sources

Import the generated CSV files from `../outputs/`:

| File | Use in Power BI |
|---|---|
| `dataset_overview.csv` | Executive KPI cards |
| `product_performance.csv` | Product performance page and product dimension |
| `order_purchase_summary.csv` | Order-level purchase behaviour |
| `customer_profile_summary.csv` | Customer repeat and purchase frequency distributions |
| `purchase_behavior_summary.csv` | Order value and basket size distributions |
| `country_sales_context.csv` | Geographic sales context |
| `product_revenue_concentration.csv` | Revenue concentration visual |
| `top_products_by_revenue.csv` | Top revenue products |
| `top_products_by_quantity.csv` | Top unit products |
| `slow_moving_product_candidates.csv` | Product review page |
| `product_quarterly_sales.csv` | Product-level time series |
| `product_next_quarter_forecast.csv` | Next-quarter planning baseline |
| `product_forecast_backtest.csv` | Forecast validation |
| `monthly_kpis.csv` | Monthly revenue and order trends |
| `data_quality_checks.csv` | Data quality appendix |

## Report Pages

Detailed page layouts are documented in [`report_pages.md`](report_pages.md).

Recommended pages:

1. Executive Overview
2. Product Performance
3. Purchase Behaviour
4. Catalogue Health
5. Geographic Sales Context
6. Forecast and Planning
7. Data Quality Appendix

## Model and Measures

- Proposed data model: [`data_model.md`](data_model.md)
- KPI and DAX measure definitions: [`measures.md`](measures.md)

## Design Principles

- Keep the first page management-friendly: KPIs, key findings and recommended actions.
- Put data quality detail in an appendix, not in the first management view.
- Use slicers for country, product, market group and time period.
- Use drill-through from summary pages into product details.
- Avoid making the report table-heavy. Tables should support investigation after the visual story is clear.

## What This Adds to the Portfolio

This Power BI design pack demonstrates:

- stakeholder-focused dashboard planning
- fact/dimension modelling
- DAX KPI thinking
- data quality communication
- forecast validation and responsible modelling
- the ability to turn analysis into a reusable reporting product
