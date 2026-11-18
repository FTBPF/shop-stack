from pathlib import Path
import duckdb
import sqlalchemy as sa

from . import db

LOAD_ORDER = ["users", "products", "orders", "order_items", "events"]

DELETE_ORDER = ["events", "order_items", "orders", "products", "users"]

READERS = {
    ".csv": "SELECT * FROM read_csv(?)",
    ".parquet": "SELECT * FROM read_parquet(?)",
}

INSERT_SQL = {
    "users": """
        INSERT INTO users (id, first_name, country, traffic_source, created_at, load_id)
        VALUES (:id, :first_name, :country, :traffic_source, :created_at, :load_id)
    """,

    "products": """
        INSERT INTO products (id, name, category, brand, department, cost, retail_price, load_id)
        VALUES (:id, :name, :category, :brand, :department, :cost, :retail_price, :load_id)
    """,

    "orders": """
        INSERT INTO orders (order_id, user_id, status, created_at, load_id)
        VALUES (:order_id, :user_id, :status, :created_at, :load_id)
    """,

    "order_items": """
        INSERT INTO order_items (id, order_id, product_id, status, created_at, sale_price, load_id)
        VALUES (:id, :order_id, :product_id, :status, :created_at, :sale_price, :load_id)
    """,

    "events": """
        INSERT INTO events (id, user_id, session_id, sequence_number, created_at, event_type, load_id)
        VALUES (:id, :user_id, :session_id, :sequence_number, :created_at, :event_type, :load_id)
    """,
}

def find_source_file(source_dir, table):
    """Procura {table}.parquet ou {table}.csv {source_dir}."""
    for file_type in (".parquet", ".csv"):
        candidate = source_dir / f"{table}{file_type}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(F"Missing source file for '{table}' in {source_dir}")


def read_rows(path):
    """Lê um ficheiro usando o DuckDB e devolve uma lista de dicionários."""
    result = duckdb.execute(READERS[path.suffix], [str(path)])
    columns = [d[0] for d in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def prepare_rows(raw_rows, load_id):
    return [
        {**row, "load_id": load_id}
        for row in raw_rows
    ]


def load_all(engine: sa.Engine, source_dir: Path) -> dict[str, int]:
    """Carrega todos os ficheiros para o PostgreSQL numa única transação e reconcilia contagens."""
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    # Lê todos os ficheiros antes de abrir transação na base de dados
    raw_data = {}
    for table in LOAD_ORDER:
        path = find_source_file(source_dir, table)
        raw_data[table] = read_rows(path)

    # Cria o esquema se ainda não existir
    db.init_schema(engine)

    counts = {}

    # Executa limpeza, inserção e reconciliação numa única transação
    # Não apagar a tabela load_batches para manter o histórico de todos os loads
    with engine.begin() as conn:
        for table in DELETE_ORDER:
            conn.execute(sa.text(f"DELETE FROM {table}"))

        load_id = conn.execute(
            sa.text("INSERT INTO load_batches DEFAULT VALUES RETURNING load_id")
        ).scalar_one()

        for table in LOAD_ORDER:
            rows = prepare_rows(raw_data[table], load_id)
            if rows:
                conn.execute(sa.text(INSERT_SQL[table]), rows)

            # Reconciliação de contagens
            db_count = conn.execute(
                sa.text(f"SELECT COUNT(*) FROM {table}")
            ).scalar_one()
            expected_count = len(rows)

            if db_count != expected_count:
                raise RuntimeError(f"Failed reconciliation for '{table}': expected {expected_count} rows, got {db_count}")
            counts[table] = db_count

        conn.execute(
            sa.text(
                "UPDATE load_batches SET load_status = 'succeeded', completed_at = NOW() WHERE load_id = :load_id"
            ),
            {"load_id": load_id},
        )

    return counts
