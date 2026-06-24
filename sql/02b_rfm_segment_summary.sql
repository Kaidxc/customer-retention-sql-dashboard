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
),
customer_metrics AS (
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
),
scored AS (
    SELECT
        customer_metrics.*,
        6 - NTILE(5) OVER (ORDER BY days_since_last_purchase ASC) AS recency_score,
        NTILE(5) OVER (ORDER BY total_orders ASC, total_revenue ASC) AS frequency_score,
        NTILE(5) OVER (ORDER BY total_revenue ASC) AS monetary_score
    FROM customer_metrics
),
segmented AS (
    SELECT
        scored.*,
        CASE
            WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
            WHEN recency_score >= 3 AND frequency_score >= 4 THEN 'Loyal Customers'
            WHEN recency_score <= 2 AND monetary_score >= 4 THEN 'At Risk High Value'
            WHEN recency_score >= 4 AND total_orders = 1 THEN 'New Customers'
            WHEN recency_score <= 2 AND frequency_score <= 2 AND monetary_score <= 2 THEN 'Low Value Inactive'
            ELSE 'Needs Nurture'
        END AS rfm_segment
    FROM scored
)
SELECT
    rfm_segment,
    COUNT(DISTINCT customer_id) AS customers,
    ROUND(SUM(total_revenue), 2) AS segment_revenue,
    ROUND(AVG(total_revenue), 2) AS average_revenue_per_customer,
    ROUND(AVG(total_orders), 2) AS average_orders,
    ROUND(AVG(days_since_last_purchase), 2) AS average_days_since_last_purchase
FROM segmented
GROUP BY rfm_segment
ORDER BY segment_revenue DESC;
