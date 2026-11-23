MERGE INTO orders AS t
USING (
    SELECT
        CAST(:order_id AS INT) AS order_id,
        CAST(:user_id AS INT) AS user_id,
        CAST(:status AS TEXT) AS status,
        CAST(:created_at AS TIMESTAMPTZ) AS created_at,
        CAST(:load_id AS UUID) AS load_id
) AS s
ON t.order_id = s.order_id
WHEN MATCHED THEN
    UPDATE SET
        user_id = s.user_id,
        status = s.status,
        created_at = s.created_at,
        load_id = s.load_id
WHEN NOT MATCHED THEN
    INSERT (order_id, user_id, status, created_at, load_id)
    VALUES (s.order_id, s.user_id, s.status, s.created_at, s.load_id);
