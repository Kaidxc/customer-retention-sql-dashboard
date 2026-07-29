# Insight to Action Map

This document connects the analysis to management decisions. It is designed for interview and portfolio review: each insight should lead to an action and a way to evaluate whether that action worked.

| Business question | Evidence generated | Recommended action | Metric to monitor | Extra data needed in a real business |
|---|---|---|---|---|
| Which products should be protected? | Top revenue products with broad order and customer reach | Protect stock availability and review supplier lead times | Revenue, units, order count, stockout rate | Inventory, supplier lead time, margin |
| Which products drive basket activity? | High-unit products that appear in many orders | Use as add-ons, bundles or merchandising support | Basket size, average order value, attach rate | Promotion exposure, margin, product category |
| Which products need lifecycle review? | Products with historical revenue but no sale for 180+ days | Check discontinuation, stockout, seasonality or clearance need | Sell-through rate, weeks since last sale, remaining stock | Inventory, product status, category owner notes |
| Which products can be forecast individually? | Stable high-revenue products active across many months | Use a simple next-quarter planning baseline | Forecast error, forecast bias, stock availability | Inventory, promotions, category, external seasonality |
| Which products need manual forecast review? | High backtest error or unusual sales spikes | Exclude from automated planning until reviewed | MAPE, MAE, bias, spike flags | Promotion history, stockout events, discontinued status |
| Where is demand concentrated geographically? | Country/region revenue and order distribution | Prioritise domestic planning while monitoring international opportunities | Revenue share, order share, customer share by country | Postcode, channel, shipping cost, local campaigns |
| Can management trust the report? | Data quality checks pass across six dimensions | Use outputs for portfolio reporting and planning discussion | Pass rate, affected rows, duplicate rate | Source-system controls and refresh monitoring |

## Decision Logic

1. Start with product range structure.
2. Separate product value, unit volume and product reach.
3. Identify products that need action: protect, promote, review or forecast.
4. Validate whether the forecast method is reasonable before using it for planning.
5. Define evaluation metrics before the business takes action.

## What This Shows

The project does not stop at descriptive analysis. It demonstrates the full analyst chain:

```text
business question -> checked data -> analytical output -> insight -> action -> evaluation metric
```
