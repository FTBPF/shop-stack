from pathlib import Path
import duckdb
import sqlalchemy as sa

SQL_DIR = Path(__file__).parent / "sql"

READERS = {
    ".csv": "SELECT * FROM read_csv(?)",
    ".parquet": "SELECT * FROM read_parquet(?)",
}

TARGET_TABLES = [
    {
        "name": "users",
        "file_prefix": "users",
        "sql_file": "merge_users.sql",
    },
    {
        "name": "products",
        "file_prefix": "products",
        "sql_file": "merge_products.sql",
    },
    {
        "name": "orders",
        "file_prefix": "orders",
        "sql_file": "merge_orders.sql",
    },
    {
        "name": "order_items",
        "file_prefix": "order_items",
        "sql_file": "merge_order_items.sql",
    },
    {
        "name": "events",
        "file_prefix": "events",
        "sql_file": "merge_events.sql",
    },
]


def files_matching(source_dir, file_prefix):
    """Procura todos os ficheiros {file_prefix}*.parquet e {file_prefix}*.csv na pasta."""
    files = []
    for file_type in (".parquet", ".csv"):
        files.extend(source_dir.glob(f"{file_prefix}*{file_type}"))
    return sorted(files)


def read_rows(filename, load_id):
    """Lê um ficheiro CSV ou Parquet usando DuckDB e adiciona o load_id em cada linha."""
    result = duckdb.execute(READERS[filename.suffix], [str(filename)])
    columns = [d[0] for d in result.description]
    return [dict(zip(columns, row), load_id=load_id) for row in result.fetchall()]


def count_rows(conn, table_name):
    """Devolve o número atual de linhas na tabela."""
    return conn.execute(sa.text(f"SELECT COUNT(*) FROM {table_name}")).scalar_one()


def count_touched(conn, table_name, load_id):
    return conn.execute(
        sa.text(f"SELECT COUNT(*) FROM {table_name} WHERE load_id = :load_id"),
        {"load_id": load_id},
    ).scalar_one()


def read_sql(name):
    """Lê um ficheiro .sql da pasta sql/."""
    return (SQL_DIR / name).read_text()


def merge_rows(conn, sql_file, rows):
    """Executa o MERGE da tabela, uma vez por linha."""
    if not rows:
        return
    conn.execute(sa.text(read_sql(sql_file)), rows)


def load_table(conn, table, source_dir, load_id):
    """Carrega todos os ficheiros e devolve as contagens."""
    name = table["name"]
    before = count_rows(conn, name)
    read = 0

    for path in files_matching(source_dir, table["file_prefix"]):
        rows = read_rows(path, load_id)
        merge_rows(conn, table["sql_file"], rows)
        read = read + len(rows)
    after = count_rows(conn, name)
    touched = count_touched(conn, name, load_id)
    inserted = after - before
    updated = touched - inserted
    return {
        "table": name, 
        "before": before, 
        "read": read, 
        "inserted": inserted, 
        "updated": updated, 
        "after": after
    }


def load_all(conn, source_dir):
    """Carrega todos os ficheiros de todas as tabelas, numa só transação."""
    load_id = conn.execute(
        sa.text("INSERT INTO load_batches DEFAULT VALUES RETURNING load_id")
    ).scalar_one()

    summaries = []
    for table in TARGET_TABLES:
        summaries = summaries + [load_table(conn, table, source_dir, load_id)]
    
    conn.execute(
        sa.text(
            "UPDATE load_batches "
            "SET load_status = 'succeeded', completed_at = clock_timestamp() "
            "WHERE load_id = :load_id"
        ),
        {"load_id": load_id},
    )
    return summaries
