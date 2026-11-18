CREATE TABLE IF NOT EXISTS load_batches (
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

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY,
    first_name TEXT,
    country TEXT,
    traffic_source TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    load_id INT NOT NULL REFERENCES load_batches(load_id)
);

CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY,
    name TEXT,
    category TEXT,
    brand TEXT,
    department TEXT,
    cost NUMERIC(10, 2) NOT NULL,
    retail_price NUMERIC(10, 2) NOT NULL,
    load_id INT NOT NULL REFERENCES load_batches(load_id),

    CONSTRAINT ck_products_cost CHECK (cost >= 0),
    CONSTRAINT ck_products_retail_price CHECK (retail_price >= 0)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INT PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id),
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    load_id INT NOT NULL REFERENCES load_batches(load_id),

    CONSTRAINT ck_orders_status CHECK (status IN ('Cancelled', 'Complete', 'Processing', 'Returned', 'Shipped'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id INT PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id),
    product_id INT NOT NULL REFERENCES products(id),
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    sale_price NUMERIC(10, 2) NOT NULL,
    load_id INT NOT NULL REFERENCES load_batches(load_id),

    CONSTRAINT ck_order_items_status CHECK (status IN ('Cancelled', 'Complete', 'Processing', 'Returned', 'Shipped')),
    CONSTRAINT ck_order_items_sale_price CHECK (sale_price >= 0)
);

CREATE TABLE IF NOT EXISTS events (
    id BIGINT PRIMARY KEY,
    user_id INT REFERENCES users(id),
    session_id TEXT NOT NULL,
    sequence_number INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    load_id INT NOT NULL REFERENCES load_batches(load_id),

    CONSTRAINT ck_events_event_type CHECK (event_type IN ('home', 'department', 'product', 'cart', 'purchase', 'cancel'))
);
