# KPI and DAX Measure Definitions

These measures are written as Power BI design documentation. Table names assume the proposed model in [`data_model.md`](data_model.md).

## Core Sales Measures

```DAX
Total Revenue =
SUM ( FactTransactionLines[line_value] )
```

```DAX
Total Orders =
DISTINCTCOUNT ( FactTransactionLines[invoice_no] )
```

```DAX
Units Sold =
SUM ( FactTransactionLines[quantity] )
```

```DAX
Known Customers =
DISTINCTCOUNT ( FactTransactionLines[customer_id] )
```

```DAX
Average Order Value =
DIVIDE ( [Total Revenue], [Total Orders] )
```

## Product Measures

```DAX
Merchandise Products =
CALCULATE (
    DISTINCTCOUNT ( DimProduct[stock_code] ),
    DimProduct[stock_line_type] = "merchandise"
)
```

```DAX
Product Revenue =
SUM ( FactTransactionLines[line_value] )
```

```DAX
Product Reach Orders =
DISTINCTCOUNT ( FactTransactionLines[invoice_no] )
```

```DAX
Product Reach Customers =
DISTINCTCOUNT ( FactTransactionLines[customer_id] )
```

```DAX
Average Selling Price =
DIVIDE ( [Product Revenue], [Units Sold] )
```

## Purchase Behaviour Measures

```DAX
Repeat Customers =
CALCULATE (
    DISTINCTCOUNT ( DimCustomer[customer_id] ),
    DimCustomer[repeat_customer_flag] = 1
)
```

```DAX
Repeat Customer Share =
DIVIDE ( [Repeat Customers], [Known Customers] )
```

```DAX
Median Order Value =
MEDIAN ( FactOrders[order_value] )
```

```DAX
Median Units per Order =
MEDIAN ( FactOrders[units_purchased] )
```

```DAX
Median Distinct Products per Order =
MEDIAN ( FactOrders[distinct_products] )
```

## Revenue Concentration Measures

For Top N analysis, use a product rank measure or a Top N parameter.

```DAX
Revenue Share =
DIVIDE ( [Total Revenue], CALCULATE ( [Total Revenue], ALL ( DimProduct ) ) )
```

```DAX
Top 500 Revenue =
CALCULATE (
    [Total Revenue],
    FILTER ( ALL ( DimProduct ), DimProduct[revenue_rank] <= 500 )
)
```

```DAX
Top 500 Revenue Share =
DIVIDE ( [Top 500 Revenue], CALCULATE ( [Total Revenue], ALL ( DimProduct ) ) )
```

## Geographic Measures

```DAX
Domestic Revenue =
CALCULATE (
    [Total Revenue],
    DimCountry[market_group] = "Domestic"
)
```

```DAX
International Revenue =
CALCULATE (
    [Total Revenue],
    DimCountry[market_group] = "International"
)
```

```DAX
Domestic Revenue Share =
DIVIDE ( [Domestic Revenue], [Total Revenue] )
```

## Forecast Measures

```DAX
Forecast Revenue =
SUM ( FactProductForecast[forecast_revenue] )
```

```DAX
Forecast Units =
SUM ( FactProductForecast[forecast_quantity] )
```

```DAX
Forecast Revenue MAE =
AVERAGE ( FactForecastBacktest[revenue_mae] )
```

```DAX
Forecast Revenue MAPE =
AVERAGE ( FactForecastBacktest[revenue_mape] )
```

```DAX
Median Forecast Revenue MAPE =
MEDIAN ( FactForecastBacktest[revenue_mape] )
```

## Data Quality Measures

```DAX
Data Quality Checks =
COUNTROWS ( DataQualityChecks )
```

```DAX
Passed Data Quality Checks =
CALCULATE (
    COUNTROWS ( DataQualityChecks ),
    DataQualityChecks[status] = "Pass"
)
```

```DAX
Data Quality Pass Rate =
DIVIDE ( [Passed Data Quality Checks], [Data Quality Checks] )
```

## Reporting Notes

- Use revenue and unit measures together. Unit rank and revenue rank answer different business questions.
- Use forecast error measures on the forecast page so the report does not imply false precision.
- Use product reach measures to separate broad-demand products from one-off bulk transactions.
- Keep data quality measures visible in an appendix and as a small status indicator on the executive page.
