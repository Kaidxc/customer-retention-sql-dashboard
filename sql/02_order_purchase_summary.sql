-- Business question: what does a completed order look like after cleaning?
-- Each row in this output is one invoice, with purchase size and value metrics.
SELECT
    invoice_no,
    customer_id,
    MIN(DATE(invoice_date)) AS order_date,
    MIN(country) AS country,
    COUNT(*) AS product_lines,
    COUNT(DISTINCT stock_code) AS distinct_products,
    SUM(quantity) AS units_purchased,
    ROUND(SUM(line_value), 2) AS order_value
FROM clean_transactions
GROUP BY invoice_no, customer_id
ORDER BY order_date, invoice_no;
