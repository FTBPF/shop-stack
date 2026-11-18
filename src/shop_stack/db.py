import os
import pathlib
import sqlalchemy as sa


THIS_DIR = pathlib.Path(__file__).parent

INIT_FILE = THIS_DIR / "sql" / "oltp-init.sql"
DROP_FILE = THIS_DIR / "sql" / "oltp-drop.sql"

DEFAULT_URL = 'postgresql+psycopg://'
TABLES = ['events', 'order_items', 'orders', 'products', 'users', 'load_batches']

def get_engine():
    return sa.create_engine(os.environ.get('SHOP_DB_URL', DEFAULT_URL))


def query(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql), params).mappings().all()


def drop_schema(engine):
    schema_sql = DROP_FILE.read_text()
    with engine.begin() as conn:
        conn.execute(sa.text(schema_sql))

def init_schema(engine):
    inspector = sa.inspect(engine)

    if inspector.has_table("users"):
        return False

    schema_sql = INIT_FILE.read_text()

    with engine.begin() as conn:
        conn.execute(sa.text(schema_sql))

    return True
