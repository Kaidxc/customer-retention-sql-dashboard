-- Business question: which customer IDs show repeat purchase behaviour?
-- WHERE removes incomplete customer records before aggregation; HAVING keeps
-- customer IDs with at least two completed orders as purchase context.
WITH customer_orders AS (
    SELECT
        customer_id,
        invoice_no,
        SUM(line_value) AS order_value
    FROM clean_transactions
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id, invoice_no
)
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    ROUND(SUM(order_value), 2) AS total_revenue,
    ROUND(AVG(order_value), 2) AS average_order_value
FROM customer_orders
GROUP BY customer_id
HAVING COUNT(*) >= 2
ORDER BY total_revenue DESC;
