-- Business question: how do product sales change by quarter?
SELECT
    stock_code,
    MAX(description) AS product_description,
    strftime('%Y', invoice_date) || '-Q' ||
        ((CAST(strftime('%m', invoice_date) AS INTEGER) - 1) / 3 + 1) AS sale_quarter,
    SUM(quantity) AS quantity_sold,
    ROUND(SUM(line_value), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS order_count,
    COUNT(DISTINCT customer_id) AS customer_count
FROM clean_transactions
WHERE stock_code NOT IN ('POST', 'M', 'DOT', 'BANK CHARGES', 'C2')
GROUP BY
    stock_code,
    strftime('%Y', invoice_date) || '-Q' ||
        ((CAST(strftime('%m', invoice_date) AS INTEGER) - 1) / 3 + 1)
ORDER BY stock_code, sale_quarter;
