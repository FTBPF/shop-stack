MERGE INTO users AS t
USING (
    SELECT
        CAST(:id AS INT) AS id,
        CAST(:first_name AS TEXT) AS first_name,
        CAST(:country AS TEXT) AS country,
        CAST(:traffic_source AS TEXT) AS traffic_source,
        CAST(:created_at AS TIMESTAMPTZ) AS created_at,
        CAST(:load_id AS INT) AS load_id
) AS s
ON t.id = s.id
WHEN MATCHED THEN
    UPDATE SET
        first_name = s.first_name,
        country = s.country,
        traffic_source = s.traffic_source,
        created_at = s.created_at,
        load_id = s.load_id
WHEN NOT MATCHED THEN
    INSERT (id, first_name, country, traffic_source, created_at, load_id)
    VALUES (s.id, s.first_name, s.country, s.traffic_source, s.created_at, s.load_id);
