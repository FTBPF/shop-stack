MERGE INTO events AS t
USING (
    SELECT
        CAST(:id AS BIGINT) AS id,
        CAST(:user_id AS INT) AS user_id,
        CAST(:session_id AS TEXT) AS session_id,
        CAST(:sequence_number AS INT) AS sequence_number,
        CAST(:created_at AS TIMESTAMPTZ) AS created_at,
        CAST(:event_type AS TEXT) AS event_type,
        CAST(:load_id AS INT) AS load_id
) AS s
ON t.id = s.id
WHEN MATCHED THEN
    UPDATE SET
        user_id = s.user_id,
        session_id = s.session_id,
        sequence_number = s.sequence_number,
        created_at = s.created_at,
        event_type = s.event_type,
        load_id = s.load_id
WHEN NOT MATCHED THEN
    INSERT (id, user_id, session_id, sequence_number, created_at, event_type, load_id)
    VALUES (s.id, s.user_id, s.session_id, s.sequence_number, s.created_at, s.event_type, s.load_id);
