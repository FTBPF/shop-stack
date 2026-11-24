SELECT
    c.traffic_source,
    COALESCE(SUM(foi.sale_price), 0) AS revenue
FROM dim_customer AS c
LEFT JOIN fact_order_items AS foi ON c.customer_id = foi.customer_id AND foi.status NOT IN ('Cancelled', 'Returned')
GROUP BY c.traffic_source
ORDER BY revenue DESC, c.traffic_source
;
