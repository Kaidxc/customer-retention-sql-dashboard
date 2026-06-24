WITH params AS (
    SELECT
        date(max(invoice_date), '+1 day') AS analysis_date
    FROM clean_transactions
)
SELECT
    (SELECT analysis_date FROM params) AS analysis_date,
    COUNT(*) AS clean_rows,
    COUNT(DISTINCT invoice_no) AS distinct_orders,
    COUNT(DISTINCT customer_id) AS distinct_customers,
    ROUND(SUM(line_value), 2) AS total_revenue,
    ROUND(AVG(line_value), 2) AS average_line_value,
    MIN(date(invoice_date)) AS first_transaction_date,
    MAX(date(invoice_date)) AS last_transaction_date
FROM clean_transactions;

