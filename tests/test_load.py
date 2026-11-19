import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from shop_stack import db, loading


def test_load_fixtures_counts_and_reconciliation(engine, fixtures_dir):
    counts = loading.load_all(engine, fixtures_dir)

    assert counts == {
        "users": 5,
        "products": 4,
        "orders": 9,
        "order_items": 11,
        "events": 19,
    }

    # Confirma que ficou registado como 'succeeded'
    batches = db.query(engine, "SELECT load_status, completed_at FROM load_batches")
    assert len(batches) == 1
    assert batches[0]["load_status"] == "succeeded"
    assert batches[0]["completed_at"] is not None


def test_load_is_idempotent(engine, fixtures_dir):
    loading.load_all(engine, fixtures_dir)
    loading.load_all(engine, fixtures_dir)

    rows = db.query(engine, "SELECT COUNT(*) AS n FROM order_items")
    assert rows[0]["n"] == 11

    batches = db.query(engine, "SELECT COUNT(*) AS n FROM load_batches")
    assert batches[0]["n"] == 2


def test_load_missing_directory_or_file(engine, fixtures_dir, tmp_path):
    with pytest.raises(FileNotFoundError):
        loading.load_all(engine, tmp_path / "does_not_exist")

    incomplete_dir = tmp_path / "incomplete"
    incomplete_dir.mkdir()

    for csv_file in fixtures_dir.glob("*.csv"):
        if csv_file.name != "events.csv":
            destination = incomplete_dir / csv_file.name
            destination.write_text(csv_file.read_text())

    with pytest.raises(FileNotFoundError):
        loading.load_all(engine, incomplete_dir)


def create_bad_fixtures(fixtures_dir, tmp_path, filename, column, value):
    """Create a temporary directory that holds bad data."""
    bad_dir = tmp_path / "bad_data"
    bad_dir.mkdir()

    for csv_file in fixtures_dir.glob("*.csv"):
        (bad_dir / csv_file.name).write_text(csv_file.read_text())

    csv_file = bad_dir / filename
    lines = csv_file.read_text().splitlines()

    headers = lines[0].split(",")
    parts = lines[1].split(",")

    parts[headers.index(column)] = value
    lines[1] = ",".join(parts)

    csv_file.write_text("\n".join(lines) + "\n")

    return bad_dir


def test_load_negative_price_rolls_back(engine, fixtures_dir, tmp_path):
    bad_dir = create_bad_fixtures(
        fixtures_dir, tmp_path, "order_items.csv", "sale_price", "-10.00"
    )

    with pytest.raises(IntegrityError):
        loading.load_all(engine, bad_dir)

    for table in loading.LOAD_ORDER:
        assert db.query(engine, f"SELECT COUNT(*) AS n FROM {table}")[0]["n"] == 0


def test_load_unknown_product_rolls_back(engine, fixtures_dir, tmp_path):
    bad_dir = create_bad_fixtures(
        fixtures_dir, tmp_path, "order_items.csv", "product_id", "99999"
    )

    with pytest.raises(IntegrityError):
        loading.load_all(engine, bad_dir)

    for table in loading.LOAD_ORDER:
        assert db.query(engine, f"SELECT COUNT(*) AS n FROM {table}")[0]["n"] == 0
