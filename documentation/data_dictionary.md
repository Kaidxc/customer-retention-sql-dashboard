# Data Dictionary

## Input fields

| Field | Definition |
|---|---|
| `invoice_no` | Invoice identifier |
| `stock_code` | Product identifier |
| `description` | Product description |
| `quantity` | Number of units on the transaction line |
| `invoice_date` | Transaction timestamp |
| `unit_price` | Unit price in GBP |
| `customer_id` | Customer identifier |
| `country` | Customer country |
| `source_period` | Source worksheet period |
| `line_value` | Transaction-line value, calculated as `quantity * unit_price` |

## Derived metrics

| Metric | Definition |
|---|---|
| `total_orders` | Count of distinct invoices per customer |
| `total_revenue` | Sum of order value per customer |
| `average_order_value` | Total revenue divided by distinct orders |
| `first_purchase_date` | Earliest order date for a customer |
| `last_purchase_date` | Latest order date for a customer |
| `days_since_last_purchase` | Difference between analysis date and last purchase date |
| `repeat_customer_flag` | 1 if a customer has at least two orders, otherwise 0 |
| `recency_score` | 1 to 5 score where 5 means most recent |
| `frequency_score` | 1 to 5 score where 5 means most frequent |
| `monetary_score` | 1 to 5 score where 5 means highest revenue |
| `retention_rate` | Retained customers divided by original cohort size |

