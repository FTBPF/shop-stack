SELECT
    d.month_start,
    SUM(foi.sale_price - foi.cost) AS gross_margin
FROM fact_order_items AS foi
JOIN dim_date AS d ON foi.created_date = d."date"
WHERE foi.status NOT IN ('Cancelled', 'Returned')
GROUP BY d.month_start
ORDER BY d.month_start
;
