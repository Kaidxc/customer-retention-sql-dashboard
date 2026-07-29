# Analysis Notes

## Analysis date

The analysis date is set to one day after the latest transaction date. This gives a stable reference point for product recency measures such as `days_since_last_sale`.

## Unit of analysis

The raw dataset is an order-line table. One invoice can contain multiple rows because each row represents one product line inside the order.

This project therefore uses four analytical layers:

| Layer | Why it matters |
|---|---|
| Transaction line | Validates quantity, price and line revenue. |
| Order | Measures order value, units purchased and basket size. |
| Customer purchase behaviour | Summarises repeat status, orders per customer and spend distribution without creating demographic profiles. |
| Product | Measures units sold, revenue, order count, customer reach and active months. |
| Country/region | Shows where revenue, orders and known customers are concentrated. |
| Planning item | Classifies products as top revenue drivers, high-unit sellers, slow-moving candidates or forecast items. |

## Product line classification

Most stock codes are merchandise products. A small number of codes represent service or administrative lines, such as postage, manual adjustments, bank charges or carriage.

Those service/admin lines are excluded from product ranking and forecasting so the report does not treat charges or adjustments as sellable products.

## Ranking logic

The report intentionally separates three product views:

| View | Question answered |
|---|---|
| Revenue ranking | Which products matter most commercially? |
| Unit ranking | Which products create volume and basket activity? |
| Customer/order reach | Which products are bought broadly rather than by only a few buyers? |

This prevents the analysis from assuming that the highest-unit products are automatically the highest-value products.

## Slow-moving logic

Slow-moving candidates are merchandise products that generated at least GBP 5,000 in historical revenue but have not appeared in a sale for at least 180 days.

They are not automatically bad products. The business should check whether they are discontinued, seasonal, out of stock, poorly merchandised or genuinely declining before discounting or delisting.

## Forecasting logic

Product-level forecasting is limited to stable high-revenue merchandise products. The current baseline uses the average of the last four quarters.

The same baseline is backtested against historical quarters. The validation output reports MAE, MAPE and bias so the business can see where the simple method is more or less reliable.

This is deliberately transparent. It is suitable for a portfolio project and early planning discussion, while leaving room for stronger models once inventory, margin, category and promotion data are available.

## Geographic logic

Country/region analysis is included because the dataset contains a `country` field. It is limited to sales context:

- revenue by country/region
- order count by country/region
- known customer count by country/region
- domestic vs international market grouping

It should not be described as detailed GIS modelling because the dataset does not include postcode, address, store, station or risk-area information.

## Limitations

- The dataset does not contain customer demographics such as age, gender, occupation or marketing channel.
- Product category, stock availability, cost and margin are unavailable.
- A missing recent sale can mean weak demand, stockout, discontinuation or seasonality; the transaction data alone cannot distinguish these causes.
- Revenue is used instead of profit because product costs are not available.
- Country/region is available, but detailed location data is not available.
