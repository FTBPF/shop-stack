WITH session_flags AS (
    SELECT
        session_id,
        MAX(CASE WHEN event_type = 'product' THEN 1 ELSE 0 END) AS has_product,
        MAX(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) AS has_cart,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS has_purchase
    FROM fact_events
    GROUP BY session_id
),
stages AS (
    SELECT 1 AS stage_order, 'sessions' AS stage, COUNT(*) AS session_count
    FROM session_flags
    UNION ALL
    SELECT 2, 'product', SUM(has_product)
    FROM session_flags
    UNION ALL
    SELECT 3, 'cart', SUM(has_cart)
    FROM session_flags
    UNION ALL
    SELECT 4, 'purchase', SUM(has_purchase)
    FROM session_flags
)
SELECT
    stage,
    session_count,
    ROUND(100.0 * session_count / LAG(session_count, 1, session_count) OVER (ORDER BY stage_order), 1) AS from_previous_stage_pct,
    ROUND(100.0 * session_count / FIRST_VALUE(session_count) OVER (ORDER BY stage_order), 1) AS overall_pct
FROM stages
ORDER BY stage_order;