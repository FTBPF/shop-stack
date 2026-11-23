MERGE INTO products AS t
USING (
    SELECT
        CAST(:id AS INT) AS id,
        CAST(:name AS TEXT) AS name,
        CAST(:category AS TEXT) AS category,
        CAST(:brand AS TEXT) AS brand,
        CAST(:department AS TEXT) AS department,
        CAST(:cost AS NUMERIC(10, 2)) AS cost,
        CAST(:retail_price AS NUMERIC(10, 2)) AS retail_price,
        CAST(:load_id AS UUID) AS load_id
) AS s
ON t.id = s.id
WHEN MATCHED THEN
    UPDATE SET
        name = s.name,
        category = s.category,
        brand = s.brand,
        department = s.department,
        cost = s.cost,
        retail_price = s.retail_price,
        load_id = s.load_id
WHEN NOT MATCHED THEN
    INSERT (id, name, category, brand, department, cost, retail_price, load_id)
    VALUES (s.id, s.name, s.category, s.brand, s.department, s.cost, s.retail_price, s.load_id);
