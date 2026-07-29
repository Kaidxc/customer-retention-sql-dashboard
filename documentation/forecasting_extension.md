# Forecasting Extension

## Purpose

The report first explains what sold historically. The forecasting extension adds a forward-looking question:

> For stable high-revenue merchandise products, what is a reasonable next-quarter planning baseline?

This is not a production demand-forecasting system. It is an interpretable baseline that shows how historical product sales can be turned into a planning input.

## Why not forecast every product?

The catalogue is broad, and many products sell only occasionally. Some appear to be seasonal, and some may be discontinued. Forecasting every stock code individually would create false precision.

The project therefore forecasts only products that are:

- merchandise products, not service or administrative lines
- active across at least 18 months
- above GBP 10,000 in historical revenue
- among the top stable high-revenue products

## Method

The build script creates [`../outputs/product_next_quarter_forecast.csv`](../outputs/product_next_quarter_forecast.csv) from product-level quarterly sales.

For each selected product, the baseline:

1. Aggregates historical sales into quarters.
2. Uses the last four quarters as the recent planning window.
3. Forecasts next-quarter quantity and revenue as the average of those four quarters.
4. Reports the method and latest-quarter values so the forecast is easy to audit.

## Generated visual

The extension creates:

```text
documentation/figures/product_forecast_next_quarter.svg
```

The chart shows the next-quarter revenue baseline for the highest-priority stable products.

## How to interpret it

- Treat the forecast as a starting point for stock and promotion planning, not as an automated buying decision.
- Review products with seasonality, recent discontinuation, unusual spikes or possible stockouts before acting.
- Combine this baseline with margin, inventory, supplier lead time and promotion plans in a real business setting.

## Transferable value

This extension demonstrates skills useful across data analyst, BI analyst, commercial analyst, merchandising analyst and demand planning roles:

- product-level time-series aggregation
- baseline forecasting
- forecast scope selection
- uncertainty-aware communication
- turning analysis into planning recommendations
