-- Business question: can the dataset be trusted before it is used for decisions?
WITH total AS (
    SELECT COUNT(*) AS clean_rows
    FROM clean_transactions
),
analysis_bounds AS (
    SELECT
        date(MAX(invoice_date), '+1 day') AS analysis_date,
        MIN(date(invoice_date)) AS first_transaction_date,
        MAX(date(invoice_date)) AS last_transaction_date
    FROM clean_transactions
),
exact_duplicates AS (
    SELECT
        COALESCE(SUM(line_count - 1), 0) AS affected_rows
    FROM (
        SELECT COUNT(*) AS line_count
        FROM clean_transactions
        GROUP BY
            invoice_no,
            stock_code,
            description,
            quantity,
            invoice_date,
            unit_price,
            customer_id,
            country,
            source_period,
            line_value
        HAVING COUNT(*) > 1
    )
),
multi_customer_invoices AS (
    SELECT COUNT(*) AS affected_rows
    FROM (
        SELECT invoice_no
        FROM clean_transactions
        GROUP BY invoice_no
        HAVING COUNT(DISTINCT customer_id) > 1
    )
),
checks AS (
    SELECT
        'Completeness' AS dimension,
        'Required fields are populated' AS check_name,
        'Rows missing invoice, customer, date, quantity, price, value or country.' AS check_description,
        COUNT(*) AS affected_rows
    FROM clean_transactions
    WHERE invoice_no IS NULL
       OR TRIM(invoice_no) = ''
       OR customer_id IS NULL
       OR TRIM(customer_id) = ''
       OR invoice_date IS NULL
       OR quantity IS NULL
       OR unit_price IS NULL
       OR line_value IS NULL
       OR country IS NULL
       OR TRIM(country) = ''

    UNION ALL

    SELECT
        'Validity',
        'Transaction values are usable',
        'Rows with non-positive quantity, non-positive unit price or negative line value.',
        COUNT(*)
    FROM clean_transactions
    WHERE quantity <= 0
       OR unit_price <= 0
       OR line_value < 0

    UNION ALL

    SELECT
        'Accuracy',
        'Line value matches quantity times price',
        'Rows where line_value differs materially from quantity * unit_price.',
        COUNT(*)
    FROM clean_transactions
    WHERE ABS(line_value - (quantity * unit_price)) > 0.01

    UNION ALL

    SELECT
        'Timeliness',
        'No transactions after the analysis date',
        'Rows dated after the analysis date used for recency calculations.',
        COUNT(*)
    FROM clean_transactions
    WHERE date(invoice_date) >= (SELECT analysis_date FROM analysis_bounds)

    UNION ALL

    SELECT
        'Consistency',
        'Invoices map to one customer',
        'Invoices linked to more than one customer ID.',
        affected_rows
    FROM multi_customer_invoices

    UNION ALL

    SELECT
        'Uniqueness',
        'No exact duplicate transaction lines',
        'Additional rows created by exact duplicate transaction-line records.',
        affected_rows
    FROM exact_duplicates
)
SELECT
    dimension,
    check_name,
    check_description,
    CAST(affected_rows AS INTEGER) AS affected_rows,
    ROUND(1.0 * affected_rows / NULLIF((SELECT clean_rows FROM total), 0), 4) AS affected_share,
    CASE
        WHEN affected_rows = 0 THEN 'Pass'
        ELSE 'Review'
    END AS status
FROM checks
ORDER BY
    CASE dimension
        WHEN 'Accuracy' THEN 1
        WHEN 'Validity' THEN 2
        WHEN 'Timeliness' THEN 3
        WHEN 'Completeness' THEN 4
        WHEN 'Consistency' THEN 5
        WHEN 'Uniqueness' THEN 6
        ELSE 7
    END;
