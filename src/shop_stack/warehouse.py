import os
from pathlib import Path
import duckdb
import sqlalchemy as sa

from . import db

THIS_DIR = Path(__file__).parent
WAREHOUSE_SQL = THIS_DIR / "sql" / "warehouse.sql"


def build_warehouse(warehouse_path, db_url=None):
    """Constrói o star schema em DuckDB lendo diretamente do PostgreSQL."""
    raw_url = db_url or os.environ.get("SHOP_DB_URL", db.DEFAULT_URL)
    pg_url = (
        sa.make_url(raw_url)
        .set(drivername="postgresql")
        .render_as_string(hide_password=False)
    )

    sql_script = WAREHOUSE_SQL.read_text()
    with duckdb.connect(str(warehouse_path)) as conn:
        conn.execute("INSTALL postgres; LOAD postgres;")
        conn.execute(f"ATTACH '{pg_url}' AS oltp (TYPE postgres, READ_ONLY);")
        conn.execute(sql_script)

    return
