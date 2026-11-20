MERGE INTO order_items AS t
USING (
    SELECT
        CAST(:id AS INT) AS id,
        CAST(:order_id AS INT) AS order_id,
        CAST(:product_id AS INT) AS product_id,
        CAST(:status AS TEXT) AS status,
        CAST(:created_at AS TIMESTAMPTZ) AS created_at,
        CAST(:sale_price AS NUMERIC(10, 2)) AS sale_price,
        CAST(:load_id AS INT) AS load_id
) AS s
ON t.id = s.id
WHEN MATCHED THEN
    UPDATE SET
        order_id = s.order_id,
        product_id = s.product_id,
        status = s.status,
        created_at = s.created_at,
        sale_price = s.sale_price,
        load_id = s.load_id
WHEN NOT MATCHED THEN
    INSERT (id, order_id, product_id, status, created_at, sale_price, load_id)
    VALUES (s.id, s.order_id, s.product_id, s.status, s.created_at, s.sale_price, s.load_id);
