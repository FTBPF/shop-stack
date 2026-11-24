CREATE OR REPLACE TABLE dim_customer AS
SELECT
    id AS customer_id,
    first_name,
    country,
    traffic_source,
    created_at
FROM oltp.public.users;


CREATE OR REPLACE TABLE dim_product AS
SELECT
    id AS product_id,
    name,
    category,
    department,
    brand,
    cost,
    retail_price
FROM oltp.public.products;


CREATE OR REPLACE TABLE dim_date AS
WITH date_bounds AS (
    SELECT
        MIN("date") AS min_date,
        MAX("date") AS max_date
    FROM (
        SELECT CAST(created_at AS DATE) AS "date"
        FROM oltp.public.order_items
        UNION ALL
        SELECT CAST(created_at AS DATE) AS "date"
        FROM oltp.public.events
    )
),
calendar AS (
    SELECT CAST(d AS DATE) AS "date"
    FROM date_bounds,
         generate_series(min_date, max_date, INTERVAL '1 day') AS series(d)
)
SELECT
    "date",
    EXTRACT(YEAR FROM "date")::INTEGER AS year,
    EXTRACT(MONTH FROM "date")::INTEGER AS month,
    DATE_TRUNC('month', "date")::DATE AS month_start,
    EXTRACT(ISODOW FROM "date")::INTEGER AS dow,
    STRFTIME("date", '%A') AS dow_name
FROM calendar;


CREATE OR REPLACE TABLE fact_order_items AS
SELECT
    oi.id AS order_item_id,
    oi.order_id,
    o.user_id AS customer_id,
    oi.product_id,
    CAST(oi.created_at AS DATE) AS created_date,
    oi.status,
    oi.sale_price,
    p.cost
FROM oltp.public.order_items AS oi
JOIN oltp.public.orders AS o
    ON oi.order_id = o.order_id
JOIN oltp.public.products AS p
    ON oi.product_id = p.id;


CREATE OR REPLACE TABLE fact_events AS
SELECT
    e.id AS event_id,
    e.user_id AS customer_id,
    e.session_id,
    e.sequence_number,
    CAST(e.created_at AS DATE) AS created_date,
    e.event_type
FROM oltp.public.events AS e;
