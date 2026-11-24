import duckdb
import pytest

from shop_stack import db, loading, warehouse


EXPECTED_COUNTS = {
    "dim_customer": 5,
    "dim_product": 4,
    "fact_order_items": 11,
    "fact_events": 19,
}


@pytest.fixture
def warehouse_source_db(db_engine, test_db_url, fixtures_dir):
    """Prepara e carrega a base PostgreSQL usada pelo warehouse."""

    # Passing db_engine because DuckDB opens an independent connection
    # and cannot see uncommitted changes from db_connection.
    with db_engine.begin() as conn:
        db.drop_schema(conn)
        db.init_schema(conn)
        loading.load_all(conn, fixtures_dir)

    yield test_db_url

    with db_engine.begin() as conn:
        db.drop_schema(conn)


@pytest.fixture
def built_warehouse(tmp_path, warehouse_source_db):
    """Constrói um warehouse temporário para os testes."""

    warehouse_path = tmp_path / "warehouse.duckdb"

    warehouse.build_warehouse(
        warehouse_path,
        db_url=warehouse_source_db,
    )

    return warehouse_path


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
