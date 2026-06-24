WITH order_values AS (
    SELECT
        invoice_no,
        customer_id,
        date(strftime('%Y-%m-01', invoice_date)) AS transaction_month,
        SUM(line_value) AS order_value
    FROM clean_transactions
    GROUP BY invoice_no, customer_id, date(strftime('%Y-%m-01', invoice_date))
),
customer_month_counts AS (
    SELECT
        transaction_month,
        customer_id,
        COUNT(*) AS monthly_orders
    FROM order_values
    GROUP BY transaction_month, customer_id
)
SELECT
    o.transaction_month,
    ROUND(SUM(o.order_value), 2) AS revenue,
    COUNT(DISTINCT o.invoice_no) AS orders,
    COUNT(DISTINCT o.customer_id) AS customers,
    ROUND(SUM(o.order_value) / COUNT(DISTINCT o.invoice_no), 2) AS average_order_value,
    ROUND(
        1.0 * COUNT(DISTINCT CASE WHEN c.monthly_orders >= 2 THEN c.customer_id END)
        / COUNT(DISTINCT o.customer_id),
        4
    ) AS repeat_purchase_rate
FROM order_values o
INNER JOIN customer_month_counts c
    ON o.transaction_month = c.transaction_month
   AND o.customer_id = c.customer_id
GROUP BY o.transaction_month
ORDER BY o.transaction_month;

