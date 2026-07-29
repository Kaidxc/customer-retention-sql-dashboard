# Executive Summary

## Objective

Analyse online retail transaction lines to understand product sales structure, identify the strongest and weakest product opportunities, and create a practical next-quarter planning baseline.

## Analysis base

- Analysis date: 2011-12-10
- Transaction lines analysed: 793,609
- Completed orders analysed: 36,969
- Known customers represented: 5,878
- Merchandise products analysed: 4,626
- Revenue analysed: GBP 17,685,461

## Key findings

- Product sales are uneven: the top 10 merchandise products contribute 8.1% of merchandise revenue, while the top 500 contribute 64.0%.
- Top revenue product: `REGENCY CAKESTAND 3 TIER` (22423), generating GBP 285,992.
- Top quantity product: `WORLD WAR 2 GLIDERS ASSTD DESIGNS` (84077), with 108,929 units sold.
- Broadest-reach product: `WHITE HANGING HEART T-LIGHT HOLDER` (85123A), appearing in 4,895 orders from 1,490 customers.
- Customer and purchase behaviour: 4,255 customers (72.4%) placed at least two orders; the median order value is GBP 305 and the median order contains 154 units.
- Geographic context: 41 countries/regions are represented; United Kingdom contributes 82.9% of analysed revenue.
- 25 high-history-revenue merchandise products have not sold for at least 180 days and should be reviewed for clearance, bundling, relisting or delisting.
- Next-quarter baseline for 20 stable high-revenue merchandise products: 76,320 units and GBP 205,589 revenue in 2012-Q1.
- Historical backtest for the forecasting baseline uses 5 validation quarters per product; median product-level revenue MAPE is 47.9%.

## Recommended product actions

Protect stock availability for high-revenue products, use high-volume lower-revenue products for bundle and add-on opportunities, review slow-moving products before discounting or delisting, and use the next-quarter product forecast as a planning baseline rather than a final buying decision.

## Evidence for decision-makers

- [Product catalogue overview](../documentation/figures/product_catalog_overview.svg) shows the stable core range, low-selling product review need and revenue concentration.
- [Customer and purchase behaviour](../documentation/figures/customer_purchase_overview.svg) shows repeat status, customer order frequency, order value and units per order.
- [Top products by revenue](../documentation/figures/top_products_by_revenue.svg) highlights the products driving income.
- [Top products by quantity](../documentation/figures/top_products_by_quantity.svg) highlights the products driving unit demand.
- [Slow-moving product candidates](../documentation/figures/slow_moving_products.svg) shows products with historical value but weak recent sales.
- [Next-quarter product forecast](../documentation/figures/product_forecast_next_quarter.svg) provides a simple planning baseline for stable high-revenue products.
- [Geographic sales context](../documentation/figures/country_sales_context.svg) shows the country/region concentration of sales.
- [Forecast backtest summary](../documentation/figures/product_forecast_backtest.svg) shows how the baseline performed when tested against historical quarters.

## Forecasting note

The product forecast uses an average of the last four quarters and is limited to stable high-revenue merchandise products. The backtest is included so the baseline can be challenged before it is used for planning. It is designed as an interpretable planning baseline, not a production demand-forecasting model.
