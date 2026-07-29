-- Business question: which stock items drive units, revenue, orders and customer reach?
WITH monthly_product_sales AS (
    SELECT
        stock_code,
        date(strftime('%Y-%m-01', invoice_date)) AS sale_month
    FROM clean_transactions
    GROUP BY stock_code, date(strftime('%Y-%m-01', invoice_date))
),
product_base AS (
    SELECT
        stock_code,
        MAX(description) AS product_description,
        SUM(quantity) AS total_quantity,
        ROUND(SUM(line_value), 2) AS total_revenue,
        COUNT(DISTINCT invoice_no) AS order_count,
        COUNT(DISTINCT customer_id) AS customer_count,
        ROUND(SUM(line_value) / NULLIF(SUM(quantity), 0), 2) AS average_selling_price,
        MIN(date(invoice_date)) AS first_sale_date,
        MAX(date(invoice_date)) AS last_sale_date
    FROM clean_transactions
    GROUP BY stock_code
),
active_months AS (
    SELECT
        stock_code,
        COUNT(*) AS active_months
    FROM monthly_product_sales
    GROUP BY stock_code
)
SELECT
    p.stock_code,
    p.product_description,
    CASE
        WHEN p.stock_code IN ('POST', 'M', 'DOT', 'BANK CHARGES', 'C2') THEN 'service_or_admin_line'
        ELSE 'merchandise'
    END AS stock_line_type,
    p.total_quantity,
    p.total_revenue,
    p.order_count,
    p.customer_count,
    p.average_selling_price,
    a.active_months,
    p.first_sale_date,
    p.last_sale_date,
    ROW_NUMBER() OVER (ORDER BY p.total_quantity DESC) AS quantity_rank,
    ROW_NUMBER() OVER (ORDER BY p.total_revenue DESC) AS revenue_rank
FROM product_base p
INNER JOIN active_months a
    ON p.stock_code = a.stock_code
ORDER BY p.total_revenue DESC;
