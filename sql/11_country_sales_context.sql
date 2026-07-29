-- Business question: where are sales, orders and known customers concentrated by country?
WITH country_sales AS (
    SELECT
        country,
        COUNT(*) AS transaction_lines,
        COUNT(DISTINCT invoice_no) AS order_count,
        COUNT(DISTINCT customer_id) AS customer_count,
        SUM(quantity) AS units_sold,
        ROUND(SUM(line_value), 2) AS revenue
    FROM clean_transactions
    GROUP BY country
),
totals AS (
    SELECT
        SUM(revenue) AS total_revenue,
        SUM(order_count) AS total_orders,
        SUM(customer_count) AS total_customers
    FROM country_sales
)
SELECT
    c.country,
    c.transaction_lines,
    c.order_count,
    c.customer_count,
    c.units_sold,
    c.revenue,
    ROUND(c.revenue / NULLIF(t.total_revenue, 0), 4) AS revenue_share,
    ROUND(c.order_count * 1.0 / NULLIF(t.total_orders, 0), 4) AS order_share,
    ROUND(c.customer_count * 1.0 / NULLIF(t.total_customers, 0), 4) AS customer_share,
    CASE
        WHEN c.country = 'United Kingdom' THEN 'Domestic'
        ELSE 'International'
    END AS market_group,
    ROW_NUMBER() OVER (ORDER BY c.revenue DESC) AS revenue_rank
FROM country_sales c
CROSS JOIN totals t
ORDER BY c.revenue DESC;
