SELECT
    p.category,
    ROUND(100.0 * SUM(CASE WHEN foi.status = 'Returned' THEN 1 ELSE 0 END) / COUNT(*), 2) AS return_rate_pct
FROM fact_order_items AS foi
JOIN dim_product AS p ON foi.product_id = p.product_id
WHERE foi.status <> 'Cancelled'
GROUP BY p.category
ORDER BY p.category
;
