WITH params AS (
    SELECT
        date(max(invoice_date), '+1 day') AS analysis_date
    FROM clean_transactions
),
customer_orders AS (
    SELECT
        customer_id,
        invoice_no,
        MIN(invoice_date) AS order_timestamp,
        SUM(line_value) AS order_value
    FROM clean_transactions
    GROUP BY customer_id, invoice_no
)
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    ROUND(SUM(order_value), 2) AS total_revenue,
    ROUND(AVG(order_value), 2) AS average_order_value,
    date(MIN(order_timestamp)) AS first_purchase_date,
    date(MAX(order_timestamp)) AS last_purchase_date,
    CAST(
        julianday((SELECT analysis_date FROM params))
        - julianday(date(MAX(order_timestamp)))
        AS INTEGER
    ) AS days_since_last_purchase,
    CASE WHEN COUNT(*) >= 2 THEN 1 ELSE 0 END AS repeat_customer_flag
FROM customer_orders
GROUP BY customer_id
ORDER BY total_revenue DESC;

