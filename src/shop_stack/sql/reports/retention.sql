WITH customer_order_months AS (
    SELECT DISTINCT
        f.customer_id,
        d.month_start AS order_month
    FROM fact_order_items f
    JOIN dim_date d ON f.created_date = d.date
    WHERE f.status <> 'Cancelled'
),
customer_cohort_month AS (
    SELECT
        customer_id,
        MIN(order_month) AS cohort_month
    FROM customer_order_months
    GROUP BY customer_id
),
customer_cohort_offset AS (
    SELECT
        ccm.customer_id,
        ccm.cohort_month,
        com.order_month,
        DATE_DIFF('month', cohort_month, order_month) AS months_since_cohort
    FROM customer_cohort_month ccm
    JOIN customer_order_months com ON ccm.customer_id = com.customer_id
    ORDER BY ccm.customer_id, com.order_month
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS customer_count
    FROM customer_cohort_month
    GROUP BY cohort_month
),
retention_counts AS (
    SELECT
        cohort_month,
        months_since_cohort,
        COUNT(DISTINCT customer_id) AS returning_customers
    FROM customer_cohort_offset
    WHERE months_since_cohort > 0
    GROUP BY cohort_month, months_since_cohort
)
SELECT
    cs.cohort_month,
    cs.customer_count,
    rc.months_since_cohort,
    rc.returning_customers,
    ROUND(100.0 * rc.returning_customers / cs.customer_count, 1) as retention_pct
FROM cohort_sizes cs
LEFT JOIN retention_counts rc ON cs.cohort_month = rc.cohort_month
ORDER BY cs.cohort_month, rc.months_since_cohort;