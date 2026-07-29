# Proposed Power BI Data Model

The project can be modelled as a simple retail star schema. The CSV outputs in `../outputs/` are already dashboard-ready, but this model shows how the same analysis would be structured in a BI environment.

## Grain

| Table | Grain |
|---|---|
| `FactTransactionLines` | One product line inside one invoice |
| `FactOrders` | One completed invoice |
| `FactProductQuarterlySales` | One product per quarter |
| `FactProductForecast` | One forecasted product for the next quarter |
| `FactForecastBacktest` | One selected product with validation error metrics |
| `DimProduct` | One stock code |
| `DimCustomer` | One customer ID |
| `DimDate` | One calendar date |
| `DimCountry` | One country/region |

## Recommended Tables

### FactTransactionLines

Source: prepared transaction table used by the build script.

Key fields:

- `invoice_no`
- `stock_code`
- `customer_id`
- `invoice_date`
- `country`
- `quantity`
- `unit_price`
- `line_value`

Use this table when the report needs transaction-level drill-through.

### FactOrders

Source: `outputs/order_purchase_summary.csv`

Key fields:

- `invoice_no`
- `customer_id`
- `order_date`
- `product_lines`
- `distinct_products`
- `units_purchased`
- `order_value`

Use this table for order value, basket size and order frequency reporting.

### DimProduct

Source: `outputs/product_performance.csv`

Key fields:

- `stock_code`
- `product_description`
- `stock_line_type`
- `average_selling_price`
- `first_sale_date`
- `last_sale_date`
- `active_months`
- `quantity_rank`
- `revenue_rank`

Use this table for product slicers and product-level attributes.

### DimCustomer

Source: `outputs/customer_metrics.csv`

Key fields:

- `customer_id`
- `total_orders`
- `total_revenue`
- `average_order_value`
- `first_purchase_date`
- `last_purchase_date`
- `days_since_last_purchase`
- `repeat_customer_flag`

Use this table for purchase behaviour context. Do not treat it as a demographic customer profile.

### DimCountry

Source: `outputs/country_sales_context.csv`

Key fields:

- `country`
- `market_group`
- `revenue_rank`

Use this table for country slicers and domestic/international grouping.

### DimDate

Source: calendar table generated in Power BI or Power Query.

Recommended fields:

- `Date`
- `Year`
- `Quarter`
- `Month`
- `Month Name`
- `Year Month`
- `Is Completed Month`

Use this table for all time intelligence.

### FactProductQuarterlySales

Source: `outputs/product_quarterly_sales.csv`

Key fields:

- `stock_code`
- `sale_quarter`
- `quantity_sold`
- `revenue`
- `order_count`
- `customer_count`

Use this table for product seasonality and forecast context.

### FactProductForecast

Source: `outputs/product_next_quarter_forecast.csv`

Key fields:

- `stock_code`
- `next_quarter`
- `method`
- `forecast_quantity`
- `forecast_revenue`
- `latest_quarter_quantity`
- `latest_quarter_revenue`

Use this table for the next-quarter planning page.

### FactForecastBacktest

Source: `outputs/product_forecast_backtest.csv`

Key fields:

- `stock_code`
- `validation_quarters`
- `revenue_mae`
- `revenue_mape`
- `revenue_bias`
- `quantity_mae`
- `quantity_mape`
- `quantity_bias`

Use this table to show whether the baseline is reliable enough for planning.

## Relationships

Recommended relationships:

| From | To | Cardinality | Direction |
|---|---|---|---|
| `FactOrders[customer_id]` | `DimCustomer[customer_id]` | Many to one | Single |
| `FactTransactionLines[customer_id]` | `DimCustomer[customer_id]` | Many to one | Single |
| `FactTransactionLines[stock_code]` | `DimProduct[stock_code]` | Many to one | Single |
| `FactProductQuarterlySales[stock_code]` | `DimProduct[stock_code]` | Many to one | Single |
| `FactProductForecast[stock_code]` | `DimProduct[stock_code]` | Many to one | Single |
| `FactForecastBacktest[stock_code]` | `DimProduct[stock_code]` | Many to one | Single |
| `FactOrders[order_date]` | `DimDate[Date]` | Many to one | Single |
| `FactTransactionLines[invoice_date]` | `DimDate[Date]` | Many to one | Single |
| `FactTransactionLines[country]` | `DimCountry[country]` | Many to one | Single |

## Power Query Notes

Recommended Power Query transformations:

- Set date and numeric data types explicitly.
- Trim text fields such as `stock_code`, `description` and `country`.
- Create `Market Group` from country: `Domestic` for United Kingdom, `International` otherwise.
- Create a calendar table from the minimum to maximum transaction date.
- Keep data quality checks as a separate appendix table instead of blending them into fact tables.

## Why This Model Matters

This structure shows relational modelling knowledge: fact tables, dimension tables, relationships, grain and KPI reuse. It also keeps the report flexible so the same model can support management overview, product drill-through, geographic context and forecast planning.
