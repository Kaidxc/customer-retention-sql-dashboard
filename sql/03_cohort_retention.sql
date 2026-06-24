WITH customer_monthly_orders AS (
    SELECT DISTINCT
        customer_id,
        date(strftime('%Y-%m-01', invoice_date)) AS order_month
    FROM clean_transactions
),
customer_cohorts AS (
    SELECT
        customer_id,
        MIN(order_month) AS cohort_month
    FROM customer_monthly_orders
    GROUP BY customer_id
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        o.order_month,
        (
            (CAST(strftime('%Y', o.order_month) AS INTEGER) - CAST(strftime('%Y', c.cohort_month) AS INTEGER)) * 12
            + (CAST(strftime('%m', o.order_month) AS INTEGER) - CAST(strftime('%m', c.cohort_month) AS INTEGER))
        ) AS months_since_first_purchase,
        COUNT(DISTINCT o.customer_id) AS retained_customers
    FROM customer_monthly_orders o
    INNER JOIN customer_cohorts c
        ON o.customer_id = c.customer_id
    GROUP BY c.cohort_month, o.order_month
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    a.months_since_first_purchase,
    s.cohort_size,
    a.retained_customers,
    ROUND(1.0 * a.retained_customers / s.cohort_size, 4) AS retention_rate
FROM cohort_activity a
INNER JOIN cohort_sizes s
    ON a.cohort_month = s.cohort_month
ORDER BY a.cohort_month, a.months_since_first_purchase;

