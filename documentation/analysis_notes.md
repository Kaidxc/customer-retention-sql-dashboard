# Analysis Notes

## Analysis date

The analysis date is set to one day after the latest transaction date. This gives a stable reference point for product recency measures such as `days_since_last_sale`.

## Unit of analysis

The raw dataset is an order-line table. One invoice can contain multiple rows because each row represents one product line inside the order.

This project therefore uses three analytical layers:

| Layer | Why it matters |
|---|---|
| Transaction line | Validates quantity, price and line revenue. |
| Product | Measures units sold, revenue, order count, customer reach and active months. |
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

This is deliberately transparent. It is suitable for a portfolio project and early planning discussion, while leaving room for stronger models once inventory, margin, category and promotion data are available.

## Limitations

- The dataset does not contain customer demographics such as age, gender, occupation or marketing channel.
- Product category, stock availability, cost and margin are unavailable.
- A missing recent sale can mean weak demand, stockout, discontinuation or seasonality; the transaction data alone cannot distinguish these causes.
- Revenue is used instead of profit because product costs are not available.
