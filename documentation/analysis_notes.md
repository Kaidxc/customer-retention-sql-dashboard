# Analysis Notes

## Analysis date

The analysis date is set to one day after the latest transaction date. This avoids treating the final transaction day as zero days inactive for all current customers.

## RFM scoring

Customers are ranked into quintiles:

- Recency: lower `days_since_last_purchase` receives a higher score.
- Frequency: more distinct orders receives a higher score.
- Monetary: higher total revenue receives a higher score.

## Segment logic

| Segment | Rule |
|---|---|
| `Champions` | High recency, frequency and monetary scores |
| `Loyal Customers` | Recent and frequent customers |
| `At Risk High Value` | Low recency score but high monetary score |
| `New Customers` | Recent customers with one order |
| `Low Value Inactive` | Low recency, frequency and monetary scores |
| `Needs Nurture` | Customers not captured by the other rules |

## Campaign targeting logic

The campaign list focuses on customers with:

- Low recency score.
- High monetary score.
- At least two historical orders.

This keeps the recommendation transparent and suitable for a first portfolio version.

## Limitations

- Historical transactions do not prove that a campaign will cause customers to return.
- Product margin and campaign cost are unavailable, so the project prioritises revenue potential rather than profit.
- Missing customer IDs are excluded because those customers cannot be reliably targeted.
- The recommended next step is an A/B test to estimate incremental campaign uplift.

