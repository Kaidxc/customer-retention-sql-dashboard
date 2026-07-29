# Evaluation Plan

## Decision to evaluate

The report recommends product actions: protect high-revenue products, use high-unit products for basket-building, review slow-moving products, and use a next-quarter baseline for selected stable products.

Those recommendations are hypotheses. Historical sales can show where to act, but a business still needs to measure whether the action improved performance.

## Evaluation questions

| Product action | Evaluation question |
|---|---|
| Stock protection | Did availability protection reduce missed sales or stockout risk for high-revenue products? |
| Bundling/add-ons | Did high-unit products increase basket value when used as add-ons or bundles? |
| Slow-moving review | Did clearance, relisting, repositioning or delisting improve stock efficiency? |
| Forecast baseline | Did the baseline improve next-quarter planning accuracy compared with a naive prior-period view? |

## Suggested design

| Element | Recommendation |
|---|---|
| Eligible products | Products identified by the report as high-revenue, high-unit, slow-moving or forecastable. |
| Comparison | Compare against similar products not receiving the action, or against the same products in a prior comparable period. |
| Measurement window | Use a fixed post-action window, such as 4, 8 or 12 weeks, depending on product seasonality. |
| Primary metrics | Revenue, units sold, order count and sell-through rate if inventory is available. |
| Secondary metrics | Average selling price, basket value, customer reach and repeat purchase context. |
| Guardrails | Margin, discount cost, stock availability, return rate and supplier constraints if available. |

## Success criteria

A product action should be considered successful only if it improves the intended metric and remains commercially sensible after considering margin, stock availability and promotion cost.

For forecasting, success should be judged by forecast error, such as MAE or MAPE, compared with a simple benchmark.

## What this prevents

This plan avoids treating historical correlation as proof. A product that sold well before may continue selling without intervention; a product that slowed down may have been out of stock rather than undesirable. Evaluation separates the effect of the action from the product's existing pattern.

## Limitations

- Inventory, stockout, margin and promotion cost are not available in the current dataset.
- Product category is not available, so similar-product comparison would need extra business data.
- Some products may be seasonal or discontinued, which should be checked before measuring impact.

## Transferable value

The same logic applies to analyst roles where recommendations need to be tested: product launches, merchandising changes, service interventions, operational process changes, communications activity or pricing decisions.
