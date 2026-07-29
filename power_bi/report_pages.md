# Power BI Report Pages

This document describes the recommended Power BI report design. It is written for a stakeholder-facing retail analytics report.

## 1. Executive Overview

Purpose: give management a fast view of what matters.

Recommended visuals:

- KPI cards: revenue, orders, merchandise products, countries/regions, Top 500 revenue share.
- Product range snapshot: stable core, high-value items, inactive products.
- Monthly revenue and orders line chart.
- Short product action panel: protect, bundle, review, forecast.

Recommended slicers:

- Date
- Country/region
- Market group
- Product

Management question answered:

> Where should management attention start?

## 2. Product Performance

Purpose: compare products by commercial value, volume and reach.

Recommended visuals:

- Bar chart: Top products by revenue.
- Bar chart: Top products by units sold.
- Scatter plot: revenue vs units sold, sized by customer reach.
- Matrix: product, revenue, units, orders, customers, active months, last sale date.

Recommended interactions:

- Click a product to filter the monthly trend and quarterly sales.
- Use drill-through to a product detail page.

Management question answered:

> Which products are commercially important, which create volume, and which have broad demand?

## 3. Purchase Behaviour

Purpose: show how customers and orders behave without creating demographic claims.

Recommended visuals:

- Repeat vs one-time customer distribution.
- Orders per customer distribution.
- Order value distribution.
- Units per order and distinct products per order distribution.

Management question answered:

> What do purchase patterns look like, and how should product reach be interpreted?

## 4. Catalogue Health

Purpose: identify products that need lifecycle or merchandising review.

Recommended visuals:

- Active months distribution.
- Revenue per product distribution.
- Days since last sale distribution.
- Slow-moving product candidate list.

Recommended flags:

- Stable core product
- High revenue product
- No sale for 180+ days
- No sale for 365+ days

Management question answered:

> Which products should be protected, reviewed, cleared, bundled or removed from planning?

## 5. Geographic Sales Context

Purpose: provide country/region sales context.

Recommended visuals:

- Filled map or bar chart by country/region.
- Domestic vs international revenue split.
- Top countries by revenue, orders and customers.

Important limitation:

The dataset only contains country/region. It does not contain postcode, city, store, station or risk-area fields. This page should therefore be presented as geographic sales context, not detailed GIS modelling.

Management question answered:

> Where is sales activity concentrated?

## 6. Forecast and Planning

Purpose: turn historical sales into a cautious next-quarter planning baseline.

Recommended visuals:

- Forecast revenue by selected stable product.
- Forecast units by selected stable product.
- Latest-quarter revenue vs forecast revenue.
- Forecast backtest error by product.
- Data table for planning review.

Recommended filters:

- Forecastable products only.
- Revenue rank.
- Backtest error threshold.

Management question answered:

> Which stable products can be planned with a simple baseline, and which need manual review?

## 7. Data Quality Appendix

Purpose: show that the report is based on checked data.

Recommended visuals:

- Data quality pass rate.
- Quality checks by dimension.
- Affected rows and status.
- Notes on cleaning assumptions.

Management question answered:

> Can the figures in this report be trusted?

## Visual Design Notes

- Put management messages at the top of each page.
- Use charts before tables.
- Use tables only for investigation and export.
- Use consistent colours for revenue, units, forecast and review flags.
- Keep data quality detail out of the first page unless there is a problem.
