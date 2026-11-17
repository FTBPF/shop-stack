CREATE TABLE if NOT EXISTS load_batches (
    load_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    load_status TEXT NOT NULL DEFAULT 'running',

    CONSTRAINT ck_load_batches_status CHECK (load_status IN ('running', 'succeeded', 'failed')),
    CONSTRAINT ck_load_batches_timestamps CHECK (
        (load_status = 'running' AND completed_at IS NULL)
        OR (load_status IN ('succeeded', 'failed') AND completed_at IS NOT NULL)
    )
);


CREATE TABLE if NOT EXISTS users (
    user_id INT PRIMARY KEY,
    first_name TEXT,
    country TEXT,
    traffic_source TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    load_id INT NOT NULL REFERENCES load_batches(load_id)
);


CREATE TABLE if NOT EXISTS products (
    product_id INT PRIMARY KEY,
    product_name TEXT,
    category TEXT,
    brand TEXT,
    department TEXT,
    cost NUMERIC(10, 2) NOT NULL,
    retail_price NUMERIC(10, 2) NOT NULL,
    load_id INT NOT NULL REFERENCES load_batches(load_id),

    CONSTRAINT ck_products_cost CHECK (cost >= 0),
    CONSTRAINT ck_products_retail_price CHECK (retail_price >= 0)
);



CREATE TABLE if NOT EXISTS orders (
    order_id INT PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    order_status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    load_id INT NOT NULL REFERENCES load_batches(load_id),

    CONSTRAINT ck_orders_status CHECK (order_status IN ('Cancelled', 'Complete', 'Processing', 'Returned', 'Shipped'))
);


CREATE TABLE if NOT EXISTS order_items (
    order_item_id INT PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id),
    product_id INT NOT NULL REFERENCES products(product_id),
    order_item_status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    sale_price NUMERIC(10, 2) NOT NULL,
    load_id INT NOT NULL REFERENCES load_batches(load_id),

    CONSTRAINT ck_order_items_status CHECK (order_item_status IN ('Cancelled', 'Complete', 'Processing', 'Returned', 'Shipped')),
    CONSTRAINT ck_order_items_sale_price CHECK (sale_price >= 0)
);


CREATE TABLE if NOT EXISTS events (
    event_id INT PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    session_id TEXT NOT NULL,
    sequence_number INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    load_id INT NOT NULL REFERENCES load_batches(load_id),

    CONSTRAINT ck_events_event_type CHECK (event_type IN ('home', 'department', 'product', 'cart', 'purchase', 'cancel'))
);
