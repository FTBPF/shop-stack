import pytest
from pathlib import Path
from sqlalchemy.exc import IntegrityError

from shop_stack import db, loading


BAD_FIXTURES_DIR = Path(__file__).parent / "bad_fixtures"

EXPECTED_COUNTS = {
    "users": 5,
    "products": 4,
    "orders": 9,
    "order_items": 11,
    "events": 19,
}


def get_last_load_id(conn):
    rows = db.query(conn, "SELECT MAX(load_id) AS load_id FROM load_batches")
    return rows[0]["load_id"]


def assert_counts(conn, load_id, expected):
    for table, count in expected.items():
        rows = db.query(conn, f"SELECT COUNT(*) AS n FROM {table} WHERE load_id = :load_id", load_id=load_id,)
        assert rows[0]["n"] == count


def assert_tables_empty(conn):
    for table in loading.TARGET_TABLES:
        name = table["name"]
        rows = db.query(conn, f"SELECT COUNT(*) AS n FROM {name}")
        assert rows[0]["n"] == 0


def test_load_fixtures_counts(db_connection, fixtures_dir):
    summaries = loading.load_all(db_connection, fixtures_dir)

    assert {summary["table"]: summary["read"] for summary in summaries} == EXPECTED_COUNTS

    load_id = get_last_load_id(db_connection)
    assert_counts(db_connection, load_id, EXPECTED_COUNTS)


def test_load_registers_successful_batch(db_connection, fixtures_dir):
    loading.load_all(db_connection, fixtures_dir)

    load_id = get_last_load_id(db_connection)

    batches = db.query(db_connection,
        """
        SELECT load_status, completed_at
        FROM load_batches
        WHERE load_id = :load_id
        """,
        load_id=load_id,
    )

    assert len(batches) == 1
    assert batches[0]["load_status"] == "succeeded"
    assert batches[0]["completed_at"] is not None


def test_load_is_idempotent(db_connection, fixtures_dir):
    first_load = loading.load_all(db_connection, fixtures_dir)
    first_load_id = get_last_load_id(db_connection)
    assert_counts(db_connection, first_load_id, EXPECTED_COUNTS)

    for summary in first_load:
        assert summary["inserted"] == EXPECTED_COUNTS[summary["table"]]
        assert summary["updated"] == 0
        assert summary["read"] == EXPECTED_COUNTS[summary["table"]]

    second_load = loading.load_all(db_connection, fixtures_dir)
    second_load_id = get_last_load_id(db_connection)
    assert second_load_id != first_load_id

    assert_counts(db_connection, second_load_id, EXPECTED_COUNTS)

    for summary in second_load:
        assert summary["inserted"] == 0
        assert summary["updated"] == EXPECTED_COUNTS[summary["table"]]
        assert summary["read"] == EXPECTED_COUNTS[summary["table"]]

    for table, expected_count in EXPECTED_COUNTS.items():
        rows = db.query(db_connection, f"SELECT COUNT(*) AS n FROM {table}")
        assert rows[0]["n"] == expected_count


def test_load_missing_directory(db_connection, tmp_path):
    with pytest.raises(FileNotFoundError):
        loading.load_all(db_connection, tmp_path / "does_not_exist")


def test_load_negative_price_violates_check_constraint(db_connection):
    bad_dir = BAD_FIXTURES_DIR / "negative_price"
    with pytest.raises(IntegrityError):
        with db_connection.begin_nested():
            loading.load_all(db_connection, bad_dir)


def test_load_unknown_product_violates_foreign_key(db_connection):
    bad_dir = BAD_FIXTURES_DIR / "unknown_product_id"
    with pytest.raises(IntegrityError):
        with db_connection.begin_nested():
            loading.load_all(db_connection, bad_dir)
