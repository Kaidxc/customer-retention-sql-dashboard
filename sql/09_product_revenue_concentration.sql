-- Business question: how concentrated is revenue across the product catalogue?
WITH product_revenue AS (
    SELECT
        stock_code,
        SUM(line_value) AS total_revenue
    FROM clean_transactions
    WHERE stock_code NOT IN ('POST', 'M', 'DOT', 'BANK CHARGES', 'C2')
    GROUP BY stock_code
),
ranked AS (
    SELECT
        stock_code,
        total_revenue,
        ROW_NUMBER() OVER (ORDER BY total_revenue DESC) AS revenue_rank
    FROM product_revenue
),
total AS (
    SELECT SUM(total_revenue) AS all_product_revenue
    FROM ranked
),
thresholds(top_n) AS (
    SELECT 10
    UNION ALL SELECT 50
    UNION ALL SELECT 100
    UNION ALL SELECT 500
),
combined AS (
    SELECT
        'Top ' || top_n AS product_group,
        top_n,
        COUNT(r.stock_code) AS products_in_group,
        ROUND(SUM(r.total_revenue), 2) AS group_revenue,
        ROUND(1.0 * SUM(r.total_revenue) / (SELECT all_product_revenue FROM total), 4) AS revenue_share
    FROM thresholds t
    INNER JOIN ranked r
        ON r.revenue_rank <= t.top_n
    GROUP BY t.top_n

    UNION ALL

    SELECT
        'All merchandise products' AS product_group,
        NULL AS top_n,
        COUNT(stock_code) AS products_in_group,
        ROUND(SUM(total_revenue), 2) AS group_revenue,
        1.0 AS revenue_share
    FROM ranked
)
SELECT
    product_group,
    top_n,
    products_in_group,
    group_revenue,
    revenue_share
FROM combined
ORDER BY
    CASE WHEN top_n IS NULL THEN 1 ELSE 0 END,
    top_n;
