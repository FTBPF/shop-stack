from shop_stack import db


EXPECTED_TABLES = {
    "load_batches",
    "users",
    "products",
    "orders",
    "order_items",
    "events",
}


def get_tables(conn):
    tables = db.query(
        conn,
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
    )
    return {table["table_name"] for table in tables}


def test_init_schema_creates_all_tables(db_connection):
    db.init_schema(db_connection)

    assert get_tables(db_connection) == EXPECTED_TABLES


def test_drop_schema_removes_all_tables(db_connection):
    db.init_schema(db_connection)

    db.drop_schema(db_connection)

    assert get_tables(db_connection) == set()


def test_init_schema_works_after_drop(db_connection):
    db.init_schema(db_connection)
    db.drop_schema(db_connection)

    db.init_schema(db_connection)

    assert get_tables(db_connection) == EXPECTED_TABLES
