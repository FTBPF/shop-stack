import os
import pathlib
import sqlalchemy as sa


THIS_DIR = pathlib.Path(__file__).parent

INIT_FILE = THIS_DIR / "sql" / "oltp-init.sql"
DROP_FILE = THIS_DIR / "sql" / "oltp-drop.sql"


DEFAULT_URL = 'postgresql+psycopg://'

def get_engine():
    return sa.create_engine(os.environ.get('SHOP_DB_URL', DEFAULT_URL))


def query(conn, sql, **params):
    return conn.execute(sa.text(sql), params).mappings().all()


def drop_schema(conn):
    schema_sql = DROP_FILE.read_text()
    conn.execute(sa.text(schema_sql))

def init_schema(conn):
    schema_sql = INIT_FILE.read_text()
    conn.execute(sa.text(schema_sql))
