# Forecasting Extension

## Purpose

The original project identifies which customers should be prioritised. The forecasting extension adds a second question:

> Based on recent monthly performance, what would a simple near-term baseline look like?

This is not intended to be a production forecasting model. It is a transparent baseline that demonstrates trend interpretation, forecast accuracy checking and careful communication of uncertainty.

## Method

The build script creates [`../outputs/monthly_forecast.csv`](../outputs/monthly_forecast.csv) from [`../outputs/monthly_kpis.csv`](../outputs/monthly_kpis.csv).

The current version uses a 3-month moving average baseline for:

- monthly revenue
- monthly repeat purchase rate

For each metric, the script:

1. Uses the previous 3 months to make one-step-ahead backtest predictions.
2. Calculates validation error using MAE and MAPE.
3. Forecasts the next 3 months from the most recent rolling average.
4. Adds a simple lower and upper band using recent backtest error.

## Generated visual

The same extension also creates:

```text
documentation/figures/monthly_forecast.svg
```

This gives a quick visual view of historical monthly revenue and the short-term forecast baseline.

## How to interpret it

- The forecast is a baseline, not a guarantee.
- The band is a practical uncertainty guide, not a formal statistical confidence interval.
- If the forecast is used for a real decision, it should be compared with stronger models and current operational context.

## Why this helps applications

This extension demonstrates skills that are useful across data analyst, BI analyst, performance analyst and insight analyst roles:

- trend analysis
- time-series thinking
- forecast accuracy assessment
- communicating uncertainty
- explaining the limits of a model
