import duckdb

from shop_stack import warehouse


EXPECTED_COUNTS = {
    "dim_customer": 5,
    "dim_product": 4,
    "fact_order_items": 11,
    "fact_events": 19,
}


def test_build_warehouse_creates_tables(built_warehouse):
    with duckdb.connect(str(built_warehouse), read_only=True) as conn:
        tables = {
            row[0]
            for row in conn.execute("SHOW TABLES").fetchall()
        }

    assert tables == {
        "dim_customer",
        "dim_product",
        "dim_date",
        "fact_order_items",
        "fact_events",
    }


def test_build_warehouse_row_counts(built_warehouse):
    with duckdb.connect(str(built_warehouse), read_only=True) as conn:
        for table, expected_count in EXPECTED_COUNTS.items():
            result = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            assert result == expected_count


def test_build_warehouse_is_idempotent(tmp_path, warehouse_source_db):
    warehouse_path = tmp_path / "warehouse.duckdb"

    # Primeira construção
    warehouse.build_warehouse(
        warehouse_path,
        db_url=warehouse_source_db,
    )

    with duckdb.connect(str(warehouse_path)) as conn:
        first_counts = {
            table: conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            for table in EXPECTED_COUNTS
        }

    # Segunda construção sobre o mesmo ficheiro
    warehouse.build_warehouse(
        warehouse_path,
        db_url=warehouse_source_db,
    )

    with duckdb.connect(str(warehouse_path), read_only=True) as conn:
        second_counts = {
            table: conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            for table in EXPECTED_COUNTS
        }

    assert first_counts == second_counts == EXPECTED_COUNTS
